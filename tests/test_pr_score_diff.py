# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from src.core.pr_score_diff import (
    ALL_SCORE_NAMES,
    build_axe_diff,
    build_score_diff,
    classify_score_delta,
    has_score_regression,
    regression_reason,
    render_pr_comment,
)


def _report(
    reusability: int,
    accessibility_risk: int,
    complexity: int = 60,
    migration_risk: int = 50,
) -> dict:
    return {
        "scores": {
            "complexity": {"value": complexity},
            "reusability": {"value": reusability},
            "accessibility_risk": {"value": accessibility_risk},
            "migration_risk": {"value": migration_risk},
        }
    }


def test_build_score_diff_tracks_expected_metrics():
    base_report = _report(reusability=80, accessibility_risk=30)
    head_report = _report(reusability=85, accessibility_risk=42)

    diff = build_score_diff(base_report, head_report)

    assert diff == {
        "reusability": {"base": 80, "head": 85, "delta": 5},
        "accessibility_risk": {"base": 30, "head": 42, "delta": 12},
    }


def test_build_score_diff_accepts_full_score_set():
    base_report = _report(
        reusability=80, accessibility_risk=30, complexity=55, migration_risk=40
    )
    head_report = _report(
        reusability=82, accessibility_risk=25, complexity=60, migration_risk=45
    )

    diff = build_score_diff(base_report, head_report, score_names=ALL_SCORE_NAMES)

    assert diff == {
        "complexity": {"base": 55, "head": 60, "delta": 5},
        "reusability": {"base": 80, "head": 82, "delta": 2},
        "accessibility_risk": {"base": 30, "head": 25, "delta": -5},
        "migration_risk": {"base": 40, "head": 45, "delta": 5},
    }


def test_classify_score_delta_respects_score_direction():
    assert classify_score_delta("reusability", 2) == "improved"
    assert classify_score_delta("reusability", -2) == "regressed"
    assert classify_score_delta("migration_risk", -2) == "improved"
    assert classify_score_delta("migration_risk", 2) == "regressed"
    assert classify_score_delta("accessibility_risk", 0) == "unchanged"


def test_render_pr_comment_has_stable_marker_and_table():
    comment = render_pr_comment(
        {
            "reusability": {"base": 80, "head": 75, "delta": -5},
            "accessibility_risk": {"base": 30, "head": 35, "delta": 5},
        },
        base_ref="base-sha",
        head_ref="head-sha",
    )

    assert "<!-- rade-pr-score-comment -->" in comment
    assert "Compared `base-sha` -> `head-sha`." in comment
    assert "Regression gate status: `disabled`." in comment
    assert (
        "Direction: higher `reusability` is better; lower `accessibility_risk` is better."
        in comment
    )
    assert "| `reusability` | 80 | 75 | -5 |" in comment
    assert "| `accessibility_risk` | 30 | 35 | +5 |" in comment


def test_render_pr_comment_includes_gate_status_value():
    comment = render_pr_comment(
        {
            "reusability": {"base": 80, "head": 80, "delta": 0},
            "accessibility_risk": {"base": 30, "head": 30, "delta": 0},
        },
        base_ref="base-sha",
        head_ref="head-sha",
        gate_status="enabled:passed",
    )

    assert "Regression gate status: `enabled:passed`." in comment


def test_has_score_regression_true_when_reusability_drops():
    assert has_score_regression(
        {
            "reusability": {"base": 80, "head": 70, "delta": -10},
            "accessibility_risk": {"base": 30, "head": 30, "delta": 0},
        }
    )


def test_has_score_regression_true_when_accessibility_risk_rises():
    assert has_score_regression(
        {
            "reusability": {"base": 80, "head": 80, "delta": 0},
            "accessibility_risk": {"base": 30, "head": 35, "delta": 5},
        }
    )


def test_has_score_regression_false_when_scores_hold_or_improve():
    assert not has_score_regression(
        {
            "reusability": {"base": 80, "head": 85, "delta": 5},
            "accessibility_risk": {"base": 30, "head": 25, "delta": -5},
        }
    )


def test_regression_reason_none_when_scores_hold_or_improve():
    assert (
        regression_reason(
            {
                "reusability": {"base": 80, "head": 85, "delta": 5},
                "accessibility_risk": {"base": 30, "head": 25, "delta": -5},
            }
        )
        == "none"
    )


def test_regression_reason_reusability_down_when_only_reusability_drops():
    assert (
        regression_reason(
            {
                "reusability": {"base": 80, "head": 75, "delta": -5},
                "accessibility_risk": {"base": 30, "head": 30, "delta": 0},
            }
        )
        == "reusability_down"
    )


def test_regression_reason_accessibility_up_when_only_accessibility_risk_rises():
    assert (
        regression_reason(
            {
                "reusability": {"base": 80, "head": 80, "delta": 0},
                "accessibility_risk": {"base": 30, "head": 31, "delta": 1},
            }
        )
        == "accessibility_risk_up"
    )


def _axe_report(
    reusability: int = 80,
    accessibility_risk: int = 30,
    *,
    by_impact: dict | None = None,
    by_rule: dict | None = None,
) -> dict:
    if by_impact is None:
        by_impact = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    if by_rule is None:
        by_rule = {}
    total = sum(by_impact.values())
    return {
        "scores": {
            "complexity": {"value": 60},
            "reusability": {"value": reusability},
            "accessibility_risk": {"value": accessibility_risk},
            "migration_risk": {"value": 50},
        },
        "accessibility_violations": {
            "findings": [],
            "summary": {
                "total": total,
                "by_impact": by_impact,
                "by_rule": by_rule,
                "engine": "axe-core",
                "engine_versions": ["4.10.2"],
            },
        },
    }


