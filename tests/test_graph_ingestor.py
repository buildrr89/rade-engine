# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import patch

from src.core.layering import CONTAINERS_LAYER, OS_SITE_LAYER
from src.database.graph_ingestor import Neo4jAuraConfig, RadeGraphIngestor
from src.engine.rade_orchestrator import (
    ConstructionGraph,
    FunctionalEdge,
    FunctionalNode,
)


@dataclass
class FakeResult:
    query: str
    parameters: dict[str, Any]

    def consume(self) -> "FakeResult":
        return self


@dataclass
class FakeSession:
    queries: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def run(self, query: str, /, **parameters: Any) -> FakeResult:
        self.queries.append((query, parameters))
        return FakeResult(query=query, parameters=parameters)

    def close(self) -> None:
        return None

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


@dataclass
class FakeDriver:
    session_obj: FakeSession = field(default_factory=FakeSession)

    def session(self, /, **parameters: Any) -> FakeSession:
        self.session_parameters = parameters
        return self.session_obj

    def close(self) -> None:
        return None


def _component(
    node_ref: str,
    *,
    element_id: str,
    parent_id: str | None,
    label: str,
    hierarchy_depth: int,
    traits: list[str],
) -> FunctionalNode:
    functional_dna = {
        "node_ref": node_ref,
        "path": "0.1",
        "role": "button",
        "element_type": "XCUIElementTypeButton",
        "label": label,
        "accessibility_identifier": None,
        "interactive": True,
        "visible": True,
        "bounds": [0, 0, 100, 44],
        "hierarchy_depth": hierarchy_depth,
        "child_count": 0,
        "traits": traits,
        "slab_layer": CONTAINERS_LAYER,
        "structural_fingerprint": "fingerprint-1234",
        "structural_frame": False,
        "frame_kind": None,
        "destination_kind": None,
        "destination_ref": None,
        "destination_template": None,
        "pattern_fingerprint": "pattern-1234",
    }
    return FunctionalNode(
        node_ref=node_ref,
        parent_node_ref=parent_id,
        element_id=element_id,
        parent_id=parent_id,
        screen_id="login-screen",
        screen_name="Login",
        platform="ios",
        source="accessibility_tree",
        element_type="XCUIElementTypeButton",
        role="button",
        label=label,
        accessibility_identifier=None,
        interactive=True,
        visible=True,
        bounds=[0, 0, 100, 44],
        hierarchy_depth=hierarchy_depth,
        child_count=0,
        text_present=True,
        traits=traits,
        slab_layer=CONTAINERS_LAYER,
        structural_fingerprint="fingerprint-1234",
        functional_dna=functional_dna,
    )


def _graph() -> ConstructionGraph:
    root = FunctionalNode(
        node_ref="login-screen#root",
        parent_node_ref=None,
        element_id="root",
        parent_id=None,
        screen_id="login-screen",
        screen_name="Login",
        platform="ios",
        source="accessibility_tree",
        element_type="XCUIElementTypeWindow",
        role="screen",
        label="Login",
        accessibility_identifier=None,
        interactive=False,
        visible=True,
        bounds=[0, 0, 390, 844],
        hierarchy_depth=0,
        child_count=2,
        text_present=True,
        traits=["window"],
        slab_layer=OS_SITE_LAYER,
        structural_fingerprint="screen-0001",
        functional_dna={
            "node_ref": "login-screen#root",
            "path": "0",
            "role": "screen",
            "element_type": "XCUIElementTypeWindow",
            "label": "Login",
            "accessibility_identifier": None,
            "interactive": False,
            "visible": True,
            "bounds": [0, 0, 390, 844],
            "hierarchy_depth": 0,
            "child_count": 2,
            "traits": ["window"],
            "slab_layer": OS_SITE_LAYER,
            "structural_fingerprint": "screen-0001",
            "structural_frame": False,
            "frame_kind": None,
            "destination_kind": None,
            "destination_ref": None,
            "destination_template": None,
            "pattern_fingerprint": "pattern-root",
        },
    )
    first = _component(
        "login-screen#continue-1",
        element_id="continue-1",
        parent_id=root.node_ref,
        label="Continue",
        hierarchy_depth=1,
        traits=["button"],
    )
    second = _component(
        "login-screen#continue-2",
        element_id="continue-2",
        parent_id=root.node_ref,
        label="Continue",
        hierarchy_depth=1,
        traits=["button"],
    )
    first.functional_dna["destination_kind"] = "route"
    first.functional_dna["destination_ref"] = "/dashboard"
    first.functional_dna["destination_template"] = "/dashboard"
    second.functional_dna["destination_kind"] = "route"
    second.functional_dna["destination_ref"] = "/dashboard"
    second.functional_dna["destination_template"] = "/dashboard"
    return ConstructionGraph(
        app_id="com.example.legacyapp",
        platform="ios",
        screen_id="login-screen",
        screen_name="Login",
        capture_source="accessibility_tree",
        nodes=[root, first, second],
        edges=[
            FunctionalEdge(
                source_node_ref=root.node_ref,
                target_node_ref=first.node_ref,
                edge_type="contains",
                screen_id="login-screen",
                screen_name="Login",
            ),
            FunctionalEdge(
                source_node_ref=root.node_ref,
                target_node_ref=second.node_ref,
                edge_type="contains",
                screen_id="login-screen",
                screen_name="Login",
            ),
            FunctionalEdge(
                source_node_ref=first.node_ref,
                target_node_ref="login-screen#destination-dashboard",
                edge_type="routes_to",
                screen_id="login-screen",
                screen_name="Login",
                metadata={
                    "destination_kind": "route",
                    "destination_ref": "/dashboard",
                    "destination_template": "/dashboard",
                },
            ),
        ],
        metadata={"project_name": "Login", "captured_at": "2026-03-21T00:00:00Z"},
    )


