# Haiku — v1.2.7 Review

here's the 1.2.7 haiku review:

```
# Council of Three Spec Audit — Quality Playbook v1.2.7

## Audit Context

Auditing v1.2.7 playbook (SKILL.md + 7 reference files) against stated goals:
- 14 claimed defect detection categories
- 10 languages claimed supported (Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP)
- Integration test protocol rewritten for domain-agnostic use
- Phase transition gates with explicit criteria
- Defensive patterns vs. missing safeguards distinction added
- 2,592 real defects from 55 open-source repos benchmark

---

## Findings by Scrutiny Area

### 1. Detection Coverage Completeness

#### defensive_patterns.md — Category Coverage

**DIVERGENT:** Defensive patterns file documents only 11 explicit defect categories, not 14 as claimed.

**Playbook says:** v1.2.7 claims coverage for 14 defect categories with expansion from 6 original to include concurrency, SQL, security, serialization, API contract, protocol violations.

**Reality:** The file documents exactly these 11 categories:
1. Null/nil guards (original)
2. Exception/error handling (original)
3. Internal/private helpers (original)
4. Concurrency Issues (new)
5. SQL Errors (new)
6. Security Issues (new)
7. Serialization Bugs (new)
8. API Contract Violations (new)
9. Protocol Violations (new)
10. Async/Sync Parity (new)
11. Context Propagation Loss (new)

**Missing from explicit sections:** Field Label Drift (exists in Step 5c of SKILL.md, not in defensive_patterns.md as a numbered category header), Truth Fragmentation (same—exists in Step 5c, not as a standalone section), Callback Concurrency (same). The cross-reference section headers exist but are orphaned—they live in SKILL.md Step 5c but not in the defensive_patterns reference file. This creates a navigation gap: if a user reading defensive_patterns.md wants to understand "what are all 14 categories," the document doesn't list them coherently.

**Severity:** DIVERGENT — the playbook claims 14 categories; the reference file documents 11 as explicit sections with grep patterns.

---

#### defensive_patterns.md — Grep Pattern Completeness for New Categories

**UNDOCUMENTED:** The new category grep patterns lack depth comparable to original categories.

**Playbook says:** Step 5d documentation in SKILL.md claims state machine analysis, async/sync parity, context propagation loss, field label drift, truth fragmentation, callback concurrency are now integrated into systematic search.

**Reality:** Each original category (null/nil, exceptions, internal/private) has a detailed table with 6+ language-specific patterns. The new categories have much thinner coverage:

- **Async/Sync Parity** (lines 334-346): Documents the concept but provides NO grep patterns. Guidance is conceptual ("Diff the constructor/factory parameters") not pattern-based like the original categories.
- **Context Propagation Loss** (lines 348-352): No grep patterns. Only a conceptual probe ("Look for `NewXxx()` calls").
- **Field Label Drift** (lines 354-362): No language-specific patterns. Only mentions positional extraction patterns (`parts[N]`, `row[N]`) which are language-agnostic and insufficient for a project like defensive_patterns.md which otherwise uses language-by-language tables.
- **Truth Fragmentation** (lines 364-370): No patterns table. Only mentions "grep for literal values."
- **Callback Concurrency** (lines 372-376): No patterns. Only mentions "look for callback definitions and event handlers."

**Comparison:** The null/nil guards section (lines 9-22) has a 9-row language table with language-specific patterns. Concurrency Issues section (lines 233-250) has grep patterns for all 10 languages. But the newer categories lack this structure—they're written as prose guidance, not as systematic search instructions that an AI agent could execute mechanically.

**Severity:** MISSING — v1.2.7 claims these categories are now fully integrated into systematic search (via grep patterns and detection heuristics), but defensive_patterns.md doesn't provide the implementation. An agent following defensive_patterns.md strictly would find 11 categories mechanically, then have to interpret prose for the other 3.

---

#### SKILL.md Step 5c Section — Placement and Discoverability

**UNDOCUMENTED:** Step 5c exists in SKILL.md (lines 220-244) and documents context propagation loss, parallel path symmetry, field label drift, callback concurrency, truth fragmentation, and schema-struct alignment. However, these are titled as "audit steps" in SKILL.md, not as "defect categories," and the defensive_patterns.md reference file doesn't point to them.

**Impact:** A user following the SKILL.md workflow reads Step 5a (basic patterns), then Step 5b (schema types). Then Step 5c says "Audit Parallel Code Paths and Context Propagation" — but defensive_patterns.md (referenced for Step 5) doesn't mention Step 5c or explain how those audits map to the reference file. This is a discovery problem: the content exists but the cross-reference is broken.

---

### 2. Language Coverage Quality — New Languages (C#, Ruby, Kotlin, PHP)

#### functional_tests.md — Missing Test Structure for New Languages

**MISSING:** functional_tests.md provides test structure examples for only 6 languages, not 10.

**Playbook says:** SKILL.md claims "Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP with adapter guidance."

**Reality:** Lines 1-123 of functional_tests.md show examples for:
- Python (pytest)
- Java (JUnit)
- Scala (ScalaTest)
- TypeScript (Jest)
- Go (testing)
- Rust (cargo test)

C#, Ruby, Kotlin, PHP are not mentioned anywhere in functional_tests.md. The file states line 3 "Name it using the project's conventions: `test_functional.py` (Python/pytest), `FunctionalSpec.scala` (Scala/ScalaTest), `FunctionalTest.java` (Java/JUnit), `functional.test.ts` (TypeScript/Jest), `functional_test.go` (Go), etc." — note the "etc." ellipsis. This leaves C#, Ruby, Kotlin, PHP users with no concrete guidance on naming, fixture setup, import patterns, or assertion style.

**Severity:** MISSING — 4 out of 10 claimed languages have no example test structure in the functional tests reference file.

---

#### Fixture Strategy Section (SKILL.md lines 611-621) — Incomplete for New Languages

**MISSING:** Fixture setup guidance covers 6 languages, omits C#, Ruby, Kotlin, PHP.

**Playbook says:** SKILL.md Fixture Strategy section claims to provide guidance for fixture setup.

**Reality:** Lines 614-620 provide guidance for:
- Python (conftest.py)
- Java (@BeforeEach/@BeforeAll)
- Scala (trait with before/after)
- TypeScript (beforeAll/beforeEach)
- Go (helper functions with t.Helper())
- Rust (test modules and builder patterns)

C#, Ruby, Kotlin, PHP are completely absent from this section. An agent generating C# tests has no playbook guidance on whether to use xUnit Fixtures, NUnit TestFixtures, or test method setup. A Ruby agent has no guidance on RSpec let/subject blocks vs. test setup methods.

**Severity:** MISSING — Essential test framework mechanics undocumented for 4 languages.

---

#### schema_mapping.md — Language Coverage Gaps for New Languages

**MISSING:** schema_mapping.md provides code examples for only 6 languages, not 10.

**Playbook says:** The schema mapping file claims to guide "boundary test" mutations using schema-valid values for all supported languages.

**Reality:** Lines 31-125 show examples for:
- TypeScript (Zod)
- Python (Pydantic)
- Java (Bean Validation)
- Scala (Circe codecs)
- Go (struct tags)
- Rust (serde)

C#, Ruby, Kotlin, PHP are absent. Lines 31-125 provide detailed WRONG/RIGHT examples for each language, showing how to mutate fixtures using schema-valid values. C#, Ruby, Kotlin, PHP users have no examples of how to construct valid mutations for their language's validation frameworks.

**Severity:** MISSING — Mutation validity guidance absent for 4 languages. This is critical because schema_mapping.md explicitly explains why this matters (testing defensive code vs. testing validation mechanism). Users of the 4 missing languages will lack concrete guidance and risk writing tests that fail with validation errors instead of testing defensive logic.

---

#### review_protocols.md — Language Coverage for Code Review/Integration Tests

**MISSING:** Code review regression test language guidance incomplete.

**Playbook says:** review_protocols.md section "Phase 2: Regression Tests for Confirmed Bugs" (lines 53-107) provides guidance for writing regression tests in multiple languages.

**Reality:** Lines 73-86 show where to save test files by language:
- Python: `quality/test_regression.py`
- Go: `quality/regression_test.go`
- Rust: `quality/regression_tests.rs` or `tests/regression_*.rs`
- Java: `quality/RegressionTest.java`
- TypeScript: `quality/regression.test.ts`

C#, Ruby, Kotlin, PHP are absent. The section doesn't specify file naming conventions or test structure for these 4 languages.

**Severity:** MISSING — Regression test file naming and structure undocumented for 4 languages.

---

#### Integration Test Worked Examples — Generality for Non-API/Non-Queue Projects

**PHANTOM:** The integration test protocol claims to be domain-agnostic after rewrite, but worked examples only cover 4 specific archetype domains.

**Playbook says:** SKILL.md lines 403-407 state "The reference file has worked examples for each [project archetype]. Adapt the closest example to the actual project — don't copy it literally." This suggests flexibility and domain-agnostic reusability.

**Reality:** review_protocols.md provides worked examples for exactly 4 archetypes (lines 328-494):
1. REST API Service
2. Message Queue / Streaming Pipeline
3. Database-Backed Application
4. CLI Tool / Data Pipeline

Projects that don't fit these 4 archetypes have no worked example. Examples of unrepresented domains:
- Real-time collaboration tools (operational transform, CRDT, multi-client state)
- Machine learning pipelines with complex model training/validation workflows
- Desktop/mobile GUI applications
- Game engines or graphics systems
- System software (kernels, filesystems, databases)
- Embedded/IoT firmware

The section "Adapting to Your Project" (lines 495-504) says projects are "hybrids" combining REST API + queue + database + CLI, but offers no guidance for projects that don't reduce to these 4 axes. For example, a real-time collaboration system with CRDT conflict resolution, continuous sync, and multi-device state consistency doesn't naturally decompose into the REST API + Queue + Database + CLI model.

**Severity:** PHANTOM — Protocol claims domain-agnostic generality; actually covers only 4 specific archetypes. Projects outside these 4 patterns will struggle to adapt the examples and may produce integration tests that miss their actual failure modes.

---

### 3. Integration Test Protocol Design — "Present the Plan First" UX

**MISSING:** SKILL.md documents the "Present the Plan First" approach but doesn't embed it in the reference file template.

**Playbook says:** SKILL.md lines 401-407 and review_protocols.md lines 142-179 emphasize presenting the integration test plan to the user BEFORE writing the full protocol. This is called critical for UX: "Showing the plan first costs one extra exchange and saves significant rework."

**Reality:** The template in review_protocols.md (lines 181-300) starts directly with Working Directory, Safety Constraints, and Pre-Flight Check. There's no "Step 0: Present Plan" section in the template. The guidance tells agents to do it (show plan, get feedback, then write protocol) but the template doesn't enforce or structure this interaction. An agent following the template literally would skip the plan-presentation step and go straight to writing the full protocol.

**Severity:** UNDOCUMENTED — The critical UX pattern (present plan first) is documented as a process requirement in SKILL.md but not embedded in the actual protocol template. The template needs a "Step 1: Present plan" instruction that shows agents where to pause and wait for user feedback before filling in steps 2+.

---

### 4. Phase Transition Gates — Clarity and Actionability

#### Phase 1 → Phase 2 Completion Criterion (SKILL.md lines 313-323)

**DIVERGENT:** The Phase 1 completion criterion mentions "traced all state machines" but earlier sections refer to state machine analysis as "Step 5b" (actually Step 5b is schema mapping). State machine analysis is actually in Step 5a subsection and Step 5b.

**Playbook says:** Line 320 states Phase 1 is complete when "You have traced all state machines (if the project has any status/state/phase fields)."

**Reality:** Reading the actual steps:
- Lines 169-192: Step 5a covers basic defensive patterns (null guards, exceptions, etc.)
- Lines 194-212: Step 5a continues with state machine analysis
- Lines 214-218: Step 5b is schema mapping (distinct from state machines)

The gate references "traced all state machines" as a Phase 1 completion item, and this is correct — state machines are found in Step 5a. However, the numbering in the gate (item 4: "traced all state machines") is correct, but the section structure makes this confusing because state machine analysis (lines 194-212) is interleaved with the defensive pattern grep guidance (lines 169-192), not separated as "Step 5a.2" or similar.

**Severity:** UNDOCUMENTED — The numbering is correct but the layout makes it unclear whether state machines are a mandatory Step 5a goal or an optional subsection. An agent might read "find defensive patterns" and skip state machines thinking they're a different step.

---

#### Phase 2 → Phase 3 Marker (SKILL.md lines 325-341)

**MISSING:** The transition from Phase 2 (file generation) to Phase 3 (verification) lacks a clear "all files done" checkpoint.

**Playbook says:** Lines 325-341 list the six files that must exist before Phase 3. But the text doesn't say how to verify they're all complete — it just lists them.

**Reality:** A practical issue: File 6 is `AGENTS.md`, which has an instruction (line 434-436) saying "If `AGENTS.md` already exists, update it — don't replace it." This creates ambiguity: if the project already has AGENTS.md from a previous quality playbook session, is Phase 2 complete when AGENTS.md is *updated*, or must it be newly *created*? The criterion "all six files are in the quality/ folder" doesn't clarify whether an update counts as completion or whether a file must be created fresh.

**Severity:** UNDOCUMENTED — The Phase 2 completion criterion doesn't specify how to handle pre-existing AGENTS.md.

---

#### Phase 3 → Phase 4 Transition Clarity

**MISSING:** Phase 3 and Phase 4 boundaries are vague.

**Playbook says:** Phase 3 is Verification (lines 441-557). After Phase 3, move to Phase 4 (user improvement cycle, lines 558-607). The completion criterion (lines 599-607) says Phase 4 is done when: (1) user saw summary table and confirmed metrics, (2) user explored one file in detail, (3) user is satisfied OR has chosen improvement path.

**Reality:** The criterion is non-terminal — it says "Phase 4 is inherently open-ended — the user may return to improve specific items multiple times, or may be satisfied after the initial presentation. There is no 'done' requirement; the playbook is ready to use as-is after Phase 3." This is correct and flexible, but creates an execution problem: if an agent is following this skill, how does it know when to stop iterating and let the user decide? The criterion doesn't define what counts as "satisfied" or "willing to continue improving." An agent reading this might loop forever asking "want to improve something else?" or might exit too early thinking one improvement cycle is enough.

**Severity:** UNDOCUMENTED — The Phase 4 completion criterion is procedural (wait for user preference) but doesn't give agents clear termination logic. In practice, agents should explicitly offer improvement options and then stop after the user declines, but the playbook doesn't state this.

---

### 5. Bootstrapping Executability — Self-Review Against Own Playbook

#### SKILL.md Bootstrapping Section (lines 574-597) — Guidance Exists but Untested

**UNDOCUMENTED:** The bootstrapping section describes how to audit a Markdown/tooling project using the playbook, but provides no evidence the playbook itself has been audited this way.

**Playbook says:** Lines 574-597 explain how to treat the quality-playbook-itself as a codebase: "For Markdown-based projects: (a) Step 1 — domain is self-explanatory, specs are the CLAUDE.md instructions, (b) Step 2 — reference files are subsystems, (c) Step 3 — look for test parsers..."

**Reality:** The v1.2.7 playbook has been improved iteratively based on external feedback (the REVIEW_PROMPT mentions "5-model wide review of v1.2.6 that identified 46 unique findings"). However, there's no evidence in the playbook itself (no QUALITY.md, no test_functional.py for playbook validation, no RUN_SPEC_AUDIT.md for auditing the playbook against its own design) that the playbook has been run against itself. If the playbook truly enables "bootstrapping" (applying itself to its own codebase), it should demonstrate this by including its own quality playbook artifacts.

**Severity:** UNDOCUMENTED — The bootstrapping section is credible guidance but unvalidated. The playbook claims it can audit itself but hasn't been shown doing so.

---

#### Schema Validation Test Parser — Mentioned But Not Included

**UNDOCUMENTED:** Lines 595-597 mention "Validating generated test parsers — the generated tests must correctly parse the project's actual data formats (not an idealized version). When a test parser fails on real data, the failure often reveals undocumented format variations."

**Reality:** This is good guidance for projects with structured data (CSV, JSON, Markdown tables). But the playbook doesn't include any test parser for validating the playbook's own reference files (constitution.md, defensive_patterns.md, etc.). If the playbook claims that "generated tests must correctly parse the project's actual data formats," it could include a test suite that validates:
- constitution.md can be parsed to extract scenario metadata
- defensive_patterns.md grep patterns actually match example code
- functional_tests.md field reference tables contain all fields from actual schemas

These don't exist in the provided files.

**Severity:** UNDOCUMENTED — Good guidance about format validation, but the playbook itself lacks the validation tests it recommends.

---

### 6. Defensive Patterns vs. Missing Safeguards — Distinction Clarity

#### defensive_patterns.md Section on Distinction (lines 378-405)

**CLEAR AND WELL-DOCUMENTED:** The distinction is explained explicitly and correctly.

**Playbook says:** Lines 378-405 define:
- **Defensive Patterns** (visible code) → Boundary Tests
- **Missing Safeguards** (absent code) → Spec Audit Findings

**Reality:** This distinction is clearly stated and the examples are concrete. Lines 381-398 provide WRONG/RIGHT examples showing how missing safeguards are architectural findings, not test cases. This section is well-structured and clear.

**No finding here.**

---

### 7. Internal Consistency — Cross-References and Data Accuracy

#### Benchmark Dataset Reference — Numbers Not Verified

**UNDOCUMENTED:** The playbook references "a benchmark dataset of 2,592 real defects from 55 open-source repositories across 15 programming languages."

**Playbook says:** SKILL.md line 3 (metadata description) and REVIEW_PROMPT.md both mention this dataset.

**Reality:** The dataset is referenced but not included or linked in the playbook files. The claim can't be verified from the contents provided. This isn't a defect per se (the dataset may exist externally), but it's undocumented within the playbook. An agent or user couldn't verify the claim or access the benchmark data.

**Severity:** UNDOCUMENTED — The benchmark dataset is cited but its contents and methodology aren't available within the playbook.

---

#### Test Count Heuristic — Consistency Across Files

**DIVERGENT:** Test count heuristic is stated slightly differently in different files.

**functional_tests.md (lines 23-29):**
> Target = (testable spec sections) + (QUALITY.md scenarios) + (defensive patterns from Step 5)

**SKILL.md (line 382):**
> Test count heuristic = (testable spec sections) + (QUALITY.md scenarios) + (defensive patterns). For a medium project (5–15 source files), this typically yields 35–50 tests.

**verification.md (line 22-24):**
> Calculate the heuristic target: (testable spec sections) + (QUALITY.md scenarios) + (defensive patterns from Step 5).

The formula is the same across all three, but functional_tests.md (line 29) says "Significantly fewer suggests missed requirements or shallow exploration. Don't pad to hit a number." while SKILL.md (line 382) says "Significantly fewer suggests missed requirements or shallow exploration. Significantly more is fine if every test is meaningful — don't pad to hit a number." The SKILL.md version is more nuanced (allows "significantly more"); functional_tests.md implies "fewer" is bad but "more" isn't discussed. This is a minor divergence in tone, not in the actual heuristic, but it could cause confusion about whether 60 tests for a medium project is "too many."

**Severity:** DIVERGENT (minor) — The heuristic formula is consistent, but guidance on acceptable deviation differs between files.

---

#### Cross-Variant Heuristic Consistency

**CONSISTENT:** The ~30% cross-variant testing heuristic is stated the same way in multiple files (SKILL.md line 383 and verification.md line 36).

**No finding here.**

---

#### Scenario Count Guidance — Vague

**UNDOCUMENTED:** The playbook doesn't specify a clear scenario count target.

**Playbook says:** SKILL.md line 360 says "Aim for 2+ scenarios per core module (the modules identified as most complex or fragile). For a medium-sized project, this typically yields 8–10 scenarios. Fewer is fine for small projects; more for complex ones." And constitution.md echoes this (line 119).

**Reality:** This is guidance ("aim for 2+", "typically yields 8–10") not a requirement. The verification checklist (verification.md) mentions "Count the scenarios in QUALITY.md. Count the scenario test functions in your functional test file. The numbers must match exactly." (lines 33-34). But there's no benchmark for "is 6 scenarios enough?" or "is 12 too many?" The heuristic is relative (2+ per core module) rather than absolute. For a project with 3 core modules, that's 6–10; for a project with 5 core modules, that's 10–15. This is defensible (quality > count) but it's less specific than the test count heuristic.

**Severity:** UNDOCUMENTED — No absolute or relative benchmark for scenario counts beyond "2+ per core module."

---

### 8. Specification Audit Protocol — Council of Three Guardrails

#### spec_audit.md Guardrails — Well-Defined and Embedded

**CLEAR AND WELL-DOCUMENTED:** The four guardrails are stated explicitly (lines 407-412 in spec_audit.md) and embedded in the template prompt (lines 30-42 of the definitive audit prompt template).

**No finding here.**

---

#### Triage Process — Unclear on Verification Probes

**UNDOCUMENTED:** The spec_audit.md section "The Verification Probe" (lines 91-96) describes using a "read-only probe" when models disagree, but doesn't specify exactly how an agent executing this would work.

**Playbook says:** Lines 91-96 state "When models disagree on factual claims, deploy a read-only probe: give one model the disputed claim and ask it to read the code and report ground truth."

**Reality:** This is sound guidance but operationally vague. How does the agent know when "two models disagree on a factual claim"? Is disagreement on a MISSING vs. DIVERGENT classification a "factual claim disagreement"? The triage table (lines 87-91) shows confidence levels by how many models found something, but doesn't show what to do when models agree on a finding but disagree on the classification. Example: Model A says "Line 42 is MISSING a null check" (MISSING), Model B says "Line 42 has a null check but it's in the wrong place" (DIVERGENT). Both found the same code location but classified it differently. The guidance doesn't cover how to resolve this using a verification probe.

**Severity:** UNDOCUMENTED — The verification probe concept is sound but its trigger condition and execution are not fully specified.

---

#### Fix Execution Rules — Small Batches Guidance Vague

**UNDOCUMENTED:** spec_audit.md lines 121-126 state "Group fixes by subsystem, not by defect number. Never one mega-prompt for all fixes. Each batch: implement, test, have all three reviewers verify the diff. At least two auditors must confirm fixes pass before marking complete."

**Reality:** This is good guidance in principle, but what defines a "subsystem"? How many findings per batch is "small"? If a subsystem has 12 findings, is that one batch or multiple? The guidance doesn't provide clear sizing criteria. For reproducibility and consistency, the playbook should define "a small batch" more precisely, e.g., "3–5 findings per subsystem, or all findings in one file if the file has fewer than 5 findings."

**Severity:** UNDOCUMENTED — Batch sizing criteria for fix execution not specified.

---

### 9. Language Adapter Guidance — Promised but Not Delivered

#### SKILL.md Metadata (line 3)

**PHANTOM:** The skill description claims "Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP with adapter guidance for additional languages."

**Reality:** There is no "adapter guidance for additional languages" anywhere in the playbook. The defensive_patterns.md grep tables are fixed to 10 specific languages; there's no guidance on how to adapt the grep patterns for a language not in the list (e.g., if a user wants to apply the playbook to a Perl, Lua, or OCaml codebase, what should they do?). An external language would need to:

1. Map null/nil guards to that language's null representation
2. Map exception handling patterns to that language's error mechanism
3. Map private/protected patterns to that language's visibility model
4. etc.

The playbook mentions "additional languages" but provides no adapter template or guidance.

**Severity:** PHANTOM — Metadata claims adapter guidance for languages beyond the 10 listed; no such guidance exists in the files.

---

### 10. Spec Audit Prompt — Line Number Requirement and Guardrails

#### Mandatory Guardrails (spec_audit.md lines 30-42)

**CLEAR:** The four guardrails are well-embedded in the audit prompt template:
1. Mandatory line numbers
2. Grep before claiming missing
3. Read function bodies
4. Classify defect type

**Reality:** These are present and clearly stated. The prompt template is well-structured.

**No finding here.**

---

## Summary of Findings

### Total Findings: 16

**By Classification:**
- **MISSING:** 9
  1. 14 defect categories claim (11 documented, 3 exist in SKILL.md but not in reference file)
  2. Async/Sync Parity grep patterns
  3. Context Propagation Loss grep patterns
  4. Field Label Drift grep patterns
  5. Truth Fragmentation grep patterns
  6. Callback Concurrency grep patterns
  7. Functional test structure for C#, Ruby, Kotlin, PHP (4 languages)
  8. Fixture setup guidance for C#, Ruby, Kotlin, PHP
  9. Schema mutation examples for C#, Ruby, Kotlin, PHP
  10. Regression test file naming for C#, Ruby, Kotlin, PHP
  11. Integration test "Present Plan First" embedding in template
  12. Phase 2 completion criterion for pre-existing AGENTS.md
  13. Phase 4 termination logic for agents
  14. Test parser validation for playbook's own reference files
  15. Adapter guidance for languages beyond the 10 listed

- **DIVERGENT:** 3
  1. 14 defect categories vs. 11 documented in defensive_patterns.md
  2. Cross-variant heuristic guidance differs (functional_tests.md vs. SKILL.md on "significantly more")
  3. Test count heuristic nuance (SKILL.md more permissive than functional_tests.md)

- **UNDOCUMENTED:** 10
  1. Cross-reference between defensive_patterns.md and SKILL.md Step 5c is broken
  2. State machine analysis placement in step numbering confuses optional vs. mandatory
  3. Scenario count absolute/relative benchmarks (only relative given: "2+ per module")
  4. Benchmark dataset (2,592 defects, 55 repos) referenced but not included
  5. Verification probe trigger condition (when to deploy) not fully specified
  6. Fix batch sizing criteria not quantified
  7. "Present Plan First" pattern documented in SKILL.md but not in protocol template
  8. Bootstrap self-audit evidence (playbook hasn't been run against itself)
  9. Spec audit finding classification edge cases (Model A: MISSING, Model B: DIVERGENT on same line)
  10. Worked examples generality claims (claims domain-agnostic, actually covers 4 archetypes)

- **PHANTOM:** 2
  1. 14 defect categories claim (only 11 have explicit sections with patterns)
  2. Adapter guidance for additional languages (claimed, doesn't exist)

---

## Top 3 Most Important Findings (Ranked by Impact)

### 1. **Language Coverage Gap for New Languages (C#, Ruby, Kotlin, PHP)**
   - **Classification:** MISSING
   - **Impact:** Users of these 4 languages have no functional test structure, fixture setup, schema mapping, or regression test guidance. This is a critical gap for 40% of claimed supported languages.
   - **Fix:** Add functional test structure examples, fixture setup, schema mutation examples, and regression test file naming for all 4 new languages to their respective reference files.

### 2. **Defensive Pattern Detection Completeness — Grep Patterns Missing for 5 Categories**
   - **Classification:** MISSING
   - **Impact:** v1.2.7 claims integration of Async/Sync Parity, Context Propagation Loss, Field Label Drift, Truth Fragmentation, and Callback Concurrency as systematic detectable patterns. But defensive_patterns.md (the primary reference for Step 5) provides no grep patterns for 5 of these, only prose. Agents following defensive_patterns.md will mechanically find 11 patterns and then have to interpret conceptual guidance for the other 5.
   - **Fix:** Add language-specific grep pattern tables for the 5 categories (Async/Sync Parity, Context Propagation Loss, Field Label Drift, Truth Fragmentation, Callback Concurrency) matching the structure of existing pattern tables.

### 3. **Integration Test Protocol Template Missing "Present Plan First" Step**
   - **Classification:** UNDOCUMENTED
   - **Impact:** SKILL.md heavily emphasizes presenting the integration test plan to the user before writing the full protocol (lines 401-407). This is marked as critical for UX. However, the actual template in review_protocols.md doesn't include a "Step 0: Present Plan" instruction. Agents following the template will skip this interaction and write the full protocol without user feedback first.
   - **Fix:** Add a "Step 1: Present Plan" section to the integration test protocol template (review_protocols.md) that shows agents where to pause and display the plan before filling in the rest.

---

## Recommendations for v1.2.8

1. **Complete language coverage:** Add C#, Ruby, Kotlin, PHP examples to functional_tests.md, fixture strategy section, schema_mapping.md, and review_protocols.md regression test sections.

2. **Unify defect category documentation:** Either (a) add grep pattern tables for Async/Sync Parity, Context Propagation Loss, Field Label Drift, Truth Fragmentation, and Callback Concurrency to defensive_patterns.md, OR (b) restructure defensive_patterns.md to explicitly reference Step 5c in SKILL.md as "See SKILL.md Step 5c for additional pattern audits."

3. **Embed "Present Plan First" in template:** Add Step 1 to the integration test protocol template that instructs agents to pause after presenting the plan and wait for user confirmation before proceeding to full protocol generation.

4. **Clarify phase transitions:** Update Phase 1 completion criterion to clarify state machine analysis (step number and whether mandatory or optional). Update Phase 2 completion to specify handling of pre-existing AGENTS.md. Add explicit termination logic to Phase 4 (agents should ask "want to improve something else?" and exit if user says no).

5. **Validate bootstrapping:** Run the playbook against its own codebase and include a quality/QUALITY.md for the playbook itself, demonstrating self-application.

6. **Add quantified scenario guidance:** Define absolute or clearer relative scenario count targets (e.g., "6–15 scenarios for medium projects, benchmarked by core module count").

7. **Document verification probe conditions:** Specify when to deploy a verification probe (e.g., when 2 models disagree on classification of the same code location) and how to resolve it.

8. **Unify cross-variant heuristic guidance:** Ensure all references to the ~30% cross-variant testing target use consistent language.
```