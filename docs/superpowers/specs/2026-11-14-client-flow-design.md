# Client shopping flow: design

Status: draft for Caden's approval (builder check done; Caden's answers folded in). Author: Copilot (Sonnet 5.5) with Caden, 2026-11-14.
Background reading: `PRODUCT.md`, `DESIGN.md`, `specs/001-mtg-warehouse-system/spec.md`, the Epic Cure brief (pasted by Caden; used as context, not as law).

## 1. Intent

A client walks into the Epic Cure warehouse and shops with their own phone. The app helps them in three ways:

- It tells them, in plain words and one glance, whether a product is safe for **their whole household**.
- It helps them find food they can actually use: recommendations, recipes, a shopping list with shelf locations.
- It records what they take, so a volunteer can check them out quickly and inventory stays accurate.

Dignity and client choice come first. The app warns and suggests; it never shames. Only checkout can stop food from leaving, and only for real safety reasons or an unapproved account.

All features below are equal priority (Caden, 2026-11-14). The demo must show the whole journey live.

## 2. Goals, non-goals, anti-goals

**Goals**
- One continuous journey, end to end: kiosk QR → sign in or sign up → shop (scan, label, recipes, shopping list, cart) → volunteer checkout → inventory updated.
- Household-level safety labels that are always right, always explained, and decided by rules, never by AI.
- Volunteers can check a client out from their own phone in under a minute.

**Non-goals**
- Storing medical conditions. They are used once to pick dietary classes, then discarded.
- Showing anyone's real name in the client or staff UI.
- Multi-language, facial recognition, camera cart tracking (already out of scope in `spec.md`).
- A native app. This is the existing mobile web app.

**Anti-goals (failure even if it "works")**
- A Yellow label that hides a dangerous allergy because it looks like "fine in moderation".
- AI deciding or changing a safety label.
- Checkout trusting the phone without a volunteer looking at the physical cart.
- Medical conditions, photos of shopping lists, or nicknames reaching logs, analytics, or reports.

## 3. Constraints

- Synthetic data only (`@example.test`), in seed data, tests, screenshots, and demos.
- Organizer variable names stay exactly as specified: `Client_Enrollment_Status`, `Household_Size`, `Dietary_Tier_ID`, `Shopping_Session_Token`, `Active_Cart_Manifest`, `Active_Floor_Shoppers`.
- Stack is fixed: React + Vite + TypeScript frontend; FastAPI + SQLAlchemy + Alembic backend; AI via `AI_PROVIDER` (Ollama locally, Groq on Azure) with the deterministic fallback always available.
- WCAG 2.2 AA; status is never shown by color alone; 44px touch targets.
- Ownership: Caden owns `frontend/`. Backend changes are made on separate `api/*` branches, logged in `docs/proposals/backend-changes-log.md`, and reviewed by Aditya (API/data) or Eric (AI). `openapi.yaml` changes go with them.
- Visual language is the existing Nutrition Facts label system in `DESIGN.md`.

## 4. The journey (decided by Caden)

### 4.1 Arrival: kiosk QR
- The kiosk shows **one QR code, the same for everyone**. It opens the web app's sign-in page.
- Signing in on the phone is the check-in. It starts the visit (`Shopping_Session_Token`) and counts toward `Active_Floor_Shoppers`.
- If the floor is full, the client lands on the existing Waiting screen (US-1.3 queue).

### 4.2 Sign-up (new clients)
- New clients create their account on their phone. Clients now create their own accounts; today only staff can.
- Sign-in stays **email + password**, the same as today.
- Sign-up also asks for the client's **real name**. It is stored encrypted and shown **only on the manager's approval screen**, so staff can verify who they're approving. It never appears in the client app, other staff screens, logs, analytics, or reports.
- Sign-up collects:
  - **Household members**: how many, and each person's **age**.
  - Each person's **nickname**. The default is "Person 1", "Person 2", and the client can rename them ("Mom", "Little one").
  - **Dietary restrictions and allergies**, either for the whole household or per person.
  - **Medical conditions**, optional and per person. They are used only to pick that person's dietary classes, then discarded and **never stored**.
- The new account is **pending**. The client can shop right away, but **cannot complete checkout until staff approve the account**.

### 4.3 Household safety label (rules engine)
- Each product gets one label for the household, computed from every member's rules:

  | Members who can't have it | Label |
  |---|---|
  | none | Green (Approved) |
  | some, but not all | Yellow (Capped) |
  | all | Red (Restricted) |

