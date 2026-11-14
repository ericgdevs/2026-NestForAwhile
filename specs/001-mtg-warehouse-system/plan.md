# Implementation Plan: NestForAwhile 2026 – MTG Warehouse System

**Branch**: `001-mtg-warehouse-system` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification plus the post-specification plan addendums (Ollama locally, Groq free-tier open-weight inference in Azure, US-1.3 Capacity Enforcement, lightweight client data model).

## Summary

A System of Record (React/Vite/TypeScript UI, FastAPI/Pydantic API, PostgreSQL in Azure, SQLite locally) runs
check-in, cart, checkout, inventory, audit, replenishment, FIFO, analytics, DOCX reports, and floor
capacity with a waiting queue. A System of Intelligence uses an open-weight model through Ollama in
development and Groq's free-tier endpoint in deployment to write
recipes, explanations, and substitutions. Safety is deterministic: a rules engine alone assigns
Approved / Capped / Restricted and re-validates every AI output before display. If the AI is
unreachable or returns invalid output, a deterministic rules-only fallback is shown.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5 / Node 20 (frontend)
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, argon2-cffi, cryptography (Fernet), PyJWT, httpx, python-docx; React 18, Vite, Tailwind CSS, shadcn/ui, a browser barcode scanner library (research R6), openapi-typescript. *All new dependencies need team approval before the first install (see Complexity Tracking).*
**Storage**: PostgreSQL (Azure Database for PostgreSQL Flexible Server) in deployment; SQLite for local development; same SQLAlchemy models and Alembic migrations for both
**Testing**: pytest (rules, API, atomic checkout, queue, AI validation, AI evaluation scenarios); Playwright for every MUST story; Vitest for UI units
**Target Platform**: Azure App Service (one container: API + built frontend); smartphone browsers for clients
**Project Type**: web application (frontend + backend)
**Performance Goals**: scan-to-status under 3 s (SC-002); login-to-recommendations under 1 min (SC-001); recipe response within 30 s or fallback shown
**Constraints**: rules-first safety; synthetic data only; designed with HIPAA safeguards; `AI_PROVIDER=ollama` locally and `AI_PROVIDER=groq` in Azure; provider credentials come only from environment configuration; the AI path may be down, so the deterministic rules-only fallback is required, not optional
**Scale/Scope**: one warehouse, demo scale (tens of concurrent users, hundreds of products), 5 roles, about 14 screens

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Pre-research | Post-design |
|---|---|---|
| MVP scope and approved stack | PASS: stack unchanged; post-MVP items excluded | PASS: no computer vision, face, multi-language, or biometrics in any design file |
| Official variable names unchanged | PASS | PASS: `Client_Enrollment_Status`, `Shopping_Session_Token`, `Household_Size`, `Dietary_Tier_ID`, `Active_Cart_Manifest`, `Active_Floor_Shoppers`, `Max_Floor_Capacity`, `Queue_Waiting` used verbatim |
| Rules decide safety; AI schema-validated with fallback | PASS | PASS: classification lives only in `rules/`; AI output goes schema check → rules validation → display |
| Real inventory; atomic checkout; audit trail | PASS | PASS: single-transaction checkout, `audit_events`, FIFO lots |
| No secrets; PHI encrypted; analytics anonymized | PASS | PASS: `.env`/`.env.example`, Fernet field encryption, aggregate-only analytics |
| Tests planned (Playwright per MUST story, AI evals) | PASS | PASS: see Testing above and `quickstart.md` |

## Architecture

```text
Phone/Desktop browser (React)
        │  OpenAPI-typed calls, JWT in HttpOnly cookie
        ▼
FastAPI (Azure App Service)
 ├─ auth + role checks (server-side)
 ├─ rules/    Clinical Rules Matrix, Dietary_Tier_ID mapping, classify(product, tier)
 ├─ services/ sessions + capacity queue, cart, checkout, inventory, audit, replenishment, FIFO, analytics, reports, recipes, nutrition
 ├─ ai/       provider client, prompts, Pydantic output schemas, rules-only fallback
 └─ db        PostgreSQL (Azure) | SQLite (local)
        │ AI_PROVIDER selects provider
        ▼
Ollama (development) | Groq free-tier endpoint (Azure deployment)
```

**System of Intelligence configuration**: local development sets `AI_PROVIDER=ollama` and
`OLLAMA_BASE_URL`; Azure deployment sets `AI_PROVIDER=groq`, `GROQ_API_KEY`, and the selected
open-weight model identifier. The backend selects the provider through one interface. Credentials never
go in the repository; local values are in `.env`, and Azure values are deployment secrets.

**Recipe flow**: build `Active_Cart_Manifest` + scanned item + in-stock inventory → selected AI provider with a JSON schema →
Pydantic validation → rules engine drops any recipe with a Restricted ingredient, or with a missing
ingredient that has no stock and no location → display. Any failure → deterministic fallback recipes filtered by the same rules.

**Capacity enforcement (US-1.3)**: queue behavior in `research.md` R7; entities in `data-model.md`.

## Roles and Permissions

| Capability | Client | Volunteer | Warehouse Staff | Warehouse Manager | Director |
|---|:-:|:-:|:-:|:-:|:-:|
| Own profile, session, cart, scan, recipes | ✔ | | | | |
| Look up an active session / validate checkout | | ✔ | | ✔ | |
| Resolve a hard stop (records intervention) | | ✔ | | ✔ | |
| Audit scan, replenishment list | | | ✔ | ✔ | |
| FIFO / expiration dashboard | | | ✔ | ✔ | |
| Queue and capacity view | | ✔ | ✔ | ✔ | |
| Change `Max_Floor_Capacity` | | | | ✔ | |
| Analytics dashboard | | | | ✔ | ✔ |
| Donor/grant reports + DOCX export | | | | ✔ | ✔ |
| User and role administration | | | | | ✔ |

Each API route declares its allowed roles through one `require_roles(...)` dependency. The UI only hides screens; the server decides.

## Project Structure

### Documentation (this feature)

```text
specs/001-mtg-warehouse-system/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── openapi.yaml
│   └── ai-schemas.json
├── checklists/requirements.md
└── tasks.md             # created later by /speckit.tasks
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py, config.py (reads .env), db.py, models.py, schemas.py
│   ├── auth.py            # Argon2, JWT, require_roles()
│   ├── crypto.py          # Fernet field encryption
│   ├── rules/             # clinical_rules_matrix.json, tiers.py, classify.py
│   ├── ai/                # ollama_client.py, recipes.py, schemas.py, fallback.py
│   ├── routes/            # one file per area
│   └── services/          # sessions, queue, cart, checkout, inventory, reports, nutrition
├── alembic/
├── seed/                  # synthetic data only
└── tests/                 # unit, api, ai_eval
frontend/
├── src/                   # pages, components, api/generated, lib
└── tests/
e2e/                       # Playwright, one spec per MUST story
deploy/                    # Dockerfile, Azure notes, hpc/ollama_serve.sbatch (no credentials)
.env.example
```

**Structure Decision**: web application (backend + frontend) plus `e2e/` and `deploy/`. One container serves the API and the built frontend to keep Azure simple.

## Complexity Tracking

| Item | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| New dependencies listed above | Required by the approved stack and security rules (Argon2, field encryption, DOCX) | Hand-rolling hashing or encryption is unsafe; none are installed until the team approves |
| Rules-only fallback recipe path | Constitution requires a deterministic fallback; the selected AI provider may be unavailable or return invalid output | Failing visibly would break the live demo |
