# Quality Playbook Toolkit

> This file is for your AI assistant to read — not for you to read yourself.
> Open it in Claude Code, Cursor, Copilot, or any AI coding tool and say:
> "Read TOOLKIT.md and help me set up the quality playbook for my project."
> The AI will guide you through everything.

## What this is

The Quality Playbook is a skill that explores any codebase from scratch and finds real bugs. It generates nine quality artifacts: exploration notes, requirements, a quality constitution, functional tests, a code review with regression tests, a consolidated bug report with patches, TDD verification, integration tests, and a multi-model spec audit. Every confirmed bug gets a regression test patch, a fix patch, and red/green TDD verification.

The skill file is `SKILL.md`. The iteration reference is `ITERATION.md`. These contain the full operational instructions the agent follows when running the playbook. This toolkit file is different — it helps you (through your AI assistant) set up, run, interpret, and iterate on the playbook.

## Quick start

The user wants to run the quality playbook on a codebase. Here's what to do:

1. **Copy skill files into the repo.** The playbook expects its files at `.github/skills/` inside the target repository:
   ```
   .github/skills/SKILL.md
   .github/skills/ITERATION.md
   .github/skills/references/          (all .md files from the references/ directory)
   .github/skills/quality_gate.sh
   ```
   Create the directories if they don't exist. Copy from wherever the user has the playbook files.

2. **Run the playbook.** Give the agent this prompt:
   ```
   Read the quality playbook skill at .github/skills/SKILL.md and execute the quality playbook for this project.
   ```
   That's it. The agent reads the skill, explores the codebase, and generates all artifacts into a `quality/` directory.

3. **Review results.** The key output files:
   - `quality/BUGS.md` — confirmed bugs with file:line references
   - `quality/PROGRESS.md` — phase completion tracker and bug summary
   - `quality/results/tdd-results.json` — structured TDD verification results
   - `quality/patches/BUG-NNN-regression-test.patch` — test that proves each bug
   - `quality/patches/BUG-NNN-fix.patch` — proposed fix for each bug

## Setting up automation scripts

Users often want to run the playbook across multiple repositories or automate the iteration cycle. Help them create two scripts adapted to their OS and shell:

### Setup script

Copies skill files into one or more target repos. Core logic:

```bash
# Adapt paths for the user's environment
SKILL_DIR="/path/to/quality-playbook"   # where SKILL.md etc. live
REPO_DIR="/path/to/repos"               # where target repos live

for repo in "$@"; do
    dst="${REPO_DIR}/${repo}/.github/skills"
    mkdir -p "${dst}/references"
    cp "${SKILL_DIR}/SKILL.md" "${dst}/SKILL.md"
    cp "${SKILL_DIR}/ITERATION.md" "${dst}/ITERATION.md"
    cp "${SKILL_DIR}/quality_gate.sh" "${dst}/quality_gate.sh"
    cp "${SKILL_DIR}/references/"*.md "${dst}/references/"
    echo "Set up ${repo}"
done
```

On Windows (PowerShell), replace the loop with `foreach ($repo in $args)` and use `Copy-Item` / `New-Item -ItemType Directory`.

### Run script

Invokes the AI agent on each repo. The prompt is always the same — what varies is how you invoke the agent. See the "Agent reference" section below for per-agent commands.

Key features the user might want in their run script:
- **Logging:** Capture output to a file per repo (use `tee` on Unix, `Tee-Object` on PowerShell)
- **Iteration support:** A `--next-iteration --strategy <name>` mode that passes the iteration prompt instead of the baseline prompt
- **Strategy all:** A loop that runs gap → unfiltered → parity → adversarial in sequence, stopping early if a strategy finds zero new bugs
- **Parallel execution:** Run multiple repos concurrently (but see "Rate limits" below)

The iteration prompt is:
```
Read the quality playbook skill at .github/skills/SKILL.md and run the next iteration using the <strategy> strategy.
```

Replace `<strategy>` with: gap, unfiltered, parity, or adversarial.

## Agent reference

The playbook works with any AI coding agent that can read files and execute shell commands. Here's what we know about each:

### Claude Code (CLI)

**Best overall results.** Claude Code with Opus follows the full instruction chain including TDD test execution — it actually runs the regression tests and captures red/green phase logs. Other agents tend to skip this step.

```bash
cd /path/to/repo
claude -p "Read the quality playbook skill at .github/skills/SKILL.md and execute the quality playbook for this project." --dangerously-skip-permissions
```

- `--dangerously-skip-permissions` lets it run shell commands without prompting (needed for test execution, mechanical verification, etc.)
- Add `--model opus` or `--model sonnet` to specify a model
- To capture output: pipe through `tee` — e.g., `claude -p "..." --dangerously-skip-permissions 2>&1 | tee output.log`
- Do NOT wrap with `script -q` — it buffers output and prevents live streaming

