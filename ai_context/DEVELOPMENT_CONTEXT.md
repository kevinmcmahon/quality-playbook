# Quality Playbook — Development Context

> This file is for AI assistants helping maintain and improve the quality playbook skill.
> It contains the project's architecture, benchmarking methodology, known issues,
> and improvement axes. Read this when working on the skill files themselves.

## Project structure

```
quality-playbook/
├── AGENTS.md                    ← AI coding agent entry point (repo root)
├── SKILL.md                     ← The skill — full operational instructions for running the playbook
├── ITERATION.md                 ← Iteration strategy reference (gap, unfiltered, parity, adversarial)
├── quality_gate.sh              ← Mechanical validation script (runs after playbook completes)
├── LICENSE.txt                  ← License terms
├── references/                  ← Reference files read during specific phases
│   ├── requirements_pipeline.md ← Requirements derivation and post-review reconciliation
│   ├── review_protocols.md      ← Three-pass code review protocol and regression test conventions
│   ├── spec_audit.md            ← Council of Three spec audit protocol
│   └── verification.md          ← 45 self-check benchmarks for Phase 3
├── ai_context/                  ← AI-readable context files
│   ├── TOOLKIT.md               ← For users' AI assistants (setup, run, interpret)
│   └── DEVELOPMENT_CONTEXT.md   ← For maintainers' AI assistants (this file)
├── repos/                       ← Benchmark infrastructure (not in skill repo)
│   ├── setup_repos.sh           ← Copies skill files into target repos
│   ├── run_playbook.sh          ← Invokes agents on repos (supports Copilot, Claude Code)
│   ├── _benchmark_lib.sh        ← Shared functions for benchmark scripts
│   └── clean/                   ← Clean clones of benchmark repos
└── council-reviews/             ← Council review briefings and responses
```

## How the skill works

The quality playbook is a single long-form instruction document (SKILL.md) that an AI agent reads and follows end-to-end. It has three phases:

**Phase 1 (Explore):** The agent explores the codebase using a three-stage approach — open exploration, quality risk analysis, and selected pattern deep-dives. Outputs: EXPLORATION.md with candidate bugs.

**Phase 2 (Generate + Execute):** The agent generates nine quality artifacts from the exploration findings, then executes three sub-phases: code review with regression tests (2b), spec audit with Council of Three triage (2c), and post-review reconciliation with terminal gate verification (2d). Every confirmed bug gets a regression test patch, fix patch, writeup, and TDD red/green verification.

**Phase 3 (Verify):** The agent runs mechanical verification and self-check benchmarks against 45 criteria.

**Iteration mode:** After the baseline run, the agent can run additional iterations using strategies defined in ITERATION.md. Each strategy re-explores the codebase with a different approach, then re-runs Phases 2-3 on the merged findings.

## Three improvement axes

When the playbook misses a bug, the miss falls on one of three axes. Identifying which axis tells you what to fix:

### 1. Exploration rules

**Symptom:** The agent never looked at the code containing the bug.

**What to fix:** Exploration patterns in SKILL.md Phase 1, pattern applicability matrix, domain-knowledge questions. Or add a new iteration strategy that targets the unexplored area.

**Example:** The parity sub-type checklist was added to ITERATION.md because the parity strategy wasn't comparing resource lifecycle (setup vs. teardown) — it was only finding "obvious" parallel-path differences.

### 2. Iteration types

**Symptom:** The agent looked at the code but the bug wasn't found by any existing iteration strategy.

**What to fix:** Add a new iteration strategy to ITERATION.md that targets the failure mode. Each strategy exists because a specific class of bugs was being systematically missed.

**History:**
- **gap** (v1.3.44): Baseline only covered subset of codebase
- **unfiltered** (v1.3.44): Structured approach over-constrained exploration
- **parity** (v1.3.45): No strategy explicitly compared parallel code paths
- **adversarial** (v1.3.44): Conservative triage kept dismissing real bugs

### 3. Triage calibration

**Symptom:** The agent found the code, flagged it as a candidate, but dismissed it during triage.

**What to fix:** Triage rules in SKILL.md (evidentiary standards, "what counts as sufficient evidence"), the Demoted Candidates Manifest in ITERATION.md (tracks dismissed findings with re-promotion criteria), adversarial strategy evidentiary bar.

**Example:** Pydantic's AliasPath bug was found and dismissed THREE times before the adversarial strategy recovered it. The triage kept classifying it as a "design choice" because the behavior was "permissive." The fix was lowering the adversarial evidentiary bar: code-path trace + semantic drift is sufficient.

## Benchmarking methodology

### Benchmark repos

The benchmark suite uses open-source codebases across multiple languages. Each repo is cloned once into `repos/clean/` and never modified. For each skill version, `setup_repos.sh` creates a working copy (e.g., `chi-1.3.47`) with the skill files installed.

