# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from urllib.parse import urlparse

from ..core.compliance import clear_terminal, emit_terminal_banner
from ..core.fingerprint import fingerprint_node
from ..core.layering import ASSETS_LAYER, layer_element
from ..core.models import build_node_ref, stable_digest
from ..core.slab03_hybrid_anchor import apply_slab03_hybrid_pulse

JsonDict = dict[str, Any]


def _bounding_box_from_bounds(bounds: list[int] | None) -> JsonDict | None:
    """Named rectangle for exporters (derived from ``bounds`` when present)."""
    if bounds is None or len(bounds) != 4:
        return None
    try:
        x, y, w, h = (int(bounds[i]) for i in range(4))
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return {"x": x, "y": y, "width": w, "height": h}


logger = logging.getLogger(__name__)
LIST_CHILD_SAMPLE_LIMIT = 5
_TOKEN_ATTRS_COLOR = ("color", "background_color", "backgroundColor")
_TOKEN_ATTRS_TYPO = ("font_family", "fontFamily", "font_weight", "fontWeight")
_TOKEN_ATTRS_SPACING = ("margin", "padding", "gap")

_RGB_RE = re.compile(
    r"rgba?\(\s*(?P<r>\d{1,3})\s*,\s*(?P<g>\d{1,3})\s*,\s*(?P<b>\d{1,3})"
    r"(?:\s*,\s*(?P<a>[0-9.]+))?\s*\)",
    flags=re.IGNORECASE,
)


def _normalize_color_value(value: str) -> str:
    """
    Normalize color tokens into deterministic string form.

    - Converts `rgb(r,g,b)` / `rgba(r,g,b,a)` into `#rrggbb` (alpha ignored)
    - Lowercases remaining values (e.g. `#fff`, `transparent`, `hsl(...)`)
    """
    v = value.strip().lower()
    if not v:
        return v
    match = _RGB_RE.fullmatch(v)
    if not match:
        return v
    r = min(max(int(match.group("r")), 0), 255)
    g = min(max(int(match.group("g")), 0), 255)
    b = min(max(int(match.group("b")), 0), 255)
    return f"#{r:02x}{g:02x}{b:02x}"


PRIORITY_TRAIT_TOKENS = {
    "button": 100,
    "link": 95,
    "header": 92,
    "heading": 92,
    "title": 90,
    "input": 85,
    "text_field": 85,
    "textfield": 85,
    "toggle": 80,
    "switch": 80,
    "checkbox": 80,
    "radio": 80,
    "tab": 78,
    "navigation": 75,
}
STATIC_TEXT_TOKENS = ("statictext", "text", "label", "copy")
CONTAINER_TOKENS = ("list", "scroll", "table", "collection", "grid")
STRUCTURAL_FRAME_TOKENS = (
    "grid",
    "row",
    "column",
    "sidebar",
    "rail",
    "list",
    "navigation",
    "header",
    "footer",
    "main",
    "aside",
    "section",
    "form",
    "dialog",
    "container",
)


class AccessibilityElementLike(Protocol):
    """Minimal shape supported by the orchestrator."""

    children: list[Any]

    def get_attribute(self, name: str) -> Any: ...


@dataclass(frozen=True)
class AWSDeviceFarmSessionConfig:
    """Managed real-device session config for AWS Device Farm/Appium style runs."""

    provider: str = "aws-device-farm"
    platform_name: str = "ios"
    remote_url: str | None = None
    session_name: str = "rade-accessibility-scan"
    app_identifier: str | None = None
    device_name: str | None = None
    platform_version: str | None = None
    automation_name: str | None = None
    appium_app: str | None = None
    bundle_id: str | None = None
    app_package: str | None = None


