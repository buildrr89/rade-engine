# MVP_REPORT_SPEC

## Purpose

This document defines the minimum JSON and Markdown report shape for v1.

## JSON structure

The JSON report must contain:

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
