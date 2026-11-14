# Data Model: MTG Warehouse System

Synthetic data only. Official variable names are used exactly. Fields marked 🔒 are encrypted at rest.
No blood pressure, blood sugar, weight, or clinical outcome fields exist anywhere.

## Users and clients

**users**: `id`, `email` 🔒 (plus a deterministic hash column for lookup), `password_hash` (Argon2), `role` (Client | Volunteer | Warehouse Staff | Warehouse Manager | Director), `is_active`, `created_at`.

**clients** (one per Client user): `user_id`, `name` 🔒, `Household_Size` (int ≥ 1), `Client_Enrollment_Status` (Active | Inactive | Pending), `Dietary_Tier_ID`, `created_at`.

**dietary_profiles** (one per client): `client_id`, `restrictions` 🔒 (list of: Low Sugar, Low Sodium, Heart Healthy, Kidney Friendly, Vegetarian, Vegan, Gluten Free, Dairy Free), `allergies` 🔒 (e.g., Nut Allergy), `preferences` 🔒 (free text/list), `updated_at`. Saving recomputes `clients.Dietary_Tier_ID` through the rules mapping.

**visits** (visit history): `id`, `client_id`, `session_id`, `started_at`, `completed_at`, `pounds_distributed`.

**saved_recipes** (NICE; table reserved, not built in MVP): `client_id`, `recipe_json`, `saved_at`.

## Sessions, capacity, and queue (US-1.3)

**shopping_sessions**: `id`, `Shopping_Session_Token` (random, unique), `client_id`, `status` (active | completed | expired | cancelled), `started_at`, `ended_at`.

**capacity_settings** (single row): `Max_Floor_Capacity` (int ≥ 1), `claim_window_minutes` (default 5), `updated_by`, `updated_at`.

**queue_entries**: `id`, `client_id`, `joined_at`, `status` (waiting | ready | claimed | expired | cancelled), `ready_at`, `claimed_session_id`.

Derived values (computed in one query, never stored):
- `Active_Floor_Shoppers` = sessions with status `active` + queue entries with status `ready`
- `Queue_Waiting` = queue entries with status `waiting`

State transitions: `waiting → ready → claimed`, `ready → expired`, `waiting|ready → cancelled`. A session ends → oldest `waiting` becomes `ready` in the same transaction. Rule: `Active_Floor_Shoppers ≤ Max_Floor_Capacity` always.

## Catalog and inventory

**products**: `id`, `sku`, `barcode` (unique), `name`, `category`, `image_url`, `serving_size_g`, nutrition per serving (`calories`, `sodium_mg`, `sugar_g`, `added_sugar_g`, `sat_fat_g`, `fiber_g`, `protein_g`, `potassium_mg`, `phosphorus_mg`, `carbs_g`), `ingredients_text`, `allergens` (list), `diet_flags` (e.g., contains_gluten, contains_dairy, is_vegan), `weight_lb`, `source` (seed | open_food_facts | usda), `fetched_at`. Missing nutrition values are stored as null, never zero.

**inventory_lots**: `id`, `product_id`, `quantity` (≥ 0), `received_at`, `expiration_date`, `aisle`, `shelf`, `bin`, `reorder_threshold`, nullable `donor_id`, nullable `grant_id`. FIFO order = earliest `expiration_date`, then `received_at`. Expiring soon = within 7 days. Expired lots are excluded from recommendations.

**audit_events**: `id`, `lot_id` or `product_id`, `expected_qty`, `counted_qty` (≥ 0), `variance` (counted − expected), `counted_by`, `counted_at`. Written in the same transaction that updates the lot quantity. Flow: Scan Item → Current Count → Actual Count → Variance → Inventory Update → Audit Log.

**inventory_movements**: `id`, `lot_id`, `change`, `reason` (checkout | audit | restock | expired), `ref_id`, `created_at` (supports auditability and "inventory usage").

## Cart and checkout

**carts**: `id`, `session_id` (unique). The `Active_Cart_Manifest` is the cart's lines serialized for AI and checkout: `[{product_id, name, quantity}]`.

**cart_items**: `cart_id`, `product_id`, `quantity` (≥ 1), `added_at`, `from_recommendation` (bool, drives adoption rate).

**recommendations**: `id`, `session_id`, `product_id`, `suggested_qty`, `rationale`, `created_at` (generated at session start; scaled by `Household_Size`).

**checkouts**: `id`, `session_id`, `validated_by`, `status` (completed | blocked), `total_lb`, `completed_at`.

**checkout_items** (receipt lines): `checkout_id`, `product_id`, `lot_id`, `quantity`, `status_at_checkout`.

**interventions**: `id`, `checkout_id`, `product_id`, `volunteer_id`, `action` (removed_item | approved_exception), `note`, `created_at`. Restricted items cannot be approved as exceptions in MVP; the action is `removed_item` only unless the team decides otherwise.

## Reporting

**reports**: `id`, `type` (donor | grant), `period_start`, `period_end`, `generated_by`, `generated_at`.
**donors** and **grants**: `id`, `name`, `attribution_label` (synthetic names only), used for attribution in reports.
Report and analytics values are computed from aggregates over visits, checkouts, movements, and cart items; no client identifiers are included.

## AI records

**ai_requests** (optional logging, no client identity): `id`, `kind` (recipe | explanation), `model`, `latency_ms`, `valid` (bool), `used_fallback` (bool), `created_at`. Used for AI evaluation and the adoption metric.

## Validation rules (selected)

- `Household_Size` ≥ 1; quantities are positive integers; counted quantity is a non-negative integer.
- A session can only be created when `Client_Enrollment_Status = Active` and capacity allows.
- Checkout fails closed: any Restricted line, unknown product, or stock shortfall blocks the whole checkout and changes nothing.
