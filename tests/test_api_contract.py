# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import io
import json
from pathlib import Path
from wsgiref.util import setup_testing_defaults

from src.api.app import app

FIXTURE_PATH = Path("examples/sample_ios_output.json")


def _call_wsgi(path: str, method: str = "GET", body: bytes = b""):
    environ = {}
    setup_testing_defaults(environ)
    environ["PATH_INFO"] = path
    environ["REQUEST_METHOD"] = method
    if body:
        environ["wsgi.input"] = io.BytesIO(body)
        environ["CONTENT_LENGTH"] = str(len(body))
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = headers

    response_body = b"".join(app(environ, start_response))
    return (
        captured["status"],
        dict(captured["headers"]),
        json.loads(response_body.decode("utf-8")),
    )


# --- Happy path: POST /analyze with the sample fixture ---


def test_analyze_returns_deterministic_report():
    """Core app contract: same fixture in -> deterministic report structure out."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["app_id"] = "com.example.legacyapp"
    body = json.dumps(fixture).encode("utf-8")

    status, headers, report = _call_wsgi("/analyze", method="POST", body=body)

    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json"

    # Report structure contract
    assert report["app_id"] == "com.example.legacyapp"
    assert report["project_name"] == "Legacy Repair App"
    assert report["platform"] == "ios"
    assert "report_version" in report
    assert "generated_at" in report

    # Summary shape
    summary = report["summary"]
    assert summary["screen_count"] == 2
    assert summary["recommendation_count"] == 3
    assert "node_count" in summary
    assert "interactive_node_count" in summary
    assert "duplicate_cluster_count" in summary

    # Scores shape
    scores = report["scores"]
    for score_name in (
        "complexity",
        "reusability",
        "accessibility_risk",
        "migration_risk",
    ):
        assert score_name in scores
        assert "value" in scores[score_name]
        assert "evidence" in scores[score_name]

    # Findings and recommendations are lists
    assert isinstance(report["findings"], list)
    assert isinstance(report["recommendations"], list)
    assert len(report["recommendations"]) == 3

    # Roadmap exists
    assert isinstance(report["roadmap"], list)

    # Legal metadata is present (from prepare_report_for_output)
    assert "rade_legal" in report

    # Telemetry is stripped (from prepare_report_for_output)
    assert "_telemetry" not in report

    # Screen inventory
    assert isinstance(report["screen_inventory"], list)
    assert len(report["screen_inventory"]) == 2


def test_analyze_report_is_deterministic_across_calls():
    """Same input produces the same report (except generated_at)."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["app_id"] = "com.example.legacyapp"
    body = json.dumps(fixture).encode("utf-8")

    _, _, report_a = _call_wsgi("/analyze", method="POST", body=body)
    _, _, report_b = _call_wsgi("/analyze", method="POST", body=body)

    # Exclude generated_at and run_id from comparison
    for r in (report_a, report_b):
        r.pop("generated_at", None)

    assert report_a["summary"] == report_b["summary"]
    assert report_a["scores"] == report_b["scores"]
    assert report_a["findings"] == report_b["findings"]
    assert report_a["screen_inventory"] == report_b["screen_inventory"]
    assert report_a["roadmap"] == report_b["roadmap"]


# --- Error handling ---


def test_analyze_rejects_empty_body():
    status, _, payload = _call_wsgi("/analyze", method="POST", body=b"")

    assert status == "400 Bad Request"
    assert payload["error"] == "empty_body"


def test_analyze_rejects_invalid_json():
    status, _, payload = _call_wsgi("/analyze", method="POST", body=b"not json")

    assert status == "400 Bad Request"
    assert payload["error"] == "invalid_json"


def test_analyze_rejects_non_object_json():
    body = json.dumps([1, 2, 3]).encode("utf-8")
    status, _, payload = _call_wsgi("/analyze", method="POST", body=body)

    assert status == "400 Bad Request"
    assert payload["error"] == "invalid_payload"


def test_analyze_rejects_missing_app_id():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    # Don't add app_id
    body = json.dumps(fixture).encode("utf-8")

    status, _, payload = _call_wsgi("/analyze", method="POST", body=body)

    assert status == "400 Bad Request"
    assert payload["error"] == "missing_app_id"


def test_analyze_rejects_invalid_payload_structure():
    body = json.dumps({"app_id": "test", "project_name": 123}).encode("utf-8")

    status, _, payload = _call_wsgi("/analyze", method="POST", body=body)

    assert status == "422 Unprocessable Entity"
    assert payload["error"] == "validation_error"


def test_analyze_rejects_get_method():
    status, _, payload = _call_wsgi("/analyze", method="GET")

    assert status == "405 Method Not Allowed"
    assert payload["error"] == "method_not_allowed"
