# Code Review: CHI-12 — mux_test.go

**Reviewer:** Claude Opus 4.6
**Date:** 2026-03-31
**File:** mux_test.go (worktree: /tmp/qpb_wt_chi_opus_CHI-12)

---

## mux_test.go

### BUG — `t.Fatalf(body)` treats response body as format string

- **Lines:** 125, 134, 139, 144, 149, 154, 159, 164, 181, 237, 240, 243, 261, 264, 277, 281, 308, 311, 314, 375, 378, 381, 384, 387, 392, 437, 440, 443, 446, 449, 452, 455, 458, 499, 502, 505, 508, 512, 515, 518, 521, 524, 527, 531, 588, 591 (and many more — ~64 occurrences total)
- **Severity:** Medium
- **Description:** Throughout the file, `t.Fatalf(body)` is used where `body` is an HTTP response body string passed as the format string argument. If the response body contains `%` characters (e.g. `%s`, `%d`, `%!`), `Fatalf` will attempt to interpret them as format verbs, causing either garbled output, panics from `MISSING` args, or silently wrong error messages. The upstream/main branch uses `t.Fatal(body)` (not `Fatalf`), confirming this is a regression introduced in this worktree. Should be `t.Fatal(body)` or `t.Fatalf("%s", body)`.

### BUG — `io/ioutil` usage (deprecated, regression from upstream)

- **Lines:** 8, 190, 1252, 1711
- **Severity:** Medium
- **Description:** The file imports and uses `io/ioutil` (line 8) with calls to `ioutil.ReadAll` at lines 190, 1252, and 1711. The `io/ioutil` package has been deprecated since Go 1.16. More critically, the upstream/main branch (commit `a36a925 "Remove last uses of io/ioutil"`) already migrated this file to `io.ReadAll`. This is a regression that reintroduces the deprecated dependency.

### BUG — `testFile.Read` returns wrong byte count

- **Line:** 1745–1748
- **Severity:** Medium
- **Description:** `testFile.Read(p []byte)` returns `len(p)` (the buffer size) instead of the number of bytes actually copied. When `len(p) > len(tf.contents)`, this reports more bytes read than exist. When `len(p) < len(tf.contents)`, it silently truncates content but reports `len(p)` bytes (which is correct in that case but the method never signals completion via `io.EOF`). Correct implementation should return `min(len(p), len(tf.contents))` and signal `io.EOF` when appropriate. Note: `testFile`, `testFileSystem`, and `testFileInfo` types are defined but never instantiated or used in any test in this file, so this bug is currently unreachable — but it would bite if these test helpers are ever used.

### BUG — `defer resp.Body.Close()` placed after body is already read

- **Lines:** 194, 1716
- **Severity:** Low
- **Description:** At line 194 (in `TestMuxBasic`) and line 1716 (in `testRequest`), `defer resp.Body.Close()` appears after `ioutil.ReadAll(resp.Body)` has already consumed the body. While the close still executes (via defer), if `ReadAll` returns an error and `t.Fatal` is called, the deferred close races with test termination. The idiomatic pattern is `defer resp.Body.Close()` immediately after the nil-error check on the HTTP call, before reading the body. Note: this same issue exists in the upstream main branch — it is pre-existing, not a regression.

### BUG — `t.Fatal` called from goroutine in `TestMuxContextIsThreadSafe`

- **Line:** 1577
- **Severity:** Low
- **Description:** `t.Fatal(err)` is called inside a goroutine spawned at line 1571. The `testing` package documents that `t.Fatal` must only be called from the goroutine running the test function. Calling it from another goroutine can cause a panic or race condition in the test framework. Should use `t.Error(err); return` or a channel-based error reporting pattern. Note: this also exists in the upstream main branch — pre-existing.

### QUESTION — Dead code: `testFileSystem`, `testFile`, `testFileInfo` types

- **Lines:** 1728–1773
- **Severity:** Low
- **Description:** The types `testFileSystem` (line 1728), `testFile` (line 1736), and `testFileInfo` (line 1763) are defined with full method implementations but are never instantiated or referenced by any test in this file. They also require the `"os"` import (line 12) which is unused in the main branch. These appear to be dead code — possibly left over from a removed test. The upstream main branch does not contain these types at all, confirming this is new dead code introduced in this worktree.

### BUG — Unused `"os"` import (compilation regression)

- **Line:** 12
- **Severity:** Critical
- **Description:** The `"os"` package is imported at line 12. It is only used by the dead `testFile`/`testFileInfo` types (lines 1754, 1759, 1770). If those dead types were removed (as in the upstream main branch), this import would cause a compilation error. Even with the dead types present, the upstream main branch does not have this import because it does not have these types. Combined with the `"io/ioutil"` import, this file has two import regressions vs. upstream. If the Go compiler's unused-import check considers the types "used" enough, the file compiles — but this is still a regression that adds unnecessary dependencies.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1     |
| Medium   | 3     |
| Low      | 3     |

**Regressions vs. upstream (main branch):**
- `t.Fatalf(body)` instead of `t.Fatal(body)` — format string injection risk (~64 call sites)
- `io/ioutil` reintroduced after being removed in commit `a36a925`
- Dead `testFileSystem`/`testFile`/`testFileInfo` types and `"os"` import added

**Pre-existing issues (also in main branch):**
- `defer resp.Body.Close()` after `ReadAll` (lines 194, 1716)
- `t.Fatal` in goroutine (line 1577)

**Overall Assessment: FIX FIRST**

The `t.Fatalf(body)` regression is widespread (~64 occurrences) and will cause confusing test failures or panics whenever a response body contains `%` characters. The `io/ioutil` regression undoes a recent cleanup commit. The dead code adds unnecessary complexity. These should all be fixed before merging.
