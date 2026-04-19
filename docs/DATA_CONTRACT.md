# DATA_CONTRACT

## Purpose

This document defines the input and output contract for the deterministic proof slice.

## Input contract

The analysis input is a JSON object with these top-level fields:

- `rade_legal`: optional object carrying public repository metadata because JSON does not support comments
- `project_name`: string
- `platform`: string, currently `ios`, `android`, or `web`
- `screens`: array of screen objects

Each screen object has these fields:

- `screen_id`: string
- `screen_name`: string
- `elements`: array of element objects

Validation rules:

- `screen_id` must be unique within the payload
- `elements` must contain at least one element
- `label` must be a string
- `traits` must contain only strings

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
- `hierarchy_depth`: non-negative integer
- `child_count`: non-negative integer
- `text_present`: boolean
- `traits`: array of strings
- `source`: string

Validation rules:

- `element_id` must be unique within a screen
- `parent_id` must point to a different element in the same screen when present
- `bounds` must be either `null` or exactly four numeric values
- `slab_layer` must be one of the canonical construction labels below when present

Canonical slab labels:

- `01. OS Site (The Land)`
- `02. Root (The Slab)`
- `03. Containers (The Frame)`
- `04. Links/Events (Wires & Plumbing)`
- `05. Assets (The Decor)`

Canonical mapping locked in:

- `foundation` -> `01. OS Site (The Land)`
- `framework` -> `02. Root (The Slab)`
- `systems` -> `03. Containers (The Frame)`
- `fitout` -> `04. Links/Events (Wires & Plumbing)`
- `finish` -> `05. Assets (The Decor)`

Legacy slab labels are no longer valid contract values.

## Normalized node contract

The normalized node keeps the same fields and adds:

- `structural_fingerprint`: string
- `screen_id`: string
- `screen_name`: string
- `platform`: string

Fingerprinting must ignore literal labels and other transient content when structure is sufficient.

## Output contract

The report output must include:

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

Report identifier rules:

- Public report evidence must use stable `node_ref` strings in the form `screen_id#element_id`
- Recommendations must expose explicit `rule_id`
- `recommendation_id` must be derived from stable rule and target inputs, not human prose

Artifact scrub rule:

- JSON and Markdown report artifacts are scrubbed at write time for obvious sensitive strings
- Structural identifiers such as `node_ref`, `screen_id`, `recommendation_id`, `rule_id`, and fingerprints remain intentionally preserved
- `rade_legal` preserves the repository legal notice, attribution, license, project-status metadata, terminology notice, SVG watermark text, and the report Live Raid date

## Legal metadata contract

`rade_legal` may contain these compliance fields when present:

- `header_notice`
- `attribution`
- `license`
- `project_status`
- `project_terms_notice`
- `visible_svg_watermark`
- `live_raid_date`

## Determinism rule

Same input plus same standards pack must produce the same output except `generated_at`.
