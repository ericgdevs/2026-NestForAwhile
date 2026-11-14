# Backend changes made on Caden's branch (for Aditya and Eric to review)

Caden can't change the backend directly, so these were made on branch `api/cart-nutrition` and logged here. Each change is meant to be reviewed and merged by its owner.

| Date | Change | Files | Owner to review | Why |
|---|---|---|---|---|
| 2026-11-14 | Cart items now include `sku`, `status`, `explanation`, `sodium_mg`, `sugar_g`, `sat_fat_g`, `potassium_mg` on `GET /cart`, `POST /cart/items`, and `PATCH /cart/items/{id}` | `backend/app/routes/cart.py`, `backend/app/services/nutrition.py`, `backend/tests/test_cart_routes.py`, `contracts/openapi.yaml` (CartItem) | Aditya | The cart page shows each item's nutrition label and rules-engine status (Agentation feedback from Caden). |

## Notes for the reviewer

- `services/nutrition.py`: the rules call and the "missing nutrition is never Approved" rule moved into `safety_label()`, and the profile parsing into `profile_for()`. `scan_local` uses both, so Scan behavior is unchanged.
- The new `local_label()` reads only the stored product row. It never calls Open Food Facts or USDA, so a cart load can't stall on outside timeouts.
- The fields are added in the cart routes (`cart_response`), not in `build_manifest`, because `routes/recipes.py` sends `build_manifest` to the AI as the `Active_Cart_Manifest`.
- Checks run on the branch: `pytest -q backend` (58 passed), `ruff check backend` (clean), `scripts/check_openapi.py` (passed).
