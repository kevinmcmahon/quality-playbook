# Quality Constitution: chi

## Purpose

Quality in chi is **built in** (Deming): the safety bar is codified in this document and the
functional tests so that every contributor — human or AI — starts from the same explicit
standard rather than re-deriving it from scratch. Without this constitution, each session
makes independent tradeoffs that quietly erode correctness guarantees.

Quality in chi means **fitness for use** (Juran): chi is infrastructure. Applications depend
on it to route every HTTP request correctly, propagate context faithfully across middleware
chains, and never silently lose a URL parameter or route match. "Tests pass" is not the bar.
The bar is: a request that matches a registered pattern always reaches the right handler with
the right URL parameters and the correct middleware stack applied, under all valid input
combinations — including encoded paths, wildcard sub-routes, inline groups, and concurrent
load.

Quality in chi is **free** (Crosby): investing in this playbook upfront costs far less than
debugging production routing bugs where a `/user/{id}` param silently returned "" or a
sub-router received the wrong path segment. The fitness scenarios below are specific enough
that any AI session can verify them — they cannot be argued down.

## Coverage Targets

| Subsystem | Target | Why |
|-----------|--------|-----|
| `mux.go` — route registration and ServeHTTP | 95% | State machine (handler nil vs non-nil) is easy to break; Use-after-routes panic must be preserved; sync.Pool reset must run. A missed branch here silently routes to the wrong handler in production. |
| `tree.go` — radix trie insert and find | 90% | The trie has 4 node types (static, regexp, param, catchAll) and must correctly resolve priorities. A missed branch silently routes to wrong handler or fails to extract URL params. |
| `context.go` — RouteContext, URLParam, RoutePattern | 90% | URLParam returns "" on miss; RoutePattern's wildcard replacement is iterative; nil guard on RoutePattern() must hold. These are called by every handler. |
| `chain.go` — middleware chaining | 85% | Simple code, but incorrect order of chain construction would reverse middleware execution order for all users. |
| `middleware/` — individual middlewares | 80% | Each middleware has its own edge cases (Recoverer re-panics ErrAbortHandler; Timeout only 504s on DeadlineExceeded; RealIP validates IP). Lower target because middlewares are independent and opt-in. |

The rationale column is not documentation — it is protection against erosion. An AI session
that reads "95%" without a "why" will optimize for speed and lower the bar.

## Coverage Theater Prevention

For chi, fake tests include:

- Asserting that `chi.NewRouter()` returns a non-nil value — this exercises no routing logic.
- Registering a route and only checking that no panic occurred — the important behavior is that the handler is actually invoked with the correct URL params, not just that registration succeeded.
- Testing that `URLParam(r, "key")` returns "" when called outside a chi handler — this only verifies the nil-guard path, not actual param extraction.
- Mocking `http.ResponseWriter` and never asserting the response status code or body — this tests that a function was called, not what it did.
- Checking that a middleware returns an `http.Handler` — what matters is that the returned handler produces the correct response with the correct behavior.
- Using `httptest.NewRecorder()` and never reading `rr.Code` or `rr.Body.String()` — this is a setup-only test.

The key quality question for every chi test: "If I deleted the routing logic inside `routeHTTP`, would this test catch it?"

## Fitness-to-Purpose Scenarios

### Scenario 1: Middleware Registered After Routes Causes Silent Panic

**Requirement tag:** [Req: inferred — from mux.go Use() guard at line 101]

**What happened:** `mux.go:101` panics if `Use()` is called after any route has been registered. This guard exists because the computed handler is built once on first route registration — adding middleware afterward would have no effect on already-built handler chains. Without the panic, a developer who writes `r.Get("/", h)` then `r.Use(authMiddleware)` would see no error but the auth middleware would silently not apply. In a production service, this produces an endpoint that appears protected but is not.

**The requirement:** Calling `mx.Use()` after any route is registered on the same Mux must panic with a message containing "all middlewares must be defined before routes". Calling `Use()` before any routes must succeed.

**How to verify:** `TestScenario1_MiddlewareAfterRoutesPanics` — register a route on a Mux, then call `Use()` and verify it panics. Also verify that `Use()` before routes does not panic.

---

### Scenario 2: sync.Pool RouteContext Reuse Corruption

**Requirement tag:** [Req: inferred — from mux.go ServeHTTP pool.Get/Reset/Put pattern at lines 81–91]

**What happened:** `mux.go` reuses `RouteContext` objects via `sync.Pool` to reduce allocations. Before each request, `rctx.Reset()` is called to zero all fields. If `Reset()` were absent or incomplete — for example, if `URLParams.Keys` were not sliced to zero — a second request served by the same goroutine could see URL parameters from a previous request. In a multi-tenant API, this would be a data leak: `/users/alice` could receive the `{id}` param `bob` from a prior request. The bug would only surface under load (when pool reuse occurs) and would be invisible in sequential tests.

