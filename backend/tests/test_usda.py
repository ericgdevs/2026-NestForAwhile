import httpx

from app.services import usda


def test_usda_lookup_maps_nutrients_and_caches(monkeypatch):
    monkeypatch.setenv("USDA_API_KEY", "synthetic-key")
    usda._CACHE.clear()
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "foods": [
                    {
                        "description": "Synthetic USDA Food",
                        "foodNutrients": [
                            {"nutrientId": 1093, "value": 21},
                            {"nutrientId": 269, "value": 4},
                            {"nutrientId": 1258, "value": 1},
                            {"nutrientId": 1092, "value": 90},
                            {"nutrientId": 1004, "value": 7},
                            {"nutrientId": 1253, "value": 12},
                            {"nutrientId": 1003, "value": 3},
                        ],
                    }
                ]
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first = usda.lookup_usda("123", client)
        second = usda.lookup_usda("123", client)

    assert first == second
    assert first["sodium_mg"] == 21
    assert first["potassium_mg"] == 90
    assert first["total_fat_g"] == 7 and first["cholesterol_mg"] == 12 and first["protein_g"] == 3
    assert first["iron_mg"] is None  # USDA sent no iron: left empty
    assert calls == 1
