# TRUTH_HIERARCHY

## Purpose

This file defines how truth is resolved in this repository.

Use this order whenever docs, backlog items, templates, or source code appear to disagree.

## Truth order

1. `README.md`
2. `PRD.md`
3. `docs/TRUTH_HIERARCHY.md`
4. `docs/APP_SCOPE.md`
5. `docs/HARD_RISKS.md`
6. `docs/ARCHITECTURE.md`
7. `docs/BUILD_SHEET.md`
8. implementation contract docs:
   - `docs/DATA_CONTRACT.md`
   - `docs/MVP_REPORT_SPEC.md`
   - `docs/SCORING_MODEL.md`
   - `docs/RECOMMENDATION_ENGINE.md`
   - `docs/STANDARDS_PACK.md`
   - `docs/SECURITY_BASELINE.md`
9. source code and tests under `src/`, `agent/`, `web/`, and `tests/`
10. supportive docs and backlogs:
   - `docs/NEXT_EXECUTION_BACKLOG.md`
   - `docs/OPEN_SOURCE_ADOPTION_BACKLOG.md`
   - `docs/PHASE_1_COMPONENTIZATION.md`
   - `docs/PR_WORKFLOW.md`
   - issue templates
   - PR template
   - local skills and editor rules

## Interpretation rules

- `PRD.md` is the current product definition for the repo.
- `PRD.md` is not a claim that every secondary or exploratory surface is already a full product workflow.
- Current implementation truth lives in the scope, build, contract docs, and executable tests.
- If source code and tests differ from a doc, treat the code and tests as executable truth and update the doc in the same change.
- Supportive docs must never invent behavior that is not present in the canonical docs and code.
- Historical files such as `RADE.md` or `RADE2.0.md` are archival only unless this truth order explicitly promotes them again.

## Unknown handling

- Prefer `UNKNOWN / NEEDS DECISION` over guessed behavior.
- Do not infer hosted architecture, auth, persistence, queueing, or tenant behavior from product language alone.
- Do not imply `Next.js`, `FastAPI`, `Redis`, `object storage`, or hosted auth are active unless the current implementation docs and code prove it.
- Do not treat tested library boundaries as shipped product surfaces without an explicit scope statement.

## Change rule

- Any change to public behavior, report shape, validation, workflow, or security expectations must update the affected canonical docs and tests in the same PR.
