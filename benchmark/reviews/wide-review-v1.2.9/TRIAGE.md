# Cross-Model Triage — Wide Review of Quality Playbook v1.2.9

**Date:** 2026-03-31
**Reviewers:** Claude Opus 4.6, Claude Sonnet 4.6, Claude Haiku 4.5, ChatGPT (with Thinking), Gemini Pro (with Deep Thinking)
**Method:** Council of Five audit with 9 reviewers reading v1.2.9 review files

---

## Raw Counts

| Reviewer   | Findings | MISSING | DIVERGENT | UNDOCUMENTED | PHANTOM |
| ---------- | -------- | ------- | --------- | ------------ | ------- |
| Opus 4.6   | 9        | 1       | 3         | 1            | 4       |
| Sonnet 4.6 | 7        | 2       | 1         | 0            | 4       |
| Haiku 4.5  | 9        | 4       | 2         | 3            | 0       |
| ChatGPT    | 4        | 0       | 3         | 0            | 1       |
| Gemini Pro | 6        | 2       | 3         | 1            | 0       |
| **Total**  | **35**   | **9**   | **12**    | **5**        | **9**   |

---

## Unique Finding Themes (v1.2.9)

### T1-1. C# Test Methods Missing `public` Modifier (CRITICAL)

**Models:** Opus, Sonnet (2/5)
**Tier:** 2
**Classification:** PHANTOM

**Summary:**
Opus and Sonnet both flag that C# test method examples in `functional_tests.md` (lines 421–436 and line 426) lack the `public` access modifier required by NUnit. In C#, methods without explicit modifiers default to `private`, causing tests to compile but silently not run—a high-trust failure pattern.

**Example locations:**
- functional_tests.md line 426: `void TestFeatureWorks(Variant variant)` should be `public void TestFeatureWorks(...)`
- functional_tests.md line 66: C# inline example shows `[TestFixture] class FunctionalTests { }` without `public`
- Cross-variant example similarly missing `public` on both class and method

**Severity:** CRITICAL. This was supposedly fixed in v1.2.9 but appears to have been missed.

---

### T2-1. Java Async Example: `CompletableFuture<r>` Compilation Error

**Models:** Sonnet (1/5)
**Tier:** 4
**Classification:** PHANTOM

**Summary:**
Sonnet flags functional_tests.md line 535 where `CompletableFuture<r>` uses lowercase undefined type `r`. Java would fail to compile with `error: cannot find symbol: class r`. The intended type is `Result`, so should be `<Result>`.

**Severity:** CRITICAL. Code does not compile.

---

### T3-1. PHP Async Example: Dead `$loop` Variable + ReactPHP 3.x API Mismatch

**Models:** Opus, Sonnet (2/5)
**Tier:** 2
**Classification:** PHANTOM

**Summary:**
Multiple reviewers (Opus line 25, Sonnet line 14) flag PHP async example in functional_tests.md lines 592–601 containing unused `$loop = \React\EventLoop\Loop::get();` that is never referenced. Additionally, Sonnet notes the example also calls `$promise->done()`, which was removed in ReactPHP/Promise 3.x.

**Severity:** HIGH. Dead code in v3.x examples, plus API method no longer exists.

---

### T4-1. PHP grep Pattern: Incorrect ReactPHP Namespace

**Models:** Opus (1/5)
**Tier:** 4
**Classification:** PHANTOM

**Summary:**
Opus flags defensive_patterns.md line 469 where PHP grep pattern lists `ReactPHP\Promise` but the correct namespace is `React\Promise` (no "PHP" suffix). A grep for `ReactPHP\Promise` would return zero results on actual ReactPHP codebases.

**Severity:** MEDIUM. Pattern would not match real code.

---

### T5-1. Field Reference Table Format Divergence (Template vs. Worked Example)

**Models:** Opus, Sonnet, Gemini (3/5)
**Tier:** 2
**Classification:** DIVERGENT

