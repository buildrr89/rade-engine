from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rade-worker")
    parser.add_argument(
        "--once", action="store_true", help="Run a single no-op worker cycle."
    )
    parser.parse_args(argv)
    print("RADE worker shell ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
