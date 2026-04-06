# Code Review: middleware/recoverer.go

**Reviewer:** sonnet
**Date:** 2026-03-31
**Worktree:** /tmp/qpb_wt_chi_sonnet_CHI-07

---

## middleware/recoverer.go

### Finding 1

- **Line 24:** [BUG] `http.ErrAbortHandler` panic is consumed but not re-panicked.
- **Severity:** High
- **Description:**
  `recover()` is called unconditionally in the deferred closure. This consumes the panic — including `http.ErrAbortHandler` — before the `&& rvr != http.ErrAbortHandler` guard is evaluated. When `rvr == http.ErrAbortHandler`, the condition is false (correct: no log, no 500 written), but `recover()` has already absorbed the panic. The panic never propagates to net/http's own deferred recovery in `(*conn).serve()`, which is responsible for closing the connection when it sees `ErrAbortHandler`.
  **Expected:** `ErrAbortHandler` is re-panicked after being recovered, so `net/http` can properly abort and close the connection.
  **Actual:** The panic is silently consumed; `fn` returns normally to the server, leaving the connection alive and sending whatever partial/empty response happens to be in the buffer (likely a 200 with no body).
  **Why it matters:** Code that calls `panic(http.ErrAbortHandler)` to forcibly abort a request and close the connection (e.g., after detecting a hijack, timeout, or security abort) gets a silent no-op instead. The connection is not closed; the client receives a response it should never see.

  The correct pattern is:
  ```go
  if rvr := recover(); rvr != nil {
      if rvr == http.ErrAbortHandler {
          panic(rvr) // re-panic so net/http closes the connection
      }
      // log and write 500
  }
  ```

---

### Finding 2

- **Line 75:** [BUG] Panic-line detection prefix `"panic(0x"` does not match Go 1.17+ stack trace format.
- **Severity:** Medium
- **Description:**
  `prettyStack.parse` searches backward through the debug stack for the panic line using `strings.HasPrefix(stack[i], "panic(0x")`. In Go 1.17+, the runtime changed the format of interface-valued arguments in stack traces from `panic(0xABCD, 0x1234)` to `panic({0xABCD, 0x1234})` (curly braces around the value pair). The prefix is now `"panic({0x"`, not `"panic(0x"`.
  **Expected:** The panic line is found, `lines` is trimmed with `lines[0:len(lines)-2]` to remove boilerplate, and the output is properly formatted.
  **Actual:** On Go 1.17+ (which covers all practical deployments), the `break` is never reached. The loop collects all stack lines from the end up to index 1. The `lines = lines[0:len(lines)-2]` slice never executes, leaving boilerplate goroutine header lines in the output. `decorateLine` will process them through the `else` branch (no error), so `parse` returns non-nil output — but the output includes the goroutine header and is not trimmed as intended. The pretty-stack output is malformed for every panic in Go 1.17+.
  **Why it matters:** Every invocation of `PrintPrettyStack` on a modern Go runtime produces incorrect output. Since `go.mod` declares `go 1.14` (not yet bumped), the code may be used with any Go version, but the practical minimum for new deployments is 1.17+.

---

### Finding 3

- **Line 103:** [BUG] `strings.HasPrefix(line, "\t")` is dead code after `strings.TrimSpace(line)` on line 102.
- **Severity:** Low
- **Description:**
  `decorateLine` calls `line = strings.TrimSpace(line)` on line 102, which strips all leading and trailing whitespace, including tab characters. The immediately following condition on line 103 checks `strings.HasPrefix(line, "\t")`. After `TrimSpace`, no line can start with `\t`, so this branch is always false. The same dead-check appears at line 108 in the else branch.
  **Expected:** Source lines (raw form: `\t/path/to/file.go:123`) are detected by the leading `\t` after trimming — OR the trim should not happen before the prefix check.
  **Actual:** Source line detection falls entirely on the `strings.Contains(line, ".go:")` second condition, which happens to be correct for all `.go` source lines — so the function still routes source lines to `decorateSourceLine` correctly. The `\t` prefix check is a dead guard that does nothing. The branch at line 108 (tab-to-spaces replacement in the else) is also unreachable.
  **Why it matters:** Low functional impact because `.go:` detection covers source lines correctly. However, any file path that does not contain `.go:` and doesn't end with `)` (e.g., a native library frame) falls through to the else and loses the tab-to-spaces replacement it would have gotten.

---

### Finding 4

- **Line 33:** [QUESTION] `w.WriteHeader(http.StatusInternalServerError)` is a no-op if the handler wrote a response before panicking.
- **Severity:** Medium
- **Description:**
  If `next.ServeHTTP(w, r)` calls `w.WriteHeader()` or `w.Write()` (which implicitly calls `WriteHeader(200)`) before panicking, the response status is already committed. A subsequent `w.WriteHeader(http.StatusInternalServerError)` will be silently ignored by `net/http`'s response writer. The client receives the partial response with the previously-committed status (e.g., 200) and an abruptly terminated body.
  **Expected:** Panics mid-response might ideally be handled differently (e.g., aborting the connection via hijack rather than writing a 500), but this is an inherent HTTP limitation.
  **Actual:** The 500 write is silently dropped; the client receives the earlier committed status with a partial or empty body.
  **Why it matters:** Flagging as QUESTION because this is a well-known limitation of HTTP response middleware — not a code error but a design gap. The alternative (response-recorder buffering) has its own tradeoffs. Callers should be aware that the 500 is not guaranteed.

---

## Summary

| # | Type | Severity | Line | Description |
|---|------|----------|------|-------------|
| 1 | BUG | High | 24 | `ErrAbortHandler` panic is consumed and not re-panicked; connection is not aborted |
| 2 | BUG | Medium | 75 | `"panic(0x"` prefix doesn't match Go 1.17+ stack trace format `"panic({0x"` |
| 3 | BUG | Low | 103 | `HasPrefix(line, "\t")` is dead code after `TrimSpace` on line 102 |
| 4 | QUESTION | Medium | 33 | `w.WriteHeader(500)` silently dropped if response already committed |

**Total:** 3 BUGs (1 High, 1 Medium, 1 Low), 1 QUESTION (Medium)

**Overall assessment: FIX FIRST** — Finding #1 is a real behavioral bug: code that panics with `http.ErrAbortHandler` to forcibly close a connection gets a silent no-op from this middleware, leaving the connection alive with an unintended response. Finding #2 means the pretty-printer is effectively broken on all Go 1.17+ runtimes.
