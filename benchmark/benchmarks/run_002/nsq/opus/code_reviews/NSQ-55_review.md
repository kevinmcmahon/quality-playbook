# Code Review: nsqd/protocol_v2.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `nsqd/protocol_v2.go` (at `/tmp/qpb_wt_opus_NSQ-55`)

---

### nsqd/protocol_v2.go

- **Line 366-371:** BUG (Severity: High) — DeflateLevel is silently set to 0 when the client requests a positive value. When `identifyData.DeflateLevel > 0`, the code skips the `deflateLevel = 6` default assignment but never assigns `identifyData.DeflateLevel` to `deflateLevel`. It remains at the zero-value from line 367. The subsequent `math.Min(0, MaxDeflateLevel)` evaluates to 0. A client requesting e.g. `DeflateLevel=4` gets level 0 (no compression). The fix should be:
  ```go
  if identifyData.DeflateLevel <= 0 {
      deflateLevel = 6
  } else {
      deflateLevel = identifyData.DeflateLevel
  }
  ```

- **Line 535:** BUG (Severity: High) — `id := *(*MessageID)(unsafe.Pointer(&params[1][0]))` performs an unsafe cast without validating that `len(params[1]) >= len(MessageID)`. If a client sends a FIN command with a message ID shorter than `MessageID` (16 bytes), this reads past the end of the slice's backing array into adjacent memory. This can cause incorrect message finishes (wrong ID) or a segfault. Same issue exists on **line 557** (REQ) and **line 695** (TOUCH).

- **Line 82:** QUESTION (Severity: Medium) — The type assertion `err.(util.ChildErr).Parent()` is unchecked. If any error returned from `p.Exec()` does not implement the `util.ChildErr` interface, this will panic and crash the connection handler goroutine. Currently all command handlers return `util.NewFatalClientErr` or `util.NewClientErr`, which presumably implement `ChildErr`, but this is fragile — any future handler returning a plain `error` would cause a panic.

- **Line 454:** QUESTION (Severity: Medium) — SUB checks `client.State != stateInit`, allowing SUB directly from `stateInit` without requiring IDENTIFY first. The IDENTIFY handler (line 323) checks the same `stateInit` state but does not transition the state to `stateConnected` — it returns without changing state. This means a client can SUB without ever sending IDENTIFY, bypassing feature negotiation, TLS enforcement (if not caught by `enforceTLSPolicy`), and authentication. If this is intentional, it should be documented; if not, SUB should require `stateConnected` (set after IDENTIFY completes).

- **Lines 206-207:** QUESTION (Severity: Medium) — `time.NewTicker(client.OutputBufferTimeout)` and `time.NewTicker(client.HeartbeatInterval)` are called at `messagePump` startup before IDENTIFY can adjust these values. `time.NewTicker` panics if the duration is <= 0. This is safe only if the client defaults guarantee positive values for both fields. If a code change ever sets either default to 0, this becomes a crash on every new connection.

---

### Summary

| Severity | Count | Type |
|----------|-------|------|
| High     | 2     | BUG  |
| Medium   | 3     | QUESTION |

- **BUG findings:** 2 (deflate level logic, unsafe pointer without length check)
- **QUESTION findings:** 3 (unchecked type assertion, SUB state machine skip, ticker panic on zero duration)

**Overall assessment:** FIX FIRST — The deflate level bug (line 366-371) silently breaks compression for clients that specify a level, and the unsafe pointer cast (lines 535/557/695) can read out-of-bounds memory on malformed input. Both should be fixed before shipping.
