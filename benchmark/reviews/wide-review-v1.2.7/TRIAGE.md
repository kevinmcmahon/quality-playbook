# Cross-Model Triage — Wide Review of Quality Playbook v1.2.7

**Date:** 2026-03-31
**Reviewers:** Claude Opus 4.6, Claude Sonnet 4.6, Claude Haiku 4.6, ChatGPT (with Thinking), Gemini Pro (with Deep Thinking)
**Method:** Council of Three audit prompt with 7 scrutiny areas targeting v1.2.7 changes, 8 playbook files attached

## Raw Counts


| Reviewer   | Findings | MISSING | DIVERGENT | UNDOCUMENTED | PHANTOM |
| ---------- | -------- | ------- | --------- | ------------ | ------- |
| Opus 4.6   | 21       | 11      | 5         | 3            | 2       |
| Sonnet 4.6 | 19       | 9       | 6         | 3            | 1       |
| Haiku 4.6  | 16       | 9       | 3         | 10           | 2       |
| ChatGPT    | 6        | 2       | 4         | 0            | 0       |
| Gemini Pro | 10       | 7       | 2         | 0            | 1       |
| **Total**  | **72**   | **38**  | **20**    | **16**       | **6**   |


## Comparison with v1.2.6 Review


| Metric                | v1.2.6     | v1.2.7 | Change                                                      |
| --------------------- | ---------- | ------ | ----------------------------------------------------------- |
| Total findings        | 78         | 72     | -8%                                                         |
| Unique themes         | 46         | ~30    | -35%                                                        |
| Tier 1 (5/5 agree)    | 2          | 1      | Defect categories partially resolved; language gap persists |
| Version hallucination | 4/5 models | 0/5    | Fixed (correct files used)                                  |


**Key shift:** The v1.2.6 review surfaced two universal findings (defect categories + language coverage). v1.2.7 partially resolved the defect categories (added sections for all 14, but some are thin). The language expansion was added to defensive_patterns.md but NOT propagated to functional_tests.md, schema_mapping.md, verification.md, review_protocols.md, or SKILL.md fixture strategy. This incomplete propagation is now the dominant finding.

---

## Tier 1 — Universal Consensus (5/5 models agree)

### T1-1. Language expansion incomplete across reference files

**Models:** ALL FIVE
**Classification:** MISSING
**Summary:** C#, Ruby, Kotlin, and PHP were added to defensive_patterns.md grep pattern tables but not to any other reference file. An agent working on a C# or Ruby project gets grep patterns for finding defects but no guidance for writing tests, setting up fixtures, naming regression files, choosing test runners, or mapping schema types. This is the single largest gap — it affects 4 of the 10 claimed languages across 5+ files.

Specific gaps flagged unanimously:

- **functional_tests.md**: No import patterns, test setup, test structure examples, or async test examples for C#/Ruby/Kotlin/PHP
- **schema_mapping.md**: No validation layer examples or mutation value guidance for C#/Ruby/Kotlin/PHP
- **verification.md**: No test runner commands for C#/Ruby/Kotlin/PHP
- **review_protocols.md**: No regression test file naming for C#/Ruby/Kotlin/PHP (also missing Scala)
- **SKILL.md fixture strategy**: No fixture guidance for C#/Ruby/Kotlin/PHP

**Opus:** "C#, Ruby, Kotlin, and PHP were added to defensive_patterns.md grep tables but not to any other reference file."
**Sonnet:** "Four of the ten claimed supported languages have no guidance here. The instruction to 'copy exactly' the import pattern cannot be followed when no pattern is documented."
**Haiku:** "C#, Ruby, Kotlin, PHP are not mentioned anywhere in functional_tests.md."
**ChatGPT:** "The added C#/Ruby/Kotlin/PHP coverage is strong in defensive_patterns.md, but incomplete in the files the skill relies on for test authoring and verification."
**Gemini:** "Every language-specific guideline, table, and code snippet in this file only covers the original 6 languages."

