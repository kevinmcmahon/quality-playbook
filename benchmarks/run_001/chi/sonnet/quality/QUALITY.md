# Quality Constitution: chi

## Purpose

Chi is a lightweight, idiomatic Go HTTP router built on a Patricia Radix trie. Quality for chi means **fitness for correctness under the full range of routing patterns its users will register** — not just happy-path GET / routes, but regexp params, wildcard catch-alls, nested sub-routers, inline middleware chains, and cross-method routing with correct 404/405 distinction. A broken chi in production silently misroutes requests or panics in ways that propagate to every service built on it.

Following Deming's principle that quality is built in rather than inspected in, chi embeds correctness requirements directly into its panic messages, making contract violations fail loud at startup rather than silently at request time. This quality constitution extends that approach: every AI session working on chi reads this file first, inheriting the same bar. Following Juran's fitness-for-use principle, "working" for chi means: patterns are parsed correctly, URL parameters are extracted accurately, middleware stacks compose in the right order, sub-router contexts nest properly, and the pool of route contexts is reused safely under concurrent load.

Following Crosby's principle that quality is free — chi's test suite, written once, prevents regressions across hundreds of subsequent changes. This quality playbook makes the bar explicit so that future AI sessions cannot argue it down.

## Coverage Targets

| Subsystem | Target | Why |
|-----------|--------|-----|
| `tree.go` — Patricia Radix trie | 90% | Pattern parsing is the most complex code in chi. A bug in `patNextSegment` or `findRoute` silently misroutes requests — e.g., a regexp param `{id:\\d+}` matching inputs it should reject, or a catch-all consuming a route that should match a more-specific static path. The trie's recursive descent makes edge cases hard to find without exhaustive coverage. |
| `mux.go` — Mux and ServeHTTP | 85% | All route registration, middleware stacking, and the sync.Pool context reuse logic lives here. Concurrency bugs in `ServeHTTP` affect every concurrent request. Panic guards at registration time (middleware ordering, nil handler, duplicate mount) must fire reliably. |
| `context.go` — RouteContext | 85% | URLParam lookup, RoutePattern assembly from subrouter stacks, and the nil-safe context accessors all live here. A bug in URLParam's backward search silently returns wrong param values when the same key appears at multiple router levels. |
| `chain.go` — Middleware chaining | 80% | Simple but critical: a bug in the reverse-order wrapping produces middleware that executes in the wrong order, which can break auth, logging, and rate-limiting middleware stacks. |
| `middleware/` — Optional middleware | 75% | Each middleware component is relatively independent, but incorrect panic guards (e.g., Throttle with limit ≤ 0), compress content-type matching, and RealIP header extraction each have failure modes worth covering. |

The rationale column is not documentation — it is protection against erosion. A future AI session cannot argue these targets down because each one references a specific class of failure.

## Coverage Theater Prevention

For chi, the following tests are fake and must not be written:

- **Asserting that NewRouter() returns a non-nil value.** This tests the Go allocator, not chi.
- **Registering a route and asserting no panic occurred.** This is true by construction for any valid pattern — it exercises the "happy path precondition" rather than routing behavior.
- **Asserting that `w.Code == 200` without checking the response body.** A misbehaving handler can return 200 with wrong content; only checking the body value catches that.
- **Testing middleware execution by asserting a counter incremented.** Count-only tests confirm the middleware ran but not that it ran in the correct order or with the correct request context.
- **Testing URLParam with `assert param != ""`** — check the actual value, not just presence.
- **Mocking the router to test middleware in isolation** — chi's value is the composition; testing components in isolation misses integration bugs.

## Fitness-to-Purpose Scenarios

### Scenario 1: Middleware After Routes Panics

**Requirement tag:** [Req: inferred — from mux.go:102 panic guard]

**What happened:** `mx.handler` is set (lazily built) the first time a route is registered. Once the handler chain is compiled, adding a new middleware via `Use()` would silently be ignored — the already-compiled chain wouldn't include it. Chi converts this silent failure into a loud panic. Without this guard, a developer who calls `r.Use(AuthMiddleware)` *after* `r.Get("/", handler)` would get zero authentication — no error, no warning, full security hole. In a multi-file setup where routes and middleware registration are split across files, this ordering bug is easy to introduce.

**The requirement:** Calling `Use()` after any route has been registered must panic with message containing "all middlewares must be defined before routes on a mux". The panic must not be suppressible by registering middleware before the first route in one file but after in another.

**How to verify:** `TestScenario1_MiddlewareAfterRoutePanics` — register a route on a mux, then call `Use()` and assert the panic fires with the expected message.

---

### Scenario 2: Wildcard Must Be Last

**Requirement tag:** [Req: inferred — from tree.go:697 and tree.go:750 panic guards]

