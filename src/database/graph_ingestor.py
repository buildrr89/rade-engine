# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from ..core.models import stable_digest
from ..engine.rade_orchestrator import ConstructionGraph
from ..scrubber.edge_shield import scrub_payload_with_metadata

JsonDict = dict[str, Any]


class SessionLike(Protocol):
    def run(self, query: str, /, **parameters: Any) -> Any: ...

    def close(self) -> None: ...

    def __enter__(self) -> "SessionLike": ...

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None: ...


class DriverLike(Protocol):
    def session(self, /, **parameters: Any) -> SessionLike: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class Neo4jAuraConfig:
    """Connection parameters for a Neo4j Aura deployment."""

    uri: str
    username: str
    password: str
    database: str = "neo4j"

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Neo4jAuraConfig":
        env = os.environ if environ is None else environ
        missing = [
            name
            for name in ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD")
            if not str(env.get(name, "")).strip()
        ]
        if missing:
            missing_vars = ", ".join(missing)
            raise ValueError(
                f"Missing Neo4j Aura environment variables: {missing_vars}"
            )
        return cls(
            uri=str(env["NEO4J_URI"]).strip(),
            username=str(env["NEO4J_USERNAME"]).strip(),
            password=str(env["NEO4J_PASSWORD"]).strip(),
            database=str(env.get("NEO4J_DATABASE", "neo4j")).strip() or "neo4j",
        )


@dataclass(frozen=True)
class _ScrubbedComponent:
    node_ref: str
    element_id: str
    parent_id: str | None
    role: str
    label: str
    accessibility_identifier: str | None
    interactive: bool
    visible: bool
    bounds: list[int] | None
    hierarchy_depth: int
    child_count: int
    text_present: bool
    traits: list[str]
    slab_layer: str
    structural_fingerprint: str
    element_type: str
    functional_dna: JsonDict
    pattern_id: str
    pattern_key: str
    pattern_dna: JsonDict
    functional_dna_json: str
    pattern_dna_json: str

    def to_cypher(self) -> JsonDict:
        return {
            "node_ref": self.node_ref,
            "element_id": self.element_id,
            "parent_id": self.parent_id,
            "role": self.role,
            "label": self.label,
            "accessibility_identifier": self.accessibility_identifier,
            "interactive": self.interactive,
            "visible": self.visible,
            "bounds": self.bounds,
            "hierarchy_depth": self.hierarchy_depth,
            "child_count": self.child_count,
            "text_present": self.text_present,
            "traits": list(self.traits),
            "slab_layer": self.slab_layer,
            "structural_fingerprint": self.structural_fingerprint,
            "element_type": self.element_type,
            "functional_dna_json": self.functional_dna_json,
            "pattern_id": self.pattern_id,
            "pattern_key": self.pattern_key,
            "pattern_dna_json": self.pattern_dna_json,
        }


def _json_dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _as_bool(value: Any) -> bool:
    return bool(value)


