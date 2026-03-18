from __future__ import annotations

from pathlib import Path
from typing import Any

from ..core.schemas import load_json_file


def load_fixture(path: Path | str) -> dict[str, Any]:
    return load_json_file(Path(path))
