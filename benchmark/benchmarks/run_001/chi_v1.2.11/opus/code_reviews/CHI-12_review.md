# CHI-12: mux_test.go Code Review

## mux_test.go

### Finding 1
- **Finding type:** BUG
- **File and line number:** mux_test.go:1686-1689
- **Severity:** High
- **Description:** In `TestServerBaseContext`, the test server is started with `httptest.NewServer(r)` at line 1686, which immediately begins accepting connections. The `BaseContext` function is then assigned *after* the server is already live (line 1687-1689). This is a temporal ordering bug: the server is "live" at creation but configured afterward. Any request arriving between `NewServer()` and the `BaseContext` assignment will not have the base context set, causing the handler to panic on the type assertion at line 1674 (`r.Context().Value(ctxKey{"base"}).(string)`). The fix is to use `httptest.NewUnstartedServer(r)`, set `ts.Config.BaseContext`, then call `ts.Start()`. While the test's own request at line 1693 happens after the assignment, the server listener is already open and subject to a data race on `ts.Config.BaseContext` since `http.Server` reads `BaseContext` on each accepted connection without synchronization against external mutation.

### Finding 2
- **Finding type:** BUG
- **File and line number:** mux_test.go:1576
- **Severity:** Medium
- **Description:** In `TestMuxContextIsThreadSafe`, `t.Fatal(err)` is called from within a goroutine spawned at line 1571. The `testing` package documentation explicitly states that `Fatal`, `Fatalf`, `FailNow`, `SkipNow`, `Skip`, and `Skipf` must only be called from the goroutine running the Test or Benchmark function. Calling `t.Fatal` from a child goroutine calls `runtime.Goexit()` which terminates that goroutine rather than the test goroutine, leading to undefined behavior. In practice this can cause a panic (`testing: t.Fatal called from a goroutine that did not create the test`) or silently swallow the error. The call should use `t.Error(err); return` instead.

### Finding 3
- **Finding type:** BUG
- **File and line number:** mux_test.go:744-746
- **Severity:** Medium
- **Description:** In `TestMuxRouteGroups`, the assertion for the first middleware group's counters at line 744-746 uses `t.Logf` (log-only, does not fail the test), while the equivalent assertion for the second group at line 753-755 correctly uses `t.Fatalf`. This means a regression in the first middleware group's initialization or handler counting would be silently ignored — the test would pass when it should fail. The `t.Logf` on line 745 should be `t.Fatalf` (or at minimum `t.Errorf`) to match the second assertion and actually catch failures.

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 2     |
| Low      | 0     |

- **Files with no findings:** N/A (single file review)
- **Overall assessment:** FIX FIRST — The `TestServerBaseContext` temporal ordering bug (Finding 1) is a real data race where the server is live before its configuration is complete. The goroutine `t.Fatal` misuse (Finding 2) violates `testing` package contracts. The silent assertion (Finding 3) defeats the purpose of the test.
