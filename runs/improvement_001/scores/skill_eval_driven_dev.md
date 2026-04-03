# Quality Playbook Review: eval-driven-dev Skill

**Artifact**: `/sessions/quirky-practical-cerf/mnt/QPB/repos/awesome-copilot/skills/eval-driven-dev/`

**Review Date**: 2026-03-31

**Reviewer Approach**: Applying Quality Playbook review principles (Steps 4–6) to a Markdown-based AI skill with reference documentation. Evaluated against playbook criteria: specification clarity, defensive patterns, state machine completeness, parallel path symmetry, domain knowledge (Goodhart's law, eval brittleness, overfitting), and output quality verification.

---

## Executive Summary

The **eval-driven-dev skill is well-structured, pedagogically sound, and grounded in real domain knowledge about LLM evaluation pitfalls.** It excels at decomposing a complex workflow (setting up evaluation infrastructure) into discrete, checkpointed steps with clear dependencies and verification gates. The reference documentation is thorough and includes concrete anti-patterns.

However, **the skill exhibits critical vulnerabilities in handling real-world brittleness and edge cases:**

1. **Underspecified eval_input/expected_output semantics** — ambiguity about when to use expected_output creates opportunities for agents to produce circular or meaningless tests
2. **Insufficient guardrails against Goodhart's Law** — the skill teaches *how* to set up evaluators but provides limited guidance on *detecting* when agents are optimizing metrics instead of actual quality
3. **No mandatory re-validation after dataset changes** — the transition from Step 3 → Step 4 assumes dataset consistency without enforcement
4. **Brittleness of reference traces as ground truth** — single reference trace (Step 2) may not cover enough data variation, and no explicit guidance on coverage adequacy
5. **Investigation protocol lacks structured outcome classification** — Step 6 instructs agents to fix issues but provides no safeguards against introducing new ones

**Overall Rating**: **7.5/10** — High pedagogical value, but defensive gaps that could lead to false-positive tests or agent-introduced regressions.

---

## Detailed Findings by Playbook Step

### Step 4: Specifications — Clarity and Ambiguity

#### Finding 4.1: Ambiguous expected_output Semantics

**Location**: SKILL.md §4a, §5a; dataset-generation.md §"Setting expected_output"

**Issue**: The skill permits three distinct interpretations of `expected_output`:

1. **Exact answer reference** ("Paris" for "What is the capital of France?") — intended for `FactualityEval`, `ClosedQAEval`
2. **Quality criteria description** ("Should mention Saturday hours and be under 2 sentences") — intended for custom LLM evaluators
3. **Omitted/UNSET** — for standalone evaluators with no reference needed

**Problem**: An agent could (and many likely do) conflate these:

- Mix expected_output semantics within a single dataset (e.g., some items with exact answers, some with style guidance)
- Use comparison evaluators on items meant for standalone evaluation, producing 0.0 scores
- Create expected_output text that is too vague for evaluators to apply ("should be good", "should be helpful")

**Example of failure mode**:

```python
# ❌ AMBIGUOUS — what does this expected_output mean?
Evaluable(
    eval_input={"question": "Tell me about climate change"},
    expected_output="Comprehensive and balanced"
)
# Is this a factual answer for FactualityEval?
# Is this style guidance for a custom evaluator?
# Should this use a standalone evaluator instead?
```

**Missing specification**: The skill should require agents to **explicitly state which evaluator class will consume each expected_output** before creating the dataset. This is touched in Step 5a mapping criteria → evaluators, but verification doesn't flow backward to validate dataset construction.

**Severity**: High — agents frequently produce datasets that cannot be evaluated correctly.

---

#### Finding 4.2: Underspecified "Diverse eval_input" Validation

**Location**: SKILL.md §4c, dataset-generation.md §"Validating the dataset"

**Issue**: The checkpoints say "Verify diversity — items have meaningfully different inputs, not just minor variations" but provide no operational definition of "meaningful difference."

**Problem**: Agents interpret this loosely:

- 5 items with the same scenario (customer service query) but different names counts as "diverse"
- Items that differ only in one field (e.g., customer_profile.tier: "basic" vs. "gold") are treated as distinct scenarios
- Edge cases are underrepresented — no explicit mandate to include "things that break"

**Missing specification**:

- **Minimum coverage checklist**: Normal paths, boundary conditions (empty input, maximum length, minimum values), error conditions, permission/role boundaries, temporal edge cases (timezone handling, date boundaries)
- **Pair-wise difference metric**: If two items would produce the same routing/code path through the app, they're not diverse
- **Explicit regression zone mapping**: Each eval criterion from Step 1 should map to at least one dataset item that would catch a regression in that criterion

**Example of failure mode**:

```python
# ❌ LOW-DIVERSITY DATASET (all items follow same path)
items = [
    Evaluable(eval_input={"role": "admin", "action": "read"}, ...),
    Evaluable(eval_input={"role": "admin", "action": "write"}, ...),
    Evaluable(eval_input={"role": "admin", "action": "delete"}, ...),
]
# All 3 items hit the same code path (admin checks pass).
# Would NOT catch the bug: "basic user can access admin features"
```

**Severity**: Medium — datasets can pass tests while missing critical regression zones.

---

#### Finding 4.3: Validation Failure Recovery Unspecified

**Location**: SKILL.md §4c, dataset-generation.md (no section on repair)

**Issue**: The checkpoints mention validation but provide no path for fixing structural failures.

**Problem**: If an agent discovers that eval_input doesn't match the reference trace shape:

- Is the dataset rebuilt, or is the reference trace rejected?
- Can the app's interface have changed since Step 2, requiring re-instrumentation?
- Should agents fall back to Step 2, or is this a fatal error?

**Missing specification**: A repair/recovery decision tree:

```
IF eval_input schema mismatch:
  ├─ IF reference trace is wrong: RE-RUN step 2, rebuild dataset
  ├─ IF app interface changed: STOP, require manual review
  └─ IF eval_input was malformed: FIX items, revalidate
```

**Severity**: Low-Medium — affects only agents working with pre-existing apps; doesn't block new setup workflows.

---

### Step 5: Defensive Patterns — Edge Case and Brittleness Handling

#### Finding 5.1: No Safeguards Against Goodhart's Law in Evaluators

**Location**: eval-tests.md, SKILL.md §5

**Issue**: The skill teaches **selection** of evaluators (FactualityEval, custom prompts, etc.) but provides no guidance on **detecting misalignment** between the metric and the actual goal.

**Goodhart's Law manifestation in evals**:

- Agent creates an LLM-as-judge evaluator with a prompt that incentivizes quantity ("Response should be detailed"). Tests now optimize for length, not accuracy.
- Evaluator prompt focuses on structure ("Response contains all required fields") but app's real purpose is helpfulness. Tests pass with unhelpful-but-complete responses.
- Threshold is set to pass 80% of items. Teams start gaming by making eval_inputs easier, not fixing the app.

**Missing guidance**:

1. **Sanity checks post-Step 5**: Re-examine the evaluators against the original app purpose from Step 1. Are we measuring what matters?
2. **Threshold calibration validation**: The skill says to use `ScoreThreshold(threshold=0.7, pct=0.8)` but provides no method for agents to verify this is realistic.
3. **Metric-goal alignment checks**: Explicit prompts like: "Do passing tests correlate with user satisfaction? How would we know if the evaluator is wrong?"

**Example of failure mode**:

```python
# ❌ GOODHART'S LAW: metric optimization without real quality
create_llm_evaluator(
    name="Helpfulness",
    prompt_template="""
    Score 1.0 if the response is long and detailed.
    Score 0.0 if brief.
    """,  # Optimizes for length, not actual helpfulness
)

# Iterates toward longer, more verbose responses
# Users rate them as less helpful
```

**Missing**: Step 5 should include a verification substep that asks agents to re-test against the original use cases from Step 1 with real users or domain experts, not just automated metrics.

**Severity**: Critical — evaluators that pass tests but don't measure real quality undermine the entire workflow.

---

#### Finding 5.2: No Recovery Path When Tests Show "No Recorded Assertions"

**Location**: SKILL.md §5b

**Statement**: "A test that passes with no recorded evaluations is worse than a failing test — it gives false confidence. Debug until real scores appear."

**Problem**: The skill identifies this anti-pattern but provides no systematic recovery:

- What are the 3 most common causes (missing `await`, wrong import, trace capture disabled)?
- What's the debugging decision tree?
- When should agents give up and ask for help?

**Missing specification**: A checklist:

```
IF "No assert_pass / assert_dataset_pass calls recorded":
  ① Is test function `async def`? (not `def`)
  ② Is `await` before `assert_dataset_pass`?
  ③ Is `enable_storage()` called at app startup in runnable()?
  ④ Does `from_trace=last_llm_call` match actual span hierarchy?
  ⑤ If all ① ④: manual trace inspection required — show trace tree
```

**Severity**: Medium — agents can get stuck in unproductive debug loops.

---

#### Finding 5.3: Dataset Consistency Assumptions Between Steps 3–4

**Location**: SKILL.md Step 3 (verify), Step 4 (build)

**Issue**: Step 3 says "verify the utility function with the reference trace's eval_input." Step 4 says "create eval_input items that match the reference trace."

**Problem**: No explicit enforcement that the function's expected interface didn't change:

- If Step 3 reveals the function needs a new field (e.g., `conversation_context`), does Step 4 get re-planned?
- If eval_input schema changes post-Step 3, are all Step 4 items re-validated?
- Can agents proceed to Step 5 with inconsistent function interface and dataset?

**Missing specification**: A re-validation gate between Steps 4 and 5:

```
BEFORE Step 5:
  → Run utility function on 2–3 Step 4 eval_inputs
  → Confirm same struct/types as Step 3 verification
  → If mismatch: ROLLBACK to Step 3, repair, rebuild Step 4
```

**Severity**: Medium — affects large-codebase workflows where refactoring happens between steps.

---

#### Finding 5.4: Insufficient Guidance on Vague Eval Criteria

**Location**: SKILL.md §1 (define criteria), §5a (map to evaluators)

**Issue**: The skill says criteria should be "specific to the app's purpose," not "generic evaluator names." But provides no method for detecting when a criterion is still too vague.

**Examples of vague criteria that might slip through**:

- "Responses are helpful" — helpful in what way? To whom?
- "The app handles edge cases" — which edge cases?
- "Output is concise" — concise for a chatbot? A report generator? A code assistant?

**Missing specification**: A concreteness rubric for criteria:

```
GOOD criterion:
  "The agent identifies the caller's account before transferring."
  → Measurable: account ID appears in routing decision
  → Observable: captured by @observe on routing function
  → Falsifiable: can fail if agent skips verification

VAGUE criterion:
  "The agent is helpful."
  → NOT measurable: what counts as helpful?
  → Unfalsifiable: almost any response could be rationalized
```

**Severity**: Medium — agents frequently define criteria that can't be operationalized into evaluators.

---

### Step 5a: State Machines — Phases, Dependencies, and Getting Stuck

#### Finding 5a.1: Workflow Sequencing Assumptions

**Location**: SKILL.md "The workflow" section, all step descriptions

**State machine as described**:

```
Step 1 (understand) → Step 2 (instrument) → Step 3 (run_app function)
                                                ↓
                        Step 4 (dataset) ← Step 2 (reference trace)
                                                ↓
                        Step 5 (test) → [evaluation result] → Decision
                                                ↓
                    [Setup mode: STOP, ask user] — [Iteration mode: Step 6]
                                                ↓
                        Step 6 (investigate/iterate) → Step 4/5 (rebuild/re-run)
```

**Issue 1: Circular dependency in iteration**

In Step 6, agents are told: "investigate → fix → rebuild dataset if needed → re-run."

**Problem**: "Rebuild dataset if needed" is underspecified:

- What triggers a rebuild? (app behavior changed? evaluation criteria changed? just new test cases?)
- If rebuilt, do all Step 5 evaluators still apply, or do they need re-tuning?
- Can iteration loop indefinitely if evaluator thresholds are unrealistic?

**Missing specification**: Explicit conditions for branching in Step 6:

```
AFTER investigation:
  ├─ Cause is LLM prompt issue → FIX prompt, RERUN Step 5
  ├─ Cause is app code bug → FIX code, REBUILD Step 4, RERUN Step 5
  ├─ Cause is evaluator misalignment → REDEFINE criterion, RERUN Step 5
  ├─ Cause is unrealistic threshold → ADJUST ScoreThreshold, RERUN Step 5
  └─ Cause is dataset too small → ADD items to Step 4, RERUN Step 5
```

**Severity**: Medium — agents can loop through iteration without making progress.

---

#### Finding 5a.2: No Explicit Termination Condition for Iteration

**Location**: SKILL.md §6, investigation.md

**Issue**: The skill says to "repeat until passing or user is satisfied" but provides no objective measure of "passing."

**Problem**:

- What if tests reach 85% pass but plateau at 85%? When do we stop iterating?
- Is 70% pass rate acceptable, or is it a symptom of broken app + broken eval?
- Should agents ever recommend "this app isn't suitable for this eval approach" as a result?

**Missing specification**: Termination conditions:

```
STOP iteration if:
  ① Pass rate ≥ 95% (comprehensive test coverage, high confidence)
  ② Pass rate stable (e.g., last 3 iterations unchanged) AND user content (optimization complete)
  ③ >5 iterations without improvement (diminishing returns, re-evaluate approach)
  ④ Failure analysis reveals non-LLM bug (recommend traditional testing)
```

**Severity**: Low-Medium — affects iteration workflows; doesn't break setup.

---

#### Finding 5a.3: Mode Ambiguity ("Setup" vs. "Iteration")

**Location**: SKILL.md "The workflow" "Two modes" section

**Statement**: "If ambiguous: default to setup."

**Problem**: The distinction between modes is fuzzy in practice:

- User says "add tests" — is that setup (build from scratch) or iteration (add to existing setup)?
- User says "improve quality" — does that assume tests already exist?
- If partial setup exists (Steps 1–3 done, Step 4–5 incomplete), which mode?

**Current guidance is insufficient**:

```python
# Current logic in skill:
if "set up" or "add tests" or "add evals" → SETUP mode
elif "fix" or "improve" or "debug" → ITERATION mode
else → DEFAULT to SETUP
```

**Missing specification**: A mode detection flowchart:

```
IF previous run exists:
  ├─ IF tests pass → ITERATION mode (improve)
  ├─ IF tests fail → ITERATION mode (debug)
  └─ IF tests incomplete → SETUP mode (complete)
ELSE → SETUP mode (from scratch)
```

**Severity**: Low — mostly affects mode selection, not correctness; documented fallback exists.

---

### Step 5c: Parallel Path Symmetry — Consistency Across Scenarios

#### Finding 5c.1: Asymmetric Guidance for Deterministic vs. Non-Deterministic Outputs

**Location**: eval-tests.md §"Evaluator selection"

**Statement**: "For open-ended LLM text, never use ExactMatchEval."

**Guidance asymmetry issue**: The skill provides strong warnings about what NOT to do (e.g., "never ExactMatchEval on LLM output") but weaker positive guidance on what to do instead.

**Problem**: When should agents use each evaluator?

| Scenario | Skill says | Gap |
|----------|-----------|-----|
| Open-ended text + reference answer | "Use FactualityEval, ClosedQAEval" | ✓ Clear |
| Open-ended text, no reference | "Use standalone like FaithfulnessEval" | ✗ Vague — when Faithfulness vs. PossibleEval? |
| Deterministic classification | "Use ExactMatchEval, JSONDiffEval" | ✓ Clear |
| Style/tone criteria | "Use create_llm_evaluator with custom prompt" | ✓ Clear |
| Multi-aspect (factuality + tone) | Not explicitly covered | ✗ Missing — should use multiple evaluators in one test? Separate test functions? |

**Missing specification**: Decision table for multi-aspect evaluation:

```
Multi-aspect evaluation:
  ├─ SAME test function, multiple evaluators (measures independence)
  │  └─ Use: await assert_dataset_pass(..., evaluators=[Eval1(), Eval2(), Eval3()])
  ├─ SEPARATE test functions per aspect (clearer failure messages)
  │  └─ Use: async def test_factuality(), async def test_style(), etc.
  └─ MIXING approaches: risk of inconsistent pass criteria
     └─ Avoid: don't mix patterns in one skill
```

**Severity**: Low-Medium — affects organization of test suites, not correctness.

---

#### Finding 5c.2: Unequal Guidance for Mock Implementation Strategies

**Location**: run-harness-patterns.md §"FastAPI / Web Server"

**Strategies presented**:

1. **Subprocess + HTTP** — launch patched server as subprocess, use `httpx` to send requests
2. **In-process + TestClient** — use FastAPI's `TestClient` directly
3. (Implicit) Direct function call for non-web apps

**Problem**: Guidance is incomplete for non-FastAPI web frameworks and older app types:

- Flask apps: guidance present? (NO — only FastAPI/uvicorn explicitly covered)
- Django: covered? (NO)
- CLI + subprocess: covered? (NO — mentioned in example, not detailed)
- Function-based (no server): coverage unclear

**Missing specification**: Parallel guidance for common frameworks:

```
Web framework → Entry point pattern:
  ├─ FastAPI → TestClient or subprocess (documented ✓)
  ├─ Flask → TestClient(app) (missing)
  ├─ Django → test.Client (missing)
  ├─ FastAPI + uvicorn.run() → subprocess required (partially documented)
  └─ Async ASGI framework → ASGITransport (not covered)

CLI app → subprocess.run() (mentioned, not detailed)
Function → direct import + call (implicit, should be explicit)
```

**Severity**: Medium — new agents must reverse-engineer patterns for non-FastAPI apps.

---

### Step 6: Domain Knowledge — Goodhart's Law, Eval Brittleness, Overfitting

#### Finding 6.1: Limited Discussion of Goodhart's Law in Evals

**Location**: SKILL.md (all), investigation.md (root-cause patterns)

**Background**: Goodhart's Law: "When a measure becomes a target, it ceases to be a good measure."

**In eval context**: When teams set ScoreThreshold(threshold=0.7, pct=0.8), they create an incentive to optimize that metric. If the metric is poorly chosen, optimization moves away from actual quality.

**Missing guidance**: The skill should include a "red flag" section for Goodhart's Law manifestations:

```
⚠️ GOODHART'S LAW RED FLAGS:

1. Evaluator is gaming-vulnerable:
   - "Response is longer" → optimizes for verbosity, not quality
   - "Follows exact format" → optimizes for structure over content
   - "Mentions topic N times" → optimizes for keyword stuffing

2. Threshold is arbitrary:
   - "0.7 feels like a B+" → no statistical basis
   - Threshold matches nothing real (no user benchmark, no baseline)

3. Iteration focuses on metrics, not code:
   - "Let's improve the evaluator" instead of "let's fix the bug"
   - "Adjust threshold to 0.6" instead of "fix the prompt"

4. Tests pass, but users complain:
   - Classic sign: metric and goal have decoupled
```

**Severity**: Critical — Goodhart's Law can render an entire eval suite meaningless while tests pass.

---

#### Finding 6.2: Brittleness of Reference Trace as Single Source of Truth

**Location**: SKILL.md §2c, dataset-generation.md §"Matching the reference trace shape"

**Issue**: Step 2 produces ONE reference trace, and Step 4 datasets are built to match that shape.

**Problem**: A single trace may not represent the full variation the app actually handles:

- Reference trace shows `conversation_history: []` (empty). Real runs might have 20 items. Does dataset include long histories?
- Reference trace shows one customer profile shape. Are other shapes tested?
- Reference trace shows "happy path" (no errors). Are failure paths covered?

**Missing specification**: Explicit guidance on trace adequacy:

```
AFTER Step 2 reference trace:
  ① Does trace show: happy path? (yes) error path? (?) extreme values? (?)
  ② Are there multiple realistic data variations not in the trace?
  ③ If YES to ①/② → run 2–3 additional traces with varied inputs BEFORE Step 4
  ④ Synthesize representative shapes from all traces
```

**Severity**: Medium — can miss data shapes, leading to brittleness in production.

---

#### Finding 6.3: No Overfitting Detection or Prevention

**Location**: SKILL.md §4 (dataset), §5 (evaluation), §6 (investigation)

**Issue**: The skill creates small, curated datasets (implied: 5–20 items) for testing. These are golden datasets, not large-scale benchmarks.

**Problem**: Agents can (and often do) overfit:

- Dataset items are cherry-picked to match the app's current behavior
- Expected_output values are written to match trace observations, not independent criteria
- Iteration converges to "tests pass" not "app is actually good"

**Example of overfitting**:

```python
# ❌ OVERFITTED DATASET
Evaluable(
    eval_input={"question": "What is π?"},
    expected_output="π is approximately 3.14159"  # Copied from actual trace
)
# Tests will pass because we're comparing against the output we already have

# ✓ CORRECT: Independent criteria
Evaluable(
    eval_input={"question": "What is π?"},
    expected_output="A number between 3 and 4"  # Criteria known independently
)
```

**Missing specification**: Anti-overfitting checklist:

```
BEFORE Step 5:
  ① Is expected_output independent of eval_output? (not copied from traces)
  ② Would expected_output be wrong if eval_output is wrong? (or is it tautology?)
  ③ Would a human QA engineer write the same expected_output? (not AI-generated)
  ④ Could dataset items have been written BEFORE seeing traces?
```

**Severity**: High — overfitting defeats the purpose of eval-based testing.

---

### Step 7 (Implicit): Verification — Does the Skill Verify Its Own Output Quality?

#### Finding 7.1: No Post-Step-5 Verification Requirement

**Location**: SKILL.md §5b (checkpoint), overall workflow

**Issue**: After tests run, the checkpoint says "Report results and ask: want to iterate?"

**Problem**: No mandatory verification that the tests are actually measuring quality:

- Did any tests fail? (If 0 failures, is dataset too easy or app too good?)
- Are scores well-distributed? (If all 100% or all 0%, evaluator might be broken)
- Do passing/failing items make intuitive sense? (Sanity check)

**Missing specification**: A verification substep:

```
AFTER Step 5 test run, BEFORE asking user:

1. Check test count: N ≥ 5? (fewer items = under-sampled)
2. Check score distribution:
   - All 100%? → Evaluator too lenient or dataset too easy
   - All 0%? → Evaluator too strict or dataset incompatible
   - Median 50–80%? → ✓ Healthy distribution
3. Spot-check 2 failures:
   - Do failure reasons make sense? (Evaluator reasoning)
   - Are the failures real bugs or eval mis-specced?
4. Check threshold realism:
   - Is pct=0.8 realistic for this app/dataset pair?
   - Do passing items correlate with "good app behavior"?
```

**Severity**: Medium — bad tests can pass verification checkpoint and mislead users.

---

#### Finding 7.2: Missing Verification of Evaluator Quality

**Location**: eval-tests.md (evaluator selection), investigation.md (root cause patterns)

**Issue**: The skill teaches agents to SELECT evaluators but not to VERIFY they work.

**Problem**: Evaluators can be silently wrong:

```python
# ❌ WRONG EVALUATOR
create_llm_evaluator(
    name="Factuality",
    prompt_template="""
    Score 1.0 if response is longer than input.
    Score 0.0 otherwise.
    """  # Measures length, not factuality — silently broken
)
```

**Missing specification**: Evaluator verification (before large-scale runs):

```
BEFORE running full test suite:
  → Test each evaluator on 2–3 hand-picked items where the score is known
  → Confirm evaluator produces expected scores
  → Check evaluator's reasoning makes sense
  → Example:
    input: "What is 2+2?"
    expected_output: "4"
    eval_output: "The answer is 4."
    → FactualityEval should score ~1.0 ✓
    → If it scores 0.0, evaluator is broken
```

**Severity**: Medium-High — broken evaluators produce false confidence.

---

## Assessment of Signal Quality

### Strengths

1. **Clear step-by-step decomposition**: The workflow is well-sequenced with explicit dependencies.
2. **Reference documentation is comprehensive**: Run-harness patterns, instrumentation rules, API references are detailed.
3. **Anti-patterns are identified**: The skill explicitly calls out common mistakes ("never use ExactMatchEval on LLM text").
4. **Checkpoints are placed correctly**: Each step has a verification gate before proceeding.
5. **Grounded in real experience**: The skill shows knowledge of actual eval pitfalls (e.g., "test that passes with no recorded assertions is worse than a failing test").

### Weaknesses

1. **Specifications are ambiguous at the boundaries**: When expected_output semantics change or dataset structure drifts, agents must infer recovery paths.
2. **Defensive patterns are incomplete**: Goodhart's Law is not addressed; overfitting is not prevented.
3. **State machine has implicit assumptions**: The iteration loop (Step 6) assumes progress without defining termination.
4. **Parallel path symmetry is broken**: Guidance for Flask/Django/CLI apps is sparse; multi-aspect evaluation is underspecified.
5. **Signal quality is not verified**: No mandatory checks that tests actually measure quality vs. gaming metrics.

---

## Ratings per Playbook Step

| Step | Aspect | Rating | Notes |
|------|--------|--------|-------|
| 4 | **Specification Clarity** | 6.5/10 | Ambiguous expected_output semantics; diversity validation underspecified; no recovery paths. |
| 5 | **Defensive Patterns** | 6.0/10 | Good safeguards against implementation mistakes; poor safeguards against Goodhart's Law and overfitting. |
| 5a | **State Machines** | 7.0/10 | Clear step sequencing; circular dependencies in iteration; no termination condition. |
| 5c | **Parallel Path Symmetry** | 6.5/10 | Asymmetric guidance for evaluator selection; incomplete coverage of app types. |
| 6 | **Domain Knowledge** | 5.5/10 | Limited discussion of Goodhart's Law; brittleness of reference trace acknowledged but not mitigated; overfitting not addressed. |
| 7 | **Verification** | 5.5/10 | No post-test verification of suite quality; no evaluator sanity checks; no overfitting detection. |
| | **OVERALL** | **6.3/10** | Pedagogically sound; implementation gaps in brittleness handling and quality verification. |

---

## Recommendations

### High Priority (Brittleness & Safety)

1. **Add a "Goodhart's Law red flags" section** to the main SKILL.md, with examples of metric gaming and how to detect it.

2. **Implement expected_output verification before dataset creation**:
   ```
   BEFORE Step 4:
     → For each eval_input, confirm which evaluator(s) will consume its expected_output
     → Verify evaluator choice is unambiguous (not mixed semantics in one dataset)
     → Generate expected_output only AFTER deciding on evaluators
   ```

3. **Require trace adequacy assessment**:
   ```
   AFTER Step 2 reference trace:
     → Run 2–3 additional traces with varied inputs
     → Confirm dataset covers happy path, error path, edge cases
     → Proceed to Step 4 only if trace coverage is adequate
   ```

4. **Add mandatory post-test verification**:
   ```
   AFTER Step 5 test run:
     → Verify test count ≥ 5 and score distribution is healthy (not all 0% or 100%)
     → Spot-check 2 failing items for evaluator correctness
     → Confirm threshold realism against score distribution
     → Proceed to report only if verification passes
   ```

### Medium Priority (Completeness)

5. **Define termination condition for iteration** (Step 6):
   - Pass rate ≥ 95%, or
   - Plateau detected (3 consecutive iterations unchanged), or
   - Iteration count ≥ 5 without improvement

6. **Expand run-harness-patterns** to cover Flask, Django, CLI apps with explicit examples.

7. **Add anti-overfitting checklist** to dataset-generation.md with verification of expected_output independence.

8. **Clarify mode detection logic** with explicit flowchart for "setup vs. iteration" ambiguity.

### Low Priority (Documentation)

9. **Add failure recovery decision tree** to investigation.md for common stuck states.

10. **Expand eval-tests guidance** for multi-aspect evaluation (multiple evaluators in single test vs. separate test functions).

---

## Conclusion

The **eval-driven-dev skill is a strong foundation** for setting up LLM evaluation infrastructure. It demonstrates real domain knowledge and provides clear, actionable steps. However, **it prioritizes implementation completeness over brittleness detection and quality verification.** The most critical gap is the lack of safeguards against Goodhart's Law and overfitting — agents can produce tests that pass while measuring the wrong thing.

**Recommended usage**:

- **With experienced QA engineers**: Skill works well; they will naturally add missing verifications.
- **With inexperienced agents**: Skill needs the high-priority recommendations (expected_output verification, trace adequacy, post-test verification) to avoid false-positive tests.

**Overall assessment**: **6.3/10** — Pedagogically solid, but defensive gaps that require augmentation before recommending to agents without human oversight.
