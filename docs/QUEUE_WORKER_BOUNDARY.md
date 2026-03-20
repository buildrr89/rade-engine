# QUEUE & WORKER BOUNDARY

## Purpose

This contract defines how the next execution slice should enqueue deterministic analysis jobs and how the worker shell processes them in a minimal, proof‑friendly way.

## Queue contract

- Jobs are immutable records that include `(run_id UUID, tenant_id UUID, project_id UUID, fixture_reference TEXT, status TEXT CHECK (status IN ('queued','running','completed','failed')), scheduled_at TIMESTAMP, started_at TIMESTAMP NULLABLE, finished_at TIMESTAMP NULLABLE, payload JSONB)`.
- `payload` mirrors the CLI inputs (app_id, normalized fixture metadata, CLI flags) but only contains scrubbed strings plus the deterministic identifiers (`node_ref`, `cluster_fingerprint`, `rule_id`) needed for traceability.
- Producers insert jobs with `status = 'queued'` and `scheduled_at` to mark readiness; a simple visibility timeout prevents job contention without sophisticated brokers (for example, `UPDATE ... WHERE status = 'queued'` and `scheduled_at <= now()` returning `status = 'running'` before the worker claims it).
- Idempotency is enforced by `run_id`: re-queuing the same `run_id` should be a no-op, and the worker must reject duplicate `run_id`s at pickup.

## Worker contract

- The worker shell (`uv run python -m src.worker.main`) currently prints a readiness message and serves as the future hook. When pledged to process real work, it will:
  1. Claim the oldest `queued` job, mark it `running`, and record `started_at`.
  2. Use the deterministic CLI (`src.core.cli`) to re-run the proof command with the job’s `payload` and `fixture_reference`.
  3. Write results (`analysis_runs`, `duplicate_clusters`, `recommendations`) back to the persistence schema, marking the job `completed` or `failed` and capturing `finished_at`.
- The worker only reads the authenticated `tenant_id` attached to the job and never materializes raw sensitive strings; scrubbed artifacts persist via the same guards described in `docs/SECURITY_BASELINE.md`.
- Observability hooks (structured logging, optional tracing) should capture `(run_id, job_status, duration_ms, error_message)` so the queue can be reconciled with downstream artifacts.

## Proof implication

Implementing this contract will keep the next slice narrowly focused: the queue is just a table, and the worker merely claims and records deterministic proof runs without introducing new languages, runtimes, or service dependencies.
