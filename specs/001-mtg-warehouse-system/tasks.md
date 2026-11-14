# Tasks: NestForAwhile 2026 – MTG Warehouse System

**Input**: `specs/001-mtg-warehouse-system/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)
**Architecture**: React + Vite + TypeScript + Tailwind + shadcn/ui · FastAPI + Pydantic · PostgreSQL (Azure) / SQLite (local) · AI: Ollama locally (`AI_PROVIDER=ollama`), Groq free-tier open-weight model on Azure (`AI_PROVIDER=groq`) · Deterministic rules-only fallback always available. No HPC, Slurm, or Azure-to-HPC tasks.

## Format and rules

`- [ ] T### [P?] [US#] [stream] Description with file path`

- **[P]**: can run in parallel with other [P] tasks in the same phase (different files, no unfinished dependency).
- **Story label**: `[US1]`–`[US14]` match the numbered user stories in `spec.md`. `[US-1.3]` is Capacity Enforcement, which comes from the plan addendum and is traced to `plan.md`, `research.md` R7 and `data-model.md` (it is not in `spec.md`). Setup, Foundational and Polish tasks have no story label.
- **Streams**: `[ui]` = Caden · `[api]` = Aditya (API and data) · `[ai]` `[qa]` `[deploy]` `[docs]` = Eric (AI, QA, deployment, documentation, integration).
- **One task = one PR** into `main` (merge commit only, never squash, reviewed before merge). Branch: `<stream>/T###-short-name`. Commit: `<type>(<stream>): <what> [<tool>, <stage>]`. Each PR appends one row to `docs/ai-usage.md`. Do not touch `docs/decisions.md`.
- **Tests ship in the same PR as the feature** (pytest or Vitest for the code you write). `[qa]` tasks cover Playwright, CI, the AI evaluation harness and cross-cutting checks.
- **Dependencies**: every new package needs team approval before the first install. Tasks that introduce one say so.
- **Excluded, no tasks**: facial recognition, warehouse computer vision, shelf cameras, cart-tracking cameras, multi-language, biometrics, and NICE stories (listed at the end).

## Shared-file ownership

A shared file has one owner. Everyone else changes it only through a small PR that the owner reviews (enforced by CODEOWNERS, T010).

| File / area | Owner | Rule for others |
|---|---|---|
| `specs/001-mtg-warehouse-system/contracts/openapi.yaml` | Aditya (api) | Contract change only when Eric/team asks; Caden and Eric review. Never hand-edit generated types. |
| `backend/app/models.py`, `backend/alembic/versions/*`, `backend/seed/*` | Aditya | Eric and Caden request columns via an issue/PR comment; Aditya adds them. |
| `backend/app/schemas.py`, `backend/app/main.py`, `backend/app/routes/__init__.py` (router registry) | Aditya | Eric adds one `include_router` line (T056) and one static-mount line (T027) in small PRs Aditya approves. |
| `backend/app/config.py` | Aditya | Eric adds the AI variables (`AI_PROVIDER`, `OLLAMA_*`, `GROQ_*`) in T049. |
| `backend/app/rules/classify.py`, `tiers.py` | Aditya | Any change needs a matching test in `backend/tests/unit/test_rules.py`. |
| `backend/app/rules/clinical_rules_matrix.json` | Eric (content from Epic Cure) | Aditya reads it only. |
| `backend/app/ai/*`, `backend/tests/ai_eval/*` | Eric | Aditya consumes `ai/` only through `POST /recipes`. |
| `backend/tests/conftest.py`, `e2e/**`, `.github/workflows/*` | Eric | Others add their own test files, not shared fixtures. |
| `frontend/src/App.tsx` (router), `frontend/src/components/**`, `frontend/src/pages/**` | Caden | Eric/Aditya send UI needs as issues. |
| `frontend/src/api/generated/*` | Generated (Caden runs `npm run gen:api`) | Never edit by hand. |
| `frontend/src/components/BarcodeScanner.tsx` | Caden | Shared by US4 and US8 screens. |
| `.env.example`, `Dockerfile`, `deploy/**`, `docs/ai-usage.md`, `README.md` | Eric | Others append their own variable or row in their PR; Eric reviews. |
| `package.json` / `requirements.txt` | Owner of that side (Caden / Aditya) | Eric reviews dependency approval. |

