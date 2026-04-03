# Quality Constitution: chi

## Purpose

Chi is a lightweight, idiomatic HTTP router for Go built entirely on the standard `net/http` library. Quality for chi means **correct routing under all path patterns, safe concurrent request handling, and reliable middleware composition** — not just "tests pass."

**Deming** ("quality is built in, not inspected in") — Quality is built into chi's architecture through its radix trie routing tree, sync.Pool context reuse, and middleware chaining. This quality constitution and the accompanying playbook ensure every AI session inherits the same bar rather than guessing at what matters.

**Juran** ("fitness for use") — Fitness for chi means: (1) every HTTP request is routed to the correct handler with correct URL parameters extracted, (2) middleware executes in the declared order without dropping or corrupting request/response state, (3) subrouters compose cleanly without leaking context across request boundaries, and (4) the router handles concurrent requests safely with zero data races. A router that passes unit tests but silently misroutes requests under concurrent load is not fit for use.

**Crosby** ("quality is free") — Building this quality playbook upfront costs less than debugging production routing failures, middleware ordering bugs, or context leaks discovered after deployment.

## Coverage Targets

| Subsystem | Target | Why |
|-----------|--------|-----|
| `tree.go` (radix trie) | 90–95% | The routing tree is the most complex and fragile component. Pattern parsing (`patNextSegment`), node insertion, and route finding have numerous boundary conditions (regex patterns, catchall wildcards, adjacent params). A bug here silently misroutes every matching request. |
| `mux.go` (mux/router) | 85–90% | Core request dispatch, middleware chaining, subrouter mounting, and 404/405 handling. Bugs here affect every request. The sync.Pool reuse of RouteContext is a concurrency hotspot. |
| `context.go` (routing context) | 85–90% | URL parameter extraction traverses backwards through stacked subrouter params. Off-by-one errors or incorrect reset produce wrong parameter values silently. |
| `chain.go` (middleware chain) | 80–85% | Middleware chaining is relatively simple but the right-to-left composition order is non-obvious. Incorrect ordering silently changes middleware execution behavior. |
| `middleware/*.go` | 75–80% | Individual middleware implementations. Each has its own defensive patterns but the risk is localized to that middleware's functionality. |

## Coverage Theater Prevention

The following test patterns look good but don't catch real bugs in a routing library:

- **Asserting a route was registered without sending a request.** Registration can succeed while routing fails — test the actual HTTP response.
- **Testing with only static routes.** Chi's complexity is in parameterized and regex routes. A test suite of only `/ping` and `/health` paths exercises none of the radix trie's interesting code paths.
- **Asserting `200 OK` without checking the response body or URL parameters.** A request to `/users/123` returning 200 with the wrong user ID is worse than a 404 — it's silent data corruption.
- **Testing middleware in isolation without a routing context.** Middleware like `URLFormat` and `StripSlashes` depend on routing context state. Testing them with a bare `http.Handler` misses integration bugs.
- **Asserting a handler was called without verifying the correct handler.** With overlapping route patterns, the wrong handler can execute and still return 200.
- **Using a single middleware in tests when production uses a stack.** Middleware interaction bugs (ordering, context mutation) only surface with multiple middlewares composed together.

## Fitness-to-Purpose Scenarios

### Scenario 1: Concurrent RouteContext Reuse via sync.Pool

**Requirement tag:** [Req: inferred — from mux.go sync.Pool usage]

**What happened:** Chi uses `sync.Pool` to reuse `RouteContext` objects across requests (`mux.go:53-57`, `mux.go:81-91`). Under concurrent load, if `Reset()` (`context.go:82-96`) fails to clear all fields — or if a handler retains a reference to the context after the request completes — subsequent requests receive stale URL parameters, route patterns, or method information from a previous request. With 1,000 concurrent requests, even a 0.1% context leak rate means ~1 request/second serves data from the wrong route. The leak is undetectable without correlation checks because each individual response looks valid.

**The requirement:** `Reset()` must clear every mutable field on `Context`. No handler must retain a reference to `RouteContext` after `ServeHTTP` returns. The pool Get/Put lifecycle must be atomic per request.

**How to verify:** Send concurrent requests to different routes with distinct URL parameters. Assert each response contains only its own route's parameters — no cross-contamination. Run with `-race` flag.

### Scenario 2: Middleware After Routes Panic

**Requirement tag:** [Req: inferred — from mux.go:101-105 Use() guard]

**What happened:** `Mux.Use()` panics if called after routes are registered (`mx.handler != nil`). This is a deliberate design constraint — the middleware chain is built once during first route registration via `updateRouteHandler()` (`mux.go:511-513`). If a developer adds middleware after defining routes, the panic occurs at registration time, not at request time. However, `With()` and `Group()` create inline muxes that bypass this check. A middleware added via `With()` after the parent's routes are defined silently creates a new inline chain — it works, but only for handlers registered through that `With()` chain, not for previously registered routes.

