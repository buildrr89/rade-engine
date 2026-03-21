# RADE

Current stage: proof-first local analysis workspace.

Primary proven slice:

- local JSON input
- deterministic validation, normalization, layering, fingerprinting, deduplication
- deterministic scoring, recommendations, and roadmap
- scrubbed JSON and Markdown reports with legal metadata

Implemented but thin surfaces:

- WSGI API shell (`src/api/app.py`)
- worker shell (`src/worker/main.py`)
- web shell runtime (`web/lib/shell.mjs`)
- agent CLI wrapper (`agent/cli.py`)
- exploratory blueprint / SVG / Neo4j path (`src/demo/`, `src/engine/`, `src/database/`)

Not implemented as full product surfaces:

- hosted auth and tenants
- queue-backed execution
- analysis API route
- build connector
- real Next.js runtime
- end-to-end device-farm integration

Read repo truth in this order:

1. README.md
2. PRD.md
3. docs/TRUTH_HIERARCHY.md
4. docs/APP_SCOPE.md
5. docs/HARD_RISKS.md
6. docs/ARCHITECTURE.md
7. docs/BUILD_SHEET.md

Quickstart:

```bash
uv sync --dev
pnpm --dir web install
./rade-proof
uv run python -m src.core.cli analyze \
  --input tests/fixtures/sample_ios_output.json \
  --app-id com.example.legacyapp \
  --json-output output/modernization_report.json \
  --md-output output/modernization_report.md
```
