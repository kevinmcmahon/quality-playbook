# Experiment: Multi-Pass Requirement Derivation and Verification

**Status: Complete**

## Background

The direct review experiment proved that requirements find bugs cold review misses — all three defects invisible to structural review (NSQ-36, NSQ-39, NSQ-44) became trivially findable with specific requirements. But those requirements were written by someone who already knew the bugs. The playbook's value depends on the full pipeline: derive requirements from documentation, then verify code against them.

This experiment tests the complete pipeline end-to-end: can a model, reading only documentation and source structure (no knowledge of specific defects), derive requirements specific enough to catch the bugs that cold review misses?

The requirement derivation analysis showed that 67% of defects in the target categories have requirements derivable from NSQ's documentation. But "derivable by a human who knows what to look for" is different from "derivable by a model reading the docs cold." This experiment measures the gap.

## Hypothesis

A model reading NSQ's documentation, README, ChangeLog, source comments, and configuration structs — with no knowledge of specific defects — can derive testable requirements that, when used as the basis for code verification, catch defects invisible to structural review.

Specifically: the pipeline should find at least one of NSQ-36, NSQ-39, or NSQ-44 — the three defects that all conditions in the 57-review benchmark missed.

## Method

### Subsystem Focus

Two subsystems selected to cover all three target defects without being so narrow that the model is pointed at the exact lines:

1. **nsqd configuration and startup**: nsqd/nsqd.go, nsqd/options.go, nsqd/guid.go
   - Covers NSQ-36 (E2E percentile validation missing) and NSQ-39 (worker ID bit width mismatch)
   - ~1,089 lines of Go code

2. **TLS and authentication path**: nsqd/nsqd.go (TLS setup), internal/auth/authorizations.go
   - Covers NSQ-44 (auth server ignores configured root CA)
   - ~958 lines of Go code (overlap with subsystem 1 on nsqd.go)

### Four Passes

**Pass 1 — Requirement Derivation**: Read documentation sources (README, ChangeLog, source comments, config structs). For each subsystem, derive a list of testable requirements organized by category (input validation, security policy propagation, resource lifecycle, API contracts). No knowledge of specific defects.

**Pass 1.5 — Requirement Filtering** (later determined to be counterproductive): Review the derived requirements and remove those that are trivially satisfied or too vague to test. Keep only requirements that are specific, testable, and nontrivial.

**Pass 2 — Requirement Verification**: Read the requirements and the source code. For each requirement, either show the code that satisfies it or explain specifically why it is not satisfied. Report violations with file, line, and evidence.

**Pass 3 — Cross-Requirement Consistency Check**: Compare pairs of requirements that reference the same field, constant, range, or security policy. Identify contradictions where two individually-satisfied requirements are mutually inconsistent. This catches bugs that live in the gap between two correct pieces of code.

### Commit Selection

The three target bugs don't all coexist at a single commit (NSQ-36 was fixed before NSQ-44's pre-fix). The experiment uses:

- **Subsystem 1** at commit `98fbcd1`: Both NSQ-36 (no percentile validation) and NSQ-39 (4096 vs 1024) are present
- **Subsystem 2** at commit `1d183d9`: NSQ-44 (auth server ignores root CA) is present
- **Pass 1** reads documentation from `98fbcd1` (docs are relatively stable across these commits)

The run script handles the checkout logistics.

### Controls

- The prompts contain NO mention of specific defects, bug IDs, or fix commits
- The model reads documentation and source structure only — no test files, no git history
- ChangeLog is available (it documents features and behaviors, not just bug fixes) — this is realistic since a quality engineer would read release notes
- Each pass runs in a fresh Copilot CLI session with no shared context
- The only connection between passes is the requirements file that earlier passes produce and later passes consume

### Execution

All passes run via Copilot CLI (GPT-5.4, --yolo mode) against the NSQ repo at the pre-fix commits.

```bash
# From the NSQ repo root (repos/nsq-req-validation/):
bash experiment_two_pass/run_experiment.sh pass1      # ~2 min
bash experiment_two_pass/run_experiment.sh pass1.5     # ~2 min (optional, see findings)
bash experiment_two_pass/run_experiment.sh pass2       # ~2 min
bash experiment_two_pass/run_experiment.sh pass3       # ~3 min
```

Total wall time: ~9 minutes. Total cost: ~4 premium requests.

## Results

