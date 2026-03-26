# NEXT_EXECUTION_BACKLOG

## Rules

- Only include the next 5 to 10 slices
- Each slice must be small and testable
- Order by risk reduction first
- No vague epics

## Completed

### 1. Truth hierarchy and doc drift enforcement

- Status: implemented in `README.md`, `docs/APP_SCOPE.md`, and `docs/BUILD_SHEET.md`
- Result: the entry docs explicitly cite `docs/TRUTH_HIERARCHY.md`, describe the ordered truth adjudication, and instruct contributors to update canonical docs alongside implementation changes when behaviors/contracts shift.

### 2. Proof workflow and template enforcement

- Status: implemented in [.github/workflows/proof.yml](../.github/workflows/proof.yml), [.github/pull_request_template.md](../.github/pull_request_template.md), [.github/ISSUE_TEMPLATE/bug_report.md](../.github/ISSUE_TEMPLATE/bug_report.md), and [.github/ISSUE_TEMPLATE/feature_request.md](../.github/ISSUE_TEMPLATE/feature_request.md)
- Result: the proof workflow and template guardrails are now covered by repository contract tests

### 3. Report artifact scrub boundary

- Status: implemented in [src/core/report_generator.py](../src/core/report_generator.py), [src/scrubber/pii_scrubber.py](../src/scrubber/pii_scrubber.py), and [tests/test_scrubber.py](../tests/test_scrubber.py)
- Result: artifacts are scrubbed before JSON and Markdown writes, including a regression test that proves the Markdown renderer never exposes sensitive strings

### 4. Input contract hardening

- Status: implemented in [src/core/schemas.py](../src/core/schemas.py) and [tests/test_schemas.py](../tests/test_schemas.py)
- Result: invalid self-parent references, non-string labels, and non-string trait entries are rejected before normalization

### 5. Stable report identifiers

- Status: implemented in [tests/test_recommendation_engine.py](../tests/test_recommendation_engine.py) and [docs/MVP_REPORT_SPEC.md](../docs/MVP_REPORT_SPEC.md)
- Result: recommendations now prove their evidence references immutable `node_ref`, `rule_id`, and fingerprint identifiers while documenting the deterministic `recommendation_id` derivation required by the MVP spec

### 6. Hosted persistence contract

- Status: documented as a deferred contract in [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) and [docs/SECURITY_BASELINE.md](../docs/SECURITY_BASELINE.md)
- Result: hosted-mode persistence expectations are written down as a future contract, but they are not current runtime claims for this proof slice

### 7. Queue and worker boundary

- Status: documented as a deferred contract in [docs/QUEUE_WORKER_BOUNDARY.md](../docs/QUEUE_WORKER_BOUNDARY.md)
- Result: the minimal queue/worker contract is written down for future implementation, but the current worker surface remains a shell

### 8. Repo connector shell

- Status: implemented in [src/connectors/repo_connector.py](../src/connectors/repo_connector.py), [tests/test_repo_connector.py](../tests/test_repo_connector.py), and [docs/REPO_CONNECTOR_SPEC.md](../docs/REPO_CONNECTOR_SPEC.md)
- Result: the stub connector now exposes deterministic repository metadata and is covered by a regression test and spec that guarantee the shape stays stable

### 9. Observability contract

- Status: documented as a deferred contract in [docs/OBSERVABILITY_CONTRACT.md](../docs/OBSERVABILITY_CONTRACT.md)
- Result: observability expectations are documented for future hosted work, but they are not a claim of current hosted monitoring or queue metrics

### 10. Proof credibility restoration

- Status: implemented 2026-03-22
- Result: all 100 tests pass in both pytest and custom runner. Compliance scan excludes non-RADE directories (`.claude/`, `rade-repo/`). Custom runner handles `capsys` fixture. Black formatting restored on 7 drifted files. BUILD_SHEET updated with honest current state. PRD open decisions resolved.

### 11. `POST /analyze` API endpoint

- Status: implemented 2026-03-22
- Result: `src/api/app.py` accepts JSON payloads via `POST /analyze`, runs the deterministic pipeline, returns scrubbed reports. 8 contract tests in `tests/test_api_contract.py` cover golden path, determinism, and 6 error cases. Error responses for empty body (400), invalid JSON (400), non-object (400), missing app_id (400), invalid payload (422), wrong method (405), payload too large (413), and analysis failure (500).

### 12. API auth and WSGI boundary

- Status: implemented 2026-03-22
- Result: `src/api/auth.py` adds `ApiKeyMiddleware` with constant-time comparison and fail-safe 503 behavior, and `src/api/wsgi.py` provides a WSGI entry point that wraps the app with auth. 8 auth middleware tests in `tests/test_api_auth.py`.

