# Contributing

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Python 3.14.3 (pinned in `.python-version`)
- Node 20.19.5 (pinned in `.node-version`)
- [pnpm](https://pnpm.io/)

## Quickstart

```bash
git clone https://github.com/buildrr89/rade-engine.git
cd rade-engine
make bootstrap
make proof
```

If all 6 gates pass, you are ready to contribute.

## Scope rule

Contributions must follow the canonical read order and scope controls in [AGENTS.md](AGENTS.md) and [docs/TRUTH_HIERARCHY.md](docs/TRUTH_HIERARCHY.md). Read [docs/APP_SCOPE.md](docs/APP_SCOPE.md) before proposing new features.

## Workflow

1. Create a branch from `main` (`feat/`, `fix/`, or `docs/` prefix).
2. Keep changes small, testable, and reversible.
3. Update canonical docs and tests in the same PR when behavior or contracts change.
4. Run `make proof` and include exact outputs.
5. Open a PR using the [PR template](.github/pull_request_template.md).

## Proof required before review

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

## Where to start

- Look at [docs/NEXT_EXECUTION_BACKLOG.md](docs/NEXT_EXECUTION_BACKLOG.md) for the current backlog.
- Issues labeled `good first issue` are scoped for new contributors.
- If you are unsure whether a change is in scope, open an issue first.

## Security

Do not report vulnerabilities in public issues. Use the process in [SECURITY.md](SECURITY.md).

## Community

By participating, you agree to the expectations in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
