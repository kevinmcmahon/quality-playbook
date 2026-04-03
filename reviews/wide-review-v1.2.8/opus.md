# Opus 4.6 (Extended Thinking) — v1.2.8 Review

## Findings

### defensive_patterns.md — "Converting Findings to Boundary Tests" (lines 85–161)
**MISSING** — The boundary test code examples show only 6 languages: Python, Java, Scala, TypeScript, Go, Rust. C#, Ruby, Kotlin, and PHP are absent from this section.
Playbook says: SKILL.md description line 3 claims "Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP." Reality: The grep pattern tables cover all 10 languages, but the section teaching agents how to *convert* those findings into boundary tests only demonstrates 6. functional_tests.md's "Boundary and Negative Tests" section (lines 940–1065) does cover all 10 languages — but defensive_patterns.md doesn't cross-reference it.

### functional_tests.md — All C# test method examples (lines 155, 300, 564, 893, 1022; also schema_mapping.md lines 157, 163)
**PHANTOM** — Every C# test method across functional_tests.md and schema_mapping.md omits the `public` access modifier. Example at functional_tests.md line 155: `[Test] void TestConfigValidation()`. In C#, methods without an explicit access modifier default to `private`. NUnit requires `public` test methods for discovery — a `private` test method compiles but silently never runs.
Playbook says: SKILL.md lines 147–151 explicitly warn about this class of bug: "Missing class-level attributes: NUnit `[TestFixture]`... without these, the test class exists but its tests never run." Reality: The playbook's own C# code templates commit the exact silent-failure pattern it warns agents to detect.

### functional_tests.md — All Ruby code block labels (lines 167, 306, 440, 571, 752, 760, 902, 1030)
**UNDOCUMENTED** — Every Ruby code example uses `//` as a comment prefix (e.g., `// Ruby (RSpec)`) instead of Ruby's `#` comment syntax. Ruby does not support `//` as a line comment — it's parsed as a regex literal. The playbook insists on idiomatic language conventions but uses non-idiomatic comment syntax in its own Ruby reference examples.

### defensive_patterns.md — Comprehensive Defect Category Detection list (lines 231–246)
**DIVERGENT** — The list claims "14 defect categories" but the numbering is inconsistent with the actual section structure. Item 13 lumps five distinct categories (Async/Sync Parity, Context Propagation Loss, Field Label Drift, Truth Fragmentation, Callback Concurrency) into a single number — each has its own section, header, and grep table. Item 14 ("Generated and Invisible Code Defects") has no section in this file; the detection guidance is in SKILL.md Steps 5d (lines 248–289).

### SKILL.md — Reference Files table (line 663)
**DIVERGENT** — The table says defensive_patterns.md contains "14-category grep patterns (10 languages)." The actual grep table count depends on counting convention — item 13 contains 5 sub-categories each with their own table, and item 14 is in a different file. The "14-category" claim is defensible but the counting convention isn't documented.

### SKILL.md — Bootstrapping for tooling projects (lines 597–603)
**MISSING** — The tooling projects bootstrapping section only covers Steps 1, 2, 3, and 5 plus Quality risks (Step 6). Step 4 ("Read the Specifications") has no explicit bootstrapping guidance for tooling projects. The Markdown section gets a dedicated Step 4 bullet; tooling projects get none.

### functional_tests.md — C# `[TestFixture]` inconsistency (lines 296–303 vs. 887–898 vs. 1018–1028)
**DIVERGENT** — Some C# examples include `[TestFixture]` on the class while others show methods without class context. When the class is shown, it also lacks the `public` modifier. The playbook's own test harness consistency audit (SKILL.md line 149) specifically warns about this pattern.

### constitution.md — Critical Rule 30% cap cross-reference (after line 166)
**UNDOCUMENTED** — The 30% cap interacts with Phase 1→2 scenario minimums (8+ for medium/large, 2+ per module for small) but the interaction is never documented. An agent doesn't know that combining these constraints limits how many missing-safeguard scenarios are allowed.

### review_protocols.md — Plan-first instruction placement (lines 152–188 vs. template at 191+)
**UNDOCUMENTED** — The generation-time plan-first instruction appears *above* the template, not *within* it. The runtime Execution UX is correctly inside the template. The asymmetric placement is a design choice that isn't explained. An agent jumping to the template section could miss the plan-first step.

## Summary
- Total findings: 9
- By classification: 2 MISSING, 3 DIVERGENT, 3 UNDOCUMENTED, 1 PHANTOM
- Top 3 most important findings:
  1. **C# test methods missing `public` (PHANTOM)** — Every C# example across two files produces the exact silent-failure pattern the playbook warns about. Agent-generated C# tests would have zero tests execute.
  2. **Defensive_patterns.md boundary test examples missing 4 languages (MISSING)** — The bridge between finding defensive patterns and writing tests only covers 6/10 languages.
  3. **Category 14 listed but not present in defensive_patterns.md (DIVERGENT)** — An agent using defensive_patterns.md standalone would miss an entire defect category.