def test_graph_ingestor_scrubs_before_write_and_deduplicates_patterns() -> None:
    captured: dict[str, Any] = {"calls": 0}

    def fake_scrub(payload: Any) -> tuple[Any, dict[str, Any]]:
        captured["calls"] += 1
        assert isinstance(payload, dict)
        scrubbed = {
            "app_id": payload["app_id"],
            "platform": payload["platform"],
            "screen_id": payload["screen_id"],
            "screen_name": payload["screen_name"],
            "capture_source": payload["capture_source"],
            "metadata": payload["metadata"],
            "nodes": payload["nodes"],
            "edges": payload["edges"],
        }
        return scrubbed, {"total_redactions": 0, "events": [], "is_scrubbed": True}

    with patch("src.database.graph_ingestor.scrub_payload_with_metadata", fake_scrub):
        driver = FakeDriver()
        ingestor = RadeGraphIngestor(
            driver=driver,
            connection=Neo4jAuraConfig(
                uri="neo4j+s://example.databases.neo4j.io",
                username="neo4j",
                password="secret",
            ),
        )

        summary = ingestor.ingest_screen(_graph())

    assert captured["calls"] == 1
    assert summary["screen_id"] == "login-screen"
    assert summary["component_count"] == 3
    assert summary["trait_count"] == 3
    assert summary["pattern_count"] == 2
    assert summary["edge_count"] == 3
    assert summary["plumbing_edge_count"] == 1
    assert len(summary["pattern_ids"]) == 2

    session_queries = driver.session_obj.queries
    assert len(session_queries) == 10
    screen_query, screen_params = next(
        item for item in session_queries if item[0].startswith("MERGE (screen:Screen")
    )
    assert screen_params["screen_id"] == "login-screen"

    component_query, component_params = next(
        item for item in session_queries if item[0].startswith("MATCH (screen:Screen")
    )
    components = component_params["components"]
    assert len(components) == 3
    pattern_ids = {component["pattern_id"] for component in components}
    assert len(pattern_ids) == 2
    assert all(component["pattern_dna_json"] for component in components)
    assert any(
        '"destination_kind":"route"' in component["functional_dna_json"]
        for component in components
    )
    assert any("PLUMBED_TO" in query for query, _ in session_queries)


def test_pattern_lookup_query_targets_pattern_id() -> None:
    query = RadeGraphIngestor.build_pattern_lookup_query()

    assert "MATCH (pattern:UIPattern {pattern_id: $pattern_id})" in query
    assert "pattern.pattern_dna_json AS pattern_dna_json" in query


def test_graph_ingestor_aborts_when_edge_shield_metadata_flags_unscrubbed() -> None:
    def fake_scrub(payload: Any) -> tuple[Any, dict[str, Any]]:
        return payload, {"total_redactions": 0, "events": [], "is_scrubbed": False}

    with patch("src.database.graph_ingestor.scrub_payload_with_metadata", fake_scrub):
        driver = FakeDriver()
        ingestor = RadeGraphIngestor(
            driver=driver,
            connection=Neo4jAuraConfig(
                uri="neo4j+s://example.databases.neo4j.io",
                username="neo4j",
                password="secret",
            ),
        )

        try:
            ingestor.ingest_screen(_graph())
        except RuntimeError as exc:
            assert "is_scrubbed=False" in str(exc)
        else:
            raise AssertionError(
                "ingest_screen should abort when edge_shield flags unsafe payloads"
            )

        assert driver.session_obj.queries == []
