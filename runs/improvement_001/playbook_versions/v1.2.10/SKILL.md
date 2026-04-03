---
name: quality-playbook
description: "Explore any codebase from scratch and generate six quality artifacts: a quality constitution (QUALITY.md), spec-traced functional tests, a code review protocol with regression test generation, an integration testing protocol, a multi-model spec audit (Council of Three), and an AI bootstrap file (AGENTS.md). Includes state machine completeness analysis and missing safeguard detection. Full support for Python, Java, Scala, TypeScript, Go, Rust, C#, Ruby, Kotlin, PHP. For other languages, the general principles and templates apply — adapt the language-specific examples (grep patterns, test setup, import conventions) to your language's idioms. Use this skill whenever the user asks to set up a quality playbook, generate functional tests from specifications, create a quality constitution, build testing protocols, audit code against specs, or establish a repeatable quality system for a project. Also trigger when the user mentions 'quality playbook', 'spec audit', 'Council of Three', 'fitness-to-purpose', 'coverage theater', or wants to go beyond basic test generation to build a full quality system grounded in their actual codebase."
license: Complete terms in LICENSE.txt
metadata:
  version: 1.2.10
  author: Andrew Stellman
  github: https://github.com/andrewstellman/
---

# Quality Playbook Generator

**When this skill starts, display this banner before doing anything else:**

```
Quality Playbook v1.2.10 — by Andrew Stellman
https://github.com/andrewstellman/
```

Generate a complete quality system tailored to a specific codebase. Unlike test stub generators that work mechanically from source code, this skill explores the project first — understanding its domain, architecture, specifications, and failure history — then produces a quality playbook grounded in what it finds.

## Why This Exists

Most software projects have tests, but few have a quality *system*. Tests check whether code works. A quality system answers harder questions: what does "working correctly" mean for this specific project? What are the ways it could fail that wouldn't be caught by tests? What should every developer (human or AI) know before touching this code?

Without a quality playbook, every new contributor (and every new AI session) starts from scratch — guessing at what matters, writing tests that look good but don't catch real bugs, and rediscovering failure modes that were already found and fixed months ago. A quality playbook makes the bar explicit, persistent, and inherited.

## What This Skill Produces

Six files that together form a repeatable quality system:

| File | Purpose | Why It Matters | Executes Code? |
|------|---------|----------------|----------------|
| `quality/QUALITY.md` | Quality constitution — coverage targets, fitness-to-purpose scenarios, theater prevention | Every AI session reads this first. It tells them what "good enough" means so they don't guess. | No |
| `quality/test_functional.*` | Automated functional tests derived from specifications | The safety net. Tests tied to what the spec says should happen, not just what the code does. Use the project's language: `test_functional.py` (Python), `FunctionalSpec.scala` (Scala), `functional.test.ts` (TypeScript), `FunctionalTest.java` (Java), etc. | **Yes** |
| `quality/RUN_CODE_REVIEW.md` | Code review protocol with guardrails that prevent hallucinated findings | AI code reviews without guardrails produce confident but wrong findings. The guardrails (line numbers, grep before claiming, read bodies) often improve accuracy. | No |
| `quality/RUN_INTEGRATION_TESTS.md` | Integration test protocol — end-to-end pipeline across all variants | Unit tests pass, but does the system actually work end-to-end with real external services? | **Yes** |
| `quality/RUN_SPEC_AUDIT.md` | Council of Three multi-model spec audit protocol | No single AI model catches everything. Three independent models with different blind spots catch defects that any one alone would miss. | No |
| `AGENTS.md` | Bootstrap context for any AI session working on this project | The "read this first" file. Without it, AI sessions waste their first hour figuring out what's going on. | No |

Plus output directories: `quality/code_reviews/`, `quality/spec_audits/`, `quality/results/`.

