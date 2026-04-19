# PRD

Status: current product definition for the repository state as of 2026-04-10.

## Product Definition

RADE is a deterministic UI intelligence engine for authorized inputs.

The current product promise is intentionally narrow:

- accept a structured interface payload or a public web URL
- analyze it deterministically
- identify repeated structure, accessibility gaps, and migration / modernization risk
- emit evidence-backed outputs with stable identifiers
- keep every result reviewable, reproducible, and auditable

The current repo is a usable first wedge, not a claim of hosted product completeness.

## Current Wedge

RADE's first commercial wedge is proof-backed interface analysis for:

- repeated structure
- accessibility gaps
- migration / modernization risk

This wedge is immediately useful for:

- frontend teams
- agencies
- design-system work
- modernization efforts
- accessibility audits

## Broader Thesis

The longer-term thesis is broader than the current wedge:

- interfaces contain market intelligence
- repeated UI structures and interaction patterns can be collected and normalized
- design conventions can be observed over time
- that can become an intelligence layer for understanding how software is built and how interface patterns evolve

The current repository does not claim that full system exists yet. It establishes the deterministic inspection and artifact boundary that such a system would need.

## Primary User

- frontend, product, design, and engineering teams reviewing an existing interface
- agencies and consultants scoping interface modernization work
- design-system and accessibility owners who need traceable structural evidence

## Current User Problem

- they need a repeatable way to inspect repeated structure, accessibility gaps, and modernization risk without relying on ad hoc screenshots, subjective review, or unverifiable AI summaries

## Current Jobs To Be Done

1. Run a deterministic analysis over an authorized fixture or a public unauthenticated web page.
2. Produce stable artifacts with explicit evidence and stable identifiers.
3. Compare two existing RADE runs and identify what changed in scores, recommendations, and repeated structure.
4. Identify repeated structures, accessibility gaps, and modernization risk in a format teams can review and diff.
5. Preserve proof and redaction boundaries so outputs can be reviewed safely.

## Functional Requirements In Current Scope

1. Accept local JSON payloads matching the project schema or collect a public `http/https` page into that schema through the Playwright CLI path.
2. Validate screen IDs, element IDs, parent references, bounds, slab layers, and string/list fields before analysis.
3. Normalize nodes into a stable project model with canonical slab layers.
4. Fingerprint nodes from structure rather than literal labels.
5. Deduplicate repeated nodes into ordered duplicate clusters.
6. Score the project on complexity, reusability, accessibility risk, and migration risk.
7. Generate deterministic recommendations and a roadmap from current standards references.
8. Write JSON, Markdown, and HTML reports with public repository metadata and scrubbed strings.
9. Compare two existing RADE JSON reports into deterministic JSON and Markdown diff artifacts.
10. Expose thin smoke surfaces for API, web, worker, and agent entrypoints.
11. Preserve an exploratory blueprint / graph path for structural SVG and Neo4j Aura ingest proofs.

## Non-Functional Requirements In Current Scope

- determinism: same input plus same timestamp seed yields the same output
- proof-first workflow: changes are not complete without executable evidence
- explicit unknowns: use `UNKNOWN / NEEDS DECISION` instead of inferred behavior
- scrubbed artifacts: emitted reports and graph payloads must neutralize sensitive strings at the appropriate boundary
- traceability: findings, recommendations, and evidence must remain reviewable by humans and tooling

## Current Implemented Features

- CLI analysis command in `src/core/cli.py`
- CLI report diff command in `src/core/cli.py`
- Playwright-backed web collector in `src/collectors/web_dom_adapter.py`
- JSON, Markdown, and HTML report generation in `src/core/report_generator.py`
- deterministic report diff generation in `src/core/report_diff.py`
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
- AI-driven scoring, ranking, or recommendation generation

## Success Criteria For The Current Stage

- the sample fixture produces stable JSON, Markdown, and HTML reports
- two existing RADE JSON reports can be compared into deterministic JSON and Markdown diff artifacts
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

## DECIDED (2026-04-10)

- The first public wedge is deterministic interface analysis for repeated structure, accessibility gaps, and migration / modernization risk. It is no longer framed as an unresolved choice between accessibility-only and modernization-only positioning.
- The bigger thesis remains present, but secondary: RADE starts as a deterministic UI intelligence engine with evidence-backed outputs, not as a broad market-intelligence platform claim.
- The blueprint / graph path remains an implemented secondary proof track. It supports the broader thesis, but it is not the primary entry workflow.
- Repo/build scanning stays as a deterministic metadata stub. It will not expand into a code-aware connector until the current proof path is stable and justified by demand.

## UNKNOWN / NEEDS DECISION

- which downstream execution surface should be prioritized after the current wedge: richer API workflows, fixture diffing, or deeper collector coverage
- pricing model validation: free tier limits, Pro price point, Team tier viability
