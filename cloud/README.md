# RADE Cloud — GitHub App (proprietary)

Hosted GitHub App that wraps the AGPL RADE Engine with stored baselines, merge-blocking check runs, per-repo billing, and a read-only dashboard.

**This directory is NOT covered by the AGPL-3.0 license that covers `src/`.** See [LICENSE](LICENSE) in this directory. The engine stays open source; the hosted service is proprietary.

Architecture and roadmap: [../docs/GITHUB_APP_PLAN.md](../docs/GITHUB_APP_PLAN.md).

## Status

Day 1–4 (worker slice). What exists:

- `../api/gh/webhook.py` and `../api/gh/analyze.py` (repo root) — thin Vercel shims that load the real handlers in this tree.
- `api/gh/webhook.py` — Webhook: HMAC verify, delivery metadata, optional Neon persistence, queue ping.
- `api/gh/run_store.py` — `DATABASE_URL`: idempotent rows, `mark_running_from_queued`, `finalize_run`, `claim_next_pr_analysis` (for pollers), optional `RADE_QUEUE_ENQUEUE_URL` POST.
- `api/gh/pr_engine.py` — Fetches the JSON input fixture at `RADE_INPUT_PATH` for base/head via GitHub Contents API, runs `src.core.report_generator.analyze_file`, `pr_score_diff` (same gates as `action.yml`), returns Markdown for the PR comment.
- `api/gh/analyze.py` — `POST` worker: bearer auth, claim row, `gh_app_client.post_pr_status_for_row` (engine + Check Run + upserted comment). `GET` health.
- `api/gh/gh_app_client.py` — App JWT, installation token, file bytes from repo, list/update comments, Check Runs, upsert by `COMMENT_MARKER`.
- `db/migrations/001_rade_webhook_runs.sql` — inbox table.
- [../vercel.json](../vercel.json) (repo root) — `installCommand` runs `pip install -r requirements.txt && pip install -e .` so the AGPL engine is importable; `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1` for size.
- [../requirements.txt](../requirements.txt) — includes `-r cloud/requirements.txt` plus the editable install provides `PyYAML` / `playwright` (import-only for `--input` analysis).

Not built yet: Stripe entitlements, dashboard, blob-stored full reports.

## Local Development

Prerequisites: Python 3.12+, `vercel` CLI, GitHub account.

Always run Vercel from the **repository root** (so `pip install -e .` and `/api/gh/*` shims match production):

```bash
cp cloud/.env.example cloud/.env.local
sh scripts/vercel-dev
```

`vercel dev` serves `/api/gh/webhook` and `/api/gh/analyze` (from the root `api/gh/*.py` shims). Linking the project once in the Vercel dashboard is enough; the root [vercel.json](../vercel.json) pins runtimes, timeouts, and `installCommand`.

Expose `localhost:3000` via `ngrok http 3000` or `cloudflared tunnel` so GitHub can reach the webhook during development.

## Creating The GitHub App

Use the manifest flow — do not click-configure, to keep the app reproducible.

1. With `vercel dev` running and a public tunnel URL (say `https://rade-dev.ngrok.app`), visit:
   `https://github.com/settings/apps/new?state=rade&manifest=<url-encoded contents of app-manifest.json>`
   Update the `url` and `hook_attributes.url` fields in `app-manifest.json` to the tunnel URL first.
2. GitHub redirects back with a `code`. Exchange it for the app config by POSTing to `https://api.github.com/app-manifests/<code>/conversions`. Save the returned `pem` (private key), `webhook_secret`, `id`, and `client_secret` to `.env.local`.
3. Install the app on a test repository you own.
4. Open a PR in that repo — the webhook handler logs should show `event=pull_request action=opened`.

## Database setup (Day 2)

1. Create a Neon (or other Postgres) database and set `DATABASE_URL` on Vercel.
2. Run the SQL in [db/migrations/001_rade_webhook_runs.sql](db/migrations/001_rade_webhook_runs.sql) once (Neon SQL editor or `psql`).

Without `DATABASE_URL`, the webhook still returns 200 after HMAC verify; rows are not persisted (useful for local tunnel testing).

## Environment Variables

See [.env.example](.env.example). Minimum for production webhook: `GITHUB_WEBHOOK_SECRET` and `DATABASE_URL`. For the analyzer: same `DATABASE_URL`, `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, and (recommended) `RADE_QUEUE_ENQUEUE_TOKEN` so only your queue or cron can `POST` `/api/gh/analyze`. Set `RADE_QUEUE_ENQUEUE_URL` to that analyze URL so the webhook notifies the worker after each new PR-analysis row.

## Verification

```bash
# From this directory: local HMAC sanity check — VALID..., then INVALID...
python api/gh/webhook.py
```

From the repository root, the same check is:

```bash
python cloud/api/gh/webhook.py
```

Automated tests live in the OSS tree: `tests/test_cloud_webhook.py`, `tests/test_cloud_analyze.py` (loaded via `importlib` so the proprietary subtree stays license-separated).

The self-check at the bottom of `api/gh/webhook.py` uses a fixed test secret — no env vars required.
