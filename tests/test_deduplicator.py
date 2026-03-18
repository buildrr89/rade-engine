from __future__ import annotations

from src.core.deduplicator import deduplicate_nodes
from src.core.normalizer import normalize_project
from src.core.schemas import validate_project_payload

from tests.helpers import load_fixture


def test_deduplicator_groups_repeated_structure():
    project = normalize_project(
        validate_project_payload(load_fixture()), "com.example.legacyapp"
    )
    clusters = deduplicate_nodes(project["nodes"])

    duplicate_clusters = [cluster for cluster in clusters if cluster["count"] > 1]
    assert len(duplicate_clusters) == 4
    assert duplicate_clusters[0]["count"] == 2
    assert any(cluster["interactive"] for cluster in duplicate_clusters)
