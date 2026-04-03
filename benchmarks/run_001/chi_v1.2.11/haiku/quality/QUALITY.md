# Quality Constitution: Chi HTTP Router

## Purpose

Chi is a lightweight, production-grade HTTP router used in distributed systems to handle millions of requests. Quality means more than code coverage — it means the router:

- **Built in, not inspected** (Deming): The safety mechanisms (panic-based input validation, context pool management, route tree ordering) prevent invalid configurations at registration time rather than detecting failures at runtime.
- **Fit for production use** (Juran): A panic in routing code should never reach production. Route patterns must be validated before handlers run. Context leakage across requests must never happen. Regexes used in route patterns must not cause denial-of-service.
- **Correct by design** (Crosby): The radix tree's insertion and lookup logic must handle all valid patterns. Parameter extraction must match the specification exactly. Method routing must never silently mismatch the HTTP spec.

## Coverage Targets

| Subsystem | Target | Why |
|-----------|--------|-----|
| tree.go (radix tree insert/lookup) | 95%+ | 877 lines of critical routing logic. Missing branches mean silent routing failures or pattern collisions. Defensive patterns at lines 697, 721, 750, 765 prevent panic-triggering patterns. Any uncovered branch is a latent bug. Radix tree is the most fragile module. |
| mux.go (handler registry, middleware ordering) | 90%+ | 526 lines managing handler lifecycle. Panic-based guards at lines 273-274, 290-291, 417-419 prevent invalid registration. Missing coverage on the middleware-locking mechanism (lines 101-103) could allow middleware/route ordering confusion. Pool management (lines 449-485) is the second most fragile area. |
| context.go (request routing context, parameter stacking) | 90%+ | Context is reused from sync.Pool. Reset logic (lines 82-96) must fully initialize all fields. Cross-request leakage (extremely unlikely but catastrophic) happens if Reset misses a slice. RouteContext nil handling (line 27) gracefully degrades but silently masks errors. |
| middleware subpackage (Recoverer, Logger, Timeout, etc) | 85%+ | Each middleware adds a surface for bugs. Recoverer (panic recovery), Timeout (context deadline), Logger (I/O) each have specific risks. Less critical than core routing but production-facing. |
| Pattern validation (chi.go, parts of tree.go) | 95%+ | Input validation happens early. Invalid patterns must panic before routes are registered. Missing validation allows crash at runtime. Pattern parsing at tree.go:690-755 has 5+ validation checks; all must execute. |

## Coverage Theater Prevention

Fake tests to avoid:

1. **Mock-based tests that validate only mock behavior** — Testing that a middleware's next handler was called by checking a mock call count doesn't validate that chi actually wires the handler correctly. Add integration tests with real HTTP requests.

2. **Tests asserting "no panic" without valid routes** — A test creating a `chi.NewRouter()` and checking it doesn't panic validates only that the constructor works, not that routing behaves correctly.

3. **Parametrization without actual parameter extraction** — A test parameterizing a route like `GET /{id}` but never extracting `id` from the context doesn't verify the parameter system works end-to-end.

4. **Boundary tests using values outside the schema** — Testing with a pattern like `{id:999999999999}` where the app expects `{id:[0-9]+}` validates nothing about the actual system. Use schema-valid values.

5. **Tests checking tree state directly (node.endpoints)** — The tree structure is internal. Tests should verify behavior (routing works, parameter extraction works), not internal node structure.

6. **Regex validation without ReDoS risk** — A test that compiles `{id:[a-z]+}` and asserts no error doesn't validate that chi rejects `{id:(?:.*)*}`. The absence of ReDoS protection is a coverage gap, not validated by normal tests.

7. **Coverage percentage without scenario verification** — A CI report showing "85% coverage" is meaningless if those 85% are straightforward code paths. The hard-to-reach branches are where bugs hide (panic paths, method-not-allowed state transitions, pool cleanup).

## Fitness-to-Purpose Scenarios

### Scenario 1: Regex Denial of Service (ReDoS) in Route Patterns

**Requirement tag:** [Req: inferred — from tree.go lines 256, 449; regex matching without timeout protection]

**What happened:** Chi allows arbitrary regex patterns in route parameters via `{param:pattern}` syntax. The regex is compiled at route registration time (tree.go:256) and matched at request time (tree.go:449). If a user defines a malicious pattern like `{id:(?:.*)*}` (catastrophic backtracking), a single HTTP request with a long path component can hang the request thread indefinitely, causing denial of service. The pattern compiles without error. No timeout is applied to `regexp.MatchString()`. A 10,000-character path triggering catastrophic backtracking could hang a goroutine for seconds. In a server handling 1,000 requests/sec with GOMAXPROCS=4, a single ReDoS pattern could exhaust all worker threads within 4 seconds, making the service unresponsive to all requests.

