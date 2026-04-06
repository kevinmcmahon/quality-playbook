# NSQ-31 Code Review: internal/dirlock/dirlock.go, nsqd/nsqd.go

## internal/dirlock/dirlock.go

- **Line 24-28:** **BUG** (Medium) — `Lock()` opens the directory file and assigns it to `l.f` before checking whether `Flock` succeeds. If `Flock` fails (line 30-31), the file descriptor stored in `l.f` is never closed, causing a file descriptor leak. The error path returns without closing `f`. Expected: `f.Close()` should be called before returning the error on line 31.

- **Line 36-38:** **BUG** (Medium) — `Unlock()` calls `defer l.f.Close()` then `Flock(LOCK_UN)`. If `Lock()` was never called successfully (or was never called at all), `l.f` is nil and this will panic with a nil pointer dereference. There is no nil guard on `l.f`. Expected: either check `l.f != nil` or document that `Unlock()` must only be called after a successful `Lock()`.

## nsqd/nsqd.go

- **Line 82:** **QUESTION** (Low) — `os.Getwd()` error is silently discarded with `cwd, _ := os.Getwd()`. If `Getwd` fails, `cwd` is empty string and `dataPath` becomes `""`, which would be passed to `dirlock.New("")`. This could cause `os.Open("")` to fail later at `dl.Lock()`, but the error message would be confusing. Worth considering whether this should be a hard error.

- **Line 106-109:** **QUESTION** (Medium) — When `dl.Lock()` fails (line 106-108), the function returns an error but does not close the TCP/HTTP listeners that haven't been created yet. However, the function *does* create TCP listeners later (lines 152-167). Since Lock is called before listeners are created, this is fine. But validation checks on lines 111-146 also return errors without cleaning up the already-acquired directory lock (`n.dl`). If any validation fails after `dl.Lock()` succeeds, the directory lock is leaked for the lifetime of the process. Expected: `n.dl.Unlock()` should be called on error paths after line 109.

- **Line 152-167:** **QUESTION** (Medium) — When `net.Listen` for HTTP (line 157-160) or HTTPS (line 163-166) fails, the function returns an error without closing the previously successfully opened TCP listener (line 152) or HTTP listener. Resources are leaked on partial initialization failure. Expected: previously opened listeners should be closed on error.

- **Line 168-173:** **BUG** (Low) — `n.RealHTTPAddr()` on line 169 returns `&net.TCPAddr{}` (port 0) when `httpListener` is nil (lines 219-222). If `opts.HTTPAddress` is empty, `httpListener` is nil, and `BroadcastHTTPPort` remains 0. The type assertion on line 169 succeeds but yields port 0, which is silently used. This may cause downstream issues with nsqlookupd registration broadcasting port 0.

- **Line 393:** **BUG** (High) — `GetMetadata()` iterates over `n.topicMap` (line 393) without holding the NSQD read lock. The caller `PersistMetadata()` (line 423) does not acquire the lock either. However, `Notify()` (line 590) calls `PersistMetadata()` under `n.Lock()`, and `Exit()` (line 464) also calls it under `n.Lock()`. But there is no guarantee that `GetMetadata` is only called under the lock — it is a public method. A concurrent `GetTopic` or `DeleteExistingTopic` modifying `topicMap` while `GetMetadata` iterates would be a data race. The `Exit()` path is protected, but any external caller of `GetMetadata(true)` (e.g., from HTTP handlers) would race.

- **Line 328-339:** **QUESTION** (Medium) — `writeSyncFile()` calls `f.Close()` (line 339) without checking its error. On some filesystems (especially NFS), `Close()` can return an error indicating data was not flushed. The error from `f.Sync()` is checked but `Close()` errors are silently lost.

- **Line 427:** **QUESTION** (Low) — `PersistMetadata()` uses `rand.Int()` for the tmp filename (line 427). Since Go 1.20, `math/rand` is auto-seeded, so this is fine for uniqueness. However, in a concurrent scenario where `PersistMetadata` is called simultaneously (e.g., from multiple `Notify` goroutines), two goroutines could race on rename. The `n.Lock()` in `Notify()` prevents this for the normal path, but the method itself is not inherently safe.

- **Line 552-573:** **QUESTION** (Medium) — `DeleteExistingTopic()` reads `topicMap` under `RLock` (line 553-558), releases the lock, calls `topic.Delete()` (line 567) without any lock, then re-acquires `Lock` to delete from map (line 569-571). Between the `RUnlock` on line 559 and `Lock` on line 569, another goroutine could call `GetTopic` with the same name and re-create the topic in the map. The new topic would then be deleted from the map by the `delete` on line 570, losing the newly-created topic. The comment on lines 561-566 acknowledges this ordering concern but the TOCTOU window still exists.

## Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 1 |
| BUG (Medium) | 2 |
| BUG (Low) | 1 |
| QUESTION (Medium) | 4 |
| QUESTION (Low) | 2 |

**Total findings:** 10

**Overall assessment:** NEEDS DISCUSSION — The most critical issue is the unprotected iteration of `topicMap` in `GetMetadata()` (public method, data race). The dirlock file descriptor leak on failed `Lock()` and resource leaks on partial `New()` initialization failure should also be addressed.
