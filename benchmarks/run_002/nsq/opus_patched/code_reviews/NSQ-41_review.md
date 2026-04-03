# NSQ-41 Code Review: nsqd/nsqd.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Source:** `/tmp/qpb_wt_retest_NSQ-41/nsqd/nsqd.go`
**Focus Areas:** 9 (Configuration Parameter Validation), 10 (Input Validation Failure Modes), 11 (Exit Path Resource Completeness), 12 (Go Channel Lifecycle in Select Statements)

---

## nsqd/nsqd.go

### Finding 1 — BUG (Medium): TLSClientAuthPolicy unconditionally overwrites TLSRequired

- **Lines 121–122**
```go
if opts.TLSClientAuthPolicy != "" {
    opts.TLSRequired = TLSRequired
}
```
- **Expected:** When a user explicitly sets `TLSRequired` to `TLSRequiredExceptHTTP` (value 1) to allow plaintext HTTP while requiring TLS for TCP, that setting should be preserved. The guard should be: `if opts.TLSClientAuthPolicy != "" && opts.TLSRequired == TLSNotRequired { opts.TLSRequired = TLSRequired }`.
- **Actual:** Any non-empty `TLSClientAuthPolicy` unconditionally sets `TLSRequired = TLSRequired` (value 2), clobbering an explicit user choice of `TLSRequiredExceptHTTP`. This matches the protocol's prohibited pattern: "An unconditional `if flagA != '' { flagB = X }` clobbers explicit user settings."
- **Impact:** An operator who sets `--tls-required=tcp-https` (meaning TLSRequiredExceptHTTP) alongside `--tls-client-auth-policy=require` will silently get full TLS requirement on HTTP as well, with no error or warning.

### Finding 2 — BUG (High): Exit() does not close active TCP connections

- **Lines 370–398** (full `Exit()` method)
- **Expected:** Shutdown should: (a) close listeners to stop new connections, (b) iterate and close all active client connections, (c) close topics/channels, (d) signal goroutines, (e) wait for all goroutines.
- **Actual:** Exit() closes listeners (lines 371–381), then closes topics (lines 389–391), then closes exitChan (line 396) and waits on waitGroup (line 397). There is **no explicit closing of active TCP connections**. The `tcpServer` struct (tcp.go:10–12) has no `conns` tracking field and no `Close()` method. `protocol.TCPServer` (internal/protocol/tcp_server.go:33) spawns `go handler.Handle(clientConn)` with no WaitGroup tracking.
- **Resource audit of Exit():**
  | Resource | Cleanup in Exit()? |
  |---|---|
  | TCP listener | Yes (line 372) |
  | HTTP listener | Yes (line 376) |
  | HTTPS listener | Yes (line 380) |
  | Active TCP connections (subscribed clients) | Partial — closed via topic.Close() → channel.exit() → client.Close() (channel.go:173–176) |
  | Active TCP connections (unsubscribed clients) | **NO** — clients in stateInit or stateConnected are not reachable via topic→channel→client path |
  | Client IOLoop goroutines | **NO** — not tracked in n.waitGroup; spawned via `go handler.Handle()` in TCPServer |
  | Metadata | Yes — PersistMetadata() at line 384 |
  | Topics/channels/backends | Yes — topic.Close() at line 390 |
  | idPump goroutine | Yes — exits via exitChan (line 500–503) |
  | lookupLoop goroutine | Yes — exits via exitChan |
  | statsdLoop goroutine | Yes — exits via exitChan |
- **Impact:** On shutdown, clients that are connected but have not yet subscribed to a channel (stateInit, stateConnected) will not be closed. Their IOLoop goroutines will continue running after `Exit()` returns. This can cause the process to hang or leak goroutines if the caller expects a clean shutdown. Additionally, `n.waitGroup.Wait()` does not wait for these client goroutines since they are not tracked.

### Finding 3 — BUG (Medium): PersistMetadata iterates topicMap without holding its own lock

