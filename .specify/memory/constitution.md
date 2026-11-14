<!--
Sync Impact Report
Version change: (template) → 1.0.0
Modified principles: none (initial ratification)
Added sections: Core Principles (I–VI), Technical Rules, Team Collaboration Rules,
  MVP Scope Guardrail, Governance
Removed sections: none
Templates:
  ✅ .specify/templates/plan-template.md (Constitution Check gates filled)
  ✅ spec-template.md, tasks-template.md (no change needed)
Follow-up TODOs: none
-->

# Nest For Awhile Constitution

**Mission**: Build a lightweight but complete Medically Tailored Grocery (MTG) warehouse system
that demonstrates a full System of Record ↔ System of Intelligence data loop for Epic Cure, with
a live cloud deployment, clinically safe recommendations, warehouse inventory operations, and
AI-assisted recipe generation.

## Core Principles

### I. Simplest Working Solution Wins
- Working, demonstrable functionality MUST be preferred over broad scope.
- A deployed end-to-end workflow outranks extra features.
- Complexity MUST be cut before reliability is cut.

### II. User Stories Are the Source of Truth
- Official user stories and use cases define required functionality.
- Required variable names MUST NOT be renamed.
- Enhancements MUST NOT conflict with official requirements.

### III. Rules First, AI Second
- Approved / Capped / Restricted decisions MUST come only from deterministic rules.
- AI provides recipes, explanations, substitutions, and recommendations only.
- AI MUST NOT override clinical guardrails.
- Final rules validation MUST run before any user-facing output.

### IV. Warehouse Realism
- Recommendations MUST use actual inventory data; recipes prioritize in-stock ingredients.
- Checkout MUST update inventory atomically.
- Inventory operations MUST support counting, replenishment, FIFO, and auditability.

### V. Dignity-First Experience
- Use friendly, non-clinical language where possible; show dietary restrictions and
  preferences in plain language.
- Clients keep their choice. Recommendations support users and MUST NOT remove autonomy.

### VI. Documentation Is a Feature
- Every planning step MUST be committed and every major decision recorded in
  `docs/decisions.md`.
- AI usage MUST be documented throughout the SDLC in `docs/ai-usage.md`.
- Process evidence is as important as application functionality.

## Technical Rules

**Approved stack**
- Frontend: React + Vite + TypeScript. UI: Tailwind CSS + shadcn/ui.
- Backend: FastAPI + Pydantic.
- Database: PostgreSQL in Azure; SQLite for local development.
- OpenAPI-generated types are the contract boundary.
- Core stack components MUST NOT be replaced without team approval.

**AI architecture**
- Development uses Ollama; deployment uses an open-weight model hosted through UNF HPC.
- AI outputs MUST use structured JSON schemas and be validated before use.
- Deterministic fallback behavior is REQUIRED.

**Security and privacy**
- No secrets in source control; `.env` and `.env.example` are REQUIRED.
- Passwords MUST be hashed with Argon2; authorization is server-side only.
- PHI-related fields MUST be encrypted at rest; analytics MUST be anonymized.
- Use the phrase "designed with HIPAA safeguards", never "HIPAA compliant".

**Testing**
- Every feature requires automated tests; a failing test MUST NOT be removed to pass CI.
- Every MUST story receives Playwright coverage.
- Verification MUST include AI evaluation scenarios and edge cases; no vibe-checking AI output.

## Team Collaboration Rules

- **Roles**: Caden owns UI. Aditya owns API and data. Eric owns AI, QA, deployment,
  integration, and documentation. Shared files require coordination.
- **Small PRs**: one task or small task group per PR; review before merge; merge commits only,
  never squash; preserve commit history as judging evidence.
- **Explainability**: every teammate MUST be able to explain every feature. Avoid unnecessary
  abstraction; prefer readability over cleverness; keep files and functions simple.

## MVP Scope Guardrail

- **MVP first**: client login and check-in; dietary restrictions and preferences; barcode
  scanning; nutrition lookup; Green / Yellow / Red classification; inventory-aware recipe
  generation; cart management; clinical checkout validation; inventory tracking and audit mode;
  replenishment support; analytics and donor/grant reporting; public Azure deployment.
- **Post-MVP**: multi-language support, facial recognition check-in, camera-based product
  tracking, advanced warehouse computer vision, and other innovation only after MVP is complete.
- **Feature freeze**: Eric determines timing. After freeze, only bug fixes, validation gaps,
  deployment fixes, and presentation-critical improvements may be merged.

## Governance

- This constitution supersedes other practices. Amendments require a documented change in
  `docs/decisions.md`, team approval, and a version bump.
- Versioning (semantic): MAJOR for incompatible principle removals or redefinitions; MINOR for
  new or materially expanded principles; PATCH for clarifications.
- Every PR review MUST verify compliance; added complexity MUST be justified.

**Version**: 1.0.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
