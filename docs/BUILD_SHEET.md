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

- Date: 2026-03-19
- Status: Passed
- Evidence:
  - `./rade-proof` -> `34 passed, 0 failed`
  - `uv run ruff check src tests agent` -> `All checks passed!`
  - `uv run black --check src tests agent` -> `All done! ✨ 🍰 ✨ 58 files would be left unchanged.`

## Current blocker

No blocker for the phase-0 proof. Hosted persistence remains deferred until the guardrail pass stays green.

GitHub-enforced branch protection is currently blocked on this private repository because GitHub returned: `Upgrade to GitHub Pro or make this repository public to enable this feature.`

## Decision log

- 2026-03-18 - Use fixture-first bootstrap - keep the proof slice narrow
- 2026-03-18 - Favor deterministic core before web, hosted API, or collector expansion
- 2026-03-18 - Use dual-track truth: `RADE.md` is strategic and the current-slice docs plus tests are implementation truth
- 2026-03-18 - Replace faux tool branding with repo-owned `rade-proof` and `rade-devserver` launchers
- 2026-03-18 - Scrub report artifacts at write time while preserving stable structural identifiers
- 2026-03-19 - Default to PR-only changes on a protected `main` branch once GitHub settings are enabled
- 2026-03-19 - GitHub branch protection could not be enabled on this private repository because the current plan returned HTTP 403 for protection APIs
- 2026-03-19 - Harden input validation to reject self-parent references and non-string labels or traits before normalization
- 2026-03-19 - Enforce proof workflow and template coverage with repository contract tests
- 2026-03-19 - Reinforce the artifact scrub boundary with Markdown regression coverage

## Next immediate action

Draft the hosted persistence contract only after the current proof, validation, and doc-sync gates remain green.

## Stop conditions

Stop broadening work if:

- the current proof is still unverified
- new scope is being added without updating `docs/APP_SCOPE.md`
- docs and implementation diverge

## Truth discipline

This sheet tracks the deterministic proof path but is subordinate to the truth hierarchy in
`docs/TRUTH_HIERARCHY.md`. When doc drift is suspected, consult the ordered list in `README.md`
and align all affected entry docs before accepting a change. The canonical docs (`README.md`,
`docs/TRUTH_HIERARCHY.md`, `docs/APP_SCOPE.md`, `docs/BUILD_SHEET.md`, etc.) and executable
code/tests are the binding implementation truth; update them together to stay aligned with the
repo’s disciplined approach.
