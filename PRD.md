# PRD

Status: current product definition for the repository state as of 2026-03-22.

## Product Definition

RADE is a software-interface analysis workspace for authorized inputs.

The current product promise is narrow:

- accept a structured interface payload or a public web URL
- analyze it deterministically
- identify repeated structure and accessibility gaps
- emit evidence-backed modernization recommendations
- write traceable JSON and Markdown artifacts

The repo also carries an exploratory blueprint path that turns accessibility-like trees into structural SVG output and scrubbed graph rows, but that path is not yet the primary user workflow. The repository is shared publicly as an early alpha technical thesis and collaboration surface, not as a claim of hosted product completeness.

## Primary User

- product, design, and engineering teams reviewing an existing interface

## Current User Problem

- they need a repeatable way to inspect structure, duplication, and accessibility gaps without relying on ad hoc screenshots or taste-based review

## Current Jobs To Be Done

1. Run a deterministic analysis over an authorized fixture or a public unauthenticated web page.
2. Produce a stable report with explicit evidence and stable identifiers.
3. Preserve proof and redaction boundaries so outputs can be reviewed safely.

## Functional Requirements In Current Scope

1. Accept local JSON payloads matching the project schema or collect a public `http/https` page into that schema through the Playwright CLI path.
2. Validate screen IDs, element IDs, parent references, bounds, slab layers, and string/list fields before analysis.
3. Normalize nodes into a stable project model with canonical slab layers.
4. Fingerprint nodes from structure rather than literal labels.
5. Deduplicate repeated nodes into ordered duplicate clusters.
6. Score the project on complexity, reusability, accessibility risk, and migration risk.
7. Generate deterministic recommendations and a roadmap from current standards references.
8. Write JSON and Markdown reports with public repository metadata and scrubbed strings.
9. Expose thin smoke surfaces for API, web, worker, and agent entrypoints.
10. Preserve an exploratory blueprint / graph path for structural SVG and Neo4j Aura ingest proofs.

## Non-Functional Requirements In Current Scope

- determinism: same input plus same timestamp seed yields the same output
- proof-first workflow: changes are not complete without executable evidence
- explicit unknowns: use `UNKNOWN / NEEDS DECISION` instead of inferred behavior
- scrubbed artifacts: emitted reports and graph payloads must neutralize sensitive strings at the appropriate boundary

## Current Implemented Features

- CLI analysis command in `src/core/cli.py`
- Playwright-backed web collector in `src/collectors/web_dom_adapter.py`
- JSON and Markdown report generation in `src/core/report_generator.py`
- standards-backed recommendation engine in `src/core/recommendation_engine.py`
- roadmap generation in `src/core/roadmap_generator.py`
- report scrubber and edge scrubber in `src/scrubber/`
- web shell runtime in `web/lib/shell.mjs`
- WSGI API surface in `src/api/app.py`
- worker shell in `src/worker/main.py`
- repo metadata extractor in `src/connectors/repo_connector.py`
- accessibility orchestrator, SVG demo runner, and Neo4j Aura ingest library in `src/engine/`, `src/demo/`, and `src/database/`

## Explicitly Deferred

- hosted auth and tenant management
- persisted analysis history
- queue-backed job execution
- build connector implementation
- real Next.js web application runtime
- end-to-end Appium / AWS Device Farm integration
- authenticated/private-page web collection, anti-bot bypass, and SPA-specific collector logic
- production claims around scale, latency, or multi-tenant isolation

## Success Criteria For The Current Stage

- the sample fixture produces stable JSON and Markdown reports
- `rade analyze --url https://example.com` produces a valid deterministic report from a public page
- report IDs and evidence remain deterministic
- report artifacts are scrubbed without losing structural traceability
- the shell surfaces remain truthful about being shells
- the blueprint path remains clearly documented as exploratory rather than the main workflow

## Evidence Sources

- `tests/test_cli_contract.py`
- `tests/test_report_generator.py`
- `tests/test_recommendation_engine.py`
- `tests/test_scoring.py`
- `tests/test_scrubber.py`
- `tests/test_edge_shield.py`
- `tests/test_demo_runner.py`
- `tests/test_rade_orchestrator.py`
- `tests/test_graph_ingestor.py`
- `tests/test_web_dom_adapter.py`
- `.github/workflows/proof.yml`

## DECIDED (2026-03-22)

- The next real execution surface is `POST /analyze` on the WSGI app. Rationale: it reuses the proven CLI pipeline, gives the first honest user-facing workflow, and is materially smaller than queue + worker + persistence. The worker queue path is deferred until batch/team demand is validated.
- The blueprint / graph path remains an internal proof track for now. It may be promoted to a first-class product surface after the API proof is stable and design-partner feedback indicates demand.
- Repo/build scanning stays as a deterministic metadata stub. It will not expand into a code-aware connector until the API proof is stable and documented.

## UNKNOWN / NEEDS DECISION

- whether the first commercial wedge is accessibility compliance audits or design system modernization (to be resolved by design-partner feedback in the first 30 days)
- pricing model validation: free tier limits, Pro price point, Team tier viability
