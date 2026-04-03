# Code Review: CHI-12

**File reviewed:** `mux_test.go`
**Reviewer:** claude-sonnet-4-6
**Date:** 2026-03-31

---

## mux_test.go

---

### Finding 1

- **Finding type:** BUG
- **File and line:** `mux_test.go:1578`
- **Severity:** Medium

**Description:** `t.Fatal(err)` is called inside a spawned goroutine in `TestMuxContextIsThreadSafe`. Per Go documentation, `t.Fatal` (and all `FailNow`-family methods) **must only be called from the goroutine running the Test function**. When called from a background goroutine, `t.Fatal` invokes `runtime.Goexit()`, which terminates only the calling goroutine — not the test goroutine. The test continues executing and can report success even if the error condition was triggered.

**Expected:** Use `t.Error(err); return` inside goroutines, or communicate the error back to the test goroutine via a channel or shared variable.

**Actual:** `t.Fatal(err)` exits only the background goroutine. An error from `http.NewRequest` would be silently swallowed; the test would not fail.

**Why it matters:** Any failure in request construction inside the loop would go unreported, defeating the purpose of the error check.

```go
// mux_test.go lines 1570-1587
go func() {
    defer wg.Done()
    for j := 0; j < 10000; j++ {
        w := httptest.NewRecorder()
        r, err := http.NewRequest("GET", "/ok", nil)
        if err != nil {
            t.Fatal(err)  // BUG: terminates goroutine only, not the test
        }
        ...
    }
}()
```

---

### Finding 2

- **Finding type:** BUG
- **File and line:** `mux_test.go:1714`
- **Severity:** Low

**Description:** In the `testRequest` helper function, `defer resp.Body.Close()` is placed **after** `ioutil.ReadAll(resp.Body)` and the error check that calls `t.Fatal`. When `t.Fatal` is invoked (via `runtime.Goexit()`), Go executes deferred functions registered up to that point — but the `defer resp.Body.Close()` at line 1714 has not yet been registered when `t.Fatal` fires at line 1713. The response body is not closed on read failure.

**Expected:** `defer resp.Body.Close()` should appear immediately after the `http.DefaultClient.Do(req)` success check (after line 1708), before `ioutil.ReadAll`.

**Actual:** On a read error, `runtime.Goexit()` runs at line 1713 before the defer at line 1714 is registered, leaving the response body open.

**Why it matters:** Resource leak in every test that uses `testRequest` when the body read fails. Since `testRequest` is a shared helper called throughout the test suite, the leak affects many tests.

```go
// mux_test.go lines 1711-1714
respBody, err := ioutil.ReadAll(resp.Body)   // line 1711
if err != nil {
    t.Fatal(err)                             // line 1713 - defer not registered yet
    return nil, ""
}
defer resp.Body.Close()                      // line 1714 - too late
```

---

### Finding 3

- **Finding type:** BUG
- **File and line:** `mux_test.go:194`
- **Severity:** Low

**Description:** Same defer-after-read pattern as Finding 2, but inline within `TestMuxBasic`. `defer resp.Body.Close()` at line 194 is placed after `ioutil.ReadAll(resp.Body)` at line 190 and its error check at line 192. If the read fails and `t.Fatal` calls `runtime.Goexit()`, the response body from the `http.Post` call at line 185 is never closed.

**Expected:** `defer resp.Body.Close()` should appear immediately after the `http.Post` success check.

**Actual:** The defer is only registered after a successful read; on read failure the body leaks.

```go
// mux_test.go lines 190-194
body, err := ioutil.ReadAll(resp.Body)  // line 190
if err != nil {
    t.Fatal(err)                        // line 192 - defer not registered yet
}
defer resp.Body.Close()                 // line 194 - too late
```

---

### Finding 4

- **Finding type:** BUG
- **File and line:** `mux_test.go:1747`
- **Severity:** Low

**Description:** The `testFile.Read` method always returns `len(p)` regardless of how many bytes were actually copied. The `copy(p, tf.contents)` call copies `min(len(p), len(tf.contents))` bytes, but the function unconditionally returns `len(p)`. When the caller supplies a buffer larger than `tf.contents`, the method reports more bytes written than were actually filled, violating the `io.Reader` contract (which requires `0 <= n <= len(p)` where `n` equals actual bytes read).

**Expected:** Return `min(len(p), len(tf.contents))` — the actual number of bytes written.

**Actual:** Returns `len(p)`, which can be larger than `len(tf.contents)`. The unfilled portion of `p` contains stale data that the caller will treat as valid file content.

**Note:** `testFile` is declared but never instantiated in any test in this file (no `testFileSystem` or `testFile` struct literals are found outside the type definitions). The bug is dormant/dead code currently, but would produce incorrect behavior if the type were used.

```go
// mux_test.go lines 1745-1748
func (tf *testFile) Read(p []byte) (n int, err error) {
    copy(p, tf.contents)
    return len(p), nil  // BUG: should be min(len(p), len(tf.contents))
}
```

---

## Summary

| # | Finding Type | File | Line | Severity |
|---|-------------|------|------|----------|
| 1 | BUG | mux_test.go | 1578 | Medium |
| 2 | BUG | mux_test.go | 1714 | Low |
| 3 | BUG | mux_test.go | 194  | Low |
| 4 | BUG | mux_test.go | 1747 | Low |

- **Total BUGs:** 4 (1 Medium, 3 Low)
- **Total QUESTIONs:** 0
- **Total SUGGESTIONs:** 0

**Overall assessment: FIX FIRST**

Finding 1 is a correctness issue — the test infrastructure misreports failures under goroutine errors. Findings 2 and 3 are resource management bugs in shared test helpers. Finding 4 is a dormant `io.Reader` contract violation that would affect any future test using `testFile`.
