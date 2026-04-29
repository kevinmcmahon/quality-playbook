# Quality Playbook v1.5.4 — Implementation Plan

*Companion to: `QPB_v1.5.4_Design.md`*
*Status: scope expanded 2026-04-28 — Phases 1-3 added in front of original Phases 1-N (renumbered as 4-7) for the Part 1 classification redesign.*
*Depends on: v1.5.3 complete (skill-as-code feature work tagged and shipped); v1.5.0/v1.5.1/v1.5.2 stable; benchmark replicate harness operational at `repos/replicate/`*

---

## Operating Principles

- v1.5.4 has **two parts**. **Part 1 (Phases 1-3)** is the classification redesign — AI-driven file role tagging during Phase 1 exploration, replacing v1.5.3's mechanical Code/Skill/Hybrid trichotomy. Part 1 DOES touch `bin/run_playbook.py` and changes the v1.5.3 four-pass pipeline's input shape; that's expected scope. **Part 2 (Phases 4-7)** is the original v1.5.4 apparatus work — `bin/regression_replay.py`, the schema, the calibration cycles. Part 2's discipline (no `SKILL.md` / `references/*.md` edits unless absolutely required) still applies; Part 1 carries narrower discipline (classifier and exploration prompt changes only — the four-pass pipeline itself stays unchanged, only its file-set selection moves).
- The apparatus must be usable for v1.6.0+ continuous improvement. That means: stable schema, deterministic replay (or at least: known noise floor with σ-aware comparison), recoverable across machine reboots (state in `metrics/regression_replay/` is append-only).
- Every calibration cycle is its own commit so the calibration log builds incrementally and each entry is reviewable in isolation.
- Validation before claiming a cycle. A cycle isn't "documented" until the apparatus can rerun it from `cell.json` and produce the same recall delta within σ.

---

## Phase 0 — v1.5.3 Stabilization Confirmation

Goal: confirm v1.5.3 is shipped, tagged, validated against the code-project benchmark suite AND against QPB's self-audit (skill-as-code work). The 1.5.4 branch is fresh from main with v1.5.3's tagged commit as its base. Disposition all v1.5.3 bootstrap bugs (BUG-001..BUG-011 from the 2026-04-28 codex+opus self-audit).

Work items:
- v1.5.3 tag exists on origin
- chi-1.5.1, virtio-1.5.1, express-1.5.1 v1.5.3 benchmark yields documented as the v1.5.4 baseline (within ±10% of v1.5.2 baseline; new skill-related findings on QPB's self-audit don't count toward code-project regression)
- QPB self-audit run with v1.5.3 produced ≥80 REQs structured phase-by-phase (success criterion 1 from `QPB_v1.5.3_Design.md`)
- 1.5.4 branch created from main at the v1.5.3 tag's parent or merge base
- Each of the 11 v1.5.3 bootstrap bugs has a disposition: `fix-in-Phase-1`, `fix-in-Phase-2`, `fix-as-stabilization-commit-before-Phase-1`, `fix-deferred-to-v1.6.0`, or `won't-fix-with-rationale`. The classification-related bugs (L1/L2/L3 — see Design Part 1) are subsumed by Phase 1's redesign rather than fixed independently.

Gate to Phase 1: all of the above confirmed; every v1.5.3 bug has a disposition; `1.5.4` branch is fresh.

---

## Phase 1 — Classification Redesign (Part 1)

Goal: replace v1.5.3's mechanical Code / Skill / Hybrid classifier with AI-driven file-by-file role tagging integrated into Phase 1 exploration. Per Part 1 of the Design.

Work items:
- **Update Phase 1 exploration prompt in `bin/run_playbook.py`** so it:
  - Reads SKILL.md (and any other top-level skill-shaped entry file) first if present
  - For each file in the tree (respecting existing ignore conventions), emits a role tag from the role taxonomy (`skill-prose`, `skill-reference`, `skill-tool`, `code`, `test`, `docs`, `config`, `fixture`, `formal-spec`, etc.)
  - Writes `quality/exploration_role_map.json` with the per-file tagging plus a top-level breakdown (`{skill-prose: N, skill-tool: M, code: K, ...}` and percentages)
  - For `skill-tool` files specifically, records the SKILL.md prose reference (which section / line invokes the script) so prose-to-code divergence checks can find it later.
