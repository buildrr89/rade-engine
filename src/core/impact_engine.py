# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from typing import Any

JsonDict = dict[str, Any]

IMPACT_BY_CATEGORY = {
    "accessibility": ("High: removes assistive technology blockers", "S"),
    "component_reuse": ("Medium: reduces duplication and drift", "M"),
    "design_system_consistency": ("Medium: reduces inconsistency risk", "M"),
    "migration_sequencing": ("High: reduces future rework risk", "S"),
    "layout": ("Medium: improves flow clarity", "M"),
    "navigation": ("High: lowers navigation friction", "M"),
    "interaction": ("Medium: simplifies interactions", "M"),
    "content_hierarchy": ("Medium: clarifies information order", "M"),
}


def estimate_impact(
    category: str, evidence_count: int, confidence: str = "high"
) -> JsonDict:
    expected_impact, effort = IMPACT_BY_CATEGORY.get(
        category, ("Medium: localized improvement", "M")
    )
    if evidence_count > 2 and effort == "S":
        effort = "M"
    if evidence_count > 4:
        confidence = "medium"
    return {
        "expected_impact": expected_impact,
        "implementation_effort": effort,
        "confidence": confidence,
    }
