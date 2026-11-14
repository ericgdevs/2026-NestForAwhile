# How we used AI across the whole lifecycle

| Stage | Tool / model | What it did | What we changed by hand | Who |
|---|---|---|---|---|
| Planning | Gemini (notebook) | | | Eric |
| Spec | Spec Kit in Copilot | | | Eric |
| Build | Copilot agent | | | |
| Review | Ponytail review / Copilot code review | | | |
| Testing & debugging | Copilot | | | |
| In the product | Local open-source model (Ollama) | | | |
| Plan | Copilot (GPT-5.6 Terra) | Updated finalized AI deployment architecture: local Ollama, Groq free-tier open-weight inference in Azure, and deterministic rules-only fallback | Eric supplied and approved the architecture decision | Eric |
| Tasks | Copilot (Sonnet 5.5) | Generated tasks.md (99 one-PR tasks by stream, shared-file ownership, Playwright per story, CI, deploy, OFF/USDA, Groq/Ollama, AI eval, US-1.3) | Eric supplied architecture, stream split, and task rules; review pending | Eric |
| Plan | Copilot (Sonnet 5.5) | Replaced stale HPC step in quickstart.md with Groq deployment config | None | Eric |
| Plan | Copilot (GPT-5.6 Terra) | Removed stale HPC deployment task path after final architecture verification | None | Eric |
| Plan | Copilot (Sonnet 5.5) | Drafted plan, research, data model, OpenAPI + AI schemas, quickstart from spec, Eric's addendums, and unf-hpc-guide.md (Ollama on HPC, no Groq) | Eric supplied architecture decisions and the HPC guide; reviewed plan | Eric |
| Spec (specify) | Copilot (Sonnet 5.5) | Drafted spec.md (14 stories, 24 FRs, 11 success criteria) and quality checklist from Eric's stories | Eric supplied all stories; reviewed and approved the plan | Eric |
| Spec (constitution) | Copilot (Sonnet 5.5) | Drafted constitution v1.0.0 from Eric's principles; filled plan-template Constitution Check | Eric supplied all principles and rules; reviewed draft | Eric |
| Install | Copilot | Installed Agentation as a development dependency | Caden approved the dependency installation | Caden |
| Install | Copilot | Installed Ponytail as a development dependency | Caden approved the dependency installation | Caden |
| Install | Copilot | Installed Impeccable globally for design skills and added the project hook | Caden selected global scope | Caden |
| Review fix | Copilot | Documented the required Impeccable global setup instead of committing a platform-specific engine | Kept the portable global hook | Caden |
| Implement T001 | Copilot (GPT-5.6 Terra) | Created the backend, frontend, e2e, deploy, and scripts skeleton directories and verified required ignore patterns | None | Caden |
| Implement T004 | Copilot (GPT-5.6 Terra) | Added the documented environment-variable template with placeholders only | None | Caden |
| Implement T005 | Copilot (GPT-5.6 Terra) | Added pull-request backend CI for Ruff and pytest | None | Caden |
| Implement T006 | Copilot (GPT-5.6 Terra) | Added pull-request frontend lint, typecheck, Vitest, and build checks | None | Caden |
| Implement T007 | Copilot (GPT-5.6 Terra) | Added hygiene CI that rejects tracked .env files and the prohibited compliance claim | None | Caden |
| Implement T021 | Copilot (GPT-5.6 Terra) | Added the versioned clinical rules matrix with synthetic nutrient thresholds and dietary/allergen exclusions | None | Caden |
| Implement T022 | Copilot (GPT-5.6 Terra) | Implemented deterministic dietary tier mapping and product classification with table-driven tests | None | Caden |
| Implement T002 | Copilot (GPT-5.6 Terra) | Initialized the FastAPI backend, approved dependency manifest, health endpoint, Ruff configuration, and pytest configuration | None | Caden |
| Implement T003 | Copilot (GPT-5.6 Terra) | Initialized the React/Vite/TypeScript frontend with Tailwind, shadcn configuration, Vitest, and a shell test | None | Caden |
| Implement T008 | Copilot (GPT-5.6 Terra) | Added Playwright local/deployed projects and role-based synthetic credential login fixture | None | Caden |
| Implement T010 | Copilot (GPT-5.6 Terra) | Added CODEOWNERS using the supplied team handles and a pull request template with task, stream, review, and validation fields | None | Caden |
| Implement T011 | Copilot (GPT-5.6 Terra) | Added environment-backed settings, SQLAlchemy engine/session setup, and SQLite connectivity tests | None | Caden |
| Implement T012 | Copilot (GPT-5.6 Terra) | Added Fernet encryption helpers, encrypted SQLAlchemy text storage, and ciphertext-at-rest tests | None | Caden |
| Implement T013 | Copilot (GPT-5.6 Terra) | Added SQLAlchemy identity, client, encrypted dietary profile, and visit models with focused metadata tests | None | Caden |
| Implement T014 | Copilot (GPT-5.6 Terra) | Added catalog, inventory lot, movement, and audit event models with required inventory metadata tests | None | Caden |
| Implement T015 | Copilot (GPT-5.6 Terra) | Added shopping session, capacity, queue, cart, recommendation, checkout, and intervention models with metadata tests | None | Caden |
| Implement T016 | Copilot (GPT-5.6 Terra) | Added donor, grant, report, and anonymized AI request models with privacy-focused metadata tests | None | Caden |
| Implement T017 | Copilot (GPT-5.6 Terra) | Added Alembic configuration, initial schema migration, and SQLite upgrade validation | None | Caden |
| Implement T018 | Copilot (GPT-5.6 Terra) | Added Argon2 password verification, JWT cookie helpers, role dependencies, and auth failure tests | None | Caden |
| Implement T019 | Copilot (GPT-5.6 Terra) | Added synthetic role, client enrollment, household-size, and dietary-profile seed data with isolated tests | None | Caden |
| Implement T020 | Copilot (GPT-5.6 Terra) | Added synthetic catalog, nutrition/allergen flags, inventory lots with mixed expiries, donors, grants, and seed coverage | None | Caden |
| Risk fix | Copilot (GPT-5.6 Terra) | Upgraded Vitest to the patched 4.1.12 release, resolving the reported Vitest, @vitest/mocker, and tinypool advisories without changing the approved frontend stack | None | Caden |
| Risk fix | Copilot (GPT-5.6 Terra) | Removed tracked TypeScript/Vite build outputs, added precise ignore rules, and changed the frontend build to typecheck without emitting artifacts | None | Caden |
| Implement T023 | Copilot (GPT-5.6 Terra) | Added isolated SQLite, seeded-data, role login, and mocked AI fixtures with a fixture smoke test | None | Caden |
| Implement T024 | Copilot (GPT-5.6 Terra) | Generated OpenAPI TypeScript types and added a cookie-including typed API client with a fetch test | None | Caden |
| Implement T025 | Copilot (GPT-5.6 Terra) | Added the mobile-first app shell, auth context, protected route guard, and signed-out behavior test | None | Caden |
| Implement T026 | Copilot (GPT-5.6 Terra) | Added accessible Green/Yellow/Red safety badges with icons, text, and focused rendering coverage | None | Caden |
| Implement T027 | Copilot (GPT-5.6 Terra) | Added a multi-stage frontend/backend Docker build and conditional FastAPI static asset mounting | None | Caden |
| Implement T029 | Copilot (GPT-5.6 Terra) | Added the production container startup script and Azure App Service image deployment workflow | None | Caden |
| Implement T031 | Copilot (GPT-5.6 Terra) | Added login, logout, current-profile, capacity, and shopping-session service routes with focused authentication tests | None | Caden |
| Implement T032 | Copilot (GPT-5.6 Terra) | Added the client login form, navigation, and friendly invalid/inactive-account messages with component tests | None | Caden |
| Implement T033 | Copilot (GPT-5.6 Terra) | Added the US1 Playwright coverage and staff-facing active shopper count in the app shell | None | Caden |
| Implement T034 | Copilot (GPT-5.6 Terra) | Added encrypted dietary profile updates, deterministic tier recomputation, validation, and route tests | None | Caden |
| Implement T035 | Copilot (GPT-5.6 Terra) | Added the editable nine-choice dietary profile page with save feedback and focused UI coverage | None | Caden |
| Implement T036 | Copilot (GPT-5.6 Terra) | Added Playwright coverage for selecting, saving, and reloading dietary choices | None | Caden |
| Implement T037 | Copilot (GPT-5.6 Terra) | Added deterministic inventory-aware recommendations with safety filtering, rationale, and household-scaled quantities | None | Caden |
| Implement T038 | Copilot (GPT-5.6 Terra) | Added the personalized recommendation page with deterministic rationale, quantities, and accessible safety badges | None | Caden |
| Implement T039 | Copilot (GPT-5.6 Terra) | Added Playwright coverage for safe recommendations, rationale visibility, and household quantities | None | Caden |
| Implement T040 | Copilot (GPT-5.6 Terra) | Added local barcode/SKU nutrition lookup with deterministic safety classification and friendly missing-product errors | None | Caden |
| Implement T041 | Copilot (GPT-5.6 Terra) | Added a short-timeout, fixture-testable Open Food Facts barcode mapper with resilient failure handling | None | Caden |
| Implement T042 | Copilot (GPT-5.6 Terra) | Added cached USDA FoodData Central enrichment and local → Open Food Facts → USDA scan fallback ordering with mocked tests | None | Caden |
| Implement T043 | Copilot (GPT-5.6 Terra) | Added an iOS-friendly ZXing camera scanner with rear-camera constraints, cleanup, and manual-entry fallback messaging | None | Caden |
| Implement T044 | Copilot (GPT-5.6 Terra) | Added the scan page with camera/manual lookup, nutrition facts, image support, explanation, and safety status | None | Caden |
| Implement T045 | Copilot (GPT-5.6 Terra) | Added Playwright coverage for manual scan success/failure and camera scanner availability | None | Caden |
| Implement T046 | Copilot (GPT-5.6 Terra) | Added active-session cart persistence APIs, manifest generation, and focused route coverage | None | Caden |
| Implement T047 | Copilot (GPT-5.6 Terra) | Added the live cart page with quantity controls, removal, and recommendation markers | None | Caden |
| Implement T048 | Copilot (GPT-5.6 Terra) | Added Playwright coverage for cart add, quantity changes, removal, and reload persistence | None | Caden |
| Implement T049 | Copilot (GPT-5.6 Terra) | Added the AI provider protocol and Ollama/Groq factory with explicit unsupported-provider validation | None | Caden |
| Implement T050-T051 | Copilot (GPT-5.6 Terra) | Added httpx-based Ollama and Groq structured JSON provider clients with timeout and configuration handling | None | Caden |
| Implement T052 | Copilot (GPT-5.6 Terra) | Added strict Pydantic recipe output models and product-ID validation against the AI contract | None | Caden |
| Implement T053 | Copilot (GPT-5.6 Terra) | Added inventory location lookup and recipe guardrails for stock availability and restricted ingredients | None | Caden |
| Implement T054-T055 | Copilot (GPT-5.6 Terra) | Added recipe prompt construction and deterministic in-stock fallback recipe generation | None | Caden |
| Implement T056 | Copilot (GPT-5.6 Terra) | Added recipe generation route with provider validation, clinical guardrails, deterministic fallback, and AI request telemetry | None | Caden |
| Implement T061 | Copilot (GPT-5.6 Terra) | Added the recipes page with ingredient/step display and a friendly fallback notice | None | Caden |
| Implement T062 | Copilot (GPT-5.6 Terra) | Added Playwright coverage for recipe visibility and fallback messaging | None | Caden |
| Implement T009 | Copilot (GPT-5.6 Terra) | Added pull-request E2E CI that seeds SQLite, builds the frontend, installs Chromium, and runs Playwright | None | Caden |
| Implement T057-T058 | Copilot (GPT-5.6 Terra) | Added synthetic AI evaluation scenarios and a dependency-free JSON/YAML-compatible evaluation runner | None | Caden |
| Implement T059 | Copilot (GPT-5.6 Terra) | Added the local Ollama model setup script and provider status in the health response | None | Caden |
| Implement T067 | Copilot (GPT-5.6 Terra) | Added role-matrix coverage for capacity permissions and unauthenticated access | None | Caden |
| Implement T068 | Copilot (GPT-5.6 Terra) | Added centralized role-to-screen authorization and an unauthorized screen response | None | Caden |
| Implement T069 | Copilot (GPT-5.6 Terra) | Added Playwright coverage for direct URL denial across role boundaries | None | Caden |
| Implement T070 | Copilot (GPT-5.6 Terra) | Added deploy health smoke tooling and an optional post-deploy workflow check | None | Caden |
| Implement T097-T099 | Copilot (GPT-5.6 Terra) | Added security/privacy audit documentation, project README, and recorded local regression results | None | Caden |
| Implement T073-T074 | Copilot (GPT-5.6 Terra) | Added a local synthetic demo reset script and judging runbook | None | Caden |
| Implement T095 | Copilot (GPT-5.6 Terra) | Added a lightweight FastAPI-to-contract OpenAPI path drift check to backend CI | None | Caden |
| Implement T063-T064 | Copilot (GPT-5.6 Terra) | Added checkout validation, FIFO inventory decrement, receipt/visit recording, and session completion APIs | None | Caden |
| Implement T065 | Copilot (GPT-5.6 Terra) | Added volunteer checkout review, hard-stop error display, completion action, and receipt view | None | Caden |
| Implement T066 | Copilot (GPT-5.6 Terra) | Added Playwright coverage for volunteer checkout session review | None | Caden |
| Implement T075/T078/T081 | Copilot (GPT-5.6 Terra) | Added inventory audit, replenishment, and FIFO lot APIs with focused route tests | None | Caden |
| Implement T084/T085 | Copilot (GPT-5.6 Terra) | Added queue promotion, claim expiry, queue endpoints, and manager capacity updates with tests | None | Caden |
| Implement T088 | Copilot (GPT-5.6 Terra) | Added anonymized analytics aggregation and excluded expired lots from checkout with route coverage | None | Caden |
| Implement T091/T092 | Copilot (GPT-5.6 Terra) | Added donor/grant lot attribution, report aggregation, migration, and dependency-free DOCX generation with validation | None | Caden |
| Implement T095 | Copilot (GPT-5.6 Terra) | Completed the contract route coverage with checkout intervention handling and a focused test | None | Caden |
| Implement T076/T079/T082/T086/T089/T093 | Copilot (GPT-5.6 Terra) | Added warehouse inventory, queue, analytics, and report screens with role routing and focused frontend coverage | None | Caden |
| Implement T077/T080/T083/T087/T090/T094 | Copilot (GPT-5.6 Terra) | Added Playwright coverage for the inventory, queue, analytics, and reports screens with safe credential skips | None | Caden |
| Complete T091 seed linkage | Copilot (GPT-5.6 Terra) | Linked synthetic seeded lots to synthetic donor and grant records | None | Caden |
| Resolve PR conflicts | Copilot | Merged main into the implementation branch, kept the approved SQLAlchemy implementation, and removed incompatible main-only scaffold files | Caden approved the conflict-resolution merge | Caden |
| Integrate Agentation | Copilot | Added the Agentation development toolbar to the frontend for local visual feedback, guarded out of tests and production builds | Caden approved frontend integration | Caden |
