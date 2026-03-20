# RADE Canonical Execution Spec

Version: `1.0`
Status: `Canonical source of truth`
Date: `2026-03-18`

If any older document conflicts with this file, this file wins.

Interpretation rule:

- `RADE.md` is the strategic product north star.
- Current implementation truth and precedence live in `docs/TRUTH_HIERARCHY.md`.
- Future-state sections below are strategic unless the current-slice docs and source code prove they are implemented now.

---

## 1. Mission

Build `RADE`, a user-facing software intelligence app that helps teams scan their own apps and projects, understand how they are built today, and receive evidence-backed recommendations for better UI, UX, accessibility, and user flows.

Build `Project Skeleton`, the internal acquisition and normalization engine that powers RADE and compounds into a long-term UI/UX knowledge graph.

Short version:

- `RADE` = revenue wedge
- `Project Skeleton` = data moat

---

## 2. Product Definition

### 2.1 What RADE is

RADE is a standards-aware, benchmark-aware, project-aware recommendation engine for software interfaces.

The product must:

- scan authorized software interfaces
- map screens, components, slab layers, and flows
- diagnose structural, accessibility, and UX issues
- recommend better patterns with explicit evidence
- prioritize what to fix first

### 2.2 What RADE is not

Do not build RADE as:

- a generic “AI design taste” app
- a code generation platform first
- a mobile consumer app first
- a Kubernetes-first system
- a broad enterprise platform before product-market proof
- an adversarial scraping product

### 2.3 Core user promise

Connect your product. Let RADE understand its structure and flows. Get a prioritized set of recommendations for what to improve and why.

---

## 3. Product Lines

### 3.1 RADE

User-facing product.

Core jobs:

- project onboarding
- scan orchestration
- findings review
- recommendation review
- report generation
- benchmark comparison
- improvement tracking

### 3.2 Project Skeleton

Internal codename for the long-term moat layer.

Core jobs:

- collect observable interface data
- scrub sensitive data at the edge
- normalize into slab layers and interface graphs
- fingerprint and deduplicate structures
- persist benchmark-quality structural data

### 3.3 Long-term destination

Over time, RADE should evolve into:

1. assessment and recommendation product
2. interface benchmark system
3. continuous modernization platform
4. UI/UX knowledge graph business

---

## 4. Customer and Use Cases

### 4.1 Primary customer

- product teams
- design teams
- mobile engineering teams
- modernization programs
- enterprise software teams with legacy UI debt

### 4.2 Primary use cases

- understand current screen and flow structure
- identify duplicated components and design-system drift
- detect accessibility and semantics gaps
- diagnose navigation and flow friction
- prioritize modernization work
- benchmark a product against known patterns

### 4.3 First user story

A customer connects an app or project, runs a scan, and receives:

- project summary
- screen inventory
- flow inventory
- findings
- prioritized recommendations
- downloadable report

---

## 5. Product Surface

Strategic / not current implementation.

Current repo reality:

- thin web shell
- local CLI proof path
- thin API shell
- no hosted onboarding, auth, queue, tenant model, or persisted analysis history yet

### 5.1 Required surfaces

- `web app`
- `local agent or CI agent`
- `API`
- `analysis worker`

### 5.2 Web app responsibilities

- auth
- org and project management
- scan setup
- scan history
- recommendation dashboard
- findings explorer
- before/after comparisons
- report downloads

### 5.3 Agent responsibilities

- connect to repos and build artifacts
- run local or CI scans
- invoke simulator or emulator scans
- upload authorized payloads
- return logs and artifacts

### 5.4 API responsibilities

- accept scans
- validate payloads
- enqueue jobs
- expose run status
- expose reports and recommendations

### 5.5 Worker responsibilities

- normalize
- layer
- fingerprint
- deduplicate
- score
- recommend
- persist artifacts

---

## 6. Supported Scan Modes

Build scan modes in this order.

### 6.1 Mode A: JSON upload scan

Purpose:

- fastest v1 path
- deterministic fixtures
- customer-provided exports

Status:

- mandatory for v1

### 6.2 Mode B: Repo and build scan

