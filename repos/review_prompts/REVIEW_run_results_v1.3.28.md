# Council Review: Quality Playbook v1.3.28 Benchmark Results

**Date:** 2026-04-11
**Version:** 1.3.28
**Repos benchmarked:** 8 (virtio, httpx, express, javalin, chi, cobra, gson, serde)
**Runner:** GitHub Copilot (gpt-5.4) via `run_playbook.sh --copilot --parallel --no-seeds`
**Result:** [FILL IN after run completes]

## Context

v1.3.28 is the "writeup inline diff" release. The core change: `quality_gate.sh` now verifies that every `quality/writeups/BUG-NNN.md` contains a ` ```diff ` block. This was added because v1.3.27's virtio run produced 4 writeups with 0 inline diffs despite clear SKILL.md instructions — the model wrote "see patch file" instead of pasting the diff inline.

### v1.3.28 changes over v1.3.27:

1. **Gate-enforced writeup inline diffs** — `quality_gate.sh` checks every writeup for a ` ```diff ` block; FAIL if missing
2. **Strengthened SKILL.md writeup template** — new "Inline diff is gate-enforced" paragraph, explicit instruction not to write "see patch file"
3. **Benchmark 45** — writeup inline fix diff validation
4. **45 total benchmarks** (up from 44)

### Changes from prior versions still in effect:
- Deep JSON validation, mandatory regression-test patches, upgraded quality_gate.sh (v1.3.27)
- Script-verified closure gate, sidecar JSON validation, canonical UC identifiers (v1.3.26)
- Artifact file-existence gate, benchmark isolation (`--no-seeds`), numeric version sort (v1.3.25)
- Immediate Phase 2a verify.sh gate, mechanical artifact immutability, forbidden probe pattern, verification receipts (v1.3.24)

## Run Results Summary

### Bug Counts

| Repo | Language | Bugs Found | Heading Format | Fix Patches | Writeup Diffs | Notes |
|------|----------|-----------|----------------|-------------|---------------|-------|
| **virtio** | C (kernel) | [N] | [✓/✗] | [N] | [N/N] | |
| **httpx** | Python | [N] | [✓/✗] | [N] | [N/N] | |
| **express** | JavaScript | [N] | [✓/✗] | [N] | [N/N] | |
| **javalin** | Kotlin | [N] | [✓/✗] | [N] | [N/N] | |
| **chi** | Go | [N] | [✓/✗] | [N] | [N/N] | |
| **cobra** | Go | [N] | [✓/✗] | [N] | [N/N] | |
| **gson** | Java | [N] | [✓/✗] | [N] | [N/N] | |
| **serde** | Rust | [N] | [✓/✗] | [N] | [N/N] | |

**Total: [N] bugs found across 8 repos, all independently discovered (no seeding).**

### quality_gate.sh Results

| Repo | Exit Code | FAIL Count | WARN Count | Notes |
|------|-----------|-----------|-----------|-------|
| virtio | [0/1] | [N] | [N] | |
| httpx | [0/1] | [N] | [N] | |
| express | [0/1] | [N] | [N] | |
| javalin | [0/1] | [N] | [N] | |
| chi | [0/1] | [N] | [N] | |
| cobra | [0/1] | [N] | [N] | |
| gson | [0/1] | [N] | [N] | |
| serde | [0/1] | [N] | [N] | |

### Artifact Completeness

| Repo | REQS | BUGS | TDD JSON | UC IDs | Auditors | Gate Log | Writeup Diffs | Patches |
|------|------|------|----------|--------|----------|----------|---------------|---------|
| virtio | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| httpx | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| express | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| javalin | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| chi | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| cobra | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| gson | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| serde | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |

**New columns: Writeup Diffs = inline diff count / writeup count, Patches = regression-test + fix patches**

### Specific Findings

[FILL IN: notable per-repo observations, quality_gate.sh output excerpts, etc.]

## Your Review Tasks

### Per-Repo Scorecard

