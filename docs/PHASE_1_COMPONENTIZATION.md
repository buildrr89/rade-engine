# Phase 1: Componentization & Frame Intelligence

**Attribution:** Buildrr89  
**Status:** Planning / RFC  
**Version:** 0.1-alpha

---

## The Objective

To transition RADE from "Structural Capture" to **"Functional Componentization."** We aim to automatically generate a deterministic Figma-ready component library directly from the **5-Slab Taxonomy**.

---

## 1. Slab 03: Frame Heuristics

To solve the **False Grouping Risk** (Portals/Modals), we will implement a **Hybrid Anchor System**:

- **Primary:** Semantic HTML5 Landmarks (`<nav>`, `<main>`, `<aside>`).
- **Secondary:** A11y Tree Roles (`role="dialog"`, `role="complementary"`).
- **Tertiary:** Visual Bounding Box (VBox) calculations to catch elements that are "teleported" via JavaScript but visually live within a Frame.

### 1.1 Implementation note (executable slice)

**Heuristic Engine** pulses live in `src/core/slab03_hybrid_anchor.py` and are composed by `apply_slab03_hybrid_pulse()` (used by `src/engine/rade_orchestrator.py` after traversal):

- **Modal (highest priority):** `dialog` / `alertdialog` roots and descendants get `slab03:modal:<root_element_id>` plus `slab03_anchor_kind` (`a11y:dialog` / `a11y:dialog-descendant`). Innermost nested modal wins.
- **Landmark:** Semantic regions (`navigation` / `nav`, `main`, `complementary` / `aside`, `banner` / header element, `contentinfo` / `footer`) assign `slab03:landmark:<kind>:<slug>:<scope_hash>` and `a11y:landmark` / `a11y:landmark-descendant`. Skipped for nodes already under a modal frame. Innermost landmark wins.
- **VBox (tertiary):** `apply_vbox_tertiary_pulse` (composed last in `apply_slab03_hybrid_pulse`) assigns orphans: elements with **no** `slab03_frame_id` whose bounding-box center falls inside a landmark **root**’s bounds receive that root’s `slab03_frame_id`, `slab03_landmark_kind`, `slab03_figma_alias`, and `slab03_anchor_kind = visual:vbox-contained`. When several roots contain the center, **smallest area** wins (then `element_id`). Modal and existing landmark assignments are never overwritten.
- **Figma-oriented alias:** `slab03_figma_alias` (e.g. `Nav_Primary`, `Modal_Confirm_Purchase`) is attached for export previews; not a substitute for final Figma naming policy.

---

## 2. The DNA Pattern Store (Pattern-to-Component)

We will promote recurring **DNA PatternHashes** into **Component Candidates**.

### Confidence Tiers

- **Tier 1 (Exact):** Identical Slab 03/04 structure across multiple views.
- **Tier 2 (Variant):** Same Frame, different Decor (Slab 05).
- **Tier 3 (Manual):** High structural complexity, requires manual review.

### 2.1 Commercialization: PatternHash salt (brand isolation)

To reduce **library drift** and accidental cross-brand merging:

- Use **Slab 01 (The Land)** context (e.g., canonical site / screen identity) as part of the **PatternHash** salt so that structurally similar controls on different surfaces (e.g., Stripe vs Apple) produce **distinct** DNA identities unless explicitly linked by a future cross-brand policy.

Exact salt composition and stability rules are **UNKNOWN / NEEDS DECISION** until locked in `docs/DATA_CONTRACT.md` and fingerprint tests.

---

## Milestone Checklist

- [x] **Heuristic Engine:** Implement `Slab03_Hybrid_Anchor` (modal + landmark pulses shipped; VBox pending).
- [ ] **The Ref-Map:** Preserve cross-frame links (Plumbing) without merging Frame DNA.
- [x] **Figma Bridge v0 / v0.2.1:** `src/core/figma_bridge_v0.py` + `ConstructionGraph.to_figma_bridge_v0_manifest()` emit legal-wrapped JSON with `component_id` / `stable_component_key`, `figma_suggested_name`, per-frame aggregates (including `anchor_kinds_observed` from `slab03_anchor_kind`), `ref_map.wires` for Slab 04 plumbing, and empty `variant_axes` (reserved for Tier 2).
- [ ] **Pilot Verification:** Run "Deep Raid" on Stripe and Apple to compare Component Library drift.

---

Copyright (c) 2026 Buildrr89. Licensed under AGPL-3.0-only.
