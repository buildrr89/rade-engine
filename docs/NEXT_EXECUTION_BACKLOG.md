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

### 21. GitHub Action comment score-direction clarity

- Status: implemented 2026-03-27
- Result: PR comment now includes an explicit direction line clarifying that higher `reusability` is better and lower `accessibility_risk` is better. Existing score table and deterministic marker remain unchanged.

### 22. GitHub Action deterministic outputs contract

- Status: implemented 2026-03-27
- Risk reduced: downstream workflow drift when score-diff results are needed outside PR comment text
- Scope: expose deterministic action outputs for `gate-status`, `should-fail`, `reusability-delta`, and `accessibility-risk-delta` from the existing regression-evaluation step
- Acceptance: `action.yml` publishes stable output keys wired to `steps.regression.outputs.*`, regression step writes all output values to `$GITHUB_OUTPUT`, and contract tests lock the keys/wiring
- Does NOT include: changing regression predicates, adding new tracked metrics, or broadening non-PR workflow scope

### 23. PR workflow step-summary contract for Action outputs

- Status: implemented 2026-03-27
- Risk reduced: CI review ambiguity when Action output values are not visible in workflow summary
- Scope: wire the PR workflow to consume the existing Action outputs and publish deterministic summary lines for gate status/fail state and both tracked deltas
- Acceptance: `.github/workflows/pr-score-diff.yml` sets an explicit action step `id`, summary step writes all four values to `$GITHUB_STEP_SUMMARY`, and contract tests lock the output references
- Does NOT include: changing comment rendering, changing regression rules, or adding new score metrics

### 24. GitHub Action strict regression-input contract

- Status: implemented 2026-03-27
- Risk reduced: ambiguous CI behavior when `fail-on-regression` receives non-boolean string values
- Scope: enforce deterministic validation that `fail-on-regression` accepts only `"true"` or `"false"` in the action regression-evaluation step
- Acceptance: invalid values exit deterministically with explicit error text and contract tests lock the validation branch
- Does NOT include: changing regression predicates or introducing additional action inputs

### 25. GitHub Action regression-reason output contract

- Status: implemented 2026-03-27
- Risk reduced: downstream drift from inferring regression cause by re-parsing deltas externally
- Scope: expose deterministic `regression-reason` output with stable enum values (`none`, `reusability_down`, `accessibility_risk_up`, `both`)
- Acceptance: score-diff helper exposes deterministic reason classifier, action exports `regression-reason`, and tests lock both classifier behavior and output wiring
- Does NOT include: changing gate pass/fail status semantics or comment markdown structure

### 26. PR workflow regression-reason summary line

- Status: implemented 2026-03-27
- Risk reduced: reviewer ambiguity when gate failure reason is not visible in workflow summary
- Scope: add deterministic regression-reason line to `.github/workflows/pr-score-diff.yml` step summary using Action outputs
- Acceptance: workflow summary includes `steps.rade_score_diff.outputs.regression-reason` and contract tests lock the reference
- Does NOT include: adding new workflow jobs or changing PR trigger conditions

### 27. GitHub Action regression-detected output contract

- Status: implemented 2026-03-27
- Risk reduced: downstream drift when consumers infer regression presence indirectly from multiple fields
- Scope: expose deterministic `regression-detected` output (`true`/`false`) from the existing regression predicate
- Acceptance: `action.yml` publishes `regression-detected`, regression step writes `regression_detected=...` to `$GITHUB_OUTPUT`, and contract tests lock wiring
- Does NOT include: changing regression predicates or gate-status values

### 28. PR workflow regression-detected summary line

- Status: implemented 2026-03-27
- Risk reduced: reviewer ambiguity when summary lacks explicit regression presence flag
- Scope: add `regression-detected` line to the PR workflow summary from Action outputs
- Acceptance: `.github/workflows/pr-score-diff.yml` summary step references `steps.rade_score_diff.outputs.regression-detected` and contract tests lock it
- Does NOT include: changes to workflow triggers, permissions, or jobs

### 29. Gate/flag consistency contract lock

- Status: implemented 2026-03-27
- Risk reduced: contract drift between gate-status fail path and regression-flag output semantics
- Scope: lock that the action writes deterministic regression-flag output and retains explicit fail-path status assignment
- Acceptance: contract test asserts `enabled:failed` + `should_fail=true` fail-path literals and `regression_detected` output emission
- Does NOT include: runtime integration tests against live GitHub Actions

### 30. CodeQL workflow baseline contract

- Status: implemented 2026-03-27
- Risk reduced: missing static-analysis coverage for public repository pull requests and main-branch pushes
- Scope: add a minimal GitHub CodeQL workflow for Python and JavaScript with least-privilege permissions and deterministic trigger contract
- Acceptance: `.github/workflows/codeql.yml` runs on PR + `main` push + weekly schedule, sets `security-events: write`, and repository contract tests lock required workflow snippets
- Does NOT include: custom query packs, SARIF post-processing, or non-default CodeQL build strategies

### 31. CodeQL workflow execution hardening

- Status: implemented 2026-03-27
- Risk reduced: duplicate or long-running CodeQL jobs that increase CI queue time and cost
- Scope: add workflow-level concurrency cancellation and explicit job timeout to the existing CodeQL workflow
- Acceptance: `.github/workflows/codeql.yml` includes `concurrency` with `cancel-in-progress: true`, `analyze` job includes deterministic `timeout-minutes`, and repository contract tests lock these snippets
- Does NOT include: changing CodeQL query packs, language matrix, or trigger coverage

### 32. Deterministic report diff workflow