Score each repo against the 45 benchmarks in `references/verification.md`. Use:
- **PASS** — benchmark met
- **FAIL** — benchmark not met (explain)
- **N/A** — not applicable to this repo

Pay special attention to benchmark 45 (writeup inline diffs) and compare against v1.3.27 performance.

### Questions to Answer

1. **Did the writeup inline diff gate work?** v1.3.27 virtio had 4 writeups with 0 inline diffs. v1.3.28 added a `quality_gate.sh` check that FAILs on missing diffs. How many repos now have inline diffs in all writeups? Did the model fix writeups after the gate caught them, or did it write them correctly the first time?

2. **Writeup quality beyond the diff.** Does the writeup follow the numbered section template (1. Summary, 2. Spec reference/Background, 3. Evidence/The code, 4. Reproduction/Observable consequence, 5. Impact/Depth judgment, 6. The fix with diff, 7. References/The test)? Or does it use freeform markdown sections? Is the numbered format important enough to gate-enforce?

3. **Patch generation rate.** v1.3.26 had 4/8 repos with 0 patches. v1.3.27 virtio had 8/8 patches. How does v1.3.28 compare across 8 repos? Did the mandatory regression-test patch gate (FAIL not WARN) close the gap?

4. **Bug discovery comparison to v1.3.27 and v1.3.25.** v1.3.25 found 22 bugs across 8 repos. v1.3.26 found [N]. Key per-repo comparisons:
   - **virtio:** v1.3.27 and v1.3.28 both found 4 bugs including RING_RESET. Stable?
   - **httpx:** v1.3.25 found 3 WSGI latin-1 bugs. Same set?
   - **express:** v1.3.25 found BUG-001 (etag) + BUG-002 (Content-Type false). Both refound?
   - **javalin:** v1.3.25 found BUG-001 (HEAD metadata) + BUG-002 (CORS). Same bugs?

5. **Sidecar JSON deep validation.** v1.3.27 added per-bug field name validation, verdict enum checks, and non-canonical field detection. Are all 8 repos conformant? Any repos still using `bug_id` instead of `id` or non-canonical verdict values?

6. **V2.0 gate assessment.** The v2.0 gate: "a clean run that catches all of the bugs that it previously found." Compare v1.3.28 bug sets against v1.3.25 and v1.3.26. Is the skill converging on a stable bug set? What's still blocking v2.0?

7. **Regression or progress since v1.3.21?** v1.3.21 was the previous high-water mark. v1.3.25 regressed significantly. v1.3.26 recovered structural conformance. v1.3.27 added patches. v1.3.28 added inline diffs. Is the skill back to v1.3.21 quality or better? What metrics are better/worse?

8. **Recommended changes for v1.3.29 (or v2.0).** Based on the 8-repo results, what changes would you recommend? Prioritize: P0 (blocking v2.0), P1 (important), P2 (nice to have). Is the skill ready for v2.0, or does it need more iteration?

## Files to Examine

All artifacts under `repos/<repo>-1.3.28/quality/`. The SKILL.md is at the repo root as `SKILL.md` (or examine `.github/skills/SKILL.md` in any benchmark repo). Benchmark definitions: `references/verification.md` (45 benchmarks).

Key files for spot-checking:
- **Every repo:** `quality/results/quality-gate.log` — did the script run? What did it report? Did the writeup diff check pass?
- **Every repo:** `quality/results/tdd-results.json` — check all 6 required root keys + per-bug fields
- **Every repo:** `quality/writeups/BUG-*.md` — verify inline diffs present AND check section numbering format
- **Every repo:** `quality/patches/` — count regression-test + fix patches vs. bug count
- **Every repo:** `quality/REQUIREMENTS.md` — grep for `UC-[0-9]` to verify canonical identifiers
- **Every repo:** `quality/BUGS.md` — grep for `^### BUG-` vs `^## BUG-`
- `virtio-1.3.28/quality/mechanical/` — mechanical verification path
- Compare any repo's `quality-gate.log` against the actual artifact state — did the model fix issues the script caught, or just write the log without fixing?
