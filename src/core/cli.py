# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import argparse
from json import JSONDecodeError
from pathlib import Path
from time import perf_counter
from typing import Sequence

from ..collectors.web_dom_adapter import collect_from_web_dom, derive_app_id_from_url
from .badge import SUPPORTED_METRICS, BadgeError, write_badge
from .compliance import emit_terminal_banner
from .metrics import increment_counter, publish_metrics, record_duration
from .report_diff import (
    build_report_diff,
    load_diffable_report,
    report_diff_error,
    write_report_diff,
)
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
        "--html-output", type=Path, help="Where to write the interactive HTML report."
    )
    analyze.add_argument(
        "--collector-timeout-ms",
        type=int,
        default=10_000,
        help="Timeout for Playwright page collection when using --url.",
    )
    analyze.add_argument(
        "--axe",
        action="store_true",
        help=(
            "Run axe-core against the page during --url collection and embed "
            "the violations in the report with provenance 'axe-core'."
        ),
    )

    diff = subparsers.add_parser(
        "diff", help="Compare two RADE JSON reports and write diff artifacts."
    )
    diff.add_argument(
        "--base-report", type=Path, required=True, help="Path to the base JSON report."
    )
    diff.add_argument(
        "--head-report", type=Path, required=True, help="Path to the head JSON report."
    )
    diff.add_argument(
        "--json-output",
        type=Path,
        default=Path("output/report_diff.json"),
        help="Where to write the JSON diff artifact.",
    )
    diff.add_argument(
        "--md-output",
        type=Path,
        default=Path("output/report_diff.md"),
        help="Where to write the Markdown diff artifact.",
    )

    badge = subparsers.add_parser(
        "badge",
        help="Render a deterministic SVG score badge from a RADE JSON report.",
    )
    badge.add_argument(
        "--report", type=Path, required=True, help="Path to a RADE JSON report."
    )
    badge.add_argument(
        "--metric",
        choices=SUPPORTED_METRICS,
        required=True,
        help="Which score to render.",
    )
    badge.add_argument(
        "--svg-output",
        type=Path,
        help="Where to write the SVG badge.",
    )
    badge.add_argument(
        "--endpoint-output",
        type=Path,
        help="Where to write a shields.io dynamic endpoint JSON.",
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
                if args.axe:
                    parser.error("--axe requires --url (axe runs on live pages).")
                report = analyze_file(
                    args.input,
                    args.app_id,
                    args.json_output,
                    args.md_output,
                    args.html_output,
                )
            else:
                app_id = args.app_id or derive_app_id_from_url(args.url)
                payload = collect_from_web_dom(
                    args.url,
                    timeout_ms=args.collector_timeout_ms,
                    run_axe=args.axe,
                )
                axe_findings = payload.pop("_axe_findings", None)
                raw_report = analyze_payload(payload, app_id, axe_findings=axe_findings)
                write_report(
                    raw_report,
                    args.json_output,
                    args.md_output,
                    args.html_output,
                )
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
            if args.html_output:
                print(f"html: {args.html_output}")
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
    if args.command == "diff":
        for path in (args.base_report, args.head_report):
            try:
                report = load_diffable_report(path)
            except (FileNotFoundError, JSONDecodeError, ValueError) as exc:
                parser.error(report_diff_error(path, exc))
            if path == args.base_report:
                base_report = report
            else:
                head_report = report

        diff = build_report_diff(base_report, head_report)
        write_report_diff(diff, json_output=args.json_output, md_output=args.md_output)
        print("generated report diff")
        print(f"json: {args.json_output}")
        print(f"md: {args.md_output}")
        return 0
    if args.command == "badge":
        if args.svg_output is None and args.endpoint_output is None:
            parser.error("--svg-output or --endpoint-output is required.")
        try:
            value = write_badge(
                args.report,
                args.metric,
                svg_output=args.svg_output,
                endpoint_output=args.endpoint_output,
            )
        except BadgeError as exc:
            parser.error(str(exc))
        print(f"generated badge for {args.metric}: {value}/100")
        if args.svg_output:
            print(f"svg: {args.svg_output}")
        if args.endpoint_output:
            print(f"endpoint: {args.endpoint_output}")
        return 0
    return 1


if __name__ == "__main__":
    emit_terminal_banner()
    raise SystemExit(main())
