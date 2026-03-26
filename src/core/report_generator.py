# SPDX-License-Identifier: AGPL-3.0-only
from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..connectors.standards_pack import load_standards_pack
from ..scrubber.pii_scrubber import scrub_report_artifact
from .compliance import (
    iso_date_from_timestamp,
    markdown_legal_lines,
    with_legal_metadata,
)
from .deduplicator import deduplicate_nodes
from .fingerprint import fingerprint_node
from .models import REPORT_VERSION
from .normalizer import normalize_project
from .recommendation_engine import build_recommendations
from .roadmap_generator import build_roadmap
from .schemas import load_json_file, validate_project_payload
from .scoring import score_project
from .telemetry import log_stage

JsonDict = dict[str, Any]


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def analyze_payload(
    payload: JsonDict, app_id: str, generated_at: str | None = None
) -> JsonDict:
    run_id = str(uuid4())
    _set_last_run_metadata({"run_id": run_id})

    with log_stage(run_id=run_id, component="cli", stage="load_payload"):
        validated = validate_project_payload(payload)

    with log_stage(run_id=run_id, component="cli", stage="normalize"):
        project = normalize_project(validated, app_id)
        for screen in project["screens"]:
            for element_index, element in enumerate(screen["elements"]):
                enriched = dict(element)
                enriched["structural_fingerprint"] = fingerprint_node(enriched)
                screen["elements"][element_index] = enriched

    project["nodes"] = [
        element for screen in project["screens"] for element in screen["elements"]
    ]

    with log_stage(run_id=run_id, component="cli", stage="score"):
        clusters = deduplicate_nodes(project["nodes"])
        scores = score_project(project, clusters)

    with log_stage(run_id=run_id, component="cli", stage="recommend"):
        standards_pack = load_standards_pack()
        recommendations = build_recommendations(project, clusters)
        roadmap = build_roadmap(recommendations)
    generated_at = generated_at or now_iso()

    findings = [
        {
            "finding_id": f"finding-{index:03d}",
            "rule_id": recommendation["rule_id"],
            "category": recommendation["category"],
            "title": recommendation["problem_statement"],
            "priority": recommendation["priority"],
            "provenance": recommendation["provenance"],
            "evidence": recommendation["evidence"],
        }
        for index, recommendation in enumerate(recommendations, start=1)
    ]

    screen_inventory = []
    for screen in project["screens"]:
        screen_nodes = screen["elements"]
        screen_inventory.append(
            {
                "screen_id": screen["screen_id"],
                "screen_name": screen["screen_name"],
                "node_count": len(screen_nodes),
                "interactive_count": sum(
                    1 for node in screen_nodes if node.get("interactive")
                ),
                "duplicate_node_count": sum(
                    1
                    for node in screen_nodes
                    if any(
                        cluster["count"] > 1
                        and cluster["fingerprint"] == node["structural_fingerprint"]
                        for cluster in clusters
                    )
                ),
                "accessibility_gap_count": sum(
                    1
                    for node in screen_nodes
                    if node.get("interactive")
                    and not node.get("accessibility_identifier")
                ),
            }
        )

    report = {
        "report_version": REPORT_VERSION,
        "generated_at": generated_at,
        "app_id": app_id,
        "project_name": project["project_name"],
        "platform": project["platform"],
        "standards_pack": standards_pack,
        "summary": {
            "screen_count": len(project["screens"]),
            "node_count": len(project["nodes"]),
            "interactive_node_count": sum(
                1 for node in project["nodes"] if node.get("interactive")
            ),
            "duplicate_cluster_count": sum(
                1 for cluster in clusters if cluster["count"] > 1
            ),
            "recommendation_count": len(recommendations),
        },
        "scores": scores,
        "screen_inventory": screen_inventory,
        "duplicate_clusters": [
            {
                "fingerprint": cluster["fingerprint"],
                "count": cluster["count"],
                "interactive": cluster["interactive"],
                "screen_ids": cluster["screen_ids"],
                "screen_names": cluster["screen_names"],
                "node_refs": cluster["node_refs"],
                "element_types": cluster["element_types"],
                "roles": cluster["roles"],
                "representative_node_ref": cluster["representative_node_ref"],
            }
            for cluster in clusters
            if cluster["count"] > 1
        ],
        "findings": findings,
        "recommendations": recommendations,
        "roadmap": roadmap,
    }
    report["_telemetry"] = {"run_id": run_id}
    return report


_last_run_metadata: dict[str, Any] | None = None


