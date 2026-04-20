# Cursor Rules

Copyright (c) 2026 Buildrr89. Licensed under AGPL-3.0-only.

## Prime directive

Accuracy over confidence. Proof before expansion. Repo truth over model assumptions.

## Non-negotiables

- No guessing.
- No scope drift.
- No production-ready claims without proof.
- Mark unknowns explicitly.
- Prefer `UNKNOWN / NEEDS DECISION` over inferred behavior.
- Prefer existing repo patterns before adding new abstractions.
- Prefer existing dependencies before adding new dependencies.
- Security-sensitive changes require explicit verification.

## Product and collection boundaries

- Prioritize semantic accessibility nodes over screen coordinates.
- Collect only from authorized or public surfaces.
- No fake accounts.
- No login bypass.
- No stealth collection.
- No deterministic scoring from LLM output.
- Update canonical docs and tests when behavior changes.

## Before coding

- Read the canonical files in order: `README.md`, `PRD.md`, `docs/TRUTH_HIERARCHY.md`, `docs/APP_SCOPE.md`, `docs/HARD_RISKS.md`, `docs/ARCHITECTURE.md`, `docs/BUILD_SHEET.md`, `AGENTS.md`, `docs/CURSOR_RULES.md`.
- Resolve truth conflicts using `docs/TRUTH_HIERARCHY.md`.
- Identify the single objective.
- Identify the biggest relevant risk.
- State what will change and what will not.
- Search the repo before creating new helpers, utilities, or components.

## During coding

- Implement only the current proof slice.
- Avoid side quests.
- Keep changes reversible.
- Reuse existing patterns.

## After coding

- Run the relevant proof.
- Return exact evidence.
- If proof was not executed, mark the result as unverified.
- Do not treat missing historical docs as canonical truth; use the files named in the truth hierarchy.

## Cursor IDE (local only)

The tracked copy of this file is canonical. If you use Cursor and want a
project root `.cursorrules` file, keep it **local** (gitignored): for example
`ln -sf docs/CURSOR_RULES.md .cursorrules` in your clone, or paste a short
summary that links here.
