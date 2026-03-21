# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
"""Slab 03 (Frame) hybrid anchor heuristics — Phase 1 componentization.

Pulses (in order):

1. **Modal** — ``dialog`` / ``alertdialog`` roots; innermost modal wins when nested.
2. **Landmark** — semantic regions (nav, main, aside, header, footer); innermost
   landmark wins; **skipped** when a node already has a modal frame (dialog wins).
3. **VBox (tertiary)** — geometric containment: nodes still without a Slab 03 frame
   whose center lies inside a **landmark root**'s bounds inherit that landmark's
   ``slab03_frame_id`` with ``visual:vbox-contained``. Never overrides modal or
   prior landmark assignments.
"""
from __future__ import annotations

from typing import Any, Iterable

from .models import stable_digest

JsonDict = dict[str, Any]

_MODAL_ROLES = frozenset({"dialog", "alertdialog"})
_MODAL_TRAIT_TOKENS = frozenset({"dialog", "alertdialog"})

# ARIA / HTML landmark roles and coarse element_type hints.
_LANDMARK_NAV_ROLES = frozenset({"navigation", "nav"})
_LANDMARK_MAIN_ROLES = frozenset({"main"})
_LANDMARK_ASIDE_ROLES = frozenset({"complementary", "aside"})
_LANDMARK_HEADER_ROLES = frozenset({"banner"})
_LANDMARK_FOOTER_ROLES = frozenset({"contentinfo", "footer"})

_FIGMA_PREFIX_BY_KIND: dict[str, str] = {
    "modal": "Modal",
    "nav": "Nav",
    "main": "Main",
    "aside": "Sidebar",
    "header": "Header",
    "footer": "Footer",
}


def _normalize_token(value: Any) -> str:
    return str(value or "").strip().lower()


def _element_id(element: JsonDict) -> str:
    raw = element.get("element_id")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    fallback = element.get("node_ref")
    if fallback is not None and str(fallback).strip():
        return str(fallback).strip()
    return ""


def _parent_id(element: JsonDict) -> str | None:
    raw = element.get("parent_id")
    if raw is None:
        return None
    s = str(raw).strip()
    return s if s else None


def _normalize_traits(element: JsonDict) -> list[str]:
    traits = element.get("traits")
    if isinstance(traits, (list, tuple)):
        return [_normalize_token(t) for t in traits if _normalize_token(t)]
    return []


def is_modal_frame_root(element: JsonDict) -> bool:
    """True if this node should open its own Slab 03 frame (dialog surface).

    Matches ARIA dialog roles and common trait/element_type spellings from trees.
    """
    role = _normalize_token(element.get("role"))
    if role in _MODAL_ROLES:
        return True
    element_type = _normalize_token(element.get("element_type"))
    if element_type in ("dialog", "alertdialog"):
        return True
    traits = element.get("traits")
    if isinstance(traits, (list, tuple)):
        for t in traits:
            if _normalize_token(t) in _MODAL_TRAIT_TOKENS:
                return True
    return False


def landmark_kind_for_element(element: JsonDict) -> str | None:
    """Return canonical landmark kind if this node is a landmark root, else None.

    Order matters: first match wins (nav before loose element_type checks).
    """
    role = _normalize_token(element.get("role"))
    element_type = _normalize_token(element.get("element_type"))
    traits = _normalize_traits(element)

    if role == "heading":
        return None

    if role in _LANDMARK_NAV_ROLES or any(
        t in _LANDMARK_NAV_ROLES for t in traits
    ):
        return "nav"
    if "navigation" in element_type or "navigationbar" in element_type.replace(
        " ", ""
    ):
        return "nav"

    if role in _LANDMARK_MAIN_ROLES or "main" in traits:
        return "main"
    if element_type == "main" or element_type.endswith(".main"):
        return "main"

    if role in _LANDMARK_ASIDE_ROLES or "complementary" in traits:
        return "aside"
    if element_type == "aside" or "sidebar" in element_type:
        return "aside"

    if role in _LANDMARK_HEADER_ROLES:
        return "header"
    if element_type == "header":
        return "header"

    if role in _LANDMARK_FOOTER_ROLES:
        return "footer"
    if element_type == "footer":
        return "footer"

    return None


def is_landmark_frame_root(element: JsonDict) -> bool:
    return landmark_kind_for_element(element) is not None


def find_modal_frame_roots(elements: Iterable[JsonDict]) -> list[str]:
    """Return stable element ids that are modal/dialog frame roots."""
    roots: list[str] = []
    seen: set[str] = set()
    for el in elements:
        eid = _element_id(el)
        if not eid or eid in seen:
            continue
        if is_modal_frame_root(el):
            roots.append(eid)
            seen.add(eid)
    return roots


