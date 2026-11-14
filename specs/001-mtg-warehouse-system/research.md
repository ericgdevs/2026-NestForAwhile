# Research: MTG Warehouse System

Each entry: Decision, Rationale, Alternatives considered. All earlier unknowns are resolved here; R2 and R8 are open risks with a safe default.

## R1. AI model and hosting
- **Decision**: Open-weight Qwen-family model served by Ollama. Local Ollama in development; UNF HPC GPU node (Slurm job + SSH tunnel) for demo inference. The final model size is picked by a small evaluation (the AI evaluation scenarios in `backend/tests/ai_eval`): valid-JSON rate, restricted-ingredient leaks (must be 0 after rules), in-stock ingredient rate, latency.
- **Rationale**: Team decision: no paid API and no Groq. The HPC guide gives a working pattern and timing numbers (a 14b model on an A30 is roughly 34 tokens/s, so a recipe takes about 10–30 s).
- **Alternatives**: Groq or any hosted paid API (rejected by the team); Azure-hosted model (cost, not chosen).

## R2. Reaching HPC from the deployed app (open risk)
- **Problem**: The tunnel is opened by a person from a machine on the UNF VPN. Azure cannot reach a GPU node directly, and Slurm jobs have `--time` limits.
- **Decision**: The backend only knows `OLLAMA_BASE_URL`. For the demo an operator keeps the job and tunnel running and exposes the tunnel endpoint to the backend. The exact relay (for example a reverse SSH tunnel from the operator's machine to the App Service host or a small relay VM) is chosen at deployment time and recorded in `deploy/`. Treat the AI path as optional at runtime: health check on startup and per request, 30 s timeout, then fallback.
- **Rationale**: Core journey must never depend on the tunnel. Judges see a working app even if HPC is down.
- **Alternatives**: Run Ollama on CPU in Azure (too slow); expose the HPC node publicly (not allowed and unsafe).

## R3. Rules engine and Dietary_Tier_ID
- **Decision**: A versioned JSON file `clinical_rules_matrix.json` lists, per restriction (Low Sugar, Low Sodium, Heart Healthy, Kidney Friendly, Vegetarian, Vegan, Gluten Free, Nut Allergy, Dairy Free), the nutrient limits (Capped above X, Restricted above Y, per serving) and ingredient/allergen exclusions. `Dietary_Tier_ID` is a small integer assigned by a fixed lookup from the selected restrictions (the strictest matching tier). `classify(product, profile)` returns Approved / Capped / Restricted plus a plain-language reason. Allergens and exclusions always produce Restricted.
- **Rationale**: One readable file and one function; no AI in the path; easy to unit test and to explain.
- **Alternatives**: Rules in the database (harder to review and version); AI-assisted classification (violates the constitution).
- **Needs team input**: actual thresholds from Epic Cure guidance (spec assumption). Placeholder values are clearly marked synthetic until then.

## R4. Missing or unknown data
- **Decision**: If nutrition or allergen data is missing for a product the client's profile cares about, the result is Capped (Yellow) with the reason "We couldn't confirm this one — please ask a volunteer." It is never Approved by default and never invented.
- **Rationale**: Keeps within three official statuses and the "safest outcome" rule in the spec.
- **Alternatives**: Treat as Restricted (too harsh, hurts dignity and choice); Approved (unsafe).

## R5. Nutrition data sources
- **Decision**: Lookup order for a barcode/SKU: (1) local `products` table (seeded, always works offline), (2) Open Food Facts by barcode, (3) USDA FoodData Central by name/UPC search. Successful external results are cached into `products`. Calls go through the backend with a short timeout; the USDA key lives in `.env`.
- **Rationale**: Open, free sources; caching keeps scans under 3 s and works if a source is down.
- **Alternatives**: Paid nutrition APIs (rejected, no paid services); calling sources directly from the phone (exposes keys, no caching).

## R6. Barcode scanning
- **Decision**: Camera scanning in the browser with a JavaScript scanning library that works on iOS Safari (the native `BarcodeDetector` API is not available there), plus a manual SKU field that is always visible. Library choice is made at implementation and needs team approval.
- **Rationale**: Spec requires camera and manual fallback on smartphones.

## R7. Capacity enforcement and queue (US-1.3)
- **Decision**: `capacity_settings` holds `Max_Floor_Capacity`. `Active_Floor_Shoppers` is computed, not stored: the count of sessions with status `active` plus queue entries with status `ready` (a held slot). `Queue_Waiting` is the count of queue entries with status `waiting`.
- **How the queue works**:
  1. Check-in succeeds → if `Active_Floor_Shoppers < Max_Floor_Capacity`, create the session and `Shopping_Session_Token` immediately.
  2. Otherwise create a queue entry (`waiting`) and show the client their position and a friendly message; the client's screen polls every few seconds.
  3. When a session ends (checkout completes, client leaves, or the session expires) the oldest `waiting` entry becomes `ready` in the same transaction, and the client is told to come in.
  4. A `ready` client confirms within a short claim window (default 5 minutes); on confirm a session is created and the entry becomes `claimed`. If the window passes the entry becomes `expired` and the next waiting entry is promoted.
  5. Order is strictly first-in-first-out by `joined_at`. Promotion and the capacity check run inside one database transaction so two shoppers cannot take the last slot.
  6. Managers can change `Max_Floor_Capacity`; if it is raised, waiting entries are promoted until full. Volunteers and staff see the counts.
- **Rationale**: Small, predictable, testable, and keeps the "active shopper count" from US-1.1 consistent.
- **Alternatives**: A stored counter (can drift); a separate queue service (more moving parts).

## R8. Auth, secrets, and PHI (open detail: key management)
- **Decision**: Argon2 password hashes; JWT in an HttpOnly cookie with short expiry; role re-read from the database on each request. Name, email, dietary restrictions, and allergies are encrypted per field with a Fernet key from `.env`. In Azure the key comes from app settings (Key Vault is a later improvement).
- **Rationale**: Meets "encrypted at rest" and "server-side authorization" with minimal parts. Wording stays "designed with HIPAA safeguards".

## R9. Checkout atomicity and FIFO
- **Decision**: One database transaction: re-validate every cart line with the rules engine, then decrement lots in FIFO order (earliest expiration first) with a row-level check that stock stays at or above zero, write the receipt and a movement record; roll back on any failure. A Restricted item returns a hard stop; resolving it needs a volunteer action that is stored in `interventions`.
- **Rationale**: Directly implements US-4.1 and the "two shoppers, last unit" edge case.

## R10. Reports
- **Decision**: python-docx builds the DOCX from a built-in template with four sections (donor metrics, grant attribution, distribution totals, visit metrics) using aggregated, anonymized queries. Custom uploaded templates are NICE scope and not planned.

## R11. Analytics anonymization
- **Decision**: Analytics queries return aggregates only; no client id, name, or email in any analytics or report payload. Small groups are not broken out by client attributes.

## R12. Deployment
- **Decision**: One Docker image on Azure App Service serves the API and the built frontend; Azure Database for PostgreSQL Flexible Server for data; settings in App Service configuration. Migrations run on start. Details go in `deploy/`.
- **Alternatives**: Separate Static Web App plus API (two deployments, CORS work, more to explain).