**Summary:**
Three reviewers independently flag that `review_protocols.md` mandates Field Reference Table with columns `| Field | Type | Constraints |` (lines 563–582 template), but the REST API worked example (lines 377–386) uses entirely different columns: `| Field | Source (code) | Expected behavior | Verified by |`. Agents have no guidance on which format to follow.

**Severity:** HIGH. Incompatible schemas undermine the standardized procedure.

---

### T6-1. Field Reference Tables Missing from 3 of 4 Worked Examples

**Models:** Opus, Haiku, Gemini (3/5)
**Tier:** 2
**Classification:** MISSING

**Summary:**
Opus, Haiku, and Gemini all note that `review_protocols.md` only includes a Field Reference Table in the REST API worked example. Queue/background job (Example 2), Database (Example 3), and CLI/Pipeline (Example 4) examples all lack Field Reference Tables despite the playbook saying this is required before writing quality gates.

**Locations:** review_protocols.md Examples 2, 3, 4 (lines 340–492)

**Severity:** HIGH. Concrete example missing for 75% of use cases.

---

### T7-1. Duplicate/Overlapping "Plan-First" Guidance in review_protocols.md

**Models:** Opus, Sonnet (2/5)
**Tier:** 3
**Classification:** DIVERGENT

**Summary:**
Opus and Sonnet independently flag that `review_protocols.md` contains two distinct adjacent sections describing the same generation-time plan-first requirement with different wording and detail levels (lines 152–189 "Integration Test Design UX" vs. lines 191–201 "Generation-Time Plan-First Step"). Neither acknowledges the other, creating ambiguity about whether these are two different steps or one described twice.

**Severity:** MEDIUM. Agents could implement plan-first twice.

---

### T8-1. SKILL.md Category Count Claims "14-Category Grep Patterns" But Category 14 Has No Patterns

**Models:** Opus, Haiku, ChatGPT, Gemini (4/5)
**Tier:** 2
**Classification:** DIVERGENT

**Summary:**
Four reviewers flag that SKILL.md line 667 claims defensive_patterns.md contains "14-category grep patterns," but category 14 ("Generated and Invisible Code Defects") explicitly states "no grep table" and references guidance that lives only in SKILL.md Step 5d, not in defensive_patterns.md. Only 13 of 14 categories have grep patterns in that file.

**Severity:** MEDIUM. Overclaim in playbook summary.

---

### T9-1. Category 13 Bundles 5 Distinct Concerns Under Single Number

**Models:** Opus, Haiku, Gemini (3/5)
**Tier:** 3
**Classification:** UNDOCUMENTED

**Summary:**
Opus, Haiku, and Gemini note that Category 13 in defensive_patterns.md silently bundles five separate concerns (Async/Sync Parity, Context Propagation Loss, Field Label Drift, Truth Fragmentation, Callback Concurrency), each with its own grep table, section heading, and methodology. Counting it as one category obscures this multiplicity. Agents instructed to "search across all 14 defect categories" might treat category 13 as a single check rather than five separate ones.

**Severity:** MEDIUM. Counting convention isn't transparent.

---

### T10-1. Ruby Examples Use Non-Idiomatic Comment Syntax (`//` instead of `#`)

**Models:** Haiku (1/5)
**Tier:** 4
**Classification:** DIVERGENT

**Summary:**
Haiku flags defensive_patterns.md lines 172–181 where Ruby boundary test examples use Minitest syntax (`def test_*()`) instead of the RSpec syntax (`it` blocks with `# Ruby (RSpec)` header) shown in functional_tests.md. Two different Ruby testing frameworks are documented without acknowledgment.

**Severity:** MEDIUM. Framework inconsistency across files.

---

### T11-1. Language-Specific Mutation Rules Only Cover 4 of 10 Languages

**Models:** Haiku, Gemini (2/5)
**Tier:** 3
**Classification:** MISSING

**Summary:**
Haiku and Gemini both flag schema_mapping.md lines 523–540 where "Language-Specific Mutation Rules" section provides guidance only for C#, Ruby, Kotlin, and PHP. Missing: Python, Java, Scala, TypeScript, Go, Rust—six of the ten claimed supported languages.

