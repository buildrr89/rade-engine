# Proprietary — RADE Cloud. See cloud/LICENSE.
"""GitHub App installation token, Check Runs, and issue comments (urllib + PyJWT)."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Final

# Monorepo root (so ``from src...`` works in Vercel + tests).
_RE_ROOT = Path(__file__).resolve().parents[3]
if str(_RE_ROOT) not in sys.path:
    sys.path.insert(0, str(_RE_ROOT))

_GITHUB_API: Final[str] = "https://api.github.com"
_API_VERSION: Final[str] = "2022-11-28"
_UA: Final[str] = "RADE-Cloud-Worker/0.4.0"


class GitHubAppError(Exception):
    """Configuration or API failure for GitHub App calls."""


def split_repo_full_name(full: str) -> tuple[str, str] | None:
    if full.count("/") != 1:
        return None
    owner, name = full.split("/", 1)
    if not owner or not name:
        return None
    return owner, name


def _app_jwt() -> str:
    import jwt  # PyJWT

    app_id = (os.environ.get("GITHUB_APP_ID") or "").strip()
    raw_key = (
        (os.environ.get("GITHUB_APP_PRIVATE_KEY") or "").strip().replace("\\n", "\n")
    )
    if not app_id or not raw_key:
        raise GitHubAppError("missing GITHUB_APP_ID or GITHUB_APP_PRIVATE_KEY")
    now = int(time.time())
    payload: dict[str, Any] = {
        "iat": now - 60,
        "exp": now + 9 * 60,
        "iss": int(app_id),
    }
    return jwt.encode(payload, raw_key, algorithm="RS256")


def installation_access_token(installation_id: int) -> str:
    """Exchange a short-lived JWT for a 1-hour installation token."""
    token = _app_jwt()
    url = f"{_GITHUB_API}/app/installations/{installation_id}/access_tokens"
    req = urllib.request.Request(  # noqa: S310
        url,
        method="POST",
        data=b"{}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": _UA,
            "Content-Type": "application/json",
        },
    )
    return _read_json_request(req, "installation token")["token"]


def get_repository_file_bytes(
    token: str, owner: str, repo: str, file_path: str, ref: str
) -> bytes:
    """Fetch a file from a repo at a commit; returns raw bytes (decodes base64)."""
    import base64
    from urllib.parse import quote

    p = quote(file_path.strip().lstrip("/"), safe="")
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/contents/{p}?ref={ref}"
    req = urllib.request.Request(  # noqa: S310
        url,
        method="GET",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": _UA,
        },
    )
    out = _read_json_request(req, "git contents")
    content = out.get("content")
    enc = (out.get("encoding") or "base64").lower()
    if not isinstance(content, str):
        raise GitHubAppError("contents: no content")
    if enc != "base64":
        raise GitHubAppError("contents: unexpected encoding")
    return base64.b64decode("".join(content.split()))


def _read_json_request(req: urllib.request.Request, ctx: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubAppError(f"{ctx} HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise GitHubAppError(f"{ctx} URL error: {exc.reason!r}") from exc
    if not raw:
        return {}
    try:
        out = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GitHubAppError(f"{ctx} invalid json") from exc
    if not isinstance(out, dict):
        raise GitHubAppError(f"{ctx} expected object")
    return out


def create_check_run(
    token: str,
    owner: str,
    repo: str,
    *,
    name: str,
    head_sha: str,
    conclusion: str,
    title: str,
    summary: str,
) -> int:
    """Create a **completed** check run. Returns check run id."""
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/check-runs"
    payload = {
        "name": name,
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": conclusion,
        "output": {
            "title": title,
            "summary": summary,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        url,
        method="POST",
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": _UA,
            "Content-Type": "application/json",
        },
    )
    out = _read_json_request(req, "check run")
    cid = out.get("id")
    if not isinstance(cid, int):
        raise GitHubAppError("check run: missing id")
    return cid


def create_pr_issue_comment(
    token: str,
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
) -> None:
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    data = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        url,
        method="POST",
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": _UA,
            "Content-Type": "application/json",
        },
    )
    _read_json_request(req, "issue comment")


def list_issue_comments(
    token: str, owner: str, repo: str, issue_number: int
) -> list[dict[str, Any]]:
    """List all issue (PR) comments (paginated)."""
    all_rows: list[dict[str, Any]] = []
    page = 1
    while True:
        path = f"/repos/{owner}/{repo}/issues/{issue_number}/comments?per_page=100&page={page}"
        url = f"{_GITHUB_API}{path}"
        req = urllib.request.Request(  # noqa: S310
            url,
            method="GET",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": _API_VERSION,
                "User-Agent": _UA,
            },
        )
        # Returns JSON array
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GitHubAppError(
                f"list comments HTTP {exc.code}: {body[:500]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise GitHubAppError(f"list comments URL: {exc.reason!r}") from exc
        if not raw:
            break
        data = json.loads(raw)
        if not isinstance(data, list):
            raise GitHubAppError("list comments: expected array")
        for item in data:
            if isinstance(item, dict):
                all_rows.append(item)
        if len(data) < 100:
            break
        page += 1
    return all_rows


def update_issue_comment(
    token: str, owner: str, repo: str, comment_id: int, body: str
) -> None:
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/issues/comments/{comment_id}"
    data = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        url,
        method="PATCH",
        data=data,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": _API_VERSION,
            "User-Agent": _UA,
            "Content-Type": "application/json",
        },
    )
    _read_json_request(req, "update comment")


def upsert_rade_pr_comment(
    token: str,
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
    marker: str,
) -> str:
    """Create or update the PR comment that contains ``marker``. Returns ``created``|``updated``."""
    comments = list_issue_comments(token, owner, repo, issue_number)
    for c in comments:
        cbody = c.get("body")
        cid = c.get("id")
        if isinstance(cbody, str) and marker in cbody and isinstance(cid, int):
            update_issue_comment(token, owner, repo, cid, body)
            return "updated"
    create_pr_issue_comment(token, owner, repo, issue_number, body)
    return "created"


def post_pr_status_for_row(row: dict[str, Any]) -> dict[str, Any]:
    """Create Check Run + PR comment for a claimed ``pr_analysis`` row. Returns a small log.

    Skips with ``skipped`` in the result when the GitHub App is not configured
    (same behavior as a dry run in local dev).
    """
    if row.get("work_kind") != "pr_analysis":
        return {"skipped": "not_pr_analysis"}

    parts = (row.get("repo_full_name") or "").strip()
    sp = split_repo_full_name(parts)
    if not sp:
        raise GitHubAppError("row missing repo_full_name")
    owner, repo = sp

    iid = row.get("installation_id")
    if iid is None:
        raise GitHubAppError("row missing installation_id")
    installation_id = int(iid)

    head = row.get("head_sha")
    if not isinstance(head, str) or len(head) < 7:
        raise GitHubAppError("row missing head_sha")

    prn = row.get("pr_number")
    if prn is None:
        raise GitHubAppError("row missing pr_number")
    pr_num = int(prn)

    if not (
        os.environ.get("GITHUB_APP_ID") and os.environ.get("GITHUB_APP_PRIVATE_KEY")
    ):
        return {
            "skipped": "github_app_not_configured",
            "repo": parts,
        }

    from pr_engine import run_pr_score_pipeline  # noqa: PLC0415
    from src.core.pr_score_diff import COMMENT_MARKER

    token = installation_access_token(installation_id)
    rid = str(row.get("id", ""))
    pl = run_pr_score_pipeline(row, token)
    should_fail = bool(pl.get("should_fail"))
    conclusion = "failure" if should_fail else "success"
    summary = (
        f"Reusability Δ {pl['reusability_delta']}, accessibility_risk Δ "
        f"{pl['accessibility_risk_delta']}. Score gate `{pl['gate_status']}`, "
        f"axe gate `{pl['axe_gate_status']}`."
    )[:6_000]
    check_id = create_check_run(
        token,
        owner,
        repo,
        name="RADE",
        head_sha=head,
        conclusion=conclusion,
        title="RADE score + axe diff",
        summary=summary,
    )
    cstat = upsert_rade_pr_comment(
        token,
        owner,
        repo,
        pr_num,
        pl["markdown"],
        COMMENT_MARKER,
    )
    eng = {k: v for k, v in pl.items() if k != "markdown"}
    return {
        "check_run_id": check_id,
        "repo": parts,
        "run_row_id": rid,
        "check_conclusion": conclusion,
        "comment": cstat,
        "engine": eng,
    }