def _plain_report(reusability: int = 80, accessibility_risk: int = 30) -> dict:
    return _report(reusability=reusability, accessibility_risk=accessibility_risk)


def test_build_axe_diff_present_on_both_sides():
    base = _axe_report(
        by_impact={"critical": 1, "serious": 2, "moderate": 0, "minor": 0},
        by_rule={"color-contrast": 2, "image-alt": 1},
    )
    head = _axe_report(
        by_impact={"critical": 0, "serious": 2, "moderate": 1, "minor": 0},
        by_rule={"color-contrast": 2, "label": 1},
    )

    diff = build_axe_diff(base, head)

    assert diff["present"] is True
    assert diff["base_present"] is True
    assert diff["head_present"] is True
    assert diff["base_total"] == 3
    assert diff["head_total"] == 3
    assert diff["delta_total"] == 0
    assert diff["delta_by_impact"] == {
        "critical": -1,
        "serious": 0,
        "moderate": 1,
        "minor": 0,
    }
    assert diff["newly_introduced_rule_ids"] == ["label"]
    assert diff["fully_resolved_rule_ids"] == ["image-alt"]


def test_build_axe_diff_head_only():
    base = _plain_report()
    head = _axe_report(
        by_impact={"critical": 1, "serious": 0, "moderate": 0, "minor": 0},
        by_rule={"color-contrast": 1},
    )

    diff = build_axe_diff(base, head)

    assert diff["present"] is True
    assert diff["base_present"] is False
    assert diff["head_present"] is True
    assert diff["base_total"] == 0
    assert diff["head_total"] == 1
    assert diff["newly_introduced_rule_ids"] == ["color-contrast"]
    assert diff["fully_resolved_rule_ids"] == []


def test_build_axe_diff_base_only():
    base = _axe_report(
        by_impact={"critical": 0, "serious": 1, "moderate": 0, "minor": 0},
        by_rule={"image-alt": 1},
    )
    head = _plain_report()

    diff = build_axe_diff(base, head)

    assert diff["present"] is True
    assert diff["base_present"] is True
    assert diff["head_present"] is False
    assert diff["base_total"] == 1
    assert diff["head_total"] == 0
    assert diff["newly_introduced_rule_ids"] == []
    assert diff["fully_resolved_rule_ids"] == ["image-alt"]


def test_build_axe_diff_absent_on_both_sides():
    diff = build_axe_diff(_plain_report(), _plain_report())
    assert diff == {"present": False}


def test_build_axe_diff_is_deterministic():
    base = _axe_report(
        by_impact={"critical": 1, "serious": 0, "moderate": 0, "minor": 0},
        by_rule={"color-contrast": 1, "image-alt": 1},
    )
    head = _axe_report(
        by_impact={"critical": 0, "serious": 1, "moderate": 0, "minor": 0},
        by_rule={"label": 1, "color-contrast": 1},
    )
    first = build_axe_diff(base, head)
    second = build_axe_diff(base, head)
    assert first == second


def test_render_pr_comment_omits_axe_section_when_absent():
    comment = render_pr_comment(
        {
            "reusability": {"base": 80, "head": 80, "delta": 0},
            "accessibility_risk": {"base": 30, "head": 30, "delta": 0},
        },
        base_ref="base-sha",
        head_ref="head-sha",
        axe_diff={"present": False},
    )

    assert "Accessibility violations (axe-core)" not in comment


def test_render_pr_comment_includes_axe_section_when_present():
    axe_diff = build_axe_diff(
        _axe_report(
            by_impact={"critical": 1, "serious": 0, "moderate": 0, "minor": 0},
            by_rule={"image-alt": 1},
        ),
        _axe_report(
            by_impact={"critical": 0, "serious": 1, "moderate": 0, "minor": 0},
            by_rule={"label": 1},
        ),
    )
    comment = render_pr_comment(
        {
            "reusability": {"base": 80, "head": 80, "delta": 0},
            "accessibility_risk": {"base": 30, "head": 30, "delta": 0},
        },
        base_ref="base-sha",
        head_ref="head-sha",
        axe_diff=axe_diff,
    )

    assert "### Accessibility violations (axe-core)" in comment
    assert "Newly introduced rule IDs: `label`." in comment
    assert "Fully resolved rule IDs: `image-alt`." in comment
    assert "| `critical` | 1 | 0 | -1 |" in comment
    assert "| `serious` | 0 | 1 | +1 |" in comment


def test_render_pr_comment_axe_section_stable_across_runs():
    axe_diff = build_axe_diff(
        _axe_report(
            by_impact={"critical": 1, "serious": 0, "moderate": 0, "minor": 0},
            by_rule={"color-contrast": 1},
        ),
        _axe_report(
            by_impact={"critical": 1, "serious": 0, "moderate": 0, "minor": 0},
            by_rule={"color-contrast": 1},
        ),
    )
    first = render_pr_comment(
        {
            "reusability": {"base": 80, "head": 80, "delta": 0},
            "accessibility_risk": {"base": 30, "head": 30, "delta": 0},
        },
        base_ref="base-sha",
        head_ref="head-sha",
        axe_diff=axe_diff,
    )
    second = render_pr_comment(
        {
            "reusability": {"base": 80, "head": 80, "delta": 0},
            "accessibility_risk": {"base": 30, "head": 30, "delta": 0},
        },
        base_ref="base-sha",
        head_ref="head-sha",
        axe_diff=axe_diff,
    )
    assert first == second


def test_regression_reason_both_when_both_regression_conditions_trigger():
    assert (
        regression_reason(
            {
                "reusability": {"base": 80, "head": 75, "delta": -5},
                "accessibility_risk": {"base": 30, "head": 31, "delta": 1},
            }
        )
        == "both"
    )
