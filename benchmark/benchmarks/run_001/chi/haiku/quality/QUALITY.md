# Quality Constitution: Chi HTTP Router

## Purpose

Chi is a lightweight HTTP router for Go that must handle high-concurrency request routing with minimal latency and zero data loss. Quality for chi means:

- **Deming** ("quality is built in, not inspected in") — Every AI session inherits a shared understanding of what "correct routing" means through this constitution and the test suite.
- **Juran** ("fitness for use") — The router must correctly match requests to handlers even under adversarial input (overlapping patterns, unicode paths, regex edge cases), correctly manage the request lifecycle through middleware stacks, and never lose or mismatch URL parameters.
- **Crosby** ("quality is free") — Building this quality playbook upfront prevents production routing failures that could silently route requests to wrong handlers or lose request context.

## Coverage Targets

| Module | Target | Why |
|--------|--------|-----|
| `tree.go` (radix trie) | 95% | The core routing algorithm is the most failure-prone. Silent bugs here (incorrect pattern matching, parameter corruption, state machine violations) route requests to wrong handlers. At scale (thousands of routes), trie insertion order, regex compilation, and edge traversal bugs become invisible without comprehensive testing. |
| `mux.go` (request multiplexing) | 90% | Middleware stack composition, context pool management, handler resolution. A middleware ordering mistake could bypass authentication. Pool exhaustion under high load could deadlock. Handler nil checks and panic recovery are critical. |
| `context.go` (routing context) | 90% | URL parameter accumulation, routing pattern tracking. Parameter order corruption or pattern tracking failure would produce wrong values in handlers. The Context lifecycle (creation, reset, reuse) must be bulletproof. |
| `middleware/*` | 85% | Individual middleware modules, each with specific contracts (Logger output format, Recoverer panic handling, Timeout signal propagation, auth state validation). |
| `chain.go` (middleware composition) | 85% | Chain execution order, middleware wrapping, handler invocation. Reversed wrapping (innermost handler called last) would break the entire stack. |

## Coverage Theater Prevention

**Fake tests for chi that look good but don't catch real bugs:**

1. **Test handler registration without invocation** — Calling `r.Get("/path", handler)` and asserting no panic, without actually serving a request and verifying the handler was invoked.
2. **Mock handler tests** — Asserting that a mocked handler was called, instead of testing that the router invoked the *actual* handler with the correct context.
3. **Pattern parsing without matching** — Testing that a pattern like `/{id:\\d+}` parses without error, but not testing whether it actually matches valid requests and rejects invalid ones.
4. **Parameter extraction without assertion** — Testing that `chi.URLParam(r, "id")` returns *something*, without asserting what it returns.
5. **Middleware stack tests with nil handlers** — Asserting that middleware chain builds without testing that it actually transforms requests through the stack.
6. **Panic-based validation without recovery** — Testing patterns that should panic (e.g., duplicate mounts), but not testing the error message or recovery behavior.
7. **Context pool reuse without state isolation** — Creating and reusing a context, but not verifying that reuse doesn't leak state from previous requests.
8. **Routing without status checks** — Serving a request and only checking "no panic," not verifying HTTP status, headers, or body.

## Fitness-to-Purpose Scenarios

### Scenario 1: Radix Trie Insertion Order Independence

**Requirement tag:** [Req: inferred — from tree.go radix trie algorithm]

**What happened:** The radix trie implementation (`tree.go`, lines 138-227) uses prefix splitting when a new pattern partially matches an existing node. If insertion order matters (e.g., `"/users"` inserted before `"/users/{id}"` vs. the reverse), the resulting tree could have different structure. For a system with thousands of routes defined in different orders across files, trie structure drift could cause silent routing failures. A pattern like `"/{user}"` matching `/alice` instead of `/bob` would route requests to wrong handlers without error.

**The requirement:** The router must produce identical routing results regardless of the order in which patterns are inserted. Patterns must be matched by the algorithm's correctness, not by insertion order side effects.

**How to verify:** Insert the same set of patterns in different orders (e.g., alphabetical vs. reverse), then verify that all test queries produce identical results. Compare tree structure equality (node counts, branching factors, endpoint placements) across different insertion orders.

---

### Scenario 2: URL Parameter Corruption Under Overlapping Routes

**Requirement tag:** [Req: inferred — from context.go parameter accumulation (lines 386-387)]

**What happened:** The routing context accumulates URL parameters as it traverses the tree (`rctx.routeParams.Values = append(...)`). If backtracking occurs during tree traversal (e.g., a param node fails to match, then a different branch succeeds), the parameter list could retain values from the failed branch. For example, request `/articles/abc-123` matching a pattern like `/articles/{slug:[a-z-]+}` but with intermediate failed matches in other branches could accumulate extra parameters, causing downstream handlers to receive wrong context.

**The requirement:** URL parameters must reflect exactly the matched pattern — no leakage from failed branches, no accumulation from backtracking. The parameter count and order must always match the matched pattern's param list.

