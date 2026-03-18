# DECISIONS

## Purpose

Lightweight decision log for scope, contracts, workflow, and security choices that affect implementation.

## Decisions

### 2026-03-18 - Dual-track truth model

- Status: accepted
- Decision: keep `RADE.md` as strategic product truth and use the current-slice docs plus source/tests as implementation truth.
- Why: the repo contains both long-term product intent and a narrow deterministic proof slice. Without an explicit hierarchy, agents can hallucinate hosted behavior that does not exist yet.

### 2026-03-18 - Guardrails before hosted persistence

- Status: accepted
- Decision: harden truth hierarchy, workflow, validation, report identifiers, and artifact scrubbing before the first hosted persistence slice.
- Why: the largest current risk is truth drift, not proof-path failure.

### 2026-03-18 - Active web runtime is the shell server

- Status: accepted
- Decision: treat `web/lib/shell.mjs` plus the smoke test as the active web surface. Treat `web/app/` as dormant scaffold only until a real Next.js runtime is installed.
- Why: the current repo does not include a real Next.js runtime or dependency set.

### 2026-03-18 - Repo-specific proof and devserver commands

- Status: accepted
- Decision: replace faux `pytest` and `uvicorn` repo entrypoints with `rade-proof` and `rade-devserver`.
- Why: custom wrappers should not masquerade as upstream tools.

### 2026-03-18 - Report artifact scrubbing at output boundary

- Status: accepted
- Decision: scrub report artifacts immediately before JSON and Markdown write while preserving explicit structural identifiers required for deterministic analysis review.
- Why: scoring and fingerprinting must stay deterministic, but emitted artifacts should not leak obvious sensitive strings.
