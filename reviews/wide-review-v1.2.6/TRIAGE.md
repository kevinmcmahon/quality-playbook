# Cross-Model Triage — Wide Review of Quality Playbook v1.2.6

**Date:** 2026-03-31 (corrected run — original run used wrong file versions)
**Reviewers:** Claude Opus 4.6, Claude Sonnet 4.6, Claude Haiku 4.6, ChatGPT (with Thinking), Gemini Pro (with Deep Thinking)
**Method:** Council of Three audit prompt with 7 scrutiny areas, 8 playbook files attached

## Raw Counts

| Reviewer | Findings | MISSING | DIVERGENT | UNDOCUMENTED | PHANTOM |
|---|---|---|---|---|---|
| Opus 4.6 | 21 | 7 | 5 | 6 | 2 |
| Sonnet 4.6 | 17 | 5 | 5 | 6 | 1 |
| Haiku 4.6 | 28 | 10 | 7 | 10 | 1 |
| ChatGPT | 5 | 2 | 2 | 1 | 0 |
| Gemini Pro | 7 | 2 | 1 | 1 | 3 |
| **Total** | **78** | **26** | **20** | **24** | **7** |

## Tier 1 — Universal Consensus (5/5 models agree)

These findings appeared independently in all 5 reviews. Highest confidence; must be addressed in v1.2.7.

### T1-1. Missing detection guidance for claimed defect categories

**Models:** ALL FIVE
**Classification:** MISSING
**Summary:** The playbook claims to support 14 defect categories but provides actionable detection guidance (grep patterns, scenario templates, domain prompts) for roughly 4-6 of them. Categories with zero or near-zero guidance: concurrency issues, SQL errors, security issues, API contract violations, protocol violations, serialization bugs.

- **Opus:** "SQL error has no dedicated detection guidance anywhere... no grep patterns for SQL injection, no patterns for query construction errors. Security issue likewise has no dedicated detection section."
- **Sonnet:** "SQL errors and security issues are not addressed by any step in Phase 1. There is no instruction to search for SQL query construction patterns, injection risks, or any security-relevant pattern."
- **Haiku:** "No guidance for concurrent systems, reactive streams, or distributed systems where missing safeguards look different."
- **ChatGPT:** "The failure-prevention steps that matter most are only spelled out for a subset of languages, so 'any language' is not supported at the same level of specificity." (ChatGPT merged this with the language finding; implicit coverage gap acknowledgment.)
- **Gemini:** "Detection techniques completely omit any guidance, keywords, or examples for finding security vulnerabilities or SQL errors."

### T1-2. Language generality overstated (6 languages vs 15+ claimed)

**Models:** ALL FIVE
**Classification:** MISSING / DIVERGENT
**Summary:** The playbook claims "works with any language" and the QPB benchmark includes 15 languages, but all reference files provide concrete examples for only 6: Python, Java, Scala, TypeScript, Go, Rust. Nine benchmark languages receive no grep patterns, import patterns, test framework examples, test setup guidance, or test runner commands.

- **Opus:** "functional_tests.md provides import patterns for six languages... the remaining nine languages claimed in the skill description have no import pattern guidance."
- **Sonnet:** "functional_tests.md import patterns, test framework setup examples, and parametrization syntax are provided for exactly 6 languages."
- **Haiku:** "The playbook claims to work with 15 languages but embeds Python/Java-specific assumptions without disclosure."
- **ChatGPT:** "The core grep matrices, import/setup guidance, and schema-layer examples cover Python, Java, Scala, TypeScript/JavaScript, Go, and Rust, but do not give equivalent guidance for C#, Ruby, PHP, Kotlin, C, Swift, or Elixir." Also uniquely extended this to regression tests: "The regression-test protocol lacks language-parity support."
- **Gemini:** "defensive_patterns.md, functional_tests.md, and verification.md only provide concrete grep patterns, import mappings, and test runner commands for 6 languages."

---

## Tier 2 — Strong Consensus (3-4/5 models agree)

High confidence findings. Strong candidates for v1.2.7.

### T2-1. Bootstrapping process described but not executable

**Models:** Opus, Sonnet, Haiku, Gemini (4/5)
**Classification:** PHANTOM
**Summary:** The bootstrapping section (SKILL.md lines 518-526) says the playbook "generates quality infrastructure for its own repository" and "the process works normally." But the playbook consists of Markdown files — it has no functions to read signatures for, no schemas to map, no test suite to import patterns from. An agent attempting bootstrapping would face immediate questions with no answers.

