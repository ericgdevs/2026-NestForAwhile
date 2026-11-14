import json
from functools import lru_cache
from pathlib import Path

MATRIX_PATH = Path(__file__).with_name("clinical_rules_matrix.json")


@lru_cache
def load_matrix() -> dict:
    matrix = json.loads(MATRIX_PATH.read_text())
    unknown = {r for rs in matrix["conditions"].values() for r in rs} - set(matrix["restrictions"])
    if unknown:
        raise ValueError(f"Conditions reference unknown restrictions: {sorted(unknown)}")
    return matrix


def restrictions_for_conditions(conditions: list[str]) -> list[str]:
    """Overlapping conditions combine; duplicates collapse, order is stable."""
    mapping = load_matrix()["conditions"]
    return list(dict.fromkeys(r for c in conditions for r in mapping[c]))
