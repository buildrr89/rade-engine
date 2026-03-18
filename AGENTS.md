# AGENTS

## Purpose

This file defines how agents should work in this repository.

## Identity

- Be precise.
- Do not add hype.
- Optimize for proof, not breadth.
- Treat the repo as the source of truth after generation.

## Read order

Before making changes, read:

1. `README.md`
2. `docs/APP_SCOPE.md`
3. `docs/HARD_RISKS.md`
4. `docs/ARCHITECTURE.md`
5. `AGENTS.md`
6. `.cursor/rules.md`
7. `docs/BUILD_SHEET.md`

## Working rules

- Implement only the current proof slice.
- Do not broaden scope without updating `docs/APP_SCOPE.md`.
- Prefer small, testable, reversible changes.
- Search the repo before inventing new helpers or abstractions.
- Keep unknowns explicit.
- Do not overwrite changes you did not make.

## Proof rule

- No claim of completion without the exact commands and outputs that support it.
- If proof was not run, label the result as unverified.

## Output format

When reporting work, use this order:

1. Proven
2. Partially proven
3. Unknown
4. Risks or blockers
5. Next smallest action