**The requirement:** `RouteContext.Reset()` must zero all mutable fields: `RoutePath`, `RouteMethod`, `RoutePatterns`, `URLParams.Keys`, `URLParams.Values`, `routePattern`, `routeParams.Keys`, `routeParams.Values`, `methodNotAllowed`, `methodsAllowed`, `parentCtx`, and `Routes`.

**How to verify:** `TestScenario2_RouteContextReset` — create a `RouteContext`, populate all fields, call `Reset()`, then assert every field is zero/empty/nil.

---

### Scenario 3: Routing Pattern Must Begin With Slash

**Requirement tag:** [Req: inferred — from mux.go handle() guard at line 417]

**What happened:** `mux.go:417` panics if a pattern does not start with '/'. This guard exists because the radix trie assumes all patterns are rooted paths — a pattern like `users/{id}` would be inserted incorrectly and produce unpredictable routing behavior. The panic is the right response, but it only fires at registration time, not at startup. A pattern registered in a rarely-executed code path (e.g., a feature flag branch) would survive until that branch runs in production.

**The requirement:** Any attempt to register a route with a pattern not starting with '/' must panic immediately with a message containing the invalid pattern.

**How to verify:** `TestScenario3_InvalidPatternPanic` — call `r.Get("no-slash", h)` and verify it panics.

---

### Scenario 4: Sub-Router Mount Path Stripping

**Requirement tag:** [Req: inferred — from mux.go Mount() nextRoutePath at lines 309–313]

**What happened:** When a sub-router is mounted at `/api`, requests to `/api/users/42` must reach the sub-router with path `/users/42` — the mount prefix must be stripped. `mux.go:313` does this via `nextRoutePath()`, which reads the last wildcard param. If this stripping were absent or off-by-one, the sub-router's `/users/{id}` route would never match `/api/users/42` because it would see `/api/users/42` instead of `/users/42`. Every sub-router registration in a real application would silently return 404 for all mounted routes.

**The requirement:** After mounting a sub-router at a prefix, requests to `prefix/path` must reach the sub-router with the path `/path`. URL parameters extracted before the mount boundary must not be visible in the sub-router's param namespace.

**How to verify:** `TestScenario4_MountPathStripping` — mount a sub-router at `/api`, register `/users/{id}` in the sub-router, send `GET /api/users/42`, assert the handler receives `URLParam(r, "id") == "42"`.

---

### Scenario 5: RealIP Middleware IP Validation Bypass

**Requirement tag:** [Req: inferred — from middleware/realip.go net.ParseIP guard at line 52]

**What happened:** `realip.go:52` validates the extracted IP string with `net.ParseIP()` before setting `RemoteAddr`. Without this guard, an attacker who controls the `X-Forwarded-For` header could inject arbitrary strings — e.g., `"attacker@example.com"` — and the application would receive this as the client IP. Any downstream IP-based access control, rate limiting, or audit logging would be bypassed. The guard exists because chi's `RealIP` middleware is designed for use behind a trusted proxy — but even then, malformed header values must be rejected.

**The requirement:** The `RealIP` middleware must only set `RemoteAddr` from `True-Client-IP`, `X-Real-IP`, or the first entry of `X-Forwarded-For` if and only if the value parses as a valid IP address. Invalid strings must be silently discarded (leaving `RemoteAddr` unchanged).

**How to verify:** `TestScenario5_RealIPValidation` — send requests with invalid `X-Forwarded-For` values (strings, email addresses, CIDR notation) and assert `RemoteAddr` is not modified.

---

### Scenario 6: Recoverer Must Re-Panic on ErrAbortHandler

**Requirement tag:** [Req: inferred — from middleware/recoverer.go ErrAbortHandler special case at line 27]

**What happened:** `recoverer.go:27` explicitly re-panics on `http.ErrAbortHandler` instead of recovering and writing a 500. `http.ErrAbortHandler` is Go's mechanism for aborting a response mid-stream — it is used by the standard library to signal that the connection should be closed without writing more bytes. If Recoverer swallowed it, the framework would attempt to write a 500 response on a connection that the application intentionally aborted, potentially corrupting the TCP stream or writing garbage bytes to a client that has already received a partial response.

**The requirement:** `Recoverer` must not catch `http.ErrAbortHandler`. All other panics must be caught, logged, and result in HTTP 500 (unless the connection is being upgraded, in which case no status is written).

**How to verify:** `TestScenario6_RecovererRepanicOnErrAbortHandler` — use `httptest` to send a request to a handler that panics with `http.ErrAbortHandler`, wrap with Recoverer, and assert the panic propagates.

---

### Scenario 7: Timeout Middleware Writes 504 Only on DeadlineExceeded

