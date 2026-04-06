# Opus 4.6 (Extended Thinking) — v1.2.9 Review

## Findings

### [functional_tests.md] — Cross-Variant Testing Strategy, C# example (lines 421–436)
**[PHANTOM]** C# cross-variant test example still missing `public` modifier on both the class and the test method — the same bug v1.2.9 was supposed to fix.
Playbook says (REVIEW_PROMPT scrutiny area 1): "C# test methods now have `public` modifier." Reality: The cross-variant C# example has `class CrossVariantTests {` (no `public`) and `void TestFeatureWorks(Variant variant) {` (no `public`). NUnit requires test fixtures and test methods to be `public` for discovery. The `static IEnumerable<Variant> VariantProvider()` data source method is also missing `public static`, which NUnit requires for `[TestCaseSource]` resolution. This code would compile but the tests would silently not run.

### [functional_tests.md] — Import Pattern section, C# inline example (line 66)
**[PHANTOM]** C# inline example shows `[TestFixture] class FunctionalTests { }` without `public`.
Playbook says: C# examples should now have the `public` modifier. Reality: The Import Pattern section's inline C# example reads `NUnit test class: [TestFixture] class FunctionalTests { }`. Should be `[TestFixture] public class FunctionalTests { }`.

### [SKILL.md] — Reference Files table (line 667)
**[DIVERGENT]** Claims "14-category grep patterns" but category 14 has no grep pattern.
Playbook says: `defensive_patterns.md` contains "14-category grep patterns (10 languages)." Reality: Category 14 explicitly has "no grep table." Only 13 of the 14 categories have grep tables.

### [review_protocols.md] — Field Reference Table: template vs. worked example (lines 563–581 vs. 377–386)
**[DIVERGENT]** The Field Reference Table template and the REST API worked example use different column structures.
Playbook says: The table should have columns `| Field | Type | Constraints |`. Reality: The REST API worked example uses `| Field | Source (code) | Expected behavior | Verified by |`. An agent has no way to know which format to follow.

### [review_protocols.md] — Duplicate plan-first guidance (lines 152–189 vs. 191–201)
**[DIVERGENT]** Two adjacent sections describe the same generation-time plan-first step with slightly different details. The "Generation-Time Plan-First Step" section adds bullet points that don't appear in the Design UX template above. An agent could wonder if these are two different steps or one described twice.

### [functional_tests.md] — PHP async test example (lines 592–601)
**[PHANTOM]** PHP async example contains unused `$loop` variable that is unnecessary in ReactPHP 3.x.
Playbook says: "PHP async uses modern ReactPHP 3.x API." Reality: `$loop = \React\EventLoop\Loop::get();` creates a variable that is never referenced. In ReactPHP 3.x, `\React\Async\await()` handles the loop internally. Dead code misleads agents.

### [defensive_patterns.md] — Async/Sync Parity grep table, PHP entry (line 469)
**[PHANTOM]** PHP grep pattern lists `ReactPHP\Promise` but the actual namespace is `React\Promise`.
A grep for `ReactPHP\Promise` on a ReactPHP codebase would return zero results. Correct terms: `React\Promise`, `React\Async`, `React\EventLoop`.

### [review_protocols.md] — Field Reference Table absent from 3 of 4 worked examples
**[MISSING]** Only the REST API worked example includes a Field Reference Table; Message Queue, Database, and CLI/Pipeline examples do not.
Playbook says building a Field Reference Table is required before writing quality gates. An agent working on a non-REST project has no concrete example.

### [defensive_patterns.md] — Category 13 bundles 5 distinct concerns (line 335)
**[UNDOCUMENTED]** Five separate defect detection concerns — each with its own grep table, section heading, and distinct methodology — are silently bundled into a single numbered category to maintain the "14 categories" count. An agent instructed to "search across all 14 defect categories" might treat category 13 as a single check rather than five separate searches.

## Summary

- Total findings: **9**
- By classification: **1** MISSING, **3** DIVERGENT, **1** UNDOCUMENTED, **4** PHANTOM
- Top 3 most important findings:
  1. **functional_tests.md C# cross-variant example missing `public`** — The exact bug class v1.2.9 claimed to fix but missed in two locations. Tests silently don't run.
  2. **review_protocols.md Field Reference Table format inconsistency** — Template shows 3-column format, worked example shows 4-column format.
  3. **SKILL.md "14-category grep patterns" overclaims** — Category 14 has no grep table, so "14-category grep patterns" is factually wrong.
