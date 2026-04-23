# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import patch


def _load_analyze():
    root = Path(__file__).resolve().parents[1]
    gh = root / "cloud" / "api" / "gh"
    gh_str = str(gh)
    if gh_str not in sys.path:
        sys.path.insert(0, gh_str)
    path = gh / "analyze.py"
    name = "rade_cloud_analyze_test"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_an = _load_analyze()


def test_analyze_get_health() -> None:
    st, body = _an.process_analyze("GET", {}, b"", conninfo="")
    assert st == 200
    assert body.get("version") == "0.4.0"
    assert body.get("service") == "rade-cloud-analyze"


def test_analyze_rejects_non_post() -> None:
    st, body = _an.process_analyze("PUT", {}, b"{}", conninfo="x")
    assert st == 405
    assert body["error"] == "method_not_allowed"


def test_analyze_missing_database() -> None:
    st, body = _an.process_analyze(
        "POST", {"Content-Type": "application/json"}, b"{}", conninfo=""
    )
    assert st == 500
    assert body.get("error") == "server_misconfigured"


def test_analyze_bearer_rejected_when_token_set() -> None:
    with patch.dict(os.environ, {"RADE_QUEUE_ENQUEUE_TOKEN": "secret"}):
        st, body = _an.process_analyze(
            "POST",
            {"Content-Type": "application/json", "Authorization": "Bearer wrong"},
            b'{"run_id":"u1"}',
            conninfo="postgres://u",
        )
    assert st == 401
    assert body["error"] == "unauthorized"


def test_analyze_bearer_accepts_token() -> None:
    def fetch(_: str) -> None:
        return None

    with patch.dict(os.environ, {"RADE_QUEUE_ENQUEUE_TOKEN": "ok-token"}):
        st, body = _an.process_analyze(
            "POST",
            {
                "Content-Type": "application/json",
                "Authorization": "Bearer ok-token",
            },
            b'{"run_id":"u1"}',
            conninfo="postgres://u",
            fetch_run=fetch,
        )
    assert st == 404
    assert body["error"] == "run_not_found"


def test_analyze_missing_run_id() -> None:
    st, body = _an.process_analyze(
        "POST",
        {"Content-Type": "application/json"},
        b"{}",
        conninfo="postgres://u",
    )
    assert st == 400
    assert body["error"] == "missing_run_id"


def test_analyze_not_queued() -> None:
    def fetch(_: str) -> dict:
        return {
            "id": "u",
            "github_delivery_id": "d1",
            "status": "running",
        }

    st, body = _an.process_analyze(
        "POST",
        {"Content-Type": "application/json"},
        b'{"run_id":"u1","github_delivery_id":"d1"}',
        conninfo="postgres://u",
        fetch_run=fetch,
    )
    assert st == 409
    assert body["error"] == "not_queued"


def test_analyze_delivery_mismatch() -> None:
    def fetch(_: str) -> dict:
        return {
            "id": "u",
            "github_delivery_id": "d1",
            "status": "queued",
        }

    st, body = _an.process_analyze(
        "POST",
        {"Content-Type": "application/json"},
        b'{"run_id":"u1","github_delivery_id":"d2"}',
        conninfo="postgres://u",
        fetch_run=fetch,
    )
    assert st == 409
    assert body["error"] == "delivery_mismatch"


def test_analyze_skips_non_pr() -> None:
    calls: list[tuple] = []

    def fetch(_: str) -> dict:
        return {
            "id": "r1",
            "github_delivery_id": "d1",
            "status": "queued",
            "work_kind": "lifecycle",
        }

    def mark(_: str) -> dict:
        return {
            "id": "r1",
            "github_delivery_id": "d1",
            "status": "running",
            "work_kind": "lifecycle",
        }

    def final(run_id, *, status, summary_patch=None) -> None:
        calls.append((run_id, status, summary_patch))

    st, body = _an.process_analyze(
        "POST",
        {"Content-Type": "application/json"},
        b'{"run_id":"r1","github_delivery_id":"d1"}',
        conninfo="postgres://u",
        fetch_run=fetch,
        mark_running=mark,
        finalize=final,
    )
    assert st == 200
    assert body.get("work") == "skipped"
    assert len(calls) == 1
    assert calls[0][0] == "r1"
    assert calls[0][1] == "completed"
    assert calls[0][2] is not None
    assert calls[0][2].get("worker") == "skipped"


def test_analyze_pr_happy_path() -> None:
    final_calls: list = []

    def fetch(_: str) -> dict:
        return {
            "id": "r1",
            "github_delivery_id": "d1",
            "status": "queued",
            "work_kind": "pr_analysis",
        }

    def mark(_: str) -> dict:
        return {
            "id": "r1",
            "github_delivery_id": "d1",
            "status": "running",
            "work_kind": "pr_analysis",
        }

    def final(run_id, *, status, summary_patch=None) -> None:
        final_calls.append((run_id, status, summary_patch))

    def post(_row) -> dict:
        return {"check_run_id": 42}

    st, body = _an.process_analyze(
        "POST",
        {"Content-Type": "application/json"},
        b'{"run_id":"r1","github_delivery_id":"d1"}',
        conninfo="postgres://u",
        fetch_run=fetch,
        mark_running=mark,
        finalize=final,
        post_github=post,
    )
    assert st == 200
    assert body.get("work") == "pr_analysis"
    assert body.get("github", {}).get("check_run_id") == 42
    assert len(final_calls) == 1
    assert final_calls[0][1] == "completed"
    assert final_calls[0][2]["worker"] == "completed"
