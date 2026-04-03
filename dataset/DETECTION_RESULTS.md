# Playbook Detection Results

Results of running the quality playbook against pre-fix commits from [DEFECT_LIBRARY.md](DEFECT_LIBRARY.md). This file is mutable and version-tracked; the defect library is immutable ground truth.

## Scoring Rubric

- **Direct hit** — Playbook output names the bug, the specific code path, or produces a test that would catch it
- **Adjacent** — Playbook flags the area, module, or pattern class but not the specific defect
- **Miss** — Playbook output does not mention it

Scoring is conservative: a "direct hit" requires that someone reading the playbook output would know to look at the specific code that has the bug. "Adjacent" means the output would lead a developer to the right neighborhood but not the specific issue.

Additional tracking (not scores, but recorded alongside):
- **Not evaluable** — Tool crashed, timed out, or produced no output for this defect
- **Novel findings** — Tool flagged an issue in the affected file that doesn't correspond to any known QPB defect. These are not necessarily false positives — they may be real, previously undiscovered bugs. Report separately and note that manual verification is needed to determine whether novel findings are true positives, false positives, or known issues outside QPB scope.

Each score should include a brief evidence note explaining why that score was assigned, to enable adjudication and cross-reviewer consistency.

## Execution Parameters

Each defect review records (see METHODOLOGY.md § Logging for the full schema):

| Parameter | Description |
|-----------|-------------|
| **run_id** | Unique identifier for this evaluation run |
| **defect_id** | QPB defect identifier (e.g., GH-03, CURL-02) |
| **repo** | Repository name |
| **pre_fix_commit** | Exact commit SHA checked out for this review |
| **Playbook version** | e.g., v1.2.0 |
| **Model** | e.g., claude-opus-4-6, claude-sonnet-4-6, gpt-4o, gemini-2.5-pro |
| **Tool** | e.g., Claude Code, Cursor, Copilot |
| **tool_version** | Tool version string |
| **Date** | ISO 8601 start time |
| **duration_ms** | Wall-clock duration of the review |
| **session_id** | Unique identifier for this isolated session |
| **prompt_hash** | SHA-256 hash of the exact prompt sent |
| **Notes** | Any relevant context (timeout, partial run, etc.) |

Tracking the model is critical. A core research question is whether different models have different detection profiles — e.g., whether one model is better at finding state machine gaps while another catches type safety issues more reliably.

---

## Run Template

Copy this section for each test run:

### Run: [playbook version] / [model] — [date]

**Parameters**: Playbook v1.2.0 | claude-opus-4-6 | Claude Code | 2026-MM-DD

#### Summary

| Metric | Value |
|--------|-------|
| Total defects tested | 56 |
| Direct hits | — |
| Adjacent | — |
| Misses | — |
| Not evaluable | — |
| Novel findings | — |
| Detection rate (direct) | —% |
| Detection rate (direct + adjacent) | —% |

#### Results by Category

| Category | Direct | Adjacent | Miss | Not Eval | Detection % |
|----------|--------|----------|------|----------|-------------|
| error handling | | | | | |
| validation gap | | | | | |
| configuration error | | | | | |
| type safety | | | | | |
| state machine gap | | | | | |
| concurrency issue | | | | | |
| serialization | | | | | |
| API contract violation | | | | | |
| protocol violation | | | | | |
| null safety | | | | | |
| silent failure | | | | | |
| security issue | | | | | |
| SQL error | | | | | |
| missing boundary check | | | | | |

#### Results by Project

| Project | Direct | Adjacent | Miss | Not Eval | Detection % |
|---------|--------|----------|------|----------|-------------|
| *(fill per tested repo)* | | | | | |

#### Results by Playbook Step

Which steps produced the detections? Maps to the "Playbook Angle" column in the defect library.

| Step | Detections | Expected | Hit Rate |
|------|------------|----------|----------|
| Step 2 (architecture) | | | |
| Step 3 (existing tests) | | | |
| Step 4 (specifications) | | | |
| Step 5 (defensive patterns) | | | |
| Step 5a (state machines) | | | |
| Step 5b (schema types) | | | |
| Step 6 (quality risks) | | | |

#### Detailed Results

| Defect | Category | Score | Detecting Step | Evidence | Novel Findings |
|--------|----------|-------|----------------|----------|----------------|
| *(fill per defect)* | | | | | |

---

## Cross-Model Comparison

After multiple runs with different models, fill in:

| Defect | Category | [Model A] | [Model B] | [Model C] |
|--------|----------|-----------|-----------|-----------|
| *(fill per defect)* | | | | |

### Detection Rate by Category × Model

| Category | [Model A] | [Model B] | [Model C] |
|----------|-----------|-----------|-----------|
| state machine gap | | | |
| type safety | | | |
| validation gap | | | |
| ... | | | |

### Observations

Record patterns here:
- Which categories does [Model A] detect better than [Model B]?
- Are there defects that no model catches?
- Are there defects that every model catches?
- Do domain-knowledge-dependent defects (Step 6) show more model variance than code-pattern defects (Step 5)?

---

## Improvement Tracking

### Playbook Changes Driven by Misses

| Version | Change | Defects Targeted | Before | After |
|---------|--------|-----------------|--------|-------|
| v1.2.0 | Added Step 5a (state machine tracing) | O-02, O-03, O-08 | Miss | Direct |
| v1.2.0 | Added Step 6 safeguard patterns | O-05, O-06, O-07 | Miss | Direct |
| v1.3.0 | (planned) | | | |

### Re-test After Improvement

When a playbook version is updated based on misses, re-run against **all defects in the improvement repo** (not just the missed ones) to detect regressions. A playbook change can fix one miss while breaking a previous hit. Record the new scores here, noting both improvements and regressions.

---

## Changelog

- **2026-03-29**: Schema created. No detection runs yet.
- **2026-03-31**: Synced with METHODOLOGY.md v3. Renamed "False positive" to "Novel findings." Updated execution parameters to match full logging schema. Added Not evaluable and Novel findings to summary/detail tables. Updated re-test policy to require full-repo reruns (not just missed defects). Added evidence and novel findings columns to detailed results.
