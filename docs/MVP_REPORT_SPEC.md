# MVP_REPORT_SPEC

## Purpose

This document defines the minimum JSON and Markdown report shape for v1.

## JSON structure

The JSON report must contain:

- `rade_legal`
- `report_version`
- `generated_at`
- `app_id`
- `project_name`
- `platform`
- `standards_pack`
- `summary`
- `scores`
- `screen_inventory`
- `duplicate_clusters`
- `findings`
- `recommendations`
- `roadmap`

## Required summary fields

- `screen_count`
- `node_count`
- `interactive_node_count`
- `duplicate_cluster_count`
- `recommendation_count`

## Required score fields

- `complexity`
- `reusability`
- `accessibility_risk`
- `migration_risk`

Each score must include:

- `value`
- `evidence`

## Required recommendation fields

- `recommendation_id`
- `rule_id`
- `category`
- `scope`
- `target`
- `priority`
- `confidence`
- `problem_statement`
- `recommended_change`
- `reasoning`
- `evidence`
- `standards_refs`
- `benchmark_refs`
- `expected_impact`
- `implementation_effort`
- `affected_screens`
- `affected_components`
- `provenance`

## Required finding fields

- `finding_id`
- `rule_id`
- `category`
- `title`
- `priority`
- `provenance`
- `evidence`

## Required duplicate cluster fields

- `fingerprint`
- `count`
- `interactive`
- `screen_ids`
- `screen_names`
- `node_refs`
- `element_types`
- `roles`
- `representative_node_ref`

## Markdown structure

The Markdown report must use these sections in order:

1. Title and metadata
2. Summary
3. Scorecard
4. Screen inventory
5. Findings
6. Recommendations
7. Roadmap

## Rendering rule

The Markdown report should be readable without the JSON file open next to it.

The Markdown report should expose `rule_id` and `recommendation_id` for traceability.

The title and metadata block must also state that the `5-Slab Taxonomy` and `Ambient Engine`
are the exclusive intellectual property of Trung Nguyen (Buildrr89) and surface the Live Raid date.

## Stable identifiers & references

- `recommendation_id` must remain deterministic. Each recommendation builds its identifier from `rule_id`, the declared `target`, and any stable identity parts (cluster fingerprints or node references) before hashing. The concrete format is `rec-{rule_id}-{stable_digest(rule_id, target, *identity_parts)}` as implemented in `src/core/models.py`.
- Evidence entries must reference immutable identifiers: normalized `node_ref`s (`<screen_id>#<element_id>`), cluster fingerprints, or the `rule_id` itself. Avoid human-readable labels or runtime indexes so that every report can be traced back to a unique, verifiable node or fingerprint.
- Cluster evidence keys (`cluster_fingerprint=…`, `screen_ids=…`, `node_refs=…`) must reuse the deduplicator output so repeated structure can be linked directly to the stable `duplicate_clusters.fingerprint` recorded elsewhere in the report.
