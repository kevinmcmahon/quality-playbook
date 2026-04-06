# NSQ Benchmark Experiment Status

## Three-Condition Design

| Condition | Model | Playbook | Status | Location |
|-----------|-------|----------|--------|----------|
| 1. v1.2.10 playbook | Opus 4.6 | v1.2.10 (current) | COMPLETE (57 defects scored) | run_002/nsq/opus/ |
| 2. v1.2.0 playbook | GPT-5.4 | v1.2.0 (baseline) | RUNNING (prompt 5/58) | repos/nsq-1.2.0/ |
| 3. No playbook | GPT-5.4 | None (naive prompt) | RUNNING (prompt 18/57) | repos/nsq-control/ |

## Condition 1 Results (Complete)

- 57 defects reviewed (NSQ-42 skipped, no files)
- 21 DIRECT HIT (36%), 8 ADJACENT (14%), 25 MISS (43%), 4 NO REVIEW (7%)
- Weak categories: protocol state machine (0%), config/flag handling (0%), cleanup ordering (33%), channel/queue semantics (40%)

## Patched Protocol Re-test (Fast Inner Loop)

Patched the v1.2.10 generated protocol with 4 new focus areas targeting weak categories. Re-ran only the 10 missed defects from the 4 weak categories.

- 7/10 DIRECT HIT (70%), 0 ADJACENT, 3 MISS
- Config/flag handling: 3/3 caught (100%)
- Channel/queue semantics: 2/2 caught (100%)
- Protocol state machine: 2/3 caught (67%)
- Cleanup ordering: 0/2 caught (0%) — reviewer misread code despite correct guidance

## What's Next

1. Wait for Conditions 2 and 3 to complete (~2 hours each at ~2.5 min/prompt)
2. Score both control conditions against same ground truth
3. Compare all three conditions + patched protocol re-test
4. Use comparison data to decide v1.2.12 playbook changes
5. Run v1.2.12 full benchmark to measure end-to-end improvement

## Key Files

- Ground truth: dataset/defects.jsonl (NSQ-01 through NSQ-58)
- Condition 1 scores: run_002/nsq/scoring/nsq_scores.md
- Patched re-test scores: run_002/nsq/scoring/patched_retest_scores.md
- Condition 2 reviews: repos/nsq-1.2.0/quality/code_reviews/
- Condition 3 reviews: repos/nsq-control/code_reviews/
- Condition 2 progress: repos/nsq-1.2.0/control_progress.txt
- Condition 3 progress: repos/nsq-control/control_progress.txt
- Analysis docs: nsq_missed_defects_analysis.md, nsq_detailed_analysis.md
