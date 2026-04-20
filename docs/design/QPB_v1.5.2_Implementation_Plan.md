# Quality Playbook v1.5.2 — Implementation Plan

*Companion to: `QPB_v1.5.2_Design.md`*
*Status: draft — to be reviewed and updated after v1.5.0 ships*
*Depends on: v1.5.0 complete (schemas.md, tier system, citation verification, disposition field all in place)*

This plan is deliberately more provisional than the v1.5.0 plan. v1.5.0's implementation will surface real constraints (what the schema actually looks like, how the citation gate actually behaves, where the orchestrator's extension points actually are) that will affect how v1.5.2 builds on top. This document captures the intended shape; it should be revisited and refined once v1.5.0 is stable.

---

## Operating Principles

- v1.5.2 builds on v1.5.0, doesn't replace it. The code-project path remains primary; skill-project handling is additive.
- Every phase produces a concrete deliverable that can be committed and benchmarked independently.
- The Haiku-generated REQUIREMENTS.md is the success benchmark throughout. At every phase, compare QPB's self-audit output against it.
- No regression on code projects. The five code benchmark repos must continue to work.

---

## Phase 0 — v1.5.0 Stabilization

Goal: v1.5.0 is shipped, tagged, and running clean on all five code benchmark repos. No outstanding gate failures. Benchmark yields documented as v1.5.2 baseline.

Work items:
- All v1.5.0 phases complete per `QPB_v1.5.0_Implementation_Plan.md`
- v1.5.0 tagged and released
- Benchmark baselines captured in `previous_runs/v1.5.0/`

Gate to Phase 1: v1.5.0 self-audit passes cleanly; no pending v1.5.0 bugs without dispositions.

---

## Phase 1 — Project Type Classifier

Goal: implement the Phase 0 project-type classification step that determines Code / Skill / Hybrid.

Work items:
- Add a `classify_project.py` module (or equivalent) that runs before Phase 1
- Heuristic implementation:
  - Check for SKILL.md at repo root
  - Count SKILL.md prose word count vs. total code LOC across repo
  - Check for orchestrator markers (`bin/`, runners, validators)
- Output: `quality/project_type.json` with classification + confidence + rationale
- Classification is writable by the Phase 4 Council if the heuristic is wrong

Test fixtures needed:
- A pure Skill project (prose-only SKILL.md, no orchestrator). If none exists in the benchmark, create a minimal one. Candidate: a stripped-down version of one of the example skills in `AI-Driven Development/Articles/Research/` if any exist, otherwise a synthetic fixture.
- Verify all five code benchmarks classify as Code
- Verify QPB itself classifies as Hybrid

Deliverable: classifier module, project_type.json output, test fixtures, classification verified on entire benchmark suite.

Gate to Phase 2: classification is correct on all known-type projects (5 code, 1 skill fixture, 1 hybrid).

---

## Phase 2 — Schema Extensions

Goal: extend `schemas.md` (from v1.5.0) to support skill-specific concepts without breaking code-project usage.

Extensions needed:
- `REQ.source_type` field: {code-derived, skill-section, reference-file, execution-observation}
- `REQ.skill_section` field: populated when `source_type = skill-section`, names which SKILL.md section the REQ came from
- `BUG.divergence_type` field: {code-spec, internal-prose, prose-to-code, execution}
- `FORMAL_DOC.role` field: {external-spec, project-spec, skill-self-spec, skill-reference}
  - `skill-self-spec` applies when SKILL.md is its own formal document (Skill/Hybrid projects)
  - `skill-reference` applies to files like `exploration_patterns.md`

Precedence rule for Skill/Hybrid: when SKILL.md (skill-self-spec) and a reference file (skill-reference) conflict, SKILL.md wins. This is documented in `schemas.md` as an explicit precedence rule, not left implicit.

Deliverable: updated `schemas.md` with new fields, updated validation in quality gate, no regression on code-project runs.

Gate to Phase 3: all five code benchmark repos pass the updated gate with no changes to their artifacts.

---

## Phase 3 — Skill-Specific Derivation Pipeline (Generate-Then-Verify)

