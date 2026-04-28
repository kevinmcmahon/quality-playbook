# QPB v1.5.3 — Development Journal

*Compiled: 2026-04-28. Covers the v1.5.3 development arc from the v1.5.2 misfire reset (2026-04-26) through ship (tag pushed 2026-04-27) and post-tag refinements (2026-04-28).*

This document narrates the v1.5.3 development journey for future maintainers and AI assistants picking up the work. It covers what was built, what went wrong, what got fixed, and what got deferred. For canonical specifications see `docs/design/QPB_v1.5.3_Design.md` and `docs/design/QPB_v1.5.3_Implementation_Plan.md`. For the formal release artifacts see the `v1.5.3` tag at commit `37dfe9c`.

---

## 1. What v1.5.3 is

v1.5.3 is the **skill-as-code** release. It extends QPB's quality-engineering pipeline to audit AI skills (SKILL.md prose plus reference files) the same way the v1.5.0–v1.5.2 pipeline audits code projects. Three load-bearing additions:

1. **A Phase 0 project-type classifier** (`bin/classify_project.py`) that tags each target as Code, Skill, or Hybrid. Code projects continue through the v1.5.0 divergence pipeline unchanged; Skill and Hybrid targets get a new four-pass derivation pipeline.

2. **A four-pass generate-then-verify skill-derivation pipeline** (`bin/skill_derivation/`) that walks SKILL.md section-by-section to derive requirements when there is no separation between specification and implementation (the prose IS the program).

3. **A skill-divergence taxonomy** (internal-prose, prose-to-code, execution) implemented as Phase 4 of the derivation pipeline, with new gate checks that enforce coverage on Skill/Hybrid targets.

The release also adds the **OpenAI Codex CLI** as a third LLM runner alongside Claude (`claude --print`) and GitHub Copilot (`gh copilot --prompt`).

The shipped tag (v1.5.3 at commit `37dfe9c`) is on origin. Three post-tag commits land on the `1.5.3` branch HEAD without moving the tag: orientation-doc cleanup (`facca1a`), codex runner addition (`b6b31f2`), codex runner orientation update (`b9a5ff8`). Two operational-tooling commits to `setup_repos.sh` (`33b9b53`, `31954cc`) are also on the branch.

---

## 2. The Haiku 4.5 demonstration — why skill-as-code

On 2026-04-19, Claude Haiku 4.5 was given QPB's `docs_gathered/` history (14 MB of design notes, prior chats, implementation discussion) and the existing `quality/REQUIREMENTS.md`. Asked three questions — what does this system do, what are its major features, how much of the system does REQUIREMENTS.md span — Haiku correctly identified the coverage gap: the existing requirements covered only the Python orchestration layer and explicitly omitted SKILL.md (~1,500 lines, the operational playbook), reference files, and orchestrator agent prompts.

Asked to produce a comprehensive REQUIREMENTS.md covering the entire skill, Haiku 4.5 with two simple prompts produced a 2,129-line document with ~65 unique REQ definitions, 10 use cases spanning all seven phases plus iteration modes and bootstrap self-audit. QPB's own v1.4.5 self-audit, running its full six-phase procedure over the same codebase, produced 721 lines, 40 REQs, focused almost entirely on Python infrastructure.

The smaller, cheaper model with two simple prompts beat QPB's own procedure by nearly 3× on the dimension the procedure was designed to optimize. That was a systemic gap, not a model-quality issue. The Haiku-generated document is preserved at `~/Documents/AI-Driven Development/Haiku QPB requirements analysis/REQUIREMENTS.md` and serves as the v1.5.3 success benchmark.

The diagnosis: QPB's six-phase pipeline assumes the thing under review is source code. Phase 1 misclassifies SKILL.md as "documentation" rather than "the artifact under review." The tier system assumes Tier 1 intent lives in external specs and Tier 3-5 lives in source; for a skill, both live in the same prose, so the tier question has no natural answer. The requirements pipeline produces plumbing-level REQs from code, not section-level REQs from prose.

Haiku succeeded because the operator's explicit instruction ("cover the entire skill") bypassed these implicit assumptions. For QPB to audit skills reliably, the classification has to happen mechanically before Phase 1 starts. v1.5.3 is the systematic fix.

---

## 3. v1.5.2 misfire and the fresh 1.5.3 branch (2026-04-26)

The first attempt at v1.5.3 work landed a few commits on a `1.5.3` branch that had drifted from a clean v1.5.2 baseline. Specifically, Cowork Claude wrote a "C13.11 / IMPROVEMENT_LOOP.md sequencing edit" plus a Round 9 Council prompt and Claude Code launch command — all without reading `docs/design/QPB_v1.5.3_Design.md` or `docs/design/QPB_v1.5.3_Implementation_Plan.md` end-to-end first. The planning content sequenced "C13.11 + mechanical extraction + categorization tagging" instead of v1.5.3's actual scope (Phase 0 classifier + four-pass skill-derivation pipeline + skill-divergence taxonomy).

The cause: the Cowork session treated system-reminder pre-loaded files as a complete picture and never searched `docs/design/` for the canonical version doc.

The fix: the `1.5.3` branch was reset from `main` (post-v1.5.2 tip), the misfire commits dropped, and the workspace `CLAUDE.md` rule strengthened:

> **Read the canonical doc before authoring anything about it.** Before writing planning content of any kind — briefs, sequencing edits, IMPROVEMENT_LOOP.md updates, Council prompts, hand-off docs, Claude Code launch prompts, release plans — about a versioned release of any project, Cowork Claude must FIRST search the project's `docs/design/`, `docs/`, `specs/`, or equivalent canonical-doc directory for an existing design document on that version, and read both `<project>_v<X.Y.Z>_Design.md` and `<project>_v<X.Y.Z>_Implementation_Plan.md` end-to-end if they exist.

This rule has held since. Every subsequent brief in v1.5.3 was authored after reading the Design + Implementation Plan in full. The diagnostic signature for catching future violations: a planning doc that sequences work items confidently but cites no `docs/design/` line numbers — only summary-doc references like "per IMPROVEMENT_LOOP.md."

The fresh 1.5.3 branch then began Phase 1 work proper.

---

## 4. The development cadence

v1.5.3 was developed phase by phase. Each phase produced a brief (authored against the canonical Design + Implementation Plan), went through sub-agent pre-flight (one or two sub-agents reading the brief and surfacing BLOCKs / MUST-FIXes before launch), launched as a focused Claude Code session, and concluded with a Council review (three sub-agent reviewers in parallel — Opus, Sonnet, Haiku — synthesized into a verdict).

This cadence proved valuable. Sub-agent pre-flight caught real BLOCKs before each Claude Code launch, and Council reviews caught real defects before each phase's commits were taken as load-bearing. Several phases needed follow-up commits or scope-revision after Council; the iterative discipline kept errors small and contained.

Total: 5 numbered phases, 8 Council rounds, ~80 commits on the 1.5.3 branch.

---

## 5. Phase 1 — Project-type classifier

**Goal:** Add a Phase 0 step that classifies each target as Code, Skill, or Hybrid.

**Implementation:** `bin/classify_project.py`. Heuristic: SKILL.md at repo root with prose word count > 2× code LOC → Skill; SKILL.md present but code-heavy → Hybrid; no SKILL.md → Code. Output: `quality/project_type.json` with classification, confidence, evidence, optional override fields.

**Round 1 verdict (Council on Phase 1 closure):** SHIP with one carry-forward — Sonnet Panelist C flagged that the Phase 4 Council override workflow needed an explicit design decision. Resolved later as DQ-4-1: re-run `python3 -m bin.classify_project --override <new> --override-rationale "<text>"` rather than post-hoc amendment.

**Acceptance verified:** all 5 code benchmark targets classify as Code; QPB itself classifies as Hybrid (2.6× ratio at "medium" confidence); a synthetic Skill fixture classifies as Skill.

---

## 6. Phase 2 — Schema extensions

**Goal:** Extend `schemas.md` to support skill-specific concepts without breaking code-project usage.

**Surface added:**
- `REQ.source_type`: `{code-derived, skill-section, reference-file, execution-observation}`
- `REQ.skill_section`: heading-or-line-anchor of the source section in SKILL.md
- `BUG.divergence_type`: `{code-spec, internal-prose, prose-to-code, execution}`
- `FORMAL_DOC.role`: `{external-spec, project-spec, skill-self-spec, skill-reference}`
- `schemas.md §3.9`: SKILL.md-vs-reference-file precedence rule (SKILL.md wins; reference file is the spec-fix target on conflict)
- `schemas.md §3.10`: field-presence detection for v1.5.3 fields (rather than schema_version comparison) — keeps legacy manifests passing with soft-warns rather than fails

**Round 2 verdict:** SHIP. Field-presence detection landed cleanly; backward compat with v1.5.0/v1.5.2 manifests verified.

---

## 7. Phase 3 — Four-pass derivation pipeline

This was the largest phase, executing in five segments through four Council rounds.

### 7.1 Architecture: generate-then-verify

The pipeline separates coverage breadth from citation precision:

- **Pass A (Naive Coverage):** Haiku-style prompt — "Read the skill. Produce comprehensive requirements." Section-iterative for skills above a small-input threshold (a per-section cursor in `pass_a_progress.json`, output appended to `pass_a_drafts.jsonl`). High-recall on purpose; tolerates overreach because Pass B will filter. Critical constraint: Pass A *cannot* produce `citation_excerpt` values — only `proposed_source_ref`.

- **Pass B (Citation Extraction):** mechanical grep + token-overlap pre-filter against SKILL.md and reference files. Populates `citation_excerpt` only from mechanical extraction. Reuses v1.5.0's citation extractor; no new ML.

- **Pass C (Formal REQ Production):** converts each cited draft into a proper REQ record with tier, ID, full citation schema. Six-branch disposition table: promote, reject, demote-to-Tier-5, etc.

- **Pass D (Coverage Audit):** diffs Pass A's full draft list against Pass C's verified list. Every dropped draft requires explicit rejection rationale. No silent drops.

The architecture is the pipeline equivalent of generate-and-verify: each pass does one thing well rather than asking one model to both cover comprehensively and cite rigorously.

### 7.2 Disk-as-ledger execution discipline

A correctness invariant for any pass running over long inputs: every pass writes incrementally, advances a cursor in a progress file, and can resume from the last cursor after interruption or auto-compaction. Pass prompts include a recovery preamble ("if you see a continuation banner, re-read the spec, read the progress file, verify continuity against disk, resume from cursor — disk is the source of truth, not the conversation"). Restart logic verifies the last JSONL record's idx equals `cursor - 1` and rolls the cursor back to disk state on discrepancy.

