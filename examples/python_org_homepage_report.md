# RADE modernization report

- Report version: 1.0
- Generated at: 2026-03-22T00:00:00Z
- App ID: org.python.www
- Project: Python.org Homepage Snapshot
- Platform: web
- Standards pack: 2026-Q1
- Legal notice: Copyright (c) 2026 Buildrr89. Licensed under AGPL-3.0-only.
- Attribution: Buildrr89
- License: AGPL-3.0-only
- Project status: early alpha
- Project terms: The labels 5-Slab Taxonomy and Ambient Engine are retained as project terminology in this repository.
- Live Raid date: 2026-03-22

## Summary
- Screen Count: 1
- Node Count: 16
- Interactive Node Count: 11
- Duplicate Cluster Count: 2
- Recommendation Count: 3

## Scorecard
| Metric | Value | Evidence |
| --- | --- | --- |
| complexity | 83 | 1 screens; 16 nodes; 11 interactive nodes |
| reusability | 98 | 2 duplicate clusters; 6 duplicated nodes |
| accessibility_risk | 100 | 10 interactive nodes without accessibility identifiers; 0 interactive nodes without labels |
| migration_risk | 71 | 100 accessibility risk; 2 duplicate clusters |

## Screen Inventory
- Python.org Home (python-org-home): 16 nodes, 11 interactive, 8 duplicated, 10 accessibility gaps

## Findings
### 10 interactive nodes are missing accessibility identifiers.
- Rule ID: accessibility_missing_identifier
- Category: accessibility
- Priority: P1
- Provenance: standards
- Evidence: python-org-home#nav-about, python-org-home#nav-downloads, python-org-home#nav-documentation, python-org-home#nav-community, python-org-home#search-go, python-org-home#hero-learn-more, python-org-home#resource-get-started, python-org-home#resource-download, python-org-home#resource-docs, python-org-home#resource-jobs

### Fix accessibility on the repeated primary action before expanding reuse or visual refinement.
- Rule ID: migration_sequence_accessibility_before_reuse
- Category: migration_sequencing
- Priority: P1
- Provenance: standards
- Evidence: missing_accessibility_node_refs=python-org-home#nav-about,python-org-home#nav-downloads,python-org-home#nav-documentation,python-org-home#nav-community,python-org-home#search-go,python-org-home#hero-learn-more,python-org-home#resource-get-started,python-org-home#resource-download,python-org-home#resource-docs,python-org-home#resource-jobs, repeated_interactive_cluster_fingerprint=52a6cab3351e0d62, primary_reuse_target=python-org-home#resource-get-started

### Repeated interactive structure appears 4 times across 1 screens.
- Rule ID: component_reuse_interactive_cluster
- Category: component_reuse
- Priority: P2
- Provenance: standards
- Evidence: cluster_fingerprint=52a6cab3351e0d62, screen_ids=python-org-home, node_refs=python-org-home#resource-get-started,python-org-home#resource-download,python-org-home#resource-docs,python-org-home#resource-jobs

## Recommendations
### accessibility - interactive_nodes_without_accessibility_identifier
- Recommendation ID: rec-accessibility_missing_identifier-70884120
- Rule ID: accessibility_missing_identifier
- Priority: P1
- Confidence: medium
- Problem: 10 interactive nodes are missing accessibility identifiers.
- Change: Add stable accessibility identifiers and preserve the accessible name, role, and value for each interactive node.
- Reasoning: Interactive controls without identifiers are harder to test, verify, and support for assistive technologies.
- Expected impact: High: removes assistive technology blockers
- Effort: M
- Standards refs: WCAG 2.2 4.1.2 Name, Role, Value, Apple HIG: accessibility and clarity
- Benchmark refs: none
- Provenance: standards
- Evidence: python-org-home#nav-about, python-org-home#nav-downloads, python-org-home#nav-documentation, python-org-home#nav-community, python-org-home#search-go, python-org-home#hero-learn-more, python-org-home#resource-get-started, python-org-home#resource-download, python-org-home#resource-docs, python-org-home#resource-jobs

### migration_sequencing - accessibility-before-reuse
- Recommendation ID: rec-migration_sequence_accessibility_before_reuse-29b66fc7
- Rule ID: migration_sequence_accessibility_before_reuse
- Priority: P1
- Confidence: high
- Problem: Fix accessibility on the repeated primary action before expanding reuse or visual refinement.
- Change: Address the missing accessibility identifiers first, then extract and standardize the repeated control.
- Reasoning: Accessibility fixes reduce user-facing risk faster than structure-only cleanup and make reuse safer.
- Expected impact: High: reduces future rework risk
- Effort: M
- Standards refs: WCAG 2.2: accessibility first, Apple HIG: system consistency
- Benchmark refs: none
- Provenance: standards
- Evidence: missing_accessibility_node_refs=python-org-home#nav-about,python-org-home#nav-downloads,python-org-home#nav-documentation,python-org-home#nav-community,python-org-home#search-go,python-org-home#hero-learn-more,python-org-home#resource-get-started,python-org-home#resource-download,python-org-home#resource-docs,python-org-home#resource-jobs, repeated_interactive_cluster_fingerprint=52a6cab3351e0d62, primary_reuse_target=python-org-home#resource-get-started

### component_reuse - link
- Recommendation ID: rec-component_reuse_interactive_cluster-d3c2246a
- Rule ID: component_reuse_interactive_cluster
- Priority: P2
- Confidence: high
- Problem: Repeated interactive structure appears 4 times across 1 screens.
- Change: Extract the repeated control into one reusable component and reuse it across screens.
- Reasoning: Copy-pasted interactive structure increases drift and makes future changes more expensive.
- Expected impact: Medium: reduces duplication and drift
- Effort: M
- Standards refs: Apple HIG: consistency, Material 3: reusable component patterns
- Benchmark refs: none
- Provenance: standards
- Evidence: cluster_fingerprint=52a6cab3351e0d62, screen_ids=python-org-home, node_refs=python-org-home#resource-get-started,python-org-home#resource-download,python-org-home#resource-docs,python-org-home#resource-jobs

## Roadmap
- Step 1: Add stable accessibility identifiers and preserve the accessible name, role, and value for each interactive node. (P1, M)
- Step 2: Address the missing accessibility identifiers first, then extract and standardize the repeated control. (P1, M)
- Step 3: Extract the repeated control into one reusable component and reuse it across screens. (P2, M)
