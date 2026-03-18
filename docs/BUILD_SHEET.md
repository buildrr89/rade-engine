# BUILD_SHEET

## Current objective

Keep the deterministic sample report path stable and keep truth, validation, and proof workflow aligned before any hosted persistence work.

## Why this is the current objective

It proves the core contract, the scoring path, and the report shape before any broader platform work.

## Current story

As a product team, I want to analyze a scan fixture so that I can get a prioritized, evidence-backed modernization report.

## Current proof slice

Fixture input -> normalize -> fingerprint -> deduplicate -> score -> recommend -> JSON and Markdown output.

## Expected proof

- What must work: the sample command should complete and write both report files
- What must be observed: stable report content and deterministic recommendation order
- What counts as success: the same input yields the same output except `generated_at`
- What does not need to exist yet: hosted auth, queues, persistent history, or full collector coverage

## Latest proof

- Date: 2026-03-18
- Status: Passed
- Evidence:
  - `./rade-proof` -> `25 passed, 0 failed`
  - `uv run ruff check src tests agent` -> `All checks passed!`
  - `uv run black --check src tests agent` -> `53 files would be left unchanged.`
  - `pnpm --dir web lint` -> `RADE web shell lint passed`
  - `pnpm --dir web test` -> `RADE web shell smoke test passed against http://127.0.0.1:<ephemeral-port>`
  - `uv run python -m src.core.cli analyze --input examples/sample_ios_output.json --app-id com.example.legacyapp --json-output output/modernization_report.json --md-output output/modernization_report.md` -> `generated 2 screens and 3 recommendations`

## Current blocker

No blocker for the phase-0 proof. Hosted persistence remains deferred until the guardrail pass stays green.

## Decision log

- 2026-03-18 - Use fixture-first bootstrap - keep the proof slice narrow
- 2026-03-18 - Favor deterministic core before web, hosted API, or collector expansion
- 2026-03-18 - Use dual-track truth: `RADE.md` is strategic and the current-slice docs plus tests are implementation truth
- 2026-03-18 - Replace faux tool branding with repo-owned `rade-proof` and `rade-devserver` launchers
- 2026-03-18 - Scrub report artifacts at write time while preserving stable structural identifiers
- 2026-03-19 - Default to PR-only changes on a protected `main` branch once GitHub settings are enabled

## Next immediate action

Draft the hosted persistence contract only after the current proof, validation, and doc-sync gates remain green.

## Stop conditions

Stop broadening work if:

- the current proof is still unverified
- new scope is being added without updating `docs/APP_SCOPE.md`
- docs and implementation diverge
