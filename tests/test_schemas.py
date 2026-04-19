# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from src.core.schemas import ValidationError, validate_project_payload

from tests.helpers import load_fixture


def _assert_validation_error(payload, expected_message: str) -> None:
    try:
        validate_project_payload(payload)
    except ValidationError as error:
        assert expected_message in str(error)
        return
    raise AssertionError("Expected ValidationError")


def test_schema_rejects_duplicate_screen_ids():
    payload = load_fixture()
    payload["screens"][1]["screen_id"] = payload["screens"][0]["screen_id"]

    _assert_validation_error(payload, "duplicate 'screen_id'")


def test_schema_rejects_duplicate_element_ids_within_a_screen():
    payload = load_fixture()
    payload["screens"][0]["elements"][1]["element_id"] = payload["screens"][0][
        "elements"
    ][0]["element_id"]

    _assert_validation_error(payload, "duplicate 'element_id'")


def test_schema_rejects_unknown_parent_reference():
    payload = load_fixture()
    payload["screens"][0]["elements"][1]["parent_id"] = "missing-parent"

    _assert_validation_error(payload, "references unknown element")


def test_schema_rejects_self_parent_reference():
    payload = load_fixture()
    payload["screens"][0]["elements"][1]["parent_id"] = payload["screens"][0][
        "elements"
    ][1]["element_id"]

    _assert_validation_error(payload, "must reference a different element")


def test_schema_rejects_non_string_label():
    payload = load_fixture()
    payload["screens"][0]["elements"][0]["label"] = 123

    _assert_validation_error(payload, "'label' must be a string")


def test_schema_rejects_non_string_traits():
    payload = load_fixture()
    payload["screens"][0]["elements"][0]["traits"] = ["shell", 123]

    _assert_validation_error(payload, "'traits[1]' must be a string")


def test_schema_rejects_invalid_bounds_and_negative_integers():
    payload = load_fixture()
    payload["screens"][0]["elements"][0]["bounds"] = [0, 1, 2]

    _assert_validation_error(payload, "array of four numbers")

    payload = load_fixture()
    payload["screens"][0]["elements"][0]["hierarchy_depth"] = -1
    _assert_validation_error(payload, "zero or greater")


def test_schema_rejects_legacy_slab_labels():
    payload = load_fixture()
    payload["screens"][0]["elements"][0]["slab_layer"] = "foundation"

    _assert_validation_error(payload, "'slab_layer' must be one of")