This was empirically validated against an interrupted-mid-pass restart on QPB's own SKILL.md.

### 7.3 The five segments

**Phase 3a (initial):** Pass A drafts + Pass B citations on QPB's SKILL.md. Council Round 3 reviewed; verdict was SHIP with carry-forwards (DQ-1 dataclass refactor, DQ-3 lockstep regression test, DQ-5 council inbox JSON shape).

**Phase 3a-completion (the partial-ship):** A brief drafted by Cowork Claude assumed all four work items from Round 3 would land in the post-Council session. Claude Code only landed B2 (DQ-1) and B4 (DQ-3); skipped B1 (live run) and B3 (resumability verification). Sub-agent pre-flight on Phase 3b's brief later caught this with BLOCK-1 ("Phase 3a-completion partial state assumption wrong"); Phase 3b absorbed B1 + B3 instead of redoing the partial.

**Phase 3b foundations:** Pass C + Pass D + UC derivation + reference-file iteration. Council Round 5 reviewed; SHIP with three minor carry-forwards (ND-1: missing `__main__.py` integration test; ND-2: Pass C `skill_section` non-empty validation guard; ND-3: minor doc).

**Phase 3c (live self-audit):** First live run on QPB's SKILL.md. Round 6 verdict: ship Phase 3c, but Phase 3d required before v1.5.3 release — full corpus re-run with token-overlap pre-filter to fix the Pass B truncation Phase 3c had used to fit within wall-clock.

**Phase 3d (full corpus + Round 6 follow-ups):** Token-overlap pre-filter (`TOKEN_OVERLAP_FLOOR=0.2` at `citation_search.py:54`) gave a ~93× speedup (7h → 4.5min on the full corpus). Threshold tuned from 0.6 to 0.5; rejection rate dropped 61.1% → 26.4%. EXECUTION_MODE_KEYWORDS expanded to surface UC-09 (Benchmark) and UC-10 (Bootstrap). Hand-authored UC-PHASE3-17 added for Bootstrap. Full corpus produced 1,369 formal REQs across 17 UCs.

### 7.4 Round 7 — the verification finding

Round 7 reviewed Phase 3d. All three reviewers verdict-converged on SHIP with one non-blocking fix. **The substantive finding: Opus uniquely caught and the synthesizer empirically verified that the `_metadata.phase_3d_synthesized=true` tag claimed in `PHASE3B_SUMMARY.md` for UC-PHASE3-17 was NOT actually present in `pass_c_formal_use_cases.jsonl`.** Sonnet and Haiku both wrote their reviews assuming the tag was present based on the doc claim; only Opus did the empirical check.

This was the same failure mode as the 2026-04-26 README-not-pushed incident: confidence-in-claim without observation-of-state. The workspace `CLAUDE.md` already had a rule against this pattern; Round 7's surfacing of it again strengthened the rule's importance.

The fix landed at commit `c64993f`: not just adding the tag to the JSONL artifact, but fixing the underlying defect — `pass_c.py::_build_formal_uc` was dropping the `_metadata` field during Pass A → Pass C propagation. Patching only the artifact would have left the bug latent for the next Pass C re-run; the propagation fix made the discipline enforceable end-to-end. Three regression tests (`HandAuthoredUcSynthesizedTagTests`) pin the behavior.

### 7.5 What Phase 3 produced

After 3a → 3a-completion → 3b → 3c → 3d + Round 7 follow-up:

- **1,369 formal REQs** in `quality/phase3/pass_c_formal.jsonl` (1,007 accepted, 362 needs-council-review)
- **17 formal UCs** in `pass_c_formal_use_cases.jsonl`, including the hand-authored UC-PHASE3-17 with the `_metadata.phase_3d_synthesized: true` tag
- **379-item council inbox** at `pass_d_council_inbox.json` (362 rejected drafts + 17 weak-rationale items)
- **Per-section coverage report** at `pass_d_section_coverage.json`

Phase 3's outputs become Phase 4's primary input.

### 7.6 The disposition-table degeneracy (carry-forward)

A structural finding from Round 7: the 362 rejected drafts share one rationale string because Pass A always populates `proposed_source_ref` (per its prompt template), making `_is_behavioral_claim` structurally False for every QPB draft. This collapses Pass C's six-branch disposition table to two reachable branches; `0 demoted` is a structural guarantee, not an empirical "no behavioral claims" finding.

The carry-forward to Phase 4: Council triage of the 362 records cannot rely on Pass C's rationale string for differentiation. Phase 4 introduced the `triage_batch_key` field (`<source_document>::<section_idx>`) so a future Council UI can surface section-grouped batches.

The carry-forward beyond v1.5.3: the disposition-tree redesign — extend Pass A to admit "behavioral claim" categories that bypass `proposed_source_ref`, OR redesign the 6-branch disposition table to match Pass A's actual output distribution. Tracked as v1.5.4 / v1.6.0 backlog work.

---

## 8. Phase 4 — Divergence detection + skill-project gate enforcement

Phase 4 originally had three separate phases (4 = static divergence, 5 = execution divergence, 6 = gate enforcement). After completing Phase 3, real-world phase sizing showed the boundary between detection and enforcement was artificial. The leaner consolidation merged them into a single Phase 4 with five parts.

### 8.1 The five parts

