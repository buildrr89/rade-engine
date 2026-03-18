from __future__ import annotations

from src.core.deduplicator import deduplicate_nodes
from src.core.normalizer import normalize_project
from src.core.recommendation_engine import build_recommendations
from src.core.roadmap_generator import build_roadmap
from src.core.schemas import validate_project_payload

from tests.helpers import load_fixture


def test_roadmap_orders_by_priority_then_category():
    project = normalize_project(
        validate_project_payload(load_fixture()), "com.example.legacyapp"
    )
    clusters = deduplicate_nodes(project["nodes"])
    recommendations = build_recommendations(project, clusters)
    roadmap = build_roadmap(recommendations)

    assert [item["step"] for item in roadmap] == [1, 2, 3]
    assert roadmap[0]["category"] == "accessibility"
    assert roadmap[1]["category"] == "migration_sequencing"
