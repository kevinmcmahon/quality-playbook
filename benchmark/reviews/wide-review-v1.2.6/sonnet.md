# Sonnet — v1.2.6 Review

claude.ai + sonnet-4.6

```
Now I have a complete picture of all the files. Let me deliver the audit.

---

# Council of Three Spec Audit — Quality Playbook v1.2.6

---

### SKILL.md — Lines 28–43 (Output table)
**UNDOCUMENTED** The table lists `quality/test_functional.*` as the functional test file and says "Use the project's language," but the table's "Executes Code?" column is the only place the distinction between executable and non-executable deliverables is flagged. SKILL.md never documents what happens when the agent cannot execute code (e.g., running inside a read-only or sandboxed environment). There is no fallback or exception path for the "Yes" cells.  
Playbook says: "Executes Code? Yes" for functional tests and integration tests. Reality: no guidance exists for what the agent should do if it cannot run the test suite — whether to generate tests anyway, flag them as unverified, or halt.

---

### SKILL.md — Step 5 (Lines 159–167) vs. verification.md — Benchmark 4
**DIVERGENT** SKILL.md says "at least 2–3 defensive patterns per source file" and "for a medium project, expect 15–30 patterns." verification.md Benchmark 4 says "ratio should be close to 1:1" (boundary tests to defensive patterns). These two numbers are inconsistent for the test count heuristic stated in File 2 guidance (line 329): "for a medium project, typically yields 35–50 tests." If 15–30 patterns produce 15–30 boundary tests, and spec sections (~12) plus scenarios (~10) are added, the expected range is 37–52 — consistent. But the "2–3 per source file" claim for a project with 15 source files implies 30–45 patterns, which would push expected test counts to 52–67. The two minimum-bar statements cannot both be correct for the same project size.

---

### SKILL.md — Step 5c (Lines 201–226)
**UNDOCUMENTED** Step 5c introduces five novel detection categories (context propagation loss, parallel path symmetry, field label drift, callback concurrency, truth fragmentation) and Step 5d adds two more (macro review, sync/async parity). None of these appear in the Reference File table at the bottom of SKILL.md (lines 566–576), which does not list a reference file for these steps. Steps 5c and 5d have no corresponding reference file at all — the skill tells agents to "read references/defensive_patterns.md" for Step 5 generically, but that file does not contain guidance for any of the 5c/5d categories.  
Playbook says (line 570): "defensive_patterns.md — Step 5 (finding skeletons)." Reality: defensive_patterns.md covers null guards, error handlers, state machines, and missing safeguards — it contains nothing about context propagation loss, parallel path symmetry, field label drift, callback concurrency, truth fragmentation, macro review, or sync/async parity.

---

### SKILL.md — Step 5a (Lines 173–194) vs. defensive_patterns.md — State Machine Patterns
**DIVERGENT** SKILL.md Step 5a says to trace cross-boundary signal propagation as part of state machine analysis (lines 188–193). defensive_patterns.md § "State Machine Patterns" describes state machines as status/lifecycle fields and does not mention signal propagation, abort/cancel chains, or middleware cross-boundary analysis at all. An agent reading the reference file would get a materially narrower definition of Step 5a than SKILL.md describes.

---

### SKILL.md — Phase 2, File 2 (Lines 316–333)
**MISSING** SKILL.md says "Read references/functional_tests.md for the complete guide" and then gives key rules. One key rule (line 327): "Read every function's signature before calling it." But neither SKILL.md nor functional_tests.md provides guidance on what to do when a function's signature cannot be determined — for example, dynamically generated functions, methods inherited through metaclasses, or Java reflection-based APIs. The playbook promises first-run passing tests (via Step 4b) but provides no fallback strategy for the cases where signature reading fails.

---

### SKILL.md — Phase 3 (Lines 394–410) vs. verification.md — Benchmark 8
**DIVERGENT** SKILL.md Phase 3 lists 10 critical checks (lines 398–408) as "the critical checks." verification.md contains 13 benchmarks. The three benchmarks in verification.md not listed in SKILL.md's summary are: Benchmark 10 (QUALITY.md scenarios reference real code and label sources), Benchmark 11 (RUN_CODE_REVIEW.md is self-contained), and Benchmark 13 (spec audit prompt is copy-pasteable). An agent reading only the Phase 3 summary in SKILL.md would skip three verification steps.  
Playbook says: "The critical checks: 1–10." Reality: verification.md defines 13 checks, not 10.

---

### SKILL.md — Phase 3, Benchmark 8 (Line 405) vs. verification.md — Benchmark 8
**DIVERGENT** SKILL.md Phase 3 check 8 says to run the test suite and lists six languages/runners. The Scala runner listed is `sbt testOnly`. verification.md Benchmark 8 lists the same runners but formats Scala as `sbt "testOnly *FunctionalSpec"` — with the specific test file name in quotes. These are not the same command. The SKILL.md version would run all tests, not just the functional spec. For a project with a large existing test suite, this would be slow and could produce misleading results.

---

### SKILL.md — Phase 2, File 4 (Lines 348–370) vs. review_protocols.md
**MISSING** SKILL.md says "Script parallelism, don't just describe it. Group runs so independent executions run concurrently. Include actual bash commands with `&` and `wait`." (lines 362–363). review_protocols.md § "Parallelism and Rate Limit Awareness" (lines 282–298) provides an example grouping table but the actual bash template only appears in prose description — not as a concrete bash template the agent could copy. The promise to "include actual bash commands" has no template to anchor it.  
Playbook says: "Include actual bash commands with `&` and `wait`." Reality: the reference file shows a conceptual grouping example but provides no bash template with actual `&`/`wait` syntax.

---

### SKILL.md — Phase 1, Step 5d (Lines 227–267)
**MISSING** Steps 5d covers generated/invisible code and adds several detection patterns (lines 243–267): boundary conditions with empty/zero values, placeholder value masking, regex metacharacter escaping, strict parsing format coverage, and API trimming attributes. The playbook claims to detect "14 defect categories" from the spec audit prompt context. Of those 14, **SQL errors** and **security issues** are not addressed by any step in Phase 1. There is no instruction to search for SQL query construction patterns, injection risks, or any security-relevant pattern. The Step 6 domain knowledge section (lines 280–286) asks "what goes wrong in systems like this" but never mentions security as a domain. The 14 categories in the audit prompt are not cross-referenced against the exploration steps anywhere.  
Playbook says (implicitly via audit prompt): covers 14 defect categories including security issues and SQL errors. Reality: no step in Phase 1 directs the agent to search for SQL construction patterns or security-relevant code paths.

---

### SKILL.md — Phase 4, Bootstrapping (Lines 518–526)
**PHANTOM** The bootstrapping section says "the playbook generates quality infrastructure for its own repository, runs the generated tests, and identifies defects in its own tooling and documentation. This is a natural validation step." It then lists three things bootstrapping is "especially useful for." But the playbook contains no actual specification files for its own repository. It has no QUALITY.md, no functional tests, no AGENTS.md. An agent attempting to bootstrap cannot follow Step 4 ("Read the Specifications") because the playbook is a set of instructions, not a codebase with a spec. The Phase 1 exploration steps (identify domain, map architecture, read existing tests) are also undefined for a repository whose "source code" is Markdown.  
Playbook says: "the process works normally — the playbook generates quality infrastructure for its own repository." Reality: Phase 1 steps 1–5 assume source code in a programming language. The playbook has no functions to read signatures for, no schemas to map, no test suite to import patterns from. The bootstrapping claim cannot execute from the description alone.

---

### SKILL.md — Phase 1, Step 1 (Lines 99–115) vs. spec_audit.md — Requirement Confidence Tiers
**DIVERGENT** SKILL.md Step 1 defines three requirement tiers: `formal`, `user-confirmed`, `inferred`. spec_audit.md defines the same three tiers identically. However, spec_audit.md adds a finding category "NEEDS REVIEW" for inferred requirements (line 57 of spec_audit.md: "Report divergence as NEEDS REVIEW, not as a definitive defect") that is not reflected anywhere in SKILL.md's guidance for how to handle inferred requirements during Phase 2 generation. SKILL.md says to "flag inferred requirements for user review in Phase 4" — but the format for flagging is never specified. An agent writing QUALITY.md scenarios from inferred requirements would not know how to mark them as needing review in a way consistent with the audit protocol.

---

### SKILL.md — Phase 1, Step 6 (Lines 269–288)
**UNDOCUMENTED** Step 6 says to generate "realistic failure scenarios from this knowledge" and write them as "architectural vulnerability analyses with specific quantities and consequences." But Step 6 provides no minimum bar and no cap. constitution.md § "Calibrating Scenario Count" (lines ~250+) gives guidance (aim for 2+ per core module, 8–10 for medium projects), but SKILL.md does not say to read constitution.md during Step 6 — it says to read it during "File 1 (QUALITY.md)." An agent executing Step 6 linearly would not yet have read constitution.md, and SKILL.md gives no calibration guidance inline in Step 6.  
Playbook says: read `references/constitution.md` during File 1. Reality: calibration guidance needed during Step 6 is only in constitution.md, which is not referenced until Phase 2.

---

### functional_tests.md — § "Import Pattern: Match the Existing Tests" (Lines 31–63)
**MISSING** The import pattern section covers Python, Java, Scala, TypeScript, Go, and Rust. It does not cover C#, Ruby, PHP, Kotlin, Swift, Elixir, or C — seven of the 15 languages the benchmark dataset covers. SKILL.md claims the playbook "Works with any language (Python, Java, Scala, TypeScript, Go, Rust, etc.)" and the audit prompt lists 15 languages. An agent working on a Kotlin, Ruby, or C# codebase would have no import pattern guidance.  
Playbook says: "Works with any language." Reality: functional_tests.md import patterns, test framework setup examples, and parametrization syntax are provided for exactly 6 languages. The 9 others receive no equivalent guidance.

---

### functional_tests.md — § "Create Test Setup BEFORE Writing Tests" (Lines 65–124)
**UNDOCUMENTED** The section covers setup for Python, Java, Scala, TypeScript, Go, and Rust. It does not mention that `quality/` is a separate directory from the project test directory, which means the test runner may not discover the quality tests by default — particularly in Java (Maven/Gradle source root conventions) and Scala (SBT project layout). SKILL.md mentions this separation (line 531: "The `quality/` folder is separate from the project's unit test folder") but neither SKILL.md nor functional_tests.md explains how to configure the test runner to discover tests in a non-standard directory. Benchmark 8 in verification.md assumes tests are run with a direct command (`mvn test -Dtest=FunctionalTest`), implying the agent must place the test file where the runner can find it — but no guidance on this is provided.

---

### review_protocols.md — Phase 2: Regression Tests (Lines 53–107)
**UNDOCUMENTED** The regression test phase says to write tests that "fail on the current implementation, confirming the bug is real." This requires the agent to have write access to the repository and to be able to run the test suite. Neither SKILL.md nor review_protocols.md documents the precondition that regression test generation requires an executable environment, or what to do if the agent can only read code (e.g., in a code review context where write access isn't available). The section also says tests should use "mocking/monkeypatching to isolate from external services" but provides no language guidance for C#, Ruby, Kotlin, or other non-covered languages.

---

### spec_audit.md — § "Model Selection Notes" (Lines 145–161)
**UNDOCUMENTED** spec_audit.md names "Claude" and "GPT-based tools" and "some Gemini variants" as models with distinct strengths. These are present-tense characterizations that will drift over time as models update. There is no version pin or caveat, and no process for updating these characterizations. The playbook's own methodology (use multiple models because blind spots differ) applies to itself here — but the playbook provides no self-update protocol for the model selection notes.

---

### SKILL.md — Phase 2, File 3 (Lines 334–346) — Regression Test Naming
**DIVERGENT** SKILL.md Phase 2 File 3 says to write regression tests in `quality/test_regression.*`. review_protocols.md Phase 2 says the Go convention is `quality/regression_test.go` (or "in the relevant package's test directory"). These are different paths — `quality/regression_test.go` is in the `quality/` directory, but review_protocols.md also says "(or in the relevant package's test directory)" which is a different location. For Go, test files must be in the same package directory or in `_test` suffixed packages. A `quality/regression_test.go` file may not compile or be discoverable if the `quality/` directory isn't a Go package.

---

## Summary

- **Total findings: 17**
- **By classification: 5 MISSING, 5 DIVERGENT, 6 UNDOCUMENTED, 1 PHANTOM**

**Top 3 most important findings:**

1. **SKILL.md — Phase 3 vs. verification.md (Benchmarks 10–13, DIVERGENT).** The Phase 3 summary lists 10 checks but verification.md defines 13. An agent executing the skill will systematically skip three verification steps on every run. This is a structural gap that affects every playbook generated — not an edge case.

2. **SKILL.md — Steps 5c/5d have no reference file (UNDOCUMENTED).** Steps 5c and 5d introduce seven detection categories across ~65 lines of SKILL.md, but the Reference File table sends agents to `defensive_patterns.md` for "Step 5" — and that file contains none of the 5c/5d content. Agents following the "read the reference file" workflow will miss the entire context propagation, parallel path symmetry, truth fragmentation, and macro review analysis. These steps are among the most architecturally sophisticated in the playbook.

3. **SKILL.md — Bootstrapping is phantom (PHANTOM).** The claim that bootstrapping "works normally" is not executable from the playbook description. The playbook has no spec documents, no importable functions, no test suite, and no schema. This is the only self-validation mechanism the playbook describes, and it doesn't work as described. Fixing this would require either removing the claim, defining a concrete bootstrapping spec for the playbook's own files, or documenting what "normal process" means when applied to Markdown-only repositories.
```