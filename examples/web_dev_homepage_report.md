# RADE modernization report

- Report version: 1.0
- Generated at: 2026-03-22T00:00:00Z
- App ID: dev.web.homepage
- Project: web.dev Homepage Snapshot
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
- Node Count: 19
- Interactive Node Count: 14
- Duplicate Cluster Count: 3
- Recommendation Count: 3

## Scorecard
| Metric | Value | Evidence |
| --- | --- | --- |
| complexity | 98 | 1 screens; 19 nodes; 14 interactive nodes |
| reusability | 100 | 3 duplicate clusters; 7 duplicated nodes |
| accessibility_risk | 100 | 14 interactive nodes without accessibility identifiers; 0 interactive nodes without labels |
| migration_risk | 79 | 100 accessibility risk; 3 duplicate clusters |

## Screen Inventory
- web.dev Home (web-dev-home): 19 nodes, 14 interactive, 10 duplicated, 14 accessibility gaps

## Findings
### 14 interactive nodes are missing accessibility identifiers.
- Rule ID: accessibility_missing_identifier
- Category: accessibility
- Priority: P1
- Provenance: standards
- Evidence: web-dev-home#nav-baseline, web-dev-home#nav-how-to-use-baseline, web-dev-home#nav-blog, web-dev-home#nav-case-studies, web-dev-home#nav-search, web-dev-home#language-switcher, web-dev-home#sign-in, web-dev-home#announcement-register, web-dev-home#platform-html, web-dev-home#platform-css, web-dev-home#platform-javascript, web-dev-home#platform-html-learn-more, web-dev-home#platform-css-learn-more, web-dev-home#platform-javascript-learn-more

### Fix accessibility on the repeated primary action before expanding reuse or visual refinement.
- Rule ID: migration_sequence_accessibility_before_reuse
- Category: migration_sequencing
- Priority: P1
- Provenance: standards
- Evidence: missing_accessibility_node_refs=web-dev-home#nav-baseline,web-dev-home#nav-how-to-use-baseline,web-dev-home#nav-blog,web-dev-home#nav-case-studies,web-dev-home#nav-search,web-dev-home#language-switcher,web-dev-home#sign-in,web-dev-home#announcement-register,web-dev-home#platform-html,web-dev-home#platform-css,web-dev-home#platform-javascript,web-dev-home#platform-html-learn-more,web-dev-home#platform-css-learn-more,web-dev-home#platform-javascript-learn-more, repeated_interactive_cluster_fingerprint=784bfa8762478fdc, primary_reuse_target=web-dev-home#nav-baseline

### Repeated interactive structure appears 4 times across 1 screens.
- Rule ID: component_reuse_interactive_cluster
- Category: component_reuse
- Priority: P2
- Provenance: standards
- Evidence: cluster_fingerprint=784bfa8762478fdc, screen_ids=web-dev-home, node_refs=web-dev-home#nav-baseline,web-dev-home#nav-how-to-use-baseline,web-dev-home#nav-blog,web-dev-home#nav-case-studies

## Recommendations
### accessibility - interactive_nodes_without_accessibility_identifier
- Recommendation ID: rec-accessibility_missing_identifier-ba3a2f81
- Rule ID: accessibility_missing_identifier
- Priority: P1
- Confidence: medium
- Problem: 14 interactive nodes are missing accessibility identifiers.
- Change: Add stable accessibility identifiers and preserve the accessible name, role, and value for each interactive node.
- Reasoning: Interactive controls without identifiers are harder to test, verify, and support for assistive technologies.
- Expected impact: High: removes assistive technology blockers
- Effort: M
- Standards refs: WCAG 2.2 4.1.2 Name, Role, Value, Apple HIG: accessibility and clarity
- Benchmark refs: none
- Provenance: standards
- Evidence: web-dev-home#nav-baseline, web-dev-home#nav-how-to-use-baseline, web-dev-home#nav-blog, web-dev-home#nav-case-studies, web-dev-home#nav-search, web-dev-home#language-switcher, web-dev-home#sign-in, web-dev-home#announcement-register, web-dev-home#platform-html, web-dev-home#platform-css, web-dev-home#platform-javascript, web-dev-home#platform-html-learn-more, web-dev-home#platform-css-learn-more, web-dev-home#platform-javascript-learn-more

### migration_sequencing - accessibility-before-reuse
- Recommendation ID: rec-migration_sequence_accessibility_before_reuse-4783a0bb
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
- Evidence: missing_accessibility_node_refs=web-dev-home#nav-baseline,web-dev-home#nav-how-to-use-baseline,web-dev-home#nav-blog,web-dev-home#nav-case-studies,web-dev-home#nav-search,web-dev-home#language-switcher,web-dev-home#sign-in,web-dev-home#announcement-register,web-dev-home#platform-html,web-dev-home#platform-css,web-dev-home#platform-javascript,web-dev-home#platform-html-learn-more,web-dev-home#platform-css-learn-more,web-dev-home#platform-javascript-learn-more, repeated_interactive_cluster_fingerprint=784bfa8762478fdc, primary_reuse_target=web-dev-home#nav-baseline

### component_reuse - link
- Recommendation ID: rec-component_reuse_interactive_cluster-18446b4d
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
- Evidence: cluster_fingerprint=784bfa8762478fdc, screen_ids=web-dev-home, node_refs=web-dev-home#nav-baseline,web-dev-home#nav-how-to-use-baseline,web-dev-home#nav-blog,web-dev-home#nav-case-studies

## Roadmap
- Step 1: Add stable accessibility identifiers and preserve the accessible name, role, and value for each interactive node. (P1, M)
- Step 2: Address the missing accessibility identifiers first, then extract and standardize the repeated control. (P1, M)
- Step 3: Extract the repeated control into one reusable component and reuse it across screens. (P2, M)