- **Replace `target_project_type` in INDEX.md schema** with `target_role_breakdown` populated from the role map. The single-string `Code|Skill|Hybrid` field is removed from `write_live_index_stub()` and `write_live_index_final()`.
- **`bin/classify_project.py` becomes a debug utility**, not part of the run path. Document this in its module docstring. The `--override` / `--override-rationale` flags can stay for ad-hoc classification overrides during Council review (per v1.5.3 Phase 4 Part E).
- **Update `bin/skill_derivation/pass_c.py`** to consume the role map instead of `project_type.json` (read `quality/exploration_role_map.json`; activate the four-pass pipeline if any file is tagged `skill-prose` or `skill-reference`).
- **Update `quality_gate.py`** skill-side checks to read the role map; the existing `target_project_type == "Skill"` gate condition becomes "any `skill-prose` files present in role map."

Test fixtures:
- pdf clean / docs_gathered (currently misclassified as Hybrid by mechanical classifier; should role-tag as primarily skill-prose with skill-tool helper scripts)
- 3 pure-Markdown skills: schedule, consolidate-memory, setup-cowork (should role-tag as 100% skill-prose)
- QPB self-audit at v1.5.4 (should role-tag with both skill-prose and code surfaces)
- 5 code benchmarks: chi-1.5.1, virtio-1.5.1, express-1.5.1, cobra-latest, casbin-latest (should role-tag as ~100% code; no skill-prose)

Deliverable: role-tagging integrated into Phase 1; mechanical classifier deprecated to debug-utility status; INDEX.md schema migrated to `target_role_breakdown`; all consumers (skill-derivation, gate) read the role map.

Gate to Phase 2: role tagging produces correct breakdowns on all test fixtures; v1.5.3-style code benchmarks produce identical role breakdowns (~100% code) and match v1.5.3 baseline yields when run end-to-end (no regression on pure-code targets).

---

## Phase 2 — Pipeline Wiring (Part 1)

Goal: thread the role map through the four-pass skill-derivation pipeline and the code-review pipeline so each runs against its appropriate file set. Update divergence detection (Phase 4 of v1.5.3 plan) to consume the role map.

Work items:
- **Four-pass skill-derivation pipeline** reads files tagged `skill-prose` and `skill-reference` from the role map; runs Pass A through Pass D over them in section-iterative order
- **Code-review pipeline** reads files tagged `code`; runs the existing Phase 1-3 code path over them
- **Prose-to-code divergence check** (from v1.5.3 Phase 4 Part A) reads files tagged `skill-tool`, looks up their SKILL.md references (recorded by Phase 1 of this plan), and runs the existing static-divergence detection — does the SKILL.md claim about the script match what the script actually does?
- **Empty side runs no-op cleanly.** When role breakdown shows 0 `skill-prose` files, the four-pass pipeline doesn't even start (no error, no false-positive findings). When 0 `code` files, the code-review pipeline no-ops. When 0 `skill-tool` files, the prose-to-code divergence check no-ops. Each gate condition is explicit; no implicit "if Skill mode then..." branches remain.
- **Update phase-gating logic** in `run_playbook.py` to consume the role map for routing decisions instead of `target_project_type`.

Deliverable: both pipelines consume the role map; downstream phases (v1.5.3 Phase 4 divergence detection, v1.5.3 Phase 5 release readiness) operate against the role-tagged inventory.

Gate to Phase 3: pdf wide-test rerun produces non-zero output from the four-pass pipeline (the test that v1.5.3 failed); all five code benchmarks produce identical bug yields to v1.5.3 (no regression on pure-code targets); QPB self-audit role breakdown surfaces both skill and code surfaces and runs both pipelines.

---

## Phase 3 — Validation (Part 1)

Goal: prove the classification redesign works on the validation set; close out Part 1.

