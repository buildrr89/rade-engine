# RADE

## Current Stage

RADE is currently a proof-first local analysis workspace.

The primary proven product slice is:

- local JSON fixture input
- deterministic validation, normalization, layering, fingerprinting, and deduplication
- deterministic scoring, recommendation generation, and roadmap generation
- scrubbed JSON and Markdown report output with legal metadata

The repo also contains secondary implemented surfaces that are real but thin:

- a WSGI API shell with `/` and `/healthz`
- a worker shell that emits staged telemetry but does not process a real queue
- a web shell server in `web/lib/shell.mjs`
- an agent wrapper that forwards to the CLI
- an accessibility-tree-to-blueprint demo path with SVG output and a Neo4j Aura ingest library boundary

## What Is Proven

- `src/core/cli.py` runs the deterministic `analyze` flow.
- `src/core/report_generator.py` validates payloads, normalizes nodes, fingerprints structure, deduplicates repeated nodes, scores the project, builds standards-backed recommendations, builds a roadmap, and writes JSON / Markdown artifacts.
- `src/core/schemas.py` enforces the JSON contract for `project_name`, `platform`, `screens`, and per-element invariants.
- `src/scrubber/pii_scrubber.py` scrubs report artifacts while preserving stable identifiers such as `node_ref`, `rule_id`, and fingerprints.
- `src/scrubber/edge_shield.py` neutralizes sensitive strings into deterministic `DATA_SLOT_XX` placeholders for the blueprint / graph path.
- `src/demo/run_raid_visualizer.py`, `src/engine/rade_orchestrator.py`, and `src/database/graph_ingestor.py` prove an exploratory blueprint pipeline from accessibility-like trees to SVG and scrubbed graph persistence primitives.
- **Slab 03 (Frame) — hybrid pulse:** `src/core/slab03_hybrid_anchor.py` runs **modal**, then **landmark**, then **VBox tertiary** (`apply_slab03_hybrid_pulse`): `dialog` / `alertdialog` subtrees win over landmarks; semantic regions get `slab03:landmark:…` frames; nodes still without a frame whose center lies inside a **landmark root**’s bounds inherit that frame with `slab03_anchor_kind = visual:vbox-contained` (never overrides modal or prior assignments). Geometry is fed from `bounds` / `bounding_box` on `FunctionalNode.to_dict()` and into the Slab 03 pipeline from `rade_orchestrator`.
- `docs/PHASE_1_COMPONENTIZATION.md` is the planning / RFC contract for Phase 1 (Figma bridge export and deeper variant promotion remain incremental).
- **Figma Bridge v0:** `src/core/figma_bridge_v0.py` builds a deterministic, legal-wrapped JSON manifest from graph node dicts (`component_id`, `stable_component_key`, `figma_suggested_name`, `variant_axes` reserved). `ConstructionGraph.to_figma_bridge_v0_manifest()` exposes this on orchestrator output.
- `tests/` contains 25 test files and 92 test cases covering the primary report path, shells, contracts, scrubbers, orchestrator, Slab 03 heuristics, Figma Bridge v0, and graph ingestor.

## What Is Implemented But Not A Full Product Surface

- `src/api/app.py` is a health/readiness WSGI app, not a report-generation API.
- `src/worker/main.py` is a telemetry-producing shell, not a queue consumer.
- `src/connectors/repo_connector.py` extracts local repo metadata only.
- `src/connectors/build_connector.py` is explicitly deferred and raises `NotImplementedError`.
- `web/lib/shell.mjs` is the active web runtime; `web/app/` is a dormant scaffold and is not the current runtime.
- `src/engine/rade_orchestrator.py` includes managed-session configuration and capability building, but the repo does not ship a real Appium / AWS Device Farm integration.

## What Is Out Of Scope Right Now

- hosted auth, tenants, and persisted analysis history
- a real queue-backed execution system
- an API route that accepts scans and runs analysis
- a build connector implementation
- a real Next.js application runtime
- fully integrated device-farm collection
- benchmark-backed ranking beyond the current standards references

## Repo Map

- `PRD.md`: current product definition for the repo state
- `docs/TRUTH_HIERARCHY.md`: conflict resolution order
- `docs/APP_SCOPE.md`: canonical current implementation scope
- `docs/ARCHITECTURE.md`: current architecture and boundaries
- `docs/BUILD_SHEET.md`: current proof target and latest verified commands
- `docs/PHASE_1_COMPONENTIZATION.md`: Phase 1 componentization / frame intelligence RFC
- `src/`: Python implementation
- `web/`: shell web runtime and smoke tests
- `tests/`: deterministic proof coverage

## Quickstart

```bash
uv sync --dev
pnpm --dir web install
./rade-proof
uv run ruff check src tests agent
uv run black --check src tests agent
pnpm --dir web lint
pnpm --dir web test
uv run python -m src.core.cli analyze \
  --input tests/fixtures/sample_ios_output.json \
  --app-id com.example.legacyapp \
  --json-output output/modernization_report.json \
  --md-output output/modernization_report.md
```

## Truth Rule

Read repo truth in this order:

1. `README.md`
2. `PRD.md`
3. `docs/TRUTH_HIERARCHY.md`
4. `docs/APP_SCOPE.md`
5. `docs/HARD_RISKS.md`
6. `docs/ARCHITECTURE.md`
7. `docs/BUILD_SHEET.md`
8. implementation contracts and executable code / tests

If a historical file such as `RADE.md` or `RADE2.0.md` reappears later, treat it as archival unless the truth hierarchy is explicitly updated to make it authoritative again.
