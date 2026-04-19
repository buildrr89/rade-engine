# RADE modernization report

- Report version: 1.0
- Generated at: 2026-03-22T00:00:00Z
- App ID: org.mozilla.mdn
- Project: MDN Homepage Snapshot
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
- Node Count: 24
- Interactive Node Count: 18
- Duplicate Cluster Count: 4
- Recommendation Count: 3

## Scorecard
| Metric | Value | Evidence |
| --- | --- | --- |
| complexity | 100 | 1 screens; 24 nodes; 18 interactive nodes |
| reusability | 100 | 4 duplicate clusters; 10 duplicated nodes |
| accessibility_risk | 100 | 18 interactive nodes without accessibility identifiers; 0 interactive nodes without labels |
| migration_risk | 88 | 100 accessibility risk; 4 duplicate clusters |

## Screen Inventory
- MDN Web Docs Home (mdn-home): 24 nodes, 18 interactive, 14 duplicated, 18 accessibility gaps

## Findings
### 18 interactive nodes are missing accessibility identifiers.
- Rule ID: accessibility_missing_identifier
- Category: accessibility
- Priority: P1
- Provenance: standards
- Evidence: mdn-home#nav-html, mdn-home#nav-css, mdn-home#nav-javascript, mdn-home#nav-web-apis, mdn-home#nav-blog, mdn-home#nav-search, mdn-home#theme-toggle, mdn-home#language-switcher, mdn-home#hero-link-css, mdn-home#hero-link-html, mdn-home#hero-link-javascript, mdn-home#hero-search, mdn-home#article-mdn-20, mdn-home#article-highlight-api, mdn-home#article-server-timing, mdn-home#article-resource-management, mdn-home#spotlight-profile, mdn-home#spotlight-get-involved

### Fix accessibility on the repeated primary action before expanding reuse or visual refinement.
- Rule ID: migration_sequence_accessibility_before_reuse
- Category: migration_sequencing
- Priority: P1
- Provenance: standards
- Evidence: missing_accessibility_node_refs=mdn-home#nav-html,mdn-home#nav-css,mdn-home#nav-javascript,mdn-home#nav-web-apis,mdn-home#nav-blog,mdn-home#nav-search,mdn-home#theme-toggle,mdn-home#language-switcher,mdn-home#hero-link-css,mdn-home#hero-link-html,mdn-home#hero-link-javascript,mdn-home#hero-search,mdn-home#article-mdn-20,mdn-home#article-highlight-api,mdn-home#article-server-timing,mdn-home#article-resource-management,mdn-home#spotlight-profile,mdn-home#spotlight-get-involved, repeated_interactive_cluster_fingerprint=46f94f2fbea74e17, primary_reuse_target=mdn-home#nav-html

### Repeated interactive structure appears 4 times across 1 screens.
- Rule ID: component_reuse_interactive_cluster
- Category: component_reuse
- Priority: P2
- Provenance: standards
- Evidence: cluster_fingerprint=46f94f2fbea74e17, screen_ids=mdn-home, node_refs=mdn-home#nav-html,mdn-home#nav-css,mdn-home#nav-javascript,mdn-home#nav-web-apis

## Recommendations
### accessibility - interactive_nodes_without_accessibility_identifier
- Recommendation ID: rec-accessibility_missing_identifier-0deb78f0
- Rule ID: accessibility_missing_identifier
- Priority: P1
- Confidence: medium
- Problem: 18 interactive nodes are missing accessibility identifiers.
- Change: Add stable accessibility identifiers and preserve the accessible name, role, and value for each interactive node.
- Reasoning: Interactive controls without identifiers are harder to test, verify, and support for assistive technologies.
- Expected impact: High: removes assistive technology blockers
- Effort: M
- Standards refs: WCAG 2.2 4.1.2 Name, Role, Value, Apple HIG: accessibility and clarity
- Benchmark refs: none
- Provenance: standards
- Evidence: mdn-home#nav-html, mdn-home#nav-css, mdn-home#nav-javascript, mdn-home#nav-web-apis, mdn-home#nav-blog, mdn-home#nav-search, mdn-home#theme-toggle, mdn-home#language-switcher, mdn-home#hero-link-css, mdn-home#hero-link-html, mdn-home#hero-link-javascript, mdn-home#hero-search, mdn-home#article-mdn-20, mdn-home#article-highlight-api, mdn-home#article-server-timing, mdn-home#article-resource-management, mdn-home#spotlight-profile, mdn-home#spotlight-get-involved

### migration_sequencing - accessibility-before-reuse
- Recommendation ID: rec-migration_sequence_accessibility_before_reuse-4ef453e7
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
- Evidence: missing_accessibility_node_refs=mdn-home#nav-html,mdn-home#nav-css,mdn-home#nav-javascript,mdn-home#nav-web-apis,mdn-home#nav-blog,mdn-home#nav-search,mdn-home#theme-toggle,mdn-home#language-switcher,mdn-home#hero-link-css,mdn-home#hero-link-html,mdn-home#hero-link-javascript,mdn-home#hero-search,mdn-home#article-mdn-20,mdn-home#article-highlight-api,mdn-home#article-server-timing,mdn-home#article-resource-management,mdn-home#spotlight-profile,mdn-home#spotlight-get-involved, repeated_interactive_cluster_fingerprint=46f94f2fbea74e17, primary_reuse_target=mdn-home#nav-html

### component_reuse - button
- Recommendation ID: rec-component_reuse_interactive_cluster-96ccd145
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
- Evidence: cluster_fingerprint=46f94f2fbea74e17, screen_ids=mdn-home, node_refs=mdn-home#nav-html,mdn-home#nav-css,mdn-home#nav-javascript,mdn-home#nav-web-apis

## Roadmap
- Step 1: Add stable accessibility identifiers and preserve the accessible name, role, and value for each interactive node. (P1, M)
- Step 2: Address the missing accessibility identifiers first, then extract and standardize the repeated control. (P1, M)
- Step 3: Extract the repeated control into one reusable component and reuse it across screens. (P2, M)
