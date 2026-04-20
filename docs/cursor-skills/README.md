# Contributor skills (reference)

These are optional checklists for agents and humans. They live in-repo under `docs/cursor-skills/` so clones stay self-contained.

If you use Cursor and want them as local “skills”, copy or symlink this directory to `.cursor/skills/` in your clone (that path is gitignored).

## Core skills

1. [scope-guard.md](scope-guard.md) — Use when a request risks adding features outside the current proof slice.
2. [search-first.md](search-first.md) — Use before proposing new dependencies, utilities, abstractions, or platform changes.
3. [proof-pack.md](proof-pack.md) — Use when implementing or validating any execution slice.
4. [docs-drift-sync.md](docs-drift-sync.md) — Use after meaningful implementation changes to keep docs aligned.

## Rule

Do not add more skills unless the product genuinely needs them.
