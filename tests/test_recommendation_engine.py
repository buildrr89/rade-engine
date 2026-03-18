from __future__ import annotations

from src.core.deduplicator import deduplicate_nodes
from src.core.normalizer import normalize_project
from src.core.recommendation_engine import build_recommendations
from src.core.schemas import validate_project_payload

from tests.helpers import load_fixture


def test_recommendation_engine_produces_three_standard_backed_actions():
    project = normalize_project(
        validate_project_payload(load_fixture()), "com.example.legacyapp"
    )
    clusters = deduplicate_nodes(project["nodes"])
    recommendations = build_recommendations(project, clusters)

    assert [rec["category"] for rec in recommendations] == [
        "accessibility",
        "migration_sequencing",
        "component_reuse",
    ]
    assert [rec["rule_id"] for rec in recommendations] == [
        "accessibility_missing_identifier",
        "migration_sequence_accessibility_before_reuse",
        "component_reuse_interactive_cluster",
    ]
    assert all(rec["provenance"] == "standards" for rec in recommendations)
    assert all(not rec["benchmark_refs"] for rec in recommendations)
    assert recommendations[0]["recommendation_id"].startswith(
        "rec-accessibility_missing_identifier-"
    )
    assert recommendations[0]["evidence"] == [
        "project-overview#primary-cta",
        "analysis-review#primary-cta",
    ]
