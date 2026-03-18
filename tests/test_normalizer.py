from __future__ import annotations

from src.core.normalizer import normalize_project
from src.core.schemas import validate_project_payload

from tests.helpers import load_fixture


def test_normalizer_produces_stable_project_shape():
    project = normalize_project(
        validate_project_payload(load_fixture()), "com.example.legacyapp"
    )

    assert project["app_id"] == "com.example.legacyapp"
    assert project["project_name"] == "Legacy Repair App"
    assert project["platform"] == "ios"
    assert len(project["screens"]) == 2
    assert len(project["nodes"]) == 10
    assert project["nodes"][0]["slab_layer"] == "foundation"
    assert project["nodes"][3]["slab_layer"] == "systems"
