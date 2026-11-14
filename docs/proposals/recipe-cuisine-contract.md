# Proposal: cuisine-grouped recipes, cart nutrition, and client IDs (contract change)

Status: proposed by Caden (UI) for Aditya (API owner) and Eric (AI owner). Nothing in `openapi.yaml`, `ai-schemas.json`, or the backend has been changed.

## Why

The client home now has a recipe sheet that groups ideas by cuisine with a top pick per cuisine. Recipes must still respect the client's dietary rules and current inventory (FR-014, FR-015). The UI also shows clients by ID and household, never by name.

The frontend already reads the fields below as optional. Until they ship, it shows a single "Suggested for you" group.

## Proposed changes

1. `POST /recipes` request body: add optional `cuisine` (string). It filters or prioritizes that cuisine; when omitted, the API returns a mix.
2. `Recipe` response schema (`openapi.yaml`) and `recipe_output` (`ai-schemas.json`): add optional `cuisine` (string, short, e.g. "Mexican"). Recipes stay ordered best-first, so the first per cuisine is shown as the top pick.
3. `recipe_output.maxItems`: raise from 3 to about 6, so two or three cuisines can each show more than one idea. The rules guard (`services/recipe_guard.py`) still validates every recipe.
4. Fill in the existing contract fields `in_cart_or_stock` and `location { aisle, shelf, bin }` on each ingredient. The backend currently returns only `name` and `product_id`, so the UI can't show where missing ingredients are (US6 scenario 2).
5. `GET /me`: add a non-identifying client ID (e.g. `client_id`). The UI can then show "Client #123" instead of nothing. `name` is already never displayed.

6. **Cart items carry nutrition and safety status (Aditya).** *Implemented on branch `api/cart-nutrition` for review; see `docs/proposals/backend-changes-log.md` there.* `GET /cart`, `POST /cart/items` and `DELETE /cart/items/{id}` all return `{"items": build_manifest(...)}` (`backend/app/routes/cart.py`). Add these fields to each item: `sku`, `status` (Approved/Capped/Restricted from the rules engine), `explanation`, `sodium_mg`, `sugar_g`, `sat_fat_g`, `potassium_mg`.
   - These are the same keys `scan_local` (`backend/app/services/nutrition.py`) already returns, so the simplest version calls `scan_local(database, product.sku, client)` per item and merges the result. Carts are small, so one lookup per item is fine.
   - Add the fields in the cart routes, not inside `build_manifest`. `routes/recipes.py` also sends `build_manifest` to the AI as the `Active_Cart_Manifest`, and nutrition there would bloat the prompt.
   - Update the `CartItem` schema in `openapi.yaml` (it already has `status`), and add one test in `backend/tests/test_cart_routes.py` checking that a cart item returns `sodium_mg` and `status`.

## Frontend status

- `frontend/src/api/client.ts` `Recipe` type: `cuisine?`, `in_cart_or_stock?`, `location?`.
- `frontend/src/components/RecipeGroups.tsx`: groups by `cuisine`, with tabs only when more than one cuisine is present.
- `frontend/src/api/client.ts` `CartItem` type: the item 6 fields, all optional.
- `frontend/src/pages/Cart.tsx`: each card shows the status bar, SKU and nutrition facts once item 6 ships, and "Nutrition facts not available yet" until then.
- After the contract change, run `npm run gen:api`; no other UI change is needed for items 2, 4 and 6.

## Also found (for Aditya): screen URLs break in production

`backend/app/main.py` serves `frontend/dist` with `StaticFiles(html=True)`, which has no fallback to `index.html`. On the deployed site:

- Opening or refreshing a screen URL such as `/scan`, `/lots`, `/audit`, `/profile` or `/waiting` returns **404**. Confirmed locally against the backend with a built `dist`.
- `/cart`, `/checkout`, `/recipes`, `/analytics` and `/reports` share their path with API routes, so a page load returns API JSON (or 401/405) instead of the app.
- Every nav link is a full page load, so this affects normal navigation too, not only refresh.

The Vite dev proxy (`frontend/vite.config.ts`) had the same collision for those five shared paths. The frontend fixed that for local dev: page loads now get the app.

Suggested fix (backend owner's call):

1. Serve `index.html` for any GET that accepts `text/html` and doesn't match a file, after the API routers.
2. Or move the API under a prefix like `/api`. This is a bigger contract change.
