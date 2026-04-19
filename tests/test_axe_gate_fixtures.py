# SPDX-License-Identifier: AGPL-3.0-only
"""Slice #46: golden axe-gate fixture pair.

Checked-in base/head report fixtures under `tests/fixtures/` that carry
`accessibility_violations` blocks so the axe regression gate (slice #41) has
a byte-stable, deterministic case to regress against. The base report has a
single `moderate` finding; the head report introduces a new `critical` rule.
The gate must fire, and the reported rule-id deltas must be stable.
"""

from __future__ import annotations

from pathlib import Path

from src.core.pr_score_diff import (
    axe_regression_reason,
    build_axe_diff,
    has_axe_regression,
    load_report,
    render_pr_comment,
)

FIXTURES = Path(__file__).parent / "fixtures"
BASE = FIXTURES / "axe_gate_base.json"
HEAD = FIXTURES / "axe_gate_head.json"


def test_fixtures_exist() -> None:
    assert BASE.is_file(), BASE
    assert HEAD.is_file(), HEAD


def test_axe_gate_fires_on_newly_introduced_critical_rule() -> None:
    base = load_report(BASE)
    head = load_report(HEAD)

    diff = build_axe_diff(base, head)

    assert diff["present"] is True
    assert diff["base_present"] is True
    assert diff["head_present"] is True
    assert diff["base_total"] == 1
    assert diff["head_total"] == 2
    assert diff["delta_total"] == 1
    assert diff["delta_by_impact"] == {
        "critical": 1,
        "serious": 0,
        "moderate": 0,
        "minor": 0,
    }
    assert diff["newly_introduced_rule_ids"] == ["color-contrast"]
    assert diff["newly_introduced_by_impact"]["critical"] == ["color-contrast"]
    assert diff["fully_resolved_rule_ids"] == []

    assert has_axe_regression(diff) is True
    assert axe_regression_reason(diff) == "critical_introduced"


def test_rendered_comment_reflects_fixture_outcome() -> None:
    base = load_report(BASE)
    head = load_report(HEAD)
    diff = build_axe_diff(base, head)

    comment = render_pr_comment(
        {
            "reusability": {"base": 80, "head": 80, "delta": 0},
            "accessibility_risk": {"base": 30, "head": 30, "delta": 0},
        },
        base_ref="axe-gate-base",
        head_ref="axe-gate-head",
        axe_diff=diff,
        axe_gate_status="enabled:failed",
    )

    assert "Axe regression gate status: `enabled:failed`." in comment
    assert "Newly introduced rule IDs: `color-contrast`." in comment
    assert "Newly introduced `critical` rules: `color-contrast`." in comment


def test_axe_gate_fixture_pair_is_deterministic() -> None:
    first = build_axe_diff(load_report(BASE), load_report(HEAD))
    second = build_axe_diff(load_report(BASE), load_report(HEAD))
    assert first == second
