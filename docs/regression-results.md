# Regression results

Recorded 2026-11-14:

- Backend: 51 pytest tests passed; Ruff clean.
- Frontend: 15 Vitest tests passed; TypeScript check and Vite build passed.
- Playwright: 13 tests discovered across US1–US7 and US11 suites.
- AI fallback evaluation: 6 scenarios, valid JSON rate 1.0, restricted leaks 0.
- OpenAPI drift check currently reports missing future paths for analytics, inventory,
  queue, reports, and checkout interventions; T095 remains open until those routes exist.
