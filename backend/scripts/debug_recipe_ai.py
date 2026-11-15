"""Debug why a recipe AI answer fails validation. Not run by tests; calls the real Groq API.

Run from backend/ with a key in your shell (synthetic data only, no PHI, no real database):

    GROQ_API_KEY=... python scripts/debug_recipe_ai.py            # current request
    GROQ_API_KEY=... python scripts/debug_recipe_ai.py --legacy   # the old request, for "before"
    python scripts/debug_recipe_ai.py --dry-run                   # build only, no network

Prints finish_reason, token usage, raw response length and validation error field names. It
never prints the model's text.
"""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault(
    "FIELD_ENCRYPTION_KEY", __import__("cryptography.fernet").fernet.Fernet.generate_key().decode()
)

import httpx
from cryptography.fernet import Fernet
from pydantic import ValidationError
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.context_manifest import build_manifest
from app.ai.provider import GROQ_DEFAULT_MODEL, AITask, GroqProvider, _payload, extract_json_object
from app.ai.schemas import RecipeOutput
from app.ai.validators import AIValidationError, validate_ai_output
from app.auth import email_lookup_hash
from app.db import Base
from app.models import Client, User
from app.routes.recipes import _allowed_stock, manifest_products
from app.services.nutrition import household_choices
from seed.load import seed_catalog, seed_users

URL = "https://api.groq.com/openai/v1/chat/completions"


def build_request(model: str, legacy: bool):
    os.environ.setdefault("FIELD_ENCRYPTION_KEY", Fernet.generate_key().decode())
    engine = create_engine("sqlite://")  # in-memory synthetic catalog; never a real database
    Base.metadata.create_all(engine)
    with Session(engine) as database:
        seed_users(database)
        seed_catalog(database)
        user = database.scalar(
            select(User).where(User.email_hash == email_lookup_hash("client.active@example.test"))
        )
        client = database.get(Client, user.id)
        profile = household_choices(client)
        products, _ = _allowed_stock(database, profile)
        items = manifest_products(products, [], profile, None)
        restrictions = [*profile["restrictions"], *profile["allergies"]]
        manifest, _ = build_manifest(items, restrictions, {}, client.Household_Size)
    content = _payload(AITask.RECIPES, manifest)
    body = GroqProvider.request_body(model, AITask.RECIPES, content)
    if legacy:  # what production sent before the fix
        body = {
            "model": model,
            "messages": body["messages"],
            "response_format": {"type": "json_object"},
        }
    return manifest, body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    model = (os.getenv("GROQ_MODEL") or "").strip() or GROQ_DEFAULT_MODEL
    manifest, body = build_request(model, args.legacy)
    print(
        f"model={model} manifest_items={len(manifest.items)} request_bytes={len(json.dumps(body))}"
    )
    print("request_keys=", sorted(body), "response_format=", body["response_format"]["type"])
    if args.dry_run:
        return
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key:
        raise SystemExit("Set GROQ_API_KEY in your shell (or use --dry-run).")

    response = httpx.post(
        URL, headers={"Authorization": f"Bearer {api_key}"}, json=body, timeout=60
    )
    print("http_status=", response.status_code)
    data = response.json()
    if response.status_code != 200:
        error = data.get("error", {})
        print("error_type=", error.get("type"), "error_code=", error.get("code"))
        print("error_message=", str(error.get("message"))[:300])
        return
    choice = data["choices"][0]
    content = choice["message"].get("content") or ""
    usage = data.get("usage", {})
    print("finish_reason=", choice.get("finish_reason"))
    print("usage=", {k: v for k, v in usage.items() if isinstance(v, int | dict)})
    print("raw_response_length=", len(content))
    try:
        output = extract_json_object(content)
    except json.JSONDecodeError as exc:
        print("json_parse=FAILED", type(exc).__name__, "at char", exc.pos)
        return
    print(
        "json_parse=ok top_level_keys=",
        sorted(output) if isinstance(output, dict) else type(output),
    )
    try:
        RecipeOutput.model_validate(output)
        print("schema=ok")
    except ValidationError as exc:
        for error in exc.errors():
            print("schema_error field=", ".".join(map(str, error["loc"])), "type=", error["type"])
    try:
        validate_ai_output("recipes", output, manifest)
        print("validate_ai_output=ok")
    except AIValidationError as exc:
        print("validate_ai_output=FAILED:", exc)


if __name__ == "__main__":
    main()
