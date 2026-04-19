# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlparse
from xml.sax.saxutils import escape

from ..core.compliance import (
    LEGAL_NOTICE,
    PROJECT_TERMS_NOTICE,
    SVG_HEADER_COMMENT,
    SVG_WATERMARK_TEXT,
    clear_terminal,
    emit_terminal_banner,
    today_iso_date,
)
from ..core.layering import (
    ASSETS_LAYER,
    CONTAINERS_LAYER,
    LINKS_EVENTS_LAYER,
    OS_SITE_LAYER,
    ROOT_LAYER,
)
from ..database.graph_ingestor import Neo4jAuraConfig, RadeGraphIngestor
from ..engine.rade_orchestrator import (
    AWSDeviceFarmSessionConfig,
    ConstructionGraph,
    FunctionalEdge,
    FunctionalNode,
    RadeOrchestrator,
)
from ..scrubber.edge_shield import scrub_payload_with_metadata

try:  # Optional dependency.
    from rich.console import Console
except Exception:  # pragma: no cover - exercised when rich is unavailable.
    Console = None


ANSI_RESET = "\033[0m"
ANSI_STYLES = {
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "magenta": "\033[35m",
    "bold": "\033[1m",
}
XML_ATTRIBUTE_ESCAPES = {'"': "&quot;"}


@dataclass(frozen=True)
class DemoNode:
    element_type: str
    label: str = ""
    accessibility_identifier: str | None = None
    traits: list[str] = field(default_factory=list)
    bounds: dict[str, int] = field(
        default_factory=lambda: {"x": 0, "y": 0, "width": 0, "height": 0}
    )
    visible: bool = True
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list["DemoNode"] = field(default_factory=list)

    def get_attribute(self, name: str) -> Any:
        mapping = {
            "element_type": self.element_type,
            "elementType": self.element_type,
            "class_name": self.metadata.get("class", self.element_type),
            "className": self.metadata.get("class", self.element_type),
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
            "bounds": self.bounds,
            "rect": self.bounds,
            "frame": self.bounds,
            "visible": self.visible,
            "displayed": self.visible,
            "enabled": self.enabled,
            "clickable": self.enabled,
        }
        if name in mapping:
            return mapping.get(name)
        return self.metadata.get(name)


@dataclass(frozen=True)
class DemoManagedSession:
    remote_url: str
    capabilities: dict[str, Any]


@dataclass(frozen=True)
class DemoNeo4jResult:
    query: str
    parameters: dict[str, Any]

    def consume(self) -> "DemoNeo4jResult":
        return self


@dataclass
class DemoNeo4jSession:
    queries: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def run(self, query: str, /, **parameters: Any) -> DemoNeo4jResult:
        self.queries.append((query, parameters))
        return DemoNeo4jResult(query=query, parameters=parameters)

    def close(self) -> None:
        return None

    def __enter__(self) -> "DemoNeo4jSession":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None


@dataclass
class DemoNeo4jDriver:
    session_obj: DemoNeo4jSession = field(default_factory=DemoNeo4jSession)

    def session(self, /, **parameters: Any) -> DemoNeo4jSession:
        self.session_parameters = parameters
        return self.session_obj

    def close(self) -> None:
        return None


@dataclass(frozen=True)
class DemoRunResult:
    graph: ConstructionGraph
    scrubbed_graph: ConstructionGraph
    redacted_items: int
    ingest_summary: dict[str, Any]
    deep_raid_summary: dict[str, Any]
    svg_path: Path


@dataclass(frozen=True)
class ChromeTabContext:
    title: str
    url: str
    app_name: str
    app_id: str
    screen_id: str
    screen_name: str


@dataclass
class _MutableDemoNode:
    element_type: str
    label: str = ""
    accessibility_identifier: str | None = None
    traits: list[str] = field(default_factory=list)
    bounds: dict[str, int] = field(
        default_factory=lambda: {"x": 0, "y": 0, "width": 0, "height": 0}
    )
    visible: bool = True
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list["_MutableDemoNode"] = field(default_factory=list)

    def freeze(self) -> DemoNode:
        return DemoNode(
            element_type=self.element_type,
            label=self.label,
            accessibility_identifier=self.accessibility_identifier,
            traits=list(self.traits),
            bounds=dict(self.bounds),
            visible=self.visible,
            enabled=self.enabled,
            metadata=dict(self.metadata),
            children=[child.freeze() for child in self.children],
        )


