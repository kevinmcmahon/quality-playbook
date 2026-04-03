# Quality Constitution: chi

## Purpose

Chi is a lightweight, idiomatic HTTP router for Go that builds composable REST API services using only the standard library. Quality for chi means **routing correctness under all path patterns, parameter types, and middleware compositions** — not just "requests get responses." A subtle bug in radix trie traversal or URL parameter extraction silently routes requests to wrong handlers with wrong parameters, producing correct-looking 200 responses with completely wrong data.

This constitution follows three principles:

- **Deming** ("quality is built in, not inspected in") — Quality is embedded in this playbook and AGENTS.md so every AI session inherits the same bar. The routing tree's correctness must be verified by functional tests that exercise real pattern matching, not by inspecting code.
- **Juran** ("fitness for use") — Chi is fit for purpose when it correctly matches any valid URL pattern (static, param, regexp, catch-all) to the right handler, extracts the right URL parameters, executes middleware in the right order, and returns appropriate 404/405 responses for unmatched routes — all while safely reusing routing contexts from a sync.Pool under concurrent load.
- **Crosby** ("quality is free") — The cost of a routing bug in production (wrong handler serving wrong data to users) vastly exceeds the cost of maintaining comprehensive routing tests.

## Coverage Targets

| Subsystem | Target | Why |
|-----------|--------|-----|
| `tree.go` (radix trie) | 90–95% | Most complex module (~878 lines). Handles route insertion, splitting, and multi-dimensional traversal across 4 node types. A bug here silently misroutes requests. The recursive `findRoute()` has 6+ branch paths per node type. |
| `mux.go` (HTTP multiplexer) | 85–90% | Orchestrates context pooling, middleware chaining, route dispatch, and sub-router mounting. A bug in `Mount()` silently drops NotFound/MethodNotAllowed handlers from sub-routers (defensive check at mux.go:301-307). |
| `context.go` (routing context) | 85–90% | URL parameter extraction uses reverse iteration (context.go:101) to handle parameter shadowing in nested routers. A bug here returns wrong parameter values silently. RoutePattern() must correctly collapse wildcards across sub-router stacks. |
| `chain.go` (middleware chain) | 80% | Small but critical — builds handler chains right-to-left. A bug reverses middleware execution order. |
| `middleware/` (built-in middleware) | 75–80% | 29 middleware files. Most are straightforward wrappers. Focus on `recoverer.go` (panic handling), `throttle.go` (rate limiting), `compress.go` (pooled encoders), and `timeout.go` (context cancellation). |

## Coverage Theater Prevention

The following test patterns are **fake tests** for chi and must be avoided:

- Asserting that a route was registered without verifying it matches requests correctly (testing `InsertRoute` succeeded without calling `FindRoute`)
- Testing that `NewMux()` returns non-nil — this is a constructor, not business logic
- Asserting `http.StatusOK` on a response without checking the response body matches the expected handler's output
- Testing middleware by asserting it calls `next.ServeHTTP()` without verifying it transforms the request/response correctly
- Testing URL parameter extraction with only single-segment paths — the real bugs are in nested sub-routers with parameter shadowing
- Mocking the radix trie and testing routing logic in isolation — the value is in the integration of trie traversal with parameter extraction
- Testing `Context.Reset()` by checking fields are zero-valued without verifying the context is correctly reused from the sync.Pool

## Fitness-to-Purpose Scenarios

### Scenario 1: Radix Trie Node Split Corruption

**Requirement tag:** [Req: inferred — from tree.go InsertRoute() split logic]

**What happened:** When two routes share a common static prefix (e.g., `/users` and `/us`), `InsertRoute()` at tree.go:200-228 splits the existing node, creating a new parent with the common prefix and two children. If the split calculation in `longestPrefix()` is off by one, the split produces a node whose prefix doesn't match either route — subsequent lookups for both routes fail silently, returning nil from `findRoute()` and triggering 404s. Because the routes appear registered (the tree has nodes), no error is raised. With 50+ routes sharing prefixes like `/api/v1/users`, `/api/v1/user-settings`, `/api/v1/us-regions`, a single off-by-one in the common prefix calculation could misroute all 50 routes, returning 404 for valid requests with no indication of the root cause.

