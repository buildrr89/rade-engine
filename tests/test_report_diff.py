# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from pathlib import Path

from src.core.report_diff import (
    build_report_diff,
    load_diffable_report,
    render_markdown_report_diff,
    write_report_diff,
)


def test_build_report_diff_matches_golden_shape():
    base_report = load_diffable_report(Path("tests/fixtures/report_diff_base.json"))
    head_report = load_diffable_report(Path("tests/fixtures/report_diff_head.json"))

    diff = build_report_diff(base_report, head_report)

    golden = json.loads(
        Path("tests/golden/sample_report_diff.json").read_text(encoding="utf-8")
    )
    assert diff == golden


def test_write_report_diff_writes_deterministic_json_and_markdown(tmp_path):
    base_report = load_diffable_report(Path("tests/fixtures/report_diff_base.json"))
    head_report = load_diffable_report(Path("tests/fixtures/report_diff_head.json"))
    diff = build_report_diff(base_report, head_report)

    json_output = tmp_path / "report_diff.json"
    md_output = tmp_path / "report_diff.md"

    write_report_diff(diff, json_output=json_output, md_output=md_output)

    assert json.loads(json_output.read_text(encoding="utf-8")) == json.loads(
        Path("tests/golden/sample_report_diff.json").read_text(encoding="utf-8")
    )
    assert md_output.read_text(encoding="utf-8") == Path(
        "tests/golden/sample_report_diff.md"
    ).read_text(encoding="utf-8")
    assert render_markdown_report_diff(diff) == Path(
        "tests/golden/sample_report_diff.md"
    ).read_text(encoding="utf-8")


def test_build_report_diff_computes_score_status_from_direction():
    diff = build_report_diff(
        load_diffable_report(Path("tests/fixtures/report_diff_base.json")),
        load_diffable_report(Path("tests/fixtures/report_diff_head.json")),
    )

    assert diff["scores"]["complexity"]["status"] == "improved"
    assert diff["scores"]["reusability"]["status"] == "improved"
    assert diff["scores"]["accessibility_risk"]["status"] == "improved"
    assert diff["scores"]["migration_risk"]["status"] == "improved"


def test_load_diffable_report_rejects_missing_required_fields():
    invalid_path = Path("tests/fixtures/invalid_report.json")

    try:
        load_diffable_report(invalid_path)
    except ValueError as exc:
        assert str(exc) == (
            "invalid RADE report: missing required keys: scores, summary"
        )
    else:
        raise AssertionError("expected ValueError for invalid report")
