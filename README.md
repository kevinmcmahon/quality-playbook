# Quality Playbook

Point an AI coding tool at any codebase. Get a complete quality engineering infrastructure: requirements derived from the actual intent of the code, functional tests traced to those requirements, a three-pass code review protocol, and a multi-model spec audit that catches bugs no single reviewer can find alone.

**Version:** 1.3.4 | **Author:** [Andrew Stellman](https://github.com/andrewstellman) | **License:** Apache 2.0

## The problem

Most AI code review can only find structural issues: null dereferences, resource leaks, race conditions. That catches about 65% of real defects. The other 35% are intent violations -- bugs that can only be found if you know what the code is *supposed* to do. A function that silently returns null instead of throwing, a duplicate-key check that passes when the first value is null, a sanitization step that runs after the branch decision it was supposed to guard. These bugs look correct to any reviewer that doesn't know the spec.

The playbook closes that gap. It reads your codebase, derives behavioral requirements from every source it can find (code, docs, specs, comments, defensive patterns, community documentation), and uses those requirements to drive review. The result is a quality system grounded in intent, not just structure.

## Quick start

The playbook is a skill for AI coding tools. Copy it into your project and ask the AI to run it.

**GitHub Copilot:**
```bash
mkdir -p .github/skills/references
cp playbook/SKILL.md .github/skills/SKILL.md
cp playbook/references/* .github/skills/references/
```

**Claude Code:**
```bash
mkdir -p .claude/skills/quality-playbook/references
cp playbook/SKILL.md .claude/skills/quality-playbook/SKILL.md
cp playbook/references/* .claude/skills/quality-playbook/references/
```

Then tell your AI tool: *"Read the quality playbook skill and generate a complete quality system for this project."*

The playbook runs in four phases: explore the codebase, generate quality artifacts, run a three-pass code review, and execute a multi-model spec audit. It takes 30-60 minutes depending on project size, and it works with any language.

## What it produces

The playbook generates these files in a `quality/` directory:

| Artifact | What it does |
|----------|-------------|
| `REQUIREMENTS.md` | Behavioral requirements derived from code, docs, and community sources via a five-phase pipeline. This is the foundation -- without requirements, review is limited to structural bugs. |
| `QUALITY.md` | Quality constitution defining what "correct" means for this specific project, with fitness-to-purpose scenarios and coverage theater prevention. |
| `test_functional.*` | Functional tests in the project's native language, traced to requirements rather than generated from source code. |
| `RUN_CODE_REVIEW.md` | Three-pass protocol: structural review, requirement verification, cross-requirement consistency. Each pass finds bugs the others can't. |
| `RUN_SPEC_AUDIT.md` | Council of Three: three independent AI models audit the code against requirements. Different models have different blind spots, and the triage uses confidence weighting, not majority vote. |
| `RUN_INTEGRATION_TESTS.md` | End-to-end test protocol that a different AI session can pick up and execute cold. |
| `AGENTS.md` | Bootstrap file so every future AI session inherits the full quality infrastructure. |

## How it works

The playbook's value comes from requirement derivation. AI code reviewers are bottlenecked by the same thing human reviewers are: if you don't know what the code is *supposed* to do, you can only find structural issues. The playbook's main job is figuring out intent, then using that intent to drive every downstream artifact.

**Phase 1: Explore.** The AI reads source files, tests, config, specs, and commit history. If you provide community documentation (GitHub issues, user guides, API docs, forum discussions), it reads those too. The goal is to understand not just what the code does, but what it's supposed to do.

**Phase 2: Generate.** A five-phase pipeline extracts behavioral contracts from the codebase, derives testable requirements, verifies coverage, checks completeness, and adds a narrative layer. The pipeline also generates functional tests, review protocols, and the quality constitution.

**Phase 3: Review.** A three-pass code review runs against HEAD: structural review with anti-hallucination guardrails, requirement verification checking each requirement against the code, and cross-requirement consistency checking whether requirements contradict each other. About 65% of findings come from Pass 1, 35% from Passes 2 and 3.

**Phase 4: Audit.** Three independent AI models audit the code against the requirements. The triage process uses verification probes -- targeted checks that ask "is this actually true?" -- rather than dismissing single-model findings. The most valuable findings are often the ones only one model catches.

### Why documentation matters

Adding community documentation to the pipeline produces measurably better results. In a controlled experiment across multiple repositories, documentation-enriched runs found more bugs, different bugs, and higher-confidence bugs than code-only baselines. The documentation gives auditors spec language to check against, turning "this code looks odd" into "this code contradicts the documented behavior."

## The benchmark

The playbook is validated against the **Quality Playbook Benchmark (QPB)**: 2,564 real defects from 50 open-source repositories across 14 programming languages. Instead of injecting synthetic faults, we use real historical bugs tied to single fix commits as ground truth. Checking out the parent commit gives you the exact code with the exact bug, so you can measure whether a review protocol would have caught it.

The key finding: approximately 65% of real defects are detectable by structural code review alone. The remaining 35% are intent violations that require knowing what the code is supposed to do. The playbook's value is in closing that gap.

See `dataset/METHODOLOGY.md` for details on how the benchmark was built, and `dataset/DEFECT_LIBRARY.md` for the full index.

## Project structure

```
QPB/
├── playbook/               # The skill itself
│   ├── SKILL.md            # Main skill file
│   ├── LICENSE.txt         # Apache 2.0
│   └── references/         # Protocol and pipeline reference docs
├── dataset/                # QPB benchmark (2,564 defects, 50 repos, 14 languages)
│   ├── DEFECT_LIBRARY.md   # Master defect index
│   ├── METHODOLOGY.md      # How the dataset was built
│   └── defects/            # Per-repo descriptions
├── repos/                  # Cloned test repositories (gitignored)
├── benchmarks/             # Cross-repo validation experiments
└── tooling/                # Dataset build scripts
```

## Context

This project supports an [O'Reilly Radar article series](https://oreillyradar.substack.com/p/the-accidental-orchestrator) on AI-driven development and agentic engineering by Andrew Stellman. The playbook was built using AI-driven development with [Octobatch](https://github.com/andrewstellman/octobatch), an open-source Python batch LLM orchestrator.

## License

The playbook skill, benchmark dataset metadata, and tooling are original work under Apache 2.0. Cloned repositories in `repos/` retain their original licenses.
