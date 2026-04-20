# Skill: scope-guard

## Purpose

Prevent scope creep and protect proof-first execution.

## Use when

- A task introduces extra features.
- The request expands beyond the current proof slice.
- Architecture is growing faster than evidence.

## Rules

- Compare requested work against `docs/APP_SCOPE.md`.
- Compare requested work against `docs/BUILD_SHEET.md`.
- Reject or defer anything not needed for the current proof.
- Propose the smallest acceptable slice.

## Output

- In scope
- Out of scope
- Minimal acceptable implementation
- Deferred items
