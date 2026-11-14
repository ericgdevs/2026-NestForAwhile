---
name: Epic-Cure MTG Warehouse
description: A grocery-safety and warehouse app set like a Nutrition Facts label; ink rules rank facts, blue marks where you are and what to do.
colors:
  blue: "#1f5fbf"
  blue-hover: "#184c99"
  blue-wash: "#e8f0fc"
  ink: "#0b1b33"
  ink-2: "#1a2b47"
  ink-soft: "#a9b6cc"
  ground: "#f1f4f9"
  panel: "#ffffff"
  muted: "#4a5874"
  line: "#d5dce8"
  field-line: "#7a8699"
  ok-bg: "#e3f1e6"
  ok-ink: "#174a27"
  warn-bg: "#fff4cc"
  warn-ink: "#6b4a00"
  stop-bg: "#fbe4e4"
  stop-ink: "#8a1c1c"
typography:
  display:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "clamp(1.75rem, 1.4rem + 1.6vw, 2.5rem)"
    fontWeight: 900
    lineHeight: 1.05
    letterSpacing: "-0.03em"
  figure:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "tnum"
  headline:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 900
    lineHeight: 1.1
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 900
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 700
  label:
    fontFamily: "Archivo, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 700
rounded:
  sm: "6px"
  md: "10px"
  lg: "14px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  base: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.panel}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "48px"
  button-primary-hover:
    backgroundColor: "{colors.blue-hover}"
  button-secondary:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 18px"
    height: "48px"
  button-secondary-hover:
    backgroundColor: "{colors.ground}"
  button-done:
    backgroundColor: "{colors.ok-bg}"
    textColor: "{colors.ok-ink}"
    rounded: "{rounded.md}"
    height: "48px"
  input:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    padding: "0 14px"
    height: "48px"
  label-panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "12px 14px 14px"
  panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "20px"
  status-approved:
    backgroundColor: "{colors.ok-bg}"
    textColor: "{colors.ok-ink}"
    rounded: "{rounded.pill}"
    padding: "4px 10px"
  status-capped:
    backgroundColor: "{colors.warn-bg}"
    textColor: "{colors.warn-ink}"
    rounded: "{rounded.pill}"
    padding: "4px 10px"
  status-restricted:
    backgroundColor: "{colors.stop-bg}"
    textColor: "{colors.stop-ink}"
    rounded: "{rounded.pill}"
    padding: "4px 10px"
  nav-item:
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.md}"
    padding: "0 14px"
    height: "44px"
  nav-item-active:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.panel}"
  tag:
    backgroundColor: "{colors.blue-wash}"
    textColor: "{colors.blue}"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
---

# Design System: Epic-Cure MTG Warehouse

## Overview

**Creative North Star: "The Nutrition Facts Label"**

Every screen reads like the label on the back of a grocery package, the one format clients already trust to tell them what is in their food. Facts are ranked by rule weight rather than by boxes and color: a heavy ink rule sits under every page title and product name, a medium rule opens each section, and hairlines separate one fact from the next. The decisive number on a screen (household size, picks in stock, items to restock) is set huge and black like the Calories line.

The world is a deep ink shell around a cool pale ground. Navigation lives in the ink: a sidebar at laptop width, a top bar on phones, and a bottom tab bar for clients. Content sits on white panels. Product panels are the label itself, with a 2px ink border; everything else floats on soft layered shadows. Epic-Cure blue is rare on purpose: it marks where you are and what to do next, never whether a food is safe.

Density is calm and touch-first. Clients may be older or have low vision, so targets are at least 44px, body text is 16px, and status always comes as an icon plus plain words. The system refuses the gray SaaS card grid with pastel icon tiles.

**Key Characteristics:**
- Ink rules at three weights (10px, 5px, 1px) carry the hierarchy.
- One family, Archivo, at three weights (400, 700, 900); headings and figures at 900 with tight tracking.
- Blue only for current location, selection and the primary action.
- Status in three tints (green, yellow, red) always with an icon and words.
- Phone-first; the client's scan-to-cart path is the fastest route.

## Colors

A near-black navy ink and a cool white ground, one confident blue for action, and three soft status tints that never carry meaning alone.

### Primary
- **Epic-Cure Blue** (blue): the primary button, the current nav item, the selected profile choice, the active tab underline, links, text selection and the 3px focus ring. It means "you are here" or "do this".
- **Pressed Blue** (blue-hover): hover state of the primary button only.
- **Blue Wash** (blue-wash): quiet backing for selected choices, the info alert, the "Recommended for you" tag and the recipe top-pick bar.

