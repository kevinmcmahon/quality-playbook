# Code Review: CHI-17 — middleware/recoverer.go

**Reviewer:** sonnet
**Date:** 2026-03-31
**Branch:** CHI-17

---

## middleware/recoverer.go

### Line 24: BUG — `http.ErrAbortHandler` panic is consumed without re-panicking

**Severity:** High

**Code:**
```go
if rvr := recover(); rvr != nil && rvr != http.ErrAbortHandler {
    // ...
    w.WriteHeader(http.StatusInternalServerError)
}
```

**Expected:** When a downstream handler panics with `http.ErrAbortHandler`, the Recoverer should re-panic with the same value so that `net/http`'s own recovery logic can abort the connection cleanly. Per Go docs: "To abort a handler so the client sees an **interrupted response** but the server doesn't log an error, panic with the value ErrAbortHandler." The "interrupted response" requires the panic to propagate to the server, which closes the connection (or sends HTTP/2 RST_STREAM).

**Actual:** The `recover()` call at line 24 consumes the `http.ErrAbortHandler` panic. Because `rvr == http.ErrAbortHandler`, the `if` body does not execute, so no 500 is written and nothing is logged — correct so far. But the function returns normally, so `next.ServeHTTP(w, r)` also returns normally to `net/http`. `net/http` never sees the panic, so it never aborts the connection. If no response was written before the panic, `net/http` will flush an implicit 200 OK with an empty body. The client does **not** see an interrupted/aborted connection as intended.

**Why it matters:** Any handler or library that uses `http.ErrAbortHandler` to signal "close the connection without logging" will silently get a 200 OK response instead of a connection abort. This can break streaming handlers, SSE endpoints, and any code relying on forced connection teardown. The CHANGELOG entry for v4.0.3 says "suppress http.ErrAbortHandler in middleware.Recoverer", which was likely intended to mean "don't log it and don't send a 500", but the implementation goes further by also preventing the connection abort.

**Fix:** Add an explicit re-panic before the deferred function returns when `rvr == http.ErrAbortHandler`:
```go
if rvr == http.ErrAbortHandler {
    panic(rvr)
}
```

---

### Line 75: BUG — Panic line detection fails on Go 1.14+ due to changed stack trace format

**Severity:** Low

**Code:**
```go
if strings.HasPrefix(stack[i], "panic(0x") {
    lines = lines[0 : len(lines)-2] // remove boilerplate
    break
}
```

**Expected:** The loop should find the `panic(...)` call in the stack trace, trim the goroutine header boilerplate, and break.

**Actual:** In Go 1.14, the internal interface representation changed, and the panic call line in stack traces changed format from `panic(0xTYPEADDR, 0xDATAADDR)` to `panic({0xTYPEADDR, 0xDATAADDR})` (with curly braces). The `strings.HasPrefix(stack[i], "panic(0x")` check never matches the `panic({0x...})` format used by every Go version since 1.14. Since `go.mod` declares a minimum of `go 1.14`, this detection is broken for all supported Go versions.

**Consequence:** The `break` never fires, `lines = lines[0 : len(lines)-2]` never executes, and the loop runs until `i == 1`. The resulting `lines` slice contains nearly the full raw stack (minus `stack[0]`), with goroutine header boilerplate not trimmed. `PrintPrettyStack` falls back to raw `os.Stderr.Write(debugStack)` only if `s.parse` returns an error; here `parse` returns `nil` error with malformed content, so the pretty-printing path is used but produces degraded output.

---

### Lines 103, 108: BUG — Dead code: `strings.HasPrefix(line, "\t")` always false after `TrimSpace`

**Severity:** Low

**Code:**
```go
line = strings.TrimSpace(line)           // line 102
if strings.HasPrefix(line, "\t") || ... // line 103 — tab check is always false
...
} else {
    if strings.HasPrefix(line, "\t") {   // line 108 — also always false
        return strings.Replace(line, "\t", "      ", 1), nil
    }
```

**Expected:** The tab-prefix checks are intended to identify tab-indented source file lines (which in Go stack traces are formatted as `\t/path/to/file.go:N`).

**Actual:** `strings.TrimSpace` on line 102 removes all leading whitespace including `\t`. After this call, `strings.HasPrefix(line, "\t")` on lines 103 and 108 can never be true. The checks are permanently dead code.

**Impact on line 103:** Source lines are still correctly routed to `decorateSourceLine` via the `strings.Contains(line, ".go:")` half of the OR condition, so the net behavior is correct. The tab check is just dead.

**Impact on line 108:** The fallback branch for lines that are neither source lines nor function-call lines: the `strings.HasPrefix(line, "\t")` check is always false, so the branch `strings.Replace(line, "\t", "      ", 1)` is never reached. Any such line always goes to `fmt.Sprintf("    %s\n", line)`. Because TrimSpace already stripped tabs from the content, the Replace would have been a no-op anyway, so the behavioral impact is nil — but the dead code is misleading.

---

## Summary

| Severity | Count |
|----------|-------|
| High     | 1     |
| Low      | 2     |

**Files with no findings:** N/A (single file reviewed)

**Overall assessment:** FIX FIRST

The High finding (line 24) causes incorrect observable behavior for any handler that panics with `http.ErrAbortHandler`: the connection is not aborted and the client receives an unexpected 200 OK. This is a correctness bug in a widely-used middleware.
