# BUILD_SHEET

## Current objective

Keep the deterministic report path, the first Playwright collector path, and the exploratory blueprint path aligned with the actual repo state. The API now serves `POST /analyze` as a real analysis surface. Worker and web surfaces remain thin shells.

## Why this is the current objective

It keeps the proven core honest: report generation is the shipped proof slice, the Playwright URL collector is the smallest real acquisition surface, the blueprint path is a tested secondary track, and the shell entrypoints must not pretend to be more complete than they are.

## Current story

As a product team, I want to analyze an authorized fixture or a public web page and get a prioritized, evidence-backed modernization report without guessing what is actually implemented in the repo.

## Current proof slice

Fixture input or `--url` collection -> normalize -> fingerprint -> deduplicate -> score -> recommend -> JSON and Markdown output.

## Secondary proof slice

Accessibility-like tree -> construction graph -> deterministic SVG blueprint -> scrubbed Neo4j Aura ingest rows.

## Expected proof

- What must work: the sample command should complete and write both report files
- What must be observed: stable report content and deterministic recommendation order
- What counts as success: the same input yields the same output except `generated_at`
- What does not need to exist yet: hosted auth, queues, persistent history, or full collector coverage

## Latest proof

- Date: 2026-03-27
- Status: Passed
- Evidence:
  - `.venv/bin/python -m pytest -q` -> `155 passed in 0.43s`
  - `.venv/bin/python -m tests.runner` -> `155 passed, 0 failed`
  - `.venv/bin/ruff check src tests agent` -> `All checks passed!`
  - `.venv/bin/python -m black --check src tests agent` -> `87 files would be left unchanged.`
  - `pnpm --dir web lint` -> `RADE web shell lint passed`
  - `pnpm --dir web test` -> `RADE web shell smoke test passed against http://127.0.0.1:59374`
  - `make proof` -> `All proof gates passed.`
- `make analyze` -> `json: output/modernization_report.json`, `md: output/modernization_report.md`, `html: output/modernization_report.html`

### Milestone: GitHub Action PR score diff

- Added root `action.yml` (`RADE PR Score Diff`) with Marketplace metadata (`name`, `description`, `branding`) and composite steps to compare PR `base_sha` vs `head_sha`.
- Added `.github/workflows/pr-score-diff.yml` to run on PR open/reopen/synchronize and invoke the local action.
- Added `src/core/pr_score_diff.py` plus `scripts/pr_score_comment.py` to produce deterministic markdown comments with `reusability` and `accessibility_risk` deltas.
- Added `tests/test_pr_score_diff.py` to lock comment marker/table format and score-delta computation.

### Milestone: GitHub Action marketplace hardening

- Hardened `action.yml` runtime pathing to use `GITHUB_ACTION_PATH` for RADE source imports and script execution.
- Resolved fixture input via `GITHUB_WORKSPACE` so action consumers can run the action from their own repository checkout.
- Added explicit input-file existence failure in the action step for deterministic early error behavior.
- Added `tests/test_github_action_contract.py` to lock path-resolution contract.

### Milestone: GitHub Action regression gate

- Added optional `fail-on-regression` action input to fail CI when `reusability` drops or `accessibility_risk` rises from base to head.
- Added deterministic regression predicate `has_score_regression()` in `src/core/pr_score_diff.py`.
- Added regression tests in `tests/test_pr_score_diff.py` and action contract assertions in `tests/test_github_action_contract.py`.

### Milestone: GitHub Action gate-status comment clarity

- Action now computes regression gate status before comment rendering and includes status text in PR comments.
- Action order now ensures comment is posted/updated before final gate enforcement failure.
- Added tests to lock gate-status comment text and action contract wiring.

### Milestone: GitHub Action deterministic outputs contract

- Added action outputs in `action.yml` for `gate-status`, `should-fail`, `reusability-delta`, and `accessibility-risk-delta`.
- Regression-evaluation step now writes all four deterministic values to `$GITHUB_OUTPUT` alongside existing gate state.
- Added output-contract assertions in `tests/test_github_action_contract.py`.

### Milestone: PR workflow step-summary contract

- `.github/workflows/pr-score-diff.yml` now pins the local action step to `id: rade_score_diff` and consumes deterministic outputs from that step.
- Workflow now writes gate status, fail state, and both tracked deltas into `$GITHUB_STEP_SUMMARY` for deterministic reviewer visibility without parsing PR comment text.
- Added workflow-output wiring assertions in `tests/test_github_action_contract.py`.

### Milestone: Action input/reason contract hardening

