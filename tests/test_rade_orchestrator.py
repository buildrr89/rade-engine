# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from src.core.compliance import TERMINAL_NOTICE
from src.core.layering import CONTAINERS_LAYER, OS_SITE_LAYER
from src.engine.rade_orchestrator import RadeOrchestrator, main


class FakeNode:
    def __init__(
        self,
        element_type: str,
        *,
        role: str | None = None,
        label: str = "",
        accessibility_identifier: str | None = None,
        traits: list[str] | None = None,
        bounds: dict[str, int] | None = None,
        visible: bool = True,
        enabled: bool = True,
        children: list["FakeNode"] | None = None,
    ) -> None:
        self.element_type = element_type
        self.role = role
        self.label = label
        self.accessibility_identifier = accessibility_identifier
        self.traits = traits or []
        self.bounds = bounds or {"x": 0, "y": 0, "width": 0, "height": 0}
        self.visible = visible
        self.enabled = enabled
        self.children = children or []

    def get_attribute(self, name: str):
        mapping = {
            "element_type": self.element_type,
            "elementType": self.element_type,
            "class_name": self.element_type,
            "className": self.element_type,
            "type": self.element_type,
            "role": self.role,
            "accessibility_role": self.role,
            "accessibilityRole": self.role,
            "label": self.label,
            "text": self.label,
            "name": self.label,
            "accessibility_identifier": self.accessibility_identifier,
            "accessibilityIdentifier": self.accessibility_identifier,
            "identifier": self.accessibility_identifier,
            "traits": self.traits,
            "bounds": self.bounds,
            "rect": self.bounds,
            "visible": self.visible,
            "displayed": self.visible,
            "enabled": self.enabled,
            "clickable": self.enabled,
        }
        return mapping.get(name)


def test_orchestrator_collects_functional_graph() -> None:
    root = FakeNode(
        "XCUIElementTypeWindow",
        children=[
            FakeNode("XCUIElementTypeButton", label="Continue", traits=["button"]),
            FakeNode("XCUIElementTypeStaticText", label="Welcome back"),
        ],
    )

    orchestrator = RadeOrchestrator(
        app_id="com.example.legacyapp",
        platform="ios",
    )
    graph = orchestrator.collect_from_root(
        root,
        screen_id="login-screen",
        screen_name="Login",
    )

    assert graph.screen_id == "login-screen"
    assert graph.screen_name == "Login"
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2

    root_node = graph.nodes[0].to_dict()
    button_node = graph.nodes[1].to_dict()

    assert root_node["slab_layer"] == OS_SITE_LAYER
    assert button_node["role"] == "button"
    assert button_node["slab_layer"] == CONTAINERS_LAYER
    assert button_node["label"] == "Continue"
    assert button_node["node_ref"].startswith("login-screen#")

    project_payload = graph.to_project_payload()
    assert project_payload["screens"][0]["screen_id"] == "login-screen"
    assert len(project_payload["screens"][0]["elements"]) == 3


def test_orchestrator_produces_stable_node_ids_for_same_tree() -> None:
    root = FakeNode(
        "XCUIElementTypeWindow",
        children=[FakeNode("XCUIElementTypeButton", label="Submit")],
    )
    orchestrator = RadeOrchestrator(
        app_id="com.example.legacyapp",
        platform="ios",
    )

    graph_a = orchestrator.collect_from_root(root, screen_id="home")
    graph_b = orchestrator.collect_from_root(root, screen_id="home")

    assert graph_a.nodes[0].element_id == graph_b.nodes[0].element_id
    assert graph_a.nodes[1].element_id == graph_b.nodes[1].element_id