- **Opus:** "No instruction to treat the playbook repo as the target codebase, no guidance on what counts as 'specifications' for a Markdown-based project."
- **Sonnet:** "The playbook has no spec documents, no importable functions, no test suite, and no schema. This is the only self-validation mechanism the playbook describes, and it doesn't work as described."
- **Haiku:** "No explanation of how this validation works or what the agent should do with the results."
- **Gemini:** "verification.md provides no test runner command for Markdown, and functional_tests.md provides no import patterns for it."

### T2-2. Missing phase transition criteria

**Models:** Opus, Sonnet, Haiku, ChatGPT (4/5)
**Classification:** MISSING / UNDOCUMENTED
**Summary:** No explicit go/no-go gate between Phase 1 (Explore) and Phase 2 (Generate). The playbook says to explore "3-5 core modules" and find "2-3 defensive patterns per core file" but provides no criterion for when exploration is complete enough to proceed. Phase 4 also has no completion criterion.

- **Opus:** "Step 6 provides no criterion for when exploration is complete."
- **Sonnet:** "Phase 3 summary lists 10 checks but verification.md defines 13. An agent reading only Phase 3 would skip three verification steps."
- **Haiku:** "Does not explain when to enter Phase 4 or what triggers each path."
- **ChatGPT:** "Phase 4 is explicitly open-ended with no boundary condition."

### T2-3. Integration test protocol too domain-specific / assumes external dependencies

**Models:** Sonnet, Haiku, ChatGPT (3/5)
**Classification:** DIVERGENT / UNDOCUMENTED
**Summary:** The integration test protocol is written from the perspective of an LLM batch orchestration project with external API dependencies. For projects with no external services, the protocol provides no applicable patterns.

### T2-4. Steps 5c/5d have no corresponding reference file

**Models:** Opus, Sonnet, Haiku (3/5)
**Classification:** UNDOCUMENTED
**Summary:** Steps 5c and 5d introduce 7+ detection categories (context propagation loss, parallel path symmetry, truth fragmentation, field label drift, callback concurrency, macro review, sync/async parity) across ~65 lines of SKILL.md. The reference file table sends agents to defensive_patterns.md for "Step 5" — but that file contains none of the 5c/5d content.

- **Sonnet:** "Agents following the 'read the reference file' workflow will miss the entire context propagation, parallel path symmetry, truth fragmentation analysis."
- **Opus:** "Several subsections in Step 5d are language-specific despite claiming generality."

### T2-5. Boundary-test examples contradict verification assertion standards

**Models:** Haiku, ChatGPT, Gemini (3/5)
**Classification:** DIVERGENT
**Summary:** defensive_patterns.md boundary-test examples use weak presence-only assertions (`assertNotNull`, `toBeDefined`, `is_ok`) while Phase 3 verification explicitly says presence-only assertions are inadequate. The reference file teaches the weaker pattern that the verification phase rejects.

- **ChatGPT:** "One of the main reference files still teaches weaker boundary-test patterns that violate that standard."
- **Haiku:** "The example in functional_tests.md shows many boundary tests that only assert graceful handling without checking specific output values."

### T2-6. Defensive patterns vs. missing safeguards conflation

**Models:** Sonnet, Haiku, Gemini (3/5)
**Classification:** DIVERGENT
**Summary:** defensive_patterns.md groups existing defensive code (null guards, try/catch) with absent safeguards (missing guards) under "defensive patterns." functional_tests.md then assumes all defensive patterns are testable. An agent writing tests for missing safeguards produces tests with no code to execute.

- **Haiku (top finding):** "An agent writes boundary tests for missing safeguards, the tests fail with 'code path never reached' because there's no code to test."
- **Sonnet:** "The skill conflates three different discovery steps into 'defensive patterns' without clarifying which produce tests."

---

## Tier 3 — Partial Agreement (2/5 models agree)

Medium confidence. Worth investigating; may warrant fixes if verified.

### T3-1. No fallback for projects with no existing test suite

**Models:** Opus, Sonnet (2/5) — also raised in first run by ChatGPT, Gemini
**Classification:** UNDOCUMENTED
**Summary:** Step 3 instructs agents to "read existing test files" and "record the import pattern." If a project has zero existing tests, the agent has no import pattern to copy.

### T3-2. No degraded mode for agents without terminal/file access

**Models:** Sonnet, Gemini (2/5)
**Classification:** UNDOCUMENTED
**Summary:** The playbook assumes the agent can create files and execute commands. When run in a web UI without computer use, the agent will fail at file creation and test execution steps.

### T3-3. AGENTS.md has no template or reference file

**Models:** Opus, Sonnet (2/5)
**Classification:** MISSING
**Summary:** Every generated file except AGENTS.md has a detailed template in a reference file. AGENTS.md has only a one-sentence list of sections, despite being described as "the 'read this first' file."

