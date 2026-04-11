# Council Review: Quality Playbook v1.3.26 Benchmark Results

**Date:** 2026-04-11
**Version:** 1.3.26
**Repos benchmarked:** 8 (virtio, httpx, express, javalin, chi, cobra, gson, serde)
**Runner:** GitHub Copilot (gpt-5.4) via `run_playbook.sh --copilot --parallel --no-seeds`
**Result:** [FILL IN after run completes]

## Context

v1.3.26 is the "script-verified closure" release. The core change: instead of relying on model self-attestation for artifact conformance, a `quality_gate.sh` script runs as the mandatory final step of Phase 2d and mechanically checks file existence, heading format, sidecar JSON schema, use case identifiers, terminal gate section, version stamps, and writeup completeness. The model must fix any FAIL results before marking Phase 2d complete.

### v1.3.26 changes over v1.3.25:

1. **Script-verified closure gate** — `quality_gate.sh` must be run as final Phase 2d step; output saved to `quality/results/quality-gate.log`; Phase 2d cannot complete until exit 0
2. **Sidecar JSON post-write validation** — mandatory reopen-and-verify step after writing `tdd-results.json` / `integration-results.json`; all required keys enumerated explicitly (benchmark 41)
3. **Canonical use case identifiers** — REQUIREMENTS.md must use `UC-01`, `UC-02` format (benchmark 43)
4. **Run prompt reinforcement** — `run_playbook.sh` prompt now explicitly tells model to run `quality_gate.sh` before Phase 2d completion
5. **3 new benchmarks (41-43)** — sidecar JSON validation, script-verified closure, canonical UC identifiers

### Motivation (from v1.3.25 council review consensus):

All three v1.3.25 council reviewers (Codex, Cursor, Claude) converged on the same root cause: gates were instructions, not scripts. Specific issues from v1.3.25:
- 3/8 repos used wrong `## BUG-NNN` heading format (model non-compliance, not ambiguity)
- 6/8 repos had non-conformant sidecar JSON (missing keys, invalid enums, invented schemas)
- 7/8 repos had no canonical use case identifiers (content existed but no UC-NN format)
- 2/8 repos missing tdd-results.json `schema_version`
- Express had terminal gate section but with non-canonical heading

### Prior version changes still in effect:
- Artifact file-existence gate, benchmark isolation (`--no-seeds`), numeric version sort (v1.3.25)
- Immediate Phase 2a verify.sh gate, mechanical artifact immutability, forbidden probe pattern, verification receipts (v1.3.24)

## Run Results Summary

### Bug Counts

| Repo | Language | Bugs Found | Heading Format | Fix Patches | Notes |
|------|----------|-----------|----------------|-------------|-------|
| **virtio** | C (kernel) | [N] | [✓/✗] | [N] | |
| **httpx** | Python | [N] | [✓/✗] | [N] | |
| **express** | JavaScript | [N] | [✓/✗] | [N] | |
| **javalin** | Kotlin | [N] | [✓/✗] | [N] | |
| **chi** | Go | [N] | [✓/✗] | [N] | |
| **cobra** | Go | [N] | [✓/✗] | [N] | |
| **gson** | Java | [N] | [✓/✗] | [N] | |
| **serde** | Rust | [N] | [✓/✗] | [N] | |

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

| Repo | REQS | BUGS | TDD JSON | UC IDs | Auditors | Gate Log | Mechanical |
|------|------|------|----------|--------|----------|----------|------------|
| virtio | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | [exit N] |
| httpx | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | N/A |
| express | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | N/A |
| javalin | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | N/A |
| chi | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | N/A |
| cobra | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | N/A |
| gson | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | N/A |
| serde | [✓/✗] | [✓/✗] | [✓/✗] | [✓/✗] | [N]+triage | [✓/✗] | N/A |

**New columns: UC IDs = canonical UC-NN identifiers, Gate Log = quality-gate.log exists**

### Specific Findings

[FILL IN: notable per-repo observations, quality_gate.sh output excerpts, etc.]

## Your Review Tasks

### Per-Repo Scorecard

Score each repo against the 43 benchmarks in `references/verification.md`. Use:
- **PASS** — benchmark met
- **FAIL** — benchmark not met (explain)
- **N/A** — not applicable to this repo

