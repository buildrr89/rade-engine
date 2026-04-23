# Proprietary — RADE Cloud. See cloud/LICENSE.
"""RADE Cloud — PR analysis worker (Fluid Compute).

Day 3–4: POST JSON ``{"run_id","github_delivery_id"?}`` with optional
``Authorization: Bearer`` when ``RADE_QUEUE_ENQUEUE_TOKEN`` is set. Claims a
``queued`` row, runs :mod:`pr_engine` (same diffs as the GitHub Action), posts
Check Run + upserted PR comment, and finalizes the row.

``GET`` returns a health JSON payload (no DB).
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Callable, Final, Mapping

_GH_DIR = Path(__file__).resolve().parent
if str(_GH_DIR) not in sys.path:
    sys.path.insert(0, str(_GH_DIR))

import gh_app_client  # noqa: E402
import run_store  # noqa: E402

logger = logging.getLogger("rade.cloud.analyze")
if not logger.handlers:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

_BEARER_ENV: Final[str] = "RADE_QUEUE_ENQUEUE_TOKEN"
_SERVICE_VERSION: Final[str] = "0.4.0"


def _header_get(headers: Mapping[str, str], name: str) -> str | None:
    lower = name.lower()
    for key, value in headers.items():
        if key.lower() == lower:
            return value
    return None


def _worker_bearer_ok(headers: Mapping[str, str]) -> bool:
    expected = (os.environ.get(_BEARER_ENV) or "").strip()
    if not expected:
        return True
    auth = _header_get(headers, "Authorization") or ""
    if not auth.lower().startswith("bearer "):
        return False
    got = auth[7:].strip()
    return hmac.compare_digest(got, expected)


def process_analyze(
    method: str,
    headers: Mapping[str, str],
    body: bytes,
    conninfo: str,
    *,
    mark_running: Callable[[str], dict[str, Any] | None] | None = None,
    fetch_run: Callable[[str], dict[str, Any] | None] | None = None,
    finalize: Callable[..., None] | None = None,
    post_github: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Worker logic for tests and the HTTP entrypoint. ``conninfo`` is required.

    Injected callables default to :mod:`run_store` and :mod:`gh_app_client`.
    """
    if method == "GET":
        return 200, {
            "status": "ok",
            "service": "rade-cloud-analyze",
            "version": _SERVICE_VERSION,
        }

    if method != "POST":
        return 405, {"error": "method_not_allowed"}

    if not _worker_bearer_ok(headers):
        return 401, {"error": "unauthorized"}

    if not (conninfo or "").strip():
        return 500, {"error": "server_misconfigured", "detail": "missing database"}

    content_type = _header_get(headers, "Content-Type")
    if content_type and "json" not in content_type.lower():
        return 415, {"error": "unsupported_media_type"}

    try:
        parsed = json.loads(body.decode("utf-8") if body else b"{}")
    except json.JSONDecodeError:
        return 400, {"error": "invalid_json"}

    if not isinstance(parsed, dict):
        return 400, {"error": "invalid_json"}

    run_id = parsed.get("run_id")
    if not isinstance(run_id, str) or not run_id.strip():
        return 400, {"error": "missing_run_id"}

    run_id = run_id.strip()
    delivery_in = parsed.get("github_delivery_id")
    if delivery_in is not None and not isinstance(delivery_in, str):
        return 400, {"error": "invalid_delivery_id"}

    _fetch = fetch_run or (lambda rid: run_store.fetch_run_by_id(conninfo, rid))
    _mark = mark_running or (
        lambda rid: run_store.mark_running_from_queued(conninfo, rid)
    )

    def _default_finalize(
        run_id: str,
        *,
        status: str,
        summary_patch: dict[str, Any] | None = None,
    ) -> None:
        run_store.finalize_run(
            conninfo, run_id, status=status, summary_patch=summary_patch
        )

    _fin = finalize or _default_finalize
    _post = post_github or gh_app_client.post_pr_status_for_row

    before = _fetch(run_id)
    if not before:
        return 404, {"error": "run_not_found"}

    if delivery_in and delivery_in != before.get("github_delivery_id"):
        return 409, {"error": "delivery_mismatch"}

    if before.get("status") != "queued":
        return 409, {"error": "not_queued", "status": before.get("status")}

    row = _mark(run_id)
    if not row:
        return 409, {"error": "claim_failed"}

    out: dict[str, Any] = {
        "status": "completed",
        "run_id": run_id,
    }

    try:
        if row.get("work_kind") != "pr_analysis":
            _fin(
                run_id,
                status="completed",
                summary_patch={
                    "worker": "skipped",
                    "reason": "work_kind",
                    "work_kind": row.get("work_kind"),
                },
            )
            out["work"] = "skipped"
            return 200, out

        result = _post(row)
        _fin(
            run_id,
            status="completed",
            summary_patch={"worker": "completed", "github": result},
        )
        out["work"] = "pr_analysis"
        out["github"] = result
        return 200, out
    except run_store.PersistError as exc:
        logger.exception("persist: %s", exc)
        return 500, {"error": "persist_failed"}
    except Exception as exc:
        logger.exception("analyze: %s", exc)
        try:
            _fin(
                run_id,
                status="error",
                summary_patch={"worker": "error", "message": str(exc)[:2_000]},
            )
        except run_store.PersistError:
            logger.exception("finalize after error")
        return 500, {"error": "worker_failed", "run_id": run_id}


def _env_conninfo() -> str:
    return (os.environ.get("DATABASE_URL") or "").strip()


def _body_from_handler(handler: BaseHTTPRequestHandler) -> bytes:
    try:
        n = int(handler.headers.get("Content-Length", "0"))
    except ValueError:
        return b""
    if n <= 0:
        return b""
    return handler.rfile.read(n)


def _headers_from_handler(handler: BaseHTTPRequestHandler) -> dict[str, str]:
    return {k: v for k, v in handler.headers.items()}


class handler(  # noqa: N801 — Vercel convention: lowercase `handler`.
    BaseHTTPRequestHandler
):
    """Vercel Python function entrypoint."""

    def log_message(self, format: str, *args: object) -> None:
        logger.debug("%s - - %s", self.address_string(), format % args)

    def _write_json(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        st, body = process_analyze("GET", _headers_from_handler(self), b"", conninfo="")
        self._write_json(st, body)

    def do_POST(self) -> None:  # noqa: N802
        ci = _env_conninfo()
        st, body = process_analyze(
            "POST",
            _headers_from_handler(self),
            _body_from_handler(self),
            conninfo=ci,
        )
        self._write_json(st, body)
