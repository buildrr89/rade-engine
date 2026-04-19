# RADE report diff

- Base report: Legacy App (`com.example.legacyapp`, `ios`) at `2026-03-18T00:00:00Z`
- Head report: Legacy App (`com.example.legacyapp`, `ios`) at `2026-03-20T00:00:00Z`
- Legal notice: Copyright (c) 2026 Buildrr89. Licensed under AGPL-3.0-only.
- Attribution: Buildrr89
- License: AGPL-3.0-only
- Project status: early alpha
- Project terms: The labels 5-Slab Taxonomy and Ambient Engine are retained as project terminology in this repository.
- Live Raid date: 2026-03-20

## Score Delta

| Metric | Direction | Base | Head | Delta | Status |
| --- | --- | ---: | ---: | ---: | --- |
| complexity | lower is better | 58 | 52 | -6 | improved |
| reusability | higher is better | 86 | 90 | +4 | improved |
| accessibility_risk | lower is better | 70 | 44 | -26 | improved |
| migration_risk | lower is better | 59 | 48 | -11 | improved |

Accessibility risk direction: improved.
Migration risk direction: improved.

## Recommendations

- Added: 1
- Removed: 1
- Unchanged: 1

### Added recommendations

- `rec-migration_sequence_accessibility_before_reuse-33333333` | migration | Settings Screen | P2

### Removed recommendations

- `rec-accessibility_missing_identifier-11111111` | accessibility | Primary CTA | P1

## Repeated Structure

- Added clusters: 1
- Removed clusters: 1
- Changed clusters: 1
- Unchanged clusters: 0

### Changed clusters

- `cluster-alpha` expanded from 2 to 3 nodes; added node refs: `settings:button:save`

### Added clusters

- `cluster-gamma` | count 2 | interactive `False`

### Removed clusters

- `cluster-beta` | count 3 | interactive `False`