Goal: implement the four-pass derivation architecture for skill projects.

The pipeline separates coverage breadth (Pass A) from citation precision (Pass B–C) from accountability (Pass D). Each pass has a narrow, specific job and a clear contract with the next.

### Pass A — Naive Coverage

- Prompt modeled on the Haiku session: "Read the skill, understand what it does, produce a comprehensive requirements document organized by functional area with testable acceptance criteria."
- Output format: machine-parseable list of draft REQs, each with `title`, `description`, `acceptance_criteria`, and `proposed_source_ref` (free-text like "Phase 1 section of SKILL.md")
- **Constraint: Pass A MUST NOT produce `citation_excerpt` values.** It can propose source references but not excerpts. Enforced structurally in the output schema (no `citation_excerpt` field).
- Prompt engineering: reuse language from the Haiku session that produced the 95-REQ output. Calibrate against Haiku's output structure.

### Pass B — Citation Extraction

- For each draft REQ from Pass A, mechanically search SKILL.md and reference files for supporting text
- Implementation: grep-based matching on the `acceptance_criteria` field, with fuzzy matching (stemming, tokenization) for robustness
- Populates `citation_excerpt` where found, `citation_status = verified`
- For drafts where no supporting text found: `citation_status = unverified`, flagged for Pass C to decide
- Reuse v1.5.0's citation extractor — no new machinery

### Pass C — Formal REQ Production

- Convert each cited draft into a proper REQ record with tier, ID, full v1.5.0 citation schema
- Disposition logic:
  - `citation_status = verified` → promote to Tier 1, full REQ record
  - `citation_status = unverified`, source is SKILL.md or reference file → Council review; either drafted Pass A overreach (reject) or citation extractor missed it (manual citation or second extraction attempt)
  - `citation_status = unverified`, claim is behavioral (not from any doc) → demote to Tier 5 (inferred), note that no documentation supports it

### Pass D — Coverage Audit

- Produce a diff report: Pass A draft list vs. Pass C formal REQ list
- Every Pass A draft that didn't make it to Pass C must have a recorded rejection rationale
- Output: `skill_coverage_audit.json` with three sections: `promoted` (A→C), `rejected` (with rationale), `demoted_to_tier_5` (with note)
- Flagged for Phase 4 Council if rejection rationale is weak or rejection rate > 30%

### Reference-File Coverage

- Passes A-D repeat over each file in `references/` (or equivalent)
- Cross-reference detection: where SKILL.md names a reference file, extract the reference's actual content and compare claims
- Contradictions flagged as internal divergences (handled in Phase 4 of this plan)

### Completeness Audit

- Every operational section of SKILL.md must produce at least one REQ after Pass D
- Meta sections (Why This Exists, Overview, etc.) are exempt — maintained in a small allowlist
- Orphan sections flagged for Phase 4 Council review

Tuning: distinguishing "operational" from "meta" sections requires prompt engineering. Iterate against QPB's own SKILL.md until orphan set matches human judgment.

Deliverable: four-pass skill-derivation code path with explicit output at each stage, applied to QPB's self-audit, compared to Haiku benchmark.

Gate to Phase 4:
- Pass A draft count within 10% of Haiku's REQ count (coverage parity check)
- Pass C formal REQ count within 50% of Haiku's 95 REQs (intermediate gate; full parity comes after Phase 4)
- Pass D rejection rate documented; every rejection has rationale
- Same 10 use cases covered as Haiku (may have different IDs)

---

## Phase 4 — Internal and Prose-to-Code Divergence Detection

Goal: implement static divergence checks for skills.

Work items:
- Internal divergence: for each pair of REQs citing the same document, check if their `citation_excerpt` content supports compatible claims. Contradictions flagged as bugs with disposition `spec-fix`.
- Prose-to-code divergence: for Hybrid projects, scan SKILL.md claims that reference code (e.g., "quality_gate.py runs 45 checks") and cross-check against the actual code. Tool: the Phase 4 Council gets the REQ + the referenced code region + asks "does the code match the prose claim?"
- Output: bugs with `divergence_type = internal-prose` or `prose-to-code`
- Dispositions populated by the Council, not auto-assigned

