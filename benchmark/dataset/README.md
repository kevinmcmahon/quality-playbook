# Quality Playbook Benchmark (QPB)

A curated dataset of 2,564 real defects from 50 open-source repositories across 14 languages, used to measure and improve the detection rate of AI-assisted code review playbooks.

## Structure

- `DEFECT_LIBRARY.md` — Master index with all QPB entries (summary table format)
- `defects/<repo>/defects.md` — Per-repo detailed defect descriptions with:
  - Full defect context (what was wrong, what files were affected)
  - Fix description (what the fix changed and why)
  - Files changed (the specific files modified by the fix commit)
  - Verification info (commit SHAs, issue references)
  - Category and severity justification

## How to Use

### For playbook evaluation (Phase 3)
1. Check out `pre_fix_commit` for a given defect
2. Run your code review playbook against the files listed in `files_changed`
3. Score: **Direct hit** (names the bug), **Adjacent** (flags the area), **Miss** (doesn't mention it)
4. The `fix_commit` diff is the ground truth oracle

### For council-of-three review
Point each reviewer at the per-repo `defects.md` file. Each description is self-contained — no git access needed to verify category, severity, and description accuracy.

## Dataset Statistics

- **2,564** total defects
- **50** repositories (55 prefixes including 5 original projects)
- **14** languages: Java, Python, Go, TypeScript, Rust, Scala, C#, JavaScript, Ruby, PHP, Kotlin, C, Swift, Elixir
- **4** repo types: Library, Framework, Application, Infrastructure
- **14** defect categories: error handling, validation gap, configuration error, type safety, state machine gap, concurrency issue, serialization, API contract violation, protocol violation, null safety, silent failure, security issue, SQL error, missing boundary check
