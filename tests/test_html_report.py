# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from src.core.cli import main
from src.core.report_generator import render_html_report

from tests.helpers import build_report


def test_html_report_is_valid_html():
    report = build_report()
    html = render_html_report(report)
    assert html.startswith("<!DOCTYPE html>")
    assert "<html lang=" in html
    assert "</html>" in html
    assert "<title>" in html
    assert "</title>" in html


def test_html_report_contains_all_sections():
    report = build_report()
    html = render_html_report(report)
    for section in (
        "Summary",
        "Scorecard",
        "Screen Inventory",
        "Findings",
        "Recommendations",
        "Roadmap",
    ):
        assert f">{section}</h2>" in html, f"Missing section: {section}"


def test_html_report_contains_metadata():
    report = build_report()
    html = render_html_report(report)
    assert "com.example.legacyapp" in html
    assert "Legacy Repair App" in html
    assert "2026-03-18T00:00:00Z" in html
    assert "AGPL-3.0-only" in html
    assert "Buildrr89" in html
    assert "5-Slab Taxonomy" in html


def test_html_report_contains_score_bars():
    report = build_report()
    html = render_html_report(report)
    for score_name in (
        "complexity",
        "reusability",
        "accessibility_risk",
        "migration_risk",
    ):
        assert score_name in html, f"Missing score: {score_name}"
    assert 'class="score-bar"' in html
    assert 'class="score-fill"' in html


def test_html_report_contains_finding_details():
    report = build_report()
    html = render_html_report(report)
    assert "accessibility_missing_identifier" in html
    assert "component_reuse_interactive_cluster" in html
    assert 'class="finding-card"' in html
    assert "data-category=" in html


def test_html_report_contains_recommendation_details():
    report = build_report()
    html = render_html_report(report)
    assert "rec-accessibility_missing_identifier-8c7b61bc" in html
    assert 'class="rec-card"' in html
    assert "WCAG" in html


def test_html_report_contains_filter_buttons():
    report = build_report()
    html = render_html_report(report)
    assert 'class="filter-btn active"' in html
    assert 'data-cat="all"' in html
    assert 'data-cat="accessibility"' in html


def test_html_report_contains_roadmap_steps():
    report = build_report()
    html = render_html_report(report)
    assert "Step 1" not in html or "<td>1</td>" in html
    for item in ("P1", "P2"):
        assert item in html


def test_html_report_contains_interactive_js():
    report = build_report()
    html = render_html_report(report)
    assert "<script>" in html
    assert "filter-btn" in html
    assert "data-category" in html


def test_html_report_escapes_special_characters():
    report = build_report()
    html = render_html_report(report)
    assert "<script" not in html.split("</style>")[0].split("<style>")[-1]


def test_html_report_is_deterministic():
    first = render_html_report(build_report())
    second = render_html_report(build_report())
    assert first == second


def test_cli_html_output(tmp_path):
    html_output = tmp_path / "report.html"
    stdout = StringIO()
    with patch(
        "src.core.report_generator.now_iso", return_value="2026-03-18T00:00:00Z"
    ):
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "analyze",
                    "--input",
                    "tests/fixtures/sample_ios_output.json",
                    "--app-id",
                    "com.example.legacyapp",
                    "--html-output",
                    str(html_output),
                ]
            )

    assert exit_code == 0
    assert html_output.exists()
    content = html_output.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "Legacy Repair App" in content
    lines = stdout.getvalue().splitlines()
    assert any("html:" in line for line in lines)


def test_cli_all_outputs(tmp_path):
    json_output = tmp_path / "report.json"
    md_output = tmp_path / "report.md"
    html_output = tmp_path / "report.html"
    stdout = StringIO()
    with patch(
        "src.core.report_generator.now_iso", return_value="2026-03-18T00:00:00Z"
    ):
        with redirect_stdout(stdout):
            exit_code = main(
                [
                    "analyze",
                    "--input",
                    "tests/fixtures/sample_ios_output.json",
                    "--app-id",
                    "com.example.legacyapp",
                    "--json-output",
                    str(json_output),
                    "--md-output",
                    str(md_output),
                    "--html-output",
                    str(html_output),
                ]
            )

    assert exit_code == 0
    assert json_output.exists()
    assert md_output.exists()
    assert html_output.exists()
    lines = stdout.getvalue().splitlines()
    assert lines[0] == "generated 2 screens and 3 recommendations"
    assert any("json:" in line for line in lines)
    assert any("md:" in line for line in lines)
    assert any("html:" in line for line in lines)