def test_orchestrator_adds_plumbing_edges_for_interactive_destinations() -> None:
    root = FakeNode(
        "XCUIElementTypeWindow",
        children=[
            FakeNode(
                "XCUIElementTypeButton",
                label="Continue",
                traits=["button"],
                accessibility_identifier="continue",
            )
        ],
    )

    original_get_attribute = root.children[0].get_attribute

    def get_attribute(name: str):
        if name == "destination":
            return "/dashboard"
        return original_get_attribute(name)

    root.children[0].get_attribute = get_attribute  # type: ignore[method-assign]

    orchestrator = RadeOrchestrator(
        app_id="com.example.legacyapp",
        platform="ios",
    )
    graph = orchestrator.collect_from_root(root, screen_id="home")

    plumbing_edges = [edge for edge in graph.edges if edge.edge_type != "contains"]

    assert len(plumbing_edges) == 1
    assert plumbing_edges[0].edge_type == "triggers"
    assert plumbing_edges[0].metadata["destination_ref"] == "/dashboard"


def test_orchestrator_main_clears_terminal_and_prints_notice() -> None:
    stdout = StringIO()

    with patch("src.core.compliance.os.system") as mocked_clear:
        with redirect_stdout(stdout):
            exit_code = main()

    mocked_clear.assert_called_once()
    assert exit_code == 0
    assert TERMINAL_NOTICE in stdout.getvalue()


def test_orchestrator_persists_modal_slab03_frame_id() -> None:
    root = FakeNode(
        "XCUIElementTypeWindow",
        children=[
            FakeNode(
                "XCUIElementTypeOther",
                role="group",
                bounds={"x": 0, "y": 0, "width": 100, "height": 100},
            ),
            FakeNode(
                "XCUIElementTypeOther",
                role="dialog",
                bounds={"x": 20, "y": 20, "width": 60, "height": 60},
                children=[
                    FakeNode(
                        "XCUIElementTypeButton",
                        label="Confirm",
                        traits=["button"],
                        bounds={"x": 30, "y": 30, "width": 20, "height": 10},
                    )
                ],
            ),
        ],
    )
    orchestrator = RadeOrchestrator(
        app_id="com.example.legacyapp",
        platform="ios",
    )
    graph = orchestrator.collect_from_root(root, screen_id="checkout")
    dialog = next(node.to_dict() for node in graph.nodes if node.role == "dialog")
    button = next(
        node.to_dict()
        for node in graph.nodes
        if node.role == "button" and node.parent_id == dialog["element_id"]
    )
    non_modal_sibling = next(
        node.to_dict()
        for node in graph.nodes
        if node.role not in {"screen", "dialog", "button"}
    )

    assert dialog["slab03_frame_id"] is not None
    assert dialog["slab03_frame_id"].startswith("slab03:modal:")
    assert dialog["slab03_anchor_kind"] == "a11y:dialog"
    assert button["slab03_frame_id"] == dialog["slab03_frame_id"]
    assert button["slab03_anchor_kind"] == "a11y:dialog-descendant"
    assert button["functional_dna"]["slab03_frame_id"] == dialog["slab03_frame_id"]
    assert (
        button["functional_dna"]["slab03_anchor_kind"] == "a11y:dialog-descendant"
    )
    assert non_modal_sibling["slab03_frame_id"] is None


def test_orchestrator_collects_token_pulse_design_metadata() -> None:
    root = FakeNode(
        "XCUIElementTypeWindow",
        children=[
            FakeNode(
                "XCUIElementTypeButton",
                label="Styled",
                traits=["button"],
            )
        ],
    )
    original_get_attribute = root.children[0].get_attribute

    def get_attribute(name: str):
        if name == "style":
            return (
                "color: #ffffff; background-color: #111111; "
                "font-family: IBM Plex Sans; font-weight: 600; padding: 16px;"
            )
        return original_get_attribute(name)

    root.children[0].get_attribute = get_attribute  # type: ignore[method-assign]
    orchestrator = RadeOrchestrator(
        app_id="com.example.legacyapp",
        platform="ios",
    )
    graph = orchestrator.collect_from_root(root, screen_id="styled")
    styled = graph.nodes[1].to_dict()["functional_dna"]

    assert "token_pulse_id" in styled
    assert styled["design_tokens"]["color_tokens"] == [
        "background-color:#111111",
        "color:#ffffff",
    ]
    assert styled["design_tokens"]["typography_tokens"] == [
        "font-family:ibm plex sans",
        "font-weight:600",
    ]
    assert styled["design_tokens"]["spacing_tokens"] == ["padding:16px"]
