# BUILD_SHEET

## Current objective

Implement the deterministic sample report path from `examples/sample_ios_output.json` to `output/modernization_report.json` and `output/modernization_report.md`.

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
- Status: In progress
- Evidence: repo scaffold created, contract docs written, and implementation pending

## Current blocker

The repo has no implementation yet for the deterministic core pipeline.

## Decision log

- 2026-03-18 - Use fixture-first bootstrap - keep the proof slice narrow
- 2026-03-18 - Favor deterministic core before web, hosted API, or collector expansion

## Next immediate action

Implement the core data model, normalization, fingerprinting, scoring, recommendation engine, and report generator.

## Stop conditions

Stop broadening work if:

- the current proof is still unverified
- new scope is being added without updating `docs/APP_SCOPE.md`
- docs and implementation diverge
