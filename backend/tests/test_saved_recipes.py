from fastapi.testclient import TestClient

from app.auth import Role, create_access_token
from app.db import get_db
from app.main import app
from app.models import User

RECIPE = {
    "title": "Oat porridge",
    "cuisine": "American",
    "ingredients": [{"name": "Synthetic Rolled Oats", "product_id": 1}],
    "steps": ["Simmer oats."],
}


def test_save_list_and_delete_only_your_own_recipes(database, logged_in_client):
    mine = logged_in_client(Role.CLIENT).cookies
    other_user = database.query(User).filter(User.role == "Client").offset(2).first()
    theirs = {"session": create_access_token(other_user.id, Role.CLIENT)}
    app.dependency_overrides[get_db] = lambda: database
    try:
        api = TestClient(app)
        saved = api.post("/me/recipes", json=RECIPE, cookies=mine)
        recipe_id = saved.json()["id"]
        listed = api.get("/me/recipes", cookies=mine).json()
        their_list = api.get("/me/recipes", cookies=theirs).json()
        their_delete = api.delete(f"/me/recipes/{recipe_id}", cookies=theirs)
        my_delete = api.delete(f"/me/recipes/{recipe_id}", cookies=mine)
        after = api.get("/me/recipes", cookies=mine).json()
        staff = api.get("/me/recipes", cookies=logged_in_client(Role.VOLUNTEER).cookies)
    finally:
        app.dependency_overrides.clear()

    assert saved.status_code == 201 and listed == [{"id": recipe_id, **RECIPE}]
    assert their_list == [] and their_delete.status_code == 404
    assert my_delete.status_code == 204 and after == []
    assert staff.status_code == 403
