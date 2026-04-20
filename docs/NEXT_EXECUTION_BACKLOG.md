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

### 45. Link CHANGELOG from README

- Status: implemented 2026-04-20
- Risk reduced: slice #40 shipped `CHANGELOG.md` but it was reachable only by knowing the filename. The Contributing section was the natural place to cross-link it so contributors actually find release-by-release context.
- Scope: single bullet added to README Contributing section pointing at `CHANGELOG.md`.
- Acceptance: README links to `CHANGELOG.md`; no other changes
- Does NOT include: generating release notes automatically, splitting the changelog by version, or restructuring the README

### 52. Case-insensitive Bearer scheme in API auth middleware

- Status: implemented 2026-04-19
- Risk reduced: `ApiKeyMiddleware._extract_bearer_token()` compared the Authorization header with `startswith("Bearer ")` (capital-B only). RFC 6750 §2.1 is explicit that the auth scheme is case-insensitive, so a client sending `bearer <token>` or `BEARER <token>` — both spec-compliant — would be rejected with `missing_token`. For a hosted-mode surface advertised as accepting Bearer auth, that's a real interoperability bug waiting for its first non-curl client.
- Scope: rewrite `_extract_bearer_token()` to partition the header on the first space and compare the scheme lower-cased. Coerce the header to `str()` for robustness against non-string environ values. Add `test_bearer_scheme_is_case_insensitive` to `tests/test_api_auth.py` using lowercase `bearer`. No behaviour change for the existing title-case path or for missing/empty headers.
- Acceptance: 212 pytest pass; existing 8 auth tests still pass unchanged; new test asserts `200 OK` for lowercase `bearer`
- Does NOT include: supporting multiple auth schemes (Basic, Digest), token introspection, JWT validation, rate limiting, or touching the constant-time comparison

### 50. Harden publish-pypi workflow against accidental manual publishes

- Status: implemented 2026-04-19
- Risk reduced: the release workflow was triggered on `release: published` (intended path) but also on `workflow_dispatch` with a `dry_run` input that defaulted to `"false"`. That meant any maintainer clicking "Run workflow" without reading the form would immediately publish a half-built wheel to PyPI — there is no undo for a PyPI version. The `if:` gate also used a negative-form predicate (`inputs.dry_run != 'true'`) which fails open on any unexpected input value. For a first-release repo wired to a trusted publisher, the safety margin needs to be the other direction.
- Scope: flip `workflow_dispatch.inputs.dry_run.default` to `"true"` so manual runs are dry by default. Tighten the publish job's `if:` to an explicit positive predicate: `github.event_name == 'release' || (github.event_name == 'workflow_dispatch' && inputs.dry_run == 'false')`. Add `test_publish_pypi_workflow_requires_explicit_manual_publish_opt_in` to `tests/test_repo_contracts.py` locking both strings in place so this can't quietly regress.
- Acceptance: 211 pytest pass; release-triggered publishes still run (no change to the `release: published` path); `workflow_dispatch` with no input changes now only builds; `workflow_dispatch` with `dry_run=false` publishes; contract test fails if either string drifts
- Does NOT include: changing the trusted-publisher config on PyPI, moving to manual version tagging, adding a second reviewer gate, or per-environment approvals

### 49. Drop CodeQL badge from README banner

- Status: implemented 2026-04-19
- Risk reduced: slice #47 added a CodeQL badge pointing at `.github/workflows/codeql.yml`, but that workflow is `disabled_manually` on `buildrr89/rade-engine` because the maintainer uses GitHub's default CodeQL setup instead (which runs via the internal `dynamic/github-code-scanning/codeql` pipeline and exposes no workflow-file badge URL). The badge therefore renders "no status" — worse than no badge at all on a public-alpha landing page. Security scanning itself is unaffected.
- Scope: remove the `[![CodeQL](...codeql.yml/badge.svg)]` line from the README banner. No other file changes.
- Acceptance: 210 tests still pass; banner carries four badges (Proof, Wheel smoke, License, Python); no broken/grey CI badge on the landing page
- Does NOT include: re-enabling the workflow file, switching away from default setup, adding a Dependabot or PyPI version badge, or touching any other README section

### 48. Unbreak the proof workflow on main (sitecustomize stdout pollution)

