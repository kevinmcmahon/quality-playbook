# Council Review: Quality Playbook v1.3.30 Benchmark Results

**Date:** 2026-04-12
**Version:** 1.3.30
**Repos benchmarked:** 8 (virtio, httpx, express, javalin, chi, cobra, gson, serde)
**Runners:**
- **Primary (8 repos):** Claude Code (claude) via `run_playbook.sh --claude --parallel --no-seeds --single-pass`
- **Comparison (virtio only):** GitHub Copilot (opus-4.6) via `run_playbook.sh --copilot --model opus-4.6 --no-seeds --single-pass virtio`
**Result:** [FILL IN after runs complete]

## Context

v1.3.30 is the "self-contained multi-pass" release. The core change: the multi-pass execution section in SKILL.md now explicitly states that the skill handles all phases internally in a single session, using files on disk as context bridges between phases. No external shell scripts, no separate `claude -p` invocations, no external orchestration.

Previously (v1.3.29), the multi-pass section was ambiguous enough that agents would create external runner scripts to launch separate sessions for each pass. v1.3.30 closes this by making the "write then read" pattern explicit: finish a phase, write findings to disk, read them back for the next phase — all within one session.

This is the first benchmark run using `--single-pass` mode, where the model receives one prompt and the skill's own instructions guide it through all phases. The copilot comparison run on virtio tests whether a different runner (gh copilot with opus-4.6) handles the self-contained multi-pass pattern differently.

### v1.3.30 changes over v1.3.29:

1. **Self-contained multi-pass execution** — SKILL.md now explicitly forbids external orchestration scripts and describes the "write then read" cycle at phase boundaries
2. **Documented handoff files** — EXPLORATION.md, PROGRESS.md, and generated artifacts are listed as the specific context bridges between phases
3. **No new benchmarks** — 45 total benchmarks (unchanged from v1.3.28)

### Changes from prior versions still in effect:
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
| **virtio** | C (kernel) | claude | [N] | [✓/✗] | [N] | [N/N] | |
| **virtio** | C (kernel) | copilot (opus-4.6) | [N] | [✓/✗] | [N] | [N/N] | comparison run |
| **httpx** | Python | claude | [N] | [✓/✗] | [N] | [N/N] | |
| **express** | JavaScript | claude | [N] | [✓/✗] | [N] | [N/N] | |
| **javalin** | Kotlin | claude | [N] | [✓/✗] | [N] | [N/N] | |
| **chi** | Go | claude | [N] | [✓/✗] | [N] | [N/N] | |
| **cobra** | Go | claude | [N] | [✓/✗] | [N] | [N/N] | |
| **gson** | Java | claude | [N] | [✓/✗] | [N] | [N/N] | |
| **serde** | Rust | claude | [N] | [✓/✗] | [N] | [N/N] | |

**Total: [N] bugs found across 8 repos (claude), [N] bugs on virtio (copilot comparison), all independently discovered (no seeding).**

### quality_gate.sh Results

| Repo | Runner | Exit Code | FAIL Count | WARN Count | Notes |
|------|--------|-----------|-----------|-----------|-------|
| virtio | claude | [0/1] | [N] | [N] | |
| virtio | copilot | [0/1] | [N] | [N] | comparison |
| httpx | claude | [0/1] | [N] | [N] | |
| express | claude | [0/1] | [N] | [N] | |
| javalin | claude | [0/1] | [N] | [N] | |
| chi | claude | [0/1] | [N] | [N] | |
| cobra | claude | [0/1] | [N] | [N] | |
| gson | claude | [0/1] | [N] | [N] | |
| serde | claude | [0/1] | [N] | [N] | |

### Artifact Completeness

| Repo | Runner | REQS | BUGS | TDD JSON | UC IDs | Auditors | Gate Log | Writeup Diffs | Patches |
|------|--------|------|------|----------|--------|----------|----------|---------------|---------|
| virtio | claude | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| virtio | copilot | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| httpx | claude | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| express | claude | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| javalin | claude | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| chi | claude | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| cobra | claude | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| gson | claude | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |
| serde | claude | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [N/N] | [N reg + N fix] |

### Specific Findings

[FILL IN: notable per-repo observations, quality_gate.sh output excerpts, etc.]

### Virtio Runner Comparison

[FILL IN: side-by-side comparison of claude vs copilot (opus-4.6) on virtio. Same bugs? Different bugs? Different artifact quality? Did both handle the self-contained multi-pass pattern correctly?]

## Your Review Tasks

### Per-Repo Scorecard

