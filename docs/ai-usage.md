# How we used AI across the whole lifecycle

| Stage | Tool / model | What it did | What we changed by hand | Who |
|---|---|---|---|---|
| Planning | Gemini (notebook) | | | Eric |
| Spec | Spec Kit in Copilot | | | Eric |
| Build | Copilot agent | | | |
| Review | Ponytail review / Copilot code review | | | |
| Testing & debugging | Copilot | | | |
| In the product | Local open-source model (Ollama) | | | |
| Plan | Copilot (GPT-5.6 Terra) | Updated finalized AI deployment architecture: local Ollama, Groq free-tier open-weight inference in Azure, and deterministic rules-only fallback | Eric supplied and approved the architecture decision | Eric |
| Tasks | Copilot (Sonnet 5.5) | Generated tasks.md (99 one-PR tasks by stream, shared-file ownership, Playwright per story, CI, deploy, OFF/USDA, Groq/Ollama, AI eval, US-1.3) | Eric supplied architecture, stream split, and task rules; review pending | Eric |
| Plan | Copilot (Sonnet 5.5) | Replaced stale HPC step in quickstart.md with Groq deployment config | None | Eric |
| Plan | Copilot (GPT-5.6 Terra) | Removed stale HPC deployment task path after final architecture verification | None | Eric |
| Plan | Copilot (Sonnet 5.5) | Drafted plan, research, data model, OpenAPI + AI schemas, quickstart from spec, Eric's addendums, and unf-hpc-guide.md (Ollama on HPC, no Groq) | Eric supplied architecture decisions and the HPC guide; reviewed plan | Eric |
| Spec (specify) | Copilot (Sonnet 5.5) | Drafted spec.md (14 stories, 24 FRs, 11 success criteria) and quality checklist from Eric's stories | Eric supplied all stories; reviewed and approved the plan | Eric |
| Spec (constitution) | Copilot (Sonnet 5.5) | Drafted constitution v1.0.0 from Eric's principles; filled plan-template Constitution Check | Eric supplied all principles and rules; reviewed draft | Eric |
| Implement (T024) | Copilot (Sonnet 5.5) | Added OpenAPI type generation and a cookie-aware typed fetch client with mocked error handling tests | Caden approved the dependency and reviewed the generated contract output | Caden |
| Implement (T035) | Copilot (Sonnet 5.5) | Added the plain-language dietary profile page with mock saved-state feedback and selection tests | Caden reviewed the UI copy and choice list | Caden |
| Implement (T038) | Copilot (Sonnet 5.5) | Added realistic mock recommendations with deterministic rationale and accessible status labels | Caden reviewed the recommendation copy | Caden |
| Implement (T043) | Copilot (Sonnet 5.5) | Added an iOS-Safari-compatible ZXing scanner with a mandatory manual SKU fallback | Caden selected and approved @zxing/browser | Caden |
| Implement (T044) | Copilot (Sonnet 5.5) | Added the scan page with synthetic safety results, explanations, nutrition facts, and unknown-code handling | Caden reviewed the mock product data | Caden |
| Implement (T047) | Copilot (Sonnet 5.5) | Added a shared mock cart with quantity controls, removal, and add-to-cart actions from recommendations and scans | Caden reviewed the cart interaction scope | Caden |
| Implement (T061) | Copilot (Sonnet 5.5) | Added inventory-aware mock recipes with fallback messaging and aisle/shelf/bin locations | Caden reviewed the fallback UX and synthetic ingredient data | Caden |
| Implement (T065) | Copilot (Sonnet 5.5) | Added volunteer checkout review, session-token validation UI, hard-stop intervention, and receipt state | Caden reviewed the mock checkout flow | Caden |
| Implement (T068) | Copilot (Sonnet 5.5) | Added role-aware navigation and protected route access using the contract’s five roles | Caden reviewed the role-to-screen mapping | Caden |
| Implement (T076) | Copilot (Sonnet 5.5) | Added the warehouse audit flow with scanner reuse, variance calculation, and confirmation state | Caden reviewed the mock inventory count | Caden |
| Implement (T082) | Copilot (Sonnet 5.5) | Added synthetic inventory lots with expiration status and an expiring-soon dashboard warning | Caden reviewed the warehouse warning copy | Caden |
