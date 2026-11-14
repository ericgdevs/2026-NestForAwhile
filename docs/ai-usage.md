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
| Install | Copilot | Installed Agentation as a development dependency | Caden approved the dependency installation | Caden |
| Install | Copilot | Installed Ponytail as a development dependency | Caden approved the dependency installation | Caden |
| Install | Copilot | Installed Impeccable globally for design skills and added the project hook | Caden selected global scope | Caden |
| Review fix | Copilot | Documented the required Impeccable global setup instead of committing a platform-specific engine | Kept the portable global hook | Caden |
| Implement T001 | Copilot (GPT-5.6 Terra) | Created the backend, frontend, e2e, deploy, and scripts skeleton directories and verified required ignore patterns | None | Caden |
| Implement T004 | Copilot (GPT-5.6 Terra) | Added the documented environment-variable template with placeholders only | None | Caden |
| Implement T005 | Copilot (GPT-5.6 Terra) | Added pull-request backend CI for Ruff and pytest | None | Caden |
| Implement T006 | Copilot (GPT-5.6 Terra) | Added pull-request frontend lint, typecheck, Vitest, and build checks | None | Caden |
| Implement T007 | Copilot (GPT-5.6 Terra) | Added hygiene CI that rejects tracked .env files and the prohibited compliance claim | None | Caden |
| Implement T021 | Copilot (GPT-5.6 Terra) | Added the versioned clinical rules matrix with synthetic nutrient thresholds and dietary/allergen exclusions | None | Caden |
| Implement T022 | Copilot (GPT-5.6 Terra) | Implemented deterministic dietary tier mapping and product classification with table-driven tests | None | Caden |
| Implement T002 | Copilot (GPT-5.6 Terra) | Initialized the FastAPI backend, approved dependency manifest, health endpoint, Ruff configuration, and pytest configuration | None | Caden |
| Implement T003 | Copilot (GPT-5.6 Terra) | Initialized the React/Vite/TypeScript frontend with Tailwind, shadcn configuration, Vitest, and a shell test | None | Caden |
| Implement T008 | Copilot (GPT-5.6 Terra) | Added Playwright local/deployed projects and role-based synthetic credential login fixture | None | Caden |
| Implement T010 | Copilot (GPT-5.6 Terra) | Added CODEOWNERS using the supplied team handles and a pull request template with task, stream, review, and validation fields | None | Caden |