Score each repo against the 45 benchmarks in `references/verification.md`. Use:
- **PASS** — benchmark met
- **FAIL** — benchmark not met (explain)
- **N/A** — not applicable to this repo

For the virtio copilot comparison, score separately and note differences.

### Questions to Answer

1. **Did the model execute all phases in a single session?** This is the core v1.3.30 question. Check `control_prompts/` for each repo — there should be exactly ONE prompt file (the single-pass prompt), not four separate pass files. Check EXPLORATION.md — did the model write it and then read it back, or did it skip the file-based handoff? Look for evidence in PROGRESS.md timestamps that all phases ran sequentially in one session.

2. **EXPLORATION.md quality.** In v1.3.29's external multi-pass runs, EXPLORATION.md was written by a dedicated exploration pass. Now the model writes it mid-session and reads it back. Is the EXPLORATION.md as thorough (domain ID, architecture map, REQ-NNN, UC-NN) as the externally-orchestrated v1.3.29 runs? Or did the model treat it as a formality and keep context in memory instead?

3. **Copilot vs Claude on virtio.** Both runners got the same SKILL.md with the same self-contained multi-pass instructions. Compare:
   - Did both produce EXPLORATION.md?
   - Same bugs found? Same bug quality?
   - Same artifact conformance (gate results)?
   - Any runner-specific behaviors (e.g., copilot splitting into multiple sessions despite instructions)?

4. **Did the writeup inline diff gate continue to work?** v1.3.28 introduced this gate. Confirm it still works in v1.3.30 across all 8 repos + the copilot comparison.

5. **Patch generation rate.** v1.3.27 virtio had 8/8 patches. How does v1.3.30 compare across 8 repos?

6. **Bug discovery comparison to v1.3.28 and v1.3.25.** v1.3.25 found 22 bugs across 8 repos. Key per-repo comparisons:
   - **virtio:** v1.3.27 and v1.3.28 both found 4 bugs including RING_RESET. Stable in v1.3.30?
   - **httpx:** v1.3.25 found 3 WSGI latin-1 bugs. Same set?
   - **express:** v1.3.25 found BUG-001 (etag) + BUG-002 (Content-Type false). Both refound?
   - **javalin:** v1.3.25 found BUG-001 (HEAD metadata) + BUG-002 (CORS). Same bugs?

7. **Sidecar JSON deep validation.** Are all 8 repos + copilot comparison conformant? Any repos still using non-canonical field names or verdict values?

8. **V2.0 gate assessment.** The v2.0 gate: "a clean run that catches all of the bugs that it previously found." Is the skill converging on a stable bug set? What's still blocking v2.0?

9. **Single-pass vs multi-pass quality.** Compare v1.3.30 (single-pass, skill-internal phases) against v1.3.29 (external multi-pass runner) if v1.3.29 results are available. Is there a measurable quality difference from letting the skill manage its own phase transitions?

10. **Recommended changes for v1.3.31 (or v2.0).** Based on the 8-repo + comparison results, what changes would you recommend? Prioritize: P0 (blocking v2.0), P1 (important), P2 (nice to have).

## Files to Examine

All artifacts under `repos/<repo>-1.3.30/quality/`. The SKILL.md is at the repo root as `SKILL.md` (or examine `.github/skills/SKILL.md` in any benchmark repo). Benchmark definitions: `references/verification.md` (45 benchmarks).

Key files for spot-checking:
- **Every repo:** `control_prompts/` — verify single prompt file, not multi-pass split
- **Every repo:** `quality/EXPLORATION.md` — was it written? Is it thorough?
- **Every repo:** `quality/results/quality-gate.log` — did the script run? What did it report?
- **Every repo:** `quality/results/tdd-results.json` — check all 6 required root keys + per-bug fields
- **Every repo:** `quality/writeups/BUG-*.md` — verify inline diffs present AND check section numbering format
- **Every repo:** `quality/patches/` — count regression-test + fix patches vs. bug count
- **Every repo:** `quality/REQUIREMENTS.md` — grep for `UC-[0-9]` to verify canonical identifiers
- **Every repo:** `quality/BUGS.md` — grep for `^### BUG-` vs `^## BUG-`
- `virtio-1.3.30/quality/mechanical/` — mechanical verification path (claude run)
- **Copilot comparison:** `virtio-1.3.30-copilot/quality/` — same checks as above, compare against claude run
- Compare any repo's `quality-gate.log` against the actual artifact state — did the model fix issues the script caught, or just write the log without fixing?