**How to verify:** Create routes with overlapping patterns that force backtracking (e.g., `/users/{id}` and `/users/{name:[a-z]+}`). Verify that parameters from failed matches are not retained. Assert that `chi.URLParam()` returns correct values for successful matches and backtracked requests.

---

### Scenario 3: Middleware Stack Ordering and Context Propagation

**Requirement tag:** [Req: inferred — from mux.go middleware composition (lines 100-105, 236-257)]

**What happened:** Middleware is composed right-to-left in the handler chain. If middleware registers in the wrong order (or if `With()` doesn't preserve parent middleware correctly), middleware might execute out of order, causing auth checks to run after request processing or logging to capture transformed requests instead of original ones. A developer adding `r.Use(LoggerMiddleware)` followed by `r.Use(AuthMiddleware)` expects auth to run first (innermost = first to execute), but order reversals could bypass auth checks entirely.

**The requirement:** Middleware must execute in declaration order: first declared runs first. Parent middleware must execute before inline middleware in sub-routers. Context values set by one middleware must be visible to downstream middleware.

**How to verify:** Create a request that flows through multiple middleware layers (Logger → Auth → Timeout → Handler). Verify order of execution by checking log timestamps or context value mutations. Assert that context values set in one middleware are visible in subsequent handlers.

---

### Scenario 4: Regex Pattern Matching Edge Cases (Anchors and Escaping)

**Requirement tag:** [Req: inferred — from tree.go regex compilation (lines 254-261, 736-743)]

**What happened:** The router auto-anchors regex patterns with `^` and `$` (lines 737-741). If a developer specifies `/{year:\d{4}}`, the router converts it to `^\d{4}$`. However, if the pattern contains unescaped metacharacters (e.g., `/{path:.+}` matching across slashes), the pattern could match more than intended. A pattern like `/{prefix:[a-z]+}` should not match `/123`, but a malformed auto-anchoring could produce false positives. Additionally, if auto-anchoring is skipped for certain regex types, some routes could match incorrectly.

**The requirement:** Regex patterns must match exactly the intended path segment. A pattern `/{id:\d+}` must reject `/id-123`, `/123abc`, and `/`. Cross-segment matching (matching `/`) must be explicitly prevented for param patterns.

**How to verify:** Test patterns with edge cases: digits, letters, mixed case, special characters, unicode, empty segments. Test both valid matches and invalid rejects. Verify that `{id:\d+}` rejects `/abc`, `/123-456`, and that patterns don't match across `/` boundaries.

---

### Scenario 5: Catch-All Pattern Greedy Matching

**Requirement tag:** [Req: inferred — from tree.go catch-all handling (lines 495-500, 752)]

**What happened:** The catch-all pattern `/*` captures the rest of the path including slashes (line 497). If routes are defined as `/admin` and `/admin/*`, a request to `/admin/edit` should match `/admin/*` not `/admin`. However, if the router's pattern matching prioritizes static routes incorrectly, a more general catch-all could suppress static routes entirely. At scale with many overlapping patterns, the routing decision between static and catch-all could become non-deterministic.

**The requirement:** Routes must be matched in order of specificity: static patterns before param patterns before catch-all. A request to `/admin/edit` must match `/admin/edit` if it exists, then `/admin/{id}`, then `/admin/*`. Catch-all routes must be the last resort.

**How to verify:** Create routes `/users`, `/users/{id}`, and `/users/*`. Verify that `/users/123` matches `/users/{id}`, not `/users/*`, and that `/users/admin/settings` matches `/users/*`, not failing with "not found."

---

### Scenario 6: Method Not Allowed (405) Handling Correctness

**Requirement tag:** [Req: inferred — from tree.go findRoute method tracking (lines 469-478, 515-524)]

**What happened:** When a route pattern matches but the HTTP method doesn't (e.g., GET `/users` exists but POST `/users` doesn't), the router must return 405 with an `Allow` header listing available methods. If method tracking (`rctx.methodsAllowed`) corrupts or skips methods, the 405 response could list incomplete or wrong allowed methods. A handler checking `if "POST" in allowed` would fail to realize POST is not allowed. Additionally, if the `methodNotAllowed` flag is not set correctly (line 478), the router could return 404 instead of 405.

**The requirement:** The router must correctly distinguish between "path not found" (404) and "path found but method not allowed" (405). The `Allow` header must list all HTTP methods that have handlers for the matched route.

**How to verify:** Create a route `r.Get("/items")` (only GET). Request `DELETE /items`. Assert status 405 (not 404) and `Allow: GET` header. Verify that `chi.AllowedMethods()` returns correct list.

---

### Scenario 7: Concurrent Request Handling and Context Pool Safety

**Requirement tag:** [Req: inferred — from mux.go context pool pattern (lines 81-91)]

