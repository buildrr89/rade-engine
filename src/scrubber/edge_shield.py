# © 2026 RADE Project. All Rights Reserved. Lead Architect: Trung Nguyen - BUILDRR89. Confidential Construction Data Model.
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .rules import BEARER_RE, CARD_RE, EMAIL_RE, PHONE_RE, SENSITIVE_KEYS, TOKEN_RE

SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PRICE_RE = re.compile(
    r"(?i)\b(?:usd|aud|cad|eur|gbp)\s?\d+(?:[.,]\d{2})?\b|[$€£]\s?\d+(?:[.,]\d{2})?"
)
NODE_PATH_RE = re.compile(r"^(root\.nodes\[\d+\])(?:\.|$)")
GENERIC_LABEL_TOKENS = {
    "app",
    "target",
    "main",
    "content",
    "project",
    "overview",
    "analysis",
    "review",
    "listing",
    "card",
    "header",
    "footer",
    "sidebar",
    "button",
    "link",
}


@dataclass
class RedactionEvent:
    path: str
    strategy: str
    entity: str
    original: str = ""
    replacement: str = ""


@dataclass
class ScrubMetadata:
    total_redactions: int = 0
    regex_hits: dict[str, int] = field(default_factory=dict)
    presidio_hits: list[dict[str, Any]] = field(default_factory=list)
    events: list[RedactionEvent] = field(default_factory=list)
    placeholder_map: dict[str, str] = field(default_factory=dict)
    neutralized_node_paths: set[str] = field(default_factory=set)
    used_presidio: bool = False
    is_scrubbed: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_redactions": self.total_redactions,
            "regex_hits": dict(self.regex_hits),
            "presidio_hits": list(self.presidio_hits),
            "events": [
                {
                    "path": event.path,
                    "strategy": event.strategy,
                    "entity": event.entity,
                    "original": event.original,
                    "replacement": event.replacement,
                }
                for event in self.events
            ],
            "neutralized_nodes": len(self.neutralized_node_paths),
            "placeholders": dict(self.placeholder_map),
            "used_presidio": self.used_presidio,
            "is_scrubbed": self.is_scrubbed,
        }


def _is_free_form_text(text: str) -> bool:
    return len(text.split()) >= 3 or any(char.isalpha() for char in text)


def _record_neutralized_node(path: str, metadata: ScrubMetadata) -> None:
    match = NODE_PATH_RE.match(path)
    if match is not None:
        metadata.neutralized_node_paths.add(match.group(1))


def _allocate_placeholder(value: str, metadata: ScrubMetadata) -> str:
    placeholder = metadata.placeholder_map.get(value)
    if placeholder is not None:
        return placeholder
    placeholder = f"DATA_SLOT_{len(metadata.placeholder_map) + 1:02d}"
    metadata.placeholder_map[value] = placeholder
    return placeholder


def _regex_entities(text: str) -> list[str]:
    regex_patterns = (
        ("email", EMAIL_RE),
        ("ssn", SSN_RE),
        ("phone", PHONE_RE),
        ("credit_card", CARD_RE),
        ("token", BEARER_RE),
        ("token", TOKEN_RE),
        ("price", PRICE_RE),
    )
    entities = [entity for entity, pattern in regex_patterns if pattern.search(text)]
    if _looks_like_person_name(text):
        entities.append("name")
    return entities


def _looks_like_person_name(text: str) -> bool:
    tokens = [token for token in re.split(r"\s+", text.strip()) if token]
    if len(tokens) < 2 or len(tokens) > 3:
        return False
    normalized_tokens = [re.sub(r"[^A-Za-z]", "", token) for token in tokens]
    if any(not token for token in normalized_tokens):
        return False
    if any(token.lower() in GENERIC_LABEL_TOKENS for token in normalized_tokens):
        return False
    return all(
        token[:1].isupper() and token[1:].islower() for token in normalized_tokens
    )


def _neutralize_text(text: str, *, path: str, metadata: ScrubMetadata) -> str:
    entities = _regex_entities(text)
    if entities:
        placeholder = _allocate_placeholder(text, metadata)
        metadata.total_redactions += len(entities)
        for entity in entities:
            metadata.regex_hits[entity] = metadata.regex_hits.get(entity, 0) + 1
            metadata.events.append(
                RedactionEvent(
                    path=path,
                    strategy="regex",
                    entity=entity,
                    original=text,
                    replacement=placeholder,
                )
            )
        _record_neutralized_node(path, metadata)
        return placeholder
    return text


