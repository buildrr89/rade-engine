# RADE

RADE is a software intelligence app for analyzing authorized product interfaces and returning evidence-backed recommendations for UI, UX, accessibility, and flow improvements.

This repository is bootstrapped to prove one thing first: a deterministic sample report path from fixture input to JSON and Markdown output.

## Current objective

Build the phase-0 proof slice:

1. load a sample iOS scan fixture
2. normalize and fingerprint the interface structure
3. deduplicate repeated structure
4. score the result deterministically
5. emit a modernization report in JSON and Markdown

## Repo order

Read these in order before changing behavior:

1. `README.md`
2. `docs/APP_SCOPE.md`
3. `docs/HARD_RISKS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/BUILD_SHEET.md`
6. `AGENTS.md`
7. `.cursor/rules.md`
8. `docs/NEXT_EXECUTION_BACKLOG.md`

## Canonical commands

Bootstrap:

```bash
uv sync --dev
pnpm --dir web install
```

Run tests:

```bash
uv run pytest
```

Run the proof slice:

```bash
uv run python -m src.core.cli analyze \
  --input examples/sample_ios_output.json \
  --app-id com.example.legacyapp \
  --json-output output/modernization_report.json \
  --md-output output/modernization_report.md
```

Run the API shell:

```bash
uv run uvicorn src.api.app:app --reload
```

Run the worker shell:

```bash
uv run python -m src.worker.main
```

Run the agent shell:

```bash
uv run python -m agent.cli scan
```

## Notes

- The repo is intentionally thin.
- Deterministic behavior matters more than breadth at this stage.
- `RADE.md` is the canonical product spec.

## Repository

- GitHub: [buildrr89/rade-project](https://github.com/buildrr89/rade-project)