**The requirement:** Chi must either (a) document that users are responsible for regex safety and verify patterns don't cause ReDoS, (b) apply a timeout or complexity limit to regex matching, or (c) provide a pattern validator that rejects high-complexity regexes. Currently chi does none. This is a gap in the architecture.

**How to verify:** The spec audit (RUN_SPEC_AUDIT.md) includes a ReDoS check: "Document the design decision on ReDoS. If chi assumes user responsibility, that assumption must be written in documentation and examples must show safe regex patterns. If chi defends against ReDoS, verify the implementation with boundary tests."

---

### Scenario 2: Context Leakage from Sync.Pool Reuse

**Requirement tag:** [Req: inferred — from context.go lines 82-96, mux.go lines 449-485; pool-based context reuse]

**What happened:** Chi reuses `*Context` objects from `sync.Pool` (mux.go:449-450). Each context is reset via `Reset()` (context.go:82-96), which truncates slices: `x.URLParams.Keys = x.URLParams.Keys[:0]`. If a request handler panics, the deferred pool return (mux.go:483-485) happens before Reset is called in the next request. In high-concurrency scenarios (100+ concurrent requests), if one request's context is not fully reset before reuse, URLParams from request A could bleed into request B. Example: Request A sets `URLParams.Keys = ["articleID", "userID"]`. If the pool returns this context mid-cleanup and request B (without URL params) grabs it from the pool, `Reset()` must clear both slices. If Reset misses one (e.g., a new field added later), request B would inherit request A's parameter keys. This is low-probability but catastrophic if it happens—request B executing with wrong parameters.

**The requirement:** All fields in Context must be explicitly reset in Reset() (verified line-by-line). The Reset() function must be called before context returns to pool OR the deferred return must happen after Reset (currently it does: mux.go:483 has "defer release(rctx)" where release resets). Tests must verify no cross-request leakage under concurrent load.

**How to verify:** Run `TestPooledContextConcurrency` (not currently written): 500 concurrent requests with different parameter counts, assert each request sees exactly the parameters it routed to, never another's parameters.

---

### Scenario 3: Panic-Based Error Handling Allows Untrusted Pattern Injection

**Requirement tag:** [Req: inferred — from tree.go lines 258, 697, 721, 750, 765; panic on invalid patterns]

**What happened:** Chi validates route patterns at registration time by panicking. Examples: duplicate parameter keys (tree.go:765-766), invalid regex (tree.go:258), wildcard in wrong position (tree.go:750). Panics are design-time safeguards—they force developers to fix patterns before deploying. However, if chi is used in a system where route patterns come from untrusted sources (user-uploaded route definitions, dynamic configuration, plugin systems), a malicious or malformed pattern could panic the server at runtime. A pattern like `{id:` (missing closing brace) panics at tree.go:721. In a service that loads routes from a user-editable config file without pre-validation, a typo or attack would crash the service. Other routers like gorilla/mux return errors; chi panics, making it less suitable for untrusted input.

**The requirement:** Either (a) document that route patterns MUST be trusted (hardcoded or loaded from version-controlled config, never user-supplied), or (b) provide a ValidatePattern() function that returns an error instead of panicking, allowing runtime validation. Option (a) is most likely correct for chi's use case, but it must be explicit.

**How to verify:** QUALITY.md must document this constraint. Spec audit checks: "Is the assumption (trusted patterns) documented?" If patterns can be user-supplied, verify try/catch around registration and graceful error handling.

---

### Scenario 4: Incorrect Method Routing Due to Integer Overflow in Bitflags

**Requirement tag:** [Req: inferred — from tree.go lines 62-72; bitflag method constants]

**What happened:** HTTP methods are stored as bitflags. Each new method gets a flag: mSTUB=1, mCONNECT=2, mDELETE=4, ..., up to 64+ flags on 64-bit systems. The code checks `len(methodMap) > strconv.IntSize-2` (tree.go:70) to prevent overflow. However, IntSize is 64 on 64-bit and 32 on 32-bit systems. If someone calls `RegisterMethod()` to add 60+ custom methods on a 32-bit system, the overflow check may not catch it early enough, and bitwise operations could wrap, causing method routing to silently mismatch. Example: on 32-bit, if flag bits wrap, `GET` request could match `POST` handler because their flags overlap. This is extremely unlikely (requires 62+ custom methods) but possible. The check exists, but the boundary is tight and platform-dependent.

**The requirement:** Verify that the method bitflag system safely handles the maximum number of methods on both 32-bit and 64-bit systems, OR document that chi supports only standard HTTP methods (GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD, CONNECT, TRACE, CUSTOM) and RegisterMethod is internal-only.

