# ARCHITECTURE

© 2026 RADE Project. All Rights Reserved.

## Purpose

This document defines the starting engine and the boundary between deconstruction and scraping.

## Principle

RADE does not start from pixels. It starts from the operating system accessibility tree.

- Android: `AccessibilityNodeInfo`
- iOS: `AXElement` / XCTest accessibility
- Web: DOM plus accessibility semantics where available

Pixels are fallback validation only.

## Deconstruction vs Scraping

Deconstruction means:

- observe the running interface
- read roles, labels, traits, containment, and bounds
- build a structural graph of the interface
- preserve logical relationships

Scraping means:

- copying rendered content without understanding structure
- treating pixels or text as the primary object

RADE is a deconstruction engine.

## Collection boundary

Allowed collection sources:

- authorized customer apps
- customer-consented devices or simulators
- public unauthenticated surfaces where collection is permitted

Forbidden collection behaviors:

- login bypass
- fake accounts
- stealth collection
- access-control circumvention

## Initial runtime target

The initial cloud target is AWS Device Farm with managed real-device sessions and Appium endpoints.

The orchestrator should be provider-adapter driven so the engine can later swap in equivalent device farms without changing the structural model.

## Edge Shield

Raw payloads must pass through the edge scrubber before durable persistence.

Required behavior:

- regex-first PII removal
- second-pass entity escalation for ambiguous free-form text
- preserve structural nodes and edges
- emit audit metadata for every redaction pass
- neutralize node-local sensitive strings into generic construction placeholders such as `DATA_SLOT_01` before persistence

## Deep Raid operating rules

The recursive crawler must emit rebuilding instructions, not a flat element list.

Required behavior:

- isolate repeating `03. Containers (The Frame)` patterns such as grids, flex rows, sidebars, and list shells as structural frames
- trace interactive `Links/Events` edges to their functional destinations so the graph records the app's plumbing, not just containment
- collapse repeated components into shared pattern identifiers derived from normalized functional DNA instead of literal labels or user data
- keep these rules deterministic so the same authorized surface yields the same frame, plumbing, and pattern graph on repeat runs

## Illustrator Bridge

The Illustrator bridge is export-only.

It maps accessibility roles and structural nodes to vector primitives:

- rectangles
- text paths
- swatches
- groups

Required export behavior:

- emit a deterministic force-relaxed schematic layout rather than a generic tree dump
- use the `Construction Dark` SVG treatment with `#04110b` background, `#62f2b1` node strokes, and `#98ffad` plumbing edges
- bias `03. Containers (The Frame)` nodes toward larger geometry and more central placement than `05. Assets (The Decor)` nodes
- inject `data-rade-dna` and `data-slab-layer` on every SVG `<g>` so downstream Illustrator selection can target plumbing, frames, and repeated DNA groups directly
- inject a `<metadata id="rade-metadata">` block plus a persistent `g#rade-legal` footer at the bottom-right of every blueprint with the Lead Architect watermark, Live Raid date, and proprietary `5-Slab Taxonomy` / `Ambient Engine` references

It is not the core model.

## Legal framing

The `5-Slab Taxonomy` and `Ambient Engine` are the exclusive intellectual property of Trung Nguyen (Buildrr89).

Use hiQ v. LinkedIn as a narrow CFAA-domain reference for public-facing collection logic.

Do not write the system as if hiQ is a blanket authorization to bypass gates, ignore terms, or collect private user content.

## Non-goals

- no pixel-first reverse engineering
- no LLM-based deterministic scoring
- no stealth collection model
- no hosted persistence assumptions inside the engine layer