Test fixtures:
- A SKILL.md with a deliberate internal contradiction (two sections disagreeing on artifact count)
- A Hybrid project with a deliberate prose-to-code divergence

Deliverable: divergence detection implemented, verified on fixtures, verified on QPB's actual self-audit (may find real bugs).

Gate to Phase 5: fixtures correctly flagged; any real divergences found on QPB are triaged (either fixed or dispositioned as known/deferred).

---

## Phase 5 — Execution Divergence Infrastructure

Goal: implement the third divergence category — comparing SKILL.md promises against observed behavior in prior runs — by aggregating existing `quality_gate.py` results across archived runs.

**Scope boundary (strict):** this phase does NOT build an LLM evaluation harness. It does NOT parse unstructured LLM outputs, grade intermediate reasoning, or evaluate semantic quality. It consumes existing structured gate results and recognizes patterns across them. If the work starts drifting into "grading LLM outputs," stop and re-scope.

Work items:
- Gate result loader: read `quality_gate.py` output files from each archived run in `previous_runs/`
- REQ-to-gate-check mapper: for each skill REQ (derived in Phase 3 from SKILL.md sections), identify which gate check(s) implement it. Mapping is authored explicitly in the REQ record, not inferred.
- Pattern aggregator: for each REQ, count pass/fail rate of its associated gate checks across all archived runs
- Divergence reporter: flag REQs where the associated gate check failed in ≥1 of the last K runs (K = 5 by default)
- Output: bugs with `divergence_type = execution`, citing the SKILL.md REQ, the associated gate check, and the archived run IDs where the check failed

What this explicitly does NOT do:
- Does not parse LLM output prose for quality
- Does not re-run any archived runs
- Does not evaluate whether gate-passing runs are "actually good"
- Does not produce statistical confidence intervals on LLM behavior

Confidence handling: a REQ whose gate check failed in 1 of 5 runs is a lower-urgency flag than one that failed in 5 of 5. Failure count reported in the bug record. Gate does not auto-reject on low-failure-count findings but surfaces them for Council review.

Minimum run threshold: if fewer than 3 prior runs exist, execution divergence check runs with a confidence caveat in the bug record. With 0 prior runs, the check is skipped entirely.

Deliverable: execution divergence module scoped strictly to gate-result aggregation, tested against QPB's archived previous_runs, findings triaged.

Gate to Phase 6: at least one real execution divergence surfaced from QPB's bootstrap history (expected based on v1.4.x self-audits known to have had gate failures on skill-related checks).

---

## Phase 6 — Quality Gate Updates

Goal: quality_gate.py enforces skill-project requirements.

New checks to add:
- Skill/Hybrid projects: every operational SKILL.md section has at least one REQ citing it
- Skill/Hybrid projects: every reference file has at least one REQ or is explicitly marked as non-normative
- Hybrid projects: cross-cutting REQs that span SKILL.md and code both populate
- All projects: project_type.json exists and matches actual repo layout

Failure modes output specific file+section references so fixes don't require re-running the full playbook.

Deliverable: updated quality_gate.py, test fixtures for each new failure mode, no regression on code projects.

Gate to Phase 7: gate correctly flags deliberately-broken skill fixtures; all five code benchmarks still pass.

---

## Phase 7 — Full Benchmark Validation

Goal: run v1.5.2 against all five code benchmark repos AND against QPB itself (Hybrid) AND against the skill test fixture (pure Skill).

