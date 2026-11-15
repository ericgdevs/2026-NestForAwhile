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