@dataclass(frozen=True)
class FunctionalNode:
    node_ref: str
    parent_node_ref: str | None
    element_id: str
    parent_id: str | None
    screen_id: str
    screen_name: str
    platform: str
    source: str
    element_type: str
    role: str
    label: str
    accessibility_identifier: str | None
    interactive: bool
    visible: bool
    bounds: list[int] | None
    hierarchy_depth: int
    child_count: int
    text_present: bool
    traits: list[str] = field(default_factory=list)
    slab_layer: str = ASSETS_LAYER
    slab03_frame_id: str | None = None
    slab03_anchor_kind: str | None = None
    structural_fingerprint: str = ""
    functional_dna: JsonDict = field(default_factory=dict)

    def to_dict(self) -> JsonDict:
        return {
            "node_ref": self.node_ref,
            "parent_node_ref": self.parent_node_ref,
            "element_id": self.element_id,
            "parent_id": self.parent_id,
            "screen_id": self.screen_id,
            "screen_name": self.screen_name,
            "platform": self.platform,
            "source": self.source,
            "element_type": self.element_type,
            "role": self.role,
            "label": self.label,
            "accessibility_identifier": self.accessibility_identifier,
            "interactive": self.interactive,
            "visible": self.visible,
            "bounds": self.bounds,
            "bounding_box": _bounding_box_from_bounds(self.bounds),
            "hierarchy_depth": self.hierarchy_depth,
            "child_count": self.child_count,
            "text_present": self.text_present,
            "traits": list(self.traits),
            "slab_layer": self.slab_layer,
            "slab03_frame_id": self.slab03_frame_id,
            "slab03_anchor_kind": self.slab03_anchor_kind,
            "structural_fingerprint": self.structural_fingerprint,
            "functional_dna": dict(self.functional_dna),
        }


@dataclass(frozen=True)
class FunctionalEdge:
    source_node_ref: str
    target_node_ref: str
    edge_type: str
    screen_id: str
    screen_name: str
    metadata: JsonDict = field(default_factory=dict)

    def to_dict(self) -> JsonDict:
        return {
            "source_node_ref": self.source_node_ref,
            "target_node_ref": self.target_node_ref,
            "edge_type": self.edge_type,
            "screen_id": self.screen_id,
            "screen_name": self.screen_name,
            "metadata": dict(self.metadata),
        }


@dataclass
class ConstructionGraph:
    """Normalized structural graph for a single captured screen or flow."""

    app_id: str
    platform: str
    screen_id: str
    screen_name: str
    capture_source: str
    nodes: list[FunctionalNode] = field(default_factory=list)
    edges: list[FunctionalEdge] = field(default_factory=list)
    metadata: JsonDict = field(default_factory=dict)

    def to_dict(self) -> JsonDict:
        return {
            "app_id": self.app_id,
            "platform": self.platform,
            "screen_id": self.screen_id,
            "screen_name": self.screen_name,
            "capture_source": self.capture_source,
            "metadata": dict(self.metadata),
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }

    def to_project_payload(self) -> JsonDict:
        """Bridge into the current proof-slice contract."""

        elements = []
        for node in self.nodes:
            element = node.to_dict()
            element.pop("node_ref", None)
            element.pop("parent_node_ref", None)
            elements.append(element)
        return {
            "project_name": self.metadata.get("project_name", self.screen_name),
            "platform": self.platform,
            "screens": [
                {
                    "screen_id": self.screen_id,
                    "screen_name": self.screen_name,
                    "elements": elements,
                }
            ],
        }

    def to_figma_bridge_v0_manifest(self) -> JsonDict:
        """Deterministic Figma-oriented component manifest (v0.2.2 + ref_map proof slice)."""

        from ..core.figma_bridge_v0 import build_figma_bridge_v0_manifest

        return build_figma_bridge_v0_manifest(
            app_id=self.app_id,
            platform=self.platform,
            screen_id=self.screen_id,
            screen_name=self.screen_name,
            nodes=[node.to_dict() for node in self.nodes],
            edges=[edge.to_dict() for edge in self.edges],
        )