Work items:
- **Re-run pdf wide-test** under v1.5.4. Expect ≥3 category-A skill-divergence findings (compared to v1.5.3's 1 of 12).
- **Wide-test schedule, consolidate-memory, setup-cowork.** Each should produce a non-zero formal REQ count from Pass C.
- **QPB self-audit at v1.5.4.** Role breakdown should surface both skill and code surfaces; REQ count should be at parity with the v1.5.3 Haiku-benchmark target (95 REQs ±20%, structured phase-by-phase).
- **Code-benchmark non-regression check.** chi-1.5.1, virtio-1.5.1, express-1.5.1 produce yields within ±10% of v1.5.3 baseline.
- **Council-of-Three review** on Phase 1-3 work (the redesigned classifier + pipeline wiring). Uses the standard nested-panel protocol from `~/Documents/AI-Driven Development/CLAUDE.md`. Ship verdict required to advance to Phase 4.

Deliverable: validation report at `quality/v1.5.4_part1_validation_report.md` documenting all five validation outcomes plus Council verdict.

Gate to Phase 4: all five validation criteria pass; Council ship verdict on Phase 1-3 work.

---

## Phase 4 — Schema First (Part 2)

Goal: write `metrics/regression_replay/SCHEMA.md` before any automation work. The schema constrains the apparatus; designing the apparatus first and the schema second produces silently-incompatible cell records.

Work items:
- Create `metrics/regression_replay/SCHEMA.md` documenting every field of a cell record
- Field inventory at minimum: `schema_version`, `timestamp`, `benchmark`, `qpb_version_under_test`, `historical_qpb_version`, `historical_bug_id`, `historical_bug_count`, `current_bug_count`, `recall_against_historical`, `lever_under_test`, `lever_change_summary`, `before_lever`, `after_lever`, `regression_check`, `noise_floor_source`
- Define types and semantics for each field
- Define the cell-record file path convention: `metrics/regression_replay/<timestamp>/<benchmark>-<version>-<bug>.json`
- Define the calibration-log entry shape (a markdown section per cycle, citing the cell record(s) it summarizes)

Deliverable: SCHEMA.md committed; field set frozen for v1.5.4 (changes go to v1.5.4.1 patch or v1.5.5+ via versioned schema bump).

Gate to Phase 5: schema is internally consistent (fields don't contradict), Council-reviewable as a standalone document, and includes at least one example record demonstrating every field populated.

---

## Phase 5 — Build `bin/regression_replay.py` Against ONE Cell

Goal: get the apparatus working end-to-end on the easiest possible cell, then iterate. Don't optimize for elegance; correctness first.

Smoke-test cell: chi at v1.3.45, BUG-001 (or whichever is first in the v1.3.45 BUGS.md). Small benchmark, well-understood, recall delta is large (10 → 0 collapse to v1.3.46), so noise floor isn't load-bearing yet.

Work items:
- Implement target-checkout: given (benchmark, version), determine the upstream commit immediately before the bug's fix landed (use BUGS.md `Commit:` field if present, otherwise `git log` for the fix and use the parent commit)
- Implement skill-installation: copy current QPB skill installation (SKILL.md, references/, agents/, quality_gate.py) into the target's `.github/skills/` or `.claude/skills/` per the install-locations contract
- Implement scoped playbook run: invoke `bin/run_playbook.py` with reduced phase scope (`--phase 1,2,3` likely; verify with smoke test) — full iterations are overkill for replay
- Implement BUGS.md parser: re-use existing parser machinery if present, otherwise mechanical heading extraction
- Implement recall calculator: count `### BUG-NNN` headings in the produced BUGS.md, match against the historical bug-ID set, compute recall percentage
- Implement cell.json writer: serialize per the schema, write to `metrics/regression_replay/<timestamp>/<benchmark>-<version>-<bug>.json`

Deliverable: `bin/regression_replay.py` runs end-to-end on the chi-1.3.45 smoke cell, produces a valid cell.json matching SCHEMA.md.

Gate to Phase 6: smoke cell completes; cell.json validates against SCHEMA.md; recall calculation is correct (manually verified against the BUGS.md output).

---

## Phase 6 — First Calibration Cycle Manually

Goal: don't optimize the automation until you've done at least one cycle by hand and seen what data you actually need. The automation should serve the cycle, not the other way around.

Cycle 1: chi-1.3.45 → 1.3.46 collapse.

Work items:
- Run the smoke-test apparatus from Phase 5 against chi at v1.3.46 (post-collapse) and confirm current QPB recovers far less than the v1.3.45 10-bug list
- Diagnose: read v1.3.45 BUGS.md, identify the categories of bugs current QPB misses, hypothesize which lever in `IMPROVEMENT_LOOP.md` (Levers 1-5) is the diagnosis
- Pull the lever (typically a prompt-side change in `references/exploration_patterns.md` or `references/iteration.md`)
- Re-run the apparatus on chi-1.3.46 with the lever change in place
- Verify recall improvement on chi-1.3.46
- Verify NO regression on chi-1.5.1, virtio-1.5.1, express-1.5.1 (cross-benchmark regression check)
- Document the cycle in a new file `Quality Playbook/Reviews/Lever_Calibration_Log.md` with: bug missed (specific BUG-IDs), lever pulled, before/after recall on chi-1.3.46 AND on the broader benchmark set, diagnostic-reasoning narrative

Deliverable: Lever_Calibration_Log.md with one complete cycle entry; cell.json files in `metrics/regression_replay/<timestamp>/` for both before and after the lever change.

Gate to Phase 7: cycle is reproducible (re-running the apparatus from the cell.json's parameters produces the same recall delta within σ); the diagnostic narrative survives Council review for soundness.

---

## Phase 7 — Iterate Cycles 2-5

Goal: each cycle teaches you something about the data shape, the lever inventory, or the diagnosis loop. Update the apparatus incrementally as you go.

Candidate cycles (from the design doc, in order of priority):
- Cycle 2: virtio-1.3.47 → 1.3.50 drop
- Cycle 3: express-1.3.50 single-version peak recovery
- Cycle 4: express options-mutation bug from naive-review experiment
- Cycle 5: casbin-1.4.4 outlier

Work items per cycle (same shape as Cycle 1):
- Run apparatus on the historical pre-fix commit
- Diagnose missed bug class
- Pull lever
- Re-run apparatus
- Verify cross-benchmark non-regression
- Document in Lever_Calibration_Log.md

Cross-cycle work items:
- If a cycle requires a new lever (one not in the existing 5-lever inventory), document it as a v1.6.x candidate in the calibration log AND in `IMPROVEMENT_LOOP.md` "Adding new levers" subsection — but DO NOT expand the inventory in v1.5.4.
- If a cycle reveals an apparatus deficiency (the schema can't capture some relevant fact, the regression check missed a benchmark side-effect), update the apparatus AND bump the schema version if the fix is breaking.
- If a cycle fails to recover the missed bug despite multiple lever-pull attempts, that's a real result. Document it in the calibration log as "lever-pull search failed; see narrative." This is honest data, not a defect.

Deliverable: Lever_Calibration_Log.md with 3+ documented cycles (success criterion 3 from the design doc).

Gate to Phase 8: 3+ cycles documented; apparatus has been used end-to-end multiple times; any apparatus deficiencies surfaced during cycles are addressed.

---

## Phase 8 — Cross-Benchmark Regression Check Hardening

Goal: validate that the apparatus catches the failure mode where a lever pull improves the targeted benchmark but harms another.

Work items:
- Construct a deliberately-bad lever pull (e.g., a prompt change that helps chi but explicitly hurts virtio's pattern coverage)
- Run the apparatus with the deliberately-bad lever pull
- Confirm the cell.json's `regression_check` field reports the failure
- Confirm the apparatus refuses to declare the cycle successful when the regression check fails
- Document this validation as a final calibration-log entry (or as a separate validation note)

Deliverable: a documented failure case showing the regression check works.

Gate to Phase 9: validation passes; the apparatus reliably distinguishes "real lever improvement" from "lever pull that helps one benchmark while breaking another."

---

## Phase 9 — IMPROVEMENT_LOOP.md Update

Goal: update the methodology doc to reflect that the apparatus is now operational.

Work items:
- Update the "Regression replay (lever calibration runs)" section's last paragraph: replace "the v1.5.4 deliverable" with "operational as of v1.5.4."
- Update the "Measurement and statistical control" trajectory: mark Stage B (regression-replay automation) as complete; note that Stage C (continuous lever-pull improvement, the v1.6.0 workflow) becomes the next target.
- Add a new subsection or appendix linking to `Lever_Calibration_Log.md` so adopters can navigate to the worked examples.
- Run the Toolkit Test Protocol against the updated doc per the orientation-doc release-gate convention.

Deliverable: IMPROVEMENT_LOOP.md updated, TTP-reviewed, committed.

Gate to Phase 10: TTP returns a Pass or Pass-With-Caveats verdict; no broken references or stale claims.

---

## Phase 10 — Benchmark Confirmation and Release

Goal: confirm v1.5.4 hasn't accidentally regressed the playbook itself; tag and release.

Work items:
- Run chi-1.5.1, virtio-1.5.1, express-1.5.1 with v1.5.4 HEAD; compare yields against v1.5.3 baseline. Within ±10% is the gate.
- QPB self-audit with v1.5.4: REQ count and structure should be unchanged from v1.5.3 (apparatus work doesn't change the skill itself).
- Tag v1.5.4 on the 1.5.4 branch; push tag to origin; verify with `git ls-remote origin v1.5.4`.
- Update README with v1.5.4 changelog entry.
- Update `bin/benchmark_lib.py::RELEASE_VERSION` to "1.5.4" and SKILL.md `version:` stamps accordingly. (The C13.11 cleanup work from the misfire branch may need to be re-applied to the fresh 1.5.3 branch first; if so, the RELEASE_VERSION constant exists and the bump is one line. If not, the RELEASE_VERSION constant is added in this phase.)

Deliverable: v1.5.4 tagged, pushed, README updated, version stamps refreshed.

Gate to release: code-project benchmarks pass; v1.5.4 tag confirmed on origin via `git ls-remote`.

---

## Council Review Scope

Each phase ends with its own commit; Council reviews happen in batches. Suggested grouping:

- **Round 1 (after Phase 2):** Review SCHEMA.md + smoke-test apparatus. Specifically: does the schema capture enough to detect bug recovery AND cross-benchmark regression? Is the smoke cell's behavior reproducible?
- **Round 2 (after Phase 4):** Review the calibration log entries. Specifically: are the cycles documented well enough that someone else could reproduce the diagnosis? Does the recall measurement methodology survive scrutiny?
- **Round 3 (after Phase 6):** Review the IMPROVEMENT_LOOP.md update via TTP, and review the apparatus end-to-end via Council if any code changed since Round 2.

---

## Out of Scope (Defer to v1.5.4.x or v1.6.x)

- Replay automation for full iteration strategies (v1.5.4 scopes to phases 1-3 only)
- Cross-model replay (running cycles against different LLM backends)
- Variance estimation as part of the apparatus (the harness produces variance separately; v1.5.4 consumes σ as input via `noise_floor_source`)
- New benchmark targets
- New lever-inventory items as part of the v1.5.4 deliverable

---

## Dependencies and Risks

**Dependencies:**
- v1.5.3 must ship first.
- v1.5.2_pinned_variance σ data helpful for noise-floor handling but not blocking (large recall deltas — chi 10 → 0 — are far outside any plausible noise floor).
- Naive-review results at `repos/replicate/naive-review/targets/<target>/quality/` are useful as Cycle 4 input.

**Risks (from the design doc, restated):**
- The historical regression isn't actually a regression; it was noise. Mitigation: only use cycles where the recall delta is >2σ from the within-version variance estimate, OR where the bug list documents *specific* bugs missing (not just lower counts).
- Lever adjustments improve the regression-replay benchmark but harm field performance. Mitigation: every cycle must include a cross-benchmark recall regression check before declaring success (this is what Phase 5 validates).
- Regression replay is not deterministic — different LLM responses across runs. Mitigation: pin model + run each replay 3 times, report median recall. Adds compute but produces honest measurements.
- "The lever I think I need to pull" turns out to not be the actual lever. This is fine and expected — that's why the diagnostic reasoning is documented, including dead ends.
