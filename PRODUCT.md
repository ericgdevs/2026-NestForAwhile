# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Clients** (primary): enrolled Epic-Cure clients with medically tailored dietary needs, shopping in the warehouse on their own phones. They may be older, have low vision, or be less comfortable with technology. Jobs: sign in, see recommended groceries, scan a product to learn if it is safe for them, build a cart, get recipe ideas.
- **Volunteers**: run checkout on a phone, tablet, or laptop; validate the cart and handle hard stops on Restricted items.
- **Warehouse Staff / Warehouse Manager**: count stock (audit), restock low items, rotate lots (FIFO), watch floor capacity. Phone, tablet, or laptop.
- **Director / Warehouse Manager**: review anonymized analytics and download donor/grant DOCX reports.

## Product Purpose

A Medically Tailored Grocery (MTG) warehouse system for Epic-Cure. It joins warehouse operations (system of record) with dietary safety and AI recipe ideas (system of intelligence): each visit updates inventory and metrics, and those feed the next visit's recommendations. Success: a client goes from login to safe, personalized recommendations in under a minute, and no Restricted item ever reaches a completed checkout.

## Positioning

Every product is classified Approved (Green), Capped (Yellow), or Restricted (Red) for the specific client by deterministic rules, never by AI; AI only suggests recipes, which the rules re-check before display.

## Operating Context

- Clients walk warehouse aisles holding a phone, scanning barcodes with the camera or typing a SKU.
- Checkout happens at a desk with a volunteer entering the client's session token.
- Staff move between shelves (aisle / shelf / bin locations) and a desk.
- The system is demoed live to judges on a public Azure URL.

## Capabilities and Constraints

- Roles: Client, Volunteer, Warehouse Staff, Warehouse Manager, Director; the server enforces permissions and each role sees only its screens.
- Screens: Login, Home (recommendations), Profile (dietary choices), Scan, Cart, Recipes, Waiting (capacity queue), Checkout, Audit, Replenishment, Lots (FIFO), Analytics, Reports.
- Terminology from the organizers is fixed: `Client_Enrollment_Status`, `Household_Size`, `Dietary_Tier_ID`, `Shopping_Session_Token`, `Active_Cart_Manifest`, `Active_Floor_Shoppers`.
- Stack: React + Vite + TypeScript, FastAPI backend; API contract in `specs/001-mtg-warehouse-system/contracts/openapi.yaml`.
- Out of scope: multi-language, facial recognition, camera analytics.

## Brand Commitments

- Name: **Epic-Cure** (product descriptor: MTG Warehouse).
- Primary brand color: **blue** (confirmed by the team lead for the UI, 2026-11-14).
- Wording is friendly, plain, and non-clinical, and preserves client choice.

## Evidence on Hand

- All clients, products, and inventory are synthetic (`@example.test`). No real client or health data may appear anywhere, including screenshots.
- No logo file exists; do not invent one beyond a wordmark.
- No testimonials, customer counts, or outcome claims exist; do not fabricate them.

## Product Principles

1. Safety status is always shown with icon and words, never color alone.
2. The client's phone journey (scan → status → cart) is the fastest path in the app.
3. Each role sees only what it can act on.
4. Plain language over clinical language.

## Accessibility & Inclusion

WCAG 2.2 AA: 4.5:1 text contrast, 44px minimum touch targets, visible focus, status never conveyed by color alone.
