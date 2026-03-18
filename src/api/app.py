from __future__ import annotations

import json
from typing import Callable

JsonResponse = Callable[[str, list[tuple[str, str]]], None]


def _json_response(start_response, status: str, payload: dict) -> list[bytes]:
    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    start_response(
        status,
        [("Content-Type", "application/json"), ("Content-Length", str(len(body)))],
    )
    return [body]


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET").upper()

    if path == "/healthz" and method == "GET":
        return _json_response(
            start_response, "200 OK", {"service": "rade-api", "status": "ok"}
        )

    if path == "/" and method == "GET":
        return _json_response(
            start_response,
            "200 OK",
            {"service": "rade-api", "status": "ready", "routes": ["/healthz"]},
        )

    return _json_response(
        start_response, "404 Not Found", {"error": "not_found", "path": path}
    )
