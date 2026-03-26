# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from src.core.slab03_hybrid_anchor import (
    apply_modal_frame_pulse,
    apply_slab03_hybrid_pulse,
    apply_vbox_tertiary_pulse,
    find_modal_frame_roots,
    is_modal_frame_root,
)


def test_is_modal_frame_root_role_dialog() -> None:
    assert is_modal_frame_root({"role": "dialog", "element_id": "a"})
    assert is_modal_frame_root({"role": "alertdialog", "element_id": "b"})


def test_is_modal_frame_root_traits() -> None:
    assert is_modal_frame_root(
        {"role": "group", "traits": ["Dialog", "focusable"], "element_id": "c"}
    )


def test_find_modal_frame_roots_order_and_dedupe() -> None:
    els = [
        {"element_id": "main", "parent_id": None, "role": "main"},
        {"element_id": "dlg", "parent_id": "root", "role": "dialog"},
        {"element_id": "dup", "parent_id": None, "role": "dialog"},
        {"element_id": "dup", "parent_id": None, "role": "button"},
    ]
    roots = find_modal_frame_roots(els)
    assert roots == ["dlg", "dup"]


def test_apply_modal_frame_pulse_subtree_not_swallowed_by_main() -> None:
    """Dialog subtree under 'main' keeps slab03:modal:* frame, not main's DOM ancestry."""
    elements = [
        {"element_id": "screen", "parent_id": None, "role": "screen"},
        {"element_id": "main", "parent_id": "screen", "role": "main"},
        {
            "element_id": "portal-host",
            "parent_id": "main",
            "role": "group",
        },
        {"element_id": "modal-root", "parent_id": "portal-host", "role": "dialog"},
        {"element_id": "modal-title", "parent_id": "modal-root", "role": "heading"},
        {"element_id": "modal-ok", "parent_id": "modal-root", "role": "button"},
    ]
    enriched = apply_modal_frame_pulse(elements)
    by_id = {e["element_id"]: e for e in enriched}

    assert by_id["modal-root"]["slab03_frame_id"] == "slab03:modal:modal-root"
    assert by_id["modal-root"]["slab03_anchor_kind"] == "a11y:dialog"
    assert by_id["modal-title"]["slab03_frame_id"] == "slab03:modal:modal-root"
    assert by_id["modal-title"]["slab03_anchor_kind"] == "a11y:dialog-descendant"
    assert by_id["modal-ok"]["slab03_frame_id"] == "slab03:modal:modal-root"

    assert "slab03_frame_id" not in by_id["main"]
    assert "slab03_frame_id" not in by_id["portal-host"]


def test_nested_modal_inner_frame_wins_for_descendants() -> None:
    elements = [
        {"element_id": "outer", "parent_id": "screen", "role": "dialog"},
        {"element_id": "inner", "parent_id": "outer", "role": "dialog"},
        {"element_id": "btn", "parent_id": "inner", "role": "button"},
    ]
    enriched = apply_modal_frame_pulse(elements)
    by_id = {e["element_id"]: e for e in enriched}
    assert by_id["btn"]["slab03_frame_id"] == "slab03:modal:inner"
    assert by_id["inner"]["slab03_anchor_kind"] == "a11y:dialog"
    assert by_id["outer"]["slab03_anchor_kind"] == "a11y:dialog"


def test_element_type_alertdialog_is_modal_root() -> None:
    assert is_modal_frame_root({"element_type": "alertdialog", "element_id": "x"})


