# AGENTS.md

The Quality Playbook is an AI coding skill that generates complete quality engineering infrastructure for any codebase: behavioral requirements derived from code intent, functional tests traced to those requirements, a three-pass code review protocol, and a multi-model spec audit.

## Repository layout

- `SKILL.md` — The skill itself. This is the primary product of this repository.
- `references/` — Protocol and pipeline reference documents used by the skill.
- `quality/` — Generated quality infrastructure from running the skill on this repo (bootstrap output).

## Key files

| File | Purpose |
|------|---------|
| `SKILL.md` | The skill — read this to understand what the playbook does and how to run it |
| `references/constitution.md` | Quality constitution template and fitness-to-purpose scenarios |
| `references/functional_tests.md` | Test generation patterns, library version awareness, anti-hallucination guardrails |
| `references/review_protocols.md` | Three-pass code review protocol with regression test generation |
| `references/spec_audit.md` | Council of Three multi-model audit and triage protocol |
| `references/requirements_pipeline.md` | Five-phase requirements derivation pipeline |
| `references/requirements_refinement.md` | Requirements refinement and versioning protocol |
| `references/requirements_review.md` | Interactive requirements review guide |
| `references/schema_mapping.md` | Schema mapping between artifacts |
| `references/verification.md` | Verification and validation protocols |
| `references/defensive_patterns.md` | Defensive coding pattern detection |

## Installing the skill

Copy the skill into your AI coding tool's skill directory:

**Claude Code:**
```bash
mkdir -p .claude/skills/quality-playbook/references
cp SKILL.md .claude/skills/quality-playbook/SKILL.md
cp LICENSE.txt .claude/skills/quality-playbook/LICENSE.txt
cp references/* .claude/skills/quality-playbook/references/
```

**GitHub Copilot:**
```bash
mkdir -p .github/skills/references
cp SKILL.md .github/skills/SKILL.md
cp LICENSE.txt .github/skills/LICENSE.txt
cp references/* .github/skills/references/
```

Then tell your AI tool: *"Read the quality playbook skill and generate a complete quality system for this project."*

## Validation

The skill is validated against the [Quality Playbook Benchmark](https://github.com/andrewstellman/quality-playbook-benchmark): 2,564 real defects from 50 open-source repositories across 14 languages.

## Current state

- Skill version: 1.3.8