**The requirement:** `InsertRoute()` must correctly split nodes at the exact common prefix boundary, and both the original and new routes must be findable after the split.

**How to verify:** Insert routes with overlapping prefixes (`/users`, `/us`, `/user-settings`), then `FindRoute()` each one and assert the correct handler is returned.

### Scenario 2: URL Parameter Extraction Across Nested Sub-Routers

**Requirement tag:** [Req: inferred — from context.go URLParam() reverse iteration]

**What happened:** `URLParam()` at context.go:100-107 iterates URL parameter keys in reverse order, returning the last-added match. This design supports parameter shadowing in nested sub-routers — a child router's `{id}` should override a parent's `{id}`. However, because `URLParams.Keys` accumulates across the entire sub-router stack (via `FindRoute` at tree.go:387-388 appending `routeParams`), a Mount at `/api/{version}` containing a route `/{id}` produces URLParams with keys `["*", "version", "*", "id"]` where the wildcard entries from mount points pollute the parameter space. If the reverse iteration encounters the wrong key first (e.g., two `{id}` params from different nesting levels), the caller gets the wrong parameter value — serving user 42's data to user 99's request. With 3 levels of sub-router nesting (common in large REST APIs), there could be 6+ accumulated parameters where only 2 are meaningful.

**The requirement:** `URLParam(key)` must return the parameter value from the innermost (most recently mounted) sub-router, ignoring wildcard mount-point artifacts.

**How to verify:** Create a 3-level nested router with `{id}` at two levels. Issue a request and verify `URLParam("id")` returns the innermost value.

### Scenario 3: Context Pool Reuse After Panic in Handler

**Requirement tag:** [Req: inferred — from mux.go ServeHTTP() pool.Get/pool.Put pattern]

**What happened:** `ServeHTTP()` at mux.go:81-91 gets a Context from the sync.Pool, calls `Reset()`, serves the request, then puts it back. But if the handler panics (before the `pool.Put` call at line 91), the Context is never returned to the pool. This is a memory leak, not a correctness bug per se — but it gets worse. If the panic recovery middleware (`middleware/recoverer.go`) catches the panic and writes a response, the deferred `pool.Put` at mux.go:91 *does* execute because `ServeHTTP` doesn't panic (the middleware caught it). The Context is returned to the pool in whatever state the panicking handler left it — potentially with stale URLParams from the failed request. The next request that gets this Context from the pool calls `Reset()`, which clears the fields — but only if `Reset()` covers every field. Under concurrent load (1000 req/s), a timing window where `pool.Get` returns a Context between the panic recovery and the `pool.Put` could serve stale routing data.

**The requirement:** Context.Reset() must clear ALL mutable fields, and the pool.Get/Reset/pool.Put lifecycle must be safe under concurrent panicking handlers.

**How to verify:** Register a handler that panics, issue concurrent requests with the Recoverer middleware, and verify subsequent requests get correct (not stale) URL parameters.

### Scenario 4: Middleware Ordering Violation After Route Registration

**Requirement tag:** [Req: inferred — from mux.go Use() panic guard]

**What happened:** `Use()` at mux.go:100-105 panics if `mx.handler != nil`, enforcing that all middleware must be registered before routes. This is a configuration-time guard, not a runtime guard. But `With()` at mux.go:236-257 creates inline mux objects that bypass this check — inline muxes set `mx.handler = http.HandlerFunc(mx.routeHTTP)` at mux.go:429 inside `handle()`, but new middleware can still be added via the parent. If a developer calls `r.With(mw1).Get("/a", h1)` then later `r.Use(mw2)` — the second `Use()` panics because the first `With()` call triggered `updateRouteHandler()`. This panic is confusing because the developer hasn't registered any routes directly on `r`. In a codebase with 200+ routes across 15 files, this ordering constraint creates a "configuration minefield" where adding one middleware in the wrong file triggers a panic at startup.

**The requirement:** `Use()` must panic with a clear message when middleware is added after routes, and the panic must not be triggerable by `With()` calls alone on sub-routers.

**How to verify:** Test that `Use()` panics after `Get()` registration. Test that `With()` on a child does not prevent `Use()` on the parent for middleware added before any route.

