# Feature Specification: NestForAwhile 2026 – Epic Cure Medically Tailored Grocery (MTG) Warehouse System

**Feature Branch**: `001-mtg-warehouse-system`  
**Created**: 2026-11-14  
**Status**: Draft  
**Input**: User description: "Provide Epic Cure with a lightweight but complete Medically Tailored Grocery platform that combines warehouse operations, dietary safety enforcement, inventory management, barcode-based nutrition assistance, and AI-powered recipe generation using available warehouse inventory, demonstrating a complete System of Record ↔ System of Intelligence data loop."

## User Scenarios & Testing *(mandatory)*

Stories are ordered by the end-to-end MVP journey: a client signs in, shops safely, checks out, and
management sees the result. Official story IDs are kept for traceability.

### User Story 1 - Client Check-In and Shopping Session (US-1.1, Priority: P1)

An enrolled client logs in and starts a shopping session. The system loads their profile and shows
a personalized recommendation view.

**Why this priority**: Every other client experience depends on a signed-in, active session.

**Independent Test**: Log in as an active client and confirm a session starts, the profile loads,
and the session is counted as an active shopper.

**Acceptance Scenarios**:

1. **Given** a client with valid credentials and `Client_Enrollment_Status` of Active, **When** they log in, **Then** their profile loads, a `Shopping_Session_Token` is created, and they see a personalized recommendation view.
2. **Given** a session was just created, **When** a staff member views the active shopper count, **Then** the count includes that session.
3. **Given** a client whose `Client_Enrollment_Status` is not Active, **When** they try to start a session, **Then** no session is created and they see a friendly message explaining what to do next. (A Pending self sign-up sees a "waiting for staff approval" screen until a Warehouse Manager approves the account.)
4. **Given** invalid credentials, **When** a user tries to log in, **Then** access is denied and no session is created.

---

### User Story 2 - Dietary Profile in Plain Language (US-2.1, Priority: P1)

A client records dietary restrictions, allergies, and preferences using friendly, non-clinical
wording. The system assigns a `Dietary_Tier_ID` from fixed rules.

**Why this priority**: Safe, personalized recommendations and checkout checks depend on the profile.

**Independent Test**: Select restrictions and allergies, save, sign out and back in, and confirm the selections persist and a tier is assigned.

**Acceptance Scenarios**:

1. **Given** a signed-in client, **When** they select restrictions and allergies and save, **Then** the profile persists across sessions.
2. **Given** a saved profile, **When** the rules mapping runs, **Then** a `Dietary_Tier_ID` is assigned by the rules and never by AI.
3. **Given** a stored profile, **When** it is held by the system, **Then** sensitive profile information is protected at rest.
4. **Given** the profile screen, **When** a client reads it, **Then** it uses plain, respectful wording and lets them change choices at any time.

---

### User Story 3 - Grocery Recommendations and Intelligent Matching (US-1.2, US-3.2, Priority: P1)

At session start, the client sees recommended products that are in stock, match their dietary needs,
and are sized to their `Household_Size`, each with a short reason.

**Why this priority**: This is the core client value and the first half of the data loop.

**Independent Test**: Start sessions for households of different sizes and profiles; verify quantities scale, every item is in stock, and no Restricted item appears.

**Acceptance Scenarios**:

1. **Given** two clients with different `Household_Size` values, **When** recommendations are generated, **Then** suggested quantities differ accordingly.
2. **Given** a product that is out of stock, **When** recommendations are generated, **Then** it is excluded.
3. **Given** a product that is Restricted for the client, **When** recommendations are generated, **Then** it never appears.
4. **Given** any recommendation, **When** it is displayed, **Then** a plain-language rationale is shown, and every item exists in current inventory.

---

### User Story 4 - Barcode Safety Scan (US-3.1, Priority: P1)

A client scans a product barcode with a smartphone camera, or types the SKU, and immediately sees
nutrition facts, an image when available, and a Green / Yellow / Red status with an explanation.

**Why this priority**: It is the signature safety feature and part of the MVP success scenario.

