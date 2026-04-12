# Council Review: Quality Playbook v1.3.31 Benchmark Results

**Date:** 2026-04-12
**Version:** 1.3.31
**Repos benchmarked:** 3 (gson, httpx, virtio) — subset run; full 8-repo run to follow
**Runner:** Claude Code (claude) via `run_playbook.sh --claude --model claude-opus-4-6 --parallel --no-seeds --single-pass`
**Result:** [FILL IN after runs complete]

## Context

v1.3.31 is the "council review response" release. It applies fixes for the four most consistent findings across three independent council reviews (Cursor, Copilot/claude-sonnet-4.6, Codex) of the v1.3.30 benchmark results.

### v1.3.31 changes over v1.3.30:

**SKILL.md changes:**
1. **EXPLORATION.md depth requirement** — minimum 60 lines of substantive content (not boilerplate headers), plus a mandatory re-read from disk after writing. Council reviews found EXPLORATION.md was often thin or treated as a formality. The re-read step forces the model to actually use the handoff artifact instead of relying on working memory.
2. **Required TDD summary sub-keys** — `confirmed_open`, `red_failed`, `green_failed` all explicitly listed as mandatory in the summary object. Council reviews found models were omitting `red_failed` and `green_failed` from summaries.
3. **Canonical patch file names** — `BUG-NNN-regression-test.patch` and `BUG-NNN-fix.patch` explicitly documented as the only patterns the gate matches. Council reviews found creative variants (`BUG-001-regression.patch`, `BUG-001-test.patch`) that the gate didn't count.
4. **Actual session date requirement** — The `date` field in sidecar JSON must use the real session date (e.g., `"2026-04-12"`), not the template placeholder `"YYYY-MM-DD"`. Council reviews found models copying the placeholder literally.

**quality_gate.sh changes:**
5. **TDD summary shape validation** — Gate now checks for `red_failed` and `green_failed` in the summary object, not just `confirmed_open`.
6. **Date validation** — Gate rejects `YYYY-MM-DD` placeholders, non-ISO-8601 strings, and future dates.
7. **Cross-run contamination detection** — Gate flags version mismatches between the directory name (e.g., `httpx-1.3.31`) and the `skill_version` in SKILL.md and tdd-results.json. This was added after discovering byte-identical artifacts across what were supposed to be independent runs.

### Changes from prior versions still in effect:
- Self-contained multi-pass execution, no external orchestration (v1.3.30)
- Multi-pass architecture, EXPLORATION.md as Phase 1 handoff artifact (v1.3.29)
- Gate-enforced writeup inline diffs, benchmark 45 (v1.3.28)
- Deep JSON validation, mandatory regression-test patches, upgraded quality_gate.sh (v1.3.27)
- Script-verified closure gate, sidecar JSON validation, canonical UC identifiers (v1.3.26)
- Artifact file-existence gate, benchmark isolation (`--no-seeds`), numeric version sort (v1.3.25)
- Immediate Phase 2a verify.sh gate, mechanical artifact immutability, forbidden probe pattern, verification receipts (v1.3.24)

## Run Results Summary

### Bug Counts

| Repo | Language | Runner | Bugs Found | Heading Format | Fix Patches | Writeup Diffs | Notes |
|------|----------|--------|-----------|----------------|-------------|---------------|-------|
| **gson** | Java | claude (opus-4.6) | [N] | [✓/✗] | [N] | [N/N] | |
| **httpx** | Python | claude (opus-4.6) | [N] | [✓/✗] | [N] | [N/N] | |
| **virtio** | C (kernel) | claude (opus-4.6) | [N] | [✓/✗] | [N] | [N/N] | |

**Total: [N] bugs found across 3 repos, all independently discovered (no seeding).**

### quality_gate.sh Results

| Repo | Runner | Exit Code | FAIL Count | WARN Count | Notes |
|------|--------|-----------|-----------|-----------|-------|
| gson | claude (opus-4.6) | [0/1] | [N] | [N] | |
| httpx | claude (opus-4.6) | [0/1] | [N] | [N] | |
| virtio | claude (opus-4.6) | [0/1] | [N] | [N] | |

### Artifact Completeness

