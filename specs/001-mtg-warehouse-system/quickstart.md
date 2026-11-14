# Quickstart: MTG Warehouse System (local development)

Planned commands. They work once the implementation tasks exist. Synthetic data only.

## 1. Configure
```bash
cp .env.example .env     # fill in locally; never commit .env
```
`.env.example` documents: `DATABASE_URL` (default SQLite file), `JWT_SECRET`, `FIELD_ENCRYPTION_KEY`, `OLLAMA_BASE_URL` (default `http://127.0.0.1:11434`), `OLLAMA_MODEL`, `USDA_API_KEY`, `ALLOWED_ORIGINS`.

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

## 5. Demo AI on UNF HPC (deployed path)
Follow `docs/unf-hpc-guide.md`: UNF VPN on, submit the Ollama Slurm job (GPU partition, `--time` set), open the SSH tunnel from your machine, then set `OLLAMA_BASE_URL` to the tunnel endpoint. Cancel the job afterwards.

## 6. Test
```bash
cd backend && pytest                 # rules, API, checkout atomicity, queue, AI validation, ai_eval
cd frontend && npm test
cd e2e && npx playwright test        # one spec per MUST story
```

## 7. Smoke test of the MVP Success Scenario
Seeded Client logs in → scans a seeded barcode → sees nutrition and Green/Yellow/Red → adds to cart → views recipes with missing-ingredient locations → Volunteer completes checkout → Manager sees updated analytics and downloads the DOCX report. Also: set `Max_Floor_Capacity` to 1, log in a second client, and confirm they are queued and promoted after the first checks out.