---

## Phase 1: Setup

- [X] T001 [deploy] Create repo skeleton `backend/`, `frontend/`, `e2e/`, `deploy/`, `scripts/` (with `.gitkeep`) and confirm `.gitignore` ignores `.env`, `*.db`, `node_modules/`, `__pycache__/`
- [X] T002 [api] Init backend: `backend/requirements.txt`, `backend/app/main.py` with `GET /health` (status + `ai_provider`), ruff config, pytest config (dependency approval: FastAPI, Pydantic, SQLAlchemy, Alembic, httpx, pytest, ruff)
- [X] T003 [P] [ui] Init frontend: Vite + React + TypeScript in `frontend/`, Tailwind CSS, shadcn/ui (`frontend/components.json`), Vitest (dependency approval)
- [X] T004 [P] [docs] Create `.env.example` with `DATABASE_URL`, `JWT_SECRET`, `FIELD_ENCRYPTION_KEY`, `AI_PROVIDER`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `GROQ_API_KEY`, `GROQ_MODEL`, `USDA_API_KEY`, `ALLOWED_ORIGINS`, `COOKIE_SECURE`, `SEED_DEMO_DATA` (placeholders only)
- [X] T005 [P] [qa] CI backend workflow `.github/workflows/backend.yml`: ruff + pytest on every PR
- [X] T006 [P] [qa] CI frontend workflow `.github/workflows/frontend.yml`: lint + typecheck + Vitest + build on every PR
- [X] T007 [P] [qa] CI hygiene workflow `.github/workflows/hygiene.yml` + `scripts/check_hygiene.sh`: fail if `.env` is tracked, if the phrase "HIPAA compliant" appears anywhere
- [X] T008 [qa] Playwright scaffold: `e2e/package.json`, `e2e/playwright.config.ts` (`BASE_URL` env, local + deployed projects), `e2e/fixtures/auth.ts` (login helper per role) (dependency approval)
- [ ] T009 [qa] CI e2e workflow `.github/workflows/e2e.yml`: start backend (SQLite + seed) and frontend build, run Playwright on every PR
- [X] T010 [docs] Add `.github/CODEOWNERS` matching the ownership table above and `.github/pull_request_template.md` (task ID, stream, merge-commit-only reminder, ai-usage row checkbox, tests run). Needs the team's GitHub handles from Eric.

**Checkpoint**: three CI workflows run on an empty repo; owners are enforced.

## Phase 2: Foundational (blocks all stories)

