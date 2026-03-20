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

- Status: implemented in [.github/workflows/proof.yml](/Users/restolad/Desktop/RADE/.github/workflows/proof.yml), [.github/pull_request_template.md](/Users/restolad/Desktop/RADE/.github/pull_request_template.md), [.github/ISSUE_TEMPLATE/bug_report.md](/Users/restolad/Desktop/RADE/.github/ISSUE_TEMPLATE/bug_report.md), and [.github/ISSUE_TEMPLATE/feature_request.md](/Users/restolad/Desktop/RADE/.github/ISSUE_TEMPLATE/feature_request.md)
- Result: the proof workflow and template guardrails are now covered by repository contract tests

### 3. Report artifact scrub boundary

- Status: implemented in [src/core/report_generator.py](/Users/restolad/Desktop/RADE/src/core/report_generator.py), [src/scrubber/pii_scrubber.py](/Users/restolad/Desktop/RADE/src/scrubber/pii_scrubber.py), and [tests/test_scrubber.py](/Users/restolad/Desktop/RADE/tests/test_scrubber.py)
- Result: artifacts are scrubbed before JSON and Markdown writes, including a regression test that proves the Markdown renderer never exposes sensitive strings

### 4. Input contract hardening

- Status: implemented in [src/core/schemas.py](/Users/restolad/Desktop/RADE/src/core/schemas.py) and [tests/test_schemas.py](/Users/restolad/Desktop/RADE/tests/test_schemas.py)
- Result: invalid self-parent references, non-string labels, and non-string trait entries are rejected before normalization

### 5. Stable report identifiers

- Status: implemented in [tests/test_recommendation_engine.py](/Users/restolad/Desktop/RADE/tests/test_recommendation_engine.py) and [docs/MVP_REPORT_SPEC.md](/Users/restolad/Desktop/RADE/docs/MVP_REPORT_SPEC.md)
- Result: recommendations now prove their evidence references immutable `node_ref`, `rule_id`, and fingerprint identifiers while documenting the deterministic `recommendation_id` derivation required by the MVP spec

### 6. Hosted persistence contract

- Status: implemented in [docs/ARCHITECTURE.md](/Users/restolad/Desktop/RADE/docs/ARCHITECTURE.md) and [docs/SECURITY_BASELINE.md](/Users/restolad/Desktop/RADE/docs/SECURITY_BASELINE.md)
- Result: hosted-mode persistence now has tenant-aware schema, RLS expectations, and audit/retention controls that mirror the proof slice’s deterministic identifiers

### 7. Queue and worker boundary

- Status: implemented in [docs/QUEUE_WORKER_BOUNDARY.md](/Users/restolad/Desktop/RADE/docs/QUEUE_WORKER_BOUNDARY.md)
- Result: the minimal queue/worker contract now documents job/job state shape, tenant isolation expectations, and worker responsibilities for deterministic proof runs

### 8. Repo connector shell

- Status: implemented in [src/connectors/repo_connector.py](/Users/restolad/Desktop/RADE/src/connectors/repo_connector.py), [tests/test_repo_connector.py](/Users/restolad/Desktop/RADE/tests/test_repo_connector.py), and [docs/REPO_CONNECTOR_SPEC.md](/Users/restolad/Desktop/RADE/docs/REPO_CONNECTOR_SPEC.md)
- Result: the stub connector now exposes deterministic repository metadata and is covered by a regression test and spec that guarantee the shape stays stable

### 9. Observability contract

- Status: implemented in [docs/OBSERVABILITY_CONTRACT.md](/Users/restolad/Desktop/RADE/docs/OBSERVABILITY_CONTRACT.md)
- Result: structured logging, queue/worker metrics, and error budget guardrails are now documented so future hosted monitoring can align with the proof slice’s deterministic identifiers

## Backlog

No additional proof slices are queued at the moment; add new tasks once the current enforcement guardrails stay proven and a new deterministic risk slice is identified.
