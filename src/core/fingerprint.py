# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from hashlib import sha256
from typing import Any

JsonDict = dict[str, Any]


def fingerprint_node(node: JsonDict) -> str:
    traits = ",".join(
        sorted(
            {
                str(trait).strip().lower()
                for trait in node.get("traits", [])
                if str(trait).strip()
            }
        )
    )
    parts = [
        str(node.get("platform", "")).strip().lower(),
        str(node.get("element_type", "")).strip().lower(),
        str(node.get("slab_layer", "")).strip().lower(),
        str(node.get("role", "")).strip().lower(),
        "interactive" if node.get("interactive") else "static",
        "visible" if node.get("visible") else "hidden",
        f"depth:{int(node.get('hierarchy_depth', 0) or 0)}",
        f"children:{int(node.get('child_count', 0) or 0)}",
        f"text:{1 if node.get('text_present') else 0}",
        f"traits:{traits or '-'}",
    ]
    digest = sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]
