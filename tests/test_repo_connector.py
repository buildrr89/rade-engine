# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from pathlib import Path

from src.connectors.repo_connector import extract_repo_metadata


def _expected_default_branch(repo_root: Path) -> str:
    head = repo_root / ".git" / "HEAD"
    if head.exists():
        content = head.read_text(encoding="utf-8").strip()
        if content.startswith("ref:"):
            ref = content.removeprefix("ref:").strip()
            return ref.rsplit("/", 1)[-1]
    return "main"


def test_repo_connector_returns_repo_shape():
    repo_root = Path.cwd().resolve()
    metadata = extract_repo_metadata(repo_root)

    assert metadata["repo_name"] == repo_root.name
    assert metadata["path"] == str(repo_root)
    assert metadata["default_branch"] == _expected_default_branch(repo_root)
    assert metadata["has_git"] is True
    assert isinstance(metadata["directories"], list)
    assert "docs" in metadata["directories"]
    remote_url = metadata["remote_url"]
    assert remote_url is None or isinstance(remote_url, str)
