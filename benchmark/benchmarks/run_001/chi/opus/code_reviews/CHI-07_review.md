# Code Review: middleware/recoverer.go

## middleware/recoverer.go

- **Line 24:** [BUG] (High) `http.ErrAbortHandler` panic is swallowed instead of re-panicked. When `recover()` catches a value equal to `http.ErrAbortHandler`, the condition `rvr != nil && rvr != http.ErrAbortHandler` is false, so the if-body is skipped and the deferred function returns normally. Since `recover()` has already consumed the panic, `http.ErrAbortHandler` never propagates to the net/http server. The stdlib server relies on seeing this panic to abort the connection immediately. Without re-panicking, the handler returns normally and the response completes as if nothing happened, defeating the purpose of `http.ErrAbortHandler`. The fix is to add `panic(http.ErrAbortHandler)` after the if-block (or in an else-if branch when `rvr == http.ErrAbortHandler`).

- **Line 102-103:** [BUG] (Low) Dead code: `strings.TrimSpace(line)` on line 102 strips all leading whitespace including tabs. The subsequent check `strings.HasPrefix(line, "\t")` on line 103 can never be true after trimming. The tab-prefix condition is dead — only the `strings.Contains(line, ".go:")` branch can trigger the source-line path. This means lines that have a leading tab but no `.go:` substring will be misclassified and routed to `decorateFuncCallLine` or the else branch instead of `decorateSourceLine`. In practice, Go stack traces have `.go:` in source lines so the impact is minimal, but the logic does not match its apparent intent.

- **Line 108:** [BUG] (Low) Dead code: same issue as line 103. The `strings.HasPrefix(line, "\t")` check on line 108 is inside the else branch and also follows the TrimSpace on line 102, so it can never be true. This entire branch is unreachable.

- **Line 129-130:** [BUG] (Low) Potential index-out-of-range panic in `decorateFuncCallLine`. If `pkg` contains no `os.PathSeparator` (line 127 returns -1), line 129 uses `strings.Index(pkg, ".")` to find a dot. If `pkg` also contains no dot, `idx` is -1, and line 130 does `pkg[-1:]` which panics with a slice bounds out of range error. While Go stack traces normally contain dots in function names, a malformed or unexpected stack trace format would cause the recoverer itself to panic — ironic for a panic-recovery middleware. The error would propagate up and potentially crash the request.

- **Line 135-136:** [BUG] (Low) Same potential panic as lines 129-130 but in the else branch. If `method` (substring after the last path separator) contains no dot, `strings.Index(method, ".")` returns -1, and line 136 does `method[0:-1]` which panics with a slice bounds out of range error.

- **Line 75:** [QUESTION] (Low) The panic-line detection heuristic `strings.HasPrefix(stack[i], "panic(0x")` is fragile. The `panic(0x...` format in Go stack traces is an implementation detail of the runtime and not guaranteed across Go versions. If the format changes, the loop will not find the panic boundary, `lines` will never be trimmed of boilerplate, and the break on line 77 will never execute — resulting in the full reversed stack (including runtime boilerplate) being displayed.

- **Line 33:** [QUESTION] (Low) `w.WriteHeader(http.StatusInternalServerError)` is called unconditionally after recovering from a panic. If the handler already called `w.WriteHeader()` or `w.Write()` before panicking, this second `WriteHeader` call is a no-op and the Go stdlib logs a "superfluous response.WriteHeader call" warning to stderr. This is arguably unavoidable, but worth noting that the 500 status code is not guaranteed to be sent to the client if headers were already flushed.

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 0     |
| Low      | 6     |

- **Total findings:** 7 (5 BUG, 2 QUESTION)
- **Files reviewed:** middleware/recoverer.go
- **Overall assessment:** NEEDS DISCUSSION — The high-severity `http.ErrAbortHandler` swallowing issue changes observable behavior for users relying on connection abort semantics. The low-severity dead-code and potential-panic issues in the pretty-printer are unlikely to cause production incidents but indicate the formatting code has a latent correctness gap.
