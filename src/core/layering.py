# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from typing import Any

JsonDict = dict[str, Any]

OS_SITE_LAYER = "01. OS Site (The Land)"
ROOT_LAYER = "02. Root (The Slab)"
CONTAINERS_LAYER = "03. Containers (The Frame)"
LINKS_EVENTS_LAYER = "04. Links/Events (Wires & Plumbing)"
ASSETS_LAYER = "05. Assets (The Decor)"
VALID_LAYERS = frozenset(
    {
        OS_SITE_LAYER,
        ROOT_LAYER,
        CONTAINERS_LAYER,
        LINKS_EVENTS_LAYER,
        ASSETS_LAYER,
    }
)
_VALID_LAYER_LOOKUP = {layer.casefold(): layer for layer in VALID_LAYERS}

OS_SITE_TYPES = {"screen", "container", "viewport", "shell"}
ROOT_TYPES = {"card", "stack", "grid", "list", "section", "group"}
CONTAINERS_TYPES = {
    "button",
    "link",
    "input",
    "toggle",
    "switch",
    "checkbox",
    "radio",
    "tab",
}
LINKS_EVENTS_TYPES = {"text", "label", "heading", "copy", "image", "media"}


def normalize_slab_layer(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return _VALID_LAYER_LOOKUP.get(normalized.casefold())


def infer_slab_layer(element: JsonDict) -> str:
    explicit = normalize_slab_layer(element.get("slab_layer"))
    if explicit is not None:
        return explicit

    element_type = str(element.get("element_type", "")).strip().lower()
    role = str(element.get("role", "")).strip().lower()
    interactive = bool(element.get("interactive"))
    text_present = bool(element.get("text_present"))
    depth = int(element.get("hierarchy_depth", 0) or 0)

    if depth == 0 and (role == "screen" or element_type in OS_SITE_TYPES):
        return OS_SITE_LAYER
    if element_type in ROOT_TYPES or role in {
        "summary",
        "section",
        "cluster",
        "group",
    }:
        return ROOT_LAYER
    if (
        interactive
        or element_type in CONTAINERS_TYPES
        or role in {"button", "link", "input", "toggle", "switch"}
    ):
        return CONTAINERS_LAYER
    if (
        text_present
        or element_type in LINKS_EVENTS_TYPES
        or role in {"heading", "label", "text", "copy"}
    ):
        return LINKS_EVENTS_LAYER
    return ASSETS_LAYER


def layer_element(element: JsonDict) -> JsonDict:
    updated = dict(element)
    updated["slab_layer"] = infer_slab_layer(updated)
    return updated
