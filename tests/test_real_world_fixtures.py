# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from pathlib import Path

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
