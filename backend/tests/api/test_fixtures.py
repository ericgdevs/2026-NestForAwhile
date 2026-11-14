import pytest

from app.models import Role


@pytest.mark.parametrize("role", list(Role))
def test_login_as_each_seeded_role(login_as, role):
    response = login_as(role).get("/me")
    assert response.status_code == 200
    assert response.json()["user"]["role"] == role.value


def test_role_guard_with_seeded_users(login_as):
    assert login_as(Role.CLIENT).get("/capacity").status_code == 403
    assert login_as(Role.VOLUNTEER).get("/capacity").status_code == 501


def test_mock_ai_fixture_is_isolated(mock_ai):
    assert mock_ai.generate.call_count == 0
