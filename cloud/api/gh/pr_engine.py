# Proprietary — RADE Cloud. See cloud/LICENSE.
"""Fetch fixture JSON at base/head from GitHub, run RADE :func:`analyze_file`, and diff.

Mirrors the GitHub Action’s ``action.yml`` path (``analyze_file`` →
``pr_score_diff``) without subprocess.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Final

_GH: Final[Path] = Path(__file__).resolve().parent
_REPO_ROOT: Final[Path] = _GH.parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import gh_app_client  # noqa: E402
from src.core.pr_score_diff import (  # noqa: E402
    axe_regression_reason,
    build_axe_diff,
    build_score_diff,
    has_axe_regression,
    has_score_regression,
    load_report,
    regression_reason,
    render_pr_comment,
)
from src.core.report_generator import analyze_file  # noqa: E402

_Fetcher = Callable[[str, str, str, str, str], bytes]


def _default_fail_score() -> bool:
    v = (os.environ.get("RADE_FAIL_ON_REGRESSION") or "true").strip().lower()
    return v in {"1", "true", "yes"}


def _default_fail_axe() -> bool:
    v = (os.environ.get("RADE_FAIL_ON_AXE_REGRESSION") or "true").strip().lower()
    return v in {"1", "true", "yes"}


def _input_path() -> str:
    return (
        os.environ.get("RADE_INPUT_PATH") or "examples/sample_ios_output.json"
    ).strip()


def _app_id() -> str:
    return (os.environ.get("RADE_APP_ID") or "com.example.legacyapp").strip()


def _default_fetch(token: str, owner: str, repo: str, path: str, ref: str) -> bytes:
    return gh_app_client.get_repository_file_bytes(token, owner, repo, path, ref)


def run_pr_score_pipeline(
    row: dict[str, Any],
    installation_token: str,
    fetch_file: _Fetcher | None = None,
) -> dict[str, Any]:
    """Run RADE on base/head input fixtures, compute gates and comment markdown."""
    _fetch: _Fetcher = fetch_file or _default_fetch

    sp = gh_app_client.split_repo_full_name((row.get("repo_full_name") or "").strip())
    if not sp:
        raise gh_app_client.GitHubAppError("row missing repo_full_name")
    owner, repo = sp

    bsha = row.get("base_sha")
    hsha = row.get("head_sha")
    if not isinstance(bsha, str) or not isinstance(hsha, str):
        raise gh_app_client.GitHubAppError("row missing base_sha or head_sha")

    in_rel = _input_path()
    app = _app_id()
    bbytes = _fetch(installation_token, owner, repo, in_rel, bsha)
    hbytes = _fetch(installation_token, owner, repo, in_rel, hsha)

    with tempfile.TemporaryDirectory() as tdir:
        tpath = Path(tdir)
        binp = tpath / "base_in.json"
        hinp = tpath / "head_in.json"
        bjson = tpath / "base_report.json"
        hjson = tpath / "head_report.json"
        binp.write_bytes(bbytes)
        hinp.write_bytes(hbytes)

        analyze_file(binp, app, json_output=bjson)
        analyze_file(hinp, app, json_output=hjson)

        base_report = load_report(bjson)
        head_report = load_report(hjson)
        sdiff = build_score_diff(base_report, head_report)
        adiff = build_axe_diff(base_report, head_report)
        hsr = has_score_regression(sdiff)
        har = has_axe_regression(adiff)

    rscore = _default_fail_score()
    raxe = _default_fail_axe()

    if rscore and hsr:
        gscore2 = "enabled:failed"
    elif rscore:
        gscore2 = "enabled:passed"
    else:
        gscore2 = "disabled"

    if raxe and har:
        gaxe2 = "enabled:failed"
    elif raxe:
        gaxe2 = "enabled:passed"
    else:
        gaxe2 = "disabled"

    should_fail = (rscore and hsr) or (raxe and har)
    body = render_pr_comment(
        sdiff,
        bsha[:7],
        hsha[:7],
        gate_status=gscore2,
        axe_diff=adiff,
        axe_gate_status=gaxe2,
    )
    return {
        "input_path": in_rel,
        "regression_reason": regression_reason(sdiff),
        "axe_regression_reason": axe_regression_reason(adiff),
        "regression_detected": hsr,
        "axe_regression_detected": har,
        "gate_status": gscore2,
        "axe_gate_status": gaxe2,
        "reusability_delta": sdiff["reusability"]["delta"],
        "accessibility_risk_delta": sdiff["accessibility_risk"]["delta"],
        "should_fail": should_fail,
        "markdown": body,
    }