def _nearest_modal_root_id(by_id: dict[str, JsonDict], start_id: str) -> str | None:
    """Innermost modal ancestor when walking from ``start_id`` toward the root."""
    cur: str | None = start_id
    while cur:
        el = by_id.get(cur)
        if el is not None and is_modal_frame_root(el):
            return cur
        el_for_parent = el
        cur = _parent_id(el_for_parent) if el_for_parent is not None else None
    return None


def _nearest_landmark_root_id(by_id: dict[str, JsonDict], start_id: str) -> str | None:
    """Innermost landmark ancestor (nav, main, …) when walking upward."""
    cur: str | None = start_id
    while cur:
        el = by_id.get(cur)
        if el is not None and is_landmark_frame_root(el):
            return cur
        el_for_parent = el
        cur = _parent_id(el_for_parent) if el_for_parent is not None else None
    return None


def _label_slug(label: str, accessibility_identifier: str | None) -> str:
    raw = (accessibility_identifier or label or "").strip().lower()
    if not raw:
        return "default"
    parts: list[str] = []
    for c in raw:
        if c.isalnum():
            parts.append(c)
        elif c in (" ", "-", ".", "/", ":"):
            parts.append("_")
    s = "".join(parts).strip("_")
    while "__" in s:
        s = s.replace("__", "_")
    return (s[:48] or "default")


def build_landmark_frame_id(root_id: str, kind: str, slug: str) -> str:
    scope = stable_digest(root_id, kind, slug)
    return f"slab03:landmark:{kind}:{slug}:{scope}"


def _parse_bounds_rect(element: JsonDict) -> tuple[int, int, int, int] | None:
    """Return ``(x, y, width, height)`` from ``bounding_box`` or ``bounds``."""
    bbox = element.get("bounding_box")
    if isinstance(bbox, dict):
        try:
            x = int(float(bbox["x"]))
            y = int(float(bbox["y"]))
            w = int(float(bbox["width"]))
            h = int(float(bbox["height"]))
        except (KeyError, TypeError, ValueError):
            pass
        else:
            if w > 0 and h > 0:
                return (x, y, w, h)
    raw = element.get("bounds")
    if isinstance(raw, (list, tuple)) and len(raw) == 4:
        try:
            x, y, w, h = (int(float(raw[i])) for i in range(4))
        except (TypeError, ValueError):
            return None
        if w > 0 and h > 0:
            return (x, y, w, h)
    return None


def _rect_area(rect: tuple[int, int, int, int]) -> int:
    return rect[2] * rect[3]


def _center_inside_rect(
    rect: tuple[int, int, int, int], cx: float, cy: float
) -> bool:
    x, y, w, h = rect
    return x <= cx <= x + w and y <= cy <= y + h


def build_figma_frame_alias(kind: str, slug: str) -> str:
    prefix = _FIGMA_PREFIX_BY_KIND.get(kind, kind.title())
    tail = slug.replace("-", "_")
    segments = [seg for seg in tail.split("_") if seg]
    if not segments:
        tail_title = "Default"
    else:
        tail_title = "_".join(seg.title() for seg in segments)
    return f"{prefix}_{tail_title}"


def apply_modal_frame_pulse(elements: list[JsonDict]) -> list[JsonDict]:
    """Annotate elements with Slab 03 modal frame metadata."""
    if not elements:
        return []

    by_id: dict[str, JsonDict] = {}
    order_ids: list[str] = []

    for el in elements:
        eid = _element_id(el)
        if not eid or eid in by_id:
            continue
        by_id[eid] = el
        order_ids.append(eid)

    assigned_frame: dict[str, str] = {}
    assigned_kind: dict[str, str] = {}
    assigned_figma: dict[str, str] = {}
    modal_figma_by_root: dict[str, str] = {}

    for eid in order_ids:
        root_id = _nearest_modal_root_id(by_id, eid)
        if root_id is None:
            continue
        frame_id = f"slab03:modal:{root_id}"
        assigned_frame[eid] = frame_id
        assigned_kind[eid] = (
            "a11y:dialog" if eid == root_id else "a11y:dialog-descendant"
        )
        if root_id not in modal_figma_by_root:
            rel = by_id[root_id]
            mslug = _label_slug(
                str(rel.get("label") or ""),
                rel.get("accessibility_identifier"),
            )
            modal_figma_by_root[root_id] = build_figma_frame_alias("modal", mslug)
        assigned_figma[eid] = modal_figma_by_root[root_id]

    out: list[JsonDict] = []
    for el in elements:
        eid = _element_id(el)
        merged = dict(el)
        if eid in assigned_frame:
            merged["slab03_frame_id"] = assigned_frame[eid]
            merged["slab03_anchor_kind"] = assigned_kind[eid]
            merged["slab03_figma_alias"] = assigned_figma[eid]
        out.append(merged)
    return out


