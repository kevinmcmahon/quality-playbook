# Code Review: nsqd/protocol_v2.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Source:** /tmp/qpb_wt_opus_NSQ-19/nsqd/protocol_v2.go

---

### nsqd/protocol_v2.go

- **Line 303, 325:** [BUG] **Sample rate off-by-one error (Severity: Low).** The condition `rand.Int31n(100) > sampleRate` keeps `sampleRate + 1` percent of messages instead of `sampleRate` percent. `rand.Int31n(100)` returns values in [0, 99]. For `sampleRate = N`, values 0 through N pass the check (N+1 values), delivering `(N+1)%` of messages. With the validated max `sampleRate = 99` (client_v2.go:440), the condition `rand.Int31n(100) > 99` is never true, so 100% of messages are delivered instead of 99%. The correct check should be `rand.Int31n(100) >= sampleRate` to deliver exactly N% of messages. This affects both `backendMsgChan` (line 303) and `memoryMsgChan` (line 325) code paths identically.

- **Line 87:** [QUESTION] **Unchecked type assertion on ChildErr interface (Severity: Medium).** The expression `err.(protocol.ChildErr)` will panic if `err` does not implement the `ChildErr` interface. Currently all error paths from `Exec()` return `*protocol.ClientErr` or `*protocol.FatalClientErr`, both of which implement `ChildErr`. However, this is fragile — if any future command handler returns a bare `error` (e.g., from a standard library call without wrapping), this line will panic and crash the client connection goroutine. A safe type assertion `if childErr, ok := err.(protocol.ChildErr); ok { ... }` would prevent this.

- **Line 627:** [QUESTION] **SUB transitions directly from stateInit to stateSubscribed, skipping stateConnected (Severity: Low).** The constant `stateConnected` is defined in client_v2.go:22 (value 1 in the iota) but is never set or checked anywhere in the client protocol V2 state machine. SUB (line 583) requires `stateInit` and transitions directly to `stateSubscribed` (line 627). IDENTIFY (line 351) and AUTH (line 491) both require `stateInit` but never change the state. This means `stateConnected` is dead code in the client protocol. Either the state is vestigial (used only for lookup_peer.go:100 which has a separate state machine) or SUB was intended to require `stateConnected` with IDENTIFY performing the `stateInit → stateConnected` transition.

- **Line 615-626:** [QUESTION] **Unbounded retry loop in SUB for ephemeral channel/topic races (Severity: Low).** The retry loop that works around the race between `GetChannel()` and `AddClient()` for ephemeral channels has no iteration limit or total timeout. If an ephemeral channel or topic is continuously recreated and immediately starts exiting (e.g., due to a bug or adversarial condition), this loop runs indefinitely with only a 1ms sleep between iterations, blocking the client's IOLoop goroutine forever. In practice this is unlikely because the race window is narrow, but the absence of a bound means a misbehaving ephemeral topic could cause goroutine leaks.

- **Line 820-822 vs 772-793:** [QUESTION] **MPUB performs auth check before reading body from wire (Severity: Low).** In `PUB` (line 772-793), the message body is read from the connection *before* `CheckAuth` is called (line 793), ensuring the wire protocol stays synchronized even on auth failure. In `MPUB` (line 820-822), `CheckAuth` is called *before* reading the body (line 826). If auth fails, the body data remains unread on the wire. This is currently safe because `CheckAuth` returns `*FatalClientErr` which causes the connection to close at line 99. However, the inconsistent ordering between PUB and MPUB is worth noting — if `CheckAuth` were ever changed to return a non-fatal error, MPUB would corrupt the wire protocol state.

---

### Summary

| Severity | BUG | QUESTION |
|----------|-----|----------|
| Medium   | 0   | 1        |
| Low      | 1   | 3        |

- **Total findings:** 5 (1 BUG, 4 QUESTION)
- **Files reviewed:** 1 (nsqd/protocol_v2.go, 1013 lines)

**Overall assessment: SHIP IT** — The protocol handler is well-structured with proper state checks, atomic operations, and error handling. The one BUG (sample rate off-by-one) is low severity and only affects the rarely-used sampling feature by delivering slightly more messages than configured. The QUESTIONs identify areas of fragility (unchecked type assertion, dead state constant, unbounded loop) but none represent current correctness failures.