**The requirement:** `Use()` must panic if called after any route registration. `With()` and `Group()` must correctly inherit parent middlewares and compose them with new ones without affecting existing routes.

**How to verify:** Test that `Use()` after `Get()` panics. Test that `With()` middlewares only apply to handlers registered through the returned router.

### Scenario 3: Wildcard Routing Path Consumption in Subrouters

**Requirement tag:** [Req: inferred — from mux.go:309-339 Mount() handler]

**What happened:** When a subrouter is mounted via `Mount()`, the mount handler shifts the URL path by consuming the wildcard parameter (`mux.go:313`, `nextRoutePath`). If the wildcard reset (`mux.go:317-319`) fails to clear the `*` URLParam, the subrouter receives a stale path — routing the request to the wrong handler or 404ing on a valid path. With deeply nested subrouters (3+ levels), each level must correctly consume its portion of the path. A bug at level 2 corrupts routing for all level 3+ subrouters, affecting every mounted handler beneath it.

**The requirement:** After mount handler execution, `rctx.RoutePath` must contain only the path segment following the mount point. The wildcard URLParam must be cleared.

**How to verify:** Mount a 3-level deep subrouter hierarchy. Send requests that traverse all levels. Assert correct URL parameters at each level and correct handler execution.

### Scenario 4: Regex Route Pattern Validation and Matching

**Requirement tag:** [Req: inferred — from tree.go patNextSegment() and InsertRoute()]

**What happened:** Route patterns like `/{id:[0-9]+}` are parsed by `patNextSegment()` in `tree.go`, which splits on the `:` delimiter and compiles the regex via `regexp.MustCompile()`. If the regex is invalid, `InsertRoute()` panics. If the regex is valid but overly permissive (e.g., `{id:.+}` matches `/` characters), the route captures more path segments than intended, starving downstream routes of input. With a route tree containing 50 patterns, one overly-greedy regex silently captures requests meant for 10+ other routes.

