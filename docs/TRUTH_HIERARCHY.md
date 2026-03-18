# TRUTH_HIERARCHY

## Purpose

This file defines how truth is resolved in this repository.

Use this order whenever docs, backlog items, templates, or source code appear to disagree.

## Truth order

1. `README.md`
2. `docs/TRUTH_HIERARCHY.md`
3. `docs/APP_SCOPE.md`
4. `docs/HARD_RISKS.md`
5. `docs/ARCHITECTURE.md`
6. `docs/BUILD_SHEET.md`
7. implementation contract docs:
   - `docs/DATA_CONTRACT.md`
   - `docs/MVP_REPORT_SPEC.md`
   - `docs/SCORING_MODEL.md`
   - `docs/RECOMMENDATION_ENGINE.md`
   - `docs/STANDARDS_PACK.md`
   - `docs/SECURITY_BASELINE.md`
8. source code and tests under `src/`, `agent/`, `web/`, and `tests/`
9. supportive docs and backlogs:
   - `docs/NEXT_EXECUTION_BACKLOG.md`
   - `docs/OPEN_SOURCE_ADOPTION_BACKLOG.md`
   - issue templates
   - PR template
   - local skills and editor rules

## Interpretation rules

- `RADE.md` is the strategic product north star.
- `RADE.md` is not a claim that every future surface already exists in the current repo.
- Current implementation truth lives in the scope, build, contract docs, and executable tests.
- If source code and tests differ from a doc, treat the code and tests as executable truth and update the doc in the same change.
- Supportive docs must never invent behavior that is not present in the canonical docs and code.

## Unknown handling

- Prefer `UNKNOWN / NEEDS DECISION` over guessed behavior.
- Do not infer hosted architecture, auth, persistence, queueing, or tenant behavior from strategic language alone.
- Do not imply `Next.js`, `FastAPI`, `Redis`, `object storage`, or hosted auth are active unless the current implementation docs and code prove it.

## Change rule

- Any change to public behavior, report shape, validation, workflow, or security expectations must update the affected canonical docs and tests in the same PR.
