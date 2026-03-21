# DECISIONS

## Purpose

Lightweight decision log for scope, contracts, workflow, and security choices that affect implementation.

## Decisions

### 2026-03-18 - Dual-track truth model

- Status: accepted
- Decision: keep a current product definition (`PRD.md`) separate from implementation truth in the current-slice docs plus source/tests.
- Why: the repo contains both product intent and a narrow deterministic proof slice. Without an explicit hierarchy, agents can hallucinate hosted behavior that does not exist yet.

### 2026-03-18 - Guardrails before hosted persistence

- Status: accepted
- Decision: harden truth hierarchy, workflow, validation, report identifiers, and artifact scrubbing before the first hosted persistence slice.
- Why: the largest current risk is truth drift, not proof-path failure.

### 2026-03-18 - Active web runtime is the shell server

- Status: accepted
- Decision: treat `web/lib/shell.mjs` plus the smoke test as the active web surface. Treat `web/app/` as dormant scaffold only until a real Next.js runtime is installed.
- Why: the current repo does not include a real Next.js runtime or dependency set.

### 2026-03-18 - Repo-specific proof and devserver commands

- Status: accepted
- Decision: replace faux `pytest` and `uvicorn` repo entrypoints with `rade-proof` and `rade-devserver`.
- Why: custom wrappers should not masquerade as upstream tools.

### 2026-03-18 - Report artifact scrubbing at output boundary

- Status: accepted
- Decision: scrub report artifacts immediately before JSON and Markdown write while preserving explicit structural identifiers required for deterministic analysis review.
- Why: scoring and fingerprinting must stay deterministic, but emitted artifacts should not leak obvious sensitive strings.

### 2026-03-21 - Figma Bridge v0 manifest

- Status: accepted (proof slice)
- Decision: add `src/core/figma_bridge_v0.py` to emit `with_legal_metadata`-wrapped JSON describing one component candidate per `slab03_frame_id`, plus `ConstructionGraph.to_figma_bridge_v0_manifest()` for orchestrator graphs. `variant_axes` stays an empty reserved list until Tier 2 variant promotion is specified.
- Why: locks an export-shaped contract for Figma-oriented tooling without implying a full design-system pipeline.

### 2026-03-21 - Figma Bridge ref_map (Slab 04 wires)

- Status: accepted (proof slice)
- Decision: manifest version `0.2.0` adds `ref_map` with deterministic `wires` built from ConstructionGraph edges whose `edge_type` is Slab 04 plumbing (`triggers`, `routes_to`, `submits_to`, `controls`). Each wire resolves `source_frame_id` / `target_frame_id` from node `slab03_frame_id` (top-level or `functional_dna`) and sets `plumbing_scope` to `internal`, `external`, or unresolved variants when a frame is missing. Optional `metadata.action_type` on an edge overrides the default mapping from `edge_type` (e.g. `hover`).
- Why: agents need cross-frame behavioral links without merging Slab 03 components; mirrors prototype “wires” in export shape.

### 2026-03-21 - Figma Bridge manifest 0.2.1 (Slab 03 anchor DNA)

- Status: accepted (proof slice)
- Decision: bump `manifest_version` to `0.2.1`. Per-frame rows already expose `anchor_kinds_observed` derived from top-level or `functional_dna` `slab03_anchor_kind` (modal, landmark, landmark-descendant, `visual:vbox-contained`, etc.); the version bump marks that Slab 03 anchor taxonomy as part of the stable export contract alongside `0.2.0` `ref_map`.
- Why: downstream Figma and review tooling need an explicit version step when anchor-kind semantics are guaranteed in the manifest, not only in SVG `data-rade-dna`.

### 2026-03-21 - Slab 03 landmark pulse and hybrid composition

- Status: accepted
- Decision: extend `src/core/slab03_hybrid_anchor.py` with semantic **landmark** frames (`nav`, `main`, `aside`, `header`, `footer`) after the modal pulse; modal assignments always win on overlap. Emit deterministic `slab03:landmark:…` IDs, `slab03_landmark_kind`, and human-oriented `slab03_figma_alias` strings; wire via `apply_slab03_hybrid_pulse()` from `src/engine/rade_orchestrator.py`.
- Why: distinguish same Slab 04 plumbing DNA by frame context (e.g. nav link vs footer link) without collapsing portal dialogs into **Main**.

### 2026-03-21 - Slab 03 VBox tertiary pulse

- Status: accepted (proof slice)
- Decision: after modal + landmark pulses, run `apply_vbox_tertiary_pulse`: only nodes **without** `slab03_frame_id`, with parseable `bounds` / `bounding_box`, whose center lies inside a landmark **root**’s rectangle, inherit that root’s frame metadata and `slab03_anchor_kind = visual:vbox-contained`. Tie-break containing roots by smallest area then `element_id`. Never override modal or existing Slab 03 assignments. `RadeOrchestrator._apply_slab03_frame_intelligence` passes geometry into the hybrid pulse; `FunctionalNode.to_dict()` adds a derived `bounding_box` object; graph payload reload drops `bounding_box` before `FunctionalNode(**row)`.
- Why: floating controls (FABs, sticky chrome) often sit outside landmark subtrees in the accessibility tree but visually belong to a landmark frame.

### 2026-03-21 - Phase 1 componentization RFC and Slab 03 modal pulse

- Status: accepted (RFC + first heuristic slice)
- Decision: add `docs/PHASE_1_COMPONENTIZATION.md` as the planning contract for Phase 1; implement modal/dialog **Slab 03** frame isolation in `src/core/slab03_hybrid_anchor.py` before landmark/VBox grouping.
- Why: portal-mounted dialogs break naive DOM-frame grouping; explicit `role="dialog"` / `alertdialog` roots must not be collapsed into semantic **Main**.

### 2026-03-21 - Replace missing strategy-file dependency

- Status: accepted
- Decision: stop treating `RADE.md` and `RADE2.0.md` as current canonical dependencies and replace that role with `PRD.md`.
- Why: those files are absent in the working tree, while multiple canonical docs still depended on them. A missing source-of-truth file is documentation drift by definition.

### 2026-03-21 - Classify blueprint work as secondary proof

- Status: accepted
- Decision: document the accessibility-tree / SVG / Neo4j path as an implemented secondary proof track, not the default user workflow.
- Why: the code and tests prove that the path exists, but the primary user-facing entrypoints still center on deterministic local report generation.
