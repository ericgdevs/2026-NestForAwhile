# Demo runbook

## Local startup

1. Copy `.env.example` to `.env` and generate a Fernet key.
2. Start the API with `uvicorn app.main:app --app-dir backend --reload`.
3. Start the frontend with `npm run dev` from `frontend/`.
4. Use synthetic accounts from `backend/seed/load.py`; every account uses `@example.test`.

## Demo flow

Sign in as the active client, review dietary choices, scan a synthetic SKU, add it to the cart,
request recipes, then use a volunteer account to review checkout.

If the configured AI provider is unavailable, the deterministic rules-only recipe fallback remains
available. Never enter real client data or credentials in the demo environment.