- [X] T011 [api] `backend/app/config.py` (settings from env/`.env`) and `backend/app/db.py` (SQLAlchemy engine/session; SQLite or PostgreSQL from `DATABASE_URL`), with a unit test
- [X] T012 [api] `backend/app/crypto.py`: Fernet field encryption + an `EncryptedText` column type; test that stored values are not plaintext
- [X] T013 [api] Models for identity and profile in `backend/app/models.py`: `users`, `clients` (`Client_Enrollment_Status`, `Household_Size`, `Dietary_Tier_ID`), `dietary_profiles` (encrypted), `visits`
- [X] T014 [api] Models for catalog and inventory in `backend/app/models.py`: `products`, `inventory_lots` (expiry, threshold, aisle/shelf/bin), `inventory_movements`, `audit_events`
- [X] T015 [api] Models for sessions and transactions in `backend/app/models.py`: `shopping_sessions` (`Shopping_Session_Token`), `capacity_settings` (`Max_Floor_Capacity`), `queue_entries`, `carts`, `cart_items`, `recommendations`, `checkouts`, `checkout_items`, `interventions`
- [X] T016 [api] Models for reporting and AI in `backend/app/models.py`: `donors`, `grants`, `reports`, `ai_requests`
- [X] T017 [api] Alembic init and migration `0001` for all tables in `backend/alembic/`; test `upgrade head` on SQLite
- [X] T018 [api] `backend/app/auth.py`: Argon2 hashing, JWT in HttpOnly cookie (`COOKIE_SECURE` from config), `get_current_user`, `Role` enum, `require_roles(...)`; tests for wrong password, expired token, wrong role (403)
- [X] T019 [api] Seed users in `backend/seed/load.py`: one synthetic user per role plus synthetic clients (Active and non-Active, various `Household_Size`) and dietary profiles (emails use `@example.test`)
- [X] T020 [api] Seed catalog in `backend/seed/load.py`: synthetic products (barcodes, nutrition, images, allergens), lots across aisles/shelves/bins with mixed expiry dates and thresholds, synthetic donors/grants
- [X] T021 [docs] `backend/app/rules/clinical_rules_matrix.json`: thresholds and exclusions for Low Sugar, Low Sodium, Heart Healthy, Kidney Friendly, Vegetarian, Vegan, Gluten Free, Nut Allergy, Dairy Free; mark values as synthetic placeholders until Epic Cure guidance is confirmed
- [X] T022 [api] `backend/app/rules/tiers.py` (`Dietary_Tier_ID` mapping) and `classify.py` (`classify(product, profile)` → Approved/Capped/Restricted + plain-language reason; allergen/exclusion → Restricted; missing data → Capped); table-driven tests in `backend/tests/unit/test_rules.py`
- [X] T023 [qa] `backend/tests/conftest.py`: temp SQLite per test, seeded data, logged-in client per role, mocked AI provider fixture
- [X] T024 [P] [ui] OpenAPI types: `npm run gen:api` script (openapi-typescript from `contracts/openapi.yaml`) and typed fetch wrapper `frontend/src/api/client.ts` (cookies included) (dependency approval)
- [X] T025 [ui] App shell: `frontend/src/App.tsx` router, mobile-first layout, auth context, protected-route guard in `frontend/src/lib/auth.tsx`
- [X] T026 [P] [ui] `frontend/src/components/StatusBadge.tsx`: Green/Yellow/Red with icon and text (never color alone), friendly wording
- [X] T027 [deploy] Multi-stage `Dockerfile` (build frontend, serve with FastAPI) and the static-files mount line in `backend/app/main.py` (coordinate with Aditya)
- [ ] T028 [deploy] `deploy/azure-setup.md` and provision Azure resource group, App Service, and PostgreSQL Flexible Server (commands recorded, no secrets)
- [X] T029 [deploy] `.github/workflows/deploy.yml` (build and deploy to App Service on merge to `main`) and `deploy/startup.sh` (`alembic upgrade head`, seed when `SEED_DEMO_DATA=true`)
- [ ] T030 [deploy] Set Azure app settings from `.env.example` (including `AI_PROVIDER=groq`; values stay in Azure) and verify the public URL serves `/health`

**Checkpoint**: an empty but real app is live on Azure, CI is green, every PR now deploys.

## Phase 3: User Story 1 – Client Check-In and Shopping Session (P1) 🎯

**Goal**: an Active client logs in, a session and `Shopping_Session_Token` are created, and staff can see the active shopper count.
**Independent test**: log in as seeded Active client; token returned; count increments; non-Active gets a friendly 403.

- [X] T031 [api] [US1] `backend/app/services/sessions.py` and `backend/app/routes/auth.py`: `POST /auth/login` (check `Client_Enrollment_Status`, create `Shopping_Session_Token`), `POST /auth/logout`, `GET /me`; plus `GET /capacity` returning the active shopper count (`routes/capacity.py`, Volunteer/Staff/Manager); tests for valid, invalid (401), non-Active (403), count
- [X] T032 [ui] [US1] `frontend/src/pages/Login.tsx`: login form, friendly messages for invalid credentials and non-Active enrollment
- [X] T033 [qa] [US1] Playwright `e2e/tests/us1-checkin.spec.ts`: valid login, invalid login, non-Active client, active count visible to a volunteer

## Phase 4: User Story 2 – Dietary Profile in Plain Language (P1)

- [X] T034 [api] [US2] `backend/app/routes/profile.py`: `PUT /me/profile` saves encrypted restrictions/allergies/preferences and recomputes `Dietary_Tier_ID` via rules; tests for persistence, encryption at rest, invalid option rejected
- [X] T035 [ui] [US2] `frontend/src/pages/Profile.tsx`: "Dietary Restrictions & Preferences" with the nine plain-language choices, editable any time
- [X] T036 [qa] [US2] Playwright `e2e/tests/us2-profile.spec.ts`: select, save, sign out/in, selections persist

## Phase 5: User Story 3 – Recommendations and Matching (P1)

