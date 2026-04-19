# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.core.report_generator import analyze_payload, prepare_report_for_output
from src.engine.axe_adapter import (
    AxeRunError,
    normalize_axe_results,
    run_axe_against_page,
    summarize_axe_findings,
)

RAW_AXE_RESULT = {
    "testEngine": {"name": "axe-core", "version": "4.10.2"},
    "violations": [
        {
            "id": "color-contrast",
            "impact": "serious",
            "description": "Ensures elements have sufficient colour contrast",
            "help": "Elements must meet minimum colour contrast",
            "helpUrl": "https://dequeuniversity.com/rules/axe/4.10/color-contrast",
            "tags": ["wcag2aa", "wcag143", "cat.color"],
            "nodes": [
                {
                    "target": [".btn-primary"],
                    "html": '<a class="btn-primary">Go</a>',
                    "failureSummary": "Fix any of the following: ...",
                },
                {
                    "target": [[".nav-link"]],
                    "html": '<a class="nav-link">Docs</a>',
                    "failureSummary": "",
                },
            ],
        },
        {
            "id": "image-alt",
            "impact": "critical",
            "description": "Ensures <img> elements have alternate text",
            "help": "Images must have alternate text",
            "helpUrl": "https://dequeuniversity.com/rules/axe/4.10/image-alt",
            "tags": ["wcag2a", "wcag111"],
            "nodes": [
                {
                    "target": ["img#logo"],
                    "html": '<img id="logo" src="/logo.png">',
                    "failureSummary": "Element does not have alt text",
                }
            ],
        },
    ],
}


def test_normalize_produces_one_finding_per_node() -> None:
    findings = normalize_axe_results(RAW_AXE_RESULT)
    assert len(findings) == 3
    rule_ids = [f["rule_id"] for f in findings]
    # Sorted deterministically by rule_id then target then html
    assert rule_ids == sorted(rule_ids)


def test_normalize_maps_impact_to_priority_and_wcag() -> None:
    findings = normalize_axe_results(RAW_AXE_RESULT)
    critical = [f for f in findings if f["rule_id"] == "image-alt"][0]
    assert critical["priority"] == "P0"
    assert critical["impact"] == "critical"
    assert "wcag2a" in critical["wcag_refs"]
    contrast = [f for f in findings if f["rule_id"] == "color-contrast"][0]
    assert contrast["priority"] == "P1"
    assert contrast["provenance"] == "axe-core"
    assert contrast["engine_version"] == "4.10.2"


def test_normalize_is_deterministic() -> None:
    a = normalize_axe_results(RAW_AXE_RESULT)
    b = normalize_axe_results(RAW_AXE_RESULT)
    assert json.dumps(a) == json.dumps(b)


def test_summarize_rolls_up_by_impact_and_rule() -> None:
    findings = normalize_axe_results(RAW_AXE_RESULT)
    summary = summarize_axe_findings(findings)
    assert summary["total"] == 3
    assert summary["by_impact"]["critical"] == 1
    assert summary["by_impact"]["serious"] == 2
    assert summary["by_rule"]["color-contrast"] == 2
    assert summary["engine_versions"] == ["4.10.2"]


def test_normalize_ignores_malformed_entries() -> None:
    payload = {"violations": ["bad", {"id": ""}, {"id": "ok", "nodes": []}]}
    assert normalize_axe_results(payload) == []


def test_run_axe_against_page_uses_injected_seams() -> None:
    calls: dict[str, object] = {}

    def fake_loader(page, url, timeout):
        calls["loader_url"] = url
        calls["loader_timeout"] = timeout

    def fake_runner(page, timeout):
        calls["runner_timeout"] = timeout
        return RAW_AXE_RESULT

    findings = run_axe_against_page(
        page=object(),
        axe_source_url="https://example.test/axe.min.js",
        timeout_ms=5_000,
        script_loader=fake_loader,
        runner=fake_runner,
    )
    assert calls["loader_url"] == "https://example.test/axe.min.js"
    assert calls["loader_timeout"] == 5_000
    assert calls["runner_timeout"] == 5_000
    assert len(findings) == 3


def test_run_axe_against_page_wraps_failures() -> None:
    def raising_loader(*_a, **_kw):
        raise RuntimeError("script blocked by CSP")

    with pytest.raises(AxeRunError):
        run_axe_against_page(
            page=object(),
            script_loader=raising_loader,
            runner=lambda *a, **k: {},
        )


def test_analyze_payload_embeds_axe_findings() -> None:
    sample = json.loads(
        Path("examples/sample_ios_output.json").read_text(encoding="utf-8")
    )
    findings = normalize_axe_results(RAW_AXE_RESULT)
    report = analyze_payload(
        sample,
        "com.example.legacyapp",
        generated_at="2026-04-19T00:00:00Z",
        axe_findings=findings,
    )
    assert "accessibility_violations" in report
    block = report["accessibility_violations"]
    assert len(block["findings"]) == 3
    assert block["summary"]["total"] == 3

    prepared = prepare_report_for_output(report)
    assert prepared["accessibility_violations"]["summary"]["engine"] == "axe-core"


def test_analyze_payload_omits_block_when_axe_not_run() -> None:
    sample = json.loads(
        Path("examples/sample_ios_output.json").read_text(encoding="utf-8")
    )
    report = analyze_payload(
        sample, "com.example.legacyapp", generated_at="2026-04-19T00:00:00Z"
    )
    assert "accessibility_violations" not in report
