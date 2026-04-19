# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from .compliance import (
    iso_date_from_timestamp,
    markdown_legal_lines,
    with_legal_metadata,
)
from .pr_score_diff import (
    ALL_SCORE_NAMES,
    SCORE_DIRECTIONS,
    build_score_diff,
    classify_score_delta,
    format_delta,
    load_report,
)

JsonDict = dict[str, Any]

DIFF_VERSION = "1.0.0"
REQUIRED_REPORT_KEYS = (
    "report_version",
    "generated_at",
    "app_id",
    "project_name",
    "platform",
    "scores",
    "summary",
)


def load_diffable_report(path: Path) -> JsonDict:
    report = load_report(path)
    _validate_report(report)
    return report


def _validate_report(report: JsonDict) -> None:
    missing_keys = [key for key in REQUIRED_REPORT_KEYS if key not in report]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(f"invalid RADE report: missing required keys: {missing}")

    missing_scores = [
        score_name
        for score_name in ALL_SCORE_NAMES
        if score_name not in report["scores"]
        or "value" not in report["scores"][score_name]
    ]
    if missing_scores:
        missing = ", ".join(missing_scores)
        raise ValueError(f"invalid RADE report: missing score metrics: {missing}")


def build_report_diff(base_report: JsonDict, head_report: JsonDict) -> JsonDict:
    score_diff = build_score_diff(base_report, head_report, score_names=ALL_SCORE_NAMES)
    scores: JsonDict = {}
    improved: list[str] = []
    regressed: list[str] = []
    unchanged: list[str] = []

    for score_name in ALL_SCORE_NAMES:
        values = score_diff[score_name]
        status = classify_score_delta(score_name, values["delta"])
        scores[score_name] = {
            "direction": SCORE_DIRECTIONS[score_name],
            "base": values["base"],
            "head": values["head"],
            "delta": values["delta"],
            "status": status,
        }
        if status == "improved":
            improved.append(score_name)
        elif status == "regressed":
            regressed.append(score_name)
        else:
            unchanged.append(score_name)

    recommendations = _build_recommendation_diff(base_report, head_report)
    duplicate_clusters = _build_duplicate_cluster_diff(base_report, head_report)

    diff = {
        "diff_version": DIFF_VERSION,
        "base_report": _report_identity(base_report),
        "head_report": _report_identity(head_report),
        "summary": {
            "score_changes": {
                "improved": improved,
                "regressed": regressed,
                "unchanged": unchanged,
            },
            "recommendation_changes": {
                "added": len(recommendations["added"]),
                "removed": len(recommendations["removed"]),
                "unchanged": len(recommendations["unchanged"]),
            },
            "duplicate_cluster_changes": {
                "added": len(duplicate_clusters["added"]),
                "removed": len(duplicate_clusters["removed"]),
                "changed": len(duplicate_clusters["changed"]),
                "unchanged": len(duplicate_clusters["unchanged"]),
            },
        },
        "scores": scores,
        "recommendations": recommendations,
        "duplicate_clusters": duplicate_clusters,
    }
    return with_legal_metadata(
        diff,
        live_raid_date=iso_date_from_timestamp(head_report.get("generated_at")),
    )


def _report_identity(report: JsonDict) -> JsonDict:
    return {
        "report_version": report["report_version"],
        "generated_at": report["generated_at"],
        "app_id": report["app_id"],
        "project_name": report["project_name"],
        "platform": report["platform"],
    }


def _recommendation_projection(recommendation: JsonDict) -> JsonDict:
    return {
        "recommendation_id": recommendation["recommendation_id"],
        "rule_id": recommendation["rule_id"],
        "category": recommendation["category"],
        "target": recommendation["target"],
        "priority": recommendation["priority"],
    }


