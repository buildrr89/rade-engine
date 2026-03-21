# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from src.core.slab03_hybrid_anchor import (
    apply_landmark_frame_pulse,
    apply_modal_frame_pulse,
    apply_slab03_hybrid_pulse,
    build_figma_frame_alias,
    build_landmark_frame_id,
    landmark_kind_for_element,
)


def test_build_landmark_frame_id_is_deterministic() -> None:
    a = build_landmark_frame_id("root-1", "nav", "primary")
    b = build_landmark_frame_id("root-1", "nav", "primary")
    assert a == b
    assert a.startswith("slab03:landmark:nav:primary:")


def test_build_figma_frame_alias_readable() -> None:
    assert build_figma_frame_alias("nav", "primary") == "Nav_Primary"
    assert build_figma_frame_alias("main", "default") == "Main_Default"
    assert build_figma_frame_alias("modal", "checkout_confirm") == (
        "Modal_Checkout_Confirm"
    )


def test_landmark_nav_and_descendant_share_frame_and_alias() -> None:
    elements = [
        {"element_id": "s", "parent_id": None, "role": "screen", "element_type": "div"},
        {
            "element_id": "nav1",
            "parent_id": "s",
            "role": "navigation",
            "element_type": "nav",
            "label": "Primary",
            "accessibility_identifier": None,
        },
        {
            "element_id": "link1",
            "parent_id": "nav1",
            "role": "link",
            "element_type": "a",
            "label": "Home",
        },
    ]
    out = apply_landmark_frame_pulse(elements)
    by_id = {e["element_id"]: e for e in out}
    nav_row = by_id["nav1"]
    link_row = by_id["link1"]
    assert nav_row["slab03_anchor_kind"] == "a11y:landmark"
    assert link_row["slab03_anchor_kind"] == "a11y:landmark-descendant"
    assert link_row["slab03_frame_id"] == nav_row["slab03_frame_id"]
    assert nav_row["slab03_landmark_kind"] == "nav"
    assert nav_row["slab03_figma_alias"] == "Nav_Primary"
    assert link_row["slab03_figma_alias"] == "Nav_Primary"


def test_nav_link_vs_footer_link_different_frames() -> None:
    elements = [
        {"element_id": "s", "parent_id": None, "role": "screen", "element_type": "div"},
        {
            "element_id": "nav1",
            "parent_id": "s",
            "role": "navigation",
            "element_type": "nav",
            "label": "Main",
        },
        {
            "element_id": "nlink",
            "parent_id": "nav1",
            "role": "link",
            "element_type": "a",
            "label": "Docs",
        },
        {
            "element_id": "foot",
            "parent_id": "s",
            "role": "contentinfo",
            "element_type": "footer",
            "label": "Site",
        },
        {
            "element_id": "flink",
            "parent_id": "foot",
            "role": "link",
            "element_type": "a",
            "label": "Legal",
        },
    ]
    out = apply_landmark_frame_pulse(elements)
    by_id = {e["element_id"]: e for e in out}
    assert by_id["nlink"]["slab03_frame_id"] != by_id["flink"]["slab03_frame_id"]
    assert by_id["nlink"]["slab03_figma_alias"] == "Nav_Main"
    assert by_id["flink"]["slab03_figma_alias"] == "Footer_Site"


def test_innermost_landmark_wins_for_nested_regions() -> None:
    elements = [
        {"element_id": "s", "parent_id": None, "role": "screen", "element_type": "div"},
        {
            "element_id": "hdr",
            "parent_id": "s",
            "role": "banner",
            "element_type": "header",
            "label": "Global",
        },
        {
            "element_id": "nav1",
            "parent_id": "hdr",
            "role": "navigation",
            "element_type": "nav",
            "label": "Primary",
        },
        {
            "element_id": "lnk",
            "parent_id": "nav1",
            "role": "link",
            "element_type": "a",
            "label": "Shop",
        },
    ]
    out = apply_landmark_frame_pulse(elements)
    by_id = {e["element_id"]: e for e in out}
    assert by_id["lnk"]["slab03_landmark_kind"] == "nav"
    assert by_id["lnk"]["slab03_frame_id"] == by_id["nav1"]["slab03_frame_id"]


def test_modal_wins_over_landmark_in_hybrid_pulse() -> None:
    elements = [
        {"element_id": "s", "parent_id": None, "role": "screen", "element_type": "div"},
        {
            "element_id": "main1",
            "parent_id": "s",
            "role": "main",
            "element_type": "main",
            "label": "Content",
        },
        {
            "element_id": "dlg",
            "parent_id": "main1",
            "role": "dialog",
            "element_type": "div",
            "label": "Confirm Purchase",
        },
        {
            "element_id": "ok",
            "parent_id": "dlg",
            "role": "button",
            "element_type": "button",
            "label": "OK",
        },
        {
            "element_id": "aside1",
            "parent_id": "main1",
            "role": "text",
            "element_type": "p",
            "label": "Hint",
        },
    ]
    out = apply_slab03_hybrid_pulse(elements)
    by_id = {e["element_id"]: e for e in out}
    assert by_id["ok"]["slab03_frame_id"] == "slab03:modal:dlg"
    assert by_id["ok"]["slab03_anchor_kind"] == "a11y:dialog-descendant"
    assert "Confirm" in by_id["ok"]["slab03_figma_alias"]
    assert by_id["aside1"]["slab03_frame_id"].startswith("slab03:landmark:main:")
    assert by_id["aside1"]["slab03_anchor_kind"] == "a11y:landmark-descendant"


def test_landmark_kind_for_element_heading_not_header() -> None:
    assert (
        landmark_kind_for_element(
            {"role": "heading", "element_type": "h1", "traits": []}
        )
        is None
    )


def test_modal_pulse_alone_does_not_set_landmark_kind() -> None:
    elements = [
        {"element_id": "d", "parent_id": None, "role": "dialog", "element_type": "div"},
        {"element_id": "b", "parent_id": "d", "role": "button", "element_type": "button"},
    ]
    out = apply_modal_frame_pulse(elements)
    assert "slab03_landmark_kind" not in out[1]
