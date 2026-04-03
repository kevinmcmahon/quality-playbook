# NSQ-06 Code Review: nsqd/lookup.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `nsqd/lookup.go` (at `/tmp/qpb_wt_opus_NSQ-06/nsqd/lookup.go`)
**Cross-reference:** `nsqd/lookup_peer.go` (for `Command()` behavior)

---

## nsqd/lookup.go

### Finding 1

- **Line 166-172:** **BUG** (Low severity)

  **Lookup peers are not closed on graceful shutdown.** When `exitChan` fires, the `lookupLoop` jumps to `exit:` which only logs and returns. The TCP connections held by each `lookupPeer` in the `lookupPeers` slice are never closed.

  Compare with the `optsNotificationChan` handler at **line 161** which correctly calls `lp.Close()` for removed peers. The exit path has no equivalent cleanup.

  **Expected:** Each peer in `lookupPeers` should be closed before the function returns, similar to how removed peers are closed at line 161.
  **Actual:** Connections are abandoned. The OS will eventually reclaim them on process exit, but this violates graceful shutdown expectations and could delay shutdown if the remote end holds the connection open.

### Finding 2

- **Line 29-48:** **QUESTION** (Medium severity)

  **Topic sync is triggered even when IDENTIFY fails.** In `connectCallback`, if `lp.Command(cmd)` at line 29 returns an error (IDENTIFY fails), the error is logged but execution continues to lines 46-48 where `lp` is sent to `syncTopicChan`. This triggers the topic registration handler (lines 126-150) to send REGISTER commands to a peer whose IDENTIFY handshake failed.

  The same applies if the IDENTIFY response is `E_INVALID` (line 32) or if JSON unmarshaling fails (line 36) — in all error cases, the function falls through to the `syncTopicChan` send.

  **Question:** Is this intentional? The peer may be in an inconsistent state. If IDENTIFY returned `E_INVALID`, should we still register topics with it? The `lp.Info` fields (including `BroadcastAddress` and `HTTPPort`) will be zero-valued, causing `lookupdHTTPAddrs()` (line 191) to correctly skip this peer — but the REGISTER commands still consume network I/O unnecessarily.

### Finding 3

- **Line 148:** **QUESTION** (Low severity)

  **`break` on first REGISTER error leaves peer with partial topic/channel view.** When syncing topics to a newly connected peer (lines 126-150), if any single `lookupPeer.Command(cmd)` call fails, the `break` at line 148 aborts the remaining REGISTER commands. The peer will only know about the topics/channels that were successfully registered before the failure.

  There is no retry mechanism for the skipped registrations. The peer will only learn about the missing topics/channels if they are subsequently updated (triggering a notification on `notifyChan`) or if the peer reconnects.

  **Question:** Should this `break` be a `continue` (skip the failed command, try the rest), or is the assumption that a single failure means the connection is broken and all subsequent commands would also fail? Given that `Command()` calls `lp.Close()` on write/read errors (lookup_peer.go lines 111, 116), a broken connection would indeed cause all subsequent calls to attempt reconnection — but the reconnection would trigger `connectCallback` again, restarting the full sync. So the `break` may be intentionally relying on this reconnection behavior.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG      | 1     |
| QUESTION | 2     |

- **BUG (1):** Lookup peers not closed on exit (line 166-172)
- **QUESTION (2):** Topic sync after failed IDENTIFY (line 29-48); break on first error during registration sync (line 148)

**Overall assessment:** **NEEDS DISCUSSION** — The missing cleanup on exit is a real (though low-severity) bug. The two QUESTIONs relate to error-recovery design decisions that could cause unnecessary work or delayed convergence but are unlikely to cause data loss.
