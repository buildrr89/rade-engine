# RECOMMENDATION_ENGINE

## Purpose

The recommendation engine turns deterministic findings into ranked, evidence-backed actions.

## Ranking order

1. Standards violations
2. High-confidence flow friction
3. Component and consistency problems
4. Migration sequencing opportunities
5. Lower-confidence benchmark suggestions
6. Cosmetic suggestions

## Recommendation categories

- `layout`
- `navigation`
- `accessibility`
- `interaction`
- `content_hierarchy`
- `component_reuse`
- `design_system_consistency`
- `migration_sequencing`

## Provenance rule

Every recommendation must show whether it is:

- standards-backed
- benchmark-backed
- both

In v1, standards-backed recommendations are the expected default.

## Minimum evidence

Every recommendation must include:

- a concrete problem statement
- a concrete recommended change
- direct evidence from the project graph
- references to standards or benchmarks when available

## v1 recommendation rules

- Accessibility gaps on interactive nodes should produce an accessibility recommendation.
- Repeated structural fingerprints across screens should produce a component reuse or consistency recommendation.
- If both are present, add a sequencing recommendation that tells the team what to fix first.
