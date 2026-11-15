"""Recipe-AI evaluation harness. Synthetic data only; the database is an in-memory SQLite seed.

Run from backend/ (Ollama needs OLLAMA_BASE_URL, Groq needs GROQ_API_KEY in your shell):

    python -m eval.run_eval --provider ollama --model gpt-oss:20b
    python -m eval.run_eval --provider groq --model openai/gpt-oss-20b --limit 3
    python -m eval.summarize        # writes docs/ai-eval-results.md

Each case goes through the app's real recipe path (manifest_products -> run_ai_task -> validation
-> apply_rules_guard -> guard_recipes -> cuisine/focus filter -> fallback). Raw results hold
counts and findings only: no prompts and no model text beyond ingredient names.
"""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
os.environ["DATABASE_URL"] = "sqlite://"  # app.db builds an engine on import: never a real one
if not os.getenv("FIELD_ENCRYPTION_KEY"):
    os.environ["FIELD_ENCRYPTION_KEY"] = (
        __import__("cryptography.fernet").fernet.Fernet.generate_key().decode()
    )

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.context_manifest import build_manifest
from app.ai.fallback import build_fallback_recipes
from app.ai.provider import GROQ_DEFAULT_MODEL, OLLAMA_DEFAULT_URL, PROVIDERS, AIProvider
from app.ai.validators import AIValidationError, validate_ai_output
from app.auth import email_lookup_hash
from app.db import Base
from app.models import Client, Product, User
from app.routes.recipes import _ai_suggestions, _allowed_stock, manifest_products
from app.services.nutrition import household_choices, members_for
from eval.safety import check_recipes
from seed.load import seed_catalog, seed_users

CASES_PATH = Path(__file__).with_name("cases.json")
RESULTS_DIR = Path(__file__).with_name("results")


class Recorder(AIProvider):
    """Wraps the real provider: times each call and records validity, finish_reason and tokens."""

    def __init__(self, inner: AIProvider):
        self.inner = inner
        self.name = inner.name
        self.last_finish_reason = None
        self.attempts: list[dict] = []
        self.raws: list[object] = []

    def generate_json(self, task, manifest, feedback=None):
        started = time.monotonic()
        attempt = {"retry": feedback is not None}
        self.inner.last_finish_reason = self.inner.last_usage = None  # never report a past call
        try:
            raw = self.inner.generate_json(task, manifest, feedback)
        except Exception as exc:
            attempt.update(valid=False, error=f"{type(exc).__name__}: {exc}"[:200])
            raise
        else:
            try:
                validate_ai_output(task.value, raw, manifest)
                attempt.update(valid=True, error=None)
            except AIValidationError as exc:
                attempt.update(valid=False, error=str(exc)[:300])
            self.raws.append(raw)
            return raw
        finally:
            self.last_finish_reason = getattr(self.inner, "last_finish_reason", None)
            attempt.update(
                latency_s=round(time.monotonic() - started, 3),
                finish_reason=self.last_finish_reason,
                usage=getattr(self.inner, "last_usage", None),
            )
            self.attempts.append(attempt)