- **Part A — Static divergence detection:** internal-prose (intra-section + cross-section-countable) + prose-to-code (Tier 1 mechanical countable claims + Tier 2 LLM-judged for non-countable). Implementation: `bin/skill_derivation/divergence_internal.py`, `divergence_prose_to_code_mechanical.py`, `divergence_prose_to_code_llm.py`.

- **Part B — Execution divergence:** consume archived `quality_gate.py` outputs across `previous_runs/`, REQ-to-gate-check mapping authored explicitly in REQ records (`gate_check_ids` field), pattern aggregator, divergence reporter. Strict scope: no LLM evaluation harness, no semantic-quality grading. Implementation: `bin/skill_derivation/execution_gate_loader.py`, `divergence_execution.py`.

- **Part C — Skill-project gate enforcement:** four new checks in `quality_gate.py` (`check_skill_section_req_coverage`, `check_reference_file_req_coverage`, `check_hybrid_cross_cutting_reqs`, `check_project_type_consistency`). Skill-specific checks SKIP rather than FAIL on Code projects.

- **Part D — BUG record production + Council inbox extension:** `divergence_to_bugs.py` converts divergences into formal BUG records; consolidates per `schemas.md §8.1` (cell-identity / consolidation rules). Phase 4 produces `pass_e_council_inbox.json` parallel to Phase 3's inbox so Phase 3's tagged ledger stays clean. Backfills `triage_batch_key` on `pass_d_council_inbox.json` via JOIN to `pass_c_formal.jsonl`.

