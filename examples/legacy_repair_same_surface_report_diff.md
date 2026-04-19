# RADE report diff

- Base report: Legacy Repair App (`com.example.legacyapp`, `ios`) at `2026-03-22T00:00:00Z`
- Head report: Legacy Repair App (`com.example.legacyapp`, `ios`) at `2026-04-10T00:00:00Z`
- Legal notice: Copyright (c) 2026 Buildrr89. Licensed under AGPL-3.0-only.
- Attribution: Buildrr89
- License: AGPL-3.0-only
- Project status: early alpha
- Project terms: The labels 5-Slab Taxonomy and Ambient Engine are retained as project terminology in this repository.
- Live Raid date: 2026-04-10

## Score Delta

| Metric | Direction | Base | Head | Delta | Status |
| --- | --- | ---: | ---: | ---: | --- |
| complexity | lower is better | 58 | 58 | 0 | unchanged |
| reusability | higher is better | 86 | 100 | +14 | improved |
| accessibility_risk | lower is better | 70 | 0 | -70 | improved |
| migration_risk | lower is better | 59 | 29 | -30 | improved |

Accessibility risk direction: improved.
Migration risk direction: improved.

## Recommendations

- Added: 0
- Removed: 2
- Unchanged: 1

### Added recommendations

- none

### Removed recommendations

- `rec-accessibility_missing_identifier-8c7b61bc` | accessibility | interactive_nodes_without_accessibility_identifier | P1
- `rec-migration_sequence_accessibility_before_reuse-536109ca` | migration_sequencing | accessibility-before-reuse | P1

## Repeated Structure

- Added clusters: 1
- Removed clusters: 0
- Changed clusters: 0
- Unchanged clusters: 4

### Changed clusters

- none

### Added clusters

- `49feb0c0396f4dff` | count 2 | interactive `True`

### Removed clusters

- none
