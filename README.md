# RADE

**Deterministic interface analysis engine for structural deduplication, accessibility gaps, and migration risk scoring.**

![Proof](https://github.com/buildrr89/rade-engine/actions/workflows/proof.yml/badge.svg)

RADE is shared early as an alpha technical thesis and open collaboration surface. The goal of this repository is to make the idea, the proof, and the implementation reviewable without pretending the project is more complete than it is.

## What It Does

RADE accepts a structured JSON payload or a public URL, runs deterministic structural analysis, and produces reproducible reports with evidence chains.

- **Structural fingerprinting and deduplication** - finds repeated interface patterns across screens
- **Accessibility gap detection** - standards-backed findings with stable identifiers
- **Migration risk and complexity scoring** - deterministic scores for reusability, complexity, and risk
- **Reproducible output** - same input, same output, every time except `generated_at`

## Try It

Prerequisites: `uv`, Python `3.14.3`, Node `20.19.5`, and `pnpm`.

```bash
# Install
uv sync --dev
.venv/bin/python -m playwright install chromium
pnpm --dir web install

# Analyze a public URL
uv run python -m src.core.cli analyze   --url https://example.com   --json-output output/example_report.json   --md-output output/example_report.md

# Or analyze a local JSON fixture
uv run python -m src.core.cli analyze   --input examples/sample_ios_output.json   --app-id com.example.legacyapp   --json-output output/modernization_report.json   --md-output output/modernization_report.md
```

See [examples/python_org_homepage_report.md](examples/python_org_homepage_report.md) for a checked-in report example.

## How It Works

```text
Input (JSON or URL)
  -> Schema validation
  -> Normalization and slab-layer inference
  -> Structural fingerprinting
  -> Deduplication into ordered clusters
  -> Scoring (complexity, reusability, accessibility risk, migration risk)
  -> Standards-backed recommendations and roadmap
  -> Scrubbed JSON + Markdown report output
```

The analysis pipeline is fully deterministic: no LLM inference, no non-deterministic scoring, and no network calls during analysis itself.

## Current Stage

RADE is in **early alpha**.

**What works today:**
- CLI analysis from local JSON fixtures or public URLs collected via Playwright
- `POST /analyze` served through `src.api.wsgi:application` with static API key auth
- Deterministic scoring, recommendations, and roadmap generation
- PII scrubbing with preserved structural identifiers

**Exploratory or secondary surfaces:**
- Accessibility-tree-to-SVG blueprint pipeline
- Neo4j Aura graph ingest boundary
- Figma Bridge v0 manifest export
- Slab 03 hybrid frame intelligence

**Not built yet:**
- Hosted auth, tenants, and persisted history
- Queue-backed execution
- Interactive HTML reports
- GitHub Action for CI/CD integration

See [docs/APP_SCOPE.md](docs/APP_SCOPE.md) for the current implementation boundary.

## Development Setup

```bash
# Python + web dependencies
uv sync --dev
.venv/bin/python -m playwright install chromium
pnpm --dir web install

# Proof gates
.venv/bin/python -m pytest -q
.venv/bin/python -m tests.runner
.venv/bin/ruff check src tests agent
.venv/bin/python -m black --check src tests agent
pnpm --dir web lint
pnpm --dir web test
```

Or use the Makefile:

```bash
make bootstrap
make test
make lint
make analyze
```

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture document.

| Layer | Entry point | Description |
|-------|-------------|-------------|
| CLI | `src/core/cli.py` | Primary analysis command |
| Web collector | `src/collectors/web_dom_adapter.py` | Playwright ARIA snapshot collection |
| Report engine | `src/core/report_generator.py` | Validation, scoring, recommendations, output |
| API | `src/api/app.py` | `POST /analyze` with API key auth |
| Scrubber | `src/scrubber/pii_scrubber.py` | PII removal preserving stable identifiers |
| Blueprint (exploratory) | `src/demo/run_raid_visualizer.py` | SVG blueprint from accessibility trees |

## Documentation

| Document | Purpose |
|----------|---------|
| [PRD.md](PRD.md) | Current product definition |
| [docs/APP_SCOPE.md](docs/APP_SCOPE.md) | Canonical implementation scope |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture and boundaries |
| [docs/BUILD_SHEET.md](docs/BUILD_SHEET.md) | Current proof target and verified commands |
| [docs/NEXT_EXECUTION_BACKLOG.md](docs/NEXT_EXECUTION_BACKLOG.md) | Ordered proof slices with acceptance criteria |
| [docs/SECURITY_BASELINE.md](docs/SECURITY_BASELINE.md) | Security controls and data handling |

## Examples

Real-world analysis outputs from public websites:

- [python.org homepage report](examples/python_org_homepage_report.md)
- [MDN homepage report](examples/mdn_homepage_report.md)
- [web.dev homepage report](examples/web_dev_homepage_report.md)

## Legal

RADE is licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).

The labels `5-Slab Taxonomy` and `Ambient Engine` are retained as project terminology in this repository.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Small, proof-backed changes are preferred.

## Security

See [SECURITY.md](SECURITY.md). Do not report vulnerabilities in public issues.
