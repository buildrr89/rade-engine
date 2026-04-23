# SPDX-License-Identifier: AGPL-3.0-only
"""Vercel entry shim — implementation lives in :file:`cloud/api/gh/webhook.py`."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_GH = _ROOT / "cloud" / "api" / "gh"
if str(_GH) not in sys.path:
    sys.path.insert(0, str(_GH))

_p = _GH / "webhook.py"
_spec = importlib.util.spec_from_file_location("rade.cloud.webhook_impl", _p)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {_p}")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
handler = _mod.handler  # Vercel Python convention
