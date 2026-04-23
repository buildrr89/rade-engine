-- RADE Cloud — webhook idempotency + analysis queue inbox (Day 2).
-- Apply against Neon / Postgres 14+ (gen_random_uuid is built-in).

CREATE TABLE IF NOT EXISTS rade_webhook_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  github_delivery_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  action TEXT,
  work_kind TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  installation_id BIGINT,
  repo_full_name TEXT,
  pr_number INTEGER,
  base_sha TEXT,
  head_sha TEXT,
  summary JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT rade_webhook_runs_delivery_key UNIQUE (github_delivery_id)
);

CREATE INDEX IF NOT EXISTS rade_webhook_runs_status_created_idx ON rade_webhook_runs (status, created_at);

CREATE INDEX IF NOT EXISTS rade_webhook_runs_repo_pr_idx ON rade_webhook_runs (repo_full_name, pr_number)
WHERE
  repo_full_name IS NOT NULL;
