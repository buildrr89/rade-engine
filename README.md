# RADE Engine

**Deterministic UI intelligence for repeated structure, accessibility gaps, and modernization risk.**

For frontend teams, agencies, design-system work, modernization efforts, and accessibility audits: analyze a public web page or structured UI payload and get proof-backed JSON, Markdown, and HTML outputs you can review, diff, and trust.

![Proof](https://github.com/buildrr89/rade-engine/actions/workflows/proof.yml/badge.svg)

Fastest way to understand the project:

- Open a checked-in report now: [Markdown](examples/python_org_homepage_report.md) · [JSON](examples/python_org_homepage_report.json)
- Open a checked-in diff now: [Markdown](examples/python_to_web_dev_report_diff.md) · [JSON](examples/python_to_web_dev_report_diff.json)
- Run it locally in two commands: `make bootstrap` and `make analyze`
- Expect deterministic outputs with stable evidence identifiers, not one-shot AI opinion text

## Why This Exists

Most interface reviews still rely on screenshots, spreadsheets, taste-based commentary, or opaque AI summaries. That makes it hard to answer basic questions with evidence:

- What structures repeat across the interface?
- Where are the accessibility gaps?
- Which surfaces are expensive to modernize?
- What changed between two runs?

RADE exists to turn interface inspection into a deterministic, traceable workflow. The current engine accepts authorized structured payloads or public web URLs, analyzes them without model inference, and emits artifacts that can be reviewed by humans or consumed by tooling.

## What You Get

- Repeated-structure analysis that clusters duplicated interface patterns across screens
- Accessibility gap detection with stable identifiers and standards-backed findings
- Modernization and migration risk scoring grounded in deterministic rules
- JSON, Markdown, and interactive HTML reports from the same engine run
- Deterministic report-to-report diffs for tracking interface change over time
- Scrubbed artifacts that preserve structural traceability without pretending the repo is a hosted platform
- A GitHub Action boundary for deterministic PR score diffs when your repository stores RADE fixtures

## Quick Start

Prerequisites:

- [uv](https://docs.astral.sh/uv/)
- Python 3.14.3
- Node 20.19.5
- [pnpm](https://pnpm.io/)

Run the sample proof path:

```bash
make bootstrap
make analyze
```

This writes:

- `output/modernization_report.json`
- `output/modernization_report.md`
- `output/modernization_report.html`

Compare two existing RADE JSON reports:

```bash
uv run python -m src.core.cli diff \
  --base-report examples/python_org_homepage_report.json \
  --head-report examples/web_dev_homepage_report.json
```

This writes:

- `output/report_diff.json`
- `output/report_diff.md`

Run against a public URL:

```bash
uv run python -m src.core.cli analyze \
  --url https://example.com \
  --json-output output/example_report.json \
  --md-output output/example_report.md \
  --html-output output/example_report.html
```

Run against a local UI payload:

```bash
uv run python -m src.core.cli analyze \
  --input examples/sample_ios_output.json \
  --app-id com.example.legacyapp \
  --json-output output/modernization_report.json \
  --md-output output/modernization_report.md \
  --html-output output/modernization_report.html
```

## Example Workflow

1. Point RADE at a public web page or a structured export of an existing interface.
2. Review repeated clusters, accessibility findings, and prioritized modernization risk in the HTML or Markdown report.
3. Compare two RADE JSON reports to see score direction, recommendation changes, and repeated-structure changes over time.
4. Use the JSON outputs for automation, diffing, or downstream scoring checks.
5. If your workflow stores fixtures in git, use the GitHub Action to compare score deltas on pull requests.

## Output Artifacts

- `JSON report`
  Machine-readable output with scores, findings, recommendations, evidence IDs, and repo metadata.
- `Markdown report`
  Review-friendly output for PRs, docs, and audit trails.
- `HTML report`
  Interactive output with filters, score bars, and expandable sections for findings and recommendations.
- `JSON report diff`
  Machine-readable base/head delta with score direction, recommendation changes, and duplicate-cluster changes.
- `Markdown report diff`
  Review-friendly change log for before/after interface runs.
- `GitHub Action comment`
  Deterministic base/head score deltas for `reusability` and `accessibility_risk` when run on fixture-backed pull requests.

See [examples/](examples/) for checked-in report artifacts from public websites.

## Why This Is Different

RADE is not a screenshot-first redesign bot and it does not try to sell confidence through vague language.

- Deterministic inspection instead of one-shot AI judgments
- Reproducible evidence chains instead of unverifiable scoring magic
- Stable identifiers and explicit report contracts instead of fuzzy summaries
- Auditable logic that can be tested and reviewed in-repo
- Structural analysis that can feed CI, docs, and downstream tooling

## Why Deterministic Matters

The core promise is simple: same input, same report, except for `generated_at`.

That matters because deterministic outputs are:

- Diffable in pull requests
- Safe to baseline in tests
- Easier to trust in modernization planning
- Easier to extend without losing traceability
- More useful than black-box advice when teams need proof, not style commentary

## Who This Is For

- Frontend teams trying to understand duplicated UI and modernization effort
- Agencies that need sharper discovery and audit outputs before a rebuild
- Design-system teams looking for repeated structures and reuse opportunities
- Accessibility reviewers who need evidence-backed findings they can trace
- Engineering leads who want a deterministic interface analysis layer rather than subjective review decks

## Current Wedge

The current commercial wedge is deliberately narrow:

- Proof-backed analysis of repeated structure
- Proof-backed analysis of accessibility gaps
- Proof-backed analysis of migration and modernization risk

That wedge is useful today for frontend teams, agencies, design-system work, modernization efforts, and accessibility audits. It is narrow enough to run, inspect, and extend now, while still sitting on top of infrastructure that can support a much larger interface-intelligence system later.

## Long-Term Vision

Interfaces contain market intelligence.

If repeated UI structures, interaction patterns, and implementation conventions can be collected, normalized, and compared over time, they become more than audit outputs. They become an intelligence layer for understanding:

- how software interfaces are actually built
- which patterns repeat across products and categories
- where conventions are converging or fragmenting
- how interface structure changes as the market moves

RADE starts with deterministic interface analysis because the foundation needs to be inspectable before it can become strategically valuable.

## Contributing

Contributions are welcome, but the repo is proof-first.

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for setup, workflow, and exact proof expectations
- Use [docs/APP_SCOPE.md](docs/APP_SCOPE.md) and [docs/TRUTH_HIERARCHY.md](docs/TRUTH_HIERARCHY.md) before broadening behavior
- Favor small, reversible changes that improve the engine, collectors, scoring, reports, docs, or examples

If you want to fork it, the natural extension points are visible in the repo: collectors, scoring rules, report generation, API boundaries, fixtures, and CI workflows.

## Status / Roadmap

RADE is a public alpha. The current repo proves a real wedge, not a full hosted platform.

**Proven today**

- CLI analysis from local JSON fixtures
- CLI analysis from public unauthenticated URLs via Playwright
- Deterministic JSON, Markdown, and HTML report generation
- CLI comparison of two existing RADE JSON reports into deterministic JSON and Markdown diff artifacts
- `POST /analyze` through `src.api.wsgi:application` with static API key auth
- PII scrubbing that preserves stable structural identifiers
- Fixture-backed GitHub Action score diffs for pull requests

**Exploratory or secondary**

- Accessibility-tree-to-SVG blueprint generation
- Neo4j Aura ingest boundary for scrubbed structural graphs
- Figma Bridge v0 manifest export

**Not built yet**

- Hosted auth and tenant management
- Persisted analysis history
- Queue-backed execution
- Authenticated private-page collection
- Broad enterprise workflow surfaces

For exact implementation boundaries, see [docs/APP_SCOPE.md](docs/APP_SCOPE.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), and [docs/BUILD_SHEET.md](docs/BUILD_SHEET.md).

## Legal

RADE is licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).

The labels `5-Slab Taxonomy` and `Ambient Engine` are retained as project terminology in this repository.

## Security

See [SECURITY.md](SECURITY.md). Do not report vulnerabilities in public issues.
