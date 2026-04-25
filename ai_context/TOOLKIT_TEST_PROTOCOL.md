# TOOLKIT.md Test Protocol

> Release-gate review for `TOOLKIT.md` and the orientation docs that reference it. Applies the same empirical-loop discipline that `IMPROVEMENT_LOOP.md` describes for the playbook itself, but to the documentation: surface problems through a panel of independent readers, fix them, re-test until convergence.

## Purpose

Documentation, like code, can drift. Claims become stale, vocabulary diverges from what's actually in the codebase, and overclaims accumulate when no one is checking. This protocol verifies that TOOLKIT.md accurately communicates what the Quality Playbook does and does not do — through panels of LLM sub-agents reading the doc as different reader personas, with a structured rubric for evaluating their responses.

This is the docs analogue of `IMPROVEMENT_LOOP.md`'s benchmark-driven calibration. There, the Check step is benchmark recovery against ground truth. Here, the Check step is whether the doc supports correct answers across reader personas.

## When to run

Release gate, not CI. Run before each version bump when TOOLKIT.md or related orientation docs (IMPROVEMENT_LOOP.md, README.md, DEVELOPMENT_CONTEXT.md) have changed.

The cost is high — M models × N personas × actual reading + response time — and the doc does not change every commit. Running constantly without acting on findings degrades the signal.

## Test method

A panel of three LLM sub-agents (Task tool sub-agents in the orchestrating Cowork session, or three separate Cowork chats) is given **only TOOLKIT.md** as context — no other QPB source files, no SKILL.md, no benchmarks. Each sub-agent is given one persona prompt and produces a response. The orchestrator (top-level agent or human) evaluates each response against the rubric below.

The "TOOLKIT.md only" constraint is load-bearing: we are testing whether the doc stands alone for an LLM that does not have the source. If the doc is fine but the agent reads source files to answer, the test is invalid — pass it the doc, restrict tool access, no Bash, no Read on other files. Sub-agents can be given the option to read `IMPROVEMENT_LOOP.md` and `TOOLKIT_TEST_PROTOCOL.md` (this file) since these are part of the orientation-doc surface, but must not read SKILL.md, references/, bin/, or any benchmark output.

## Personas

These prompts simulate distinct reader populations. Each is designed to surface a specific failure mode if the doc has one. Add personas as new failure modes are discovered; do not remove personas without recording why.

### Persona 1 — The skeptical adversarial reviewer

> Read TOOLKIT.md as a hostile reviewer. What does the Quality Playbook actually guarantee? Where does the doc overclaim? Cite specific passages where the language outruns the evidence. Be specific about precision-vs-recall, process-vs-outcome, and any quantitative claims you cannot verify from the doc itself.

Tests: overclaiming, unsourced numerics, process-vs-outcome conflation.

### Persona 2 — The Rails adopter

> I'm the lead engineer on a Rails 7 monolith. We have ~80% scaffolded CRUD controllers and a small set of bespoke service modules handling payments and inventory. I'm thinking of running the Quality Playbook against our codebase. Should I? What part should I run it against, and what part should I skip?

Tests: scope-limit awareness; "where this adds little" surfacing.

### Persona 3 — The infrastructure adopter

> We're a Terraform shop with about 50 modules and a small Helm chart. Will the Quality Playbook find misconfigurations and policy violations in our infrastructure code?

Tests: scope-limit awareness; declarative-IaC exclusion.

### Persona 4 — The zero-bug interpreter

> We ran the Quality Playbook on our microservice and it found zero confirmed bugs. Does that mean the code is clean and we can ship?

Tests: process-vs-outcome separation; recall-vs-precision distinction; agent-quality requirement awareness.

### Persona 5 — The mechanical-extraction skeptic

> Walk me through how mechanical extraction proves the code is correct. The doc says it's an anti-hallucination measure — what does it actually prove and what does it not prove?

Tests: shape-vs-semantics distinction.

### Persona 6 — The model-quality challenger

