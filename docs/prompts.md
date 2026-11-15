# Prompt history

Prompts we gave our AI tools while building the Epic Cure MTG warehouse app. Which tool was used for each step is recorded in `docs/ai-usage.md`.

Entries summarise the prompts we used, reconstructed from commit messages, `docs/decisions.md`, `docs/ai-usage.md`, `specs/` and `docs/ai-eval-results.md`. Short hashes and PR numbers link each entry to the repo history (all work happened 2026-11-12 to 2026-11-14).

## 0. How planning worked

- Before any planning, we loaded all project direction documents into our planning chat: the official problem case, the kick-off slides, the judging criteria, and our Epic Cure research. Every plan was grounded in the actual requirements.
- All planning was done on one computer, as one shared conversation, so decisions stayed consistent: problem breakdown, requirements and assumptions, architecture (rules-first AI), team split, and judging priorities.
- Only after the Spec Kit constitution, spec, plan and tasks were set up for parallel work did we split into streams (backend/AI and frontend) on separate branches.
- Planning outputs became the prompts we gave our AI coding agent (sections below).

## 1. How we prompted

1. Plan the work together in the planning chat.
2. Turn the plan into a precise, scoped prompt (one task or one small group of tasks).
3. Run it with our AI coding agent on a branch.
4. Review the agent's report, then test on a preview deploy.
5. Commit with a tagged message, open a PR, merge.

Rules we put in every prompt (also in `AGENTS.md`):

- Stay in your stream's files; only touch files for the current task.
- No plan step inside the agent run (the plan was already agreed).
- Run the tests before reporting done.
- Don't commit: report a suggested commit message instead.
- No secrets in code; config from `.env`.
- Synthetic data only, no real client or health data.

## 2. Key prompts by theme

### Planning & spec
- **Constitution, spec, plan, tasks.** Goal: a shared contract so two streams can build in parallel. Gist: Spec Kit commands fed with the planning-chat output (rules-first AI, roles, FIFO queue, safety tiers). Outcome: `13a3fc9` constitution, `43b3c83` spec, `118f2bf` plan, `a56ee55` tasks; plan later corrected to drop a stale deployment path (`dc6ab3a`, `b24df02`, `9007dea`). Merged in PR #1.