- [X] T037 [api] [US3] `backend/app/services/recommendations.py` and `routes/recommendations.py`: `GET /recommendations`; in-stock, non-expired, never Restricted, quantity scaled by `Household_Size`, deterministic rationale; generated when the session starts; tests for each rule
- [X] T038 [ui] [US3] `frontend/src/pages/Home.tsx`: personalized recommendation view with rationale and `StatusBadge`
- [X] T039 [qa] [US3] Playwright `e2e/tests/us3-recommendations.spec.ts`: quantities differ by household size, no Restricted item, rationale visible

## Phase 6: User Story 4 – Barcode Safety Scan (P1)

- [X] T040 [api] [US4] `backend/app/services/nutrition.py` (local lookup) and `routes/products.py`: `GET /products/scan/{code}` returns nutrition, image, status, explanation; unknown code gives a friendly 404; tests for Green, Yellow, Red, missing nutrition → Capped
- [X] T041 [api] [US4] `backend/app/services/off.py`: Open Food Facts lookup by barcode with short timeout, mapping into `products`, cache; tests use saved fixtures (`backend/tests/fixtures/off_*.json`), never live network
- [X] T042 [api] [US4] `backend/app/services/usda.py`: USDA FoodData Central enrichment for missing nutrients (`USDA_API_KEY`), cache, and the lookup order local → Open Food Facts → USDA in `nutrition.py`; fixture-based tests, scan stays under 3 s when cached
- [X] T043 [ui] [US4] `frontend/src/components/BarcodeScanner.tsx`: smartphone camera scanning that works on iOS Safari (library choice needs approval, research R6)
- [X] T044 [ui] [US4] `frontend/src/pages/Scan.tsx`: scanner plus always-visible manual SKU field and product result card (nutrition facts, image when available, status, explanation)
- [X] T045 [qa] [US4] Playwright `e2e/tests/us4-scan.spec.ts`: manual SKU for Green, Yellow, Red, unknown SKU; camera permission smoke test using Chromium fake media device

## Phase 7: User Story 5 – Digital Cart (P1)

- [X] T046 [api] [US5] `backend/app/services/cart.py` and `routes/cart.py`: `GET /cart`, `POST /cart/items`, `PATCH` and `DELETE /cart/items/{product_id}`, `build_manifest()` for `Active_Cart_Manifest`; the server marks items that were recommended; tests include persistence within the session
- [X] T047 [ui] [US5] `frontend/src/pages/Cart.tsx` live cart (add, remove, change quantity) plus add-to-cart buttons on `Home.tsx` and `Scan.tsx`
- [X] T048 [qa] [US5] Playwright `e2e/tests/us5-cart.spec.ts`: add, change quantity, remove, reload keeps the cart

## Phase 8: User Story 6 – Inventory-Aware Recipes (P1)

**Goal**: provider-selected AI proposes recipes; structured-output validation and the rules engine gate every result; the rules-only fallback guarantees an answer.

