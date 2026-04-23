# Proprietary — RADE Cloud. See cloud/LICENSE.
"""RADE Cloud — GitHub webhook receiver.

Vercel Python Fluid Compute function. Verifies the HMAC-SHA256 signature
GitHub sends on every webhook delivery, extracts the event/action/delivery
metadata, and acknowledges the delivery within GitHub's 10-second budget.

Day 1: verify + log + 200.

Day 2: optional Neon persistence (``DATABASE_URL``) — idempotent row per
``X-GitHub-Delivery``, optional queue notify via ``RADE_QUEUE_ENQUEUE_URL``
for PR events that should trigger analysis.

Security notes:
- Constant-time signature comparison (hmac.compare_digest).
- Rejects requests without X-Hub-Signature-256 with 401.
- Rejects requests where the signature does not match the body with 401.
- Never logs the raw body or the secret.
- Verifies body size matches Content-Length when declared.
"""

from __future__ import annotations

import hashlib
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

import run_store  # noqa: E402 — sys.path bootstrap above

# Environment
_WEBHOOK_SECRET_ENV: Final[str] = "GITHUB_WEBHOOK_SECRET"
_SIGNATURE_HEADER: Final[str] = "X-Hub-Signature-256"
_DELIVERY_HEADER: Final[str] = "X-GitHub-Delivery"
_EVENT_HEADER: Final[str] = "X-GitHub-Event"
_MAX_BODY_BYTES: Final[int] = (
    25 * 1024 * 1024
)  # GitHub caps webhook payloads at 25 MiB.

# Events we care about in v1. Unknown events are 200-acknowledged without processing.
_HANDLED_EVENTS: Final[frozenset[str]] = frozenset(
    {
        "ping",
        "installation",
        "installation_repositories",
        "pull_request",
        "pull_request_review",
        "check_run",
    }
)

logger = logging.getLogger("rade.cloud.webhook")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class InvalidSignatureError(Exception):
    """Raised when the webhook signature header is missing or does not match."""


def _header_get(headers: Mapping[str, str], name: str) -> str | None:
    """Case-insensitive header lookup (proxies may normalize casing)."""
    lower = name.lower()
    for key, value in headers.items():
        if key.lower() == lower:
            return value
    return None


def verify_signature(secret: bytes, body: bytes, signature_header: str | None) -> None:
    """Verify the GitHub webhook HMAC.

    Raises InvalidSignatureError on any problem. Uses constant-time compare.
    """
    if not signature_header:
        raise InvalidSignatureError("missing signature header")
    if not signature_header.startswith("sha256="):
        raise InvalidSignatureError("unexpected signature algorithm")

    expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
    provided = signature_header.split("=", 1)[1]
    if not provided:
        raise InvalidSignatureError("empty signature digest")
    if not hmac.compare_digest(expected, provided):
        raise InvalidSignatureError("signature mismatch")


def _summarize_event(event: str, payload: dict[str, Any]) -> dict[str, object]:
    """Pull a small, log-safe summary out of the payload.

    Intentionally narrow. We do NOT log PR titles, commit messages, or file
    contents; only stable identifiers. Extend this carefully.
    """
    summary: dict[str, object] = {"event": event}
    if event == "pull_request":
        summary["action"] = payload.get("action")
        pr = payload.get("pull_request") or {}
        summary["pr_number"] = pr.get("number")
        summary["base_sha"] = (pr.get("base") or {}).get("sha")
        summary["head_sha"] = (pr.get("head") or {}).get("sha")
        summary["repo_full_name"] = (payload.get("repository") or {}).get("full_name")
    elif event == "pull_request_review":
        summary["action"] = payload.get("action")
        pr = payload.get("pull_request") or {}
        summary["pr_number"] = pr.get("number")
        summary["review_id"] = (payload.get("review") or {}).get("id")
        summary["repo_full_name"] = (payload.get("repository") or {}).get("full_name")
    elif event == "installation":
        summary["action"] = payload.get("action")
        inst = payload.get("installation") or {}
        summary["installation_id"] = inst.get("id")
        summary["account_login"] = (inst.get("account") or {}).get("login")
    elif event == "installation_repositories":
        summary["action"] = payload.get("action")
        summary["installation_id"] = (payload.get("installation") or {}).get("id")
        summary["added_count"] = len(payload.get("repositories_added") or [])
        summary["removed_count"] = len(payload.get("repositories_removed") or [])
    elif event == "check_run":
        summary["action"] = payload.get("action")
        summary["check_run_id"] = (payload.get("check_run") or {}).get("id")
    elif event == "ping":
        summary["zen"] = payload.get("zen")
    return summary


