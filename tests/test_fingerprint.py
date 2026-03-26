# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from src.core.fingerprint import fingerprint_node
from src.core.layering import CONTAINERS_LAYER


def test_fingerprint_ignores_labels_but_keeps_structure():
    base = {
        "platform": "ios",
        "element_type": "button",
        "slab_layer": CONTAINERS_LAYER,
        "role": "button",
        "interactive": True,
        "visible": True,
        "hierarchy_depth": 1,
        "child_count": 0,
        "text_present": True,
        "traits": ["primary"],
    }
    first = dict(base, label="Start scan")
    second = dict(base, label="View details")

    assert fingerprint_node(first) == fingerprint_node(second)


def test_fingerprint_changes_for_different_structure():
    first = {
        "platform": "ios",
        "element_type": "button",
        "slab_layer": CONTAINERS_LAYER,
        "role": "button",
        "interactive": True,
        "visible": True,
        "hierarchy_depth": 1,
        "child_count": 0,
        "text_present": True,
        "traits": ["primary"],
    }
    second = dict(first, element_type="link", role="link")

    assert fingerprint_node(first) != fingerprint_node(second)