Purpose:

- understand project structure
- connect runtime findings back to code ownership
- inspect component usage and route structure

Inputs may include:

- repository metadata
- screen modules
- route definitions
- design-system components
- build artifacts

Status:

- mandatory for v2

### 6.3 Mode C: Simulator or emulator runtime scan

Purpose:

- capture real flows
- read accessibility trees
- identify runtime-only semantics and friction

Status:

- mandatory for Project Skeleton pilot

### 6.4 Accessibility hook scanning

This is the preferred runtime collection method.

Primary sources:

- Android `AccessibilityNodeInfo` / accessibility services
- iOS XCTest accessibility / `AXElement` tree
- web DOM plus accessibility tree where available

Principle:

- do not parse pixels first when the accessibility tree already exposes structure, roles, labels, and hierarchy
- use visual capture only as a fallback or corroborating signal

Why this matters:

- the operating system already knows containment, actions, labels, and semantics
- the collector should observe the interface as a functional hierarchy, not as a pixel grid

### 6.5 Virtual device farm

Project Skeleton may eventually use controlled Android and iOS emulators or simulators to scale authorized scans.

Rule:

- device-farm execution is an orchestration layer
- the product is the captured functional graph and recommendations
- scale does not substitute for redaction quality or product clarity

### 6.6 Mode D: Public web interface scan

Purpose:

- benchmark corpus acquisition
- public pattern discovery
- public interface comparison

Status:

- optional after v1

Rule:

- project-owned scans are the highest-trust signal for user-specific recommendations
- benchmark scans enrich the corpus but never override direct project evidence

---

## 7. Authorized Acquisition Boundary

This is non-negotiable.

### 7.1 Allowed acquisition modes

1. authorized enterprise collection
2. public unauthenticated web interface crawling
3. opt-in partner ingestion

### 7.2 Authorized enterprise collection

Allowed examples:

- customer-owned apps
- customer-provided builds
- customer-consented devices
- internal QA, staging, and production replicas where the customer has authority
- simulators and emulators under customer control

### 7.3 Public web interface crawling

Allowed only when all are true:

- public surface
- unauthenticated surface
- no login-wall bypass
- no fake accounts
- no access-control circumvention
- no stealth collection as the default operating model
- robots, rate limits, takedowns, and restrictions are respected

### 7.4 Opt-in partner ingestion

Allowed forms:

- SDK
- signed export
- secure upload
- connector integration

### 7.5 Never do

- no credential sharing
- no fake user identities
- no anti-bot evasion as a default strategy
- no collection from private user accounts without authority
- no persistence of sensitive raw user content when structural data is enough

### 7.6 hiQ and CFAA framing

Use hiQ as a narrow domain-logic reference, not as a blanket permission slip.

Current working interpretation:

- public-facing data collection has stronger CFAA footing than gated access
- access-control bypass, credential sharing, fake accounts, and anti-bot circumvention materially raise risk
- privacy law, contract law, platform terms, and anti-circumvention law still apply

Do not write product copy that says “hiQ makes scraping legal.” That is too broad and not defensible.

---

## 8. Recommendation Philosophy

RADE must not output a generic “ultimate UI/UX” based on taste.

RADE must output a best-fit recommendation based on four signals:

1. official standards
2. benchmark corpus
3. project graph
4. business context

### 8.1 Recommendation ranking order

1. standards violations
2. high-confidence flow friction
3. component and consistency problems
4. migration sequencing opportunities
5. lower-confidence benchmark suggestions
6. cosmetic or aesthetic suggestions

### 8.2 Hard rule

- standards-backed recommendations outrank corpus-only recommendations
- corpus-only recommendations must never be presented as official standards

---

## 9. Official Standards Pack

The standards pack is a versioned dependency of the recommendation engine.

### 9.1 Required baseline sources

- Apple Human Interface Guidelines
- Apple iOS design guidance
- Android Material 3 guidance
- Android accessibility guidance
- Android semantics guidance
- WCAG 2.2

### 9.2 Baseline source URLs

