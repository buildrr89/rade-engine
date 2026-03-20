# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from src.core.compliance import SVG_HEADER_COMMENT, SVG_WATERMARK_TEXT
from src.core.layering import ASSETS_LAYER, CONTAINERS_LAYER, OS_SITE_LAYER
from src.demo.run_raid_visualizer import (
    ChromeTabContext,
    DemoNode,
    RadeVectorBridge,
    main,
    run_demo,
)
from src.engine.rade_orchestrator import (
    ConstructionGraph,
    FunctionalEdge,
    FunctionalNode,
)


def test_demo_runner_writes_svg_and_reports_redactions(tmp_path) -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        result = run_demo(
            output_dir=tmp_path,
            sleep_seconds=0.0,
            live_raid_date="2026-03-21",
        )

    output = buffer.getvalue()
    svg_path = tmp_path / "RADE_RECONSTRUCTION.svg"

    assert svg_path.exists()
    assert result.svg_path == svg_path
    assert result.redacted_items >= 4
    assert result.ingest_summary["component_count"] >= 1
    assert result.deep_raid_summary["plumbing_edge_count"] >= 1
    assert "PII NUKED" in output
    assert "Neo4j pattern_id=" in output
    assert "Pattern Deduplication Rate:" in output
    assert "[RADE] Layer 03: Frame Stability" in output
    assert "[RADE] Layer 04: Mapping Plumbing..." in output
    assert "[RADE] EdgeShield:" in output
    assert "RADE Lead Architect View Demo Runner" in output


def test_demo_runner_visual_consistency_against_golden_svg(tmp_path) -> None:
    with redirect_stdout(io.StringIO()):
        run_demo(
            output_dir=tmp_path,
            sleep_seconds=0.0,
            live_raid_date="2026-03-21",
        )

    generated_svg = tmp_path / "RADE_RECONSTRUCTION.svg"
    golden_svg = Path("tests/fixtures/golden_raid.svg")

    assert _svg_structure(generated_svg) == _svg_structure(golden_svg)


def test_demo_runner_svg_is_illustrator_ready(tmp_path) -> None:
    with redirect_stdout(io.StringIO()):
        result = run_demo(
            output_dir=tmp_path,
            sleep_seconds=0.0,
            live_raid_date="2026-03-21",
        )

    svg_text = result.svg_path.read_text(encoding="utf-8")
    root = ET.fromstring(svg_text)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    groups = root.findall(".//svg:g", namespace)
    assert groups
    assert all("data-rade-dna" in group.attrib for group in groups)
    assert all("data-slab-layer" in group.attrib for group in groups)
    assert SVG_HEADER_COMMENT in svg_text
    metadata_block = root.find(".//svg:metadata[@id='rade-metadata']", namespace)
    assert metadata_block is not None
    assert SVG_WATERMARK_TEXT in (metadata_block.text or "")

    background_stop = root.find(
        ".//svg:linearGradient[@id='bg']/svg:stop[@offset='0%']",
        namespace,
    )
    assert background_stop is not None
    assert background_stop.attrib["stop-color"] == "#04110b"

    plumbing_paths = root.findall(".//svg:g[@id='plumbing-edges']//svg:path", namespace)
    assert plumbing_paths
    assert all(path.attrib["stroke"] == "#98ffad" for path in plumbing_paths)

    root_node_rect = root.find(".//svg:g[@id='raid-demo#abfff1af']/svg:rect", namespace)
    assert root_node_rect is not None
    assert root_node_rect.attrib["stroke"] == "#62f2b1"

    legal_group = root.find(".//svg:g[@id='rade-legal']", namespace)
    assert legal_group is not None
    assert any(
        (text.text or "") == SVG_WATERMARK_TEXT
        for text in legal_group.findall("svg:text", namespace)
    )
    assert any("Live Raid: 2026-03-21" in (text.text or "") for text in legal_group)


def test_demo_runner_main_returns_zero(tmp_path) -> None:
    with patch("src.core.compliance.os.system") as mocked_clear:
        with redirect_stdout(io.StringIO()):
            exit_code = main(["--output-dir", str(tmp_path), "--sleep-seconds", "0"])

    mocked_clear.assert_called_once()
    assert exit_code == 0


