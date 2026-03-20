# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..connectors.standards_pack import load_standards_pack
from ..scrubber.pii_scrubber import scrub_report_artifact
from .compliance import (
    iso_date_from_timestamp,
    markdown_legal_lines,
    with_legal_metadata,
)
from .deduplicator import deduplicate_nodes
from .fingerprint import fingerprint_node
from .models import REPORT_VERSION
from .normalizer import normalize_project
from .recommendation_engine import build_recommendations
from .roadmap_generator import build_roadmap
from .schemas import load_json_file, validate_project_payload
from .scoring import score_project
from .telemetry import log_stage

JsonDict = dict[str, Any]


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def analyze_payload(
    payload: JsonDict, app_id: str, generated_at: str | None = None
) -> JsonDict:
    run_id = str(uuid4())
    _set_last_run_metadata({"run_id": run_id})

    with log_stage(run_id=run_id, component="cli", stage="load_payload"):
        validated = validate_project_payload(payload)

    with log_stage(run_id=run_id, component="cli", stage="normalize"):
        project = normalize_project(validated, app_id)
        for screen in project["screens"]:
            for element_index, element in enumerate(screen["elements"]):
                enriched = dict(element)
                enriched["structural_fingerprint"] = fingerprint_node(enriched)
                screen["elements"][element_index] = enriched

    project["nodes"] = [
        element for screen in project["screens"] for element in screen["elements"]
    ]

    with log_stage(run_id=run_id, component="cli", stage="score"):
        clusters = deduplicate_nodes(project["nodes"])
        scores = score_project(project, clusters)

    with log_stage(run_id=run_id, component="cli", stage="recommend"):
        standards_pack = load_standards_pack()
        recommendations = build_recommendations(project, clusters)
        roadmap = build_roadmap(recommendations)
    generated_at = generated_at or now_iso()

    findings = [
        {
            "finding_id": f"finding-{index:03d}",
            "rule_id": recommendation["rule_id"],
            "category": recommendation["category"],
            "title": recommendation["problem_statement"],
            "priority": recommendation["priority"],
            "provenance": recommendation["provenance"],
            "evidence": recommendation["evidence"],
        }
        for index, recommendation in enumerate(recommendations, start=1)
    ]

    screen_inventory = []
    for screen in project["screens"]:
        screen_nodes = screen["elements"]
        screen_inventory.append(
            {
                "screen_id": screen["screen_id"],
                "screen_name": screen["screen_name"],
                "node_count": len(screen_nodes),
                "interactive_count": sum(
                    1 for node in screen_nodes if node.get("interactive")
                ),
                "duplicate_node_count": sum(
                    1
                    for node in screen_nodes
                    if any(
                        cluster["count"] > 1
                        and cluster["fingerprint"] == node["structural_fingerprint"]
                        for cluster in clusters
                    )
                ),
                "accessibility_gap_count": sum(
                    1
                    for node in screen_nodes
                    if node.get("interactive")
                    and not node.get("accessibility_identifier")
                ),
            }
        )

    report = {
        "report_version": REPORT_VERSION,
        "generated_at": generated_at,
        "app_id": app_id,
        "project_name": project["project_name"],
        "platform": project["platform"],
        "standards_pack": standards_pack,
        "summary": {
            "screen_count": len(project["screens"]),
            "node_count": len(project["nodes"]),
            "interactive_node_count": sum(
                1 for node in project["nodes"] if node.get("interactive")
            ),
            "duplicate_cluster_count": sum(
                1 for cluster in clusters if cluster["count"] > 1
            ),
            "recommendation_count": len(recommendations),
        },
        "scores": scores,
        "screen_inventory": screen_inventory,
        "duplicate_clusters": [
            {
                "fingerprint": cluster["fingerprint"],
                "count": cluster["count"],
                "interactive": cluster["interactive"],
                "screen_ids": cluster["screen_ids"],
                "screen_names": cluster["screen_names"],
                "node_refs": cluster["node_refs"],
                "element_types": cluster["element_types"],
                "roles": cluster["roles"],
                "representative_node_ref": cluster["representative_node_ref"],
            }
            for cluster in clusters
            if cluster["count"] > 1
        ],
        "findings": findings,
        "recommendations": recommendations,
        "roadmap": roadmap,
    }
    report["_telemetry"] = {"run_id": run_id}
    return report


_last_run_metadata: dict[str, Any] | None = None


def _set_last_run_metadata(metadata: dict[str, Any]) -> None:
    global _last_run_metadata
    _last_run_metadata = metadata.copy()


def get_last_run_metadata() -> dict[str, Any] | None:
    return _last_run_metadata


