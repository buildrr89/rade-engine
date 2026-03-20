# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Iterable


def _format_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_event(
    *,
    run_id: str | None,
    component: str,
    stage: str,
    job_status: str,
    tenant_id: str | None = None,
    duration_ms: int | None = None,
    error_message: str | None = None,
    error_code: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    event: dict[str, Any] = {
        "timestamp": _format_timestamp(),
        "run_id": run_id or "unknown",
        "tenant_id": tenant_id,
        "component": component,
        "stage": stage,
        "job_status": job_status,
        "duration_ms": duration_ms,
        "error_message": error_message,
        "error_code": error_code,
    }
    if extra:
        event.update(extra)
    print(json.dumps(event), file=sys.stderr, flush=True)


@contextmanager
def log_stage(
    *,
    run_id: str | None,
    component: str,
    stage: str,
    tenant_id: str | None = None,
    error_code: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Iterable[None]:
    start = perf_counter()
    log_event(
        run_id=run_id,
        component=component,
        stage=stage,
        job_status="running",
        tenant_id=tenant_id,
        error_code=error_code,
        extra=extra,
    )
    try:
        yield
    except Exception as error:
        duration = int((perf_counter() - start) * 1000)
        log_event(
            run_id=run_id,
            component=component,
            stage=stage,
            job_status="failed",
            tenant_id=tenant_id,
            duration_ms=duration,
            error_message=str(error),
            error_code=getattr(error, "code", error_code),
            extra=extra,
        )
        raise
    else:
        duration = int((perf_counter() - start) * 1000)
        log_event(
            run_id=run_id,
            component=component,
            stage=stage,
            job_status="completed",
            tenant_id=tenant_id,
            duration_ms=duration,
            extra=extra,
        )
