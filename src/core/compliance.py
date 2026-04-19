# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from typing import Any

SOURCE_HEADER = "SPDX-License-Identifier: AGPL-3.0-only"
ATTRIBUTION = "Buildrr89"
LICENSE_ID = "AGPL-3.0-only"
PROJECT_STATUS = "early alpha"
LEGAL_NOTICE = "Copyright (c) 2026 Buildrr89. Licensed under AGPL-3.0-only."
PROJECT_TERMS_NOTICE = (
    "The labels 5-Slab Taxonomy and Ambient Engine are retained as project "
    "terminology in this repository."
)
TERMINAL_NOTICE = "RADE | BUILDRR89 | EARLY ALPHA"
JSON_LEGAL_KEY = "rade_legal"
SVG_HEADER_COMMENT = f"<!-- {LEGAL_NOTICE} -->"
SVG_WATERMARK_TEXT = "Buildrr89 | RADE alpha"
TECH_GREEN_ANSI = "\033[38;2;98;242;177m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"

_banner_emitted = False


def today_iso_date() -> str:
    return datetime.now(UTC).date().isoformat()


def iso_date_from_timestamp(value: str | None) -> str | None:
    if value is None or "T" not in value:
        return value
    return value.split("T", 1)[0]


def build_legal_metadata(*, live_raid_date: str | None = None) -> dict[str, str]:
    legal = {
        "header_notice": LEGAL_NOTICE,
        "attribution": ATTRIBUTION,
        "license": LICENSE_ID,
        "project_status": PROJECT_STATUS,
        "project_terms_notice": PROJECT_TERMS_NOTICE,
        "visible_svg_watermark": SVG_WATERMARK_TEXT,
    }
    if live_raid_date is not None:
        legal["live_raid_date"] = live_raid_date
    return legal


def with_legal_metadata(
    payload: dict[str, Any], *, live_raid_date: str | None = None
) -> dict[str, Any]:
    normalized = {key: value for key, value in payload.items() if key != JSON_LEGAL_KEY}
    return {
        JSON_LEGAL_KEY: build_legal_metadata(live_raid_date=live_raid_date),
        **normalized,
    }


def markdown_legal_lines(*, live_raid_date: str | None = None) -> list[str]:
    lines = [
        f"- Legal notice: {LEGAL_NOTICE}",
        f"- Attribution: {ATTRIBUTION}",
        f"- License: {LICENSE_ID}",
        f"- Project status: {PROJECT_STATUS}",
        f"- Project terms: {PROJECT_TERMS_NOTICE}",
    ]
    if live_raid_date is not None:
        lines.append(f"- Live Raid date: {live_raid_date}")
    return lines


def render_terminal_banner() -> str:
    return f"{ANSI_BOLD}{TECH_GREEN_ANSI}{TERMINAL_NOTICE}{ANSI_RESET}"


def clear_terminal() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def emit_terminal_banner(stream: Any = None, *, force: bool = False) -> None:
    global _banner_emitted
    if _banner_emitted and not force:
        return
    target = sys.stdout if stream is None else stream
    print(render_terminal_banner(), file=target, flush=True)
    _banner_emitted = True
