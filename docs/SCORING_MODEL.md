# SCORING_MODEL

## Purpose

The scoring model ranks structural risk and reuse opportunities deterministically.

## Required scores

- `complexity`
- `reusability`
- `accessibility_risk`
- `migration_risk`

## Scoring rules

- Scores are deterministic.
- Scores are explainable.
- Scores are versioned.
- Scores are test-locked.

## Suggested formulas

- `complexity` increases with total nodes, interactive nodes, and screen count
- `reusability` increases with repeated structural fingerprints and decreases when structure is highly fragmented
- `accessibility_risk` increases when interactive nodes lack accessibility identifiers or comparable metadata
- `migration_risk` increases when repeated structure, accessibility gaps, and hierarchy friction stack together

## Evidence rule

Every score must expose evidence fields describing why the value was assigned.

## Locking rule

No score change ships unless:

1. tests are updated
2. the scoring doc is updated
3. a sample report diff is reviewed
