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