- Status: implemented 2026-04-19
- Risk reduced: `proof` has been red on `main` since at least March because `sitecustomize.py` unconditionally prints the terminal banner on every Python process start. `uv run <python>` introspects the venv's interpreter by parsing its stdout as JSON; the banner appears before the JSON response and corrupts uv's parse (`Querying Python at \`.venv/bin/python3\` returned an invalid response: expected value at line 1 column 1`). Every new slice was merging against a broken signal — we had no protection against a real proof regression because proof was already red for an unrelated reason. This slice makes the `proof` badge on the README honest again.
- Scope: gate the `emit_terminal_banner()` call in `sitecustomize.py` on `sys.stdout.isatty()`. CLI entry points (`agent/cli.py`, `tests/runner.py`, `src/core/cli.py`) already call `emit_terminal_banner()` explicitly for user-facing invocations, so this only suppresses the banner during non-interactive subprocess introspection. No other code paths change.
- Acceptance: full 210-test suite still passes; `./rade-proof` runs to completion locally printing `210 passed, 0 failed` (previously failed immediately on uv bootstrap); the `proof` workflow on the PR goes green for the first time in months
- Does NOT include: removing the banner entirely, refactoring the compliance module, adding a new env var to control banner emission, or fixing any of the `[RADE DIAG]` stderr lines that also appear in proof output

### 47. Professional-repo polish: CI status badges in README

