# Spec Audit Report — Claude Opus 4.6

Date: 2026-04-06
Model: Claude Opus 4.6
Effective council slot: 1/3

## Scope
- Canonical/public docs and the generated quality system for the self-bootstrap run

## Findings

### BUG 1 — README license text contradicts the shipped MIT license
- **Evidence:** `README.md:5,77,87`; `LICENSE.txt:1`

### BUG 2 — README still presents a four-phase flow instead of the tracked six-phase lifecycle
- **Evidence:** `README.md:33,53-59`; `SKILL.md:282-285`

### BUG 3 — Install snippets omit the `LICENSE.txt` copy step
- **Evidence:** `README.md:17-28`; `AGENTS.md:32-42`

### BUG 4 — SKILL frontmatter says six artifacts while the body defines seven
- **Evidence:** `SKILL.md:3,42`

### BUG 5 — README artifact table says the listed files are generated in `quality/`, but the same table includes root-level `AGENTS.md`
- **Evidence:** `README.md:37-47`; `SKILL.md:42-53`
- **Why it matters:** the location guidance is internally inconsistent and sends users to the wrong path for one of the core outputs.

## Improvement notes not promoted as code bugs
- The integration protocol should verify `quality/VERSION_HISTORY.md`, `quality/REFINEMENT_HINTS.md`, and the persisted terminal-gate arithmetic.
- Mid-run incompleteness in `quality/spec_audits/` and `quality/PROGRESS.md` required closure work, not duplicate bug records.