**What happened:** A pattern like `/api/*/users` would be ambiguous — the `*` is supposed to consume the rest of the path, so no segment can follow it. If chi allowed this, the routing tree would produce undefined behavior: the catch-all node would match, consume everything, and the static `/users` segment would never be reached. Two separate guards enforce this: one when `*` appears before `{` in the pattern string (tree.go:697), one when `*` appears before the end of the pattern string (tree.go:750).

**The requirement:** Any pattern containing `*` not at the final position must panic at route registration time, not at request time. Pattern `/api/*/rest` and pattern `/api/*extra` (with trailing text) must both panic.

**How to verify:** `TestScenario2_WildcardNotLastPanics` — attempt to register patterns with mid-path wildcard and assert panic.

---

### Scenario 3: Duplicate Param Keys Panic

**Requirement tag:** [Req: inferred — from tree.go:765 panic guard]

**What happened:** A pattern like `/{id}/{id}` contains the same URL parameter key twice. When the handler calls `chi.URLParam(r, "id")`, the context's backward-search would return whichever value appeared last in the URL params stack — silently returning the second `id` value while dropping the first. In a real API with routes like `/{userID}/posts/{userID}`, the second `{userID}` would shadow the first, corrupting both values depending on search order.

**The requirement:** Any pattern containing a duplicate parameter key (e.g., `/{id}/path/{id}`) must panic at route registration time with a message identifying the duplicate key.

**How to verify:** `TestScenario3_DuplicateParamKeyPanics` — register a route with duplicate param key and assert panic.

---

### Scenario 4: Nil Handler Panics at Mount Time

**Requirement tag:** [Req: inferred — from mux.go:291 and mux.go:274 panic guards]

**What happened:** If `Mount()` silently accepted a nil handler, the first request to that path prefix would call `nil.ServeHTTP(...)` and produce a nil pointer dereference panic — crashing the entire server, not just the handler. Chi converts this to a registration-time panic so the bug is caught during server startup or test initialization rather than under production traffic. Similarly, `Route()` with a nil function panics rather than registering an empty subrouter.

**The requirement:** `Mount(pattern, nil)` and `Route(pattern, nil)` must both panic at call time with descriptive messages. The panics must fire regardless of whether a route context already exists.

**How to verify:** `TestScenario4_NilHandlerMountPanics` and `TestScenario4_NilRouteFunc Panics` — call both functions with nil and assert panics.

---

### Scenario 5: Context Pool Reuse Is Safe

**Requirement tag:** [Req: inferred — from mux.go:81-91 sync.Pool usage]

**What happened:** `ServeHTTP` uses `sync.Pool` to reuse `*Context` objects across requests. If `Reset()` does not zero all fields — including `methodNotAllowed`, `methodsAllowed`, `RoutePatterns`, `URLParams`, `routeParams`, `parentCtx` — a reused context carries stale routing state from a previous request. In practice: a previous request's URL params could leak into the next request, or a previous `methodNotAllowed=true` flag could cause chi to return 405 for a route that should return 200.

**The requirement:** After a request completes and its context is returned to the pool, all routing state must be zero. A subsequent request that reuses the same context object must see no stale params, patterns, or method flags from the previous request.

**How to verify:** `TestScenario5_ContextPoolReuseIsSafe` — make two sequential requests through the same mux, second request to a different path; assert no URL params from first request appear in second request's handler.

---

### Scenario 6: Method Not Allowed vs Not Found

**Requirement tag:** [Req: inferred — from mux.go:480-484 and tree.go findRoute methodNotAllowed flag]

**What happened:** When a route exists for a path but not for the requested method (e.g., `GET /users/{id}` exists but client sends `DELETE /users/123`), chi must return 405 with an Allow header listing valid methods — not 404. Returning 404 violates HTTP semantics (RFC 9110 §15.5.5) and breaks API clients that use the 405 response to discover allowed methods. The `rctx.methodNotAllowed` flag is set during tree traversal when a node has endpoints but none match the current method.

**The requirement:** A request to a registered path using an unregistered HTTP method must receive a 405 response with a non-empty Allow header. A request to an unregistered path must receive 404. These two cases must not be confused.

**How to verify:** `TestScenario6_MethodNotAllowedVsNotFound` — register GET on a path, send DELETE; assert 405 with Allow header. Send request to unregistered path; assert 404.

---

### Scenario 7: URLParams Stack Correctly Across Nested Subrouters

**Requirement tag:** [Req: inferred — from tree.go:387-388 URLParams append logic and mux.go Mount mountHandler]

**What happened:** When a request traverses a mounted subrouter, both the parent router and the subrouter contribute URL parameters. The parent matches `/api/{version}/*` capturing `version`, and the subrouter matches `/users/{id}` capturing `id`. Both param sets are appended to `rctx.URLParams` during `FindRoute`. If this stacking is broken — e.g., the subrouter's `Reset()` wipes the parent's params — then `chi.URLParam(r, "version")` returns empty string inside subrouter handlers, silently losing parent-captured parameters and breaking versioned API routing.

