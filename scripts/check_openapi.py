from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "backend"))
from app.main import app


def contract_paths(path: Path) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(r"^  (/[^:]+):\s*$", path.read_text(), re.MULTILINE)
    }


def main() -> None:
    generated = set(app.openapi()["paths"])
    declared = contract_paths(
        Path(__file__).parents[1] / "specs/001-mtg-warehouse-system/contracts/openapi.yaml"
    )
    missing = declared - generated
    if missing:
        raise SystemExit(f"OpenAPI paths missing from FastAPI: {sorted(missing)}")
    print(f"OpenAPI path check passed ({len(declared)} contract paths).")


if __name__ == "__main__":
    main()