- The card always says **who** and **why** using nicknames, for example "Not for Little one: nut allergy".
- **Allergy safeguard:** an item that matches an **allergy** of any member (not just a diet limit) shows its Yellow label with an allergy warning. At checkout it **pauses** for the volunteer, who must confirm with the client and acknowledge it before completing. The acknowledgement is logged as an intervention.
- Labels are computed by the deterministic rules engine only.

### 4.4 Home (first screen after sign-in)
1. **Recommended groceries**, chosen from current stock, the household's past visits, and their saved recipes, and sized to the household (sizes and ages). Each one shows its label and location.
2. **The scanner**, ready to use (camera plus manual SKU entry).

### 4.5 Scan result
Top to bottom:
1. The household label (status bar), plus who it is not for and why.
2. The nutrition facts.
3. **Add to cart**. Scanning alone never adds anything.
4. If the label is **Red**: a warning plus **one or two safer in-stock swaps**, each with aisle, shelf, bin and its own Add to cart.
5. **Recipe ideas** using this product, filterable by **cuisine** (many cuisines, as clickable filters). Each recipe has **Save** and **Add to cart**.
   - **Save** stores the recipe on the client's profile for later.
   - **Add to cart** puts the recipe's missing ingredients on the Shopping list (4.6). It does not put them in the tracked cart.

### 4.6 Shopping list tab (one list)
- Holds both the client's own items and recipe ingredients.
- Clients add their own items by typing or pasting text, or by **taking or uploading a photo** of a handwritten list. The app reads it and matches each line to products in stock.
- Each line shows: the item, its **aisle, shelf and bin**, its household label, and where it came from: **"You added"** or **"For: <recipe>"** with a button that opens that recipe.
- Lines we don't carry, or that are out of stock today, say so.
- Ticking a line adds that product to the tracked cart.

### 4.7 Cart (tracked)
- Only taps on **Add to cart** (or ticking a shopping-list line) put things here. This is the record checkout uses.
- Each item shows its label, nutrition facts, and quantity with − / +.

### 4.8 Checkout (volunteer's phone)
1. The volunteer **scans the QR code on the client's phone**, or types the client ID.
2. The client's tracked cart loads on the volunteer's screen.
3. The volunteer **confirms** items against the physical cart, **scans** items the client forgot, and **removes** items that aren't there.
4. **Complete checkout** removes everything from inventory in one atomic transaction.
- Hard stops before completion:
  - a **Red** item: remove it, or a manager records an override;
  - a **pending** account: a manager approves it;
  - an **allergy match** for any member: the volunteer acknowledges it with the client (logged).

## 5. Decisions made by Copilot (Caden to check)

These are my calls to fill gaps. Each is marked so Caden can overturn it.

1. **Where "can't have it" comes from.** A member "can't have" a product when the rules engine gives Restricted for that member's own restrictions and allergies. Capped for any member (e.g. above a sugar guideline) makes the household label at least Yellow. Missing nutrition data counts as Capped (existing rule).
2. **Red behavior.** Red items can still be added to the cart (client choice), after one confirmation: "This isn't recommended for anyone in your household. Add anyway?". Checkout then hard-stops on them (existing US-7 behavior).
3. **Who approves pending accounts.** Warehouse Manager approves; the volunteer's checkout screen shows "Waiting for approval", and the manager approves from their own screen. Approval is logged.
4. **Medical conditions list.** A fixed short list per person (e.g. Diabetes, High blood pressure, Kidney disease, Heart disease, Celiac), each mapped to dietary classes in `clinical_rules_matrix.json`. No free text. The chosen conditions are processed in the request and never written to the database or logs.
5. **Stored per person:** nickname, age, dietary classes, restrictions, allergies, all encrypted at rest like today's profile. `Household_Size` stays on the client and equals the member count.
6. **Portion sizing by age.** Suggested quantities count children under 12 as half a portion and adults as one. The Recommendation rationale says so.
7. **Swaps.** A swap is a product in the same category, in stock, whose household label is Green, or Yellow if no Green exists. Chosen by rules and inventory, not AI. At most two.
8. **Recipes.** AI generates recipes from the scanned product, the household's combined restrictions, and current stock; the rules guard then removes any recipe with a Restricted ingredient for any member (stricter than the household label), and the deterministic fallback still applies. Cuisine comes from the AI output (`cuisine` field, already proposed in `docs/proposals/recipe-cuisine-contract.md`).
9. **Photo shopping lists.** A vision-capable model reads the photo into text lines; matching lines to products uses the same AI-plus-rules path as recipes. The photo is not stored.
10. **Recommendations from past visits and saved recipes.** Past visits = products in this household's completed checkouts. Saved recipes add their in-stock ingredients. Rules filter out anything Red for the household.
11. **Client QR at checkout** encodes the active `Shopping_Session_Token` only, never personal data. The typed fallback is the client ID shown on the client's Cart screen.
12. **Volunteer edits** (add, remove, quantity change) are recorded as checkout interventions, the same as today's Restricted-item removal.

