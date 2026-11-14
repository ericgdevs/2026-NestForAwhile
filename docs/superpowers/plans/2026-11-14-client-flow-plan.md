# Implementation plan: client shopping flow

Design: `docs/superpowers/specs/2026-11-14-client-flow-design.md` (approved by Caden, 2026-11-14). Section numbers like "§4.3" point there.
Status: proposed; waiting for Caden to say go.

## How every step runs

1. **Branches.** Backend steps (B*) go on `api/client-flow`, branched from `api/cart-nutrition` (that branch's cart nutrition change is needed here). Frontend steps (F*) go on `001-mtg-warehouse-system`. Caden commits by hand; each step ends with a suggested commit message.
2. **Ponytail** to write the code: reuse first, smallest complete change. Run **Ponytail review** before calling the step done.
3. **Impeccable** for any screen work: extend the existing world (`DESIGN.md`, `.impeccable/surfaces/frontend-src.md`). No new direction roll. Run `impeccable detect` on every UI step, and the finish review at the end of each frontend phase.
4. **Agentation:** after each frontend step, Caden reviews in the dev app and pastes Page Feedback, which is applied in the same step.
5. **Tests ship with the step.** pytest for backend, Vitest for frontend, and a Playwright spec per journey step in `e2e/tests/` (Eric reviews). Run them before reporting done.
6. **Logging.** Each step adds one row to `docs/ai-usage.md` (tool: Copilot (Sonnet 5.5)). Each backend step adds a row to `docs/proposals/backend-changes-log.md` for Aditya or Eric. Caden's decisions go in `docs/decisions.md`.
7. **Contract.** Any API change updates `openapi.yaml` in the same step, then `npm run gen:api` and `scripts/check_openapi.py`. Organizer names stay exactly as they are.

## Phase 1: Household and rules (backend)

**B1. Household members** (reviewer: Aditya)
- `models.py`: new `HouseholdMember` (client_id, position, nickname, age, restrictions, allergies, dietary classes; restrictions/allergies/classes encrypted like `DietaryProfile`). Nickname defaults to "Person N".
- Migration `0003_household_members.py`: create the table and copy each existing `DietaryProfile` into a "Person 1" member (§5 #14). `Household_Size` stays as stored, but equals the member count for new clients.
- `seed/load.py`: give the synthetic active client two members (adult + child with "Nut Allergy") so the demo shows a Yellow allergy case.
- Tests: migration up/down, encryption at rest, Person 1 copy.
- Done when: migrations and seed run on SQLite and existing tests pass.

**B2. Household label rule** (reviewers: Aditya rules, Eric matrix)
- `rules/classify.py`: add `household_label(product, members)` returning status, explanation, a `not_for` list (nickname + reason), and `allergy_match` (bool). It reuses `classify` per member. Rules: none restricted → Green; some → Yellow; all → Red; any Capped → at least Yellow; missing nutrition → Capped (§4.3, §5 #1).
- `clinical_rules_matrix.json`: add the condition → dietary class map for the fixed list (§5 #4), marked as placeholders (§5 #15).
- `Dietary_Tier_ID` for the household = strictest member tier (§5 #13).
- Tests in `tests/unit/test_rules.py`: 0/2, 1/2, 2/2, 1/1, capped-only, allergy flag, missing data.

**B3. Use the household label everywhere** (reviewer: Aditya)
- `services/nutrition.py` (`safety_label`, `scan_local`, `local_label`), `services/recommendations.py`, `services/recipe_guard.py` (per member, stricter: §5 #8), `services/checkout.py` (`validate_checkout`).
- Scan and cart responses gain `not_for` and `allergy_match`. `openapi.yaml` updated.
- Tests: scan, cart, recommendation, and recipe-guard route tests with a two-member household.

## Phase 2: Sign-up and approval

**B4. Self sign-up; Pending clients can shop** (reviewer: Aditya)
- `routes/auth.py`: `POST /auth/signup` (email, password, real name, members with nickname/age/restrictions/allergies, optional conditions per member). Creates a `Pending` client and starts a session through the existing login path.
- Conditions are only turned into dietary classes in the request; they are never stored or logged. A test checks they appear in no table or log line.
- `/auth/login`: allow `Pending` (shop, can't check out); keep rejecting `Inactive`.
- `spec.md` FR-004 and US-1 scenario 3 amended (§5 #17).
- Tests: signup happy path, duplicate email, Pending login, Inactive still rejected, no conditions stored.

**B5. Manager approvals** (reviewer: Aditya)
- `GET /clients/pending` (Warehouse Manager) returns client ID, real name, sign-up time. `POST /clients/{id}/approve` sets Active and logs who approved.
- Real name is returned only here (§4.2).
- Tests: role matrix (only the Manager can call these), approve flips status, name absent from other endpoints.

**F1. Sign-up flow** (reuses `Login.tsx` form styles, `.choices`/`.choice` from Profile)
- New `pages/Signup.tsx`, reached from the existing **Create Account** button. Steps: account (email, password, real name) → household (add members: nickname, age) → restrictions and allergies (whole household or per person, reusing Profile's nine choices) → optional conditions (fixed list, "skip" clearly offered) → done, with a "Waiting for staff approval before checkout" notice.
- Vitest: step navigation, validation, payload shape (no conditions sent beyond the request).

**F2. Profile edits per person** (extends `Profile.tsx`)
- Profile lists members; each can be renamed and have choices changed. "Add person" and "Remove person" are allowed.
- Vitest: rename, add, save payload.

**F3. Manager approvals screen** (new `pages/Approvals.tsx`; `lib/roles.ts` + nav)
- Table of pending clients (ID, real name, signed up) with Approve. Overview shows a "N waiting for approval" row for managers.
- Vitest + role nav test update.

## Phase 3: Scanning, labels, swaps, recipes

**B6. Swaps** (reviewer: Aditya)
- `services/swaps.py`: same category, in stock, household Green (or Yellow if no Green), at most 2, with aisle/shelf/bin (§5 #7). Included in the scan response when the label is Red.
- Tests: picks Green over Yellow, skips out-of-stock, empty when none.

**B7. Per-product recipes with cuisines** (reviewer: Eric)
- `ai/schemas.py` + `ai-schemas.json`: optional `cuisine`; raise `maxItems` (about 6). `ai/recipes.py`: prompt with the scanned product, household combined restrictions, stock, and an optional cuisine filter.
- `routes/recipes.py`: accept `scanned_product_id` (exists) and `cuisine`; return ingredient `in_cart_or_stock` and `location` (already in the contract, never filled).
- Fallback recipes get a cuisine too, so the cuisine filter works with AI off.
- Tests: schema accepts cuisine; guard still removes restricted recipes; fallback has cuisines; `tests/ai_eval/scenarios.yaml` gets a two-member case.

**B8. Saved recipes** (reviewer: Aditya)
- `SavedRecipe` model + migration; `GET/POST/DELETE /me/recipes`. Stores the recipe JSON as shown.
- Tests: save, list, delete, other clients can't see it.

**F4. "Not for" line everywhere** (extends `StatusBadge`)
- Small component under the status bar: "Not for Little one: nut allergy", with an allergy icon when `allergy_match`. Used in Scan, Cart, Home, and Shopping list.
- Vitest.

**F5. Scan result** (extends `Scan.tsx`; reuses `NutritionFacts`, `RecipeGroups`)
- Order per §4.5: label → not-for line → facts → Add to cart → swaps (Red only, each with Add to cart and location) → recipes with cuisine filter buttons; each recipe gets **Save** and **Add to cart** (to Shopping list).
- Red Add to cart asks once: "This isn't recommended for anyone in your household. Add anyway?" (§5 #2).
- `RecipeGroups` gains the two buttons through props; its cuisine toggles already exist.
- Vitest: swaps shown only on Red, confirm on Red add, Save calls API, Add sends to list.

**F6. Saved recipes** (reuses `pages/Recipes.tsx`)
- Recipes tab becomes **Saved recipes**: list from `/me/recipes`, open and delete. The cart-based recipe view moves into Scan and Home.

## Phase 4: Shopping list and Home

**B9. Shopping list** (reviewers: Aditya, Eric for parsing)
- `ShoppingListItem` model + migration (client, product or free text, source: "you" or recipe ID, ticked).
- `GET/POST/PATCH/DELETE /shopping-list`; ticking a matched item also adds it to the cart (§4.6).
- `POST /shopping-list/parse` takes text or an image. The AI reads the lines (a vision model for images, §5 #9), then products are matched and labelled by rules. The image isn't stored; a test checks this.
- Tests: CRUD, tick adds to cart, parse with the AI provider mocked, unknown items marked "not carried".

**B10. Smarter recommendations** (reviewer: Aditya)
- `services/recommendations.py`: add products from this household's completed checkouts and saved-recipe ingredients; size by members (adults 1, under 12 is ½, §5 #6); drop household Red. The rationale says why ("You took this last visit").
- Tests: history boosts, child half portion, Red excluded.

**F7. Shopping list tab** (new `pages/ShoppingList.tsx`; nav)
- Add by typing, pasting, or photo (camera/upload input). Lines sorted by aisle, each with location, label, source tag ("You added" or "For: recipe" with an Open button), and a tick box.
- Tab bar becomes: Home, Scan, List, Cart, Recipes; Profile moves to the top bar. This is my call; Caden can change it in Agentation review.
- Vitest: sort by aisle, tick calls API, recipe button opens it.

**F8. Home** (extends `Home.tsx`; reuses `BarcodeScanner`)
- Recommendations (now with "why" from B10) followed by the scanner inline. The bottom `RecipeSheet` is removed from Home, since recipes now live on Scan (and the component is deleted if nothing else uses it).

## Phase 5: Checkout

**B11. Volunteer checkout** (reviewer: Aditya)
- `GET /checkout/lookup?token=` or `?client_id=` loads the session's cart with household labels.
- `POST /checkout/{token}/items` (volunteer add by SKU/barcode) and `DELETE /checkout/{token}/items/{product_id}`, both logged as interventions (§5 #12).
- `validate` returns `blocking` (Red items; Pending account) and `needs_ack` (allergy matches). `POST /checkout/{token}/acknowledge` records allergy acknowledgements. `complete` refuses until nothing is blocking and every allergy is acknowledged. The atomic decrement stays as it is.
- `spec.md` FR-017 / US-7 amended.
- Tests: each stop, ack logged, complete still atomic, volunteer add/remove logged.

**B12. Client checkout QR** (reviewer: Aditya)
- `GET /me/session` returns the active `Shopping_Session_Token` and client ID for the QR (§5 #11). `/me` gains the client ID; still no name.

**F9. Cart QR** (extends `Cart.tsx`)
- "Show at checkout" opens a full-screen QR of the session token plus the client ID in large type. Needs a QR-drawing package (e.g. `qrcode`, about 30 kB), which is a new dependency and needs Caden's OK at that step.

**F10. Volunteer checkout** (extends `Checkout.tsx`; reuses `BarcodeScanner`, which already reads QR codes)
- Scan the client QR or type the client ID → cart list with labels → per line: confirm tick, remove → "Scan a missed item" → stops panel (Red: remove or manager override; Pending: waiting for approval; allergy: acknowledge with client) → Complete → receipt.
- Vitest: each stop disables Complete; ack flow; add and remove.

## Phase 6: Whole-journey checks

**T1. Playwright journey specs** (Eric reviews; `e2e/tests/`)
- `client-signup.spec.ts`: sign up → pending → shop.
- `client-scan.spec.ts`: scan → household label → not-for line → swap on Red → recipe Save / Add to list.
- `client-list.spec.ts`: list → tick → cart.
- `checkout-volunteer.spec.ts`: QR or ID lookup → allergy ack → Red stop → complete → inventory down.
- `manager-approval.spec.ts`: approve → checkout allowed.
- Same sign-in approach as `ui-redesign.spec.ts` (page context login).

**T2. Final passes**
- Impeccable finish review on Signup, Scan, Shopping list, Checkout, Approvals at 390px and 1440px; fix, then refresh `DESIGN.md` if the system grew.
- Ponytail review of the whole branch diff.
- Full pytest, Vitest, build, and the Playwright run; record in `docs/regression-results.md` (Eric's file, via PR).

## Order and dependencies

```
B1 → B2 → B3 ─┬─ B4 → B5 ─┬─ F1, F2, F3
              ├─ B6, B7, B8 ── F4 → F5, F6
              ├─ B9, B10 ──── F7, F8
              └─ B11, B12 ─── F9, F10
                                  └─ T1 → T2
```
Frontend steps can start against mocked responses as soon as their backend contract (the `openapi.yaml` change) exists.

## Open items to settle at the step, not now

- F9: the QR package choice (needs Caden's approval).
- F7: the tab bar order is my call; Agentation review decides.
- B9: which vision model Groq/Ollama provides for list photos (Eric).
