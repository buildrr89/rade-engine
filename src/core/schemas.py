# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .layering import VALID_LAYERS, normalize_slab_layer

JsonDict = dict[str, Any]
ALLOWED_PLATFORMS = {"ios", "android", "web"}


class ValidationError(ValueError):
    """Raised when the input fixture does not match the data contract."""


def load_json_file(path: Path | str) -> JsonDict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValidationError("The top-level payload must be a JSON object.")
    return payload


def _require_str(mapping: dict[str, Any], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{context}: '{key}' must be a non-empty string.")
    return value.strip()


def _require_optional_str(
    mapping: dict[str, Any], key: str, context: str
) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{context}: '{key}' must be a string or null.")
    value = value.strip()
    return value or None


def _require_optional_slab_layer(
    mapping: dict[str, Any], key: str, context: str
) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{context}: '{key}' must be a string or null.")
    normalized = normalize_slab_layer(value)
    if normalized is None:
        raise ValidationError(
            f"{context}: '{key}' must be one of {sorted(VALID_LAYERS)} or null."
        )
    return normalized


def _require_label(mapping: dict[str, Any], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str):
        raise ValidationError(f"{context}: '{key}' must be a string.")
    return value.strip()


def _require_bool(mapping: dict[str, Any], key: str, context: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ValidationError(f"{context}: '{key}' must be a boolean.")
    return value


def _require_int(mapping: dict[str, Any], key: str, context: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int):
        raise ValidationError(f"{context}: '{key}' must be an integer.")
    return value


def _require_non_negative_int(mapping: dict[str, Any], key: str, context: str) -> int:
    value = _require_int(mapping, key, context)
    if value < 0:
        raise ValidationError(f"{context}: '{key}' must be zero or greater.")
    return value


def _require_list(mapping: dict[str, Any], key: str, context: str) -> list[Any]:
    value = mapping.get(key)
    if not isinstance(value, list):
        raise ValidationError(f"{context}: '{key}' must be an array.")
    return value


def _require_str_list(mapping: dict[str, Any], key: str, context: str) -> list[str]:
    value = _require_list(mapping, key, context)
    for item_index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValidationError(f"{context}: '{key}[{item_index}]' must be a string.")
    return list(value)


def _require_bounds(
    mapping: dict[str, Any], key: str, context: str
) -> list[Any] | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 4:
        raise ValidationError(
            f"{context}: '{key}' must be an array of four numbers or null."
        )
    if not all(
        isinstance(item, (int, float)) and not isinstance(item, bool) for item in value
    ):
        raise ValidationError(f"{context}: '{key}' must contain only numeric values.")
    return list(value)


def validate_project_payload(payload: JsonDict) -> JsonDict:
    project_name = _require_str(payload, "project_name", "project")
    platform = _require_str(payload, "platform", "project").lower()
    if platform not in ALLOWED_PLATFORMS:
        raise ValidationError(
            f"project: 'platform' must be one of {sorted(ALLOWED_PLATFORMS)}."
        )

    screens = _require_list(payload, "screens", "project")
    if not screens:
        raise ValidationError("project: 'screens' must contain at least one screen.")

    validated_screens: list[JsonDict] = []
    seen_screen_ids: set[str] = set()
    for screen_index, screen in enumerate(screens):
        if not isinstance(screen, dict):
            raise ValidationError(f"screen[{screen_index}] must be an object.")
        screen_context = f"screen[{screen_index}]"
        screen_id = _require_str(screen, "screen_id", screen_context)
        if screen_id in seen_screen_ids:
            raise ValidationError(
                f"{screen_context}: duplicate 'screen_id' value '{screen_id}'."
            )
        seen_screen_ids.add(screen_id)
        screen_name = _require_str(screen, "screen_name", screen_context)
        elements = _require_list(screen, "elements", screen_context)
        if not elements:
            raise ValidationError(
                f"{screen_context}: 'elements' must contain at least one node."
            )

        validated_elements: list[JsonDict] = []
        seen_element_ids: set[str] = set()
        for element_index, element in enumerate(elements):
            if not isinstance(element, dict):
                raise ValidationError(
                    f"{screen_context}.element[{element_index}] must be an object."
                )
            element_context = f"{screen_context}.element[{element_index}]"
            element_id = _require_str(element, "element_id", element_context)
            if element_id in seen_element_ids:
                raise ValidationError(
                    f"{element_context}: duplicate 'element_id' value '{element_id}'."
                )
            seen_element_ids.add(element_id)
            validated_elements.append(
                {
                    "element_id": element_id,
                    "parent_id": _require_optional_str(
                        element, "parent_id", element_context
                    ),
                    "element_type": _require_str(
                        element, "element_type", element_context
                    ),
                    "role": _require_str(element, "role", element_context),
                    "slab_layer": _require_optional_slab_layer(
                        element, "slab_layer", element_context
                    ),
                    "label": _require_label(element, "label", element_context),
                    "accessibility_identifier": _require_optional_str(
                        element, "accessibility_identifier", element_context
                    ),
                    "interactive": _require_bool(
                        element, "interactive", element_context
                    ),
                    "visible": _require_bool(element, "visible", element_context),
                    "bounds": _require_bounds(element, "bounds", element_context),
                    "hierarchy_depth": _require_non_negative_int(
                        element, "hierarchy_depth", element_context
                    ),
                    "child_count": _require_non_negative_int(
                        element, "child_count", element_context
                    ),
                    "text_present": _require_bool(
                        element, "text_present", element_context
                    ),
                    "traits": _require_str_list(element, "traits", element_context),
                    "source": _require_str(element, "source", element_context),
                }
            )

        element_id_set = {str(element["element_id"]) for element in validated_elements}
        for element_index, element in enumerate(validated_elements):
            parent_id = element["parent_id"]
            element_id = element["element_id"]
            if parent_id is not None and parent_id == element_id:
                raise ValidationError(
                    f"{screen_context}.element[{element_index}]: 'parent_id' must "
                    "reference a different element in the same screen."
                )
            if parent_id is not None and parent_id not in element_id_set:
                raise ValidationError(
                    (
                        f"{screen_context}.element[{element_index}]: 'parent_id' "
                        f"references unknown element '{parent_id}'."
                    )
                )

        validated_screens.append(
            {
                "screen_id": screen_id,
                "screen_name": screen_name,
                "elements": validated_elements,
            }
        )

    return {
        "project_name": project_name,
        "platform": platform,
        "screens": validated_screens,
    }
