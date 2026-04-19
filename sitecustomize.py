# SPDX-License-Identifier: AGPL-3.0-only
import sys

# Only emit the banner when stdout is an interactive terminal. Tools like
# `uv run` introspect the venv's interpreter by parsing its stdout as JSON;
# an unconditional print here corrupts that parse and breaks the proof
# workflow. CLI entry points (agent/cli.py, tests/runner.py, src/core/cli.py)
# still call emit_terminal_banner() explicitly for user-facing invocations.
if sys.stdout.isatty():
    from src.core.compliance import emit_terminal_banner

    emit_terminal_banner()