def test_vector_bridge_centralizes_frames_over_decor() -> None:
    bridge = RadeVectorBridge()
    graph = ConstructionGraph(
        app_id="com.example.arch",
        platform="ios",
        screen_id="arch-test",
        screen_name="Architect Test",
        capture_source="accessibility_tree",
        nodes=[
            FunctionalNode(
                node_ref="arch-test#root",
                parent_node_ref=None,
                element_id="root",
                parent_id=None,
                screen_id="arch-test",
                screen_name="Architect Test",
                platform="ios",
                source="accessibility_tree",
                element_type="screen",
                role="screen",
                label="Architect Test",
                accessibility_identifier=None,
                interactive=False,
                visible=True,
                bounds=None,
                hierarchy_depth=0,
                child_count=2,
                text_present=True,
                traits=["window"],
                slab_layer=OS_SITE_LAYER,
                structural_fingerprint="root0001",
                functional_dna={"instruction_role": "component"},
            ),
            FunctionalNode(
                node_ref="arch-test#frame",
                parent_node_ref="arch-test#root",
                element_id="frame",
                parent_id="root",
                screen_id="arch-test",
                screen_name="Architect Test",
                platform="ios",
                source="accessibility_tree",
                element_type="button",
                role="button",
                label="Primary Frame",
                accessibility_identifier=None,
                interactive=True,
                visible=True,
                bounds=None,
                hierarchy_depth=1,
                child_count=0,
                text_present=True,
                traits=["button"],
                slab_layer=CONTAINERS_LAYER,
                structural_fingerprint="frame0001",
                functional_dna={
                    "instruction_role": "frame",
                    "structural_frame": True,
                    "pattern_fingerprint": "frame-pattern",
                },
            ),
            FunctionalNode(
                node_ref="arch-test#decor",
                parent_node_ref="arch-test#root",
                element_id="decor",
                parent_id="root",
                screen_id="arch-test",
                screen_name="Architect Test",
                platform="ios",
                source="accessibility_tree",
                element_type="image",
                role="image",
                label="Decor Asset",
                accessibility_identifier=None,
                interactive=False,
                visible=True,
                bounds=None,
                hierarchy_depth=1,
                child_count=0,
                text_present=True,
                traits=["image"],
                slab_layer=ASSETS_LAYER,
                structural_fingerprint="decor0001",
                functional_dna={
                    "instruction_role": "component",
                    "pattern_fingerprint": "decor-pattern",
                },
            ),
        ],
        edges=[
            FunctionalEdge(
                source_node_ref="arch-test#root",
                target_node_ref="arch-test#frame",
                edge_type="contains",
                screen_id="arch-test",
                screen_name="Architect Test",
                metadata={},
            ),
            FunctionalEdge(
                source_node_ref="arch-test#root",
                target_node_ref="arch-test#decor",
                edge_type="contains",
                screen_id="arch-test",
                screen_name="Architect Test",
                metadata={},
            ),
        ],
    )

    root = ET.fromstring(bridge._render_svg(graph))
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    frame_rect = root.find(".//svg:g[@id='arch-test#frame']/svg:rect", namespace)
    decor_rect = root.find(".//svg:g[@id='arch-test#decor']/svg:rect", namespace)

    assert frame_rect is not None
    assert decor_rect is not None

    frame_width = float(frame_rect.attrib["width"])
    decor_width = float(decor_rect.attrib["width"])
    frame_center_x = float(frame_rect.attrib["x"]) + (frame_width / 2)
    decor_center_x = float(decor_rect.attrib["x"]) + (decor_width / 2)

    assert frame_width > decor_width
    assert abs(frame_center_x - 700.0) < abs(decor_center_x - 700.0)


def test_demo_runner_can_render_active_chrome_tab_structurally(tmp_path) -> None:
    def fake_chrome_tree() -> tuple[DemoNode, ChromeTabContext]:
        return (
            DemoNode(
                "web_surface_window",
                label="Spotify Surface",
                traits=["window"],
                children=[
                    DemoNode("navigation", label="Navigation", traits=["navigation"]),
                    DemoNode(
                        "main_container",
                        label="Main Content",
                        traits=["container", "main"],
                        children=[
                            DemoNode("heading_text", label="Heading", traits=["text"]),
                            DemoNode(
                                "button",
                                label="Button",
                                traits=["button"],
                                metadata={"destination": "/play"},
                            ),
                            DemoNode(
                                "link",
                                label="Link",
                                traits=["navigation"],
                                metadata={"href": "/discover"},
                            ),
                        ],
                    ),
                ],
            ),
            ChromeTabContext(
                title="Spotify - Web Player: Music for everyone",
                url="https://open.spotify.com/",
                app_name="Spotify",
                app_id="com.rade.chrome.spotify",
                screen_id="spotify-surface",
                screen_name="Spotify Surface",
            ),
        )

    opened: list[Path] = []

    buffer = io.StringIO()
    with patch(
        "src.demo.run_raid_visualizer._build_chrome_tab_tree",
        fake_chrome_tree,
    ):
        with patch(
            "src.demo.run_raid_visualizer._auto_open_artifact",
            lambda path: opened.append(path),
        ):
            with redirect_stdout(buffer):
                result = run_demo(
                    output_dir=tmp_path,
                    sleep_seconds=0.0,
                    capture_mode="active-chrome-tab",
                    output_name="PRO_TECH_RECONSTRUCTION.svg",
                    auto_open=True,
                    live_raid_date="2026-03-21",
                )

    output = buffer.getvalue()
    svg_text = result.svg_path.read_text(encoding="utf-8")

    assert result.svg_path == tmp_path / "PRO_TECH_RECONSTRUCTION.svg"
    assert result.svg_path.exists()
    assert opened == [result.svg_path]
    assert "Active Chrome tab mapped to Spotify structural surface." in output
    assert "Pattern Deduplication Rate:" in output
    assert "[RADE] Layer 04: Mapping Plumbing..." in output
    assert "Spotify - Web Player" not in svg_text
    assert "Navigation" in svg_text
    assert "Main Content" in svg_text


def _svg_structure(
    path: Path,
) -> tuple[str, tuple[tuple[str, tuple[tuple[str, str], ...], tuple], ...]]:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    return _element_structure(root)


def _element_structure(
    element: ET.Element,
) -> tuple[str, tuple[tuple[str, str], ...], tuple]:
    return (
        _local_name(element.tag),
        tuple(
            sorted((_local_name(name), value) for name, value in element.attrib.items())
        ),
        tuple(_element_structure(child) for child in list(element)),
    )


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag
