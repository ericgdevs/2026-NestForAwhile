import json
import logging
from collections.abc import Iterable
from dataclasses import dataclass

from app.ai.context_manifest import build_manifest, manifest_hash
from app.ai.provider import AIProvider, AITask, get_provider
from app.ai.validators import validate_ai_output

logger = logging.getLogger(__name__)


class AIOrchestrationError(RuntimeError):
    """A runtime AI failure (provider error, malformed or rule-violating output).

    Callers fall back to rules-only."""


@dataclass(frozen=True)
class AIResult:
    output: object  # validated schema for the task
    manifest_hash: str
    index_map: dict[int, int]  # manifest index -> real product_id; server-side only
    provider: str


def run_ai_task(
    task: AITask,
    products: Iterable,
    restrictions: list[str],
    cart_quantities: dict[int, int] | None = None,
    household_size: int | None = None,
    provider: AIProvider | None = None,
    focus_product_id: int | None = None,
    cuisine: str | None = None,
) -> AIResult:
    """manifest (statuses from classify()) -> provider -> validation.

    Never creates or changes a status."""
    task = AITask(task)
    provider = (
        provider or get_provider()
    )  # a bad AI_PROVIDER is a startup error, not an orchestration failure
    try:
        manifest, index_map = build_manifest(
            products, restrictions, cart_quantities, household_size, focus_product_id, cuisine
        )
        logger.debug("AI manifest size: %d bytes", len(json.dumps(manifest.model_dump())))
        raw = provider.generate_json(task, manifest)
        output = validate_ai_output(task.value, raw, manifest)
    except Exception as exc:
        raise AIOrchestrationError(f"{type(exc).__name__}: {exc}") from exc
    return AIResult(output, manifest_hash(manifest), index_map, provider.name)
