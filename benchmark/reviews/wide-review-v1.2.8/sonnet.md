# Sonnet 4.6 (Extended Thinking) — v1.2.8 Review

## Findings

### defensive_patterns.md — Lines 81–162: "Converting Findings to Boundary Tests"
**[MISSING]** The boundary test conversion examples cover only 6 of the 10 claimed supported languages (Python, Java, Scala, TypeScript, Go, Rust). C#, Ruby, Kotlin, and PHP — four of the five newly claimed "fully supported" languages — have no boundary test example in this section.
Playbook says: SKILL.md description: "Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP." Reality: The section providing concrete conversion guidance from defensive pattern to boundary test provides examples in only six of those ten languages. An agent generating tests for a C# project gets no example to follow in the section that is explicitly titled for this purpose.

### defensive_patterns.md — Line 246: Category 14 in "Comprehensive Defect Category Detection"
**[MISSING]** Category 14 ("Generated and Invisible Code Defects") is listed in the numbered enumeration without any parenthetical pointer to where its guidance lives. Every other category in the same list includes a pointer: "(grep table, Systematic Search)", "(grep table, State Machine Patterns section)", "(grep table below)", etc. Category 14 has none.
Playbook says: "14. Generated and Invisible Code Defects" with no attribution. Reality: The guidance lives in SKILL.md Step 5d, which has no grep table in defensive_patterns.md itself. An agent reading defensive_patterns.md in isolation cannot locate this guidance from the list.

### functional_tests.md — Lines 167, 439, 571, 752, 760, 901, 1030 (all Ruby examples)
**[UNDOCUMENTED]** Every Ruby code example in functional_tests.md uses `// Ruby` or `// Ruby (RSpec)` as the language label inside the Ruby fenced code block. Ruby uses `#` for comments, not `//`. `// Ruby` inside a ``` ```ruby ``` block is syntactically invalid Ruby — the interpreter would parse `//` as an empty regex literal followed by an unexpected identifier. This is a systematic error present in every Ruby example across the file.

### SKILL.md — Line 143: "Import Pattern" reference
**[DIVERGENT]** SKILL.md describes functional_tests.md's "Import Pattern" section as "the full ten-language matrix." functional_tests.md contains language-specific prose paragraphs, not a table or matrix.
Playbook says: "See `references/functional_tests.md` § 'Import Pattern' for the full ten-language matrix." Reality: The section titled "Import Pattern: Match the Existing Tests" presents narrative paragraphs per language, not a structured matrix.

### SKILL.md — Line 467: Phase 3 benchmark #8, inline test runner list
**[DIVERGENT]** The inline test runner note in Phase 3 benchmark #8 lists six languages — "(Python: `pytest -v`, Scala: `sbt testOnly`, Java: `mvn test`/`gradle test`, TypeScript: `npx jest`, Go: `go test -v`, Rust: `cargo test`)" — but verification.md covers all ten languages including C#, Ruby, Kotlin, and PHP. This is the same six-language list that was present before the ten-language expansion, and it was not updated.

### functional_tests.md — Lines 592–605: PHP async example
**[PHANTOM]** The PHP async test example uses `$loop = EventLoop::getLoop();` — a method that does not exist in ReactPHP. ReactPHP 1.x uses `React\EventLoop\Loop::get()` (static method). The example also calls `$promise->done()`, which was removed in ReactPHP/Promise 3.x. The code as written would throw a fatal error on any current ReactPHP installation.

### functional_tests.md — Lines 296–304 vs. 242–252, 316–326, 328–340: C# spec-derived test example
**[DIVERGENT]** In the "Writing Spec-Derived Tests" section, the Java, Kotlin, and PHP examples show full test class structure. The C# example shows only the method body with `[Test]` and `[Description]` attributes, with no enclosing `[TestFixture]` class. SKILL.md Step 3 (lines 147–153) explicitly warns that a C# test class missing `[TestFixture]` will compile but never run — the canonical C# example exemplifies the failure mode the playbook warns about.

## Summary
- **Total findings:** 7
- **By classification:** 2 MISSING, 1 UNDOCUMENTED, 3 DIVERGENT, 1 PHANTOM

**Top 3 most important findings:**

1. **defensive_patterns.md lines 81–162 (MISSING — C#, Ruby, Kotlin, PHP boundary test examples):** The boundary test conversion section is where agents get their concrete template. Four of the ten claimed languages get nothing.

2. **functional_tests.md lines ~592–605 (PHANTOM — PHP async example):** Code examples that produce fatal errors undermine trust. An agent following this example will produce broken tests.

3. **SKILL.md line 467 (DIVERGENT — 6-language test runner list):** Residual artifact of v1.2.7. SKILL.md's self-check benchmark note still reads as six-language guidance, leaving C#, Ruby, Kotlin, and PHP projects without test runner guidance at self-check time.
