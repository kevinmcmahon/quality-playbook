# Council of Three Spec Audit — Quality Playbook v1.2.6

## Context

You are auditing a quality playbook skill. The skill is a set of instructions (SKILL.md + 7 reference files) that tells AI coding agents how to explore a codebase and generate quality infrastructure: a quality constitution, functional tests, review protocols, integration test protocols, and a spec audit protocol.

The playbook has been iteratively improved using a benchmark dataset of 2,592 real defects from 55 open-source repositories across 15 programming languages (Java, Python, Go, TypeScript, Rust, Scala, C#, JavaScript, Ruby, PHP, Kotlin, C, Swift, Elixir, Markdown).

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

1. **Detection coverage**: The playbook claims to help agents find bugs across 14 defect categories (error handling, validation gap, configuration error, type safety, state machine gap, concurrency issue, serialization, API contract violation, protocol violation, null safety, silent failure, security issue, SQL error, missing boundary check). For each category, does the playbook provide actionable guidance that would lead an agent to find that category of bug? Which categories have strong guidance and which have only passing mention?

2. **Language generality**: The playbook claims to work with "any language." Read the specific examples, grep patterns, and detection techniques. Which are genuinely language-agnostic? Which silently assume a specific language ecosystem (Python, Java, Go, TypeScript)? Would an agent working on a Rust, C#, Ruby, PHP, Kotlin, C, Swift, or Elixir codebase get equivalent guidance?

3. **Phase transitions**: The playbook has 4 phases (Explore → Generate → Verify → Present). At each phase boundary, is it clear when the agent should move to the next phase? Are there situations where an agent would get stuck at a phase boundary or skip a phase?

4. **Reference file completeness**: The main SKILL.md frequently says "Read references/X.md for details." Do the reference files actually deliver what SKILL.md promises? Are there gaps between what SKILL.md says a reference file contains and what it actually contains?

5. **Test generation quality**: Step 4b says "Read every function's signature before calling it." The functional test reference file provides detailed guidance. But: does the playbook provide enough guidance to generate tests that actually pass on the first run, without manual debugging? What's most likely to go wrong?

6. **Bootstrapping consistency**: The playbook was recently bootstrapped (applied to its own repository). The bootstrapping section in the playbook claims this is "a natural validation step." Is the bootstrapping process adequately described? Could an agent actually execute it from the description alone?

7. **Implicit prerequisites**: What does the playbook assume the agent already knows or has access to? Are these assumptions documented? What happens if an assumption is violated (e.g., no specs exist, no tests exist, the project is tiny, the project is enormous)?

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
