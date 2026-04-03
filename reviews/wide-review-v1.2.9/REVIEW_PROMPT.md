# Council of Three Spec Audit — Quality Playbook v1.2.9

## Context

You are auditing a quality playbook skill. The skill is a set of instructions (SKILL.md + 7 reference files) that tells AI coding agents how to explore a codebase and generate quality infrastructure: a quality constitution, functional tests, review protocols, integration test protocols, and a spec audit protocol.

The playbook has been iteratively improved using a benchmark dataset of 2,592 real defects from 55 open-source repositories across 15 programming languages (Java, Python, Go, TypeScript, Rust, Scala, C#, JavaScript, Ruby, PHP, Kotlin, C, Swift, Elixir, Markdown). v1.2.9 is the result of addressing 23 issues identified in the v1.2.8 wide review (5-model cross-model triage). This is the fourth review iteration (v1.2.6 → v1.2.7 → v1.2.8 → v1.2.9).

All playbook files follow below this prompt.

## Task

Act as the Tester. Read all provided files and audit the playbook against its own stated goals and methodology.

**Rules:**
- ONLY list defects. Do not summarize what works well.
- For EVERY defect, cite the specific file and section/line where the issue exists.
  If you cannot cite a location, do not include the finding.
- Before claiming something is missing, search all provided files — it may be in a reference file.
- Before claiming something exists, read the actual text, not just the section heading.
- Classify each finding: MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM

**Defect classifications:**
- **MISSING** — The playbook claims to cover something but doesn't actually provide guidance for it
- **DIVERGENT** — Two sections give conflicting or inconsistent guidance
- **UNDOCUMENTED** — The playbook does something (implicitly assumes, silently requires) without documenting it
- **PHANTOM** — The playbook describes a capability or process that doesn't actually work as described

**Scrutiny areas (targeted at v1.2.9 changes):**

1. **Code example correctness** — v1.2.9 fixed four PHANTOM code bugs from v1.2.8: C# test methods now have `public` modifier, Ruby comments now use `#` instead of `//`, PHP async uses modern ReactPHP 3.x API, Go test setup uses the `tmpDir` variable. Verify these fixes are correct and complete — are there any remaining instances of the old patterns? Are the new code examples idiomatic and would they compile/run without errors?

2. **Language coverage completeness** — v1.2.9 expanded downstream files to match the 10-language claim. Check: Do functional_tests.md, schema_mapping.md, defensive_patterns.md, verification.md, and review_protocols.md now consistently cover all 10 languages (Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP)? Are there sections where some languages still appear and others don't? Is SKILL.md's Phase 3 benchmark #8 test runner list now complete?

3. **New boundary test examples** — v1.2.9 added C#, Ruby, Kotlin, PHP boundary test conversion examples to defensive_patterns.md. Are these examples idiomatic for each language? Do they follow the same pattern quality as the existing Python/Java/Scala/TypeScript/Go/Rust examples? Would they compile and run?

4. **Plan-first template embedding** — v1.2.9 embedded the generation-time plan-first step in review_protocols.md. Is the distinction between generation-time (before writing the protocol) and runtime (before executing tests) now clear in review_protocols.md? Could an agent following review_protocols.md alone implement both moments correctly?

5. **Field Reference Table in worked examples** — v1.2.9 added a Field Reference Table to the REST API worked example. Is the table format consistent with what the template mandates? Do the other 3 worked examples still lack it, or is one example sufficient as a model?

6. **Bootstrapping sub-step adaptation** — v1.2.9 added adaptation guidance for Steps 4b, 5a, 5b, 5c, 5d for documentation/tooling projects. Is the guidance specific enough to be actionable? Does it create any contradictions with the main Step guidance?

7. **30% cap interaction** — v1.2.9 documented the interaction between the constitution's 30% non-testable scenario cap and Phase 1→2 scenario minimums. Is the interaction clearly explained? Is the math consistent (e.g., with 10 scenarios, no more than 3 can be non-testable)?

8. **Internal consistency** — With 3,602 lines across 8 files, are there any cross-file contradictions? Do numbers, counts, cross-references, and version numbers all align? Check: Does the "14 defect categories" claim in defensive_patterns.md now have proper cross-references for all 14? Does the SKILL.md reference to functional_tests.md's Import Pattern section accurately describe what's there?

**Output format:**

For each finding:
```
### [filename] — Section/Line
**[MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM]** Description.
Playbook says: [quote or reference]. Reality: [what actually happens or is missing].
```

After all findings, provide:
```
## Summary
- Total findings: [N]
- By classification: [N] MISSING, [N] DIVERGENT, [N] UNDOCUMENTED, [N] PHANTOM
- Top 3 most important findings (the ones that would most improve the playbook if fixed)
```
