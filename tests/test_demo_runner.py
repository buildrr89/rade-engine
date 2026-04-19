# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import io
import json
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import pytest
from src.core.compliance import SVG_HEADER_COMMENT, SVG_WATERMARK_TEXT
from src.core.layering import ASSETS_LAYER, CONTAINERS_LAYER, OS_SITE_LAYER
from src.demo.run_raid_visualizer import (
    ChromeTabContext,
    DemoNode,
    RadeVectorBridge,
    StructuralDomParser,
    _app_name_from_host,
    _build_chrome_tab_tree,
    _count_tree_nodes,
    _parse_structural_dom,
    main,
    run_demo,
)
from src.engine.rade_orchestrator import (
    ConstructionGraph,
    FunctionalEdge,
    FunctionalNode,
    RadeOrchestrator,
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
    assert "RADE alpha demo runner" in output


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
    plumbing_group = root.find(".//svg:g[@id='INTERACTIVE_PLUMBING']", namespace)
    assert plumbing_group is not None
    assert plumbing_group.attrib["data-slab-layer"] == "04"

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
            exit_code = main(
                [
                    "--output-dir",
                    str(tmp_path),
                    "--sleep-seconds",
                    "0",
                    "--depth",
                    "5",
                ]
            )

    mocked_clear.assert_called_once()
    assert exit_code == 0


def test_structural_dom_parser_promotes_accessible_labels_and_decor() -> None:
    parser = StructuralDomParser(app_name="Test App", max_depth=5)
    parser.feed("""
        <main>
          <button aria-label="Close"></button>
          <img class="hero-image" alt="Hero Artwork" />
          <svg id="site-logo" aria-hidden="true"></svg>
        </main>
        """)
    parser.close()

    root = parser.root.freeze()
    main_container = root.children[0]
    labels = [child.label for child in main_container.children]
    asset_nodes = [
        child
        for child in main_container.children
        if child.metadata.get("slab_layer") == ASSETS_LAYER
    ]

    assert "Close Button" in labels
    assert any(child.label == "Hero Artwork" for child in asset_nodes)
    assert any(child.label == "Site Logo" for child in asset_nodes)


def test_structural_dom_parser_depth_limit_skips_deeper_controls() -> None:
    parser = StructuralDomParser(app_name="Test App", max_depth=1)
    parser.feed("""
        <main>
          <section>
            <button aria-label="Close"></button>
          </section>
        </main>
        """)
    parser.close()

    root = parser.root.freeze()
    assert len(root.children) == 1
    assert root.children[0].label == "Main Content"
    assert root.children[0].children == []


def test_token_pulse_captures_inline_style_from_structural_parser() -> None:
    parser = StructuralDomParser(app_name="Test App", max_depth=5, max_nodes=20)
    parser.feed("""
    <main>
      <button
        aria-label="Styled"
        style="color: rgb(255, 0, 0); padding: 16px; font-family: IBM Plex Sans; font-weight: 600;"
      >
        X
      </button>
    </main>
    """)
    parser.close()

    orch = RadeOrchestrator(app_id="com.example.web", platform="web")
    graph = orch.collect_from_root(
        parser.root.freeze(),
        screen_id="home",
        screen_name="Home",
        max_depth=5,
    )

    styled_nodes = [n for n in graph.nodes if n.functional_dna.get("token_pulse_id")]
    assert len(styled_nodes) == 1

    design_tokens = styled_nodes[0].functional_dna["design_tokens"]
    assert design_tokens["color_tokens"] == ["color:#ff0000"]
    assert design_tokens["spacing_tokens"] == ["padding:16px"]
    assert design_tokens["typography_tokens"] == [
        "font-family:ibm plex sans",
        "font-weight:600",
    ]


def test_parse_structural_dom_respects_max_nodes() -> None:
    buttons = "".join(f'<button aria-label="B{i}"></button>' for i in range(30))
    dom = f"<!DOCTYPE html><html><body><main>{buttons}</main></body></html>"
    tree_full = _parse_structural_dom(
        dom, app_name="Test App", max_depth=10, max_nodes=64
    )
    tree_limited = _parse_structural_dom(
        dom, app_name="Test App", max_depth=10, max_nodes=8
    )
    assert _count_tree_nodes(tree_full) > _count_tree_nodes(tree_limited)
    assert _count_tree_nodes(tree_limited) <= 8


def test_run_demo_emits_compression_diagnostic(capsys, tmp_path) -> None:
    run_demo(
        output_dir=tmp_path,
        sleep_seconds=0.0,
        live_raid_date="2026-03-21",
    )
    out = capsys.readouterr().out
    assert "[RADE] Compression:" in out
    assert "DOM nodes collapsed into" in out


def test_run_demo_emits_high_density_warning_on_stderr(capsys, tmp_path) -> None:
    with redirect_stdout(io.StringIO()):
        run_demo(
            output_dir=tmp_path,
            sleep_seconds=0.0,
            max_nodes=300,
            live_raid_date="2026-03-21",
        )
    captured = capsys.readouterr()
    assert (
        "⚠️ HIGH DENSITY RAID: SVG rendering may impact system performance."
        in captured.err
    )


def test_parser_decor_asset_produces_slab_05_svg_layer(tmp_path) -> None:
    parser = StructuralDomParser(app_name="Test App", max_depth=5)
    parser.feed("""
        <main>
          <h1 title="Overview"></h1>
          <button aria-label="Close"></button>
          <img class="hero-image" alt="Hero Artwork" />
        </main>
        """)
    parser.close()

    orchestrator = RadeOrchestrator(app_id="com.example.web", platform="web")
    graph = orchestrator.collect_from_root(
        parser.root.freeze(),
        screen_id="home",
        screen_name="Home",
        max_depth=5,
    )
    bridge = RadeVectorBridge(live_raid_date="2026-03-21")
    svg_path = bridge.export_svg(graph, tmp_path / "decor.svg")
    svg_text = svg_path.read_text(encoding="utf-8")

    assert any(node.label == "Close Button" for node in graph.nodes)
    assert any(
        node.label == "Hero Artwork" and node.slab_layer == ASSETS_LAYER
        for node in graph.nodes
    )
    assert 'data-slab-layer="05. Assets (The Decor)"' in svg_text


def test_vector_bridge_node_dna_includes_slab03_anchor_kind() -> None:
    bridge = RadeVectorBridge()
    node = FunctionalNode(
        node_ref="t#1",
        parent_node_ref=None,
        element_id="1",
        parent_id=None,
        screen_id="s",
        screen_name="S",
        platform="ios",
        source="x",
        element_type="div",
        role="button",
        label="X",
        accessibility_identifier=None,
        interactive=True,
        visible=True,
        bounds=[0, 0, 10, 10],
        hierarchy_depth=1,
        child_count=0,
        text_present=False,
        slab03_anchor_kind="visual:vbox-contained",
        structural_fingerprint="abc12345",
        functional_dna={
            "instruction_role": "component",
            "frame_kind": "sidebar",
        },
    )
    assert bridge._node_dna(node) == (
        "component|sidebar|visual:vbox-contained|abc12345|button"
    )


def test_vector_bridge_node_dna_appends_token_pulse_when_present() -> None:
    bridge = RadeVectorBridge()
    node = FunctionalNode(
        node_ref="t#2",
        parent_node_ref=None,
        element_id="2",
        parent_id=None,
        screen_id="s",
        screen_name="S",
        platform="ios",
        source="x",
        element_type="div",
        role="button",
        label="X",
        accessibility_identifier=None,
        interactive=True,
        visible=True,
        bounds=[0, 0, 10, 10],
        hierarchy_depth=1,
        child_count=0,
        text_present=False,
        slab03_anchor_kind="visual:vbox-contained",
        structural_fingerprint="abc12345",
        functional_dna={
            "instruction_role": "component",
            "frame_kind": "sidebar",
            "token_pulse_id": "pulse1234",
        },
    )
    assert bridge._node_dna(node) == (
        "component|sidebar|visual:vbox-contained|abc12345|button|token-pulse:pulse1234"
    )


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
    def fake_chrome_tree(
        max_depth: int = 20,
        max_nodes: int = 64,
        *,
        resolve_computed_style_tokens: bool = False,
        redline_output_path: Path | None = None,
    ) -> tuple[DemoNode, ChromeTabContext]:
        assert max_depth == 20
        assert redline_output_path is not None
        assert resolve_computed_style_tokens is False
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


def test_build_chrome_tab_tree_retries_after_empty_structural_parse() -> None:
    context = ChromeTabContext(
        title="Wikipedia, the free encyclopedia",
        url="https://en.wikipedia.org/wiki/Main_Page",
        app_name="Wikipedia",
        app_id="com.rade.chrome.wikipedia",
        screen_id="wikipedia-surface",
        screen_name="Wikipedia Surface",
    )
    dom_attempts = iter(
        (
            "<!DOCTYPE html><html><head></head><body></body></html>",
            """
            <!DOCTYPE html>
            <html>
              <body>
                <main>
                  <button aria-label="Close"></button>
                </main>
              </body>
            </html>
            """,
        )
    )

    with patch(
        "src.demo.run_raid_visualizer._active_chrome_tab_context",
        return_value=context,
    ):
        with patch(
            "src.demo.run_raid_visualizer._rendered_dom_from_url",
            side_effect=lambda url, **_: next(dom_attempts),
        ) as mocked_dump_dom:
            with patch("src.demo.run_raid_visualizer.time.sleep") as mocked_sleep:
                tree, returned_context = _build_chrome_tab_tree(
                    max_depth=8,
                    retry_attempts=2,
                    retry_delay_seconds=0.0,
                )

    assert returned_context == context
    assert mocked_dump_dom.call_count == 2
    mocked_sleep.assert_called_once_with(0.0)
    assert len(tree.children) == 1
    assert tree.children[0].label == "Main Content"
    assert tree.children[0].children[0].label == "Close Button"


def test_build_chrome_tab_tree_retries_after_runtime_error() -> None:
    context = ChromeTabContext(
        title="Wikipedia, the free encyclopedia",
        url="https://en.wikipedia.org/wiki/Main_Page",
        app_name="Wikipedia",
        app_id="com.rade.chrome.wikipedia",
        screen_id="wikipedia-surface",
        screen_name="Wikipedia Surface",
    )
    dom_attempts = iter(
        (
            """
            <!DOCTYPE html>
            <html>
              <body>
                <main>
                  <button aria-label="Close"></button>
                </main>
              </body>
            </html>
            """,
        )
    )

    call_count = {"value": 0}

    def _rendered_dom_with_transient_error(url: str, **_: object) -> str:
        call_count["value"] += 1
        if call_count["value"] == 1:
            raise RuntimeError("temporary chrome capture error")
        return next(dom_attempts)

    with patch(
        "src.demo.run_raid_visualizer._active_chrome_tab_context",
        return_value=context,
    ):
        with patch(
            "src.demo.run_raid_visualizer._rendered_dom_from_url",
            side_effect=_rendered_dom_with_transient_error,
        ) as mocked_dump_dom:
            with patch("src.demo.run_raid_visualizer.time.sleep") as mocked_sleep:
                tree, returned_context = _build_chrome_tab_tree(
                    max_depth=8,
                    retry_attempts=2,
                    retry_delay_seconds=0.0,
                )

    assert returned_context == context
    assert mocked_dump_dom.call_count == 2
    mocked_sleep.assert_called_once_with(0.0)
    assert len(tree.children) == 1
    assert tree.children[0].label == "Main Content"
    assert tree.children[0].children[0].label == "Close Button"


def test_build_chrome_tab_tree_writes_redline_on_exhausted_failure(tmp_path) -> None:
    context = ChromeTabContext(
        title="Locked Surface",
        url="chrome://settings/",
        app_name="Chrome",
        app_id="com.rade.chrome.chrome",
        screen_id="chrome-surface",
        screen_name="Chrome Surface",
    )
    redline_path = tmp_path / "redline_report.json"

    with patch(
        "src.demo.run_raid_visualizer._active_chrome_tab_context",
        return_value=context,
    ):
        with patch(
            "src.demo.run_raid_visualizer._rendered_dom_from_url",
            side_effect=RuntimeError("capture blocked"),
        ):
            with patch("src.demo.run_raid_visualizer.time.sleep"):
                with pytest.raises(RuntimeError):
                    _build_chrome_tab_tree(
                        max_depth=8,
                        retry_attempts=2,
                        retry_delay_seconds=0.0,
                        redline_output_path=redline_path,
                    )

    payload = json.loads(redline_path.read_text(encoding="utf-8"))
    assert payload["url"] == "chrome://settings/"
    assert payload["title"] == "Locked Surface"
    assert payload["last_known_a11y_state"] in {"UNKNOWN", "EMPTY"}
    assert "capture blocked" in payload["error"]


def test_run_demo_active_chrome_falls_back_with_redline_notice(tmp_path) -> None:
    buffer = io.StringIO()
    with patch(
        "src.demo.run_raid_visualizer._build_chrome_tab_tree",
        side_effect=RuntimeError("capture blocked"),
    ):
        with redirect_stdout(buffer):
            result = run_demo(
                output_dir=tmp_path,
                sleep_seconds=0.0,
                capture_mode="active-chrome-tab",
                output_name="fallback.svg",
                live_raid_date="2026-03-21",
            )

    output = buffer.getvalue()
    assert result.svg_path.exists()
    assert "falling back to demo tree" in output
    assert "redline_report.json" in output


def test_app_name_from_host_handles_common_www_and_wiki_hosts() -> None:
    assert _app_name_from_host("www.amazon.com.au") == "Amazon"
    assert _app_name_from_host("en.wikipedia.org") == "Wikipedia"


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