- Action regression step now validates `fail-on-regression` input strictly to `"true"`/`"false"` and exits deterministically for invalid values.
- Added deterministic `regression_reason()` helper in `src/core/pr_score_diff.py` with stable reason codes (`none`, `reusability_down`, `accessibility_risk_up`, `both`), plus regression-reason unit tests.
- Action now exports `regression-reason`, and PR workflow summary now includes a regression-reason line sourced from Action outputs.
- Added action/workflow contract assertions for input validation and regression-reason wiring in `tests/test_github_action_contract.py`.

### Milestone: Regression-flag output and summary contract

- Action now exports deterministic `regression-detected` (`true`/`false`) alongside gate/delta/reason outputs.
- PR workflow summary now includes a `Regression detected` line sourced from action outputs.
- Added contract assertions to lock output wiring and gate/flag consistency literals in `tests/test_github_action_contract.py`.

### Milestone: CodeQL baseline workflow

- Added `.github/workflows/codeql.yml` with a minimal CodeQL matrix for `python` and `javascript`.
- Workflow triggers on pull requests to `main`, pushes to `main`, and weekly schedule; permissions are least-privilege with `security-events: write`.
- Added repository contract coverage in `tests/test_repo_contracts.py` to lock the CodeQL workflow trigger/permission/action snippets.

### Milestone: CodeQL execution hardening

- Added workflow-level concurrency to `.github/workflows/codeql.yml` with `cancel-in-progress: true` to avoid duplicate runs on rapid updates.
- Added explicit `timeout-minutes: 45` to the CodeQL `analyze` job for deterministic runtime bounds.
- Expanded `tests/test_repo_contracts.py` guardrails to lock concurrency and timeout snippets.

### Milestone: Three real-world fixture pack

- Added three public-page fixture snapshots under `examples/`: `python_org_homepage.json`, `mdn_homepage.json`, and `web_dev_homepage.json`.
- Added matching checked-in report artifacts under `examples/` for each fixture (`*_report.json` and `*_report.md`) using a fixed `generated_at` of `2026-03-22T00:00:00Z`.
- Added `tests/test_real_world_fixtures.py` to prove the checked-in reports still match pipeline output and remain deterministic.

### Milestone: Web DOM collector (Playwright)

- `src/collectors/web_dom_adapter.py` now collects public unauthenticated pages through Playwright, parses ARIA snapshots, and converts them into the RADE project schema.
- `src/core/cli.py` now accepts `--url` as an alternative to `--input` and derives `app_id` from the URL when one is not supplied.
- `agent/cli.py` forwards the same `--url` path through the agent shell.
- `tests/test_web_dom_adapter.py` and the new URL path in `tests/test_cli_contract.py` prove deterministic conversion and CLI output.

### Milestone: API auth boundary

- `src/api/wsgi.py` is the served API entry point for `POST /analyze`: it wraps the core `src/api/app.py` handler with auth middleware and returns scrubbed reports.
- `src/api/auth.py` provides `ApiKeyMiddleware`: static API key auth via `RADE_API_KEY` env var, constant-time comparison, fail-safe 503 if unconfigured.
- `src/api/app.py` remains the core handler beneath the served auth boundary.

### Previous milestones (same cycle)

- POST /analyze endpoint with 8 contract tests
- Compliance scan scope fix, capsys fixture support, black formatting restoration
- BUILD_SHEET corrected from `63 passed` to actual count

## Current blocker

No blocker on the deterministic report slice, exploratory blueprint test slice, or current lint/format gates.

Public GitHub repository is now created at `https://github.com/buildrr89/rade-engine`. Local docs and generated metadata are aligned to that public repository identity.

The ignored `rade-repo/` subtree remains outside canonical repo truth and should stay ignored or removed to avoid future compliance test contamination.

## Decision log