Expected outcomes:
- **Code projects** (virtio, chi, cobra, express, httpx): bug yields within ±10% of v1.5.0 baseline. No new false positives from skill-specific checks (they shouldn't fire).
- **QPB self-audit** (Hybrid): REQ count and structure at parity with Haiku benchmark (within ±20% of Haiku's 95 REQs, same 10 UCs in some form). Real skill-related bugs surfaced and triaged.
- **Pure skill fixture**: clean run. Section-to-REQ mapping produces expected structure.
- Cross-model consistency: repeating self-audit with claude-opus, claude-sonnet, copilot+gpt produces comparable coverage (within ±20% REQ count, same UC set).

Deliverable: comparison report across all 7 runs (5 code + QPB + skill fixture), cross-model report for self-audit, go/no-go decision for release.

Gate to release: all success criteria from design doc met; no unresolved regressions on code benchmarks.

---

## Phase 8 — Self-Audit Bootstrap

Goal: QPB v1.5.2 audits itself one more time with full v1.5.2 machinery, artifacts committed as bootstrap evidence.

Same pattern as v1.5.0 Phase 8. Any bugs found go to v1.5.3 backlog.

Deliverable: v1.5.2 self-audit complete, artifacts in `quality/` and archived to `previous_runs/v1.5.2/`.

Gate to release: self-audit completes cleanly OR any failures are explicitly dispositioned.

---

## Release

- Tag v1.5.2
- Update release notes citing the Haiku demonstration as originating evidence
- Document the project-type classification as the key v1.5.2 feature
- Start v1.5.3 backlog

---

## Parking Lot (deferred from v1.5.2)

- Runtime skill validation (executing another skill and observing in real time)
- Automatic skill repair (generating SKILL.md prose fixes)
- Skill-to-skill benchmarking
- Non-markdown skill formats (YAML, structured prompts)
- **Semantic execution divergence (LLM evaluation harness).** Catching cases where gate checks pass but the LLM ignored the spirit of an instruction. Requires building an eval harness — parsing unstructured LLM outputs, grading intermediate reasoning, computing statistical reliability. Out of scope for v1.5.2; revisit for v1.6+ or as a separate tool.

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| v1.5.0 schema doesn't cleanly extend for skill fields | Medium | Review schemas.md before Phase 2 starts; adjust v1.5.0 design if needed mid-flight |
| Classification heuristic misfires on edge-case repos | Medium | Council of Three can override; classification rationale logged for review |
| Section-to-REQ extraction produces too many REQs (explosion) | Medium | Completeness audit sets upper bound; Phase 4 Council prunes redundant REQs |
| Execution divergence has too few archived runs to be useful | Low for QPB (has bootstrap history); Medium for new projects | Document minimum run threshold; emit confidence caveat with low-N findings |
| Hybrid projects produce unwieldy REQUIREMENTS.md length | Medium | Functional section grouping (from v1.5.0) handles this; verify during Phase 7 |
| Cross-model inconsistency on skill derivation | Medium | Test with opus + sonnet + copilot+gpt explicitly in Phase 7; adjust prompts if variance too high |

---

## Open Questions to Resolve

These need answers during implementation but don't block planning:

1. (Phase 1) What's the exact threshold of "prose vs code" for Skill vs Hybrid? Lean: if SKILL.md word count > 2× code LOC, classify as Skill; otherwise Hybrid. Calibrate against real examples.
2. (Phase 3) Should section-to-REQ extraction happen in one pass or iteratively (first draft, then refine)? Lean: iterative, with a Council review between passes.
3. (Phase 4) How strict should "SKILL.md prose claim about code" detection be? Over-eager = false positives. Under-eager = missed bugs. Lean: tune against QPB's own known prose-code drift.
4. (Phase 5) Should execution divergence consume ALL prior runs or a sliding window? Lean: sliding window of last 5; older runs may reflect older skill versions.
5. (All phases) Is SKILL.md always the single Tier 1 source for a skill, or can a project designate external Tier 1 docs? Lean: project can designate; if project has a formal spec elsewhere (e.g., a published methodology paper), that's Tier 1 and SKILL.md is Tier 2 implementation. Uncommon but possible.

---

## Plan Revision Expectations

This plan is explicitly provisional. Revisit after v1.5.0 ships with:

- Any schema changes from v1.5.0 implementation that affect Phase 2 extensions
- Any orchestrator refactors that change where classification logic belongs
- Any Phase 4 Council changes that affect divergence detection integration
- Updated Haiku benchmark if the Haiku-generated REQUIREMENTS.md is refined based on v1.5.0 learnings
- Any new benchmark repos added during v1.5.0 work

The review pass should update this document in place (no separate revision log needed; git history captures changes).
