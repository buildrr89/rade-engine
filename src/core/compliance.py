# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from typing import Any

LEAD_ARCHITECT = "Trung Nguyen - BUILDRR89"
IP_OWNER = "Trung Nguyen (Buildrr89)"
LEGAL_NOTICE = (
    "© 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - "
    "BUILDRR89. "
    "Confidential Construction Data Model."
)
LEAD_ARCHITECT_NOTICE = (
    "The 5-Slab Taxonomy and Ambient Engine are the exclusive intellectual "
    "property of Trung Nguyen (Buildrr89)."
)
TERMINAL_NOTICE = "RADE PROJECT | LEAD ARCHITECT: TRUNG NGUYEN - BUILDRR89"
JSON_LEGAL_KEY = "rade_legal"
SVG_HEADER_COMMENT = f"<!-- {LEGAL_NOTICE} -->"
SVG_WATERMARK_TEXT = f"© 2026 RADE Project | Lead Architect: {LEAD_ARCHITECT}"
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
        "lead_architect": LEAD_ARCHITECT,
        "classification": "Confidential Construction Data Model",
        "ownership": f"Exclusive intellectual property of {IP_OWNER}",
        "proprietary_systems": (
            "The 5-Slab Taxonomy and Ambient Engine are the exclusive intellectual "
            f"property of {IP_OWNER}."
        ),
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
        f"- Ownership: Exclusive intellectual property of {IP_OWNER}.",
        (
            "- Proprietary systems: The 5-Slab Taxonomy and Ambient Engine are "
            f"the exclusive intellectual property of {IP_OWNER}."
        ),
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
