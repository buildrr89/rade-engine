# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from src.core.compliance import JSON_LEGAL_KEY, LEGAL_NOTICE
from src.core.figma_bridge_v0 import build_figma_bridge_v0_manifest
from src.engine.rade_orchestrator import RadeOrchestrator

from tests.test_rade_orchestrator import FakeNode


def test_build_figma_bridge_v0_manifest_groups_frames_and_legal() -> None:
    nodes = [
        {
            "node_ref": "s#n1",
            "slab03_frame_id": "slab03:landmark:nav:primary:deadbeef",
            "slab03_anchor_kind": "a11y:landmark",
            "functional_dna": {
                "slab03_figma_alias": "Nav_Primary",
                "slab03_landmark_kind": "nav",
                "pattern_fingerprint": "fp-aaa",
            },
        },
        {
            "node_ref": "s#n2",
            "slab03_frame_id": "slab03:landmark:nav:primary:deadbeef",
            "slab03_anchor_kind": "a11y:landmark-descendant",
            "functional_dna": {"pattern_fingerprint": "fp-bbb"},
        },
        {
            "node_ref": "s#n3",
            "functional_dna": {},
        },
    ]
    manifest = build_figma_bridge_v0_manifest(
        app_id="com.example.app",
        platform="ios",
        screen_id="home",
        screen_name="Home",
        nodes=nodes,
    )
    assert JSON_LEGAL_KEY in manifest
    assert LEGAL_NOTICE in manifest[JSON_LEGAL_KEY]["header_notice"]
    assert manifest["manifest_version"] == "0.2.2"
    assert manifest["bridge_kind"] == "rade_figma_bridge_v0"
    assert manifest["frame_count"] == 1
    assert manifest["unassigned_node_count"] == 1
    assert manifest["variant_axes"] == []
    frame0 = manifest["frames"][0]
    assert frame0["component_id"] == "slab03:landmark:nav:primary:deadbeef"
    assert frame0["figma_suggested_name"] == "Nav_Primary"
    assert frame0["member_count"] == 2
    assert set(frame0["pattern_fingerprints"]) == {"fp-aaa", "fp-bbb"}
    assert frame0["design_tokens"] == {
        "color_tokens": [],
        "typography_tokens": [],
        "spacing_tokens": [],
    }
    assert "n1" in frame0["sample_node_refs"][0]
    assert manifest["ref_map"]["wire_count"] == 0
    assert manifest["ref_map"]["wires"] == []


def test_ref_map_nav_primary_button_wires_modal_search() -> None:
    nav_fid = "slab03:landmark:nav:primary:deadbeef"
    modal_fid = "slab03:modal:search:cafebabe"
    nodes = [
        {
            "node_ref": "home#open_search",
            "slab03_frame_id": nav_fid,
            "slab03_anchor_kind": "a11y:landmark",
            "functional_dna": {
                "slab03_figma_alias": "Nav_Primary",
                "slab03_landmark_kind": "nav",
            },
        },
        {
            "node_ref": "home#modal_search_root",
            "slab03_frame_id": modal_fid,
            "slab03_anchor_kind": "a11y:dialog",
            "functional_dna": {"slab03_figma_alias": "Modal_Search"},
        },
    ]
    edges = [
        {
            "source_node_ref": "home#open_search",
            "target_node_ref": "home#modal_search_root",
            "edge_type": "triggers",
            "screen_id": "home",
            "screen_name": "Home",
            "metadata": {},
        }
    ]
    manifest = build_figma_bridge_v0_manifest(
        app_id="com.example.app",
        platform="ios",
        screen_id="home",
        screen_name="Home",
        nodes=nodes,
        edges=edges,
    )
    assert manifest["frame_count"] == 2
    wires = manifest["ref_map"]["wires"]
    assert len(wires) == 1
    w0 = wires[0]
    assert w0["source_frame_id"] == nav_fid
    assert w0["target_frame_id"] == modal_fid
    assert w0["plumbing_scope"] == "external"
    assert w0["action_type"] == "click"
    assert w0["edge_type"] == "triggers"