def build_world() -> Session:
    """Seeded in-memory database (synthetic users, households and catalog)."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    database = Session(engine)
    seed_users(database)
    seed_catalog(database)
    return database


def _client(database: Session, persona: str) -> Client:
    user = database.scalar(
        select(User).where(User.email_hash == email_lookup_hash(f"{persona}@example.test"))
    )
    return database.get(Client, user.id)


def _resolve(index: object, index_map: dict[int, int]) -> dict:
    if isinstance(index, int) and index in index_map:
        return {"product_id": index_map[index]}
    why = "unknown index" if isinstance(index, int) else "null product_id"
    return {"product_id": None, "why": f"not in manifest ({why})"}


def raw_recipes(raw: object, index_map: dict[int, int]) -> list[dict]:
    """Recipes from a raw model answer, tolerant of schema errors, with manifest indexes mapped
    to real product ids (None when null or unknown) so unsafe-but-invalid output is still seen."""
    recipes = raw.get("recipes") if isinstance(raw, dict) else None
    out = []
    for recipe in recipes if isinstance(recipes, list) else []:
        if not isinstance(recipe, dict):
            continue
        ingredients = [
            {"name": str(i.get("name", "")), **_resolve(i.get("product_id"), index_map)}
            for i in recipe.get("ingredients") or []
            if isinstance(i, dict)
        ]
        steps = [s for s in recipe.get("steps") or [] if isinstance(s, str)]
        out.append(
            {"title": str(recipe.get("title", "")), "ingredients": ingredients, "steps": steps}
        )
    return out


def _in_stock(recipes: list[dict], stock: dict[int, Product]) -> tuple[int, int]:
    ingredients = [i for r in recipes for i in r["ingredients"]]
    return sum(i["product_id"] in stock for i in ingredients), len(ingredients)


def run_case(database: Session, case: dict, provider: AIProvider) -> dict:
    """One case through the app's recipe path, with safety checks before and after the guard."""
    client = _client(database, case["persona"])
    profile, members = household_choices(client), members_for(client)
    by_sku = {p.sku: p for p in database.scalars(select(Product))}
    focus = by_sku[case["scanned_sku"]].id
    cart = [
        {
            "product_id": by_sku[i["sku"]].id,
            "name": by_sku[i["sku"]].name,
            "quantity": i["quantity"],
        }
        for i in case["cart"]
    ]
    stock, locations = _allowed_stock(database, profile)
    items = manifest_products(stock, cart, profile, focus)
    restrictions = [*profile["restrictions"], *profile["allergies"]]
    quantities = {row["product_id"]: row["quantity"] for row in cart}
    manifest_stock = {p.id: p for p in items}
    _, index_map = build_manifest(items, restrictions, quantities, client.Household_Size)

    recorder = Recorder(provider)
    started = time.monotonic()
    error = None
    with patch("app.ai.orchestrator.get_provider", return_value=recorder):
        try:  # same shape as the route: any AI failure falls back to the deterministic recipes
            _, final, _ = _ai_suggestions(
                stock, locations, cart, profile, client.Household_Size, focus, case["cuisine"]
            )
            used_fallback = False
        except Exception as exc:
            used_fallback, error = True, f"{type(exc).__name__}: {exc}"[:200]
            inventory = [{"product_id": p.id, "name": p.name} for p in stock.values()]
            final = build_fallback_recipes(cart, inventory, focus, case["cuisine"])
    latency = round(time.monotonic() - started, 3)

    pre = [r for raw in recorder.raws for r in raw_recipes(raw, index_map)]
    pre_in, pre_total = _in_stock(pre, manifest_stock)
    post_in, post_total = _in_stock(final, stock)
    attempts = recorder.attempts
    return {
        "id": case["id"],
        "persona": case["persona"],
        "tags": case["tags"],
        "json_valid_first_try": bool(attempts) and attempts[0]["valid"],
        "json_valid_after_retry": any(a["valid"] for a in attempts),
        "retried": len(attempts) > 1,
        "used_fallback": used_fallback,
        "fallback_reason": error,
        "recipes_pre_guard": len(pre),
        "recipes_after_guard": 0 if used_fallback else len(final),
        "recipes_final": len(final),
        "ingredients_pre_guard": {"in_stock": pre_in, "total": pre_total},
        "ingredients_final": {"in_stock": post_in, "total": post_total},
        "latency_s": latency,
        "attempts": attempts,
        "pre_guard_findings": check_recipes(pre, members, manifest_stock),
        "post_guard_findings": check_recipes(final, members, stock),
    }


def warm_up_ollama(model: str) -> None:
    """Load the model before timing starts, so the first case does not pay for it."""
    host = (os.getenv("OLLAMA_BASE_URL") or OLLAMA_DEFAULT_URL).rstrip("/")
    httpx.post(
        f"{host}/api/generate",
        json={"model": model, "prompt": "ok", "stream": False, "options": {"num_predict": 1}},
        timeout=600,
    ).raise_for_status()


def select_model(provider_name: str, model: str | None) -> str:
    """Resolve the model and set the env var the provider reads."""
    env = "OLLAMA_MODEL" if provider_name == "ollama" else "GROQ_MODEL"
    fallback = "" if provider_name == "ollama" else GROQ_DEFAULT_MODEL
    model = model or os.getenv(env) or fallback
    if not model:
        raise SystemExit("Pass --model or set OLLAMA_MODEL.")
    os.environ[env] = model
    return model


def main() -> None:
    from eval.summarize import aggregate, print_summary

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument("--model")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument(
        "--pause", type=float, default=0, help="seconds between cases (rate limits)"
    )
    args = parser.parse_args()
    if args.provider == "groq" and not (os.getenv("GROQ_API_KEY") or "").strip():
        raise SystemExit("Set GROQ_API_KEY in your shell.")

    model = select_model(args.provider, args.model)
    cases = json.loads(args.cases.read_text())["cases"][: args.limit]
    if args.provider == "ollama":
        warm_up_ollama(model)
    database = build_world()
    provider = PROVIDERS[args.provider]()
    results = []
    for case in cases:
        time.sleep(args.pause if results else 0)
        result = run_case(database, case, provider)
        results.append(result)
        print(
            f"{result['id']:<18} valid1={int(result['json_valid_first_try'])} "
            f"fallback={int(result['used_fallback'])} recipes={result['recipes_after_guard']} "
            f"latency={result['latency_s']}s"
        )

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_model = re.sub(r"[^A-Za-z0-9._-]+", "-", model)
    out = args.out_dir / f"{args.provider}_{safe_model}_{stamp}.json"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"provider": args.provider, "model": model, "results": results}, indent=1)
    )
    print_summary(f"{args.provider} {model}", aggregate(results))
    print("wrote", out)


if __name__ == "__main__":
    main()