**How to verify:** Test on 32-bit and 64-bit systems (or in tests checking both cases) that adding methods up to the limit works, and exceeding the limit panics with a clear error, not silently failing. Verify no method bit collision.

---

### Scenario 5: Pattern Ordering Bugs in Radix Tree Insertion

**Requirement tag:** [Req: inferred — from tree.go lines 793-798, 240-270; node sorting and splitting]

**What happened:** Chi's radix tree uses a specific node ordering strategy: static nodes first (sorted lexicographically), then parameter nodes, then catchall. When routes are inserted in unusual orders, nodes may be split and re-ordered. The tailSort() function (tree.go:793-798) is complex and handles "tail" matching (parameters with matching suffix patterns). If a later route insertion causes a split that changes node order or regex, previously matched routes could be missed. Example: registering `/users/{id}` then `/users/admin` (both parameterized) might reorder nodes such that `/users/admin` matches as `{id}=admin` instead of the static `admin` node. This would route both to the parameter handler, losing the explicit admin-specific behavior. The tree structure is invisible at request time—a test would only catch this if it registered routes in the problematic order and verified behavior.

**The requirement:** All route insertion orders (static then param, param then static, overlapping static/param/regex/catchall patterns) must produce identical behavior: each pattern matches only its intended paths. No insertion order should change routing outcomes.

**How to verify:** TestRouteInsertionOrder: Register the same routes in permutations and verify routing behavior is identical. Include: static-param overlaps, param-regex overlaps, literal wildcard conflicts.

---

### Scenario 6: Middleware Ordering Lock Prevents Intended Routes

**Requirement tag:** [Req: formal — README "middlewares must be defined before routes"; panic at mux.go:101-103]

**What happened:** Chi enforces middleware-before-routes ordering by panicking if `Use()` is called after a route is registered. The check is `if mx.handler != nil` (mux.go:101-103), which fires when the first route handler is computed. However, `Use()` on subrouters created with `Route()` or `Group()` does NOT share the parent mux's handler state. A developer might register routes on the parent, then call `Route("/sub", ...)` and `Use(...)` on the subrouter, expecting the middleware to apply to sub-routes. This works (subrouter has its own check). But if they call `Use()` on the parent after calling `Route()`, it panics. This is by design, but the error message doesn't explain WHY the ordering matters (middleware sits outside the router handler, changing its timing and access). Developers unfamiliar with chi might think this is a arbitrary restriction and attempt to work around it.

**The requirement:** The panic message must explain that middlewares apply to the entire mux including all routes, and must be registered first. Alternatively, chi could decouple middleware registration from route registration by building middleware and route registration separately.

**How to verify:** Verify that the panic message at tree.go:101-103 is clear and references the README's explanation. Verify that subrouters created with Route() can have their own middlewares registered independently.

---

### Scenario 7: Cross-Request Parameter Collision in Nested Subrouters

**Requirement tag:** [Req: inferred — from context.go lines 45-79, 147-149; RouteParams with per-level and combined parameter stacking]

**What happened:** When routes are nested (e.g., `Mount("/api", subrouter)`), URL parameters are accumulated across levels. RouteParams.Keys and RouteParams.Values are parallel arrays. If a parent router extracts `{version}` and a child router extracts `{id}`, both are appended to the same URLParams (context.go:156-165). If an intermediate subrouter mishandles the path offset (RoutePath is shifted, context.go:141-144), a child router might read the wrong substring, extracting the parent's parameter value into the wrong key. Example: Parent matches `/api/{version}`, child matches `/{id}`. If child reads from the wrong offset, it might extract version-string where id should go. The replaceWildcards() function (context.go:140-144) uses string.ReplaceAll in a loop, which could produce unexpected results if path segments contain the replaceable substrings.

**The requirement:** Parameter stacking across subrouters must preserve parameter isolation. A child router must never extract parent parameters. Path offsets must be correctly maintained. Tests must verify parameter extraction in nested routers with multiple levels of nesting and overlapping parameter names.

**How to verify:** TestNestedRouterParameters: Mount subrouters 3+ levels deep, each with parameters, verify each router extracts only its own parameters and never sees sibling/parent parameters.

---

### Scenario 8: Empty Route Pattern Matches All Paths (Silent Configuration Bug)

**Requirement tag:** [Req: inferred — from mux.go:417-419 pattern validation; boundary condition on empty pattern]

**What happened:** Chi validates that route patterns start with `/` (mux.go:417-419) but doesn't explicitly reject empty patterns. An empty string `""` fails the length check (`len(pattern) == 0`), but what about a pattern that becomes empty after processing? A buggy middleware that strips context before subrouter matching might pass an empty remaining pattern. The catchall node (`/*`) is the closest valid empty pattern, and it matches everything. If configuration or routing logic accidentally creates an empty pattern without triggering the validation panic, it could become a catchall, routing all unmatched requests to an unexpected handler.