**What happened:** The router uses a `sync.Pool` to reuse `RouteContext` objects for each request to reduce allocations. If context reset is incomplete (line 82) or if concurrent requests share context state, parameter values could leak between requests. For example, request A stores parameter `id=123`, then request B reuses the same context object without proper reset, causing request B to see `id=123` instead of its actual `id=456`. At high concurrency (thousands of concurrent requests), the probability of state leakage increases dramatically.

**The requirement:** Each request must have isolated routing context with no leakage from previous requests. Context reset must clear all state: patterns, parameters, method tracking, and flag bits.

**How to verify:** Simulate high-concurrency requests using the same route with different parameters. Use goroutines to serve requests concurrently (e.g., `go serveRequest()` × 1000). Verify that each goroutine reads the correct parameter value without interference from others.

---

### Scenario 8: Empty and Boundary Path Cases

**Requirement tag:** [Req: inferred — from tree.go path handling (lines 414-417, 429-430, 461-462)]

**What happened:** Edge cases in path matching: empty paths, paths with trailing slashes, and single-character segments. If the router fails to check `len(search) == 0` before accessing `search[0]` (line 416), it could panic on empty paths. Param patterns with empty tail bytes (line 700 default `/`) could mismatch segments. A request for `/` against routes `/{id}` should not match (requires non-empty param). A request for `/users/` against routes `/users/{id}` should not match (requires segment without trailing slash).

**The requirement:** The router must safely handle empty segments, trailing slashes, and boundary conditions without panics. Empty params must be rejected. Trailing slashes must be explicitly handled (not silently matched or ignored).

**How to verify:** Test paths: `/`, `//`, `/users/`, `/users//123`, `/users/{}`, `/?query=1`. Assert no panics and correct match/no-match outcomes.

---

### Scenario 9: Memory Safety Under Malformed Patterns

**Requirement tag:** [Req: inferred — from tree.go pattern parsing (lines 687-752)]

**What happened:** The pattern parser uses string indexing and loop bounds. If a developer defines a malformed pattern like `/{unclosed`, the parsing logic (lines 720-721) correctly detects the missing `}` and panics. However, if the panic message doesn't include the pattern, debugging is harder. Additionally, if regex compilation fails (line 256), the panic message should include the actual regex that failed. Stack overflow could occur if a pattern contains deeply nested groups or if recursion in `addChild` (line 308) or `findRoute` (line 483) doesn't have bounds.

**The requirement:** Pattern validation must catch malformed patterns at registration time and provide actionable panic messages. Recursion depths must not overflow stack for any valid pattern.

**How to verify:** Register invalid patterns: `/{unclosed`, `/{id:\d(}`, `/{id:(?P<name>\d+)}` (nested group), deep nesting like `/a/{a:{a:{a}}}`. Verify that meaningful panic messages are produced and that no stack overflow occurs for valid patterns.

---

### Scenario 10: Handler Nil Checks and Middleware Stack Freezing

**Requirement tag:** [Req: inferred — from mux.go handler management (lines 65-66, 100-105, 239-241)]

**What happened:** The router panics if middleware is added after routes (line 102-104). This design prevents subtle bugs where route order matters, but a lazy middleware registration could bypass the check. Additionally, if the computed handler (`mx.handler`, line 24) is not properly initialized before a request arrives, the default 404 handler might not be accessible. A nil handler in an endpoint (line 510) could cause a panic at request time instead of a registration-time error.

**The requirement:** Middleware must be frozen after the first route is added. All endpoints must have valid (non-nil) handlers at registration time or be explicitly initialized with defaults (404, MethodNotAllowed). Nil handlers must not reach request-serving time.

**How to verify:** Register handlers, then attempt to add middleware. Assert panic. Create a router with no routes, serve a request, verify 404. Register a route with explicit handler vs. default handler, verify both work.

---

## AI Session Quality Discipline

1. Read this QUALITY.md before starting work on chi router changes.
2. Run the full functional test suite (`go test ./quality -v`) before marking any task complete.
3. Add tests for any new routing patterns, middleware, or handler logic (not just happy path — include boundary and error cases).
4. If a scenario's verification test fails, update this file to document the failure mode and add a regression test.
5. Before committing routing changes, run the spec audit protocol (`quality/RUN_SPEC_AUDIT.md`) to catch cross-model issues.
6. Never remove a fitness-to-purpose scenario — only add new ones as new failure modes are discovered.

## The Human Gate

These items require human judgment before proceeding:

- **Breaking API changes** — Removing or renaming public functions (e.g., `chi.URLParam()`, `Router` interface) requires explicit approval.
- **Performance trade-offs** — Changes that optimize routing speed at the cost of memory (or vice versa) need confirmation that the trade-off aligns with production priorities.
- **Middleware contract changes** — Changing the signature of middleware or the execution order of middleware stacks could break production code.
- **Pattern syntax changes** — Modifying how patterns are parsed (e.g., supporting new param syntax) could silently break existing routes.
- **Error handling philosophy** — Decisions between panicking vs. returning errors require design review (chi currently panics on invalid patterns; this could change).