def process_github_webhook(
    secret: str | None,
    method: str,
    headers: Mapping[str, str],
    body: bytes,
    *,
    persist: Callable[[dict[str, Any]], tuple[str, bool]] | None = None,
) -> tuple[int, dict[str, Any]]:
    """Pure webhook logic for tests and the HTTP handler.

    ``headers`` should map original header names to values (any casing).
    Returns ``(status_code, response_json_dict)``.
    """
    if method != "POST":
        return 405, {"error": "method_not_allowed"}

    if secret is None or secret == "":
        logger.error("webhook misconfigured: missing secret env var")
        return 500, {"error": "server_misconfigured"}

    content_length_raw = _header_get(headers, "Content-Length")
    try:
        content_length = int(content_length_raw or "0")
    except ValueError:
        return 400, {"error": "invalid_content_length"}

    if content_length <= 0 or content_length > _MAX_BODY_BYTES:
        return 413, {"error": "payload_too_large"}

    if len(body) != content_length:
        return 400, {"error": "body_length_mismatch"}

    content_type = _header_get(headers, "Content-Type")
    if content_type is not None and "json" not in content_type.lower():
        return 415, {"error": "unsupported_media_type"}

    signature = _header_get(headers, _SIGNATURE_HEADER)
    try:
        verify_signature(secret.encode("utf-8"), body, signature)
    except InvalidSignatureError as exc:
        logger.warning("signature rejected: %s", exc)
        return 401, {"error": "invalid_signature"}

    delivery_id = _header_get(headers, _DELIVERY_HEADER) or "unknown"
    event = _header_get(headers, _EVENT_HEADER) or "unknown"

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.warning("delivery %s event %s: invalid json body", delivery_id, event)
        return 400, {"error": "invalid_json"}

    if not isinstance(payload, dict):
        return 400, {"error": "invalid_json"}

    if event not in _HANDLED_EVENTS:
        logger.info("delivery=%s event=%s action=ignored_event", delivery_id, event)
        return 200, {"status": "ignored", "event": event}

    summary = _summarize_event(event, payload)
    logger.info("delivery=%s %s", delivery_id, json.dumps(summary))

    response: dict[str, Any] = {
        "status": "received",
        "event": event,
        "delivery_id": delivery_id,
    }

    if persist is not None:
        if delivery_id == "unknown":
            logger.warning("persist skipped: missing %s header", _DELIVERY_HEADER)
        else:
            try:
                row = run_store.delivery_row_from_webhook(
                    delivery_id, event, payload, summary
                )
                run_id, inserted = persist(row)
            except run_store.PersistError as exc:
                logger.exception("persist failed: %s", exc)
                return 500, {"error": "persist_failed"}
            response["run_id"] = run_id
            response["duplicate"] = not inserted
            if not inserted:
                response["status"] = "duplicate"

    return 200, response


def _headers_from_handler(handler: BaseHTTPRequestHandler) -> dict[str, str]:
    return {k: v for k, v in handler.headers.items()}


class handler(
    BaseHTTPRequestHandler
):  # noqa: N801 — Vercel convention: lowercase `handler`.
    """Vercel Python function entrypoint."""

    def log_message(self, format: str, *args: object) -> None:
        """Route stdlib request noise through our logger at DEBUG."""
        logger.debug("%s - - %s", self.address_string(), format % args)

    def _write_json(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self) -> None:  # noqa: N802 — stdlib interface.
        secret = os.environ.get(_WEBHOOK_SECRET_ENV)
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._write_json(400, {"error": "invalid_content_length"})
            return
        if content_length <= 0 or content_length > _MAX_BODY_BYTES:
            self._write_json(413, {"error": "payload_too_large"})
            return

        body = self.rfile.read(content_length)
        status, payload = process_github_webhook(
            secret,
            "POST",
            _headers_from_handler(self),
            body,
            persist=run_store.make_persist_fn_from_env(),
        )
        self._write_json(status, payload)

    def do_GET(self) -> None:  # noqa: N802
        # Cheap liveness probe — no secrets, no payload.
        self._write_json(
            200,
            {"status": "ok", "service": "rade-cloud-webhook", "version": "0.2.0"},
        )


# ---------------------------------------------------------------------------
# Dev-only sanity check: `python cloud/api/gh/webhook.py`
# ---------------------------------------------------------------------------


def _dev_self_check() -> int:
    """Print VALID/INVALID for a hand-rolled signed payload. Returns exit code."""
    secret = b"test-secret"
    body = b'{"zen":"Keep it logically awesome."}'
    good_sig = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    bad_sig = "sha256=" + ("0" * 64)

    try:
        verify_signature(secret, body, good_sig)
        print("VALID: signed payload accepted")
    except InvalidSignatureError as exc:
        print(f"UNEXPECTED: valid signature rejected: {exc}")
        return 1

    try:
        verify_signature(secret, body, bad_sig)
        print("UNEXPECTED: bad signature accepted")
        return 1
    except InvalidSignatureError:
        print("INVALID: forged signature rejected (as expected)")

    return 0


if __name__ == "__main__":
    sys.exit(_dev_self_check())