> We've been running the Quality Playbook in Cursor with auto-mode selecting the model. We get clean artifacts, all the gates pass, but no real bugs are found. The codebase is known to have bugs. What's wrong?

Tests: model-requirement awareness; surface-area-as-theater risk articulation; pass-process / fail-recall identification.

### Persona 7 — The TDD-NOT_RUN edge case

> Our test runner doesn't work in our CI environment. The TDD logs show NOT_RUN. Are the bugs still verified? Can I trust the bug reports?

Tests: NOT_RUN-as-acknowledgment-not-verification distinction.

### Persona 8 — The methodology challenger

> How do you know the Quality Playbook works? What evidence supports the claim that it finds real bugs? What's your validation method?

Tests: empirical-loop awareness; benchmark recovery framing; honest "moving toward statistical control" framing rather than overclaiming.

### Persona 9 — The vocabulary trap

> Tell me about the two axes of the playbook. What are they and how do they relate?

Tests: vocabulary correctness. The right answer involves the two axes of *improvement* (process compliance + outcome recall) per IMPROVEMENT_LOOP.md — NOT external syntheses (like "structured ↔ freeform" + "recall ↔ rigor") which describe design space, not improvement methodology. If a panelist invents axes that aren't in the doc, the doc has a vocabulary problem; if a panelist correctly distinguishes "improvement methodology axes" from "internal design tensions," the doc is doing its job.

### Persona 10 — The summary overclaim trap

> Summarize what the Quality Playbook guarantees in 100 words.

Tests: overclaim under length pressure. A correct summary names the process-vs-outcome split, names the agent-quality requirement, names the scope limits. A sloppy summary reaches for "finds bugs in any codebase."

### Persona 11 — The iteration-strategy explainer

> Explain the difference between the gap and unfiltered iteration strategies. Why are they separate? What kinds of bugs does each find?

Tests: canonical vocabulary preservation; doc fidelity to the four-strategy taxonomy.

### Persona 12 — The improvement-method asker

> Is the Quality Playbook itself quality-engineered? How is it improved between releases?

Tests: IMPROVEMENT_LOOP.md awareness; honest "moving toward statistical control" framing; benchmark-driven calibration vocabulary.

### Persona 13 — The categorization-asker (post-v1.5.3)

> The bug report has tags like "standout," "confirmed," "probable," "candidate." What do these mean? Which should I prioritize?

Tests: categorization-tier vocabulary correctness; standout-as-earned framing.

(Activate Persona 13 after v1.5.3 ships the categorization tagging.)

## Rubric

For each persona response, evaluate on three dimensions:

1. **Correctness.** Does the response make true claims? Does it surface the right caveats? Does it preserve the canonical vocabulary?
2. **Completeness.** Does the response surface the relevant scope limits, edge cases, and prerequisites? Or does it answer at face value without naming what's missing?
3. **Doc-grounded.** Can each claim in the response be traced back to a specific passage in TOOLKIT.md (or IMPROVEMENT_LOOP.md / TOOLKIT_TEST_PROTOCOL.md when in scope)? If a panelist makes a true claim that the doc doesn't actually support, the doc is missing the support.

Each persona response gets one of four verdicts:

- **PASS** — correct, complete, doc-grounded.
- **DOC GAP** — response is correct but the doc doesn't actually support all the claims; doc needs to add the support.
- **DOC WRONG** — response surfaces a claim that conflicts with the doc, or the doc led the panelist to a wrong claim.
- **PANELIST DRIFT** — response goes off the doc into general LLM knowledge; doc is fine but the test setup needs tightening (was the panelist actually restricted to TOOLKIT.md?).

## Convergence criterion

The protocol has converged when, for one full round across all active personas, no new DOC GAP or DOC WRONG verdicts are produced — AND every DOC GAP / DOC WRONG verdict from previous rounds has been demonstrably fixed (re-run the persona prompts that surfaced them; the new responses give a PASS verdict).

