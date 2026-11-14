# Quickstart: MTG Warehouse System (local development)

Planned commands. They work once the implementation tasks exist. Synthetic data only.

## 1. Configure
```bash
cp .env.example .env     # fill in locally; never commit .env
```
`.env.example` documents: `DATABASE_URL` (default SQLite file), `JWT_SECRET`, `FIELD_ENCRYPTION_KEY`, `AI_PROVIDER` (`ollama` locally, `groq` in Azure), `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`), `OLLAMA_MODEL`, `GROQ_API_KEY`, `GROQ_MODEL`, `USDA_API_KEY`, `ALLOWED_ORIGINS`.

## 2. Local AI (development)
```bash
ollama serve &
ollama pull <qwen-model-chosen-by-evaluation>
```
If Ollama is not running, the app still works and shows fallback recipes.

## 3. Backend
```bash
cd backend && pip install -r requirements.txt
alembic upgrade head && python -m seed.load      # synthetic users, products, lots
uvicorn app.main:app --reload
```

## 4. Frontend
```bash
cd frontend && npm install && npm run gen:api && npm run dev
```
`gen:api` regenerates TypeScript types from `specs/001-mtg-warehouse-system/contracts/openapi.yaml`.

## 5. Deployed AI (Azure)
Set `AI_PROVIDER=groq`, `GROQ_MODEL` (an open-weight model), and `GROQ_API_KEY` as Azure App Service settings; never commit the key. If Groq is unreachable or rate-limited, recipes fall back to the deterministic rules-only path.

## 6. Test
```bash
cd backend && pytest                 # rules, API, checkout atomicity, queue, AI validation, ai_eval
cd frontend && npm test
cd e2e && npx playwright test        # one spec per MUST story
```

## 7. Smoke test of the MVP Success Scenario
Seeded Client logs in → scans a seeded barcode → sees nutrition and Green/Yellow/Red → adds to cart → views recipes with missing-ingredient locations → Volunteer completes checkout → Manager sees updated analytics and downloads the DOCX report. Also: set `Max_Floor_Capacity` to 1, log in a second client, and confirm they are queued and promoted after the first checks out.