def _build_recommendation_diff(
    base_report: JsonDict, head_report: JsonDict
) -> JsonDict:
    base = {
        item["recommendation_id"]: _recommendation_projection(item)
        for item in base_report.get("recommendations", [])
        if "recommendation_id" in item
    }
    head = {
        item["recommendation_id"]: _recommendation_projection(item)
        for item in head_report.get("recommendations", [])
        if "recommendation_id" in item
    }

    added_ids = sorted(set(head) - set(base))
    removed_ids = sorted(set(base) - set(head))
    unchanged_ids = sorted(set(base) & set(head))

    return {
        "added": [head[item_id] for item_id in added_ids],
        "removed": [base[item_id] for item_id in removed_ids],
        "unchanged": [head[item_id] for item_id in unchanged_ids],
    }


def _build_duplicate_cluster_diff(
    base_report: JsonDict, head_report: JsonDict
) -> JsonDict:
    base = _cluster_map(base_report)
    head = _cluster_map(head_report)

    added_fingerprints = sorted(set(head) - set(base))
    removed_fingerprints = sorted(set(base) - set(head))
    shared_fingerprints = sorted(set(base) & set(head))

    changed: list[JsonDict] = []
    unchanged: list[JsonDict] = []

    for fingerprint in shared_fingerprints:
        base_cluster = base[fingerprint]
        head_cluster = head[fingerprint]
        if base_cluster == head_cluster:
            unchanged.append(head_cluster)
            continue
        changed.append(
            {
                "fingerprint": fingerprint,
                "base_count": base_cluster["count"],
                "head_count": head_cluster["count"],
                "delta": head_cluster["count"] - base_cluster["count"],
                "status": _cluster_change_status(base_cluster, head_cluster),
                "interactive": head_cluster["interactive"],
                "base_node_refs": base_cluster["node_refs"],
                "head_node_refs": head_cluster["node_refs"],
                "node_refs_added": sorted(
                    set(head_cluster["node_refs"]) - set(base_cluster["node_refs"])
                ),
                "node_refs_removed": sorted(
                    set(base_cluster["node_refs"]) - set(head_cluster["node_refs"])
                ),
            }
        )

    return {
        "added": [head[fingerprint] for fingerprint in added_fingerprints],
        "removed": [base[fingerprint] for fingerprint in removed_fingerprints],
        "changed": changed,
        "unchanged": unchanged,
    }


def _cluster_map(report: JsonDict) -> dict[str, JsonDict]:
    return {
        cluster["fingerprint"]: _normalize_cluster(cluster)
        for cluster in report.get("duplicate_clusters", [])
        if "fingerprint" in cluster
    }


def _normalize_cluster(cluster: JsonDict) -> JsonDict:
    normalized = dict(cluster)
    for key in (
        "screen_ids",
        "screen_names",
        "node_refs",
        "element_types",
        "roles",
    ):
        if key in normalized:
            normalized[key] = list(normalized[key])
    return normalized


def _cluster_change_status(base_cluster: JsonDict, head_cluster: JsonDict) -> str:
    if head_cluster["count"] > base_cluster["count"]:
        return "expanded"
    if head_cluster["count"] < base_cluster["count"]:
        return "contracted"
    return "changed"


