# DATA_CONTRACT

## Purpose

This document defines the input and output contract for the deterministic proof slice.

## Input contract

The analysis input is a JSON object with these top-level fields:

- `project_name`: string
- `platform`: string, currently `ios`, `android`, or `web`
- `screens`: array of screen objects

Each screen object has these fields:

- `screen_id`: string
- `screen_name`: string
- `elements`: array of element objects

Each element object has these fields:

- `element_id`: string
- `parent_id`: string or null
- `element_type`: string
- `role`: string
- `slab_layer`: string or null
- `label`: string or empty string
- `accessibility_identifier`: string or null
- `interactive`: boolean
- `visible`: boolean
- `bounds`: array of four numbers or null
- `hierarchy_depth`: integer
- `child_count`: integer
- `text_present`: boolean
- `traits`: array of strings
- `source`: string

## Normalized node contract

The normalized node keeps the same fields and adds:

- `structural_fingerprint`: string
- `screen_id`: string
- `screen_name`: string
- `platform`: string

Fingerprinting must ignore literal labels and other transient content when structure is sufficient.

## Output contract

The report output must include:

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

## Determinism rule

Same input plus same standards pack must produce the same output except `generated_at`.
