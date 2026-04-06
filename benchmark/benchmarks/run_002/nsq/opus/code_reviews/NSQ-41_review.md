# NSQ-41 Code Review: nsqd/nsqd.go

## nsqd/nsqd.go

- **Line 315:** [BUG] `PersistMetadata()` iterates `n.topicMap` without acquiring any lock itself. It relies entirely on callers to hold `n.Lock()`. Both current callers (`Exit()` at line 383 and `Notify()` at line 518) do hold the lock, but `PersistMetadata` is an exported method. Any future or external caller that omits the lock will cause a data race on the `topicMap` iteration. Severity: **Medium**. The function should either acquire its own lock or be unexported to make the locking contract enforceable.

- **Line 461-468:** [QUESTION] `DeleteExistingTopic()` checks topic existence under `RLock` (line 462), releases `RUnlock` (line 468), then calls `topic.Delete()` (line 476), then acquires `Lock` to remove from map (line 478). Two concurrent `DeleteExistingTopic` calls for the same topic name will both pass the existence check and both call `topic.Delete()`. The `atomic.CompareAndSwapInt32` in `topic.exit()` (topic.go:298) prevents double-close, so the second caller gets an error from `Delete()` but this error is silently discarded — `DeleteExistingTopic` still proceeds to `delete(n.topicMap, topicName)` and returns `nil` (success) to both callers. Severity: **Low**. Not a crash bug due to CAS protection, but the second caller receives a false success.

- **Line 423:** [QUESTION] `n.lookupPeers` is read without holding the NSQD lock (released at line 420). In `lookup.go:58`, `lookupPeers` is appended to inside `lookupLoop()`, which runs concurrently. Slice reads concurrent with slice appends are a data race in Go. In practice, `lookupLoop` likely finishes populating `lookupPeers` before any client connects and calls `GetTopic`, but this is a scheduling-dependent assumption, not a guarantee. Severity: **Low**.

- **Line 348:** [QUESTION] `rand.Int()` is used to generate temp file names for atomic metadata writes. On Go versions prior to 1.20, the default `math/rand` source is seeded with a constant (0), making temp file names predictable and identical across restarts. This could cause temp file collisions if a previous temp file was not cleaned up, or in theory a symlink attack on the data directory. Go 1.20+ auto-seeds the global source, making this a non-issue on newer versions. Severity: **Low** (depends on Go version in use).

- **Line 554:** [QUESTION] `MaxVersion` is hardcoded to `tls.VersionTLS12` with a comment referencing Go 1.5 (`TLS_FALLBACK_SCSV`). Go 1.5 is from 2015 and Go has supported TLS 1.3 since Go 1.12 (2019). This cap prevents TLS 1.3 negotiation, which provides improved security and performance. If the codebase has moved to Go >= 1.12, this limit is unnecessarily restrictive. Severity: **Low**.

- **Line 511-526:** [QUESTION] `Notify()` spawns a new goroutine per call. Each goroutine sends on the unbuffered `notifyChan`, then acquires `n.Lock()` and calls `PersistMetadata()`. During shutdown, `Exit()` holds the lock (line 383), persists metadata, closes topics, then releases the lock (line 393). Any `Notify` goroutines that already sent to `notifyChan` but are blocked waiting for the lock will then acquire it and call `PersistMetadata()` on already-closed topics. `PersistMetadata` reads `topic.IsPaused()` and iterates `topic.channelMap` — if `Close()` has already cleared or modified channel state, this could persist stale or inconsistent metadata. Severity: **Low**. The persisted file would be overwritten on next clean startup anyway, but a crash during this window could leave inconsistent metadata on disk.

## Summary

| Severity | Count |
|----------|-------|
| BUG      | 1     |
| QUESTION | 5     |

- **BUG findings:** 1 (exported PersistMetadata without lock self-protection)
- **QUESTION findings:** 5 (TOCTOU in DeleteExistingTopic, lookupPeers race, rand seed, TLS 1.2 cap, post-shutdown Notify)
- **Files with no findings:** N/A (single file review)

**Overall assessment:** NEEDS DISCUSSION — The one BUG (PersistMetadata lock contract) is currently safe because all callers hold the lock, but the exported API makes it fragile. The QUESTIONs are low-severity concurrency concerns that appear mitigated by runtime ordering but lack formal guarantees.