def _set_last_run_metadata(metadata: dict[str, Any]) -> None:
    global _last_run_metadata
    _last_run_metadata = metadata.copy()


def get_last_run_metadata() -> dict[str, Any] | None:
    return _last_run_metadata


def prepare_report_for_output(report: JsonDict) -> JsonDict:
    scrubbed = scrub_report_artifact(report)
    scrubbed.pop("_telemetry", None)
    return with_legal_metadata(
        scrubbed,
        live_raid_date=iso_date_from_timestamp(scrubbed.get("generated_at")),
    )


def render_markdown_report(report: JsonDict) -> str:
    report = prepare_report_for_output(report)
    lines: list[str] = []
    lines.append("# RADE modernization report")
    lines.append("")
    lines.append(f"- Report version: {report['report_version']}")
    lines.append(f"- Generated at: {report['generated_at']}")
    lines.append(f"- App ID: {report['app_id']}")
    lines.append(f"- Project: {report['project_name']}")
    lines.append(f"- Platform: {report['platform']}")
    lines.append(f"- Standards pack: {report['standards_pack']['version']}")
    lines.extend(
        markdown_legal_lines(live_raid_date=report["rade_legal"].get("live_raid_date"))
    )
    lines.append("")
    lines.append("## Summary")
    for key, value in report["summary"].items():
        lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    lines.append("")
    lines.append("## Scorecard")
    lines.append("| Metric | Value | Evidence |")
    lines.append("| --- | --- | --- |")
    for score_name in (
        "complexity",
        "reusability",
        "accessibility_risk",
        "migration_risk",
    ):
        score = report["scores"][score_name]
        lines.append(
            f"| {score_name} | {score['value']} | {'; '.join(score['evidence'])} |"
        )
    lines.append("")
    lines.append("## Screen Inventory")
    for screen in report["screen_inventory"]:
        lines.append(
            f"- {screen['screen_name']} ({screen['screen_id']}): {screen['node_count']} nodes, {screen['interactive_count']} interactive, {screen['duplicate_node_count']} duplicated, {screen['accessibility_gap_count']} accessibility gaps"
        )
    lines.append("")
    lines.append("## Findings")
    for finding in report["findings"]:
        lines.append(f"### {finding['title']}")
        lines.append(f"- Rule ID: {finding['rule_id']}")
        lines.append(f"- Category: {finding['category']}")
        lines.append(f"- Priority: {finding['priority']}")
        lines.append(f"- Provenance: {finding['provenance']}")
        lines.append(f"- Evidence: {', '.join(finding['evidence'])}")
        lines.append("")
    lines.append("## Recommendations")
    for recommendation in report["recommendations"]:
        lines.append(f"### {recommendation['category']} - {recommendation['target']}")
        lines.append(f"- Recommendation ID: {recommendation['recommendation_id']}")
        lines.append(f"- Rule ID: {recommendation['rule_id']}")
        lines.append(f"- Priority: {recommendation['priority']}")
        lines.append(f"- Confidence: {recommendation['confidence']}")
        lines.append(f"- Problem: {recommendation['problem_statement']}")
        lines.append(f"- Change: {recommendation['recommended_change']}")
        lines.append(f"- Reasoning: {recommendation['reasoning']}")
        lines.append(f"- Expected impact: {recommendation['expected_impact']}")
        lines.append(f"- Effort: {recommendation['implementation_effort']}")
        lines.append(f"- Standards refs: {', '.join(recommendation['standards_refs'])}")
        lines.append(
            f"- Benchmark refs: {', '.join(recommendation['benchmark_refs']) or 'none'}"
        )
        lines.append(f"- Provenance: {recommendation['provenance']}")
        lines.append(f"- Evidence: {', '.join(recommendation['evidence'])}")
        lines.append("")
    lines.append("## Roadmap")
    for item in report["roadmap"]:
        lines.append(
            f"- Step {item['step']}: {item['title']} ({item['priority']}, {item['implementation_effort']})"
        )
    lines.append("")
    return "\n".join(lines)


def _h(text: object) -> str:
    return escape(str(text))


def _score_bar_color(score_name: str, value: int) -> str:
    if score_name in ("accessibility_risk", "migration_risk", "complexity"):
        if value >= 70:
            return "#e74c3c"
        if value >= 40:
            return "#f39c12"
        return "#27ae60"
    if value >= 70:
        return "#27ae60"
    if value >= 40:
        return "#f39c12"
    return "#e74c3c"


def _priority_class(priority: str) -> str:
    return priority.lower().replace(" ", "")


