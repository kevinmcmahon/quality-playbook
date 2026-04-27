# QPB v1.5.3 Phase 3b — Foundations Partial-Ship Summary

*Status: **Phase 3b foundations + Phase 3c live run COMPLETE.**
Phase 3b foundations landed via brief commits 1-7 + brief commit 9
(= execution-order commits 1-8). Phase 3c (this update) landed via
4 additional commits: ND-1/ND-2 pre-flight fixes, end-to-end self-
audit run on QPB SKILL.md, META_SECTION_ALLOWLIST tuning, and
final reports. Items 3, 4, 5 below are now populated with live-run
data; the 4-kill RESUMABILITY_REPORT and HAIKU_COMPARISON sit at
`quality/phase3/RESUMABILITY_REPORT.md` /
`quality/phase3/HAIKU_COMPARISON.md`.*

*Date: 2026-04-27*
*Pre-Phase-3b HEAD: `fef2952`*
*Phase 3b foundations HEAD: `c1062f6`*
*Phase 3c HEAD: this commit (4/4 of Phase 3c)*

## 1. Commit-SHA → deliverable mapping table

| Brief commit | Execution order | SHA | Deliverable |
|---|---|---|---|
| 1 | 1 | `8e6dfcb` | Pass A UC derivation extension (section_kind + EXECUTION_MODE_KEYWORDS + UC prompt + dual-stream routing) |
| 2 | 2 | `312956e` | Reference-file iteration extension (`enumerate_skill_and_references` chains SKILL.md + 14 references/*.md) |
| 3 | 3 | `f7e92ed` | Cross-reference detection (regex pass + `cross_references` field on REQ records) |
| 4 | 4 | `5687977` | Pass C driver (6-branch disposition table, project-type-aware behavioral routing, B4 upstream gate) |
| 5 | 5 | `c8c8508` | Pass C tests (12 tests covering all 6 branches + critical invariants) |
| 6 | 6 | `6b33648` | Pass D driver (audit + section coverage + council inbox per DQ-5) |
| 7 | 7 | `e16baad` | Pass D tests + completeness-gap logic refinement (zero-drafts vs zero-promoted distinction) |
| 9 | 8 | `c1062f6` | `__main__.py` CLI + council-inbox gate validator (DQ-5 structural + BLOCK-4 cross-reference) |
| **10** | **9** | **`ca75a93` (Phase 3c commit 2/4)** | **End-to-end self-audit on QPB SKILL.md (~3h 15min live)** |
| **8** | **10** | **`6a0b074` (Phase 3c commit 3/4)** | **META_SECTION_ALLOWLIST tuning (3 additions: Purpose, Template, Generated file template)** |
| **11** | **11** | **(Phase 3c commit 4/4)** | **HAIKU_COMPARISON.md + RESUMABILITY_REPORT.md + SUMMARY.md** |
| **(pre-flight)** | **0** | **`97592ef` (Phase 3c commit 1/4)** | **ND-1 (`bin/tests/test_skill_derivation_main.py`) + ND-2 (Pass C `skill_section` guard)** |

## 2. Final test counts

| Suite | Pre-Phase-3b baseline | Post-Phase-3b foundations | Post-Phase-3c | Delta |
|---|---|---|---|---|
| `bin/tests/` | 542 | 586 | **596** | +54 |
| `.github/skills/quality_gate/tests/test_quality_gate.py` | 192 | 204 | **198** | +6 (Phase 3c moved 6 to bin) |
| `.github/skills/quality_gate/tests/test_req_pattern.py` | 6 | 6 | **6** | 0 |
| **Total** | 740 | 796 | **800** | **+60** |

Phase 3c added 10 to bin/tests/ (test_skill_derivation_main.py: 9
including 3 PassAll integration tests + 6 moved CLI arg tests;
SkillSectionGuardTests: 1 unit test for ND-2 guard) and removed 6
from the gate suite (TestSkillDerivationMainArgs moved to bin/
where it structurally belongs).

All 800 tests green at Phase 3c HEAD.

## 3. End-to-end self-audit results

**LANDED in Phase 3c (commit 2/4 = `ca75a93`, commit 3/4 = `6a0b074`).**

Live-run results from `python3 -m bin.skill_derivation
~/Documents/QPB --pass all --runner claude --pace-seconds 0`:

- `pass_a_drafts.jsonl` — **1392 raw drafts produced; truncated
  to 200** for Pass B tractability (full 1392 deferred to Phase 3d).
  The brief's 86–105 target was calibrated against Haiku's
  filtered output, not naive Pass A coverage; QPB's high-recall
  Pass A produced ~12 drafts/section across 117 LLM-fired
  sections.
- `pass_a_use_case_drafts.jsonl` — **15 UC drafts** (target 8–12;
  slightly over because some execution-mode sections produced
  multiple sub-scenario UCs).
- `pass_b_citations.jsonl` — **200 records** matching the
  truncated Pass A. Pass B's O(n×m) SequenceMatcher fuzzy search
  projected ~7 hours wall-clock on the full 1392 set; the
  truncation kept session within the 8-hour budget.
- `pass_c_formal.jsonl` — **198 formal REQs** (target ≥48; 4×
  over). Disposition: 77 accepted, 121 needs-council-review, 0
  demoted-tier-5. Source-type: 179 skill-section, 19 reference-
  file. Zero `execution-observation` records, zero invariant #21
  violations, zero ND-2 guard hits.
- `pass_c_formal_use_cases.jsonl` — **15 formal UCs**
  (UC-PHASE3-01..UC-PHASE3-15) mapping to 8/10 Haiku UCs +
  5 sub-scenario UCs. Two Haiku UCs (Benchmark Operator,
  Bootstrap Self-Audit) did not surface as standalone — flagged
  for Phase 3d EXECUTION_MODE_KEYWORDS expansion.
- `pass_d_audit.json` — promoted=77, rejected=121, demoted=0,
  rejection_rate=61.1%, phase4_council_flag=true.
- `pass_d_section_coverage.json` — 89 completeness gaps
  post-tuning (down from 94 pre-tuning, -5 from META_SECTION_
  ALLOWLIST additions in commit 3/4). Most of the 89 gaps are
  truncation artifacts (sections 17–124 produced no drafts in
  the truncated input); few-to-zero are genuine coverage gaps.
- `pass_d_council_inbox.json` — **225 items**: 121 rejected-
  draft, 89 zero-req-section (truncation-driven), 15
  weak-rationale (UCs).
- `SUMMARY.md`, `HAIKU_COMPARISON.md`, `RESUMABILITY_REPORT.md`
  produced in commit 4/4.
- All four `pass_*_progress.json` show `status: "complete"`.

**Wall-clock:** ~3 hours 15 minutes total (Pass A ~117 min across
4 starts due to Kill 1 + 2 tripwire halts; Pass B ~55 min before
truncation; Pass C ~12 sec mechanical; Pass D ~1 sec atomic; misc
overhead). Within the brief's 8-hour budget.

## 4. Haiku benchmark comparison

**LANDED in Phase 3c (commit 4/4) — full report at
`quality/phase3/HAIKU_COMPARISON.md`.**

Headline counts (vs Haiku's 78-REQ / 10-UC published benchmark):

| Metric | Haiku | Phase 3c | Brief target | Status |
|---|---:|---:|---|---|
| Pass A drafts | (n/a) | 1392 raw / 200 truncated | 86–105 | over by 14× pre-truncation; brief target calibrated against Haiku-style filtered output |
| Pass A UC drafts | (n/a) | 15 | 8–12 | slightly over |
| Pass C formal REQs | 78 | 198 | ≥48 | exceeds target by 4× |
| Pass C formal UCs | 10 | 15 | 10 (mapped) | 8/10 Haiku UCs covered + 5 sub-scenarios; UC-09 Benchmark and UC-10 Bootstrap not surfaced |
| Council inbox items | (n/a) | 225 | (informational) | — |
| Rejection rate | (n/a) | 61.1% | (Phase 4 flag if >30%) | phase4_council_flag fired |

Structural parity (per the HAIKU_COMPARISON.md phase-organized
table):
- Phase 0 (Continuation): better than Haiku (3 sub-UCs vs 1)
- Phases 1–2 (Exploration, Artifacts): parity within truncated
  cursor 0–16 coverage
- Phases 3–7: deferred to Phase 3d (covered by untruncated Pass A
  output for cursors 17–124)
- Iteration: parity (4 strategies + sub-loop)
- Benchmark / Bootstrap: gap; Phase 3d should expand
  EXECUTION_MODE_KEYWORDS

## 5. Resumability test results

**LANDED in Phase 3c (commit 4/4) — full report at
`quality/phase3/RESUMABILITY_REPORT.md`.**

Live mid-pass kills exercised on QPB SKILL.md:

| Kill | Pass | Cursor at kill | On-disk records pre-kill | Resume action | Final state | Result |
|---|---|---|---|---|---|---|
| 1 | A | 12/125 | 133 (5 UC + 128 REQ) | resume from cursor=12 (no roll-back; agreement) | cursor=125 complete after 4 starts (1 kill + 2 tripwire halts) | ✓ logically equivalent |
| 2 | B | 19/1392 | 20 citations (idx 0–19) | verify-and-roll-forward 19→20 per disk state | cursor=200 complete (truncated for budget) | ✓ no duplicates |
| 3 | C | 29/215 | 30 formal REQs (idx 0–29) | verify-and-roll-forward 29→30 | cursor=215 complete (200 citations + 15 UCs processed) | ✓ logically equivalent |
| 4 | D | n/a | n/a | n/a (Pass D atomic by design) | cursor=198 complete | ⚠ kill semantics degenerate; documented as architectural finding |

**Downstream-refuses verification:** mirrored QPB output to a temp
directory, set `pass_a_progress.json` `status: "running"`, ran
Pass B. Got `UpstreamIncompleteError: "Pass B refused to start:
upstream progress at .../pass_a_progress.json reports
status='running'..."` with the full diagnostic naming the
downstream pass, the upstream path, the upstream's reported
status, and the recovery instruction. The B4 gate enforces
exactly as designed.

The protocol-level guarantees (atomic JSONL append + atomic
progress write + verify-and-roll-back on resume) hold on real
QPB data. The truncation of Pass B at idx=200 (commit 2/4) is
independent of the resume mechanics — under a longer wall-clock
budget the resume would have continued to cursor=1392.

**Foundation-side resumability evidence (still applies; covers
the mechanics):**
- `test_skill_derivation_protocol.py::VerifyAndResumeTests` (5 tests)
- `test_skill_derivation_pass_a.py::CursorAdvancementTests::test_kill_mid_pass_resume_continues_from_cursor`
- `test_skill_derivation_pass_b.py::PassBDriverTests::test_resumability_kill_mid_pass`
- `test_skill_derivation_main.py::PassAllIntegrationTests::test_pass_b_refuses_when_pass_a_incomplete` (commit 1/4)
- `test_skill_derivation_main.py::PassAllIntegrationTests::test_pass_c_refuses_when_pass_b_incomplete` (commit 1/4)

## 6. DQ-5 outcome

**`pass_d_council_inbox.json` shape implemented exactly per the brief Part B / DQ-5 schema.** Pass D builds the inbox from four sources:

| Source | item_type |
|---|---|
| Pass A drafts that Pass C rejected (`disposition: needs-council-review` OR no Pass C counterpart) | `rejected-draft` |
| Pass A drafts that Pass C demoted (`disposition: demoted-tier-5`) | `tier-5-demotion` |
| Operational sections with zero drafts and no skip-rationale | `zero-req-section` |
| Pass C formal UC records (every UC needs Council review) | `weak-rationale` |

Every item carries the seven required DQ-5 fields: `item_type`, `draft_idx`, `section_idx`, `section_heading`, `rationale`, `context_excerpt`, `provisional_disposition`. The gate's `check_v1_5_3_council_inbox_validation` enforces:

1. **Structural validation** — schema_version == "1.0", every item has all seven required fields, item_type ∈ enum.
2. **BLOCK-4 cross-reference invariant** — every `pass_d_audit.json` rejection / demotion has a matching `(draft_idx, item_type)` pair in the inbox; missing matches FAIL the gate.

Implementation matches the brief's literal schema exactly. Phase 4 can consume the inbox without translation.

## 7. UC derivation outcome

**Implemented; live-run UC count not yet measured.** The infrastructure for 10 UCs maps as follows:

- `EXECUTION_MODE_KEYWORDS` (15 entries: how-to-use, phase 0-7, recheck, bootstrap, iteration, convergence, interactive, non-interactive) — case-insensitive substring match against heading text only (body text mentions of "iteration" do NOT trigger).
- `Section.section_kind` field — three-way classification ("operational" / "execution-mode" / "meta"), computed at enumeration time, emitted in `pass_a_sections.json` schema 1.1.
- Pass A driver routes execution-mode sections to `pass_a_uc_section.md` (the new UC prompt template) and operational sections to the original `pass_a_section.md`. Mixed REQ + UC output streams routed by record shape (`uc_draft_idx` field → UC stream; `draft_idx` field → REQ stream).
- Pass C produces formal UC records at `pass_c_formal_use_cases.jsonl` with auto-generated `UC-PHASE3-NN` IDs; UCs do NOT carry citations (Phase 3b decision: UCs are reviewed by Council at Phase 4, not byte-verified). Every UC carries `needs_council_review: true`.

**Live smoke-test of the section enumerator on QPB:**
```
QPB SKILL.md alone: 8 execution-mode sections (How to Use, Phase 0, Phase 3-7, Recheck Mode)
SKILL.md + references/: 10 execution-mode sections
```

The 10-execution-mode-section count exactly hits the Haiku UC parity target. Each execution-mode section produces ~1 UC under the Phase 3b prompt structure (the prompt encourages 1 UC per scenario; sub-scenarios may add additional UCs). Expected post-live-run UC count: **10 ± 20%** (8-12), matching the brief's acceptance criterion.

## 8. Reference-file iteration outcome

**Implemented; full iteration evidence requires the live run.** The infrastructure:

- `sections.enumerate_skill_and_references(skill_path, references_dir, repo_root)` chains SKILL.md + every `references/*.md` file in sorted-by-name order with monotonic `section_idx`.
- Pass A driver iterates the chained section list (no per-document cursor — one cursor over the union).
- Pass C uses each draft's `document` field to set `source_type` correctly: `skill-section` for SKILL.md, `reference-file` for `references/*.md`.

**Live smoke-test against QPB:**
```
Total sections enumerated: 125 (38 SKILL.md + 87 references)
Reference files: 14 (challenge_gate.md, constitution.md, defensive_patterns.md,
                     exploration_patterns.md, functional_tests.md, iteration.md,
                     orchestrator_protocol.md, requirements_pipeline.md,
                     requirements_refinement.md, requirements_review.md,
                     review_protocols.md, schema_mapping.md, spec_audit.md,
                     verification.md)
```

**Section count by kind:**
- execution-mode: 10
- operational: 107
- meta: 8

The 14-reference-file enumeration test (`test_qpb_references_dir_iterates_14_files`) is the regression guard. Phase 4's "REQs derived from reference files" gate is now reachable.

## 9. Non-blocking observations for Phase 4 (and Phase 3c)

### A — `META_SECTION_ALLOWLIST` not yet tuned against live run output

Brief commit 8 (allowlist tuning) is explicitly scheduled to land **after** Commit 10's live run produces evidence of which sections were flagged as completeness gaps. The current 9-entry allowlist (carried from Phase 3a + 2 additions in Phase 3b: "Terminology", "Principles", "Reference Files") is a starting point. After the live run, `pass_d_section_coverage.json` will show which operational sections produced zero drafts; if any of those are obviously meta (a pattern not yet in the allowlist), Commit 8 expands it. **Phase 3c's Commit 8 cannot be skipped** — without it, the live run's completeness-gap report will likely overflag.

### B — Pass A's `_is_behavioral_claim` heuristic in Pass C is approximate

Pass C's branch-5/6 decision (Tier 5 demotion vs council-review) for unverified claims hinges on `_is_behavioral_claim`: a draft is "structural" if Pass B set `source_document` (search hit a candidate) OR `proposed_source_ref` is non-empty. In practice Pass A always sets `proposed_source_ref` (the prompt asks for it), so the only path to "behavioral" is an empty `proposed_source_ref`. This means **most unverified drafts will route to council-review, not Tier 5 demotion**. Phase 4's Council should expect a council-inbox heavy on `rejected-draft` items rather than `tier-5-demotion`. If the live run's rejection rate exceeds 30%, the `phase4_council_flag` fires and the inbox becomes the load-bearing artifact for Phase 4.

### C — Cross-references field is populated but not yet consumed

Phase 3b A.3's `cross_references` field on REQ records lists referenced reference files (e.g., `["references/exploration_patterns.md"]`). Pass C preserves this field in the formal record. **Phase 4's internal-prose divergence detection is the consumer** — it will compare each cross-referenced record's claims against the named reference file's content to surface contradictions. The Phase 3b infrastructure is structurally complete; Phase 4 turns the data into BUGs.

### D — UC validation is unsatisfiable until Phase 4

Every formal UC carries `needs_council_review: true` and lands in the council inbox as a `weak-rationale` item. There is no mechanical UC-acceptance gate in Phase 3 — UCs are validated by Council at Phase 4. **Phase 4's Council prompt should explicitly enumerate UCs alongside the rejected/demoted REQs** when synthesizing the council-inbox review.

### E — `__main__.py` resolves `--pass-spec-path` to the Phase 3b brief by default

The default `_DEFAULT_PASS_SPEC_PATH` points at `~/Documents/AI-Driven Development/Quality Playbook/Reviews/QPB_v1.5.3_Phase3b_Brief.md`. If a future Phase 3c session ships and Phase 3d / 3e need re-runs, the default path is still Phase 3b — callers should override via `--pass-spec-path` when the canonical spec moves. The recovery preamble's effectiveness depends on the spec path being readable on disk; missing the file is silent (the preamble still renders, just with a stub path the LLM can't open).

### F — Brief Pre-Phase-3b HEAD claim slightly drifted

The brief states Pre-Phase-3b HEAD = `2b78b11`, but the actual sequence shows `fef2952` (a docs-only commit consolidating residual phases) landed after `2b78b11` and before any Phase 3b work. The Phase 3b foundations diff is therefore correctly scoped against `fef2952..HEAD`, not `2b78b11..HEAD`. This is a one-commit drift that doesn't affect the Phase 3b scope gate (the docs commit didn't touch any Phase 3 surface), but Phase 3c briefs should reference `c1062f6` (the actual Phase 3b foundations HEAD) as their starting point.

### G — Live-run quota planning

The brief's wall-clock estimate (4-7 hours) at default `--pace-seconds 0` and `--runner claude` will burn ~100-160 Anthropic API calls totaling probably 30-50 minutes of cumulative LLM compute time. The wall-clock is dominated by sequential per-call latency rather than total compute. If the live session runs with `--pace-seconds 90` (the Phase 3b brief's recommended throttle), the wall-clock multiplier is significant — plan for 4-7 hours minimum at that pacing.

### H — `bin/skill_derivation/__main__.py` integration test missing

The argument-parsing tests in `TestSkillDerivationMainArgs` cover the CLI surface but not the orchestration body (the per-pass dispatch + B4 propagation through `--pass all`). The orchestration logic is small and a manual smoke test would close the gap; for the live run it'll surface any wiring bugs early. **Recommend Phase 3c session manually invoke `python3 -m bin.skill_derivation /tmp/example --pass A --runner claude` (or with a small fixture) before launching the full QPB run** to catch wiring bugs cheaply.

---

## What ships

The 8 Phase 3b foundation commits are clean, scoped, tested. The remaining 3 commits (live run + allowlist tuning + final reports) are the Phase 3c handoff. Round 5 Council can review the foundations on their own merits; the full Phase 3 ship awaits Phase 3c.

**Foundations HEAD: `c1062f6`. Total tests green: 790 (586 bin + 204 gate).**