- Status: implemented 2026-04-10
- Risk reduced: one-shot report output that cannot show deterministic interface evolution over time
- Scope: add a local CLI workflow that compares two existing RADE JSON reports, reuses the existing score-diff semantics, highlights recommendation additions/removals and duplicate-cluster changes, and writes deterministic JSON plus Markdown diff artifacts
- Acceptance: `rade diff --base-report <base.json> --head-report <head.json>` writes deterministic `report_diff.json` and `report_diff.md`; score deltas are direction-aware for `complexity`, `reusability`, `accessibility_risk`, and `migration_risk`; recommendation and repeated-structure changes are stable and traceable by identifiers/fingerprints; CLI and artifact contract tests cover deterministic output and invalid-input failures
- Does NOT include: hosted persistence, historical storage, auth changes, tenant concepts, queues, private-page collection, or LLM-generated comparison logic

### 36. Packaging, PyPI publish, and hosted demo

- Status: implemented 2026-04-19
- Risk reduced: install friction (requiring clone + `uv sync`) and the lack of a hosted shareable artifact were the biggest remaining blockers to public-alpha adoption
- Scope: flip `pyproject.toml` to a real installable wheel under the PyPI name `rade-engine`, expose a `rade` console script, add a GitHub Actions workflow that publishes tagged releases to PyPI via OIDC trusted-publishing (no long-lived token), add a GitHub Pages workflow that rebuilds a live HTML report + SVG badges from the checked-in fixture on every push to main, and ship paste-ready HN/Reddit/Twitter launch copy in `docs/LAUNCH_POST.md`. The PyPI workflow requires a one-time trusted-publisher setup on pypi.org; no further per-release secrets are needed.
- Acceptance: `uv build` produces `rade_engine-0.1.0-py3-none-any.whl` and installing it exposes a working `rade --help`; `pytest` still passes against the new packaging; `.github/workflows/publish-pypi.yml` and `.github/workflows/deploy-pages.yml` are present with least-privilege permissions and pinned action SHAs where practical; README features `pip install rade-engine` as the primary install path; launch copy exists and is honest about current scope
- Does NOT include: rewriting the internal module layout into a `rade/` package, publishing the actual release (that happens when the maintainer tags `v0.1.0` and enables PyPI trusted publishing), or building a hosted dashboard

### 35. axe-core accessibility findings integration

- Status: implemented 2026-04-19
- Risk reduced: the accessibility_risk score is a bespoke RADE heuristic that is not grounded in a trusted third-party standard, which limits adoption for agencies and audit teams that already trust axe-core
- Scope: add an optional `--axe` flag on `rade analyze --url` that injects Deque's axe-core engine into the live Playwright page, runs `axe.run()`, and embeds the normalized violations in the generated report as a new `accessibility_violations` block. Findings carry explicit `provenance: "axe-core"`, WCAG tag refs, axe rule help URLs, and impact-to-priority mapping. The existing deterministic structural analysis, scoring, and report shape are unchanged when `--axe` is not set, so all existing golden fixtures remain valid.
- Acceptance: `rade analyze --url <url> --axe` attaches deterministic axe-core violations to the report without changing the existing contract; adapter exposes injected `script_loader`/`runner` seams so tests can exercise normalization, summarization, and error paths without a real browser; Markdown report renders a dedicated axe section when the block is present; CLI tests cover both the axe-on and axe-off paths; full test suite remains green
- Does NOT include: rescoring `accessibility_risk` against axe violations, offline vendoring of axe-core, axe custom rule configuration, SPA-aware axe runs, or authenticated/private-page collection

### 34. Deterministic SVG score badges

- Status: implemented 2026-04-19
- Risk reduced: public-alpha adoption is limited when score artifacts cannot be embedded as shareable README badges alongside existing JSON/Markdown/HTML reports
- Scope: add a `rade badge` CLI command that reads a RADE JSON report and writes a deterministic, compliance-compliant SVG badge for any of the four tracked score metrics, plus an optional shields.io dynamic endpoint JSON payload. Ship checked-in sample badges for `examples/python_org_homepage_report.json` and cover the new surface with contract tests.
- Acceptance: `rade badge --report <report.json> --metric <metric> --svg-output <svg> [--endpoint-output <json>]` produces byte-deterministic SVG and shields endpoint artifacts; color direction respects `reusability` (higher is better) versus `accessibility_risk`/`complexity`/`migration_risk` (lower is better); all emitted artifacts pass the sole-architect legal-metadata compliance tests; unknown metrics, invalid reports, and missing outputs fail deterministically; CLI contract tests cover the golden path and error paths
- Does NOT include: a hosted badge service, dynamic badge generation without a stored report, trend/spark visualizations, or non-shields badge formats

### 33. Same-surface before/after diff fixture pack

- Status: implemented 2026-04-10
- Risk reduced: report diff proof can look less truthful when it only compares unrelated public pages instead of a before/after evolution of the same interface family
- Scope: add a small checked-in before/after fixture pair for the same app surface, generate deterministic RADE reports for both runs, generate a checked-in diff artifact between those reports, and lock the pair in fixture regression tests
- Acceptance: `examples/legacy_repair_before.json` and `examples/legacy_repair_after.json` exist as the same-app before/after pair; checked-in reports exist for both fixtures with fixed timestamps; `examples/legacy_repair_same_surface_report_diff.json` and `.md` capture the deterministic diff between those reports; regression tests prove the checked-in reports still match pipeline output and the same-surface diff artifact still matches `build_report_diff()`
- Does NOT include: new collector surfaces, new diff semantics, hosted persistence, auth changes, tenant concepts, queues, or LLM-generated comparison logic
