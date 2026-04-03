# anthropics/skills Defects — Quality Playbook Benchmark (QPB)

**Repository**: [anthropics/skills](https://github.com/anthropics/skills)
**Language**: Python, Markdown (AI skill definitions with Python tooling scripts)
**Repo type**: Skill Framework / Registry
**Defect count**: 7 (AS-01 through AS-07; initial catalog)
**Generated**: 2026-03-31

This is a hybrid repo: it contains both skill definition files (SKILL.md) and Python tooling scripts (validators, evaluators, converters). Some defects are in the skill definitions themselves, others in the Python infrastructure that manages skills.

**Note on fix status**: Only AS-01 has a merged fix commit. AS-02 through AS-07 have open PRs or documented issues with proposed fixes. These defects exist at the current HEAD and can be evaluated against the pre-fix code. The QPB entries below document the defect and its proposed fix; they will be updated with final fix commit SHAs when the PRs merge.

---

## AS-01 | Description Optimizer Crashes Without ANTHROPIC_API_KEY | configuration error | High

**Fix commit**: [`b0cbd3d`](https://github.com/anthropics/skills/commit/b0cbd3d)
**Pre-fix commit**: `b0cbd3d~1`
**Issue/PR**: [#532](https://github.com/anthropics/skills/issues/532) → [PR #547](https://github.com/anthropics/skills/pull/547)

**Files changed**:
- `skills/skill-creator/SKILL.md`
- `skills/skill-creator/scripts/improve_description.py`

**Commit message**:
```
skill-creator: drop ANTHROPIC_API_KEY requirement from description optimizer (#547)

improve_description.py now calls `claude -p`
as a subprocess instead of the Anthropic SDK, so users no longer need a
separate ANTHROPIC_API_KEY to run the description optimization loop. Same
auth pattern run_eval.py already used for the triggering eval.
```

**Defect summary**: The skill-creator's description optimization workflow used `anthropic.Anthropic()` directly, which requires `ANTHROPIC_API_KEY` environment variable. The majority of Claude Code users authenticate via enterprise SSO or managed licenses and don't have a raw API key. The optimizer would crash immediately with an authentication error for these users. Additionally, `run_eval.py` aggressively stripped `CLAUDECODE` env var, and real skills in `.claude/skills/` competed with temporary eval commands, causing false-negative trigger rates.

**Diff stat**:
```
skills/skill-creator/SKILL.md                      |  10 +-
skills/skill-creator/scripts/improve_description.py | 103 ++++++++++-----------
 2 files changed, ~60 insertions(+), ~50 deletions(-)
```

**Playbook angle**: Step 5c (parallel code paths) — `run_eval.py` already used `claude -p` subprocess pattern, but `improve_description.py` used the SDK directly. Inconsistent auth patterns across files in the same tool. Step 4 (specifications) — the skill advertised description optimization but silently required credentials most users don't have.

---

## AS-02 | Binary PDF Breaks JSON Serialization (API 400 for All Users) | serialization | Critical

**Fix commit**: Pending ([PR #510](https://github.com/anthropics/skills/pull/510), open)
**Issue**: [#462](https://github.com/anthropics/skills/issues/462)

**Files affected**:
- `skills/theme-factory/theme-showcase.pdf` (124KB binary)
- `skills/theme-factory/SKILL.md`

**Defect summary**: The theme-factory skill included a binary PDF file (`theme-showcase.pdf`) containing 9 unpaired UTF-16 high surrogate byte sequences. When Claude Code loads the plugin, it reads all files including this PDF, treats it as text, and includes it in the JSON request body. The unpaired surrogates make the JSON invalid, causing a `400 invalid_request_error` that blocks all user sessions. Every user who enables the document-skills plugin encounters this error.

**Proposed fix**: Remove the binary PDF and update SKILL.md to reference theme markdown files instead.

**Playbook angle**: Step 5d (generated/invisible code) — binary files in a text-oriented skill directory are invisible landmines. Step 6 (domain knowledge) — UTF-16 surrogate handling is a known serialization failure mode.

---

## AS-03 | TodoWrite Overwrites Phase Todos, Silently Skipping Quality Review | state machine gap | High

**Fix commit**: Pending ([PR #363](https://github.com/anthropics/skills/pull/363), open)
**Issue**: [#266](https://github.com/anthropics/skills/issues/266)

**Files affected**:
- `/feature-dev` workflow skill (SKILL.md)

**Defect summary**: The `/feature-dev` command's 7-phase workflow creates a todo list in Phase 1 tracking all phases. In Phase 5 (Implementation), the workflow updates task-level todos — but since TodoWrite replaces the entire list on each call, this overwrites and deletes the phase-level todos for Phases 6 and 7. Phase 6 (Quality Review, with code-reviewer agents) is **always skipped**, and Phase 7 is also lost. The workflow silently terminates after Phase 5, never reaching the quality review that is one of its key features.

**Proposed fix**: Use `[PHASE]` and `[TASK]` prefixes, add checkpoint after Phase 5, remove TodoWrite from agent tool lists.

**Playbook angle**: Step 5a (state machines) — the todo list is a state machine, and wholesale replacement loses state. Step 5 (defensive patterns) — when updating a subset of a data structure, verify the rest is preserved.

---

## AS-04 | Generated SKILL.md Template Fails Immediate Validation (YAML List Parse) | serialization | Medium

**Fix commit**: Pending ([PR #261](https://github.com/anthropics/skills/pull/261), open)
**Issue**: [#239](https://github.com/anthropics/skills/issues/239)

**Files affected**:
- `skills/skill-creator/scripts/init_skill.py`

**Defect summary**: The `init_skill.py` template generates a description field as `description: [TODO: Complete and informative explanation...]`. YAML parses the unquoted square brackets as a list and the colon as a key-value pair, producing `{'description': [{'TODO': 'Complete...'}]}` instead of a string. The `quick_validate.py` validator then rejects it with "Description must be a string, got list." Freshly generated skills fail validation immediately — the official generate→validate→package workflow is broken out of the box.

**Proposed fix**: Quote the description value in the template: `description: "TODO: Complete..."`.

**Playbook angle**: Step 5d (generated code) — templates that produce invalid output. Step 4 (specifications) — YAML special characters in unquoted strings are a known gotcha.

---

## AS-05 | Inconsistent Skill Name Length Limit (40 vs 64 Characters) | validation gap | Low

**Fix commit**: Pending ([PR #200](https://github.com/anthropics/skills/pull/200), open)
**Issue**: [#199](https://github.com/anthropics/skills/issues/199)

**Files affected**:
- `skills/skill-creator/scripts/init_skill.py` (line 279)
- `skills/skill-creator/scripts/quick_validate.py` (line 70)

**Defect summary**: `init_skill.py` displays "Max 40 characters" in its help text, but `quick_validate.py` validates against a 64-character limit (matching the official Agent Skills Specification). Users creating skills with names between 41-64 characters would either: (a) self-censor based on the help text, or (b) succeed at creation but be confused by the contradictory documentation.

**Proposed fix**: Update `init_skill.py` help text to "Max 64 characters".

**Playbook angle**: Step 5c (parallel code paths) — two validators for the same field with different limits. Step 4 (specifications) — constants should be derived from a single source of truth.

---

## AS-06 | Plugin Marketplace Installs 16 Extra Unintended Skills | configuration error | High

**Fix commit**: Pending ([PR #208](https://github.com/anthropics/skills/pull/208), approved but open)
**Issue**: [#206](https://github.com/anthropics/skills/issues/206)

**Files affected**:
- `marketplace.json`

**Defect summary**: The `marketplace.json` plugin configuration uses `"source": "./"` (repo root) for the document-skills plugin. The installer's auto-discovery scans the entire source directory for skills, ignoring the explicit `skills` array. Result: instead of installing 4 specified skills (xlsx, docx, pptx, pdf), it installs 16 skills including unrelated ones like `algorithmic-art`, `slack-gif-creator`, and `canvas-design`. Users get unexpected skills that may conflict or consume resources.

**Proposed fix**: Change source path from `"./"` to `"./skills"` and adjust skill paths accordingly.

**Playbook angle**: Step 5 (defensive patterns) — broad directory scopes override explicit lists. Step 6 (domain knowledge) — auto-discovery patterns that ignore explicit configuration.

---

## AS-07 | Zip Slip Path Traversal in 15 OOXML Processing Calls | security issue | Critical

**Fix commit**: Pending ([PR #542](https://github.com/anthropics/skills/pull/542), open)
**Issue**: [#540](https://github.com/anthropics/skills/issues/540)

**Files affected**:
- `skills/docx/` (unpack, validate, validators modules)
- `skills/pptx/` (unpack, validate, validators modules)
- `skills/xlsx/` (unpack, validate, validators modules)

**Defect summary**: 15 instances of `zipfile.extractall()` across the docx, pptx, and xlsx skills extract Office document contents without validating archive entry paths. A maliciously crafted Office document could include entries with path traversal sequences (e.g., `../../etc/cron.d/malicious`) that write files outside the intended extraction directory (CWE-22: Zip Slip). Since these skills process user-uploaded documents, the attack surface is direct.

**Proposed fix**: Replace all `extractall()` calls with `_safe_extractall()` helper that validates every member path stays within the target directory.

**Playbook angle**: Step 5 (defensive patterns) — archive extraction without path validation. Step 6 (domain knowledge) — Zip Slip is a well-known vulnerability class (CWE-22).

---

## Summary

| ID | Title | Category | Severity | Fix Status |
|----|-------|----------|----------|------------|
| AS-01 | Description optimizer crashes without API key | configuration error | High | Merged (b0cbd3d) |
| AS-02 | Binary PDF breaks JSON serialization | serialization | Critical | PR #510 (open) |
| AS-03 | TodoWrite overwrites phase todos | state machine gap | High | PR #363 (open) |
| AS-04 | Generated template fails YAML validation | serialization | Medium | PR #261 (open) |
| AS-05 | Inconsistent name length limit | validation gap | Low | PR #200 (open) |
| AS-06 | Plugin marketplace installs extra skills | configuration error | High | PR #208 (approved) |
| AS-07 | Zip Slip path traversal (15 instances) | security issue | Critical | PR #542 (open) |

**Category distribution**: configuration error (2), serialization (2), security issue (1), state machine gap (1), validation gap (1)
**Severity distribution**: Critical (2), High (3), Medium (1), Low (1)
**Fix status**: 1 merged, 1 approved, 5 open PRs

**Note**: AS-02 through AS-07 have documented defects at current HEAD with proposed fixes in open PRs. These can be evaluated against the pre-fix code immediately. QPB entries will be updated with fix commit SHAs when PRs merge. For scored evaluation, use the pre-fix code (current HEAD for unmerged, `b0cbd3d~1` for AS-01).
