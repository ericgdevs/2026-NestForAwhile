# How we used AI across the whole lifecycle

| Stage | Tool / model | What it did | What we changed by hand | Who |
|---|---|---|---|---|
| Planning | Gemini (notebook) | | | Eric |
| Spec | Spec Kit in Copilot | | | Eric |
| Build | Copilot agent | | | |
| Review | Ponytail review / Copilot code review | | | |
| Testing & debugging | Copilot | | | |
| In the product | Local open-source model (Ollama) | | | |
| Implement | Copilot (Sonnet 5.5) | T031: session service (Initialize Shopping Session), POST /auth/login, POST /auth/logout, GET /me per contract, flow tests | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T037: deterministic recommendation service (stock, expiry, rules, household scaling), generated at session start, GET /recommendations and tests | None | Eric |
| Implement | Copilot (Sonnet 5.5) | US1.3: FIFO queue service (join, promote, expire), session start/end/claim primitives, GET/POST /queue/me and tests | None | Eric |
| Implement | Copilot (Sonnet 5.5) | US1.3: capacity service (computed Active_Floor_Shoppers/Queue_Waiting), GET/PUT /capacity, cookie renamed to `session` per contract | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T023: shared conftest fixtures (seeded DB, login_as per role, mock_ai stub) and fixture tests | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T020: catalog seed framework (6 sample products, locations, lots, donors/grants) and loader tests | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T019: idempotent seed loader (tiers, one user per role, five synthetic personas) and tests | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T022: tiers.py (placeholder tiers, strictest wins) and classify.py with table-driven tests | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T021: clinical_rules_matrix.json (synthetic placeholders, condition mapping) + validating loader and tests | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T018: Argon2/JWT auth skeleton, Role guard, route skeletons (501) and tests | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T017: Alembic init + migration 0001 for all tables, upgrade-head test | Fixed generated migration import by hand | Eric |
| Implement | Copilot (Sonnet 5.5) | T013-T016: SQLModel tables (incl. DietaryTier, ClinicalRule, InventoryLocation, DonationSource, GrantFundingStream) with official field names, Pydantic schemas, model test | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T011/T012: config, db engine (SQLite/PostgreSQL), Fernet EncryptedText, deps, .env.example | None | Eric |
| Plan | Copilot (GPT-5.6 Terra) | Updated finalized AI deployment architecture: local Ollama, Groq free-tier open-weight inference in Azure, and deterministic rules-only fallback | Eric supplied and approved the architecture decision | Eric |
| Tasks | Copilot (Sonnet 5.5) | Generated tasks.md (99 one-PR tasks by stream, shared-file ownership, Playwright per story, CI, deploy, OFF/USDA, Groq/Ollama, AI eval, US-1.3) | Eric supplied architecture, stream split, and task rules; review pending | Eric |
| Plan | Copilot (Sonnet 5.5) | Replaced stale HPC step in quickstart.md with Groq deployment config | None | Eric |
| Plan | Copilot (GPT-5.6 Terra) | Removed stale HPC deployment task path after final architecture verification | None | Eric |
| Plan | Copilot (Sonnet 5.5) | Drafted plan, research, data model, OpenAPI + AI schemas, quickstart from spec, Eric's addendums, and unf-hpc-guide.md (Ollama on HPC, no Groq) | Eric supplied architecture decisions and the HPC guide; reviewed plan | Eric |
| Spec (specify) | Copilot (Sonnet 5.5) | Drafted spec.md (14 stories, 24 FRs, 11 success criteria) and quality checklist from Eric's stories | Eric supplied all stories; reviewed and approved the plan | Eric |
| Spec (constitution) | Copilot (Sonnet 5.5) | Drafted constitution v1.0.0 from Eric's principles; filled plan-template Constitution Check | Eric supplied all principles and rules; reviewed draft | Eric |
| Implement | Copilot (Sonnet 5.5) | Added DietaryProfileWrite schema (matrix-validated options) and Dietary_Tier_ID assignment service (strictest wins) | Eric approved plan and decisions | Eric |
| Implement | Copilot (Sonnet 5.5) | Added create/update client and profile save services with automatic tier recalculation; PUT /me/profile route | Eric approved plan and decisions | Eric |
| Implement | Copilot (Sonnet 5.5) | Added profile tests: persistence, encryption at rest, invalid option, strictest tier, recalculation, Household_Size | Eric approved plan and decisions | Eric |
| Implement | Copilot (Sonnet 5.5) | T081: FIFO service (received_at, expiry, id), 7-day expiring flag, GET /inventory/lots per contract, tests | Eric approved plan and decisions | Eric |
| Implement | Copilot (Sonnet 5.5) | T078: replenishment service (ratio priority, sort=location as aisle-sequenced route) and GET /inventory/replenishment, tests | Eric approved plan and decisions | Eric |
| Implement | Copilot (Sonnet 5.5) | T063: checkout validation service (re-classify lines; Restricted, unknown product, shortfall, expired stock block) and movement logger, tests | Eric approved plan and decisions | Eric |
| Implement | Copilot (Sonnet 5.5) | T064: atomic checkout (FIFO guarded decrement, movements, receipt, visit, session end), interventions, /checkout routes; renamed cookie param in auth.py to free the session_token path name; tests | Eric approved plan and decisions | Eric |
| Implement | Copilot (Sonnet 5.5) | T088: analytics service (contract metrics plus service-level category/tier/checkout-history breakdowns) and GET /analytics, identifier-scan tests | Eric approved plan and decisions (2a: breakdowns stay internal) | Eric |
| Implement | Copilot (Sonnet 5.5) | T091: donor_id/grant_id on inventory_lots (model, migration 0002, seed) and attribution/distribution/visit aggregations in reports.py, tests | Eric approved the data-model change (1a) | Eric |
| Implement | Copilot (Sonnet 5.5) | T092: deterministic four-section ReportData builder (service-level; no DOCX, no route, no python-docx), tests | Eric approved plan (3b: structured object, DOCX later) | Eric |
