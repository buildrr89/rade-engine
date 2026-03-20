# REPO CONNECTOR SPEC

## Purpose

This spec codifies the minimal repo metadata stub that backs the initial repo/build connector shell.
It exists purely to keep the repo shape deterministic and traceable while the real connector work remains deferred.

## Output shape

- `repo_name`: the sanitized name of the repository directory.
- `path`: the absolute filesystem path that contains the repo.
- `default_branch`: the branch name discovered from `.git/HEAD` (falls back to `main` when detached or missing).
- `has_git`: boolean flag indicating whether the `.git` directory is present.
- `remote_url`: `git remote get-url origin` if available, otherwise `null`.
- `directories`: sorted list of top-level directories in the repo (hidden directories are skipped).

## Guardrails

- The extractor must remain deterministic: no randomness, no network calls except for the local `git config` lookup, and no reliance on external services.
- Metadata must be derived from files under version control so that proof can re-run the stub on worker nodes without additional configuration.
- The stub exists only until the backed repo/build connector is implemented; downstream code should expect all fields to be readable and to follow the proof slice’s deterministic pattern.

## Proof

- `tests/test_repo_connector.py` is the golden test that verifies every field is populated and that the branch detection logic matches `.git/HEAD`.
