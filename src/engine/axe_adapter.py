# SPDX-License-Identifier: AGPL-3.0-only
"""axe-core integration for RADE web collection.

Runs Deque's axe-core accessibility engine against a live Playwright page and
normalizes the violations into the RADE finding shape. Findings emitted here
carry explicit `provenance: "axe-core"` so downstream consumers can tell them
apart from RADE's structural rule set.

Design notes:
- The adapter accepts an injected axe script loader, which means tests can
  exercise the normalization path without Playwright or network.
- Output is deterministically sorted by rule id then target selector so the
  same page yields the same output across runs.
- axe-core is MPL-2.0. We load it from a pinned CDN URL at runtime (no code
  is vendored into this repo); users can override the source for offline use.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

JsonDict = dict[str, Any]

# Pinned to a specific minor so output stays stable across RADE runs.
DEFAULT_AXE_CDN_URL = (
    "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
)
AXE_PROVENANCE = "axe-core"

_IMPACT_TO_PRIORITY = {
    "critical": "P0",
    "serious": "P1",
    "moderate": "P2",
    "minor": "P3",
}


class AxeRunError(RuntimeError):
    """Raised when axe-core cannot be executed against the page."""


def normalize_axe_results(
    raw: JsonDict, *, axe_version: str | None = None
) -> list[JsonDict]:
    """Convert a raw `axe.run()` result into deterministic RADE findings.

    Each violation becomes one finding per affected node. Findings are sorted
    by `(rule_id, target)` so identical input yields identical output order.
    """
    violations = raw.get("violations", []) if isinstance(raw, dict) else []
    version = axe_version or (
        raw.get("testEngine", {}).get("version") if isinstance(raw, dict) else None
    )

    findings: list[JsonDict] = []
    for violation in violations:
        if not isinstance(violation, dict):
            continue
        rule_id = str(violation.get("id") or "").strip()
        if not rule_id:
            continue
        impact = str(violation.get("impact") or "moderate").lower()
        priority = _IMPACT_TO_PRIORITY.get(impact, "P2")
        help_text = str(violation.get("help") or "").strip()
        description = str(violation.get("description") or "").strip()
        help_url = str(violation.get("helpUrl") or "").strip() or None
        tags = sorted(
            tag
            for tag in violation.get("tags", [])
            if isinstance(tag, str) and tag.strip()
        )
        wcag_refs = [tag for tag in tags if tag.startswith("wcag")]

        for node in violation.get("nodes", []) or []:
            if not isinstance(node, dict):
                continue
            target = _first_target(node.get("target"))
            failure_summary = str(node.get("failureSummary") or "").strip()
            html_snippet = str(node.get("html") or "").strip()
            findings.append(
                {
                    "rule_id": rule_id,
                    "provenance": AXE_PROVENANCE,
                    "engine_version": version,
                    "priority": priority,
                    "impact": impact,
                    "category": "accessibility",
                    "title": help_text or description or rule_id,
                    "description": description or help_text,
                    "help_url": help_url,
                    "wcag_refs": wcag_refs,
                    "tags": tags,
                    "target": target,
                    "html": html_snippet,
                    "failure_summary": failure_summary,
                }
            )

    findings.sort(key=lambda f: (f["rule_id"], f["target"] or "", f["html"] or ""))
    return findings


def summarize_axe_findings(findings: Iterable[JsonDict]) -> JsonDict:
    """Deterministic rollup for the report summary block."""
    by_impact: dict[str, int] = {"critical": 0, "serious": 0, "moderate": 0, "minor": 0}
    by_rule: dict[str, int] = {}
    engine_versions: set[str] = set()
    for finding in findings:
        impact = str(finding.get("impact") or "moderate").lower()
        if impact not in by_impact:
            by_impact[impact] = 0
        by_impact[impact] += 1
        rule_id = str(finding.get("rule_id") or "")
        if rule_id:
            by_rule[rule_id] = by_rule.get(rule_id, 0) + 1
        version = finding.get("engine_version")
        if version:
            engine_versions.add(str(version))
    return {
        "total": sum(by_impact.values()),
        "by_impact": by_impact,
        "by_rule": dict(sorted(by_rule.items())),
        "engine": AXE_PROVENANCE,
        "engine_versions": sorted(engine_versions),
    }


def run_axe_against_page(
    page: Any,
    *,
    axe_source_url: str = DEFAULT_AXE_CDN_URL,
    timeout_ms: int = 10_000,
    script_loader: Callable[[Any, str, int], None] | None = None,
    runner: Callable[[Any, int], JsonDict] | None = None,
) -> list[JsonDict]:
    """Inject axe-core into `page` and execute `axe.run()`.

    The `script_loader` and `runner` seams exist so tests can exercise this
    function without a real browser: pass fakes that return canned data.
    """
    loader = script_loader or _default_script_loader
    execute = runner or _default_runner
    try:
        loader(page, axe_source_url, timeout_ms)
        raw = execute(page, timeout_ms)
    except Exception as exc:
        raise AxeRunError(f"axe-core run failed: {exc}") from exc

    if not isinstance(raw, dict):
        raise AxeRunError("axe-core returned an unexpected payload shape")
    return normalize_axe_results(raw)


def _default_script_loader(page: Any, source_url: str, timeout_ms: int) -> None:
    page.add_script_tag(url=source_url, timeout=timeout_ms)  # pragma: no cover


def _default_runner(page: Any, timeout_ms: int) -> JsonDict:
    return page.evaluate(  # pragma: no cover
        "async () => await axe.run(document, {resultTypes: ['violations']})"
    )


def _first_target(value: Any) -> str:
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, list) and first:
            return str(first[0])
        return str(first)
    if isinstance(value, str):
        return value.strip()
    return ""
