a# NestForAwhile MTG Warehouse

## 1. Project Overview

Epic Cure's Medically Tailored Groceries (MTG) warehouse hands out food to clients with health conditions such as diabetes, high blood pressure and kidney disease. Staff must make sure each item is safe for every person in a household. This app checks each product against the household's dietary needs, shows a clear status (Approved, Capped or Restricted), and runs the client queue and checkout. AI helps with recipes and photo shopping lists, but **safety is decided by a rules engine, never by the AI**.

**Live app:** https://nestforawhile-mtg.vercel.app

Key features:
- Barcode or SKU scan with a safety status per household member
- Household profiles with encrypted ICD-10 codes mapped to a dietary tier
- Cart with nutrition totals
- Recipe ideas from the cart, with a rules-only fallback if the AI fails
- Shopping list, including reading a photo of a handwritten list
- Safer swaps for items that are not Approved
- Volunteer checkout and queue, plus warehouse inventory and replenishment
- Director overview and analytics (anonymized)

Demo accounts (synthetic data only). Password for all: `demo-password`

| Role | Email |
|---|---|
| Client (Low Sodium, child with nut allergy) | client.active@example.test |
| Client (pending approval, 6 people) | client.pending@example.test |
| Client (inactive) | client.inactive@example.test |
| Client (diabetes + high blood pressure) | client.diabetes.htn@example.test |
| Client (kidney disease + high blood pressure) | client.ckd.htn@example.test |
| Client (diabetes + kidney disease) | client.diabetes.ckd@example.test |
| Volunteer | volunteer@example.test |
| Warehouse staff | warehouse.staff@example.test |
| Warehouse manager | warehouse.manager@example.test |
| Director | director@example.test |

## 2. Setup Instructions

Needs Python 3 and Node.js. Run from the repo root.

**Backend**
```sh
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env      # then fill in JWT_SECRET and FIELD_ENCRYPTION_KEY (a Fernet key)
cd backend
alembic upgrade head
python -m seed.load
uvicorn app.main:app --reload
```

**Frontend** (second terminal)
```sh
cd frontend
npm install
npm run dev
```

**Tests**
```sh
cd backend && pytest
cd frontend && npm test
```

Notes:
- Local AI defaults to Ollama. Production uses Groq (`AI_PROVIDER=groq`, `GROQ_API_KEY`). Keys stay in `.env` (gitignored), never in code.
- End-to-end Playwright tests are in `e2e/` (`npx playwright test`).
- Deploy: Vercel (frontend + FastAPI) with Supabase Postgres. Env vars are listed in `.env.example`; run the migration and seed once against the Supabase `DATABASE_URL`.

## 3. Tool Usage Summary

Full log: [docs/ai-usage.md](docs/ai-usage.md)

| Component                                      | AI tool(s)                                                                 | What for                                   |
| ---------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------ |
| Planning                                       | Gemini (notebook)                                                          | Planning the project                       |
| Spec (constitution, specify, plan, tasks)      | Spec Kit in Copilot (Sonnet 5.5, GPT-5.6 Terra)                            | Spec, plan and task list in `specs/`       |
| Backend (API, rules, seed, scan, deploy fixes) | Copilot (Sonnet 5.5, GPT-5.6 Terra)                                        | Writing routes, rules engine and seed data |
| Frontend                                       | Copilot (Sonnet 5.5, GPT-5.6 Terra) with Impeccable, Agentation, Ponytail  | UI build, design pass, feedback fixes      |
| Testing, CI, AI evaluation                     | Gemini, Copilot                                                            | Tests, CI, recipe model evaluation         |
| Deploy                                         | Gemini, Copilot (Sonnet 5.5)                                               | Vercel and Supabase setup                  |
| Review                                         | Ponytail review, Copilot code review                                       | Reviewing changes                          |
| In the app                                     | Groq `openai/gpt-oss-20b` (recipes), Groq `qwen/qwen3.8-27b` (photo lists) | Recipe ideas and reading list photos       |

In-app model: we ran 20 synthetic cases against `gpt-oss:20b` and `qwen3:8b`. Both had 0 unsafe items after the rules guard. `gpt-oss` was picked for better valid-JSON rate and speed. Production runs the same model on Groq. Details: [docs/ai-eval-results.md](docs/ai-eval-results.md).

## 4. Team Collaboration

- **Eric Good:** backend, AI, testing, deploy.
- **Caden Wondell:** frontend, slides.
- **How we worked:** one branch per task or stream, pull requests into `main`, one person merges, and decisions go in [docs/decisions.md](docs/decisions.md).
- **Approved team and tool changes:** TODO (not recorded in the repo).

## 5. Software Engineering Strategy

- **Design:** Spec Kit spec, plan and tasks in `specs/001-mtg-warehouse-system/`, with an API contract (OpenAPI).
- **Build:** AI agents write the code in small tasks and small pull requests; each step is logged.
- **Test:** automated tests (backend pytest, frontend Vitest, Playwright), live tests on phones, and an AI evaluation with 0 unsafe items.
- **Fix:** bugs found from logs and the evaluation (for example, recipes dropped for free basics like water, and Groq 400 errors now retry).
- **Deploy:** Vercel (frontend and FastAPI) with Supabase Postgres.

## More docs

- docs/prompts.md (TODO: file does not exist yet)
- docs/assumptions.md (TODO: file does not exist yet)
- docs/reflection.md (TODO: file does not exist yet)
- [docs/decisions.md](docs/decisions.md)
- [docs/ai-usage.md](docs/ai-usage.md)
- [docs/ai-eval-results.md](docs/ai-eval-results.md)
