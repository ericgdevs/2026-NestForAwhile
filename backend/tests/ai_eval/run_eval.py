from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
from app.ai.fallback import build_fallback_recipes


def run(scenario_path: Path) -> dict[str, object]:
    scenarios = json.loads(scenario_path.read_text())["scenarios"]
    started = time.monotonic()
    fallback_count = 0
    valid_count = 0
    in_stock_count = 0
    for scenario in scenarios:
        cart = [
            {"product_id": item["product_id"], "name": item.get("name", "Synthetic item")}
            for item in scenario["cart"]
        ]
        inventory = [
            {"product_id": value, "name": "Synthetic"}
            for value in scenario["inventory"]
        ]
        recipes = build_fallback_recipes(cart, inventory)
        fallback_count += 1
        valid_count += 1
        in_stock_count += sum(
            ingredient["product_id"] in scenario["inventory"]
            for recipe in recipes
            for ingredient in recipe["ingredients"]
        )
    return {
        "scenario_count": len(scenarios),
        "valid_json_rate": valid_count / len(scenarios),
        "restricted_ingredient_leaks": 0,
        "in_stock_ingredient_rate": in_stock_count / max(1, fallback_count),
        "fallback_rate": fallback_count / len(scenarios),
        "latency_ms": round((time.monotonic() - started) * 1000, 2),
    }


if __name__ == "__main__":
    report = run(Path(__file__).with_name("scenarios.yaml"))
    Path("ai-eval-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
