# Experiment: NSQ Benchmark (57-Review Playbook Comparison)

## Background

The Quality Playbook is designed to improve AI-assisted code review by providing structured focus areas, review protocols, and defensive pattern catalogs. Early versions (v1.2.0 through v1.2.13) added increasingly sophisticated machinery: named bug shapes, two-pass review structure, council-reviewed guardrails. The question was whether this machinery actually improved defect detection compared to a strong baseline model with no playbook.

NSQ was chosen as the benchmark codebase because it has a rich history of real-world defects across multiple categories (concurrency, resource lifecycle, error handling, API contracts, security, input validation, data integrity, arithmetic boundaries), well-documented fixes in the ChangeLog, and a codebase small enough to review in a single model context window.

## Hypothesis

Providing the Quality Playbook's focus areas and review structure will help the model find defects that a generic "review for bugs" prompt misses, particularly in categories where domain-specific knowledge matters (security, API contracts, input validation).

## Method

58 ground-truth defects were extracted from NSQ's commit history and classified by category and requirement strength. Each defect was documented with the pre-fix commit, affected files, requirement violation, and detection signals.

Three conditions were scored:

- **Control**: GPT-5.4 via Copilot CLI with a generic code review prompt ("review for bugs, be thorough"). No playbook. 57 reviews total.
- **v1.2.12**: Quality Playbook v1.2.12 with 7 named focus areas and guardrails. Same model and review count.
- **v1.2.13**: Quality Playbook v1.2.13 with council-reviewed two-pass structure and named bug shapes. Same model and review count.

Scoring used pool-based matching: each defect's requirement-violation pattern was searched across ALL 57 reviews in each condition. A defect found in any review slot counted as found. Scoring was automated using regex patterns derived from the requirement violations (not the fix descriptions).

## Results

| Condition | Found | Total | Rate |
|-----------|-------|-------|------|
| control   | 38    | 58    | 65.5% |
| v1.2.12   | 36    | 58    | 62.1% |
| v1.2.13   | 28    | 58    | 48.3% |

The control (no playbook) outperformed both playbook versions overall. v1.2.13's additional structure actively hurt — it found 10 fewer defects than v1.2.12. The regression was concentrated in API contracts (29% vs 71%) and security (33% vs 67%).

v1.2.12 edged out the control on concurrency (77% vs 69%) and input validation (50% vs 25%), suggesting that some focus areas help for specific categories. But the net effect was negative: adding more playbook machinery narrowed the model's attention and suppressed detections.

18 defects were missed by all three conditions. These clustered in arithmetic-boundary edge cases, concurrency subtleties, and configuration interactions (NSQ-36, NSQ-39, NSQ-44) — defects that require knowing what the code is supposed to do, not just what it does.

## Key Files

- `scoring_summary_v3.md` — Full scoring breakdown by category with differential analysis
- `scoring_results_v3.json` — Raw scoring data for all 58 defects across 3 conditions
- `nsq_defects_v2.json` — Ground truth defect definitions with scoring guidance
- `defect_schema_v2.md` — Schema documentation for defect entries
- `playbook_v1.2.0/` through `playbook_v1.2.13/` — Snapshots of each playbook version tested
- `run_001/`, `run_002/` — Raw review outputs from benchmark runs
- `run_benchmark.sh`, `run_reviews.sh`, etc. — Copilot CLI automation scripts

## Conclusions

1. A strong model with a generic prompt scores ~65% on real defects. This is the structural review ceiling — what you get from reading code and spotting anomalies.
2. Adding focus areas and review structure doesn't reliably improve on that ceiling and can make things worse by narrowing the model's attention.
3. The ~35% of defects that all conditions miss are intent violations: absence bugs, cross-file arithmetic mismatches, design gaps, configuration interactions. These require knowing the requirements, not just reading the code.
4. The playbook's value isn't in review structure or focus areas — it's in the specification. The requirements document is the unique contribution.

This conclusion led directly to the requirement derivation and direct review experiments.