### Scenario 5: Wildcard Pattern Collision on Mount

**Requirement tag:** [Req: inferred — from mux.go Mount() duplicate pattern check]

**What happened:** `Mount()` at mux.go:296-298 checks for duplicate patterns by calling `mx.tree.findPattern(pattern+"*")` and `mx.tree.findPattern(pattern+"/*")`. If both return false, the mount proceeds. But this check is incomplete — it doesn't detect the case where a static route like `/api/users` was registered and then `Mount("/api", subRouter)` is called. The mount adds `/api/*` which would conflict with the existing `/api/users` at the tree level. Because the tree stores static and catch-all nodes in separate children arrays (`children[ntStatic]` vs `children[ntCatchAll]`), the duplicate isn't detected. The result: requests to `/api/users` match the static route, but requests to `/api/users/123` might match the mounted sub-router's catch-all — or might not, depending on tree traversal order. With 10 API modules mounted under `/api/`, each with 5-10 sub-routes, a single Mount ordering issue could cause 50+ routes to silently resolve to the wrong handler.

**The requirement:** Route matching must be deterministic regardless of registration order for static routes vs mounted sub-routers sharing a prefix.

**How to verify:** Register a static route `/api/users`, then Mount `/api` with a sub-router that has `/{resource}`. Verify `/api/users` hits the static handler and `/api/other` hits the mounted sub-router.

### Scenario 6: Regexp Pattern Validation Accepts Catastrophic Backtracking

**Requirement tag:** [Req: inferred — from tree.go addChild() regexp.Compile]

**What happened:** `addChild()` at tree.go:257-259 compiles regexp patterns from route definitions like `/{id:[0-9]+}`. It panics on invalid patterns (compile error), but does not check for pathological patterns that cause exponential backtracking — e.g., `/{x:(a+)+$}`. Go's `regexp` package uses RE2 which guarantees linear-time matching, so catastrophic backtracking is not possible in Go. However, the pattern is applied to every incoming request via `xn.rex.MatchString()` at tree.go:449. A complex but valid regexp like `/{id:[a-zA-Z0-9._~:@!$&'()*+,;=-]+}` applied to long URL segments (256+ chars) will still consume measurable CPU per request. At 10,000 req/s, this creates a latency spike that's hard to diagnose because it's in the routing layer, not the handler.

**The requirement:** Regexp patterns in route definitions must compile successfully and match within reasonable time for typical URL segment lengths.

**How to verify:** Register a route with a complex regexp pattern, issue requests with segments of varying lengths (1, 50, 256 chars), and assert the correct match/no-match behavior.

### Scenario 7: Method Not Allowed Handler Missing Allow Header Methods

**Requirement tag:** [Req: inferred — from mux.go methodNotAllowedHandler() and tree.go findRoute() methodsAllowed accumulation]

**What happened:** When `findRoute()` at tree.go:469-479 encounters a route that matches the path but not the method, it sets `rctx.methodNotAllowed = true` and accumulates allowed methods in `rctx.methodsAllowed`. The `methodNotAllowedHandler()` at mux.go:518-526 iterates these methods and sets the `Allow` header. But `methodsAllowed` is accumulated during tree traversal, which can visit multiple nodes before concluding no method match exists. If the traversal visits a param node that matches the path but not the method, then backtracks and finds a static node, the `methodsAllowed` from the param node persists — the 405 response advertises methods that are actually on a different route pattern. With 8 HTTP methods × 20 route patterns sharing a prefix, the Allow header could list methods from 3-4 different route patterns, misleading the client.

**The requirement:** The `Allow` header in 405 responses must list only methods available for the exact matched route pattern, not methods from unrelated routes visited during backtracking.

**How to verify:** Register `GET /users/{id}` and `POST /users`. Request `DELETE /users/123` and verify the 405 Allow header lists only GET (and possibly HEAD), not POST.

### Scenario 8: RoutePattern Wildcard Collapse Across Deep Nesting

**Requirement tag:** [Req: inferred — from context.go RoutePattern() and replaceWildcards()]

**What happened:** `RoutePattern()` at context.go:123-134 joins `RoutePatterns` and removes interior `/*/ ` sequences via `replaceWildcards()`. This works for 1-2 levels of nesting but the iterative replacement `for strings.Contains(p, "/*/")` at context.go:140-142 is designed to handle consecutive wildcards. However, when a route pattern itself contains a literal `*` as part of a parameter name or path segment (e.g., `/*special_path/*`), the wildcard replacement could incorrectly collapse it. The test at context_test.go:67-78 verifies this exact case. With 4+ levels of Mount/Route nesting (common in API gateway patterns), the accumulated RoutePatterns slice could have 8+ entries with 4+ wildcards, and the pattern used for metrics, logging, or OpenTelemetry tracing would be wrong — causing metric cardinality explosion or incorrect trace grouping.

