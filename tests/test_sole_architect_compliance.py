# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from src.core.compliance import (
    JSON_LEGAL_KEY,
    LEGAL_NOTICE,
    SVG_HEADER_COMMENT,
    SVG_WATERMARK_TEXT,
    TERMINAL_NOTICE,
    render_terminal_banner,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_SUFFIXES = {".py", ".json", ".svg"}
SKIP_PARTS = {".git", ".venv", "node_modules", "__pycache__"}


def _iter_project_files() -> list[Path]:
    return sorted(
        path
        for path in REPO_ROOT.rglob("*")
        if path.is_file()
        and path.suffix in TARGET_SUFFIXES
        and not any(part in SKIP_PARTS for part in path.parts)
    )


def test_terminal_banner_uses_tech_green_founder_notice() -> None:
    banner = render_terminal_banner()
    assert banner.startswith("\033[1m\033[38;2;98;242;177m")
    assert TERMINAL_NOTICE in banner


def test_python_files_have_lead_architect_header() -> None:
    for path in _iter_project_files():
        if path.suffix != ".py":
            continue
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == f"# {LEGAL_NOTICE}", path


def test_json_files_have_header_slot_legal_metadata() -> None:
    for path in _iter_project_files():
        if path.suffix != ".json":
            continue
        raw = path.read_text(encoding="utf-8")
        normalized = raw.lstrip()
        assert normalized.startswith('{\n  "rade_legal": {') or normalized.startswith(
            '{"rade_legal": {'
        ), path
        payload = json.loads(raw)
        assert payload[JSON_LEGAL_KEY]["header_notice"] == LEGAL_NOTICE, path


def test_svg_files_have_legal_header_and_footer_group() -> None:
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    for path in _iter_project_files():
        if path.suffix != ".svg":
            continue
        raw = path.read_text(encoding="utf-8")
        lines = raw.splitlines()
        assert len(lines) >= 2, path
        assert lines[1] == SVG_HEADER_COMMENT, path
        root = ET.fromstring(raw)
        metadata_block = root.find(".//svg:metadata[@id='rade-metadata']", namespace)
        assert metadata_block is not None, path
        legal_group = root.find(".//svg:g[@id='rade-legal']", namespace)
        assert legal_group is not None, path
        assert any(
            (text.text or "") == SVG_WATERMARK_TEXT
            for text in legal_group.findall("svg:text", namespace)
        ), path
