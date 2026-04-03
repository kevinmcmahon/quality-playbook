# Quality Playbook Benchmark (QPB) — Methodology

## Purpose

The QPB is a curated dataset of 2,564 real defects from 50 open-source repositories across 14 programming languages. Its purpose is to iteratively improve the quality playbook skill by testing it against real historical bugs: if the playbook can't guide an agent to find a bug that actually existed and was actually fixed, that's a real miss worth learning from.

**Research question**: Does iterative, evidence-driven improvement of a structured code review playbook improve its bug detection rate on unseen codebases, as measured by a before/after comparison on held-out repositories?

This is mutation testing applied one level up — instead of injecting synthetic faults into code, we use real historical bugs as the oracle.

## Dataset Composition

- **2,592 defects** across **55 repositories** (60 prefixes including 5 original projects)
- **15 languages**: Java, Python, Go, TypeScript, Rust, Scala, C#, JavaScript, Ruby, PHP, Kotlin, C, Swift, Elixir, Markdown (AI skill/agent definitions)
- **5 repo types**: Library, Framework, Application, Infrastructure, Skill/Agent Registry
- **14 defect categories**: error handling, validation gap, configuration error, type safety, state machine gap, concurrency issue, serialization, API contract violation, protocol violation, null safety, silent failure, security issue, SQL error, missing boundary check

### New Code Repositories (2026-03-31)

One traditional code repository was added:

- **modelcontextprotocol/servers** — 8 defects (MCP-01 through MCP-08). TypeScript and Python MCP tool server implementations (filesystem, git, memory, fetch, sequential-thinking). These are standard code defects in the tool infrastructure that AI agents use, not skill/agent definitions. Defect categories: security issue (1), type safety (2), error handling (2), missing boundary check (1), silent failure (1), configuration error (1).

### Skill/Agent Extension (2026-03-31)

Three skill/agent repositories were added to test whether the playbook generalizes beyond traditional source code to AI instruction documents:

- **github/awesome-copilot** — 10 defects (AC-01 through AC-10). Skill and agent definition files (.md with YAML frontmatter, embedded scripts). Defect categories: API contract violation (4), configuration error (3), validation gap (2), missing boundary check (1).
- **anthropics/skills** — 7 defects (AS-01 through AS-07). Skill framework with Python tooling scripts. 1 merged fix, 6 with open PRs documenting confirmed defects at HEAD. Defect categories: configuration error (2), serialization (2), security issue (1), state machine gap (1), validation gap (1).
- **sickn33/antigravity-awesome-skills** — 3 defects (AG-01 through AG-03). Security-focused fixes in skill tooling scripts (config data exposure, pipe-to-shell patterns, CI injection). Defect categories: security issue (3).

These 20 skill/agent defects across 3 repos expand the QPB into a new artifact class (Markdown-based AI skills and agents with their supporting scripts), testing whether structured review principles transfer from code to instruction documents.

## How Defects Were Mined

For each repository:

1. **Clone the repo** with full history
2. **Scan git log** for commits whose messages indicate bug fixes (keywords: fix, bug, patch, resolve, repair, correct, handle, prevent, avoid, etc.)
3. **Examine the diff** of each fix commit to understand what was wrong in the pre-fix code
4. **Record**: fix commit SHA, pre-fix commit SHA (parent of fix), severity, category, one-line description, playbook detection angle
5. **Verify**: confirm the fix commit exists and the parent commit is its immediate ancestor (`git rev-parse FIX_COMMIT^`)

### Defect Inclusion Criteria

Every defect in the QPB dataset must satisfy **all** of the following criteria. These are the formal rules for "QPB-worthiness."

**Structural requirements** (must have):

1. **Single fix commit.** The defect is tied to exactly one commit whose diff is the ground truth oracle. Checking out the parent gives you the exact code with the exact bug.
2. **Single parent.** Fix commits with multiple parents (merges) are excluded so the pre-fix state is unambiguous.
3. **Reviewable scope.** The fix touches files that a code reviewer could plausibly examine — source code, configuration, schemas, skill/agent definitions, templates. The defect must be discoverable by reading the pre-fix files, not only by running the system.
4. **Canonical category.** The defect maps to one of the 14 canonical categories (see Dataset Composition above). If a defect doesn't fit any category, either propose a new category with justification or exclude the defect.

**Substantiveness requirements** (the defect must be real and non-trivial):

5. **Behavioral impact.** The defect caused (or would cause) incorrect behavior, data loss, security vulnerability, silent failure, or user-facing error. Cosmetic issues (typos in comments, whitespace, formatting) are excluded.
6. **Non-trivial fix.** The fix involves a logic change, not just a rename, reformatting, or dependency version bump. A useful heuristic: if the fix diff contains only string literal changes with no control flow or structural impact, it's probably too trivial. Exception: string changes that fix API field names, GraphQL queries, file paths, or tool references that cause functional failures *are* substantive.
7. **Independent defect.** Each defect entry represents one logical bug. If a single commit fixes multiple independent bugs, split them into separate entries (each referencing the same commit but scoping to different files/hunks). If the bugs are entangled, keep as one entry.

**Documentation requirements** (the entry must be useful):

8. **Defect description explains what was wrong.** Not just "fixed X" — the entry must describe the incorrect behavior in the pre-fix code clearly enough that a reviewer reading only the description could understand the bug.
9. **Playbook angle identifies a detection strategy.** Each entry must suggest which playbook step(s) could catch this class of bug, framed as a general principle rather than a codebase-specific check.
10. **Severity is justified.** High/Medium/Low with a rationale tied to impact (data loss = High, silent incorrect output = High, edge case with workaround = Medium, minor UX degradation = Low).

