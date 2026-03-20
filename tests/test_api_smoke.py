# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import json
from wsgiref.util import setup_testing_defaults

from src.api.app import app


def _call_wsgi(path: str):
    environ = {}
    setup_testing_defaults(environ)
    environ["PATH_INFO"] = path
    environ["REQUEST_METHOD"] = "GET"
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    body = b"".join(app(environ, start_response))
    return (
        captured["status"],
        dict(captured["headers"]),
        json.loads(body.decode("utf-8")),
    )


def test_api_health_route_returns_ok():
    status, headers, payload = _call_wsgi("/healthz")

    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json"
    assert payload == {"service": "rade-api", "status": "ok"}


def test_api_root_route_returns_ready_metadata():
    status, headers, payload = _call_wsgi("/")

    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json"
    assert payload == {
        "routes": ["/healthz"],
        "service": "rade-api",
        "status": "ready",
    }


def test_api_unknown_route_returns_not_found():
    status, headers, payload = _call_wsgi("/missing")

    assert status == "404 Not Found"
    assert headers["Content-Type"] == "application/json"
    assert payload == {"error": "not_found", "path": "/missing"}
