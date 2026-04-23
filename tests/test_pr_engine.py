# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import patch


def _load_pr_engine():
    root = Path(__file__).resolve().parents[1]
    gh = root / "cloud" / "api" / "gh"
    s = str(gh)
    if s not in sys.path:
        sys.path.insert(0, s)
    path = gh / "pr_engine.py"
    name = "rade_pr_engine_test"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_pe = _load_pr_engine()


def test_pr_engine_identical_base_head_no_regression() -> None:
    sample = Path("examples/sample_ios_output.json").read_bytes()

    def fetch(_t: str, _o: str, _r: str, _p: str, _ref: str) -> bytes:
        return sample

    row = {
        "repo_full_name": "o/r",
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
    }
    out = _pe.run_pr_score_pipeline(row, "fake-token", fetch_file=fetch)
    assert out["should_fail"] is False
    assert out["reusability_delta"] == 0
    assert "RADE score diff" in out["markdown"]
    assert "<!-- rade-pr-score-comment -->" in out["markdown"]


def test_pr_engine_regression_gate_toggles() -> None:
    sample = Path("examples/sample_ios_output.json").read_bytes()

    def fetch(_t: str, _o: str, _r: str, _p: str, _ref: str) -> bytes:
        return sample

    row = {
        "repo_full_name": "o/r",
        "base_sha": "a" * 40,
        "head_sha": "b" * 40,
    }
    with patch.dict(
        os.environ,
        {"RADE_FAIL_ON_REGRESSION": "false", "RADE_FAIL_ON_AXE_REGRESSION": "false"},
    ):
        out = _pe.run_pr_score_pipeline(row, "t", fetch_file=fetch)
    assert out["gate_status"] == "disabled"
    assert out["axe_gate_status"] == "disabled"
