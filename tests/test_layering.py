# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from src.core.layering import (
    CONTAINERS_LAYER,
    LINKS_EVENTS_LAYER,
    OS_SITE_LAYER,
    infer_slab_layer,
)


def test_layering_respects_explicit_layer():
    assert (
        infer_slab_layer(
            {
                "slab_layer": LINKS_EVENTS_LAYER,
                "element_type": "text",
                "role": "text",
            }
        )
        == LINKS_EVENTS_LAYER
    )


def test_layering_infers_containers_for_interactive_controls():
    assert (
        infer_slab_layer(
            {
                "element_type": "button",
                "role": "button",
                "interactive": True,
                "text_present": True,
            }
        )
        == CONTAINERS_LAYER
    )


def test_layering_infers_os_site_for_screen_shell():
    assert (
        infer_slab_layer(
            {"element_type": "container", "role": "screen", "hierarchy_depth": 0}
        )
        == OS_SITE_LAYER
    )