def _scrub_string_value(text: str, *, path: str, metadata: ScrubMetadata) -> str:
    redacted = _neutralize_text(text, path=path, metadata=metadata)
    if redacted != text or not _is_free_form_text(text):
        return redacted

    try:
        from presidio_analyzer import AnalyzerEngine
    except Exception:
        return redacted

    try:
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(text=text, language="en")
    except Exception:
        return redacted

    if not results:
        return redacted

    placeholder = _allocate_placeholder(text, metadata)
    metadata.total_redactions += len(results)
    metadata.used_presidio = True
    for result in results:
        entity = str(result.entity_type).lower()
        metadata.presidio_hits.append(
            {
                "entity": entity,
                "score": float(getattr(result, "score", 0.0) or 0.0),
                "start": max(0, int(result.start)),
                "end": max(int(result.start), int(result.end)),
            }
        )
        metadata.events.append(
            RedactionEvent(
                path=path,
                strategy="presidio",
                entity=entity,
                original=text,
                replacement=placeholder,
            )
        )
    _record_neutralized_node(path, metadata)
    return placeholder


def presidio_escalation(text: str) -> tuple[str, dict[str, Any]]:
    """
    Escalate ambiguous free-form text to Presidio when available.

    Regex is still applied first. Presidio is a second-pass safeguard for
    unstructured strings that may contain names or other ambiguous entities.
    """
    metadata = ScrubMetadata()
    redacted = _scrub_string_value(text, path="text", metadata=metadata)
    return redacted, metadata.to_dict()


def scrub_text(text: str) -> str:
    metadata = ScrubMetadata()
    return _scrub_string_value(text, path="text", metadata=metadata)


def scrub_payload(payload: Any, *, path: str = "root") -> Any:
    if isinstance(payload, str):
        return scrub_text(payload)
    if isinstance(payload, list):
        return [
            scrub_payload(item, path=f"{path}[{index}]")
            for index, item in enumerate(payload)
        ]
    if isinstance(payload, dict):
        placeholder_metadata = ScrubMetadata()
        scrubbed: dict[str, Any] = {}
        for key, value in payload.items():
            key_lower = str(key).lower()
            child_path = f"{path}.{key_lower}"
            if key_lower in SENSITIVE_KEYS:
                placeholder = _allocate_placeholder(str(value), placeholder_metadata)
                scrubbed[key] = placeholder
            else:
                scrubbed[key] = scrub_payload(value, path=child_path)
        return scrubbed
    return payload


def scrub_payload_with_metadata(payload: Any) -> tuple[Any, dict[str, Any]]:
    metadata = ScrubMetadata()

    def _walk(value: Any, path: str) -> Any:
        if isinstance(value, str):
            return _scrub_string_value(value, path=path, metadata=metadata)
        if isinstance(value, list):
            return [_walk(item, f"{path}[{index}]") for index, item in enumerate(value)]
        if isinstance(value, dict):
            scrubbed: dict[str, Any] = {}
            for key, item in value.items():
                key_lower = str(key).lower()
                child_path = f"{path}.{key_lower}"
                if key_lower in SENSITIVE_KEYS:
                    replacement = _allocate_placeholder(str(item), metadata)
                    scrubbed[key] = replacement
                    metadata.total_redactions += 1
                    metadata.regex_hits[key_lower] = (
                        metadata.regex_hits.get(key_lower, 0) + 1
                    )
                    metadata.events.append(
                        RedactionEvent(
                            path=child_path,
                            strategy="sensitive-key",
                            entity=key_lower,
                            original=str(item),
                            replacement=replacement,
                        )
                    )
                    _record_neutralized_node(child_path, metadata)
                else:
                    scrubbed[key] = _walk(item, child_path)
            return scrubbed
        return value

    scrubbed = _walk(payload, "root")
    metadata_dict = metadata.to_dict()
    metadata_dict["neutralized_node_paths"] = sorted(metadata.neutralized_node_paths)
    return scrubbed, metadata_dict


def scrub_graph(graph: Any) -> tuple[Any, dict[str, Any]]:
    return scrub_payload_with_metadata(graph)