- `https://developer.apple.com/design/human-interface-guidelines/`
- `https://developer.apple.com/design/human-interface-guidelines/designing-for-ios`
- `https://developer.android.com/develop/ui/compose/designsystems/material3`
- `https://developer.android.com/develop/ui/compose/accessibility`
- `https://developer.android.com/develop/ui/compose/accessibility/semantics`
- `https://www.w3.org/TR/WCAG22/`

### 9.3 Standards pack rules

- standards pack must be versioned
- standards pack must be refreshed quarterly
- every recommendation run must record the standards pack version used

---

## 10. Core Data Model

### 10.1 Normalized slab node

Every normalized node must support:

- `screen_id`
- `screen_name`
- `element_id`
- `parent_id`
- `element_type`
- `role`
- `slab_layer`
- `label`
- `accessibility_identifier`
- `interactive`
- `visible`
- `bounds`
- `hierarchy_depth`
- `child_count`
- `text_present`
- `traits`
- `platform`
- `source`
- `structural_fingerprint`

### 10.2 Slab construction model

RADE must reason about interfaces using five slab layers:

1. `01. OS Site (The Land)`
2. `02. Root (The Slab)`
3. `03. Containers (The Frame)`
4. `04. Links/Events (Wires & Plumbing)`
5. `05. Assets (The Decor)`

Definitions:

- `01. OS Site (The Land)`: screen footprint, primary regions, shell placement
- `02. Root (The Slab)`: containers, stacks, lists, grids, cards, hierarchy skeleton
- `03. Containers (The Frame)`: buttons, inputs, navigation, toggles, interaction controls
- `04. Links/Events (Wires & Plumbing)`: content, labels, helper text, media, semantic user-facing elements
- `05. Assets (The Decor)`: visual styling, theme, tokens, cosmetic treatment

Rule:

- layers `01. OS Site (The Land)`, `02. Root (The Slab)`, `03. Containers (The Frame)`, and `04. Links/Events (Wires & Plumbing)` are first-class for deterministic analysis
- layer `05. Assets (The Decor)` is secondary in v1 and must not dominate scoring

### 10.3 Interface graph entities

Initial entities:

- `organization`
- `project`
- `app`
- `platform`
- `build`
- `analysis_run`
- `screen`
- `screen_state`
- `slab_node`
- `component_cluster`
- `control`
- `navigation_edge`
- `flow_edge`
- `report_artifact`
- `recommendation`
- `scrub_event`

Rule:

- do not introduce a separate graph database in v1
- use Postgres tables and adjacency tables first

---

## 11. Recommendation Contract

Every recommendation must include:

- `recommendation_id`
- `category`
- `scope`
- `target`
- `priority`
- `confidence`
- `problem_statement`
- `recommended_change`
- `reasoning`
- `evidence`
- `standards_refs`
- `benchmark_refs`
- `expected_impact`
- `implementation_effort`
- `affected_screens`
- `affected_components`

Recommendation categories:

- `layout`
- `navigation`
- `accessibility`
- `interaction`
- `content_hierarchy`
- `component_reuse`
- `design_system_consistency`
- `migration_sequencing`

Hard rule:

- every recommendation must be evidence-backed
- every recommendation must show whether it is standards-backed, benchmark-backed, or both

---

## 12. Deterministic Core Rules

The following systems must be deterministic:

- normalization
- slab layering
- fingerprinting
- deduplication
- scoring
- evidence extraction

LLMs may be used later for:

- narrative rewriting
- report summarization
- explanatory prose

LLMs must not decide:

- scores
- rule violations
- primary evidence
- structural fingerprints

---

## 13. Fingerprinting Rules

Fingerprint structure, not transient content.

Include:

- element type
- slab layer
- hierarchy shape
- child structure
- interaction traits
- stable layout relationships

Exclude:

- literal text
- timestamps
- colors
- session identifiers
- transient tokens
- absolute pixel values when relative structure is sufficient

---

## 14. Scoring Model

Required scores:

- `complexity`
- `reusability`
- `accessibility_risk`
- `migration_risk`

Score rules:

- deterministic
- explainable
- versioned
- test-locked

