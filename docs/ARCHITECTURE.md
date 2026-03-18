# ARCHITECTURE

## Rule

This is a thin architecture document. It exists to support the current proof slice, not a fantasy future platform.

## System shape

- Client: CLI first, web shell second
- Backend: Python core library with thin API shell
- Auth: deferred until hosted mode
- Database: deferred until the first real persisted run
- Payments: not in this slice
- AI: not used for deterministic scoring
- Integrations: local fixture input only for the proof slice

## Current architecture decision

Use a single repository with deterministic Python core modules, a thin API shell, a thin agent shell, and a simple web scaffold.

## Request flow

1. User runs the analysis command with a local fixture
2. The CLI loads and validates the input
3. The core normalizer and fingerprint engine derive stable structure
4. The scorer and recommendation engine produce evidence-backed output
5. The report generator writes JSON and Markdown files

## Data model

- `project`: source file and app-level metadata
- `screen`: named view or screen in the source fixture
- `node`: normalized structural element
- `cluster`: repeated structural fingerprint group
- `score`: deterministic metric with evidence
- `recommendation`: evidence-backed action item

## Security baseline

- Secrets stay in environment variables
- Protected actions require auth in hosted mode
- Validation happens before persistence
- Raw sensitive content is not retained by default

## Known unknowns

- Exact hosted auth provider
- Exact queue choice for worker orchestration
- Exact database schema for multi-tenant persistence
- Exact web app navigation structure

## Deferred decisions

- Hosted auth implementation
- Persistent analysis history
- Benchmark corpus ingestion
- Real-time collection modes
