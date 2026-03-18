# PR_WORKFLOW

## Purpose

This file defines the default change workflow for this repository.

The goal is to preserve proof, contract discipline, and doc sync without slowing down a small team.

## Default rule

- All non-emergency changes should land through a pull request.
- Direct pushes to `main` are discouraged once branch protection is enabled.
- The only acceptable reason to bypass the PR path is an urgent fix that cannot wait for normal review and CI.

## Current enforcement status

- PR-first is the active repo policy by convention.
- GitHub branch protection is not currently enforced on this private repository because GitHub returned: `Upgrade to GitHub Pro or make this repository public to enable this feature.`
- Until that platform constraint is removed, treat the workflow in this file as mandatory operating policy even though GitHub cannot enforce every rule automatically.

## Branch model

- `main` is the protected production branch.
- Create short-lived branches from `main`.
- Branch names should describe the change clearly, for example:
  - `feat/report-id-hardening`
  - `fix/scrubber-artifact-redaction`
  - `docs/truth-hierarchy-sync`

## Pull request requirements

- Use the PR template completely.
- State scope and non-scope explicitly.
- Include exact proof commands and exact outputs.
- Update canonical docs and tests in the same PR when behavior, contracts, workflow, or security expectations change.
- Mark unresolved items as `UNKNOWN / NEEDS DECISION`.

## Review rule

- Require one approval before merge.
- For solo work, self-review is acceptable after the `Proof` workflow passes and the PR description is complete.
- If a PR changes report shape, scoring, validation, or security behavior, review the fixture diff and contract docs before merge.

## Required checks

- Required status check: `Proof`
- No merge while `Proof` is failing or pending.

## Merge strategy

- Recommended merge method: squash merge
- Reason: keep `main` readable while preserving detailed discussion in the PR

## Branch protection settings

Configure these settings in GitHub for `main`:

1. Require a pull request before merging: enabled
2. Required approvals: `1`
3. Dismiss stale approvals: disabled for now
4. Require review from Code Owners: enabled after `CODEOWNERS` is present
5. Require status checks to pass before merging: enabled
6. Required status check: `Proof`
7. Require branches to be up to date before merging: enabled
8. Allow force pushes: disabled
9. Allow deletions: disabled
10. Restrict direct pushes: enabled if the repo owner is comfortable with full PR-only flow

## Hotfix exception

- If an emergency direct push is required, open a follow-up PR or issue immediately after the push.
- The follow-up must capture:
  - what was changed
  - why the PR path was bypassed
  - exact proof run after the fix
  - any doc or test debt created by the hotfix

## Repo-specific notes

- The current authoritative CI gate is `.github/workflows/proof.yml`.
- The current canonical templates are:
  - `.github/pull_request_template.md`
  - `.github/ISSUE_TEMPLATE/feature_request.md`
  - `.github/ISSUE_TEMPLATE/bug_report.md`
- `CODEOWNERS` is intentionally lightweight for this repo.
