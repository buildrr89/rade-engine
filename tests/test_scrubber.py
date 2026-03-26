# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json

from src.core.layering import CONTAINERS_LAYER
from src.core.report_generator import (
    analyze_payload,
    render_markdown_report,
    write_report,
)
from src.scrubber.pii_scrubber import scrub_payload, scrub_text


def test_scrubber_redacts_common_sensitive_strings():
    text = "Contact alice@example.com or +1 415 555 0101 with token sk_test_12345678."
    scrubbed = scrub_text(text)

    assert "[redacted-email]" in scrubbed
    assert "[redacted-phone]" in scrubbed
    assert "[redacted-token]" in scrubbed


def test_scrubber_redacts_sensitive_mapping_fields():
    payload = {
        "name": "Alice Example",
        "email": "alice@example.com",
        "nested": {"token": "sk_test_12345678", "note": "keep"},
    }

    scrubbed = scrub_payload(payload)

    assert scrubbed["name"] == "[redacted]"
    assert scrubbed["email"] == "[redacted]"
    assert scrubbed["nested"]["token"] == "[redacted]"
    assert scrubbed["nested"]["note"] == "keep"


def test_report_artifacts_are_scrubbed_but_node_refs_stay_stable(tmp_path):
    report = analyze_payload(
        {
            "project_name": "alice@example.com",
            "platform": "ios",
            "screens": [
                {
                    "screen_id": "project-overview",
                    "screen_name": "Project Overview",
                    "elements": [
                        {
                            "element_id": "tok_primary",
                            "parent_id": None,
                            "element_type": "button",
                            "role": "button",
                            "slab_layer": CONTAINERS_LAYER,
                            "label": "Contact alice@example.com",
                            "accessibility_identifier": "",
                            "interactive": True,
                            "visible": True,
                            "bounds": [0, 0, 100, 40],
                            "hierarchy_depth": 0,
                            "child_count": 0,
                            "text_present": True,
                            "traits": ["primary"],
                            "source": "fixture",
                        }
                    ],
                }
            ],
        },
        "com.example.legacyapp",
        generated_at="2026-03-18T00:00:00Z",
    )

    report["recommendations"][0][
        "problem_statement"
    ] = "Contact alice@example.com with token sk_test_12345678."
    report["recommendations"][0]["evidence"] = ["project-overview#tok_primary"]
    report["findings"][0]["evidence"] = ["project-overview#tok_primary"]

    json_output = tmp_path / "report.json"
    md_output = tmp_path / "report.md"
    write_report(report, json_output, md_output)

    written = json.loads(json_output.read_text(encoding="utf-8"))
    markdown = md_output.read_text(encoding="utf-8")

    assert written["project_name"] == "[redacted-email]"
    assert "[redacted-email]" in written["recommendations"][0]["problem_statement"]
    assert "[redacted-token]" in written["recommendations"][0]["problem_statement"]
    assert written["recommendations"][0]["evidence"] == ["project-overview#tok_primary"]
    assert written["findings"][0]["evidence"] == ["project-overview#tok_primary"]
    assert "project-overview#tok_primary" in markdown
    assert "[redacted-email]" in markdown


def test_render_markdown_report_scrubs_sensitive_strings_before_output():
    report = analyze_payload(
        {
            "project_name": "alice@example.com",
            "platform": "ios",
            "screens": [
                {
                    "screen_id": "project-overview",
                    "screen_name": "Project Overview",
                    "elements": [
                        {
                            "element_id": "tok_primary",
                            "parent_id": None,
                            "element_type": "button",
                            "role": "button",
                            "slab_layer": CONTAINERS_LAYER,
                            "label": "Contact alice@example.com",
                            "accessibility_identifier": "",
                            "interactive": True,
                            "visible": True,
                            "bounds": [0, 0, 100, 40],
                            "hierarchy_depth": 0,
                            "child_count": 0,
                            "text_present": True,
                            "traits": ["primary"],
                            "source": "fixture",
                        }
                    ],
                }
            ],
        },
        "com.example.legacyapp",
        generated_at="2026-03-18T00:00:00Z",
    )

    report["project_name"] = "alice@example.com"
    report["recommendations"][0][
        "problem_statement"
    ] = "Contact alice@example.com with token sk_test_12345678."

    markdown = render_markdown_report(report)

    assert "[redacted-email]" in markdown
    assert "[redacted-token]" in markdown
    assert "alice@example.com" not in markdown
