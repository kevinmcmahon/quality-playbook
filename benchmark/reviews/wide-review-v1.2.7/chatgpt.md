# Chatgpt — v1.2.7 Review

chatgpt

```
### SKILL.md — language support claims vs. reference-file coverage

**DIVERGENT** The playbook claims “full support” for 10 languages, but the downstream reference material still centers key execution guidance on the original 6-language set. SKILL.md advertises “Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP,” yet its own Step 3 points readers to a “full six-language matrix” in `references/functional_tests.md`, and the verification checklist only gives runnable test commands for Python, Scala, Java, TypeScript, Go, and Rust. `schema_mapping.md` likewise only gives language-specific mutation rules for those same six. Reality: the added C#/Ruby/Kotlin/PHP coverage is strong in `defensive_patterns.md`, but incomplete in the files the skill relies on for test authoring and verification.     

### SKILL.md + review_protocols.md — integration protocol workflow

**DIVERGENT** The integration-test workflow conflicts with itself. SKILL.md and `review_protocols.md` both say the agent must present the integration-test plan first and “only generate the full protocol file after the user confirms the plan.” But Phase 4 in SKILL.md assumes Phases 1–3 have already produced all six files and even gives a summary-table example that includes `RUN_INTEGRATION_TESTS.md` as already generated. Reality: the skill describes both a confirmation-gated workflow and an autonomous “all six files already generated” workflow, without resolving which one wins.    

### SKILL.md — phase transition gates

**MISSING** The playbook says v1.2.7 added explicit phase-transition criteria, but it only defines a concrete gate for Phase 1 → Phase 2 and a checklist for being “Ready for Phase 3.” The review prompt explicitly asks whether “the Phase 4 completion criterion” is well-defined, but SKILL.md’s Phase 4 section only describes what to present and how to discuss it; it never states when Phase 4 is complete or what condition allows the agent to stop. Reality: the phase-gate system is incomplete.   

### SKILL.md + verification.md — non-code / Markdown/tooling bootstrap

**MISSING** The playbook claims it was expanded to address non-code projects, but the operational instructions still assume a code project with a runnable test framework. SKILL.md says the skill can be pointed at “any codebase,” includes AGENTS bootstrapping, and says degraded mode still leaves the output valuable; but the critical deliverable remains an automated functional test file, and Phase 3 verification still requires running language-specific test runners only for Python/Scala/Java/TypeScript/Go/Rust. Reality: there is no concrete alternative path for a Markdown/tooling repository to satisfy the functional-test and verification phases using only the provided instructions.    

### constitution.md + defensive_patterns.md — missing safeguards vs. automatable scenarios

**DIVERGENT** The playbook’s distinction between defensive patterns and missing safeguards still leaks across files. `defensive_patterns.md` says missing safeguards are absent code, should become quality/spec-audit findings, and explicitly says “Do NOT write boundary tests for them.” But `constitution.md` says each scenario’s “How to verify” must map to at least one automated test in the functional test file, with only a narrow exception for Human Gate cases. Reality: for missing-safeguard scenarios such as “no confirmation before expensive operation,” the playbook simultaneously says they should not produce boundary tests and that each scenario should map to automated tests.  

### SKILL.md + verification.md — internal consistency on supported frameworks

**DIVERGENT** SKILL.md’s Step 3 test-harness audit explicitly brings in NUnit, xUnit, and MSTest-style discovery problems, which implies first-class concern for C# test ecosystems, but the verification phase never provides C# runner guidance and the functional-test reference never adds C# setup/import conventions alongside the original six-language execution matrix. Reality: the skill partially teaches the agent to inspect C# test infrastructure but does not carry that support through to the files that tell the agent how to generate and verify tests.   

## Summary

* Total findings: 6
* By classification: 2 MISSING, 4 DIVERGENT, 0 UNDOCUMENTED, 0 PHANTOM
* Top 3 most important findings:

  1. The 10-language “full support” claim is not matched by the test-authoring and verification references.
  2. The integration-test workflow conflicts with itself on whether user confirmation is required before `RUN_INTEGRATION_TESTS.md` can exist.
  3. The phase-gate system has no explicit Phase 4 completion criterion.

```