class RadeOrchestrator:
    """
    Collect accessibility trees and emit a deterministic structural graph.

    This scaffold keeps the provider boundary explicit:
    AWS Device Farm, Appium, and the actual tree source are runtime inputs.
    The engine itself only depends on a root accessibility object or a driver
    that can expose one.
    """

    def __init__(
        self,
        *,
        app_id: str,
        platform: str,
        session_config: AWSDeviceFarmSessionConfig | None = None,
        session_factory: Callable[[str, dict[str, Any]], Any] | None = None,
        source: str = "accessibility_tree",
    ) -> None:
        self.app_id = app_id
        self.platform = platform.strip().lower()
        self.session_config = session_config or AWSDeviceFarmSessionConfig(
            platform_name=self.platform
        )
        self.session_factory = session_factory
        self.source = source
        self.driver: Any | None = None

    def build_session_capabilities(self) -> dict[str, Any]:
        """Build platform-specific Appium capabilities for a managed session."""

        automation_name = self.session_config.automation_name
        if not automation_name:
            automation_name = "XCUITest" if self.platform == "ios" else "UiAutomator2"

        capabilities: dict[str, Any] = {
            "platformName": "iOS" if self.platform == "ios" else "Android",
            "appium:automationName": automation_name,
            "appium:newCommandTimeout": 120,
            "appium:noReset": True,
        }
        if self.session_config.device_name:
            capabilities["appium:deviceName"] = self.session_config.device_name
        if self.session_config.platform_version:
            capabilities["appium:platformVersion"] = (
                self.session_config.platform_version
            )
        if self.session_config.appium_app:
            capabilities["appium:app"] = self.session_config.appium_app
        if self.session_config.bundle_id:
            capabilities["appium:bundleId"] = self.session_config.bundle_id
        if self.session_config.app_package:
            capabilities["appium:appPackage"] = self.session_config.app_package
        if self.session_config.session_name:
            capabilities["appium:sessionName"] = self.session_config.session_name
        return capabilities

    def initialize_managed_session(self) -> Any:
        """
        Bind to the remote Appium endpoint.

        The actual AWS Device Farm wire-up is provider-specific, so the caller
        provides an Appium session factory that knows how to connect to the
        managed endpoint.
        """

        if not self.session_config.remote_url:
            raise ValueError("remote_url is required to initialize a managed session")
        if self.session_factory is None:
            raise NotImplementedError(
                "Provide a session_factory that returns an Appium driver."
            )
        self.driver = self.session_factory(
            self.session_config.remote_url, self.build_session_capabilities()
        )
        return self.driver

    def collect_from_driver(
        self,
        driver: Any,
        *,
        screen_id: str,
        screen_name: str | None = None,
        max_depth: int = 20,
    ) -> ConstructionGraph:
        """Resolve the accessibility root from a driver and collect the graph."""

        root = self._resolve_root(driver)
        return self.collect_from_root(
            root,
            screen_id=screen_id,
            screen_name=screen_name,
            max_depth=max_depth,
        )

    def collect_from_root(
        self,
        root_element: Any,
        *,
        screen_id: str,
        screen_name: str | None = None,
        max_depth: int = 20,
    ) -> ConstructionGraph:
        """Collect a deterministic graph with traversal guards."""

        screen_name = screen_name or screen_id
        graph = ConstructionGraph(
            app_id=self.app_id,
            platform=self.platform,
            screen_id=screen_id,
            screen_name=screen_name,
            capture_source=self.source,
            metadata={
                "session_provider": self.session_config.provider,
                "captured_at": self._now_iso(),
                "session_name": self.session_config.session_name,
                "project_name": screen_name,
                "accessibility_source": self.source,
            },
        )
        visited_nodes: set[str] = set()
        depth_limit_logged = {"value": False}

        self._traverse(
            element=root_element,
            graph=graph,
            screen_id=screen_id,
            screen_name=screen_name,
            parent_node_ref=None,
            parent_id=None,
            path=("0",),
            depth=0,
            max_depth=max_depth,
            visited_nodes=visited_nodes,
            depth_limit_logged=depth_limit_logged,
        )
        graph.nodes = self._apply_slab03_frame_intelligence(graph.nodes)
        graph.metadata["node_count"] = len(graph.nodes)
        graph.metadata["edge_count"] = len(graph.edges)
        return graph

    def _apply_slab03_frame_intelligence(
        self, nodes: list[FunctionalNode]
    ) -> list[FunctionalNode]:
        if not nodes:
            return nodes
        raw_elements = [
            {
                "element_id": node.element_id,
                "node_ref": node.node_ref,
                "parent_id": node.parent_id,
                "role": node.role,
                "element_type": node.element_type,
                "traits": list(node.traits),
                "label": node.label,
                "accessibility_identifier": node.accessibility_identifier,
                "bounds": node.bounds,
                "bounding_box": _bounding_box_from_bounds(node.bounds),
            }
            for node in nodes
        ]
        enriched = apply_slab03_hybrid_pulse(raw_elements)
        enriched_by_element_id: dict[str, JsonDict] = {}
        for element in enriched:
            eid = str(element.get("element_id") or "").strip()
            if eid:
                enriched_by_element_id[eid] = element
        slab03_payload_keys = (
            "slab03_frame_id",
            "slab03_anchor_kind",
            "slab03_landmark_kind",
            "slab03_figma_alias",
        )
        updated_nodes: list[FunctionalNode] = []
        for node in nodes:
            row = enriched_by_element_id.get(node.element_id)
            if row is None or row.get("slab03_frame_id") is None:
                updated_nodes.append(node)
                continue
            dna = dict(node.functional_dna)
            for key in slab03_payload_keys:
                value = row.get(key)
                if value is not None:
                    dna[key] = value
            updated_nodes.append(
                replace(
                    node,
                    slab03_frame_id=str(row["slab03_frame_id"]),
                    slab03_anchor_kind=(
                        str(row["slab03_anchor_kind"])
                        if row.get("slab03_anchor_kind") is not None
                        else None
                    ),
                    functional_dna=dna,
                )
            )
        return updated_nodes

    def scrub_graph(self, graph: ConstructionGraph) -> tuple[JsonDict, JsonDict]:
        """Apply the edge scrubber at the persistence boundary."""

        from ..scrubber.edge_shield import scrub_payload_with_metadata

        return scrub_payload_with_metadata(graph.to_dict())

    def _traverse(
        self,
        *,
        element: Any,
        graph: ConstructionGraph,
        screen_id: str,
        screen_name: str,
        parent_node_ref: str | None,
        parent_id: str | None,
        path: tuple[str, ...],
        depth: int,
        max_depth: int,
        visited_nodes: set[str],
        depth_limit_logged: dict[str, bool],
    ) -> None:
        visit_key = self._node_visit_key(element)
        if visit_key in visited_nodes:
            return

        children = self._get_children(element)
        node = self._build_node(
            element=element,
            graph=graph,
            screen_id=screen_id,
            screen_name=screen_name,
            parent_node_ref=parent_node_ref,
            parent_id=parent_id,
            path=path,
            depth=depth,
            child_count=len(children),
        )
        visited_nodes.add(visit_key)
        graph.nodes.append(node)

        if parent_node_ref is not None:
            graph.edges.append(
                FunctionalEdge(
                    source_node_ref=parent_node_ref,
                    target_node_ref=node.node_ref,
                    edge_type="contains",
                    screen_id=screen_id,
                    screen_name=screen_name,
                    metadata={"path": ".".join(path), "depth": depth},
                )
            )
        graph.edges.extend(
            self._build_plumbing_edges(
                element=element,
                node=node,
                screen_id=screen_id,
                screen_name=screen_name,
                path=path,
                depth=depth,
            )
        )

        if depth >= max_depth:
            if not depth_limit_logged["value"]:
                logger.warning(
                    "Traversal max_depth=%s reached for screen_id=%s; preserving partial graph.",
                    max_depth,
                    screen_id,
                )
                depth_limit_logged["value"] = True
            return

        traversal_children = self._select_children_for_traversal(node, children)
        for original_index, child in traversal_children:
            child_path = path + (str(original_index),)
            self._traverse(
                element=child,
                graph=graph,
                screen_id=screen_id,
                screen_name=screen_name,
                parent_node_ref=node.node_ref,
                parent_id=node.element_id,
                path=child_path,
                depth=depth + 1,
                max_depth=max_depth,
                visited_nodes=visited_nodes,
                depth_limit_logged=depth_limit_logged,
            )

    def _build_node(
        self,
        *,
        element: Any,
        graph: ConstructionGraph,
        screen_id: str,
        screen_name: str,
        parent_node_ref: str | None,
        parent_id: str | None,
        path: tuple[str, ...],
        depth: int,
        child_count: int | None = None,
    ) -> FunctionalNode:
        element_type = self._normalize_text(
            self._read_attribute(
                element,
                "element_type",
                "elementType",
                "type",
                "class_name",
                "className",
                "tag_name",
                "tagName",
            )
        )
        role = self._infer_role(element, element_type, depth)
        label = self._normalize_text(
            self._read_attribute(element, "label", "text", "name", "value", "title")
        )
        accessibility_identifier = self._normalize_text(
            self._read_attribute(
                element,
                "accessibility_identifier",
                "accessibilityIdentifier",
                "identifier",
                "resource_id",
                "resourceId",
                "content_desc",
                "contentDescription",
            )
        )
        traits = self._normalize_traits(
            self._read_attribute(element, "traits", "accessibilityTraits", "role")
        )
        interactive = self._infer_interactive(element, role, element_type, traits)
        visible = self._infer_visible(element)
        bounds = self._normalize_bounds(
            self._read_attribute(element, "bounds", "rect", "frame")
        )
        slab_layer = self._normalize_text(
            self._read_attribute(element, "slab_layer", "slabLayer")
        )
        text_present = bool(label)
        resolved_child_count = (
            child_count if child_count is not None else len(self._get_children(element))
        )

        base_node = {
            "screen_id": screen_id,
            "screen_name": screen_name,
            "element_id": "",
            "parent_id": parent_id,
            "element_type": element_type,
            "role": role,
            "label": label,
            "accessibility_identifier": accessibility_identifier,
            "interactive": interactive,
            "visible": visible,
            "bounds": bounds,
            "hierarchy_depth": depth,
            "child_count": resolved_child_count,
            "text_present": text_present,
            "slab_layer": slab_layer,
            "traits": traits,
            "platform": self.platform,
            "source": self.source,
        }
        layered = layer_element(base_node)
        fingerprint = fingerprint_node(layered)
        element_id = stable_digest(
            screen_id,
            ".".join(path),
            role,
            element_type,
            label,
            accessibility_identifier or "",
            fingerprint,
        )
        node_ref = build_node_ref(screen_id, element_id)
        functional_dna = {
            "node_ref": node_ref,
            "path": ".".join(path),
            "role": role,
            "element_type": element_type,
            "label": label,
            "accessibility_identifier": accessibility_identifier,
            "interactive": interactive,
            "visible": visible,
            "bounds": bounds,
            "hierarchy_depth": depth,
            "child_count": resolved_child_count,
            "traits": traits,
            "slab_layer": layered["slab_layer"],
            "structural_fingerprint": fingerprint,
        }
        functional_dna.update(
            self._deep_raid_metadata(
                element=element,
                role=role,
                element_type=element_type,
                traits=traits,
                child_count=resolved_child_count,
            )
        )
        return FunctionalNode(
            node_ref=node_ref,
            parent_node_ref=parent_node_ref,
            element_id=element_id,
            parent_id=parent_id,
            screen_id=screen_id,
            screen_name=screen_name,
            platform=self.platform,
            source=self.source,
            element_type=element_type,
            role=role,
            label=label,
            accessibility_identifier=accessibility_identifier,
            interactive=interactive,
            visible=visible,
            bounds=bounds,
            hierarchy_depth=depth,
            child_count=resolved_child_count,
            text_present=text_present,
            traits=traits,
            slab_layer=layered["slab_layer"],
            structural_fingerprint=fingerprint,
            functional_dna=functional_dna,
        )

    def _deep_raid_metadata(
        self,
        *,
        element: Any,
        role: str,
        element_type: str,
        traits: list[str],
        child_count: int,
    ) -> JsonDict:
        frame_kind = self._infer_frame_kind(
            element=element,
            role=role,
            element_type=element_type,
            traits=traits,
            child_count=child_count,
        )
        destination = self._infer_destination(element)
        metadata: JsonDict = {
            "instruction_role": (
                "frame" if frame_kind else "plumbing" if destination else "component"
            ),
            "structural_frame": frame_kind is not None,
            "frame_kind": frame_kind,
            "destination_kind": destination.get("kind") if destination else None,
            "destination_ref": destination.get("ref") if destination else None,
            "destination_template": (
                destination.get("template") if destination else None
            ),
        }
        metadata["pattern_fingerprint"] = stable_digest(
            role,
            element_type,
            frame_kind or "-",
            metadata["destination_kind"] or "-",
            str(child_count),
            ",".join(traits),
        )
        design_tokens = self._extract_design_tokens(element)
        if design_tokens is not None:
            metadata["design_tokens"] = design_tokens
            metadata["token_pulse_id"] = stable_digest(
                "token-pulse",
                "|".join(design_tokens["color_tokens"]),
                "|".join(design_tokens["typography_tokens"]),
                "|".join(design_tokens["spacing_tokens"]),
            )
        return metadata

    def _extract_design_tokens(self, element: Any) -> JsonDict | None:
        color_tokens: set[str] = set()
        typography_tokens: set[str] = set()
        spacing_tokens: set[str] = set()

        style_value = self._normalize_text(
            self._read_attribute(element, "style", "cssText")
        )
        if style_value:
            style_tokens = self._parse_inline_style(style_value)
            color_tokens.update(style_tokens["color_tokens"])
            typography_tokens.update(style_tokens["typography_tokens"])
            spacing_tokens.update(style_tokens["spacing_tokens"])

        for attr_name in _TOKEN_ATTRS_COLOR:
            value = self._normalize_text(self._read_attribute(element, attr_name))
            if value:
                color_tokens.add(
                    f"{attr_name.replace('_', '-')}:{_normalize_color_value(value)}"
                )

        for attr_name in _TOKEN_ATTRS_TYPO:
            value = self._normalize_text(self._read_attribute(element, attr_name))
            if value:
                typography_tokens.add(f"{attr_name.replace('_', '-')}:{value.lower()}")

        for attr_name in _TOKEN_ATTRS_SPACING:
            value = self._normalize_text(self._read_attribute(element, attr_name))
            if value:
                spacing_tokens.add(f"{attr_name}:{value.lower()}")

        if not color_tokens and not typography_tokens and not spacing_tokens:
            return None
        return {
            "color_tokens": sorted(color_tokens),
            "typography_tokens": sorted(typography_tokens),
            "spacing_tokens": sorted(spacing_tokens),
        }

    def _parse_inline_style(self, style_value: str) -> JsonDict:
        color_tokens: set[str] = set()
        typography_tokens: set[str] = set()
        spacing_tokens: set[str] = set()
        for declaration in style_value.split(";"):
            if ":" not in declaration:
                continue
            raw_key, raw_value = declaration.split(":", 1)
            key = raw_key.strip().lower()
            value = raw_value.strip().lower()
            if not key or not value:
                continue
            token = f"{key}:{value}"
            if key in {"color", "background", "background-color", "border-color"}:
                color_tokens.add(f"{key}:{_normalize_color_value(value)}")
            elif key in {"font-family", "font-size", "font-weight", "line-height"}:
                typography_tokens.add(token)
            elif key in {"margin", "padding", "gap", "row-gap", "column-gap"}:
                spacing_tokens.add(token)
        return {
            "color_tokens": sorted(color_tokens),
            "typography_tokens": sorted(typography_tokens),
            "spacing_tokens": sorted(spacing_tokens),
        }

    def _select_children_for_traversal(
        self, node: FunctionalNode, children: list[Any]
    ) -> list[tuple[int, Any]]:
        if not children:
            return []

        if not self._is_sampling_container(node):
            return list(enumerate(children))

        ordered_children = sorted(
            enumerate(children),
            key=lambda item: (
                -self._node_priority_score(item[1]),
                item[0],
            ),
        )
        sample_limit = min(len(children), LIST_CHILD_SAMPLE_LIMIT)
        return ordered_children[:sample_limit]

    def _is_sampling_container(self, node: FunctionalNode) -> bool:
        element_type = node.element_type.lower()
        role = node.role.lower()
        traits = node.traits
        return (
            any(token in element_type for token in CONTAINER_TOKENS)
            or any(token in role for token in ("container", "list", "scroll"))
            or any(
                any(token in trait for token in CONTAINER_TOKENS) for trait in traits
            )
        )

    def _node_priority_score(self, element: Any) -> int:
        element_type = self._normalize_text(
            self._read_attribute(
                element,
                "element_type",
                "elementType",
                "type",
                "class_name",
                "className",
                "tag_name",
                "tagName",
            )
        ).lower()
        role = self._normalize_text(
            self._read_attribute(
                element,
                "role",
                "accessibility_role",
                "accessibilityRole",
                "type",
                "class_name",
                "className",
            )
        ).lower()
        label = self._normalize_text(
            self._read_attribute(element, "label", "text", "name", "value", "title")
        )
        traits = self._normalize_traits(
            self._read_attribute(element, "traits", "accessibilityTraits", "role")
        )
        score = 0

        for token, token_score in PRIORITY_TRAIT_TOKENS.items():
            if (
                token in element_type
                or token in role
                or any(token in trait for trait in traits)
            ):
                score = max(score, token_score)

        if (
            any(token in element_type for token in STATIC_TEXT_TOKENS)
            or any(token in role for token in STATIC_TEXT_TOKENS)
            or any(
                any(token in trait for token in STATIC_TEXT_TOKENS) for trait in traits
            )
        ):
            score = max(score, 10)

        if (
            any(token in element_type for token in CONTAINER_TOKENS)
            or any(token in role for token in ("container", "list", "scroll"))
            or any(
                any(token in trait for token in CONTAINER_TOKENS) for trait in traits
            )
        ):
            score = max(score, 20)

        if label:
            score += 1
        return score

    def _build_plumbing_edges(
        self,
        *,
        element: Any,
        node: FunctionalNode,
        screen_id: str,
        screen_name: str,
        path: tuple[str, ...],
        depth: int,
    ) -> list[FunctionalEdge]:
        destination = self._infer_destination(element)
        if destination is None or not node.interactive:
            return []
        destination_ref = str(destination["ref"])
        destination_kind = str(destination["kind"])
        edge_type = {
            "route": "routes_to",
            "submit": "submits_to",
            "control": "controls",
            "action": "triggers",
        }.get(destination_kind, "routes_to")
        target_node_ref = f"{screen_id}#destination-{stable_digest(destination_kind, destination_ref)}"
        return [
            FunctionalEdge(
                source_node_ref=node.node_ref,
                target_node_ref=target_node_ref,
                edge_type=edge_type,
                screen_id=screen_id,
                screen_name=screen_name,
                metadata={
                    "path": ".".join(path),
                    "depth": depth,
                    "destination_kind": destination_kind,
                    "destination_ref": destination_ref,
                    "destination_template": destination.get("template"),
                },
            )
        ]

    def _node_visit_key(self, element: Any) -> str:
        element_type = self._normalize_text(
            self._read_attribute(
                element,
                "element_type",
                "elementType",
                "type",
                "class_name",
                "className",
                "tag_name",
                "tagName",
            )
        ).lower()
        bounds = self._normalize_bounds(
            self._read_attribute(element, "bounds", "rect", "frame")
        )
        bounds_key = (
            "none" if bounds is None else ",".join(str(item) for item in bounds)
        )
        return stable_digest(element_type, bounds_key)

    def _resolve_root(self, driver: Any) -> Any:
        for name in ("root_element", "root", "page_source_root", "element"):
            candidate = getattr(driver, name, None)
            if candidate is not None:
                return candidate
        return driver

    def _get_children(self, element: Any) -> list[Any]:
        if isinstance(element, dict):
            children = element.get("children", [])
            return list(children) if isinstance(children, list) else []

        children = getattr(element, "children", None)
        if isinstance(children, list):
            return children
        if isinstance(children, tuple):
            return list(children)
        if callable(children):
            try:
                value = children()
            except TypeError:
                value = None
            if isinstance(value, list):
                return value
            if isinstance(value, tuple):
                return list(value)

        find_elements = getattr(element, "find_elements", None)
        if callable(find_elements):
            for args in (("xpath", "./*"), ("xpath", ".//*")):
                try:
                    children = find_elements(*args)
                except Exception:
                    continue
                if isinstance(children, list):
                    return children
        return []

    def _read_attribute(self, element: Any, *names: str) -> Any:
        if isinstance(element, dict):
            for name in names:
                if name in element and element[name] not in (None, ""):
                    return element[name]
            return None

        for name in names:
            if hasattr(element, name):
                value = getattr(element, name)
                if value not in (None, ""):
                    return value
            get_attribute = getattr(element, "get_attribute", None)
            if callable(get_attribute):
                try:
                    value = get_attribute(name)
                except Exception:
                    value = None
                if value not in (None, ""):
                    return value
        return None

    def _infer_role(self, element: Any, element_type: str, depth: int) -> str:
        raw = self._normalize_text(
            self._read_attribute(
                element,
                "role",
                "accessibility_role",
                "accessibilityRole",
                "type",
                "class_name",
                "className",
            )
        )
        candidate = raw or element_type
        normalized = candidate.lower()
        if depth == 0:
            if "window" in normalized or "screen" in normalized or "view" in normalized:
                return "screen"
        if any(token in normalized for token in ("button", "cta", "action")):
            return "button"
        if any(
            token in normalized
            for token in ("text_field", "textfield", "input", "edittext", "search")
        ):
            return "input"
        if any(
            token in normalized for token in ("toggle", "switch", "checkbox", "radio")
        ):
            return "toggle"
        if any(token in normalized for token in ("tab", "navigation")):
            return "navigation"
        if any(token in normalized for token in ("dialog", "alertdialog", "modal")):
            return "dialog"
        if any(token in normalized for token in ("image", "icon", "media")):
            return "image"
        if any(
            token in normalized
            for token in ("label", "text", "title", "copy", "statictext")
        ):
            return "text"
        if any(
            token in normalized
            for token in ("stack", "container", "group", "card", "list", "grid")
        ):
            return "container"
        return "unknown"

    def _infer_interactive(
        self, element: Any, role: str, element_type: str, traits: list[str]
    ) -> bool:
        if role in {"button", "input", "toggle", "navigation"}:
            return True
        if "interactive" in traits or "action" in traits:
            return True
        enabled = self._read_attribute(element, "enabled", "isEnabled", "clickable")
        if isinstance(enabled, bool) and enabled:
            return role not in {"text", "image", "container", "screen"}
        if any(
            token in element_type.lower()
            for token in ("button", "input", "switch", "tab")
        ):
            return True
        return False

    def _infer_visible(self, element: Any) -> bool:
        visible = self._read_attribute(
            element,
            "visible",
            "isVisible",
            "displayed",
            "is_displayed",
        )
        if isinstance(visible, bool):
            return visible
        return True

    def _normalize_text(self, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    def _normalize_traits(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            items = value
        else:
            items = [value]
        normalized = {
            self._normalize_text(item).lower()
            for item in items
            if self._normalize_text(item)
        }
        return sorted(normalized)

    def _normalize_bounds(self, value: Any) -> list[int] | None:
        if value is None:
            return None
        if isinstance(value, dict):
            keys = ("x", "y", "width", "height")
            if all(key in value for key in keys):
                try:
                    return [int(float(value[key])) for key in keys]
                except (TypeError, ValueError):
                    return None
        if isinstance(value, (list, tuple)) and len(value) == 4:
            try:
                return [int(float(item)) for item in value]
            except (TypeError, ValueError):
                return None
        if isinstance(value, str):
            cleaned = value.replace("{", "").replace("}", "").replace(",", " ")
            parts = [part for part in cleaned.split() if part]
            if len(parts) == 4:
                try:
                    return [int(float(part)) for part in parts]
                except (TypeError, ValueError):
                    return None
        return None

    def _infer_frame_kind(
        self,
        *,
        element: Any,
        role: str,
        element_type: str,
        traits: list[str],
        child_count: int,
    ) -> str | None:
        explicit = self._normalize_text(
            self._read_attribute(
                element, "frame_kind", "layout_hint", "data-rade-frame-kind"
            )
        ).lower()
        if explicit:
            return explicit

        normalized_tokens = " ".join(
            item
            for item in (
                element_type.lower(),
                role.lower(),
                " ".join(traits),
                self._normalize_text(
                    self._read_attribute(
                        element, "class_name", "className", "class", "data-testid"
                    )
                ).lower(),
            )
            if item
        )
        if (
            "sidebar" in normalized_tokens
            or "aside" in normalized_tokens
            or "rail" in normalized_tokens
        ):
            return "sidebar"
        if "grid" in normalized_tokens:
            return "grid"
        if "row" in normalized_tokens or "flex" in normalized_tokens:
            return "flex_row"
        if (
            any(token in normalized_tokens for token in STRUCTURAL_FRAME_TOKENS)
            and child_count > 0
        ):
            return "container"
        if role in {"navigation", "container"} and child_count > 1:
            return "container"
        return None

    def _infer_destination(self, element: Any) -> JsonDict | None:
        route = self._normalize_text(
            self._read_attribute(element, "href", "to", "url", "destination_ref")
        )
        if route:
            return {
                "kind": "route",
                "ref": self._normalize_destination_ref(route),
                "template": self._destination_template(route),
            }

        action = self._normalize_text(
            self._read_attribute(element, "action", "formaction", "data-action")
        )
        if action:
            return {
                "kind": "submit",
                "ref": self._normalize_destination_ref(action),
                "template": self._destination_template(action),
            }

        control = self._normalize_text(
            self._read_attribute(element, "aria-controls", "target", "target_id")
        )
        if control:
            return {
                "kind": "control",
                "ref": control,
                "template": control,
            }

        action_name = self._normalize_text(
            self._read_attribute(element, "destination", "on_click", "onClick")
        )
        if action_name:
            return {
                "kind": "action",
                "ref": action_name,
                "template": action_name,
            }
        return None

    def _normalize_destination_ref(self, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme or parsed.netloc:
            normalized_path = parsed.path or "/"
            return f"{parsed.netloc.lower()}{normalized_path}"
        if "#" in value:
            return value.split("#", 1)[0] or value
        if "?" in value:
            return value.split("?", 1)[0] or value
        return value

    def _destination_template(self, value: str) -> str:
        normalized = self._normalize_destination_ref(value)
        parts = [
            (
                "{id}"
                if any(char.isdigit() for char in segment) or len(segment) > 24
                else segment
            )
            for segment in normalized.split("/")
            if segment
        ]
        if not parts:
            return "/"
        return "/" + "/".join(parts)

    def _now_iso(self) -> str:
        return (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        )


def main() -> int:
    clear_terminal()
    emit_terminal_banner(force=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
