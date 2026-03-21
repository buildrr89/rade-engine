# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import argparse
from typing import Sequence

from src.core.cli import main as core_main
from src.core.compliance import emit_terminal_banner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rade-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser(
        "scan", help="Run the analysis proof slice through the agent shell."
    )
    scan.add_argument("--input", required=True)
    scan.add_argument("--app-id", required=True)
    scan.add_argument("--json-output")
    scan.add_argument("--md-output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "scan":
        forwarded = [
            "analyze",
            "--input",
            args.input,
            "--app-id",
            args.app_id,
        ]
        if args.json_output:
            forwarded.extend(["--json-output", args.json_output])
        if args.md_output:
            forwarded.extend(["--md-output", args.md_output])
        return core_main(forwarded)
    return 1


if __name__ == "__main__":
    emit_terminal_banner()
    raise SystemExit(main())
