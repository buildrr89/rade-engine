# APP_SCOPE

## Authority

This file is the canonical implementation scope for the current slice.

If `PRD.md` is broader, this file wins for implementation decisions until the scope changes here.

## Product summary

RADE helps teams analyze authorized software interfaces and get evidence-backed modernization recommendations from deterministic structural analysis.

## Current stage

Current stage is a local proof slice with one real authenticated API surface, thin worker/web shells, and one exploratory blueprint / graph track.

- Primary proof path: JSON payload or Playwright-collected public web page -> validated project model -> scores and recommendations -> JSON / Markdown report.
- Secondary implemented surfaces: worker shell, web shell, agent wrapper, repo metadata stub, SVG blueprint demo, and Neo4j Aura ingest library boundary.

## Target user

- Primary user: product, design, and engineering teams owning an app or project
- Their urgent problem: they need a structured way to understand duplicated structure, accessibility gaps, and what to fix first
- Current workaround: manual review, screenshots, ad hoc audits, and scattered design feedback

## In scope for the current slice

- local JSON upload scan through the CLI, agent wrapper, and `POST /analyze` API endpoint
- public unauthenticated `http/https` URL scan through the CLI and agent wrapper via Playwright web collection
- schema validation for projects, screens, nodes, parent references, bounds, and slab layers
- deterministic normalization, slab-layer inference, and structural fingerprinting
- deduplication of repeated interface structure
- deterministic scores for complexity, reusability, accessibility risk, and migration risk
- standards-backed recommendations and roadmap generation
- JSON and Markdown report generation
- report-artifact scrubbing that preserves stable identifiers
- public repository metadata on generated JSON, Markdown, and blueprint SVG artifacts
- demo SVG blueprint generation from accessibility-like trees
- deterministic Figma Bridge v0 JSON manifest from construction graph nodes (export contract only; not a full Figma API integration)
- tested Neo4j Aura ingest library boundary for scrubbed construction graphs
- sample proof runs from fixtures and shell smoke tests
- API key auth middleware with constant-time comparison and fail-safe for unconfigured keys

## Implemented but explicitly not full product surfaces yet

- `src/api/wsgi.py` is the served WSGI entrypoint for `POST /analyze`; it wraps the core `src/api/app.py` handler with API key auth middleware.
- `src/collectors/web_dom_adapter.py` serves a real collector path for public unauthenticated web pages. It converts Playwright ARIA snapshots into the RADE input contract and falls back to semantic DOM extraction if needed.
- `src/worker/main.py` is only a telemetry-producing shell
- `web/lib/shell.mjs` is only a shell runtime with `/` and `/report`
- `src/connectors/repo_connector.py` is only a deterministic metadata extractor
- `src/connectors/build_connector.py` remains deferred
- `src/engine/rade_orchestrator.py` is a library boundary and demo input path, not a shipped collector integration

## Explicitly deferred

- multi-tenant auth, tenants, and persisted analysis history (single-tenant static API key auth is implemented)
- queue-backed job execution
- ~~an analysis API route~~ (implemented: `POST /analyze`)
- build connector implementation
- a real Next.js runtime
- end-to-end Appium / AWS Device Farm integration
- benchmark-aware ranking beyond the current standards references
- broad enterprise workflow platform
- authenticated/private-page web collection
- anti-bot evasion or login bypass

## Current boundaries

- Platform(s): Python CLI, local analysis from JSON or public URLs, hosted API (`POST /analyze` with API key auth), and shell web/worker surfaces
- Active web runtime: `web/lib/shell.mjs`; `web/app/` is dormant scaffold only
- Geography: none
- Integrations allowed in the current slice: local file input, public unauthenticated web-page collection through Playwright, sample fixture output, local repo metadata extraction, test-only Neo4j Aura ingest boundary
- Integrations explicitly deferred: hosted auth, queues, object storage, Redis, real build scanning, authenticated/private-page collection, real device-farm collection
- AI use allowed in the current slice: none for deterministic scoring; prose generation only if needed later
- AI use explicitly deferred: autonomous scoring, recommendation ranking, and structural fingerprinting
- Project terminology preserved in generated docs: `5-Slab Taxonomy` and `Ambient Engine`

## Non-goals

- taste-based "ultimate UI" output
- claiming enterprise completeness before proof
- expanding collectors before the core is stable
- building unrelated platform surface area

## Success criteria for the current slice

- a sample iOS fixture produces the same report structure on every run except `generated_at`
- the report contains deterministic scores and evidence-backed recommendations
- the report is readable as both JSON and Markdown
- shell surfaces remain truthful about being shells
- the blueprint demo remains deterministic for the demo input set

## Scope guard rules

- If a feature does not support the proof slice or current success criteria, defer it.
- If a task adds complexity before risk reduction, defer it.
- If a new dependency is proposed, prove why the current repo cannot solve the need.
- Do not describe the blueprint / graph path as the default user workflow unless the primary entrypoints actually use it.

## Truth discipline

`docs/APP_SCOPE.md` is the canonical declaration of current scope for this proof slice. When scope, behavior, or contract questions arise, follow the read-order list in `README.md` and the adjudication rules described in `docs/TRUTH_HIERARCHY.md`: canonical docs + implementation truth win, while `PRD.md` remains product-definition context only. Always update these canonical artifacts together with any implementation change that touches their expressed behavior.
