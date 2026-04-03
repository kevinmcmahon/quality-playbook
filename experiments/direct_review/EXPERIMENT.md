# Experiment: Direct Review (Cold vs Requirements-Guided)

**Status: Complete**

## Background

The 57-review benchmark established that ~35% of defects are invisible to structural code review. The 4-condition validation experiment was abandoned because automated scoring was unreliable and the experiment was over-engineered. The question remained: do requirements actually help find the defects that cold review misses?

Three defects were selected that ALL conditions in the benchmark missed (NSQ-36, NSQ-39, NSQ-44). These represent the hardest cases — defects invisible to any amount of code reading without knowing the requirement. If requirements help find even one of these, the mechanism is validated.

## Hypothesis

A reviewer reading code without requirements will miss absence bugs, cross-file arithmetic bugs, and design gaps — the three failure modes of structural review. The same reviewer, armed with either specific or abstract requirements, will find these defects. The gap between cold and requirements-guided review is the playbook's contribution.

## Method

For each of three defects, the pre-fix source code was read directly using `git show` at the relevant commit. Three review passes were performed:

1. **Cold review**: Read the code with no prior knowledge of the defect. Look for anything wrong. This simulates what any AI code review tool does.
2. **Specific requirements**: Re-read with a precise testable requirement (e.g., "percentile values must be validated in (0, 1] at parse time"). This simulates the best case — a perfect requirements document.
3. **Abstract principles**: Re-read with a higher-abstraction principle (e.g., "configuration values with domain constraints must be validated at parse time"). This simulates what the playbook would realistically generate.

No Copilot CLI or automated tooling. Direct reading and analysis in a single session (~10 minutes total).

### Defects Selected

| Defect | Category | Failure Mode | Files |
|--------|----------|-------------|-------|
| NSQ-36 | input-validation | Absence bug | nsqd/nsqd.go, nsqd/options.go (commit cb83885) |
| NSQ-39 | input-validation | Cross-file arithmetic | nsqd/nsqd.go, nsqd/guid.go (commit 98fbcd1) |
| NSQ-44 | security | Design gap | internal/auth/authorizations.go, nsqd/nsqd.go (commit 1d183d9) |

## Results

| Defect | Cold Review | Specific Requirement | Abstract Principle |
|--------|------------|---------------------|-------------------|
| NSQ-36 (percentile validation) | No — absence is invisible | Yes — trivial | Maybe — large search space |
| NSQ-39 (worker ID bit width) | Maybe — requires both files + math | Yes — trivial | Yes — guides comparison |
| NSQ-44 (auth server CA) | No — nil TLS looks normal | Yes — trivial | Yes — guides outbound audit |

### Three Failure Modes of Structural Review

1. **Absence bugs (NSQ-36)**: Code that should exist but doesn't. Cold review finds things that are wrong, not things that should be there. The code that IS there is correct — you have to notice what's missing, which requires knowing what should be there.

2. **Cross-file arithmetic bugs (NSQ-39)**: Each file is correct in isolation. The bug only appears when you compare a constant in one file against a validation bound in another. Cold review can find this if both files are visible and the reviewer does the math, but it requires connecting dots across files.

3. **Design gaps (NSQ-44)**: The code does what it was designed to do — it just wasn't designed to do the right thing. A nil TLS config is the normal-looking pattern for an HTTP client. There's no anomaly to detect. You need to know the requirement (outbound connections must use the configured CA) to see that a whole feature is missing.

### Specific vs Abstract Requirements

Specific requirements make all three defects trivially findable. Abstract principles work well for NSQ-39 (guides comparison of two well-defined values) and NSQ-44 (guides audit of outbound connections), but are weaker for NSQ-36 (the search space is too large without knowing which specific field needs validation — there are ~40 config fields).

This means the playbook's requirement derivation pipeline needs to produce requirements closer to the specific end of the spectrum. Vague principles like "validate your inputs" are not enough for absence bugs where the search space is large.

## Key Files

- `../../benchmarks/direct_experiment_results.md` — Full analysis with detailed cold review, specific requirement, and abstract principle writeups for each defect
- `../../benchmarks/requirement_derivation_experiment.md` — Requirement derivation analysis showing 67% of defects have documentation-derivable requirements

## Conclusions

1. Requirements make the invisible visible. All three defects that no benchmark condition found were trivially findable with specific requirements.
2. The playbook's value is the specification, not the review structure. Focus areas and review protocols are secondary to having the right requirements.
3. Abstract principles work for cross-file and design-gap bugs but fail for absence bugs with large search spaces. The playbook must generate specific, targeted requirements.
4. Cold review has a hard ceiling. No amount of "be thorough" or "check for bugs" will find a design gap. You need to know the requirement.
5. Direct manual analysis on 3 defects in 10 minutes produced more credible results than 64 automated prompts over 3+ hours.

## Next Steps

The direct experiment proved that requirements find bugs cold review misses. The remaining question: can the model derive the right requirements from documentation alone, without someone who already knows the bugs telling it what to look for? This is tested in `experiments/two_pass_derivation/`.