**The requirement:** Regex patterns must be validated at registration time. The regex must not match `/` characters (enforced by chi's route matching algorithm). Invalid patterns must panic with a descriptive error.

**How to verify:** Register routes with valid and invalid regex patterns. Assert invalid patterns panic. Assert regex routes don't match across `/` boundaries. Assert regex routes don't starve sibling routes.

### Scenario 5: Method Not Allowed vs Not Found Disambiguation

**Requirement tag:** [Req: inferred — from mux.go:480-484 routeHTTP() and tree.go FindRoute()]

**What happened:** When `FindRoute()` finds a matching route but not for the requested HTTP method, it sets `rctx.methodNotAllowed = true` and populates `rctx.methodsAllowed`. The router then returns 405 with an `Allow` header listing valid methods (`mux.go:518-526`). If `FindRoute()` incorrectly fails to set `methodNotAllowed` (e.g., because the method check happens before the route match in certain tree traversal paths), the router returns 404 instead of 405 — violating RFC 9110 §15.5.6. An API client receiving 404 instead of 405 will assume the resource doesn't exist rather than that it used the wrong method.

**The requirement:** When a path matches but the method doesn't, the response must be 405 with a correct `Allow` header. When no path matches, the response must be 404.

**How to verify:** Register `GET /resource`. Send `POST /resource`. Assert 405 response with `Allow: GET` header. Send `GET /nonexistent`. Assert 404.

### Scenario 6: Route Pattern Conflict on Mount

**Requirement tag:** [Req: inferred — from mux.go:296-298 Mount() conflict check]

**What happened:** `Mount()` checks for existing patterns before mounting (`mx.tree.findPattern(pattern+"*")`) and panics on conflict. However, the check examines only exact pattern matches — not semantic overlap. Mounting `/api` and then `/api/v2` as separate subrouters succeeds because the patterns differ, but requests to `/api/v2/users` are ambiguous: the `/api/*` catchall captures them before `/api/v2/*` can match. The first-registered mount wins, silently routing requests to the wrong subrouter.

**The requirement:** Mount patterns must not create ambiguous routing. The conflict check must detect overlapping mount points, or documentation must clearly state mount ordering semantics.

**How to verify:** Mount subrouters at `/api` and `/api/v2`. Send requests to `/api/v2/users`. Assert the request reaches the `/api/v2` subrouter, not the `/api` catchall.

### Scenario 7: RouteContext Reset Preserves Slice Capacity

**Requirement tag:** [Req: inferred — from context.go:82-96 Reset()]

**What happened:** `Reset()` slices all arrays to zero length (`x.URLParams.Keys[:0]`) rather than nilling them. This is an intentional optimization — preserving backing array capacity reduces GC pressure under high-throughput load. However, if `Reset()` is modified to nil slices instead (a common "cleanup" refactor), every request allocates new slices, increasing GC pause time. Under 10,000 req/s, this can increase p99 latency by 2-5ms due to additional allocations. The optimization is invisible — both implementations produce correct results, but the nil version degrades performance under load.

**The requirement:** `Reset()` must use `[:0]` slicing, not nil assignment, for all slice fields. After reset, `cap()` of each slice must be preserved from the previous request.

**How to verify:** Get a `Context` from the pool, add URL params, reset it, verify `len()` is 0 but `cap()` is preserved. Benchmark allocation count.

### Scenario 8: Nil Handler Mount Panic

**Requirement tag:** [Req: inferred — from mux.go:291-292 Mount() nil check]

**What happened:** `Mount()` panics if the handler is nil. Similarly, `Route()` panics if the callback function is nil (`mux.go:274-276`). These panics occur at registration time, which is correct — a nil handler at serve time would cause a nil pointer dereference crash on every matching request. The panic message includes the pattern, aiding debugging. However, `Handle()` and `HandleFunc()` do NOT have nil checks — passing a nil handler to `Handle("/path", nil)` silently registers a nil endpoint that will crash on the first matching request.

**The requirement:** All handler registration methods must validate their handler argument. Nil handlers must panic at registration time with a descriptive message, not crash at serve time.

**How to verify:** Test `Mount(pattern, nil)` panics. Test `Route(pattern, nil)` panics. Test `Handle(pattern, nil)` behavior.

### Scenario 9: Unsupported HTTP Method Handling

**Requirement tag:** [Req: inferred — from mux.go:128-133 Method() and tree.go:62-77 RegisterMethod()]

**What happened:** Chi supports 9 standard HTTP methods via `methodMap`. Custom methods can be added via `RegisterMethod()`. If a request arrives with an unrecognized method (e.g., `PURGE` without prior registration), `routeHTTP()` calls `MethodNotAllowedHandler()` because `methodMap` lookup fails (`mux.go:462-465`). This is semantically incorrect — the method isn't "not allowed for this route," it's "unknown to the router entirely." The distinction matters for HTTP proxies and caches that interpret 405 differently from 501 (Not Implemented).

**The requirement:** Unregistered methods must result in 405 (current behavior) or a configurable response. `RegisterMethod()` must handle edge cases: empty string (returns silently), already-registered methods (returns silently), and method count overflow (panics).

**How to verify:** Send a request with an unregistered HTTP method. Verify the response code. Test `RegisterMethod()` with empty string, duplicate, and valid new method.

### Scenario 10: Recoverer Middleware WebSocket Upgrade Handling

**Requirement tag:** [Req: inferred — from middleware/recoverer.go:25-42]

**What happened:** The Recoverer middleware has special handling for `http.ErrAbortHandler` — it re-panics rather than recovering, allowing the HTTP server to abort the connection cleanly. It also checks for the `Connection: Upgrade` header before writing a 500 status, because WebSocket upgrade connections may have already switched protocols. If the Recoverer writes a 500 status after protocol upgrade, it corrupts the WebSocket stream. However, the check only examines the request header, not whether the upgrade actually completed — a failed upgrade attempt that panics after the Upgrade header is sent but before protocol switch will silently swallow the error.

**The requirement:** Recoverer must re-panic on `http.ErrAbortHandler`. It must not write HTTP status codes on connections that have the `Connection: Upgrade` header. For non-upgrade connections, it must write 500.

**How to verify:** Test panic recovery with a normal handler (expect 500). Test panic with `http.ErrAbortHandler` (expect re-panic). Test panic with `Connection: Upgrade` header (expect no status write).

## AI Session Quality Discipline

1. Read `quality/QUALITY.md` before starting work on chi.
2. Run `go test ./...` before marking any task complete.
3. Run `go test -race ./...` for any changes touching shared state (sync.Pool, context, middleware).
4. Add tests for new functionality — not just happy path, include edge cases and concurrent access.
5. Update this file if new failure modes are discovered.
6. Output a Quality Compliance Checklist before ending a session.
7. Never remove a fitness-to-purpose scenario. Only add new ones.

## The Human Gate

The following require human judgment:

- **API design decisions** — Whether a new method should be on `Router` interface vs `Mux` struct
- **Performance trade-offs** — sync.Pool vs fresh allocation, radix trie vs hash map for specific access patterns
- **Backward compatibility** — Whether a bug fix changes public API behavior
- **Security implications** — Path traversal, header injection, and other HTTP-level security concerns in middleware
- **Documentation accuracy** — Whether code examples in README and godoc match actual behavior
