import httpx

from app.services.off import lookup_open_food_facts


def test_open_food_facts_maps_saved_response():
    response = httpx.Response(
        200,
        json={
            "status": 1,
            "product": {
                "product_name": "Synthetic OFF Product",
                "image_front_url": "https://example.test/image.png",
                "ingredients_text": "Synthetic ingredient",
                "allergens_tags": ["en:milk"],
                "nutriments": {"sodium_100g": 0.012, "sugars_100g": 3}  # grams per 100 g,
            },
        },
    )
    transport = httpx.MockTransport(lambda request: response)
    with httpx.Client(transport=transport) as client:
        result = lookup_open_food_facts("123", client)

    assert result["name"] == "Synthetic OFF Product"
    assert result["sodium_mg"] == 12
    assert result["source"] == "openfoodfacts"


def test_open_food_facts_maps_label_nutrients_per_serving():
    nutriments = {
        "fat_serving": 8, "trans-fat_serving": 0, "cholesterol_serving": 0.005,
        "fiber_serving": 4, "proteins_serving": 3, "added-sugars_serving": 10,
        "vitamin-d_serving": 0.000002, "calcium_serving": 0.26, "iron_serving": 0.008,
    }  # fmt: skip
    payload = {"status": 1, "product": {"serving_quantity": 55, "nutriments": nutriments}}
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    with httpx.Client(transport=transport) as client:
        result = lookup_open_food_facts("label-1", client)

    assert result["serving_size_g"] == 55
    assert result["total_fat_g"] == 8 and result["trans_fat_g"] == 0
    assert result["cholesterol_mg"] == 5 and result["vitamin_d_mcg"] == 2
    assert result["calcium_mg"] == 260 and result["iron_mg"] == 8
    assert result["fiber_g"] == 4 and result["protein_g"] == 3 and result["added_sugar_g"] == 10
    assert result["calories"] is None  # no value from the source stays empty
