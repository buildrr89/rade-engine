# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from src.collectors.web_dom_adapter import (
    _build_payload_from_accessibility_tree,
    _build_payload_from_aria_snapshot,
    derive_app_id_from_url,
)


def test_derive_app_id_from_url_is_stable() -> None:
    assert (
        derive_app_id_from_url("https://developer.mozilla.org/en-US/docs/Web")
        == "web.developer.mozilla.org"
    )


def test_accessibility_tree_converts_to_rade_payload() -> None:
    snapshot = {
        "role": "WebArea",
        "name": "Example Domain",
        "children": [
            {
                "role": "heading",
                "name": "Example Domain",
                "children": [],
            },
            {
                "role": "paragraph",
                "name": "This domain is for use in illustrative examples.",
                "children": [],
            },
            {
                "role": "link",
                "name": "More information...",
                "children": [],
            },
        ],
    }

    payload = _build_payload_from_accessibility_tree(
        snapshot, "https://example.com/", "Example Domain"
    )

    assert payload["project_name"] == "Example Domain"
    assert payload["platform"] == "web"
    assert len(payload["screens"]) == 1

    screen = payload["screens"][0]
    assert screen["screen_name"] == "Example Domain"
    assert screen["screen_id"] == "example-com"

    elements = screen["elements"]
    assert elements[0]["element_id"] == "screen-root"
    assert elements[0]["role"] == "screen"
    assert elements[0]["child_count"] == 3

    heading = next(
        element for element in elements if element["element_id"] == "heading-1"
    )
    assert heading["label"] == "Example Domain"
    assert heading["slab_layer"] == "05. Assets (The Decor)"
    assert heading["interactive"] is False

    link = next(element for element in elements if element["element_id"] == "link-3")
    assert link["label"] == "More information..."
    assert link["slab_layer"] == "04. Links/Events (Wires & Plumbing)"
    assert link["interactive"] is True
    assert link["parent_id"] == "screen-root"


def test_aria_snapshot_converts_to_rade_payload() -> None:
    snapshot = """
    - heading "Example Domain" [level=1]
    - paragraph: This domain is for use in illustrative examples.
    - link "More information..."
    """

    payload = _build_payload_from_aria_snapshot(
        snapshot, "https://example.com/", "Example Domain"
    )

    screen = payload["screens"][0]
    elements = screen["elements"]

    assert screen["screen_id"] == "example-com"
    assert elements[0]["child_count"] == 3

    paragraph = next(
        element for element in elements if element["element_id"] == "paragraph-2"
    )
    assert paragraph["label"] == "This domain is for use in illustrative examples."

    link = next(element for element in elements if element["element_id"] == "link-3")
    assert link["interactive"] is True
