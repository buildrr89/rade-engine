from __future__ import annotations

from typing import Any

JsonDict = dict[str, Any]
PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2}


def build_roadmap(recommendations: list[JsonDict]) -> list[JsonDict]:
    ordered = sorted(
        recommendations,
        key=lambda item: (
            PRIORITY_ORDER.get(item["priority"], 99),
            item["category"],
            item["recommendation_id"],
        ),
    )
    roadmap: list[JsonDict] = []
    for index, recommendation in enumerate(ordered, start=1):
        roadmap.append(
            {
                "step": index,
                "title": recommendation["recommended_change"],
                "why_now": recommendation["problem_statement"],
                "category": recommendation["category"],
                "priority": recommendation["priority"],
                "implementation_effort": recommendation["implementation_effort"],
                "affected_screens": recommendation["affected_screens"],
            }
        )
    return roadmap
