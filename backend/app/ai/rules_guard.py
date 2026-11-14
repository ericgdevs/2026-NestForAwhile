"""Final deterministic safety layer: re-checks validated AI output against current inventory and classify()."""
from collections.abc import Iterable
from dataclasses import dataclass

from app.ai.orchestrator import AIResult
from app.ai.schemas import ContextManifest, ExplanationOutput, MissingIngredientsOutput, RecipeOutput, SubstitutionsOutput
from app.rules.classify import classify


@dataclass(frozen=True)
class GuardedResult:
    output: object  # same schema type as the input; lists may be empty after filtering
    dropped: list[tuple[str, int]]  # (reason, manifest index)


class _Checker:
    def __init__(self, result: AIResult, manifest: ContextManifest, products: Iterable, restrictions: list[str], in_stock_ids: set[int]):
        self.index_map = result.index_map
        self.by_id = {p.id: p for p in products}
        self.in_stock_ids = in_stock_ids
        self.restrictions = restrictions
        self.seen_status = {item.index: item.status for item in manifest.items}
        self.dropped: list[tuple[str, int]] = []

    def reason(self, index: int) -> str | None:
        if index not in self.index_map:
            return "invalid_index"
        product = self.by_id.get(self.index_map[index])
        if product is None:
            return "stale_index"
        if product.id not in self.in_stock_ids:
            return "unavailable"
        status = classify(product, {"restrictions": self.restrictions})[0]
        if status == "Restricted":
            return "restricted"
        if status != self.seen_status.get(index):
            return "classification_mismatch"
        return None

    def ok(self, index: int) -> bool:
        reason = self.reason(index)
        if reason:
            self.dropped.append((reason, index))
        return reason is None


def apply_rules_guard(
    result: AIResult,
    manifest: ContextManifest,
    products: Iterable,
    restrictions: list[str],
    in_stock_ids: set[int],
) -> GuardedResult:
    """Drop every suggestion that fails a fresh check; never raises, never sets a status, makes no external calls."""
    check = _Checker(result, manifest, list(products), restrictions, in_stock_ids)
    output = result.output
    if isinstance(output, RecipeOutput):
        recipes = [
            r for r in output.recipes
            if all([check.ok(i.product_id) for i in r.ingredients if i.product_id is not None])
        ]
        output = output.model_copy(update={"recipes": recipes})
    elif isinstance(output, MissingIngredientsOutput):
        output = output.model_copy(update={"items": [i for i in output.items if check.ok(i.product_id)]})
    elif isinstance(output, SubstitutionsOutput):
        # the original may be Restricted or out of stock; that is why it is being substituted
        subs = [s for s in output.substitutions if check.ok(s.substitute_product_id)]
        output = output.model_copy(update={"substitutions": subs})
    elif not isinstance(output, ExplanationOutput):
        raise TypeError(f"unsupported output type {type(output).__name__}")
    return GuardedResult(output, check.dropped)
