# Contributing

RADE is a proof-first open-source engine. Useful contributions are small, explicit, and backed by exact verification.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3.14.3
- Node 20.19.5
- [pnpm](https://pnpm.io/)

## Quickstart

```bash
git clone https://github.com/buildrr89/rade-engine.git
cd rade-engine
make bootstrap
make proof
```

If all proof gates pass, your environment is ready.

## Read This First

Before proposing scope changes, read the canonical files in this order:

1. [README.md](README.md)
2. [PRD.md](PRD.md)
3. [docs/TRUTH_HIERARCHY.md](docs/TRUTH_HIERARCHY.md)
4. [docs/APP_SCOPE.md](docs/APP_SCOPE.md)
5. [docs/HARD_RISKS.md](docs/HARD_RISKS.md)
6. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
7. [docs/BUILD_SHEET.md](docs/BUILD_SHEET.md)
8. [AGENTS.md](AGENTS.md)
9. [docs/CURSOR_RULES.md](docs/CURSOR_RULES.md)
10. Optional agent checklists: [docs/cursor-skills/README.md](docs/cursor-skills/README.md)

## Good Contribution Paths

- `Engine improvements`
  Validation, normalization, fingerprinting, deduplication, scoring, and recommendation logic under `src/core/`.
- `Adapters and collectors`
  Playwright collection, agent entrypoints, API boundaries, and deterministic input acquisition paths.
- `Scoring and evidence logic`
  Rules, thresholds, report IDs, recommendation ordering, and standards-backed evidence references.
- `Report improvements`
  JSON, Markdown, and HTML report clarity, artifact structure, and reviewer usability.
- `Docs and examples`
  README clarity, canonical docs, checked-in fixtures, checked-in reports, and contributor onboarding.

## Scope Rule

Contributions must follow the canonical read order and scope controls in [AGENTS.md](AGENTS.md) and [docs/TRUTH_HIERARCHY.md](docs/TRUTH_HIERARCHY.md).

- Do not broaden the product without updating canonical docs in the same change.
- Do not present planned behavior as implemented behavior unless code and proof support it.
- Prefer `UNKNOWN / NEEDS DECISION` over guessed behavior.

## Workflow

1. Create a short-lived branch from `main`.
2. Keep the change small, testable, and reversible.
3. Update canonical docs and tests in the same PR when behavior, contracts, workflow, or security expectations change.
4. Run the relevant proof commands before asking for review.
5. Open a PR using the [PR template](.github/pull_request_template.md).

## Proof Required Before Review

Run all gates with `make proof`, or individually:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m tests.runner
.venv/bin/ruff check src tests agent
.venv/bin/python -m black --check src tests agent
pnpm --dir web lint
pnpm --dir web test
```

If a proof command was not run, mark the result as unverified.

## Formatting

Auto-fix formatting before committing:

```bash
make format
```

## Picking Work

- Check [docs/NEXT_EXECUTION_BACKLOG.md](docs/NEXT_EXECUTION_BACKLOG.md) for the next proof slices.
- Issues labeled `good first issue` are intended to be low-risk entry points.
- If you want to add a new collector, score, artifact, or workflow surface, show the smallest proof slice first.

## Submitting A Strong PR

- State the problem and non-scope clearly.
- Include exact proof commands and exact outputs.
- Call out any `UNKNOWN / NEEDS DECISION` items directly.
- Keep architectural claims consistent with [docs/APP_SCOPE.md](docs/APP_SCOPE.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Security

Do not report vulnerabilities in public issues. Use the process in [SECURITY.md](SECURITY.md).

## Community

By participating, you agree to the expectations in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