class StructuralDomParser(HTMLParser):
    SKIP_CONTAINER_TAGS = {
        "defs",
        "head",
        "iframe",
        "noscript",
        "script",
        "style",
        "template",
        "title",
    }
    IGNORE_TAGS = {
        "base",
        "link",
        "meta",
        "path",
    }
    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(
        self,
        *,
        app_name: str,
        max_nodes: int = 64,
        max_depth: int = 20,
    ) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _MutableDemoNode(
            element_type="web_surface_window",
            label=f"{app_name} Surface",
            traits=["window"],
        )
        self._container_stack: list[_MutableDemoNode] = [self.root]
        self._open_container_tags: list[str] = []
        self._skip_depth = 0
        self._max_nodes = max_nodes
        self._max_depth = max_depth
        self._node_count = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        attributes = {
            name.lower(): (value or "").strip() for name, value in attrs if name
        }
        if self._skip_depth > 0:
            if (
                normalized_tag not in self.VOID_TAGS
                and normalized_tag not in self.IGNORE_TAGS
            ):
                self._skip_depth += 1
            return

        if normalized_tag in self.SKIP_CONTAINER_TAGS:
            self._skip_depth = 1
            return

        if normalized_tag in self.IGNORE_TAGS:
            return

        if self._is_hidden(normalized_tag, attributes):
            return

        if self._node_count >= self._max_nodes:
            return
        node = self._build_node(normalized_tag, attributes)
        if node is None:
            return
        if len(self._container_stack) > self._max_depth:
            return

        self._container_stack[-1].children.append(node)
        self._node_count += 1
        if normalized_tag not in self.VOID_TAGS and self._should_push_container(node):
            self._container_stack.append(node)
            self._open_container_tags.append(normalized_tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.lower()
        if (
            normalized_tag in self.SKIP_CONTAINER_TAGS
            or normalized_tag in self.IGNORE_TAGS
        ):
            return

        attributes = {
            name.lower(): (value or "").strip() for name, value in attrs if name
        }
        if (
            self._is_hidden(normalized_tag, attributes)
            or self._node_count >= self._max_nodes
        ):
            return
        node = self._build_node(normalized_tag, attributes)
        if node is None:
            return
        if len(self._container_stack) > self._max_depth:
            return
        self._container_stack[-1].children.append(node)
        self._node_count += 1

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if not self._open_container_tags:
            return
        normalized_tag = tag.lower()
        if normalized_tag == self._open_container_tags[-1]:
            self._open_container_tags.pop()
            if len(self._container_stack) > 1:
                self._container_stack.pop()

    def _build_node(
        self, tag: str, attributes: dict[str, str]
    ) -> _MutableDemoNode | None:
        role = attributes.get("role", "").lower()
        input_type = attributes.get("type", "").lower()
        frame_kind = self._frame_kind(tag, attributes)
        accessible_label = self._preferred_accessible_label(attributes)
        decor_label = self._decor_label(attributes)
        slab_layer_hint = self._slab_layer_hint(
            tag=tag,
            role=role,
            frame_kind=frame_kind,
            attributes=attributes,
        )
        element_type = ""
        label = ""
        traits: list[str] = []
        metadata = self._build_metadata(attributes)

        if tag in {"main"} or role == "main":
            element_type = "main_container"
            label = "Main Content"
            traits = ["container", "main"]
        elif tag in {"header"} or role == "banner":
            element_type = "header_container"
            label = "Header"
            traits = ["container", "header"]
        elif tag in {"footer"} or role == "contentinfo":
            element_type = "footer_container"
            label = "Footer"
            traits = ["container", "footer"]
        elif tag in {"nav"} or role == "navigation":
            element_type = "navigation"
            label = "Navigation"
            traits = ["navigation"]
        elif tag in {"section"} or role == "region":
            element_type = "section_container"
            label = "Section"
            traits = ["container", "section"]
        elif tag in {"article"} or role == "article":
            element_type = "article_container"
            label = "Article"
            traits = ["container", "article"]
        elif tag in {"aside"} or role == "complementary":
            element_type = "aside_container"
            label = "Sidebar"
            traits = ["container", "aside"]
        elif tag in {"form"} or role == "form":
            element_type = "form_container"
            label = "Form"
            traits = ["container", "form"]
        elif role == "search":
            element_type = "search_container"
            label = "Search Region"
            traits = ["container", "search"]
        elif tag == "button" or role == "button":
            element_type = "button"
            label = "Button"
            traits = ["button"]
        elif tag == "a" or role == "link":
            element_type = "link"
            label = "Link"
            traits = ["navigation", "link"]
        elif tag == "input":
            if input_type == "search":
                element_type = "search_input"
                label = "Search Field"
                traits = ["input", "search"]
            else:
                element_type = "input"
                label = "Input Field"
                traits = ["input"]
        elif tag == "textarea":
            element_type = "text_area"
            label = "Text Area"
            traits = ["input", "text"]
        elif tag == "select":
            element_type = "select_input"
            label = "Select Menu"
            traits = ["input", "select"]
        elif tag in {"ul", "ol"}:
            element_type = "list_container"
            label = "List"
            traits = ["container", "list"]
        elif tag == "li":
            element_type = "list_item"
            label = "List Item"
            traits = ["list"]
        elif tag == "div" and frame_kind is not None:
            element_type = f"{frame_kind}_container"
            label = self._frame_label(frame_kind)
            traits = ["container", "structural_frame", frame_kind]
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"} or role == "heading":
            element_type = "heading_text"
            label = "Heading"
            traits = ["text", "heading"]
        elif tag in {"p"}:
            element_type = "text_block"
            label = "Text Block"
            traits = ["text"]
        elif tag in {"img", "svg"} or role == "img":
            element_type = "image"
            label = "Decor Asset" if slab_layer_hint == ASSETS_LAYER else "Image"
            traits = ["image"]
        elif self._is_decorative_asset_candidate(
            tag=tag,
            role=role,
            frame_kind=frame_kind,
            attributes=attributes,
        ):
            element_type = "image_asset"
            label = "Decor Asset"
            traits = ["image", "decor"]
        elif role in {"dialog", "alertdialog"}:
            element_type = "dialog_container"
            label = "Dialog"
            traits = ["container", "dialog"]
        elif role in {"list", "listbox", "menu", "tablist"}:
            element_type = f"{role}_container"
            label = self._structural_label_from_role(role)
            traits = ["container", role]
        elif role in {"tab", "menuitem", "option"}:
            element_type = role
            label = self._structural_label_from_role(role)
            traits = [role]
        elif role:
            element_type = role.replace("-", "_")
            label = self._structural_label_from_role(role)
            traits = [role]
        else:
            return None

        if frame_kind is not None and "structural_frame" not in traits:
            traits = [*traits, "structural_frame"]
            metadata.setdefault("frame_kind", frame_kind)
        if slab_layer_hint is not None:
            metadata["slab_layer"] = slab_layer_hint
            if slab_layer_hint == ASSETS_LAYER and "decor" not in traits:
                traits = [*traits, "decor"]

        resolved_label = self._resolve_label(
            default_label=label,
            accessible_label=accessible_label,
            decor_label=decor_label,
            element_type=element_type,
        )

        return _MutableDemoNode(
            element_type=element_type,
            label=resolved_label,
            traits=traits,
            bounds=self._synthetic_bounds(),
            enabled=True,
            visible=True,
            metadata=metadata,
        )

    def _is_hidden(self, tag: str, attributes: dict[str, str]) -> bool:
        aria_hidden = attributes.get("aria-hidden", "").lower()
        hidden = "hidden" in attributes
        if not hidden and aria_hidden != "true":
            return False
        return not self._should_capture_hidden_asset(tag, attributes)

    def _structural_label_from_role(self, role: str) -> str:
        return role.replace("-", " ").replace("_", " ").title()

    def _should_push_container(self, node: _MutableDemoNode) -> bool:
        element_type = node.element_type
        return (
            element_type == "navigation"
            or element_type.endswith("_container")
            or element_type in {"list_container", "list_item"}
        )

    def _synthetic_bounds(self) -> dict[str, int]:
        ordinal = self._node_count
        depth = len(self._container_stack)
        return {
            "x": 24 * ordinal,
            "y": 72 * depth,
            "width": 220,
            "height": 52,
        }

    def _frame_kind(self, tag: str, attributes: dict[str, str]) -> str | None:
        signals = " ".join(
            part
            for part in (
                tag,
                attributes.get("class", ""),
                attributes.get("style", ""),
                attributes.get("data-testid", ""),
                attributes.get("aria-label", ""),
            )
            if part
        ).lower()
        if "sidebar" in signals or "aside" in signals or "rail" in signals:
            return "sidebar"
        if "grid" in signals:
            return "grid"
        if "row" in signals or "flex" in signals:
            return "flex_row"
        if "list" in signals or "results" in signals or "cards" in signals:
            return "container"
        return None

    def _frame_label(self, frame_kind: str) -> str:
        return {
            "grid": "Grid Frame",
            "flex_row": "Flex Row",
            "sidebar": "Sidebar",
            "container": "Container Frame",
        }.get(frame_kind, "Frame")

    def _preferred_accessible_label(self, attributes: dict[str, str]) -> str:
        for key in ("aria-label", "alt", "title"):
            value = self._clean_label(attributes.get(key, ""))
            if value:
                return value
        return ""

    def _resolve_label(
        self,
        *,
        default_label: str,
        accessible_label: str,
        decor_label: str,
        element_type: str,
    ) -> str:
        primary_label = accessible_label or decor_label
        if not primary_label:
            return default_label
        if element_type == "button" and not primary_label.lower().endswith("button"):
            return f"{primary_label} Button"
        return primary_label

    def _clean_label(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _decor_label(self, attributes: dict[str, str]) -> str:
        for candidate in (
            attributes.get("id", ""),
            attributes.get("data-testid", ""),
            attributes.get("class", "").split()[0] if attributes.get("class") else "",
        ):
            value = self._humanize_token(candidate)
            if value:
                return value
        return ""

    def _humanize_token(self, value: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", " ", value).strip()
        if not normalized:
            return ""
        return normalized.title()

    def _slab_layer_hint(
        self,
        *,
        tag: str,
        role: str,
        frame_kind: str | None,
        attributes: dict[str, str],
    ) -> str | None:
        if self._is_decorative_asset_candidate(
            tag=tag,
            role=role,
            frame_kind=frame_kind,
            attributes=attributes,
        ):
            return ASSETS_LAYER
        return None

    def _is_decorative_asset_candidate(
        self,
        *,
        tag: str,
        role: str,
        frame_kind: str | None,
        attributes: dict[str, str],
    ) -> bool:
        if frame_kind is not None:
            return False
        if tag in {"img", "svg"} or role == "img":
            return True
        if tag not in {"div", "span"}:
            return False
        if not self._has_identifier(attributes):
            return False
        signals = " ".join(
            part
            for part in (
                attributes.get("id", ""),
                attributes.get("class", ""),
                attributes.get("data-testid", ""),
                attributes.get("style", ""),
            )
            if part
        ).lower()
        return any(
            token in signals
            for token in (
                "avatar",
                "badge",
                "hero",
                "icon",
                "illustration",
                "image",
                "logo",
                "media",
                "poster",
                "thumbnail",
            )
        )

    def _has_identifier(self, attributes: dict[str, str]) -> bool:
        return any(
            self._clean_label(attributes.get(key, ""))
            for key in ("id", "class", "data-testid")
        )

    def _should_capture_hidden_asset(
        self, tag: str, attributes: dict[str, str]
    ) -> bool:
        return self._is_decorative_asset_candidate(
            tag=tag,
            role=attributes.get("role", "").lower(),
            frame_kind=self._frame_kind(tag, attributes),
            attributes=attributes,
        ) and self._has_identifier(attributes)

    def _build_metadata(self, attributes: dict[str, str]) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        for source_key, target_key in (
            ("style", "style"),
            ("href", "href"),
            ("action", "action"),
            ("formaction", "action"),
            ("aria-controls", "aria-controls"),
            ("aria-label", "aria-label"),
            ("alt", "alt"),
            ("data-action", "data-action"),
            ("data-rade-token-color", "color"),
            ("data-rade-token-background-color", "background_color"),
            ("data-rade-token-font-family", "font_family"),
            ("data-rade-token-font-weight", "font_weight"),
            ("data-rade-token-margin", "margin"),
            ("data-rade-token-padding", "padding"),
            ("data-rade-token-gap", "gap"),
            ("id", "id"),
            ("class", "class"),
            ("data-testid", "data-testid"),
            ("title", "title"),
        ):
            value = attributes.get(source_key, "").strip()
            if value:
                metadata[target_key] = value
        frame_kind = self._frame_kind("", attributes)
        if frame_kind is not None:
            metadata["frame_kind"] = frame_kind
        return metadata


class TerminalStyler:
    def __init__(self) -> None:
        self._console = Console(width=96) if Console is not None else None

    def emit(self, text: str, *, color: str | None = None, bold: bool = False) -> None:
        if self._console is not None:
            style_parts = [part for part in (color, "bold" if bold else None) if part]
            self._console.print(text, style=" ".join(style_parts) or None)
            return

        prefix = ""
        if bold:
            prefix += ANSI_STYLES["bold"]
        if color:
            prefix += ANSI_STYLES[color]
        suffix = ANSI_RESET if prefix else ""
        print(f"{prefix}{text}{suffix}")


def _escape_xml_attribute(value: Any) -> str:
    return escape(str(value), XML_ATTRIBUTE_ESCAPES)


@dataclass(frozen=True)
class _PositionedNode:
    node: FunctionalNode
    order: int
    x: float
    y: float
    width: float
    height: float


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_raid_visualizer",
        description="Run the RADE alpha demo pipeline.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory where RADE_RECONSTRUCTION.svg will be written.",
    )
    parser.add_argument(
        "--capture-mode",
        choices=("demo", "active-chrome-tab"),
        default="demo",
        help="Source to deconstruct before scrubbing and SVG export.",
    )
    parser.add_argument(
        "--output-name",
        default="RADE_RECONSTRUCTION.svg",
        help="SVG file name written under --output-dir.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.5,
        help="Pause between demo steps.",
    )
    parser.add_argument(
        "--depth",
        type=_positive_int("depth"),
        default=20,
        help="Maximum structural depth collected by the ambient crawler.",
    )
    parser.add_argument(
        "--max-nodes",
        type=_positive_int("max-nodes"),
        default=64,
        help="Maximum DOM nodes parsed for active-chrome-tab structural capture.",
    )
    parser.add_argument(
        "--resolve-computed-style-tokens",
        action="store_true",
        help=(
            "Resolve computed styles via Playwright and inject data-rade-token-* "
            "attributes so Slab 05 token pulse captures brand colors behind CSS vars."
        ),
    )
    parser.add_argument(
        "--emit-figma-bridge-v0-manifest",
        action="store_true",
        help=(
            "Write a deterministic Figma Bridge v0 JSON manifest (including Slab 05 design tokens) "
            "next to the exported SVG."
        ),
    )
    parser.add_argument(
        "--auto-open",
        action="store_true",
        help="Open the generated SVG with the default macOS handler.",
    )
    parser.add_argument(
        "--live-raid-date",
        help="Override the Live Raid date embedded in blueprint metadata.",
    )
    return parser


def _positive_int(field_name: str):
    def _parser(value: str) -> int:
        parsed = int(value)
        if parsed < 1:
            raise argparse.ArgumentTypeError(f"{field_name} must be >= 1")
        return parsed

    return _parser


def _build_demo_tree() -> DemoNode:
    return DemoNode(
        "XCUIElementTypeWindow",
        label="Authorized Target App",
        traits=["window"],
        children=[
            DemoNode(
                "XCUIElementTypeStaticText",
                label="jane.doe@example.com",
                traits=["staticText"],
                bounds={"x": 24, "y": 96, "width": 240, "height": 32},
            ),
            DemoNode(
                "XCUIElementTypeButton",
                label="+1 415 555 0101",
                traits=["button"],
                bounds={"x": 24, "y": 144, "width": 240, "height": 44},
            ),
            DemoNode(
                "XCUIElementTypeStaticText",
                label="Bearer sk_test_12345678",
                traits=["staticText"],
                bounds={"x": 24, "y": 204, "width": 280, "height": 32},
            ),
            DemoNode(
                "XCUIElementTypeStaticText",
                label="SSN 123-45-6789",
                traits=["staticText"],
                bounds={"x": 24, "y": 252, "width": 220, "height": 32},
            ),
            DemoNode(
                "XCUIElementTypeButton",
                label="Continue",
                traits=["button"],
                metadata={"destination": "authorized-demo://continue"},
                bounds={"x": 24, "y": 316, "width": 240, "height": 44},
            ),
        ],
    )


def _run_subprocess(command: Sequence[str], *, error_context: str) -> str:
    completed = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout if completed.stdout.strip() else completed.stderr
    if completed.returncode != 0:
        error_output = output.strip() or "unknown error"
        raise RuntimeError(f"{error_context}: {error_output}")
    return output


def _active_chrome_tab_context() -> ChromeTabContext:
    raw_output = _run_subprocess(
        [
            "osascript",
            "-l",
            "JavaScript",
            "-e",
            (
                "const chrome = Application('Google Chrome');"
                "const window = chrome.windows[0];"
                "const tab = window.activeTab();"
                "console.log(JSON.stringify({title: tab.name(), url: tab.url()}));"
            ),
        ],
        error_context="unable to read active Google Chrome tab",
    ).strip()
    payload = json.loads(raw_output)
    url = str(payload.get("url", "")).strip()
    title = str(payload.get("title", "")).strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    app_name = _app_name_from_host(host)
    screen_token = re.sub(r"[^a-z0-9]+", "-", app_name.lower()).strip("-") or "surface"
    return ChromeTabContext(
        title=title,
        url=url,
        app_name=app_name,
        app_id=f"com.rade.chrome.{screen_token}",
        screen_id=f"{screen_token}-surface",
        screen_name=f"{app_name} Surface",
    )


def _app_name_from_host(host: str) -> str:
    known_names = {
        "airbnb.com": "Airbnb",
        "amazon.com": "Amazon",
        "amazon.com.au": "Amazon",
        "linear.app": "Linear",
        "open.spotify.com": "Spotify",
        "spotify.com": "Spotify",
        "wikipedia.org": "Wikipedia",
    }
    for suffix, app_name in known_names.items():
        if host == suffix or host.endswith(f".{suffix}"):
            return app_name
    if not host:
        return "Chrome"
    primary = host.split(".")[0]
    return primary.replace("-", " ").title()


def _resolve_chrome_binary() -> str:
    candidates = (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    raise RuntimeError("Google Chrome binary not found for headless DOM capture")


def _rendered_dom_from_url(
    url: str,
    *,
    max_nodes: int,
    resolve_computed_style_tokens: bool = False,
) -> str:
    if resolve_computed_style_tokens:
        script_path = (
            Path(__file__).resolve().parents[2]
            / "web"
            / "scripts"
            / "dump_computed_style_tokens_dom.mjs"
        )
        output = _run_subprocess(
            [
                "node",
                str(script_path),
                url,
                str(max_nodes),
            ],
            error_context="unable to capture computed-style DOM from Playwright",
        )
    else:
        chrome_binary = _resolve_chrome_binary()
        output = _run_subprocess(
            [
                chrome_binary,
                "--headless=new",
                "--disable-gpu",
                "--dump-dom",
                url,
            ],
            error_context="unable to capture rendered DOM from Chrome",
        )
    for marker in ("<!DOCTYPE", "<html"):
        index = output.find(marker)
        if index >= 0:
            return output[index:]
    raise RuntimeError("rendered DOM capture did not return HTML")


def _parse_structural_dom(
    dom: str, *, app_name: str, max_depth: int, max_nodes: int = 64
) -> DemoNode:
    parser = StructuralDomParser(
        app_name=app_name,
        max_depth=max_depth,
        max_nodes=max_nodes,
    )
    parser.feed(dom)
    parser.close()
    return parser.root.freeze()


def _count_tree_nodes(root: DemoNode) -> int:
    total = 1
    for child in root.children:
        total += _count_tree_nodes(child)
    return total


def _write_redline_report(
    *,
    output_path: Path,
    context: ChromeTabContext | None,
    last_known_a11y_state: str,
    error: str,
) -> None:
    payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "url": (context.url if context is not None else ""),
        "title": (context.title if context is not None else ""),
        "last_known_a11y_state": last_known_a11y_state,
        "error": error,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _build_chrome_tab_tree(
    max_depth: int = 20,
    max_nodes: int = 64,
    *,
    retry_attempts: int = 3,
    retry_delay_seconds: float = 0.5,
    redline_output_path: Path | None = None,
    resolve_computed_style_tokens: bool = False,
) -> tuple[DemoNode, ChromeTabContext]:
    last_context: ChromeTabContext | None = None
    last_known_a11y_state = "UNKNOWN"
    for attempt in range(1, retry_attempts + 1):
        try:
            context = _active_chrome_tab_context()
            last_context = context
            is_internal_page = context.url.startswith(
                "chrome://"
            ) or context.url.startswith("about:")
            print(
                "[RADE DIAG] State of the Land: "
                f"url={context.url!r} internal_page={is_internal_page}"
            )
            dom = _rendered_dom_from_url(
                context.url,
                max_nodes=max_nodes,
                resolve_computed_style_tokens=resolve_computed_style_tokens,
            )
            tree = _parse_structural_dom(
                dom,
                app_name=context.app_name,
                max_depth=max_depth,
                max_nodes=max_nodes,
            )
            initial_node_count = _count_tree_nodes(tree)
            last_known_a11y_state = "POPULATED" if initial_node_count > 1 else "EMPTY"
            print(
                "[RADE DIAG] A11y Pulse: "
                f"state={last_known_a11y_state} node_count={initial_node_count}"
            )
            if tree.children:
                return tree, context
        except RuntimeError as error:
            if redline_output_path is not None:
                _write_redline_report(
                    output_path=redline_output_path,
                    context=last_context,
                    last_known_a11y_state=last_known_a11y_state,
                    error=str(error),
                )
                print(f"[RADE DIAG] Redline report emitted: {redline_output_path}")
            if attempt >= retry_attempts:
                raise
        if attempt < retry_attempts:
            time.sleep(retry_delay_seconds)

    context = last_context
    assert context is not None
    if redline_output_path is not None:
        _write_redline_report(
            output_path=redline_output_path,
            context=context,
            last_known_a11y_state=last_known_a11y_state,
            error=(
                "active Chrome tab did not yield a structural DOM tree after "
                f"{retry_attempts} attempts"
            ),
        )
        print(f"[RADE DIAG] Redline report emitted: {redline_output_path}")
    raise RuntimeError(
        "active Chrome tab did not yield a structural DOM tree after "
        f"{retry_attempts} attempts: title={context.title!r} url={context.url!r}"
    )


def _node_from_graph_payload(row: dict[str, Any]) -> FunctionalNode:
    data = {k: v for k, v in row.items() if k != "bounding_box"}
    return FunctionalNode(**data)


def _build_graph_from_payload(payload: dict[str, Any]) -> ConstructionGraph:
    nodes = [_node_from_graph_payload(node) for node in payload.get("nodes", [])]
    edges = [FunctionalEdge(**edge) for edge in payload.get("edges", [])]
    return ConstructionGraph(
        app_id=str(payload["app_id"]),
        platform=str(payload["platform"]),
        screen_id=str(payload["screen_id"]),
        screen_name=str(payload["screen_name"]),
        capture_source=str(payload["capture_source"]),
        metadata=dict(payload.get("metadata", {})),
        nodes=nodes,
        edges=edges,
    )


class RadeVectorBridge:
    """Export a scrubbed construction graph as a deterministic SVG."""

    BACKGROUND = "#04110b"
    NODE_STROKE = "#62f2b1"
    PLUMBING_STROKE = "#98ffad"
    CONTAINMENT_STROKE = "#24553e"
    HEADER_TEXT = "#98ffad"
    SUBTITLE_TEXT = "#6fdaa3"
    DETAIL_TEXT = "#8ed8b2"
    LABEL_TEXT = "#ecfff5"
    MONO_FONT = "Menlo, SFMono-Regular, Consolas, monospace"

    def __init__(self, *, live_raid_date: str | None = None) -> None:
        self._live_raid_date = live_raid_date or today_iso_date()

    def export_svg(self, graph: ConstructionGraph, output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        svg = self._render_svg(graph)
        output_path.write_text(svg, encoding="utf-8")
        return output_path

    def _render_svg(self, graph: ConstructionGraph) -> str:
        width = 1400
        row_height = 168
        top_margin = 132
        left_margin = 88
        right_margin = 88
        bottom_margin = 168

        rows: dict[int, list[tuple[int, FunctionalNode]]] = {}
        for index, node in enumerate(graph.nodes):
            rows.setdefault(node.hierarchy_depth, []).append((index, node))

        max_depth = max(rows) if rows else 0
        max_node_height = max(
            (self._node_dimensions(node)[1] for node in graph.nodes),
            default=72.0,
        )
        required_height = top_margin + ((max_depth + 1) * row_height) + max_node_height
        height = max(860, int(required_height + bottom_margin))
        positioned_nodes = self._layout_nodes(
            graph=graph,
            rows=rows,
            width=width,
            height=height,
            row_height=row_height,
            top_margin=top_margin,
            left_margin=left_margin,
            right_margin=right_margin,
        )
        node_lookup = {item.node.node_ref: item for item in positioned_nodes}
        nodes_by_layer: dict[str, list[str]] = {}
        containment_edges_markup: list[str] = []
        plumbing_edges_markup: list[str] = []

        for edge_index, edge in enumerate(graph.edges):
            source = node_lookup.get(edge.source_node_ref)
            target = node_lookup.get(edge.target_node_ref)
            if source is None:
                continue
            if target is None and edge.edge_type != "contains":
                plumbing_edges_markup.append(
                    self._render_open_plumbing_edge(
                        edge=edge,
                        order=edge_index,
                        source=source,
                        width=width,
                        height=height,
                        right_margin=right_margin,
                    )
                )
                continue
            if target is None:
                continue
            rendered_edge = self._render_edge(
                edge=edge,
                order=edge_index,
                source=source,
                target=target,
            )
            if edge.edge_type == "contains":
                containment_edges_markup.append(rendered_edge)
            else:
                plumbing_edges_markup.append(rendered_edge)

        for positioned_node in positioned_nodes:
            nodes_by_layer.setdefault(positioned_node.node.slab_layer, []).append(
                self._render_node(positioned_node)
            )

        title = escape(f"RADE Reconstruction - {graph.screen_name}")
        subtitle = escape(
            f"{graph.app_id} | nodes={len(graph.nodes)} | edges={len(graph.edges)}"
        )
        layer_markup: list[str] = []
        ordered_layers = [
            OS_SITE_LAYER,
            ROOT_LAYER,
            CONTAINERS_LAYER,
            LINKS_EVENTS_LAYER,
            ASSETS_LAYER,
        ]
        for layer in ordered_layers:
            if not nodes_by_layer.get(layer):
                continue
            children = nodes_by_layer[layer]
            if layer == LINKS_EVENTS_LAYER:
                children = [
                    "\n".join(
                        [
                            '<g id="INTERACTIVE_PLUMBING" '
                            'data-rade-dna="nodes|interactive-plumbing" '
                            'data-slab-layer="04" '
                            f'data-slab-layer-label="{_escape_xml_attribute(LINKS_EVENTS_LAYER)}">',
                            *children,
                            "</g>",
                        ]
                    )
                ]
            layer_markup.append(
                self._wrap_layer_group(
                    group_id=f"nodes-{self._slugify(layer)}",
                    rade_dna=f"nodes|{self._slugify(layer)}",
                    slab_layer=layer,
                    children=children,
                )
            )

        return "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                SVG_HEADER_COMMENT,
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
                'role="img" aria-label="RADE reconstruction">',
                self._render_metadata_block(),
                "<defs>",
                '<linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">',
                f'<stop offset="0%" stop-color="{self.BACKGROUND}" />',
                '<stop offset="100%" stop-color="#072116" />',
                "</linearGradient>",
                '<pattern id="minor-grid" width="24" height="24" patternUnits="userSpaceOnUse">',
                '<path d="M 24 0 L 0 0 0 24" fill="none" stroke="#0e261c" stroke-width="1" />',
                "</pattern>",
                '<pattern id="major-grid" width="120" height="120" patternUnits="userSpaceOnUse">',
                '<rect width="120" height="120" fill="url(#minor-grid)" />',
                '<path d="M 120 0 L 0 0 0 120" fill="none" stroke="#153726" stroke-width="1.2" />',
                "</pattern>",
                '<marker id="arrow-plumbing" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">',
                f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{self.PLUMBING_STROKE}" />',
                "</marker>",
                "</defs>",
                f'<rect width="{width}" height="{height}" fill="url(#bg)" />',
                f'<g id="site-grid" data-rade-dna="construction-grid" data-slab-layer="{_escape_xml_attribute(OS_SITE_LAYER)}">',
                f'<rect width="{width}" height="{height}" fill="url(#major-grid)" opacity="0.72" />',
                f'<rect width="{width}" height="{height}" fill="url(#minor-grid)" opacity="0.16" />',
                "</g>",
                f'<g id="drawing-header" data-rade-dna="drawing-header" data-slab-layer="{_escape_xml_attribute(ROOT_LAYER)}">',
                f'<text x="{left_margin}" y="46" font-family="{self.MONO_FONT}" '
                f'font-size="26" fill="{self.HEADER_TEXT}" font-weight="700">{title}</text>',
                f'<text x="{left_margin}" y="74" font-family="{self.MONO_FONT}" '
                f'font-size="13" fill="{self.SUBTITLE_TEXT}">{subtitle}</text>',
                f'<line x1="{left_margin}" y1="92" x2="{width - right_margin}" y2="92" '
                'stroke="#173d2b" stroke-width="1.2" opacity="0.85" />',
                "</g>",
                self._wrap_layer_group(
                    group_id="containment-edges",
                    rade_dna="edges|containment",
                    slab_layer=ROOT_LAYER,
                    children=containment_edges_markup,
                ),
                self._wrap_layer_group(
                    group_id="plumbing-edges",
                    rade_dna="edges|plumbing",
                    slab_layer=LINKS_EVENTS_LAYER,
                    children=plumbing_edges_markup,
                ),
                *layer_markup,
                self._render_legal_footer(
                    width=width,
                    height=height,
                    right_margin=right_margin,
                ),
                "</svg>",
            ]
        )

    def _render_legal_footer(
        self, *, width: int, height: int, right_margin: int
    ) -> str:
        x = width - right_margin
        base_y = height - 72
        return "\n".join(
            [
                f'<g id="rade-legal" data-rade-dna="rade-legal" data-slab-layer="{_escape_xml_attribute(ROOT_LAYER)}">',
                f'<text x="{x}" y="{base_y}" text-anchor="end" font-family="{self.MONO_FONT}" font-size="12" fill="{self.SUBTITLE_TEXT}">{escape(SVG_WATERMARK_TEXT)}</text>',
                f'<text x="{x}" y="{base_y + 18}" text-anchor="end" font-family="{self.MONO_FONT}" font-size="11" fill="{self.DETAIL_TEXT}">5-Slab Taxonomy | Ambient Engine</text>',
                f'<text x="{x}" y="{base_y + 36}" text-anchor="end" font-family="{self.MONO_FONT}" font-size="11" fill="{self.DETAIL_TEXT}">Live Raid: {escape(self._live_raid_date)}</text>',
                "</g>",
            ]
        )

    def _render_metadata_block(self) -> str:
        metadata_lines = [
            f"legal_notice={LEGAL_NOTICE}",
            "attribution=Buildrr89",
            "license=AGPL-3.0-only",
            "systems=5-Slab Taxonomy; Ambient Engine",
            f"watermark={SVG_WATERMARK_TEXT}",
            f"live_raid_date={self._live_raid_date}",
        ]
        return (
            '<metadata id="rade-metadata">'
            f"{escape(' | '.join(metadata_lines))}"
            "</metadata>"
        )

    def _layout_nodes(
        self,
        *,
        graph: ConstructionGraph,
        rows: dict[int, list[tuple[int, FunctionalNode]]],
        width: int,
        height: int,
        row_height: int,
        top_margin: int,
        left_margin: int,
        right_margin: int,
    ) -> list[_PositionedNode]:
        positions: dict[str, list[float]] = {}
        anchors: dict[str, tuple[float, float]] = {}
        nodes_by_ref: dict[str, FunctionalNode] = {}
        order_by_ref: dict[str, int] = {}

        for depth in sorted(rows):
            nodes_at_depth = rows[depth]
            ordered_nodes = sorted(
                nodes_at_depth,
                key=lambda item: (-self._centrality_priority(item[1]), item[0]),
            )
            x_slots = self._center_out_positions(
                count=len(ordered_nodes),
                width=width,
                left_margin=left_margin,
                right_margin=right_margin,
            )
            y = float(top_margin + (depth * row_height))
            for x, (original_index, node) in zip(x_slots, ordered_nodes, strict=False):
                positions[node.node_ref] = [x, y]
                anchors[node.node_ref] = (x, y)
                nodes_by_ref[node.node_ref] = node
                order_by_ref[node.node_ref] = original_index

        node_refs = list(positions)
        edge_lookup = [
            edge
            for edge in graph.edges
            if edge.source_node_ref in positions and edge.target_node_ref in positions
        ]

        for _ in range(96):
            forces = {node_ref: [0.0, 0.0] for node_ref in node_refs}
            for index, left_ref in enumerate(node_refs):
                left_node = nodes_by_ref[left_ref]
                left_width, left_height = self._node_dimensions(left_node)
                left_x, left_y = positions[left_ref]
                for right_ref in node_refs[index + 1 :]:
                    right_node = nodes_by_ref[right_ref]
                    right_width, right_height = self._node_dimensions(right_node)
                    right_x, right_y = positions[right_ref]
                    delta_x = left_x - right_x
                    delta_y = left_y - right_y
                    if abs(delta_x) < 1e-3 and abs(delta_y) < 1e-3:
                        delta_x = 0.01 * (index + 1)
                    distance = math.sqrt((delta_x * delta_x) + (delta_y * delta_y))
                    distance = max(distance, 1.0)
                    preferred_gap = (
                        (max(left_width, right_width) * 0.52)
                        + ((left_height + right_height) * 0.18)
                        + 44.0
                    )
                    overlap = max(preferred_gap - distance, 0.0)
                    repulsion = (
                        6200.0
                        * self._repulsion_weight(left_node)
                        * self._repulsion_weight(right_node)
                    ) / ((distance * distance) + 48.0)
                    push = repulsion + (overlap * 0.48)
                    unit_x = delta_x / distance
                    unit_y = delta_y / distance
                    forces[left_ref][0] += unit_x * push
                    forces[left_ref][1] += unit_y * push * 0.38
                    forces[right_ref][0] -= unit_x * push
                    forces[right_ref][1] -= unit_y * push * 0.38

            for edge in edge_lookup:
                source = positions[edge.source_node_ref]
                target = positions[edge.target_node_ref]
                delta_x = target[0] - source[0]
                delta_y = target[1] - source[1]
                distance = math.sqrt((delta_x * delta_x) + (delta_y * delta_y))
                distance = max(distance, 1.0)
                preferred_distance = 180.0 if edge.edge_type == "contains" else 226.0
                spring_strength = 0.010 if edge.edge_type == "contains" else 0.014
                pull = (distance - preferred_distance) * spring_strength
                unit_x = delta_x / distance
                unit_y = delta_y / distance
                forces[edge.source_node_ref][0] += unit_x * pull
                forces[edge.source_node_ref][1] += unit_y * pull * 0.24
                forces[edge.target_node_ref][0] -= unit_x * pull
                forces[edge.target_node_ref][1] -= unit_y * pull * 0.24

            for node_ref in node_refs:
                node = nodes_by_ref[node_ref]
                anchor_x, anchor_y = anchors[node_ref]
                current_x, current_y = positions[node_ref]
                center_x = width / 2
                forces[node_ref][0] += (anchor_x - current_x) * 0.035
                forces[node_ref][1] += (anchor_y - current_y) * 0.18
                forces[node_ref][0] += (center_x - current_x) * self._center_pull(node)

            for node_ref in node_refs:
                node = nodes_by_ref[node_ref]
                node_width, node_height = self._node_dimensions(node)
                next_x = positions[node_ref][0] + max(
                    min(forces[node_ref][0], 16.0), -16.0
                )
                next_y = positions[node_ref][1] + max(
                    min(forces[node_ref][1], 12.0), -12.0
                )
                positions[node_ref][0] = min(
                    max(next_x, left_margin + (node_width / 2)),
                    width - right_margin - (node_width / 2),
                )
                positions[node_ref][1] = min(
                    max(next_y, top_margin + (node_height / 2)),
                    height - 96 - (node_height / 2),
                )

        return [
            _PositionedNode(
                node=nodes_by_ref[node_ref],
                order=order_by_ref[node_ref],
                x=positions[node_ref][0],
                y=positions[node_ref][1],
                width=self._node_dimensions(nodes_by_ref[node_ref])[0],
                height=self._node_dimensions(nodes_by_ref[node_ref])[1],
            )
            for node_ref in sorted(
                node_refs, key=lambda node_ref: order_by_ref[node_ref]
            )
        ]

    def _render_edge(
        self,
        *,
        edge: FunctionalEdge,
        order: int,
        source: _PositionedNode,
        target: _PositionedNode,
    ) -> str:
        is_plumbing = edge.edge_type != "contains"
        start_x, start_y = self._edge_anchor(source, target)
        end_x, end_y = self._edge_anchor(target, source)
        stroke = self.PLUMBING_STROKE if is_plumbing else self.CONTAINMENT_STROKE
        stroke_width = 2.6 if is_plumbing else 1.2
        opacity = "0.96" if is_plumbing else "0.58"
        dash = "" if is_plumbing else ' stroke-dasharray="8 10"'
        marker = ' marker-end="url(#arrow-plumbing)"' if is_plumbing else ""
        slab_layer = LINKS_EVENTS_LAYER if is_plumbing else ROOT_LAYER
        return "\n".join(
            [
                f'<g id="edge-{order:03d}" data-rade-dna="{_escape_xml_attribute(self._edge_dna(edge))}" '
                f'data-slab-layer="{_escape_xml_attribute(slab_layer)}">',
                f'<path d="{self._edge_path(start_x, start_y, end_x, end_y, is_plumbing=is_plumbing)}" '
                f'fill="none" stroke="{stroke}" stroke-width="{stroke_width:.1f}" opacity="{opacity}" '
                f'stroke-linecap="round"{dash}{marker} />',
                "</g>",
            ]
        )

    def _render_open_plumbing_edge(
        self,
        *,
        edge: FunctionalEdge,
        order: int,
        source: _PositionedNode,
        width: int,
        height: int,
        right_margin: int,
    ) -> str:
        synthetic_target = _PositionedNode(
            node=source.node,
            order=-1,
            x=min(width - right_margin - 56, source.x + 280 + ((order % 2) * 36)),
            y=min(height - 120, source.y + 118 + ((order % 3) * 18)),
            width=20.0,
            height=20.0,
        )
        start_x, start_y = self._edge_anchor(source, synthetic_target)
        end_x = synthetic_target.x
        end_y = synthetic_target.y
        label = escape(
            str(edge.metadata.get("destination_kind") or edge.edge_type).upper()
        )
        return "\n".join(
            [
                f'<g id="edge-{order:03d}" data-rade-dna="{_escape_xml_attribute(self._edge_dna(edge))}" '
                f'data-slab-layer="{_escape_xml_attribute(LINKS_EVENTS_LAYER)}">',
                f'<path d="{self._edge_path(start_x, start_y, end_x, end_y, is_plumbing=True)}" '
                f'fill="none" stroke="{self.PLUMBING_STROKE}" stroke-width="2.6" opacity="0.96" '
                'stroke-linecap="round" marker-end="url(#arrow-plumbing)" />',
                f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="6" fill="{self.BACKGROUND}" '
                f'stroke="{self.PLUMBING_STROKE}" stroke-width="1.8" />',
                f'<text x="{end_x + 14:.1f}" y="{end_y + 4:.1f}" font-family="{self.MONO_FONT}" '
                f'font-size="10" fill="{self.PLUMBING_STROKE}" letter-spacing="0.8">{label}</text>',
                "</g>",
            ]
        )

    def _render_node(self, positioned_node: _PositionedNode) -> str:
        node = positioned_node.node
        x = positioned_node.x
        y = positioned_node.y
        rect_x = x - (positioned_node.width / 2)
        rect_y = y - (positioned_node.height / 2)
        inset_x = rect_x + 10
        inset_y = rect_y + 10
        inset_width = positioned_node.width - 20
        inset_height = positioned_node.height - 20
        title_x = rect_x + 20
        title_y = rect_y + 38
        subtitle_y = title_y + 22
        label = escape(node.label or node.role or node.element_type)
        subtitle = escape(f"{node.role} | {node.structural_fingerprint[:8]}")
        layer_badge = escape(self._layer_badge(node.slab_layer))
        accent = self._accent_for_node(node)
        return "\n".join(
            [
                f'<g id="{_escape_xml_attribute(node.node_ref)}" data-order="{positioned_node.order}" '
                f'data-rade-dna="{_escape_xml_attribute(self._node_dna(node))}" '
                f'data-slab-layer="{_escape_xml_attribute(node.slab_layer)}">',
                f'<rect x="{rect_x:.1f}" y="{rect_y:.1f}" width="{positioned_node.width:.1f}" '
                f'height="{positioned_node.height:.1f}" rx="18" ry="18" fill="{self._fill_for_node(node)}" '
                f'fill-opacity="0.34" stroke="{self.NODE_STROKE}" '
                f'stroke-width="{self._node_stroke_width(node):.1f}" />',
                f'<rect x="{inset_x:.1f}" y="{inset_y:.1f}" width="{inset_width:.1f}" '
                f'height="{inset_height:.1f}" rx="12" ry="12" fill="none" stroke="{accent}" '
                'stroke-width="1" opacity="0.42" />',
                f'<line x1="{rect_x + 18:.1f}" y1="{rect_y + 22:.1f}" '
                f'x2="{rect_x + positioned_node.width - 18:.1f}" y2="{rect_y + 22:.1f}" '
                f'stroke="{accent}" stroke-width="1.2" opacity="0.78" />',
                f'<text x="{rect_x + positioned_node.width - 20:.1f}" y="{rect_y + 18:.1f}" '
                f'text-anchor="end" font-family="{self.MONO_FONT}" font-size="10" '
                f'fill="{self.DETAIL_TEXT}" letter-spacing="1.2">{layer_badge}</text>',
                f'<text x="{title_x:.1f}" y="{title_y:.1f}" font-family="{self.MONO_FONT}" '
                f'font-size="{self._label_font_size(node):.1f}" fill="{self.LABEL_TEXT}" font-weight="700">{label}</text>',
                f'<text x="{title_x:.1f}" y="{subtitle_y:.1f}" font-family="{self.MONO_FONT}" '
                f'font-size="11" fill="{self.DETAIL_TEXT}" letter-spacing="0.4">{subtitle}</text>',
                "</g>",
            ]
        )

    def _wrap_layer_group(
        self,
        *,
        group_id: str,
        rade_dna: str,
        slab_layer: str,
        children: list[str],
    ) -> str:
        return "\n".join(
            [
                f'<g id="{_escape_xml_attribute(group_id)}" '
                f'data-rade-dna="{_escape_xml_attribute(rade_dna)}" '
                f'data-slab-layer="{_escape_xml_attribute(slab_layer)}">',
                *children,
                "</g>",
            ]
        )

    def _center_out_positions(
        self,
        *,
        count: int,
        width: int,
        left_margin: int,
        right_margin: int,
    ) -> list[float]:
        if count <= 1:
            return [width / 2]
        span = width - left_margin - right_margin
        center = width / 2
        gap = span / count
        offsets: list[float] = []
        if count % 2 == 1:
            offsets.append(0.0)
            step = 1
            while len(offsets) < count:
                offsets.extend((-gap * step, gap * step))
                step += 1
        else:
            step = 0
            while len(offsets) < count:
                magnitude = gap * (step + 0.5)
                offsets.extend((-magnitude, magnitude))
                step += 1
        return [center + offset for offset in offsets[:count]]

    def _node_dimensions(self, node: FunctionalNode) -> tuple[float, float]:
        if node.role.lower() == "screen":
            return (356.0, 94.0)
        if node.slab_layer == CONTAINERS_LAYER:
            base_width = 332.0
            base_height = 88.0
            if bool(node.functional_dna.get("structural_frame")):
                return (368.0, 102.0)
            return (base_width, base_height)
        if node.slab_layer == ASSETS_LAYER:
            return (220.0, 56.0)
        if node.slab_layer == LINKS_EVENTS_LAYER:
            return (248.0, 60.0)
        if node.slab_layer == ROOT_LAYER:
            return (300.0, 78.0)
        return (274.0, 68.0)

    def _centrality_priority(self, node: FunctionalNode) -> float:
        priority = 0.0
        if node.role.lower() == "screen":
            priority += 7.0
        if node.slab_layer == CONTAINERS_LAYER:
            priority += 4.2
        if bool(node.functional_dna.get("structural_frame")):
            priority += 2.8
        if node.slab_layer == ROOT_LAYER:
            priority += 2.0
        if node.slab_layer == LINKS_EVENTS_LAYER:
            priority += 0.8
        if node.slab_layer == ASSETS_LAYER:
            priority -= 2.6
        return priority

    def _repulsion_weight(self, node: FunctionalNode) -> float:
        if node.role.lower() == "screen":
            return 1.35
        if node.slab_layer == CONTAINERS_LAYER:
            return 1.25
        if node.slab_layer == ASSETS_LAYER:
            return 0.78
        return 1.0

    def _center_pull(self, node: FunctionalNode) -> float:
        if node.role.lower() == "screen":
            return 0.105
        if node.slab_layer == CONTAINERS_LAYER:
            return 0.078 if bool(node.functional_dna.get("structural_frame")) else 0.062
        if node.slab_layer == ASSETS_LAYER:
            return 0.012
        if node.slab_layer == LINKS_EVENTS_LAYER:
            return 0.024
        return 0.032

    def _edge_anchor(
        self, source: _PositionedNode, target: _PositionedNode
    ) -> tuple[float, float]:
        if target.y > source.y + 8:
            return (source.x, source.y + (source.height / 2) - 10)
        if target.y < source.y - 8:
            return (source.x, source.y - (source.height / 2) + 10)
        if target.x >= source.x:
            return (source.x + (source.width / 2) - 10, source.y)
        return (source.x - (source.width / 2) + 10, source.y)

    def _edge_path(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        *,
        is_plumbing: bool,
    ) -> str:
        if abs(end_y - start_y) < 24:
            bend = 82.0 if is_plumbing else 42.0
            if end_x >= start_x:
                return (
                    f"M {start_x:.1f} {start_y:.1f} "
                    f"C {start_x + bend:.1f} {start_y:.1f}, "
                    f"{end_x - bend:.1f} {end_y:.1f}, {end_x:.1f} {end_y:.1f}"
                )
            return (
                f"M {start_x:.1f} {start_y:.1f} "
                f"C {start_x - bend:.1f} {start_y:.1f}, "
                f"{end_x + bend:.1f} {end_y:.1f}, {end_x:.1f} {end_y:.1f}"
            )
        control_y = (start_y + end_y) / 2
        tension = 44.0 if is_plumbing else 18.0
        return (
            f"M {start_x:.1f} {start_y:.1f} "
            f"C {start_x:.1f} {control_y - tension:.1f}, "
            f"{end_x:.1f} {control_y + tension:.1f}, {end_x:.1f} {end_y:.1f}"
        )

    def _node_dna(self, node: FunctionalNode) -> str:
        dna = node.functional_dna
        slab03_kind = dna.get("slab03_anchor_kind") or node.slab03_anchor_kind

        def _slot(raw: object, default: str) -> str:
            if raw is None:
                text = default
            else:
                text = str(raw).strip() or default
            return text.replace('"', "").replace("|", ":")

        # Fixed first five slots: token 3 is always slab03_anchor_kind.
        slots = [
            _slot(dna.get("instruction_role"), "component"),
            _slot(dna.get("frame_kind"), "node"),
            _slot(slab03_kind, "none"),
            _slot(
                dna.get("pattern_fingerprint") or node.structural_fingerprint, "none"
            ),
            _slot(node.role or node.element_type, "unknown"),
        ]
        token_pulse_id = _slot(dna.get("token_pulse_id"), "none")
        if token_pulse_id != "none":
            slots.append(f"token-pulse:{token_pulse_id}")
        return "|".join(slots)

    def _edge_dna(self, edge: FunctionalEdge) -> str:
        edge_family = "plumbing" if edge.edge_type != "contains" else "containment"
        destination_kind = str(edge.metadata.get("destination_kind") or "none")
        return "|".join((edge_family, edge.edge_type, destination_kind))

    def _layer_badge(self, slab_layer: str) -> str:
        badges = {
            OS_SITE_LAYER: "L01 SITE",
            ROOT_LAYER: "L02 SLAB",
            CONTAINERS_LAYER: "L03 FRAME",
            LINKS_EVENTS_LAYER: "L04 PLUMB",
            ASSETS_LAYER: "L05 DECOR",
        }
        return badges.get(slab_layer, "LXX NODE")

    def _accent_for_node(self, node: FunctionalNode) -> str:
        if node.slab_layer == CONTAINERS_LAYER:
            return "#98ffad"
        if node.slab_layer == LINKS_EVENTS_LAYER:
            return "#77dcb1"
        if node.slab_layer == ASSETS_LAYER:
            return "#43856a"
        return "#5ecb94"

    def _node_stroke_width(self, node: FunctionalNode) -> float:
        if node.role.lower() == "screen":
            return 2.8
        if node.slab_layer == CONTAINERS_LAYER:
            return 2.4
        if node.slab_layer == ASSETS_LAYER:
            return 1.8
        return 2.1

    def _label_font_size(self, node: FunctionalNode) -> float:
        if node.slab_layer == CONTAINERS_LAYER:
            return 17.0
        if node.slab_layer == ASSETS_LAYER:
            return 15.0
        return 16.0

    def _slugify(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

    def _fill_for_node(self, node: FunctionalNode) -> str:
        role = node.role.lower()
        if role == "screen":
            return "#0d2c1d"
        if node.slab_layer == CONTAINERS_LAYER:
            return "#103a26"
        if node.slab_layer == LINKS_EVENTS_LAYER:
            return "#0f2d22"
        if node.slab_layer == ASSETS_LAYER:
            return "#0b1d18"
        return "#112c21"


def _fake_session_factory(
    remote_url: str, capabilities: dict[str, Any]
) -> DemoManagedSession:
    return DemoManagedSession(remote_url=remote_url, capabilities=dict(capabilities))


def _build_scrubbed_graph(
    graph: ConstructionGraph,
) -> tuple[ConstructionGraph, dict[str, Any]]:
    scrubbed_payload, metadata = scrub_payload_with_metadata(graph.to_dict())
    return _build_graph_from_payload(scrubbed_payload), metadata


def _summarize_deep_raid(
    graph: ConstructionGraph,
    *,
    scrub_metadata: dict[str, Any],
    ingest_summary: dict[str, Any],
) -> dict[str, Any]:
    frame_nodes = [
        node
        for node in graph.nodes
        if bool(node.functional_dna.get("structural_frame"))
    ]
    frame_patterns = {
        str(node.functional_dna.get("pattern_fingerprint", "")) for node in frame_nodes
    } - {""}
    plumbing_edges = [edge for edge in graph.edges if edge.edge_type != "contains"]
    destinations = {
        str(edge.metadata.get("destination_ref", ""))
        for edge in plumbing_edges
        if str(edge.metadata.get("destination_ref", "")).strip()
    }
    recognized_frames = sum(
        1
        for node in frame_nodes
        if str(node.functional_dna.get("frame_kind", "")).strip()
    )
    frame_stability = 100
    if frame_nodes:
        frame_stability = int(round((recognized_frames / len(frame_nodes)) * 100))
    return {
        "frame_count": len(frame_nodes),
        "frame_pattern_count": len(frame_patterns),
        "frame_stability": frame_stability,
        "plumbing_edge_count": len(plumbing_edges),
        "destination_count": len(destinations),
        "neutralized_node_count": int(
            scrub_metadata.get(
                "neutralized_nodes", scrub_metadata.get("total_redactions", 0)
            )
        ),
        "pattern_count": int(ingest_summary.get("pattern_count", 0)),
        "repeated_pattern_count": int(ingest_summary.get("pattern_count", 0)),
    }


def _auto_open_artifact(path: Path) -> None:
    subprocess.run(["open", str(path)], check=False)


def run_demo(
    *,
    output_dir: Path,
    sleep_seconds: float = 0.5,
    capture_mode: str = "demo",
    depth: int = 20,
    max_nodes: int = 64,
    output_name: str = "RADE_RECONSTRUCTION.svg",
    auto_open: bool = False,
    live_raid_date: str | None = None,
    resolve_computed_style_tokens: bool = False,
    emit_figma_bridge_v0_manifest: bool = False,
) -> DemoRunResult:
    styler = TerminalStyler()
    if max_nodes > 256:
        print(
            "⚠️ HIGH DENSITY RAID: SVG rendering may impact system performance.",
            file=sys.stderr,
        )
    styler.emit("RADE alpha demo runner", color="magenta", bold=True)
    styler.emit(LEGAL_NOTICE, color="cyan")
    styler.emit(PROJECT_TERMS_NOTICE, color="cyan")
    styler.emit("Authorized surfaces only. No login bypass.", color="cyan")

    screen_name = "Target App"
    screen_id = "raid-demo"
    app_id = "com.example.authorizeddemo"
    capture_notice = "Target App connected on AWS Device Farm demo surface."
    root = _build_demo_tree()
    if capture_mode == "active-chrome-tab":
        redline_path = output_dir / "redline_report.json"
        try:
            root, context = _build_chrome_tab_tree(
                max_depth=depth,
                max_nodes=max_nodes,
                redline_output_path=redline_path,
                resolve_computed_style_tokens=resolve_computed_style_tokens,
            )
            screen_name = context.screen_name
            screen_id = context.screen_id
            app_id = context.app_id
            capture_notice = (
                f"Active Chrome tab mapped to {context.app_name} structural surface."
            )
        except RuntimeError as error:
            capture_notice = (
                "Active Chrome tab capture failed; "
                f"falling back to demo tree. Redline: {redline_path} ({error})"
            )

    orchestrator = RadeOrchestrator(
        app_id=app_id,
        platform="ios",
        session_config=AWSDeviceFarmSessionConfig(
            provider="aws-device-farm-demo",
            platform_name="ios",
            remote_url="https://device-farm.invalid/session",
            session_name="rade-ambient-engine-demo",
            app_identifier="com.example.authorizeddemo",
            device_name="iPhone 15 Pro",
            platform_version="17.0",
            bundle_id="com.example.authorizeddemo",
        ),
        session_factory=_fake_session_factory,
    )

    styler.emit("[1/4] The Raid", color="cyan", bold=True)
    orchestrator.initialize_managed_session()
    graph = orchestrator.collect_from_root(
        root,
        screen_id=screen_id,
        screen_name=screen_name,
        max_depth=depth,
    )
    raw_dom_nodes = _count_tree_nodes(root)
    graph_node_count = len(graph.nodes)
    print(
        f"[RADE] Compression: {raw_dom_nodes} DOM nodes collapsed into "
        f"{graph_node_count} components."
    )
    styler.emit(capture_notice, color="green")
    time.sleep(sleep_seconds)

    styler.emit("[2/4] The Scrubber", color="cyan", bold=True)
    scrubbed_graph, scrub_metadata = _build_scrubbed_graph(graph)
    redacted_items = int(scrub_metadata.get("total_redactions", 0))
    neutralized_node_count = int(
        scrub_metadata.get(
            "neutralized_nodes", scrub_metadata.get("total_redactions", 0)
        )
    )
    styler.emit(
        f"PII NUKED: {redacted_items} item(s) redacted by EdgeShield.",
        color="yellow",
        bold=True,
    )
    time.sleep(sleep_seconds)

    if emit_figma_bridge_v0_manifest:
        bridge_manifest = scrubbed_graph.to_figma_bridge_v0_manifest()
        stem = Path(output_name).with_suffix("").name
        manifest_path = output_dir / f"{stem}.figma_bridge_v0_manifest.json"
        manifest_path.write_text(
            json.dumps(bridge_manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        styler.emit(
            f"Figma Bridge v0 manifest export complete: {manifest_path}",
            color="green",
            bold=True,
        )

    styler.emit("[3/4] The Graph", color="cyan", bold=True)
    ingestor = RadeGraphIngestor(
        driver=DemoNeo4jDriver(),
        connection=Neo4jAuraConfig(
            uri="neo4j://demo.invalid",
            username="demo",
            password="demo",
            database="neo4j",
        ),
    )
    ingest_summary = ingestor.ingest_screen(scrubbed_graph)
    pattern_ids = list(ingest_summary.get("pattern_ids", []))
    primary_pattern_id = pattern_ids[0] if pattern_ids else "unknown"
    new_nodes_created = int(ingest_summary.get("component_count", 0))
    styler.emit(
        f"Neo4j pattern_id={primary_pattern_id} | new_nodes_created={new_nodes_created}",
        color="green",
        bold=True,
    )
    styler.emit(
        "Pattern Deduplication Rate: "
        f"Mapped {int(ingest_summary.get('component_count', 0))} components "
        f"to {int(ingest_summary.get('pattern_count', 0))} unique DNA patterns.",
        color="yellow",
        bold=True,
    )
    deep_raid_summary = _summarize_deep_raid(
        graph,
        scrub_metadata=scrub_metadata,
        ingest_summary=ingest_summary,
    )
    styler.emit(
        f"[RADE] Layer 03: Frame Stability {deep_raid_summary['frame_stability']}%",
        color="green",
        bold=True,
    )
    styler.emit("[RADE] Layer 04: Mapping Plumbing...", color="cyan", bold=True)
    styler.emit(
        "[RADE] Layer 04: "
        f"{deep_raid_summary['plumbing_edge_count']} interactive edges traced "
        f"to {deep_raid_summary['destination_count']} destinations.",
        color="green",
        bold=True,
    )
    styler.emit(
        f"[RADE] EdgeShield: {neutralized_node_count} PII Nodes Neutralized",
        color="yellow",
        bold=True,
    )
    time.sleep(sleep_seconds)

    styler.emit("[4/4] The Bridge", color="cyan", bold=True)
    bridge = RadeVectorBridge(live_raid_date=live_raid_date)
    svg_path = bridge.export_svg(scrubbed_graph, output_dir / output_name)
    styler.emit(f"SVG export complete: {svg_path}", color="green")
    if auto_open:
        _auto_open_artifact(svg_path)
        styler.emit("SVG opened with the default macOS handler.", color="green")
    styler.emit("Demo logs complete.", color="magenta", bold=True)

    return DemoRunResult(
        graph=graph,
        scrubbed_graph=scrubbed_graph,
        redacted_items=redacted_items,
        ingest_summary=ingest_summary,
        deep_raid_summary=deep_raid_summary,
        svg_path=svg_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    clear_terminal()
    emit_terminal_banner(force=True)
    parser = build_parser()
    args = parser.parse_args(argv)
    run_demo(
        output_dir=args.output_dir,
        sleep_seconds=float(args.sleep_seconds),
        capture_mode=str(args.capture_mode),
        depth=int(args.depth),
        max_nodes=int(args.max_nodes),
        output_name=str(args.output_name),
        auto_open=bool(args.auto_open),
        live_raid_date=(
            str(args.live_raid_date) if args.live_raid_date is not None else None
        ),
        resolve_computed_style_tokens=bool(args.resolve_computed_style_tokens),
        emit_figma_bridge_v0_manifest=bool(args.emit_figma_bridge_v0_manifest),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
