# Launch post drafts

Paste-ready copy for the public alpha announcement. Replace `<pages-url>` with the real GitHub Pages URL once the workflow runs, and `<repo-url>` with the public repo URL.

---

## Hacker News (Show HN)

**Title:** Show HN: RADE – deterministic UI audits with axe-core, score diffs, and shield badges

**Body:**

Hi HN — I built RADE because every UI audit I ran was either a screenshot PDF or an opinionated AI summary I couldn't diff, baseline, or trust.

RADE is a deterministic CLI for UI analysis. You point it at a local JSON fixture or a public URL and get three artifacts from one run: JSON for automation, Markdown for PRs, and a self-contained interactive HTML report. Same input, same output, except for the timestamp — so you can check it in and diff it.

What's in the wedge right now:
- Repeated-structure detection across screens (stable fingerprints, not label matching)
- Accessibility gaps, with optional `--axe` to embed Deque's axe-core WCAG violations in the same report (provenance is explicit, so you can tell heuristics apart from standards-backed findings)
- Modernization / migration risk scored from deterministic rules
- A `diff` command that compares two RADE runs into a byte-stable delta of scores, recommendations, and duplicate clusters
- A GitHub Action that posts PR comments with score deltas and can fail the build on regressions
- Embeddable SVG badges for your README

What RADE explicitly does not claim to be: a hosted SaaS, a redesign bot, or a substitute for human judgment on taste. It is a boring, reviewable, diffable layer underneath all of that.

Install: `pip install rade-engine` (or `uvx rade analyze --url https://example.com`)

Live example report: <pages-url>

Repo: <repo-url>

Looking for honest feedback — especially from agencies doing modernization discovery and accessibility audit teams. Is the axe-core integration enough to replace one of the tools in your current stack, or is something still missing?

---

## Reddit r/webdev

**Title:** I built a deterministic CLI for UI audits — diffable reports, axe-core integration, PR score gates

**Body:**

Most UI audit tools I've used fall into two buckets: "screenshot-first PDF deck" or "one-shot AI summary you can't verify." Neither is diffable or reviewable in a PR.

RADE takes a different shape. It's a Python CLI that accepts a public URL (or a local JSON payload) and emits three artifacts from the same deterministic pipeline:

- `report.json` — machine-readable, with stable identifiers for every finding
- `report.md` — review-friendly for PRs and audit trails
- `report.html` — self-contained interactive page with filters and score bars

Everything runs from inspectable rules, not a model. Same input, same output — so you can baseline it in CI and diff it over time.

The pieces I'm proudest of:

1. **axe-core integration.** `--axe` injects Deque's axe-core engine into the live page during collection and embeds the WCAG violations in the same report with `provenance: "axe-core"`. You see heuristics and standards-backed findings side by side without losing the determinism.

2. **Report diffs.** `rade diff --base-report a.json --head-report b.json` produces a byte-stable delta artifact. Score direction is interpreted correctly (higher reusability good, lower a11y risk good).

3. **GitHub Action.** Drop it into PRs and get a comment with score deltas. Optional `fail-on-regression: true` turns it into a gate.

4. **SVG badges.** `rade badge --metric reusability --svg-output badge.svg` — embed your score in a README.

Install: `pip install rade-engine` or `uvx rade analyze --url https://example.com`

Live example: <pages-url>
Repo: <repo-url>

Honest question for this sub: what's missing before you'd actually drop it in? I'm trying to avoid building anyone's fantasy product.

---

## X / Twitter thread

1/ I kept auditing UIs with tools that were either PDFs or AI summaries. Neither was diffable. So I built a deterministic CLI that emits the same report for the same input, every time. It's called RADE. Public alpha today.

2/ One command turns a public URL into three artifacts: JSON (automation), Markdown (PRs), and a self-contained HTML report. No hosted service. No accounts. No "trust me" scoring.

3/ `--axe` flag injects Deque's axe-core into the live page and embeds the WCAG violations in the same report. Heuristics and standards-backed findings are clearly labeled with provenance.

4/ `rade diff` compares two runs into a byte-stable delta artifact. `rade badge` emits SVG shields for your README. A GitHub Action posts score deltas on PRs and can fail on regression.

5/ Live example: <pages-url>
Install: `pip install rade-engine`
Repo: <repo-url>

Feedback welcome, especially from agencies and a11y teams.

---

## Notes for promotion

- Post to HN on a Tuesday or Wednesday around 08:00 Pacific for best visibility.
- Reply to r/webdev comments within the first hour — Reddit engagement decay is steep.
- Do not repost the same body across platforms verbatim — each variant above is intentionally scoped.
- Avoid all superlatives ("revolutionary", "unparalleled") — the repo itself is positioned against them and readers will notice.
- The live GitHub Pages URL stays fresh automatically because `.github/workflows/deploy-pages.yml` rebuilds the report on every push to `main`.
