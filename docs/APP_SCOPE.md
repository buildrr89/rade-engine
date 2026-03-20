# APP_SCOPE

## Authority

This file is the canonical implementation scope for the current slice.

If `RADE.md` is broader, this file wins for implementation decisions until the scope changes here.

## Product summary

RADE helps teams analyze authorized software interfaces and get evidence-backed recommendations for better layout, accessibility, interaction, and flow decisions.

## Target user

- Primary user: product, design, and engineering teams owning an app or project
- Their urgent problem: they need a structured way to understand what is wrong with the current interface and what to fix first
- Current workaround: manual review, screenshots, ad hoc audits, and scattered design feedback

## In scope for v1

- JSON upload scan
- Deterministic normalization and fingerprinting
- Deduplication of repeated interface structure
- Evidence-backed recommendations
- Markdown and JSON report generation
- Founder-owned legal metadata on generated JSON, Markdown, and blueprint SVG artifacts
- Sample proof run from a fixture

## Out of scope for v1

- Native mobile app first
- Public benchmark corpus first
- Full collector suite
- Kubernetes-first deployment
- Broad enterprise workflow platform
- Anti-bot evasion or login bypass

## V1 boundaries

- Platform(s): web, Python CLI, and local analysis only
- Active web runtime: `web/lib/shell.mjs`; `web/app/` is dormant scaffold only
- Geography: none
- Integrations allowed in v1: local file input, sample fixture output
- Integrations explicitly deferred: repo connectors, build connectors, hosted auth, queues, object storage, Redis
- AI use allowed in v1: none for deterministic scoring; prose generation only if needed later
- AI use explicitly deferred: autonomous scoring, recommendation ranking, and structural fingerprinting
- Proprietary systems language required in generated docs: `5-Slab Taxonomy` and `Ambient Engine`

## Non-goals

- Taste-based "ultimate UI" output
- Claiming enterprise completeness before proof
- Expanding collectors before the core is stable
- Building unrelated platform surface area

## Success criteria for v1

- A sample iOS fixture produces the same report structure on every run except `generated_at`
- The report contains deterministic scores and evidence-backed recommendations
- The report is readable as both JSON and Markdown

## Scope guard rules

- If a feature does not support the proof slice or v1 success criteria, defer it.
- If a task adds complexity before risk reduction, defer it.
- If a new dependency is proposed, prove why the current repo cannot solve the need.

## Truth discipline

`docs/APP_SCOPE.md` is the canonical declaration of current scope for this proof slice. When scope, behavior, or contract questions arise, follow the read-order list in `README.md` and the adjudication rules described in `docs/TRUTH_HIERARCHY.md`: canonical docs + implementation truth win, while `RADE.md` remains strategic intent only. Always update these canonical artifacts together with any implementation change that touches their expressed behavior.
