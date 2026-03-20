# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _git_remote_url(base_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=True,
            capture_output=True,
            text=True,
            cwd=str(base_path),
        )
    except subprocess.CalledProcessError, FileNotFoundError:
        return None
    url = result.stdout.strip()
    return url or None


def _default_branch(base_path: Path) -> str:
    head_path = base_path / ".git" / "HEAD"
    if head_path.exists():
        content = head_path.read_text(encoding="utf-8").strip()
        if content.startswith("ref:"):
            ref = content.removeprefix("ref:").strip()
            return ref.rsplit("/", 1)[-1]
    return "main"


def extract_repo_metadata(base_path: str | Path | None = None) -> dict[str, Any]:
    """
    Return a simple description of the current repository.

    The goal is to provide deterministic metadata for future connectors without
    relying on remote services.
    """
    base = Path(base_path or Path.cwd()).resolve()
    directories = sorted(
        child.name
        for child in base.iterdir()
        if child.is_dir() and not child.name.startswith(".")
    )
    metadata: dict[str, Any] = {
        "repo_name": base.name,
        "path": str(base),
        "default_branch": _default_branch(base),
        "has_git": (base / ".git").exists(),
        "remote_url": _git_remote_url(base),
        "directories": directories,
    }
    return metadata
