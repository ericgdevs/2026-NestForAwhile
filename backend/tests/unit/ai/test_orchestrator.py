from types import SimpleNamespace

import pytest

from app.ai.orchestrator import AIOrchestrationError, run_ai_task
from app.ai.provider import AIProvider, AITask, GroqProvider, ProviderError
from app.ai.schemas import RecipeOutput
from app.rules.classify import classify


def product(pid, name, **kw):
    base = dict(id=pid, sku=f"SKU{pid}", barcode="0123456789012", category="Canned", image_url="https://img.test/a.png",
                sodium_mg=100.0, allergens=[], diet_flags=["vegan"], ingredients_text="x")
    return SimpleNamespace(**{**base, "name": name, **kw})


PRODUCTS = [product(501, "Beans"), product(502, "Almond milk", allergens=["tree nuts"], diet_flags=[])]
RESTRICTIONS = ["Nut Allergy"]


class FakeProvider(AIProvider):
    name = "fake"

    def __init__(self, response=None, error=None):
        self.response, self.error, self.seen = response, error, None

    def generate_json(self, task, manifest):
        self.seen = manifest
        if self.error:
            raise self.error
        return self.response


def recipe(index):
    return {"recipes": [{"title": "T", "ingredients": [{"name": "x", "product_id": index}], "steps": ["go"]}]}


def run(provider, task=AITask.RECIPES):
    return run_ai_task(task, PRODUCTS, RESTRICTIONS, {501: 1}, 3, provider)


def test_valid_response_returns_validated_schema():
    result = run(FakeProvider(recipe(0)))
    assert isinstance(result.output, RecipeOutput)
    assert result.index_map == {0: 501, 1: 502}
    assert result.provider == "fake" and len(result.manifest_hash) == 64


def test_provider_receives_rules_statuses_and_no_identifiers():
    provider = FakeProvider(recipe(0))
    run(provider)
    assert [i.status.lower() for i in provider.seen.items] == [classify(p, RESTRICTIONS).status.name.lower() for p in PRODUCTS]
    dumped = str(provider.seen.model_dump())
    assert "SKU501" not in dumped and "0123456789012" not in dumped and "img.test" not in dumped


@pytest.mark.parametrize("response", ["not json", None, [], {"recipes": []}, '{"recipes": ['])
def test_malformed_provider_response_raises_orchestration_error(response):
    with pytest.raises(AIOrchestrationError):
        run(FakeProvider(response))


def test_restricted_item_suggestion_rejected():
    with pytest.raises(AIOrchestrationError, match="restricted"):
        run(FakeProvider(recipe(1)))


def test_unknown_index_rejected():
    with pytest.raises(AIOrchestrationError, match="unknown index"):
        run(FakeProvider(recipe(9)))


def test_status_override_rejected():
    data = recipe(0)
    data["recipes"][0]["ingredients"][0]["status"] = "Approved"
    with pytest.raises(AIOrchestrationError, match="status"):
        run(FakeProvider(data))


@pytest.mark.parametrize("error", [ProviderError("rate limited"), TimeoutError(), ConnectionRefusedError()])
def test_provider_exception_is_wrapped(error):
    with pytest.raises(AIOrchestrationError) as info:
        run(FakeProvider(error=error))
    assert info.value.__cause__ is error


def test_unimplemented_stub_surfaces_as_orchestration_error():
    with pytest.raises(AIOrchestrationError):
        run(GroqProvider())


@pytest.mark.parametrize("value", [None, "openai"])
def test_bad_ai_provider_stays_a_startup_error(monkeypatch, value):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    if value:
        monkeypatch.setenv("AI_PROVIDER", value)
    with pytest.raises(ValueError) as info:
        run_ai_task(AITask.EXPLAIN, PRODUCTS, RESTRICTIONS)
    assert not isinstance(info.value, AIOrchestrationError)


def test_provider_selected_from_env_when_not_injected(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    with pytest.raises(AIOrchestrationError) as info:
        run_ai_task(AITask.EXPLAIN, PRODUCTS, RESTRICTIONS)
    assert isinstance(info.value.__cause__, ProviderError)
    assert "OLLAMA_HOST and OLLAMA_MODEL must be configured" in str(info.value.__cause__)


def test_unsupported_task_is_a_programming_error():
    with pytest.raises(ValueError):
        run_ai_task("chat", PRODUCTS, RESTRICTIONS, provider=FakeProvider({}))