### Neutral
- **Label Ink** (ink): all body text, every label rule, the product panel border, and the app shell (sidebar, top bar on phones, login brand side).
- **Shell Ink Raised** (ink-2): the staff nav row under the phone top bar and the sign-out hover inside the ink shell.
- **Ink Mist** (ink-soft): resting nav text and secondary text on ink; never on white.
- **Cool Ground** (ground): the page background, secondary-button hover, media backing.
- **Panel White** (panel): panels, inputs, the tab bar and the recipe sheet.
- **Slate Note** (muted): supporting copy, page subtitles, meta lines, placeholders, resting tab bar items.
- **Soft Line** (line): non-label dividers only: table row lines, the tab strip baseline, "or" dividers.
- **Field Line** (field-line): 1px borders on inputs, steppers, choices, and the desktop sign-out button.

### Status
- **Good match** (ok-bg on ok-ink): Approved status, success alerts, the "Added to cart" confirmation.
- **Please check** (warn-bg on warn-ink): Capped status and warning alerts.
- **Not recommended** (stop-bg on stop-ink): Restricted status, hard stops and error alerts.

### Named Rules
**The Blue Means Go Rule.** Blue marks location, selection and the next action. It never signals safety; safety belongs to the three status tints.

**The Words-First Status Rule.** Every status shows an icon and a plain-language label ("Good match", "Please check", "Not recommended"). Color is the third signal, never the only one.

## Typography

**Display Font:** Archivo variable (self-hosted woff2, weights 400 to 900; with -apple-system, Segoe UI, Roboto, sans-serif)
**Body Font:** Archivo
**Label/Mono Font:** Archivo; numbers use tabular figures.

**Character:** A sturdy grotesque that holds up at 900 for label-style headings and stays plain and readable at 400 for body copy. One family keeps the label feel honest.

### Hierarchy
- **Display** (900, fluid 28px to 40px, 1.05): page titles over the heavy rule; login heading at a fixed 32px.
- **Figure** (900, 40px, 1, tabular): the one decisive number in a page head. Inline figure rows inside panels use 36px.
- **Headline** (900, 22px, 1.1): product and recipe names on label panels, panel titles over a heavy rule.
- **Title** (900, 20px): headings inside plain panels.
- **Body** (400, 16px, 1.5): running text; page subtitles cap at 60ch.
- **Body small** (700, 15px): fact rows, table cells, field labels, alerts, rationale text.
- **Label** (700, 13px): tab bar labels, role tag, tags, table headers (900). Sentence case, no tracking.

### Named Rules
**The Calories Line Rule.** Each page gets at most one oversized figure, set at 900 with tabular numbers, beside a short muted unit ("people in your household").

**The Three Weights Rule.** Only 400, 700 and 900. Hierarchy comes from weight and rules, not from extra sizes or colors.

## Layout

Phone-first single column inside a centered container (max 1200px, 16px gutters, 24px top padding). Spacing follows a 4px base with common steps of 4, 8, 12, 16, 24 and 32px; card grids use a 16px gap.

- **Below 1024px:** sticky ink top bar (wordmark, role, sign out). Staff get a wrapping nav row under it; clients get a fixed five-item bottom tab bar (56px items, safe-area padding) and extra bottom padding so content clears the bar and recipe sheet.
- **At 1024px and up:** a 248px sticky ink sidebar holds the wordmark and nav; the top bar moves onto the ground and turns light; content gets 32px side padding.
- **Grids:** two and three columns from 720px; auto grids go two columns from 720px and three from 1280px.
- **Tables:** below 640px each row becomes a stacked label block with the column name on the left, ruled by an ink hairline.
- **Login:** an ink top bar with the wordmark over a centered 420px form panel at every width.

## Elevation & Depth

A hybrid: the label panels get a structural ink border and a medium shadow, plain panels float on a soft ambient shadow with no border. All shadows are tinted with the ink color, never neutral black, and are layered (a tight contact shadow plus a wide soft one).

### Shadow Vocabulary
- **Resting** (`0 1px 2px rgba(11,27,51,0.06), 0 6px 16px -6px rgba(11,27,51,0.12)`): plain panels.
- **Raised** (`0 2px 4px rgba(11,27,51,0.06), 0 16px 32px -12px rgba(11,27,51,0.24)`): product label panels and the login form.
- **Lifted** (`0 4px 8px rgba(11,27,51,0.08), 0 28px 56px -16px rgba(11,27,51,0.34)`): the top recipe pick, the recipe sheet.
- **Primary glow** (`0 1px 2px rgba(11,27,51,0.12), 0 6px 14px -6px rgba(31,95,191,0.6)`): the primary button only.
- **Tab bar** (`0 -10px 28px -14px rgba(11,27,51,0.3)`): upward shadow on the fixed client tab bar.