### Pass 1: Requirement Derivation

Pass 1 derived 20 requirements across both subsystems. Key findings against target defects:

**NSQ-39 (worker ID bit width)**: The model derived BOTH sides of the contradiction without noticing it was a contradiction:
- Input Validation: "`--worker-id` must satisfy `0 <= worker-id < 4096`" (from nsqd.go validation code)
- API Contracts: "default worker ID constrained to the 10-bit worker-ID space by hashing the hostname and taking the result modulo `1024`" (from options.go and guid.go)

These two requirements are individually correct descriptions of what the code does, but they contradict each other: 4096 vs 1024.

**NSQ-36 (E2E percentile validation)**: NOT derived. The model derived requirements for fields that already have visible validation (MaxDeflateLevel, worker ID, TLS config, statsd prefix) but did not derive a requirement for a field that lacks validation. This confirms the direct experiment's finding: absence bugs require knowing what should exist, which means the intent has to come from somewhere outside the codebase.

**NSQ-44 (auth server root CA)**: Weakly derived. One "directional" requirement stated that "security-relevant configuration for inbound TLS and auth decisions should be applied consistently wherever NSQD opens or evaluates a connection." This is the right principle at the wrong specificity — it doesn't name the auth client specifically.

### Pass 1.5: Requirement Filtering (Counterproductive)

The filter reduced 20 requirements to 18, removing two resource lifecycle requirements (startup ordering, shutdown sequencing) and the directional TLS consistency requirement. The directional requirement was the closest thing to catching NSQ-44.

**Finding: The filter hurt more than it helped.** The cost of checking extra requirements is low (~30 seconds). The cost of filtering out the requirement that would have caught NSQ-44 is high. For the playbook: err on the side of keeping requirements, not pruning them.

### Pass 2: Requirement Verification (Run Twice)

**First run (filtered requirements, 18 REQs)**: Marked all requirements SATISFIED or PARTIALLY SATISFIED. Did NOT catch NSQ-39 — it checked each requirement independently and found that the validation code satisfies the "< 4096" requirement, and the default derivation satisfies the "modulo 1024" requirement. It never compared the two.

**Second run (raw requirements, 20 REQs)**: Found NSQ-39. The GUID encoding requirement (REQ-5) was marked PARTIALLY SATISFIED because "startup accepts values up to 4095, while a 10-bit field can only represent 0..1023. For worker IDs 1024..4095, the high worker bits spill into the timestamp region." This detection came from checking the GUID bit layout requirement against the actual startup validation code.

Also found two other issues not in our target set: auth path routing for non-URL authd addresses (REQ-15 PARTIALLY SATISFIED), and randomized auth daemon failover order (REQ-17 PARTIALLY SATISFIED).

### Pass 3: Cross-Requirement Consistency Check

Pass 3 found 3 inconsistencies and 4 consistent shared concepts:

**INCONSISTENT — Worker ID space and GUID bit width** (NSQ-39): Connected the validation bound (4096), the GUID bit width (10 bits = 1024), and the default derivation (modulo 1024). Concluded: "values 1024..4095 spill into the timestamp region instead of staying inside the declared worker-ID field." Clean, precise detection with full code evidence from both files.

**INCONSISTENT — TLS trust propagation to outbound auth requests** (NSQ-44): Connected three requirements: REQ-11 (tls-root-ca-file loads a CA bundle), REQ-17 (NSQD sends TLS context to auth daemon), and REQ-21 (the directional requirement about consistent TLS policy across connection paths). Found `NewClient(nil, connectTimeout, requestTimeout)` in authorizations.go and traced it to the transport layer where `tlsConfig` is set to nil. Concluded: "the outbound auth HTTP client is created with nil TLS config. So any HTTPS auth request uses system defaults instead of the configured CA bundle."

**INCONSISTENT — Auth daemon list semantics**: Found that configured auth daemon order is not preserved due to randomized starting index. Not a target defect but a real finding.

**CONSISTENT**: TLS requirement activation/listener behavior, inbound TLS policy assembly, listener lifecycle (startup/shutdown), auth daemon request/response contract.

## Summary

| Defect | Pass 1 (Derive) | Pass 2 (Verify) | Pass 3 (Consistency) | Result |
|--------|-----------------|-----------------|---------------------|--------|
| NSQ-39 (worker ID bit width) | Derived both sides of contradiction | **Found** (2nd run) | **Found** | **DETECTED** |
| NSQ-44 (auth server root CA) | Weak directional requirement | Not found | **Found** | **DETECTED** |
| NSQ-36 (E2E percentile validation) | No requirement derived | N/A | N/A | Not detected |

