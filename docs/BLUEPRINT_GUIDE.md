# Blueprint Guide

## Redline report

When the structural DOM capture fails, RADE writes `redline_report.json` with the URL, title, last known accessibility state, and the capture error. Use it to distinguish an empty tree from a blocked or incomplete capture.

## Illustrator and Figma handoff

RADE SVGs keep `INTERACTIVE_PLUMBING` as a distinct group so Slab 04 links, buttons, and event edges can be inspected separately from Slab 05 decor. Group metadata keeps `data-rade-dna` and `data-slab-layer` available for deterministic review and bulk selection.

## Accessibility-first mapping

If a control is labeled from `aria-label` or `title` instead of visible text, the engine is preserving structural semantics over presentation noise.