def apply_landmark_frame_pulse(elements: list[JsonDict]) -> list[JsonDict]:
    """Add landmark-based ``slab03_frame_id`` where modal pulse did not assign one.

    Preserves existing ``slab03_frame_id`` / ``slab03_anchor_kind`` / modal figma alias.
    """
    if not elements:
        return []

    by_id: dict[str, JsonDict] = {}
    order_ids: list[str] = []

    for el in elements:
        eid = _element_id(el)
        if not eid or eid in by_id:
            continue
        by_id[eid] = el
        order_ids.append(eid)

    assigned_frame: dict[str, str] = {}
    assigned_kind: dict[str, str] = {}
    assigned_landmark_kind: dict[str, str] = {}
    assigned_figma: dict[str, str] = {}

    for eid in order_ids:
        base = by_id[eid]
        existing_modal = str(base.get("slab03_frame_id") or "").startswith(
            "slab03:modal:"
        )
        if existing_modal:
            continue
        root_id = _nearest_landmark_root_id(by_id, eid)
        if root_id is None:
            continue
        root_el = by_id[root_id]
        kind = landmark_kind_for_element(root_el)
        if kind is None:
            continue
        slug = _label_slug(
            str(root_el.get("label") or ""),
            root_el.get("accessibility_identifier"),
        )
        frame_id = build_landmark_frame_id(root_id, kind, slug)
        assigned_frame[eid] = frame_id
        assigned_kind[eid] = (
            "a11y:landmark" if eid == root_id else "a11y:landmark-descendant"
        )
        assigned_landmark_kind[eid] = kind
        assigned_figma[eid] = build_figma_frame_alias(kind, slug)

    out: list[JsonDict] = []
    for el in elements:
        eid = _element_id(el)
        merged = dict(el)
        if eid in assigned_frame:
            merged["slab03_frame_id"] = assigned_frame[eid]
            merged["slab03_anchor_kind"] = assigned_kind[eid]
            merged["slab03_landmark_kind"] = assigned_landmark_kind[eid]
            merged["slab03_figma_alias"] = assigned_figma[eid]
        out.append(merged)
    return out


def apply_vbox_tertiary_pulse(elements: list[JsonDict]) -> list[JsonDict]:
    """Assign Slab 03 frames by visual containment inside landmark roots (tertiary).

    Runs after modal + landmark pulses. Only elements **without** an existing
    ``slab03_frame_id`` are considered. Containers are nodes with
    ``slab03_anchor_kind == a11y:landmark`` that have parseable bounds. When
    multiple landmarks contain the orphan's center, the **smallest-area** root
    wins (then ``element_id``) for determinism.
    """
    if not elements:
        return []

    containers: list[dict[str, Any]] = []
    for el in elements:
        if str(el.get("slab03_anchor_kind") or "") != "a11y:landmark":
            continue
        frame_id = el.get("slab03_frame_id")
        if not frame_id or not str(frame_id).strip():
            continue
        rect = _parse_bounds_rect(el)
        if rect is None:
            continue
        kind = str(el.get("slab03_landmark_kind") or "").strip()
        if not kind:
            lk = landmark_kind_for_element(el)
            kind = lk if lk else "unknown"
        figma = el.get("slab03_figma_alias")
        figma_s = str(figma).strip() if figma is not None else ""
        containers.append(
            {
                "eid": _element_id(el),
                "frame_id": str(frame_id).strip(),
                "landmark_kind": kind,
                "figma_alias": figma_s or build_figma_frame_alias(kind, "default"),
                "rect": rect,
                "area": _rect_area(rect),
            }
        )

    out: list[JsonDict] = []
    for el in elements:
        merged = dict(el)
        if merged.get("slab03_frame_id"):
            out.append(merged)
            continue
        rect = _parse_bounds_rect(merged)
        if rect is None:
            out.append(merged)
            continue
        x, y, w, h = rect
        cx = x + w / 2.0
        cy = y + h / 2.0
        candidates = [
            c
            for c in containers
            if _center_inside_rect(c["rect"], cx, cy)
        ]
        if not candidates:
            out.append(merged)
            continue
        pick = min(candidates, key=lambda c: (c["area"], c["eid"]))
        merged["slab03_frame_id"] = pick["frame_id"]
        merged["slab03_anchor_kind"] = "visual:vbox-contained"
        merged["slab03_landmark_kind"] = pick["landmark_kind"]
        merged["slab03_figma_alias"] = pick["figma_alias"]
        out.append(merged)
    return out


def apply_slab03_hybrid_pulse(elements: list[JsonDict]) -> list[JsonDict]:
    """Run modal pulse, then landmark pulse, then VBox tertiary (dialog always wins)."""
    return apply_vbox_tertiary_pulse(
        apply_landmark_frame_pulse(apply_modal_frame_pulse(elements))
    )
