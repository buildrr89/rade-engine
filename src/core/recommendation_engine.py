# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from typing import Any

from ..connectors.standards_pack import references_for
from .impact_engine import estimate_impact
from .models import (
    RECOMMENDATION_CATEGORIES,
    build_node_ref_from_node,
    stable_digest,
)

JsonDict = dict[str, Any]

PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2}


def _build_recommendation(
    *,
    rule_id: str,
    category: str,
    scope: str,
    target: str,
    priority: str,
    problem_statement: str,
    recommended_change: str,
    reasoning: str,
    evidence: list[str],
    affected_screens: list[str],
    affected_components: list[str],
    standards_refs: list[str] | None = None,
    benchmark_refs: list[str] | None = None,
    identity_parts: list[str] | None = None,
) -> JsonDict:
    impact = estimate_impact(category, len(evidence))
    standards_refs = standards_refs or references_for(category)
    benchmark_refs = benchmark_refs or []
    identity_parts = identity_parts or []
    provenance = "standards"
    if benchmark_refs and standards_refs:
        provenance = "standards + benchmark"
    elif benchmark_refs:
        provenance = "benchmark"

    return {
        "recommendation_id": (
            f"rec-{rule_id}-{stable_digest(rule_id, target, *identity_parts)}"
        ),
        "rule_id": rule_id,
        "category": category,
        "scope": scope,
        "target": target,
        "priority": priority,
        "confidence": impact["confidence"],
        "problem_statement": problem_statement,
        "recommended_change": recommended_change,
        "reasoning": reasoning,
        "evidence": evidence,
        "standards_refs": standards_refs,
        "benchmark_refs": benchmark_refs,
        "expected_impact": impact["expected_impact"],
        "implementation_effort": impact["implementation_effort"],
        "affected_screens": affected_screens,
        "affected_components": affected_components,
        "provenance": provenance,
    }


def build_recommendations(
    project: JsonDict, clusters: list[JsonDict]
) -> list[JsonDict]:
    recommendations: list[JsonDict] = []

    missing_accessibility_nodes = [
        node
        for node in project["nodes"]
        if node.get("interactive") and not node.get("accessibility_identifier")
    ]
    if missing_accessibility_nodes:
        node_refs = [
            build_node_ref_from_node(node) for node in missing_accessibility_nodes
        ]
        screen_ids = sorted(
            {str(node["screen_id"]) for node in missing_accessibility_nodes}
        )
        recommendations.append(
            _build_recommendation(
                rule_id="accessibility_missing_identifier",
                category="accessibility",
                scope="project",
                target="interactive_nodes_without_accessibility_identifier",
                priority="P1",
                problem_statement=f"{len(missing_accessibility_nodes)} interactive nodes are missing accessibility identifiers.",
                recommended_change="Add stable accessibility identifiers and preserve the accessible name, role, and value for each interactive node.",
                reasoning="Interactive controls without identifiers are harder to test, verify, and support for assistive technologies.",
                evidence=node_refs,
                affected_screens=screen_ids,
                affected_components=node_refs,
                identity_parts=node_refs,
            )
        )

    interactive_clusters = [
        cluster
        for cluster in clusters
        if cluster["count"] > 1 and cluster["interactive"]
    ]
    if interactive_clusters:
        cluster = interactive_clusters[0]
        representative = cluster["representative"]
        recommendations.append(
            _build_recommendation(
                rule_id="component_reuse_interactive_cluster",
                category="component_reuse",
                scope="component",
                target=str(representative["element_type"]),
                priority="P2",
                problem_statement=(
                    f"Repeated interactive structure appears {cluster['count']} times across {len(cluster['screen_ids'])} screens."
                ),
                recommended_change="Extract the repeated control into one reusable component and reuse it across screens.",
                reasoning="Copy-pasted interactive structure increases drift and makes future changes more expensive.",
                evidence=[
                    f"cluster_fingerprint={cluster['fingerprint']}",
                    f"screen_ids={','.join(cluster['screen_ids'])}",
                    f"node_refs={','.join(cluster['node_refs'])}",
                ],
                affected_screens=cluster["screen_ids"],
                affected_components=[cluster["fingerprint"]],
                identity_parts=[
                    cluster["fingerprint"],
                    str(representative["element_type"]),
                    *cluster["screen_ids"],
                ],
            )
        )

    if missing_accessibility_nodes and interactive_clusters:
        first_cluster = interactive_clusters[0]
        missing_node_refs = [
            build_node_ref_from_node(node) for node in missing_accessibility_nodes
        ]
        recommendations.append(
            _build_recommendation(
                rule_id="migration_sequence_accessibility_before_reuse",
                category="migration_sequencing",
                scope="project",
                target="accessibility-before-reuse",
                priority="P1",
                problem_statement="Fix accessibility on the repeated primary action before expanding reuse or visual refinement.",
                recommended_change="Address the missing accessibility identifiers first, then extract and standardize the repeated control.",
                reasoning="Accessibility fixes reduce user-facing risk faster than structure-only cleanup and make reuse safer.",
                evidence=[
                    f"missing_accessibility_node_refs={','.join(missing_node_refs)}",
                    (
                        "repeated_interactive_cluster_fingerprint="
                        f"{first_cluster['fingerprint']}"
                    ),
                    (
                        "primary_reuse_target="
                        f"{first_cluster['representative_node_ref']}"
                    ),
                ],
                affected_screens=sorted(
                    {str(node["screen_id"]) for node in missing_accessibility_nodes}
                    | set(str(screen_id) for screen_id in first_cluster["screen_ids"])
                ),
                affected_components=[first_cluster["representative_node_ref"]],
                identity_parts=[
                    *missing_node_refs,
                    first_cluster["fingerprint"],
                    first_cluster["representative_node_ref"],
                ],
            )
        )

    priority_rank = {
        key: index
        for index, key in enumerate(sorted(PRIORITY_ORDER, key=PRIORITY_ORDER.get))
    }
    category_rank = {
        category: index for index, category in enumerate(RECOMMENDATION_CATEGORIES)
    }
    recommendations.sort(
        key=lambda item: (
            priority_rank.get(item["priority"], 99),
            category_rank.get(item["category"], 99),
            item["recommendation_id"],
        )
    )
    return recommendations
