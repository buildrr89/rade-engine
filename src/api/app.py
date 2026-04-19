# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from typing import Any, Callable

from ..core.report_generator import analyze_payload, prepare_report_for_output
from ..core.schemas import ValidationError

JsonResponse = Callable[[str, list[tuple[str, str]]], None]
JsonDict = dict[str, Any]

MAX_PAYLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _json_response(start_response, status: str, payload: dict) -> list[bytes]:
    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    start_response(
        status,
        [("Content-Type", "application/json"), ("Content-Length", str(len(body)))],
    )
    return [body]


def _read_body(environ) -> bytes:
    content_length = environ.get("CONTENT_LENGTH")
    if not content_length:
        return b""
    length = int(content_length)
    if length > MAX_PAYLOAD_BYTES:
        raise ValueError(f"Payload too large: {length} bytes (max {MAX_PAYLOAD_BYTES})")
    return environ["wsgi.input"].read(length)


def _handle_analyze(environ, start_response) -> list[bytes]:
    try:
        raw = _read_body(environ)
    except ValueError as exc:
        return _json_response(
            start_response,
            "413 Payload Too Large",
            {"error": "payload_too_large", "detail": str(exc)},
        )

    if not raw:
        return _json_response(
            start_response,
            "400 Bad Request",
            {"error": "empty_body", "detail": "Request body must be a JSON object."},
        )

    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return _json_response(
            start_response,
            "400 Bad Request",
            {"error": "invalid_json", "detail": str(exc)},
        )

    if not isinstance(payload, dict):
        return _json_response(
            start_response,
            "400 Bad Request",
            {
                "error": "invalid_payload",
                "detail": "Top-level value must be a JSON object.",
            },
        )

    app_id = payload.pop("app_id", None)
    if not app_id or not isinstance(app_id, str):
        return _json_response(
            start_response,
            "400 Bad Request",
            {
                "error": "missing_app_id",
                "detail": "Field 'app_id' is required and must be a non-empty string.",
            },
        )

    try:
        report = analyze_payload(payload, app_id)
    except ValidationError as exc:
        return _json_response(
            start_response,
            "422 Unprocessable Entity",
            {"error": "validation_error", "detail": str(exc)},
        )
    except Exception as exc:
        return _json_response(
            start_response,
            "500 Internal Server Error",
            {"error": "analysis_failed", "detail": str(exc)},
        )

    output = prepare_report_for_output(report)
    return _json_response(start_response, "200 OK", output)


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
            {
                "service": "rade-api",
                "status": "ready",
                "routes": ["/healthz", "/analyze"],
            },
        )

    if path == "/analyze" and method == "POST":
        return _handle_analyze(environ, start_response)

    if path == "/analyze" and method != "POST":
        return _json_response(
            start_response,
            "405 Method Not Allowed",
            {"error": "method_not_allowed", "detail": "Use POST for /analyze."},
        )

    return _json_response(
        start_response, "404 Not Found", {"error": "not_found", "path": path}
    )
