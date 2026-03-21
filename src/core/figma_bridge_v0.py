# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
"""Figma Bridge v0 — deterministic manifest from captured graph nodes.

Emits one component row per distinct ``slab03_frame_id`` so downstream tooling can
map Slab 03 frames to Figma component candidates. ``ref_map`` records Slab 04
plumbing edges as cross-frame (or internal) wires. ``variant_axes`` is reserved
for Tier 2 pattern promotion and is empty in v0.2.2.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Sequence

from .compliance import with_legal_metadata
from .models import stable_digest

JsonDict = dict[str, Any]

MANIFEST_VERSION = "0.2.2"
BRIDGE_KIND = "rade_figma_bridge_v0"
_SAMPLE_NODE_REF_LIMIT = 5
_PATTERN_FINGERPRINT_LIMIT = 8

# Slab 04 interactive plumbing (non-hierarchy edges from ConstructionGraph).
_PLUMBING_EDGE_TYPES = frozenset({"routes_to", "submits_to", "controls", "triggers"})


def _dna(node: JsonDict) -> JsonDict:
    raw = node.get("functional_dna")
    return raw if isinstance(raw, dict) else {}


def _slab03_frame_id(node: JsonDict) -> str | None:
    top = node.get("slab03_frame_id")
    if top is not None and str(top).strip():
        return str(top).strip()
    raw = _dna(node).get("slab03_frame_id")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _slab03_anchor_kind(node: JsonDict) -> str | None:
    top = node.get("slab03_anchor_kind")
    if top is not None and str(top).strip():
        return str(top).strip()
    raw = _dna(node).get("slab03_anchor_kind")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _slab03_figma_alias(node: JsonDict) -> str | None:
    raw = _dna(node).get("slab03_figma_alias")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _slab03_landmark_kind(node: JsonDict) -> str | None:
    raw = _dna(node).get("slab03_landmark_kind")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _pattern_fingerprint(node: JsonDict) -> str | None:
    raw = _dna(node).get("pattern_fingerprint")
    if raw is not None and str(raw).strip():
        return str(raw).strip()
    return None


def _design_tokens(node: JsonDict) -> JsonDict:
    raw = _dna(node).get("design_tokens")
    if not isinstance(raw, dict):
        return {"color_tokens": [], "typography_tokens": [], "spacing_tokens": []}
    colors = raw.get("color_tokens")
    typos = raw.get("typography_tokens")
    spacing = raw.get("spacing_tokens")
    return {
        "color_tokens": (
            sorted(str(item).strip() for item in colors if str(item).strip())
            if isinstance(colors, list)
            else []
        ),
        "typography_tokens": (
            sorted(str(item).strip() for item in typos if str(item).strip())
            if isinstance(typos, list)
            else []
        ),
        "spacing_tokens": (
            sorted(str(item).strip() for item in spacing if str(item).strip())
            if isinstance(spacing, list)
            else []
        ),
    }


def _anchor_family(kind: str | None) -> str:
    if not kind:
        return "unknown"
    if "dialog" in kind:
        return "modal"
    if "landmark" in kind:
        return "landmark"
    return "other"


def _action_type_for_edge(edge_type: str) -> str:
    """Normalize orchestrator edge_type to an agent-oriented action label."""
    return {
        "triggers": "click",
        "routes_to": "navigate",
        "submits_to": "submit",
        "controls": "control",
    }.get(edge_type, edge_type)


def _wire_action_type(edge: JsonDict, edge_type: str) -> str:
    meta = edge.get("metadata")
    if isinstance(meta, dict):
        raw = meta.get("action_type")
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    return _action_type_for_edge(edge_type)


def _plumbing_scope(
    source_frame_id: str | None, target_frame_id: str | None
) -> str:
    if source_frame_id is None:
        return "unresolved_source"
    if target_frame_id is None:
        return "unresolved_target"
    if source_frame_id == target_frame_id:
        return "internal"
    return "external"


def _index_nodes_by_ref(nodes: Sequence[JsonDict]) -> dict[str, JsonDict]:
    out: dict[str, JsonDict] = {}
    for node in nodes:
        ref = node.get("node_ref")
        if ref is not None and str(ref).strip():
            out[str(ref).strip()] = node
    return out


def build_ref_map(
    nodes: Sequence[JsonDict], edges: Sequence[JsonDict] | None
) -> JsonDict:
    """Slab 04 ref-map: wires between Slab 03 frames from interactive graph edges."""

    by_ref = _index_nodes_by_ref(nodes)
    raw_edges = edges or ()
    wires: list[JsonDict] = []
    for edge in raw_edges:
        et = edge.get("edge_type")
        if et not in _PLUMBING_EDGE_TYPES:
            continue
        sn = str(edge.get("source_node_ref") or "").strip()
        tn = str(edge.get("target_node_ref") or "").strip()
        if not sn or not tn:
            continue
        src_node = by_ref.get(sn, {})
        tgt_node = by_ref.get(tn, {})
        source_frame_id = _slab03_frame_id(src_node)
        target_frame_id = _slab03_frame_id(tgt_node)
        scope = _plumbing_scope(source_frame_id, target_frame_id)
        wires.append(
            {
                "source_node_ref": sn,
                "target_node_ref": tn,
                "source_frame_id": source_frame_id,
                "target_frame_id": target_frame_id,
                "edge_type": str(et),
                "action_type": _wire_action_type(edge, str(et)),
                "plumbing_scope": scope,
            }
        )

    wires.sort(
        key=lambda w: (
            w["source_node_ref"],
            w["target_node_ref"],
            w["edge_type"],
        )
    )
    return {
        "wires": wires,
        "wire_count": len(wires),
        "note": (
            "Slab 04 interactive edges mapped to Slab 03 frames; "
            "plumbing_scope internal = same frame, external = cross-frame, "
            "unresolved_* = missing frame on source or target node."
        ),
    }


def build_figma_bridge_v0_manifest(
    *,
    app_id: str,
    platform: str,
    screen_id: str,
    screen_name: str,
    nodes: Sequence[JsonDict],
    edges: Sequence[JsonDict] | None = None,
    manifest_version: str = MANIFEST_VERSION,
) -> JsonDict:
    """Build a legal-wrapped JSON manifest: one component candidate per Slab 03 frame."""

    by_frame: dict[str, list[JsonDict]] = defaultdict(list)
    unassigned = 0
    for node in nodes:
        fid = _slab03_frame_id(node)
        if fid is None:
            unassigned += 1
            continue
        by_frame[fid].append(node)

    frames_out: list[JsonDict] = []
    for fid in sorted(by_frame.keys()):
        members = by_frame[fid]
        first = members[0]
        anchor_kinds = {_slab03_anchor_kind(m) for m in members}
        anchor_kinds.discard(None)
        families = {_anchor_family(k) for k in anchor_kinds}
        if len(families) == 1:
            anchor_family = next(iter(families))
        elif len(families) > 1:
            anchor_family = "mixed"
        else:
            anchor_family = "unknown"

        pattern_set: set[str] = set()
        color_tokens: set[str] = set()
        typography_tokens: set[str] = set()
        spacing_tokens: set[str] = set()
        for m in members:
            fp = _pattern_fingerprint(m)
            if fp is not None:
                pattern_set.add(fp)
            token_bucket = _design_tokens(m)
            color_tokens.update(token_bucket["color_tokens"])
            typography_tokens.update(token_bucket["typography_tokens"])
            spacing_tokens.update(token_bucket["spacing_tokens"])
        patterns = sorted(pattern_set)[:_PATTERN_FINGERPRINT_LIMIT]

        sample_refs = [
            str(m["node_ref"])
            for m in members
            if m.get("node_ref") is not None and str(m.get("node_ref")).strip()
        ][: _SAMPLE_NODE_REF_LIMIT]

        figma_alias = _slab03_figma_alias(first)
        if not figma_alias:
            figma_alias = fid.replace(":", "_").replace("/", "_")

        stable_key = stable_digest(
            BRIDGE_KIND,
            manifest_version,
            app_id,
            platform,
            screen_id,
            fid,
        )

        landmark_kind: str | None = _slab03_landmark_kind(first)
        if landmark_kind is None:
            for m in members:
                landmark_kind = _slab03_landmark_kind(m)
                if landmark_kind is not None:
                    break

        frames_out.append(
            {
                "component_id": fid,
                "stable_component_key": stable_key,
                "slab03_frame_id": fid,
                "figma_suggested_name": str(figma_alias),
                "slab03_landmark_kind": landmark_kind,
                "anchor_family": anchor_family,
                "anchor_kinds_observed": sorted(anchor_kinds),
                "member_count": len(members),
                "sample_node_refs": sample_refs,
                "pattern_fingerprints": patterns,
                "design_tokens": {
                    "color_tokens": sorted(color_tokens),
                    "typography_tokens": sorted(typography_tokens),
                    "spacing_tokens": sorted(spacing_tokens),
                },
            }
        )

    core: JsonDict = {
        "manifest_version": manifest_version,
        "bridge_kind": BRIDGE_KIND,
        "app_id": app_id,
        "platform": platform,
        "screen_id": screen_id,
        "screen_name": screen_name,
        "frame_count": len(frames_out),
        "unassigned_node_count": unassigned,
        "frames": frames_out,
        "ref_map": build_ref_map(nodes, edges),
        "variant_axes": [],
        "variant_axes_note": (
            "Reserved for Tier 2 variant promotion from DNA patterns; "
            "empty in Figma Bridge v0.2.2."
        ),
    }
    return with_legal_metadata(core)
