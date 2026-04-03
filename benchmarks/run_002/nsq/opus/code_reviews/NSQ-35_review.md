# Code Review: NSQ-35 — apps/nsq_to_file/topic_discoverer.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `apps/nsq_to_file/topic_discoverer.go`

---

### topic_discoverer.go

- **Line 80:** BUG (High). `break` inside a `select` only breaks out of the `select` statement, not the enclosing `for` loop (line 67). After receiving a termination signal, the code closes all `cfl.F.termChan` channels (lines 77-79), then breaks out of the `select` — but immediately re-enters the `for` loop and blocks on `select` again. Consequences:
  1. **`t.wg.Wait()` on line 87 is unreachable dead code.** The process never cleanly waits for consumer goroutines to finish, so graceful shutdown with in-flight message draining never occurs.
  2. **Double-close panic.** If a second `SIGINT`/`SIGTERM` arrives (common when users press Ctrl-C twice), the `termChan` case fires again and attempts to `close(cfl.F.termChan)` on already-closed channels, causing a panic.
  3. **Post-shutdown topic creation.** If `sync` is true, the ticker can fire after termination was signaled, calling `updateTopics()` which creates new consumers and goroutines that will never be shut down.

  **Fix:** Use a labeled break (`break` with a label on the `for` loop) or simply `return` after closing the termChans and waiting.

- **Line 65:** QUESTION (Low). `time.Tick(*topicPollRate)` returns a channel backed by a `time.Ticker` that can never be stopped or garbage collected. In this case the ticker lives for the entire process lifetime so it's not a real leak, but if `poller` were ever called in a context where it returns (e.g., after fixing the break bug above with a `return`), the ticker would leak. The standard recommendation is `time.NewTicker()` with a deferred `Stop()`.

- **Line 94:** QUESTION (Low). `regexp.MatchString(pattern, name)` recompiles the regex pattern on every call to `allowTopicName`. If `updateTopics` is called frequently with many topics, this is redundant work. Not a correctness bug — `MatchString` handles compilation errors by returning false (line 96) — but the repeated compilation is wasteful. A pre-compiled `regexp.Regexp` passed into the function or stored on the struct would avoid this.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 1 |
| QUESTION (Low) | 2 |

**Overall assessment:** **FIX FIRST** — The `break`-in-`select` bug on line 80 means graceful shutdown is completely broken: consumer goroutines are never waited on, and a second signal causes a panic from double-closing channels. This must be fixed before shipping.