**Independent Test**: Scan or enter a SKU for one Approved, one Capped, and one Restricted product and verify status, explanation, and nutrition for each.

**Acceptance Scenarios**:

1. **Given** a camera-enabled phone, **When** the client scans a barcode, **Then** product information and status appear.
2. **Given** a camera that is unavailable or a barcode that will not scan, **When** the client enters the SKU manually, **Then** the same result appears.
3. **Given** a scanned product, **When** results show, **Then** nutrition facts are displayed, and the product image is displayed when one exists.
4. **Given** a scanned product, **When** the rules evaluate it, **Then** status is Approved (Green), Capped (Yellow), or Restricted (Red), with an explanation.
5. **Given** an unknown SKU, **When** it is looked up, **Then** the client sees a friendly "not found" message and no status is invented.

---

### User Story 5 - Digital Cart (Priority: P1)

A client builds a digital cart that mirrors their physical cart: add, remove, change quantity, and
see it live. The cart lasts for the whole session.

**Why this priority**: Recipes, checkout, and inventory updates all work from the cart.

**Independent Test**: Add, change, and remove items, refresh the page, and confirm the cart is unchanged within the session.

**Acceptance Scenarios**:

1. **Given** an active session, **When** the client adds an item, **Then** it appears in the live cart.
2. **Given** an item in the cart, **When** the client changes its quantity or removes it, **Then** the cart updates immediately.
3. **Given** a populated cart, **When** the page is reloaded within the session, **Then** the cart contents persist.

---

### User Story 6 - Inventory-Aware Recipe Suggestions (US-3.3, Priority: P1)

The client receives recipe ideas built from scanned products and cart contents (the
`Active_Cart_Manifest`) and current inventory. Missing ingredients are listed with their warehouse
locations. Rules validate every suggestion before it is shown.

**Why this priority**: It completes the System of Intelligence half of the data loop.

**Independent Test**: Build a cart, request recipes, and verify they favor in-stock items, list missing ingredients with locations, and never include a Restricted ingredient.

**Acceptance Scenarios**:

1. **Given** a cart, **When** recipes are requested, **Then** the AI receives the `Active_Cart_Manifest` and current inventory.
2. **Given** suggested recipes, **When** displayed, **Then** they prioritize available inventory, and missing ingredients are identified with warehouse locations.
3. **Given** any AI output, **When** it is checked by the rules engine, **Then** suggestions that contain Restricted ingredients are removed or replaced before display.
4. **Given** the AI service is unavailable or returns invalid output, **When** recipes are requested, **Then** a deterministic fallback suggestion is shown instead of an error.

---

### User Story 7 - Clinical Checkout Guardrail (US-4.1, Priority: P1)

A volunteer validates the cart at checkout. Restricted items cause a hard stop that needs volunteer
intervention. A successful checkout produces a receipt and decrements inventory atomically.

**Why this priority**: It is the last safety check before food leaves the warehouse.

**Independent Test**: Check out one clean cart and one cart containing a Restricted item; verify the hard stop, the receipt, and that inventory changes only on success.

**Acceptance Scenarios**:

1. **Given** a cart with a Restricted item, **When** the volunteer validates checkout, **Then** checkout stops and requires volunteer intervention.
1a. **Given** a household where an item is restricted for every member (Red), **When** the volunteer validates, **Then** checkout stops until the item is removed or a Warehouse Manager records an override with a reason. **Given** an item matching an allergy of some members (Yellow with allergy), **Then** checkout pauses until the volunteer confirms it with the client and acknowledges it (logged). *(Added 2026-11-14, client flow design; review: Aditya.)*
2. **Given** a cart with no Restricted items, **When** checkout completes, **Then** a receipt is generated.
3. **Given** a successful checkout, **When** it completes, **Then** every item's inventory is decremented together or not at all.
4. **Given** a checkout that fails partway, **When** the failure occurs, **Then** no inventory is changed.

---

### User Story 8 - Inventory Audit Scanner (Priority: P2)

Warehouse staff scan a product, see its current quantity, enter the counted quantity, and the
system records the variance and updates inventory.