**2 of 3 target defects detected end-to-end with zero knowledge of the bugs.**

Additional findings not in the target set:
- Auth path routing inconsistency for non-URL authd addresses (Pass 2)
- Randomized auth daemon failover order violates configured precedence (Pass 2 and Pass 3)

## Key Findings

### 1. The pipeline works for cross-file and design-gap bugs

NSQ-39 (cross-file arithmetic) and NSQ-44 (design gap) were both found by a pipeline that had no knowledge of any specific defects. The model derived requirements from documentation, then used those requirements to find real bugs. This validates the playbook's core architecture: derive requirements from intent sources, then verify code against them.

### 2. Cross-requirement consistency checking is essential

Pass 2 alone missed NSQ-39 on its first run (checking each requirement independently) and completely missed NSQ-44. Pass 3's cross-requirement consistency check found both. The key insight: bugs often live in the gap between two individually-correct pieces of code. Per-requirement verification can't find these — you need to compare requirements against each other.

### 3. Requirement filtering is counterproductive

Pass 1.5 removed the directional TLS requirement that was essential for Pass 3 to find NSQ-44. The cost of extra requirements is low; the cost of missing a bug because you pruned the requirement that would have caught it is high. The playbook should keep all derived requirements and let the verification and consistency passes handle the noise.

### 4. Absence bugs remain the hardest class

NSQ-36 was not detected because no requirement was derived for E2E percentile validation. The model derived requirements for fields that already have visible validation but couldn't derive requirements for fields that lack it. This is the fundamental limit of deriving requirements from code and documentation alone — absence bugs require knowing what should exist, which means the intent has to come from richer sources (support tickets, config documentation, systematic field-by-field audit checklists).

### 5. The pipeline architecture for the playbook

Based on this experiment, the playbook's review pipeline should be:

1. **Structural review** (Pass 0): Standard code review — what every AI tool already does. Catches ~65% of defects.
2. **Requirement derivation** (Pass 1): Mine all available intent sources for testable requirements. Keep everything, don't filter.
3. **Per-requirement verification** (Pass 2): Check each requirement against the code. Catches violations where a single requirement is not satisfied.
4. **Cross-requirement consistency** (Pass 3): Compare pairs of requirements that reference the same concepts. Catches contradictions where two correct pieces of code disagree.

Passes 2-4 are the playbook's unique contribution — the ~35% that structural review can't reach.

## Key Files

- `pass1_derive_requirements.md` — Pass 1 prompt (requirement derivation)
- `pass1_5_filter_requirements.md` — Pass 1.5 prompt (requirement filtering) — counterproductive, see findings
- `pass2_verify_requirements.md` — Pass 2 prompt (per-requirement verification)
- `pass3_cross_requirement_consistency.md` — Pass 3 prompt (cross-requirement consistency check)
- `requirements_raw.md` — Pass 1 output: 20 derived requirements
- `requirements_filtered.md` — Pass 1.5 output: 18 filtered requirements (not recommended for use)
- `verification_report.md` — Pass 2 output: per-requirement verification (2nd run with raw requirements)
- `consistency_report.md` — Pass 3 output: cross-requirement consistency analysis
- `run_experiment.sh` — Automation script for all passes
- `pass1_output_*.txt`, `pass2_output_*.txt`, `pass3_output_*.txt` — Raw Copilot CLI output logs

## Relationship to Other Experiments

- **57-review benchmark** (`benchmarks/EXPERIMENT.md`): Established the ~65% structural review ceiling and the ~35% intent-violation gap.
- **4-condition validation** (`experiments/req_validation/EXPERIMENT.md`): Attempted to test requirements-as-prompt with automated scoring. Abandoned — over-engineered and scoring was unreliable.
- **Direct review** (`experiments/direct_review/EXPERIMENT.md`): Proved that requirements find bugs cold review misses. Left open the question of whether requirements can be derived without prior knowledge of the bugs.
- **This experiment**: Proved the full end-to-end pipeline works. 2 of 3 target defects detected with zero bug knowledge. Identified the pipeline architecture (derive → verify → consistency check) and the limit (absence bugs need richer intent sources).