Every score must expose evidence fields.

No score change ships unless:

1. tests are updated
2. scoring doc is updated
3. sample report diff is reviewed

---

## 15. Edge Scrubber

Project Skeleton only works safely if redaction happens before durable persistence.

### 15.1 Default rule

- raw collector output must pass through the edge scrubber before durable storage

### 15.2 Minimum scrubber responsibilities

- detect and remove names
- detect and remove email addresses
- detect and remove phone numbers
- detect and remove postal addresses
- detect and remove payment details
- detect and remove personal identifiers
- detect and remove secrets, tokens, and session identifiers
- detect and remove free-form user text unless structurally required

Implementation guidance:

- use deterministic regex rules first
- use NER or classification only as a second pass
- preserve structure while dropping literal sensitive strings
- keep a scrub log so redaction coverage is measurable

Required target:

- define redaction coverage as a measurable metric
- do not promise 100 percent PII removal in marketing copy unless it is empirically validated on the exact data class

### 15.3 Storage rules

- persist normalized structural data by default
- persist raw captures only when strictly needed
- encrypt any retained raw captures
- apply short retention to retained raw captures
- support deletion-by-default for sensitive customers

---

## 16. System Architecture

Strategic / not current implementation.

### 16.1 Required services

Build exactly these services first:

1. `web`
2. `api`
3. `worker`
4. `agent`
5. `postgres`
6. `redis`
7. `object storage`

This is the intended hosted shape, not a claim that these services are active in the current repo.

### 16.2 Technology choices

Default stack:

- `web`: Next.js + TypeScript
- `api`: FastAPI
- `worker`: Python background worker
- `agent`: Python CLI and CI-compatible runtime
- `database`: Postgres
- `auth`: Supabase Auth or equivalent managed auth
- `storage`: S3-compatible storage or Supabase Storage
- `queue/cache`: Redis

These are target technology choices for hosted mode, not proof of current runtime adoption.

### 16.3 Architecture rules

- API remains thin
- worker does the heavy analysis
- agent performs local and CI collection
- Postgres stores metadata and graph relations
- object storage stores artifacts and optional raw captures
- do not build separate microservices for every subsystem

### 16.4 User-facing flow

```text
User
  -> RADE web app
  -> project setup
  -> choose scan mode
  -> upload or run agent
  -> analysis run created
  -> worker processes run
  -> findings and recommendations generated
  -> report and dashboard displayed
```

### 16.5 Long-term Project Skeleton flow

```text
Controlled device / simulator / emulator / public web surface
  -> collector
  -> edge scrubber
  -> normalizer
  -> slab layering
  -> fingerprinting
  -> deduplication
  -> interface graph persistence
  -> recommendation and benchmark surfaces
```

---

## 17. Repo Layout

Use this exact structure.

