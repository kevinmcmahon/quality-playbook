# Quality Playbook

An open-source skill that generates a complete quality system for any codebase. Give it a repository and it produces six artifacts: a quality constitution, functional tests, a code review protocol, an integration test protocol, a multi-model spec audit, and a bootstrap context file for AI agents. It works with any language and any project type.

**Version:** 1.2.15 | **Author:** Andrew Stellman | **License:** Apache 2.0

## What it does

The playbook explores your codebase — reading source, specs, tests, config, and commit history — then generates artifacts grounded in what it actually finds, not generic templates. The core insight is that AI code review quality is bottlenecked by requirements: a reviewer that doesn't know what the code is *supposed* to do can only find structural issues. The playbook's main job is deriving requirements from every available source, then using those requirements to drive review.

### Generated artifacts

The playbook generates these files in a `quality/` directory:

| Artifact | Purpose |
|----------|---------|
| `QUALITY.md` | Quality constitution — coverage targets, fitness-to-purpose scenarios, theater prevention rules |
| `test_functional.*` | Automated functional tests in the project's native language and framework |
| `RUN_CODE_REVIEW.md` | Three-pass code review protocol (structural, requirement verification, cross-requirement consistency) |
| `RUN_INTEGRATION_TESTS.md` | Integration test protocol for end-to-end validation across all variants |
| `RUN_SPEC_AUDIT.md` | Council of Three spec audit — three independent models catch what any one alone misses |
| `AGENTS.md` | Bootstrap context file for any AI session working on the project |

Running these protocols produces output in `quality/code_reviews/`, `quality/spec_audits/`, and `quality/results/`.

### Fitness-to-purpose over coverage

The playbook prioritizes whether code works correctly under real-world conditions over how much of it ran during tests. A system can have 95% test coverage and still lose records silently. Fitness-to-purpose scenarios are natural-language assertions an LLM can evaluate against code — things like "a map with duplicate keys where the first value is null must still throw an exception."

## Installation

### Claude Code / Copilot

Copy the skill to your project:

```bash
mkdir -p .skills/skills/quality-playbook
cp SKILL.md .skills/skills/quality-playbook/SKILL.md
```

Or for GitHub Copilot:

```bash
mkdir -p .github/skills
cp SKILL.md .github/skills/SKILL.md
```

### Running the pipeline

The playbook runs as a 9-step pipeline. Each step can be invoked through any LLM coding assistant (Claude Code, GitHub Copilot CLI, Cursor, etc.):

1. Generate the quality constitution, requirements, and protocols from codebase exploration
2. Run the three-pass code review against HEAD
3. Run functional tests
4. Run integration tests
5. Run spec audit (auditor 1)
6. Run spec audit (auditor 2)
7. Run spec audit (auditor 3)
8. Triage and summarize all findings
9. Run structural-only control (no playbook — baseline comparison)

See `repos/gson-1.2.15/control_prompts/` for example prompts for each step.

## Real bug found: Gson duplicate-key bypass

