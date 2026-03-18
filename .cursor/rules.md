# Cursor Rules

## Prime directive

Accuracy over confidence. Proof before expansion. Repo truth over model assumptions.

## Non-negotiables

- No guessing.
- No scope drift.
- No production-ready claims without proof.
- Mark unknowns explicitly.
- Prefer existing repo patterns before adding new abstractions.
- Prefer existing dependencies before adding new dependencies.
- Security-sensitive changes require explicit verification.

## Before coding

- Read the canonical files in order.
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