**Why this priority**: Accurate counts keep recommendations and recipes honest.

**Independent Test**: Scan an item, enter a different count, and confirm the variance, the stored audit event, and the updated quantity.

**Acceptance Scenarios**:

1. **Given** a scanned product, **When** staff view it, **Then** the current quantity is shown.
2. **Given** a counted quantity, **When** staff submit it, **Then** the variance is calculated, an audit event is stored, and inventory is updated.

---

### User Story 9 - Replenishment Workflow (US-4.2, Priority: P2)

Staff see items below their threshold and receive a restocking list with aisle, shelf, and bin,
which they can sort by priority.

**Why this priority**: It keeps shelves stocked so recommendations stay useful.

**Independent Test**: Lower an item below its threshold and confirm it appears on the list with its location and correct priority order.

**Acceptance Scenarios**:

1. **Given** an item below threshold, **When** staff open the replenishment list, **Then** it is listed with aisle, shelf, and bin.
2. **Given** several low items, **When** staff sort by priority, **Then** the list reorders accordingly.

---

### User Story 10 - FIFO and Expiration Management (US-4.3, Priority: P2)

A warehouse manager sees lots in FIFO order and a dashboard warning for items expiring within
seven days.

**Why this priority**: It reduces waste and supports waste-reduction reporting.

**Independent Test**: Load lots with different expiration dates and verify the order, the seven-day flag, and the dashboard warning.

**Acceptance Scenarios**:

1. **Given** multiple lots of an item, **When** viewed, **Then** they are sorted by FIFO using tracked expiration dates.
2. **Given** a lot expiring within seven days, **When** the dashboard loads, **Then** the lot is flagged and a warning is visible.

---

### User Story 11 - Role-Based Access (Priority: P1)

Every user signs in and sees only the screens their role allows. Roles are Client, Volunteer,
Warehouse Staff, Warehouse Manager, and Director.

**Why this priority**: It protects client data and operational controls, and gates every other story.

**Independent Test**: Sign in as each role and try to reach both allowed and disallowed screens and actions.

**Acceptance Scenarios**:

1. **Given** an unauthenticated visitor, **When** they open any protected screen, **Then** they are sent to login.
2. **Given** a signed-in user, **When** they attempt an action outside their role, **Then** the server denies it, even if they bypass the interface.
3. **Given** each role, **When** they sign in, **Then** they see only the screens appropriate to that role.

---

### User Story 12 - Analytics Dashboard (Priority: P2)

Warehouse management reviews anonymized operational metrics: families served, visits completed,
pounds distributed, inventory usage, recommendation adoption rate, and waste-reduction metrics.

**Why this priority**: It closes the data loop by showing the effect of each visit.

**Independent Test**: Complete a checkout and confirm the metrics update, with no client-identifying information shown.

**Acceptance Scenarios**:

1. **Given** completed visits, **When** a manager opens the dashboard, **Then** all six metrics are shown.
2. **Given** a new checkout, **When** the dashboard refreshes, **Then** the figures reflect it.
3. **Given** any analytics view or export, **When** inspected, **Then** no client names or identifying details appear.

---

### User Story 13 - Donor and Grant Reporting (US-5.2, Priority: P2)

Management generates a professional report from a template and exports it as DOCX, with donor
metrics, grant attribution, food distribution totals, and visit metrics.

**Why this priority**: It turns operational data into funding evidence.

**Independent Test**: Generate a report after sample visits and open the DOCX to confirm all four sections.

**Acceptance Scenarios**:

1. **Given** collected data, **When** management generates a report, **Then** a DOCX file downloads.
2. **Given** the report, **When** opened, **Then** it contains donor metrics, grant attribution, food distribution totals, and visit metrics.

---

### User Story 14 - Public Deployment (Priority: P1)

The system is publicly reachable at a stable URL during judging, with a hosted database, working
login, and the core journey demonstrable live.

**Why this priority**: A deployed end-to-end workflow is required for judging.

**Independent Test**: From an outside network, open the public URL, log in, and run the MVP Success Scenario.