**Severity:** MEDIUM. Incomplete coverage undermines "10-language support" claim.

---

### T12-1. SKILL.md Bootstrapping Sub-Step Adaptation Lacks Expected Artifact Form

**Models:** Sonnet, Haiku (2/5)
**Tier:** 3
**Classification:** MISSING

**Summary:**
Sonnet and Haiku note that SKILL.md lines 598–599 (bootstrapping adaptation guidance) tells agents what each sub-step means for documentation/tooling projects but does not specify what artifact the adapted sub-step should produce. The main guidance produces concrete artifacts (function call map, schema type map table, etc.), but the adaptation substitutes a new scope without corresponding artifact form.

**Severity:** MEDIUM. Agents don't know what output to produce for Markdown projects.

---

### T13-1. Ruby Testing Framework Inconsistency: RSpec vs. Minitest

**Models:** Haiku (1/5)
**Tier:** 4
**Classification:** DIVERGENT

**Summary:**
Haiku flags defensive_patterns.md lines 172–181 showing Ruby boundary test examples using Minitest syntax while functional_tests.md uses RSpec. The playbook should standardize on one framework or clearly document both.

**Severity:** MEDIUM. Inconsistent examples could cause framework mismatch.

---

### T14-1. Integration Test Generation Step Count Conflict

**Models:** Gemini (1/5)
**Tier:** 4
**Classification:** DIVERGENT

**Summary:**
Gemini flags SKILL.md claiming integration test generation is a "two-step process" but review_protocols.md "Integration Test Design UX" outlines a three-step process. Conflicting step counts.

**Severity:** LOW-MEDIUM. Workflow clarity issue.

---

### T15-1. Verification Step 7 (Mutation Validity) Assumes Schema Map Always Exists

**Models:** Gemini (1/5)
**Tier:** 4
**Classification:** UNDOCUMENTED

**Summary:**
Gemini flags verification.md Benchmark 7 ("Mutation Validity") universally demands "verify the mutation value is in the 'Accepts' column of your Step 5b schema map" but schema_mapping.md states "If the project has no schema validation layer... you can skip the mapping." The verification step doesn't document what to do if Step 5b was legitimately skipped.

**Severity:** LOW. Edge case for projects without schema validation.

---

### T16-1. Constitution & Verification: 30% Cap Interaction With Phase 1→2 Minimums Undocumented

**Models:** Haiku (1/5)
**Tier:** 4
**Classification:** MISSING

**Summary:**
Haiku flags that the 30% non-testable scenario cap and Phase 1→2 scenario minimums interact but this interaction is not found in constitution.md or verification.md reference files (may exist only in SKILL.md).

**Severity:** LOW. Edge case for large projects with many critical rules.

---

### T17-1. Verification.md: Minimum Scenario Count for Phase 2 Transition Undocumented

**Models:** Haiku (1/5)
**Tier:** 4
**Classification:** UNDOCUMENTED

**Summary:**
Haiku notes verification.md requires scenario count to match test count but does not document a minimum scenario count requirement to proceed to Phase 2.

**Severity:** LOW-MEDIUM. Reference file completeness issue.

---

### T18-1. Review Protocols Code Review Template Missing Generation-Time Planning Distinction

**Models:** Haiku (1/5)
**Tier:** 4
**Classification:** UNDOCUMENTED

**Summary:**
Haiku flags review_protocols.md lines 7–51 (Code Review Protocol Template) show only runtime protocol (Bootstrap, What to Check, Guardrails). No distinction documented between generation-time planning and runtime planning. An agent reading only review_protocols.md could implement runtime execution but would miss generation-time plan-first step.

**Severity:** MEDIUM. Could cause workflow gap.

---

### T19-1. Bootstrapping Sub-Step Adaptation: Steps 5a and 5c Guidance Too Vague

**Models:** Haiku (1/5)
**Tier:** 4
**Classification:** UNDOCUMENTED