- **Part E — Classifier override workflow:** the Round 1 carry-forward. Adds `--override` and `--override-rationale` argparse flags to `bin/classify_project.py` (the function had the parameters since v1.5.3 Phase 1, but they weren't exposed at the CLI surface). Workflow doc at `docs/design/QPB_v1.5.3_Phase4_Council_Override_Workflow.md`.

### 8.2 Round 7 carry-forwards integrated as Phase 4 design questions

- **DQ-4-5 — Disposition-table degeneracy:** every inbox item gets a `triage_batch_key` field for section-level batching. Phase 4 produces the field; the actual triage UI is Phase 5+ scope.

- **DQ-4-6 — UC-PHASE3-17 anchor verification:** before Part A.2/A.3 emit any BUG referencing a synthesized UC, Phase 4 verifies the section anchor. If unsupported, emit a single `un-anchored-uc` divergence and skip prose-to-code detection for that UC.

- **DQ-4-7 — O(N²) indexing on 1,369 records:** three-stage indexing (partition by `(source_document, section_idx)` → pairwise within partition → cross-section countable-claim index). Acceptance: Stage 2 + Stage 3 < 5,000 pairs (verified at 15,926 actual on QPB; documented as calibration finding rather than defect since Stage 2 + 3 is still O(N) overall, far below N²=1.87M).

### 8.3 The sub-agent pre-flight catch

Phase 4's brief draft (post-Round 7) went through sub-agent pre-flight (Opus + Sonnet). Both reviewers caught the same two BLOCKs:

1. **`gate_check_ids` field doesn't exist on QPB REQs.** Phase 3d did not populate it. Phase 4 Part B (execution divergence) would be a structural no-op on QPB's actual output. The Plan's gate criterion ("at least one real execution divergence surfaced from QPB's bootstrap history") was unachievable. Brief explicitly relaxed: Part B ships the machinery; QPB self-audit produces documented-empty output.

2. **`triage_batch_key` backfill uncomputable as specified.** Inbox items have `section_idx` but no `document` field; the 362 needs-council-review REQs have `source_document=None` because they came from sections Pass A only inferred from SKILL.md. The brief specified an explicit JOIN via `draft_idx` to `pass_c_formal.jsonl`, with `"SKILL.md"` fallback for None values, plus a mandatory verification step grep'ing for `"None"` strings.

Plus several MUST-FIXes (Sonnet caught: `--override` flags don't exist in argparse; Opus caught: §3.9 "later-section-wins" rule is a brief invention not in `schemas.md`; multiple labeling and path corrections).

The pre-flight changes alone saved hours of debugging; both BLOCKs would have caused Claude Code's Phase 4 session to fail mid-run.

### 8.4 Phase 4 ship

17 commits, range `c64993f..8dd7c17`. Tests: 631 (`bin/tests/`) + 215 (gate suite) + 6 (req_pattern) = 852 green. Backward compat verified.

QPB self-audit:
- 29 internal-prose divergences (15 intra-section, 14 cross-section-countable, 0 un-anchored-uc)
- 5 prose-to-code mechanical divergences (all "claimed=50 tests, actual=631" — same SKILL.md prose phrase repeated across 5 sections)
- 0 execution divergences (expected per DQ-4-3)
- 0 LLM-judged divergences (A.3 deferred to Phase 5)
- 33 BUG records produced
- 1 source-fix discovered live during the run (A.2 regex `^def test_` → `^\s*def test_`)

### 8.5 Round 8 — three convergent findings

Council Round 8 reviewed Phase 4. Three reviewers, three convergent SHIP-WITH-FIXES verdicts:

1. **Stage 3 dedupe bug:** DIV-INT-016 and DIV-INT-017 are byte-for-byte identical except for `divergence_id`. Same root: `_COUNTABLE_RE.findall("...7 use cases ... 7 use cases")` returns the same `(value, noun)` token twice; the token-index loop emits 2 records for what should be 1.

2. **§8.1 consolidation:** the 5 prose-to-code BUGs all reference the same prose fragment ("35-50 tests"). Per `schemas.md §8.1` they should consolidate into 1 BUG with a 5-element `covers` array. The brief's Part D.1 explicitly cited §8.1 — this should have been done in Phase 4.

3. **PHASE4_SUMMARY.md test-count baseline wrong:** claims gate `pre=198, post=215`; verified is `pre=204, post=221`.

Phase 4 follow-up commit at `a42674a` landed all three fixes:
- Stage 3 dedupe (one-line + unit test)
- §8.1 consolidation in `divergence_to_bugs.py` (BUG-PHASE4-029 now carries `covers=[5 DIVs]`)
- PHASE4_SUMMARY.md count correction

Net: 855 tests green (+3); BUG count dropped from 34 to 29 (5 prose-to-code consolidated to 1, 1 internal-prose dropped from dedupe).

### 8.6 Detector precision — the calibration finding (carry-forward)

Both Opus and Sonnet independently analyzed the 29 internal-prose divergences and converged on the same finding: ~70% are likely false positives from semantic shadowing. The patterns:

- **Tier-N matches:** regex matches `\bN\s+req\b` against "Tier 1/2 REQ" — extracting the tier digit as if it were a REQ count.
- **Line-budget vs line-count:** "previous-run scan ~20-30 lines" vs "deep-reads ~40-60 lines" — different operations, not a contradiction.
- **Section list numbering:** SKILL.md's `1., 2., 3.` heading numbering triggering as countable `line` claims against genuine line-count guidance.
- **Output-minimum vs read-budget:** "EXPLORATION_ITER{N}.md must contain ≥80 lines" vs "read first 2-3 lines" — different concepts.

The 5 prose-to-code divergences are also FPs: the prose says "*typically yields* 35-50 tests *for a medium project (5-15 source files)*" — comparing against QPB's full corpus is a category error.

Root cause: the detector has no semantic grounding for whether two tokens reference the same noun-target, and no recognition of context-qualified claims (`typically`, `roughly`, `~`, parenthetical conditions).

The four-prong fix designed during Round 8 → Phase 5 brief drafting:
1. Skip ordinal-context numbers (preceded by `Tier`, `section`, `Phase`, numbered-list patterns).
2. Require artifact-name proximity for cross-section-countable matches (shared artifact-name token within ±100 characters).
3. Filter context-qualified claims (`typically|roughly|approximately|~|≈|about` within 30 characters before the number, or parenthetical condition `\([\d\-–]+\s+[a-z]+\s*(files?|projects?|sources?)\)` within ±50 characters).
4. Downgrade Stage 3 emissions to "candidate" status by default — give Council-as-low-confidence-flag (`provisional_disposition: null`, `subtype: "cross-section-countable-candidate"`), not BUG production.

Implementation deferred from Phase 4 follow-up to Phase 5 Stage 1 (see §9 below).

---

## 9. Phase 5 — Release readiness

Phase 5 was the consolidated release-readiness phase, including the precision fixes from Round 8 plus the original Implementation Plan's Phase 5 surface (cross-target validation, self-audit bootstrap, version bump, carry-forward cleanup, TTP, tag + push). 9 stages, 19 commits + 1 tag.

### 9.1 The eight stages

- **Stage 0 — CLI prerequisites:** Add `--phase 4`, `--part`, `--model` argparse flags to `bin/skill_derivation/__main__.py` (Pre-flight had caught this BLOCK; without these flags, every Stage 2/4 invocation would fail with argparse error).

- **Stage 1 — Detector precision:** Four-prong fix per Round 8 carry-forwards. Plus UC-PHASE3-17 anchor threshold tightening (require ≥3 overlapping tokens with at least 1 non-generic-English token; was 2 generic-English tokens), performance budget recalibration to 25,000 pairs, A.2 regex audit for other patterns, pytest vs unittest reconciliation (locked to unittest discover per DQ-5-8).

- **Stage 2 — Re-run self-audit + A.3 LLM live run:** With precision-fixed detectors, internal-prose divergences dropped from 28 → 11 (60% reduction); prose-to-code mechanical FPs filtered to 0 by hedge + parenthetical rules. A.3 LLM run on QPB: 8 candidates (vs 58 estimated), 4 llm-judged divergences, 42 seconds wall-clock.

- **Stage 3 — Schemas/code carry-forward cleanup:** schemas.md §10 invariant re-sequencing (#19-20 follow #18 sequentially with #21-23 after #20); `bin/classify_project.py` calibration anchor refresh (1.67× → 1.10× per current `--benchmark`); `_BENCHMARK_TARGETS` cobra-path snapshot pinned.

- **Stage 4 — Cross-target validation:** Per the brief's 9-cell matrix (5 code + QPB Hybrid + 3 pure skills + optional cross-version v1.4.5). Pragmatically deferred most of this to v1.5.3.1 (the brief authorized deferral for wall-clock budget). What landed: code-target snapshots captured for chi/virtio/express/cobra; 3 pure-skill cells (skill-creator, pdf, claude-api) classified correctly as Skill, ran cleanly through Phase 3 + Phase 4, produced 0 false-positive divergences.

- **Stage 5 — Self-audit bootstrap:** Curated REQUIREMENTS.md generation. The pipeline-produced 1,007 accepted REQs needed consolidation to reach the brief's [80, 110] target. Algorithm: group by section, Jaccard 0.6 dedup, K-cap iteration. Output landed at 171 REQs — over the target. Documented as a calibration finding (B-4 in v1.5.4 backlog): the algorithm hits a 171-floor on QPB because there are 171 partitions each with ≥1 distinct post-Jaccard REQ. Reaching [80, 110] requires cross-partition consolidation that the v1.5.3 algorithm doesn't specify.

- **Stage 6 — Version stamp bump:** All version stamps in one commit (DQ-5-3): `bin/benchmark_lib.py::RELEASE_VERSION` (1.5.2 → 1.5.3), `SKILL.md` `metadata.version` plus inline references, `schemas.md` banner, `README.md` v1.5.3 changelog entry.

- **Stage 7 — TTP pass:** Toolkit Test Protocol on orientation docs returned **Pass-With-Caveats**. Stage 6's actual changes (README + SKILL.md) were clean. Pre-existing forward-looking claims in `ai_context/TOOLKIT.md` (lines 494, 506, 575) and `ai_context/TOOLKIT_TEST_PROTOCOL.md` (Persona 13) about a v1.5.3 "categorization tagging" surface that did NOT ship were deferred to v1.5.4 backlog as B-13 + B-14 rather than blocking the release.

- **Stage 8 — Tag + push + verify:** Annotated tag `v1.5.3` created locally at SHA `99f649a3a92bc008fb1810ee35705edccc3b0f2a` pointing to commit `37dfe9c58bc2ac770c72db883583cc3e01930cfa`. Per the workspace verification rule (no claiming "shipped" without observing origin's state), pushed and verified via `git ls-remote origin refs/heads/1.5.3 refs/tags/v1.5.3`.

### 9.2 v1.5.3 ships

Verified on origin at 2026-04-27:

```
37dfe9c58bc2ac770c72db883583cc3e01930cfa	refs/heads/1.5.3
90757cb0ba9ce6eec1f7e21d294611226fd7b0f3	refs/tags/v1.5.3
```

The annotated tag dereferences to commit `37dfe9c`. Final test count at ship: 883 green (662 `bin/tests/` + 221 gate suite via unittest discover).

---

## 10. Post-tag refinements

After the v1.5.3 tag was on origin, three commits landed on the `1.5.3` branch HEAD without moving the tag. Per release discipline: tags don't move once published unless the change is purely reconciling docs to what shipped (and even then only if the tag has minimal exposure).

### 10.1 Orientation-doc cleanup (`facca1a`)

The TTP Pass-With-Caveats from Stage 7 surfaced forward-looking categorization-tagging claims in `ai_context/TOOLKIT.md` and `TOOLKIT_TEST_PROTOCOL.md` that did not actually ship in v1.5.3. Phase 5 deferred those to v1.5.4 backlog (B-13/B-14). The post-tag cleanup commit reconciled the docs: removed the forward-looking claims, added v1.5.3-actual-scope mentions, added Persona 19 (v1.5.3 skill-as-code adopter) to TOOLKIT_TEST_PROTOCOL.md, updated the lever inventory in IMPROVEMENT_LOOP.md to reflect `bin/skill_derivation/` as a new lever surface.

The tag stays at `37dfe9c`. The branch HEAD advances to `facca1a`. Standard practice for post-tag clarification commits.

### 10.2 Codex CLI runner addition (`b6b31f2`)

The OpenAI Codex CLI (https://github.com/openai/codex, v0.125+) added as a third LLM runner alongside Claude (`claude --print`) and GitHub Copilot (`gh copilot --prompt`). Codex's non-interactive mode is `codex exec --full-auto -m <model>` with prompt on stdin (codex exec reads stdin when no positional prompt is given). Default model is empty — codex picks from `~/.codex/config.toml`.

Touched 9 dispatch sites in `bin/run_playbook.py` (mutex group flag, command construction, availability check, orchestrator pass-through, error message), added `CodexRunner` to `bin/skill_derivation/runners.py`, extended `--runner` choices in `__main__.py`, added 7 unit tests.

Smoke test: `CodexRunner().run("Print HELLO and nothing else.")` → returns "HELLO" in 6 seconds, picks `gpt-5.5` from config. Tests at 890 green (+7).

### 10.3 Codex orientation update (`b9a5ff8`)

Updated orientation docs (README.md, AGENTS.md, ai_context/*) to reflect the three-runner reality — codex mentions added alongside claude/copilot in install/run instructions, lever 6 enumeration, persona-CLI examples, benchmark protocol's runner-choice section.

---

## 11. Cross-version harness contamination diagnosis

A separate operational thread: the `repos/replicate/` cross-version benchmark harness (used internally to build per-version run history toward statistical control) showed unexpected results when re-run.

### 11.1 The contamination signature

`cross_v1.5.0` cells (chi, express, casbin, virtio, cobra) all returned `bug_count=0` with suspiciously fast wall-clock (chi 41m, express 13m, casbin 28m). The `cross_v1.4.6` cells showed similar patterns. cross_v1.5.2 and cross_v1.5.1 had real bug counts (5-11 per cell) — those were uncontaminated.

Investigation of the actual run logs revealed: the runner self-marked the run-archive directories with a `-PARTIAL` suffix when required artifacts (BUGS.md, REQUIREMENTS.md) were missing at exit. The runner exited 0 anyway. The harness's success path counted `^### BUG-` in BUGS.md and got 0 (because BUGS.md didn't exist), then logged the run as `event:"completed"` with `bug_count=0`.

Root cause in the LLM behavior: copilot-cli running with v1.5.0 / v1.4.x SKILL.md prose hallucinated a "background agent" delegation. Phase 1 completed; phases 2-6 were "delegated to a background agent" that died with the parent session. The runner self-marked `-PARTIAL`, the harness recorded `completed; bug_count=0`, and the contamination silently entered the variance dataset.

### 11.2 The harness `-PARTIAL` detection patch

Added to both `replicate.sh` and `replicate_parallel.sh`: after `bin/run_playbook` exits 0, check for the `-PARTIAL` archive marker. If present, log `event:"partial"` with the marker path in the reason field. Cells without `event:"completed"` are auto-retried by the parallel script's pending-cell logic on next orchestrator run.

The patch is operational tooling under `repos/replicate/` (gitignored); not part of the release surface but committed to the working directory.

### 11.3 The setup_target.sh extension

A deeper diagnosis after a re-queue showed cross_v1.4.5 cells failing even faster — within 70 seconds across all 5 cells. The actual playbook log:

```
WARN: No SKILL.md found for ... — the playbook may not be installed there.
SKIP: replicate-1 - docs_gathered/ is missing or empty
=== Full run halted: main run reported failures; skipping iterations. ===
```

Root cause: `setup_target.sh:77` only copied `quality_gate.py` into the target's `.github/skills/` directory. It did NOT install SKILL.md, references/, agents/, or docs_gathered/. The runs worked to varying degrees by accident depending on each QPB version's tolerance for missing input:
- v1.4.5: BLOCK on missing `docs_gathered/` (correct, fails fast in ~1 min)
- v1.4.6: WARN + continue → 26-33 min run with 0 bugs (silent degraded output)
- v1.5.0+: runs but the LLM falls back to reading `~/Documents/QPB/SKILL.md` (workspace tip), creating the agent-delegation pattern

Patched `setup_target.sh` to install the full skill bundle (SKILL.md + references/ + LICENSE + gate + per-target `docs_gathered/`) from `QPB_DIR`. The orchestrator (`replicate_parallel.sh::checkout_qpb`) checks out `QPB_DIR` at the version-pinned tag before invoking `setup_target.sh`, so the installed SKILL.md matches the cell's `qpb_version`. Per-target `docs_gathered/` comes from the workspace's `repos/docs_gathered/<target>/` (not version-pinned — documentation is owned by the workspace).

Verified working on the first cross-version cell of the redo: the playbook log now shows three install lines confirming the full skill bundle is in place.

### 11.4 Companion `setup_repos.sh` improvements

Two commits to `setup_repos.sh` (the canonical benchmark setup script, tracked in git):

- **`33b9b53` — `--target-folder` and `--replace` flags:** Override default `repos/<repo>-<version>/` destination; safety guard requires `--replace` when overwriting a non-conventional target. Useful for ad-hoc cross-version harness setup.

- **`31954cc` — docs_gathered → reference_docs mirror:** The v1.5.2+ playbook reads documentation from `<target>/reference_docs/` via `bin/reference_docs_ingest.py`. setup_repos.sh historically populated only the legacy `<target>/docs_gathered/` location, leaving reference_docs/ as an empty cite/ scaffold. The mirror copies docs_gathered/ → reference_docs/ at the end of each setup, preserving any adopter-supplied files. Without this, curated documentation was invisible to Phase 1 and the playbook fell back to Tier 3 (source-only) review.

---

## 12. v1.5.3 wide-test (in progress)

After v1.5.3 ship + post-tag refinements, the wide test exercises v1.5.3's skill-as-code surface across multiple targets to validate end-to-end correctness.

### 12.1 First target — pdf (codex)

`pdf-1.5.3` ran end-to-end with codex+gpt-5.5. Result: **18 confirmed bugs** (6 HIGH, 12 MEDIUM) with regression tests + patches generated for each. 12 derived REQs. Bug yield from a 1K-word skill is high — comparable to or higher than typical code-target benchmarks (chi-1.5.1 typically produces 5-15 bugs).

The top three defects, by impact:

1. **BUG-001 (HIGH, SKILL.md:11):** Support file routing references missing uppercase paths. SKILL.md tells agents to load `REFERENCE.md` and `FORMS.md`, but the repository contains `reference.md` and `forms.md`. Breaks the skill completely on case-sensitive filesystems (Linux), works on macOS by accident.

2. **BUG-002 (HIGH, forms.md:3 + scripts/check_fillable_fields.py:7):** Fillable detector command broken at first contact. Documented command (`python scripts/check_fillable_fields <file.pdf>`) doesn't match the actual filename (`check_fillable_fields.py`), and the script reads `sys.argv[1]` at module top level → `IndexError` on no-arg call. Three failure modes in the user's first 30 seconds with the skill.

3. **BUG-014 (HIGH, scripts/extract_form_field_info.py:53):** Parent fields with widget kids silently dropped. Real-world PDFs (government forms, employer onboarding) commonly use hierarchical AcroForm structures where a parent text or choice field has multiple widget children. The current extraction silently drops them. Silent data loss.

The bugs are real, specific, mechanical, fixable. The methodology delivered.

### 12.2 codex CLI rate-limit

After pdf, codex ran out of usage credits when invoked on claude-api and skill-creator. Both targets failed at Phase 1 with OpenAI's quota error. The codex runner integration is correct (proved by pdf); the failures were on the user-quota side.

### 12.3 The wide-test plan with claude+opus

Switched to `claude --print --model opus` for the remaining 8-target wide-test (5 code targets via `setup_repos.sh chi cobra express virtio casbin` + 3 skills via `setup_repos.sh skill-creator pdf claude-api`, with `setup_repos.sh`'s mirror handling the docs_gathered → reference_docs correctly). Two parallel terminals, ~12-18h wall-clock, opus quota burn as a planned data point for v1.5.4 budgeting.

QPB self bootstrap deferred — to be run via codex interactive desktop app with a single prompt (separate from this wide-test).

---

## 13. v1.5.4 backlog

Items captured during v1.5.3 release-readiness as deferred to v1.5.4. The full list lives at `~/Documents/AI-Driven Development/Quality Playbook/Reviews/v1.5.4_backlog.md`. Notable items:

- **B-1 — Full playbook regression sweep on 5 code targets** (deferred from Stage 4A; Phase 5 captured pre-snapshot BUGS.md but didn't run the full re-run).
- **B-2 — Cross-model second backend (opus)** for the Design success criterion #4 cross-model consistency check (Stage 4D).
- **B-4 — Stage 5 curation 171-floor on QPB** (cross-partition consolidation work).
- **B-5 — Disposition-table degeneracy redesign** (Round 7 carry-forward — extend Pass A to admit "behavioral claim" categories OR redesign 6-branch table).
- **B-9 — Detector precision FP analysis** (additional shapes the four prongs don't catch; surfaced from the wide-test results).
- **B-13 / B-14 — Categorization tagging surface and orientation-doc release-cadence review** (TTP DOC-WRONG carry-forward; v1.5.4 should establish a release-gate review cadence for orientation docs).

---

## 14. Methodological lessons from v1.5.3

Three lessons that survived multiple Council rounds and are worth keeping:

### 14.1 Read the canonical doc before authoring planning content

The 2026-04-26 v1.5.3 misfire happened because Cowork Claude treated system-reminder pre-loaded files as a complete picture and never searched `docs/design/` for the canonical version doc. The workspace `CLAUDE.md` rule has been load-bearing since: any planning doc that references "per IMPROVEMENT_LOOP.md" or "per the work items in $LATER_FILE" without citing `docs/design/` line numbers is suspect.

### 14.2 Verify before claiming shipped

The 2026-04-26 README-not-pushed incident and the Round 7 UC-PHASE3-17 `_metadata` tag finding are the same failure mode: confidence-in-claim without observation-of-state. The workspace `CLAUDE.md` rule: don't say "shipped" / "pushed" / "tagged" without `git ls-remote origin <ref>` confirmation. Don't say "the test passed" without seeing test output. Generalizes to any external state.

### 14.3 Sub-agent pre-flight catches real BLOCKs

Every Phase 4+ brief went through sub-agent pre-flight before Claude Code launch. Both Phase 4 (gate_check_ids non-existence; triage_batch_key uncomputable) and Phase 5 (CLI flags missing; baseline data missing; target paths broken; curation algorithm under-specified) had real BLOCKs caught during pre-flight that would otherwise have failed Claude Code mid-run. The cost of pre-flight (one or two sub-agent reviews per brief) is small compared to the cost of failed Claude Code sessions.

---

## 15. Artifacts and where to find them

- **Source code:** `bin/skill_derivation/`, `bin/classify_project.py`, `bin/citation_verifier.py`, `.github/skills/quality_gate/quality_gate.py`
- **Design docs:** `docs/design/QPB_v1.5.3_Design.md`, `docs/design/QPB_v1.5.3_Implementation_Plan.md`, `docs/design/QPB_v1.5.3_Phase4_Council_Override_Workflow.md`
- **Bootstrap evidence:** `previous_runs/v1.5.3/` (29 files including curated REQUIREMENTS.md, full pass_a/b/c/d output, pass_e divergence files, partition density warnings, PHASE3B/PHASE4/PHASE5 summaries)
- **Council reviews and briefs:** `~/Documents/AI-Driven Development/Quality Playbook/Reviews/QPB_v1.5.3_*.md`
- **v1.5.4 backlog:** `~/Documents/AI-Driven Development/Quality Playbook/Reviews/v1.5.4_backlog.md`
- **Tag:** `v1.5.3` (annotated, SHA `90757cb`) → commit `37dfe9c`

---

## 16. Open work (post-v1.5.3 ship)

In flight as of 2026-04-28:

- **v1.5.3 wide-test** with claude+opus — 5 code targets + 3 skills, two parallel terminals, results pending.
- **Cross-version harness redo** with patched `setup_target.sh` — cross_v1.5.0 / 1.4.6 / 1.4.5 / 1.5.2 plans re-queued with version-pinned skill bundle install. Wall-clock ~22-26h.
- **awesome-copilot PR #1402** — closed as superseded; fresh v1.5.3 PR pending after wide-test results land.
- **QPB bootstrap with codex desktop app** — deferred until wide-test results land.

After the wide-test produces real cross-runner data (codex pdf vs claude+opus pdf, claude+opus on the other 7 targets), v1.5.3 has its broad validation evidence. The cross-version harness redo produces fresh data for statistical-control history. The awesome-copilot PR distributes v1.5.3 to a wider audience.

v1.5.4 begins after v1.5.3 wide-test results are in.

---

*End of journal. v1.5.3 shipped 2026-04-27 at tag `v1.5.3` → commit `37dfe9c`.*
