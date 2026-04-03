# Patched Protocol Re-test Scores

## Experiment

Re-ran the 10 previously-missed NSQ defects using Opus 4.6 with the patched review protocol (v1.2.10 generated protocol + 4 new focus areas + 3 new guardrails).

## Results

| Defect | Category | Baseline (v1.2.10) | Patched | Notes |
|--------|----------|-------------------|---------|-------|
| NSQ-04 | Cleanup ordering | MISS | MISS | Reviewer claimed connections ARE closed (incorrect) |
| NSQ-12 | Channel/queue | MISS | DIRECT HIT | Found unbuffered vs nil asymmetry |
| NSQ-14 | Protocol state machine | MISS | MISS | Found DPUB variant but said REQ already clamps |
| NSQ-17 | Protocol state machine | MISS | DIRECT HIT | Found IOLoop/messagePump exit race |
| NSQ-19 | Config/flag handling | MISS | DIRECT HIT | Found missing else clause precisely |
| NSQ-41 | Config/flag handling | MISS | DIRECT HIT | Found unconditional override, gave exact fix |
| NSQ-47 | Cleanup ordering | MISS | MISS | Same issue as NSQ-04: claimed TCP already closed |
| NSQ-53 | Channel/queue | MISS | DIRECT HIT | Found unbuffered send blocking pattern |
| NSQ-55 | Protocol state machine | MISS | DIRECT HIT | Found server default vs client value |
| NSQ-56 | Config/flag handling | MISS | DIRECT HIT | Found missing whitelist validation |

## Summary

- **Baseline: 0/10 (0%)**
- **Patched: 7/10 (70%)**
- **Improvement: +7 DIRECT HITs**

## By Category

| Category | Baseline | Patched | Improvement |
|----------|----------|---------|-------------|
| Protocol state machine (3) | 0/3 | 2/3 | +67% |
| Config/flag handling (3) | 0/3 | 3/3 | +100% |
| Cleanup ordering (2) | 0/2 | 0/2 | 0% |
| Channel/queue (2) | 0/2 | 2/2 | +100% |

## Analysis

### What worked
- **Config/flag handling**: 3/3 caught. Focus Area 9 (Configuration Parameter Validation) directly guided the reviewer to check branch completeness, whitelist validation, and flag interaction guards.
- **Channel/queue semantics**: 2/2 caught. Focus Area 12 (Go Channel Lifecycle) directly guided the reviewer to check nil vs unbuffered and closed-channel patterns.
- **Protocol state machine**: 2/3 caught. Focus Area 10 (Input Validation Failure Modes) caught the RemoveClient race and MsgTimeout response mismatch.

### What didn't work
- **Cleanup ordering**: 0/2 still missed. Focus Area 11 (Exit Path Resource Completeness) told the reviewer to enumerate all resource types, but the reviewer incorrectly reported that TCP connections were being closed. This is a false-negative where the reviewer read the code and reached the wrong conclusion — guidance pointed at the right area but the reviewer misread the code.
- **NSQ-14 (REQ timeout)**: The reviewer found the same pattern in DPUB but claimed REQ already clamps. Possibly the reviewer saw a different version of the code or confused REQ/DPUB handling. The guidance was correct but the reviewer's code reading was inaccurate.

### Remaining gaps
The 3 remaining misses share a pattern: the reviewer looked at the right code and reached the wrong conclusion. This isn't a guidance gap — it's a code reading accuracy issue. Possible mitigations:
1. Add a "double-check" guardrail: "If you conclude that a resource IS properly cleaned up, grep for all Close() calls and verify the one you found actually runs on the exit path"
2. Add specific examples: "Closing a listener is NOT the same as closing active connections. Look for BOTH."
