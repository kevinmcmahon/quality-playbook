# AGENTS.md

The Quality Playbook is an AI coding skill that generates complete quality engineering infrastructure for any codebase: behavioral requirements derived from code intent, functional tests traced to those requirements, a three-pass code review protocol, and a multi-model spec audit.

## Repository layout

- `SKILL.md` — The skill itself. This is the primary product of this repository.
- `references/` — Protocol and pipeline reference documents used by the skill.
- `benchmark/` — The Quality Playbook Benchmark (QPB): 2,564 real defects from 50 repositories across 14 languages, used to validate and improve the skill.
  - `benchmark/dataset/` — The publishable dataset: master defect index, methodology, per-repo defect descriptions.
  - `benchmark/tooling/` — Python scripts for building and maintaining the dataset.
  - `benchmark/benchmarks/` — Cross-repo validation experiments.
  - `benchmark/experiments/` — Requirement validation experiments.
  - `benchmark/reviews/` — Bootstrap review results from running the skill on itself.
  - `benchmark/runs/` — Playbook run outputs against test repositories.
- `quality/` — Generated quality infrastructure from running the skill on this repo (bootstrap output).
- `repos/` — Cloned test repositories (gitignored, ~3.6GB).

## Key files

| File | Purpose |
|------|---------|
| `SKILL.md` | The skill — read this to understand what the playbook does and how to run it |
| `references/*.md` | Protocol references: constitution, functional tests, review protocols, spec audit, etc. |
| `benchmark/dataset/DEFECT_LIBRARY.md` | Master defect index — one row per defect with ID, title, fix SHA, severity, category |
| `benchmark/dataset/METHODOLOGY.md` | How defects were mined, constraints, format spec, known limitations |
| `benchmark/tooling/normalize_categories.py` | Maps raw mining categories to 14 canonical labels |
| `benchmark/tooling/assemble_v8.py` | Assembles DEFECT_LIBRARY.md from mining round outputs |
| `benchmark/tooling/extract_defect_data.py` | Extracts commit metadata and issue references from all repos |

## Installing the skill

Copy the skill into your AI coding tool's skill directory:

**Claude Code:**
```bash
mkdir -p .claude/skills/quality-playbook/references
cp SKILL.md .claude/skills/quality-playbook/SKILL.md
cp references/* .claude/skills/quality-playbook/references/
```

**GitHub Copilot:**
```bash
mkdir -p .github/skills/references
cp SKILL.md .github/skills/SKILL.md
cp references/* .github/skills/references/
```

Then tell your AI tool: *"Read the quality playbook skill and generate a complete quality system for this project."*

## Working with the benchmark dataset

### Evaluating a playbook

For each defect in `benchmark/dataset/DEFECT_LIBRARY.md`:

1. Look up the `pre_fix_commit` and `files_changed` in `benchmark/dataset/defects/<repo>/defects.md`
2. Check out the pre-fix commit: `cd repos/<repo> && git checkout <pre_fix_commit>`
3. Run the code review playbook against the listed files
4. Score using the rubric: direct hit, adjacent, or miss
5. The fix commit diff is the oracle: `git diff <pre_fix_commit>..<fix_commit>`

### Adding defects

1. Clone the repo into `repos/` if not already present
2. Scan `git log` for fix-related commits
3. Record: SHA, parent SHA, severity, category (one of 14 canonical), description, playbook angle
4. Add rows to `benchmark/dataset/DEFECT_LIBRARY.md`
5. Run `python3 benchmark/tooling/normalize_categories.py` to ensure category consistency

### 14 canonical defect categories

error handling, validation gap, configuration error, type safety, state machine gap, concurrency issue, serialization, API contract violation, protocol violation, null safety, silent failure, security issue, SQL error, missing boundary check

### Severity scale

- **Critical** — System-wide failure: authentication broken, deadlock, data corruption, unsafe defaults
- **High** — Feature broken or significantly degraded, common use case fails
- **Medium** — Edge case or specific scenario fails, workaround possible
- **Low** — Cosmetic, misleading message, minor UX issue

## Conventions

- Every defect is tied to a single fix commit (no merge commits, no multi-commit fixes)
- Pre-fix commit is always the immediate parent: `git rev-parse FIX_COMMIT^`
- Defect IDs use the format `PREFIX-NN` where PREFIX maps to a repository
- Category normalization uses keyword-based rules with ordered precedence (security first, validation gap as fallback)

## Current state

- Skill version: 1.3.7
- Benchmark: 2,564 defects across 55 prefixes (50 unique repositories), 14 languages
