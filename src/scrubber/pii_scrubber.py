from __future__ import annotations

from typing import Any

from .rules import BEARER_RE, CARD_RE, EMAIL_RE, PHONE_RE, SENSITIVE_KEYS, TOKEN_RE

PRESERVE_REPORT_STRING_KEYS = {
    "app_id",
    "category",
    "confidence",
    "element_type",
    "expected_impact",
    "finding_id",
    "fingerprint",
    "generated_at",
    "implementation_effort",
    "node_ref",
    "platform",
    "priority",
    "provenance",
    "recommendation_id",
    "report_version",
    "representative_node_ref",
    "role",
    "rule_id",
    "scope",
    "screen_id",
    "source",
    "target",
    "url",
    "version",
}
PRESERVE_REPORT_STRING_LIST_KEYS = {
    "affected_components",
    "affected_screens",
    "benchmark_refs",
    "element_types",
    "evidence",
    "node_refs",
    "roles",
    "screen_ids",
    "standards_refs",
    "traits",
}


def scrub_text(value: str) -> str:
    text = EMAIL_RE.sub("[redacted-email]", value)
    text = PHONE_RE.sub("[redacted-phone]", text)
    text = CARD_RE.sub("[redacted-card]", text)
    text = BEARER_RE.sub("Bearer [redacted-token]", text)
    text = TOKEN_RE.sub("[redacted-token]", text)
    return text


def scrub_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        return scrub_text(payload)
    if isinstance(payload, list):
        return [scrub_payload(item) for item in payload]
    if isinstance(payload, dict):
        scrubbed: dict[str, Any] = {}
        for key, value in payload.items():
            if str(key).lower() in SENSITIVE_KEYS:
                scrubbed[key] = "[redacted]"
            else:
                scrubbed[key] = scrub_payload(value)
        return scrubbed
    return payload


def scrub_report_artifact(
    payload: Any,
    *,
    current_key: str | None = None,
    preserve_strings: bool = False,
) -> Any:
    if isinstance(payload, str):
        if preserve_strings:
            return payload
        return scrub_text(payload)
    if isinstance(payload, list):
        preserve_list_items = (
            preserve_strings
            or (current_key or "").lower() in PRESERVE_REPORT_STRING_LIST_KEYS
        )
        return [
            scrub_report_artifact(
                item,
                current_key=current_key,
                preserve_strings=preserve_list_items,
            )
            for item in payload
        ]
    if isinstance(payload, dict):
        scrubbed: dict[str, Any] = {}
        for key, value in payload.items():
            key_lower = str(key).lower()
            scrubbed[key] = scrub_report_artifact(
                value,
                current_key=key_lower,
                preserve_strings=key_lower in PRESERVE_REPORT_STRING_KEYS,
            )
        return scrubbed
    return payload