- [X] T049 [ai] [US6] `backend/app/ai/provider.py`: provider interface and factory driven by `AI_PROVIDER` (`ollama` or `groq`; anything else is a startup error), plus the AI variables in `config.py` (coordinate with Aditya)
- [X] T050 [ai] [US6] `backend/app/ai/ollama_provider.py`: local Ollama client with JSON-schema output and 30 s timeout; httpx-mocked tests for success, timeout, connection refused
- [X] T051 [ai] [US6] `backend/app/ai/groq_provider.py`: Groq free-tier chat-completions client (`GROQ_API_KEY`, `GROQ_MODEL`), JSON output, 30 s timeout, retry/backoff on 429; httpx-mocked tests for success, rate limit, 5xx, missing key
- [X] T052 [ai] [US6] `backend/app/ai/schemas.py`: Pydantic models mirroring `contracts/ai-schemas.json` and `validate_recipe_output()`; tests for malformed JSON, extra fields, empty list, unknown `product_id`
- [X] T053 [api] [US6] `backend/app/services/inventory_locations.py` and `services/recipe_guard.py`: look up aisle/shelf/bin for missing ingredients; drop recipes with a Restricted ingredient or a missing ingredient that has no stock and no location; tests
- [X] T054 [ai] [US6] `backend/app/ai/recipes.py`: prompt builder from `Active_Cart_Manifest`, scanned item, in-stock inventory, and the client's restrictions in plain list form
- [X] T055 [ai] [US6] `backend/app/ai/fallback.py`: deterministic rules-only recipes built from in-cart and in-stock items, filtered by the same rules; tests
- [X] T056 [ai] [US6] `backend/app/routes/recipes.py`: `POST /recipes` runs provider → structure validation → rules guard → display, falls back on any failure, logs `ai_requests` (no client identity), caches by manifest hash; one `include_router` line in `main.py` (coordinate with Aditya); route tests with the mocked provider (leak, provider down, invalid JSON, missing-ingredient location)
- [ ] T057 [qa] [US6] AI evaluation scenarios `backend/tests/ai_eval/scenarios.yaml`: profiles, carts, inventories, and edge cases (nut allergy, vegan, kidney friendly, empty cart, out-of-stock-only cart, prompt-injection text in a product name)
- [ ] T058 [qa] [US6] AI evaluation runner `backend/tests/ai_eval/run_eval.py`: reports valid-JSON rate, restricted-ingredient leaks (must be 0 after rules), in-stock ingredient rate, fallback rate, and latency for a chosen provider; writes a report file
- [ ] T059 [ai] [US6] Ollama local-development setup: `scripts/dev/ollama_setup.sh` (pull the chosen model), README snippet, and `/health` reporting provider availability
- [ ] T060 [ai] [US6] Run the evaluation on Ollama candidates and on the Groq open-weight model, record the choice in `docs/ai-eval-results.md`, and set the default model names in `.env.example`
- [X] T061 [ui] [US6] `frontend/src/pages/Recipes.tsx`: recipes with in-cart/in-stock ingredients, missing ingredients with aisle/shelf/bin, friendly notice when the fallback was used
- [X] T062 [qa] [US6] Playwright `e2e/tests/us6-recipes.spec.ts`: recipes appear, missing-ingredient locations shown, no Restricted ingredient, fallback path with the AI provider unreachable

## Phase 9: User Story 7 – Clinical Checkout Guardrail (P1)

- [X] T063 [api] [US7] `backend/app/services/checkout.py` and `routes/checkout.py`: `POST /checkout/{session_token}/validate` (Volunteer/Manager) re-classifies every cart line; any Restricted line, unknown product, or stock shortfall returns a hard stop; tests
- [X] T064 [api] Atomic completion in `services/checkout.py`: one transaction decrements lots in FIFO order, writes movements, receipt (`checkouts`, `checkout_items`), visit with pounds, ends the session; `POST /checkout/{session_token}/interventions` records `removed_item`; tests for rollback on failure and two checkouts racing for the last unit
- [X] T065 [ui] [US7] `frontend/src/pages/Checkout.tsx` (volunteer): enter session token, review cart, hard-stop dialog with intervention action, receipt view
- [ ] T066 [qa] [US7] Playwright `e2e/tests/us7-checkout.spec.ts`: clean cart completes with a receipt and inventory drops; Restricted item hard-stops, then completes after intervention

## Phase 10: User Story 11 – Role-Based Access (P1)

- [ ] T067 [qa] [US11] `backend/tests/api/test_role_matrix.py`: every route × every role against the plan's permission matrix (allowed, 403, and 401 when logged out)
- [ ] T068 [ui] [US11] `frontend/src/lib/roles.ts` and nav: each role sees only its screens; unauthorized page
- [ ] T069 [qa] [US11] Playwright `e2e/tests/us11-roles.spec.ts`: each role sees only its menu, direct URL to another role's screen is denied, API call from the wrong role returns 403

## Phase 11: User Story 14 – Public Deployment (P1)

- [ ] T070 [deploy] [US14] `scripts/smoke_public.sh` (health, login, scan) and a post-deploy step in `deploy.yml`
- [ ] T071 [qa] [US14] Playwright `e2e/tests/mvp-success.spec.ts`: the full MVP Success Scenario (login → scan → status → cart → recipes → checkout → manager analytics → report), runnable locally and against `BASE_URL`
- [ ] T072 [deploy] [US14] Verify Groq on Azure: `AI_PROVIDER=groq` returns valid recipes; with the key removed or rate-limited the fallback still answers; record the result in `deploy/azure-setup.md`
- [ ] T073 [deploy] [US14] `deploy/reset_demo.sh`: reset synthetic demo data and accounts before judging
- [ ] T074 [docs] [US14] `docs/demo-runbook.md`: judging steps, demo accounts per role (synthetic), fallback plan if Groq is down