**Summary:**
Haiku flags SKILL.md lines 599–607 where adaptation guidance for Steps 5a ("trace document/content lifecycle states") and 5c ("check whether metadata, configuration, or settings propagate correctly") is too vague to be reliably actionable. Key terms like "correctly" remain undefined.

**Severity:** MEDIUM. Agents need clearer definitions.

---

### T20-1. Regression Test Language-Specific Tips Incomplete

**Models:** Sonnet (1/5)
**Tier:** 4
**Classification:** MISSING

**Summary:**
Sonnet flags review_protocols.md lines 107–115 where regression test language-specific tips section lists only 8 of 10 supported languages. TypeScript and Scala receive no tips.

**Severity:** MEDIUM. Incomplete coverage for two languages.

---

## Summary Statistics

### By Tier

| Tier | Count | Description                      |
| ---- | ----- | -------------------------------- |
| T1   | 0     | 5/5 models agree (universal)     |
| T2   | 6     | 3-4/5 models agree (strong)      |
| T3   | 3     | 2/5 models agree (partial)       |
| T4   | 11    | 1/5 models flag (single model)   |
| **Total unique themes** | **20** | |

### By Classification

| Classification | Count |
| -------------- | ----- |
| MISSING        | 6     |
| DIVERGENT      | 7     |
| UNDOCUMENTED   | 4     |
| PHANTOM        | 3     |

---

## Comparison with v1.2.8

### v1.2.8 Context

- Total findings: 35 unique themes
- Tier 1 (5/5): 1 theme (Language expansion incomplete)
- Tier 2 (3-5/5): 5 themes
- Tier 3 (2/5): 10 themes
- Tier 4 (1/5): 9 themes (actually 7 listed in v1.2.8 triage but calculations suggest 9)

### v1.2.9 Changes

| Metric | v1.2.8 | v1.2.9 | Change |
| ------ | ------ | ------ | ------ |
| Total unique themes | 23 | 20 | -13% (slight improvement) |
| Tier 1 (5/5) | 1 | 0 | **Resolved** |
| Tier 2 (3-5/5) | 5 | 6 | +20% (regressed) |
| Tier 3 (2/5) | 10 | 3 | -70% (improved) |
| Tier 4 (1/5) | 7 | 11 | +57% (more single-model noise) |

---

## Status of v1.2.8 Findings in v1.2.9

### Resolved in v1.2.9

1. **T1-1 "Language expansion incomplete across files"** — NO LONGER A TIER 1 ISSUE. No single finding flagged by all 5 reviewers. This indicates either:
   - Partial fixes reduced the issue enough that models no longer universally agree
   - The issue is now fragmented into smaller, more specific findings that some models miss
   - v1.2.9 made progress but didn't fully resolve the underlying problem

### Persisting from v1.2.8

1. **Field Reference Table format divergence** — PERSISTS. Still flagged by 3/5 models (Opus, Sonnet, Gemini) in v1.2.9. No change in status.

2. **Field Reference Tables missing from worked examples** — PERSISTS. Still flagged by 3/5 models (Opus, Haiku, Gemini) in v1.2.9. This was v1.2.8 T3-2.

3. **Category 14 off-document** — PERSISTS. Now flagged by 4/5 models (up from 4/5 in v1.2.8). Stronger consensus that this issue remains unresolved.

4. **Ruby/Kotlin/PHP/C# language gaps downstream** — PARTIALLY PERSISTS. In v1.2.8 this was T1-1 (universal). In v1.2.9 it fragments into:
   - T1-1 C# test method accessibility (2/5)
   - T11-1 Language-specific mutation rules incomplete (2/5)
   - T6-1 Field Reference Tables missing from 3 of 4 examples (3/5)

5. **Bootstrapping adaptation missing** — PERSISTS. v1.2.8 T3-6 about Steps 4 & 6 adaptation now appears as T12-1 (2/5 models). Still not resolved.