- 2026-03-18 - Use fixture-first bootstrap - keep the proof slice narrow
- 2026-03-18 - Favor deterministic core before web, hosted API, or collector expansion
- 2026-03-18 - Use dual-track truth: product definition plus current-slice docs/tests are separate from implementation proof
- 2026-03-18 - Replace faux tool branding with repo-owned `rade-proof` and `rade-devserver` launchers
- 2026-03-18 - Scrub report artifacts at write time while preserving stable structural identifiers
- 2026-03-19 - Default to PR-only changes on a protected `main` branch once GitHub settings are enabled
- 2026-03-19 - Historical note: branch protection could not be enabled on the earlier private repository because the current plan returned HTTP 403 for protection APIs
- 2026-03-19 - Harden input validation to reject self-parent references and non-string labels or traits before normalization
- 2026-03-19 - Enforce proof workflow and template coverage with repository contract tests
- 2026-03-19 - Reinforce the artifact scrub boundary with Markdown regression coverage
- 2026-03-21 - Replace stale `RADE.md` references with a current `PRD.md` because the strategic files are absent from the working tree
- 2026-03-21 - Document the blueprint / graph path as an implemented secondary proof slice rather than the main product workflow
- 2026-03-21 - Document API, worker, repo connector, and web surfaces as shells or stubs unless a proof command exercises real business behavior
- 2026-03-21 - Restore repo-wide Python import/format compliance and re-verify the official web lint command
- 2026-03-22 - Restore proof credibility: fix compliance scan scope, add capsys to custom runner, fix black drift on 7 files. Actual test count is 100, not 63.
- 2026-03-22 - Resolve PRD open decisions: `POST /analyze` is the next execution surface, blueprint path stays internal, repo connector stays as stub
- 2026-03-22 - Populate execution backlog with 7 ordered proof slices from `POST /analyze` through GitHub Action
- 2026-03-22 - Implement `POST /analyze` endpoint: 8 contract tests, 108 total tests passing. API is now a real surface, no longer a shell.
- 2026-03-22 - Add API auth middleware and WSGI entry point. 8 auth tests, 116 total tests passing.
- 2026-03-22 - Add three real-world web fixtures (`python.org`, `developer.mozilla.org`, `web.dev`) plus checked-in JSON/Markdown reports and deterministic regression coverage. 122 pytest cases and 118 custom-runner cases pass.
- 2026-03-22 - Implement Playwright-backed `--url` collection with ARIA snapshot parsing, semantic DOM fallback, agent-shell forwarding, and real CLI proof against `https://example.com`. Full gates pass with 122 pytest cases and 122 custom-runner cases.
- 2026-03-26 - public repo alignment: created `buildrr89/rade-engine`, switched repository posture to AGPL-3.0, updated public metadata/output wording, and re-generated checked-in proof artifacts to match the new public alpha story.
- 2026-03-27 - interactive HTML report: `render_html_report()` produces self-contained HTML with score bars, expandable findings/recommendations, category filters, and priority badges. `--html-output` on CLI and agent CLI. Golden fixture and 15 new tests. 137 total tests passing.
- 2026-03-27 - public alpha onboarding: improved README quickstart (Makefile-first, multiline commands, HTML output), expanded CONTRIBUTING with prerequisites/quickstart/formatting/where-to-start, added `make proof` target running all 6 gates via `.venv/bin/python`, added `--html-output` to Makefile analyze and CI workflow, added checked-in HTML example for python.org, fixed README API entry point to wsgi.py. 138 total tests passing.
- 2026-03-27 - GitHub Action CI/CD integration: added root `action.yml` and `.github/workflows/pr-score-diff.yml` to run RADE on PR base/head refs and post/update a deterministic score-diff comment for `reusability` and `accessibility_risk`. Added supporting helper module/script and regression tests.
- 2026-03-27 - GitHub Action marketplace hardening: action now resolves code and scripts from `GITHUB_ACTION_PATH` and fixture input from `GITHUB_WORKSPACE` for external action consumers, with deterministic missing-input failure and path-contract regression coverage.
- 2026-03-27 - GitHub Action regression gate: optional `fail-on-regression` input now enforces CI failure when reusability regresses or accessibility risk increases; deterministic regression rule and action contract are test-locked.
- 2026-03-27 - GitHub Action gate-status comment clarity: PR comments now include explicit regression gate status, and workflow ordering posts comment before optional failure enforcement.
- 2026-03-27 - GitHub Action deterministic outputs contract: composite action now exports stable output keys for gate status/fail state and both tracked score deltas so downstream workflows can consume values without parsing comment markdown.
- 2026-03-27 - PR workflow step-summary contract: PR workflow now consumes local action outputs via a stable step id and writes deterministic gate/delta lines to the GitHub Actions step summary.
- 2026-03-27 - Action input/reason contract hardening: fail-on-regression input now enforces strict boolean-string values, action exports deterministic regression reason code, and PR workflow summary surfaces that reason for reviewer clarity.
- 2026-03-27 - Regression-flag output and summary contract: action now exports explicit regression-detected flag and workflow summary includes that flag to reduce ambiguity for downstream consumers and reviewers.
- 2026-03-27 - CodeQL baseline workflow: added GitHub CodeQL analysis for Python and JavaScript on PR/push/schedule with least-privilege permissions and contract-test coverage.
- 2026-03-27 - CodeQL execution hardening: added concurrency cancellation and explicit timeout to reduce duplicate CodeQL runs and cap job runtime deterministically.

## Next immediate action

Define slice #32 in `docs/NEXT_EXECUTION_BACKLOG.md` (currently `UNKNOWN / NEEDS DECISION`) before implementation.

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
