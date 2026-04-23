# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import hashlib
import hmac
import importlib.util
import sys
from pathlib import Path


def _load_webhook():
    root = Path(__file__).resolve().parents[1]
    gh = root / "cloud" / "api" / "gh"
    gh_str = str(gh)
    if gh_str not in sys.path:
        sys.path.insert(0, gh_str)
    path = gh / "webhook.py"
    name = "rade_cloud_webhook_test"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_wh = _load_webhook()
_rs = _wh.run_store


def _sign(secret: bytes, body: bytes) -> str:
    return "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()


def test_verify_signature_accepts_github_header() -> None:
    secret = b"octocat"
    body = b'{"hook_id":1}'
    sig = _sign(secret, body)
    _wh.verify_signature(secret, body, sig)


def test_verify_signature_rejects_missing_header() -> None:
    try:
        _wh.verify_signature(b"s", b"{}", None)
    except _wh.InvalidSignatureError as exc:
        assert "missing" in str(exc).lower()
        return
    raise AssertionError("expected InvalidSignatureError")


def test_verify_signature_rejects_wrong_prefix() -> None:
    try:
        _wh.verify_signature(b"s", b"{}", "sha1=abc")
    except _wh.InvalidSignatureError as exc:
        assert "algorithm" in str(exc).lower()
        return
    raise AssertionError("expected InvalidSignatureError")


def test_verify_signature_rejects_empty_digest() -> None:
    try:
        _wh.verify_signature(b"s", b"{}", "sha256=")
    except _wh.InvalidSignatureError as exc:
        assert "empty" in str(exc).lower()
        return
    raise AssertionError("expected InvalidSignatureError")


def test_process_webhook_rejects_non_post() -> None:
    status, body = _wh.process_github_webhook("secret", "GET", {}, b"")
    assert status == 405
    assert body["error"] == "method_not_allowed"


def test_process_webhook_missing_secret() -> None:
    status, body = _wh.process_github_webhook(
        None, "POST", {"Content-Length": "2"}, b"{}"
    )
    assert status == 500
    assert body["error"] == "server_misconfigured"


def test_process_webhook_body_length_mismatch() -> None:
    headers = {"Content-Length": "10", "Content-Type": "application/json"}
    status, body = _wh.process_github_webhook("s", "POST", headers, b"{}")
    assert status == 400
    assert body["error"] == "body_length_mismatch"


def test_process_webhook_unsupported_media_type() -> None:
    raw = b"{}"
    headers = {
        "Content-Length": str(len(raw)),
        "Content-Type": "text/plain",
        "X-Hub-Signature-256": _sign(b"k", raw),
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "d1",
    }
    status, body = _wh.process_github_webhook("k", "POST", headers, raw)
    assert status == 415
    assert body["error"] == "unsupported_media_type"


def test_process_webhook_header_lookup_is_case_insensitive() -> None:
    raw = b'{"zen":"x"}'
    sig = _sign(b"key", raw)
    headers = {
        "content-length": str(len(raw)),
        "content-type": "application/json",
        "x-hub-signature-256": sig,
        "x-github-event": "ping",
        "x-github-delivery": "del",
    }
    status, body = _wh.process_github_webhook("key", "POST", headers, raw)
    assert status == 200
    assert body["status"] == "received"


def test_process_webhook_invalid_json() -> None:
    raw = b"not-json"
    headers = {
        "Content-Length": str(len(raw)),
        "Content-Type": "application/json",
        "X-Hub-Signature-256": _sign(b"k", raw),
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "d1",
    }
    status, body = _wh.process_github_webhook("k", "POST", headers, raw)
    assert status == 400
    assert body["error"] == "invalid_json"


def test_process_webhook_json_not_object() -> None:
    raw = b"[]"
    headers = {
        "Content-Length": str(len(raw)),
        "Content-Type": "application/json",
        "X-Hub-Signature-256": _sign(b"k", raw),
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "d1",
    }
    status, body = _wh.process_github_webhook("k", "POST", headers, raw)
    assert status == 400
    assert body["error"] == "invalid_json"


def test_process_webhook_unknown_event_acknowledged() -> None:
    raw = b"{}"
    headers = {
        "Content-Length": str(len(raw)),
        "Content-Type": "application/json",
        "X-Hub-Signature-256": _sign(b"k", raw),
        "X-GitHub-Event": "workflow_run",
        "X-GitHub-Delivery": "d1",
    }
    status, body = _wh.process_github_webhook("k", "POST", headers, raw)
    assert status == 200
    assert body["status"] == "ignored"


def test_process_webhook_bad_signature() -> None:
    raw = b"{}"
    headers = {
        "Content-Length": str(len(raw)),
        "Content-Type": "application/json",
        "X-Hub-Signature-256": "sha256=" + ("a" * 64),
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "d1",
    }
    status, body = _wh.process_github_webhook("k", "POST", headers, raw)
    assert status == 401


