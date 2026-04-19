# SPDX-License-Identifier: AGPL-3.0-only
"""WSGI entry point for the authenticated API surface.

The application wraps the core RADE app with API key auth middleware.
Set ``RADE_API_KEY`` in the environment before starting.
"""

from __future__ import annotations

from .app import app
from .auth import ApiKeyMiddleware

application = ApiKeyMiddleware(app)