**Exclusion criteria** (must not have any of these):

- **Pure documentation fixes** — README typos, comment corrections, changelog updates with no code change
- **Dependency bumps** — version updates in package managers unless the bump fixes a bug *in the project's own code*
- **CI/CD configuration** — workflow file changes, build script tweaks (unless the build defect caused incorrect artifacts)
- **Test-only fixes** — changes that only fix test code without a corresponding production defect (test refactors, flaky test fixes)
- **Spelling/grammar corrections** — in code comments, error messages, or documentation (unless the misspelling caused a functional failure, e.g., a misspelled enum value)

### Special Considerations for Skill/Agent Defects

Skills and agents (Markdown-based AI instruction documents) are eligible for QPB if they meet the above criteria with these adaptations:

- **"Source code" includes SKILL.md, agent.md, and supporting files** (reference docs, scripts, templates). These are the reviewable artifacts.
- **Behavioral impact for skills** means: the skill would produce incorrect output, reference non-existent tools/APIs, give fabricated instructions, fail to trigger on intended queries, or silently skip edge cases.
- **Common qualifying defect types for skills**: incorrect API/tool references, fabricated commands or installation instructions, missing edge case handling, broken handoff JSON schemas, incorrect GraphQL/REST field names in reference docs, missing tool declarations in frontmatter.
- **Common non-qualifying changes for skills**: description rewording for better trigger matching (unless the old description caused functional misfires), adding new features or sections, reorganizing content without fixing a bug.

### Constraints

- **Categories are normalized to exactly 14 canonical labels.** Raw category strings from mining were mapped to canonical categories using keyword-based rules (see `normalize_categories.py`). As the dataset expands to skills/agents, new categories may be proposed through the standard process (document rationale, update normalization rules, re-run categorization).

---

## Repository Split

The 50 repositories are divided into two groups before any evaluation begins:

### Improvement Repos (~30)

These repos are used for the iterative improvement process. The playbook is tested against their QPB defects, misses are analyzed, and playbook changes are proposed and validated. The playbook accumulates improvements as you work through these repos.

### Held-Out Repos (~20)

These repos are untouched during the improvement process. After all improvement iterations are complete, the held-out repos provide clean before/after evidence: run the original playbook (v1.2.0) against their defects, then run the final improved playbook against the same defects. The difference measures whether the improvements generalize to unseen codebases.

### Split Criteria

The held-out set must be stratified to cover the same spread as the improvement set:

