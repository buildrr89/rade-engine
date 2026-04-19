# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from pathlib import Path

from src.core.report_diff import (
    build_report_diff,
    load_diffable_report,
    render_markdown_report_diff,
)
from src.core.report_generator import (
    analyze_payload,
    prepare_report_for_output,
    render_html_report,
    render_markdown_report,
)

FIXED_TIMESTAMP = "2026-03-22T00:00:00Z"
REAL_WORLD_FIXTURES = [
    (
        "examples/python_org_homepage.json",
        "org.python.www",
        "examples/python_org_homepage_report.json",
        "examples/python_org_homepage_report.md",
    ),
    (
        "examples/mdn_homepage.json",
        "org.mozilla.mdn",
        "examples/mdn_homepage_report.json",
        "examples/mdn_homepage_report.md",
    ),
    (
        "examples/web_dev_homepage.json",
        "dev.web.homepage",
        "examples/web_dev_homepage_report.json",
        "examples/web_dev_homepage_report.md",
    ),
]

HTML_FIXTURES = [
    (
        "examples/python_org_homepage.json",
        "org.python.www",
        "examples/python_org_homepage_report.html",
    ),
]

SAME_SURFACE_FIXTURES = [
    (
        "examples/legacy_repair_before.json",
        "com.example.legacyapp",
        "2026-03-22T00:00:00Z",
        "examples/legacy_repair_before_report.json",
        "examples/legacy_repair_before_report.md",
    ),
    (
        "examples/legacy_repair_after.json",
        "com.example.legacyapp",
        "2026-04-10T00:00:00Z",
        "examples/legacy_repair_after_report.json",
        "examples/legacy_repair_after_report.md",
    ),
]


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_real_world_fixture_reports_match_checked_in_examples() -> None:
    for fixture_path, app_id, report_json_path, report_md_path in REAL_WORLD_FIXTURES:
        payload = _load_json(fixture_path)

        report = analyze_payload(payload, app_id, generated_at=FIXED_TIMESTAMP)
        prepared = prepare_report_for_output(report)

        assert prepared == _load_json(report_json_path)
        assert render_markdown_report(report) == Path(report_md_path).read_text(
            encoding="utf-8"
        )


def test_real_world_html_reports_match_checked_in_examples() -> None:
    for fixture_path, app_id, report_html_path in HTML_FIXTURES:
        payload = _load_json(fixture_path)
        report = analyze_payload(payload, app_id, generated_at=FIXED_TIMESTAMP)
        expected = Path(report_html_path).read_text(encoding="utf-8")
        assert render_html_report(report) == expected


def test_real_world_fixtures_are_deterministic() -> None:
    for fixture_path, app_id, _, _ in REAL_WORLD_FIXTURES:
        payload = _load_json(fixture_path)

        first = prepare_report_for_output(
            analyze_payload(payload, app_id, generated_at=FIXED_TIMESTAMP)
        )
        second = prepare_report_for_output(
            analyze_payload(payload, app_id, generated_at=FIXED_TIMESTAMP)
        )

        assert first == second


def test_real_world_report_diff_matches_checked_in_example() -> None:
    base_report = load_diffable_report(Path("examples/python_org_homepage_report.json"))
    head_report = load_diffable_report(Path("examples/web_dev_homepage_report.json"))
    diff = build_report_diff(base_report, head_report)

    assert diff == _load_json("examples/python_to_web_dev_report_diff.json")
    assert render_markdown_report_diff(diff) == Path(
        "examples/python_to_web_dev_report_diff.md"
    ).read_text(encoding="utf-8")


def test_same_surface_fixture_reports_match_checked_in_examples() -> None:
    for (
        fixture_path,
        app_id,
        generated_at,
        report_json_path,
        report_md_path,
    ) in SAME_SURFACE_FIXTURES:
        payload = _load_json(fixture_path)

        report = analyze_payload(payload, app_id, generated_at=generated_at)
        prepared = prepare_report_for_output(report)

        assert prepared == _load_json(report_json_path)
        assert render_markdown_report(report) == Path(report_md_path).read_text(
            encoding="utf-8"
        )


def test_same_surface_report_diff_matches_checked_in_example() -> None:
    base_report = load_diffable_report(
        Path("examples/legacy_repair_before_report.json")
    )
    head_report = load_diffable_report(Path("examples/legacy_repair_after_report.json"))
    diff = build_report_diff(base_report, head_report)

    assert base_report["app_id"] == head_report["app_id"] == "com.example.legacyapp"
    assert (
        base_report["project_name"]
        == head_report["project_name"]
        == "Legacy Repair App"
    )
    assert diff == _load_json("examples/legacy_repair_same_surface_report_diff.json")
    assert render_markdown_report_diff(diff) == Path(
        "examples/legacy_repair_same_surface_report_diff.md"
    ).read_text(encoding="utf-8")
