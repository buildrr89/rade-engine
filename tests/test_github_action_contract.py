# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from pathlib import Path


def test_action_uses_action_and_workspace_paths_for_marketplace_execution():
    action_text = Path("action.yml").read_text(encoding="utf-8")

    assert 'PYTHONPATH="${GITHUB_ACTION_PATH}"' in action_text
    assert 'INPUT_FILE="${GITHUB_WORKSPACE}/${{ inputs.input-path }}"' in action_text
    assert 'python "${GITHUB_ACTION_PATH}/scripts/pr_score_comment.py"' in action_text
