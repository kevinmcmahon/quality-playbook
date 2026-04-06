# Council of Three Spec Audit — Quality Playbook v1.2.8

## Context

You are auditing a quality playbook skill. The skill is a set of instructions (SKILL.md + 7 reference files) that tells AI coding agents how to explore a codebase and generate quality infrastructure: a quality constitution, functional tests, review protocols, integration test protocols, and a spec audit protocol.

The playbook has been iteratively improved using a benchmark dataset of 2,592 real defects from 55 open-source repositories across 15 programming languages (Java, Python, Go, TypeScript, Rust, Scala, C#, JavaScript, Ruby, PHP, Kotlin, C, Swift, Elixir, Markdown). v1.2.8 is the result of addressing 8 issues identified in the v1.2.7 wide review.

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

**Scrutiny areas (targeted at v1.2.8 changes):**

1. **Language coverage completeness and quality** — v1.2.8 claims "Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP" (SKILL.md description). Do the newly added C#, Ruby, Kotlin, PHP examples in functional_tests.md, schema_mapping.md, verification.md follow idiomatic conventions for each language? Are there any languages still missing from any section? Are there inconsistencies where a language appears in one file but not another?

2. **New grep pattern table quality** — v1.2.8 added 6 new grep pattern tables (Protocol Violations, Async/Sync Parity, Context Propagation Loss, Field Label Drift, Truth Fragmentation, Callback Concurrency) to defensive_patterns.md. Are the patterns accurate and useful? Do they miss common patterns in any language? Are they at the same depth as the original categories?

3. **Plan-first workflow resolution** — SKILL.md now references "present the plan first" in multiple contexts (generation-time in Phase 2, runtime in Phase 4 Execution UX). Does the instruction now avoid the structural contradiction from v1.2.7? Is the generation-time vs runtime distinction clear? Is the plan-first template embedded in review_protocols.md so agents following the template get it automatically?

4. **Phase gate quality** — Phase 1→2 now has flexible scenario counts ("8+ for medium/large projects" or "2+ per core module for small projects"). Phase 2→3 now checks "substantive content not just existence." Phase 4 no longer claims to be a gate. Are these consistent with each other and with the constitution? Do they avoid the small-project contradiction from v1.2.7?

5. **Constitution Critical Rule revision** — The rule now has explicit exceptions for missing safeguard scenarios (30% cap) and Human Gate scenarios. Does this resolve the conflict with defensive_patterns.md's "do not write boundary tests for missing safeguards"? Is the 30% cap consistent with scenario count guidance in SKILL.md?

6. **Bootstrapping completeness** — Steps 4 and 6 now have adaptation guidance for Markdown/documentation projects. Is the guidance specific enough to be actionable? Does it address the same concerns as the Steps 1-3, 5 guidance?

7. **Internal consistency** — With 3,487 lines across 8 files, are there any cross-file contradictions introduced by the v1.2.8 changes? Do numbers, counts, and cross-references align? For example: SKILL.md mentions "ten-language matrix" (line 143) — does the matrix exist in functional_tests.md? SKILL.md line 141 previously said "six-language matrix" (v1.2.7) — has it been updated?

8. **Canonical defect category list** — The new numbered list in defensive_patterns.md (line 232+) claims 14 categories. Count the actual sections in defensive_patterns.md — do the category count and enumeration match the list?

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
