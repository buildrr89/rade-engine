# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import importlib.util
import inspect
import io
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


class _CapturedOutput:
    """Minimal capsys-compatible capture fixture for the custom runner."""

    def __init__(self) -> None:
        self._out = io.StringIO()
        self._err = io.StringIO()

    def readouterr(self):
        import collections

        CaptureResult = collections.namedtuple("CaptureResult", ["out", "err"])
        result = CaptureResult(self._out.getvalue(), self._err.getvalue())
        self._out = io.StringIO()
        self._err = io.StringIO()
        return result


def _run_test_function(func):
    signature = inspect.signature(func)
    kwargs = {}
    needs_capsys = "capsys" in signature.parameters
    needs_tmp = "tmp_path" in signature.parameters

    if needs_capsys:
        capsys = _CapturedOutput()
        kwargs["capsys"] = capsys

    if needs_tmp:
        with TemporaryDirectory() as tempdir:
            kwargs["tmp_path"] = Path(tempdir)
            if needs_capsys:
                old_out, old_err = sys.stdout, sys.stderr
                sys.stdout = capsys._out
                sys.stderr = capsys._err
                try:
                    return func(**kwargs)
                finally:
                    sys.stdout, sys.stderr = old_out, old_err
            return func(**kwargs)

    if needs_capsys:
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout = capsys._out
        sys.stderr = capsys._err
        try:
            return func(**kwargs)
        finally:
            sys.stdout, sys.stderr = old_out, old_err

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
