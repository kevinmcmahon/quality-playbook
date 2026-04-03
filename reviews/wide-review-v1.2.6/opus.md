# Opus — v1.2.6 Review

claude.ai + opus-4.6

```
I need to read all the files carefully before auditing. Let me start with the main SKILL.md and the remaining reference files whose contents aren't already in my context.Now let me read the remaining reference files:Now I have all the content. Let me produce the audit.

---

### SKILL.md — Line 2 (metadata block) vs. Lines 16–17 (banner)
**DIVERGENT** Version number inconsistency. The YAML metadata says `version: 1.2.0`. The banner also says `v1.2.0`. But INSTRUCTIONS.md (which orchestrates this review) consistently refers to `v1.2.6`, and the review prompt itself says "Quality Playbook v1.2.6." Either the SKILL.md version wasn't bumped to match the actual iteration, or INSTRUCTIONS.md references a version that doesn't exist in the delivered files.

---

### SKILL.md — Step 5, Lines 151–159 (Finding the Skeletons)
**MISSING** No guidance for concurrency defect detection. The playbook claims (in REVIEW_PROMPT.md scrutiny area 1) to cover 14 defect categories including "concurrency issue." Step 5 focuses on defensive code patterns (null guards, try/catch, normalization). Step 5a covers state machines. But there is no systematic guidance for finding concurrency bugs — no grep patterns for locks, mutexes, atomics, channels, `synchronized`, `async/await` race conditions, or shared mutable state. The `references/defensive_patterns.md` file also has no concurrency-specific section. An agent working on a Go, Rust, or Java codebase with goroutines/threads would get no actionable detection guidance for this category.

---

### SKILL.md — Step 5, Lines 151–159; references/defensive_patterns.md
**MISSING** No guidance for SQL error detection. The playbook claims coverage of "SQL error" as a defect category. Neither SKILL.md nor any reference file provides grep patterns for SQL injection, query construction, ORM misuse, raw string interpolation in queries, missing parameterization, or transaction management. An agent working on a project with database access would have no SQL-specific detection guidance.

---

### SKILL.md — Step 5, Lines 151–159; references/defensive_patterns.md
**MISSING** No guidance for serialization defect detection. The playbook claims to cover "serialization" defects. The defensive patterns reference mentions JSON parsing briefly (in the "Parsing functions" bullet), but provides no systematic guidance for serialization issues: version skew in serialized formats, missing fields after schema evolution, forward/backward compatibility, binary serialization pitfalls, or deserialization of untrusted data. The guidance for "parsing functions" is two sentences.

---

### SKILL.md — Step 5, Lines 151–159; references/defensive_patterns.md
**MISSING** No guidance for security issue detection. The playbook claims to cover "security issue" as a defect category. There are no grep patterns or guidance for finding authentication/authorization bugs, injection vulnerabilities, insecure defaults, secrets in code, path traversal, SSRF, or other security-specific patterns. The code review guardrails in review_protocols.md mention reviewing "auth changes" in the Human Gate section of constitution.md, but this is a human review checkpoint, not detection guidance for the agent.

---

### SKILL.md — Step 6, Lines 182–200 (Quality Risks from Domain Knowledge)
**MISSING** No guidance for API contract violation or protocol violation detection. The playbook claims to cover "API contract violation" and "protocol violation." Step 6 mentions "external dependencies can change without warning" as a question to ask, but provides no actionable technique: no guidance on checking HTTP status code handling, response schema validation, retry/backoff behavior, content-type negotiation, or protocol-level concerns (TLS version requirements, websocket lifecycle, gRPC error codes). An agent would need to infer these from first principles.

---

### references/defensive_patterns.md — "State Machine Patterns" section
**DIVERGENT** The state machine section in defensive_patterns.md says "see SKILL.md Step 5a for the complete process." But SKILL.md Step 5a (lines 161–174) contains the complete process inline — it doesn't refer back to defensive_patterns.md for state machine details. The reference file's state machine section duplicates and slightly extends the SKILL.md content (adding scenario templates), but the cross-reference direction is backwards. The reference file tells you to look at SKILL.md, but SKILL.md tells you to look at `references/defensive_patterns.md` (line 157: "Read references/defensive_patterns.md for the systematic search approach"). An agent following SKILL.md → defensive_patterns.md → "see SKILL.md Step 5a" hits a circular reference.

---

### SKILL.md — Lines 92–93 (Step 1: build config examples)
**MISSING** Incomplete build config file list for claimed language coverage. Step 1 lists `pyproject.toml / package.json / Cargo.toml` as build config examples. Missing: `build.sbt` (Scala), `pom.xml`/`build.gradle` (Java/Kotlin), `go.mod` (Go), `*.csproj`/`*.sln` (C#), `mix.exs` (Elixir), `Gemfile` (Ruby), `composer.json` (PHP), `Package.swift` (Swift). Step 4b (line 147) does list several of these, but Step 1 — the first place an agent reads build config — omits them. An agent working on a Scala or C# project might not know where to look during the initial orientation step.

---

### references/functional_tests.md — Import Pattern section (lines 36–63)
**MISSING** No import pattern guidance for C#, Ruby, PHP, Kotlin, C, Swift, or Elixir. The playbook claims to work with "any language" and the benchmark includes 15 languages, but import patterns are only provided for Python, Java, Scala, TypeScript, Go, and Rust. The six missing benchmark languages get no import guidance. Import patterns are identified as critical ("getting it wrong means every test fails"), making this a significant gap for those languages.

---

### references/functional_tests.md — "Create Test Setup BEFORE Writing Tests" section (lines 66–83)
**MISSING** No test setup guidance for C#, Ruby, PHP, Kotlin, C, Swift, or Elixir. Same gap as imports — only six languages covered for fixture/setup patterns. An agent generating tests for an Elixir project using ExUnit, or a C# project using xUnit/NUnit, would have no framework-specific setup guidance.

---

### references/defensive_patterns.md — Grep pattern tables
**MISSING** No grep patterns for C#, Ruby, PHP, Kotlin, C, Swift, or Elixir. The null/nil guards, exception handling, and internal helper tables cover Python, Java, Scala, TypeScript, Go, and Rust. The remaining benchmark languages are absent. For example, C# (`?`, `??`, `null!`, `is null`), Kotlin (`?.`, `!!`, `?: throw`), Ruby (`nil?`, `rescue`, `begin/end`), and Elixir (`case`, `with`, `{:ok, _}` / `{:error, _}` pattern matching) all have distinct defensive code idioms that the grep tables don't cover.

---

### references/schema_mapping.md — Mutation value rules and examples
**MISSING** No schema mapping examples for C#, Ruby, PHP, Kotlin, C, Swift, or Elixir. The "Rules for Choosing Mutation Values" section lists idiomatic missing/empty values for Python, Java, Scala, TypeScript, Go, and Rust only. An agent working on a Kotlin project (nullable types, sealed classes) or C# project (nullable reference types, `default`) would get no language-specific guidance for choosing schema-valid mutation values.

---

### SKILL.md — Phase 2, File 2 (lines 227–244); references/verification.md — Benchmark 8
**DIVERGENT** Test runner command inconsistency. SKILL.md line 317 lists test runners as "Python: `pytest -v`, Scala: `sbt testOnly`..." but verification.md Benchmark 8 lists them as "Python: `pytest quality/test_functional.py -v`, Scala: `sbt "testOnly *FunctionalSpec"`..." — the verification reference includes the specific file/pattern targets while SKILL.md gives abbreviated forms. An agent following SKILL.md's shorter commands would run the entire test suite (not just the new functional tests), which contradicts the intent of Benchmark 8 (verify the new tests pass) and could be confused with Benchmark 9 (verify existing tests still pass).

---

### SKILL.md — Phase 1, Step 0 (lines 73–88)
**UNDOCUMENTED** Step 0 assumes filesystem access to chat history folders. The instruction "point me to the folder" and "scan for an index file" assume the agent has filesystem access to read arbitrary directories. This works for Claude Code or Cursor but would not work for a web-UI-based agent (like Claude.ai or ChatGPT) where the user would need to upload files. The prerequisite of filesystem access is not documented, and no fallback is described for agents without it.

---

### SKILL.md — Phase 4 (lines 325–428)
**UNDOCUMENTED** Phase 4 describes an interactive improvement loop, but Phase 3 (Verify) ends with "If any benchmark fails, go back and fix it before proceeding" (line 321). There is no explicit transition criterion from Phase 3 to Phase 4. Specifically: must ALL 13 verification benchmarks pass before moving to Phase 4? Or can the agent present partial results? If the agent is stuck on Benchmark 8 (all tests pass) due to an environmental issue, should it still present results? The phase boundary is ambiguous.

---

### SKILL.md — Phase 2, File 4, line 276
**PHANTOM** "Calibrate unit counts to the project. Read `chunk_size` or equivalent config." This instruction assumes the project has a chunking/batching concept with a configurable chunk size. Many project types (web apps, CLI tools, compilers, libraries) have no such concept. For projects without batch processing, this instruction is meaningless but presented as a universal step. The review_protocols.md reference (lines 352–363) does provide "When in doubt, 10–30 records" as a fallback, but SKILL.md's phrasing implies chunk_size will exist.

---

### references/constitution.md — "Calibrating Scenario Count" section
**DIVERGENT** The constitution reference says "Aim for 2+ scenarios per core module" and "typically yields 8–10 scenarios." SKILL.md line 219 says the same: "2+ scenarios per core module — typically 8–10 total for a medium project." But the QUALITY.md template section "Fitness-to-Purpose Scenarios" says "5–10 scenarios." The lower bound differs: 5 (template) vs. 8 (calibration guidance). An agent aiming for 5 scenarios could pass the template guidance but fail the calibration check.

---

### SKILL.md — Lines 30–39 (What This Skill Produces table)
**UNDOCUMENTED** The table lists `quality/test_functional.*` and `quality/RUN_*.md` but doesn't mention `quality/test_regression.*`, which is a deliverable of Phase 2 File 3 (code review protocol, line 258). The regression test file is described in detail in review_protocols.md as a concrete output, but it's absent from the "What This Skill Produces" summary. An agent or user reading only the summary table wouldn't know regression tests are part of the output.

---

### references/review_protocols.md — Regression test section (lines 53–107)
**UNDOCUMENTED** The regression test protocol says to write tests that "fail on the current implementation, confirming the bug exists." This implies the agent should run the code review, generate findings, then immediately write and run regression tests — all within the same session. But Phase 2 generates the `RUN_CODE_REVIEW.md` protocol as a document; it doesn't say to execute the review during generation. When does the regression test file get created? During Phase 2 generation (before the review is run)? Or only when someone later executes the code review protocol? The lifecycle is undocumented.

---

### SKILL.md — Phase 1, Step 3, line 130
**UNDOCUMENTED** "Critical: Record the import pattern." This instruction says to record the pattern but doesn't say where to record it. The function call map (Step 4b) is similarly undocumented as to where it lives. Are these notes in a scratch file? In the agent's memory? In a generated artifact? For a long-running session, the lack of a specified persistence location means these critical intermediate artifacts could be lost when context windows fill.

---

### references/spec_audit.md — "Model Selection Notes" section
**PHANTOM** The section says "Architecture-focused models (e.g., Claude) tend to find the most issues with fewest false positives" and "Edge-case focused models (e.g., GPT-based tools) tend to catch boundary conditions." These characterizations are presented as empirical findings but are not tied to any specific benchmark data or version. The parenthetical "(e.g., Claude)" and "(e.g., GPT-based tools)" frame model-specific claims as established facts. The note "The specific models that excel will change over time" partially hedges this, but the guidance still reads as concrete model recommendations that may not hold for current model versions.

---

## Summary

- Total findings: 19
- By classification: 9 MISSING, 4 DIVERGENT, 5 UNDOCUMENTED, 1 PHANTOM
- Top 3 most important findings:
  1. **Missing detection guidance for 5+ claimed defect categories** (concurrency, SQL, serialization, security, API/protocol violations). The playbook claims 14-category coverage but provides actionable grep patterns and detection techniques for roughly half. This is the highest-impact gap because it directly undermines the playbook's primary value proposition — an agent following the playbook for a Go service with a Postgres database and concurrent goroutines would get strong guidance on null guards and state machines but essentially nothing on race conditions, SQL errors, or security issues.
  2. **Nine benchmark languages missing from all language-specific guidance tables** (C#, Ruby, PHP, Kotlin, C, Swift, Elixir, plus JavaScript and Markdown from the benchmark). Import patterns, grep tables, test setup, schema mapping, and mutation value rules only cover 6 of 15 benchmark languages. Since import patterns are flagged as "getting this wrong means every test fails," this gap means the playbook will likely produce broken tests for projects in the uncovered languages.
  3. **Version number divergence between SKILL.md (1.2.0) and INSTRUCTIONS.md/REVIEW_PROMPT.md (1.2.6)**. While cosmetic in isolation, this signals that the SKILL.md file being reviewed may not reflect the latest iteration, which could mean other content is also out of sync. It also undermines the playbook's own emphasis on "character-for-character" accuracy and schema fidelity.
```