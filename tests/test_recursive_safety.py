# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import logging

from src.engine.rade_orchestrator import RadeOrchestrator


class FakeNode:
    def __init__(
        self,
        element_type: str,
        *,
        label: str = "",
        accessibility_identifier: str | None = None,
        traits: list[str] | None = None,
        bounds: dict[str, int] | None = None,
        visible: bool = True,
        enabled: bool = True,
        children: list["FakeNode"] | None = None,
    ) -> None:
        self.element_type = element_type
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
            "label": self.label,
            "text": self.label,
            "name": self.label,
            "value": self.label,
            "title": self.label,
            "accessibility_identifier": self.accessibility_identifier,
            "accessibilityIdentifier": self.accessibility_identifier,
            "identifier": self.accessibility_identifier,
            "traits": self.traits,
            "accessibilityTraits": self.traits,
            "bounds": self.bounds,
            "rect": self.bounds,
            "frame": self.bounds,
            "visible": self.visible,
            "displayed": self.visible,
            "enabled": self.enabled,
            "clickable": self.enabled,
        }
        return mapping.get(name)


def test_collect_from_root_breaks_circular_reference() -> None:
    root = FakeNode(
        "XCUIElementTypeWindow",
        bounds={"x": 0, "y": 0, "width": 390, "height": 844},
    )
    scroll = FakeNode(
        "XCUIElementTypeScrollView",
        bounds={"x": 0, "y": 88, "width": 390, "height": 756},
    )
    button = FakeNode(
        "XCUIElementTypeButton",
        label="Continue",
        traits=["Button"],
        bounds={"x": 16, "y": 120, "width": 358, "height": 44},
    )
    scroll.children = [button, root]
    root.children = [scroll]

    orchestrator = RadeOrchestrator(
        app_id="com.example.legacyapp",
        platform="ios",
    )
    graph = orchestrator.collect_from_root(
        root,
        screen_id="home",
        screen_name="Home",
    )

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert [node.element_type for node in graph.nodes] == [
        "XCUIElementTypeWindow",
        "XCUIElementTypeScrollView",
        "XCUIElementTypeButton",
    ]


def test_collect_from_root_warns_and_preserves_partial_graph_at_max_depth() -> None:
    tail = FakeNode(
        "XCUIElementTypeStaticText",
        label="Leaf",
        bounds={"x": 0, "y": 60, "width": 200, "height": 20},
    )
    mid = FakeNode(
        "XCUIElementTypeStaticText",
        label="Mid",
        bounds={"x": 0, "y": 40, "width": 200, "height": 20},
        children=[tail],
    )
    top = FakeNode(
        "XCUIElementTypeStaticText",
        label="Top",
        bounds={"x": 0, "y": 20, "width": 200, "height": 20},
        children=[mid],
    )
    root = FakeNode(
        "XCUIElementTypeWindow",
        bounds={"x": 0, "y": 0, "width": 390, "height": 844},
        children=[top],
    )

    orchestrator = RadeOrchestrator(
        app_id="com.example.legacyapp",
        platform="ios",
    )

    logger = logging.getLogger("src.engine.rade_orchestrator")
    records: list[str] = []

    class _CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(self.format(record))

    handler = _CaptureHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    try:
        graph = orchestrator.collect_from_root(
            root, screen_id="depth-check", max_depth=2
        )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)

    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert any("max_depth=2" in message for message in records)
    assert [node.label for node in graph.nodes] == ["", "Top", "Mid"]


def test_collect_from_root_samples_scroll_children_by_priority() -> None:
    scroll_children = [
        FakeNode(
            "XCUIElementTypeStaticText",
            label=f"Item {index}",
            bounds={"x": 0, "y": 80 + index * 20, "width": 320, "height": 20},
        )
        for index in range(8)
    ]
    semantic_children = [
        FakeNode(
            "XCUIElementTypeButton",
            label="Continue",
            traits=["Button"],
            bounds={"x": 16, "y": 40, "width": 320, "height": 44},
        ),
        FakeNode(
            "XCUIElementTypeLink",
            label="Terms",
            traits=["Link"],
            bounds={"x": 16, "y": 540, "width": 120, "height": 20},
        ),
        FakeNode(
            "XCUIElementTypeStaticText",
            label="Section Title",
            traits=["Header"],
            bounds={"x": 16, "y": 20, "width": 200, "height": 24},
        ),
    ]
    scroll = FakeNode(
        "XCUIElementTypeScrollView",
        bounds={"x": 0, "y": 88, "width": 390, "height": 756},
        children=scroll_children[:4] + semantic_children + scroll_children[4:],
    )
    root = FakeNode(
        "XCUIElementTypeWindow",
        bounds={"x": 0, "y": 0, "width": 390, "height": 844},
        children=[scroll],
    )

    orchestrator = RadeOrchestrator(
        app_id="com.example.legacyapp",
        platform="ios",
    )
    graph = orchestrator.collect_from_root(root, screen_id="feed")

    assert len(graph.nodes) == 7
    assert {node.label for node in graph.nodes} >= {
        "Continue",
        "Terms",
        "Section Title",
    }
    assert sum(node.label.startswith("Item ") for node in graph.nodes) == 2
