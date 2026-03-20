# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory

from src.core.compliance import emit_terminal_banner


def _discover_test_files(selection: list[str]) -> list[Path]:
    if selection:
        files: list[Path] = []
        for item in selection:
            path = Path(item)
            if path.is_dir():
                files.extend(sorted(path.glob("test_*.py")))
            elif path.suffix == ".py":
                files.append(path)
        return files
    return sorted(Path("tests").glob("test_*.py"))


def _run_test_function(func):
    signature = inspect.signature(func)
    kwargs = {}
    if "tmp_path" in signature.parameters:
        with TemporaryDirectory() as tempdir:
            kwargs["tmp_path"] = Path(tempdir)
            return func(**kwargs)
    return func()


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    selection = [arg for arg in argv if not arg.startswith("-")]
    files = _discover_test_files(selection)
    failures: list[str] = []
    passes = 0

    for path in files:
        module = _load_module(path)
        for name, value in sorted(module.__dict__.items()):
            if name.startswith("test_") and callable(value):
                try:
                    _run_test_function(value)
                    passes += 1
                except Exception:
                    failures.append(f"{path}:{name}\n{traceback.format_exc()}")

    if failures:
        print(f"{passes} passed, {len(failures)} failed")
        for failure in failures:
            print(failure)
        return 1

    print(f"{passes} passed, 0 failed")
    return 0


if __name__ == "__main__":
    emit_terminal_banner()
    raise SystemExit(main())