Current benchmark repos (10 actively benchmarked):
- **C:** virtio (Linux kernel driver — hardest repo, reference target for parity strategy)
- **Go:** chi, cobra
- **Python:** httpx, pydantic
- **Java:** javalin, gson
- **JavaScript:** express
- **Rust:** axum, serde
- **TypeScript:** zod

60+ additional repos in `repos/clean/` for expanded benchmarking.

### Running benchmarks

```bash
cd repos/
./setup_repos.sh <repo-names>           # copy skill files
./run_playbook.sh <repo-names>          # baseline runs (Copilot default)
./run_playbook.sh --claude <repo-names> # baseline runs (Claude Code)
./run_playbook.sh --next-iteration --strategy all <repo-names>  # full iteration cycle
```

### Interpreting results

**Bug counts vary between runs.** The same skill on the same codebase produces different bug counts due to non-determinism in exploration. A single run isn't definitive. Compare across 5+ runs or use iteration cycles to compensate.

**Baseline vs. iteration yield.** Baseline typically finds 1-3 bugs per repo. Full iteration cycle (gap + unfiltered + parity + adversarial) multiplies by 3-4x. If a skill change doesn't improve baseline yield, it may still improve iteration yield or vice versa.

**Spot-check every new version.** After making skill changes, spot-check 3-5 bugs from the new version against actual source code. Verify the bug is real, the file:line is correct, and the regression test would actually fail. In v1.3.46 benchmarking, 15/15 spot-checked bugs were verified as real.

### Council reviews

For major skill changes, we run a council review: three different AI agents independently analyze the benchmark data, iteration logs, and bug quality, then propose improvements. The agents don't modify code — they write analysis documents.

Council review artifacts go in `council-reviews/`. Each review has:
- `COUNCIL_BRIEFING_VN.md` — data and questions for the council
- `COUNCIL_VN_PROMPTS.md` — prompts for each reviewer (must include "DO NOT modify any code")
- `{AGENT}_RESPONSE_VN.md` — each reviewer's analysis

### Known agent behavior differences

| Agent | Exploration | TDD execution | Known issues |
|-------|------------|---------------|-------------|
| Claude Code / Opus | Strong | Reliable (creates red/green logs) | Expensive on large repos |
| Copilot / gpt-5.4 | Strong | Weak (skips log creation) | 54hr rate limit on heavy use |
| Cursor / Sonnet | Good | Weak first pass, follows up when asked | Workspace scope bleeds to siblings |
| Cursor / Codex 5.3 | Weak (zero bugs) | N/A | Insufficient reasoning depth |

## Version history highlights

- **v1.3.13–v1.3.14:** Early structured approach. Zero bugs found — too rigid.
- **v1.3.21:** Gate hardening. First confirmed bugs (2 total across 10 repos).
- **v1.3.25:** Unfiltered domain-driven exploration. Major breakthrough — 14 bugs.
- **v1.3.40:** Parity patterns. Found 5 virtio bugs using fallback path comparison.
- **v1.3.44:** Iteration mode (gap, unfiltered, adversarial). 3.7x baseline yield.
- **v1.3.45:** ITERATION.md reference file, parity strategy, suggested-next-prompt UX.
- **v1.3.46:** Demoted Candidates Manifest, parity sub-type checklist, adversarial bar adjustment, TDD execution enforcement.
- **v1.3.47:** TDD log enforcement — six insertion points from Cursor diagnostic (artifact contract, closure gate, bash template, progress checkbox, file-existence gate, sidecar contradiction check).

## Current known issues

1. **Virtio missing bugs.** Two bugs found in v1.3.40 have never been recovered: MSI-X slow_virtqueues reattach and GFP_KERNEL under spinlock. Both are exploration axis issues — the agent doesn't reach the relevant code. The parity sub-type checklist was designed to address this but hasn't been validated yet.

2. **TDD execution compliance.** Only Claude Code reliably creates red/green log files. Copilot and Cursor skip the step despite v1.3.47's six insertion points (not yet tested on v1.3.47). If v1.3.47 doesn't fix it, a post-run script that mechanically runs the TDD cycle may be needed.

3. **Rate limits.** Running 6+ repos simultaneously through iteration cycles triggers Copilot's 54-hour cooldown. Users need to stagger runs (2-3 repos at a time) or use Claude Code / Cursor.

4. **Cursor workspace contamination.** Cursor reads sibling directories and imports findings from prior runs. Repos must be isolated in their own parent directory.

## Making changes to the skill

**Always back up before editing.** Copy any file you're about to modify to a `.bak` version first.

**Test on at least 2 repos after changes.** One large (virtio or cobra) and one small (express or httpx). Check both baseline and at least one iteration strategy.

**Update the version.** The `version:` field in SKILL.md metadata must be bumped for every change. All generated artifacts stamp this version, and mismatches cause quality_gate.sh failures.

**Run quality_gate.sh after testing.** The gate validates artifact conformance mechanically. If it passes on your test repos, the change is safe to commit.

**Update TOOLKIT.md and this file.** If your change affects how users run the playbook or how maintainers work on it, update the relevant context file.