- At least 2 repos per language (where the dataset has 2+ repos in that language)
- At least 1 repo per project type (Library, Framework, Application, Infrastructure)
- Proportional representation of defect categories (the held-out repos' combined defect categories should approximate the full dataset distribution)

Record the split and the rationale. The split is fixed before any improvement work begins and must not be changed based on results.

---

## Improvement Protocol

This is the core workflow for iteratively improving the playbook using QPB defects. Work through the improvement repos one at a time, accumulating playbook changes. The goal is to hill-climb the playbook's quality by exposing it to a diverse set of real-world failure modes — searching for general principles that improve detection, not overfitting to specific bugs.

### Step 1: Generate Quality Infrastructure

For each improvement repo, use the playbook to generate quality infrastructure at the HEAD of the repo. This is the normal playbook workflow — the same thing a user would do when installing the playbook on a new project.

```
cd repos/<repo>
git checkout HEAD    # or the default branch
```

Give the agent the playbook and ask it to generate the quality infrastructure. The agent runs the playbook's exploration and generation steps (Steps 0–6 from SKILL.md), producing:

- `quality/QUALITY.md` — quality constitution
- `quality/test_functional.py` — spec-traced functional tests
- `quality/RUN_CODE_REVIEW.md` — code review protocol
- `quality/RUN_INTEGRATION_TESTS.md` — integration test protocol
- `quality/RUN_SPEC_AUDIT.md` — spec audit protocol
- `AGENTS.md` — AI bootstrap file

These files go into the repo's `quality/` folder (or whatever the playbook generates). This is the quality infrastructure that will be used for all subsequent defect reviews in this repo.

**Why generate at HEAD, not at each pre-fix commit?** This is a deliberate design choice for two reasons:

1. **Cost**: Generating quality infrastructure is token-intensive (the playbook's Steps 0–6 involve deep codebase exploration, architecture analysis, and multi-file generation). Regenerating per defect would multiply cost by the number of defects per repo — prohibitively expensive for a 2,564-defect dataset.
2. **Consistency**: Generating once per repo means every defect in that repo is reviewed against the same quality infrastructure. If quality infrastructure varied per commit, differences in detection would reflect both playbook quality *and* quality-infrastructure quality, muddying the comparison. A single set of quality artifacts per repo isolates the playbook as the variable under study.

The tradeoff is that HEAD-generated artifacts may encode post-fix knowledge (see Threats to Validity). This means the evaluation measures *retrospective defect review using modern repository context*, not historically pure pre-fix review. This framing is accurate to how the playbook is actually deployed: a user generates quality infrastructure on their current codebase, then uses it to review code. The before/after comparison controls for this because both playbook versions see the same HEAD-generated artifacts for the same repo, so any HEAD contamination is a constant, not a confound.

**Optional ablation**: To measure the magnitude of HEAD contamination, run a small subset of defects (e.g., 5–10 per language) with quality infrastructure generated at the `pre_fix_commit` instead of HEAD. Compare detection rates between HEAD-generated and pre-fix-generated infrastructure. This quantifies the tradeoff rather than merely arguing for it.

### Step 2: Review Pre-Fix Code

For each QPB defect in this repo, rewind to the commit before the bug was fixed and run a code review using the quality infrastructure.

```
cd repos/<repo>
git checkout <pre_fix_commit>

# The quality/ folder from Step 1 is still present (it's untracked, so git checkout doesn't remove it)
```

Give the agent this prompt:

> "Use the quality infrastructure files in the quality/ folder to review the following files: [list of files from git diff-tree --no-commit-id --name-only -r <fix_commit>]"

**What the agent receives**:
- The quality infrastructure from Step 1 (quality constitution, review protocol, functional tests, etc.)
- The file paths to review
- Access to the full repository at the `pre_fix_commit`

**What the agent does NOT receive**:
- The defect ID, title, or description
- The fix commit SHA or diff
- The defect category or severity
- Any hint that there is a known bug in these files

**Crucially, this is a blind review.** The agent has no knowledge of the defect. It believes it is doing a routine code review using the project's quality infrastructure. This is a cornerstone of the protocol's validity — the agent must find the bug through the playbook's guidance alone, not from any hint about what to look for.

### Step 3: Score the Review

Compare the agent's findings against the oracle (fix commit diff) using the scoring rubric (see Scoring Rubric below). Record the score for each defect.

### Step 4: Analyze Misses

For each miss, examine:
- The oracle (what the fix actually changed)
- The agent's findings (what it actually said)
- The quality infrastructure (what guidance was available)

Identify the class of bug the playbook failed to guide the agent toward. Ask: what general principle, if added to the playbook, would have caught this?

### Step 5: Propose Playbook Changes

Draft playbook text changes as edits to the actual playbook files in `playbook/`. Each change must pass the Abstraction Level Validation (see below). Changes should be general software engineering principles, not fixes for specific codebases.

### Step 6: Validate Changes

Repeat the exercise from scratch for this repo:

1. Remove the `quality/` folder
2. Use the **updated** playbook to regenerate quality infrastructure (same as Step 1)
3. Re-run the code review for **all** defects in this repo, not just the misses (same as Step 2). This detects regressions — a playbook change can fix one miss while breaking a previous hit.
4. Score the results (same as Step 3). Compare each defect's new score against its original score.

If the updated playbook catches previously missed bugs without regressing on previous hits, the changes are validated. If some misses still slip through, or if previous hits regressed, decide whether to iterate again, revise the changes, or accept the result.

### Step 7: Bootstrapping Gate (Before Version Bump)

Before finalizing a new playbook version, run the current playbook against the QPB repository itself. This catches defects in the QPB's own tooling scripts, data files, and documentation — and validates that the playbook's new detection patterns actually work on a real codebase.

**Procedure:**

1. Clone QPB into `repos/quality-playbook-benchmark` (or pull latest if already cloned)
2. Copy the candidate playbook version into `.claude/skills/quality-playbook/` in the cloned repo
3. Run the playbook's Phase 1–2 (explore + generate) to produce quality infrastructure for QPB
4. Run `pytest quality/test_functional.py -v` — all generated tests must pass
5. Run the generated code review protocol against QPB's tooling scripts
6. If the review finds defects: fix them in QPB, then assess whether the fix pattern is general enough to warrant a new detection pattern in the playbook
7. If new patterns are added, re-run from step 3 with the updated playbook to verify the additions don't break anything

**Gate criteria:**
- All generated functional tests pass (zero failures, zero errors)
- No new tooling bugs found that the playbook should have caught but didn't
- Any new detection patterns added during bootstrapping are grounded in real bugs (not hypothetical)

**Why this matters:** The bootstrapping gate prevents two failure modes. First, it catches regressions — a playbook change that improves detection on external repos but breaks the playbook's own test generation. Second, it ensures that each version of the playbook can successfully review a real Python + Markdown codebase end-to-end, which is the minimum bar for deployment.

**Record keeping:** Save the bootstrapping test results in `runs/improvement_001/bootstrapping/v<version>/` with the generated quality infrastructure and test output. This provides an audit trail showing that each version passed the gate.

### Step 8: Proceed to Next Repo

Move to the next improvement repo. The playbook now includes the changes from the previous repo. As you work through more repos, the playbook accumulates improvements.

**Important**: Each repo gets a fresh start — generate quality infrastructure from scratch using the current playbook version, don't carry over quality files from previous repos.

### Ordering

Work through improvement repos in any order, but consider starting with repos that have diverse defect categories to maximize early learning. Record the order — it's part of the experimental design.

---

## Validation Protocol

After completing the improvement loop across all improvement repos, run the validation protocol on the held-out repos to measure generalization.

### Before/After Comparison

For each held-out repo:

1. **"Before" run**: Use the **original** playbook (v1.2.0) to generate quality infrastructure at HEAD, then review each QPB defect at its pre-fix commit using the quality infrastructure. Score each defect.

2. **"After" run**: Use the **final improved** playbook to generate quality infrastructure at HEAD for the same repo, then review the same defects at the same pre-fix commits. Score each defect.

Both runs use the same prompts — the only difference is the playbook version. Same agent, same model, same files. The playbook is the independent variable.

**Session isolation**: Each `(repo, defect, playbook version)` evaluation must run in a fresh, isolated session with no retained conversation state, cached summaries, or tool memory from previous runs. This prevents cross-condition contamination — if the same agent reviews the same defect under both playbook versions, later runs must not inherit knowledge from earlier ones. Log a session identifier for each run. If feasible, randomize the order of before/after runs across defects to guard against systematic order effects.

### What This Proves

If the improved playbook detects more bugs than the original on the held-out repos, the improvement generalizes — it's not just overfitting to the specific bugs that motivated the changes. This is the paper's primary evidence.

### Running Controls

Each held-out defect gets scored twice (before and after). For paired comparison, use McNemar's test on the before/after scores. Report the transition matrix: how many defects moved from miss→hit, miss→adjacent, hit→miss, etc.

---

## Scoring Rubric

Scoring compares the agent's raw findings against the oracle (fix commit diff).

| Score | Criteria | Example |
|-------|----------|---------|
| **Direct hit** | The findings name the specific bug, the specific code path, or describe the root cause such that a developer reading the findings would know exactly what to fix | "The `err =` on line 279 should be `err :=` to avoid sharing the outer-scope variable with the goroutine" |
| **Adjacent** | The findings flag the affected area, function, or a related concern, but don't identify the specific bug | "The goroutine in UpdatePortVisibility has potential concurrency issues" (without naming the specific variable scoping problem) |
| **Miss** | The findings don't mention the bug, the affected code area, or any related concern | Review discusses other files or other issues entirely |
| **Not evaluable** | The agent crashed, timed out, produced no output, or the defect couldn't be checked out | Tool error, git checkout failure, empty response |

**Scoring is conservative**: direct hit requires that a developer reading the findings would know what to fix without looking at the oracle. Adjacent means they'd know where to look but would need to investigate further.

### Scoring Handbook (Worked Examples)

To ensure inter-rater agreement, the following examples illustrate boundary cases:

**Direct hit examples**:
- "The `err =` on line 279 should be `err :=` — the current code reuses the outer-scope error variable inside a goroutine, which creates a data race." → Direct hit: names the bug, the line, and the root cause.
- "The cache key uses only `(user_id, query)` but doesn't include `locale`. Two users with different locales will get each other's cached results." → Direct hit: identifies the exact missing field and the consequence.

**Adjacent examples**:
- "The goroutine in `UpdatePortVisibility` has potential concurrency issues." → Adjacent: correct function, correct concern category, but doesn't identify the specific variable scoping problem.
- "The caching layer should be reviewed for correctness — the key generation may not account for all relevant parameters." → Adjacent: correct area, but no specifics about which parameter is missing.

**Miss examples**:
- The review discusses error handling in a completely different module and doesn't mention the affected function at all. → Miss.
- The review mentions the affected file but only comments on naming conventions and code style. → Miss: the comments are unrelated to the defect.

**Borderline cases**:
- The review identifies the correct invariant ("cache keys must include all user-facing parameters") but names the wrong specific parameter. → Adjacent, not direct hit: the invariant is right but a developer would still need to investigate which parameter is actually missing.
- The review identifies the exact bug but attributes it to the wrong root cause. → Direct hit if the finding would still lead a developer to the correct fix; adjacent if the wrong root cause would lead to the wrong fix.
- Multi-file bugs: a direct hit requires identifying the bug's root cause, not merely flagging one of several affected files. If the review flags the right file but misses the cross-file interaction that constitutes the actual bug, score as adjacent.

**Inter-rater reliability**: For paper publication, a random sample of at least 50 scores (or 20% of the sample, whichever is larger) should be independently rated by at least two scorers. Report Cohen's kappa or percent agreement. Disagreements should be resolved by a third scorer or by consensus.

---

## Abstraction Level Validation

Every proposed playbook change must be a general principle, not a fix for a specific codebase. Before any change is accepted:

- **Strip all codebase-specific references.** The proposed text must not mention specific libraries, specific function names from the test repos, or specific variable names from the miss that motivated the change. If you can't state the rule without naming the library, the rule is too narrow.
- **State the underlying invariant.** Each change should express a general software engineering principle that applies across languages and domains.
- **Provide cross-language examples.** If the principle is real, it should have natural examples in at least 3 languages/ecosystems. If you can only think of examples from the miss that motivated it, the principle may be too narrow.
- **Check for existing coverage.** Verify the playbook doesn't already cover the principle under a different name or in a different section. Duplication dilutes the playbook.

### Council of Three Review Gate

Before any proposed change is published to the playbook, a Council of Three review must validate:

- **Abstraction level**: Is the rule general enough to apply to codebases the QPB hasn't tested? Could you explain it to a reviewer working on a completely different tech stack?
- **Overfitting risk**: Does the rule help only with the specific miss, or does it plausibly help with a class of bugs? If you removed the QPB dataset entirely, would a senior engineer still agree this belongs in a code review playbook?
- **Regression risk**: Could the new rule cause false positives that waste reviewer attention? Is the signal-to-noise ratio acceptable?
- **Minimal scope**: Is the change the smallest addition that captures the principle? Could it be a single sentence added to an existing section instead of a new section?

### Wide Multi-Tool Review

After a playbook version passes the bootstrapping gate (Step 7) and Council of Three review, submit it for review across a diverse set of AI tools and models. The goal is to surface tool-specific failure modes — places where the playbook's instructions are clear to one model but ambiguous to another, or where a tool's orchestration layer interferes with the playbook's workflow.

**Review targets** (v1.2.6):

| # | Tool | Model | Category |
|---|------|-------|----------|
| 1 | Claude Code | Opus 4.6 | Coding agent — flagship |
| 2 | Claude Code | Haiku 4.6 | Coding agent — small/fast |
| 3 | Claude.ai web UI | Opus 4.6 (extended thinking) | Chat UI — Anthropic flagship |
| 4 | Claude.ai web UI | Haiku 4.6 (extended thinking) | Chat UI — Anthropic small |
| 5 | Cursor | CPT 5.4 | Coding IDE — OpenAI |
| 6 | Copilot | Gemini 2.5 Pro | Coding IDE — Google |
| 7 | ChatGPT web UI | GPT (with Thinking) | Chat UI — OpenAI |
| 8 | Copilot web UI | Copilot (with Think Deeper) | Chat UI — Microsoft |
| 9 | Ollama | Llama 3.3 70B | Local/open-weight — Meta |
| 10 | Ollama | Qwen 2.5 72B | Local/open-weight — Alibaba |
| 11 | Ollama | DeepSeek-R1 70B | Local/open-weight — reasoning |

**What each reviewer does**: Point the tool at a QPB improvement repo (one that has cloned source), install the playbook as a skill or paste it as context, and ask the tool to generate quality infrastructure. Record: whether the tool successfully completed all phases, what it got wrong, where it got stuck, and any findings that other tools missed.

**What to look for**:
- Does the tool follow the playbook's phase structure, or does it skip phases?
- Does it correctly parse function signatures before writing tests (Step 4b)?
- Does the generated QUALITY.md contain project-specific scenarios, or generic filler?
- Do the generated tests actually pass?
- Does the tool handle the playbook's length (500+ lines) without losing context?
- Does the local/open model produce usable output, or does it require frontier-model capabilities?

**Recording results**: Save each review as a structured report in `reviews/` following the existing review schema. Tag with `type: wide-review`, the tool name, model name, playbook version, and target repo. Cross-tool comparison should focus on the detection patterns that vary by model — these are the playbook's weak spots where instructions need to be more explicit.

---

## Statistical Framework

### Metrics

Primary metrics (always report):

| Metric | Definition |
|--------|-----------|
| **Detection rate (strict)** | direct_hits / (total - not_evaluable) |
| **Detection rate (relaxed)** | (direct_hits + adjacent) / (total - not_evaluable) |
| **Miss rate** | misses / (total - not_evaluable) |

Secondary metrics (report when sample size permits):

| Metric | Definition |
|--------|-----------|
| **Detection rate by category** | Strict detection rate computed per defect category |
| **Detection rate by language** | Strict detection rate computed per programming language |
| **Detection rate by severity** | Strict detection rate computed per severity level |
| **Detection rate by playbook step** | Which playbook step produced the detection (from the "playbook angle" field) |
| **Novel findings rate** | Findings that flag an issue in the reviewed files that doesn't correspond to any known QPB defect. These are *not* necessarily false positives — they may be real, previously undiscovered bugs. Report separately and note that manual verification is needed to determine whether novel findings are true positives, false positives, or known issues outside the QPB scope. |
| **Not-evaluable rate** | Proportion of defects scored as not_evaluable, reported by repo, category, and model. A high not-evaluable rate could mask poor performance. If >10% of defects in any stratum are not-evaluable, investigate and report the cause. |

### Confidence Intervals

Report 95% Wilson score confidence intervals for all detection rates. For a sample of size n with k detections:

```
p̂ = k/n
CI = Wilson score interval (not Wald — Wald is unreliable for extreme proportions)
```

For the before/after validation comparison, use McNemar's test (paired, since both playbook versions score the same defects).

### Clustering

Defects are clustered within repositories — defects from the same repo are not independent observations. To account for this:

- Report repo-level detection rates alongside pooled rates. If a few held-out repos dominate the defect count or respond unusually well to the revised playbook, pooled rates can be misleading.
- Compute bootstrap confidence intervals resampled at the repo level (resample repos, not individual defects) to capture between-repo variability.
- If sample size permits, fit a mixed-effects logistic regression with repository as a random effect and playbook version as a fixed effect. This directly models the clustering structure and provides an estimate of the playbook effect that accounts for repo-level heterogeneity.

### Power and Sample Size

The held-out set should contain enough defects to detect a meaningful before/after difference. Planning guidance:

- **Target**: At least 15–20 held-out repos with a combined total of at least 200 defects. This provides reasonable power to detect a 10–15 percentage point improvement with McNemar's test (alpha=0.05, power=0.80), assuming moderate within-repo correlation.
- **Sensitivity check**: If the held-out set is smaller than planned, compute the minimum detectable effect size for the actual sample and report it. An underpowered comparison should be described as exploratory.
- **Repo diversity**: The held-out set should span enough languages and project types that a null result is informative (not attributable to an unrepresentative sample).

### Stopping Criterion

Stop iterating on improvement repos when:
- Detection rate on newly encountered repos plateaus (less than 2 percentage point improvement across two consecutive repos), OR
- The proposed changes fail the Abstraction Level Validation (changes are becoming too specific to particular codebases), OR
- The novel findings rate increases materially (new guidance is causing false alarms)

---

## Reproducibility Requirements

For paper publication, the following must be available:

| Artifact | Purpose | Location |
|----------|---------|----------|
| QPB defect dataset | Ground truth | `dataset/DEFECT_LIBRARY.md`, `dataset/defects.jsonl` |
| Repository snapshots | Code under test | `repos/` (git clones with full history) |
| Playbook versions | The intervention (before and after) | `playbook/SKILL.md` + `playbook/references/` (versioned) |
| Repo split | Which repos are improvement vs held-out | `dataset/REPO_SPLIT.md` |
| Quality infrastructure | Generated per repo | `runs/<run_id>/quality/<repo>/` |
| Agent prompts | Exact prompts sent | `runs/<run_id>/prompts/<defect_id>.md` |
| Agent outputs | Raw findings | `runs/<run_id>/findings/<defect_id>.md` |
| Scoring log | Score + evidence | `runs/<run_id>/results.jsonl` |
| Run metadata | Parameters, timing, model, playbook version | `runs/<run_id>/metadata.json` |
| Improvement log | What changed and why per repo | `runs/<run_id>/improvement_log.md` |

All run artifacts should be committed to version control or archived with the paper.

### Logging

For each defect review, record:

| Field | Description |
|-------|-------------|
| `run_id` | Unique identifier for this evaluation run |
| `defect_id` | QPB defect identifier (e.g., GH-03, CURL-02) |
| `repo` | Repository name |
| `pre_fix_commit` | Exact commit SHA checked out for this review |
| `playbook_version` | Playbook version being tested |
| `model` | Model identifier (e.g., claude-opus-4-6) |
| `tool` | Tool used (e.g., Claude Code, Cursor, Copilot) |
| `tool_version` | Tool version string (e.g., VS Code extension version, Cursor app version, Claude Code CLI version) |
| `timestamp` | ISO 8601 start time |
| `duration_ms` | Wall-clock duration of the review |
| `session_id` | Unique identifier for this isolated session (confirms no cross-condition state leakage) |
| `files_reviewed` | List of file paths reviewed |
| `findings_file` | Path to the full findings file (e.g., `findings/<defect_id>.md`) |
| `prompt_hash` | SHA-256 hash of the exact prompt sent (for verifying prompt consistency across conditions) |
| `retry_count` | Number of retries needed (0 if first attempt succeeded) |
| `timeout_policy` | Timeout setting used, if configurable by the tool |
| `score` | direct_hit / adjacent / miss / not_evaluable |
| `score_evidence` | Brief explanation of why this score was assigned |

### Review Output Directory

Council of Three reviews, methodology audits, and playbook change reviews are stored in `reviews/` at the repo root. These are authored artifacts and should be version-controlled as part of the paper's audit trail.

Naming convention: `{type}-{reviewer}-{subject}-{date}.md`

- **type**: `council-review`, `spec-audit`, `playbook-review`
- **reviewer**: `copilot`, `cursor`, `claude`, `human`
- **subject**: what was reviewed (e.g., `methodology`, `playbook-v1.3.0`)
- **date**: `YYYY-MM-DD`

### Run Directory Structure

```
runs/
  <run_id>/
    metadata.json          # Run parameters, model, playbook version, dates
    quality/
      <repo>/              # Quality infrastructure generated for each repo
    prompts/
      <defect_id>.md       # Exact prompt sent for each defect review
    findings/
      <defect_id>.md       # Raw agent output for each defect review
    results.jsonl          # One JSON line per defect: score, evidence, timing
    improvement_log.md     # What misses were found, what changes were proposed
    summary.md             # Aggregate statistics, tables
```

---

## Per-Repo Description File Format

Each repository will have a `dataset/defects/<repo>/defects.md` file containing detailed descriptions of its defects. Currently, sample files exist for `curl` (5 of 49 entries) and `cli` (20 of 71 entries). The remaining repositories will be generated after council review of the format. The target format for each defect entry is:

```markdown
## PREFIX-NN | Title | Category | Severity

**Fix commit**: [`<sha>`](https://github.com/<owner>/<repo>/commit/<sha>)
**Pre-fix commit**: `<parent_sha>`
**Issue/PR**: [#NNN](https://github.com/<owner>/<repo>/pull/NNN)

**Files changed**:
- `path/to/file1.ext`
- `path/to/file2.ext`

**Commit message**:
(verbatim commit message from git log)

**Issue/PR summary**:
(1-3 sentence summary of the GitHub issue or PR, in our own words; see Issue Text Reuse Policy below)

**Defect summary**:
(2-4 sentence description of what was wrong, derived from examining the actual git diff)

**Diff stat**:
(output of git diff --stat between pre-fix and fix commits)

**Playbook angle**:
(which playbook step should catch this, and what pattern to look for)
```

### Data Sources for Each Field

| Field | Source | Availability |
|-------|--------|-------------|
| Fix commit | DEFECT_LIBRARY.md | 100% (2,564/2,564) |
| Pre-fix commit | DEFECT_LIBRARY.md (parent of fix) | 100% |
| Issue/PR | Extracted from commit message | 73% (1,877/2,564) |
| Files changed | `git diff-tree --name-only` on fix commit | 97% (2,480/2,564) |
| Commit message | `git log --format=%B` on fix commit | 98% (2,508/2,564) |
| Original issue description | Fetched from GitHub issue/PR page | Available for all with issue refs |
| Defect summary | Written by mining agent based on diff analysis | 100% |
| Diff stat | `git diff --stat` between pre-fix and fix | 97% |
| Playbook angle | Written by mining agent | 100% |

---

## Threats to Validity

### Internal Validity

1. **Quality infrastructure generated at HEAD includes post-fix information**: Quality infrastructure is generated at repo HEAD, which includes all fix commits. The generated artifacts (quality constitution, review protocol, functional tests) may encode defensive patterns, tests, or architectural knowledge introduced by those fixes. We chose repo-level HEAD-generated quality infrastructure because it matches real playbook deployment, keeps evaluation cost tractable (regenerating per defect would multiply cost by defects-per-repo), and ensures consistent review guidance across all defects in a repository. This introduces post-fix contamination risk, so claims are limited to *retrospective review with modern context* rather than unbiased historical detection. For many defects, especially recent ones, the project's architectural intent and quality expectations are stable enough that HEAD-generated infrastructure remains relevant; however, this may be less valid for older defects or repos with major architectural drift. The before/after comparison controls for this because both playbook versions see the same HEAD-generated artifacts. **Optional mitigation**: A HEAD-vs-pre-fix-commit ablation on a subset of defects can quantify the magnitude of this effect (see Step 1).

2. **Prompt sensitivity**: Agent performance depends on exact prompt wording. Mitigation: Use the same prompts for before and after runs. Log exact prompts for reproducibility.

3. **Scorer bias**: Human scorers who know the oracle may be biased toward generous scores. Mitigation: Use the conservative rubric (direct hit requires actionable specificity); report inter-rater reliability.

4. **Model nondeterminism**: LLM outputs are stochastic. The same defect may score differently on two runs. Mitigation: For the improvement protocol, single-pass is acceptable. For the validation protocol, consider running each defect multiple times (e.g., 3 runs with majority vote) if cost permits, to reduce noise in the before/after comparison.

5. **Model training-data leakage**: QPB uses public open-source repositories. Frontier LLMs may have been trained on some of the same repositories, issue discussions, or fix diffs. Measured "detection" may partly reflect prior exposure rather than playbook quality. Mitigation: (a) The before/after comparison controls for this — if the model has memorized a fix, it will find it with both playbook versions. (b) Report results separately for newer vs. older commits. (c) Limit claims to "performance on this benchmark" rather than "general code review ability."

6. **Tool/model drift**: Model behavior can change over time for the same model tag. Mitigation: Run before and after validation as close together in time as possible. Record model identifiers and dates.

### External Validity

1. **Mining bias**: Defects were mined from commit messages containing fix-related keywords. Bugs fixed without such keywords are missed.

2. **Repository selection**: The 50 repositories were hand-selected for diversity, not randomly sampled. Results may not generalize to closed-source or enterprise codebases.

3. **Single-commit constraint**: Bugs fixed across multiple commits are not captured.

4. **Category judgment**: Category assignment involves judgment calls. We chose one primary category per defect.

5. **Severity subjectivity**: Severity was assessed from the defect description, not production impact data.

### Construct Validity

1. **Detection ≠ Prevention**: Finding a bug in a code review doesn't mean it would have been prevented in practice.

2. **File scoping as oracle hint**: The agent is told exactly which files to review — the files changed by the fix commit. A real reviewer wouldn't have this information. This means QPB evaluates the playbook's ability to *find bugs within a given review scope*, not its ability to *identify which files contain bugs*. Detection rates are inflated relative to realistic unscoped review. This narrower claim must be maintained consistently throughout the paper (abstract, introduction, method, and discussion). **Recommended ablation**: Run a subset of held-out defects (e.g., 5–10 per language) with an unscoped prompt that asks the agent to review the entire repository or a broad module rather than specific files. Report scoped and unscoped detection rates side by side. This quantifies the file-scoping advantage rather than leaving it as a qualitative caveat.

3. **Improvement repo ordering**: The order in which improvement repos are processed affects which bugs the playbook learns from first. Different orderings might produce different final playbooks. Mitigation: Record the ordering and note it as a design choice.

---

## Issue Text Reuse Policy

The per-repo description files include an "Original issue description" field. To avoid legal risk from reproducing full GitHub issue or PR text:

- **Commit messages** are included verbatim (they are part of the repository's version-controlled history under its license).
- **Issue/PR descriptions** are summarized in our own words, not quoted verbatim. Each summary is 1-3 sentences capturing the essential technical content.
- **Links** to the original issue/PR are always provided so readers can access the full context.
- **No reproduction of comments, discussion threads, or reproduction steps** from issue trackers.

---

## Related Work

QPB should be positioned against existing benchmarks and evaluation methodologies in the AI-for-SE and software testing literature:

**Real-bug benchmarks**: Defects4J (Just et al., 2014) provides 835 real bugs from 17 Java projects and is the standard benchmark for automated program repair (APR) research. Bears (Madeiral et al., 2019) and Bugs.jar (Saha et al., 2018) extend this approach to different Java project sets. QPB differs in three ways: (a) it spans 14 languages rather than Java only, (b) it evaluates *detection* (can a reviewer find the bug?) rather than *repair* (can a tool generate the fix?), and (c) it evaluates a structured review protocol rather than a standalone tool.

**LLM-oriented benchmarks**: SWE-bench (Jimenez et al., 2024) evaluates LLM agents on their ability to resolve GitHub issues end-to-end (from issue description to passing tests). SWE-bench provides the issue description as input, while QPB provides no bug description — the agent must find the bug blind. HumanEval and MBPP evaluate code generation, not code review. QPB occupies a different niche: evaluating review protocols rather than generation or repair capabilities.

**Mutation testing**: The conceptual ancestor of QPB. Mutation testing injects synthetic faults and measures whether tests detect them. QPB uses real historical bugs instead of injected mutants, which avoids the "unrealistic mutant" criticism but introduces different biases (mining bias, single-commit constraint).

**Static analysis evaluation**: Tools like FindBugs/SpotBugs, PMD, and SonarQube are evaluated against known bug databases. QPB applies a similar oracle-based methodology to AI-assisted review protocols rather than rule-based static analyzers.

**Code review research**: Studies on modern code review (Bacchelli & Bird, 2013; McIntosh et al., 2016) establish that code review finds bugs but is far from comprehensive. QPB quantifies this for AI-assisted review specifically, using the playbook as a structured intervention.

The key novelty of QPB is combining real historical bugs as oracles with iterative improvement of a structured AI review protocol, across a multi-language dataset, with held-out repositories to validate generalization.

---

## Bootstrapping (Self-Review)

The playbook is applied to the QPB repository itself as a validation step. This "bootstrapping" check verifies that the playbook can detect defects in its own supporting infrastructure — tooling scripts, data files, and documentation.

### Procedure

1. **Clone**: `git clone https://github.com/andrewstellman/quality-playbook-benchmark.git repos/quality-playbook-benchmark`
2. **Install playbook**: Copy the current playbook version into `.claude/skills/quality-playbook/` in the cloned repo
3. **Generate quality infrastructure**: Run the playbook's Phase 1 (explore) and Phase 2 (generate) against the QPB codebase, producing `quality/QUALITY.md`, `quality/test_functional.py`, `quality/RUN_CODE_REVIEW.md`, `quality/RUN_INTEGRATION_TESTS.md`, and `quality/RUN_SPEC_AUDIT.md`
4. **Run tests**: Execute `pytest quality/test_functional.py -v` and record results
5. **Fix findings**: Implement fixes for real data quality issues and tooling bugs
6. **Assess playbook improvements**: Determine whether any findings suggest general playbook improvements (e.g., new detection patterns, new step guidance)
7. **Iterate**: If playbook changes were made, re-run from step 3 to verify the updated playbook still generates passing tests

### Bootstrapping Results (v1.2.5, 2026-03-31)

**Generated infrastructure**: 38 functional tests across 7 test classes covering format compliance, category normalization, commit SHA validity, scenario-based data integrity, tooling integration, edge cases, and data quality.

**Tooling script findings** (5 bugs fixed):
- `extract_defect_data.py`: Bare `except:` clause in `git_cmd()` silently masks all errors — fixed to catch specific exceptions with stderr warning
- `assemble_v8.py`: Unchecked `re.search().group(0)` crashes if "Total" row missing — fixed with None guard
- `extract_defect_data.py`: Variable named `title` actually holds issue/PR reference — fixed label and downstream references
- `normalize_categories.py` vs `assemble_v8.py`: Parallel canonical category definitions could diverge — added cross-reference comment
- `generate_sample.py`: Only ZOOKEEPER and KAFKA JIRA prefixes mapped to URLs — expanded to all Apache JIRA projects

**Markdown artifact findings** (detected by generated tests):
- SHA placeholder values (`--`, `N/A`, `(merge)`, `(parent)`, `(commit before)`) found in 35 pre-fix commit entries — documented as known data gaps
- Rows with unescaped pipe characters in description fields (e.g., CHI-06 with 10 columns) — parser handles gracefully
- All 2,564 defect IDs follow PREFIX-NN format, all categories are canonical, no duplicates

**Test outcome**: 37 passed, 1 skipped (commit resolution requires cloned repos), 0 failed.

**Playbook improvement signal**: The bootstrapping found three patterns worth encoding as new detection guidance:
1. **Truth fragmentation** (Finding 4) — canonical values defined in multiple files can silently diverge. Added to Step 5c.
2. **Placeholder values masking data gaps** (SHA findings) — sentinel values like `--`, `N/A`, `(merge)` pass type checks but are semantically meaningless. Added to Step 5d.
3. **Field label drift** (Finding 3) — positional extraction assigns data to variable names that become stale as the data format evolves. Added to Step 5c.

These patterns were promoted to playbook v1.2.6, along with a Bootstrapping section documenting self-review as an explicit capability.

---

## Changelog

- **2026-03-29**: Initial methodology document created with dataset composition, mining protocol, and scoring rubric.
- **2026-03-30**: Major revision. Added: complete evaluation protocol (Phase 1/Phase 2 separation), statistical framework (sampling, confidence intervals, metrics), improvement iteration protocol (train/holdout split, stopping criterion), reproducibility requirements (run directory structure, logging schema), threats to validity (internal, external, construct). Moved scoring rubric into evaluation protocol. Added contamination controls, inter-rater reliability requirements, and "no playbook" baseline recommendation.
- **2026-03-30**: Council of Three revision (addressing reviews from Cursor and GitHub Copilot). Added matched control conditions, scoring handbook, training-data leakage threat, clustering analysis, and Related Work section.
- **2026-03-30**: Major restructure. Replaced the formal experimental protocol with an iterative improvement protocol that matches the actual playbook workflow: generate quality infrastructure at HEAD, review pre-fix code using quality infrastructure, analyze misses, improve playbook, validate by regenerating from scratch. Split repos into improvement (~30) and held-out (~20) groups. Held-out repos provide clean before/after validation evidence. Removed matched control conditions and budget-matched baselines (impractical with real tools like Claude Code, Cursor, Copilot which don't expose token-level control). Simplified logging to fields actually available from these tools. Preserved scoring rubric, scoring handbook, abstraction level validation, Council of Three review gate, threats to validity, and related work.
- **2026-03-31**: Bootstrapping (self-review). Applied playbook v1.2.5 to QPB repository itself. Generated 38 functional tests, found and fixed 5 tooling script bugs, documented 35 SHA placeholder entries as known data gaps. Promoted three detection patterns to playbook v1.2.6: truth fragmentation (Step 5c), placeholder values masking data gaps (Step 5d), field label drift (Step 5c). Added Bootstrapping (Self-Review) subsection to playbook. Formalized bootstrapping as a mandatory gate in the improvement protocol (Step 7) — every new playbook version must pass bootstrapping before release. Added Wide Multi-Tool Review section with 8 review targets (Claude Code Opus/Haiku, Claude.ai web UI, Cursor + CPT 5.4, Copilot + Gemini 2.5 Pro, ChatGPT with Thinking, Copilot with Think Deeper, Ollama local model).
- **2026-03-31**: Round 3 council revision. Added explicit research question. Strengthened HEAD contamination rationale with cost and consistency arguments; reframed as "retrospective review with modern context." Added HEAD-vs-pre-fix-commit ablation suggestion. Added session isolation requirement for validation protocol. Restored clustering analysis (repo-level bootstrap, mixed-effects model) and power/sample-size guidance. Restored unscoped file ablation and tightened file-scoping claim language. Extended logging table with tool_version, session_id, prompt_hash, retry_count, timeout_policy. Added hill-climbing rationale to improvement protocol intro. Emphasized blind review as protocol cornerstone.
