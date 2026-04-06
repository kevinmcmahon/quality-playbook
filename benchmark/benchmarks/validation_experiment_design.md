# Validation Experiment: Requirements-as-Prompt (4 conditions)

## Purpose

Test whether providing testable requirements derived from documentation helps find defects that structural code review (human or AI) cannot reach. This is NOT about beating the control at everything — it's about filling the 35% gap where intent-based defects live.

The experiment also tests whether the mechanism works at different levels of abstraction: precise requirements (where we essentially tell the model the answer) vs abstract requirement principles (what the playbook would actually generate).

## Framing

AI code review tools (Copilot code review, CodeRabbit, etc.) and generic prompts all do the same thing: read the code, spot structural anomalies. They score ~65% on known defects, which is useful. But they can't know what the software is *supposed to do*. The 35% they miss are intent violations: configuration semantics, protocol contracts, security policy interactions, shutdown ordering guarantees.

The playbook's value is the specification — the requirements document derived from intent sources. This experiment tests whether that specification actually helps find the defects that structural review misses.

## Background

From the v3 scoring:
- Control: 38/58 (65.5%), 11/16 derivable defects found
- v1.2.12: 36/58 (62.1%), 10/16 derivable defects found
- v1.2.13: 28/58 (48.3%), 8/16 derivable defects found

5 derivable defects missed by control: NSQ-14, NSQ-36, NSQ-39, NSQ-44, NSQ-55
3 derivable defects missed by ALL conditions: NSQ-36, NSQ-39, NSQ-44

## Requirement Derivation Results

From documentation only (README, ChangeLog, source comments, Go stdlib docs):

| Classification | Count | % | Description |
|---|---|---|---|
| **(a) Explicit** | 7 | 29% | Requirement clearly stated in docs/changelog |
| **(b) Inferable** | 9 | 38% | Derivable from docs but not explicit |
| **(c) Insufficient** | 8 | 33% | Docs lack signal; need broader intent sources |

**Key finding**: 67% of defects in the target categories have requirements derivable from documentation — even for a project with sparse docs. The (c) group is mostly general programming practices and emergent interaction bugs, where community intent sources (language docs, Stack Overflow) would close the gap.

## Four Conditions

### A. Control (generic review)
Same prompt as the original benchmark. "Review for bugs. Be thorough." No requirements, no focus areas.

### B. Specific Requirements
Precise testable requirements per defect. Example for NSQ-39: "Worker ID validation must reject values >= 1024 (2^10). The GUID format uses a 10-bit worker ID field, so valid IDs are [0, 1023]. If validation accepts [0, 4096), IDs 1024-4095 will silently produce GUID collisions."

**Note**: This is the strongest version of the mechanism. It essentially tells the model the answer. Real-world requirements would be less precise. Detection rates from this condition represent an upper bound.

### C. Abstract Requirements
Higher-abstraction requirement principles — what the playbook would actually generate. Example for NSQ-39: "Validation ranges for configuration parameters must match the actual bit width or storage capacity of the field they populate. Accepting values wider than the destination field causes silent truncation or collision."

**This is the key condition.** If abstract requirements find defects the control misses, the playbook's architecture is validated at a realistic abstraction level.

### D. v1.2.12 (focus areas)
The v1.2.12 protocol with 7 named focus areas and guardrails. Same prompt structure as the benchmark.

## Defect Selection (16 defects)

| Defect | Category | Class | Baseline | Key Question |
|--------|----------|-------|----------|---|
| NSQ-04 | resource-lifecycle | (a) | FOUND | Retention test |
| NSQ-12 | api-contract | (a) | FOUND | Retention test |
| **NSQ-14** | input-validation | (a) | **MISSED** | Can requirements recover? |
| NSQ-19 | api-contract | (b) | FOUND | Retention test |
| NSQ-22 | resource-lifecycle | (b) | FOUND | Retention test |
| NSQ-33 | security | (a) | FOUND | Retention test |
| **NSQ-36** | input-validation | (a) | **MISSED ALL** | Hardest test — nobody found this |
| NSQ-37 | api-contract | (b) | FOUND | Retention test |
| **NSQ-39** | input-validation | (b) | **MISSED ALL** | Hardest test — nobody found this |
| NSQ-41 | security | (b) | FOUND | Retention test |
| NSQ-42 | api-contract | (b) | FOUND | Retention test |
| **NSQ-44** | security | (a) | **MISSED ALL** | Hardest test — nobody found this |
| NSQ-47 | resource-lifecycle | (a) | FOUND | Retention test |
| NSQ-48 | resource-lifecycle | (b) | FOUND | Retention test |
| NSQ-50 | resource-lifecycle | (b) | FOUND | Retention test |
| **NSQ-55** | api-contract | (b) | **MISSED** | Can requirements recover? |

## Success Criteria

The experiment is NOT about beating the control overall. It's about finding the 35%.

**Primary question**: Do requirements-as-prompt find defects in the gap that structural review can't reach?

