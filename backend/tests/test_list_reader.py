import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai import list_reader
from app.ai.provider import ProviderError
from app.auth import Role
from app.db import get_db
from app.main import app
from app.services.shopping_list import first_lots, match_line

VALID = json.dumps({"items": [{"name": "black beans", "quantity": 2}, {"name": "oats"}]})


@pytest.fixture
def ollama(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_VISION_MODEL", "test-vision")


def _model_says(monkeypatch, *replies):
    """Each call to the vision model returns the next reply (an Exception is raised instead)."""
    queue = list(replies)

    def fake_post(*_args, **_kwargs):
        reply = queue.pop(0)
        if isinstance(reply, Exception):
            raise reply
        response = httpx.Response(200, json={"response": reply}, request=httpx.Request("POST", "http://x"))
        return response

    monkeypatch.setattr(list_reader.httpx, "post", fake_post)
    return queue


def test_valid_json_becomes_items(ollama, monkeypatch):
    _model_says(monkeypatch, VALID)
    items = list_reader.read_list_photo("aGVsbG8=", "image/jpeg")
    assert [(i.name, i.quantity) for i in items] == [("black beans", 2), ("oats", 1)]


def test_invalid_json_is_retried_once(ollama, monkeypatch):
    queue = _model_says(monkeypatch, "not json", VALID)
    assert len(list_reader.read_list_photo("aGVsbG8=", "image/jpeg")) == 2
    assert queue == []


def test_wrong_shape_counts_as_invalid(ollama, monkeypatch):
    _model_says(monkeypatch, '{"items": [{"name": "", "quantity": 0}]}', VALID)
    assert len(list_reader.read_list_photo("aGVsbG8=", "image/jpeg")) == 2


def test_total_failure_raises_provider_error_after_two_tries(ollama, monkeypatch):
    queue = _model_says(monkeypatch, "nope", httpx.ConnectError("down"), VALID)
    with pytest.raises(ProviderError):
        list_reader.read_list_photo("aGVsbG8=", "image/jpeg")
    assert len(queue) == 1  # a third try was never made


def test_route_reports_total_failure_clearly_and_not_configured_separately(
    database, logged_in_client, monkeypatch
):
    cookies = logged_in_client(Role.CLIENT).cookies
    app.dependency_overrides[get_db] = lambda: database
    api = TestClient(app)
    try:
        monkeypatch.setenv("AI_PROVIDER", "ollama")
        monkeypatch.setenv("OLLAMA_VISION_MODEL", "test-vision")
        _model_says(monkeypatch, "nope", "nope")
        failed = api.post("/shopping-list/parse", json={"image_base64": "aGVsbG8="}, cookies=cookies)
        monkeypatch.delenv("OLLAMA_VISION_MODEL")
        unset = api.post("/shopping-list/parse", json={"image_base64": "aGVsbG8="}, cookies=cookies)
    finally:
        app.dependency_overrides.clear()
    assert failed.status_code == 502 and "clearer" in failed.json()["detail"]
    assert unset.status_code == 503 and "type your list" in unset.json()["detail"]


def test_photo_items_are_matched_and_restricted_ones_get_swaps(
    database, logged_in_client, ollama, monkeypatch
):
    _model_says(monkeypatch, json.dumps({"items": [{"name": "Blak Beans", "quantity": 3}]}))
    app.dependency_overrides[get_db] = lambda: database
    try:
        body = TestClient(app).post(
            "/shopping-list/parse",
            json={"image_base64": "aGVsbG8="},
            cookies=logged_in_client(Role.CLIENT).cookies,
        ).json()
    finally:
        app.dependency_overrides.clear()
    line = body["lines"][0]
    assert line["text"] == "Blak Beans ×3"
    assert "black beans" in line["name"].lower()  # several catalog items match
    assert line["status"] in {"Approved", "Capped", "Restricted"}
    assert "swaps" in line


def test_matching_is_case_insensitive_and_tolerates_typos(database):
    stocked = first_lots(database)
    assert "black beans" in match_line("BLACK BEANS", stocked).name.lower()
    assert "black beans" in match_line("blak bean", stocked).name.lower()
    assert match_line("unicorn glitter", stocked) is None
