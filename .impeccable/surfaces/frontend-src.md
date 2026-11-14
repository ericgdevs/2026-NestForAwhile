---
version: 1
slug: "frontend-src"
primary_target: "frontend/src"
related_targets: []
---

# Surface: Epic-Cure app (all roles)

Mode: Operate. Clients on phones (primary); volunteers/staff on phone, tablet, or laptop.
Job: clients find safe groceries and recipes fast; staff run checkout, audit, restock, FIFO; management reads metrics and exports reports.
Constraints: Epic-Cure name + blue brand; WCAG 2.2 AA; status never color-only; no names (IDs/household only); synthetic data.
Unresolved: cuisine field and ingredient locations need backend (see docs/proposals/recipe-cuisine-contract.md).

## Direction contract

THESIS: The Nutrition Facts label is the grammar: heavy, medium and hairline rules rank every fact, so the screen reads like the label everyone already trusts. Refuses the gray-SaaS card grid with pastel icon tiles.
OWN-WORLD: Ink #0B1B33 shell (sidebar ≥1024px, top bar below), cool ground #F1F4F9, white panels with a 2px ink border on product panels and layered soft shadows elsewhere; Epic-Cure blue #1F5FBF only for current nav and the primary action; Archivo 400/700/900; status bar in words + icon at the top of every product panel.
STORY: The client sees picks sized for their household, each safe-or-not in words, scans to confirm, adds to cart, and recipe ideas rise from the bottom grouped by cuisine. Staff see the one number that needs action first.
FIRST VIEWPORT: Phone: ink top bar (wordmark, role, sign out); page title over a 10px rule; household figure as the "Calories" number; recommendation panels; recipe sheet handle docked above the bottom tab bar. Desktop: ink sidebar nav left, same content in a 2-column grid.
FORM: Nutrition Facts Panel, Impeccable's pick (list position 1), seed:6ed0ae4ece57868c.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
