from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .report_generator import analyze_file


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
        report = analyze_file(args.input, args.app_id, args.json_output, args.md_output)
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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