def prepare_report_for_output(report: JsonDict) -> JsonDict:
    scrubbed = scrub_report_artifact(report)
    scrubbed.pop("_telemetry", None)
    return with_legal_metadata(
        scrubbed,
        live_raid_date=iso_date_from_timestamp(scrubbed.get("generated_at")),
    )


def render_markdown_report(report: JsonDict) -> str:
    report = prepare_report_for_output(report)
    lines: list[str] = []
    lines.append("# RADE modernization report")
    lines.append("")
    lines.append(f"- Report version: {report['report_version']}")
    lines.append(f"- Generated at: {report['generated_at']}")
    lines.append(f"- App ID: {report['app_id']}")
    lines.append(f"- Project: {report['project_name']}")
    lines.append(f"- Platform: {report['platform']}")
    lines.append(f"- Standards pack: {report['standards_pack']['version']}")
    lines.extend(
        markdown_legal_lines(
            live_raid_date=report["rade_legal"].get("live_raid_date")
        )
    )
    lines.append("")
    lines.append("## Summary")
    for key, value in report["summary"].items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    lines.append("")
    lines.append("## Scorecard")
    lines.append("| Metric | Value | Evidence |")
    lines.append("| --- | --- | --- |")
    for score_name in (
        "complexity",
        "reusability",
        "accessibility_risk",
        "migration_risk",
    ):
        score = report["scores"][score_name]
        lines.append(
            f"| {score_name} | {score['value']} | {'; '.join(score['evidence'])} |"
        )
    lines.append("")
    lines.append("## Screen Inventory")
    for screen in report["screen_inventory"]:
        lines.append(
            f"- {screen['screen_name']} ({screen['screen_id']}): {screen['node_count']} nodes, {screen['interactive_count']} interactive, {screen['duplicate_node_count']} duplicated, {screen['accessibility_gap_count']} accessibility gaps"
        )
    lines.append("")
    lines.append("## Findings")
    for finding in report["findings"]:
        lines.append(f"### {finding['title']}")
        lines.append(f"- Rule ID: {finding['rule_id']}")
        lines.append(f"- Category: {finding['category']}")
        lines.append(f"- Priority: {finding['priority']}")
        lines.append(f"- Provenance: {finding['provenance']}")
        lines.append(f"- Evidence: {', '.join(finding['evidence'])}")
        lines.append("")
    lines.append("## Recommendations")
    for recommendation in report["recommendations"]:
        lines.append(f"### {recommendation['category']} - {recommendation['target']}")
        lines.append(f"- Recommendation ID: {recommendation['recommendation_id']}")
        lines.append(f"- Rule ID: {recommendation['rule_id']}")
        lines.append(f"- Priority: {recommendation['priority']}")
        lines.append(f"- Confidence: {recommendation['confidence']}")
        lines.append(f"- Problem: {recommendation['problem_statement']}")
        lines.append(f"- Change: {recommendation['recommended_change']}")
        lines.append(f"- Reasoning: {recommendation['reasoning']}")
        lines.append(f"- Expected impact: {recommendation['expected_impact']}")
        lines.append(f"- Effort: {recommendation['implementation_effort']}")
        lines.append(f"- Standards refs: {', '.join(recommendation['standards_refs'])}")
        lines.append(
            f"- Benchmark refs: {', '.join(recommendation['benchmark_refs']) or 'none'}"
        )
        lines.append(f"- Provenance: {recommendation['provenance']}")
        lines.append(f"- Evidence: {', '.join(recommendation['evidence'])}")
        lines.append("")
    lines.append("## Roadmap")
    for item in report["roadmap"]:
        lines.append(
            f"- Step {item['step']}: {item['title']} ({item['priority']}, {item['implementation_effort']})"
        )
    lines.append("")
    return "\n".join(lines)


def write_report(
    report: JsonDict, json_output: Path | None, md_output: Path | None
) -> None:
    run_id = report.get("_telemetry", {}).get("run_id")
    with log_stage(run_id=run_id, component="cli", stage="report_write"):
        report_for_output = prepare_report_for_output(report)
        if json_output is not None:
            json_output.parent.mkdir(parents=True, exist_ok=True)
            json_output.write_text(
                json.dumps(report_for_output, indent=2, sort_keys=False) + "\n",
                encoding="utf-8",
            )
        if md_output is not None:
            md_output.parent.mkdir(parents=True, exist_ok=True)
            md_output.write_text(
                render_markdown_report(report_for_output), encoding="utf-8"
            )


def analyze_file(
    input_path: Path | str,
    app_id: str,
    json_output: Path | None = None,
    md_output: Path | None = None,
) -> JsonDict:
    payload = load_json_file(Path(input_path))
    report = analyze_payload(payload, app_id)
    write_report(report, json_output, md_output)
    return prepare_report_for_output(report)
