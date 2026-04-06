# NSQ-39 Code Review: nsqd/nsqd.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `nsqd/nsqd.go` (at `/tmp/qpb_wt_opus_NSQ-39/nsqd/nsqd.go`)

---

### nsqd/nsqd.go

- **Line 664-678:** BUG (Medium). `queueScanLoop` `goto loop` bypasses `exitChan` check, preventing graceful shutdown under sustained load. When the dirty channel percentage exceeds `QueueScanDirtyPercent`, `goto loop` at line 678 jumps back to label `loop:` at line 664, which dispatches work and waits for responses — but never re-enters the `select` statement (lines 646-657) that checks `n.exitChan`. If channels are continuously dirty (sustained write load), this tight loop runs indefinitely and `queueScanLoop` never observes the exit signal. This causes `n.waitGroup.Wait()` in `Exit()` (line 419) to hang, blocking shutdown. **Expected:** The loop should check `exitChan` between iterations. **Actual:** `goto loop` skips the only `exitChan` check.

- **Line 392-395:** BUG (Low). `Exit()` reads `n.tcpListener`, `n.httpListener`, and `n.httpsListener` without holding any lock. These fields are set under `n.Lock()` in `Main()` (lines 207-209, 221-222, 238-240). If `Exit()` is called while `Main()` is still initializing listeners, this is a data race. **Expected:** Read listener fields under `n.RLock()`, or use a synchronization mechanism to ensure `Main()` has completed before `Exit()` runs. **Actual:** Raw pointer reads with no synchronization.

- **Line 484-504:** QUESTION (Medium). `DeleteExistingTopic` uses a two-phase lock pattern: reads `topicMap` under `RLock` (line 484), releases (line 490), calls `topic.Delete()` (line 498), then re-acquires `Lock` (line 500) to remove from map. Between `RUnlock` at line 490 and `Lock` at line 500, `GetTopic()` could acquire the write lock, find the topic still in the map, and return a reference to a topic that is being (or has been) deleted. The comment at lines 493-497 suggests this is intentional (to make incoming writes fail), but it means callers of `GetTopic` may receive a closed/deleted topic object.

- **Line 337:** QUESTION (Medium). `PersistMetadata()` iterates `n.topicMap` (line 337: `for _, topic := range n.topicMap`) without acquiring its own lock — it relies entirely on callers to hold `n.Lock()`. The function is exported, making it fragile. Current internal callers are correct: `Exit()` (line 405), `Notify()` (line 547), and HTTP handlers (http.go lines 432-434, 503-505) all hold the lock. However, the test file (`nsqd_test.go` line 99) calls `PersistMetadata()` without holding the lock, which is a data race under `-race` testing if any other goroutine accesses `topicMap` concurrently.

- **Line 695-708:** QUESTION (Low). In `buildTLSConfig`, `tlsClientAuthPolicy` is initialized to `tls.VerifyClientCertIfGiven` at line 695, but this is immediately overwritten by the switch at lines 701-708 — the initialization is dead code. More importantly, the `default` case (line 706) silently sets `tls.NoClientCert` for any unrecognized `TLSClientAuthPolicy` string. A typo in configuration (e.g., `"require_verify"` instead of `"require-verify"`) would silently disable client certificate verification with no warning, which is a security-sensitive silent failure.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (Medium) | 1 |
| BUG (Low) | 1 |
| QUESTION (Medium) | 2 |
| QUESTION (Low) | 1 |

**Overall assessment:** NEEDS DISCUSSION

The `goto loop` issue in `queueScanLoop` (line 664-678) is a real correctness bug that can prevent graceful shutdown under sustained load. The other findings are lower severity but worth reviewing — particularly the lock-free reads in `Exit()` and the silent TLS policy downgrade in `buildTLSConfig`.
