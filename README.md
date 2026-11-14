# NestForAwhile MTG Warehouse

Synthetic-data grocery support warehouse for client check-in, dietary matching,
barcode safety scans, carts, recipes, and volunteer checkout.

## Local development

```sh
cp .env.example .env
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/python -m seed.load
../.venv/bin/uvicorn app.main:app --reload
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

The local AI default is Ollama. Azure deployment is configured for Groq through
App Service settings; API keys remain outside the repository. All seeded accounts
and products are synthetic and use `@example.test`.

## Deploy (Vercel + Supabase)

Configure the Vercel function region to `pdx1` and set the following environment variables:
- `DATABASE_URL`
- `JWT_SECRET`
- `FIELD_ENCRYPTION_KEY`
- `AI_PROVIDER=groq`
- `GROQ_API_KEY`
- `GROQ_MODEL`
- `ALLOWED_ORIGINS`
- `COOKIE_SECURE=true`
- `SEED_DEMO_DATA=false`

One-time database migration and seed from your laptop (use the same `FIELD_ENCRYPTION_KEY` and `DATABASE_URL` as Vercel):

```sh
cd backend
python -m alembic upgrade head
python -m seed.load
```

## Validation

```sh
.venv/bin/pytest -q backend
cd frontend && npm test -- --run && npm run build
cd ../e2e && npx playwright test
```

See `specs/001-mtg-warehouse-system/` for the specification, plan, contracts,
and task list. See `docs/demo-runbook.md` for a synthetic judging flow.
