# NEXT_EXECUTION_BACKLOG

## Rules

- Only include the next 5 to 10 slices
- Each slice must be small and testable
- Order by risk reduction first
- No vague epics

## Backlog

### 1. Truth hierarchy and doc drift enforcement

- Goal: make the repo explicit about strategic truth versus current implementation truth
- Why now: future changes will drift or hallucinate without a written precedence rule
- Input files: `README.md`, `docs/TRUTH_HIERARCHY.md`, `docs/APP_SCOPE.md`, `docs/BUILD_SHEET.md`
- Output: aligned entry docs and rule surfaces
- Proof: read order and truth precedence agree across the repo
- Blockers: none
- Est. complexity: S

### 2. Proof workflow and template enforcement

- Goal: require proof, scope, security, and docs sync on every change
- Why now: the repo has local proof commands but no automated gate
- Input files: `.github/`, `Makefile`, canonical docs
- Output: CI proof workflow and stronger issue/PR templates
- Proof: workflow definition plus template fields covering proof and open decisions
- Blockers: none
- Est. complexity: S

### 3. Report artifact scrub boundary

- Goal: scrub obvious sensitive strings before report artifacts are written
- Why now: the current core is deterministic but output artifacts can still echo raw sensitive values
- Input files: `src/core/report_generator.py`, `src/scrubber/pii_scrubber.py`, `docs/SECURITY_BASELINE.md`
- Output: explicit artifact scrub boundary and regression tests
- Proof: redaction tests against JSON and Markdown output
- Blockers: none
- Est. complexity: M

### 4. Input contract hardening

- Goal: reject malformed and ambiguous fixture inputs earlier
- Why now: duplicate IDs and invalid parent references are avoidable contract drift
- Input files: `src/core/schemas.py`, `docs/DATA_CONTRACT.md`
- Output: stricter validation and negative-path tests
- Proof: invalid fixtures fail predictably
- Blockers: none
- Est. complexity: M

### 5. Stable report identifiers

- Goal: replace ambiguous report-level element references with stable node references and rule IDs
- Why now: current report evidence can be ambiguous across screens
- Input files: `src/core/report_generator.py`, `src/core/recommendation_engine.py`, `docs/MVP_REPORT_SPEC.md`
- Output: stable `node_ref`, `rule_id`, and recommendation identity behavior
- Proof: golden fixture diff and identifier tests
- Blockers: input contract hardening
- Est. complexity: M

### 6. Hosted persistence contract

- Goal: define the first tenant-aware persistence model
- Why now: this becomes the next risk after the guardrail pass is proven
- Input files: `docs/ARCHITECTURE.md`, `docs/SECURITY_BASELINE.md`
- Output: a concrete hosted-mode data contract
- Proof: a short doc update with explicit entities and trust boundaries
- Blockers: guardrail pass completion
- Est. complexity: M

### 7. Queue and worker boundary

- Goal: define how analysis jobs are enqueued and processed
- Why now: hosted mode needs an execution boundary
- Input files: `src/worker/main.py`, `docs/SECURITY_BASELINE.md`
- Output: a minimal queue and worker contract
- Proof: documented request and lifecycle states
- Blockers: hosted persistence contract
- Est. complexity: M

### 8. Repo connector shell

- Goal: define the first repo metadata extractor
- Why now: future scans need a bridge back to source ownership
- Input files: `src/connectors/repo_connector.py`
- Output: a stub that returns repo shape and metadata
- Proof: stub connector test or smoke check
- Blockers: queue and worker boundary
- Est. complexity: S
