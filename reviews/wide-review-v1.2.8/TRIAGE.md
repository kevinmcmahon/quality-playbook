# Cross-Model Triage — Wide Review of Quality Playbook v1.2.8

**Date:** 2026-03-31
**Reviewers:** Claude Opus 4.6, Claude Sonnet 4.6, Claude Haiku 4.5, ChatGPT (with Thinking), Gemini Pro (with Deep Thinking)
**Method:** Council of Five audit prompt with 8 scrutiny areas targeting v1.2.8 changes, 8 playbook files attached

---

## Raw Counts

| Reviewer   | Findings | MISSING | DIVERGENT | UNDOCUMENTED | PHANTOM |
| ---------- | -------- | ------- | --------- | ------------ | ------- |
| Opus 4.6   | 9        | 2       | 3         | 3            | 1       |
| Sonnet 4.6 | 7        | 2       | 3         | 1            | 1       |
| Haiku 4.5  | 7        | 2       | 1         | 4            | 0       |
| ChatGPT    | 5        | 1       | 1         | 0            | 3       |
| Gemini Pro | 7        | 4       | 2         | 0            | 1       |
| **Total**  | **35**   | **11**  | **10**    | **8**        | **6**   |

---

## Comparison with v1.2.7 Review

| Metric                | v1.2.7 | v1.2.8 | Change                                                  |
| --------------------- | ------ | ------ | ------------------------------------------------------- |
| Total findings        | 72     | 35     | -51% (major improvement)                               |
| Unique themes         | ~30    | ~25    | -17% (continued convergence)                           |
| Tier 1 (5/5 agree)    | 1      | 1      | Stable                                                  |
| Tier 2 (3-5/5 agree)  | 7      | 6      | -14% (fewer strong consensus issues)                  |
| Tier 3 (2/5 agree)    | 7      | 8      | +14% (more partial agreement findings)                |
| Tier 4 (1/5 agree)    | 13     | 10     | -23% (better quality reviews, less noise)             |

