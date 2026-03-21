# BUILD_SHEET

## Current objective

Keep the deterministic report path and the exploratory blueprint path aligned with the actual repo state while the API, worker, and web surfaces remain thin shells.

## Why this is the current objective

It keeps the proven core honest: report generation is the shipped proof slice, the blueprint path is a tested secondary track, and the shell entrypoints must not pretend to be more complete than they are.

## Current story

As a product team, I want to analyze an authorized fixture and get a prioritized, evidence-backed modernization report without guessing what is actually implemented in the repo.

## Current proof slice

Fixture input -> normalize -> fingerprint -> deduplicate -> score -> recommend -> JSON and Markdown output.

## Secondary proof slice

Accessibility-like tree -> construction graph -> deterministic SVG blueprint -> scrubbed Neo4j Aura ingest rows.

## Expected proof

- What must work: the sample command should complete and write both report files
- What must be observed: stable report content and deterministic recommendation order
- What counts as success: the same input yields the same output except `generated_at`
- What does not need to exist yet: hosted auth, queues, persistent history, API-triggered analysis, or full collector coverage

## Latest proof

- Date: 2026-03-21
- Status: Passed
- Evidence:
  - `./rade-proof` -> `63 passed, 0 failed`
  - `uv run python -m src.core.cli analyze --input examples/sample_ios_output.json --app-id com.example.legacyapp --json-output output/modernization_report.json --md-output output/modernization_report.md` -> `generated 2 screens and 3 recommendations`
  - `uv run pytest tests/test_demo_runner.py -q` -> `9 passed in 0.15s`
  - `uv run pytest tests/test_sole_architect_compliance.py tests/test_recursive_safety.py tests/test_report_generator.py tests/test_fingerprint.py -q` -> `11 passed in 0.22s`
  - `uv run ruff check --fix src tests agent` -> `All checks passed!`
  - `uv run ruff check src tests agent` -> `All checks passed!`
  - `uv run black src tests agent` -> `72 files left unchanged.`
  - `uv run black --check src tests agent` -> `72 files would be left unchanged.`
  - `node web/scripts/lint.mjs` -> `RADE web shell lint passed`
  - `pnpm --dir web lint` -> `RADE web shell lint passed`

## Current blocker

No blocker on the deterministic report slice, exploratory blueprint test slice, or current lint/format gates. Python lint is clean across `src`, `tests`, and `agent`, and the official `pnpm --dir web lint` command now runs successfully.

GitHub-enforced branch protection is currently blocked on this private repository because GitHub returned: `Upgrade to GitHub Pro or make this repository public to enable this feature.`

## Decision log

- 2026-03-18 - Use fixture-first bootstrap - keep the proof slice narrow
- 2026-03-18 - Favor deterministic core before web, hosted API, or collector expansion
- 2026-03-18 - Use dual-track truth: product definition plus current-slice docs/tests are separate from implementation proof
- 2026-03-18 - Replace faux tool branding with repo-owned `rade-proof` and `rade-devserver` launchers
- 2026-03-18 - Scrub report artifacts at write time while preserving stable structural identifiers
- 2026-03-19 - Default to PR-only changes on a protected `main` branch once GitHub settings are enabled
- 2026-03-19 - GitHub branch protection could not be enabled on this private repository because the current plan returned HTTP 403 for protection APIs
- 2026-03-19 - Harden input validation to reject self-parent references and non-string labels or traits before normalization
- 2026-03-19 - Enforce proof workflow and template coverage with repository contract tests
- 2026-03-19 - Reinforce the artifact scrub boundary with Markdown regression coverage
- 2026-03-21 - Replace stale `RADE.md` references with a current `PRD.md` because the strategic files are absent from the working tree
- 2026-03-21 - Document the blueprint / graph path as an implemented secondary proof slice rather than the main product workflow
- 2026-03-21 - Document API, worker, repo connector, and web surfaces as shells or stubs unless a proof command exercises real business behavior
- 2026-03-21 - Restore repo-wide Python import/format compliance and re-verify the official web lint command

## Next immediate action

Implement one real non-shell execution surface by reusing the existing report pipeline, preferably `POST /analyze` on the WSGI app or the first queue-backed worker claim cycle.

## Stop conditions

Stop broadening work if:

- the current proof is still unverified
- new scope is being added without updating `docs/APP_SCOPE.md`
- docs and implementation diverge

## Truth discipline

This sheet tracks the deterministic proof path but is subordinate to the truth hierarchy in
`docs/TRUTH_HIERARCHY.md`. When doc drift is suspected, consult the ordered list in `README.md`
and align all affected entry docs before accepting a change. The canonical docs (`README.md`,
`PRD.md`, `docs/TRUTH_HIERARCHY.md`, `docs/APP_SCOPE.md`, `docs/BUILD_SHEET.md`, etc.) and executable
code/tests are the binding implementation truth; update them together to stay aligned with the
repo’s disciplined approach.
