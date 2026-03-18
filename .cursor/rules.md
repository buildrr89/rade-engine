# Cursor Rules

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

## Before coding

- Read the canonical files in order.
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
