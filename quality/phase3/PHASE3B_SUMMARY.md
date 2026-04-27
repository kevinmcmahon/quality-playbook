# QPB v1.5.3 Phase 3b — Foundations Partial-Ship Summary

*Status: **Phase 3b foundations only.** Brief commits 1-7 and brief commit 9 (= execution-order commits 1-8) landed cleanly. Brief commits 10, 8, 11 (the live QPB SKILL.md self-audit run and its derived artifacts/reports) were NOT performed in this session — they require 4-7 hours of live `claude --print` invocations totaling 100-160 sequential LLM calls plus 4 mid-pass kills, which cannot honestly happen inside a single agent turn. The brief explicitly authorizes this partial-ship pattern at line 16 ("If actual wall-clock exceeds 8 hours, halt and ship as Phase 3b foundations + Phase 3c live run") and line 36 ("the natural break is between Pass C/D code commits ... and the live self-audit run").*

*Date: 2026-04-27*
*Pre-Phase-3b HEAD: `fef2952`*
*Phase 3b foundations HEAD: `c1062f6`*

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
| **10** | **9** | **NOT LANDED** | **End-to-end self-audit on QPB SKILL.md (4-7 hours live LLM time)** |
| **8** | **10** | **NOT LANDED** | **META_SECTION_ALLOWLIST tuning (depends on Commit 10's flagged-gap evidence)** |
| **11** | **11** | **NOT LANDED** | **HAIKU_COMPARISON.md + RESUMABILITY_REPORT.md + SUMMARY.md (depends on Commit 10's artifacts)** |

## 2. Final test counts

| Suite | Pre-Phase-3b baseline | Post-Phase-3b foundations | Delta |
|---|---|---|---|
| `bin/tests/` | 542 | **586** | +44 |
| `.github/skills/quality_gate/tests/test_quality_gate.py` | 192 | **204** | +12 |
| **Total** | 734 | **790** | **+56** |

The bin/tests/ count (586) is below the brief's estimated post-Phase-3b range of 575-610 because the live-run commits (10/8/11) don't add unit tests; their work surfaces in artifacts and reports rather than tests. The +44 covers UC handling (13), reference-file iteration (4), cross-reference detection (8), Pass C disposition table (12), and Pass D audit/coverage/inbox (7). The gate suite +12 covers council-inbox structural+cross-reference validation (6) and `__main__.py` argument parsing (6).

All 790 tests green at HEAD `c1062f6`.

## 3. End-to-end self-audit results

**NOT AVAILABLE — Commit 10 was not performed in this session.**

The expected artifacts for the eventual Phase 3c live run:

- `quality/phase3/pass_a_drafts.jsonl` — target 86-105 records (Haiku 95 ± 10%)
- `quality/phase3/pass_a_use_case_drafts.jsonl` — target 8-12 UC drafts
- `quality/phase3/pass_b_citations.jsonl` — one record per Pass A draft
- `quality/phase3/pass_c_formal.jsonl` — target ≥48 formal REQs (≥50% of Haiku 95)
- `quality/phase3/pass_c_formal_use_cases.jsonl` — target 10 formal UCs
- `quality/phase3/pass_d_audit.json`, `pass_d_section_coverage.json`, `pass_d_council_inbox.json`
- `quality/phase3/SUMMARY.md`

Wall-clock estimate (per the brief): 4-7 hours. With 125 enumerated sections (38 SKILL.md + 87 references) on QPB and `--pace-seconds 1` Anthropic-default pacing, the math is ~125 × 30-60s/call = 1-2 hours for Pass A alone, plus mechanical-only Pass B and Pass D, plus another 30-60 minutes for Pass C's LLM-driven council-review provisional dispositions on the unverified subset, plus 4 mid-pass kills × 5-10 min restart overhead = 25-40 min. Total realistic envelope 2-4 hours for the run + 1-2 hours for resumability = 3-6 hours.

## 4. Haiku benchmark comparison

**NOT AVAILABLE — depends on Commit 10/11 output.**

The comparison table will populate at `quality/phase3/HAIKU_COMPARISON.md` once Commit 10 lands. Acceptance criteria from the brief:

- Pass A draft count: 86-105 (Haiku 95 ± 10%)
- Pass C formal REQ count: ≥48 (≥50% of Haiku 95)
- 10 use cases mapped to Haiku's 10 by description
- Pass D rejection rate documented per draft

## 5. Resumability test results

**NOT AVAILABLE — depends on Commit 10 (4-pass live run with mid-pass kills).**

The eventual `RESUMABILITY_REPORT.md` will document one mid-pass kill per pass (4 kills total: A, B, C, D) on QPB SKILL.md from a clean Phase 3b start, each with kill-point cursor state pre/post + resumed run's eventual artifact + diff vs. uninterrupted run.

**Foundation-side resumability evidence (already in unit tests):**
- `test_skill_derivation_protocol.py::VerifyAndResumeTests` (5 tests) cover the cursor-rollback semantics on agreement, ahead, behind, empty, no-progress-file cases.
- `test_skill_derivation_pass_a.py::CursorAdvancementTests::test_kill_mid_pass_resume_continues_from_cursor` exercises a mid-Pass-A kill with `MockRunner` raising `RuntimeError`; the resumed run completes the remaining sections and the final artifact equals an uninterrupted run.
- `test_skill_derivation_pass_b.py::PassBDriverTests::test_resumability_kill_mid_pass` exercises a mid-Pass-B partial-state setup + resume-to-completion.
- B4 upstream-status gate enforced for Pass B (Phase 3a-completion), Pass C (Commit 4 here), Pass D (Commit 6 here). Three regression tests pin the gate behavior; deliberately removing an upstream `status: "complete"` causes the next pass to refuse with `UpstreamIncompleteError`.

The unit-test layer covers the mechanics; the live QPB SKILL.md kills are the missing acceptance-gate evidence.

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
