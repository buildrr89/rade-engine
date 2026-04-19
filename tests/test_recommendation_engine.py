# SPDX-License-Identifier: AGPL-3.0-only
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
    assert [rec["recommendation_id"] for rec in recommendations] == [
        "rec-accessibility_missing_identifier-8c7b61bc",
        "rec-migration_sequence_accessibility_before_reuse-536109ca",
        "rec-component_reuse_interactive_cluster-df13c83b",
    ]
    assert [rec["evidence"] for rec in recommendations] == [
        [
            "project-overview#primary-cta",
            "analysis-review#primary-cta",
        ],
        [
            "missing_accessibility_node_refs=project-overview#primary-cta,analysis-review#primary-cta",
            "repeated_interactive_cluster_fingerprint=25610e7cc32de585",
            "primary_reuse_target=project-overview#primary-cta",
        ],
        [
            "cluster_fingerprint=25610e7cc32de585",
            "screen_ids=analysis-review,project-overview",
            "node_refs=project-overview#primary-cta,analysis-review#primary-cta",
        ],
    ]