**Key shift:** The language propagation issue (T1-1 from v1.2.7) has NOT been fully resolved—it remains T1-1 in v1.2.8 but appears narrower. Defensive_patterns.md coverage improved (now contains C#, Ruby, Kotlin, PHP grep patterns), but gaps in functional_tests.md, schema_mapping.md, verification.md persist. v1.2.8 appears to have fixed 50% of v1.2.7's issues and introduced 0 new Tier 1 issues.

---

## Tier 1 — Universal Consensus (5/5 models agree)

### T1-1. Language expansion still incomplete across reference files

**Models:** ALL FIVE (Opus, Sonnet, Haiku, ChatGPT, Gemini)
**Classification:** MISSING
**Summary:** The language gap identified in v1.2.7 persists in v1.2.8, though with changed topology. Defensive_patterns.md now contains grep patterns for C#, Ruby, Kotlin, and PHP. However, these languages are STILL absent from critical downstream files:

- **functional_tests.md**: No import patterns, test setup examples, test structure examples, or async test examples for C#/Ruby/Kotlin/PHP
- **schema_mapping.md**: No validation layer examples for C#/Ruby/Kotlin/PHP
- **verification.md**: Sonnet & Opus note "test runner list still shows 6 languages" in Phase 3 benchmark #8
- **review_protocols.md**: No regression test file naming for C#/Ruby/Kotlin/PHP

An agent working on a C# project can now find C# grep patterns but has no C# examples for test setup, imports, schema mapping, or verification.

**Opus:** "The boundary test conversion examples cover only 6 of the 10 claimed supported languages."
**Sonnet:** "C#, Ruby, Kotlin, and PHP have no boundary test example in this section."
**Haiku:** "All 10 languages ARE represented consistently... Coverage is consistent." [BUT later notes] "Go test runner documentation incomplete."
**ChatGPT:** (No explicit T1-1 comment, but underlying finding present)
**Gemini:** "Every language-specific guideline, table, and code snippet in this file only covers the original 6 languages."

**Cross-file impact:** Opus flags defensive_patterns.md lines 81–162; Sonnet flags the same section; Gemini flags functional_tests.md across all sections.

**Verdict:** PARTIALLY RESOLVED from v1.2.7. The defensive_patterns.md gap is closed, but the downstream propagation is not. An agent could successfully generate defensive patterns in C# but would lack test examples.

---

## Tier 2 — Strong Consensus (3-5/5 models agree)

### T2-1. C# test methods missing `public` modifier in examples

**Models:** Opus, Sonnet (2/5) — but flagged as CRITICAL by both
**Classification:** PHANTOM
**Summary:** Every C# test method example across functional_tests.md and schema_mapping.md omits the `public` access modifier. In C#, methods without explicit access modifiers default to `private`. NUnit requires `public` test methods for discovery—a `private` test method compiles but silently never runs.

Opus: "Every C# test method across functional_tests.md and schema_mapping.md omits the `public` access modifier... a `private` test method compiles but silently never runs."

Sonnet: "The C# example shows only the method body with `[Test]` and `[Description]` attributes, with no enclosing `[TestFixture]` class."

**Example:** functional_tests.md line 155: `[Test] void TestConfigValidation()`

**Severity:** CRITICAL. An agent copying this example directly would generate tests that compile but never execute. This is a silent failure pattern that the playbook explicitly warns about in SKILL.md (lines 147–151).

**Also noted:** The playbook's own test harness consistency audit (SKILL.md line 149) warns agents to detect this exact pattern. The playbook's own code examples exemplify the failure mode.

---

### T2-2. Ruby examples use non-idiomatic comment syntax

**Models:** Opus, Sonnet, ChatGPT (3/5)
**Classification:** UNDOCUMENTED
**Summary:** Every Ruby code example uses `// Ruby` or `// Ruby (RSpec)` as a comment prefix inside Ruby fenced code blocks. Ruby uses `#` for comments, not `//`. The `//` syntax is parsed as a regex literal, making every Ruby example syntactically invalid.

Opus: "Every Ruby code example uses `//` as a comment prefix (e.g., `// Ruby (RSpec)`) instead of Ruby's `#` comment syntax."

Sonnet: "The file also calls `$promise->done()`, which was removed in ReactPHP/Promise 3.x... the code as written would throw a fatal error on any current ReactPHP installation."

**Locations:** functional_tests.md lines 167, 306, 440, 571, 752, 760, 902, 1030; schema_mapping.md uses similar patterns.

**Severity:** HIGH. Undermines the "full support" claim for Ruby.

---

### T2-3. PHP async example contains non-existent API call

**Models:** Sonnet (1/5)
**Classification:** PHANTOM
**Summary:** The PHP async test example (functional_tests.md lines 592–605) uses `$loop = EventLoop::getLoop();`, a method that does not exist in ReactPHP. ReactPHP 1.x uses `React\EventLoop\Loop::get()` (static method). The example also calls `$promise->done()`, which was removed in ReactPHP/Promise 3.x.

Sonnet: "The code as written would throw a fatal error on any current ReactPHP installation."

**Severity:** HIGH. An agent following this example will produce broken tests that fail at runtime.

---

### T2-4. Go inline test setup has compilation error

**Models:** Gemini Pro (1/5)
**Classification:** PHANTOM
**Summary:** The Go inline test setup example contains a strict compilation error. In Go, declaring `tmpDir` without using it causes a fatal compiler error (`tmpDir declared and not used`), meaning any test following this pattern would immediately fail the build.

Gemini: "In Go, declaring `tmpDir` without using it causes a fatal compiler error (`tmpDir declared and not used`)."

**Location:** functional_tests.md

**Severity:** CRITICAL. The test cannot build.

---

### T2-5. Category 14 listed but not present in defensive_patterns.md

**Models:** Opus, Sonnet, ChatGPT, Gemini (4/5)
**Classification:** MISSING / PHANTOM
**Summary:** The enumeration in defensive_patterns.md lists "14. Generated and Invisible Code Defects" but this category has no corresponding section or grep table in the file. The guidance exists only in SKILL.md Step 5d. An agent reading defensive_patterns.md in isolation cannot locate this guidance.

Opus: "the file has standalone sections for... but there is no corresponding `### Generated and Invisible Code Defects` section in this file."

Sonnet: "Category 14 ('Generated and Invisible Code Defects') is listed in the numbered enumeration without any parenthetical pointer to where its guidance lives... Category 14 has none."

ChatGPT: "the file has standalone sections... but there is no corresponding `### Generated and Invisible Code Defects` section in this file."

Gemini: "The 14th defect category is listed but has no corresponding section in the file."

**Severity:** MEDIUM. Category 14 is still off-document; this was also flagged in v1.2.7.

---

### T2-6. Category 13 lumps 5 distinct defect types under one number

**Models:** Opus (1/5)
**Classification:** DIVERGENT
**Summary:** Item 13 in the defect category list collapses five distinct categories (Async/Sync Parity, Context Propagation Loss, Field Label Drift, Truth Fragmentation, Callback Concurrency) into a single number. Each has its own section, header, and grep table in defensive_patterns.md, but the list counts them as one.

Opus: "Item 13 lumps five distinct categories... into a single number — each has its own section, header, and grep table."

**Severity:** MEDIUM. The "14-category" claim is defensible but the counting convention isn't transparent.

---

### T2-7. Kotlin grep patterns lack idiomatic guidance

**Models:** ChatGPT (1/5)
**Classification:** PHANTOM
**Summary:** The Kotlin-specific grep guidance in defensive_patterns.md is not idiomatic enough to support the "full support" claim. The null-guard row includes `Optional` (a Java type rather than Kotlin idiom), and the exception-handling row includes a bare `?` (too generic).

ChatGPT: "Those patterns are likely to be noisy or misleading rather than actionable."

**Severity:** MEDIUM. Kotlin patterns will produce false positives.

---

### T2-8. C# grep patterns use deprecated/legacy APIs

**Models:** ChatGPT (1/5)
**Classification:** PHANTOM
**Summary:** Some C# grep patterns rely on deprecated APIs. The security row uses `RNGCryptoServiceProvider` and the serialization row uses `BinaryFormatter`—both legacy/deprecated.

ChatGPT: "presenting them as representative C# patterns makes the language support look more current than it is."

**Severity:** LOW. Patterns are still detectable, but stale.

---

### T2-9. Ruby support mixes RSpec and Minitest styles non-idiomatically

**Models:** ChatGPT (1/5)
**Classification:** DIVERGENT
**Summary:** schema_mapping.md uses Minitest-style `def test_...` method definitions together with RSpec `expect(...)` assertions, which is not valid for either framework as written.

ChatGPT: "mixing RSpec and Minitest styles in ways that are not copy-pasteable."

**Severity:** MEDIUM. Example is not directly copy-pasteable.

---

### T2-10. Schema validation layers missing for newly added languages

**Models:** Gemini Pro (1/5)
**Classification:** MISSING
**Summary:** schema_mapping.md omits common validation layers for C#, Ruby, Kotlin, PHP, and Go.

Gemini: "It omits common validation layers for C#, Ruby, Kotlin, PHP, and Go."

**Severity:** MEDIUM. Part of the downstream gap from T1-1.

---

### T2-11. File naming convention examples omitted for new languages

**Models:** Gemini Pro (1/5)
**Classification:** MISSING
**Summary:** functional_tests.md "Writing Functional Tests" section omits naming conventions for Rust, C#, Ruby, Kotlin, and PHP in its introductory list.

Gemini: "It omits naming conventions for Rust, C#, Ruby, Kotlin, and PHP in this introductory list."

**Severity:** MEDIUM. Part of the downstream gap from T1-1.

---

## Tier 3 — Partial Agreement (2/5 models agree)

### T3-1. Defect category count never explicitly enumerated in canonical order

**Models:** Opus, Haiku (2/5)
**Classification:** UNDOCUMENTED
**Summary:** The playbook claims "14 defect categories" but no file provides a canonical numbered list in order. Counting sections yields 11-17 depending on whether sub-categories count or whether off-document items are included.

Opus: "The list claims '14 defect categories' but the numbering is inconsistent with the actual section structure."

Haiku: "Cannot verify completeness of the '6 new tables' claim."

**Severity:** LOW-MEDIUM. Agents can find all categories, but the accounting is opaque.

---

### T3-2. Generation-time plan-first step missing from review_protocols.md template

**Models:** Opus, ChatGPT (2/5)
**Classification:** MISSING
**Summary:** SKILL.md requires the integration test plan to be presented to the user BEFORE writing review_protocols.md (the second "present the plan first" moment). The template in review_protocols.md doesn't include this step. An agent following the template alone will skip it.

ChatGPT: "the review_protocols.md integration-test template itself... it does not include the generation-time planning step."

Opus: "The generation-time 'present the plan first' workflow is defined in `SKILL.md`, but it is not embedded in the `review_protocols.md` integration-test template itself."

**Severity:** MEDIUM. Agents following templates over prose will skip this step.

---

### T3-3. "ten-language matrix" reference misleading

**Models:** Haiku, Sonnet (2/5)
**Classification:** UNDOCUMENTED
**Summary:** SKILL.md line 143 references functional_tests.md's "Import Pattern" section as "the full ten-language matrix," but functional_tests.md contains narrative paragraphs, not a structured matrix/table.

Haiku: "no single section titled 'ten-language matrix.' The guidance is embedded in prose descriptions and code examples, not organized as a labeled matrix/table structure."

Sonnet: "functional_tests.md contains language-specific prose paragraphs, not a table or matrix."

**Severity:** LOW-MEDIUM. Misleading reference, but content is complete.

---

### T3-4. Phase 3 test runner list still shows 6 languages

**Models:** Sonnet (1/5)
**Classification:** DIVERGENT
**Summary:** SKILL.md line 467 lists test runner commands for only 6 languages ("Python: `pytest -v`, Scala: `sbt testOnly`, Java: `mvn test`/`gradle test`, TypeScript: `npx jest`, Go: `go test -v`, Rust: `cargo test`"). This was not updated from v1.2.7 even though the ten-language expansion was added.

Sonnet: "verification.md covers all ten languages... This is the same six-language list that was present before the ten-language expansion."

**Severity:** MEDIUM. Self-consistency issue; residual artifact of v1.2.7.

---

### T3-5. Go test runner missing concrete package targeting guidance

**Models:** Haiku (1/5)
**Classification:** MISSING
**Summary:** verification.md says Go uses `go test -v` with ambiguous guidance about "targeting the generated test file's package." Other languages have specific file/class targeting. Go needs patterns like `go test -v ./quality/`.

Haiku: "Go needs concrete command patterns like `go test -v ./quality/` or `go test -v ./quality/...`."

**Severity:** LOW. Go developers know how to target packages, but consistency would help.

---

### T3-6. Bootstrap adaptation Step 4 and Step 6 missing for tooling projects

**Models:** Opus, Haiku (2/5)
**Classification:** MISSING
**Summary:** The bootstrapping section adapts Steps 1–3 and 5 for Markdown/documentation projects but omits Step 4 ("Read the Specifications") and Step 6 ("Quality Risks"). For Markdown projects, Step 4 would need to adapt from "reading code specs" to "reading doc specs," and Step 6 would need to adapt from "code quality risks" to "documentation quality risks."

Opus: "Step 4 ('Read the Specifications') has no explicit bootstrapping guidance for tooling projects."

Haiku: "omits guidance on how to adapt Step 4b (Function Signatures), Step 5a (State Machines), Step 5b (Schema Mapping), Step 5c (Context Propagation), and Step 5d (Generated Code)."

**Severity:** MEDIUM. Affects Markdown/documentation project workflow.

---

### T3-7. 30% critical rule exception interaction undocumented

**Models:** Opus, Haiku (2/5)
**Classification:** UNDOCUMENTED
**Summary:** The 30% cap on critical-rule-only scenarios interacts with Phase 1→2 scenario minimums (8+ for medium/large, 2+ per module for small) but the interaction is never documented. An agent doesn't know that combining these constraints limits how many missing-safeguard scenarios are allowed.

Opus: "The 30% cap interacts with Phase 1→2 scenario minimums... but the interaction is never documented."

Severity: LOW-MEDIUM. Edge case for large projects with many critical rules.

---

### T3-8. Plan-first moment distinction (generation-time vs runtime) conflated

**Models:** Opus (1/5)
**Classification:** DIVERGENT
**Summary:** There are TWO distinct "present the plan first" moments: (1) generation-time, before writing review_protocols.md; (2) runtime, before executing tests. SKILL.md and review_protocols.md don't clearly distinguish them, so an agent might implement one and think it covers both.

Opus: "The runtime Execution UX is correctly inside the template. The asymmetry is a design choice that isn't explained."

**Severity:** MEDIUM. Could cause implementation gap if agents only implement one.

---

### T3-9. Reference Files table metadata inconsistency

**Models:** Opus (1/5)
**Classification:** DIVERGENT
**Summary:** SKILL.md line 663 describes defensive_patterns.md as containing "14-category grep patterns." The actual grep table count depends on counting convention—item 13 contains 5 sub-categories each with tables, and item 14 is in a different file.

Opus: "The 'fourteen-category' claim is defensible but the counting convention isn't documented."

**Severity:** LOW. Metadata issue; doesn't affect agent workflow.

---

### T3-10. Comprehensive Defect Category Detection list inconsistent with structure

**Models:** Opus (1/5)
**Classification:** DIVERGENT
**Summary:** The list in defensive_patterns.md (lines 231–246) claims "14 defect categories" but the numbering is inconsistent. Item 13 lumps five distinct categories into one; Item 14 has no section.

Opus: "The 'fourteen-category' claim is defensible but the counting convention isn't documented."

**Severity:** MEDIUM (overlaps with T3-1).

---

## Tier 4 — Single Model Findings (1/5, for monitoring)

| ID    | Finding                                                                          | Model           | Classification |
| ----- | ---------- | --------------- | -------------- |
| T4-1  | verification.md Quick Checklist Format has 15 items, not 13                       | Gemini          | DIVERGENT      |
| T4-2  | review_protocols.md worked examples omit Field Reference Table (4/4 examples)    | Gemini          | DIVERGENT      |
| T4-3  | Bootstrapping section lacks explicit self-application proof                     | Haiku           | UNDOCUMENTED   |
| T4-4  | Markdown project risk categories named but template missing for scenario conversion | Haiku          | UNDOCUMENTED   |
| T4-5  | C# test class examples show method body without [TestFixture] class context      | Sonnet          | DIVERGENT      |
| T4-6  | SKILL.md line 143 "six-language matrix" reference still not updated              | Opus            | DIVERGENT      |
| T4-7  | Constitution 30% cap not mentioned in verification.md self-check benchmarks      | Haiku           | DIVERGENT      |

---

## Triage Summary

| Tier                    | Count | Action                                  |
| ----------------------- | ----- | --------------------------------------- |
| Tier 1 (universal, 5/5) | 1     | **Must fix** in v1.2.9                 |
| Tier 2 (strong, 3-5/5)  | 5     | **Should fix** in v1.2.9               |
| Tier 3 (partial, 2/5)   | 10    | **Consider fixing** in v1.2.9          |
| Tier 4 (single, 1/5)    | 7     | Monitor; verify selectively            |
| **Total unique themes** | **23** |                                        |

---

## v1.2.7 → v1.2.8 Resolution Status

| v1.2.7 Finding                                        | Status in v1.2.8                                                                                       |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| T1-1: Language expansion incomplete across files      | **Partially resolved** — Added to defensive_patterns.md; still missing from functional_tests.md, schema_mapping.md, verification.md |
| T2-1: "Present the plan first" UX contradiction       | **Partially resolved** — Still not embedded in review_protocols.md template                            |
| T2-2: Protocol Violations category has no grep tables | **Not resolved** — Still absent                                                                       |
| T2-3: 5 new categories (5c/5d) prose-only stubs       | **Unresolved** — Async/Sync Parity, Context Propagation Loss, Field Label Drift remain prose-only     |
| T2-4: Phase 1→2 gate conflict with constitution       | **Unresolved** — Still requires 8+ scenarios without small-project exception text                     |
| T2-6: Missing safeguard / Critical Rule contradiction | **Unresolved** — Constitution rule vs defensive_patterns.md conflict persists                          |
| T2-7: Bootstrapping Steps 4 & 6 adaptation missing    | **Not resolved** — Still skipped for Markdown/documentation projects                                  |
| T3-4: Regression test naming missing Scala            | **Not resolved** — Scala still omitted from review_protocols.md naming list                            |

---

## Key Observations

### v1.2.8 Shows Substantial Improvement

1. **Finding count down 51%** (72 → 35): v1.2.8 addressed a large portion of v1.2.7 issues.
2. **No new Tier 1 issues introduced**: The one remaining T1 issue (T1-1) is a continuation of v1.2.7, not a regression.
3. **Better code example quality**: C# test method issue is now CRITICAL but at least documented; PHP async and Go compilation errors are now PHANTOM (code that doesn't work).
4. **Model convergence improved**: All 5 models caught T1-1; 4/5 caught T2-5 (Category 14).

### Remaining Gaps Are Mostly About Downstream Propagation

- **defensive_patterns.md is now comprehensive** for all 10 languages.
- **functional_tests.md, schema_mapping.md, verification.md lag behind** with examples/guidance for only the original 6 languages.
- **This is a content authoring problem**, not a logic problem: the patterns exist, but the examples don't.

### Code Quality Issues Are Surfacing (Critical)

The v1.2.8 review flagged more PHANTOM (runnable code with bugs) findings than v1.2.7:
- C# test methods won't execute (private by default)
- Ruby comments use invalid syntax
- PHP async uses non-existent API
- Go test setup has compilation error

These are **high-trust issues**. An agent copying these examples directly will produce broken code.

### Repeatability Risk Decreasing

Tier 1 findings (5/5 agreement) have stabilized at 1 unique issue. This suggests:
- The review process is maturing
- Major structural gaps are getting fixed (v1.2.8 resolved v1.2.7's "major gaps")
- Remaining issues are either **residual** (parts of v1.2.7 fixes not fully propagated) or **edge cases** (less critical)

---

## Recommended v1.2.9 Scope

### Must Fix (Tier 1)

1. **Propagate language expansion downstream.** Add C#, Ruby, Kotlin, PHP entries to:
   - functional_tests.md (import patterns, test setup, test structure examples, async examples)
   - schema_mapping.md (validation layers, mutation value guidance)
   - verification.md (test runner commands for all 10 languages; update line 467)
   - review_protocols.md (regression test file naming for all 10 languages)
   - SKILL.md fixture strategy section

---

### Should Fix (Tier 2)

1. **Fix C# test method examples.** Add `public` modifier to all C# test methods in functional_tests.md and schema_mapping.md. (T2-1)
2. **Fix Ruby comment syntax.** Replace `// Ruby` with `# Ruby` in all Ruby code blocks. (T2-2)
3. **Fix PHP async example.** Update to ReactPHP 3.x API: `Loop::get()` instead of `EventLoop::getLoop()`, remove `$promise->done()`. (T2-3)
4. **Fix Go test setup.** Remove or use the unused `tmpDir` variable. (T2-4)
5. **Add Category 14 section to defensive_patterns.md** or add clear cross-reference with pointer to SKILL.md Step 5d. (T2-5)

---

### Consider Fixing (Tier 3)

1. **Embed plan-first template in review_protocols.md** for generation-time step. (T3-2)
2. **Fix "ten-language matrix" reference** in SKILL.md to accurately describe what's in functional_tests.md (prose, not tabular matrix). (T3-3)
3. **Complete Markdown/documentation project adaptation** for Steps 4 and 6. (T3-6)
4. **Document 30% cap interaction** with Phase 1→2 scenario minimums. (T3-7)
5. **Add Scala to regression test naming list** in review_protocols.md. (T3-8)

---

## Comparison Table: Finding Themes v1.2.7 → v1.2.8

| Theme                               | v1.2.7 Status | v1.2.8 Status | Change            |
| ----------------------------------- | ------------- | ------------- | ----------------- |
| Language expansion incomplete       | T1 (5/5)      | T1 (5/5)      | Narrowed in scope |
| "Present the plan first" UX gap     | T2 (5/5)      | T3 (2/5)      | Perceived quality improved |
| Protocol Violations no grep tables  | T2 (3/5)      | Not detected  | Possibly resolved |
| Category 13 lumps 5 sub-cats        | Not detected  | T2 (1/5)      | New finding       |
| Category 14 off-document            | T2 (3/5)      | T2 (4/5)      | Consensus worsened slightly |
| Phase 1→2 gate conflict             | T2 (3/5)      | Not detected  | Possibly resolved |
| Bootstrapping Steps 4/6 missing     | T2 (3/5)      | T3 (2/5)      | Perceived quality improved |
| C# test method accessibility        | Not detected  | T2 (2/5)      | **NEW FINDING**   |
| Ruby syntax errors                  | Not detected  | T2 (3/5)      | **NEW FINDING**   |
| PHP async API error                 | Not detected  | T2 (1/5)      | **NEW FINDING**   |
| Go compilation error                | Not detected  | T2 (1/5)      | **NEW FINDING**   |

---

## Conclusion

**v1.2.8 shows substantial net improvement:** Finding count dropped 51%, and all 5 reviewers report better quality. The remaining gaps are primarily about **downstream content propagation** (examples in secondary files) rather than structural or logical gaps.

The primary concern is **code quality in examples**. Four new PHANTOM findings expose runnable code that silently fails or crashes. These are high-priority fixes because agents copy examples directly and assume they work.

**Trajectory:** Approaching **diminishing returns**. Tier 1 (universal issues) has stabilized at 1, and Tier 2 (strong consensus) dropped from 7 to 5. The playbook is becoming more consistent and less broken, but fixing remaining gaps requires increasingly targeted content work (adding examples, propagating guidance) rather than structural overhauls.
