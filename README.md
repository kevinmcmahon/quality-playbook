# Quality Playbook Benchmark (QPB)

A curated dataset of **2,564 real defects** from **50 open-source repositories** across **14 programming languages**, designed to measure and improve the detection rate of AI-assisted code review playbooks.

This is mutation testing applied one level up: instead of injecting synthetic faults into code, we use real historical bugs as ground truth. Each defect is tied to a single fix commit, so checking out the parent commit gives you the exact code with the exact bug, and the fix commit diff serves as the oracle.

## Quick start

Pick a defect from `dataset/DEFECT_LIBRARY.md`, check out its `pre_fix_commit`, run your code review tool against the affected files, and score whether the review identifies the bug. The `fix_commit` diff tells you exactly what was wrong.

```bash
# Example: CURL-01, use-after-free in transfer URL pointer
cd repos/curl
git checkout 28fbf4a8          # pre-fix commit
# Run your code review against lib/transfer.c
# Then compare your findings to the fix:
git diff 28fbf4a8..86b39c2     # shows the actual fix
```

## What's in the dataset

Each defect has: a fix commit SHA, the pre-fix parent commit, severity, one of 14 canonical defect categories, a description derived from the actual git diff, the original GitHub issue/PR text (when available), the complete list of files changed, and a suggested detection angle for code review playbooks.

### Languages

Go, Python, TypeScript, Java, C, C#, Rust, Ruby, PHP, Kotlin, Scala, JavaScript, Swift, Elixir

### Defect categories

error handling (621), validation gap (359), configuration error (284), type safety (231), state machine gap (217), concurrency issue (130), serialization (121), API contract violation (117), protocol violation (106), null safety (103), silent failure (89), security issue (83), SQL error (68), missing boundary check (35)

### Repository types

Libraries, frameworks, applications, and infrastructure projects — ranging from curl and redis to Rails and Kafka.

## Directory structure

```
QPB/
├── dataset/                    # The publishable dataset
│   ├── DEFECT_LIBRARY.md       # Master index (2,564 defects, one row each)
│   ├── METHODOLOGY.md          # How the dataset was built
│   ├── DETECTION_RESULTS.md    # Scoring results schema
│   ├── COUNCIL_REVIEW_PROMPT.md # Cross-model verification prompt
│   └── defects/                # Per-repo detailed descriptions
│       ├── cli/defects.md      # cli/cli (Go) — 71 defects
│       ├── curl/defects.md     # curl/curl (C) — 49 defects
│       └── ...                 # One directory per repository
├── tooling/                    # Scripts used to build the dataset
│   ├── extract_defect_data.py  # Extracts commit msgs, files, diffs from repos
│   ├── normalize_categories.py # Maps raw categories to 14 canonical labels
│   ├── assemble_v8.py          # Assembles DEFECT_LIBRARY.md from mining output
│   └── generate_sample.py      # Generates per-repo description files
├── repos/                      # Cloned repositories (gitignored, ~3.6GB)
└── .gitignore
```

## Scoring rubric

When evaluating a code review tool against the QPB:

- **Direct hit** — The review names the specific bug or its root cause
- **Adjacent** — The review flags the affected area or a related concern but doesn't identify the specific bug
- **Miss** — The review doesn't mention the bug or the affected code area

## Context

This dataset supports an O'Reilly Radar article series on AI-assisted code quality. Article 6 ("testing the test") uses the QPB to measure playbook detection rates and drive iterative improvement: run the playbook, score the misses, update the playbook, re-run, repeat until detection rate plateaus.

## License

The defect metadata (descriptions, categories, severity ratings, playbook angles) is original work. The fix commit SHAs and file paths reference public open-source repositories under their respective licenses. The cloned repositories in `repos/` retain their original licenses.
