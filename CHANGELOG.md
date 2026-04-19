# Changelog

All notable changes to RADE (`rade-engine`) are documented here.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
from v0.1.0 onward.

## [Unreleased]

### Added

- Optional axe-core regression gate on the GitHub Action via new
  `fail-on-axe-regression` input. When enabled, the Action fails the PR
  if any newly-introduced axe rule has `critical` or `serious` impact in
  the head report. Pre-existing violations and new `moderate` / `minor`
  findings do not trigger the gate. New deterministic outputs:
  `axe-gate-status`, `axe-regression-detected`, `axe-regression-reason`.
  The score regression gate (`fail-on-regression`) is unchanged (slice
  #41).

### Changed

- GitHub Action runtime no longer installs the `neo4j` driver; only
  `playwright` and `pyyaml` are pulled, matching the base package surface
  (slice #39).
- PR workflow step summary now surfaces the three axe gate outputs
  alongside the existing score gate outputs, and switches to env-var
  indirection for all interpolated output values to comply with the
  GitHub Actions workflow-injection security pattern (slice #42).

### Fixed

- Six `except A, B:` Python-2 tuple-less syntax sites in
  `src/engine/rade_orchestrator.py` and
  `src/core/slab03_hybrid_anchor.py` that parsed silently on Python
  3.14 (thanks to PEP 758) but failed at import time on Python 3.12
  and 3.13. The package advertised `>=3.12` but was effectively
  broken on two of its three advertised versions until this fix
  (slice #44).

### Documentation

- README gains a dedicated `## GitHub Action` section with a working
  YAML example covering both `fail-on-regression` and
  `fail-on-axe-regression`, plus an inventory of the 9 deterministic
  outputs (slice #43).
- README Contributing section now cross-links `CHANGELOG.md` so
  contributors can find release-by-release context without knowing
  the filename (slice #45).
- README landing banner now surfaces five CI/status badges (Proof,
  Wheel smoke, CodeQL, License AGPL-3.0, Python 3.12/3.13/3.14)
  instead of the single Proof image, each clickable through to the
  backing workflow or file (slice #47).

### Tests

- New `tests/fixtures/axe_gate_base.json` and
  `tests/fixtures/axe_gate_head.json` provide a byte-stable golden
  case for the slice #41 axe regression gate: base has one pre-existing
  `moderate` rule, head adds a newly-introduced `critical` rule. The
  paired `tests/test_axe_gate_fixtures.py` asserts the gate fires with
  reason `critical_introduced`, the PR comment reflects the gate
  status, and the diff is deterministic across repeated calls (slice
  #46).

### CI

- New `.github/workflows/wheel-smoke.yml` matrix-builds the wheel and
  installs it into clean venvs on Python 3.12, 3.13, and 3.14, then
  verifies the `rade` CLI runs, the `[graph]` extra installs
  `neo4j`, and the base install does NOT pull `neo4j`. Guards
  against both future tuple-less-except drift and accidental
  re-promotion of `neo4j` to a base dependency (slice #44).

## [0.1.0] — pending tag

First public-alpha release on PyPI as `rade-engine`. The package exposes the
`rade` CLI for deterministic UI analysis of public URLs and JSON payloads.

### Added

- `rade analyze` deterministic pipeline with JSON, Markdown, and interactive
  HTML report outputs.
- Playwright-backed `--url` collection for public, unauthenticated pages.
- Optional `--axe` flag injecting Deque's axe-core engine and embedding
  normalized WCAG violations in the report as an `accessibility_violations`
  block (slice #35).
- `rade badge` CLI producing deterministic SVG score badges and optional
  shields.io endpoint JSON, with direction-aware coloring for `reusability`,
  `accessibility_risk`, `complexity`, and `migration_risk` (slice #34).
- `rade diff` CLI for deterministic report-to-report diffs with stable
  recommendation and repeated-structure traceability (slices #32–#33).
- GitHub Action (`buildrr89/rade-engine`) that posts a PR comment with
  `reusability` / `accessibility_risk` deltas and a configurable regression
  gate (slice #17 and hardening slices #18–#31).
- PR comment now includes an `Accessibility violations (axe-core)`
  subsection at rule-id granularity when axe data is present on either side
  of the diff; the subsection is omitted entirely when neither side has axe
  output (slice #38). The regression gate is unchanged — axe deltas are
  reported, not enforced.
- `POST /analyze` HTTP surface with API-key auth middleware and WSGI entry
  point for hosted-mode experimentation (slices #11–#12).
- Three real-world fixture reports (`python.org`, `MDN`, `web.dev`) with
  checked-in golden outputs to guard determinism (slice #13).
- Live GitHub Pages demo workflow that rebuilds an HTML report and SVG
  badges from checked-in fixtures on every push to `main` (slice #36).
- PyPI trusted-publishing workflow ready for the maintainer to tag
  `v0.1.0` (slice #36).

### Changed

- `neo4j>=6.1.0` is now an opt-in extra under `rade-engine[graph]` instead
  of a base dependency, saving ~40MB on the common install path. The
  Neo4j Aura ingest path raises a clear `ImportError` pointing at the
  extra when the driver is absent (slice #37).

### Security

- Report artifacts are scrubbed on every JSON and Markdown write; PII
  scrubber covers the Markdown renderer as well as raw JSON (slice #3).
- API-key middleware uses constant-time comparison and fails safe with
  503 when the key is unset (slice #12).