**Requirement tag:** [Req: inferred — from middleware/timeout.go ctx.Err() guard at line 38]

**What happened:** `timeout.go:38` only writes `504 Gateway Timeout` if `ctx.Err() == context.DeadlineExceeded`. A cancelled context (client disconnected mid-request) must not produce a 504 — that would be a false timeout response for a deliberate client disconnect. Without this guard, a request cancelled by the client (e.g., browser navigating away) would log a 504 and potentially trigger alerting systems, masking real latency problems with noise.

**The requirement:** The `Timeout` middleware must write `504 Gateway Timeout` if and only if the context deadline was exceeded. Client-initiated cancellations (`ctx.Err() == context.Canceled`) must not produce a 504 response.

**How to verify:** `TestScenario7_TimeoutOnly504OnDeadline` — simulate a context cancellation (not expiry) and assert no 504 is written.

---

### Scenario 8: Throttle Rejects Invalid Configuration at Startup

**Requirement tag:** [Req: inferred — from middleware/throttle.go panic guards at lines 45, 49]

**What happened:** `throttle.go:45-49` panics on `limit < 1` and `backlogLimit < 0`. These panics fire at server startup (when the middleware is configured), not at request time. Without them, a `Throttle(0)` configuration would create a throttler with a zero-capacity token channel, causing all requests to immediately return 429 or deadlock. The configuration error would be silent until the server was under load and all requests started failing. Panic-at-startup is the correct pattern for infrastructure configuration — it forces the error to be visible at deploy time.

**The requirement:** `ThrottleWithOpts` must panic on `Limit < 1` or `BacklogLimit < 0`. The panic message must identify which constraint was violated.

**How to verify:** `TestScenario8_ThrottleInvalidConfig` — call `Throttle(0)` and `ThrottleBacklog(1, -1, time.Second)` and assert each panics.

---

### Scenario 9: URLParam Returns Last Value for Duplicate Keys

**Requirement tag:** [Req: inferred — from context.go URLParam backward search at line 101]

**What happened:** `context.go:101` iterates `URLParams.Keys` from the end, returning the first (last-inserted) match. This means if two different route segments happen to produce the same parameter name — possible in complex nested router configurations — the most recently set value wins. This is the correct behavior for chi's layered routing model, where inner routers can override outer params. An AI session that assumes first-match semantics and modifies the URLParam lookup would break inner-router param override, causing `{id}` params set by sub-routers to be shadowed by outer router params.

**The requirement:** `URLParam(r, key)` must return the last value associated with `key` in the params stack (most recently inserted), not the first.

**How to verify:** `TestScenario9_URLParamLastValueWins` — manually build a `RouteContext` with duplicate keys (same key added twice with different values), verify `URLParam` returns the second value.

---

### Scenario 10: Mount Panics on Duplicate Pattern

**Requirement tag:** [Req: inferred — from mux.go Mount() findPattern guard at lines 296–297]

**What happened:** `mux.go:296-297` panics if `Mount()` is called for a pattern that already exists (with or without trailing wildcard). Without this guard, two sub-routers mounted at the same prefix would silently overwrite each other — the second mount would replace the first in the trie, and all routes registered in the first sub-router would become unreachable with no error message. This is a common mistake when composing large APIs from reusable route groups.

**The requirement:** Mounting a handler at a pattern that already has a mounted handler must panic with a message identifying the conflicting pattern.

**How to verify:** `TestScenario10_MountDuplicatePanic` — mount two handlers at the same pattern and assert the second `Mount()` panics.

---

## AI Session Quality Discipline

1. Read `quality/QUALITY.md` before starting any work.
2. Run `go test ./...` from the repo root before marking any task complete.
3. Add tests for new functionality — not just happy path. Include edge cases for all 4 node types (static, param, regexp, catchAll).
4. Update this file if new failure modes are discovered during review or testing.
5. Output a Quality Compliance Checklist before ending a session.
6. Never remove a fitness-to-purpose scenario. Only add new ones.
7. Never call `Use()` after routes in test setup — it will panic.
8. Use `httptest.NewRecorder()` + `httptest.NewRequest()` for all handler tests. Always assert `rr.Code` and `rr.Body.String()`.

## The Human Gate

The following require human judgment and cannot be automated:

- Performance benchmark results — latency and allocations are meaningful only against baseline hardware and Go version
- Route documentation accuracy — whether generated docgen output correctly describes the intended API design
- Security review of `RealIP` deployment — only a human can verify that the upstream proxy is actually trusted
- Wildcard pattern semantics review — whether `*` catch-all matches are intentionally broad or accidentally over-broad requires domain knowledge about the API being built
- Compatibility decisions when upgrading Go — chi supports the four most recent Go versions; a human must verify no stdlib changes affect routing behavior