### Backend
- **Foundation, rules, seed.** Goal: models, auth, clinical rules matrix, tier mapping, catalog seed. Outcome: `ab100a5`..`bf3436c`, PRs #6, #14.
- **Sessions, queue, checkout.** Goal: capacity limit, FIFO queue, atomic promotion at checkout. Gist: "prove queue promotion is atomic with checkout" (`0e97d87`, PR #16); review findings on concurrency and FIFO fixed in `b9837d7`.
- **Seed to 135 products and 5 personas.** Goal: a realistic synthetic catalog; every limit cites its guideline source. Outcome: `ea06a67`, PR #33.
- **Recommendations.** Goal: deterministic picks only from history, saved recipes and the shopping list; cart items hidden; fall back to most-taken. Outcome: `f314738`, then `153466f` (PR #33).
- **External product safety.** Goal: products not in our catalog (Open Food Facts / USDA) must still be checked. Gist: map their allergens and units to our rules, add calories and carbs. Outcome: `b58f041`, PR #33.
- **Visit flow and client flow.** Check-in, visit state, one list line per item, household members, approval (`2d96c43`, `02a2349`, PRs #20, #26).

### Frontend (Caden's commits)
- **Scan.** Barcode scanner with manual fallback, camera that works on phones and laptops, calories and carbs on the scan card (`7da339a`, `6b386b2`, `2b44486`).
- **List.** Photo/scan-to-add shopping list with a review step, single Upload photo button, Home grocery-list widget (`f6ea670`, `ae55360`, `34fe020`).
- **Checkout.** Volunteer checkout review, visit gate and visit-complete screen (`56f7366`, `251af62`, PR #27).
- **Director dashboard.** Stat cards, checkout in the Director nav, Reports page removed (`c6f94e2`, `1423dbe`, PR #34).
- **Visual direction.** Nutrition-label style redesign and Epic-Cure branding (`baaf856`, `83726d4`).

### AI layer
- **Rules-first recipe AI.** Goal: the model only writes; deterministic rules decide what is safe. Gist: provider abstraction, prompt builder, schema validation, in-stock fallback recipes, rules guard (`a26468c`, `1b8528e`, `61304b8`). Outcome: PRs #13, #17, #18.
- **Manifest.** The model sees a capped shortlist of safe, in-stock items, never Restricted ones (`14608dd`, `b58f041`).
- **Guard and fallback.** Recipes with unknown or unsafe ingredients are dropped; if nothing survives, a deterministic fallback is returned (`61304b8`, `c0bd011`).
- **Merging parallel AI layers.** Two AI layers existed; we kept one and folded the other in (`967ba5e`).

### Deployment
- **Vercel services + Supabase.** Goal: one deploy for frontend and backend with a hosted database. Outcome: config, entrypoint, database engine, pinned driver (`d190472`..`7bc2d14`), then fixes: prepared statements off (`f6bdadd`), install requirements (`ca57617`), SPA fallback for deep links (`ccca403`), report downloads through `/api` (`7a1cc23`). PRs #24, #25, #28.

### Testing & evaluation
- **Eval harness.** Goal: measure the recipe model instead of guessing. Gist: 20 synthetic cases over the 5 personas, three independent safety layers, results summarised in `docs/ai-eval-results.md`. Outcome: `de540d7`, PR #35. Runs were done locally on a self-hosted Ollama server.
- **End-to-end and CI.** Playwright journeys per user story, CI workflow, fake AI provider in CI (`cacbaa6`, `2ad69de`, `46ee092`, PR #19).

## 3. How prompts evolved

- **Seed.** "Expand to 100 products" → "idempotent, self-healing seed". A live test showed a household member was missing after re-seeding, so the prompt asked for a sync that repairs household rows on every run (`ea06a67`; ai-usage row: "self-healing household sync").
- **Recipe AI.** First prompt sent the full catalog → the provider rejected it (HTTP 413). We capped the manifest to a shortlist. Next, calls returned 200 but invalid JSON, so we asked for a debug script (`backend/scripts/debug_recipe_ai.py`) and then strict JSON schema plus low reasoning effort; reasoning tokens fell from 1,240 to 26. Commits `b58f041`, `c0bd011`.
- **Safety.** External products showed Yellow for a peanut-containing snack scanned for a household member with a nut allergy → prompt with an explicit allergen-mapping table from external allergen tags to our rule categories → Red (`b58f041`, tests in `test_external_scan.py`).
- **Eval.** "Test the model" → three independent safety layers (rules check, keyword scan, name-ID consistency). The first run showed 35.7% fallback on normal cases because the guard dropped recipes with free basics like water → we added a free-basics allowlist and fixed the prompt → re-measured 14.3% (`19f538c`, `docs/ai-eval-results.md`). Post-guard safety violations stayed at 0.

## 4. Co-created prompts

Eric ran planning and the backend/AI stream; Caden ran the frontend stream and QA. Prompts were shaped from each other's findings:

- Caden's recommendation findings became the backend recommendations prompt (history, saved recipes, shopping list only; `153466f`).
- Caden asked for calories and total carbs on the scan card, which became a contract change (`carbs_g`) and a backend prompt (`b58f041`, `2b44486`; see `docs/decisions.md`).
- Caden's report that recipes fell back despite the model API answering 200 became the validation-fix prompt (`docs/decisions.md`, "Fix recipe AI validation failures").
- Review feedback became follow-up prompts: client-flow review items (`8dcb021`, `42715e5`), checkout concurrency findings (`b9837d7`).
- Director feedback (Reports removed, Checkout in nav) became frontend prompts (`c6f94e2`, `1423dbe`).

## 5. What worked / what didn't

**Worked**
- Loading all direction documents into the planning chat before planning.
- Small, scoped prompts tied to one task or contract section.
- "Don't commit, report" so a human read the diff first.
- Testing on preview deploys, which caught problems local tests missed (missing household member, deep-link 404s).
- Eval-driven fixes: measure, fix, re-measure.
- A contract in `specs/` that let two streams build in parallel.

**Didn't**
- Agents sometimes committed despite the instruction not to.
- Commit tags sometimes named the wrong tool and were corrected afterwards (see the correction note on main).
- Parallel agents built a duplicate AI layer; merging cost time (`967ba5e`).
- Merges dropped rows from `docs/ai-usage.md` and `docs/decisions.md`, restored by hand (`8e90abd`, `17d08b2`).
