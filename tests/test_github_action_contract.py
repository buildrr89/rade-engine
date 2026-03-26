# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from pathlib import Path


def test_action_uses_action_and_workspace_paths_for_marketplace_execution():
    action_text = Path("action.yml").read_text(encoding="utf-8")

    assert 'PYTHONPATH="${GITHUB_ACTION_PATH}"' in action_text
    assert 'INPUT_FILE="${GITHUB_WORKSPACE}/${{ inputs.input-path }}"' in action_text
    assert 'python "${GITHUB_ACTION_PATH}/scripts/pr_score_comment.py"' in action_text


def test_action_exposes_optional_regression_gate_input_and_step():
    action_text = Path("action.yml").read_text(encoding="utf-8")

    assert "fail-on-regression:" in action_text
    assert 'default: "false"' in action_text
    assert "name: Evaluate regression gate status" in action_text
    assert "id: regression" in action_text
    assert "--gate-status" in action_text
    assert "steps.regression.outputs.gate_status" in action_text
    assert "name: Enforce regression gate" in action_text
    assert "steps.regression.outputs.should_fail == 'true'" in action_text


def test_action_exposes_deterministic_outputs_contract():
    action_text = Path("action.yml").read_text(encoding="utf-8")

    assert "outputs:" in action_text
    assert "gate-status:" in action_text
    assert "should-fail:" in action_text
    assert "reusability-delta:" in action_text
    assert "accessibility-risk-delta:" in action_text
    assert "steps.regression.outputs.gate_status" in action_text
    assert "steps.regression.outputs.should_fail" in action_text
    assert "steps.regression.outputs.reusability_delta" in action_text
    assert "steps.regression.outputs.accessibility_risk_delta" in action_text
    assert "reusability_delta=" in action_text
    assert "accessibility_risk_delta=" in action_text
