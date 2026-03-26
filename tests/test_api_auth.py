# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import io
import json
import os
from unittest.mock import patch
from wsgiref.util import setup_testing_defaults

from src.api.app import app
from src.api.auth import ApiKeyMiddleware

TEST_API_KEY = "test-rade-key-2026"


def _build_authed_app(api_key: str | None = TEST_API_KEY):
    """Build an authed WSGI app with a controlled API key."""
    with patch.dict(
        os.environ, {"RADE_API_KEY": api_key} if api_key else {}, clear=False
    ):
        # Clear RADE_API_KEY if api_key is None
        env = os.environ.copy()
        if api_key is None:
            env.pop("RADE_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            return ApiKeyMiddleware(app)


def _call_wsgi(
    wsgi_app,
    path: str,
    method: str = "GET",
    body: bytes = b"",
    auth_header: str | None = None,
):
    environ = {}
    setup_testing_defaults(environ)
    environ["PATH_INFO"] = path
    environ["REQUEST_METHOD"] = method
    if body:
        environ["wsgi.input"] = io.BytesIO(body)
        environ["CONTENT_LENGTH"] = str(len(body))
    if auth_header:
        environ["HTTP_AUTHORIZATION"] = auth_header
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    response_body = b"".join(wsgi_app(environ, start_response))
    return (
        captured["status"],
        dict(captured["headers"]),
        json.loads(response_body.decode("utf-8")),
    )


# --- Public routes pass through without auth ---


def test_healthz_accessible_without_auth():
    authed_app = _build_authed_app()
    status, _, payload = _call_wsgi(authed_app, "/healthz")

    assert status == "200 OK"
    assert payload["status"] == "ok"


def test_root_accessible_without_auth():
    authed_app = _build_authed_app()
    status, _, payload = _call_wsgi(authed_app, "/")

    assert status == "200 OK"
    assert payload["status"] == "ready"


# --- Authenticated routes require valid Bearer token ---


def test_analyze_requires_auth_header():
    authed_app = _build_authed_app()
    fixture_path = "examples/sample_ios_output.json"
    with open(fixture_path, encoding="utf-8") as f:
        fixture = json.load(f)
    fixture["app_id"] = "com.example.test"
    body = json.dumps(fixture).encode("utf-8")

    # No auth header -> 401
    status, _, payload = _call_wsgi(authed_app, "/analyze", method="POST", body=body)
    assert status == "401 Unauthorized"
    assert payload["error"] == "missing_token"


def test_analyze_rejects_wrong_key():
    authed_app = _build_authed_app()
    fixture_path = "examples/sample_ios_output.json"
    with open(fixture_path, encoding="utf-8") as f:
        fixture = json.load(f)
    fixture["app_id"] = "com.example.test"
    body = json.dumps(fixture).encode("utf-8")

    # Wrong key -> 403
    status, _, payload = _call_wsgi(
        authed_app,
        "/analyze",
        method="POST",
        body=body,
        auth_header="Bearer wrong-key",
    )
    assert status == "403 Forbidden"
    assert payload["error"] == "invalid_token"


def test_analyze_accepts_valid_key():
    authed_app = _build_authed_app()
    fixture_path = "examples/sample_ios_output.json"
    with open(fixture_path, encoding="utf-8") as f:
        fixture = json.load(f)
    fixture["app_id"] = "com.example.test"
    body = json.dumps(fixture).encode("utf-8")

    # Correct key -> 200
    status, _, payload = _call_wsgi(
        authed_app,
        "/analyze",
        method="POST",
        body=body,
        auth_header=f"Bearer {TEST_API_KEY}",
    )
    assert status == "200 OK"
    assert payload["app_id"] == "com.example.test"
    assert "report_version" in payload


# --- Misconfigured API key ---


def test_unconfigured_api_key_returns_503():
    authed_app = _build_authed_app(api_key=None)

    status, _, payload = _call_wsgi(
        authed_app,
        "/analyze",
        method="POST",
        body=b"{}",
        auth_header="Bearer some-key",
    )
    assert status == "503 Service Unavailable"
    assert payload["error"] == "auth_not_configured"


# --- Auth header format edge cases ---


def test_non_bearer_auth_header_rejected():
    authed_app = _build_authed_app()
    status, _, payload = _call_wsgi(
        authed_app,
        "/analyze",
        method="POST",
        body=b"{}",
        auth_header=f"Basic {TEST_API_KEY}",
    )
    assert status == "401 Unauthorized"
    assert payload["error"] == "missing_token"


def test_empty_bearer_token_rejected():
    authed_app = _build_authed_app()
    status, _, payload = _call_wsgi(
        authed_app,
        "/analyze",
        method="POST",
        body=b"{}",
        auth_header="Bearer ",
    )
    assert status == "403 Forbidden"
    assert payload["error"] == "invalid_token"
