# NSQ-57 Code Review: nsqd/nsqd.go and nsqd/topic.go

## nsqd/nsqd.go

- **Line 82:** QUESTION (Low) — `os.Getwd()` error is silently discarded (`cwd, _ := os.Getwd()`). If the working directory has been deleted or is otherwise inaccessible, `cwd` will be an empty string, causing `dataPath` to be `""`. Downstream, `dirlock.New("")` and `diskqueue.New` will operate on the current directory root, and metadata will be written to unexpected locations. Unlikely in practice but the error discard masks a startup misconfiguration.

- **Line 338:** BUG (Medium) — `writeSyncFile()` discards the error from `f.Close()`. After a successful `Write` and `Sync`, the file is closed but the `Close` return value is ignored. On certain filesystems (NFS, FUSE), `Close` can report deferred write errors. Since `PersistMetadata` (lines 427-436) writes to a temp file via `writeSyncFile` and then renames it over the real metadata file, a silent `Close` failure means a corrupt temp file could be atomically renamed into place, corrupting metadata. Expected: `return f.Close()` when `err == nil`, or capture the close error.

- **Lines 389-413:** BUG (Medium) — `GetMetadata()` iterates `n.topicMap` (line 393) without acquiring `n.RLock()`. The method relies on callers to hold the NSQD-level lock. All current callers do hold the lock (`PersistMetadata` is called from `Exit` and `Notify` under `n.Lock()`, and HTTP handlers in http.go:424-426 and http.go:495-497 acquire `n.Lock()` before calling `PersistMetadata`). However, `GetMetadata` is an exported method with no documentation of this precondition. A future caller invoking `GetMetadata` without the lock would cause a data race on the `topicMap` map. The locking should either be internal to `GetMetadata` or the method should be unexported.

- **Line 427:** QUESTION (Low) — `PersistMetadata()` uses `rand.Int()` (line 427) to generate the temp file suffix. Since Go 1.20, the global `math/rand` source is automatically seeded, but prior to that, `rand.Int()` returns deterministic values unless explicitly seeded. If two processes start simultaneously with the old behavior, they could generate the same temp filename. In current Go versions this is not an issue.

- **Line 479:** QUESTION (Low) — In `Exit()`, `n.ctxCancel()` is called at line 479 after `close(n.exitChan)` at line 475 and `n.waitGroup.Wait()` at line 476. Any code relying on `n.ctx` for shutdown signaling will not observe cancellation until after all goroutines tracked by the wait group have already exited. If the intent is for `n.ctx` to be usable as a shutdown signal (the `Context()` method at line 798 suggests this), the cancellation ordering may be too late. Currently `exitChan` is the primary shutdown mechanism, so this may be intentional.

## nsqd/topic.go

- **Lines 418-439:** BUG (Medium) — `flush()` always returns `nil` (line 439) even when `writeMessageToBackend` fails at line 428. Errors are logged but not propagated. The caller `exit()` at line 401 calls `t.flush()` but the return value is discarded anyway. During graceful shutdown, if the disk backend is unhealthy, messages drained from `memoryMsgChan` will be silently lost with no error surfaced to the operator beyond log lines. Expected: accumulate or return the first error so that `exit()` can report shutdown data loss.

- **Lines 79-81:** QUESTION (Medium) — `NewTopic()` starts the `messagePump` goroutine (line 79) and calls `n.Notify()` (line 81) inside the constructor, before the caller (`GetTopic`) assigns the topic to `n.topicMap` (nsqd.go line 504). The `Notify` goroutine will eventually call `PersistMetadata` -> `GetMetadata`, which iterates `topicMap`. Because the Notify goroutine must first send on `notifyChan` (which blocks until `lookupLoop` receives), and `GetTopic` holds `n.Lock()` during assignment while `Notify`'s goroutine needs `n.Lock()` for `PersistMetadata`, the ordering is safe in practice. However, this is a fragile implicit ordering dependency — if `notifyChan` were buffered or the locking in `Notify` changed, the newly created topic could be missed from metadata persistence.

- **Lines 224-231:** QUESTION (Low) — In `put()`, when `cap(t.memoryMsgChan) == 0` (mem-queue-size=0) and the message is deferred (`m.deferred != 0`), the code enters the if-block (line 224, `m.deferred != 0` is true), attempts a non-blocking send on the zero-capacity channel (which always falls through to `default`), and writes to the backend. The comment at lines 221-223 acknowledges that deferred messages "lose deferred timer in backend queue." This means with `mem-queue-size=0`, all deferred messages lose their deferred semantics and are delivered immediately when read back from disk. This is a known limitation but not obvious from the API.

- **Lines 377-381:** No bug — In `exit(deleted=true)`, `channel.Delete()` is called at line 380 after `delete(t.channelMap, channel.name)` at line 379 within the same iteration, while holding `t.Lock()` (line 377). Verified: `channel.Delete()` calls `channel.exit(true)` (channel.go:161-162) which does NOT invoke `deleteCallback` — the callback is only triggered from a different path (channel.go:505, when an ephemeral channel loses all clients). So no deadlock occurs. The map-delete-during-iteration is safe in Go.

## Summary

| Severity | Count | Details |
|----------|-------|---------|
| BUG (Medium) | 3 | `writeSyncFile` ignoring `Close()` error (nsqd.go:338), `GetMetadata` missing lock (nsqd.go:393), `flush()` swallowing errors (topic.go:418) |
| QUESTION (Medium) | 1 | Constructor side-effects ordering (topic.go:79) |
| QUESTION (Low) | 4 | `os.Getwd` error discard (nsqd.go:82), `rand.Int` seeding (nsqd.go:427), context cancel ordering (nsqd.go:479), deferred msg backend limitation (topic.go:224) |

**Overall assessment:** NEEDS DISCUSSION — The three medium-severity BUGs are in the metadata persistence and shutdown paths. The `writeSyncFile` close-error discard and `GetMetadata` missing internal lock are correctness issues in the metadata persistence path that could lead to silent metadata corruption. The `flush()` error swallowing means shutdown data loss is not reported to callers.
