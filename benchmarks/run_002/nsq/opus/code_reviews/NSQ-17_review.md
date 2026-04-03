# NSQ-17 Code Review: nsqd/protocol_v2.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `/tmp/qpb_wt_opus_NSQ-17/nsqd/protocol_v2.go` (701 lines)

---

## Findings

### nsqd/protocol_v2.go

- **Line 316-321:** BUG (High). **DeflateLevel is always 0 when client specifies a positive value.** The variable `deflateLevel` is initialized to `0` on line 316. When `identifyData.DeflateLevel <= 0`, it is set to `6` (line 319) as a default. But when `identifyData.DeflateLevel > 0`, there is no `else` branch to assign the client's requested value — `deflateLevel` stays `0`. Line 321 then computes `min(0, maxDeflateLevel)` which is always `0`. The client-requested deflate level is silently ignored and deflate compression effectively operates at level 0 (no compression). The fix is to add an `else` clause: `deflateLevel = identifyData.DeflateLevel`.

  ```go
  deflateLevel := 0
  if deflate {
      if identifyData.DeflateLevel <= 0 {
          deflateLevel = 6            // default
      }
      // BUG: missing else { deflateLevel = identifyData.DeflateLevel }
      deflateLevel = int(math.Min(float64(deflateLevel), float64(p.context.nsqd.options.maxDeflateLevel)))
  }
  ```

- **Line 483:** BUG (Medium). **Unsafe pointer cast without length validation on params[1].** `id := *(*nsq.MessageID)(unsafe.Pointer(&params[1][0]))` reinterprets the byte slice as a `MessageID` (16 bytes). The check at line 479 only validates `len(params) < 2` (i.e., that `params[1]` exists), but does not validate that `len(params[1]) >= len(MessageID)`. If a client sends a FIN command with a short ID (fewer than 16 bytes), this reads past the end of the slice's backing array, causing a buffer over-read. Same bug exists at **line 505** (REQ) and **line 643** (TOUCH).

- **Line 66:** QUESTION (Low). **Unchecked type assertion may panic.** `err.(util.ChildErr).Parent()` performs an unguarded type assertion. If any error returned by `p.Exec()` does not implement the `util.ChildErr` interface, this line panics. Currently all `Exec` paths return `NewFatalClientErr` or `NewClientErr` which likely implement `ChildErr`, but if a future code change introduces a different error type (or a nil-wrapped error), this becomes a runtime crash. A comma-ok assertion would be safer.

- **Line 402:** QUESTION (Low). **SUB requires StateInit, allowing SUB without IDENTIFY.** The `SUB` command checks `client.State != nsq.StateInit` (line 402), but `IDENTIFY` also requires `StateInit` (line 277) and does not transition the state to any intermediate value. This means a client can issue `SUB` without ever sending `IDENTIFY`, skipping feature negotiation (heartbeat, TLS, compression). This may be intentional for backward compatibility, but the review protocol flags "SUB jumping from stateInit to stateSubscribed (skipping stateConnected) is a known concern."

- **Line 111-114:** QUESTION (Low). **In-flight timeout starts before message is sent.** `StartInFlightTimeout(msg, client.ID)` is called at line 111 before `p.Send()` at line 114. If `Send` fails, the message is tracked as in-flight but was never delivered to the client. The message will eventually time out and be requeued (at-least-once semantics), so this may be intentional — but if the in-flight timeout is short relative to network latency, messages could churn through requeue cycles unnecessarily.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 1 |
| BUG (Medium) | 1 (3 locations) |
| QUESTION (Low) | 3 |

**Overall assessment: FIX FIRST**

The deflate level bug (line 316-321) silently breaks client-requested compression levels — any client requesting deflate with a specific level gets level 0 instead. The unsafe pointer cast without length validation (lines 483/505/643) is a memory safety issue exploitable by any connected client sending a malformed command. Both should be fixed before shipping.