def test_summarize_pull_request() -> None:
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "base": {"sha": "aaa"},
            "head": {"sha": "bbb"},
        },
        "repository": {"full_name": "o/r"},
    }
    s = _wh._summarize_event("pull_request", payload)
    assert s["pr_number"] == 42
    assert s["base_sha"] == "aaa"
    assert s["head_sha"] == "bbb"
    assert s["repo_full_name"] == "o/r"


def test_summarize_pull_request_review() -> None:
    payload = {
        "action": "submitted",
        "pull_request": {"number": 7},
        "review": {"id": 99},
        "repository": {"full_name": "a/b"},
    }
    s = _wh._summarize_event("pull_request_review", payload)
    assert s["pr_number"] == 7
    assert s["review_id"] == 99


def test_classify_work_ping() -> None:
    k, enq = _rs.classify_work("ping", None)
    assert k == "lifecycle"
    assert enq is False


def test_classify_work_pr_opened_enqueues() -> None:
    k, enq = _rs.classify_work("pull_request", "opened")
    assert k == "pr_analysis"
    assert enq is True


def test_classify_work_pr_labeled_does_not_enqueue() -> None:
    k, enq = _rs.classify_work("pull_request", "labeled")
    assert k == "lifecycle"
    assert enq is False


def test_delivery_row_pr_analysis() -> None:
    payload = {
        "action": "synchronize",
        "pull_request": {
            "number": 9,
            "base": {"sha": "base1"},
            "head": {"sha": "head1"},
        },
        "repository": {"full_name": "org/repo"},
        "installation": {"id": 12345},
    }
    summary = _wh._summarize_event("pull_request", payload)
    row = _rs.delivery_row_from_webhook("del-1", "pull_request", payload, summary)
    assert row["work_kind"] == "pr_analysis"
    assert row["enqueue_analysis"] is True
    assert row["pr_number"] == 9
    assert row["base_sha"] == "base1"
    assert row["head_sha"] == "head1"
    assert row["repo_full_name"] == "org/repo"
    assert row["installation_id"] == 12345


def test_process_webhook_persist_called() -> None:
    raw = b'{"zen":"x"}'
    sig = _sign(b"k", raw)
    headers = {
        "Content-Length": str(len(raw)),
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sig,
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "delivery-ping-1",
    }
    calls: list[dict] = []

    def fake_persist(row: dict) -> tuple[str, bool]:
        calls.append(row)
        return "00000000-0000-0000-0000-000000000001", True

    status, body = _wh.process_github_webhook(
        "k", "POST", headers, raw, persist=fake_persist
    )
    assert status == 200
    assert body["run_id"] == "00000000-0000-0000-0000-000000000001"
    assert body["duplicate"] is False
    assert len(calls) == 1
    assert calls[0]["github_delivery_id"] == "delivery-ping-1"
    assert calls[0]["work_kind"] == "lifecycle"


def test_process_webhook_persist_duplicate() -> None:
    raw = b'{"zen":"y"}'
    sig = _sign(b"k", raw)
    headers = {
        "Content-Length": str(len(raw)),
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sig,
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "same-delivery",
    }

    def fake_persist(_row: dict) -> tuple[str, bool]:
        return "00000000-0000-0000-0000-000000000099", False

    status, body = _wh.process_github_webhook(
        "k", "POST", headers, raw, persist=fake_persist
    )
    assert status == 200
    assert body["status"] == "duplicate"
    assert body["duplicate"] is True
    assert body["run_id"] == "00000000-0000-0000-0000-000000000099"


def test_process_webhook_persist_skips_unknown_delivery() -> None:
    raw = b'{"zen":"z"}'
    sig = _sign(b"k", raw)
    headers = {
        "Content-Length": str(len(raw)),
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sig,
        "X-GitHub-Event": "ping",
    }
    called: list[int] = []

    def fake_persist(_row: dict) -> tuple[str, bool]:
        called.append(1)
        return "x", True

    status, body = _wh.process_github_webhook(
        "k", "POST", headers, raw, persist=fake_persist
    )
    assert status == 200
    assert "run_id" not in body
    assert called == []


def test_process_webhook_persist_error_500() -> None:
    raw = b'{"zen":"q"}'
    sig = _sign(b"k", raw)
    headers = {
        "Content-Length": str(len(raw)),
        "Content-Type": "application/json",
        "X-Hub-Signature-256": sig,
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "d-err",
    }

    def bad(_row: dict) -> tuple[str, bool]:
        raise _rs.PersistError("db unavailable")

    status, body = _wh.process_github_webhook("k", "POST", headers, raw, persist=bad)
    assert status == 500
    assert body["error"] == "persist_failed"
