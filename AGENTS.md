# Quality Playbook — Agent Guide

This file helps AI coding agents work on this repository. Read it first.

## What this repo is

The Quality Playbook is a skill for AI coding agents that explores any codebase from scratch and finds real bugs. It generates nine quality artifacts including a consolidated bug report with regression test patches, fix patches, and TDD red/green verification. It works with any language (Python, Java, Go, Rust, TypeScript, C, etc.) and any AI coding agent (Claude Code, GitHub Copilot, Cursor).

## Key files

| File | Purpose | When to read |
|------|---------|-------------|
| `SKILL.md` | Full operational instructions for running the playbook | When executing the playbook on a target repo |
| `references/iteration.md` | Iteration strategy reference (gap, unfiltered, parity, adversarial) | When running iteration mode |
| `quality_gate.sh` | Mechanical validation script | After playbook completes, to validate artifacts |
| `references/*.md` | Phase-specific reference files (review protocols, spec audit, etc.) | During specific phases as directed by SKILL.md |
| `ai_context/TOOLKIT.md` | User-facing interactive documentation | When helping a user set up or run the playbook |
| `ai_context/DEVELOPMENT_CONTEXT.md` | Maintainer context (architecture, benchmarking, known issues) | When working on the skill itself |
| `agents/quality-playbook.agent.md` | Orchestrator agent (Copilot / general format) | When setting up automated phase-by-phase execution |
| `agents/quality-playbook-claude.agent.md` | Orchestrator agent (Claude Code format, uses sub-agents) | When running in Claude Code with automatic orchestration |

## Installing the skill

Copy the skill into your AI coding tool's skill directory in the target repo:

**GitHub Copilot:**
```bash
mkdir -p .github/skills/references
cp SKILL.md .github/skills/SKILL.md
cp quality_gate.sh .github/skills/quality_gate.sh
cp references/* .github/skills/references/
# v1.5.2: single reference_docs/ tree at the target repo root.
mkdir -p reference_docs reference_docs/cite
# Optional: append suggested .gitignore rules for adopters.
cat skill-template.gitignore >> .gitignore
```

**Claude Code:**
```bash
mkdir -p .claude/skills/quality-playbook/references
cp SKILL.md .claude/skills/quality-playbook/SKILL.md
cp quality_gate.sh .claude/skills/quality-playbook/quality_gate.sh
cp references/* .claude/skills/quality-playbook/references/
# v1.5.2: single reference_docs/ tree at the target repo root.
mkdir -p reference_docs reference_docs/cite
cat skill-template.gitignore >> .gitignore
```

Then tell your AI tool:
```
Run the quality playbook on this project.
```

## Repository layout

```
AGENTS.md                ← you are here
SKILL.md                 ← the skill (operational instructions)
quality_gate.sh          ← artifact validation script
LICENSE.txt
references/              ← phase-specific reference documents
agents/
  quality-playbook.agent.md       ← orchestrator agent (Copilot / general)
  quality-playbook-claude.agent.md ← orchestrator agent (Claude Code)
ai_context/
  TOOLKIT.md             ← interactive documentation for users
  DEVELOPMENT_CONTEXT.md ← development context for maintainers
```

## Conventions

- **Don't edit skill files without backups.** Copy to `.bak` before modifying SKILL.md or any reference file.
- **Bump the version** in SKILL.md metadata for every change. Generated artifacts stamp this version.
- **Test changes** on at least 2 benchmark repos before committing.
- **Update ai_context/ files** if your change affects users or maintainers.
