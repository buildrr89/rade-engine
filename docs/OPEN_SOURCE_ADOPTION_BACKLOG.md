# OPEN_SOURCE_ADOPTION_BACKLOG

## Purpose

This backlog turns the GitHub scan into concrete repo work. The goal is to borrow proven patterns that improve RADE's determinism, testability, and developer throughput without adding scope for its own sake.

## Selection rule

- Prefer patterns that reduce risk, not novelty.
- Do not add dependencies unless the current repo cannot solve the need.
- Keep native Swift references as future-only until native mobile returns to scope.

## Completed

### 1. Lock the report contract with pytest-style golden tests

- Status: implemented in [tests/test_cli_contract.py](/Users/restolad/Desktop/RADE/tests/test_cli_contract.py)
- Borrowed pattern: fixtures, golden files, and CLI-bound contract checks
- Result: the deterministic report command now fails on JSON or Markdown drift

### 2. Standardize formatting and linting with Ruff and Black conventions

- Status: implemented with [pyproject.toml](/Users/restolad/Desktop/RADE/pyproject.toml), [Makefile](/Users/restolad/Desktop/RADE/Makefile), and [README.md](/Users/restolad/Desktop/RADE/README.md)
- Borrowed pattern: one lint gate, one formatter, and fast local feedback
- Result: the repo now has explicit lint and format commands for the Python surface

## Now

### 3. Add browser smoke coverage for the web shell

- Status: implemented in [web/scripts/test.mjs](/Users/restolad/Desktop/RADE/web/scripts/test.mjs), [web/package.json](/Users/restolad/Desktop/RADE/web/package.json), and [Makefile](/Users/restolad/Desktop/RADE/Makefile)
- Borrowed pattern: real-browser smoke checks with a reusable route server
- Result: the root route and `/report` route now have deterministic browser coverage

## Later

### 4. Move the web shell toward a component-driven UI stack

- Source signal: `next.js`, `react`, `storybook`, `tailwindcss`, `shadcn-ui`
- Borrow: component isolation, route conventions, accessible primitives, utility-first styling
- Why later: the web UI should have a stable test and lint foundation first
- First slice: define one reusable card or report component and render it in isolation
- Proof: a component inventory that can grow without page-level coupling

### 5. Model tenant-aware hosted persistence on a Supabase-style boundary

- Source signal: `supabase`
- Borrow: Postgres-first data modeling, auth boundaries, row-level security, hosted state
- Why later: the current proof slice is deterministic local analysis, not hosted execution
- First slice: draft project, tenant, analysis-run, and artifact entities plus RLS rules
- Proof: a documented contract that matches the next execution backlog

## Deferred

- `pointfreeco/swift-composable-architecture` is a future reference for any native Swift client. It is not actionable until native mobile returns to scope.
