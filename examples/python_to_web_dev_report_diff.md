# RADE report diff

- Base report: Python.org Homepage Snapshot (`org.python.www`, `web`) at `2026-03-22T00:00:00Z`
- Head report: web.dev Homepage Snapshot (`dev.web.homepage`, `web`) at `2026-03-22T00:00:00Z`
- Legal notice: Copyright (c) 2026 Buildrr89. Licensed under AGPL-3.0-only.
- Attribution: Buildrr89
- License: AGPL-3.0-only
- Project status: early alpha
- Project terms: The labels 5-Slab Taxonomy and Ambient Engine are retained as project terminology in this repository.
- Live Raid date: 2026-03-22

## Score Delta

| Metric | Direction | Base | Head | Delta | Status |
| --- | --- | ---: | ---: | ---: | --- |
| complexity | lower is better | 83 | 98 | +15 | regressed |
| reusability | higher is better | 98 | 100 | +2 | improved |
| accessibility_risk | lower is better | 100 | 100 | 0 | unchanged |
| migration_risk | lower is better | 71 | 79 | +8 | regressed |

Accessibility risk direction: unchanged.
Migration risk direction: regressed.

## Recommendations

- Added: 3
- Removed: 3
- Unchanged: 0

### Added recommendations

- `rec-accessibility_missing_identifier-ba3a2f81` | accessibility | interactive_nodes_without_accessibility_identifier | P1
- `rec-component_reuse_interactive_cluster-18446b4d` | component_reuse | link | P2
- `rec-migration_sequence_accessibility_before_reuse-4783a0bb` | migration_sequencing | accessibility-before-reuse | P1

### Removed recommendations

- `rec-accessibility_missing_identifier-70884120` | accessibility | interactive_nodes_without_accessibility_identifier | P1
- `rec-component_reuse_interactive_cluster-d3c2246a` | component_reuse | link | P2
- `rec-migration_sequence_accessibility_before_reuse-29b66fc7` | migration_sequencing | accessibility-before-reuse | P1

## Repeated Structure

- Added clusters: 2
- Removed clusters: 1
- Changed clusters: 1
- Unchanged clusters: 0

### Changed clusters

- `784bfa8762478fdc` changed from 4 to 4 nodes; added node refs: `web-dev-home#nav-baseline`, `web-dev-home#nav-blog`, `web-dev-home#nav-case-studies`, `web-dev-home#nav-how-to-use-baseline`; removed node refs: `python-org-home#nav-about`, `python-org-home#nav-community`, `python-org-home#nav-documentation`, `python-org-home#nav-downloads`

### Added clusters

- `59437a97d18ace13` | count 3 | interactive `True`
- `b871c4c6b83d0ef0` | count 3 | interactive `True`

### Removed clusters

- `52a6cab3351e0d62` | count 4 | interactive `True`
