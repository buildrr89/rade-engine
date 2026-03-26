# SPDX-License-Identifier: AGPL-3.0-only
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
    source = scan.add_mutually_exclusive_group(required=True)
    source.add_argument("--input")
    source.add_argument("--url")
    scan.add_argument("--app-id")
    scan.add_argument("--json-output")
    scan.add_argument("--md-output")
    scan.add_argument("--collector-timeout-ms")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "scan":
        forwarded = ["analyze"]
        if args.input:
            if not args.app_id:
                parser.error("--app-id is required when using --input.")
            forwarded.extend(["--input", args.input, "--app-id", args.app_id])
        else:
            forwarded.extend(["--url", args.url])
            if args.app_id:
                forwarded.extend(["--app-id", args.app_id])
        if args.json_output:
            forwarded.extend(["--json-output", args.json_output])
        if args.md_output:
            forwarded.extend(["--md-output", args.md_output])
        if args.collector_timeout_ms:
            forwarded.extend(["--collector-timeout-ms", args.collector_timeout_ms])
        return core_main(forwarded)
    return 1


if __name__ == "__main__":
    emit_terminal_banner()
    raise SystemExit(main())