```text
rade/
├── README.md
├── RADE.md
├── RADE2.0.md
├── pyproject.toml
├── uv.lock
├── Makefile
├── .env.example
├── examples/
│   ├── sample_ios_output.json
│   └── sample_modernization_report.md
├── docs/
│   ├── TRUTH_HIERARCHY.md
│   ├── DECISIONS.md
│   ├── APP_SCOPE.md
│   ├── HARD_RISKS.md
│   ├── ARCHITECTURE.md
│   ├── BUILD_SHEET.md
│   ├── NEXT_EXECUTION_BACKLOG.md
│   ├── DATA_CONTRACT.md
│   ├── MVP_REPORT_SPEC.md
│   ├── SCORING_MODEL.md
│   ├── RECOMMENDATION_ENGINE.md
│   ├── STANDARDS_PACK.md
│   ├── SECURITY_BASELINE.md
│   └── OPEN_SOURCE_ADOPTION_BACKLOG.md
├── src/
│   ├── core/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── normalizer.py
│   │   ├── layering.py
│   │   ├── fingerprint.py
│   │   ├── deduplicator.py
│   │   ├── scoring.py
│   │   ├── impact_engine.py
│   │   ├── roadmap_generator.py
│   │   ├── recommendation_engine.py
│   │   ├── report_generator.py
│   │   └── cli.py
│   ├── connectors/
│   │   ├── repo_connector.py
│   │   ├── build_connector.py
│   │   └── standards_pack.py
│   ├── collectors/
│   │   ├── json_ingest.py
│   │   ├── xcuitest_adapter.py
│   │   ├── android_accessibility_adapter.py
│   │   └── web_dom_adapter.py
│   ├── scrubber/
│   │   ├── pii_scrubber.py
│   │   └── rules.py
│   ├── api/
│   │   └── app.py
│   └── worker/
│       └── main.py
├── agent/
│   ├── cli.py
│   ├── runner/
│   ├── connectors/
│   └── collectors/
├── web/
│   ├── app/            # dormant scaffold until a real Next.js runtime is adopted
│   ├── components/
│   ├── lib/
│   ├── scripts/
│   └── package.json
├── tests/
│   ├── fixtures/
│   ├── golden/
│   ├── helpers.py
│   ├── runner.py
│   ├── test_normalizer.py
│   ├── test_layering.py
│   ├── test_fingerprint.py
│   ├── test_deduplicator.py
│   ├── test_scoring.py
│   ├── test_impact_engine.py
│   ├── test_roadmap_generator.py
│   ├── test_recommendation_engine.py
│   ├── test_report_generator.py
│   ├── test_api_smoke.py
│   └── test_scrubber.py
└── output/
```

---

## 18. Canonical Commands

Use these commands as the expected developer interface.

### 18.1 Bootstrap

```bash
uv sync --dev
pnpm --dir web install
```

### 18.2 Run tests

```bash
./rade-proof
pnpm --dir web test
```

### 18.3 Run API

```bash
./rade-devserver src.api.app:app --reload
```

### 18.4 Run worker

```bash
uv run python -m src.worker.main
```

### 18.5 Run web app

```bash
pnpm --dir web dev
```

### 18.6 Run agent

```bash
uv run python -m agent.cli scan
```

### 18.7 Generate sample report

```bash
uv run python -m src.core.cli analyze \
  --input examples/sample_ios_output.json \
  --app-id com.example.legacyapp \
  --json-output output/modernization_report.json \
  --md-output output/modernization_report.md
```

---

## 19. Build Phases

Strategic / not current execution order.

Use `docs/BUILD_SHEET.md` and `docs/NEXT_EXECUTION_BACKLOG.md` for the actual current sequence.

Build in this exact order.

### Phase 0: Foundation Reset

Deliver:

- pin Python version everywhere
- use one dependency source of truth
- make every command environment-pinned
- remove non-v1 heavy dependencies from default path
- fix legacy test and import drift

Acceptance criteria:

- clean machine bootstrap works
- sample report generation works from pinned environment
- CI, local, and container runtime use the same Python line

### Phase 1: Contracts and Fixtures

Deliver:

- `DATA_CONTRACT.md`
- `MVP_REPORT_SPEC.md`
- `SCORING_MODEL.md`
- `RECOMMENDATION_ENGINE.md`
- `STANDARDS_PACK.md`
- stable fixtures

Acceptance criteria:

- malformed inputs fail predictably
- report schema is locked
- recommendation contract is locked

### Phase 2: Deterministic Core

Deliver:

- normalizer
- layering engine
- fingerprint engine
- deduplicator
- scoring engine

Acceptance criteria:

- same input yields same output except `generated_at`
- golden tests pass
- score evidence is present

### Phase 3: Recommendation Engine v1

Deliver:

- standards-backed recommendation engine
- benchmark hook points
- impact engine
- roadmap generator

Acceptance criteria:

- recommendations are evidence-backed
- recommendations show standards and benchmark provenance
- top issues are prioritized correctly

### Phase 4: User-Facing RADE App v1

Deliver:

- auth
- project setup
- scan creation
- findings dashboard
- recommendation dashboard
- report downloads

Acceptance criteria:

- user can onboard a project and run a scan
- user can see top findings and recommendations within 90 seconds of a completed sample run

### Phase 5: Agent v1

Deliver:

- JSON upload mode
- local CLI mode
- CI mode
- initial repo/build connector shell

