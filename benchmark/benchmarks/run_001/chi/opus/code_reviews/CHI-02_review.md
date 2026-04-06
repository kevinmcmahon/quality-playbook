# CHI-02 Code Review: mux.go

**Reviewer:** Claude Opus
**Date:** 2026-03-31
**File:** `mux.go` (worktree at `/tmp/qpb_worktree_chi_opus_2722`)

---

### mux.go

- **Line 90-91:** [QUESTION] **Severity: Medium.** `pool.Put(rctx)` is not deferred after `pool.Get()` at line 81. If `mx.handler.ServeHTTP(w, r)` panics and no Recoverer middleware is in the chain, the panic propagates past line 91 and the `Context` object is never returned to the pool, causing a resource leak. The common mitigation is using `middleware.Recoverer`, which catches panics via `defer/recover` so that `ServeHTTP` returns normally and line 91 executes. However, Recoverer is optional middleware — nothing in chi enforces its use. A `defer mx.pool.Put(rctx)` after line 81 would guarantee cleanup regardless. This appears to be a deliberate performance tradeoff (avoiding defer overhead), but it creates a silent leak for any user who doesn't use Recoverer.

- **Line 461-464:** [QUESTION] **Severity: Low.** When `rctx.RouteMethod` is not found in `methodMap` (i.e., an HTTP method chi doesn't know about, such as a custom method not registered via `RegisterMethod`), the code responds with `mx.MethodNotAllowedHandler()` (HTTP 405). Semantically, HTTP 405 means "the method is recognized by the server but not allowed for the target resource." An unrecognized method is more accurately a 501 Not Implemented. This is a common pattern across routers but is technically incorrect per RFC 7231 Section 6.6.2. The `MethodNotAllowedHandler()` is also called here without any `methodsAllowed` arguments, so the `Allow` header will be empty — further confusing clients.

- **Line 517:** [BUG] **Severity: Low.** `methodNotAllowedHandler` uses `reverseMethodMap[m]` to populate the `Allow` header. However, `RegisterMethod()` in `tree.go:60-75` adds custom methods to `methodMap` and `mALL` but never updates `reverseMethodMap`. When a 405 response involves a route that allows a custom-registered method, that method will be missing from the `Allow` header (the map lookup returns `""`), and an empty string will be added to the header. Root cause is in `tree.go:RegisterMethod`, but the symptom manifests here. Verified by grepping: `reverseMethodMap` is never written to outside its `var` initializer at `tree.go:46-56`.

- **Line 302:** [QUESTION] **Severity: Low.** The duplicate mount check uses `mx.tree.findPattern(pattern+"*") || mx.tree.findPattern(pattern+"/*")`. When `pattern` ends with `/` (e.g., `/api/`), the second check becomes `findPattern("/api//*")` with a double slash, which would never match a real pattern. This doesn't cause a bug in practice because when `pattern` ends with `/`, the first check `findPattern("/api/*")` correctly catches duplicates (since that exact pattern is registered at line 341). The double-slash check is simply dead code for that path. No action needed, but worth noting the asymmetry.

---

### Summary

| Severity | BUG | QUESTION | SUGGESTION |
|----------|-----|----------|------------|
| Critical | 0   | 0        | 0          |
| High     | 0   | 0        | 0          |
| Medium   | 0   | 1        | 0          |
| Low      | 1   | 2        | 0          |

**Total findings:** 4 (1 BUG, 3 QUESTION)

**Overall assessment:** SHIP IT

The mux.go code is well-structured and correct for the vast majority of use cases. The pool.Put deferral question (Medium) is the most impactful finding but is mitigated by the common use of Recoverer middleware. The RegisterMethod/reverseMethodMap bug is real but affects only the uncommon case of custom HTTP methods combined with 405 responses. No critical or high-severity issues found.
