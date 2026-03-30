# AGENTS.md

The Quality Playbook Benchmark (QPB) is a curated dataset of 2,564 real defects from 50 open-source repositories across 14 programming languages. It measures and improves the detection rate of AI-assisted code review playbooks by providing ground truth: known bugs at known commits with known fixes.

## Repository layout

- `dataset/` — The publishable dataset. Contains the master defect index (`DEFECT_LIBRARY.md`), methodology documentation, scoring schema, and per-repo detailed defect descriptions in `defects/<repo>/defects.md`.
- `tooling/` — Python scripts used to build and maintain the dataset. These read from the cloned repos in `repos/` and produce the files in `dataset/`.
- `repos/` — 51 cloned open-source repositories used for defect mining. Gitignored (~3.6GB). Required for running tooling scripts and for checking out pre-fix commits during playbook evaluation.

## Key files

| File | Purpose |
|------|---------|
| `dataset/DEFECT_LIBRARY.md` | Master index — one row per defect with ID, title, fix SHA, pre-fix SHA, severity, category, description, playbook angle |
| `dataset/METHODOLOGY.md` | How defects were mined, constraints, format spec, known limitations |
| `dataset/DETECTION_RESULTS.md` | Schema for recording playbook evaluation scores |
| `dataset/defects/<repo>/defects.md` | Detailed per-defect descriptions including commit message, files changed, original issue text, diff stat |
| `tooling/extract_defect_data.py` | Extracts commit messages, file lists, diff stats, and issue references from all repos |
| `tooling/normalize_categories.py` | Maps raw mining categories to 14 canonical labels |
| `tooling/assemble_v8.py` | Assembles DEFECT_LIBRARY.md from mining round outputs |
| `tooling/defect_data.json` | Cached extraction output (gitignored, regenerable) |

## Working with the dataset

### Regenerating extracted data

If `tooling/defect_data.json` is missing, regenerate it:

```bash
cd /path/to/QPB
python3 tooling/extract_defect_data.py
```

This reads every fix commit from every repo in `repos/` and extracts commit messages, file lists, diff stats, and issue references. Takes ~2 minutes for 2,564 defects.

### Evaluating a playbook

For each defect in `dataset/DEFECT_LIBRARY.md`:

1. Look up the `pre_fix_commit` and `files_changed` in the corresponding `dataset/defects/<repo>/defects.md`
2. Check out the pre-fix commit in the appropriate repo: `cd repos/<repo> && git checkout <pre_fix_commit>`
3. Run the code review playbook against the listed files
4. Score using the rubric: direct hit, adjacent, or miss
5. The fix commit diff is the oracle: `git diff <pre_fix_commit>..<fix_commit>`

### Adding defects

To mine additional defects from a repo:

1. Clone the repo into `repos/` if not already present
2. Scan `git log` for fix-related commits (keywords: fix, bug, patch, resolve, correct, handle, prevent, avoid)
3. For each fix commit, record: SHA, parent SHA, severity, category (one of 14 canonical), description, playbook angle
4. Add rows to `dataset/DEFECT_LIBRARY.md` following the existing format
5. Run `python3 tooling/normalize_categories.py` to ensure category consistency
6. Generate the per-repo description file in `dataset/defects/<repo>/defects.md`

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
- Defect IDs use the format `PREFIX-NN` where PREFIX maps to a repository (e.g., GH = cli/cli, CURL = curl/curl, RLS = rails/rails)
- The DEFECT_LIBRARY.md table has 8 columns separated by `|`: ID, title, fix_commit, pre_fix_commit, severity, category, description, playbook_angle
- Category normalization uses keyword-based rules with ordered precedence (security first, validation gap as fallback)

## Current state

- 2,564 defects across 55 prefixes (50 unique repositories, 5 original-round prefixes retained)
- Per-repo description files generated for cli/cli (20 of 71 entries) and curl/curl (5 of 49 entries) as format samples
- Remaining 48 repos need per-repo description files generated
- Council of three review pending (see `dataset/COUNCIL_REVIEW_PROMPT.md`)
- Iterative playbook improvement loop planned but not yet started