- Status: implemented 2026-04-19
- Risk reduced: the README advertised only the `Proof` workflow badge, leaving the `wheel-smoke` (Python 3.12/3.13/3.14 install verification from slice #44) and `CodeQL` (security scanning) workflows invisible at the repo landing page. A public-alpha PyPI candidate should surface its full CI signal — missing badges erode credibility and hide the guardrails that actually ship with the package. Adding License and Python-version badges also makes the install surface readable at a glance.
- Scope: in `README.md`, replace the single `![Proof]` image with a five-badge block: Proof (clickable to its workflow), Wheel smoke (clickable to `wheel-smoke.yml`), CodeQL (clickable to `codeql.yml`), a static License: AGPL-3.0 badge linking to `LICENSE`, and a static Python 3.12 | 3.13 | 3.14 badge linking to `pyproject.toml`. All three workflow badges point at workflow files that already exist in `.github/workflows/`.
- Acceptance: 210 pytest pass unchanged; all three referenced workflows exist on disk; each badge image URL is paired with a clickable link target; no code changes
- Does NOT include: Codecov/coverage badges (no coverage tool wired yet), PyPI version badge (package not yet published), downloads badge, or per-OS matrix badges

### 46. Golden axe-gate fixture pair

- Status: implemented 2026-04-20
- Risk reduced: slice #41 shipped `has_axe_regression()` and the `fail-on-axe-regression` Action input, but no checked-in fixture exercised the gate end-to-end. All axe-gate test cases built reports inline in `tests/test_pr_score_diff.py`, meaning a regression that changed the on-disk report shape or the `accessibility_violations` serialization could silently bypass the gate without any test noticing. A checked-in pair locks the gate against that drift.
- Scope: add `tests/fixtures/axe_gate_base.json` (one pre-existing `moderate` `image-alt` violation) and `tests/fixtures/axe_gate_head.json` (same `moderate` finding plus a newly-introduced `critical` `color-contrast` rule). Both files carry the required `rade_legal` header for compliance. New `tests/test_axe_gate_fixtures.py` loads the pair via `load_report()`, asserts the exact delta shape, asserts the gate fires with reason `critical_introduced`, verifies the rendered PR comment line for the `Axe regression gate status: enabled:failed` case, and asserts build determinism across repeated calls.
- Acceptance: full pytest suite stays green at 210 passing; the two JSON fixtures pass the sole-architect JSON compliance check; the rendered comment contains the expected `Newly introduced critical rules: color-contrast` line; fixtures are stable byte-for-byte across repeated `build_axe_diff()` calls
- Does NOT include: generating the fixtures from a live Playwright run, adding a matching CLI-level e2e test, or exercising the `enabled:passed` / `none` / `serious_introduced` gate branches (already covered by inline tests in `test_pr_score_diff.py`)

### 44. Wheel smoke test + Python 3.12/3.13 syntax fix

- Status: implemented 2026-04-20
- Risk reduced: `pyproject.toml` advertises `requires-python = ">=3.12"` and ships 3.12/3.13/3.14 classifiers, but nothing in CI actually verified the wheel installs and the `rade` CLI runs on any version other than the 3.14 dev environment. A local smoke test against a clean 3.12 venv surfaced six real `except A, B:` Python-2 syntax sites in `src/engine/rade_orchestrator.py` and `src/core/slab03_hybrid_anchor.py` that Python 3.14 silently accepts (PEP 758 relaxed the parse rule) but 3.12 and 3.13 reject at import time. In other words, the package as shipped before this slice was broken for two of its three advertised Python versions.
- Scope: (a) fix all six `except TypeError, ValueError:` → `except (TypeError, ValueError):` sites so the package actually parses on 3.12/3.13; (b) add `.github/workflows/wheel-smoke.yml` that on PR / push-to-main builds `dist/*.whl`, installs it into clean `.venv-smoke` venvs on 3.12, 3.13, and 3.14 in a matrix, runs `rade --help / analyze --help / diff --help / badge --help`, installs the `[graph]` extra and verifies `neo4j` imports, and separately verifies a base install does NOT pull `neo4j`.
- Acceptance: full pytest suite still passes (206); `uv build` → `uv pip install dist/rade_engine-0.1.0-py3-none-any.whl` → `rade --help` works on a clean Python 3.12 venv locally; workflow uses env-var indirection for matrix value interpolation per the workflow-injection security pattern
- Does NOT include: publishing to PyPI, reworking the internal package layout, adding 3.11 or earlier support, or wiring the smoke test into the existing pr-score-diff workflow

### 43. README docs pass for axe gate and graph extra

- Status: implemented 2026-04-20
- Risk reduced: slices #37 and #41 shipped user-facing surfaces (the `[graph]` pip extra and the `fail-on-axe-regression` Action input) that were reachable only by reading the backlog or the code. External consumers had no canonical doc showing how to wire either one. That's a credibility problem on a public-alpha repo.
- Scope: add a dedicated `## GitHub Action` section to `README.md` with a minimal working YAML example that uses both `fail-on-regression` and `fail-on-axe-regression`, and an inventory of the 9 deterministic outputs. Tighten the existing Features bullet to mention the axe gate, and the Output Artifacts bullet to mention the `Accessibility violations (axe-core)` PR subsection when fixtures include axe output. The `[graph]` extra callout from slice #37 already exists in the Install section and needs no further edits.
- Acceptance: README carries a `## GitHub Action` section with a copy-pasteable YAML snippet pinning a release tag; mentions `fail-on-axe-regression` and the three new outputs; explicitly states the gate semantics (newly-introduced critical/serious only); test suite unchanged (206 passing)
- Does NOT include: a standalone Action README inside a `docs/` directory, marketplace listing copy, per-input tables, or any code changes

### 42. PR workflow step-summary surfaces axe gate outputs

- Status: implemented 2026-04-20
- Risk reduced: slice #41 exposed three new Action outputs (`axe-gate-status`, `axe-regression-detected`, `axe-regression-reason`) but the PR workflow's GITHUB_STEP_SUMMARY still only rendered the score-gate lines. Without surfacing axe outputs in the step summary, reviewers scanning the Actions tab would miss whether the axe gate fired at all — breaking the visibility invariant that #23/#26/#28 established for the score gate.
- Scope: extend `.github/workflows/pr-score-diff.yml` to emit three additional summary lines for the axe outputs. Switch all output interpolation to env-var indirection to comply with the workflow-injection security pattern even though the values are Action-owned status codes (not user-controlled). Contract test in `tests/test_github_action_contract.py` asserts the three new `steps.rade_score_diff.outputs.axe-*` references are wired through.
- Acceptance: workflow file contains exactly three new `echo` lines for axe gate status / regression reason / regression detected; env-var indirection is used for all interpolations; `tests/test_github_action_contract.py::test_pr_workflow_consumes_action_outputs_in_summary` asserts the new wiring; 206 tests stay green
- Does NOT include: new Action inputs, new Action outputs, score-gate direction changes, or per-impact gate configuration

### 41. Opt-in axe-core regression gate on the GitHub Action

- Status: implemented 2026-04-20
- Risk reduced: slice #38 made axe deltas visible in the PR comment but left them toothless — teams that want axe to actually block merges had no lever. Gating on total count is too noisy (any new `minor` finding would fire); gating on newly-introduced `critical`/`serious` rules matches how real a11y programs operate and avoids punishing pre-existing debt.
- Scope: extend `build_axe_diff()` with a `newly_introduced_by_impact` bucketing derived from head-side findings, plus `has_axe_regression()` and `axe_regression_reason()` helpers. Add a new `fail-on-axe-regression` Action input (default `"false"`) that gates independently of the existing `fail-on-regression` score gate — both gates are OR'd into `should-fail`. Add three new deterministic outputs: `axe-gate-status`, `axe-regression-detected`, `axe-regression-reason`. The PR comment's `Accessibility violations (axe-core)` subsection now leads with an `Axe regression gate status` line and lists newly-introduced critical/serious rules explicitly.
- Acceptance: new cases in `tests/test_pr_score_diff.py` cover (a) gate fires on newly-introduced critical, (b) fires on newly-introduced serious, (c) fires on both with reason `"both"`, (d) does not fire when only `moderate`/`minor` are introduced, (e) does not fire when a pre-existing `critical` rule's count grows without introducing new rule IDs, (f) absent-on-both-sides stays `none`. `tests/test_github_action_contract.py` asserts the new input, outputs, and input-validation predicate. All 206 tests pass; existing golden-output tests are unchanged.
- Does NOT include: per-impact thresholds exposed as Action inputs, node-target-level gating, rescoring `accessibility_risk` against axe findings, or changing the score-gate direction rules

### 40. CHANGELOG.md for public-alpha release

- Status: implemented 2026-04-20
- Risk reduced: PyPI v0.1.0 is pending a maintainer tag, and without a curated changelog the first external release notes would be raw `git log` output — unreadable for adopters and hostile to downstream security reviewers who need to see what actually changed between slices.
- Scope: add `CHANGELOG.md` at the repo root covering the path from slice #1 shell through slices #32–#39 under an `[Unreleased]` / `[0.1.0]` pair, grouped by Keep-a-Changelog sections (Added / Changed / Security). Include the file in the hatch sdist include list so it ships with the wheel.
- Acceptance: `CHANGELOG.md` exists, reflects the as-shipped state of the branch (slices #32–#39), and does not claim features beyond what the code supports; `pyproject.toml` sdist includes `CHANGELOG.md`; test suite stays green
- Does NOT include: a release-notes automation (towncrier / release-drafter), v0.1.0 tagging, or backfilling entries for every historical slice below #32

### 39. Drop neo4j from GitHub Action runtime install

- Status: implemented 2026-04-20
- Risk reduced: slice #37 made `neo4j` an optional extra at the package level, but `action.yml`'s runtime-deps step still `pip install`ed it on every PR run — wasting ~40MB of bandwidth and cold-start time for every Action consumer, who by definition never exercises the Neo4j Aura ingest path from inside the Action.
- Scope: remove `neo4j` from the `Install RADE runtime dependencies` step in `action.yml`. No new inputs, no test changes — the graph ingest path is not reachable from the Action's CLI invocation, so dropping the driver there has no runtime effect.
- Acceptance: full test suite stays green; `action.yml` contract tests still pass; Action runtime install is now `playwright pyyaml` only
- Does NOT include: switching the Action to install from PyPI, pinning transitive deps, or changing the Action's CLI surface

### 38. axe-core violations in PR score-diff comment

- Status: implemented 2026-04-20
- Risk reduced: `--axe` is the headline credibility feature, but the PR score-diff comment was structural-only. Teams reviewing PRs could not see axe findings where they actually decide — making the axe surface effectively invisible to the adoption audience.
- Scope: add `build_axe_diff(base_report, head_report)` to `src/core/pr_score_diff.py` that returns a deterministic, rule-id-granularity delta: per-impact counts (critical/serious/moderate/minor), total delta, and sorted `newly_introduced_rule_ids` / `fully_resolved_rule_ids` sets. Handles both-sides-have-axe, head-only, base-only, and neither-side. `render_pr_comment()` gains an optional `axe_diff` parameter; when present, a dedicated `### Accessibility violations (axe-core)` subsection is appended below the score table. `scripts/pr_score_comment.py` now computes the axe diff and threads it through. When neither side has axe data, the section is omitted entirely — the existing comment shape is unchanged.
- Acceptance: `tests/test_pr_score_diff.py` covers both-sides-have-axe, head-only, base-only, neither-side, determinism across repeated calls, and the comment-with-axe vs comment-without-axe rendering contracts; all previously-green tests still pass (198 total); regression gate is unchanged — axe deltas are reported, not enforced, in this slice
- Does NOT include: turning axe into a gate, new Action inputs, rescoring `accessibility_risk` against axe violations, node-target-level pairing, or score-direction changes

### 37. Optional `graph` extra for Neo4j driver

- Status: implemented 2026-04-19
- Risk reduced: every `pip install rade-engine` pulled in the ~40MB neo4j driver even though the Neo4j Aura ingest path is an exploratory/secondary surface — a poor first-install experience for accessibility-focused users who will never touch the graph path
- Scope: move `neo4j>=6.1.0` out of base `[project.dependencies]` into `[project.optional-dependencies] graph`; the single `from neo4j import GraphDatabase` site in `src/database/graph_ingestor.py` was already lazy and now raises `ImportError("Install rade-engine[graph] to use the Neo4j ingest path.")` when the driver is absent. README install section now documents the `pip install 'rade-engine[graph]'` path for Neo4j ingest users.
- Acceptance: `tests/test_neo4j_optional.py` proves `src.core.cli` and `src.database.graph_ingestor` import cleanly with `neo4j` shadowed out of `sys.modules`, and that `RadeGraphIngestor._session()` raises a clear `ImportError` pointing at the extra; full pytest suite stays green; existing `test_graph_ingestor.py` continues to exercise the ingest surface through the injected driver seam
- Does NOT include: rewriting the ingest surface, adding new graph features, removing the ingest code, or renaming the existing module layout

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