6. **Plan-first UX gaps** — PERSISTS. v1.2.8 T3-2 about generation-time planning now appears as T7-1 (duplicate sections) and T18-1 (runtime-only template). Still creating confusion.

### New Issues in v1.2.9 (Not in v1.2.8)

1. **Java CompletableFuture<r> compilation error** — NEW (T2-1, 1/5 Sonnet). Code quality regression in examples.

2. **PHP ReactPHP namespace error in grep patterns** — NEW (T4-1, 1/5 Opus). Grep patterns don't match real code.

3. **Ruby Minitest vs. RSpec framework inconsistency** — NEW (T10-1, T13-1, 1/5 Haiku). Framework documentation split.

4. **Integration test generation step count conflict** — NEW (T14-1, 1/5 Gemini). Conflicting step counts between files.

5. **Verification step assumes schema map always exists** — NEW (T15-1, 1/5 Gemini). Edge case documentation gap.

---

## Trajectory Assessment (v1.2.6 → v1.2.7 → v1.2.8 → v1.2.9)

Based on v1.2.8 triage and v1.2.9 observations:

### Finding Count Trend

- v1.2.7: ~72 findings
- v1.2.8: ~35 findings (-51%)
- v1.2.9: ~35 findings (stable)

**Interpretation:** v1.2.8 made major improvements. v1.2.9 shows a plateau—no additional dramatic improvement, but no regression either.

### Tier 1 Trend (Universal Issues)

- v1.2.7: 1 (language expansion)
- v1.2.8: 1 (language expansion, narrowed)
- v1.2.9: 0 (fragmented, no universal consensus)

**Interpretation:** Universal issues have been reduced. The playbook no longer has a problem that ALL reviewers agree on. This is positive progress.

### Consensus Erosion

v1.2.9 shows **consensus fragmentation**:
- v1.2.8 had 1 T1 + 5 T2 = **6 high-consensus issues**
- v1.2.9 has 0 T1 + 6 T2 = **6 high-consensus issues (but weaker)**

The T2 issues in v1.2.9 are mostly 2-3/5 models rather than 4-5/5. This could indicate:
- Issues are becoming more subtle/edge-case-ish
- Models are less aligned on what constitutes a problem
- The playbook is diverging in different ways depending on reading depth

### Code Quality Issue Emergence

v1.2.9 introduces **new PHANTOM findings** (runnable code with bugs):
- Java `CompletableFuture<r>` doesn't compile
- PHP async uses deleted APIs
- C# methods won't execute
- Go test setup has unused variables

This is a NEW concern not present in v1.2.8's summary. Reviewers are catching bugs in code examples more systematically.

### Resolution Pattern

Most v1.2.8 findings NOT resolved in v1.2.9; rather, they:
- **Fragmented** (T1-1 language gap split into 3 separate T2/T3 issues)
- **Persisted** (Field Reference Table divergence still there)
- **Reappeared** (Plan-first UX gap repackaged differently)

Only a handful of v1.2.8 findings show true resolution (disappeared entirely).

---

## Clear Recommendation

### Is Further Iteration Warranted?

**YES, but with caveats.**

#### Positive Signals

1. **No new universal failures:** Zero Tier 1 issues means no structural collapse.
2. **Code example quality visibility:** Reviewers catching PHANTOM bugs in examples is a sign of maturing review depth.
3. **Manageable issue count:** 20 unique themes is workable scope.

#### Concerns

1. **Plateau effect:** Finding count unchanged since v1.2.8 suggests diminishing returns.
2. **Persistent core gaps:** Field Reference Tables and language downstream propagation STILL present.
3. **Fragmentation:** Issues are becoming granular and harder to resolve as a group.
4. **Code quality regressions:** New PHANTOM findings (broken code examples) are high-priority but manual to fix.

#### Recommended v1.2.10 Scope (High Priority)

**Tier 2 Issues (MUST FIX):** 6 issues, mostly code quality + format divergence

