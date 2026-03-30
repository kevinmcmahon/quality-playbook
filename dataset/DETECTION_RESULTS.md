# Playbook Detection Results

Results of running the quality playbook against pre-fix commits from [DEFECT_LIBRARY.md](DEFECT_LIBRARY.md). This file is mutable and version-tracked; the defect library is immutable ground truth.

## Scoring Rubric

- **Direct hit** — Playbook output names the bug, the specific code path, or produces a test that would catch it
- **Adjacent** — Playbook flags the area, module, or pattern class but not the specific defect
- **Miss** — Playbook output does not mention it

Scoring is conservative: a "direct hit" requires that someone reading the playbook output would know to look at the specific code that has the bug. "Adjacent" means the output would lead a developer to the right neighborhood but not the specific issue.

## Execution Parameters

Each test run records:

| Parameter | Description |
|-----------|-------------|
| **Playbook version** | e.g., v1.2.0 |
| **Model** | e.g., claude-opus-4-6, claude-sonnet-4-6, gpt-4o, gemini-2.5-pro |
| **Tool** | e.g., Claude Code, Cursor, Cowork |
| **Date** | When the run was executed |
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
| Detection rate (direct) | —% |
| Detection rate (direct + adjacent) | —% |

#### Results by Category

| Category | Direct | Adjacent | Miss | Detection % |
|----------|--------|----------|------|-------------|
| state machine gap | | | | |
| type safety | | | | |
| validation gap | | | | |
| error handling | | | | |
| silent failure | | | | |
| configuration error | | | | |
| security issue | | | | |
| concurrency issue | | | | |
| SQL error | | | | |
| protocol violation | | | | |
| null safety | | | | |
| missing boundary check | | | | |
| API contract violation | | | | |

#### Results by Project

| Project | Direct | Adjacent | Miss | Detection % |
|---------|--------|----------|------|-------------|
| gson | | | | |
| javalin | | | | |
| petclinic | | | | |
| octobatch | | | | |

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

| Defect | Category | Score | Detecting Step | Notes |
|--------|----------|-------|----------------|-------|
| G-01 | type safety | | | |
| G-02 | concurrency | | | |
| ... | | | | |

---

## Cross-Model Comparison

After multiple runs with different models, fill in:

| Defect | Category | [Model A] | [Model B] | [Model C] |
|--------|----------|-----------|-----------|-----------|
| G-01 | type safety | | | |
| G-02 | concurrency | | | |
| ... | | | | |

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

When a playbook version is updated based on misses, re-run against the missed defects and record the new scores here.

---

## Changelog

- **2026-03-29**: Schema created. No detection runs yet.
