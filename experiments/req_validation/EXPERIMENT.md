# Experiment: Requirements-as-Prompt (4-Condition Validation)

**Status: Abandoned** — Replaced by the direct experiment (see `benchmarks/direct_experiment_results.md`) and the two-pass derivation experiment (see `experiments/two_pass_derivation/`).

## Background

The 57-review benchmark showed that ~35% of defects are invisible to structural code review. The requirement derivation analysis (see `benchmarks/requirement_derivation_experiment.md`) showed that 67% of defects in the target categories have requirements derivable from documentation. The next question: does giving the model those requirements actually help it find the defects?

This experiment was designed to test requirements-as-prompt at two abstraction levels, with controls for cross-contamination.

## Hypothesis

Providing testable requirements in the review prompt will help the model find defects in the 35% gap that structural review cannot reach. The effect should be strongest with specific requirements (upper bound) and still present with abstract requirement principles (realistic test of what the playbook would generate).

A secondary hypothesis: mixing "find bugs" with "check these requirements" in a single prompt causes cross-contamination that hurts both tasks. Clean separation (requirements-only prompts) should outperform mixed prompts.

## Method

### Part 1: Four Conditions (64 prompts)

16 defects selected from the benchmark (mix of baseline-found and baseline-missed). For each defect, 4 prompts generated:

- **Control**: Generic review prompt, same as benchmark. "Review for bugs. Be thorough."
- **Specific Requirements**: Same review prompt plus precise testable requirements per defect (e.g., "Worker ID validation must reject values >= 1024").
- **Abstract Requirements**: Same review prompt plus higher-abstraction principles (e.g., "Validation ranges must match the actual bit width of the destination field").
- **v1.2.12 Focus Areas**: Playbook v1.2.12 prompt with 7 named focus areas.

Each prompt targeted the pre-fix commit of its defect with only the relevant source files, run via Copilot CLI (GPT-5.4).

### Part 2: Clean Two-Pass (32 additional prompts)

- **Clean Specific**: Requirements-only prompt with NO general review instruction. "This is a requirements verification audit ONLY."
- **Clean Abstract**: Same but with abstract principles.

Designed to test whether removing the "also find other bugs" instruction improves requirements-focused detection.

### Scoring

Automated regex-based scoring against ground truth defect definitions. The scorer matched requirement-violation patterns against review text.

## Results

**Part 1 was abandoned after ~10 of 16 control runs completed.** Part 2 was never run.

The automated scoring produced unreliable results — false positives from keyword co-occurrence (e.g., "config" appearing in both a defect definition and a review about a different config issue) and false negatives from paraphrase mismatches. Three iterations of the scorer (v1, v2, v3) failed to produce trustworthy results.

The partial control results did produce one useful finding: the control found NSQ-39 (worker ID bit width mismatch) on the tighter per-defect file set, despite missing it in the original 57-review benchmark. This confirmed that file scoping affects detection — giving the model only the 2-3 relevant files is different from giving it a broader set.

## Why It Was Abandoned

1. **Automated scoring didn't work.** Regex patterns can't reliably distinguish "the review found this specific defect" from "the review mentioned similar keywords in a different context." LLM-based scoring was blocked by API access limitations.

2. **The experiment was over-engineered.** 64 prompts × ~3 minutes each = 3+ hours of Copilot CLI time, producing data that required unreliable automated scoring to interpret. Manual reading of 3 defects in 10 minutes produced clearer, more credible results.

3. **The question shifted.** "Do requirements help find bugs?" was answered decisively by the direct experiment. The more important question became "Can the model derive the right requirements from documentation alone?" — which this experiment wasn't designed to test.

## Key Files

- `generate_prompts.py` — Generates all 64 Part 1 prompts (contains full defect metadata)
- `generate_prompts_part2.py` — Generates 32 Part 2 prompts
- `run_experiment.sh` — Copilot CLI runner for Part 1
- `run_experiment_part2.sh` — Copilot CLI runner for Part 2
- `score_experiment.py` — Automated scorer (all 6 conditions)
- `prompts_*/` — Generated prompt files for all conditions
- `reviews_control/` — Partial results (~10 of 16 completed)

Also mirrored in the NSQ repo clone at `repos/nsq-req-validation/`.

## Lessons Learned

1. Automated scoring of free-text reviews is harder than it looks. Invest in LLM-based scoring or skip straight to manual evaluation on a smaller set.
2. Start with 3 defects, not 16. If the signal is strong on 3, it'll be strong on 16. If it's weak on 3, running 16 won't help.
3. File scoping is a confound. Per-defect experiments give the model a tighter file set than real-world reviews, which inflates detection rates.
4. Cross-contamination between "find bugs" and "check requirements" is real but needs clean separation to measure properly — don't try to test it within a mixed prompt.