**The requirement:** `RoutePattern()` must correctly collapse interior mount-point wildcards while preserving wildcards that are part of the actual route pattern.

**How to verify:** Create a 4-level nested router with mixed wildcards and named params. Verify `RoutePattern()` returns the correct collapsed pattern.

### Scenario 9: Handle() With Space-Delimited Method Pattern Bypass

**Requirement tag:** [Req: inferred — from mux.go Handle() pattern parsing at line 110-114]

**What happened:** `Handle()` at mux.go:110-116 checks if the pattern contains a space or tab character, and if so, splits it into method and path. This allows patterns like `"GET /path"` — matching Go 1.22+'s stdlib ServeMux syntax. But `strings.IndexAny(pattern, " \t")` at mux.go:110 finds the first space/tab, meaning a pattern like `"/path with spaces"` would be incorrectly split, treating `"/path"` as the method and `"with spaces"` as the path. The `Method()` call at mux.go:111 would then panic because `"/path"` is not a valid HTTP method (mux.go:130). While spaces in URL patterns are unusual, this parsing means chi silently interprets any pattern with a space as a method+path pair, with no way to escape the space. A route registered as `"/my path"` panics at startup instead of registering the literal path.

**The requirement:** `Handle()` must correctly parse space-delimited method+path patterns and panic with a clear error for invalid method names.

**How to verify:** Test `Handle("GET /path", h)` routes correctly. Test `Handle("INVALID /path", h)` panics with method error. Test that patterns without spaces register as all-method handlers.

### Scenario 10: RegisterMethod() Exhausts Bit Space

**Requirement tag:** [Req: inferred — from tree.go RegisterMethod() bit limit check]

**What happened:** `RegisterMethod()` at tree.go:61-77 maps custom HTTP methods to bit flags using `methodTyp(2 << n)` where n is the current map size. It panics when `n > strconv.IntSize-2`, which is 62 on 64-bit systems. This limits chi to 62 custom methods (plus the 9 built-in ones). While hitting this limit is extremely unlikely in practice, the `2 << n` calculation means the bit flag for method n uses position n+1, not n — so the actual limit is `strconv.IntSize - 2` total methods (built-in + custom). Registering 55+ custom methods (conceivable in a gRPC-HTTP gateway that maps gRPC methods to custom HTTP verbs) would hit this limit and panic at startup with a non-obvious error message.

**The requirement:** `RegisterMethod()` must correctly assign unique bit flags for custom methods and panic with a clear message before exceeding the platform's integer bit width.

**How to verify:** Register custom methods up to the limit and verify each gets a unique bit flag. Verify exceeding the limit panics with the expected message.

## AI Session Quality Discipline

1. Read QUALITY.md before starting work.
2. Run the full test suite (`go test ./...`) before marking any task complete.
3. Add tests for new functionality (not just happy path — include edge cases for each node type: static, param, regexp, catch-all).
4. Update this file if new failure modes are discovered.
5. Output a Quality Compliance Checklist before ending a session.
6. Never remove a fitness-to-purpose scenario. Only add new ones.

## The Human Gate

- **Routing correctness for complex real-world patterns** — requires domain knowledge of REST API design conventions
- **Performance regression assessment** — routing latency under load requires benchmarking, not just test passage
- **Middleware composition ordering** — whether middleware A should run before B is a design decision
- **Breaking API changes** — backward compatibility with existing chi users requires human judgment
- **Security review of auth-related middleware** — `basic_auth.go`, `realip.go` changes need security expertise