**The requirement:** `chi.URLParam()` must return correct values for all URL parameters captured at every level of a nested router hierarchy. Parent params must be accessible inside subrouter handlers.

**How to verify:** `TestScenario7_NestedRouterURLParams` — mount a subrouter under `/{org}/api`, register `/{repo}` on the subrouter, and assert both `org` and `repo` params are accessible in the leaf handler.

---

### Scenario 8: RoutePattern Removes Intermediate Wildcards

**Requirement tag:** [Req: inferred — from context.go:139-144 replaceWildcards and RoutePattern]

**What happened:** When using `Mount()` and `Route()`, each router level appends its matching pattern segment to `rctx.RoutePatterns`. A mount at `/v1` adds `/v1/*`, a sub-mount adds `/resources/*`, and the leaf route adds `/{id}`. The final `RoutePattern()` must produce `/v1/resources/{id}` — not `/v1/resources/*/{id}`. Without `replaceWildcards()` iteratively removing `/*/ ` sequences, the accumulated pattern would contain every intermediate wildcard, producing incorrect pattern strings used in observability (metrics, tracing) and docgen.

**The requirement:** `Context.RoutePattern()` must remove all intermediate `/*` segments from the accumulated route pattern stack, leaving only the final pattern and any trailing wildcard.

**How to verify:** `TestScenario8_RoutePatternWildcardCleanup` — build a context with route patterns simulating a two-level mount and assert the cleaned pattern matches expected.

---

### Scenario 9: Invalid Regexp Panics at Registration

**Requirement tag:** [Req: inferred — from tree.go:258 regexp.Compile panic guard]

**What happened:** A route parameter like `{id:[invalid}` contains a malformed regexp. If chi deferred the error until request time, the router would compile fine, start accepting traffic, and then panic on the first matching request — crashing the request goroutine. Chi compiles the regexp at route registration time (tree.go:258) so the panic fires during server initialization, preventing malformed regexp routes from ever entering production.

**The requirement:** A route pattern containing a syntactically invalid regexp (e.g., `{id:[unclosed}`) must panic at route registration time with a message identifying the invalid regexp pattern.

**How to verify:** `TestScenario9_InvalidRegexpPanics` — call `r.Get` with an invalid regexp pattern and assert the panic fires.

---

### Scenario 10: Duplicate Mount Path Conflicts

**Requirement tag:** [Req: inferred — from mux.go:296-299 findPattern duplicate mount check]

**What happened:** If two `Mount()` calls register handlers at the same path prefix (e.g., `r.Mount("/api", handlerA)` and `r.Mount("/api", handlerB)`), chi must panic rather than silently routing all traffic to whichever handler was registered last (or creating an undefined split). The check at mux.go:296-299 uses `findPattern` to detect existing `pattern*` or `pattern/*` nodes before registering the new mount.

**The requirement:** Attempting to `Mount()` a handler at a path prefix that is already mounted (whether the exact pattern or a wildcard extension) must panic with a message identifying the conflicting path.

**How to verify:** `TestScenario10_DuplicateMountPanics` — mount two handlers at the same prefix and assert panic.

---

## AI Session Quality Discipline

1. Read `quality/QUALITY.md` before starting any work on chi.
2. Run `go test ./...` from the chi module root before marking any task complete. All existing tests must pass.
3. Add tests for new functionality — not just happy path. Every new pattern type, panic guard, or routing edge case needs a test.
4. Update this file when new failure modes are discovered during development or code review.
5. Output a Quality Compliance Checklist before ending a session:
   - [ ] All scenarios still have corresponding tests
   - [ ] `go test ./...` passes with no failures
   - [ ] No new coverage theater introduced
6. Never remove a fitness-to-purpose scenario. Only add new ones.
7. Never remove a panic guard from chi's registration-time checks — they prevent silent production failures.

## The Human Gate

The following quality decisions require human judgment and cannot be automated:

- **Performance regression evaluation** — Whether a routing change that makes tests pass but adds 5ns/op to `BenchmarkChi_GithubAll` is acceptable requires understanding the project's performance commitments.
- **Backward compatibility** — Whether a behavior change (e.g., changing how wildcard params are named) breaks existing users' code requires knowledge of the ecosystem.
- **Security review** — Changes to `middleware/basic_auth.go`, `middleware/realip.go`, or `middleware/request_id.go` that affect authentication, IP attribution, or request identification require security-focused review.
- **Error message wording** — Chi's panic messages are user-facing. Changes to wording affect developer experience across all projects that depend on chi.
- **New middleware acceptance** — Whether a proposed middleware belongs in the core `middleware/` package vs. in a separate repository requires maintainer judgment.