1. **C# Test Method Accessibility (T1-1)** — Add `public` modifier to all C# test method examples
2. **Java CompletableFuture Type Error (T2-1)** — Change `<r>` to `<Result>`
3. **PHP Async Dead Code + API Mismatch (T3-1)** — Remove unused `$loop`, update ReactPHP 3.x API calls
4. **Field Reference Table Format Divergence (T5-1)** — Align worked example to template format
5. **Field Reference Tables Missing from Examples 2/3/4 (T6-1)** — Add tables to all 4 worked examples
6. **Duplicate Plan-First Guidance (T7-1)** — Merge duplicate sections or clarify distinction

**Tier 3 Issues (SHOULD FIX if time permits):** 3 issues, downstream propagation + completeness

1. **Language-Specific Mutation Rules Incomplete (T11-1)** — Add rules for Python, Java, Scala, TypeScript, Go, Rust
2. **Bootstrapping Artifact Form Missing (T12-1)** — Specify what Markdown project artifacts should look like
3. **Ruby Framework Inconsistency (T10-1, T13-1)** — Standardize on one testing framework

#### Expected Impact

Fixing Tier 2 issues should:
- Eliminate code quality regressions
- Remove format divergence that confuses agents
- Resolve the "Field Reference Table" persistence from v1.2.8

This would drop total themes from 20 to approximately **8-10**, with most remaining issues being **Tier 3 edge cases or Tier 4 single-model flags**.

#### Iteration Frequency

- **v1.2.9 → v1.2.10:** Proceed with focused Tier 2 fixes (reasonable scope).
- **v1.2.10 → v1.2.11:** Re-review to assess if Tier 2 fixes actually eliminate the issues or fragment them further.
- **Beyond v1.2.11:** Consider quarterly review cadence rather than per-release, as finding count suggests approach to stability.

---

## Files and Locations Summary

| Issue | Files Affected |
| ----- | --------------- |
| C# test method `public` modifier | functional_tests.md lines 66, 426, 421–436 |
| Java `CompletableFuture<r>` error | functional_tests.md line 535 |
| PHP async dead code | functional_tests.md lines 592–601 |
| PHP ReactPHP namespace | defensive_patterns.md line 469 |
| Field Reference Table format | review_protocols.md lines 563–582 (template) vs. 377–386 (example) |
| Field Reference Tables missing | review_protocols.md Examples 2/3/4 (lines 340–492) |
| Duplicate plan-first guidance | review_protocols.md lines 152–189 vs. 191–201 |
| Category 14 off-document | SKILL.md line 667, defensive_patterns.md Comprehensive Defect Categories section |
| Category 13 lumps 5 concerns | defensive_patterns.md Category 13 |
| Language mutation rules incomplete | schema_mapping.md lines 523–540 |
| Bootstrapping artifact form | SKILL.md lines 598–599 |
| Ruby framework inconsistency | defensive_patterns.md lines 172–181 vs. functional_tests.md |
| Integration test step count | SKILL.md vs. review_protocols.md "Integration Test Design UX" |
| Verification edge case (schema map skip) | verification.md Benchmark 7 vs. schema_mapping.md skip condition |
| Generation-time vs. runtime planning | review_protocols.md lines 7–51 (template) |

---

## Conclusion

**v1.2.9 shows stabilization but not resolution.** The playbook has improved from v1.2.7 (51% finding reduction) but v1.2.8 → v1.2.9 plateau suggests approaching asymptotic quality. The remaining 20 issues are predominantly **downstream propagation gaps** (examples not covering all languages) and **code quality bugs in examples** (runnable code that silently fails).

A focused v1.2.10 iteration addressing the **6 Tier 2 issues** (mostly code fixes + format alignment) is **strongly recommended** and should be tractable in a single release cycle. This would resolve persistent issues from v1.2.8 and new code quality regressions introduced in v1.2.9.

**Likelihood of further substantial improvement beyond v1.2.10:** Moderate. Remaining issues are increasingly granular; further iterations will likely focus on **targeted example addition** (adding mutation rules, field tables, language examples) rather than structural refactoring.
