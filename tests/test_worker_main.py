# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from src.worker.main import main


def test_worker_shell_emits_stage_logs_and_ready_message():
    stdout = StringIO()
    stderr = StringIO()

    with redirect_stdout(stdout), redirect_stderr(stderr):
        exit_code = main(["--once"])

    assert exit_code == 0
    assert "RADE worker shell ready (one cycle)" in stdout.getvalue()
    assert '"component": "worker"' in stderr.getvalue()
    assert '"stage": "claim_job"' in stderr.getvalue()
    assert '"stage": "run_cli"' in stderr.getvalue()
    assert '"stage": "complete_job"' in stderr.getvalue()
