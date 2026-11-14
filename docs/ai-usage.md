# How we used AI across the whole lifecycle

| Stage | Tool / model | What it did | What we changed by hand | Who |
|---|---|---|---|---|
| Planning | Gemini (notebook) | | | Eric |
| Spec | Spec Kit in Copilot | | | Eric |
| Build | Copilot agent | | | |
| Review | Ponytail review / Copilot code review | | | |
| Testing & debugging | Copilot | | | |
| In the product | Local open-source model (Ollama) | | | |
| Implement | Copilot (Sonnet 5.5) | T017: Alembic init + migration 0001 for all tables, upgrade-head test | Fixed generated migration import by hand | Eric |
| Implement | Copilot (Sonnet 5.5) | T013-T016: SQLModel tables (incl. DietaryTier, ClinicalRule, InventoryLocation, DonationSource, GrantFundingStream) with official field names, Pydantic schemas, model test | None | Eric |
| Implement | Copilot (Sonnet 5.5) | T011/T012: config, db engine (SQLite/PostgreSQL), Fernet EncryptedText, deps, .env.example | None | Eric |
| Plan | Copilot (GPT-5.6 Terra) | Updated finalized AI deployment architecture: local Ollama, Groq free-tier open-weight inference in Azure, and deterministic rules-only fallback | Eric supplied and approved the architecture decision | Eric |
| Tasks | Copilot (Sonnet 5.5) | Generated tasks.md (99 one-PR tasks by stream, shared-file ownership, Playwright per story, CI, deploy, OFF/USDA, Groq/Ollama, AI eval, US-1.3) | Eric supplied architecture, stream split, and task rules; review pending | Eric |
| Plan | Copilot (Sonnet 5.5) | Replaced stale HPC step in quickstart.md with Groq deployment config | None | Eric |
| Plan | Copilot (GPT-5.6 Terra) | Removed stale HPC deployment task path after final architecture verification | None | Eric |
| Plan | Copilot (Sonnet 5.5) | Drafted plan, research, data model, OpenAPI + AI schemas, quickstart from spec, Eric's addendums, and unf-hpc-guide.md (Ollama on HPC, no Groq) | Eric supplied architecture decisions and the HPC guide; reviewed plan | Eric |
| Spec (specify) | Copilot (Sonnet 5.5) | Drafted spec.md (14 stories, 24 FRs, 11 success criteria) and quality checklist from Eric's stories | Eric supplied all stories; reviewed and approved the plan | Eric |
| Spec (constitution) | Copilot (Sonnet 5.5) | Drafted constitution v1.0.0 from Eric's principles; filled plan-template Constitution Check | Eric supplied all principles and rules; reviewed draft | Eric |