def render_markdown_report_diff(diff: JsonDict) -> str:
    base_report = diff["base_report"]
    head_report = diff["head_report"]
    lines = [
        "# RADE report diff",
        "",
        (
            f"- Base report: {base_report['project_name']} (`{base_report['app_id']}`, "
            f"`{base_report['platform']}`) at `{base_report['generated_at']}`"
        ),
        (
            f"- Head report: {head_report['project_name']} (`{head_report['app_id']}`, "
            f"`{head_report['platform']}`) at `{head_report['generated_at']}`"
        ),
        *markdown_legal_lines(
            live_raid_date=diff.get("rade_legal", {}).get("live_raid_date")
        ),
        "",
        "## Score Delta",
        "",
        "| Metric | Direction | Base | Head | Delta | Status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]

    for score_name in ALL_SCORE_NAMES:
        score = diff["scores"][score_name]
        lines.append(
            f"| {score_name} | {score['direction'].replace('_', ' ')} | "
            f"{score['base']} | {score['head']} | {format_delta(score['delta'])} | "
            f"{score['status']} |"
        )

    lines.extend(
        [
            "",
            f"Accessibility risk direction: {diff['scores']['accessibility_risk']['status']}.",
            f"Migration risk direction: {diff['scores']['migration_risk']['status']}.",
            "",
            "## Recommendations",
            "",
            f"- Added: {len(diff['recommendations']['added'])}",
            f"- Removed: {len(diff['recommendations']['removed'])}",
            f"- Unchanged: {len(diff['recommendations']['unchanged'])}",
            "",
            "### Added recommendations",
            "",
        ]
    )
    lines.extend(_render_recommendation_lines(diff["recommendations"]["added"]))
    lines.extend(["", "### Removed recommendations", ""])
    lines.extend(_render_recommendation_lines(diff["recommendations"]["removed"]))
    lines.extend(
        [
            "",
            "## Repeated Structure",
            "",
            f"- Added clusters: {len(diff['duplicate_clusters']['added'])}",
            f"- Removed clusters: {len(diff['duplicate_clusters']['removed'])}",
            f"- Changed clusters: {len(diff['duplicate_clusters']['changed'])}",
            f"- Unchanged clusters: {len(diff['duplicate_clusters']['unchanged'])}",
            "",
            "### Changed clusters",
            "",
        ]
    )
    lines.extend(_render_changed_cluster_lines(diff["duplicate_clusters"]["changed"]))
    lines.extend(["", "### Added clusters", ""])
    lines.extend(_render_cluster_lines(diff["duplicate_clusters"]["added"]))
    lines.extend(["", "### Removed clusters", ""])
    lines.extend(_render_cluster_lines(diff["duplicate_clusters"]["removed"]))
    lines.append("")
    return "\n".join(lines)


def _render_recommendation_lines(recommendations: list[JsonDict]) -> list[str]:
    if not recommendations:
        return ["- none"]
    return [
        (
            f"- `{item['recommendation_id']}` | {item['category']} | "
            f"{item['target']} | {item['priority']}"
        )
        for item in recommendations
    ]


def _render_changed_cluster_lines(clusters: list[JsonDict]) -> list[str]:
    if not clusters:
        return ["- none"]

    lines: list[str] = []
    for cluster in clusters:
        added = ", ".join(f"`{node_ref}`" for node_ref in cluster["node_refs_added"])
        removed = ", ".join(
            f"`{node_ref}`" for node_ref in cluster["node_refs_removed"]
        )
        suffix_parts: list[str] = []
        if added:
            suffix_parts.append(f"added node refs: {added}")
        if removed:
            suffix_parts.append(f"removed node refs: {removed}")
        if not suffix_parts:
            suffix_parts.append("node refs unchanged")
        lines.append(
            f"- `{cluster['fingerprint']}` {cluster['status']} from "
            f"{cluster['base_count']} to {cluster['head_count']} nodes; "
            + "; ".join(suffix_parts)
        )
    return lines


def _render_cluster_lines(clusters: list[JsonDict]) -> list[str]:
    if not clusters:
        return ["- none"]
    return [
        (
            f"- `{cluster['fingerprint']}` | count {cluster['count']} | "
            f"interactive `{cluster['interactive']}`"
        )
        for cluster in clusters
    ]


def write_report_diff(
    diff: JsonDict,
    json_output: Path | None,
    md_output: Path | None,
) -> None:
    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(diff, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
    if md_output is not None:
        md_output.parent.mkdir(parents=True, exist_ok=True)
        md_output.write_text(render_markdown_report_diff(diff), encoding="utf-8")


def report_diff_error(path: Path, exc: Exception) -> str:
    if isinstance(exc, FileNotFoundError):
        return f"report diff input does not exist: {path}"
    if isinstance(exc, JSONDecodeError):
        return f"invalid JSON in report diff input: {path}"
    if isinstance(exc, ValueError):
        return str(exc)
    raise exc
