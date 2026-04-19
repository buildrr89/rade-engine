# SPDX-License-Identifier: AGPL-3.0-only
"""Helpers for PR score diffs in GitHub Action comments."""

from __future__ import annotations

import json
from pathlib import Path

COMMENT_MARKER = "<!-- rade-pr-score-comment -->"
ALL_SCORE_NAMES = (
    "complexity",
    "reusability",
    "accessibility_risk",
    "migration_risk",
)
TRACKED_SCORES = ("reusability", "accessibility_risk")
SCORE_DIRECTIONS = {
    "complexity": "lower_is_better",
    "reusability": "higher_is_better",
    "accessibility_risk": "lower_is_better",
    "migration_risk": "lower_is_better",
}


def load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_score(report: dict, score_name: str) -> int:
    return int(report["scores"][score_name]["value"])


def build_score_diff(
    base_report: dict,
    head_report: dict,
    score_names: tuple[str, ...] = TRACKED_SCORES,
) -> dict[str, dict[str, int]]:
    diff: dict[str, dict[str, int]] = {}
    for score_name in score_names:
        base_value = extract_score(base_report, score_name)
        head_value = extract_score(head_report, score_name)
        diff[score_name] = {
            "base": base_value,
            "head": head_value,
            "delta": head_value - base_value,
        }
    return diff


def format_delta(delta: int) -> str:
    if delta > 0:
        return f"+{delta}"
    return str(delta)


def classify_score_delta(score_name: str, delta: int) -> str:
    if delta == 0:
        return "unchanged"
    direction = SCORE_DIRECTIONS[score_name]
    if direction == "higher_is_better":
        return "improved" if delta > 0 else "regressed"
    return "improved" if delta < 0 else "regressed"


AXE_IMPACT_LEVELS = ("critical", "serious", "moderate", "minor")


def _axe_block(report: dict) -> dict | None:
    block = report.get("accessibility_violations")
    if isinstance(block, dict):
        return block
    return None


def _axe_by_impact(summary: dict) -> dict[str, int]:
    raw = summary.get("by_impact") or {}
    counts: dict[str, int] = {}
    for level in AXE_IMPACT_LEVELS:
        counts[level] = int(raw.get(level, 0))
    return counts


def _axe_rule_ids(summary: dict) -> set[str]:
    by_rule = summary.get("by_rule") or {}
    return {str(rule_id) for rule_id, count in by_rule.items() if int(count) > 0}


def build_axe_diff(base_report: dict, head_report: dict) -> dict:
    """Deterministic axe-core violation delta at rule-id granularity.

    `present` is True when either side carries an `accessibility_violations`
    block. When neither side has axe data, callers should omit the PR comment
    section entirely.
    """
    base_block = _axe_block(base_report)
    head_block = _axe_block(head_report)
    if base_block is None and head_block is None:
        return {"present": False}

    base_summary = (base_block or {}).get("summary") or {}
    head_summary = (head_block or {}).get("summary") or {}
    base_total = int(base_summary.get("total", 0))
    head_total = int(head_summary.get("total", 0))
    base_by_impact = _axe_by_impact(base_summary)
    head_by_impact = _axe_by_impact(head_summary)
    delta_by_impact = {
        level: head_by_impact[level] - base_by_impact[level]
        for level in AXE_IMPACT_LEVELS
    }
    base_rules = _axe_rule_ids(base_summary)
    head_rules = _axe_rule_ids(head_summary)
    return {
        "present": True,
        "base_present": base_block is not None,
        "head_present": head_block is not None,
        "base_total": base_total,
        "head_total": head_total,
        "delta_total": head_total - base_total,
        "base_by_impact": base_by_impact,
        "head_by_impact": head_by_impact,
        "delta_by_impact": delta_by_impact,
        "newly_introduced_rule_ids": sorted(head_rules - base_rules),
        "fully_resolved_rule_ids": sorted(base_rules - head_rules),
    }


def render_axe_section(axe_diff: dict) -> list[str]:
    """Markdown subsection for the PR comment. Returns [] when absent."""
    if not axe_diff.get("present"):
        return []
    lines = [
        "",
        "### Accessibility violations (axe-core)",
        "",
    ]
    if not axe_diff["base_present"]:
        lines.append("Base report has no axe-core output; head introduced axe data.")
    elif not axe_diff["head_present"]:
        lines.append("Head report has no axe-core output; base carried axe data.")
    lines.extend(
        [
            "",
            "| Impact | Base | Head | Delta |",
            "|---|---:|---:|---:|",
            f"| `total` | {axe_diff['base_total']} | {axe_diff['head_total']} | {format_delta(axe_diff['delta_total'])} |",
        ]
    )
    for level in AXE_IMPACT_LEVELS:
        base_count = axe_diff["base_by_impact"][level]
        head_count = axe_diff["head_by_impact"][level]
        delta = axe_diff["delta_by_impact"][level]
        lines.append(
            f"| `{level}` | {base_count} | {head_count} | {format_delta(delta)} |"
        )
    newly = axe_diff["newly_introduced_rule_ids"]
    resolved = axe_diff["fully_resolved_rule_ids"]
    lines.append("")
    if newly:
        rule_list = ", ".join(f"`{rule_id}`" for rule_id in newly)
        lines.append(f"Newly introduced rule IDs: {rule_list}.")
    else:
        lines.append("Newly introduced rule IDs: none.")
    if resolved:
        rule_list = ", ".join(f"`{rule_id}`" for rule_id in resolved)
        lines.append(f"Fully resolved rule IDs: {rule_list}.")
    else:
        lines.append("Fully resolved rule IDs: none.")
    lines.append(
        "Reported for visibility; the regression gate still tracks only `reusability` and `accessibility_risk`."
    )
    return lines


def render_pr_comment(
    diff: dict[str, dict[str, int]],
    base_ref: str,
    head_ref: str,
    gate_status: str = "disabled",
    axe_diff: dict | None = None,
) -> str:
    lines = [
        COMMENT_MARKER,
        "## RADE score diff",
        "",
        f"Compared `{base_ref}` -> `{head_ref}`.",
        f"Regression gate status: `{gate_status}`.",
        "Direction: higher `reusability` is better; lower `accessibility_risk` is better.",
        "",
        "| Metric | Base | Head | Delta |",
        "|---|---:|---:|---:|",
    ]
    for score_name in TRACKED_SCORES:
        values = diff[score_name]
        lines.append(
            f"| `{score_name}` | {values['base']} | {values['head']} | {format_delta(values['delta'])} |"
        )
    if axe_diff is not None:
        lines.extend(render_axe_section(axe_diff))
    lines.extend(
        [
            "",
            "_Generated by RADE GitHub Action._",
        ]
    )
    return "\n".join(lines)


def has_score_regression(diff: dict[str, dict[str, int]]) -> bool:
    """Regression rule: reusability down OR accessibility risk up."""
    return diff["reusability"]["delta"] < 0 or diff["accessibility_risk"]["delta"] > 0


def regression_reason(diff: dict[str, dict[str, int]]) -> str:
    """Stable reason code for regression outcome."""
    reusability_down = diff["reusability"]["delta"] < 0
    accessibility_up = diff["accessibility_risk"]["delta"] > 0

    if reusability_down and accessibility_up:
        return "both"
    if reusability_down:
        return "reusability_down"
    if accessibility_up:
        return "accessibility_risk_up"
    return "none"