| Repo | Runner | REQS | BUGS | TDD JSON | UC IDs | Auditors | Gate Log | Writeup Diffs | Patches |
|------|--------|------|------|----------|--------|----------|----------|---------------|---------|
| gson | claude (opus-4.6) | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| httpx | claude (opus-4.6) | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| virtio | claude (opus-4.6) | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |

### Specific Findings

[FILL IN: notable per-repo observations, quality_gate.sh output excerpts, new gate checks firing]

### v1.3.31 Gate Changes — Did They Fire?

[FILL IN: For each new gate check, note whether it fired (caught a problem) or passed:
- **TDD summary shape (red_failed, green_failed):** [PASS/FAIL for each repo]
- **Date validation:** [Did any repo have placeholder dates? Future dates?]
- **Cross-run contamination:** [Did the version-mismatch check flag anything?]
]

## Your Review Tasks

### Per-Repo Scorecard

Score each repo against the 45 benchmarks in `references/verification.md`. Use:
- **PASS** — benchmark met
- **FAIL** — benchmark not met (explain)
- **N/A** — not applicable to this repo

### Questions to Answer

1. **Did the v1.3.31 EXPLORATION.md depth requirement work?** Check each repo's `quality/EXPLORATION.md` — is it at least 60 lines of substance? Did the model re-read it from disk before Phase 2 (look for evidence in PROGRESS.md or control_prompts)?

2. **Did the TDD summary shape fix land?** Check `tdd-results.json` in each repo — does the `summary` object contain all five required keys (`total`, `verified`, `confirmed_open`, `red_failed`, `green_failed`)? Compare against v1.3.30 runs where `red_failed`/`green_failed` were often missing.

3. **Did models use canonical patch names?** Check `quality/patches/` in each repo — are they all `BUG-NNN-regression-test.patch` and `BUG-NNN-fix.patch`? Any creative variants that the gate would miss?

4. **Did models use real dates?** Check the `date` field in `tdd-results.json` and `integration-results.json` — is it `2026-04-12` (or today's date), not `YYYY-MM-DD`?

5. **Cross-run contamination.** Did the new gate check flag any version mismatches? Run `quality_gate.sh` on each repo and check the `[Cross-Run Contamination]` section.

6. **Bug discovery comparison to v1.3.30.** Same bugs found? Different bugs? Quality regression or improvement?
   - **gson:** v1.3.30 found [N] bugs. Same set in v1.3.31?
   - **httpx:** v1.3.30 found [N] bugs (WSGI latin-1 variants). Same set?
   - **virtio:** v1.3.30 found [N] bugs (RING_RESET + others). Same set?

7. **Sidecar JSON deep validation.** Are all 3 repos conformant? Any repos still using non-canonical field names or verdict values?

8. **Writeup inline diff gate.** Do all writeups contain `\`\`\`diff` blocks? Any regressions from v1.3.30?

9. **Single-session execution.** Check `control_prompts/` — exactly one prompt file per repo? PROGRESS.md shows sequential phase timestamps?

10. **Recommended changes for v1.3.32 (or v2.0).** Based on the 3-repo results, what changes would you recommend? Prioritize: P0 (blocking v2.0), P1 (important), P2 (nice to have). Specifically: is the contamination problem (copying from prior-run repos instead of clean checkouts) something the gate should detect more aggressively?

## Files to Examine

All artifacts under `repos/<repo>-1.3.31/quality/`. The SKILL.md is at the repo root as `SKILL.md` (or examine `.github/skills/SKILL.md` in any benchmark repo). Benchmark definitions: `references/verification.md` (45 benchmarks).

Key files for spot-checking:
- **Every repo:** `control_prompts/` — verify single prompt file, not multi-pass split
- **Every repo:** `quality/EXPLORATION.md` — verify 60+ lines of substance, re-read evidence
- **Every repo:** `quality/results/quality-gate.log` — check new gate checks (summary shape, dates, contamination)
- **Every repo:** `quality/results/tdd-results.json` — check summary has all 5 keys, date is real
- **Every repo:** `quality/writeups/BUG-*.md` — verify inline diffs present
- **Every repo:** `quality/patches/` — verify canonical naming `BUG-NNN-regression-test.patch`
- **Every repo:** `quality/REQUIREMENTS.md` — grep for `UC-[0-9]` to verify canonical identifiers
- **Every repo:** `quality/BUGS.md` — grep for `^### BUG-` vs `^## BUG-`
