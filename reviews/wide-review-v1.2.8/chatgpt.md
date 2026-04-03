# ChatGPT (Thinking) — v1.2.8 Review

## Findings

### review_protocols.md / SKILL.md — Generation-time plan-first flow

**MISSING** The generation-time "present the plan first" workflow is defined in `SKILL.md`, but it is not embedded in the `review_protocols.md` integration-test template itself.
Playbook says: `SKILL.md` requires File 4 to be a two-step workflow where the agent first presents an integration test plan and only writes `RUN_INTEGRATION_TESTS.md` after user adjustment/confirmation (SKILL.md lines 409–414, 430).
Reality: `review_protocols.md` only includes a runtime "Execution UX" section for when an agent later runs the finished protocol; it does not include the generation-time planning step, so an agent following the template alone will not automatically do the required pre-write plan review (review_protocols.md lines 273–309; SKILL.md lines 409–414, 430).

### defensive_patterns.md — Comprehensive defect category count

**PHANTOM** The file claims a canonical list of 14 defect categories, but the enumeration does not match the actual section structure.
Playbook says: "The playbook addresses 14 defect categories" and lists "Generated and Invisible Code Defects" as item 14 (defensive_patterns.md lines 229–246).
Reality: the file has standalone sections for `Concurrency Issues`, `SQL Errors`, `Security Issues`, `Serialization Bugs`, `API Contract Violations`, `Protocol Violations`, `Async/Sync Parity`, `Context Propagation Loss`, `Field Label Drift`, `Truth Fragmentation`, and `Callback Concurrency` (defensive_patterns.md lines 250–440), but there is no corresponding `### Generated and Invisible Code Defects` section in this file. Item 13 also collapses five separate tables into one numbered category, so the promised count is not reflected by the actual document structure.

### defensive_patterns.md — Kotlin grep patterns

**PHANTOM** The Kotlin-specific grep guidance is not idiomatic enough to support the "full support" claim.
Playbook says: the skill has "Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP" (SKILL.md lines 1–6).
Reality: the Kotlin null-guard row includes `Optional`, which is a Java type rather than an idiomatic Kotlin signal, and the exception-handling row includes a bare `?`, which is too generic to be a useful grep pattern in Kotlin codebases (defensive_patterns.md lines 21, 36). Those patterns are likely to be noisy or misleading rather than actionable.

### functional_tests.md / schema_mapping.md — Ruby examples

**DIVERGENT** Ruby support is internally inconsistent across the examples, mixing RSpec and Minitest styles in ways that are not copy-pasteable.
Playbook says: Ruby support covers "RSpec/Minitest" and should provide usable framework guidance (functional_tests.md lines 105, 167–173; schema_mapping.md lines 131–145).
Reality: `schema_mapping.md` uses Minitest-style `def test_...` method definitions together with RSpec `expect(...)` assertions (schema_mapping.md lines 131–145), which is not a valid example for either framework as written. `functional_tests.md` also labels the Ruby snippet with `// Ruby` rather than Ruby comment syntax (functional_tests.md lines 167–173), which further undermines the "full support" claim for Ruby copyable examples.

### defensive_patterns.md — C# grep patterns

**PHANTOM** Some C# grep patterns rely on outdated or deprecated APIs, so the "full support" language overstates how current the guidance is.
Playbook says: full support includes C# (SKILL.md lines 1–6).
Reality: the C# security row uses `RNGCryptoServiceProvider` and the serialization row uses `BinaryFormatter` as first-class grep targets (defensive_patterns.md lines 300, 319). Those APIs are legacy/deprecated enough that presenting them as representative C# patterns makes the language support look more current than it is.

## Summary

* Total findings: 5
* By classification: 1 MISSING, 1 DIVERGENT, 0 UNDOCUMENTED, 3 PHANTOM
* Top 3 most important findings:

  1. The generation-time plan-first step is missing from `review_protocols.md`, so agents following the template alone can still skip the required pre-write plan review.
  2. `defensive_patterns.md` claims a canonical 14-category list, but the section structure does not actually implement that list.
  3. Ruby and Kotlin language support still has examples/patterns that are not idiomatic or directly usable, which weakens the v1.2.8 "full support" claim.
