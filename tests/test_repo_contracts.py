# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _assert_contains_all(text: str, snippets: list[str]) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    assert not missing, f"Missing snippets: {missing}"


def test_proof_workflow_contains_required_guardrails():
    workflow = _read(".github/workflows/proof.yml")
    _assert_contains_all(
        workflow,
        [
            "name: Proof",
            "pull_request:",
            "branches:\n      - main",
            "proof:\n    runs-on: ubuntu-latest",
            "python-version-file: .python-version",
            "node-version-file: .node-version",
            "uv sync --dev",
            "pnpm --dir web install --frozen-lockfile",
            "./rade-proof",
            "uv run ruff check src tests agent",
            "uv run black --check src tests agent",
            "pnpm --dir web lint",
            "pnpm --dir web test",
            "uv run python -m src.core.cli analyze",
            "Publish proof summary",
        ],
    )


def test_codeql_workflow_contains_required_guardrails():
    workflow = _read(".github/workflows/codeql.yml")
    _assert_contains_all(
        workflow,
        [
            "name: CodeQL",
            "pull_request:",
            "branches:\n      - main",
            'cron: "0 6 * * 1"',
            "security-events: write",
            "matrix:\n        language: [python, javascript]",
            "github/codeql-action/init@v3",
            "github/codeql-action/autobuild@v3",
            "github/codeql-action/analyze@v3",
        ],
    )


def test_pull_request_template_covers_required_sections():
    template = _read(".github/pull_request_template.md")
    _assert_contains_all(
        template,
        [
            "## Problem",
            "## Why now",
            "## Scope",
            "## Non-scope",
            "## Acceptance criteria",
            "## What changed",
            "## Docs and contracts updated",
            "## Verification",
            "## Exact proof outputs",
            "## Risks",
            "## Security impact",
            "## Scalability / performance impact",
            "## Open decisions / unknowns",
        ],
    )


def test_issue_templates_and_config_require_decisions():
    bug_template = _read(".github/ISSUE_TEMPLATE/bug_report.md")
    feature_template = _read(".github/ISSUE_TEMPLATE/feature_request.md")
    issue_config = _read(".github/ISSUE_TEMPLATE/config.yml")

    _assert_contains_all(
        bug_template,
        [
            "## What happened",
            "## Expected",
            "## Scope of impact",
            "## Evidence",
            "## Reproduction steps",
            "## Security / data exposure risk",
            "## Unknowns / decisions",
        ],
    )
    _assert_contains_all(
        feature_template,
        [
            "## Problem",
            "## Why now",
            "## Scope",
            "## Non-scope",
            "## Proposed change",
            "## Acceptance criteria",
            "## Verification plan",
            "## Security / scalability notes",
            "## Unknowns / decisions",
        ],
    )
    assert "blank_issues_enabled: false" in issue_config
