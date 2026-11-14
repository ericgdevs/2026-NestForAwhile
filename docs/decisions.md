# Decisions log

Every decision the team makes: what we decided, who decided it, why, and which AI suggested what.

| When | Decision | Who | Why | AI input (tool → suggestion → what we kept or changed) |
|---|---|---|---|---|
| Sat 9:30 | Chose the EPIC Cure "Medically Tailored Groceries" case | Team | | Gemini: |
| 2026-11-14 | Add Agentation as a development dependency | Caden | Enable Agentation in this repository | Copilot web search -> recommended the official npm package -> kept |
| 2026-11-14 | Add Ponytail as a development dependency | Caden | Make Ponytail available in this repository | Copilot web search -> recommended the official npm package -> kept |
| 2026-11-14 | Install Impeccable globally with Copilot integration | Caden | Make design skills available across projects | Copilot web search -> recommended global installation -> kept |
| 2026-11-14 | Document Impeccable setup instead of committing its engine | Caden | Avoid a platform-specific 20 MB binary in the repository | Ponytail review -> identified non-reproducible global setup -> kept documentation fix |
| 2026-11-14 | Keep the approved SQLAlchemy implementation during PR conflict resolution | Caden | Main contained an incompatible SQLModel scaffold and tests | Copilot review -> identified the architecture clash -> kept the feature branch implementation |
| 2026-11-14 | Integrate Agentation into the frontend development build | Caden | Enable visual annotations while designing the UI without shipping the toolbar to production | Copilot -> recommended a dev-only React integration -> kept |
| 2026-11-14 | Render the sign-in form for all unauthenticated routes | Caden | The prior placeholder redirected the URL without triggering a React rerender, leaving a blank sign-in state | Copilot -> identified the stale render path -> kept |
| 2026-11-14 | Use a warm cream, charcoal, and coral nutrition-app visual system | Caden | Match the supplied visual references while keeping the warehouse flows and accessibility semantics intact | Impeccable-inspired design pass -> kept the palette, rounded cards, and bottom navigation while using original UI code |
| 2026-11-14 | Add a staff-guided Create Account action on login | Caden | Self-service enrollment is not implemented, so the button explains the current safe path | Agentation feedback -> requested the button -> kept with staff guidance |
| 2026-11-14 | Apply modern dashboard layout with multi-stop ambient shadows and pastel chips | Caden | Provide a user-friendly, professional visual hierarchy guided by reference designs | Impeccable -> recommended multi-stop ambient shadows, pastel stat chips, and hybrid header-canvas architecture -> kept |
| 2026-11-14 | Redesign the UI in the "Nutrition Facts Panel" direction (ink rules, Archivo, Epic-Cure blue, WCAG 2.2 AA) | Caden | Professional, plain-language UI that clients on phones and staff on any device can use; status never shown by color alone | Impeccable direction roll → offered Community Cookbook, Nutrition Facts Panel, Ticket Wallet, and the category standard → Caden chose Nutrition Facts Panel |
| 2026-11-14 | Show recipes in a bottom sheet grouped by cuisine with a top pick per cuisine; identify clients by ID/household, never by name | Caden | Recipes must respect diet restrictions and current inventory; privacy | Caden steer on the decision page; Copilot → proposed the contract change in docs/proposals instead of editing the shared contract → kept |
| 2026-11-14 | Caden may make backend changes on a separate `api/*` branch, logged in docs/proposals/backend-changes-log.md, for Aditya/Eric to review and merge | Caden | Caden owns the UI only; backend owners keep the final say | Copilot → suggested a separate worktree branch so UI and backend changes stay apart → kept |
| 2026-11-14 | Cart responses include nutrition facts and rules-engine status per item (no outside lookups) | Caden | The cart page shows each item's label | Copilot → reused the scan rules path offline → pending Aditya review |