### 13. Three real-world fixtures

- Status: implemented 2026-03-22
- Result: added [examples/python_org_homepage.json](../examples/python_org_homepage.json), [examples/mdn_homepage.json](../examples/mdn_homepage.json), and [examples/web_dev_homepage.json](../examples/web_dev_homepage.json) with matching checked-in reports under `examples/`. [tests/test_real_world_fixtures.py](../tests/test_real_world_fixtures.py) proves those outputs still match the deterministic pipeline at a fixed timestamp.

### 14. Web DOM collector (Playwright)

- Status: implemented 2026-03-22
- Result: [src/collectors/web_dom_adapter.py](../src/collectors/web_dom_adapter.py) now collects public unauthenticated `http/https` pages through Playwright ARIA snapshots, converts them into the RADE schema, and falls back to semantic DOM extraction if needed. [src/core/cli.py](../src/core/cli.py) and [agent/cli.py](../agent/cli.py) now accept `--url`, and [tests/test_web_dom_adapter.py](../tests/test_web_dom_adapter.py) plus [tests/test_cli_contract.py](../tests/test_cli_contract.py) cover the new path. Real proof command: `rade analyze --url https://example.com`.

### 15. Interactive HTML report

- Status: implemented 2026-03-27
- Result: `render_html_report()` in `src/core/report_generator.py` produces a self-contained HTML report with score-bar visualizations, expandable finding and recommendation cards, category filter buttons, priority badges, and responsive layout. `--html-output` flag added to CLI (`src/core/cli.py`) and agent CLI (`agent/cli.py`). `write_report()` and `analyze_file()` accept `html_output`. Golden fixture at `tests/golden/sample_modernization_report.html`. 14 new tests in `tests/test_html_report.py` plus 1 golden contract test in `tests/test_report_generator.py`. 137 total tests passing.

### 16. Public alpha onboarding

- Status: implemented 2026-03-27
- Result: README refactored with Makefile-first quickstart, multiline CLI commands, HTML output coverage, and corrected API entry point (`wsgi.py`). CONTRIBUTING expanded with prerequisites, clone-to-proof quickstart, formatting instructions, and where-to-start guidance. Makefile gains `make proof` target (all 6 gates via `.venv/bin/python`), `--html-output` in `make analyze`, and `*.html` in `make clean`. CI workflow updated to produce HTML output. Checked-in HTML example at `examples/python_org_homepage_report.html` with contract test. Examples section in README now links all three output formats. 138 total tests passing.

### 17. GitHub Action

- Status: implemented 2026-03-27
- Result: added marketplace-ready root `action.yml` (`RADE PR Score Diff`) and PR workflow `.github/workflows/pr-score-diff.yml` to run on PR open/reopen/synchronize. The action compares base/head commits by running `rade analyze` against the fixture input and posts/updates a PR comment with deterministic `reusability` and `accessibility_risk` score deltas. Added helper module `src/core/pr_score_diff.py`, comment builder script `scripts/pr_score_comment.py`, and tests in `tests/test_pr_score_diff.py`.

## Backlog

### 18. GitHub Action marketplace hardening

- Status: implemented 2026-03-27
- Result: hardened `action.yml` for external Marketplace-style use by resolving action code from `GITHUB_ACTION_PATH` and fixture input from `GITHUB_WORKSPACE`, plus explicit input-file existence failure. Added `tests/test_github_action_contract.py` to lock these path contracts.

### 19. GitHub Action regression gate

- Status: implemented 2026-03-27
- Result: added optional `fail-on-regression` input in `action.yml`. When enabled, the action fails if `reusability` decreases or `accessibility_risk` increases between base/head reports, while still preserving deterministic score-diff behavior. Added regression-rule tests in `tests/test_pr_score_diff.py` and action contract assertions in `tests/test_github_action_contract.py`.

### 20. GitHub Action comment gate-status clarity

- Status: implemented 2026-03-27
- Result: action comment now includes explicit regression gate status (`disabled`, `enabled:passed`, or `enabled:failed`). Action flow now computes gate status before commenting, always posts/updates the PR comment, and then enforces failure when configured and regressed. Tests updated in `tests/test_pr_score_diff.py` and `tests/test_github_action_contract.py`.

### 21. UNKNOWN / NEEDS DECISION

- Risk reduced: UNKNOWN / NEEDS DECISION
- Scope: define the next smallest proof slice after GitHub Action comment gate-status clarity
- Acceptance: explicit slice statement with deterministic proof gates
- Does NOT include: unscoped platform expansion
