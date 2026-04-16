# Quality Playbook — Development Context

> This file is for AI assistants helping maintain and improve the quality playbook skill.
> It contains the project's architecture, benchmarking methodology, known issues,
> and improvement axes. Read this when working on the skill files themselves.
>
> The project accompanies the O'Reilly Radar article [AI Is Writing Our Code Faster Than We Can Verify It](https://www.oreilly.com/radar/ai-is-writing-our-code-faster-than-we-can-verify-it/).
> The README was coauthored with Claude Cowork.

## Project structure

```
quality-playbook/
├── AGENTS.md                    ← AI coding agent entry point (repo root)
├── SKILL.md                     ← The skill — full operational instructions for running the playbook
├── references/iteration.md      ← Iteration strategy reference (gap, unfiltered, parity, adversarial)
├── quality_gate.sh              ← Mechanical validation script (runs after playbook completes)
├── LICENSE.txt                  ← License terms
├── references/                  ← Reference files read during specific phases
│   ├── requirements_pipeline.md ← Requirements derivation and post-review reconciliation
│   ├── review_protocols.md      ← Three-pass code review protocol and regression test conventions
│   ├── spec_audit.md            ← Council of Three spec audit protocol
│   └── verification.md          ← 45 self-check benchmarks for Phase 6
├── ai_context/                  ← AI-readable context files
│   ├── TOOLKIT.md               ← For users' AI assistants (setup, run, interpret, recheck)
│   └── DEVELOPMENT_CONTEXT.md   ← For maintainers' AI assistants (this file)
├── repos/                       ← Benchmark infrastructure (not in skill repo)
│   ├── setup_repos.sh           ← Copies skill files into target repos
│   ├── run_playbook.sh          ← Invokes agents on repos (supports Copilot, Claude Code)
│   ├── _benchmark_lib.sh        ← Shared functions for benchmark scripts
│   └── clean/                   ← Clean clones of benchmark repos
└── council-reviews/             ← Council review briefings and responses (not distributed)
```

## How the skill works

The quality playbook is a long-form instruction document (SKILL.md) that an AI agent reads and follows. It is designed to run one phase at a time, with the user driving each phase forward. Each phase runs in its own session with a clean context window, producing files on disk that the next phase reads.

**Phase 1 (Explore):** The agent explores the codebase using a three-stage approach — open exploration, quality risk analysis, and selected pattern deep-dives. Outputs: EXPLORATION.md with candidate bugs.

**Phase 2 (Generate):** The agent generates nine quality artifacts from the exploration findings: requirements, constitution, functional tests, code review protocol, integration tests, spec audit protocol, TDD protocol, AGENTS.md.

**Phase 3 (Code Review):** Three-pass code review against HEAD. Regression tests for every confirmed bug. Generates patches.

**Phase 4 (Spec Audit):** Three independent AI auditors review the code against requirements. Triage with verification probes. Regression tests for net-new findings.

**Phase 5 (Reconciliation):** Close the loop — every bug tracked, regression-tested. TDD red-green cycle for all confirmed bugs. Writeups, fix patches, completeness report.

**Phase 6 (Verify):** Mechanical verification and 45 self-check benchmarks.

After each phase, the skill prints a prominent end-of-phase message telling the user what happened and what to say next. The user says "keep going" or "run phase N" to continue. This interactive protocol gives much better results than single-session execution because each phase gets the full context window.

**Iteration mode:** After the baseline run, the agent can run additional iterations using strategies defined in references/iteration.md. Each strategy re-explores the codebase with a different approach, then re-runs Phases 2-6 on the merged findings. Iterations typically add 40-60% more confirmed bugs.

**Recheck mode:** After the user fixes bugs, saying "recheck" triggers a lightweight verification pass. Recheck reads BUGS.md, checks each bug against the current source (reverse-applying fix patches, inspecting cited lines, optionally running regression tests), and writes results to `quality/results/recheck-results.json` and `quality/results/recheck-summary.md`. Takes 2-10 minutes instead of a full re-run. Does not find new bugs — only verifies previously found bugs.

## Three improvement axes

When the playbook misses a bug, the miss falls on one of three axes. Identifying which axis tells you what to fix:

### 1. Exploration rules

**Symptom:** The agent never looked at the code containing the bug.

**What to fix:** Exploration patterns in SKILL.md Phase 1, pattern applicability matrix, domain-knowledge questions. Or add a new iteration strategy that targets the unexplored area.

**Example:** The parity sub-type checklist was added to references/iteration.md because the parity strategy wasn't comparing resource lifecycle (setup vs. teardown) — it was only finding "obvious" parallel-path differences.

### 2. Iteration types

**Symptom:** The agent looked at the code but the bug wasn't found by any existing iteration strategy.

**What to fix:** Add a new iteration strategy to references/iteration.md that targets the failure mode. Each strategy exists because a specific class of bugs was being systematically missed.

**History:**
- **gap** (v1.3.44): Baseline only covered subset of codebase
- **unfiltered** (v1.3.44): Structured approach over-constrained exploration
- **parity** (v1.3.45): No strategy explicitly compared parallel code paths
- **adversarial** (v1.3.44): Conservative triage kept dismissing real bugs

### 3. Triage calibration

**Symptom:** The agent found the code, flagged it as a candidate, but dismissed it during triage.

**What to fix:** Triage rules in SKILL.md (evidentiary standards, "what counts as sufficient evidence"), the Demoted Candidates Manifest in references/iteration.md (tracks dismissed findings with re-promotion criteria), adversarial strategy evidentiary bar.

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
- **v1.3.45:** references/iteration.md reference file, parity strategy, suggested-next-prompt UX.
- **v1.3.46:** Demoted Candidates Manifest, parity sub-type checklist, adversarial bar adjustment, TDD execution enforcement.
- **v1.3.47:** TDD log enforcement — six insertion points from Cursor diagnostic (artifact contract, closure gate, bash template, progress checkbox, file-existence gate, sidecar contradiction check).
- **v1.4.0** (promoted from v1.3.50)**:** Six-phase interactive architecture (renumbered from 3 phases to 6), interactive phase-by-phase execution with end-of-phase messages, `--phase` flag in runner, quality gate script, four iteration strategies with 40-60% yield boost, TDD enforcement, documentation warning, help system, "keep going" continuation, O'Reilly Radar article, moved ITERATION.md to references/iteration.md, orchestrator agents for Claude Code and Copilot, **recheck mode** for lightweight fix verification (reads BUGS.md, checks each bug against current source, outputs recheck-results.json). Benchmarked: Express.js (14 bugs), Gson (9 bugs), Linux virtio (8 bugs) — all with 100% TDD coverage and 0 gate failures. Bootstrap self-audit: 19 bugs found across 4 iterations, all fixed and verified by recheck.

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
