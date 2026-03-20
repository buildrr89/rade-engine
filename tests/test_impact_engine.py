# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from src.core.impact_engine import estimate_impact


def test_impact_engine_maps_accessibility_to_high_impact():
    impact = estimate_impact("accessibility", 2)

    assert impact["expected_impact"] == "High: removes assistive technology blockers"
    assert impact["implementation_effort"] == "S"
    assert impact["confidence"] == "high"


def test_impact_engine_maps_component_reuse_to_medium_effort():
    impact = estimate_impact("component_reuse", 3)

    assert impact["expected_impact"] == "Medium: reduces duplication and drift"
    assert impact["implementation_effort"] == "M"