def render_html_report(report: JsonDict) -> str:
    report = prepare_report_for_output(report)
    legal = report.get("rade_legal", {})
    summary = report["summary"]
    scores = report["scores"]

    score_rows = []
    for name in ("complexity", "reusability", "accessibility_risk", "migration_risk"):
        s = scores[name]
        color = _score_bar_color(name, s["value"])
        evidence_str = _h("; ".join(s["evidence"]))
        score_rows.append(
            f"<tr><td>{_h(name)}</td>"
            f'<td><div class="score-bar"><div class="score-fill" '
            f'style="width:{s["value"]}%;background:{color}">'
            f'{s["value"]}</div></div></td>'
            f"<td>{evidence_str}</td></tr>"
        )

    screen_rows = []
    for screen in report["screen_inventory"]:
        screen_rows.append(
            f"<tr><td>{_h(screen['screen_name'])}</td>"
            f"<td><code>{_h(screen['screen_id'])}</code></td>"
            f"<td>{screen['node_count']}</td>"
            f"<td>{screen['interactive_count']}</td>"
            f"<td>{screen['duplicate_node_count']}</td>"
            f"<td>{screen['accessibility_gap_count']}</td></tr>"
        )

    categories = sorted({f["category"] for f in report["findings"]})
    filter_buttons = ['<button class="filter-btn active" data-cat="all">All</button>']
    for cat in categories:
        filter_buttons.append(
            f'<button class="filter-btn" data-cat="{_h(cat)}">{_h(cat)}</button>'
        )

    finding_cards = []
    for finding in report["findings"]:
        evidence_items = "".join(
            f"<li><code>{_h(e)}</code></li>" for e in finding["evidence"]
        )
        finding_cards.append(
            f'<details class="finding-card" data-category="{_h(finding["category"])}">'
            f"<summary>"
            f'<span class="priority-badge {_priority_class(finding["priority"])}">'
            f'{_h(finding["priority"])}</span> '
            f'{_h(finding["title"])}'
            f"</summary>"
            f'<div class="finding-body">'
            f"<dl>"
            f"<dt>Rule ID</dt><dd><code>{_h(finding['rule_id'])}</code></dd>"
            f"<dt>Category</dt><dd>{_h(finding['category'])}</dd>"
            f"<dt>Provenance</dt><dd>{_h(finding['provenance'])}</dd>"
            f"</dl>"
            f"<strong>Evidence</strong><ul>{evidence_items}</ul>"
            f"</div></details>"
        )

    rec_cards = []
    for rec in report["recommendations"]:
        evidence_items = "".join(
            f"<li><code>{_h(e)}</code></li>" for e in rec["evidence"]
        )
        standards_items = "".join(f"<li>{_h(s)}</li>" for s in rec["standards_refs"])
        benchmark_items = (
            "".join(f"<li>{_h(b)}</li>" for b in rec["benchmark_refs"])
            or "<li>none</li>"
        )
        rec_cards.append(
            f'<details class="rec-card" data-category="{_h(rec["category"])}">'
            f"<summary>"
            f'<span class="priority-badge {_priority_class(rec["priority"])}">'
            f'{_h(rec["priority"])}</span> '
            f'{_h(rec["category"])} &mdash; {_h(rec["target"])}'
            f"</summary>"
            f'<div class="rec-body">'
            f"<dl>"
            f"<dt>Recommendation ID</dt>"
            f"<dd><code>{_h(rec['recommendation_id'])}</code></dd>"
            f"<dt>Rule ID</dt><dd><code>{_h(rec['rule_id'])}</code></dd>"
            f"<dt>Confidence</dt><dd>{_h(rec['confidence'])}</dd>"
            f"<dt>Effort</dt><dd>{_h(rec['implementation_effort'])}</dd>"
            f"<dt>Expected impact</dt><dd>{_h(rec['expected_impact'])}</dd>"
            f"</dl>"
            f"<p><strong>Problem:</strong> {_h(rec['problem_statement'])}</p>"
            f"<p><strong>Change:</strong> {_h(rec['recommended_change'])}</p>"
            f"<p><strong>Reasoning:</strong> {_h(rec['reasoning'])}</p>"
            f"<strong>Standards</strong><ul>{standards_items}</ul>"
            f"<strong>Benchmarks</strong><ul>{benchmark_items}</ul>"
            f"<strong>Evidence</strong><ul>{evidence_items}</ul>"
            f"</div></details>"
        )

    roadmap_rows = []
    for item in report["roadmap"]:
        screens = ", ".join(item["affected_screens"])
        roadmap_rows.append(
            f'<tr><td>{item["step"]}</td>'
            f'<td>{_h(item["title"])}</td>'
            f'<td><span class="priority-badge {_priority_class(item["priority"])}">'
            f'{_h(item["priority"])}</span></td>'
            f'<td>{_h(item["implementation_effort"])}</td>'
            f"<td>{_h(screens)}</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RADE report &mdash; {_h(report['project_name'])}</title>
<style>
*,*::before,*::after{{box-sizing:border-box}}
:root{{--bg:#0f1117;--surface:#1a1d27;--border:#2a2d3a;--text:#e4e4e7;
--text-muted:#9ca3af;--accent:#62f2b1;--accent-dim:#1a3d2e}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",
Roboto,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);
line-height:1.6}}
.container{{max-width:960px;margin:0 auto;padding:24px 16px}}
h1{{font-size:1.5rem;color:var(--accent);margin:0 0 4px}}
h2{{font-size:1.15rem;color:var(--accent);margin:32px 0 12px;
border-bottom:1px solid var(--border);padding-bottom:6px}}
.meta{{color:var(--text-muted);font-size:0.85rem;margin-bottom:24px}}
.meta span{{display:inline-block;margin-right:16px}}
.legal{{color:var(--text-muted);font-size:0.75rem;margin-bottom:20px;
padding:8px 12px;background:var(--surface);border-radius:6px;
border:1px solid var(--border)}}
.summary-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
gap:12px;margin-bottom:8px}}
.summary-card{{background:var(--surface);border:1px solid var(--border);
border-radius:8px;padding:16px;text-align:center}}
.summary-card .num{{font-size:1.8rem;font-weight:700;color:var(--accent)}}
.summary-card .label{{font-size:0.8rem;color:var(--text-muted);margin-top:2px}}
table{{width:100%;border-collapse:collapse;margin-bottom:8px;font-size:0.9rem}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--border)}}
th{{color:var(--accent);font-weight:600;font-size:0.8rem;text-transform:uppercase;
letter-spacing:0.04em}}
.score-bar{{background:var(--surface);border-radius:4px;height:22px;
width:100%;min-width:100px;position:relative;overflow:hidden;
border:1px solid var(--border)}}
.score-fill{{height:100%;border-radius:3px;display:flex;align-items:center;
padding-left:8px;font-size:0.75rem;font-weight:700;color:#fff;
min-width:28px;transition:width .3s}}
.filter-bar{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}}
.filter-btn{{background:var(--surface);color:var(--text-muted);border:1px solid var(--border);
border-radius:4px;padding:4px 12px;cursor:pointer;font-size:0.8rem}}
.filter-btn:hover{{border-color:var(--accent)}}
.filter-btn.active{{background:var(--accent-dim);color:var(--accent);
border-color:var(--accent)}}
details{{background:var(--surface);border:1px solid var(--border);
border-radius:8px;margin-bottom:8px}}
summary{{cursor:pointer;padding:12px 16px;font-weight:500;font-size:0.9rem;
list-style:none;display:flex;align-items:center;gap:8px}}
summary::-webkit-details-marker{{display:none}}
summary::before{{content:"\\25B6";font-size:0.6rem;transition:transform .2s;
color:var(--text-muted)}}
details[open] summary::before{{transform:rotate(90deg)}}
.finding-body,.rec-body{{padding:4px 16px 16px}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:4px 16px;margin:8px 0}}
dt{{color:var(--text-muted);font-size:0.8rem;font-weight:600}}
dd{{margin:0;font-size:0.9rem}}
.priority-badge{{display:inline-block;padding:2px 8px;border-radius:4px;
font-size:0.75rem;font-weight:700;text-transform:uppercase}}
.p1{{background:#3b1318;color:#e74c3c}}
.p2{{background:#3b2e10;color:#f39c12}}
.p3{{background:#1a3d2e;color:#27ae60}}
code{{background:var(--surface);padding:1px 5px;border-radius:3px;
font-size:0.85em;border:1px solid var(--border)}}
ul{{padding-left:20px;margin:4px 0}}
li{{margin:2px 0;font-size:0.9rem}}
.hidden{{display:none}}
footer{{margin-top:40px;padding-top:12px;border-top:1px solid var(--border);
color:var(--text-muted);font-size:0.75rem;text-align:center}}
</style>
</head>
<body>
<div class="container">
<h1>RADE modernization report</h1>
<div class="meta">
<span>v{_h(report['report_version'])}</span>
<span>{_h(report['generated_at'])}</span>
<span>{_h(report['app_id'])}</span>
<span>{_h(report['platform'])}</span>
<span>Standards: {_h(report['standards_pack']['version'])}</span>
</div>
<div class="legal">
{_h(legal.get('header_notice', ''))} &middot;
{_h(legal.get('attribution', ''))} &middot;
{_h(legal.get('license', ''))} &middot;
{_h(legal.get('project_status', ''))}
<br>{_h(legal.get('project_terms_notice', ''))}
</div>

<h2>Summary</h2>
<div class="summary-grid">
<div class="summary-card"><div class="num">{summary['screen_count']}</div>
<div class="label">Screens</div></div>
<div class="summary-card"><div class="num">{summary['node_count']}</div>
<div class="label">Nodes</div></div>
<div class="summary-card"><div class="num">{summary['interactive_node_count']}</div>
<div class="label">Interactive</div></div>
<div class="summary-card"><div class="num">{summary['duplicate_cluster_count']}</div>
<div class="label">Dup Clusters</div></div>
<div class="summary-card"><div class="num">{summary['recommendation_count']}</div>
<div class="label">Recommendations</div></div>
</div>

<h2>Scorecard</h2>
<table>
<thead><tr><th>Metric</th><th>Score</th><th>Evidence</th></tr></thead>
<tbody>{''.join(score_rows)}</tbody>
</table>

<h2>Screen Inventory</h2>
<table>
<thead><tr><th>Screen</th><th>ID</th><th>Nodes</th><th>Interactive</th>
<th>Duplicated</th><th>A11y Gaps</th></tr></thead>
<tbody>{''.join(screen_rows)}</tbody>
</table>

<h2>Findings</h2>
<div class="filter-bar" id="finding-filters">{''.join(filter_buttons)}</div>
<div id="findings">{''.join(finding_cards)}</div>

<h2>Recommendations</h2>
<div class="filter-bar" id="rec-filters">{''.join(filter_buttons)}</div>
<div id="recommendations">{''.join(rec_cards)}</div>

<h2>Roadmap</h2>
<table>
<thead><tr><th>#</th><th>Action</th><th>Priority</th><th>Effort</th>
<th>Screens</th></tr></thead>
<tbody>{''.join(roadmap_rows)}</tbody>
</table>

<footer>
RADE &middot; {_h(legal.get('attribution', ''))} &middot;
{_h(legal.get('license', ''))} &middot;
{_h(legal.get('project_status', ''))}
</footer>
</div>
<script>
document.querySelectorAll(".filter-bar").forEach(function(bar){{
  bar.addEventListener("click",function(e){{
    var btn=e.target.closest(".filter-btn");
    if(!btn)return;
    bar.querySelectorAll(".filter-btn").forEach(function(b){{
      b.classList.remove("active")}});
    btn.classList.add("active");
    var cat=btn.getAttribute("data-cat");
    var section=bar.nextElementSibling;
    section.querySelectorAll("details").forEach(function(d){{
      if(cat==="all"||d.getAttribute("data-category")===cat){{
        d.classList.remove("hidden")}}else{{
        d.classList.add("hidden")}}}});
  }});
}});
</script>
</body>
</html>
"""


def write_report(
    report: JsonDict,
    json_output: Path | None,
    md_output: Path | None,
    html_output: Path | None = None,
) -> None:
    run_id = report.get("_telemetry", {}).get("run_id")
    with log_stage(run_id=run_id, component="cli", stage="report_write"):
        report_for_output = prepare_report_for_output(report)
        if json_output is not None:
            json_output.parent.mkdir(parents=True, exist_ok=True)
            json_output.write_text(
                json.dumps(report_for_output, indent=2, sort_keys=False) + "\n",
                encoding="utf-8",
            )
        if md_output is not None:
            md_output.parent.mkdir(parents=True, exist_ok=True)
            md_output.write_text(
                render_markdown_report(report_for_output), encoding="utf-8"
            )
        if html_output is not None:
            html_output.parent.mkdir(parents=True, exist_ok=True)
            html_output.write_text(
                render_html_report(report_for_output), encoding="utf-8"
            )


def analyze_file(
    input_path: Path | str,
    app_id: str,
    json_output: Path | None = None,
    md_output: Path | None = None,
    html_output: Path | None = None,
) -> JsonDict:
    payload = load_json_file(Path(input_path))
    report = analyze_payload(payload, app_id)
    write_report(report, json_output, md_output, html_output)
    return prepare_report_for_output(report)
