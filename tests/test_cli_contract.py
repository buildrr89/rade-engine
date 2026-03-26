# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from src.core.cli import main


def test_cli_analyze_writes_golden_reports(tmp_path):
    json_output = tmp_path / "report.json"
    md_output = tmp_path / "report.md"
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
                ]
            )

    assert exit_code == 0
    assert stdout.getvalue().splitlines() == [
        "generated 2 screens and 3 recommendations",
        f"json: {json_output}",
        f"md: {md_output}",
    ]

    golden_json = json.loads(
        Path("tests/golden/sample_modernization_report.json").read_text(
            encoding="utf-8"
        )
    )
    generated_json = json.loads(json_output.read_text(encoding="utf-8"))
    assert generated_json == golden_json

    golden_md = Path("tests/golden/sample_modernization_report.md").read_text(
        encoding="utf-8"
    )
    generated_md = md_output.read_text(encoding="utf-8")
    assert generated_md == golden_md


def test_cli_analyze_url_uses_collector_and_writes_reports(tmp_path):
    json_output = tmp_path / "report.json"
    md_output = tmp_path / "report.md"
    stdout = StringIO()

    fixture = json.loads(
        Path("tests/fixtures/sample_ios_output.json").read_text(encoding="utf-8")
    )

    with patch("src.core.cli.collect_from_web_dom", return_value=fixture) as collector:
        with patch(
            "src.core.cli.derive_app_id_from_url",
            return_value="com.example.legacyapp",
        ):
            with patch(
                "src.core.report_generator.now_iso",
                return_value="2026-03-18T00:00:00Z",
            ):
                with redirect_stdout(stdout):
                    exit_code = main(
                        [
                            "analyze",
                            "--url",
                            "https://example.com",
                            "--json-output",
                            str(json_output),
                            "--md-output",
                            str(md_output),
                        ]
                    )

    assert exit_code == 0
    collector.assert_called_once_with("https://example.com", timeout_ms=10_000)
    assert stdout.getvalue().splitlines() == [
        "generated 2 screens and 3 recommendations",
        f"json: {json_output}",
        f"md: {md_output}",
    ]

    golden_json = json.loads(
        Path("tests/golden/sample_modernization_report.json").read_text(
            encoding="utf-8"
        )
    )
    generated_json = json.loads(json_output.read_text(encoding="utf-8"))
    assert generated_json == golden_json

    golden_md = Path("tests/golden/sample_modernization_report.md").read_text(
        encoding="utf-8"
    )
    generated_md = md_output.read_text(encoding="utf-8")
    assert generated_md == golden_md
