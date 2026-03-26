# RADE modernization report

- Report version: 1.0
- Generated at: 2026-03-18T00:00:00Z
- App ID: com.example.legacyapp
- Project: Legacy Repair App
- Platform: ios
- Standards pack: 2026-Q1
- Legal notice: Copyright (c) 2026 Buildrr89. Licensed under AGPL-3.0-only.
- Attribution: Buildrr89
- License: AGPL-3.0-only
- Project status: early alpha
- Project terms: The labels 5-Slab Taxonomy and Ambient Engine are retained as project terminology in this repository.
- Live Raid date: 2026-03-18

## Summary
- Screen Count: 2
- Node Count: 10
- Interactive Node Count: 4
- Duplicate Cluster Count: 4
- Recommendation Count: 3

## Scorecard
| Metric | Value | Evidence |
| --- | --- | --- |
| complexity | 58 | 2 screens; 10 nodes; 4 interactive nodes |
| reusability | 86 | 4 duplicate clusters; 4 duplicated nodes |
| accessibility_risk | 70 | 2 interactive nodes without accessibility identifiers; 0 interactive nodes without labels |
| migration_risk | 59 | 70 accessibility risk; 4 duplicate clusters |

## Screen Inventory
- Project Overview (project-overview): 5 nodes, 2 interactive, 4 duplicated, 1 accessibility gaps
- Analysis Review (analysis-review): 5 nodes, 2 interactive, 4 duplicated, 1 accessibility gaps

## Findings
### 2 interactive nodes are missing accessibility identifiers.
- Rule ID: accessibility_missing_identifier
- Category: accessibility
- Priority: P1
- Provenance: standards
- Evidence: project-overview#primary-cta, analysis-review#primary-cta

### Fix accessibility on the repeated primary action before expanding reuse or visual refinement.
- Rule ID: migration_sequence_accessibility_before_reuse
- Category: migration_sequencing
- Priority: P1
- Provenance: standards
- Evidence: missing_accessibility_node_refs=project-overview#primary-cta,analysis-review#primary-cta, repeated_interactive_cluster_fingerprint=25610e7cc32de585, primary_reuse_target=project-overview#primary-cta

### Repeated interactive structure appears 2 times across 2 screens.
- Rule ID: component_reuse_interactive_cluster
- Category: component_reuse
- Priority: P2
- Provenance: standards
- Evidence: cluster_fingerprint=25610e7cc32de585, screen_ids=analysis-review,project-overview, node_refs=project-overview#primary-cta,analysis-review#primary-cta

## Recommendations
### accessibility - interactive_nodes_without_accessibility_identifier
- Recommendation ID: rec-accessibility_missing_identifier-8c7b61bc
- Rule ID: accessibility_missing_identifier
- Priority: P1
- Confidence: high
- Problem: 2 interactive nodes are missing accessibility identifiers.
- Change: Add stable accessibility identifiers and preserve the accessible name, role, and value for each interactive node.
- Reasoning: Interactive controls without identifiers are harder to test, verify, and support for assistive technologies.
- Expected impact: High: removes assistive technology blockers
- Effort: S
- Standards refs: WCAG 2.2 4.1.2 Name, Role, Value, Apple HIG: accessibility and clarity
- Benchmark refs: none
- Provenance: standards
- Evidence: project-overview#primary-cta, analysis-review#primary-cta

### migration_sequencing - accessibility-before-reuse
- Recommendation ID: rec-migration_sequence_accessibility_before_reuse-536109ca
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
- Evidence: missing_accessibility_node_refs=project-overview#primary-cta,analysis-review#primary-cta, repeated_interactive_cluster_fingerprint=25610e7cc32de585, primary_reuse_target=project-overview#primary-cta

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
- Step 1: Add stable accessibility identifiers and preserve the accessible name, role, and value for each interactive node. (P1, S)
- Step 2: Address the missing accessibility identifiers first, then extract and standardize the repeated control. (P1, M)
- Step 3: Extract the repeated control into one reusable component and reuse it across screens. (P2, M)