def test_vbox_tertiary_sweeps_floating_fab_into_main_landmark() -> None:
    """FAB is a DOM sibling of main but geometrically over main → vbox frame match."""
    elements = [
        {
            "element_id": "screen",
            "parent_id": None,
            "role": "screen",
            "bounds": [0, 0, 400, 800],
        },
        {
            "element_id": "main-root",
            "parent_id": "screen",
            "role": "main",
            "element_type": "main",
            "label": "Editorial",
            "bounds": [0, 80, 400, 640],
        },
        {
            "element_id": "fab",
            "parent_id": "screen",
            "role": "button",
            "element_type": "button",
            "traits": ["button"],
            "label": "Compose",
            "bounds": [320, 600, 56, 56],
        },
    ]
    out = apply_slab03_hybrid_pulse(elements)
    by_id = {e["element_id"]: e for e in out}
    main_frame = by_id["main-root"]["slab03_frame_id"]
    assert by_id["fab"]["slab03_frame_id"] == main_frame
    assert by_id["fab"]["slab03_anchor_kind"] == "visual:vbox-contained"
    assert by_id["fab"]["slab03_landmark_kind"] == "main"
    assert (
        by_id["fab"]["slab03_figma_alias"] == by_id["main-root"]["slab03_figma_alias"]
    )


def test_vbox_prefers_smallest_containing_landmark() -> None:
    """When center lies in nested landmark rects, smallest area wins."""
    elements = [
        {
            "element_id": "screen",
            "parent_id": None,
            "role": "screen",
            "bounds": [0, 0, 400, 900],
        },
        {
            "element_id": "main-root",
            "parent_id": "screen",
            "role": "main",
            "element_type": "main",
            "label": "App",
            "bounds": [0, 0, 400, 800],
        },
        {
            "element_id": "nav1",
            "parent_id": "main-root",
            "role": "navigation",
            "element_type": "nav",
            "label": "Top",
            "bounds": [0, 0, 400, 72],
        },
        {
            "element_id": "floater",
            "parent_id": "screen",
            "role": "button",
            "element_type": "button",
            "label": "InNav",
            "bounds": [180, 16, 40, 40],
        },
    ]
    out = apply_slab03_hybrid_pulse(elements)
    by_id = {e["element_id"]: e for e in out}
    assert by_id["floater"]["slab03_frame_id"] == by_id["nav1"]["slab03_frame_id"]
    assert by_id["floater"]["slab03_anchor_kind"] == "visual:vbox-contained"
    assert by_id["floater"]["slab03_landmark_kind"] == "nav"


def test_vbox_does_not_override_modal_subtree_even_if_inside_main_bounds() -> None:
    elements = [
        {
            "element_id": "screen",
            "parent_id": None,
            "role": "screen",
            "bounds": [0, 0, 400, 800],
        },
        {
            "element_id": "main-root",
            "parent_id": "screen",
            "role": "main",
            "element_type": "main",
            "label": "Content",
            "bounds": [0, 0, 400, 800],
        },
        {
            "element_id": "dlg",
            "parent_id": "main-root",
            "role": "dialog",
            "element_type": "div",
            "label": "Alert",
            "bounds": [50, 100, 300, 200],
        },
        {
            "element_id": "ok",
            "parent_id": "dlg",
            "role": "button",
            "element_type": "button",
            "label": "OK",
            "bounds": [100, 220, 80, 44],
        },
    ]
    out = apply_slab03_hybrid_pulse(elements)
    by_id = {e["element_id"]: e for e in out}
    assert by_id["ok"]["slab03_frame_id"] == "slab03:modal:dlg"
    assert by_id["ok"]["slab03_anchor_kind"] == "a11y:dialog-descendant"


def test_vbox_tertiary_accepts_bounding_box_dict() -> None:
    after_landmark = [
        {
            "element_id": "m",
            "parent_id": None,
            "role": "main",
            "slab03_frame_id": "slab03:landmark:main:app:abc",
            "slab03_anchor_kind": "a11y:landmark",
            "slab03_landmark_kind": "main",
            "slab03_figma_alias": "Main_App",
            "bounding_box": {"x": 0, "y": 0, "width": 200, "height": 200},
        },
        {
            "element_id": "orphan",
            "parent_id": None,
            "role": "button",
            "bounding_box": {"x": 80, "y": 80, "width": 40, "height": 40},
        },
    ]
    out = apply_vbox_tertiary_pulse(after_landmark)
    by_id = {e["element_id"]: e for e in out}
    assert by_id["orphan"]["slab03_frame_id"] == "slab03:landmark:main:app:abc"
    assert by_id["orphan"]["slab03_anchor_kind"] == "visual:vbox-contained"
