# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import argparse
from pathlib import Path

from src.core.pr_score_diff import build_score_diff, load_report, render_pr_comment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pr-score-comment",
        description="Build a PR markdown comment for RADE score deltas.",
    )
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--head-report", type=Path, required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--gate-status", default="disabled")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    base_report = load_report(args.base_report)
    head_report = load_report(args.head_report)
    diff = build_score_diff(base_report, head_report)
    comment = render_pr_comment(
        diff, args.base_ref, args.head_ref, gate_status=args.gate_status
    )
    args.output.write_text(comment, encoding="utf-8")
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
