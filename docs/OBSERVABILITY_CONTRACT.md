# OBSERVABILITY CONTRACT

## Purpose

Define the minimum telemetry footprint for the deterministic proof slice so future hosted execution can be measured and debugged without guessing. This contract keeps instrumentation lightweight while aligning with industry standards for structured logging, metrics, and error budgets.

## Logging

- Logs must be structured (JSON or equivalent) and include the fields: `run_id`, `tenant_id` (if present), `job_status`, `stage`, `duration_ms`, `error_message`, `error_code`, and `component` (`cli`, `worker`, or `persistence`). Each log record should be emitted through a single shared helper (e.g., `src.core.logging` once introduced) so the format remains stable.
- The CLI emits a `stage` entry for `load_payload`, `normalize`, `score`, `recommend`, and `report_write`. Each stage logs start and end events with durations so traces can be reconstructed.
- The worker emits logs when it claims a job (`claim_job`), starts replaying the CLI (`run_cli`), and finishes (`complete_job`). Failures include stack traces, sanitized error descriptions, and capture the deterministic `run_id`/`tenant_id` pair for traceability.
- Log output is scrubbed at the artifact boundary: only deterministic identifiers and reprimanded contextual strings (no raw tokens) are permitted, consistent with `docs/SECURITY_BASELINE.md`.

## Metrics

- Emit counters for `proof_runs.read`, `proof_runs.success`, `proof_runs.failure`, and `proof_runs.duration` (histogram) derived from CLI executions so success/failure rates are visible.
- Queue/worker-specific metrics include `job_queue.pending`, `job_queue.claimed`, `job_queue.completed`, `worker.errors`, and `artifact.storage.latency`. Each metric should tag on `component`, `priority`, and `scope` for filtering.
- Export metrics in a host-friendly format (e.g., Prometheus exposition or CSV for now) so external systems can consume them without new dependencies.

## Error budgets & alerts

- Define an error budget threshold (e.g., `errors/run` > 3% over a 24h rolling window) and document the alerting behavior alongside the metrics so the team knows when the proof path is unstable.
- Track `job_queue.backlog` and alert when the queue builds up beyond 5x the average job completion time, to catch deadlock or worker starvation early.

## Implementation notes

- CLI and worker instrumentation materialize the logging contract via `src/core/telemetry.py`; each stage (`load_payload`, `normalize`, `score`, `recommend`, `report_write` on the CLI plus `claim_job`, `run_cli`, `complete_job` on the worker) logs JSON events to `stderr`.
- Metrics are captured inside `src/core/metrics.py`, which increments counters for `proof_runs.read`, `proof_runs.success`, `proof_runs.failure`, and records the `proof_runs.duration` histogram. After each CLI run, `publish_metrics` emits a host-friendly JSON snapshot containing counters and duration summaries.

## Proof implication

Implementing this contract keeps instrumentation consistent even before hosted telemetry exists; it also sets expectations for structured events so future observability work can plug into the same fields without refactoring existing logs.
