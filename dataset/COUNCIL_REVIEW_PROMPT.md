# Council of Three Review (Round 2) — Quality Playbook Benchmark (QPB)

This is a follow-up review. In Round 1, two reviewers identified issues with schema consistency, hardcoded tooling paths, overstated documentation, missing categories in DETECTION_RESULTS.md, and lack of a machine-readable export. Changes have been made to address all findings. Your job is to verify whether the issues were fixed, identify any remaining problems, and assess readiness to proceed with generating the full dataset.

## Scope of this review

Read and evaluate all the documentation and sample files listed below. For spot-checking, you have access to one full repository clone: **curl/curl** in `repos/curl/`. Use it to verify claims by examining actual commits, diffs, and history. Do **not** crawl into the other 50 repos — they're present on disk but are out of scope for this review.

## Files to read (in order)

1. **`README.md`** (repo root) — Public-facing overview for humans
2. **`AGENTS.md`** (repo root) — AI-facing reference with conventions, workflows, current state
3. **`PROJECT_PLAN.md`** (repo root) — Full roadmap: dataset completion, playbook improvement loop, cross-model comparison, publication
4. **`dataset/METHODOLOGY.md`** — How defects were mined, constraints, format spec, issue text reuse policy, known limitations
5. **`dataset/DEFECT_LIBRARY.md`** — Master index of all 2,564 defects (skim the structure, read the header material, sample a few dozen rows across different prefixes)
6. **`dataset/defects.jsonl`** — Machine-readable export (one JSON object per line, verify it matches DEFECT_LIBRARY.md)
7. **`dataset/DETECTION_RESULTS.md`** — Scoring results schema
8. **`dataset/defects/curl/defects.md`** — Per-repo description file for curl/curl (5 of 49 entries, format sample)
9. **`dataset/defects/cli/defects.md`** — Per-repo description file for cli/cli (20 of 71 entries, older format with note about adoption of newer format)
10. **`tooling/extract_defect_data.py`** — Script that extracts commit messages, files, diffs from repos
11. **`tooling/normalize_categories.py`** — Category normalization script

## Round 1 findings to verify

The following issues were identified in Round 1. Please verify whether each has been adequately addressed:

### From Cursor/GPT-5.4:
1. **Schema inconsistency in DEFECT_LIBRARY.md** — Early sections used markdown-linked issue numbers in the title column; severity casing varied (high/High). *Fix applied: stripped markdown links from titles, normalized all severity to Title Case.*
2. **Docs overstate completeness** — METHODOLOGY.md implied all repos had defects.md files; curl sample header said "Defect count: 49" but only had 5 entries. *Fix applied: updated language to say "samples", fixed headers.*
3. **Hardcoded paths in tooling** — Scripts used `/sessions/...` absolute paths. *Fix applied: converted to relative paths with CLI argument overrides.*
4. **DETECTION_RESULTS.md missing serialization category** — Category table had 13 of 14 categories; used `concurrency` instead of `concurrency issue`. *Fix applied: added serialization, fixed label.*
5. **No machine-readable export** — Markdown alone is awkward for benchmarking. *Fix applied: added dataset/defects.jsonl.*
6. **Legal concern about issue text reuse** — *Fix applied: added issue text reuse policy in METHODOLOGY.md (summarize in own words, link to original, no verbatim reproduction).*

### From Copilot/Gemini 2.5 Pro:
7. **Hardcoded paths in tooling** — Same as #3 above.
8. **Adopt newer curl format for all repos** — *Acknowledged in cli/defects.md header; will be applied when generating remaining files.*

## Spot-check instructions (curl/curl only)

For at least 3 of the 5 CURL defects in `dataset/defects/curl/defects.md`, verify the following against the actual repo in `repos/curl/`:

```bash
cd repos/curl

# 1. Confirm the fix commit exists and its parent matches pre_fix_commit
git log --oneline CURL_FIX_SHA -1
git rev-parse CURL_FIX_SHA^    # should match pre_fix_commit

# 2. Confirm the files changed match
git diff-tree --no-commit-id --name-only -r CURL_FIX_SHA

# 3. Read the actual diff and verify the defect description is accurate
git diff CURL_PRE_FIX_SHA..CURL_FIX_SHA

# 4. Confirm the commit message matches
git log --format="%B" CURL_FIX_SHA -1
```

Also: pick 5 random entries from `dataset/defects.jsonl` and verify they match the corresponding rows in `dataset/DEFECT_LIBRARY.md`.

## Review areas

### 1. Round 1 fix verification
- For each of the 8 findings above, is the fix adequate?
- Are there any issues that were only partially addressed?

### 2. New content review
- **PROJECT_PLAN.md** — Is the roadmap realistic? Are the phases well-ordered? Is the cross-model comparison methodology sound? Anything missing?
- **dataset/defects.jsonl** — Does the schema match the documented format? Any fields missing?
- **Issue text reuse policy** — Is the policy clear and sufficient for publication?

### 3. Remaining review areas (same as Round 1)
- Methodology soundness (single-commit constraint, mining approach, categories, severity)
- Dataset format and completeness
- Sample data quality (curl and cli)
- Scoring rubric (now includes not-evaluable and false-positive tracking)
- Tooling review (now with relative paths and CLI arguments)
- Publication readiness

## Deliverable

Please provide:

1. **Overall assessment**: Sound / Needs revision / Fundamentally flawed
2. **Round 1 fix verification**: For each of the 8 findings, Resolved / Partially resolved / Not resolved
3. **Spot-check results**: For each CURL defect verified, pass/fail. For JSONL cross-check, pass/fail.
4. **New content feedback**: Specific feedback on PROJECT_PLAN.md, defects.jsonl, and issue text reuse policy
5. **Remaining issues**: Anything still needing attention before generating the full 2,500 entries
6. **Recommended next steps**: What should we do first?
