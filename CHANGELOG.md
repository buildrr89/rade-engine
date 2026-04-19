# Changelog

All notable changes to RADE (`rade-engine`) are documented here.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
from v0.1.0 onward.

## [Unreleased]

### Changed

- GitHub Action runtime no longer installs the `neo4j` driver; only
  `playwright` and `pyyaml` are pulled, matching the base package surface
  (slice #39).

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
