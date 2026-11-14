import pytest

from app.auth import COOKIE_NAME, create_access_token
from app.models import Role, User


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize("method,path", [("get", "/me"), ("get", "/capacity"), ("get", "/inventory/lots")])
def test_protected_routes_require_login(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_inventory_skeleton_is_staff_only(session, client):
    user = User(email="v@example.test", email_hash="hv", password_hash="x", role=Role.VOLUNTEER)
    session.add(user)
    session.commit()
    client.cookies.set(COOKIE_NAME, create_access_token(user.id, Role.VOLUNTEER))
    assert client.get("/inventory/lots").status_code == 403
