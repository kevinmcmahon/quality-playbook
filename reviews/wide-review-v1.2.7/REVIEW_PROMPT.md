# Council of Three Spec Audit — Quality Playbook v1.2.7

## Context

You are auditing a quality playbook skill. The skill is a set of instructions (SKILL.md + 7 reference files) that tells AI coding agents how to explore a codebase and generate quality infrastructure: a quality constitution, functional tests, review protocols, integration test protocols, and a spec audit protocol.

The playbook has been iteratively improved using a benchmark dataset of 2,592 real defects from 55 open-source repositories across 15 programming languages (Java, Python, Go, TypeScript, Rust, Scala, C#, JavaScript, Ruby, PHP, Kotlin, C, Swift, Elixir, Markdown). v1.2.7 is the result of a 5-model wide review of v1.2.6 that identified 46 unique findings across consensus tiers.

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

**Scrutiny areas:**

1. **Detection coverage completeness**: v1.2.7 added detection guidance for categories that were previously missing (concurrency, SQL, security, serialization, API contract, protocol violations). For each of the 14 claimed defect categories, does the guidance now include actionable grep patterns, scenario templates, or domain prompts? Are the new additions as strong as the original categories (null safety, state machines, error handling), or are some still thin?

2. **Language coverage quality**: v1.2.7 expanded from 6 to 10 languages (added C#, Ruby, Kotlin, PHP). Check the new language entries across all reference files (defensive_patterns.md, functional_tests.md, review_protocols.md, schema_mapping.md, verification.md). Are the new entries complete and correct? Do they follow the same structure and depth as the original 6? Are there inconsistencies where a language appears in one file but not another?

3. **Integration test protocol generality**: The integration test protocol was rewritten in v1.2.7 to be domain-agnostic. It now has general principles, adaptation prompts, and 4 worked examples (REST API, message queue/Kafka, database application, CLI/pipeline). Does the protocol now work for projects that don't resemble an LLM batch orchestrator? Are the worked examples realistic and complete? Does the "present the plan first" UX flow actually work as described?

4. **Phase transition gates**: v1.2.7 added explicit phase transition criteria. Are the gates clear and actionable? Would an agent know exactly when to move from Phase 1 to Phase 2? Is the Phase 4 completion criterion well-defined?

5. **Bootstrapping executability**: v1.2.7 expanded the bootstrapping section to address non-code (Markdown/tooling) projects. Could an agent actually bootstrap the playbook against its own repository using only the instructions provided? What would go wrong?

6. **Defensive patterns vs missing safeguards**: v1.2.7 added a distinction between defensive patterns (existing code that produces tests) and missing safeguards (absent code that produces spec audit findings). Is this distinction clear throughout? Are there places where the old conflation persists?

7. **Internal consistency**: Check cross-references between SKILL.md and reference files. Does SKILL.md accurately describe what each reference file contains? Do verification benchmarks match the Phase 3 summary? Are test count heuristics consistent across files?

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
