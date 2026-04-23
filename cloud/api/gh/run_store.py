# Proprietary — RADE Cloud. See cloud/LICENSE.
"""Persist GitHub webhook deliveries and optionally notify an analysis queue.

Day 2: idempotent insert on ``github_delivery_id`` (GitHub ``X-GitHub-Delivery``),
optional fire-and-forget POST to ``RADE_QUEUE_ENQUEUE_URL``.

Day 3: fetch / claim (``mark_running_from_queued``, ``claim_next_pr_analysis``) and
``finalize_run`` for the analyzer worker.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Final

logger = logging.getLogger("rade.cloud.run_store")

_PR_ANALYSIS_ACTIONS: Final[frozenset[str]] = frozenset(
    {"opened", "synchronize", "reopened"}
)


class PersistError(Exception):
    """Database or required configuration failure during persist."""


def classify_work(event: str, action: str | None) -> tuple[str, bool]:
    """Return ``(work_kind, enqueue_analysis)``.

    ``enqueue_analysis`` is True only for pull_request events that should spawn
    a RADE run (opened / synchronize / reopened).
    """
    if event == "ping":
        return "lifecycle", False
    if event == "pull_request":
        if action in _PR_ANALYSIS_ACTIONS:
            return "pr_analysis", True
        return "lifecycle", False
    if event in (
        "installation",
        "installation_repositories",
        "pull_request_review",
        "check_run",
    ):
        return "lifecycle", False
    return "lifecycle", False


def delivery_row_from_webhook(
    delivery_id: str,
    event: str,
    payload: dict[str, Any],
    summary: dict[str, object],
) -> dict[str, Any]:
    """Build a row dict for ``persist_delivery``. No raw webhook body."""
    action = summary.get("action")
    action_str = action if isinstance(action, str) else None
    work_kind, enqueue_analysis = classify_work(event, action_str)

    installation_id: int | None = None
    inst = payload.get("installation")
    if isinstance(inst, dict) and inst.get("id") is not None:
        try:
            installation_id = int(inst["id"])
        except (TypeError, ValueError):
            installation_id = None

    repo = payload.get("repository")
    repo_full_name = repo.get("full_name") if isinstance(repo, dict) else None
    if not isinstance(repo_full_name, str):
        repo_full_name = None

    pr_number: int | None = None
    base_sha: str | None = None
    head_sha: str | None = None
    pr = payload.get("pull_request")
    if isinstance(pr, dict):
        if pr.get("number") is not None:
            try:
                pr_number = int(pr["number"])
            except (TypeError, ValueError):
                pr_number = None
        b = pr.get("base")
        h = pr.get("head")
        if isinstance(b, dict) and isinstance(b.get("sha"), str):
            base_sha = b["sha"]
        if isinstance(h, dict) and isinstance(h.get("sha"), str):
            head_sha = h["sha"]

    return {
        "github_delivery_id": delivery_id,
        "event_type": event,
        "action": action_str,
        "work_kind": work_kind,
        "enqueue_analysis": enqueue_analysis,
        "summary": summary,
        "installation_id": installation_id,
        "repo_full_name": repo_full_name,
        "pr_number": pr_number,
        "base_sha": base_sha,
        "head_sha": head_sha,
    }


def _notify_queue(run_id: str, delivery_id: str, enqueue_analysis: bool) -> None:
    if not enqueue_analysis:
        return
    url = (os.environ.get("RADE_QUEUE_ENQUEUE_URL") or "").strip()
    if not url:
        return
    token = (os.environ.get("RADE_QUEUE_ENQUEUE_TOKEN") or "").strip()
    body = json.dumps(
        {"run_id": run_id, "github_delivery_id": delivery_id},
        separators=(",", ":"),
    ).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310 — URL is operator-controlled env, not user input.
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status >= 300:
                logger.warning(
                    "queue notify non-success: status=%s delivery=%s run=%s",
                    resp.status,
                    delivery_id,
                    run_id,
                )
    except urllib.error.HTTPError as exc:
        logger.warning(
            "queue notify HTTP error: %s delivery=%s run=%s",
            exc.code,
            delivery_id,
            run_id,
        )
    except urllib.error.URLError as exc:
        logger.warning(
            "queue notify URL error: %s delivery=%s run=%s",
            exc.reason,
            delivery_id,
            run_id,
        )


def persist_delivery(conninfo: str, row: dict[str, Any]) -> tuple[str, bool]:
    """Insert delivery idempotently. Returns ``(run_id, inserted)``.

    On duplicate ``github_delivery_id``, returns the existing row id and
    ``inserted=False``. Caller commits are handled inside this function.
    """
    import psycopg
    from psycopg.types.json import Json

    enqueue_analysis = bool(row["enqueue_analysis"])
    delivery_id = row["github_delivery_id"]

    insert_sql = """
        INSERT INTO rade_webhook_runs (
            github_delivery_id, event_type, action, work_kind, status,
            installation_id, repo_full_name, pr_number, base_sha, head_sha, summary
        ) VALUES (
            %(github_delivery_id)s, %(event_type)s, %(action)s, %(work_kind)s, 'queued',
            %(installation_id)s, %(repo_full_name)s, %(pr_number)s, %(base_sha)s, %(head_sha)s,
            %(summary)s
        )
        ON CONFLICT (github_delivery_id) DO NOTHING
        RETURNING id::text
    """

    select_sql = "SELECT id::text FROM rade_webhook_runs WHERE github_delivery_id = %s"

    try:
        with psycopg.connect(conninfo) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    insert_sql,
                    {
                        "github_delivery_id": row["github_delivery_id"],
                        "event_type": row["event_type"],
                        "action": row["action"],
                        "work_kind": row["work_kind"],
                        "installation_id": row["installation_id"],
                        "repo_full_name": row["repo_full_name"],
                        "pr_number": row["pr_number"],
                        "base_sha": row["base_sha"],
                        "head_sha": row["head_sha"],
                        "summary": Json(row["summary"]),
                    },
                )
                out = cur.fetchone()
                if out:
                    run_id = str(out[0])
                    inserted = True
                else:
                    cur.execute(select_sql, (delivery_id,))
                    found = cur.fetchone()
                    if not found:
                        raise PersistError("insert skipped but row missing")
                    run_id = str(found[0])
                    inserted = False
            conn.commit()
    except PersistError:
        raise
    except Exception as exc:
        raise PersistError(str(exc)) from exc

    if inserted:
        _notify_queue(run_id, delivery_id, enqueue_analysis)

    return run_id, inserted


def make_persist_fn_from_env() -> Callable[[dict[str, Any]], tuple[str, bool]] | None:
    """Return a persist callable if ``DATABASE_URL`` is set; otherwise ``None``."""
    conninfo = (os.environ.get("DATABASE_URL") or "").strip()
    if not conninfo:
        return None

    def persist(row: dict[str, Any]) -> tuple[str, bool]:
        return persist_delivery(conninfo, row)

    return persist


def _row_to_dict(cur: Any, row: Any) -> dict[str, Any]:
    desc = [c.name for c in cur.description]
    return {desc[i]: row[i] for i in range(len(desc))}


def fetch_run_by_id(conninfo: str, run_id: str) -> dict[str, Any] | None:
    """Load a single ``rade_webhook_runs`` row by primary key, or ``None``."""
    import psycopg

    q = (
        "SELECT id::text, github_delivery_id, event_type, action, work_kind, status, "
        "installation_id, repo_full_name, pr_number, base_sha, head_sha, "
        "summary, created_at, updated_at "
        "FROM rade_webhook_runs WHERE id = %s::uuid"
    )
    try:
        with psycopg.connect(conninfo) as conn:
            with conn.cursor() as cur:
                cur.execute(q, (run_id,))
                one = cur.fetchone()
                if not one:
                    return None
                return _row_to_dict(cur, one)
    except Exception as exc:
        raise PersistError(str(exc)) from exc


def mark_running_from_queued(conninfo: str, run_id: str) -> dict[str, Any] | None:
    """Set ``status='running'`` if currently ``queued``. Returns the row or ``None``."""
    import psycopg

    q = """
        UPDATE rade_webhook_runs
        SET status = 'running', updated_at = now()
        WHERE id = %s::uuid AND status = 'queued'
        RETURNING
          id::text, github_delivery_id, event_type, action, work_kind, status,
          installation_id, repo_full_name, pr_number, base_sha, head_sha, summary, created_at, updated_at
    """
    try:
        with psycopg.connect(conninfo) as conn:
            with conn.cursor() as cur:
                cur.execute(q, (run_id,))
                one = cur.fetchone()
                if not one:
                    return None
                row = _row_to_dict(cur, one)
            conn.commit()
    except Exception as exc:
        raise PersistError(str(exc)) from exc
    return row


def claim_next_pr_analysis(conninfo: str) -> dict[str, Any] | None:
    """Atomically take the oldest queued ``pr_analysis`` run (``SKIP LOCKED``)."""
    import psycopg

    q = """
        UPDATE rade_webhook_runs r
        SET status = 'running', updated_at = now()
        FROM (
          SELECT id
          FROM rade_webhook_runs
          WHERE status = 'queued' AND work_kind = 'pr_analysis'
          ORDER BY created_at
          FOR UPDATE SKIP LOCKED
          LIMIT 1
        ) s
        WHERE r.id = s.id
        RETURNING
          r.id::text, r.github_delivery_id, r.event_type, r.action, r.work_kind, r.status,
          r.installation_id, r.repo_full_name, r.pr_number, r.base_sha, r.head_sha, r.summary, r.created_at, r.updated_at
    """
    try:
        with psycopg.connect(conninfo) as conn:
            with conn.cursor() as cur:
                cur.execute(q)
                one = cur.fetchone()
                if not one:
                    return None
                row = _row_to_dict(cur, one)
            conn.commit()
    except Exception as exc:
        raise PersistError(str(exc)) from exc
    return row


def finalize_run(
    conninfo: str,
    run_id: str,
    *,
    status: str,
    summary_patch: dict[str, Any] | None = None,
) -> None:
    """Set terminal ``status`` and merge an optional ``summary`` JSONB patch."""
    import psycopg
    from psycopg.types.json import Json

    if summary_patch is None:
        patch_obj: Any = None
    else:
        patch_obj = Json(summary_patch)
    if patch_obj is None:
        q = (
            "UPDATE rade_webhook_runs SET status = %s, updated_at = now() "
            "WHERE id = %s::uuid"
        )
        args: tuple[Any, ...] = (status, run_id)
    else:
        q = (
            "UPDATE rade_webhook_runs SET status = %s, "
            "summary = COALESCE(summary, '{}'::jsonb) || %s::jsonb, "
            "updated_at = now() WHERE id = %s::uuid"
        )
        args = (status, patch_obj, run_id)
    try:
        with psycopg.connect(conninfo) as conn:
            with conn.cursor() as cur:
                cur.execute(q, args)
            conn.commit()
    except Exception as exc:
        raise PersistError(str(exc)) from exc
