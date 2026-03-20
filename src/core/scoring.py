# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from typing import Any

from .models import SCORING_MODEL_VERSION

JsonDict = dict[str, Any]


def clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def score_project(project: JsonDict, clusters: list[JsonDict]) -> dict[str, JsonDict]:
    nodes = project["nodes"]
    screen_count = len(project["screens"])
    total_nodes = len(nodes)
    interactive_nodes = sum(1 for node in nodes if node.get("interactive"))
    duplicate_nodes = sum(
        cluster["count"] - 1 for cluster in clusters if cluster["count"] > 1
    )
    duplicate_clusters = sum(1 for cluster in clusters if cluster["count"] > 1)
    missing_accessibility_ids = sum(
        1
        for node in nodes
        if node.get("interactive") and not node.get("accessibility_identifier")
    )
    missing_labels = sum(
        1
        for node in nodes
        if node.get("interactive") and not str(node.get("label", "")).strip()
    )

    complexity = clamp(10 + screen_count * 8 + total_nodes * 2 + interactive_nodes * 3)
    reusability = clamp(
        30 + duplicate_nodes * 10 + duplicate_clusters * 5 - screen_count * 2
    )
    accessibility_risk = clamp(missing_accessibility_ids * 35 + missing_labels * 10)
    migration_risk = clamp(
        (accessibility_risk + duplicate_clusters * 10 + interactive_nodes * 2) // 2
    )

    return {
        "complexity": {
            "value": complexity,
            "version": SCORING_MODEL_VERSION,
            "evidence": [
                f"{screen_count} screens",
                f"{total_nodes} nodes",
                f"{interactive_nodes} interactive nodes",
            ],
        },
        "reusability": {
            "value": reusability,
            "version": SCORING_MODEL_VERSION,
            "evidence": [
                f"{duplicate_clusters} duplicate clusters",
                f"{duplicate_nodes} duplicated nodes",
            ],
        },
        "accessibility_risk": {
            "value": accessibility_risk,
            "version": SCORING_MODEL_VERSION,
            "evidence": [
                f"{missing_accessibility_ids} interactive nodes without accessibility identifiers",
                f"{missing_labels} interactive nodes without labels",
            ],
        },
        "migration_risk": {
            "value": migration_risk,
            "version": SCORING_MODEL_VERSION,
            "evidence": [
                f"{accessibility_risk} accessibility risk",
                f"{duplicate_clusters} duplicate clusters",
            ],
        },
    }