class RadeGraphIngestor:
    """Persist scrubbed construction graphs into Neo4j Aura."""

    def __init__(
        self,
        *,
        driver: DriverLike | None = None,
        connection: Neo4jAuraConfig | None = None,
        driver_factory: Callable[[Neo4jAuraConfig], DriverLike] | None = None,
    ) -> None:
        self._driver = driver
        self._connection = connection
        self._driver_factory = driver_factory

    @property
    def connection(self) -> Neo4jAuraConfig:
        if self._connection is None:
            self._connection = Neo4jAuraConfig.from_env()
        return self._connection

    def close(self) -> None:
        driver = self._driver
        if driver is not None:
            driver.close()
            self._driver = None

    @staticmethod
    def build_pattern_lookup_query() -> str:
        return (
            "MATCH (pattern:UIPattern {pattern_id: $pattern_id}) "
            "RETURN pattern.pattern_id AS pattern_id, "
            "pattern.pattern_key AS pattern_key, "
            "pattern.pattern_dna_json AS pattern_dna_json, "
            "pattern.hierarchy_depth AS hierarchy_depth"
        )

    def ingest_screen(self, graph: ConstructionGraph) -> JsonDict:
        raw_payload = graph.to_dict()
        scrubbed_payload, scrub_metadata = scrub_payload_with_metadata(raw_payload)
        self._ensure_scrubbed_before_write(scrubbed_payload, scrub_metadata)

        screen_row = self._build_screen_row(scrubbed_payload)
        component_rows = [
            component.to_cypher()
            for component in self._build_component_rows(scrubbed_payload)
        ]
        trait_rows = self._build_trait_rows(scrubbed_payload)
        edge_rows = self._build_edge_rows(scrubbed_payload)

        with self._session() as session:
            self._write_graph(
                session, screen_row, component_rows, trait_rows, edge_rows
            )

        return {
            "screen_id": screen_row["screen_id"],
            "component_count": len(component_rows),
            "trait_count": sum(len(row["traits"]) for row in trait_rows),
            "pattern_count": len({row["pattern_id"] for row in component_rows}),
            "pattern_ids": sorted({row["pattern_id"] for row in component_rows}),
            "edge_count": len(edge_rows),
            "plumbing_edge_count": len(
                [row for row in edge_rows if row["edge_type"] != "contains"]
            ),
            "scrub_metadata": scrub_metadata,
        }

    def _session(self) -> SessionLike:
        driver = self._driver
        if driver is None:
            if self._driver_factory is not None:
                driver = self._driver_factory(self.connection)
            else:
                try:
                    from neo4j import GraphDatabase
                except Exception as exc:  # pragma: no cover - exercised when missing
                    raise RuntimeError(
                        "Neo4j driver is required to connect to Aura"
                    ) from exc
                driver = GraphDatabase.driver(
                    self.connection.uri,
                    auth=(self.connection.username, self.connection.password),
                )
            self._driver = driver
        return driver.session(database=self.connection.database)

    def _ensure_schema(self, session: SessionLike) -> None:
        statements = (
            "CREATE CONSTRAINT screen_id IF NOT EXISTS FOR (screen:Screen) "
            "REQUIRE screen.screen_id IS UNIQUE",
            "CREATE CONSTRAINT component_node_ref IF NOT EXISTS FOR (component:Component) "
            "REQUIRE component.node_ref IS UNIQUE",
            "CREATE CONSTRAINT trait_name IF NOT EXISTS FOR (trait:Trait) "
            "REQUIRE trait.trait_name IS UNIQUE",
            "CREATE CONSTRAINT pattern_id IF NOT EXISTS FOR (pattern:UIPattern) "
            "REQUIRE pattern.pattern_id IS UNIQUE",
            "CREATE CONSTRAINT destination_ref IF NOT EXISTS FOR (destination:Destination) "
            "REQUIRE destination.destination_ref IS UNIQUE",
        )
        for statement in statements:
            session.run(statement).consume()

    def _write_graph(
        self,
        session: SessionLike,
        screen_row: JsonDict,
        component_rows: Sequence[JsonDict],
        trait_rows: Sequence[JsonDict],
        edge_rows: Sequence[JsonDict],
    ) -> None:
        begin_transaction = getattr(session, "begin_transaction", None)
        if callable(begin_transaction):
            transaction = begin_transaction()
            try:
                self._ensure_schema(transaction)
                self._write_screen(transaction, screen_row)
                self._write_components(transaction, screen_row, component_rows)
                self._write_traits(transaction, trait_rows)
                self._write_edges(transaction, edge_rows)
            except Exception:
                rollback = getattr(transaction, "rollback", None)
                if callable(rollback):
                    rollback()
                raise
            else:
                commit = getattr(transaction, "commit", None)
                if callable(commit):
                    commit()
            return

        self._ensure_schema(session)
        self._write_screen(session, screen_row)
        self._write_components(session, screen_row, component_rows)
        self._write_traits(session, trait_rows)
        self._write_edges(session, edge_rows)

    def _write_screen(self, session: SessionLike, screen_row: JsonDict) -> None:
        query = (
            "MERGE (screen:Screen {screen_id: $screen_id}) "
            "SET screen.app_id = $app_id, "
            "screen.platform = $platform, "
            "screen.screen_name = $screen_name, "
            "screen.capture_source = $capture_source, "
            "screen.metadata_json = $metadata_json "
            "RETURN screen.screen_id AS screen_id"
        )
        session.run(query, **screen_row).consume()

    def _write_components(
        self,
        session: SessionLike,
        screen_row: JsonDict,
        component_rows: Sequence[JsonDict],
    ) -> None:
        if not component_rows:
            return

        query = (
            "MATCH (screen:Screen {screen_id: $screen_id}) "
            "UNWIND $components AS component "
            "MERGE (node:Component {node_ref: component.node_ref}) "
            "SET node.element_id = component.element_id, "
            "node.parent_id = component.parent_id, "
            "node.role = component.role, "
            "node.label = component.label, "
            "node.accessibility_identifier = component.accessibility_identifier, "
            "node.interactive = component.interactive, "
            "node.visible = component.visible, "
            "node.bounds = component.bounds, "
            "node.hierarchy_depth = component.hierarchy_depth, "
            "node.child_count = component.child_count, "
            "node.text_present = component.text_present, "
            "node.traits = component.traits, "
            "node.slab_layer = component.slab_layer, "
            "node.structural_fingerprint = component.structural_fingerprint, "
            "node.element_type = component.element_type, "
            "node.functional_dna_json = component.functional_dna_json, "
            "node.pattern_id = component.pattern_id, "
            "node.pattern_key = component.pattern_key, "
            "node.pattern_dna_json = component.pattern_dna_json, "
            "node.app_id = $app_id, "
            "node.screen_id = $screen_id, "
            "node.screen_name = $screen_name, "
            "node.platform = $platform, "
            "node.source = $source, "
            "node.scrubbed = true "
            "MERGE (screen)-[:HAS_COMPONENT]->(node) "
            "MERGE (pattern:UIPattern {pattern_id: component.pattern_id}) "
            "ON CREATE SET pattern.pattern_key = component.pattern_key, "
            "pattern.pattern_dna_json = component.pattern_dna_json, "
            "pattern.hierarchy_depth = component.hierarchy_depth, "
            "pattern.role = component.role, "
            "pattern.traits = component.traits, "
            "pattern.element_type = component.element_type, "
            "pattern.slab_layer = component.slab_layer, "
            "pattern.platform = $platform "
            "MERGE (node)-[:USES_PATTERN]->(pattern)"
        )
        session.run(
            query,
            screen_id=screen_row["screen_id"],
            app_id=screen_row["app_id"],
            screen_name=screen_row["screen_name"],
            platform=screen_row["platform"],
            source=screen_row["capture_source"],
            components=list(component_rows),
        ).consume()

    def _write_traits(
        self, session: SessionLike, trait_rows: Sequence[JsonDict]
    ) -> None:
        if not trait_rows:
            return

        query = (
            "UNWIND $trait_rows AS item "
            "MATCH (component:Component {node_ref: item.node_ref}) "
            "UNWIND item.traits AS trait_name "
            "MERGE (trait:Trait {trait_name: trait_name}) "
            "MERGE (component)-[:HAS_TRAIT]->(trait)"
        )
        session.run(query, trait_rows=list(trait_rows)).consume()

    def _write_edges(self, session: SessionLike, edge_rows: Sequence[JsonDict]) -> None:
        if not edge_rows:
            return

        contains_rows = [row for row in edge_rows if row["edge_type"] == "contains"]
        if contains_rows:
            session.run(
                (
                    "UNWIND $edge_rows AS edge "
                    "MATCH (source:Component {node_ref: edge.source_node_ref}) "
                    "MATCH (target:Component {node_ref: edge.target_node_ref}) "
                    "MERGE (source)-[rel:CONTAINS]->(target) "
                    "SET rel.screen_id = edge.screen_id, "
                    "rel.screen_name = edge.screen_name, "
                    "rel.metadata_json = edge.metadata_json"
                ),
                edge_rows=contains_rows,
            ).consume()

        plumbing_rows = [row for row in edge_rows if row["edge_type"] != "contains"]
        if not plumbing_rows:
            return

        session.run(
            (
                "UNWIND $edge_rows AS edge "
                "MATCH (source:Component {node_ref: edge.source_node_ref}) "
                "MERGE (destination:Destination {destination_ref: edge.destination_ref}) "
                "SET destination.destination_kind = edge.destination_kind, "
                "destination.destination_template = edge.destination_template, "
                "destination.screen_id = edge.screen_id, "
                "destination.screen_name = edge.screen_name, "
                "destination.scrubbed = true "
                "MERGE (source)-[rel:PLUMBED_TO {edge_type: edge.edge_type, destination_ref: edge.destination_ref}]->(destination) "
                "SET rel.screen_id = edge.screen_id, "
                "rel.screen_name = edge.screen_name, "
                "rel.metadata_json = edge.metadata_json"
            ),
            edge_rows=plumbing_rows,
        ).consume()

    def _build_screen_row(self, payload: JsonDict) -> JsonDict:
        return {
            "screen_id": str(payload["screen_id"]),
            "app_id": str(payload["app_id"]),
            "platform": str(payload["platform"]),
            "screen_name": str(payload["screen_name"]),
            "capture_source": str(payload["capture_source"]),
            "metadata_json": _json_dumps(payload.get("metadata", {})),
        }

    def _build_component_rows(self, payload: JsonDict) -> list[_ScrubbedComponent]:
        components: list[_ScrubbedComponent] = []
        for node in payload.get("nodes", []):
            if not isinstance(node, dict):
                continue
            functional_dna = self._normalized_functional_dna(node)
            traits = sorted(
                {str(trait) for trait in node.get("traits", []) if str(trait).strip()}
            )
            hierarchy_depth = int(node.get("hierarchy_depth", 0) or 0)
            pattern_dna = self._pattern_dna(
                functional_dna, node, traits, hierarchy_depth
            )
            pattern_dna_json = _json_dumps(pattern_dna)
            pattern_id = stable_digest(pattern_dna_json)
            components.append(
                _ScrubbedComponent(
                    node_ref=str(node["node_ref"]),
                    element_id=str(node["element_id"]),
                    parent_id=(
                        str(node["parent_id"])
                        if node.get("parent_id") is not None
                        else None
                    ),
                    role=str(node["role"]),
                    label=str(node["label"]),
                    accessibility_identifier=(
                        str(node["accessibility_identifier"])
                        if node.get("accessibility_identifier") is not None
                        else None
                    ),
                    interactive=_as_bool(node.get("interactive")),
                    visible=_as_bool(node.get("visible")),
                    bounds=(
                        list(node["bounds"])
                        if isinstance(node.get("bounds"), list)
                        else None
                    ),
                    hierarchy_depth=hierarchy_depth,
                    child_count=int(node.get("child_count", 0) or 0),
                    text_present=_as_bool(node.get("text_present")),
                    traits=traits,
                    slab_layer=str(node.get("slab_layer", "")),
                    structural_fingerprint=str(node.get("structural_fingerprint", "")),
                    element_type=str(node.get("element_type", "")),
                    functional_dna=functional_dna,
                    pattern_id=pattern_id,
                    pattern_key=pattern_dna_json,
                    pattern_dna=pattern_dna,
                    functional_dna_json=_json_dumps(functional_dna),
                    pattern_dna_json=pattern_dna_json,
                )
            )
        return components

    def _build_trait_rows(self, payload: JsonDict) -> list[JsonDict]:
        rows: list[JsonDict] = []
        for node in payload.get("nodes", []):
            if not isinstance(node, dict):
                continue
            traits = sorted(
                {str(trait) for trait in node.get("traits", []) if str(trait).strip()}
            )
            if not traits:
                continue
            rows.append(
                {
                    "node_ref": str(node["node_ref"]),
                    "traits": traits,
                }
            )
        return rows

    def _build_edge_rows(self, payload: JsonDict) -> list[JsonDict]:
        rows: list[JsonDict] = []
        for edge in payload.get("edges", []):
            if not isinstance(edge, dict):
                continue
            metadata = dict(edge.get("metadata") or {})
            rows.append(
                {
                    "source_node_ref": str(edge["source_node_ref"]),
                    "target_node_ref": str(edge["target_node_ref"]),
                    "edge_type": str(edge["edge_type"]),
                    "screen_id": str(edge["screen_id"]),
                    "screen_name": str(edge["screen_name"]),
                    "destination_kind": str(metadata.get("destination_kind", ""))
                    or None,
                    "destination_ref": str(metadata.get("destination_ref", "")) or None,
                    "destination_template": str(
                        metadata.get("destination_template", "")
                    )
                    or None,
                    "metadata_json": _json_dumps(metadata),
                }
            )
        return rows

    def _normalized_functional_dna(self, node: JsonDict) -> JsonDict:
        dna = dict(node.get("functional_dna") or {})
        return {
            "role": str(dna.get("role", node.get("role", ""))),
            "element_type": str(dna.get("element_type", node.get("element_type", ""))),
            "label": str(dna.get("label", node.get("label", ""))),
            "accessibility_identifier": (
                str(
                    dna.get(
                        "accessibility_identifier",
                        node.get("accessibility_identifier"),
                    )
                )
                if dna.get(
                    "accessibility_identifier", node.get("accessibility_identifier")
                )
                is not None
                else None
            ),
            "interactive": _as_bool(dna.get("interactive", node.get("interactive"))),
            "visible": _as_bool(dna.get("visible", node.get("visible"))),
            "bounds": dna.get("bounds", node.get("bounds")),
            "child_count": int(dna.get("child_count", node.get("child_count", 0)) or 0),
            "traits": sorted(
                {
                    str(trait)
                    for trait in (dna.get("traits", node.get("traits", [])) or [])
                    if str(trait).strip()
                }
            ),
            "slab_layer": str(dna.get("slab_layer", node.get("slab_layer", ""))),
            "structural_fingerprint": str(
                dna.get(
                    "structural_fingerprint",
                    node.get("structural_fingerprint", ""),
                )
            ),
            "structural_frame": bool(dna.get("structural_frame", False)),
            "frame_kind": (
                str(dna.get("frame_kind"))
                if dna.get("frame_kind") is not None
                else None
            ),
            "destination_kind": (
                str(dna.get("destination_kind"))
                if dna.get("destination_kind") is not None
                else None
            ),
            "destination_ref": (
                str(dna.get("destination_ref"))
                if dna.get("destination_ref") is not None
                else None
            ),
            "destination_template": (
                str(dna.get("destination_template"))
                if dna.get("destination_template") is not None
                else None
            ),
            "pattern_fingerprint": (
                str(dna.get("pattern_fingerprint"))
                if dna.get("pattern_fingerprint") is not None
                else None
            ),
        }

    def _pattern_dna(
        self,
        functional_dna: JsonDict,
        node: JsonDict,
        traits: list[str],
        hierarchy_depth: int,
    ) -> JsonDict:
        return {
            "role": str(functional_dna.get("role", node.get("role", ""))),
            "element_type": str(
                functional_dna.get("element_type", node.get("element_type", ""))
            ),
            "interactive": _as_bool(
                functional_dna.get("interactive", node.get("interactive"))
            ),
            "child_count": int(
                functional_dna.get("child_count", node.get("child_count", 0)) or 0
            ),
            "traits": traits,
            "slab_layer": str(
                functional_dna.get("slab_layer", node.get("slab_layer", ""))
            ),
            "hierarchy_depth": hierarchy_depth,
            "structural_fingerprint": str(
                functional_dna.get(
                    "structural_fingerprint",
                    node.get("structural_fingerprint", ""),
                )
            ),
            "structural_frame": bool(functional_dna.get("structural_frame", False)),
            "frame_kind": functional_dna.get("frame_kind"),
            "destination_kind": functional_dna.get("destination_kind"),
            "destination_template": functional_dna.get("destination_template"),
            "pattern_fingerprint": functional_dna.get("pattern_fingerprint"),
        }

    def _ensure_scrubbed_before_write(
        self,
        scrubbed_payload: JsonDict,
        scrub_metadata: JsonDict,
    ) -> None:
        if not bool(scrub_metadata.get("is_scrubbed")):
            raise RuntimeError(
                "edge_shield metadata reported is_scrubbed=False; aborting graph write"
            )
        if scrubbed_payload is None:
            raise RuntimeError("scrubbed payload missing before Neo4j persistence")
