from __future__ import annotations

from copy import deepcopy

from ..core.models import DEFAULT_STANDARDS_PACK_VERSION

STANDARDS_PACK = {
    "version": DEFAULT_STANDARDS_PACK_VERSION,
    "refs": [
        {
            "name": "Apple Human Interface Guidelines",
            "url": "https://developer.apple.com/design/human-interface-guidelines/",
        },
        {
            "name": "Apple iOS design guidance",
            "url": "https://developer.apple.com/design/human-interface-guidelines/designing-for-ios",
        },
        {
            "name": "Android Material 3 guidance",
            "url": "https://developer.android.com/develop/ui/compose/designsystems/material3",
        },
        {
            "name": "Android accessibility guidance",
            "url": "https://developer.android.com/develop/ui/compose/accessibility",
        },
        {
            "name": "Android semantics guidance",
            "url": "https://developer.android.com/develop/ui/compose/accessibility/semantics",
        },
        {
            "name": "WCAG 2.2",
            "url": "https://www.w3.org/TR/WCAG22/",
        },
    ],
}

CATEGORY_REFERENCES = {
    "accessibility": [
        "WCAG 2.2 4.1.2 Name, Role, Value",
        "Apple HIG: accessibility and clarity",
    ],
    "component_reuse": [
        "Apple HIG: consistency",
        "Material 3: reusable component patterns",
    ],
    "migration_sequencing": [
        "WCAG 2.2: accessibility first",
        "Apple HIG: system consistency",
    ],
    "layout": [
        "Apple HIG: layout clarity",
    ],
    "navigation": [
        "Material 3: navigation clarity",
    ],
}


def load_standards_pack() -> dict:
    return deepcopy(STANDARDS_PACK)


def references_for(category: str) -> list[str]:
    return list(CATEGORY_REFERENCES.get(category, ["Apple HIG", "WCAG 2.2"]))
