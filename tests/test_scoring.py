from __future__ import annotations

from src.core.deduplicator import deduplicate_nodes
from src.core.normalizer import normalize_project
from src.core.schemas import validate_project_payload
from src.core.scoring import score_project

from tests.helpers import load_fixture


def test_scoring_is_deterministic_and_evidence_backed():
    project = normalize_project(
        validate_project_payload(load_fixture()), "com.example.legacyapp"
    )
    clusters = deduplicate_nodes(project["nodes"])
    scores = score_project(project, clusters)

    assert scores["complexity"]["value"] == 58
    assert scores["reusability"]["value"] == 86
    assert scores["accessibility_risk"]["value"] == 70
    assert scores["migration_risk"]["value"] == 59
    assert scores["complexity"]["evidence"] == [
        "2 screens",
        "10 nodes",
        "4 interactive nodes",
    ]