### GitHub Copilot (CLI)

**Good exploration, weak on TDD execution.** Copilot with gpt-5.4 finds bugs reliably but typically generates regression test patches without actually executing them. The TDD red/green logs will be missing or incomplete.

```bash
cd /path/to/repo
gh copilot -p "Read the quality playbook skill at .github/skills/SKILL.md and execute the quality playbook for this project." --model gpt-5.4 --yolo
```

- `--yolo` is Copilot's equivalent of skip-permissions
- Rate limits are aggressive: running 6+ repos in parallel with iteration cycles can trigger a 54-hour cooldown
- Stagger runs: 2-3 repos at a time, with pauses between batches

### Cursor (IDE)

**Good, but watch for two gotchas:**

1. **Isolate the repo.** Open ONLY the target repo folder in Cursor — not a parent directory containing other repos. Cursor's workspace scope bleeds upward, and it will find and read BUGS.md files from sibling directories, contaminating the run with prior findings.

2. **Choose the right model.** Cursor's "auto" mode may select a model that's too weak for deep code exploration. Code-generation models (like Codex) can produce all the artifacts and pass all the gates while finding zero bugs — they follow the structure without the reasoning depth. Explicitly select Claude Sonnet, Claude Opus, or GPT-5.4 in Cursor's model dropdown.

Prompt: paste the same prompt into the chat.

### Other agents

The playbook should work with any agent that can read markdown files and execute shell commands. The key requirement is **reasoning depth** — the agent needs to be able to read unfamiliar code, form hypotheses about edge cases, and trace code paths across multiple functions. Models optimized purely for code generation (autocomplete, inline suggestions) typically lack this capability.

## Iteration strategies

After the baseline run, iteration strategies find additional bugs by re-exploring the codebase with different approaches. Each strategy targets a different failure mode. Run them in order:

**gap** — Scans what the baseline covered and explores what it missed. Best for large codebases where the first run only reached a subset of modules.

**unfiltered** — Ignores the structured three-stage approach entirely. Explores like an experienced developer: reading code, following hunches, tracing suspicious paths. Finds bugs that the structured approach suppresses by over-constraining exploration.

**parity** — Systematically compares parallel implementations of the same contract (e.g., setup vs. teardown, primary vs. fallback, sync vs. async). Finds bugs by spotting inconsistencies between code paths that should behave the same way but don't.

**adversarial** — Re-investigates findings that previous iterations dismissed as "design choices" or "insufficient evidence." Uses a lower evidentiary bar — a code-path trace showing the output differs from spec is sufficient. Finds bugs that conservative triage keeps rejecting.

**all** — Runs gap → unfiltered → parity → adversarial in sequence. Convenient but burns through rate limits fast. For Copilot users: run strategies individually and stagger them to avoid multi-day cooldowns.

### Typical yield

In benchmarking across 10+ open-source repos, iterations typically multiply the baseline bug count by 3-4x:
- Baseline alone: 1-3 bugs per repo on average
- After full iteration cycle: 4-10 bugs per repo on average

Bug counts vary between runs on the same repo due to non-determinism in exploration. A single run isn't definitive — iterations compensate by providing multiple independent exploration attempts.

### When to iterate

- If the baseline found bugs → iterate. The codebase has more.
- If the baseline found zero bugs → try one iteration (unfiltered is a good choice) before concluding the codebase is clean. A zero-bug baseline on a non-trivial codebase is often a low roll, not a clean bill of health.
- After the adversarial iteration, returns diminish sharply. Starting a fresh baseline run from scratch often finds more than a fifth iteration strategy would.

## Understanding results

### BUGS.md

Each confirmed bug has a heading `### BUG-NNN` with: file:line location, description, severity, spec basis (what documented contract it violates), regression test reference, and fix patch reference.

**Are these real bugs?** In benchmarking, 15 out of 15 spot-checked bugs were verified as real against actual source code. The playbook is conservative — it's more likely to miss bugs (Type II errors) than to report false positives (Type I errors). If BUGS.md says something is a bug, it almost certainly is.

### TDD verification

Each bug should have a red/green TDD cycle proving it's real:
- `quality/results/BUG-NNN.red.log` — the regression test fails on unpatched code (proves the bug exists)
- `quality/results/BUG-NNN.green.log` — the regression test passes after applying the fix patch (proves the fix works)

If these log files are missing, the agent generated the test patches but didn't execute them. This is a known issue with some agents (see "Agent reference"). You can run the TDD cycle manually:

```bash
# Red phase: revert fix, run test
git apply -R quality/patches/BUG-NNN-fix.patch
<test command for your language>
# Green phase: apply fix, run test
git apply quality/patches/BUG-NNN-fix.patch
<test command for your language>
```