**The requirement:** Empty patterns must always panic with a clear error. The validation must be absolute, not relative to processing state. Tests must verify that only patterns starting with `/` and having content are accepted.

**How to verify:** TestEmptyPatternRejection: Verify that `chi.NewRouter().Get("", handler)` panics with a clear message about empty patterns.

---

### Scenario 9: Method Not Allowed (405) vs. Not Found (404) Mismatch

**Requirement tag:** [Req: formal — HTTP spec (RFC 7231) requires 405 for method-not-allowed; inferred from tree.go:468-478, mux.go:481-482]

**What happened:** When a route path exists but the HTTP method doesn't, chi should return 405 Method Not Allowed, not 404 Not Found. The routing logic detects this via `rctx.methodNotAllowed` flag (tree.go:468-478). However, if a handler is not found during the tree traversal (no matching path segment), the flag is never set, and 404 is returned. The issue is subtle: in some edge cases (e.g., static vs. param node ordering), a request might fail to match a static node but also not trigger the methodNotAllowed flag correctly. If the tree structure changes due to insertion order bugs (Scenario 5), the 404 vs. 405 distinction could be lost. The HTTP spec is clear: a request to `POST /users/123` where only `GET /users/123` exists MUST return 405, not 404.

**The requirement:** All paths that exist in any HTTP method must trigger 405 when an unsupported method is used. The methodNotAllowed flag must be set reliably regardless of how the tree is structured.

**How to verify:** TestMethodNotAllowedVsNotFound: Register routes with different methods (GET /users/123, POST /users/123), then request unsupported methods (DELETE, PATCH, PUT), verify 405 responses, never 404.

---

### Scenario 10: Regex Pattern Anchoring Allows Partial Matches

**Requirement tag:** [Req: inferred — from tree.go:449, regex matching without anchors]

**What happened:** Regex patterns in chi are matched using `rex.MatchString(xsearch[:p])` (tree.go:449), where `xsearch[:p]` is a substring of the current path segment. The regex is user-provided and may lack anchors (`^`, `$`). A pattern like `{id:123}` (matching the string "123") is compiled as the regex "123" and matched with `MatchString`. This correctly matches "123" anywhere in the segment. However, a pattern intended to match full segments (e.g., `{id:^[0-9]{3}$}`) must have anchors—without them, the regex matches partial segments, causing unintended routes to match. Example: A pattern `{id:17}` (regex for digits 17-99) without anchors would match `/users/217-approved`, extracting "17" as the id and leaving "-approved" for the next segment. The current implementation correctly passes only a segment (xsearch[:p]), but the lack of explicit anchoring advice in documentation could lead developers to write partial-match regexes. A test using a non-anchored regex would reveal this, but the behavior is correct if the developer intended partial matching.

**The requirement:** Documentation must clarify regex behavior. If regexes are meant to match full segments, documentation should recommend anchors. The implementation itself is correct; the risk is developer misunderstanding.

**How to verify:** Spec audit (RUN_SPEC_AUDIT.md) includes documentation review: "Check that regex pattern guidance is in README or examples."

---

## AI Session Quality Discipline

1. **Read QUALITY.md before starting work** — Every session begins by understanding chi's fitness requirements and known risks.
2. **Run the full test suite before marking work complete** — `go test ./...` must pass with zero failures.
3. **Add tests for new functionality** — If a defensive pattern is added or modified, add a regression test in `quality/test_functional.go`.
4. **Update QUALITY.md if new failure modes are discovered** — Real incidents trump inferred scenarios. Document them.
5. **Never remove a fitness scenario** — Scenarios record why certain code exists. Removing a scenario means forgetting the lesson.
6. **Verify no panic-based errors leak to production** — All panics must be design-time guards (route registration), never runtime (request handling).

## The Human Gate

1. **ReDoS Risk Assessment** — Decide: does chi assume user responsibility for regex safety (document it), or does chi add complexity to defend against ReDoS? This is an architectural choice requiring human judgment.
2. **Untrusted Pattern Input** — If chi is used in a system where route patterns come from untrusted sources, provide SafeRegisterRoute() or ValidatePattern() functions that return errors instead of panicking.
3. **Performance Trade-offs** — Some scenarios (cross-request isolation, regex timeout limits) add overhead. Verify these are acceptable for chi's use case.
4. **Documentation Accuracy** — README and examples must match implementation. Spot-check that statements about middleware ordering, method routing, and parameter stacking are accurate.
