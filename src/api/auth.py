# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import hmac
import json
import os
from typing import Any

# Routes that do not require authentication.
PUBLIC_PATHS = frozenset({"/", "/healthz"})


def _json_response(start_response, status: str, payload: dict) -> list[bytes]:
    body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    start_response(
        status,
        [("Content-Type", "application/json"), ("Content-Length", str(len(body)))],
    )
    return [body]


def _extract_bearer_token(environ: dict[str, Any]) -> str | None:
    """Extract Bearer token from the Authorization header."""
    auth_header = environ.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:].strip()


class ApiKeyMiddleware:
    """WSGI middleware that enforces static API key auth on non-public routes.

    The API key is read from the ``RADE_API_KEY`` environment variable at
    construction time. If the variable is unset or empty the middleware rejects
    every authenticated request with 503, making misconfiguration visible
    rather than silently open.
    """

    def __init__(self, wrapped_app):
        self.wrapped_app = wrapped_app
        self.api_key: str | None = os.environ.get("RADE_API_KEY") or None

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "/")

        # Public routes pass through without auth.
        if path in PUBLIC_PATHS:
            return self.wrapped_app(environ, start_response)

        # If RADE_API_KEY is not configured, reject with 503.
        if self.api_key is None:
            return _json_response(
                start_response,
                "503 Service Unavailable",
                {
                    "error": "auth_not_configured",
                    "detail": "RADE_API_KEY is not set. The API cannot serve authenticated requests.",
                },
            )

        token = _extract_bearer_token(environ)
        if token is None:
            return _json_response(
                start_response,
                "401 Unauthorized",
                {
                    "error": "missing_token",
                    "detail": "Authorization header with Bearer token is required.",
                },
            )

        # Constant-time comparison to avoid timing attacks.
        if not hmac.compare_digest(token, self.api_key):
            return _json_response(
                start_response,
                "403 Forbidden",
                {"error": "invalid_token", "detail": "Invalid API key."},
            )

        return self.wrapped_app(environ, start_response)
