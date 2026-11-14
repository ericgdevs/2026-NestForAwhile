from fastapi.testclient import TestClient

from app.auth import Role
from app.db import get_db
from app.main import app


def test_recommendations_scale_to_household_and_exclude_restricted(database, logged_in_client):
    app.dependency_overrides[get_db] = lambda: database
    try:
        response = TestClient(app).get(
            "/recommendations",
            cookies=logged_in_client(Role.CLIENT).cookies,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    items = response.json()
    assert items
    assert all(item["status"] != "Restricted" for item in items)
    assert all(item["quantity"] == 2 for item in items)
    assert all(item["rationale"] for item in items)


def test_portions_count_children_as_half():
    from app.services.recommendations import household_portions

    adult, child = {"age": 40}, {"age": 7}
    assert household_portions([adult, child], 2) == 2  # 1.5 rounds up
    assert household_portions([adult, adult, child, child], 4) == 3
    assert household_portions([{"age": None}], 1) == 1
    assert household_portions([], 3) == 3


def test_saved_recipe_items_come_first_with_a_reason(database, logged_in_client):
    from app.models import Product, SavedRecipe

    login = logged_in_client(Role.CLIENT)
    beans = database.query(Product).filter_by(sku="SYN-BEANS-001").one()
    database.add(
        SavedRecipe(
            client_id=login.user.id,
            title="Bean tacos",
            recipe={
                "title": "Bean tacos",
                "ingredients": [{"name": "beans", "product_id": beans.id}],
                "steps": ["Cook."],
            },
        )
    )
    database.commit()
    app.dependency_overrides[get_db] = lambda: database
    try:
        picks = TestClient(app).get("/recommendations", cookies=login.cookies).json()
    finally:
        app.dependency_overrides.clear()
    assert picks[0]["product_id"] == beans.id
    assert "recipe you saved" in picks[0]["rationale"]
