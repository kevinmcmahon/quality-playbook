# ChatGPT (Thinking) — v1.2.9 Review

## Findings

### defensive_patterns.md — Converting Findings to Boundary Tests (lines 96–246) / functional_tests.md — Anti-Patterns to Avoid (lines 614–639)

**DIVERGENT** The new C#, Ruby, Kotlin, and PHP boundary-test examples for null-guard cases use exception-only assertions, but the functional-test guidance says exception-catching is the wrong layer and tests should assert output/behavior instead.
Playbook says: boundary tests must "check actual values, not just presence" and "Catching exceptions instead of checking output … isn't testing that it handles input correctly. Test the output."
Reality: the newly added examples use `Assert.Throws<ArgumentNullException>`, `raise_error(ArgumentError, /api_key/)`, `assertThrows<IllegalArgumentException>`, and `$this->expectException(...)` as their primary assertion pattern.

### functional_tests.md — Testing Async Functions / PHP example (lines 592–601)

**PHANTOM** The PHP async example is not runnable as shown in PHPUnit because it is a bare method, not a method inside a `TestCase` subclass.
Playbook says: language examples should reflect the project's actual test framework conventions, and the same file's valid PHP examples place test methods inside `class ... extends TestCase`.
Reality: the async PHP snippet shows only `public function testAsyncFunction(): void { ... }` with no surrounding test class, so PHPUnit would not discover it as written.

### review_protocols.md — Field Reference Table template vs. REST worked example (lines 555–591 vs. 377–385)

**DIVERGENT** The required Field Reference Table format does not match the worked example that is supposed to model it.
Playbook says: before writing quality gates, build a schema-derived table with columns `Field | Type | Constraints`, re-reading schema files and copying field names character-for-character.
Reality: the REST worked example uses a different table shape — `Field | Source (code) | Expected behavior | Verified by` — which is not the mandated schema-derived format.

### defensive_patterns.md — Comprehensive Defect Category Detection (lines 321–336)

**DIVERGENT** The file claims all 14 defect categories are covered in "the following sections and subsections," but category 14 is explicitly not covered in this file and instead points outside it.
Playbook says: "The playbook addresses 14 defect categories, covered in the following sections and subsections."
Reality: item 14 is "Generated and Invisible Code Defects (detection guidance in SKILL.md Step 5d …)," so that category is not actually covered in this file's own sections/subsections.

## Summary

* Total findings: 4
* By classification: 0 MISSING, 3 DIVERGENT, 0 UNDOCUMENTED, 1 PHANTOM
* Top 3 most important findings:

  1. Boundary-test guidance now conflicts with the playbook's own anti-pattern rule on exception-only testing.
  2. The Field Reference Table template and the worked example disagree on the required format.
  3. The PHP async example is not executable as shown (missing TestCase class).
