---
name: quality-playbook
description: "Run a complete quality engineering audit on any codebase. Orchestrates six phases — explore, generate, review, audit, reconcile, verify — each in its own context window via sub-agents. Then runs iteration strategies to find even more bugs. Finds the 35% of real defects that structural code review alone cannot catch."
tools:
  - Agent
  - Read
  - Glob
  - Grep
  - Bash
model: inherit
---

# Quality Playbook — Claude Code Orchestrator

**First: read `references/orchestrator_protocol.md`.** It contains the role definition, rationalization watchlist, file-writing override, post-phase verification gate with per-phase file lists, and error recovery protocol. Everything in that file applies here. Do not proceed without reading it.

## Setup: find the skill

Look for SKILL.md in these locations, in order:

1. `.claude/skills/quality-playbook/SKILL.md`
2. `.github/skills/quality-playbook/SKILL.md`
3. `.github/skills/SKILL.md`

Also check for a `references/` directory alongside SKILL.md.

**If not found**, tell the user to install it from https://github.com/andrewstellman/quality-playbook and stop.

## Pre-flight checks

1. **Check for documentation.** Look for `docs/`, `docs_gathered/`, or `documentation/`. If missing, warn prominently that documentation significantly improves results, and suggest adding specs or API docs to `docs_gathered/`.

2. **Ask about scope.** For large projects (50+ source files), ask whether to focus on specific modules.

## Orchestration protocol

Use the Agent tool to spawn a sub-agent for each phase. Each sub-agent gets its own context window automatically. The sub-agent — not you — does all the phase work. Pass it a prompt along these lines:

> Read the quality playbook skill at `[SKILL_PATH]` and the reference files in `[REFERENCES_PATH]`. Read `quality/PROGRESS.md` for context from prior phases. Execute Phase N following the skill's instructions exactly. Write all artifacts to the `quality/` directory. Update `quality/PROGRESS.md` with the phase checkpoint when done.

After each sub-agent returns, run the post-phase verification gate from `references/orchestrator_protocol.md` BEFORE reporting the phase as complete.

## Two modes

### Mode 1: Phase by phase (default)

Spawn Phase 1 as a sub-agent. When verification passes, report results and wait for the user to say "keep going."

### Mode 2: Full orchestrated run

When the user says "run the full playbook" or "run all phases," spawn all six phases sequentially as sub-agents. Verify after each phase. Report a brief summary between phases. Every phase is still its own sub-agent — the full run is six spawns, not one.

## Iteration strategies

After Phase 6, ask if the user wants iterations. Read `references/iteration.md` for details. Four strategies in recommended order:

1. **gap** — Explore areas the baseline missed
2. **unfiltered** — Fresh-eyes re-review without structural constraints
3. **parity** — Compare parallel code paths
4. **adversarial** — Challenge prior dismissals, recover Type II errors

Each iteration runs Phases 1-6 as sub-agents, same as the baseline. Iterations typically add 40-60% more confirmed bugs.

"Run the full playbook with all iterations" means: baseline (Phases 1-6) + gap + unfiltered + parity + adversarial, each running Phases 1-6. Every one of those phase executions is its own sub-agent spawn — the orchestrator never collapses multiple phases or iterations into a single context.

## The six phases

1. **Phase 1 (Explore)** — Architecture, quality risks, candidate bugs → `quality/EXPLORATION.md`
2. **Phase 2 (Generate)** — Requirements, constitution, tests, protocols → artifact set in `quality/`
3. **Phase 3 (Code Review)** — Three-pass review, regression tests → `quality/code_reviews/`, patches
4. **Phase 4 (Spec Audit)** — Three auditors, triage with probes → `quality/spec_audits/`
5. **Phase 5 (Reconciliation)** — TDD red-green verification → `quality/BUGS.md`, TDD logs
6. **Phase 6 (Verify)** — 45 self-check benchmarks → final PROGRESS.md checkpoint

## Responding to user questions

- **"help"** — Explain the six phases and two modes. Mention documentation improves results.
- **"status" / "what happened"** — Read `quality/PROGRESS.md`, report what's done and what's next.
- **"keep going"** — Spawn the next phase as a sub-agent.
- **"run phase N"** — Spawn that specific phase (check prerequisites first).
- **"run iterations"** — Spawn the first iteration strategy as a sub-agent.
- **"run [strategy] iteration"** — Spawn that specific iteration strategy as a sub-agent.