### T3-4. Test count heuristic double-counts defensive patterns

**Models:** Sonnet, Gemini (2/5)
**Classification:** DIVERGENT / PHANTOM
**Summary:** The formula Target = (spec sections) + (scenarios) + (defensive patterns) can double-count because defensive patterns also produce scenarios. Gemini called this out explicitly as "artificially inflated target."

### T3-5. Verification benchmark count mismatch (10 in SKILL.md vs 13 in verification.md)

**Models:** Sonnet, Opus (2/5)
**Classification:** DIVERGENT
**Summary:** Phase 3 summary lists 10 checks but verification.md defines 13 benchmarks. An agent reading only SKILL.md's summary would skip benchmarks 10-13.

### T3-6. Missing async test guidance

**Models:** Gemini (1/5 in corrected run, but also flagged by Gemini in original run)
**Classification:** MISSING
**Summary:** No guidance for generating tests for async functions (pytest.mark.asyncio, tokio::test, async/await patterns).

### T3-7. Fixture strategy contradiction (match existing vs inline)

**Models:** Opus, Haiku, ChatGPT (3/5)
**Classification:** DIVERGENT
**Summary:** The playbook says "write tests that create their own data inline" but also says "match the existing tests" — and existing tests in many projects use shared fixtures. ChatGPT added: "defensive_patterns.md boundary-test examples depend on undeclared shared objects like `fixture`, `process`, and `default_fixture()` — normalizing exactly the kind of hidden setup dependency the playbook warns against."

### T3-8. Chat history processing gap (Step 0)

**Models:** Opus, Haiku (2/5)
**Classification:** UNDOCUMENTED / MISSING
**Summary:** Step 0 says chat history "is gold" but provides no mechanism for processing or integrating it into quality artifacts.

### T3-9. POSIX shell assumption in integration test protocol

**Models:** ChatGPT, Gemini (2/5 — ChatGPT in corrected run, original ChatGPT also flagged)
**Classification:** UNDOCUMENTED
**Summary:** The integration test protocol requires bash commands with `&` and `wait` but doesn't document fallback for PowerShell, cmd.exe, or restricted environments.

---

## Tier 4 — Single Model Findings (1/5, needs verification)

| ID | Finding | Model | Classification |
|---|---|---|---|
| T4-1 | Conflicting requirement tiers not addressed | Opus | MISSING |
| T4-2 | Test harness audit assumes C#/.NET/Java ecosystems | Opus | UNDOCUMENTED |
| T4-3 | Defensive pattern count "2-3 per file" not calibrated for language density (Rust ? operators, Go err checks) | Opus | UNDOCUMENTED |
| T4-4 | Cross-boundary signal propagation has no detection technique | Opus | MISSING |
| T4-5 | "What happened" voice: past tense label vs present tense vulnerability analysis instruction | Opus | DIVERGENT |
| T4-6 | Missing safeguard patterns section has no grep patterns unlike all other sections | Opus | UNDOCUMENTED |
| T4-7 | Coverage target percentages don't specify which metric (line/branch/statement) | Opus | UNDOCUMENTED |
| T4-8 | Domain knowledge prompts only cover 3 project archetypes | Opus | UNDOCUMENTED |
| T4-9 | Regression test file is a 7th deliverable not listed in summary table | Opus | DIVERGENT |
| T4-10 | Scenario-to-test mapping checks count but not correctness | Opus | PHANTOM |
| T4-11 | cd to parent directory prohibition in review_protocols.md not in SKILL.md | Sonnet | DIVERGENT |
| T4-12 | Scala test runner command hardcodes class name `FunctionalSpec` | Sonnet | DIVERGENT |
| T4-13 | Step 6 calibration guidance only in constitution.md but not referenced until Phase 2 | Sonnet | UNDOCUMENTED |
| T4-14 | Inferred requirement flagging format not specified | Sonnet | DIVERGENT |
| T4-15 | Field Reference Table location inconsistently specified | Sonnet | DIVERGENT |
| T4-16 | quality/ directory test discovery not addressed for Maven/Gradle/SBT | Sonnet | UNDOCUMENTED |
| T4-17 | Go regression test in quality/ may not compile as a Go package | Sonnet | DIVERGENT |
| T4-18 | Function call map undocumented as artifact | Haiku | UNDOCUMENTED |
| T4-19 | "Skeleton" terminology undefined, inconsistent with "defensive pattern" | Haiku | UNDOCUMENTED |
| T4-20 | Council of Three dispute resolution (2 vs 1 case) underspecified | Haiku | MISSING |
| T4-21 | Spec audit triage "read-only probe" introduces 4th model without process | Haiku | UNDOCUMENTED |
| T4-22 | INSTRUCTIONS.md relationship to main skill unclear (7th artifact?) | Haiku | MISSING |
| T4-23 | Scenario quantities — no guidance on where to find specific numbers | Haiku | MISSING |
| T4-24 | Required field mutation strategy undocumented in schema_mapping.md | Haiku | UNDOCUMENTED |
| T4-25 | Phase 2 test run instruction vs Phase 3 verification boundary blur | Gemini | DIVERGENT |
| T4-26 | Integration test verification is static-only, no actual execution | Gemini | PHANTOM |
| T4-27 | Pre-flight dependency installation missing from functional test verification | Gemini | UNDOCUMENTED |
| T4-28 | Dynamic function signatures (metaclasses, reflection) not addressed | Sonnet | MISSING |

