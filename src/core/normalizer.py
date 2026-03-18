from __future__ import annotations

from typing import Any

from .layering import layer_element

JsonDict = dict[str, Any]


def _normalize_traits(traits: Any) -> list[str]:
    if not isinstance(traits, list):
        return []
    return sorted(
        {str(trait).strip().lower() for trait in traits if str(trait).strip()}
    )


def _normalize_bounds(bounds: Any) -> list[int] | None:
    if bounds is None:
        return None
    if not isinstance(bounds, list) or len(bounds) != 4:
        return None
    if not all(isinstance(value, (int, float)) for value in bounds):
        return None
    return [int(value) for value in bounds]


def normalize_project(payload: JsonDict, app_id: str) -> JsonDict:
    screens: list[JsonDict] = []
    nodes: list[JsonDict] = []

    for screen in payload["screens"]:
        screen_id = str(screen["screen_id"]).strip()
        screen_name = str(screen["screen_name"]).strip()
        normalized_elements: list[JsonDict] = []
        for element in screen["elements"]:
            normalized = dict(element)
            normalized["app_id"] = app_id
            normalized["platform"] = payload["platform"]
            normalized["screen_id"] = screen_id
            normalized["screen_name"] = screen_name
            normalized["label"] = str(element.get("label") or "").strip()
            normalized["accessibility_identifier"] = (
                str(element["accessibility_identifier"]).strip()
                if element.get("accessibility_identifier")
                else None
            )
            normalized["parent_id"] = (
                str(element["parent_id"]).strip() if element.get("parent_id") else None
            )
            normalized["traits"] = _normalize_traits(element.get("traits"))
            normalized["bounds"] = _normalize_bounds(element.get("bounds"))
            normalized["slab_layer"] = element.get("slab_layer") or None
            normalized = layer_element(normalized)
            normalized_elements.append(normalized)
            nodes.append(normalized)
        screens.append(
            {
                "screen_id": screen_id,
                "screen_name": screen_name,
                "elements": normalized_elements,
            }
        )

    return {
        "app_id": app_id,
        "project_name": payload["project_name"],
        "platform": payload["platform"],
        "screens": screens,
        "nodes": nodes,
    }