The critical deliverable is the functional test file (named for the project's language and test framework conventions). The Markdown protocols are documentation for humans and AI agents. The functional tests are the automated safety net.

## How to Use

Point this skill at any codebase:

```
Generate a quality playbook for this project.
```

```
Update the functional tests — the quality playbook already exists.
```

```
Run the spec audit protocol.
```

If a quality playbook already exists (`quality/QUALITY.md`, functional tests, etc.), read the existing files first, then evaluate them against the self-check benchmarks in the verification phase. Don't assume existing files are complete — treat them as a starting point.

### Degraded Mode (Limited Environment)

This skill assumes access to file creation and command execution. If running in a restricted environment (web UI without computer use, or read-only access):

1. **File creation:** You can still read the codebase and generate all Markdown files (QUALITY.md, protocols). Copy them manually from the chat to your editor.
2. **Test execution:** If you cannot run tests, verify them against the reference file standards instead (check imports match existing tests, assertions follow verification standards, etc.). Include a note in AGENTS.md that tests need manual verification.
3. **Integration test verification:** You can still write the protocol — it will be executable by humans or unrestricted agents later. Include setup instructions clearly.
4. **Spec audit:** The audit protocol is a prompt — paste it into your preferred models even if this environment is restricted.

5. **Phase 4 interactive UX:** If running in a non-interactive environment (batch mode, no user present), skip the interactive improvement loop. Present the summary table and improvement options in the output — the user can follow up in a separate session.

The skill's output is still valuable in degraded mode — it just requires manual verification steps that would normally be automated.

---

## Phase 1: Explore the Codebase (Do Not Write Yet)

Spend the first phase understanding the project. The quality playbook must be grounded in this specific codebase — not generic advice.

**Why explore first?** The most common failure in AI-generated quality playbooks is producing generic content — coverage targets that could apply to any project, scenarios that describe theoretical failures, tests that exercise language builtins instead of project code. Exploration prevents this by forcing every output to reference something real: a specific function, a specific schema, a specific defensive code pattern. If you can't point to where something lives in the code, you're guessing — and guesses produce quality playbooks nobody trusts.

**Scaling for large codebases:** For projects with more than ~50 source files, don't try to read everything. Focus exploration on the 3–5 core modules (the ones that handle the primary data flow, the most complex logic, and the most failure-prone operations). Read representative tests from each subsystem rather than every test file. The goal is depth on what matters, not breadth across everything.

### Step 0: Ask About Development History

Before exploring code, ask the user one question:

> "Do you have exported AI chat history from developing this project — Claude exports, Gemini takeouts, ChatGPT exports, Claude Code transcripts, or similar? If so, point me to the folder. The design discussions, incident reports, and quality decisions in those chats will make the generated quality playbook significantly better."

If the user provides a chat history folder:

1. **Scan for an index file first.** Look for files named `INDEX*`, `CONTEXT.md`, `README.md`, or similar navigation aids. If one exists, read it — it will tell you what's there and how to find things.
2. **Search for quality-relevant conversations.** Look for messages mentioning: quality, testing, coverage, bugs, failures, incidents, crashes, validation, retry, recovery, spec, fitness, audit, review. Also search for the project name.
3. **Extract design decisions and incident history.** The most valuable content is: (a) incident reports — what went wrong, how many records affected, how it was detected, (b) design discussions — why a particular approach was chosen, what alternatives were rejected, (c) quality framework discussions — coverage targets, testing philosophy, model review experiences, (d) cross-model feedback — where different AI models disagreed about the code.
4. **Don't try to read everything.** Chat histories can be enormous. Use the index to find the most relevant conversations, then search within those for quality-related content. 10 minutes of targeted searching beats 2 hours of exhaustive reading.

This context is gold. A chat history where the developer discussed "why we chose this concurrency model" or "the time we lost 1,693 records in production" transforms generic scenarios into authoritative ones.

If the user doesn't have chat history, proceed normally — the skill works without it, just with less context.

### Step 1: Identify Domain, Stack, and Specifications

Read the README, existing documentation, and build config (`pyproject.toml` / `package.json` / `Cargo.toml`). Answer:

- What does this project do? (One sentence.)
- What language and key dependencies?
- What external systems does it talk to?
- What is the primary output?

**Find the specifications.** Specs are the source of truth for functional tests. Search in order: `AGENTS.md`/`CLAUDE.md` in root, `specs/`, `docs/`, `spec/`, `design/`, `architecture/`, `adr/`, then `.md` files in root. Record the paths.

**If no formal spec documents exist**, the skill still works — but you need to assemble requirements from other sources. In order of preference:

1. **Ask the user** — they often know the requirements even if they're not written down.
2. **README and inline documentation** — many projects embed requirements in their README, API docs, or code comments.
3. **Existing test suite** — tests are implicit specifications. If a test asserts `process(x) == y`, that's a requirement.
4. **Type signatures and validation rules** — schemas, type annotations, and validators define what the system accepts and rejects.
5. **Infer from code behavior** — as a last resort, read the code and infer what it's supposed to do. Mark these as *inferred requirements* in QUALITY.md and flag them for user confirmation.

When working from non-formal requirements, label each scenario and test with a **requirement tag** that includes a confidence tier and source:

- `[Req: formal — README §3]` — written by humans in a spec document. Authoritative.
- `[Req: user-confirmed — "must handle empty input"]` — stated by the user but not in a formal doc. Treat as authoritative.
- `[Req: inferred — from validate_input() behavior]` — deduced from code. Flag for user review.

Use this exact tag format in QUALITY.md scenarios, functional test documentation, and spec audit findings. It makes clear which requirements are authoritative and which need validation.

### Step 2: Map the Architecture

List source directories and their purposes. Read the main entry point, trace execution flow. Identify:

- The 3–5 major subsystems
- The data flow (Input → Processing → Output)
- The most complex module
- The most fragile module

### Step 3: Read Existing Tests

Read the existing test files — all of them for small/medium projects, or a representative sample from each subsystem for large ones. Identify: test count, coverage patterns, gaps, and any coverage theater (tests that look good but don't catch real bugs).

**Critical: Record the import pattern.** How do existing tests import project modules? Every language has its own conventions (Python `sys.path` manipulation, Java/Scala package imports, TypeScript relative paths or aliases, Go package/module paths, Rust `use crate::` or `use myproject::`). You must use the exact same pattern in your functional tests — getting this wrong means every test fails with import/resolution errors. See `references/functional_tests.md` § "Import Pattern" for the full ten-language Import Pattern guide.

**Identify integration test runners.** Look for scripts or test files that exercise the system end-to-end against real external services (APIs, databases, etc.). Note their patterns — you'll need them for `RUN_INTEGRATION_TESTS.md`.

**Test harness consistency audit.** Check that all test files have the required framework-level annotations or attributes to be discovered and executed by the test runner. Common silent failures:

- **Missing class-level attributes**: NUnit `[TestFixture]`, xUnit/MSTest `[TestClass]`, JUnit `@RunWith` — without these, the test class exists but its tests never run. The test suite reports success because zero tests were executed.
- **Conditional compilation gaps**: When test files use `#if`/`#ifdef` for platform-specific compilation, verify that test discovery attributes are present in *all* conditional branches, not just one.
- **Framework mismatch**: When a project uses multiple test frameworks (e.g., NUnit for some suites, xUnit for others), verify each test file uses the correct framework's conventions. A test written with NUnit assertions but missing `[TestFixture]` will compile but never run.

Compare each test file against a reference test file in the same directory. If the reference has `[TestFixture]` and the new file doesn't, that's likely a missing attribute.

**If the project has zero existing tests:** This is a greenfield project. Document this clearly — you cannot infer import patterns or fixture conventions from code that isn't there. Instead:

1. **Read the build/configuration files** to understand the project structure (`src/`, `tests/`, `spec/`, etc.). Where would tests *normally* go?
2. **Check the project language and common test frameworks** — Python projects typically use pytest, Java projects use JUnit, TypeScript projects use Jest, etc. Assume the conventional framework unless the project specifies otherwise.
3. **Use language-standard import patterns** — Without existing code to copy, use the idiomatic pattern for the language: Python package imports, Java package structure, TypeScript relative paths with typical tsconfig setup, etc.
4. **Fixtures: choose inline setup** — Prefer inline test data over shared fixtures, since there's no existing convention to follow. Use the framework's built-in temp directory support (`tmp_path` in pytest, `@TempDir` in JUnit, etc.).
5. **Record assumptions** — In the AGENTS.md file, note "no existing tests, assuming [framework] with [import pattern]." This tells future sessions what you assumed so they can correct it if wrong.

### Step 4: Read the Specifications

Walk each spec document section by section. For every section, ask: "What testable requirement does this state?" Record spec requirements without corresponding tests — these are the gaps the functional tests must close.

If using inferred requirements (from tests, types, or code behavior), tag each with its confidence tier using the `[Req: tier — source]` format defined in Step 1. Inferred requirements feed into QUALITY.md scenarios and should be flagged for user review in Phase 4.

### Step 4b: Read Function Signatures and Real Data

Before writing any test, you must know exactly how each function is called. For every module you identified in Step 2:

1. **Read the actual function signatures** — parameter names, types, defaults. Don't guess from usage context — read the function definition and any documentation (Python docstrings, Java/Scala Javadoc/ScalaDoc, TypeScript type annotations, Go godoc comments, Rust doc comments and type signatures).
2. **Read real data files** — If the project has items files, fixture files, config files, or sample data (in `pipelines/`, `fixtures/`, `test_data/`, `examples/`), read them. Your test fixtures must match the real data shape exactly.
3. **Read existing test fixtures** — How do existing tests create test data? Copy their patterns. If they build config dicts with specific keys, use those exact keys.
4. **Check library versions** — Check the project's dependency manifest (`requirements.txt`, `build.sbt`, `package.json`, `pom.xml`/`build.gradle`, `go.mod`, `Cargo.toml`) to see what's actually available. Don't write tests that depend on library features that aren't installed. If a dependency might be missing, use the test framework's skip mechanism — see `references/functional_tests.md` § "Library version awareness" for framework-specific examples.

Record a **function call map**: for each function you plan to test, write down its name, module, parameters, and what it returns. This map prevents the most common test failure: calling functions with wrong arguments.

### Step 5: Find the Skeletons

This is the most important step. Search for defensive code patterns — each one is evidence of a past failure or known risk.

**Why this matters:** Developers don't write `try/except` blocks, null checks, or retry logic for fun. Every piece of defensive code exists because someone got burned. A `try/except` around a JSON parse means malformed JSON happened in production. A null check on a field means that field was missing when it shouldn't have been. These patterns are the codebase whispering its history of failures. Each one becomes a fitness-to-purpose scenario and a boundary test.

**Read `references/defensive_patterns.md`** for the systematic search approach, comprehensive grep patterns across 14 defect categories, language-specific detection guidance, and how to convert findings into fitness-to-purpose scenarios and boundary tests.

Minimum bar: at least 2–3 defensive patterns per core source file. If you find fewer, you're skimming — read function bodies, not just signatures. Search across all 14 defect categories, not just null guards and exceptions.

**Error envelope extraction.** When error callbacks or catch handlers receive wrapper objects (e.g., `{ error, path, context }`), check whether downstream code extracts the inner error before passing it to error constructors or logging. A common bug: the entire envelope is passed where only the inner error is expected, producing corrupted error messages or lost stack traces. Similarly, when wrapping arbitrary objects as Error instances, verify that the `message` property is explicitly extracted and passed to the constructor — don't rely on `Object.assign()` or spread operators, which may not transfer error-specific properties across execution boundaries (VMs, workers, iframes).

**Hardcoded indices in iteration.** When code iterates over a collection (array, list, map) using `.map()`, `.forEach()`, or a loop, check that array accesses inside the loop body use the loop variable, not a hardcoded index. A hardcoded `items[0]` inside a `.map((item, i) => ...)` routes all iterations to the first element — a bug that produces correct results for single-element inputs but silently corrupts multi-element batches.

### Step 5a: Trace State Machines

If the project has any kind of state management — status fields, lifecycle phases, workflow stages, mode flags — trace the state machine completely. This catches a category of bugs that defensive pattern analysis alone misses: states that exist but aren't handled.

**How to find state machines:** Search for status/state fields in models, enums, or constants (e.g., `status`, `state`, `phase`, `mode`). Search for guards that check status before allowing actions (e.g., `if status == "running"`, `match self.state`). Search for state transitions (assignments to status fields).

**For each state machine you find:**

1. **Enumerate all possible states.** Read the enum, the constants, or grep for every value the field is assigned. List them all.
2. **For each consumer of state** (UI handlers, API endpoints, control flow guards), check: does it handle every possible state? A `switch`/`match` without a meaningful default, or an `if/elif` chain that doesn't cover all states, is a gap.
3. **For each state transition**, check: can you reach every state? Are there states you can enter but never leave? Are there states that block operations that should be available?
4. **Record gaps as findings.** A status guard that allows action X for "running" but not for "stuck" is a real bug if the user needs to perform action X on stuck processes. A process that enters a terminal state but never triggers cleanup is a real bug.

**Why this matters:** State machine gaps produce bugs that are invisible during normal operation but surface under stress or edge conditions — exactly when you need the system to work. A batch processor that can't be killed when it's in "stuck" status, or a watcher that never self-terminates after all work completes, or a UI that refuses to resume a "pending" run, are all symptoms of incomplete state handling. These bugs don't show up in defensive pattern analysis because the code isn't defending against them — it's simply not handling them at all.

**Cross-boundary signal propagation.** In request/response pipelines, streaming systems, and middleware chains, trace control signals (abort, cancel, timeout, close) from their point of creation through every abstraction boundary they cross. Common failure: a "combined" signal is created (e.g., merging timeout + client abort) but a downstream layer passes only one of its constituent signals, so the combined behavior is lost. For each signal:

- Where is it created?
- Through how many layers/functions does it pass?
- At each boundary, is the *correct* signal forwarded, or a subset?
- Do both normal completion and error/abort paths handle the signal consistently? (Watch for cases where close handlers and abort handlers both attempt the same cleanup, creating a race.)

### Step 5b: Map Schema Types

If the project has a validation layer (Pydantic models in Python, JSON Schema, TypeScript interfaces/Zod schemas, Java Bean Validation annotations, Scala case class codecs), read the schema definitions now. For every field you found a defensive pattern for, record what the schema accepts vs. rejects.

**Read `references/schema_mapping.md`** for the mapping format and why this matters for writing valid boundary tests.

### Step 5c: Audit Parallel Code Paths and Context Propagation

This step catches a category of bugs that arises in code with parallel structures — analogous code paths that should behave symmetrically but don't.

**Context propagation loss.** When a function receives an object as a parameter (HTTP client, database connection, configuration bundle, request context) and then creates a *new* instance of that type internally, check whether the new instance preserves all relevant context from the original. The most common pattern: a factory function builds a fresh object with only some fields copied, silently dropping headers, metadata, authentication tokens, or configuration that the original carried. Look for `NewXxx()` calls inside functions that already receive an `Xxx` parameter — if the function could reuse or shallow-copy the original instead, the new construction likely loses context.

**Parallel path symmetry.** When code handles two or more analogous entities through similar code paths (e.g., reviewers vs. assignees, readers vs. writers, request vs. response), audit for symmetry:

- **Condition symmetry**: If path A enters a branch using a computed flag, path B should use the same kind of flag — not a raw nil check or a different boolean that happens to correlate.
- **Transformation symmetry**: If path A applies a set of transformers (validators, replacers, formatters), path B should apply the same set unless there's a documented reason for divergence.
- **Contract symmetry**: If path A handles special values (e.g., `@me`, bot suffixes, escape sequences), check whether path B handles the same special values.

Asymmetries in parallel paths are a reliable signal of bugs: when one path was updated and its sibling was forgotten.

**Field label drift.** When code extracts fields from structured data (CSV columns, table rows, API responses, config entries) by positional index and assigns them to named variables, check that the variable name still matches what the position actually contains. Data formats evolve — a column that was once "title" may now contain an issue reference number, but the variable name `title` persists because it still works at the type level (both are strings). Search for positional extraction patterns (`parts[N]`, `row[N]`, `columns[N]`) and verify each variable name against the current column header or schema definition. This is especially common in Markdown table parsers, CSV processors, and any code that uses integer indices instead of named fields.

**Callback concurrency.** When code passes a callback or closure to a library, determine whether the library invokes it synchronously or in a separate thread/goroutine/task. If the callback captures mutable state that the main code path also writes, this is a data race risk even if neither the callback nor the main code looks concurrent in isolation. Search for library APIs that document or imply asynchronous callback execution (options functions, event handlers, stream processors).

**Truth fragmentation.** When a set of allowed values (canonical categories, status codes, permission levels, feature flags) is defined in more than one location — a Python list in one file, a dict in another, an enum in a third — check that all definitions contain exactly the same set. Over time, one copy gets updated and the others drift. Search for parallel definitions by grepping for the canonical values themselves. If the same string literal (e.g., `"API contract violation"`) appears in two different constant definitions, that's a fragmentation risk. The fix is usually to define the canonical set once and import it everywhere, or to add cross-reference comments and a test that asserts equality. This pattern is especially common in data processing pipelines where normalization, validation, and reporting each define their own version of the allowed values.

**Schema-struct alignment.** When a data structure (struct, class, interface) is serialized or used to generate queries (GraphQL, SQL, API requests), verify that every field in the structure has a corresponding entry in the serialization layer. Look for:

- Struct fields with serialization tags (JSON, XML, protobuf) that don't appear in query builders or schema generators
- Hardcoded field lists that can drift from the struct definition when fields are added
- Missing fields in generated queries that the struct expects to be populated

### Step 5d: Check Generated and Invisible Code

Some code that executes at runtime isn't visible in source files. This step catches bugs in code produced by metaprogramming, code generation, and macro expansion.

**Macro and code generation review.** Identify all code generation mechanisms in the project: derive macros (Rust `#[derive(...)]`), annotation processors (Java `@Generated`), template engines, code generators, build-time scripts. For each:

- Determine what code the mechanism produces. If tools exist to expand or dump generated code (Rust: `cargo expand`; Java: look in `target/generated-sources`; TypeScript: check compiled output), use them.
- Apply the same review principles to generated code as to hand-written code — especially trait/interface conflicts, type resolution ambiguity, and missing bounds.
- When a macro generates implementations of multiple traits or interfaces, check whether any two implementations create ambiguous method resolution (e.g., two traits providing the same method name with different type bounds).

**Sync/async implementation parity.** When a project provides both synchronous and asynchronous versions of the same functionality (common in HTTP clients, database drivers, I/O libraries), compare their parameter lists, configuration propagation, and error handling:

- Diff the constructor/factory parameters of sync vs. async variants. Missing parameters in one variant indicate context propagation loss.
- Check that configuration options (timeouts, SSL context, proxy settings, connection pools) are forwarded identically in both paths.
- Verify error types and error handling paths are symmetric.

**Boundary conditions with empty and zero values.** Systematically check what happens when inputs are empty or zero:

- Empty strings, empty arrays, zero-length files, zero-size buffers: trace through all arithmetic and iteration. Integer underflow from `length - 1` when `length == 0` is a common crash.
- Streaming/chunked processing: does the code yield or propagate empty chunks? Empty chunks in text streaming can produce spurious empty strings that confuse consumers.
- Search for subtraction operations on unsigned integers or length values — each is a potential underflow when the value is zero.

**Placeholder values masking data gaps.** When structured data files (CSV, Markdown tables, JSON, YAML configs) contain sentinel values like `--`, `N/A`, `TBD`, `TODO`, `unknown`, `(none)`, or parenthesized notes like `(see above)`, `(merge)`, `(parent)` — these often mask missing data that downstream code assumes is present. Search for common placeholder patterns and check: (a) does downstream code handle these values, or will it crash or produce wrong results? (b) is the set of accepted placeholders documented, or does each new one silently pass through? (c) do validation tests check for placeholder leakage into output? The most dangerous case is when placeholder values are valid in the schema's type system (e.g., `"unknown"` passes a string-type check) but meaningless semantically. Tests that validate format but not content miss this entirely.

**Regex pattern correctness.** When code uses regular expressions for validation (hostnames, IPs, URLs, emails, version strings), verify metacharacter escaping:

- Literal dots must be escaped as `\.` — an unescaped `.` matches any character, silently accepting invalid input.
- Anchors (`^`, `$`) must be present when the intent is full-string matching.
- Character classes and quantifiers must match the specification (e.g., IPv4 octets are 1-3 digits, not unbounded).

**Strict parsing format coverage.** When code uses strict parsing functions (`ParseExact`, `strptime` with exact format, `DateTimeFormatter.ofPattern`), verify that the format string covers all valid inputs the system should accept:

- If the function accepts `HH:mm:ss.FFFFFFF` but users can provide `HH:mm`, the shorter format will be rejected. Check whether a format array or fallback chain handles common variations.
- Compare strict parsing against the corresponding lenient parser (`Parse` vs. `ParseExact`, `strptime` vs. `dateutil.parser`). If lenient parsing accepts inputs that strict parsing rejects, the strict format may be too narrow.
- Check that API-level documentation of accepted formats matches the implementation's format strings.

**API visibility and trimming attributes.** In compiled languages with dead-code elimination, link-time optimization, or IL trimming (.NET, Rust, C/C++ LTO), verify that public API methods carry the required attributes to survive trimming:

- If an internal method is annotated with `[RequiresUnreferencedCode]` or similar, all public methods that call it must either carry the same annotation, be marked as trim-safe, or suppress the warning explicitly.
- Check for asymmetry between method overloads — when one overload has trimming annotations and another doesn't, the unannotated overload may silently break in trimmed builds.
- Visibility changes (public → private, or vice versa) on methods with trimming implications must be audited for downstream impact.

### Step 6: Identify Quality Risks (Code + Domain Knowledge)

Every project has a different failure profile. This step uses **two sources** — not just code exploration, but your training knowledge of what goes wrong in similar systems.

**From code exploration**, ask:
- What does "silently wrong" look like for this project?
- What external dependencies can change without warning?
- What looks simple but is actually complex?
- Where do cross-cutting concerns hide?

**From domain knowledge**, ask:
- "What goes wrong in systems like this?" — If it's a batch processor, think about crash recovery, idempotency, silent data loss, state corruption. If it's a web app, think about auth edge cases, race conditions, input validation bypasses. If it handles randomness or statistics, think about seeding, correlation, distribution bias.
- "Does this code implement a published specification (RFC, W3C, POSIX, language spec)?" — If so, identify the specific specification sections the code implements. Check that multi-step computations (hash construction, authentication handshakes, encoding sequences) follow the specification's exact ordering and field inclusion. Pay special attention to conditional branches that handle different protocol versions or modes — each branch must independently satisfy its specification. When code comments reference RFC section numbers, verify the implementation matches that section.
- "What produces correct-looking output that is actually wrong?" — This is the most dangerous class of bug: output that passes all checks but is subtly corrupted.
- "What happens at 10x scale that doesn't happen at 1x?" — Chunk boundaries, rate limits, timeout cascading, memory pressure.
- "What happens when this process is killed at the worst possible moment?" — Mid-write, mid-transaction, mid-batch-submission.
- "What information does the user need before committing to an irreversible or expensive operation?" — Pre-run cost estimates, confirmation of scope (especially when fan-out or expansion will multiply the work), resource warnings. If the system can silently commit the user to hours of processing or significant cost without showing them what they're about to do, that's a missing safeguard. Search for operations that start long-running processes, submit batch jobs, or trigger expansion/fan-out — and check whether the user sees a preview, estimate, or confirmation with real numbers before the point of no return.
- "What happens when a long-running process finishes — does it actually stop?" — Polling loops, watchers, background threads, and daemon processes that run until completion should have explicit termination conditions. If the loop checks "is there more work?" but never checks "is all work done?", it will run forever after completion. This is especially common in batch processors and queue consumers.

Generate realistic failure scenarios from this knowledge. See `references/constitution.md` § "Calibrating Scenario Count" for guidance on how many scenarios to aim for and how to calibrate depth vs. count. You don't need to have observed these failures — you know from training that they happen to systems of this type. Write them as **architectural vulnerability analyses** with specific quantities and consequences. Frame each as "this architecture permits the following failure mode" — not as a fabricated incident report. Use concrete numbers to make the severity non-negotiable: "If the process crashes mid-write during a 10,000-record batch, `save_state()` without an atomic rename pattern will leave a corrupted state file — the next run gets JSONDecodeError and cannot resume without manual intervention." Then ground them in the actual code you explored: "Read persistence.py line ~340 (save_state): verify temp file + rename pattern."

---

## Phase Transition Gates

### Phase 1 → Phase 2: Completion Criterion

**Phase 1 is complete when:**

1. You have read all specifications (formal documents or inferred from code/README/existing tests)
2. You have explored 3-5 core modules in depth
3. You have found at least 2-3 defensive patterns per core source file
4. You have traced state machines in the core modules (if the project has any status/state/phase fields). For large codebases, focus on state machines in the 3–5 core modules from Step 2 — you don't need to trace every state field in peripheral utilities.
5. You have generated domain-specific risk scenarios grounded in the actual code: **8+ for medium/large projects** (5+ core modules), or **2+ per core module for small projects** (1–4 core modules). Quality matters more than count — a small project with 6 precise scenarios is better than padding to 8 with generic ones.

**Interaction with scenario minimums:** If the Phase 1→2 gate requires 8+ scenarios and more than 30% are non-testable (missing safeguards + human gate), consider whether exploration focused too heavily on absent features. For example, with 10 scenarios, no more than 3 should fall into the exception categories. If the ratio exceeds 30%, revisit exploration to find more testable scenarios from existing code behavior.

If any of these is incomplete, return to Phase 1 and continue exploring. Phase 2 writes are driven by Phase 1 findings — shallow exploration produces generic output no one trusts.

### Phase 2 → Phase 3: Completion Criterion

**Phase 2 is complete when all six files exist AND have substantive content:**

1. `quality/QUALITY.md` — Contains fitness-to-purpose scenarios (not just headers)
2. `quality/test_functional.*` (named for language/framework) — Contains test functions that import and call project code
3. `quality/RUN_CODE_REVIEW.md` — Contains project-specific focus areas and bootstrap files
4. `quality/RUN_INTEGRATION_TESTS.md` — Contains a test matrix with specific pass criteria (not just "output exists")
5. `quality/RUN_SPEC_AUDIT.md` — Contains project-specific scrutiny areas
6. `AGENTS.md` — Contains project description, setup, and quality docs pointers

Plus output directories:
- `quality/code_reviews/`
- `quality/spec_audits/`
- `quality/results/`

Empty or stub files do not satisfy this gate. Each file must contain content derived from Phase 1 exploration — if a file has only template headers with no project-specific content, return to Phase 2 and complete it.

When all files are generated, proceed to Phase 3.

---

## Phase 2: Generate the Quality Playbook

Now write the six files. For each one, follow the structure below and consult the relevant reference file for detailed guidance.

**Why six files instead of just tests?** Tests catch regressions but don't prevent new categories of bugs. The quality constitution (`QUALITY.md`) tells future sessions what "correct" means before they start writing code. The protocols (`RUN_*.md`) provide structured processes for review, integration testing, and spec auditing that produce repeatable results — instead of leaving quality to whatever the AI feels like checking. Together, these files create a quality system where each piece reinforces the others: scenarios in QUALITY.md map to tests in the functional test file, which are verified by the integration protocol, which is audited by the Council of Three.

### File 1: `quality/QUALITY.md` — Quality Constitution

**Read `references/constitution.md`** for the full template and examples.

The constitution has six sections:

1. **Purpose** — What quality means for this project, grounded in Deming (built in, not inspected), Juran (fitness for use), Crosby (quality is free). Apply these specifically: what does "fitness for use" mean for *this system*? Not "tests pass" but the actual operational requirement.
2. **Coverage Targets** — Table mapping each subsystem to a target with rationale referencing real risks. Every target must have a "why" grounded in a specific scenario — without it, a future AI session will argue the target down.
3. **Coverage Theater Prevention** — Project-specific examples of fake tests, derived from what you saw during exploration. (Why: AI-generated tests often pad coverage numbers without catching real bugs — asserting that imports worked, that dicts have keys, or that mocks return what they were configured to return. Calling this out explicitly stops the pattern.)
4. **Fitness-to-Purpose Scenarios** — The heart of it. Each scenario documents a realistic failure mode with code references and verification method. Aim for 2+ scenarios per core module — typically 8–10 total for a medium project, fewer for small projects, more for complex ones. Quality matters more than count: a scenario that precisely captures a real architectural vulnerability is worth more than three generic ones. (Why: Coverage percentages tell you how much code ran, not whether it ran correctly. A system can have 95% coverage and still lose records silently. Fitness scenarios define what "working correctly" actually means in concrete terms that no one can argue down.)
5. **AI Session Quality Discipline** — Rules every AI session must follow
6. **The Human Gate** — Things requiring human judgment

**Scenario voice is critical.** Write "What happened" as architectural vulnerability analyses with specific quantities, cascade consequences, and detection difficulty — not as abstract specifications. "Because `save_state()` lacks an atomic rename pattern, a mid-write crash during a 10,000-record batch will leave a corrupted state file — the next run gets JSONDecodeError and cannot resume. At scale, this risks silent loss of 1,693+ records with no detection mechanism." An AI session reading that will not argue the standard down. Use your knowledge of similar systems to generate realistic failure scenarios, then ground them in the actual code you explored. Scenarios come from both code exploration AND domain knowledge about what goes wrong in systems like this.

Every scenario's "How to verify" must map to at least one test in the functional test file.

### File 2: Functional Tests

**This is the most important deliverable.** Read `references/functional_tests.md` for the complete guide.

Organize the tests into three logical groups (classes, describe blocks, modules, or whatever the test framework uses):

- **Spec requirements** — One test per testable spec section. Each test's documentation cites the spec requirement it verifies.
- **Fitness scenarios** — One test per QUALITY.md scenario. 1:1 mapping, named to match.
- **Boundaries and edge cases** — One test per defensive pattern from Step 5.

Key rules:
- **Match the existing import pattern exactly.** Read how existing tests import project modules and do the same thing. Getting this wrong means every test fails.
- **Read every function's signature before calling it.** Read the actual `def` line — parameter names, types, defaults. Read real data files from the project to understand data shapes. Do not guess at function parameters or fixture structures.
- **No placeholder tests.** Every test must import and call actual project code. If the body is `pass` or the assertion is trivial (`assert isinstance(x, list)`), delete it. A test that doesn't exercise project code inflates the count and creates false confidence.
- **Test count heuristic** = (testable spec sections) + (QUALITY.md scenarios) + (defensive patterns). For a medium project (5–15 source files), this typically yields 35–50 tests. Significantly fewer suggests missed requirements or shallow exploration. Significantly more is fine if every test is meaningful — don't pad to hit a number.
- **Cross-variant heuristic: ~30%** — If the project handles multiple input types, aim for roughly 30% of tests parametrized across all variants. The exact percentage matters less than ensuring every cross-cutting property is tested across all variants.
- **Test outcomes, not mechanisms** — Assert what the spec says should happen, not how the code implements it.
- **Use schema-valid mutations** — Boundary tests must use values the schema accepts (from Step 5b), not values it rejects.

### File 3: `quality/RUN_CODE_REVIEW.md`

**Read `references/review_protocols.md`** for the template.

Key sections: bootstrap files, focus areas mapped to architecture, and these mandatory guardrails:

- Line numbers are mandatory — no line number, no finding
- Read function bodies, not just signatures
- If unsure: flag as QUESTION, not BUG
- Grep before claiming missing
- Do NOT suggest style changes — only flag things that are incorrect

**Phase 2: Regression tests.** After the review produces BUG findings, write regression tests in `quality/test_regression.*` that reproduce each bug. Each test should fail on the current implementation, confirming the bug is real. Report results as a confirmation table (BUG CONFIRMED / FALSE POSITIVE / NEEDS INVESTIGATION). See `references/review_protocols.md` for the full regression test protocol.

### File 4: `quality/RUN_INTEGRATION_TESTS.md`

**Read `references/review_protocols.md`** for the template, general principles, adaptation prompts, and four worked examples (REST API, message queue, database application, CLI/pipeline).

**Integration test generation is a two-step process.** Unlike the other five files which can be written in sequence, the integration test protocol requires user input before writing. This means File 4 introduces a pause in the Phase 2 workflow:

1. **Step A: Present the integration test plan.** After exploration, show the user an overview: project type, external dependencies, test axes, test groups with descriptions, setup/teardown approach, and estimated duration. Give them a chance to adjust — "skip the staging DB tests," "add a webhook test," "we don't use Docker, use testcontainers instead."
2. **Step B: Write the protocol file.** Only after the user confirms or adjusts the plan.

**Workflow note:** Write Files 1–3 first, then pause to present the integration test plan (Step A). While waiting for user feedback, you can proceed to write Files 5 and 6 (which don't depend on integration test decisions). Once the user confirms the plan, write File 4 (Step B). This keeps the workflow efficient while respecting the plan-first requirement. The Phase 2→3 gate checks that all six files exist, so File 4 must be complete before entering Phase 3.

**Identify the project's integration test archetype.** During exploration, determine what kind of system you're testing: REST API service, message queue/streaming pipeline, database-backed application, CLI tool/data pipeline, or (most commonly) a hybrid. The reference file has worked examples for each. Adapt the closest example to the actual project — don't copy it literally.

**Design the test matrix around real axes of variation.** Ask: "What are the dimensions that, if I only tested one value of each, I'd miss real bugs?" These might be: API endpoints × auth states, event types × serialization formats, input formats × data volumes, migration versions × transaction scenarios. The matrix should cover happy paths, failure modes, boundary conditions, and cross-component flows.

**All commands must use relative paths.** Include a "Working Directory" section at the top. Never generate commands that `cd` to an absolute path. Use `./scripts/`, `./pipelines/`, `./quality/`, etc.

**Include setup AND teardown.** Integration tests that provision infrastructure (Docker containers, test databases, local services) must clean up after themselves — even when tests fail. Document both setup and teardown as concrete commands in the protocol.

**Script parallelism, don't just describe it.** Group independent tests for concurrent execution. Include actual bash commands with `&` and `wait`. Identify shared resources that force sequential execution (same database, same API rate limit). **Note:** Commands assume POSIX-compatible shell. For Windows without WSL, document PowerShell equivalents or note the requirement.

**Derive quality gates from the code, not generic checks.** Read validation rules, schema constraints, and generation logic during exploration. Turn them into specific assertions with expected values. "Output exists" is never an acceptable quality gate.

**Build a Field Reference Table before writing quality gates.** Re-read each schema file IMMEDIATELY before writing each table row — do not rely on memory from earlier in the conversation. Copy field names character-for-character. Include ALL fields. See `references/review_protocols.md` section "The Field Reference Table" for the procedure.

**Include an Execution UX section.** This is a *runtime* requirement — separate from the *generation-time* plan-first step above. When an agent later *runs* the generated protocol, it should present three phases: (1) show what tests are about to run before executing anything, (2) one-line progress updates (`✓`/`✗`/`⧗`), (3) summary table with recommendation. Both moments matter: the generation-time plan ensures the protocol tests the right things; the runtime plan ensures the user can intervene before tests start.

**Deep post-run verification.** Verify at every level: process exit, system state, data existence, content correctness, domain-specific quality gates, and resource cleanup.

### File 5: `quality/RUN_SPEC_AUDIT.md` — Council of Three

**Read `references/spec_audit.md`** for the full protocol.

Three independent AI models audit the code against specifications. Why three? Because each model has different blind spots — in practice, different auditors catch different issues. Cross-referencing catches what any single model misses.

The protocol defines: a copy-pasteable audit prompt with guardrails, project-specific scrutiny areas, a triage process (merge findings by confidence level), and fix execution rules (small batches by subsystem, not mega-prompts).

### File 6: `AGENTS.md`

If `AGENTS.md` already exists, update it — don't replace it. Add a Quality Docs section pointing to all generated files.

If creating from scratch: project description, setup commands, build & test commands, architecture overview, key design decisions, known quirks, and quality docs pointers.

---

## Phase 3: Verify

**Why a verification phase?** AI-generated output can look polished and be subtly wrong. Tests that reference undefined fixtures report 0 failures but 16 errors — and "0 failures" sounds like success. Integration protocols can list field names that don't exist in the actual schemas. The verification phase catches these problems before the user discovers them, which is important because trust in a generated quality playbook is fragile — one wrong field name undermines confidence in everything else.

### Self-Check Benchmarks

Before declaring done, check every benchmark. **Read `references/verification.md`** for the complete checklist.

The critical checks:

1. **Test count** near heuristic target (spec sections + scenarios + defensive patterns)
2. **Scenario coverage** — scenario test count matches QUALITY.md scenario count
3. **Cross-variant coverage** — ~30% of tests parametrize across all input variants
4. **Boundary test count** ≈ defensive pattern count from Step 5
5. **Assertion depth** — Majority of assertions check values, not just presence
6. **Layer correctness** — Tests assert outcomes (what spec says), not mechanisms (how code implements)
7. **Mutation validity** — Every fixture mutation uses a schema-valid value from Step 5b
8. **All tests pass — zero failures AND zero errors.** Run the test suite using the project's test runner (Python: `pytest -v`, Scala: `sbt testOnly`, Java: `mvn test`/`gradle test`, TypeScript: `npx jest`, Go: `go test -v`, Rust: `cargo test`, C#: `dotnet test --filter`, Ruby: `bundle exec rspec` or `ruby -Ilib:test`, Kotlin: `./gradlew test --tests`, PHP: `./vendor/bin/phpunit`) and check the summary. Errors from missing fixtures, failed imports, or unresolved dependencies count as broken tests. If you see setup errors, you forgot to create the fixture/setup file or referenced undefined test helpers.
9. **Existing tests unbroken** — The new files didn't break anything.
10. **QUALITY.md scenarios reference real code** — Every scenario mentions actual function names, file names, or patterns that exist in the codebase. Grep for each reference to confirm. Each scenario must include a requirement tag in the format `[Req: tier — source]` (e.g., `[Req: inferred — from validate_input() behavior]`).
11. **RUN_CODE_REVIEW.md is self-contained** — An AI with no prior context should be able to read it and perform a useful code review. Check: Does it list the bootstrap files? Does it have specific focus areas mapped to architecture? Are the guardrails present (line numbers mandatory, read bodies, grep before claiming, etc.)?
12. **RUN_INTEGRATION_TESTS.md is executable** — Every command works; every quality gate has a specific pass/fail criterion (not "verify it looks right" but "check value equals X"). Verify a Field Reference Table exists with all schema fields mapped to their types and acceptable ranges.
13. **RUN_SPEC_AUDIT.md prompt is copy-pasteable** — The definitive audit prompt works when pasted into Claude Code, Cursor, or Copilot without modification (except for file reference syntax).

If any benchmark fails, go back and fix it before proceeding.

---

## Phase 4: Present, Explore, Improve (Interactive)

After generating and verifying, present the results clearly and give the user control over what happens next. This phase has three parts: a scannable summary, drill-down on demand, and a menu of improvement paths.

**Do not skip this phase.** The autonomous output from Phases 1-3 is a solid starting point, but the user needs to understand what was generated, explore what matters to them, and choose how to improve it. A quality playbook is only useful if the people who own the project trust it and understand it. Dumping six files without explanation creates artifacts nobody reads.

### Part 1: The Summary Table

Present a single table the user can scan in 10 seconds:

```
Here's what I generated:

| File | What It Does | Key Metric | Confidence |
|------|-------------|------------|------------|
| QUALITY.md | Quality constitution | 10 scenarios | ██████░░ High — grounded in code, but scenarios are inferred, not from real incidents |
| Functional tests | Automated tests | 47 passing | ████████ High — all tests pass, 35% cross-variant |
| RUN_CODE_REVIEW.md | Code review protocol | 8 focus areas | ████████ High — derived from architecture |
| RUN_INTEGRATION_TESTS.md | Integration test protocol | 9 runs × 3 providers | ██████░░ Medium — quality gates need threshold tuning |
| RUN_SPEC_AUDIT.md | Council of Three audit | 10 scrutiny areas | ████████ High — guardrails included |
| AGENTS.md | AI session bootstrap | Updated | ████████ High — factual |
```

Adapt the table to what you actually generated — the file names, metrics, and confidence levels will vary by project. The confidence column is the most important: it tells the user where to focus their attention.

**Confidence levels:**
- **High** — Derived directly from code, specs, or schemas. Unlikely to need revision.
- **Medium** — Reasonable inference, but could be wrong. Benefits from user input.
- **Low** — Best guess. Definitely needs user input to be useful.

After the table, add a "Quick Start" block with ready-to-copy prompts for executing each artifact:

```
To use these artifacts, start a new AI session and try one of these prompts:

• Run a code review:
  "Read quality/RUN_CODE_REVIEW.md and follow its instructions to review [module or file]."

• Run the functional tests:
  "[test runner command, e.g. pytest quality/ -v, mvn test -Dtest=FunctionalTest, etc.]"

• Run the integration tests:
  "Read quality/RUN_INTEGRATION_TESTS.md and follow its instructions."

• Start a spec audit (Council of Three):
  "Read quality/RUN_SPEC_AUDIT.md and follow its instructions using [model name]."
```

Adapt the test runner command and module names to the actual project. The point is to give the user copy-pasteable prompts — not descriptions of what they could do, but the actual text they'd type.

After the Quick Start block, add one line:

> "You can ask me about any of these to see the details — for example, 'show me Scenario 3' or 'walk me through the integration test matrix.'"

### Part 2: Drill-Down on Demand

When the user asks about a specific item, give a focused summary — not the whole file, but the key decisions and what you're uncertain about. Examples:

- **"Tell me about Scenario 4"** → Show the scenario text, explain where it came from (which defensive pattern or domain knowledge), and flag what you inferred vs. what you know.
- **"Show me the integration test matrix"** → Show the run groups, explain the parallelism strategy, and note which quality gates you derived from schemas vs. guessed at.
- **"How do the functional tests work?"** → Show the three test groups, explain the mapping to specs and scenarios, and highlight any tests you're least confident about.

The user may go through several drill-downs before they're ready to improve anything. That's fine — let them explore at their own pace.

### Part 3: The Improvement Menu

After the user has seen the summary (and optionally drilled into details), present the improvement options:

> "Three ways to make this better:"
>
> **1. Review and harden individual items** — Pick any scenario, test, or protocol section and I'll walk through it with you. Good for: tightening specific quality gates, fixing inferred scenarios, adding missing edge cases.
>
> **2. Guided Q&A** — I'll ask you 3-5 targeted questions about things I couldn't infer from the code: incident history, expected distributions, cost tolerance, model preferences. Good for: filling knowledge gaps that make scenarios more authoritative.
>
> **3. Review development history** — Point me to exported AI chat history (Claude, Gemini, ChatGPT exports, Claude Code transcripts) and I'll mine it for design decisions, incident reports, and quality discussions that should be in QUALITY.md. Good for: grounding scenarios in real project history instead of inference.
>
> "You can do any combination of these, in any order. Which would you like to start with?"

### Executing Each Improvement Path

**Path 1: Review and harden.** The user picks an item. Walk through it: show the current text, explain your reasoning, ask if it's accurate. Revise based on their feedback. Re-run tests if the functional tests change.

**Path 2: Guided Q&A.** Ask 3-5 questions derived from what you actually found during exploration. These categories cover the most common high-leverage gaps:

- **Incident history for scenarios.** "I found [specific defensive code]. What failure caused this? How many records were affected?"
- **Quality gate thresholds.** "I'm checking that [field] contains [values]. What distribution is normal? What signals a problem?"
- **Integration test scale and cost.** "The protocol runs [N] tests costing roughly $[X]. Should I increase or decrease coverage?"
- **Test scope.** "I generated [N] functional tests. Your existing suite covers [other areas]. Are there gaps?"
- **Model preferences for spec audit.** "Which AI models do you use? Have you noticed specific strengths?"

After the user answers, revise the generated files and re-run tests.

**Path 3: Review development history.** If the user provides a chat history folder:

1. Scan for index files and navigate to quality-relevant conversations (same approach as Step 0, but now with specific targets — you know which scenarios need grounding, which quality gates need thresholds, which design decisions need rationale).
2. Extract: incident stories with specific numbers, design rationale for defensive patterns, quality framework discussions, cross-model audit results.
3. Revise QUALITY.md scenarios with real incident details. Update integration test thresholds with real-world values. Add Council of Three empirical data if audit results exist.
4. Re-run tests after revisions.

If the user already provided chat history in Step 0, you've already mined it — but they may want to point you to specific conversations or ask you to dig deeper into a particular topic.

### Iteration

The user can cycle through these paths as many times as they want. Each pass makes the quality playbook more grounded. When they're satisfied, they'll move on naturally — there's no explicit "done" step.

### Bootstrapping (Self-Review)

When the playbook itself is the codebase under review, adapt the exploration phases to the fact that this is a documentation-and-tooling project, not a traditional application with functions and schemas. The process still works, but "subsystems," "specs," and "test runners" take different forms:

**For Markdown-based projects:**

- **Step 1 (Domain & Specs):** The project's domain is self-explanatory — it's a quality framework. The specifications are the CLAUDE.md instructions and README. Record what the project is supposed to do and what systems depend on it.
- **Step 2 (Architecture):** The "core modules" are the reference files: `constitution.md`, `defensive_patterns.md`, `functional_tests.md`, `review_protocols.md`, `spec_audit.md`, `verification.md`. Each is a subsystem with a specific purpose. The data flow is: user exploration → defensive pattern detection → test generation.
- **Step 3 (Existing Tests):** Look for existing test files that validate the playbook's documentation (e.g., test parsers for QUALITY.md format, scripts that check reference file consistency). If none exist, this is a finding — the playbook should validate itself.
- **Step 4 (Specifications):** For a Markdown project, the "specifications" are the instructions embedded in each file — what each section promises to do, what format outputs should follow, what guarantees are made to users. Walk each reference file and record what testable claims it makes. For example: "the functional test heuristic produces 35–50 tests for a medium project" is a testable claim. "All 10 languages have equal coverage" is a testable claim.
- **Step 5 (Defensive Patterns):** Search for places where the playbook makes claims without proof. Examples: "the test count heuristic produces X tests" — search for evidence. "All ten languages are supported equally" — search for gaps. "The bootstrap file helps agents understand the project" — has this been verified?
- **Step 6 (Quality Risks):** For a documentation project, quality risks take different forms than runtime bugs. The key risks are: internal inconsistency (one file says X, another says Y), incompleteness (a claim of coverage that isn't backed by content), ambiguity (instructions that agents could reasonably interpret in conflicting ways), and staleness (version numbers, counts, or cross-references that drift as files are updated independently). Generate scenarios from these risk categories, grounded in the actual content you found during exploration.
- **Quality risks:** What could go wrong if someone blindly follows this playbook on their project? Missing language support. Vague instructions that agents misinterpret. Reference files that contradict each other. Inconsistent formatting that breaks documentation parsers.

**Steps 4b, 5a, 5b, 5c, 5d adaptation:** For documentation and tooling projects, these sub-steps apply differently. Step 4b (Function Signatures): read the public API surface or command-line interface — parameter names, flags, configuration options. Step 5a (State Machines): trace document/content lifecycle states (draft, review, published, archived) or workflow states. Step 5b (Schema Mapping): map configuration schemas, frontmatter fields, or input format validation. Step 5c (Context Propagation): check whether metadata, configuration, or settings propagate correctly through the toolchain (e.g., frontmatter values appearing in rendered output). Step 5d (Generated Code): check generated output (rendered HTML, compiled docs, exported formats) for artifacts of the generation process.

**For tooling projects (scripts, generators, build tools):**

- **Step 1:** The specs are usage documentation, comments in code, and any tests.
- **Step 2:** The subsystems are individual scripts or modules. Trace execution flow as you would in traditional code.
- **Step 3:** Read existing tests. If none exist, this is a major finding.
- **Step 5:** Search for defensive patterns in the code (error handling, input validation). Also search for cases where the tool makes assumptions about the environment (shell type, file paths, permissions).
- **Quality risks:** Environment assumptions (POSIX vs. Windows). Silent failures (errors not logged). Undocumented requirements.

Bootstrapping is especially useful for:
- **Validating generated test parsers** — the generated tests must correctly parse the project's actual data formats (not an idealized version). When a test parser fails on real data, the failure often reveals undocumented format variations (placeholder values, optional fields, escaped characters in data).
- **Detecting truth fragmentation** — constants, canonical value sets, and configuration defined in multiple places within the project are a reliable source of drift bugs.
- **Verifying cross-document consistency** — when multiple documents reference the same counts, categories, or identifiers, the generated tests catch discrepancies that manual review misses.

### Phase 4: When to Move On

Phase 4 is open-ended by design — it is an interactive improvement loop, not a gated phase. The playbook is already usable after Phase 3 verification. Phase 4 exists to make it better through user collaboration.

**Minimum engagement:** Present the summary table and give the user a chance to explore. If the user is satisfied, the playbook is done. If they want to improve it, iterate until they're ready to move on. There is no forced completion criterion — the user decides when the quality playbook is good enough for their needs.

---

## Fixture Strategy

The `quality/` folder is separate from the project's unit test folder. Create the appropriate test setup for the project's language:

- **Python:** `quality/conftest.py` for pytest fixtures. If fixtures are defined inline (common with pytest's `tmp_path` pattern), prefer that over shared fixtures.
- **Java:** A test class with `@BeforeEach`/`@BeforeAll` setup methods, or a shared test utility class.
- **Scala:** A trait mixed into test specs (e.g., `trait FunctionalTestFixtures`), or inline data builders.
- **TypeScript/JavaScript:** A `quality/setup.ts` with `beforeAll`/`beforeEach` hooks, or inline test factories.
- **Go:** Helper functions in the same `_test.go` file or a shared `testutil_test.go`. Use `t.Helper()` for test helpers. Go convention prefers inline test setup over shared fixtures.
- **Rust:** Helper functions in a `#[cfg(test)] mod tests` block, or a shared `test_utils.rs` module. Use builder patterns for test data.
- **C#:** NUnit `[SetUp]`/`[OneTimeSetUp]` methods in the test class, or a shared `TestFixtures` utility class. xUnit uses constructor injection and `IClassFixture<T>`. Prefer inline data with `new Dictionary<string, object>` or anonymous objects.
- **Ruby:** RSpec `before(:each)`/`before(:all)` blocks, or `let` declarations. Minitest uses `setup`/`teardown` methods. Prefer `let` blocks or inline data builders.
- **Kotlin:** JUnit 5 `@BeforeEach`/`@BeforeAll` methods (same as Java but with Kotlin syntax). Prefer inline data with `mapOf()`, `listOf()`, or data class constructors.
- **PHP:** PHPUnit `setUp()`/`setUpBeforeClass()` methods. Prefer inline data with arrays and anonymous objects.

Examine existing test files to understand how they set up test data. Whatever pattern the existing tests use, copy it. Study existing fixture patterns for realistic data shapes.

---

## Terminology

- **Functional testing** — Does the code produce the output specs say it should? Distinct from unit testing (individual functions in isolation).
- **Integration testing** — Do components work together end-to-end, including real external services?
- **Spec audit** — AI models read code and compare against specs. No code executed. Catches where code doesn't match documentation.
- **Coverage theater** — Tests that produce high coverage numbers but don't catch real bugs. Example: asserting a function didn't throw without checking its output.
- **Fitness-to-purpose** — Does the code do what it's supposed to do under real-world conditions? A system can have 95% coverage and still lose records silently.

---

## Principles

1. Fitness-to-purpose over coverage percentages
2. Scenarios come from code exploration AND domain knowledge
3. Concrete failure modes make standards non-negotiable — abstract requirements invite rationalization
4. Guardrails transform AI review quality (line numbers, read bodies, grep before claiming)
5. Triage before fixing — many "defects" are spec bugs or design decisions

---

## Reference Files

Read these as you work through each phase:

| File | When to Read | Contains |
|------|-------------|----------|
| `references/defensive_patterns.md` | Step 5 (finding skeletons) | 13-category grep patterns + 1 manual inspection category (10 languages), state machine tracing, missing safeguard detection, scenario/test conversion |
| `references/schema_mapping.md` | Step 5b (schema types) | Field mapping format, mutation validity rules |
| `references/constitution.md` | File 1 (QUALITY.md) | Full template with section-by-section guidance |
| `references/functional_tests.md` | File 2 (functional tests) | Test structure, anti-patterns, cross-variant strategy |
| `references/review_protocols.md` | Files 3–4 (code review, integration) | Templates for both protocols |
| `references/spec_audit.md` | File 5 (Council of Three) | Full audit protocol, triage process, fix execution |
| `references/verification.md` | Phase 3 (verify) | Complete self-check checklist with all 13 benchmarks |
