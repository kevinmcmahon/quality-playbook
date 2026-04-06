# Code Review: NSQ-13 — nsqd/lookup_peer.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `nsqd/lookup_peer.go` (at `/tmp/qpb_wt_opus_NSQ-13`)

---

### nsqd/lookup_peer.go

- **Line 93:** [BUG] Severity: **Medium**. `lp.Write(nsq.MagicV1)` return value (error) is discarded. If the magic bytes write fails (e.g., connection reset immediately after dial), the connection is left in an indeterminate protocol state. The `connectCallback` on line 95 is still invoked (which sends IDENTIFY + REGISTER commands per `lookup.go:26-55`), and the subsequent `cmd.WriteTo(lp)` on line 101 proceeds on a connection that nsqlookupd may not recognize as valid. The error should be checked and, on failure, `lp.Close()` called with the error returned, matching the error-handling pattern used on lines 102-104 and 107-109.

- **Line 75-76:** [BUG] Severity: **Medium**. `Close()` unconditionally calls `lp.conn.Close()` but `lp.conn` may be nil — the field is only set inside `Connect()` (line 52). If `Close()` is called on a peer that was never successfully connected (or was created but `Connect()` returned an error), this panics with a nil pointer dereference. While current callers in `lookup.go:143` iterate over all peers at shutdown, a peer whose initial `Command(nil)` (line 57) failed to connect would have `conn == nil` and `state == stateDisconnected`, so `Close()` would panic. A nil guard on `lp.conn` before calling `Close()` is needed.

- **Line 86-92:** [QUESTION] Severity: **Low**. `lp.state` is typed `int32` but is read and written with plain (non-atomic) operations throughout `Command()`, `Close()`, and `newLookupPeer()`. The shared state constants (`stateInit`, `stateDisconnected`, `stateConnected` defined in `client_v2.go:20-22`) are used with `atomic.LoadInt32`/`atomic.StoreInt32` for client state in `protocol_v2.go`, but `lookupPeer` uses bare assignments. This is safe only if `lookupPeer` is always accessed from a single goroutine. Reviewing `lookup.go`, all `Command()` calls happen within the `lookupLoop` goroutine, and `Close()` in `lookup.go:143` runs after the loop exits. So this appears safe in current usage, but the lack of synchronization makes it fragile if usage ever changes.

- **Line 87-96:** [QUESTION] Severity: **Low**. The three-state logic in `Command()` is subtle. When `state != stateConnected`, it reconnects. But the `connectCallback` is only invoked when `initialState == stateDisconnected` (line 94), not when `initialState == stateInit`. Since `stateInit = 0` (iota), a zero-valued `lookupPeer` (not created via `newLookupPeer`) would have `state == stateInit`, which means on first `Command()` call it would connect and write magic bytes but skip the `connectCallback`. This is not a bug because `newLookupPeer` explicitly sets `state: stateDisconnected` (line 40), but the implicit reliance on the constructor is worth noting — the `stateInit` value has no meaningful role for `lookupPeer` and exists only because the constants are shared with `client_v2`.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (Medium) | 2 |
| QUESTION (Low) | 2 |

**Overall assessment:** **NEEDS DISCUSSION** — The unchecked write error on line 93 can silently corrupt the protocol handshake with nsqlookupd, causing registration failures that are hard to diagnose. The nil conn panic in `Close()` is a crash risk during error paths at shutdown. Both are straightforward fixes.
