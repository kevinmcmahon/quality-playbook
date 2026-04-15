# Quality Playbook

Point an AI coding tool at any codebase. Get a complete quality engineering infrastructure: requirements derived from the actual intent of the code, functional tests traced to those requirements, a three-pass code review protocol, and a multi-model spec audit that catches bugs no single reviewer can find alone.

**Version:** 1.3.33 | **Author:** [Andrew Stellman](https://github.com/andrewstellman) | **License:** Apache 2.0

## Need help? Just ask your AI

You don't need to read the documentation to use the Quality Playbook — your AI coding tool can read it for you. The `ai_context/TOOLKIT.md` file explains everything about the playbook in a format designed for AI assistants to read and answer questions about.

Open it in any AI tool — Claude Code, Cursor, GitHub Copilot, ChatGPT, Gemini, whatever you use — and tell it:

> "Read TOOLKIT.md. Now you're an expert in the Quality Playbook."

<a href="https://chatgpt.com/share/69dee323-1f34-832f-aa98-06e606aff1d0"><img src="images/chatgpt-toolkit.png" alt="ChatGPT with TOOLKIT.md attached" width="1000"></a>

Then ask it anything you want. How do I set this up? What does Phase 3 actually do? How does it find bugs that structural code review misses? What's the difference between gap and adversarial iteration? Why did my run only find one bug? Ask as many questions as you want — the toolkit has detailed explanations of every technique, every phase, and every iteration strategy. Your AI assistant will walk you through setup, running, interpreting results, and improving your next run.

[Here's what that conversation looks like in ChatGPT](https://chatgpt.com/share/69dee323-1f34-832f-aa98-06e606aff1d0) — it works just as well in Claude, Copilot, Gemini, or any other AI coding tool.

## Reproduce the benchmark: Linux virtio bug discovery

These commands clone the Linux kernel's virtio subsystem, install the playbook skill, and run a single GitHub Copilot prompt that independently discovers a confirmed kernel bug — a missing `VIRTIO_F_RING_RESET` case label in `vring_transport_features()` that silently drops queue-reset support on MMIO and vDPA transports.

The entire run takes about 17 minutes with GPT-5.4 and costs one Copilot Premium request. No seeds, no prior run data, no human guidance — the model reads the skill, explores the code, derives requirements, and finds the bug on its own.

**Prerequisites:** [GitHub Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli) with a model that supports `--yolo` mode (GPT-5.4 or later).

```bash
# 1. Clone the playbook skill
git clone https://github.com/andrewstellman/quality-playbook.git
SKILL_DIR="$(pwd)/quality-playbook"

# 2. Shallow-clone the Linux kernel virtio subsystem (66 files, ~1 MB)
git clone --filter=blob:none --no-checkout --sparse \
  https://github.com/torvalds/linux.git virtio-benchmark
cd virtio-benchmark
git sparse-checkout set drivers/virtio include/linux include/uapi/linux
git checkout bfe62a454542cfad3379f6ef5680b125f41e20f4

# 3. Strip to just the virtio files
mkdir -p ../virtio-clean/drivers ../virtio-clean/include/linux ../virtio-clean/include/uapi/linux
cp -a drivers/virtio ../virtio-clean/drivers/
cp include/linux/virtio*.h ../virtio-clean/include/linux/
cp include/uapi/linux/virtio*.h ../virtio-clean/include/uapi/linux/
cd .. && rm -rf virtio-benchmark && cd virtio-clean

# 4. Install the skill
mkdir -p .github/skills/references
cp "$SKILL_DIR/SKILL.md" .github/skills/SKILL.md
cp "$SKILL_DIR/LICENSE.txt" .github/skills/LICENSE.txt
cp "$SKILL_DIR/references/"* .github/skills/references/

# 5. Run the playbook (single prompt, ~17 minutes)
gh copilot -p "Read the quality playbook skill at .github/skills/SKILL.md \
and its reference files in .github/skills/references/. Execute the quality \
playbook for this project. IMPORTANT: Skip Phase 0 and Phase 0b entirely — \
do not look for previous_runs/ or sibling versioned directories. This is a \
clean benchmark run testing independent bug discovery. Start directly at \
Phase 1." --model gpt-5.4 --yolo
```

When it finishes, check `quality/BUGS.md` for confirmed findings with file locations, regression tests, and fix patches. The run also produces a full quality system in `quality/` — requirements, functional tests, code review protocols, and a spec audit.

**What this demonstrates:** The playbook derives behavioral requirements from the code and virtio specification, then uses those requirements to drive a three-pass code review and multi-model spec audit. The bug it finds is a real intent violation: the transport-feature whitelist is *structurally correct* (valid C, no crashes, no warnings) but *behaviorally wrong* (it silently drops a feature the spec says it should preserve). This is the class of bug that structural code review alone cannot catch.

## The problem

Most AI code review can only find structural issues: null dereferences, resource leaks, race conditions. That catches about 65% of real defects. The other 35% are intent violations -- bugs that can only be found if you know what the code is *supposed* to do. A function that silently returns null instead of throwing, a duplicate-key check that passes when the first value is null, a sanitization step that runs after the branch decision it was supposed to guard. These bugs look correct to any reviewer that doesn't know the spec.

The playbook closes that gap. It reads your codebase, derives behavioral requirements from every source it can find (code, docs, specs, comments, defensive patterns, community documentation), and uses those requirements to drive review. The result is a quality system grounded in intent, not just structure.

## Quick start

The playbook is a skill for AI coding tools. Copy it into your project and ask the AI to run it.

**GitHub Copilot:**
```bash
mkdir -p .github/skills/references
cp SKILL.md .github/skills/SKILL.md
cp LICENSE.txt .github/skills/LICENSE.txt
cp references/* .github/skills/references/
```

**Claude Code:**
```bash
mkdir -p .claude/skills/quality-playbook/references
cp SKILL.md .claude/skills/quality-playbook/SKILL.md
cp LICENSE.txt .claude/skills/quality-playbook/LICENSE.txt
cp references/* .claude/skills/quality-playbook/references/
```

Then tell your AI tool: *"Read the quality playbook skill and generate a complete quality system for this project."*

The playbook runs in six tracked phases: explore the codebase (Phase 1), generate quality artifacts (Phase 2), run a three-pass code review with regression tests (Phase 3), execute a multi-model spec audit (Phase 4), reconcile and close findings (Phase 5), and verify against self-check benchmarks (Phase 6). It takes anywhere from 5 to 60 minutes depending on project size, and it works with any language.

## What it produces

The playbook generates these files:

| Artifact | Location | What it does |
|----------|----------|-------------|
| `REQUIREMENTS.md` | `quality/` | Behavioral requirements derived from code, docs, and community sources via a five-phase pipeline. This is the foundation -- without requirements, review is limited to structural bugs. |
| `QUALITY.md` | `quality/` | Quality constitution defining what "correct" means for this specific project, with fitness-to-purpose scenarios and coverage theater prevention. |
| `test_functional.*` | `quality/` | Functional tests in the project's native language, traced to requirements rather than generated from source code. |
| `RUN_CODE_REVIEW.md` | `quality/` | Three-pass protocol: structural review, requirement verification, cross-requirement consistency. Each pass finds bugs the others can't. |
| `RUN_SPEC_AUDIT.md` | `quality/` | Council of Three: three independent AI models audit the code against requirements. Different models have different blind spots, and the triage uses confidence weighting, not majority vote. |
| `RUN_INTEGRATION_TESTS.md` | `quality/` | End-to-end test protocol grounded in use cases, with a traceability column mapping each test to the user outcome it validates. |
| `RUN_TDD_TESTS.md` | `quality/` | Red-green TDD verification protocol: for each confirmed bug, prove the regression test fails on unpatched code and passes with the fix. |
| `BUGS.md` | `quality/` | Consolidated bug report with spec basis, severity, reproduction steps, and patch references for every confirmed finding. |
| `AGENTS.md` | project root | Bootstrap file so every future AI session inherits the full quality infrastructure. |

## How it works

The playbook's value comes from requirement derivation. AI code reviewers are bottlenecked by the same thing human reviewers are: if you don't know what the code is *supposed* to do, you can only find structural issues. The playbook's main job is figuring out intent, then using that intent to drive every downstream artifact.

**Phase 1: Explore.** The AI reads source files, tests, config, specs, and commit history. If you provide community documentation (GitHub issues, user guides, API docs, forum discussions), it reads those too. The goal is to understand not just what the code does, but what it's supposed to do.

**Phase 2: Generate.** A five-phase pipeline extracts behavioral contracts from the codebase, derives testable requirements, verifies coverage, checks completeness, and adds a narrative layer with validated use cases. The pipeline also generates functional tests, review protocols, a TDD verification protocol, and the quality constitution.

**Phase 3: Code review.** A three-pass code review runs against HEAD: structural review with anti-hallucination guardrails, requirement verification checking each requirement against the code, and cross-requirement consistency checking whether requirements contradict each other. About 65% of findings come from Pass 1, 35% from Passes 2 and 3. Each confirmed bug gets a regression test.

**Phase 4: Spec audit.** Three independent AI models audit the code against the requirements. The triage process uses verification probes -- targeted checks that ask "is this actually true?" -- rather than dismissing single-model findings. As of v1.3.17, verification probes must produce executable test assertions (not just prose reasoning) to confirm or reject findings, which prevents the triage from hallucinating code compliance. The most valuable findings are often the ones only one model catches.

**Phase 5: Reconciliation.** Post-review reconciliation closes the loop: every bug from code review and spec audit is tracked, regression-tested or explicitly exempted, and the completeness report is finalized with one authoritative verdict.

**Phase 6: Verify.** 45 self-check benchmarks validate the generated artifacts against internal consistency rules -- requirement counts match across all surfaces, no stale text remains, every finding has a closure status, and triage probes include executable evidence.

### Why documentation matters

Adding community documentation to the pipeline produces measurably better results. In a controlled experiment across multiple repositories, documentation-enriched runs found more bugs, different bugs, and higher-confidence bugs than code-only baselines. The documentation gives auditors spec language to check against, turning "this code looks odd" into "this code contradicts the documented behavior."

### What's new in v1.3.20

- **Mechanical verification artifacts with integrity check (council-recommended).** Before CONTRACTS.md can assert that a dispatch function handles specific constants, you must generate and execute a shell pipeline (awk/grep) that extracts actual case labels from the function body, saving to `quality/mechanical/<function>_cases.txt`. Each extraction command is also appended to `quality/mechanical/verify.sh`, which re-runs the same commands and diffs against saved files. Phase 6 must execute `verify.sh` — if any diff is non-empty, the artifact was tampered with. This integrity check was added because v1.3.19 testing showed the model can execute the correct command but write fabricated output to the file instead of letting the shell redirect capture it.
- **Source-inspection tests must execute (no `run=False`).** Regression tests that verify source structure (string presence, case label existence) are safe, deterministic, and must run. The `run=False` flag is banned for these tests. In v1.3.18, the correct assertion existed but never fired because `run=False` made it inert.
- **Contradiction gate.** Before closure, executed evidence (mechanical artifacts, regression test results, TDD red-phase failures) is compared against prose artifacts (requirements, contracts, triage, BUGS.md). If they contradict, the executed result wins — the prose artifact must be corrected before proceeding.
- **Effective council gating for enumeration checks.** If the council is incomplete (<3/3) and the run includes whitelist/dispatch checks, the audit cannot close those checks without mechanical proof artifacts.
- **Normative vs. descriptive contract language.** Requirements use "must preserve" (normative) unless a mechanical artifact confirms the claim, in which case "preserves" (descriptive) is allowed.
- **Self-contained iterative convergence.** New Phase 0 (Prior Run Analysis) builds a seed list from prior runs' confirmed bugs and mechanically re-checks each seed against the current source tree. After Phase 6, a convergence check compares net-new bugs against the seed list. When net-new bugs = 0, bug discovery has converged. When not converged, the skill automatically archives the current run to `previous_runs/` and re-iterates from Phase 0 — up to 5 iterations by default (configurable). No external scripts needed; the skill handles the full iteration loop internally with context-window awareness. A `run_iterate.sh` script is also available for shell-level orchestration.
- **45 self-check benchmarks** (up from 22).

## Validation

The playbook is validated against the [Quality Playbook Benchmark](https://github.com/andrewstellman/quality-playbook-benchmark): 2,564 real defects from 50 open-source repositories across 14 programming languages. Instead of injecting synthetic faults, we use real historical bugs tied to single fix commits as ground truth.

The key finding: approximately 65% of real defects are detectable by structural code review alone. The remaining 35% are intent violations that require knowing what the code is supposed to do. The playbook's value is in closing that gap.

## Repository structure

```
quality-playbook/
├── SKILL.md                # The skill (main file)
├── references/             # Protocol and pipeline reference docs
├── LICENSE.txt             # Apache 2.0
├── AGENTS.md               # AI bootstrap file
└── quality/                # Generated quality infrastructure (from running the skill on itself)
    ├── REQUIREMENTS.md     # Behavioral requirements
    ├── QUALITY.md          # Quality constitution
    ├── test_functional.py  # Spec-traced functional tests
    ├── CONTRACTS.md        # Extracted behavioral contracts
    ├── COVERAGE_MATRIX.md  # Contract-to-requirement traceability
    ├── COMPLETENESS_REPORT.md  # Final gate with verdict
    ├── PROGRESS.md         # Phase checkpoint log + bug tracker
    ├── BUGS.md             # Consolidated bug report with spec basis
    ├── RUN_CODE_REVIEW.md  # Three-pass review protocol
    ├── RUN_SPEC_AUDIT.md   # Council of Three audit protocol
    ├── RUN_INTEGRATION_TESTS.md  # Integration test protocol (use-case traced)
    ├── RUN_TDD_TESTS.md    # Red-green TDD verification protocol
    ├── TDD_TRACEABILITY.md # Bug → requirement → spec → test mapping
    ├── test_regression.*   # Regression tests for confirmed bugs
    ├── SEED_CHECKS.md     # Prior-run seed list (continuation mode)
    ├── mechanical/         # Shell-extracted verification artifacts + verify.sh
    ├── writeups/           # Per-bug detailed writeups (BUG-NNN.md)
    ├── patches/            # Fix and regression-test patches
    ├── code_reviews/       # Code review output
    └── spec_audits/        # Auditor reports + triage
```

## Example output

The `quality/` directory contains the results of running the playbook against itself. These are real outputs, not samples — every file was generated by the skill analyzing its own repository.

| File | What to look at |
|------|----------------|
| [REQUIREMENTS.md](quality/REQUIREMENTS.md) | Behavioral requirements derived from the skill specification. This is the foundation that drives everything else. |
| [QUALITY.md](quality/QUALITY.md) | Quality constitution defining fitness-to-purpose scenarios and coverage targets for the playbook itself. |
| [test_functional.py](quality/test_functional.py) | Functional tests traced to requirements, written in the project's native language. |
| [CONTRACTS.md](quality/CONTRACTS.md) | Raw behavioral contracts extracted from the codebase before requirement derivation. |
| [COVERAGE_MATRIX.md](quality/COVERAGE_MATRIX.md) | Traceability matrix mapping every contract to the requirement that covers it. |
| [COMPLETENESS_REPORT.md](quality/COMPLETENESS_REPORT.md) | Final gate report with post-reconciliation verdict. |
| [RUN_CODE_REVIEW.md](quality/RUN_CODE_REVIEW.md) | Three-pass code review protocol ready for any AI session to execute. |
| [RUN_SPEC_AUDIT.md](quality/RUN_SPEC_AUDIT.md) | Council of Three spec audit protocol. |
| [RUN_TDD_TESTS.md](quality/RUN_TDD_TESTS.md) | Red-green TDD verification protocol for confirmed bugs. |
| [PROGRESS.md](quality/PROGRESS.md) | Phase-by-phase checkpoint log with cumulative bug tracker — the external memory that prevents findings from being orphaned. |
| [code_reviews/](quality/code_reviews/) | Actual code review output from the three-pass protocol. |
| [spec_audits/](quality/spec_audits/) | Individual auditor reports and triage from the Council of Three. |

## Context

This project supports an [O'Reilly Radar article series](https://oreillyradar.substack.com/p/the-accidental-orchestrator) on AI-driven development and agentic engineering by Andrew Stellman. The playbook was built using AI-driven development with [Octobatch](https://github.com/andrewstellman/octobatch), an open-source Python batch LLM orchestrator.

## License

Apache 2.0.