Pay special attention to the 3 new benchmarks (41-43) and compare against v1.3.25 performance on the issues they target.

### Questions to Answer

1. **Did quality_gate.sh improve conformance?** The script was added specifically to catch heading format, sidecar JSON, and use case identifier issues that v1.3.25 missed. Compare: v1.3.25 had 3/8 wrong headings, 6/8 non-conformant JSON, 7/8 no UC identifiers. Did v1.3.26 improve? Did the model actually run the script and fix issues, or did it ignore the instruction?

2. **Sidecar JSON schema compliance.** v1.3.25 had httpx inventing alternate schemas, serde using legacy shape, javalin missing summary, etc. Did the explicit post-write validation instruction fix this? Check each repo's tdd-results.json for the required keys: `schema_version`, `skill_version`, `date`, `project`, `bugs`, `summary` (with `confirmed_open` in summary).

3. **Use case identifier adoption.** v1.3.25 had use case content in most repos but no canonical `UC-NN` identifiers. Did the explicit instruction + quality_gate.sh check produce canonical identifiers? Or did the model write use cases without identifiers and pass the gate anyway?

4. **Bug discovery comparison to v1.3.25.** v1.3.25 found 22 bugs across 8 repos with 0 seeds. How does v1.3.26 compare? Key per-repo comparisons:
   - **javalin:** v1.3.25 found BUG-001 (HEAD metadata) + BUG-002 (CORS). Same bugs refound?
   - **virtio:** v1.3.25 found 4 bugs including RING_RESET. Same core bugs?
   - **httpx:** v1.3.25 found 3 WSGI latin-1 bugs (different from v1.3.24's seeded bugs). Same, different, or expanded set?
   - **express:** v1.3.25 found BUG-001 (etag) + BUG-002 (Content-Type false). Both refound?

5. **Fix patch generation.** v1.3.25 had 5/8 repos with 0 fix patches despite having bugs (virtio: 4 bugs/0 patches, chi: 6/0, cobra: 2/0, gson: 2/0, serde: 1/0). Did v1.3.26 improve patch generation rate? (Note: patch generation isn't directly targeted by v1.3.26 changes — this tests whether script-verified closure has indirect quality benefits.)

6. **V2.0 gate assessment.** The v2.0 gate: "a clean run that catches all of the bugs that it previously found." Key comparisons against v1.3.25 (the prior clean run):
   - Per repo: did v1.3.26 find the same bugs as v1.3.25, plus any new ones?
   - Overall: is the bug discovery set converging (same bugs found across clean runs)?
   - What's still blocking v2.0?

7. **Regression or progress since v1.3.21?** The user observed that ~v1.3.21 was the best run. v1.3.21 had 9/9 repos with use cases, 6/9 with correct schema_version. v1.3.25 regressed to 1/8 use cases, 6/8 with schema_version. Has v1.3.26 recovered ground? Is the skill complexity still a barrier?

8. **Recommended changes for v1.3.27.** Based on the 8-repo results and the effectiveness (or not) of quality_gate.sh, what specific SKILL.md changes would you recommend? Prioritize: P0 (blocking v2.0), P1 (important), P2 (nice to have). Should the skill be simplified?

## Files to Examine

All artifacts under `repos/<repo>-1.3.26/quality/`. The SKILL.md is at the repo root as `SKILL.md` (or examine `.github/skills/SKILL.md` in any benchmark repo). Benchmark definitions: `references/verification.md` (43 benchmarks).

Key files for spot-checking:
- **Every repo:** `quality/results/quality-gate.log` — did the script run? What did it report?
- **Every repo:** `quality/results/tdd-results.json` — check all 6 required root keys
- **Every repo:** `quality/REQUIREMENTS.md` — grep for `UC-[0-9]` to verify canonical identifiers
- **Every repo:** `quality/BUGS.md` — grep for `^### BUG-` vs `^## BUG-`
- `virtio-1.3.26/quality/mechanical/` — mechanical verification path
- Compare any repo's `quality-gate.log` against the actual artifact state — did the model fix issues the script caught, or just write the log without fixing?