**Checkpoint (MVP-A)**: client journey, checkout, roles, and deployment work live on Azure.

## Phase 12: User Story 8 – Inventory Audit Scanner (P2)

- [ ] T075 [api] [US8] `backend/app/services/audit.py` and `routes/inventory.py`: `GET /inventory/audit/{code}` and `POST /inventory/audit`; variance = counted − expected, `audit_events` row, lot update, and movement in one transaction; negative counts rejected; tests
- [ ] T076 [ui] [US8] `frontend/src/pages/Audit.tsx`: Scan Item → Current Count → Actual Count → Variance → confirm (reuses `BarcodeScanner`)
- [ ] T077 [qa] [US8] Playwright `e2e/tests/us8-audit.spec.ts`: count differs, variance shown, inventory and audit log updated

## Phase 13: User Story 9 – Replenishment Workflow (P2)

- [ ] T078 [api] [US9] `backend/app/services/replenishment.py` and `GET /inventory/replenishment?sort=`: items below threshold with aisle/shelf/bin and priority; tests
- [ ] T079 [ui] [US9] `frontend/src/pages/Replenishment.tsx`: list with location and priority sort
- [ ] T080 [qa] [US9] Playwright `e2e/tests/us9-replenishment.spec.ts`: lowering stock adds the item; sort changes order

## Phase 14: User Story 10 – FIFO Management (P2)

- [ ] T081 [api] [US10] `GET /inventory/lots` in `routes/inventory.py`: lots in FIFO order with `expiring_soon` for 7 days or less; boundary tests (day 7 flagged, day 8 not, expired excluded from recommendations and checkout)
- [ ] T082 [ui] [US10] `frontend/src/pages/Lots.tsx` and a dashboard warning banner for expiring lots
- [ ] T083 [qa] [US10] Playwright `e2e/tests/us10-fifo.spec.ts`: order, flag, and visible warning

## Phase 15: User Story US-1.3 – Capacity Enforcement and Queue (P2, from plan addendum)

**Goal**: honor `Max_Floor_Capacity`; extra clients wait in a FIFO queue (`Queue_Waiting`) and are promoted as shoppers finish. See `research.md` R7.

- [ ] T084 [api] [US-1.3] `backend/app/services/queue.py`: compute `Active_Floor_Shoppers`, `Queue_Waiting`; login joins the queue when full (extends T031); promotion `waiting → ready` in one transaction when a session ends (checkout, logout, lazy expiry); `ready` claim window expires; tests for FIFO order, last-slot race, expiry
- [ ] T085 [api] [US-1.3] `GET`/`POST /queue/me` (confirm when ready) and `PUT /capacity` (Manager; raising it promotes waiting clients); extend `GET /capacity` with all three counts; tests
- [ ] T086 [ui] [US-1.3] `frontend/src/pages/Waiting.tsx` (position, polling, "come in" confirmation) and staff/manager capacity widgets
- [ ] T087 [qa] [US-1.3] Playwright `e2e/tests/us1-3-capacity.spec.ts`: capacity 1, second client queued, promoted after the first checks out, manager raises capacity

## Phase 16: User Story 12 – Analytics Dashboard (P2)

- [ ] T088 [api] [US12] `backend/app/services/analytics.py` and `GET /analytics`: families served, visits completed, pounds distributed, inventory usage, recommendation adoption rate, waste reduction; aggregates only; tests include a payload scan for names, emails, and IDs
- [ ] T089 [ui] [US12] `frontend/src/pages/Analytics.tsx` dashboard (Manager/Director)
- [ ] T090 [qa] [US12] Playwright `e2e/tests/us12-analytics.spec.ts`: completing a checkout updates the metrics; no client identifiers shown

## Phase 17: User Story 13 – Donor and Grant Reporting (P2)

