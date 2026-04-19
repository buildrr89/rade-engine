# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict

_COUNTERS: Counter[str] = Counter()
_DURATION_RECORDS: Dict[str, list[int]] = defaultdict(list)


def increment_counter(name: str, value: int = 1) -> None:
    _COUNTERS[name] += value


def record_duration(name: str, duration_ms: int) -> None:
    _DURATION_RECORDS[name].append(duration_ms)


def _durations_summary() -> Dict[str, Dict[str, float | int]]:
    summary: Dict[str, Dict[str, float | int]] = {}
    for name, values in _DURATION_RECORDS.items():
        if not values:
            continue
        summary[name] = {
            "count": len(values),
            "avg": sum(values) / len(values),
            "last": values[-1],
        }
    return summary


def _snapshot() -> Dict[str, Any]:
    return {
        "counters": dict(_COUNTERS),
        "durations": _durations_summary(),
    }


def _reset() -> None:
    _COUNTERS.clear()
    _DURATION_RECORDS.clear()


def publish_metrics(
    *,
    run_id: str | None,
    component: str,
    job_status: str,
    extra: Dict[str, Any] | None = None,
) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id or "unknown",
        "component": component,
        "job_status": job_status,
        "metrics": _snapshot(),
    }
    if extra:
        payload["extra"] = extra
    print(json.dumps(payload), file=sys.stderr, flush=True)
    _reset()
