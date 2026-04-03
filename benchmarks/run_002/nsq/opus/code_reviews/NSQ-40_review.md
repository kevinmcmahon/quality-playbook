# Code Review: apps/nsq_stat/nsq_stat.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**Source:** `/tmp/qpb_wt_opus_NSQ-40/apps/nsq_stat/nsq_stat.go`

---

### apps/nsq_stat/nsq_stat.go

- **Line 105-106:** BUG (Severity: High) — **Division by zero panic for sub-second `--status-every` values.** The rate calculation divides by `int64(interval.Seconds())`. `Duration.Seconds()` returns a `float64`, and `int64()` truncates toward zero. For any interval under 1 second (e.g., `500ms`), `int64(0.5)` evaluates to `0`, causing a divide-by-zero panic. The validation on line 144 (`int64(*statusEvery) <= 0`) only rejects non-positive durations (in nanoseconds), so sub-second positive durations pass validation but crash at runtime. Fix: use floating-point division or express the rate in terms of nanoseconds/duration rather than truncating to integer seconds.

- **Lines 63, 69, 74, 76:** BUG (Severity: Medium) — **Global `log.SetOutput` is not goroutine-safe.** `statLoop` runs in a separate goroutine (launched on line 170) and toggles the global default logger output between `ioutil.Discard` and `os.Stdout` to suppress internal logging from lookupd functions. The `log` package's default logger is a shared `*log.Logger`, and `SetOutput` is not safe for concurrent use. If a signal arrives and the runtime invokes any logging (or if future code adds logging elsewhere), a data race occurs. Additionally, if the process receives a fatal signal while output is set to `Discard`, the `log.Fatalf` on lines 71, 78, or 83 would print to `/dev/null`, silently swallowing the error message.

- **Line 59:** QUESTION (Severity: Low) — **Loop runs `countNum.value + 1` iterations but the first iteration is a warm-up.** The loop condition `countNum.value >= i` with `i` starting at 0 means the loop body executes `countNum.value + 1` times. The first iteration (i=0) sets the baseline `o` and continues without printing. This means `--count N` produces exactly N printed reports, which appears intentional. However, this is non-obvious and worth confirming — does the warm-up iteration count toward the user's requested count or not?

---

### Summary

| Severity | Count |
|----------|-------|
| High     | 1     |
| Medium   | 1     |
| Low      | 1     |

- **BUG findings:** 2
- **QUESTION findings:** 1
- **Files with no findings:** N/A (single file review)

**Overall assessment:** FIX FIRST — The division-by-zero on sub-second intervals is a runtime panic that is easy to trigger via valid CLI input. The global logger mutation is a latent race condition and can swallow fatal error messages.