During development, the playbook found a [real, previously unreported bug](https://github.com/google/gson/pull/2999) in Google's Gson library (23K+ GitHub stars). The documentation-enriched pipeline derived null-handling requirements from Gson's GitHub issues, then used those requirements to ground a code review. The review flagged that `MapTypeAdapterFactory`'s duplicate-key detection fails when the first value is `null`:

```java
// Bug: Map.put() returns null when previous value was null,
// so this check misses duplicates where the first value is null
V replaced = map.put(key, value);
if (replaced != null) { ... }  // fails for {"a":null,"a":1}
```

This bug had existed since the duplicate-key check was introduced and was invisible to every existing test because they all used non-null first values. It was only detectable by knowing, from community documentation, that Gson's null handling has edge cases — exactly the kind of intent violation the playbook is designed to surface.

## How it works

The playbook's value comes from requirement derivation. The 9-step pipeline:

1. **Explores the codebase** — reads source files, configuration, specifications, test suites, and commit history to understand what the code does and what it's supposed to do
2. **Derives requirements** — extracts behavioral contracts from code, documentation, and (when available) community sources like GitHub issues and user guides
3. **Generates a quality constitution** — fitness-to-purpose scenarios that can be evaluated by an LLM, plus coverage targets and theater prevention rules
4. **Runs a three-pass code review** — structural review (does the code have issues?), requirement verification (does the code satisfy the requirements?), and cross-requirement consistency (do the requirements contradict each other?)
5. **Runs a multi-model spec audit** — three independent models audit the code against the specification, catching defects that any single model misses
6. **Triages findings** — merges results across all passes, deduplicates, and assigns confidence levels

### Why community documentation matters

The playbook's documentation enrichment experiment (see `repos/gson-1.2.15/EXPERIMENT.md`) showed that adding community documentation — GitHub issues, user guides, Javadoc, tutorials — to the pipeline produces measurably better results:

| Metric | Baseline (code only) | Enriched (+ community docs) |
|--------|---------------------|----------------------------|
| Requirements derived | 43 | 48 (+5) |
| Fitness-to-purpose scenarios | 10 | 12 (+2) |
| Spec audit findings | 5 | 9 (+80%) |
| Cross-auditor redundancy | ~50% | 0% |

All five new requirements from community docs targeted behavioral contracts invisible in source code. Three led directly to the confirmed Gson bug.

## The benchmark

The playbook is validated against the **Quality Playbook Benchmark (QPB)**: 2,564 real defects from 50 open-source repositories across 14 programming languages. This is mutation testing applied one level up — instead of injecting synthetic faults into code, we use real historical bugs as ground truth. Each defect is tied to a single fix commit, so checking out the parent commit gives you the exact code with the exact bug.

### Quick start (benchmark)

```bash
# Example: CURL-01, use-after-free in transfer URL pointer
cd repos/curl
git checkout 28fbf4a8          # pre-fix commit
# Run your code review against lib/transfer.c
# Then compare your findings to the fix:
git diff 28fbf4a8..86b39c2     # shows the actual fix
```

### Dataset summary

| Dimension | Count |
|-----------|-------|
| Total defects | 2,564 |
| Repositories | 50 |
| Languages | 14 (Go, Python, TypeScript, Java, C, C#, Rust, Ruby, PHP, Kotlin, Scala, JavaScript, Swift, Elixir) |
| Defect categories | 14 (error handling, validation gap, configuration error, type safety, state machine gap, concurrency, serialization, API contract violation, protocol violation, null safety, silent failure, security, SQL error, missing boundary check) |

### Key finding from the benchmark

Approximately 65% of real defects are detectable by structural code review alone. The remaining 35% are intent violations — bugs that can only be found if you know what the code is supposed to do. The playbook's value is in closing that gap through requirement derivation.

## Directory structure

```
QPB/
├── README.md                   # This file
├── dataset/                    # The benchmark dataset
│   ├── DEFECT_LIBRARY.md       # Master index (2,564 defects)
│   ├── METHODOLOGY.md          # How the dataset was built
│   └── defects/                # Per-repo detailed descriptions
├── repos/                      # Cloned repositories (gitignored)
│   └── gson-1.2.15/            # Gson documentation enrichment experiment
│       ├── EXPERIMENT.md        # Full experiment documentation
│       ├── quality/             # Enriched pipeline output
│       ├── quality_baseline/    # Baseline pipeline output
│       ├── retrieved_documentation/  # 24-file community docs corpus
│       └── control_prompts/     # 9-step pipeline prompts
├── benchmarks/                 # Cross-repo validation experiments
├── tooling/                    # Scripts for building the dataset
└── .gitignore
```

## Context

This project supports an O'Reilly Radar article series on AI-assisted code quality by Andrew Stellman. The playbook was built using AI-driven development with Octobatch, an open-source Python batch LLM orchestrator. See the [AI-Driven Development](https://github.com/andrewstellman/ai-driven-development) workspace for the full development history.

## License

The playbook skill, benchmark dataset metadata, and tooling are original work under Apache 2.0. The cloned repositories in `repos/` retain their original licenses.
