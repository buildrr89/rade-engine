# NEXT_EXECUTION_BACKLOG

## Rules

- Only include the next 5 to 10 slices
- Each slice must be small and testable
- Order by risk reduction first
- No vague epics

## Backlog

### 1. Deterministic core proof

- Goal: make the sample report command work end to end
- Why now: it proves the core contract and report shape
- Input files: `examples/sample_ios_output.json`
- Output: JSON and Markdown modernization reports
- Proof: identical output for repeated runs except timestamp
- Blockers: none once the core modules exist
- Est. complexity: M

### 2. Golden test lock

- Goal: lock the JSON and Markdown report shapes
- Why now: it prevents silent contract drift
- Input files: generated sample report
- Output: golden fixtures
- Proof: comparison tests pass
- Blockers: deterministic report generation
- Est. complexity: S

### 3. Scrubber baseline

- Goal: redact obvious sensitive content before durable persistence
- Why now: it protects the future Project Skeleton layer
- Input files: sample raw text and structured payloads
- Output: scrubbed strings and payloads
- Proof: scrubber regression tests pass
- Blockers: none
- Est. complexity: S

### 4. API shell health route

- Goal: expose a simple service health check
- Why now: it gives the backend shell a visible contract
- Input files: `src/api/app.py`
- Output: `/healthz` response
- Proof: smoke test passes against the app callable
- Blockers: core package structure
- Est. complexity: XS

### 5. Web shell scaffold

- Goal: keep a minimal front-end folder and entry point
- Why now: it reserves the product surface without overbuilding it
- Input files: `web/package.json` and `web/app/*`
- Output: a shell that can be extended into Next.js later
- Proof: package metadata and placeholder app files exist
- Blockers: none
- Est. complexity: XS

### 6. Hosted persistence plan

- Goal: define the first real storage and tenant isolation path
- Why now: the next phase will need durable state
- Input files: security and architecture docs
- Output: a constrained hosted-mode plan
- Proof: updated docs with explicit unknowns and decisions
- Blockers: proof slice completion
- Est. complexity: M