**Acceptance Scenarios**:

1. **Given** the public URL, **When** opened from outside the team network, **Then** the application loads.
2. **Given** the deployed system, **When** a tester logs in, **Then** authentication works against the hosted database.
3. **Given** the deployed system, **When** the MVP Success Scenario is run, **Then** it completes end to end.

---

### Nice-to-Have Stories (Priority: P3, only after all MUST stories pass)

- **Recipe Saving**: a client can save favorite recipes.
- **Smart Product Substitutions**: suggest healthier alternatives that are already in inventory.
- **Expiring-Item Promotion**: recommend healthy items nearing expiration.
- **Enhanced Analytics Visualizations**: trend charts and category breakdowns.
- **Custom Report Templates**: management uploads DOCX templates with placeholders.

### Edge Cases

- Two clients check out the same last unit at the same time: only one succeeds, and inventory never goes negative.
- A client's profile changes mid-session: recommendations and checks use the latest profile.
- A product has no nutrition data or image: the product still displays, saying the information is unavailable, and the status falls back to the safest rule outcome.
- Missing profile or unknown restrictions: the product is not marked Approved by default.
- The AI returns malformed output, an unsafe recipe, or times out: rules validation and deterministic fallback apply.
- A counted quantity is negative or not a number: it is rejected.
- A session expires or the client logs out: the cart is retained only per session rules, and no inventory is changed.
- A volunteer overrides a hard stop: the intervention is recorded for audit.
- A lot is already expired: it is flagged and excluded from recommendations.

## Requirements *(mandatory)*

### Functional Requirements

**Access and sessions**
- **FR-001**: System MUST require login for all screens and authenticate users with valid credentials only.
- **FR-002**: System MUST support the roles Client, Volunteer, Warehouse Staff, Warehouse Manager, and Director, and MUST enforce permissions on the server, denying unauthorized access.
- **FR-003**: System MUST show each role only the screens appropriate to it.
- **FR-004**: System MUST start a shopping session only when `Client_Enrollment_Status` is Active, create a `Shopping_Session_Token`, load the client profile, and count the session as an active shopper.

**Dietary profile and rules**
- **FR-005**: Clients MUST be able to select, save, and later change dietary restrictions, allergies, and preferences, and the profile MUST persist across sessions.
- **FR-006**: System MUST assign `Dietary_Tier_ID` through deterministic rules mapping.
- **FR-007**: System MUST protect sensitive profile information at rest.
- **FR-008**: System MUST classify every product as Approved (Green), Capped (Yellow), or Restricted (Red) using deterministic rules only, with a plain-language explanation. AI MUST NOT decide or override a status.
- **FR-009**: Dietary profile and status wording MUST be friendly and non-clinical, and MUST preserve client choice.

**Recommendations and scanning**
- **FR-010**: System MUST generate recommendations at session creation, scale quantities by `Household_Size`, use only items currently in stock, and show a rationale for each.
- **FR-011**: Restricted items and out-of-stock items MUST NEVER appear in recommendations.
- **FR-012**: Clients MUST be able to scan a barcode with a smartphone camera or enter a SKU manually, and see nutrition facts, the product image when available, status, and explanation.

**Cart and recipes**
- **FR-013**: Clients MUST be able to add, remove, and change quantity of cart items, view the cart live, and keep it through the session.
- **FR-014**: System MUST send the `Active_Cart_Manifest` and current inventory to the AI recipe service, prefer available inventory, and identify missing ingredients with their warehouse locations.
- **FR-015**: System MUST validate all recipe output with the rules engine before display, MUST validate AI output against a defined structure, and MUST never show Restricted ingredients.
- **FR-016**: System MUST provide a deterministic fallback when AI output is unavailable or invalid.

