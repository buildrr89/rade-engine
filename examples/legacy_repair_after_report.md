# RADE modernization report

- Report version: 1.0
- Generated at: 2026-04-10T00:00:00Z
- App ID: com.example.legacyapp
- Project: Legacy Repair App
- Platform: ios
- Standards pack: 2026-Q1
- Legal notice: Copyright (c) 2026 Buildrr89. Licensed under AGPL-3.0-only.
- Attribution: Buildrr89
- License: AGPL-3.0-only
- Project status: early alpha
- Project terms: The labels 5-Slab Taxonomy and Ambient Engine are retained as project terminology in this repository.
- Live Raid date: 2026-04-10

## Summary
- Screen Count: 2
- Node Count: 10
- Interactive Node Count: 4
- Duplicate Cluster Count: 5
- Recommendation Count: 1

## Scorecard
| Metric | Value | Evidence |
| --- | --- | --- |
| complexity | 58 | 2 screens; 10 nodes; 4 interactive nodes |
| reusability | 100 | 5 duplicate clusters; 5 duplicated nodes |
| accessibility_risk | 0 | 0 interactive nodes without accessibility identifiers; 0 interactive nodes without labels |
| migration_risk | 29 | 0 accessibility risk; 5 duplicate clusters |

## Screen Inventory
- Project Overview (project-overview): 5 nodes, 2 interactive, 5 duplicated, 0 accessibility gaps
- Analysis Review (analysis-review): 5 nodes, 2 interactive, 5 duplicated, 0 accessibility gaps

## Findings
### Repeated interactive structure appears 2 times across 2 screens.
- Rule ID: component_reuse_interactive_cluster
- Category: component_reuse
- Priority: P2
- Provenance: standards
- Evidence: cluster_fingerprint=25610e7cc32de585, screen_ids=analysis-review,project-overview, node_refs=project-overview#primary-cta,analysis-review#primary-cta

## Recommendations
### component_reuse - button
- Recommendation ID: rec-component_reuse_interactive_cluster-df13c83b
- Rule ID: component_reuse_interactive_cluster
- Priority: P2
- Confidence: high
- Problem: Repeated interactive structure appears 2 times across 2 screens.
- Change: Extract the repeated control into one reusable component and reuse it across screens.
- Reasoning: Copy-pasted interactive structure increases drift and makes future changes more expensive.
- Expected impact: Medium: reduces duplication and drift
- Effort: M
- Standards refs: Apple HIG: consistency, Material 3: reusable component patterns
- Benchmark refs: none
- Provenance: standards
- Evidence: cluster_fingerprint=25610e7cc32de585, screen_ids=analysis-review,project-overview, node_refs=project-overview#primary-cta,analysis-review#primary-cta

## Roadmap
- Step 1: Extract the repeated control into one reusable component and reuse it across screens. (P2, M)
