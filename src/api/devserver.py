from __future__ import annotations

import argparse
import importlib
import os
from wsgiref.simple_server import make_server


def _load_app(spec: str):
    module_name, _, attribute = spec.partition(":")
    if not module_name or not attribute:
        raise SystemExit("Expected an app spec in the form module:callable")
    module = importlib.import_module(module_name)
    app = getattr(module, attribute)
    if not callable(app):
        raise SystemExit("Loaded app is not callable")
    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rade-devserver", add_help=True)
    parser.add_argument("app", nargs="?", default="src.api.app:app")
    parser.add_argument("--host", default=os.environ.get("API_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("API_PORT", "8000"))
    )
    parser.add_argument(
        "--reload", action="store_true", help="Accepted for compatibility; ignored."
    )
    args, _ = parser.parse_known_args(argv)

    app = _load_app(args.app)
    with make_server(args.host, args.port, app) as server:
        print(f"Serving {args.app} on http://{args.host}:{args.port}")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
