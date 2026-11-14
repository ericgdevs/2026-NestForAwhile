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
