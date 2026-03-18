from __future__ import annotations

from typing import Any

JsonDict = dict[str, Any]

FOUNDATION_TYPES = {"screen", "container", "viewport", "shell"}
FRAMEWORK_TYPES = {"card", "stack", "grid", "list", "section", "group"}
SYSTEM_TYPES = {
    "button",
    "link",
    "input",
    "toggle",
    "switch",
    "checkbox",
    "radio",
    "tab",
}
FITOUT_TYPES = {"text", "label", "heading", "copy", "image", "media"}
VALID_LAYERS = {"foundation", "framework", "systems", "fitout", "finish"}


def infer_slab_layer(element: JsonDict) -> str:
    explicit = element.get("slab_layer")
    if isinstance(explicit, str) and explicit.strip():
        layer = explicit.strip().lower()
        if layer in VALID_LAYERS:
            return layer

    element_type = str(element.get("element_type", "")).strip().lower()
    role = str(element.get("role", "")).strip().lower()
    interactive = bool(element.get("interactive"))
    text_present = bool(element.get("text_present"))
    depth = int(element.get("hierarchy_depth", 0) or 0)

    if depth == 0 and (role == "screen" or element_type in FOUNDATION_TYPES):
        return "foundation"
    if element_type in FRAMEWORK_TYPES or role in {
        "summary",
        "section",
        "cluster",
        "group",
    }:
        return "framework"
    if (
        interactive
        or element_type in SYSTEM_TYPES
        or role in {"button", "link", "input", "toggle", "switch"}
    ):
        return "systems"
    if (
        text_present
        or element_type in FITOUT_TYPES
        or role in {"heading", "label", "text", "copy"}
    ):
        return "fitout"
    return "finish"


def layer_element(element: JsonDict) -> JsonDict:
    updated = dict(element)
    updated["slab_layer"] = infer_slab_layer(updated)
    return updated