### Named Rules
**The Lift Means Priority Rule.** A heavier shadow means more important, not more interactive. Only the top recipe pick and floating surfaces use the lifted level.

## Shapes

Gently rounded and restrained. Product label panels and status bars use the tightest corners (6px) so they still read as a printed label; buttons, inputs, choices and nav items use 10px; plain panels, the login form and the top of the recipe sheet use 14px. Status badges are full pills. Rules are flat ink bars with no rounding. Icons are one authored 24px stroke set (1.75 stroke, round caps and joins), thickening to 2.25 to 2.5 for active tabs and status.

## Components

### Buttons
- **Shape:** gently curved (10px), 48px tall, 18px side padding, 2px border slot, 16px bold text, icon gap 8px.
- **Primary:** blue fill, white text, primary glow shadow; hover moves to pressed blue. 160ms ease-out color transition.
- **Secondary:** white with a 2px ink border and ink text; hover fills with the ground color.
- **Done:** green tint with "Added to cart" and a check icon, shown for 2 seconds after adding.
- **Disabled:** 55% opacity, not-allowed cursor.
- **Focus:** 3px blue outline at 2px offset (global).

### Status Badge and Status Bar
- **Badge:** pill, 4px by 10px, 14px weight-900 text, 16px icon at heavy stroke. Check for Good match, warning triangle for Please check, cross for Not recommended.
- **Bar:** the same badge stretched full width with 6px corners as the first line of every product label panel.

### Cards / Containers
- **Label panel (signature):** white, 2px ink border, 6px corners, raised shadow, 12px to 14px padding. Order: status bar, name (headline), heavy rule, figure row, medium rule, location line with pin icon, rationale, action button pinned to the bottom.
- **Plain panel:** white, 14px corners, resting shadow, 20px padding, no border.
- **Facts list:** label/value rows split left and right, 5px vertical padding, 1px ink hairline between rows, labels at 900 and values at 700 tabular.

### Inputs / Fields
- **Style:** white, 1px field-line border, 10px corners, 48px tall, 14px side padding; label above at 15px bold.
- **Focus:** 3px blue outline at 0 offset and blue border.
- **Choices:** 56px rows with a 20px native checkbox in blue; checked choice gets a 2px blue border and blue wash.
- **Stepper:** bordered 48px minus/plus buttons with a weight-900 tabular count.
- **Password field:** a 44px show/hide eye button inside the right edge.

### Navigation
- **Sidebar / nav row:** 44px items, 10px corners, bold 15px text in ink mist with an icon; hover lightens to white on a faint white wash; current page is a solid blue item with white text.
- **Client tab bar:** fixed bottom, five equal items 56px tall with icon over a 13px label; current item turns blue with a heavier icon stroke.
- **Tabs (recipe cuisines):** text buttons with a 4px bottom bar that turns blue when pressed; soft line baseline.

### Alerts
- Full-width blocks with 10px corners, 14px by 16px padding, bold 15px text and a leading icon. Info uses blue wash on ink; warn, danger and ok use the status tints.

### Recipe Sheet (signature)
- A bottom sheet docked above the client tab bar, 14px top corners, lifted shadow. The 64px handle has a 5px ink rule under it. It slides up in 420ms with the ease-out curve and the chevron flips; when closed its body is hidden from focus and screen readers. This is the one authored motion in the app.

### Tables
- Header cells at 13px weight 900 over a 5px ink rule; body rows 12px padding with a soft line; numbers right-aligned and tabular. Expiring rows get a pale yellow backing.

## Do's and Don'ts

### Do:
- **Do** put a 10px ink rule under every page title and product name, a 5px rule above sections and table headers, and 1px ink hairlines between facts.
- **Do** show every safety status as icon plus words, using only the three status tints.
- **Do** keep touch targets at 44px minimum; buttons and inputs at 48px.
- **Do** use tabular figures for every quantity, count, location and table number.
- **Do** keep blue for the current nav item, selection, links, focus and the primary action.
- **Do** honor reduced motion; transitions collapse to near zero.

### Don't:
- **Don't** use blue, or any color alone, to say whether a product is safe.
- **Don't** build gray SaaS card grids with pastel icon tiles; facts go in labelled rows under ink rules.
- **Don't** add uppercase eyebrows or tracked kicker labels above headings.
- **Don't** add a fourth font weight, a second typeface, or icon fonts; use the authored stroke icon set.
- **Don't** put ink-mist text on white; it is only for text on the ink shell.
- **Don't** invent a logo; the brand is the "Epic-Cure" wordmark with the "MTG Warehouse" descriptor.