Acceptance criteria:

- local and CI scans create valid runs
- artifacts and logs are attached to runs

### Phase 6: Hosted MVP Hardening

Deliver:

- job queue
- worker orchestration
- object storage
- retention controls
- structured logging
- metrics

Acceptance criteria:

- multiple concurrent jobs run safely
- artifact retrieval is reliable
- retention and deletion behavior is enforced

### Phase 7: Customer Pilot

Deliver:

- three pilot scans
- recommendation walkthrough flow
- benchmark comparison view
- customer-ready report pack

Acceptance criteria:

- one real customer can use the product end to end
- recommendation quality is strong enough for a live review

### Phase 8: Project Skeleton Pilot

Deliver:

- one controlled iOS runtime collector
- one controlled Android runtime collector
- one public web interface collector
- edge scrubber metrics
- graph persistence for screens and flow edges

Acceptance criteria:

- one authorized app is captured into reusable graph form
- raw sensitive content is not retained by default
- repeated structures can be compared across runs and apps

### Phase 9: Portfolio SaaS

Deliver:

- benchmark history
- recommendation history
- improvement tracking
- multi-project dashboards

Acceptance criteria:

- one customer can track changes over time across multiple apps or teams

---

## 20. Testing Gates

### 20.1 Required tests

- normalization tests
- layering tests
- fingerprint stability tests
- deduplication tests
- scoring tests
- recommendation tests
- report tests
- API smoke tests
- scrubber tests

### 20.2 Golden tests

Lock:

- JSON report shape
- Markdown report shape
- recommendation object shape
- sample fixture scores
- sample fixture recommendations

### 20.3 Security tests

Minimum required:

- secret scanning
- dependency scanning
- static security scanning
- scrubber regression tests
- policy validation for deterministic core

---

## 21. Observability and Performance

### 21.1 Required observability

- structured logs
- request IDs
- run IDs
- job duration metrics
- failure counts by stage
- artifact generation success rate
- scrubber redaction counters

### 21.2 Performance targets

- scan creation response under `500ms`
- small sample report generation under `5s`
- medium assessment run under `60s`
- benchmark query under `2s` for cached common views

---

## 22. Security and Compliance Baseline

### 22.1 Required controls

- auth for hosted mode
- tenant isolation
- encryption in transit
- encryption at rest
- file and payload validation
- audit logging
- short raw data retention
- secure artifact access
- secrets manager in production

### 22.2 Platform policy constraint

Treat Android accessibility policy and Apple platform policy as product design constraints from day one.

Rule:

- deep collectors are more realistic as enterprise tooling, controlled device-farm software, partner-operated agents, or internal software than as a consumer mobile app

---

## 23. Monetization Path

### Step 1

Sell:

- single-project assessment
- recommendation review
- modernization workshop

### Step 2

Sell:

- recurring portfolio subscription
- benchmark tracking
- recommendation tracking
- governance and remediation tracking

### Step 3

Sell:

- continuous modernization platform
- flow intelligence
- design-system intelligence
- product optimization recommendations

---

## 24. Success Metrics

Track these from the start:

- scans started
- scans completed
- time to first recommendation
- recommendation acceptance rate
- recommendation implementation rate
- repeat scan rate
- benchmark comparison usage
- raw data retained rate
- scrubber redaction coverage

---

## 25. Never Do Rules

These are hard bans.

- do not build a native mobile app first
- do not start with Kubernetes
- do not use LLMs for deterministic scoring
- do not retain raw sensitive data by default
- do not depend on pixel-only analysis when structure is available
- do not build a separate graph database first
- do not expand into Android, web, and iOS collectors simultaneously before the core is stable
- do not overclaim hidden business-logic reverse engineering
- do not collapse official standards and benchmark heuristics into one opaque score
- do not ship collector behavior that relies on fake accounts, login bypass, or anti-bot evasion

---

## 26. Strategic Next Actions

For the current execution order and next smallest action, use:

- `docs/BUILD_SHEET.md`
- `docs/NEXT_EXECUTION_BACKLOG.md`
