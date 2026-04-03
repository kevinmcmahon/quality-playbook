# v1.2.11 Regression Test Results

**Date:** 2026-03-31
**Methodology:** Generated v1.2.11 playbooks for chi repo (3 models), then re-ran targeted code reviews on the 3 defects that v1.2.10 missed.

## Results

| Defect | Change Targeting It | Opus v1.2.10 | Opus v1.2.11 | Sonnet v1.2.10 | Sonnet v1.2.11 | Haiku v1.2.10 | Haiku v1.2.11 |
|--------|-------------------|-------------|-------------|----------------|----------------|---------------|---------------|
| CHI-03 | Change 1 (accessor consistency) + Change 5 (sibling rule) | MISS | MISS | MISS | MISS | MISS | MISS |
| CHI-04 | Change 2 (string normalization) | MISS | MISS | MISS | MISS | MISS | MISS |
| CHI-12 | Change 3 (test setup ordering) | MISS | **DIRECT HIT** | MISS | MISS | MISS | MISS |

**Summary:** 1 of 9 reviews improved (11%). 1 of 3 defects now caught by at least 1 model (33%).

## Detailed Scoring

### CHI-03: Method Accessor Confusion (Close() uses cw.writer() instead of cw.w)

**Opus:** MISS — Found the same accessor bug in Hijack() and Push() but still did not audit Close(). The "exhaust the sibling set" guardrail did not propagate into the generated review protocol strongly enough to trigger systematic sibling checking.

**Sonnet:** MISS — Found other bugs (matchAcceptEncoding, nil encoder, WriteHeader logic, error suppression in Close) but did not identify the accessor confusion in Close().

**Haiku:** MISS — Found a duplicate Flush() call issue using cw.writer() but did not examine Close() specifically. Ironically, the review's own checklist claimed "Sibling methods checked for consistency (Hijack, Push, Close all follow same pattern)" but the actual analysis didn't include Close().

### CHI-04: Boundary Value Destruction (TrimSuffix destroys root route "/")

**All 3 models:** MISS — All three found the methodsAllowed pool-reuse bug (a different real defect) but none traced TrimSuffix with the minimal input "/". The string normalization guidance in the playbook did not translate into the generated review protocol with enough specificity to trigger boundary tracing.

### CHI-12: Test Setup Temporal Ordering (NewServer before configuration)

**Opus:** DIRECT HIT — Explicitly identified: "the test server is started with httptest.NewServer(r) at line 1686, which immediately begins accepting connections. The BaseContext function is then assigned after the server is already live." Recommended the exact fix: NewUnstartedServer → configure → Start().

**Sonnet:** MISS — Reviewed wrong files entirely (recoverer.go, realip.go, mux.go instead of mux_test.go).

**Haiku:** MISS — Read the correct file but declared all NewServer patterns "correct" and stated "No data race risks identified from resource creation/configuration ordering."

## Analysis

### What Worked
- **CHI-12 / Opus:** The test setup ordering guidance (Change 3) successfully propagated into Opus's generated review protocol and caught the exact defect. This validates the methodology — playbook changes CAN improve detection.

### What Didn't Work
- **CHI-03 (all models):** The accessor consistency and sibling rule changes didn't produce strong enough signals in the generated review protocols. The models still find the pattern in some methods (Hijack, Push) but don't systematically check all methods on the type.
- **CHI-04 (all models):** The string normalization guidance didn't translate into actual boundary tracing during review. Models review structurally but don't trace transformation chains with minimal inputs.
- **CHI-12 / Sonnet:** Reviewed the wrong files — the review prompt specified mux_test.go but Sonnet's generated protocol may have directed it elsewhere.
- **CHI-12 / Haiku:** Read the right file, explicitly checked for the pattern, but concluded it was fine. This is a false negative despite having the right guidance.

### Implications for v1.2.12

1. **The playbook → generated protocol → review chain has signal loss.** Changes to the playbook don't mechanically propagate to the generated review protocol. The playbook tells the agent what to look for during exploration; the agent must then encode those patterns into the review protocol it generates. If the agent doesn't encounter the pattern during exploration, it may not include it in the protocol.

2. **CHI-03 needs stronger guidance.** The "exhaust the sibling set" rule needs to be more prominent — perhaps in the review prompt itself, not just in the playbook. Consider adding it as a mandatory guardrail in the review protocol template.

3. **CHI-04 needs worked examples.** The string normalization guidance is abstract. Adding a worked example with "/" specifically, or requiring "trace each string operation with the minimum-length valid input" as a mandatory step, may help.

4. **Test file targeting matters.** CHI-12 was originally missed partly because test files were filtered out. When we included the test file, 1 of 3 models caught it. The review automation should not filter out test files for defects that ARE test bugs.

## Methodology Notes

- v1.2.11 playbooks were generated fresh for all 3 models against chi HEAD
- Reviews used the generated RUN_CODE_REVIEW.md from each model's v1.2.11 playbook
- CHI-12 reviews included the test file (mux_test.go) — original v1.2.10 benchmark filtered test files out
- The review prompt included an extra guardrail: "When you find a bug in one method of a type, check ALL sibling methods for the same pattern"
- Worktrees were used at the same pre-fix commits as the original benchmark