13. **Household `Dietary_Tier_ID`** is the strictest tier across all members.
14. **Existing clients** move to one member, "Person 1", carrying their current profile; their `Household_Size` stays as it is.
15. **Condition → dietary class mappings** start as placeholders in `clinical_rules_matrix.json` (already labelled as placeholders) until Epic Cure confirms them.
16. **Strangers creating accounts:** a pending account can shop but can't take any food out until a manager approves it, so no extra sign-up protection is added for now.
17. **Shared contract changes** (Caden allowed backend changes on separate branches, logged): `spec.md` FR-004 and US-1 scenario 3 change so Pending clients can sign in and shop but not check out; FR-017 and US-7 add the allergy acknowledgement; `openapi.yaml` gets the new endpoints. All of this is made on `api/*` branches and logged in `docs/proposals/backend-changes-log.md` for Aditya and Eric to review.

## 6. What changes, by area

| Area | Change | Owner to review |
|---|---|---|
| Data model | Household members table (nickname, age, encrypted classes, restrictions, allergies); saved recipes; shopping list items; pending status already exists (`Client_Enrollment_Status = Pending`) | Aditya |
| Rules | Household label from per-member results; swap finder | Aditya (rules), Eric (matrix content) |
| Auth / sign-up | Self sign-up (email, password, staff-only real name) creating a Pending client; Pending can sign in; manager approval endpoint and screen | Aditya |
| Checkout | Load cart by session QR or client ID; volunteer add/remove; pending, Red, and allergy-acknowledge stops; atomic decrement (exists) | Aditya |
| AI | Per-product recipes with cuisine; shopping-list photo/text parsing | Eric |
| Frontend | Sign-up flow, Home, Scan result, Shopping list tab, Cart, Saved recipes, volunteer Checkout with QR scanner, manager approvals | Caden |
| Tests | Unit tests per rule, route tests per endpoint, one Playwright spec per journey step | everyone; Playwright with Eric |

## 7. How it gets built (Caden, 2026-11-14)

- **Reuse the existing frontend.** Extend the current screens, components, and styles (`AppShell`, `StatusBadge`, `NutritionFacts`, `RecipeGroups`, `RecipeSheet`, `BarcodeScanner`, `Icon`, the `index.css` classes, `lib/roles.ts`, `api/client.ts`). Only rebuild a piece when the new flow can't fit in it. No full rewrite.
  - Expected reuse: Scan gains swaps, recipes, and the household "who/why" line; Cart already has labels, facts, and the stepper; Home keeps recommendations and adds the scanner; Recipes/RecipeGroups power per-item recipes with cuisine filters; Checkout is extended, not replaced.
  - Expected new pieces: sign-up flow, Shopping list tab, Saved recipes, the volunteer QR scan on Checkout, and manager approvals.
- **Tools on every step:**
  - **Impeccable** for UI design. The visual world is already set in `DESIGN.md` and `.impeccable/surfaces/frontend-src.md`, so new screens extend that world (no new direction roll). Run its detector, and the finish review on new screens.
  - **Ponytail** for writing code (smallest complete change, reuse first) and for reviewing each change before it's called done.
  - **Agentation** for Caden's page feedback in the running dev app. Each feedback round is logged in `docs/ai-usage.md`.

## 8. Left to the builder

- Screen-level layout within the Nutrition Facts label system in `DESIGN.md`.
- API shapes, as long as `openapi.yaml` is updated with them and organizer names are kept.
- Which vision model, within `AI_PROVIDER` constraints.
- Exact wording of messages, within the plain, non-clinical voice in `PRODUCT.md`.