**Also noted:** SKILL.md line 141 still says "six-language matrix" when referring to functional_tests.md, explicitly acknowledging the gap wasn't addressed (Opus, Sonnet).

---

## Tier 2 — Strong Consensus (3-5/5 models agree)

### T2-1. "Present the plan first" UX conflicts with batch file generation

**Models:** Opus, Sonnet, ChatGPT, Gemini, Haiku (5/5)
**Classification:** DIVERGENT / PHANTOM
**Summary:** SKILL.md says "write the six files" in a batch but also says "present the integration test plan to the user BEFORE writing the protocol." These two instructions cannot both be followed. The template in review_protocols.md doesn't include the plan-first step, so agents following the template skip it entirely.

**Two distinct sub-issues identified:**

1. **Structural contradiction** (Gemini, ChatGPT): An agent cannot pause mid-batch to await user confirmation on File 4
2. **Template gap** (Sonnet, Haiku, Opus): The plan-first instruction is in SKILL.md but not in the review_protocols.md template that agents actually follow

This should arguably be Tier 1, but the models split on whether it's DIVERGENT, PHANTOM, or MISSING.

### T2-2. Protocol Violations category has no grep patterns table

**Models:** Opus, Sonnet, Gemini (3/5)
**Classification:** MISSING
**Summary:** Protocol Violations is the only one of the 14 categories that has a heading but no language-specific grep patterns table. Every other category has an explicit table.

### T2-3. Several new detection categories (5c/5d) are prose-only stubs

**Models:** Opus, Sonnet, Haiku (3/5)
**Classification:** MISSING
**Summary:** Async/Sync Parity, Context Propagation Loss, Field Label Drift, Truth Fragmentation, and Callback Concurrency have no per-language grep pattern tables — only prose descriptions. The original categories (null guards, exceptions, etc.) have detailed tables. The new categories are detectable in name but not in depth.

### T2-4. Phase 1→2 gate criterion conflicts with constitution guidance

**Models:** Opus, Sonnet, Haiku (3/5)
**Classification:** DIVERGENT
**Summary:** Phase 1 gate requires "8+ domain-specific risk scenarios." Constitution.md says "fewer is fine for small projects." A small project with 4-6 well-grounded scenarios would satisfy the constitution but fail the phase gate.

### T2-5. Phase 4 completion criterion is not a real gate

**Models:** Opus, Sonnet, ChatGPT, Haiku (4/5)
**Classification:** UNDOCUMENTED / PHANTOM
**Summary:** Phase 4 says it has completion criteria but also says "there is no 'done' requirement." These contradict. The criterion reduces to "the user decides," which is valid but isn't a gate in the structured sense the other phase transitions use.

### T2-6. Missing safeguard / constitution Critical Rule contradiction persists

**Models:** Opus, Sonnet, ChatGPT (3/5)
**Classification:** DIVERGENT
**Summary:** Constitution.md says every scenario's "How to verify" must map to a test. Defensive_patterns.md says "Do NOT write boundary tests" for missing safeguards. A scenario based on a missing safeguard violates one rule or the other. v1.2.7 added the distinction but didn't resolve this cross-file conflict.

### T2-7. Bootstrapping Steps 4 and 6 have no adaptation guidance

**Models:** Opus, Sonnet, Gemini (3/5)
**Classification:** MISSING
**Summary:** The bootstrapping section adapts Steps 1, 2, 3, and 5 for Markdown projects but skips Step 4 (Specifications) and Step 6 (Quality Risks).

---

## Tier 3 — Partial Agreement (2/5 models agree)

### T3-1. 14 defect categories never explicitly enumerated

**Models:** Opus, Haiku (2/5)
**Classification:** UNDOCUMENTED / DIVERGENT
**Summary:** The playbook claims 14 categories but no file provides a canonical numbered list. Counting sections yields 11-17 depending on whether sub-categories count.

