# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

from hashlib import sha256
from typing import Any, TypeAlias

JsonDict: TypeAlias = dict[str, Any]
ScoreMap: TypeAlias = dict[str, JsonDict]
RecommendationMap: TypeAlias = dict[str, Any]

DEFAULT_STANDARDS_PACK_VERSION = "2026-Q1"
SCORING_MODEL_VERSION = "2026-03-18"
REPORT_VERSION = "1.0"

SCORE_NAMES = (
    "complexity",
    "reusability",
    "accessibility_risk",
    "migration_risk",
)

RECOMMENDATION_CATEGORIES = (
    "layout",
    "navigation",
    "accessibility",
    "interaction",
    "content_hierarchy",
    "component_reuse",
    "design_system_consistency",
    "migration_sequencing",
)


def build_node_ref(screen_id: str, element_id: str) -> str:
    return f"{screen_id}#{element_id}"


def build_node_ref_from_node(node: JsonDict) -> str:
    return build_node_ref(str(node["screen_id"]), str(node["element_id"]))


def stable_digest(*parts: object) -> str:
    normalized = "|".join(str(part).strip() for part in parts if str(part).strip())
    return sha256(normalized.encode("utf-8")).hexdigest()[:8]
