# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from src.scrubber.edge_shield import (
    presidio_escalation,
    scrub_payload,
    scrub_payload_with_metadata,
    scrub_text,
)


def test_edge_shield_regex_first_redacts_known_pii() -> None:
    text = "Email jane.doe@example.com or call +1 415 555 0101. SSN 123-45-6789."

    scrubbed = scrub_text(text)

    assert scrubbed == "DATA_SLOT_01"


def test_edge_shield_scrubs_payload_and_returns_metadata() -> None:
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "note": "Meet me at 123-45-6789 with token sk_test_12345678.",
    }

    scrubbed, metadata = scrub_payload_with_metadata(payload)

    assert scrubbed["name"] == "DATA_SLOT_01"
    assert scrubbed["email"] == "DATA_SLOT_02"
    assert scrubbed["note"] == "DATA_SLOT_03"
    assert metadata["total_redactions"] >= 3
    assert metadata["regex_hits"]["email"] >= 1
    assert metadata["neutralized_nodes"] == 0
    assert metadata["is_scrubbed"] is True


def test_edge_shield_presidio_escalation_is_safe_without_dependency() -> None:
    scrubbed, metadata = presidio_escalation(
        "Contact Jane Doe at hello@example.com for support."
    )

    assert scrubbed == "DATA_SLOT_01"
    assert metadata["total_redactions"] >= 1


def test_edge_shield_scrub_payload_preserves_structure() -> None:
    payload = {"screens": [{"name": "Jane Doe", "nodes": [{"label": "Submit"}]}]}

    scrubbed = scrub_payload(payload)

    assert isinstance(scrubbed["screens"], list)
    assert isinstance(scrubbed["screens"][0]["nodes"], list)
    assert scrubbed["screens"][0]["name"] == "DATA_SLOT_01"


def test_edge_shield_counts_neutralized_graph_nodes() -> None:
    payload = {
        "nodes": [
            {"label": "Jane Doe", "price": "$129.00"},
            {"label": "Listing Card", "price": "$189.00"},
        ]
    }

    scrubbed, metadata = scrub_payload_with_metadata(payload)

    assert scrubbed["nodes"][0]["label"] == "DATA_SLOT_01"
    assert scrubbed["nodes"][0]["price"] == "DATA_SLOT_02"
    assert scrubbed["nodes"][1]["price"] == "DATA_SLOT_03"
    assert metadata["neutralized_nodes"] == 2
