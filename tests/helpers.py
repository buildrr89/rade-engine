# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.core.report_generator import analyze_payload


def load_fixture() -> dict[str, Any]:
    return json.loads(
        Path("tests/fixtures/sample_ios_output.json").read_text(encoding="utf-8")
    )


def build_report(generated_at: str = "2026-03-18T00:00:00Z") -> dict[str, Any]:
    return analyze_payload(
        load_fixture(), "com.example.legacyapp", generated_at=generated_at
    )
