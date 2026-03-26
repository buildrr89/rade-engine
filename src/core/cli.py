# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import argparse
from pathlib import Path
from time import perf_counter
from typing import Sequence

from ..collectors.web_dom_adapter import collect_from_web_dom, derive_app_id_from_url
from .compliance import emit_terminal_banner
from .metrics import increment_counter, publish_metrics, record_duration
from .report_generator import (
    analyze_file,
    analyze_payload,
    get_last_run_metadata,
    prepare_report_for_output,
    write_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rade")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser(
        "analyze", help="Analyze a fixture and write a report."
    )
    source = analyze.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="Path to the JSON input fixture.")
    source.add_argument(
        "--url",
        help="Public http/https URL to collect with the Playwright web collector.",
    )
    analyze.add_argument("--app-id", help="Application identifier.")
    analyze.add_argument(
        "--json-output", type=Path, help="Where to write the JSON report."
    )
    analyze.add_argument(
        "--md-output", type=Path, help="Where to write the Markdown report."
    )
    analyze.add_argument(
        "--collector-timeout-ms",
        type=int,
        default=10_000,
        help="Timeout for Playwright page collection when using --url.",
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
            if args.input:
                if not args.app_id:
                    parser.error("--app-id is required when using --input.")
                report = analyze_file(
                    args.input, args.app_id, args.json_output, args.md_output
                )
            else:
                app_id = args.app_id or derive_app_id_from_url(args.url)
                payload = collect_from_web_dom(
                    args.url, timeout_ms=args.collector_timeout_ms
                )
                raw_report = analyze_payload(payload, app_id)
                write_report(raw_report, args.json_output, args.md_output)
                report = prepare_report_for_output(raw_report)
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
