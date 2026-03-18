# HARD_RISKS

## How to use this file

This file exists to force proof-first development. Do not broaden the product before de-risking the items below.

## Risk 1 - Report contract drift

- Type: Technical
- Why this matters: if the report shape changes silently, tests and downstream consumers will not trust the output
- Current status: Proven
- What would de-risk it:
  - a locked data contract
  - golden report fixtures
  - a deterministic CLI proof run
- Smallest proof slice: one fixture to one JSON and one Markdown report
- Proof output expected:
  - Code path: `src/core/cli.py` and `src/core/report_generator.py`
  - Test: report shape comparison against a golden fixture
  - Screenshot / log / metric: command output showing the generated files
  - Pass condition: identical report content except `generated_at`

## Risk 2 - Sensitive data retention

- Type: Security
- Why this matters: raw captures can contain personal data, tokens, and secrets
- Current status: Proven
- What would de-risk it:
  - edge scrubber rules
  - explicit redaction tests
  - default short retention
- Smallest proof slice: a scrubber that redacts obvious sensitive strings in collector payloads and report artifacts before write
- Proof output expected:
  - Code path: `src/scrubber/pii_scrubber.py` and `src/core/report_generator.py`
  - Test: scrubber regression test and report artifact redaction test
  - Screenshot / log / metric: scrubbed JSON / Markdown output
  - Pass condition: sensitive strings are removed or masked

## Risk 3 - Bootstrap and toolchain drift

- Type: Delivery
- Why this matters: if the project is not reproducible, every later slice slows down
- Current status: Proven
- What would de-risk it:
  - pinned Python version
  - pinned Node version
  - a stable repo layout
  - a working sample proof command
  - CI proof gates
- Smallest proof slice: run the sample report command from the pinned repository layout
- Proof output expected:
  - Code path: `pyproject.toml`, `.python-version`, `.node-version`, `Makefile`, `.github/workflows/proof.yml`, `rade-proof`, `rade-devserver`
  - Test: bootstrap and proof commands
  - Screenshot / log / metric: command output
  - Pass condition: the repo can be opened, understood, and executed without guessing

## Priority order

1. Report contract drift
2. Sensitive data retention
3. Bootstrap and toolchain drift
