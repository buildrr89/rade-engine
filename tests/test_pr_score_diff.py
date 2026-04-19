# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from src.core.pr_score_diff import (
    ALL_SCORE_NAMES,
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
