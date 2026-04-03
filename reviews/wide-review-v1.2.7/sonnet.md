# Sonnet — v1.2.7 Review

sonnet-4.6

```
Now let me read the remaining reference files:Now I have read all files thoroughly. Let me compile the audit findings.

---

# Council of Three Spec Audit — Quality Playbook v1.2.7

---

### [defensive_patterns.md] — "Protocol Violations" section (lines 329–332)
**[MISSING]** The Protocol Violations category is the only one of the 14 claimed defect categories that has no grep patterns table.
Playbook says: "The playbook addresses 14 defect categories" and lists Protocol Violations as one. Reality: every other category has an explicit language-by-language grep patterns table. Protocol Violations has only prose ("Search for code implementing or consuming protocols…") with no patterns, no language breakdown, and no "What to look for" examples that are distinct from the API Contract section above it. The guidance is thinner by a significant margin than any original category.

---

### [defensive_patterns.md] — "Async/Sync Parity" section (lines 334–346)
**[MISSING]** The Async/Sync Parity grep pattern table omits C#, Ruby, Kotlin, and PHP — four of the six languages added in v1.2.7.
Playbook says it has "Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP." Reality: the Async/Sync Parity table lists only Python, Java, TypeScript, Go, and Rust. C#, Ruby, Kotlin, and PHP have no entries.

---

### [defensive_patterns.md] — "Context Propagation Loss" section (lines 348–352)
**[MISSING]** Context Propagation Loss has no grep patterns table and no language-specific guidance at all.
Playbook says: "Covered in detail in SKILL.md Step 5c." Reality: SKILL.md Step 5c does describe the concept, but defensive_patterns.md — the reference file the agent is supposed to read during Step 5 — provides only one sentence of guidance with zero grep patterns and no language breakdown. Every other category directs readers to a grep table. This one does not, making it effectively unactionable during search.

---

### [defensive_patterns.md] — "Callback Concurrency" section (lines 373–376)
**[MISSING]** Callback Concurrency has no grep patterns and no language-specific examples for C#, Ruby, Kotlin, or PHP.
Playbook says this is a covered defect category. Reality: the section contains two sentences of prose with no patterns and no language breakdown. Unlike the Concurrency Issues category (which has a complete 10-language table), Callback Concurrency — a distinct sub-category — has no actionable search guidance.

---

### [SKILL.md] — Phase Transition Gates, "Phase 1 → Phase 2" (lines 313–323)
**[DIVERGENT]** Gate criterion 5 requires "8+ domain-specific risk scenarios" before Phase 1 is complete, but constitution.md says to "aim for 2+ scenarios per core module — typically 8–10 total for a medium project, fewer for small projects."
Playbook says: Phase 1 gate: "You have generated 8+ domain-specific risk scenarios grounded in the actual code." Reality: the constitution.md guidance (which agents read during Phase 2, File 1) explicitly says "Fewer is fine for small projects." The Phase 1 gate gives no small-project exception, creating a conflict where a small project must generate 8+ scenarios to leave Phase 1 but is told fewer are fine when writing QUALITY.md.

---

### [SKILL.md] — Phase Transition Gates, "After File 6: Ready for Phase 3" (lines 325–341)
**[UNDOCUMENTED]** The "After File 6" gate is a list of files, not a completion criterion. There is no stated check that any of the files are correct, self-consistent, or pass any standard before Phase 3 begins.
Playbook says: "When all files are generated, proceed to Phase 3." Reality: the gate only checks file existence. An agent that generated six empty or placeholder files would satisfy the gate. Phase 3 verification is where correctness is checked, but the transition gate gives no signal that correctness matters before moving. This is a phantom gate — it appears to be a quality control point but isn't.

---

### [SKILL.md] — Phase 2, File 4 (lines 401–423) vs. [review_protocols.md] — "Integration Test Design UX" (lines 142–179)
**[DIVERGENT]** SKILL.md says to present the integration test plan to the user "BEFORE writing the protocol" (line 405). The review_protocols.md template (lines 181–300) contains no equivalent "present-first" placeholder — it goes directly to the protocol structure.
Playbook says: SKILL.md: "Present the integration test plan to the user BEFORE writing the protocol file." Reality: the template in review_protocols.md that agents use to generate the file does not include a pre-presentation step. An agent following the template literally would generate the file without the plan-first step. The guidance exists in SKILL.md but not in the reference file that governs file content.

---

### [SKILL.md] — Bootstrapping section (lines 574–607) vs. [spec_audit.md] — "Mandatory line numbers" guardrail
**[PHANTOM]** The bootstrapping section says an agent "could actually bootstrap the playbook against its own repository using only the instructions provided," but the instructions contain a critical failure mode: the spec audit guardrail ("if you cannot cite a line number, do not include the finding") cannot be satisfied when auditing Markdown documentation rather than code files.
Playbook says: "Could an agent actually bootstrap the playbook against its own repository?" (implicit in scrutiny area 5). Reality: during bootstrapping, the "codebase" is Markdown. The spec audit guardrail requires line numbers for every finding. Markdown files do have line numbers, but the guardrail was written for code (the example output format shows `filename.ext — Line NNN`). The bootstrapping section doesn't acknowledge this mismatch or adapt the guardrail for documentation audits. An agent bootstrapping the playbook will either ignore the guardrail (violating it) or cite meaningless line numbers in prose documents.

---

### [SKILL.md] — Bootstrapping, Step 3 (line 582)
**[MISSING]** The bootstrapping section says "Look for existing test files that validate the playbook's documentation (e.g., test parsers for QUALITY.md format, scripts that check reference file consistency). If none exist, this is a finding." But nowhere in the playbook does it specify what those tests should look like or how to generate them for a Markdown project.
Playbook says: "This is a finding — the playbook should validate itself." Reality: Phase 2, File 2 guidance (functional tests) is entirely oriented toward code projects with functions, schemas, and test runners. No adaptation guidance exists for generating functional tests against Markdown-only projects, which is exactly what bootstrapping requires. The "present the plan first" UX flow and the Field Reference Table procedure both assume code schemas — neither works for documentation.

---

### [verification.md] — Benchmark 8 (lines 108–127) vs. [functional_tests.md] — import pattern section
**[DIVERGENT]** verification.md lists Haiku 4.5 as a supported test runner command for C#: `dotnet test` — but functional_tests.md has no C# import pattern, no C# test structure example, and no C# fixture guidance.
Playbook says: verification.md Benchmark 8 lists test runner commands for Python, Scala, Java, TypeScript, Go, and Rust. Reality: C#, Ruby, Kotlin, and PHP test runners are not listed in verification.md Benchmark 8 at all — the four added languages have no entries in the self-check benchmark that verifies test execution. An agent generating C# tests will find no guidance on how to verify them in Phase 3.

---

### [functional_tests.md] — Import Pattern section (lines 32–63)
**[MISSING]** The import pattern matrix covers Python, Java, Scala, TypeScript/JavaScript, Go, and Rust — six languages. C#, Ruby, Kotlin, and PHP import patterns are absent.
Playbook says: "Full support for… C#, Ruby, Kotlin, PHP." Reality: the import pattern section is the foundation of functional test generation ("getting this wrong means every test fails"). Four of the ten claimed supported languages have no guidance here. The instruction to "copy exactly" the import pattern cannot be followed when no pattern is documented.

---

### [functional_tests.md] — No C#, Ruby, Kotlin, or PHP test examples
**[MISSING]** Every test structure section (spec-derived tests, fitness-to-purpose tests, boundary tests, async tests, cross-variant tests, anti-patterns) shows examples in Python, Java, Scala, TypeScript, Go, and Rust. C#, Ruby, Kotlin, and PHP have zero examples in functional_tests.md.
Playbook says: "Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP." Reality: functional_tests.md — the primary reference for the most important deliverable — provides no examples, no test framework guidance (NUnit? xUnit? MSTest? RSpec? Minitest? JUnit for Kotlin? PHPUnit?), and no fixture conventions for the four new languages.

---

### [verification.md] — Benchmark 8 (lines 108–127)
**[MISSING]** C#, Ruby, Kotlin, and PHP test runner commands are absent from the self-check benchmark.
Playbook says: "Run the test suite using the project's test runner." Reality: the benchmark lists Python (`pytest`), Scala (`sbt`), Java (`mvn`/`gradle`), TypeScript (`npx jest`), Go (`go test`), Rust (`cargo test`). The four new languages have no entries. An agent generating tests for a Ruby project has no self-check command to run.

---

### [SKILL.md] — Step 3, test harness consistency audit (lines 145–151) vs. [functional_tests.md]
**[UNDOCUMENTED]** SKILL.md Step 3 adds a "test harness consistency audit" specifically mentioning NUnit `[TestFixture]`, xUnit/MSTest `[TestClass]`, JUnit `@RunWith`. These are C#-specific (.NET) and Java framework attributes. But functional_tests.md has no C# test structure examples, so an agent following Step 3's new audit guidance then opening functional_tests.md for C# test generation will find nothing.
Playbook says: SKILL.md Step 3 (line 147): "Common silent failures: Missing class-level attributes: NUnit [TestFixture], xUnit/MSTest [TestClass], JUnit @RunWith." Reality: the NUnit/MSTest/xUnit guidance implies C# test generation is supported, but the functional tests reference file provides no C# framework examples, structure, or conventions. The audit finds the problem; the fix pathway is missing.

---

### [review_protocols.md] — General Principles, Principle 1 (line 132) vs. actual worked examples
**[DIVERGENT]** The general principles say "Identify the project's independent axes of variation and test across their combinations." All four worked examples have exactly three axes. This creates an implicit but undocumented assumption that three axes is normal, while the general principle implies the number should vary by project.
Playbook says: "Ask: 'What are the dimensions that, if I only tested one value of each, I'd miss real bugs?'" Reality: all four worked examples present exactly three test axes each. An agent pattern-matching on worked examples may default to three regardless of project complexity, while the principle calls for project-specific identification.

---

### [SKILL.md] — Phase 2, File 2 test count heuristic (line 382) vs. [functional_tests.md] — test count heuristic (lines 23–29) vs. [verification.md] — Benchmark 1 (implied)
**[DIVERGENT]** The test count heuristic is stated consistently in formula form but the example numbers diverge. SKILL.md says "35–50 tests" for a medium project. functional_tests.md says "35–50 tests." But verification.md Benchmark 1 does not restate the range — it only describes the heuristic formula — creating a situation where the Phase 3 self-check offers no numeric target to compare against. The formula is the same, but no range is provided for agents to use as a sanity check during verification.

---

### [SKILL.md] — Step 5 (lines 178–186) vs. [defensive_patterns.md] — Minimum Bar (lines 407–411)
**[DIVERGENT]** SKILL.md Step 5 says "Minimum bar: at least 2–3 defensive patterns per core source file." defensive_patterns.md Minimum Bar section says "For a medium-sized project (5–15 source files), expect to find 15–30 defensive patterns total." For a 15-file medium project, 2–3 per file = 30–45 patterns, which is higher than the 15–30 range in defensive_patterns.md. The two figures are inconsistent for larger-end medium projects.

---

### [constitution.md] — "Where Scenarios Come From" → "Combining Both Sources" (lines 90–105)
**[UNDOCUMENTED]** The constitution.md guidance on combining code exploration and domain knowledge has no connection to the requirement tag system. It shows how to write scenarios but doesn't specify which `[Req: tier]` tag to use when a scenario combines a code-found defensive pattern with domain knowledge. Is it `inferred`? `user-confirmed`? The spec audit template in spec_audit.md treats tag tiers as authoritative for confidence weighting, but no guidance covers the combined-source case.

---

### [SKILL.md] — Phase 4 Completion Criterion (lines 599–607)
**[UNDOCUMENTED]** The Phase 4 completion criterion says "The user has explored at least one file in detail (drill-down)" but never specifies what counts as a "drill-down" or how the agent should determine whether the user has done this. An agent running autonomously (Claude Code, Cursor) cannot solicit this interactively — but the criterion is stated as a hard requirement.
Playbook says: "Phase 4 is complete when… The user has explored at least one file in detail." Reality: in agentic environments, Phase 4 collapses — there is no user to satisfy criterion 2. The playbook has no guidance for autonomous completion of Phase 4.

---

### [review_protocols.md] — Regression test naming, line 67–71
**[DIVERGENT]** The regression test file naming table lists Scala as absent — it is the only one of the six original languages with no entry. Python, Go, Rust, Java, and TypeScript all have regression test file naming guidance. Scala does not.
Playbook says: the skill claims full support for Scala. Reality: `review_protocols.md` lines 67–71 list regression test file paths for Python, Go, Rust, Java, and TypeScript but not Scala. An agent generating regression tests for a Scala project has no naming convention to follow.

---

## Summary

- **Total findings: 19**
- **By classification: 9 MISSING, 6 DIVERGENT, 3 UNDOCUMENTED, 1 PHANTOM**

**Top 3 most important findings (highest improvement impact):**

1. **[functional_tests.md] — No import patterns, test examples, or test runner commands for C#, Ruby, Kotlin, PHP (findings 10, 11, 12, 13).** These four findings are effectively one systemic gap: the four languages added in v1.2.7 have no representation in the primary deliverable reference file. Since functional tests are described as "the most important deliverable," a C#, Ruby, Kotlin, or PHP project using this playbook will get generic or broken test output with no guidance to fix it. This is the largest structural gap in v1.2.7.

2. **[defensive_patterns.md] — Protocol Violations category has no grep patterns; Async/Sync Parity, Context Propagation Loss, and Callback Concurrency are missing patterns for new languages (findings 1, 2, 3, 4).** The new defect categories are present in name but not in depth. Protocol Violations is the weakest of the 14 categories with no actionable patterns at all. The new-language gaps in Async/Sync Parity and Callback Concurrency mean that for C#, Ruby, Kotlin, and PHP projects, several defect categories are effectively blind spots.

3. **[SKILL.md] / [review_protocols.md] — "Present the plan first" UX flow exists in SKILL.md but is absent from the review_protocols.md template (finding 7).** The integration test plan-first pattern is described as critical ("This single extra exchange prevents the most common failure"), but the template agents use to generate `RUN_INTEGRATION_TESTS.md` doesn't include it. The instruction is in the right place for human-read documentation but in the wrong place for agent execution — agents follow templates, not meta-commentary.
```