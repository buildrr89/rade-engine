# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.badge import (
    BadgeError,
    load_score,
    render_badge_svg,
    render_shields_endpoint,
    write_badge,
)
from src.core.cli import main

EXAMPLE_REPORT = Path("examples/python_org_homepage_report.json")


def test_load_score_reads_metric_value() -> None:
    assert load_score(EXAMPLE_REPORT, "reusability") == 98


def test_load_score_rejects_unknown_metric() -> None:
    with pytest.raises(BadgeError):
        load_score(EXAMPLE_REPORT, "vibes")


def test_load_score_rejects_missing_report(tmp_path: Path) -> None:
    with pytest.raises(BadgeError):
        load_score(tmp_path / "nope.json", "reusability")


def test_render_badge_svg_is_deterministic() -> None:
    a = render_badge_svg("reusability", 98)
    b = render_badge_svg("reusability", 98)
    assert a == b
    assert a.startswith('<?xml version="1.0"')
    assert "<svg" in a
    assert "rade reusability" in a
    assert 'id="rade-legal"' in a
    assert 'id="rade-metadata"' in a
    assert "98/100" in a


def test_render_badge_svg_color_flips_by_direction() -> None:
    # reusability: higher is better -> high value is green
    assert "#4c1" in render_badge_svg("reusability", 95)
    # accessibility_risk: lower is better -> low value is green
    assert "#4c1" in render_badge_svg("accessibility_risk", 5)
    assert "#e05d44" in render_badge_svg("accessibility_risk", 95)


def test_shields_endpoint_shape() -> None:
    payload = render_shields_endpoint("reusability", 98)
    assert payload["schemaVersion"] == 1
    assert payload["label"] == "rade reusability"
    assert payload["message"] == "98/100"
    assert payload["color"] == "4c1"
    assert payload["rade_legal"]["license"] == "AGPL-3.0-only"


def test_write_badge_emits_svg_and_endpoint(tmp_path: Path) -> None:
    svg_out = tmp_path / "badge.svg"
    endpoint_out = tmp_path / "badge.json"
    value = write_badge(
        EXAMPLE_REPORT,
        "reusability",
        svg_output=svg_out,
        endpoint_output=endpoint_out,
    )
    assert value == 98
    assert svg_out.read_text(encoding="utf-8").startswith('<?xml version="1.0"')
    data = json.loads(endpoint_out.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == 1
    assert data["message"] == "98/100"


def test_cli_badge_command_roundtrip(tmp_path: Path) -> None:
    svg_out = tmp_path / "badge.svg"
    rc = main(
        [
            "badge",
            "--report",
            str(EXAMPLE_REPORT),
            "--metric",
            "reusability",
            "--svg-output",
            str(svg_out),
        ]
    )
    assert rc == 0
    assert svg_out.exists()
    # Determinism: two runs produce byte-identical output.
    first = svg_out.read_bytes()
    main(
        [
            "badge",
            "--report",
            str(EXAMPLE_REPORT),
            "--metric",
            "reusability",
            "--svg-output",
            str(svg_out),
        ]
    )
    assert svg_out.read_bytes() == first


def test_cli_badge_requires_an_output(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(
            [
                "badge",
                "--report",
                str(EXAMPLE_REPORT),
                "--metric",
                "reusability",
            ]
        )