Note: convergence is NOT "all panelists agree." Agreement optimizes for plausibility, not correctness. We care about whether the doc supports the right answers, not whether reviewers happen to land on the same answer. A round where all three panelists land on the same wrong answer is a failure, not a convergence.

## Roles and orchestration

The protocol is best run with a top-level agent orchestrating sub-agents:

1. The top-level agent fans out the persona prompts to N sub-agents (Task tool with restricted Read access, separate Cowork sessions, or three Council-of-Three terminals run via `gh copilot --model …`).
2. Each sub-agent is given TOOLKIT.md (and optionally IMPROVEMENT_LOOP.md / this file) as context, plus its persona prompt.
3. Sub-agents return responses to the top-level agent.
4. The top-level agent applies the rubric, identifies DOC GAP / DOC WRONG findings, and proposes fixes.
5. The human (Andrew) reviews the proposed fixes, approves or rejects each.
6. The top-level agent applies approved fixes to the relevant orientation doc.
7. Re-run the protocol on the personas that produced findings; verify PASS.
8. Repeat until convergence.

For Council-of-Three execution, the canonical commands follow the workspace `AGENTS.md` Council protocol but with one substantive difference: the working directory should be the orientation-docs surface, not the QPB source repo, since panelists must not have access to source files. Suggested form:

```zsh
cd /Users/andrewstellman/Documents/QPB/ai_context && \
  gh copilot --model <MODEL> --prompt "$(cat ../Reviews/toolkit_test_persona_<N>.md)" \
  | tee "/Users/andrewstellman/Documents/AI-Driven Development/Quality Playbook/Reviews/toolkit_test_runs/<timestamp>/<persona-id>_<MODEL>.md"
```

The acceptance check from Council-of-Three Invocation still applies: each response file should show actual Reads against `TOOLKIT.md`, IMPROVEMENT_LOOP.md, or this file — not against SKILL.md, bin/, or .github/skills/. If a response file shows source-file Reads, the panelist was outside the test envelope and the run is invalid.

## Output artifacts

Each protocol run produces:

- `Quality Playbook/Reviews/toolkit_test_runs/<timestamp>/` directory under the workspace folder (kept out of QPB to avoid polluting the repo with review artifacts; same convention as the code-review responses).
- One `<persona-id>_<panelist-model>.md` file per response.
- One `_rubric.md` file with the verdicts and proposed fixes per persona.
- One `_summary.md` file describing whether the round converged, what was changed, and which personas need re-running.

When the protocol converges, archive the run as the release-gate evidence for that version bump. Cite the convergence run in the release notes.

## Test prompt files

Persona prompts should be saved as standalone files so they can be passed to `gh copilot --prompt "$(cat ...)"` without quoting issues. Suggested location:

`Quality Playbook/Reviews/toolkit_test_personas/persona_<N>_<short_name>.md`

Each file contains:

```markdown
# Toolkit Test — Persona <N>: <short name>

**Reviewers requested:** `gpt-5.4`, `gpt-5.3-codex`, `claude-sonnet-4.6` (each outer model spawns its own three-reviewer panel internally).

**Constraint:** Read only TOOLKIT.md, IMPROVEMENT_LOOP.md, and TOOLKIT_TEST_PROTOCOL.md. Do not Read or Bash into SKILL.md, bin/, .github/skills/, references/, or any benchmark output. If a question requires information beyond the orientation docs, say "the doc does not support this" rather than searching.

<persona prompt body>
```

The nested-panel header is required for the same reason as in code review: each outer model spawns its own three-reviewer panel internally, giving 9 perspectives per persona per round rather than 3. This is non-negotiable; flat-3 mode collapses inter-model diversity.

## First-run notes

The first invocation of this protocol on TOOLKIT.md after the v1.5.2 honesty pass should treat any DOC GAP / DOC WRONG findings as v1.5.2-blocking. After the first convergence, subsequent runs are release-gate (not blocking unless severity warrants).
