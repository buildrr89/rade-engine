# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

from collections import defaultdict
from typing import Any

from .fingerprint import fingerprint_node
from .models import build_node_ref_from_node

JsonDict = dict[str, Any]


def deduplicate_nodes(nodes: list[JsonDict]) -> list[JsonDict]:
    clusters: dict[str, list[JsonDict]] = defaultdict(list)
    for node in nodes:
        fingerprint = str(node.get("structural_fingerprint") or fingerprint_node(node))
        node_copy = dict(node)
        node_copy["structural_fingerprint"] = fingerprint
        clusters[fingerprint].append(node_copy)

    ordered_clusters: list[JsonDict] = []
    for fingerprint, group in sorted(
        clusters.items(), key=lambda item: (-len(item[1]), item[0])
    ):
        representative = group[0]
        ordered_clusters.append(
            {
                "fingerprint": fingerprint,
                "count": len(group),
                "interactive": any(node.get("interactive") for node in group),
                "screen_ids": sorted({str(node.get("screen_id")) for node in group}),
                "screen_names": sorted(
                    {str(node.get("screen_name")) for node in group}
                ),
                "element_ids": [str(node.get("element_id")) for node in group],
                "node_refs": [build_node_ref_from_node(node) for node in group],
                "element_types": sorted(
                    {str(node.get("element_type")) for node in group}
                ),
                "roles": sorted({str(node.get("role")) for node in group}),
                "representative_node_ref": build_node_ref_from_node(representative),
                "representative": representative,
            }
        )
    return ordered_clusters