### T3-2. Two "present the plan" moments (generation-time vs runtime) are conflated

**Models:** Opus, Sonnet (2/5)
**Classification:** DIVERGENT
**Summary:** SKILL.md line 405 is a generation-time UX requirement (show plan before writing .md file). The Execution UX section is a runtime requirement (show plan before running tests). An agent might implement one and think it covers both.

### T3-3. Phase 2→3 gate only checks file existence, not correctness

**Models:** Sonnet, Haiku (2/5)
**Classification:** UNDOCUMENTED
**Summary:** The gate says "all six files exist" but an agent that generated six empty files would satisfy it.

### T3-4. Regression test naming missing Scala

**Models:** Opus, Sonnet (2/5)
**Classification:** MISSING
**Summary:** review_protocols.md lists regression test file naming for Python, Go, Rust, Java, TypeScript — but Scala (one of the original 6) is missing.

### T3-5. Minimum bar inconsistency (SKILL.md vs defensive_patterns.md)

**Models:** Opus, Sonnet (2/5)
**Classification:** DIVERGENT
**Summary:** For a 15-file medium project: SKILL.md says 2-3 patterns per file (30-45 patterns), defensive_patterns.md says expect 15-30 total. The ranges don't align at the upper end.

### T3-6. Integration test worked examples only cover 4 archetypes

**Models:** Haiku, Gemini (2/5)
**Classification:** PHANTOM
**Summary:** The protocol claims domain-agnostic generality but only has examples for REST API, message queue, database, and CLI. Projects outside these patterns (real-time collaboration, ML pipelines, game engines, embedded systems) have no guidance.

### T3-7. "Adapter guidance for additional languages" claimed but doesn't exist

**Models:** Opus, Haiku (2/5)
**Classification:** PHANTOM
**Summary:** SKILL.md metadata claims "adapter guidance for additional languages" beyond the 10. No such guidance exists.

---

## Tier 4 — Single Model Findings (1/5, needs verification)


| ID    | Finding                                                                           | Model           | Classification |
| ----- | --------------------------------------------------------------------------------- | --------------- | -------------- |
| T4-1  | "Trace all state machines" gate vs "don't read everything" scaling guidance       | Opus            | PHANTOM        |
| T4-2  | Missing safeguard template "How to verify" reads like a test spec                 | Opus            | DIVERGENT      |
| T4-3  | Degraded mode doesn't cover Phase 4 interactive UX                                | Opus            | MISSING        |
| T4-4  | Reference Files table undersells defensive_patterns.md scope                      | Opus            | DIVERGENT      |
| T4-5  | Async test examples missing Java and Scala                                        | Opus            | MISSING        |
| T4-6  | Verification Benchmark 8 Scala runner hardcodes `FunctionalSpec`                  | Sonnet          | DIVERGENT      |
| T4-7  | Step 6 calibration guidance only in constitution.md, not referenced until Phase 2 | Sonnet          | UNDOCUMENTED   |
| T4-8  | Phase 2→3 gate doesn't mention integration test plan confirmation                 | Sonnet          | UNDOCUMENTED   |
| T4-9  | Spec audit triage probe execution underspecified                                  | Haiku           | UNDOCUMENTED   |
| T4-10 | Fix batch sizing criteria not quantified in spec_audit.md                         | Haiku           | UNDOCUMENTED   |
| T4-11 | Bootstrapping section lacks evidence of self-application                          | Haiku           | UNDOCUMENTED   |
| T4-12 | Benchmark dataset referenced but not included/linked                              | Haiku           | UNDOCUMENTED   |
| T4-13 | C# test harness audit in Step 3 but no C# test generation support                 | ChatGPT, Sonnet | DIVERGENT      |


---

## Triage Summary