- [ ] T091 [api] [US13] Link lots to donors/grants (`donor_id`, `grant_id` on `inventory_lots`, migration, seed) and `backend/app/services/reports.py` aggregations (donor metrics, grant attribution, distribution totals, visit metrics); needs a `data-model.md` update first (see Open questions)
- [ ] T092 [api] [US13] `backend/app/services/docx_report.py` and `POST /reports/{donor|grant}`: python-docx report with four sections from a built-in template; test opens the DOCX and checks the sections and the absence of client identifiers (dependency approval)
- [ ] T093 [ui] [US13] `frontend/src/pages/Reports.tsx`: choose type and period, download DOCX
- [ ] T094 [qa] [US13] Playwright `e2e/tests/us13-reports.spec.ts`: generate and download, file is a valid DOCX with all four sections

**Checkpoint (MVP-B, scenario complete)**: the full MVP Success Scenario passes live, including manager analytics and the report.

## Phase 18: Polish and Cross-Cutting

- [ ] T095 [qa] CI OpenAPI drift check `scripts/check_openapi.py`: FastAPI's generated schema must match `contracts/openapi.yaml`; add to `backend.yml`
- [ ] T096 [qa] Accessibility pass: axe checks in Playwright on login, scan, cart, checkout (status never color-only), fix findings as separate PRs (dependency approval)
- [ ] T097 [qa] Privacy and security audit: seed/test data synthetic only, no secrets in repo, analytics anonymized, Argon2 and encrypted fields verified, wording "designed with HIPAA safeguards" only
- [ ] T098 [docs] `README.md`: architecture, run instructions (Ollama locally, Groq on Azure), team streams, link to specs
- [ ] T099 [qa] Feature-freeze regression run: all pytest, Vitest, Playwright (local and deployed), AI evaluation report; record results

---

## Dependencies and order

- Setup → Foundational → stories. Foundational blocks every story. Finish `T027`–`T030` (walking-skeleton deploy) early so every merge goes live.
- US1 (T031) first. US2 → US3 (recommendations need a profile) → US4 → US5 → US6 (needs cart) → US7 (needs cart and inventory). US11 and US14 come after the routes exist. US8–US10, US-1.3, US12, US13 follow; US-1.3 extends T031 and hooks into T064; US12/US13 need checkouts from T064.
- Inside a story: api → ui → Playwright. UI can start from the OpenAPI contract with mocks, so Caden and Aditya can work in parallel.
- Within US6, T049 → T050/T051/T052 → T054–T056 → T057–T060.

## Parallel examples

- Setup: T003 (Caden) in parallel with T004–T007 (Eric).
- Foundational: T024 and T026 (Caden) while Aditya does T011–T018 and Eric does T021, T023.
- US4: T041 and T042 (Aditya) while T043 and T044 (Caden) build against the contract.
- US6: Eric's AI tasks T049–T052 while Aditya does T053.
- Phases 12–14 (US8, US9, US10) can run in parallel across streams.

## Implementation strategy

1. **MVP-A** (Phases 1–11): shopping journey, checkout, roles, live on Azure.
2. **MVP-B** (Phases 12–17): audit, replenishment, FIFO, capacity queue, analytics, reports — completes the success scenario end to end.
3. **Polish** (Phase 18), then feature freeze (Eric decides timing).
4. Merge a story only with its tests and its Playwright spec; the CI is the gate.

## Open questions (need a team decision before the task is picked up)

- **T075**: Audit takes one counted total per product while stock sits in several lots. Proposed: apply the variance to the oldest lot first when stock is short, and to the newest when it is over. Confirm.
- **T091**: Lots have no donor or grant link in `data-model.md`; attribution needs `donor_id` and `grant_id`. This is a data-model change to approve first.
- **T078**: Define replenishment priority. Proposed: lowest quantity-to-threshold ratio first.
- **T088**: Define the waste-reduction metric. Proposed: pounds distributed from lots that were within 7 days of expiry, plus the count of expiring-soon lots. Adoption rate = checked-out items that were recommended ÷ all checked-out items.
- **T046**: Restricted items may be added to the cart (the client keeps choice) and are stopped at checkout (US7). Confirm.
- **T084**: Session expiry is checked lazily on request (no background scheduler). Confirm the idle time limit.
- **T010**: GitHub handles for CODEOWNERS.

## Parked (NICE, not scheduled until every MUST task passes)

Recipe saving · Smart product substitutions · Expiring-item promotion · Enhanced analytics visualizations · Custom report templates (DOCX upload).
