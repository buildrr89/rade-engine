# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter
from typing import Sequence

from .compliance import emit_terminal_banner
from .metrics import increment_counter, publish_metrics, record_duration
from .report_generator import analyze_file, get_last_run_metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rade")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser(
        "analyze", help="Analyze a fixture and write a report."
    )
    analyze.add_argument(
        "--input", required=True, help="Path to the JSON input fixture."
    )
    analyze.add_argument("--app-id", required=True, help="Application identifier.")
    analyze.add_argument(
        "--json-output", type=Path, help="Where to write the JSON report."
    )
    analyze.add_argument(
        "--md-output", type=Path, help="Where to write the Markdown report."
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        increment_counter("proof_runs.read")
        start = perf_counter()
        run_status = "failure"
        try:
            report = analyze_file(
                args.input, args.app_id, args.json_output, args.md_output
            )
            run_status = "success"
            print(
                "generated",
                report["summary"]["screen_count"],
                "screens and",
                report["summary"]["recommendation_count"],
                "recommendations",
            )
            if args.json_output:
                print(f"json: {args.json_output}")
            if args.md_output:
                print(f"md: {args.md_output}")
            return 0
        finally:
            duration_ms = int((perf_counter() - start) * 1000)
            metadata = get_last_run_metadata() or {}
            run_id = metadata.get("run_id")
            if run_status == "success":
                increment_counter("proof_runs.success")
            else:
                increment_counter("proof_runs.failure")
            record_duration("proof_runs.duration", duration_ms)
            publish_metrics(run_id=run_id, component="cli", job_status=run_status)
    return 1


if __name__ == "__main__":
    emit_terminal_banner()
    raise SystemExit(main())
