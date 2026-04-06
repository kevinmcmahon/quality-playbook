# Sonnet 4.6 (Extended Thinking) — v1.2.9 Review

## Findings

### functional_tests.md — "Cross-Variant Testing Strategy" C# example (~line 426)
**[PHANTOM]** v1.2.9 claims to have fixed C# test methods to include the `public` modifier, but the cross-variant `TestFeatureWorks` method still lacks it.
Playbook says: v1.2.9 "C# test methods now have `public` modifier." Reality: `[TestCaseSource(nameof(VariantProvider))]` `void TestFeatureWorks(Variant variant)` has no access modifier, defaulting to `private`. Every other C# test method in the file correctly carries `public`. This one was missed.

### functional_tests.md — "Testing Async Functions" Java example (~line 535)
**[PHANTOM]** The Java async example declares `CompletableFuture<r>` using a lowercase, undefined type `r`. Java has no implicit class named `r`, so this does not compile — it produces `error: cannot find symbol: class r`.
Playbook says (implicit claim): code examples are idiomatic and would compile. Reality: the variable is declared as `CompletableFuture<r> future = processAsync(fixture);` followed immediately by `Result result = future.get(...)`, making clear the intended type is `Result`. The `<r>` should be `<Result>`.

### functional_tests.md — "Testing Async Functions" PHP example (~lines 597–598)
**[PHANTOM]** The PHP async example assigns `$loop = \React\EventLoop\Loop::get();` but never uses `$loop` — the variable is orphaned. `\React\Async\await($promise)` takes the promise, not the loop. The example looks like a partial migration from ReactPHP v2 to v3 style, stopped midway.
Playbook says: v1.2.9 "PHP async uses modern ReactPHP 3.x API." Reality: the API calls are v3-compatible but the dead `$loop` assignment implies unfinished work and will generate an "unused variable" notice under strict PHP configurations.

### review_protocols.md — "The Field Reference Table" template vs. REST API worked example (~lines 563–582 vs. 377–386)
**[DIVERGENT]** The canonical Field Reference Table template mandates columns `Field | Type | Constraints`. The REST API worked example uses entirely different columns: `Field | Source (code) | Expected behavior | Verified by`. An agent must choose between two incompatible schemas with no guidance on which to use.

### review_protocols.md — Dual generation-time plan sections (~lines 152–188 and 191–200)
**[PHANTOM]** The file contains two distinct sections describing the same generation-time plan requirement. "Integration Test Design UX: Present the Plan First" (lines 152–188) is a full, three-step description. "Generation-Time Plan-First Step" (lines 191–200) covers the same requirement in condensed form. Neither section acknowledges the other. An agent could perform the plan-first step twice.

### review_protocols.md — "Language-specific tips" for regression tests (~lines 107–115)
**[MISSING]** The regression test language-specific tips section lists 8 of the 10 supported languages. TypeScript and Scala receive no tips.

### SKILL.md — Bootstrapping sub-step adaptation, Steps 4b/5a/5b/5c/5d (~lines 598–599)
**[MISSING]** The bootstrapping adaptation guidance says what each sub-step means for documentation/tooling projects but does not say what artifact the adapted sub-step should produce. The main guidance produces concrete artifacts (function call map, schema type map table, etc.). The adaptation substitutes a new scope but gives no corresponding artifact form.

## Summary
- **Total findings:** 7
- **By classification:** 2 MISSING, 1 DIVERGENT, 0 UNDOCUMENTED, 4 PHANTOM

**Top 3 most important findings:**

1. **functional_tests.md — Java `CompletableFuture<r>` (PHANTOM):** Outright compilation failure. Fixing requires only changing `<r>` to `<Result>`.

2. **review_protocols.md — Field Reference Table column divergence (DIVERGENT):** Two incompatible formats (template vs. worked example) undermine the standardized procedure.

3. **SKILL.md — Bootstrapping adaptation artifact form (MISSING):** Agents don't know what Step 4b/5b outputs should look like for documentation projects.