def test_ref_map_internal_same_frame_wire() -> None:
    fid = "slab03:landmark:main:content:111"
    nodes = [
        {
            "node_ref": "p#a",
            "slab03_frame_id": fid,
            "functional_dna": {},
        },
        {
            "node_ref": "p#b",
            "slab03_frame_id": fid,
            "functional_dna": {},
        },
    ]
    edges = [
        {
            "source_node_ref": "p#a",
            "target_node_ref": "p#b",
            "edge_type": "routes_to",
            "screen_id": "p",
            "screen_name": "P",
            "metadata": {},
        }
    ]
    manifest = build_figma_bridge_v0_manifest(
        app_id="x",
        platform="ios",
        screen_id="p",
        screen_name="P",
        nodes=nodes,
        edges=edges,
    )
    assert manifest["ref_map"]["wires"][0]["plumbing_scope"] == "internal"
    assert manifest["ref_map"]["wires"][0]["action_type"] == "navigate"


def test_ref_map_metadata_action_type_overrides_edge_mapping() -> None:
    fid = "slab03:landmark:nav:primary:x"
    nodes = [
        {"node_ref": "s#h1", "slab03_frame_id": fid, "functional_dna": {}},
        {"node_ref": "s#h2", "slab03_frame_id": fid, "functional_dna": {}},
    ]
    edges = [
        {
            "source_node_ref": "s#h1",
            "target_node_ref": "s#h2",
            "edge_type": "triggers",
            "screen_id": "s",
            "screen_name": "S",
            "metadata": {"action_type": "hover"},
        }
    ]
    manifest = build_figma_bridge_v0_manifest(
        app_id="x",
        platform="ios",
        screen_id="s",
        screen_name="S",
        nodes=nodes,
        edges=edges,
    )
    assert manifest["ref_map"]["wires"][0]["action_type"] == "hover"


def test_construction_graph_figma_manifest_after_orchestrator() -> None:
    root = FakeNode(
        "XCUIElementTypeWindow",
        children=[
            FakeNode(
                "XCUIElementTypeNavigationBar",
                bounds={"x": 0, "y": 0, "width": 300, "height": 44},
                label="Main",
            ),
            FakeNode(
                "XCUIElementTypeLink",
                label="Docs",
                bounds={"x": 10, "y": 10, "width": 40, "height": 20},
            ),
        ],
    )
    orch = RadeOrchestrator(app_id="com.example.app", platform="ios")
    graph = orch.collect_from_root(root, screen_id="docs", screen_name="Docs")
    manifest = graph.to_figma_bridge_v0_manifest()
    assert manifest["screen_id"] == "docs"
    assert manifest["frame_count"] >= 1
    assert manifest["unassigned_node_count"] >= 0
    assert isinstance(manifest["frames"], list)
    assert "ref_map" in manifest
    assert "wires" in manifest["ref_map"]
    assert isinstance(manifest["ref_map"]["wire_count"], int)


def test_build_figma_bridge_v0_manifest_aggregates_design_tokens() -> None:
    fid = "slab03:landmark:main:content:a1"
    nodes = [
        {
            "node_ref": "home#n1",
            "slab03_frame_id": fid,
            "functional_dna": {
                "design_tokens": {
                    "color_tokens": ["color:#fff", "background-color:#111"],
                    "typography_tokens": ["font-family:ibm plex sans"],
                    "spacing_tokens": ["padding:16px"],
                }
            },
        },
        {
            "node_ref": "home#n2",
            "slab03_frame_id": fid,
            "functional_dna": {
                "design_tokens": {
                    "color_tokens": ["color:#fff"],
                    "typography_tokens": ["font-weight:600"],
                    "spacing_tokens": ["margin:8px"],
                }
            },
        },
    ]
    manifest = build_figma_bridge_v0_manifest(
        app_id="x",
        platform="web",
        screen_id="home",
        screen_name="Home",
        nodes=nodes,
    )
    frame = manifest["frames"][0]
    assert frame["design_tokens"]["color_tokens"] == [
        "background-color:#111",
        "color:#fff",
    ]
    assert frame["design_tokens"]["typography_tokens"] == [
        "font-family:ibm plex sans",
        "font-weight:600",
    ]
    assert frame["design_tokens"]["spacing_tokens"] == ["margin:8px", "padding:16px"]
