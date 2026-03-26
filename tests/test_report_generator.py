# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from pathlib import Path

from src.core.report_generator import (
    analyze_payload,
    prepare_report_for_output,
    render_markdown_report,
    write_report,
)

from tests.helpers import load_fixture


def test_report_generator_matches_golden_outputs(tmp_path):
    report = analyze_payload(
        load_fixture(), "com.example.legacyapp", generated_at="2026-03-18T00:00:00Z"
    )
    write_report(report, tmp_path / "report.json", tmp_path / "report.md")

    golden_json = json.loads(
        Path("tests/golden/sample_modernization_report.json").read_text(
            encoding="utf-8"
        )
    )
    generated_json = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert generated_json == golden_json

    golden_md = Path("tests/golden/sample_modernization_report.md").read_text(
        encoding="utf-8"
    )
    generated_md = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert generated_md == golden_md
    assert render_markdown_report(report) == golden_md


def test_report_generator_is_deterministic_with_fixed_timestamp():
    first = prepare_report_for_output(
        analyze_payload(
            load_fixture(), "com.example.legacyapp", generated_at="2026-03-18T00:00:00Z"
        )
    )
    second = prepare_report_for_output(
        analyze_payload(
            load_fixture(), "com.example.legacyapp", generated_at="2026-03-18T00:00:00Z"
        )
    )

    assert first == second