| Tier                    | Count  | Action                       |
| ----------------------- | ------ | ---------------------------- |
| Tier 1 (universal, 5/5) | 1      | **Must fix** in v1.2.8       |
| Tier 2 (strong, 3-5/5)  | 7      | **Should fix** in v1.2.8     |
| Tier 3 (partial, 2/5)   | 7      | Investigate; fix if verified |
| Tier 4 (single, 1/5)    | 13     | Verify selectively           |
| **Total unique themes** | **28** |                              |


## v1.2.6 → v1.2.7 Resolution Status


| v1.2.6 Finding                                    | Status in v1.2.7                                                                                   |
| ------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| T1-1: Missing defect category detection           | **Partially resolved** — sections added for all 14, but 5 are prose-only stubs without grep tables |
| T1-2: Language coverage overstated                | **Not resolved** — added to defensive_patterns.md only, not propagated to other files              |
| T2-1: Bootstrapping not executable                | **Partially resolved** — adaptation guidance added but Steps 4/6 skipped                           |
| T2-2: Phase transition gates missing              | **Partially resolved** — gates added but have conflicts (8+ scenario vs small projects)            |
| T2-3: Integration protocol domain-specific        | **Resolved** — rewritten with general principles and 4 worked examples                             |
| T2-4: Steps 5c/5d no reference file               | **Not resolved** — content still only in SKILL.md, not in defensive_patterns.md                    |
| T2-5: Boundary-test assertion weakness            | **Resolved** — examples updated                                                                    |
| T2-6: Defensive vs missing safeguard conflation   | **Partially resolved** — distinction added, but constitution Critical Rule conflict persists       |
| T2-7 (new): "Present plan first" UX contradiction | **New issue** introduced by v1.2.7 changes                                                         |


## Recommended v1.2.8 Scope

### Must Fix

1. **Propagate language expansion to all reference files.** Add C#, Ruby, Kotlin, PHP entries to functional_tests.md (import patterns, test setup, test structure, async examples), schema_mapping.md (validation layers, mutation values), verification.md (test runner commands), review_protocols.md (regression test naming), and SKILL.md fixture strategy. Update SKILL.md line 141 from "six-language matrix" to "ten-language matrix." (T1-1)

### Should Fix

1. **Resolve the "present the plan first" structural contradiction.** Either: (a) restructure Phase 2 so File 4 has an explicit pause-and-confirm step, or (b) move the plan-first requirement to Phase 4 as a pre-execution step. Also embed the plan-first template in review_protocols.md so agents following the template get it automatically. (T2-1)
2. **Add grep pattern tables for the 5 stub categories.** Protocol Violations, Async/Sync Parity, Context Propagation Loss, Field Label Drift/Truth Fragmentation, and Callback Concurrency need per-language tables matching the structure of existing categories. (T2-2, T2-3)
3. **Fix Phase 1→2 gate for small projects.** Change "8+ scenarios" to "8+ for medium/large projects, or 2+ per core module for small projects." (T2-4)
4. **Resolve constitution Critical Rule vs missing safeguard conflict.** Add an explicit exception: scenarios derived from missing safeguards should describe the desired behavior as a requirement, not map to a current automated test. (T2-6)
5. **Complete bootstrapping adaptation for Steps 4 and 6.** (T2-7)
6. **Add canonical numbered list of all 14 defect categories.** (T3-1)

## Observations on Reviewer Behavior

- **Convergence improved from v1.2.6:** The dominant finding (language propagation gap) was caught by all 5 models — stronger consensus than v1.2.6 where 2 findings split 5/5.
- **New issue detection:** The "present the plan first" contradiction was a new finding not present in v1.2.6 — all 5 models caught it, showing the review process catches regressions introduced by fixes.
- **ChatGPT remained the most concise** (6 findings) but every finding hit Tier 1 or 2. Zero noise.
- **Haiku caught the most findings** (16 v1.2.7, down from 28 for v1.2.6) — more focused this round.
- **Gemini uniquely caught** the "present plan first" as structurally impossible during batch generation (not just a template gap but a logical impossibility).