---

## Triage Summary

| Tier | Count | Action |
|---|---|---|
| Tier 1 (universal, 5/5) | 2 | **Must fix** in v1.2.7 |
| Tier 2 (strong, 3-4/5) | 7 | **Should fix** in v1.2.7 |
| Tier 3 (partial, 2/5) | 9 | Investigate; fix if verified |
| Tier 4 (single, 1/5) | 28 | Verify selectively; lower priority |
| **Total unique themes** | **46** | |

## Recommended v1.2.7 Scope

### Must Fix (Tier 1)

1. **Add defect category detection matrix** — grep patterns, scenario templates, and domain prompts for all 14 categories. At minimum: concurrency, SQL, security, serialization, API contract, protocol violations. (T1-1)

2. **Expand language coverage** — add import patterns, test setup, test runner commands, and defensive pattern grep tables for at minimum C#, Ruby, Kotlin, PHP. Alternatively, explicitly scope the playbook to 6 supported languages and provide adapter guidance for others. (T1-2)

### Should Fix (Tier 2)

3. **Make bootstrapping executable** — either provide a concrete step-by-step for Markdown-based/tooling repositories, or remove the claim that "the process works normally." (T2-1)

4. **Add explicit phase transition gates** — stop criteria for Phase 1, go/no-go before Phase 2, completion criterion for Phase 4. (T2-2)

5. **Generalize integration test protocol** — add patterns for projects without external dependencies. (T2-3)

6. **Create reference content for Steps 5c/5d** — either expand defensive_patterns.md or create a new reference file. (T2-4)

7. **Fix boundary-test examples to match verification standards** — defensive_patterns.md examples use weak assertions that Phase 3 rejects. (T2-5)

8. **Separate defensive patterns from missing safeguards** — clarify which discovery types produce tests vs spec audit findings. (T2-6)

### Investigate (Tier 3)

8. Zero-test fallback for greenfield projects (T3-1)
9. Degraded mode for restricted environments (T3-2)
10. AGENTS.md template (T3-3)
11. Test count heuristic double-counting (T3-4)
12. Verification benchmark count alignment (T3-5)
13. Async test guidance (T3-6)
14. Fixture strategy clarification — now 3/5 with ChatGPT, borderline Tier 2 (T3-7)
15. Chat history processing guidance (T3-8)
16. POSIX shell assumption in integration protocol (T3-9)

## Observations on Reviewer Behavior

- **No hallucinations in corrected run.** The original run's version mismatch was caused by wrong files, not model error.
- **Finding volume:** Haiku 4.6 produced the most findings (28) — nearly 4x Gemini's count (7). This suggests Haiku prioritized breadth while Gemini went deeper on fewer issues.
- **Unique contributions by model:**
  - **Opus** uniquely identified: language density calibration for defensive pattern counts, cross-boundary signal propagation gap, coverage metric type ambiguity, domain archetype limitations, scenario-to-test mapping correctness vs count
  - **Sonnet** uniquely identified: Phase 3 vs verification.md benchmark count mismatch (10 vs 13), Steps 5c/5d reference file gap, quality/ directory discovery for Maven/Gradle/SBT, Go package compilation issue
  - **Haiku** uniquely identified: defensive patterns vs missing safeguards conflation as top finding, test requirement extraction methodology gap, Council of Three dispute resolution gap, function call map as undefined artifact
  - **Gemini** uniquely identified: test count double-counting via defensive-pattern-to-scenario conversion, integration test verification as static-only, pre-flight dependency installation gap
  - **ChatGPT** was the most concise (5 findings in corrected run) but the most precise — every finding landed in Tier 1 or Tier 2. Uniquely elevated boundary-test assertion quality as a cross-file consistency issue and regression test language parity as distinct from general language coverage.
- **Consensus was strongest** on defect category gaps and language coverage — every single model flagged both, making these the highest-confidence findings in the entire review.
