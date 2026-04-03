# Code Review: CHI-17 — middleware/recoverer.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**File:** `middleware/recoverer.go`

---

## Findings

### middleware/recoverer.go

- **Line 24:** [BUG] **Severity: High** — `http.ErrAbortHandler` panic is silently swallowed instead of being re-panicked. When `rvr == http.ErrAbortHandler`, the condition `rvr != nil && rvr != http.ErrAbortHandler` evaluates to false, so the deferred function does nothing and the panic is absorbed by `recover()`. The Go `net/http` server relies on `ErrAbortHandler` panics propagating up to its own recovery handler to abort the connection. By catching and not re-panicking, the middleware prevents the server from aborting the connection, causing it to complete normally (likely sending an empty 200 or a partial response). The CHANGELOG describes this as "suppress http.ErrAbortHandler" but suppression via silent swallow is incorrect — the fix is to `recover()`, then re-`panic(rvr)` when `rvr == http.ErrAbortHandler`.

- **Line 33:** [QUESTION] **Severity: Medium** — `w.WriteHeader(http.StatusInternalServerError)` is called after a panic, but if the handler already wrote headers (or partial body) before panicking, this call is a no-op (Go's `ResponseWriter` silently ignores a second `WriteHeader`). The client may receive a 200 with a truncated body rather than a 500. This is a known limitation of panic recovery in Go, but the middleware does not wrap the `ResponseWriter` to detect whether headers have been sent, so there is no indication to the operator that the 500 was not delivered.

- **Line 102–103:** [BUG] **Severity: Low** — Dead code in `decorateLine`: line 102 calls `strings.TrimSpace(line)` which strips all leading whitespace (including tabs). Then line 103 checks `strings.HasPrefix(line, "\t")` — this can never be true because TrimSpace already removed any leading tab. The branch still functions because the second part of the OR (`strings.Contains(line, ".go:")`) matches source lines, but the tab prefix check is dead logic.

- **Line 108:** [BUG] **Severity: Low** — Same dead code issue: after TrimSpace on line 102, the `strings.HasPrefix(line, "\t")` check on line 108 can never be true. This entire `if` branch inside the `else` is unreachable. The `else` block on lines 107–113 will always take the `else` path (line 111), formatting the line with 4-space indent.

- **Line 76:** [QUESTION] **Severity: Medium** — Potential panic inside the recoverer itself. If `"panic(0x"` is found on the first or second iteration of the reverse loop (lines 73–79), `len(lines)` could be 1 or 2, making `len(lines)-2` equal to -1 or 0. A slice expression `lines[0:-1]` would cause a runtime panic with "slice bounds out of range", which would occur inside the deferred `recover()` handler, potentially masking the original panic. In practice, `debug.Stack()` output typically has several trailing lines before the `panic(0x` line, but this is a Go runtime implementation detail that could change.

- **Line 75:** [QUESTION] **Severity: Low** — The heuristic `strings.HasPrefix(stack[i], "panic(0x")` for locating the panic frame is tied to Go runtime internals. Different Go versions or build modes (e.g., `-trimpath`) may produce different stack trace formats, causing the heuristic to fail. When it fails (no match found), the `lines` array contains the entire stack in reverse, producing garbled output. This is a robustness concern rather than a correctness bug.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 1 |
| Medium   | 2 |
| Low      | 3 |

**Total findings:** 6 (2 BUG, 4 QUESTION)

**Overall assessment:** **FIX FIRST** — The silent swallowing of `http.ErrAbortHandler` (line 24) is a high-severity bug that breaks the intended semantics of `ErrAbortHandler` for any application using this middleware. The dead code issues (lines 103, 108) are low-impact but indicate the parsing logic has a latent correctness problem.
