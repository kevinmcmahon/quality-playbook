# Code Review: CHI-11 — mux.go

## mux.go

---

### Finding 1

**Line 192:** [BUG] `NotFound()` on an inline mux assigns the inline mux's full middleware stack (including inline-specific middleware) to the **parent** mux's `notFoundHandler`.

**Expected:** When `NotFound()` is called on an inline mux, the handler stored on the parent should be wrapped only with the parent's own middleware, not with the inline group's extra middleware.

**Actual:** At line 192, `h` is built with `Chain(mx.middlewares...).HandlerFunc(handlerFn).ServeHTTP`. For an inline mux created via `Group(func(r) { r.Use(authMW); r.NotFound(fn) })`, `mx.middlewares` is `[parentMW, authMW]`. Because lines 193–195 set `m = mx.parent`, the parent mux gets `m.notFoundHandler = h` — a handler that includes `authMW`. Every 404 response served by the parent (including routes outside the auth group) will now execute `authMW`, which is wrong.

**Severity:** Medium

**Why it matters:** Middleware in an inline group is scope-limited by design. Propagating it to the parent's global `notFoundHandler` silently applies it to routes outside the group — an auth middleware would run on all 404 responses across the entire router, potentially rejecting unauthenticated 404s with 401.

---

### Finding 2

**Line 211:** [BUG] `MethodNotAllowed()` on an inline mux has the identical flaw: `h` at line 211 is built with `Chain(mx.middlewares...).HandlerFunc(handlerFn).ServeHTTP`, and then `m = mx.parent` at lines 213–215, causing the parent's `methodNotAllowedHandler` to include the inline group's extra middleware.

**Expected:** Same as Finding 1 — only the parent's own middleware should wrap the parent-level 405 handler.

**Actual:** Inline group's extra middleware (e.g., auth, rate-limiting) is injected into the parent's 405 handler.

**Severity:** Medium

**Why it matters:** Same as Finding 1 — 405 responses outside the inline group incorrectly execute inline-scoped middleware.

---

### Finding 3

**Line 200–202:** [QUESTION] Recursive propagation via `m.updateSubRoutes` passes `h` — which already has `mx.middlewares` wrapped around it — to each subrouter's `NotFound(h)` call. Inside that recursive call, line 192 wraps `h` again with `subMux.middlewares`, producing `subMux.middlewares → mx.middlewares → originalFn`. When a 404 occurs inside a subrouter's `routeHTTP`, `subMux.middlewares` has already executed (via the subrouter's `mx.handler = chain(subMux.middlewares, routeHTTP)`), so they execute a second time via the `notFoundHandler`.

**Severity:** Low

**Question:** Is this double-execution of subrouter middleware for 404 responses intentional? The wrapping is also applied at the parent level (line 192 before the inline mux check), so the parent also double-runs its own middleware for 404s. The only scenario that requires middleware in the `notFoundHandler` is the early-exit path at mux.go:63–65 (when `mx.handler == nil`). In the normal path through `routeHTTP`, middleware has already run.

---

### Finding 4

**Line 99–101:** [QUESTION] The `Use()` guard `if mx.handler != nil` applies to inline muxes as well. An inline mux's `handler` field is set to `http.HandlerFunc(mx.routeHTTP)` at line 399 each time `handle()` is called. Therefore, calling `Use()` on an inline mux after any route is registered panics with "all middlewares must be defined before routes on a mux."

**Severity:** Low

**Question:** Is this panic intentional for inline muxes? The behavior is consistent with the non-inline case and prevents late middleware registration, but the panic message says "on a mux" with no mention of inline muxes, which may confuse users who believe inline group middleware can be added later.

---

### Finding 5

**Line 460–468:** [QUESTION] `updateSubRoutes()` casts `r.SubRoutes` to `*Mux` with an `ok` check and silently skips any non-`*Mux` subrouter (e.g., a plain `http.Handler` mounted via `Mount()`).

**Severity:** Low

**Question:** Is it intentional that custom `NotFound`/`MethodNotAllowed` handlers are not propagated to non-chi subrouters? If a user mounts a third-party router (`Mount("/api", thirdPartyRouter)`), the custom 404 handler is not applied to it. This could produce inconsistent 404 behavior (chi's custom page for routes in chi, Go's default 404 for routes in the mounted handler). The skip is silent — no warning to the user.

---

## Summary

| Severity | Count |
|----------|-------|
| BUG      | 2     |
| QUESTION | 3     |

**BUG findings:**
- Finding 1 (Medium): `NotFound()` on inline mux incorrectly propagates inline middleware to parent's `notFoundHandler` (mux.go:192–198)
- Finding 2 (Medium): `MethodNotAllowed()` on inline mux has same flaw (mux.go:211–218)

**QUESTION findings:**
- Finding 3 (Low): Double middleware execution for 404/405 due to recursive `notFoundHandler` wrapping (mux.go:200–202)
- Finding 4 (Low): `Use()` panic applies to inline muxes, undocumented (mux.go:99–101)
- Finding 5 (Low): `updateSubRoutes()` silently skips non-`*Mux` handlers (mux.go:460–468)

**Overall assessment: FIX FIRST** — Findings 1 and 2 cause scope-leaked middleware on the parent's 404/405 handlers when `NotFound()`/`MethodNotAllowed()` is called on an inline group. This is a silent correctness bug: no error, no panic, but middleware from a scoped group silently executes on all error responses across the entire router.
