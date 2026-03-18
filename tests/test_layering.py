from __future__ import annotations

from src.core.layering import infer_slab_layer


def test_layering_respects_explicit_layer():
    assert (
        infer_slab_layer(
            {"slab_layer": "fitout", "element_type": "text", "role": "text"}
        )
        == "fitout"
    )


def test_layering_infers_systems_for_interactive_controls():
    assert (
        infer_slab_layer(
            {
                "element_type": "button",
                "role": "button",
                "interactive": True,
                "text_present": True,
            }
        )
        == "systems"
    )


def test_layering_infers_foundation_for_screen_shell():
    assert (
        infer_slab_layer(
            {"element_type": "container", "role": "screen", "hierarchy_depth": 0}
        )
        == "foundation"
    )