### quality_gate.sh

The gate script validates all artifacts mechanically. Run it after the playbook completes:

```bash
bash .github/skills/quality_gate.sh .
```

If it reports FAIL results, the most common causes:
- Missing `quality/patches/BUG-NNN-regression-test.patch` files
- BUGS.md heading format (`### BUG-NNN` not `## BUG-NNN`)
- Missing fields in `tdd-results.json`
- Writeups without inline fix diffs
- Missing red-phase log files

## Rate limits and cost management

The quality playbook is a large workload — a full run with iterations can consume 15+ million tokens. This matters for rate limits and costs.

**GitHub Copilot:** Aggressive rate limits. Running 6 repos simultaneously through iteration cycles triggered a 54-hour cooldown. Recommendation: run 2-3 repos at a time, use individual iteration strategies instead of `--strategy all`, and pause between batches.

**Claude Code:** Usage counts against your Claude plan. The Max plan provides the most headroom. A single baseline run on a medium-sized repo is manageable; a full iteration cycle on a large repo (like a Linux kernel driver) is expensive.

**Cursor:** Usage depends on the model selected and the plan. Same advice: stagger runs, don't run everything in parallel.

**General:** The playbook's multi-pass mode (explore in one session, generate artifacts in another) uses shorter sessions that each fit in a smaller context window. This can reduce per-session token usage compared to single-pass mode, at the cost of more manual coordination.

## Language support

The playbook works with any programming language. It adapts its exploration patterns, test generation, and regression test framework to the project's language:

- **Go:** `go test`, `t.Skip()` guards, `go vet` for static analysis
- **Python:** `pytest` with `@pytest.mark.xfail(strict=True)`, `mypy` for type checking
- **Java:** Maven/Gradle + JUnit 5, `@Disabled` annotations
- **Rust:** `cargo test`, `#[ignore]` attributes, `#[should_panic]` for panic-manifesting bugs
- **TypeScript/JavaScript:** Jest (`test.failing`) or Vitest (`test.fails`), ESLint
- **C:** Source-inspection tests via shell scripts (grep/awk on source files) for kernel-style projects where a full build environment may not be available

If the project's test runner isn't available (e.g., a C kernel module on a machine without the kernel build environment), the playbook records `NOT_RUN` in the TDD log with an explanation — it doesn't fail silently.

## Gathered documentation

The playbook works best when it has access to project documentation — specs, RFCs, API docs, design docs. If you have these, put them in a `docs_gathered/` directory in the repo root before running the playbook. The playbook will use them as the ground truth for what the code should do, which dramatically improves bug-finding accuracy.

If no docs exist, the playbook derives requirements from the code itself — comments, function signatures, error messages, test expectations. This works but produces weaker spec-basis evidence for each bug.

## Troubleshooting

**Zero bugs found on a non-trivial codebase:**
- Check which model the agent used. Code-generation models (Codex, small/fast variants) lack the reasoning depth for exploration. Switch to Claude Opus, Claude Sonnet, or GPT-5.4.
- Check that `.github/skills/SKILL.md` exists and was read. Some agents skip reading referenced files.
- Try the unfiltered iteration strategy — it removes structural constraints that can over-constrain weaker models.

**Agent found bugs but no TDD log files:**
- This is a known issue with Copilot and Cursor (see "Agent reference"). The agent wrote "TDD verified" in the JSON without actually running the tests.
- Run the TDD cycle manually using the bash template in the "TDD verification" section above.
- Or ask the agent in a follow-up prompt: "Read the TDD execution enforcement section in .github/skills/SKILL.md and execute the red/green TDD cycle for every confirmed bug."

**Rate limited (Copilot 54-hour cooldown):**
- Wait for the cooldown to clear. Reduce parallelism on the next batch.
- Switch to Claude Code or Cursor for immediate runs while waiting.
- Use individual iteration strategies instead of `--strategy all`.

**Cursor contamination from sibling directories:**
- Move the target repo to an isolated directory before opening in Cursor.
- Or open only the repo folder, not a parent directory.

**quality_gate.sh fails:**
- Read the output carefully — each FAIL line tells you exactly what's wrong.
- The most common fix: missing patch files. Ask the agent to generate them.
- Second most common: heading format. BUGS.md must use `### BUG-NNN` (three hashes), not `## BUG-NNN`.

**Phase 0 finds seeds from a previous run:**
- This is expected if you're re-running on a repo that already has `quality/` artifacts from a prior run.
- If you want a clean baseline, delete or rename the existing `quality/` directory first.
- If you want to build on prior findings, leave it — Phase 0 will import previously confirmed bugs as seeds.
