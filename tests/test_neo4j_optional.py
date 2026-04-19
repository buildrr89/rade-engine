# SPDX-License-Identifier: AGPL-3.0-only
"""Slice #37: neo4j is an optional extra, not a base dependency.

These tests prove the CLI surface imports without neo4j present, and that
attempting to actually use the graph ingest path raises a clear ImportError
pointing users at the `rade-engine[graph]` extra.
"""

from __future__ import annotations

import contextlib
import importlib
import sys
from collections.abc import Iterator

import pytest


@contextlib.contextmanager
def _neo4j_hidden() -> Iterator[None]:
    """Shadow `neo4j` as unimportable for the duration of the context."""
    saved_neo4j = {
        key: sys.modules.pop(key)
        for key in list(sys.modules)
        if key == "neo4j" or key.startswith("neo4j.")
    }
    sys.modules["neo4j"] = None  # type: ignore[assignment]
    try:
        yield
    finally:
        sys.modules.pop("neo4j", None)
        for key, value in saved_neo4j.items():
            sys.modules[key] = value


def _reimport(module_names: list[str]) -> dict[str, object]:
    for name in module_names:
        sys.modules.pop(name, None)
    return {name: importlib.import_module(name) for name in module_names}


def test_cli_imports_without_neo4j() -> None:
    with _neo4j_hidden():
        modules = _reimport(["src.core.cli", "src.database.graph_ingestor"])
        assert hasattr(modules["src.core.cli"], "main")
        assert hasattr(modules["src.database.graph_ingestor"], "RadeGraphIngestor")


def test_graph_ingestor_raises_clear_error_without_neo4j() -> None:
    with _neo4j_hidden():
        modules = _reimport(["src.database.graph_ingestor"])
        graph_ingestor = modules["src.database.graph_ingestor"]

        config = graph_ingestor.Neo4jAuraConfig(
            uri="neo4j+s://example.databases.neo4j.io",
            username="neo4j",
            password="secret",
        )
        ingestor = graph_ingestor.RadeGraphIngestor(connection=config)

        with pytest.raises(ImportError) as excinfo:
            ingestor._session()

        assert "rade-engine[graph]" in str(excinfo.value)