1. **Specific requirements (upper bound)**: Should find at least 4/5 missed defects. If it can't find them even when told the answer, requirements-as-prompt doesn't work at all.

2. **Abstract requirements (realistic test)**: Should find at least 2/5 missed defects. This is what the playbook would actually generate. If abstract principles guide the model to the right bugs, the architecture is validated.

3. **Retention**: Neither requirements condition should lose more than 2 of the 11 baseline-found defects.

4. **The 3 that nobody found** (NSQ-36, NSQ-39, NSQ-44): If specific requirements find 2+ of these, and abstract requirements find 1+, that's the proof point. These are defects invisible to any amount of code reading without knowing the requirement.

## Running the Experiment

### Files

All experiment files are in `experiments/req_validation/`:

```
experiments/req_validation/
├── generate_prompts.py      # Generates all 64 prompt files
├── run_experiment.sh         # Copilot CLI automation (run from NSQ repo root)
├── score_experiment.py       # Automated scoring against ground truth
├── prompts_control/          # 16 control prompts
├── prompts_specific/         # 16 specific-requirement prompts
├── prompts_abstract/         # 16 abstract-requirement prompts
├── prompts_v1212/            # 16 v1.2.12 focus-area prompts
├── reviews_*/                # Model-generated review files (output)
└── outputs_*/                # Raw Copilot CLI output
```

### Execution

```bash
# From the NSQ repo root:
cd /path/to/nsq-repo
bash /path/to/experiments/req_validation/run_experiment.sh

# Or run one condition at a time:
bash /path/to/experiments/req_validation/run_experiment.sh control
bash /path/to/experiments/req_validation/run_experiment.sh specific
bash /path/to/experiments/req_validation/run_experiment.sh abstract
bash /path/to/experiments/req_validation/run_experiment.sh v1212
```

### Scoring

```bash
cd experiments/req_validation
python3 score_experiment.py
```

The scorer uses the same defect definitions and scoring guidance from `nsq_defects_v2.json`. Produces a comparison table and identifies which missed defects were recovered.

## What the Results Tell Us

**If specific ≫ abstract ≫ control**: The mechanism works but only when you hand the model precise requirements. The playbook needs to generate very specific requirements, which means the intent harvesting pipeline must be high-fidelity.

**If specific ≈ abstract ≫ control**: The mechanism works even at realistic abstraction levels. The playbook's value is in the direction it provides (what class of thing to check), not the precision. This is the best outcome.

**If specific ≫ control but abstract ≈ control**: Abstract principles don't help — the model already checks those. Only precise "check THIS specific thing" works. The playbook would need to generate very targeted requirements, which limits scalability.

**If specific ≈ abstract ≈ control**: Requirements-as-prompt doesn't work. The model either already finds these bugs or can't find them regardless of prompting. Back to the drawing board.

**Pay most attention to NSQ-36, NSQ-39, NSQ-44.** These are the defects that ALL conditions in the original benchmark missed. If requirements help find even one of them, that's a validated contribution to the 35% gap.

---

## Part 2: Clean Two-Pass (cross-contamination test)

### Rationale

Previous experiments showed that combining structural review ("find bugs") with other guidance (focus areas, requirements) caused cross-contamination — the model compromised on both tasks. v1.2.13 with 7 focus areas scored worse (48.3%) than the control (65.5%). The Part 1 specific and abstract prompts include "Also report any other bugs you find," which is the same mixed instruction.

Part 2 tests clean separation: requirements-only prompts with NO general review instruction. The model's only job is to answer "does this code satisfy this requirement?" — not to also do a general review.

In a real deployment, these would be two separate passes:
- Pass 1: Structural review (the control — what every AI code review tool already does)
- Pass 2: Requirements verification (the playbook's unique contribution)

Results combine: Pass 1 catches structural anomalies, Pass 2 catches intent violations. No cross-contamination.

### Part 2 Conditions

- **clean_specific** — precise requirements, requirements-only prompt, no general review
- **clean_abstract** — abstract principles, requirements-only prompt, no general review

### Running Part 2

```bash
cd nsq-req-validation
bash run_experiment_part2.sh                # both conditions
bash run_experiment_part2.sh clean_specific  # one at a time
```

### What Part 2 Adds

The comparison between Part 1 (mixed) and Part 2 (clean) on the same requirements tells us whether cross-contamination is real and how much it costs. If clean_specific > specific, the model is better at requirements checking when that's its only job. If clean_abstract > abstract, the same applies at realistic abstraction levels.

The scorer automatically compares Part 1 vs Part 2 when both have data.

### Early Observations

From partial Part 1 control results (10/16 runs): the control found NSQ-39 (worker ID range vs bit width) — a defect that no condition found in the original 57-review benchmark. This is likely because the per-defect experiment gives the model just 2 files to review instead of a broader set, providing tighter focus. This is a confound worth noting: the experiment's file scoping is different from the benchmark's.
