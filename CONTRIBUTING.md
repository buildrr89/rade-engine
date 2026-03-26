# Contributing

## Scope rule

Contributions must follow the canonical read order and scope controls in [AGENTS.md](AGENTS.md) and [docs/TRUTH_HIERARCHY.md](docs/TRUTH_HIERARCHY.md).

## Workflow

1. Create a branch from `main`.
2. Keep changes small, testable, and reversible.
3. Update canonical docs in the same PR when behavior or contracts change.
4. Open a PR using `.github/pull_request_template.md`.

## Proof required before review

Run and include exact outputs for:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m tests.runner
.venv/bin/ruff check src tests agent
.venv/bin/python -m black --check src tests agent
pnpm --dir web lint
pnpm --dir web test
```

If a proof command was not run, mark the result as unverified.

## Security

Do not report vulnerabilities in public issues. Use the process in [SECURITY.md](SECURITY.md).

## Community

By participating, you agree to the expectations in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