- **Line 315**
```go
for _, topic := range n.topicMap {
```
- **Expected:** `PersistMetadata()` should either acquire `n.RLock()` internally or document that callers must hold the lock.
- **Actual:** The function does not acquire any lock. It relies on callers holding `n.Lock()`. Current callers (Exit() at line 383, Notify() at line 518) do hold the lock, so this is not a bug with current code. However, `PersistMetadata()` is an exported method, making it callable without the lock by any new caller (including HTTP handlers or tests).
- **Impact:** A future caller without the lock would cause a data race on `n.topicMap` iteration. The function's exported status makes this a latent correctness hazard.
- **Note:** Flagging as BUG (not QUESTION) because an exported method that requires external locking without documentation or enforcement is a defect in the API contract.

### Finding 4 — QUESTION (Low): buildTLSConfig silently accepts invalid TLSClientAuthPolicy values

- **Lines 541–548**
```go
switch opts.TLSClientAuthPolicy {
case "require":
    tlsClientAuthPolicy = tls.RequireAnyClientCert
case "require-verify":
    tlsClientAuthPolicy = tls.RequireAndVerifyClientCert
default:
    tlsClientAuthPolicy = tls.NoClientCert
}
```
- **Observation:** Any unrecognized value (e.g., `"required"`, `"verify"`, `"yes"`) silently falls through to `default` and sets `tls.NoClientCert`. Combined with Finding 1, this means setting `--tls-client-auth-policy=typo` will: (a) trigger `TLSRequired = TLSRequired` at line 122 (because the string is non-empty), AND (b) set the actual TLS client auth to `NoClientCert`. The operator gets full TLS requirement with no client certificate verification — the opposite of what they likely intended.
- **Impact:** A typo in a security-critical configuration silently degrades to the least secure option while simultaneously escalating TLS requirement. No error or warning is produced.

### Finding 5 — QUESTION (Low): Dead initialization in buildTLSConfig

- **Line 535**
```go
tlsClientAuthPolicy := tls.VerifyClientCertIfGiven
```
- **Observation:** This initial value is immediately overwritten by the switch statement at lines 541–548, which covers all cases including default. The `VerifyClientCertIfGiven` value is never used. This is dead code that could mislead readers into thinking it serves as a fallback.

### Finding 6 — QUESTION (Low): DeleteExistingTopic has TOCTOU gap

- **Lines 461–479**
```go
func (n *NSQD) DeleteExistingTopic(topicName string) error {
    n.RLock()
    topic, ok := n.topicMap[topicName]
    ...
    n.RUnlock()       // line 468: releases lock

    topic.Delete()    // line 476: no lock held, gap here

    n.Lock()          // line 478: re-acquires write lock
    delete(n.topicMap, topicName)
    n.Unlock()
```
- **Observation:** Between `n.RUnlock()` at line 468 and `n.Lock()` at line 478, another goroutine could call `GetTopic()` with the same name. `GetTopic()` would find the topic in the map (it hasn't been deleted yet), return it, and the caller would have a reference to a deleted/deleting topic. The code comment at lines 470–475 acknowledges this is intentional (topic.Delete() sets exitFlag before map removal), but it relies on callers checking `topic.Exiting()` after getting a reference — which `GetTopic()` does not do.

---

## Summary

| Severity | Count | Findings |
|----------|-------|----------|
| Critical | 0 | — |
| High | 1 | #2 (Exit path missing active connection cleanup) |
| Medium | 2 | #1 (TLSRequired clobber), #3 (PersistMetadata locking) |
| Low | 3 | #4 (silent invalid TLS policy), #5 (dead init), #6 (TOCTOU gap) |
| **Total** | **6** | |

| Type | Count |
|------|-------|
| BUG | 3 (#1, #2, #3) |
| QUESTION | 3 (#4, #5, #6) |

**Overall Assessment:** **FIX FIRST**

Finding #2 (High) is the most impactful: `Exit()` cannot guarantee a clean shutdown because unsubscribed client connections and their goroutines are not tracked or closed. This is the classic "closing a listener does not close existing connections" pattern identified in Focus Area 11. Findings #1 and #4 combine to create a dangerous configuration interaction where a typo silently escalates TLS requirements while disabling client certificate verification.
