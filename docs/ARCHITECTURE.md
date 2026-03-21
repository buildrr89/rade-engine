# ARCHITECTURE

© 2026 RADE Project. All Rights Reserved.

## Purpose

This document defines the current executable architecture and the boundaries between the primary proof path and secondary experimental paths.

## Architecture at a glance

- Primary path: deterministic local report generation from a structured JSON payload.
- Secondary path: accessibility-like tree collection -> construction graph -> blueprint SVG / scrubbed graph ingest helpers.
- Thin shells: API, worker, web, and agent surfaces exist to keep entrypoints explicit without claiming hosted product completeness.

## Primary proof path

### 1. Input boundary

`src/core/cli.py` is the main entrypoint.

- Input is a local JSON payload.
- `src/core/schemas.py` validates required fields, uniqueness, parent references, slab layers, and scalar types.
- Only `ios`, `android`, and `web` are valid platforms.

### 2. Normalization boundary

`src/core/normalizer.py` converts validated payloads into a stable project model.

- every node is stamped with `app_id`, `platform`, `screen_id`, and `screen_name`
- traits are normalized and sorted
- bounds are normalized to integer arrays
- slab layers are inferred or normalized through `src/core/layering.py`

### 3. Structural analysis boundary

The deterministic structural path is:

1. fingerprint each node in `src/core/fingerprint.py`
2. deduplicate nodes into ordered clusters in `src/core/deduplicator.py`
3. score the project in `src/core/scoring.py`
4. build recommendations in `src/core/recommendation_engine.py`
5. build a roadmap in `src/core/roadmap_generator.py`

Current score outputs are:

- `complexity`
- `reusability`
- `accessibility_risk`
- `migration_risk`

Current recommendations are standards-backed and derived from current deterministic rules rather than model inference.

### 4. Output boundary

`src/core/report_generator.py` writes:

- JSON report
- Markdown report

Before write, report artifacts are scrubbed by `src/scrubber/pii_scrubber.py`.

- stable identifiers such as `node_ref`, `rule_id`, `recommendation_id`, and fingerprints are intentionally preserved
- emitted artifacts receive legal metadata from `src/core/compliance.py`

### 5. Supporting runtime shells

- `agent/cli.py` forwards `scan` to the core CLI analyze path
- `src/api/app.py` exposes only `/` and `/healthz`
- `src/worker/main.py` emits staged telemetry but performs no real queue work
- `web/lib/shell.mjs` serves the active web shell; `web/app/` is dormant scaffold only

## Secondary blueprint path

This path is implemented and tested, but it is not the default product workflow.

### Collection and graph model

`src/engine/rade_orchestrator.py` can collect from:

- an in-memory accessibility-like root object
- a caller-provided driver

It produces a `ConstructionGraph` containing normalized nodes, containment edges, and plumbing edges for interactive destinations.

The file also defines managed-session configuration and capability building for Appium-style providers, but the repo does not ship a full provider integration.

### SVG blueprint rendering

`src/demo/run_raid_visualizer.py` renders a deterministic SVG blueprint.

Current blueprint behavior includes:

- slab-layer-aware node styling
- `data-rade-dna` and `data-slab-layer` metadata on groups
- legal metadata and visible watermark text
- deterministic demo outputs validated against a golden SVG fixture

### Graph persistence boundary

`src/database/graph_ingestor.py` persists scrubbed construction graphs to Neo4j Aura.

Current status:

- schema creation and write queries exist
- scrub-before-write is enforced
- pattern IDs and plumbing edges are derived deterministically
- the ingestor is library-level proof, not a user-facing persistence workflow

## Deconstruction boundary

RADE currently supports two proven deconstruction inputs:

- structured JSON payloads for the report path
- accessibility-like trees for the blueprint / graph path

Pixel-first analysis is not the current core architecture.

## Collection boundary

Allowed collection sources:

- authorized customer payloads
- customer-consented accessibility trees or simulators when the caller provides them
- public unauthenticated surfaces where collection is permitted

Forbidden collection behaviors:

- login bypass
- fake accounts
- stealth collection
- access-control circumvention

## Scrubbing boundaries

- Graph / blueprint persistence uses `src/scrubber/edge_shield.py`.
- Report artifact emission uses `src/scrubber/pii_scrubber.py`.

Required behavior:

- regex-first PII removal
- optional second-pass Presidio escalation for ambiguous free-form text
- preserve structural nodes and edges where needed for proof
- emit audit metadata for persistence-side scrubbing
- neutralize persistence-side sensitive strings into placeholders such as `DATA_SLOT_01`

## Legal framing

The `5-Slab Taxonomy` and `Ambient Engine` are the exclusive intellectual property of Trung Nguyen (Buildrr89).

Use hiQ v. LinkedIn as a narrow CFAA-domain reference for public-facing collection logic.

Do not write the system as if hiQ is a blanket authorization to bypass gates, ignore terms, or collect private user content.

## Deferred architecture

These are not current architecture claims:

- hosted auth
- tenant-aware persistence
- queue-backed execution
- API-triggered analysis runs
- build scanning beyond deterministic local repo metadata
- a real Next.js runtime
- a shipped AWS Device Farm / Appium integration

## Non-goals

- no pixel-first reverse engineering
- no LLM-based deterministic scoring
- no stealth collection model
- no hosted persistence assumptions inside the engine layer