**Checkout and inventory**
- **FR-017**: Volunteers MUST be able to validate a cart at checkout, loading it from the client's QR code or client ID. An item Restricted for the whole household MUST cause a hard stop (removal, or a logged Warehouse Manager override with a reason). An item matching any member's allergy MUST require a logged volunteer acknowledgement. A Pending account MUST NOT complete checkout. Volunteer additions and removals MUST be recorded. *(Amended 2026-11-14.)*
- **FR-018**: A successful checkout MUST generate a receipt and decrement all affected inventory atomically.
- **FR-019**: Warehouse staff MUST be able to scan a product, view its quantity, enter a counted quantity, and have the system calculate the variance, store an audit event, and update inventory.
- **FR-020**: System MUST detect items below threshold and produce a replenishment list showing aisle, shelf, and bin, sortable by priority.
- **FR-021**: System MUST track expiration dates, order lots by FIFO, flag items expiring within seven days, and show a dashboard warning.

**Analytics and reporting**
- **FR-022**: System MUST show families served, visits completed, pounds distributed, inventory usage, recommendation adoption rate, and waste-reduction metrics, all anonymized.
- **FR-023**: Management MUST be able to generate a report from a template and export it as DOCX with donor metrics, grant attribution, food distribution totals, and visit metrics.

**Deployment**
- **FR-024**: System MUST be publicly accessible on Azure at a stable URL with a hosted database and working authentication, and MUST demonstrate the core journey live.

**Out of scope**: Facial recognition check-in, computer-vision cart tracking, camera-based shelf tracking, automated pickup detection, multi-language support, advanced health outcome biometrics, and warehouse camera analytics.

### Key Entities

- **Client**: an enrolled person with `Client_Enrollment_Status`, `Household_Size`, and a dietary profile.
- **Dietary Profile**: restrictions, allergies, preferences, and the assigned `Dietary_Tier_ID`.
- **Shopping Session**: a visit identified by `Shopping_Session_Token`, owning one cart.
- **Product**: SKU or barcode, nutrition facts, image, and category.
- **Inventory Lot**: a quantity of a product with expiration date, threshold, and aisle/shelf/bin location.
- **Cart / Active_Cart_Manifest**: the items and quantities a client has chosen in a session.
- **Recommendation**: a suggested product with quantity and rationale.
- **Recipe Suggestion**: a validated recipe with in-stock and missing ingredients and their locations.
- **Checkout Receipt**: the record of a completed checkout and its items.
- **Audit Event**: a recorded count, with expected and counted quantities and the variance.
- **User / Role**: a person who logs in and the role that sets their access.
- **Report**: a generated donor or grant document built from anonymized data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A client can go from login to seeing personalized recommendations in under 1 minute.
- **SC-002**: A scan or manual SKU entry shows product status and nutrition in under 3 seconds.
- **SC-003**: Zero Restricted items appear in any recommendation, recipe, or successfully completed checkout across all test scenarios.
- **SC-004**: 100% of recipe suggestions are validated by the rules engine before being shown, and 100% of invalid AI responses fall back to a safe result.
- **SC-005**: Inventory after any checkout equals the prior quantity minus the checked-out quantity, with no partial updates in failure tests.
- **SC-006**: Every audit count produces a stored event, and variances are calculated correctly in 100% of test cases.
- **SC-007**: 100% of items expiring within seven days are flagged and 100% of below-threshold items are listed for replenishment.
- **SC-008**: Every role can reach all of its screens, and 100% of out-of-role attempts are denied.
- **SC-009**: Analytics views and exports contain no client-identifying information.
- **SC-010**: A DOCX report with all four required sections can be generated in under 2 minutes.
- **SC-011**: The full MVP Success Scenario, login through manager report, completes live on the public URL without manual database changes.

## Assumptions

- Clients use a smartphone with a camera and a standard browser; manual SKU entry is always available.
- Synthetic data only is used for clients, products, and inventory (designed with HIPAA safeguards).
- Product nutrition data comes from a lookup source plus local inventory data; items without data fall back to the safest rules outcome.
- Rules thresholds and the tier mapping are defined by the team from Epic Cure guidance before implementation.
- A single warehouse location is in scope.
- NICE stories and all out-of-scope items are not planned until every MUST story passes.
- Any AI use runs in development and deployment as defined in the project constitution. The specifics belong to the plan.
