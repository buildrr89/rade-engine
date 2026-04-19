# SPDX-License-Identifier: AGPL-3.0-only
"""Deterministic SVG score badge rendering for RADE reports.

Generates shields.io-style badges so teams can embed RADE scores in their
READMEs. Output is byte-deterministic for identical inputs so badges can be
committed alongside reports without diff churn.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .compliance import (
    LEGAL_NOTICE,
    SVG_HEADER_COMMENT,
    SVG_WATERMARK_TEXT,
    with_legal_metadata,
)

SUPPORTED_METRICS: tuple[str, ...] = (
    "complexity",
    "reusability",
    "accessibility_risk",
    "migration_risk",
)

# Higher is better for these; lower is better for the rest.
_HIGHER_IS_BETTER: frozenset[str] = frozenset({"reusability"})

_LABEL_COLOR = "#555"
_TEXT_COLOR = "#fff"
_SHADOW_COLOR = "#010101"

_METRIC_LABELS: Mapping[str, str] = {
    "complexity": "rade complexity",
    "reusability": "rade reusability",
    "accessibility_risk": "rade a11y risk",
    "migration_risk": "rade migration risk",
}


class BadgeError(ValueError):
    """Raised for invalid badge inputs."""


def _pick_color(metric: str, value: int) -> str:
    # Normalize so "good" is high.
    score = value if metric in _HIGHER_IS_BETTER else 100 - value
    if score >= 90:
        return "#4c1"  # brightgreen
    if score >= 75:
        return "#97ca00"  # green
    if score >= 60:
        return "#a4a61d"  # yellowgreen
    if score >= 40:
        return "#dfb317"  # yellow
    if score >= 20:
        return "#fe7d37"  # orange
    return "#e05d44"  # red


def _text_width(text: str) -> int:
    # Deterministic width heuristic (shields.io uses 7px avg for 11px Verdana).
    return 6 * len(text) + 10


def load_score(report_path: Path, metric: str) -> int:
    if metric not in SUPPORTED_METRICS:
        raise BadgeError(
            f"unsupported metric '{metric}'. "
            f"choose one of: {', '.join(SUPPORTED_METRICS)}"
        )
    try:
        payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BadgeError(f"report not found: {report_path}") from exc
    except json.JSONDecodeError as exc:
        raise BadgeError(f"report is not valid JSON: {report_path}") from exc

    scores = payload.get("scores")
    if not isinstance(scores, dict):
        raise BadgeError("report is missing a 'scores' object")
    entry = scores.get(metric)
    if not isinstance(entry, dict) or "value" not in entry:
        raise BadgeError(f"report does not contain score '{metric}'")
    value = entry["value"]
    if not isinstance(value, int) or not 0 <= value <= 100:
        raise BadgeError(f"score '{metric}' must be an integer 0..100")
    return value


def render_badge_svg(metric: str, value: int) -> str:
    if metric not in SUPPORTED_METRICS:
        raise BadgeError(f"unsupported metric '{metric}'")
    if not isinstance(value, int) or not 0 <= value <= 100:
        raise BadgeError("value must be an integer 0..100")

    label = _METRIC_LABELS[metric]
    message = f"{value}/100"
    label_w = _text_width(label)
    msg_w = _text_width(message)
    total_w = label_w + msg_w
    color = _pick_color(metric, value)

    label_mid = label_w * 10 // 2
    msg_mid = label_w * 10 + msg_w * 10 // 2
    label_text_w = (label_w - 10) * 10
    msg_text_w = (msg_w - 10) * 10

    metadata_text = (
        f"legal_notice={LEGAL_NOTICE} | attribution=Buildrr89 | "
        f"license=AGPL-3.0-only | watermark={SVG_WATERMARK_TEXT}"
    )
    badge_height = 20
    legal_height = 14
    svg_height = badge_height + legal_height
    legal_y = badge_height + 10
    legal_font_size = 9
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f"{SVG_HEADER_COMMENT}\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w}" height="{svg_height}" role="img" '
        f'aria-label="{label}: {message}">'
        f"<title>{label}: {message}</title>"
        f'<metadata id="rade-metadata">{metadata_text}</metadata>'
        f'<linearGradient id="s" x2="0" y2="100%">'
        f'<stop offset="0" stop-color="#bbb" stop-opacity=".1"/>'
        f'<stop offset="1" stop-opacity=".1"/>'
        f"</linearGradient>"
        f'<clipPath id="r"><rect width="{total_w}" height="20" rx="3" fill="#fff"/></clipPath>'
        f'<g clip-path="url(#r)">'
        f'<rect width="{label_w}" height="20" fill="{_LABEL_COLOR}"/>'
        f'<rect x="{label_w}" width="{msg_w}" height="20" fill="{color}"/>'
        f'<rect width="{total_w}" height="20" fill="url(#s)"/>'
        f"</g>"
        f'<g fill="{_TEXT_COLOR}" text-anchor="middle" '
        f'font-family="Verdana,Geneva,DejaVu Sans,sans-serif" '
        f'font-size="110" text-rendering="geometricPrecision">'
        f'<text aria-hidden="true" x="{label_mid}" y="150" '
        f'fill="{_SHADOW_COLOR}" fill-opacity=".3" transform="scale(.1)" '
        f'textLength="{label_text_w}">{label}</text>'
        f'<text x="{label_mid}" y="140" transform="scale(.1)" '
        f'fill="{_TEXT_COLOR}" textLength="{label_text_w}">{label}</text>'
        f'<text aria-hidden="true" x="{msg_mid}" y="150" '
        f'fill="{_SHADOW_COLOR}" fill-opacity=".3" transform="scale(.1)" '
        f'textLength="{msg_text_w}">{message}</text>'
        f'<text x="{msg_mid}" y="140" transform="scale(.1)" '
        f'fill="{_TEXT_COLOR}" textLength="{msg_text_w}">{message}</text>'
        f"</g>"
        f'<g id="rade-legal">'
        f'<text x="{total_w - 4}" y="{legal_y}" text-anchor="end" '
        f'font-family="Menlo,SFMono-Regular,Consolas,monospace" '
        f'font-size="{legal_font_size}" fill="#6fdaa3">{SVG_WATERMARK_TEXT}</text>'
        f"</g>"
        f"</svg>\n"
    )


def render_shields_endpoint(metric: str, value: int) -> dict:
    """Shields.io dynamic endpoint JSON (schemaVersion 1).

    Lets users embed a live badge via:
        https://img.shields.io/endpoint?url=<raw-json-url>
    """
    if metric not in SUPPORTED_METRICS:
        raise BadgeError(f"unsupported metric '{metric}'")
    return with_legal_metadata(
        {
            "schemaVersion": 1,
            "label": _METRIC_LABELS[metric],
            "message": f"{value}/100",
            "color": _pick_color(metric, value).lstrip("#"),
        }
    )


def write_badge(
    report_path: Path,
    metric: str,
    svg_output: Path | None = None,
    endpoint_output: Path | None = None,
) -> int:
    value = load_score(Path(report_path), metric)
    if svg_output is not None:
        svg = render_badge_svg(metric, value)
        svg_output = Path(svg_output)
        svg_output.parent.mkdir(parents=True, exist_ok=True)
        svg_output.write_text(svg, encoding="utf-8")
    if endpoint_output is not None:
        endpoint = render_shields_endpoint(metric, value)
        endpoint_output = Path(endpoint_output)
        endpoint_output.parent.mkdir(parents=True, exist_ok=True)
        endpoint_output.write_text(
            json.dumps(endpoint, indent=2) + "\n",
            encoding="utf-8",
        )
    return value
