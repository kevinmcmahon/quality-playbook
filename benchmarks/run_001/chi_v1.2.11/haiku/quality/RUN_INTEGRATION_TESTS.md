# Integration Test Protocol: Chi Router

Integration tests validate chi's behavior in realistic scenarios: HTTP request flow, middleware chaining, subrouter composition, and performance under load. Unlike unit tests, these exercise the full request/response cycle.

## Test Architecture

**Working Directory:** Run all commands from the chi repo root (`/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/`).

**Test Groups:**

1. **HTTP Request Flow** — Basic routing, method matching, parameter extraction
2. **Middleware Chaining** — Middleware ordering, context propagation, panic recovery
3. **Subrouter Composition** — Mounted routers, nested groups, parameter accumulation
4. **Boundary Conditions** — Empty paths, special characters, edge cases
5. **Performance & Concurrency** — Concurrent requests, memory leaks, throughput
6. **Error Handling** — 404 vs 405, custom error handlers, panic recovery

## Test Matrix

| Group | Scenario | Input | Expected Output | Verification |
|-------|----------|-------|-----------------|---------------|
| HTTP Request Flow | GET /users | HTTP GET request | 200 OK, response body | Status code + body content |
| HTTP Request Flow | POST /users | HTTP POST with JSON | 200 OK, created | Status code + resource created in response |
| HTTP Request Flow | GET /users/123 | Path parameter | 200 OK, user 123 | URLParam("id") == "123" |
| HTTP Request Flow | GET /posts/{year}-{month}-{day} | Multi-param extraction | 200 OK, date correct | All 3 params extracted correctly |
| HTTP Request Flow | GET /articles/{id:[0-9]+} | Regex constraint | 200 if digits, 404 if alpha | Correct status based on pattern match |
| Middleware Chaining | GET /test with MW1→MW2 | HTTP GET | MW1(MW2(handler)) execution order | Execution log shows MW1→MW2→handler→MW2→MW1 |
| Middleware Chaining | GET /protected with panic | Handler panics | Recoverer middleware catches | Status 500, error logged, no goroutine leak |
| Middleware Chaining | GET /api with context | Middleware injects context | Handler reads context | Value present in handler context |
| Subrouter Composition | GET /api/v1/users | Mounted subrouter | 200, api response | Mounted handler executed |
| Subrouter Composition | GET /api/v2/users | Mounted subrouter v2 | 200, api v2 response | Different subrouter, different response |
| Subrouter Composition | GET /api/users/{id}/posts/{pid} | Nested params | 200, all params extracted | version + id + pid all present |
| Boundary Conditions | GET /files/* | Wildcard catch-all | 200, path captured | URLParam("*") contains full subpath |
| Boundary Conditions | GET /files/a/b/c | Deep wildcard | 200, "a/b/c" captured | Slashes preserved in wildcard |
| Boundary Conditions | GET / | Root path | 200 if registered, 404 if not | Exact match for root |
| Performance & Concurrency | 1000 concurrent GET /users/{id} | 1000 parallel reqs | All 200, all correct params | No param mixing, correct extraction for each |
| Error Handling | DELETE /users/123 (only GET exists) | Method not allowed | 405 Method Not Allowed | Status 405, not 404 |
| Error Handling | GET /undefined | Route not found | 404 Not Found | Status 404 |

## Setup Instructions

### 1. Create Test Server (SKIP if using Go test server)

Go's `httptest.Server` handles setup/teardown automatically. No external server needed.

### 2. Build Chi

```bash
cd /sessions/quirky-practical-cerf/mnt/QPB/repos/chi/
go build ./...
```

Verify no build errors. Output should be silent (no errors).

### 3. Run Functional Tests

Chi's existing tests + new functional tests validate routing behavior.

```bash
go test -v -run TestBasic
go test -v -run TestURL
go test -v -run TestRegex
go test -v -run TestCatchAll
go test -v -run TestMiddleware
go test -v -run TestNotFound
go test -v -run TestMethodNotAllowed
go test -v -run TestContext
go test -v -run TestMount
go test -v -run TestRoute
```

Expected: All tests pass (0 failures, 0 errors).

## Integration Test Execution

### Group 1: HTTP Request Flow (10 tests)

**Run:**
```bash
go test ./... -v -run "TestBasicRouting|TestURLParameters|TestRegexParameters|TestCatchAll|TestNotFoundHandler|TestMethodNotAllowedHandler|TestURLParamOnMultipleMatches|TestWildcardEmptySegment|TestRoutePatternConstruction" -timeout 30s
```

**Quality Gates (all must pass):**

1. **TestBasicRouting:** Verifies status 200 + correct body for GET, POST, PUT, DELETE
   - Assertion: `w.Code == 200 && w.Body.String() contains expected method`
   - Pass threshold: All 4 methods return expected response

2. **TestURLParameters:** Verifies parameter extraction
   - Assertion: `chi.URLParam(r, "id") == "42"` and multi-param extraction works
   - Pass threshold: 100% of tested parameters extracted correctly

3. **TestRegexParameters:** Verifies regex pattern constraints
   - Assertion: `[0-9]+ pattern matches only digits`, `[a-z-]+ rejects underscore`
   - Pass threshold: Pattern matching is precise (false positives == failure)

4. **TestCatchAll:** Verifies wildcard matching
   - Assertion: `/files/*` captures subpaths including slashes
   - Pass threshold: All test paths captured correctly

5. **TestNotFoundHandler:** Verifies 404 for undefined routes
   - Assertion: `w.Code == 404`
   - Pass threshold: Exactly 404, not 200 or 500

6. **TestMethodNotAllowedHandler:** Verifies 405 for method not allowed
   - Assertion: `w.Code == 405`
   - Pass threshold: Exactly 405, not 404 or 200

7. **TestURLParamOnMultipleMatches:** Verifies multi-param extraction
   - Assertion: `/2025/03/31` extracts as year=2025, month=03, day=31
   - Pass threshold: All three parameters correct

8. **TestWildcardEmptySegment:** Verifies wildcard matches empty segment
   - Assertion: `/files/` captures empty string as path
   - Pass threshold: URLParam("*") == ""

9. **TestRoutePatternConstruction:** Verifies RoutePattern()
   - Assertion: `chi.RoutePattern(r) == "/users/{id}"`
   - Pass threshold: Pattern matches registration pattern exactly

**Expected Outcome:** 9 tests pass (0 failures)

### Group 2: Middleware Chaining (5 tests)

**Run:**
```bash
go test ./... -v -run "TestMiddlewareExecution|TestMiddlewareStackOrder|TestGroupMiddlewareAppliedToGroup|TestWithMiddlewareInlineApplication|TestRequestContext" -timeout 30s
```

**Quality Gates:**

1. **TestMiddlewareExecution:** Verifies middleware wraps handler correctly
   - Assertion: Middleware stack executes in order (mw1-in → mw2-in → handler → mw2-out → mw1-out)
   - Pass threshold: Exact execution order

2. **TestMiddlewareStackOrder:** Verifies registration order = execution order
   - Assertion: Two middlewares registered in order execute in that order
   - Pass threshold: Execution matches registration order

3. **TestGroupMiddlewareAppliedToGroup:** Verifies Route() middlewares apply only to group
   - Assertion: Middleware on `/admin` group applies to `/admin/dashboard`, not `/public`
   - Pass threshold: Scoped middleware doesn't leak to other routes

4. **TestWithMiddlewareInlineApplication:** Verifies With() applies to specific routes
   - Assertion: `With(mw).Get("/protected")` applies mw only to /protected
   - Pass threshold: Inline middleware is scoped

5. **TestRequestContext:** Verifies context propagation
   - Assertion: Value injected in middleware is available in handler
   - Pass threshold: Context value flows through entire chain

**Expected Outcome:** 5 tests pass (0 failures)

### Group 3: Subrouter Composition (4 tests)

**Run:**
```bash
go test ./... -v -run "TestSubrouterMounting|TestRouteGrouping|TestSubrouterParameterAccumulation|TestScenario9NestedRouterParameterIsolation" -timeout 30s
```

**Quality Gates:**

1. **TestSubrouterMounting:** Verifies Mount() composes routers
   - Assertion: Routes on parent and mounted subrouter both accessible
   - Pass threshold: Both `/health` and `/api/status` return correct responses

2. **TestRouteGrouping:** Verifies Route() for nested groups
   - Assertion: Routes within Route() group are accessible with full path
   - Pass threshold: `/api/users` and `/api/posts/` both work

3. **TestSubrouterParameterAccumulation:** Verifies params accumulate across levels
   - Assertion: Nested routers all parameters present: `version + userID + postID`
   - Pass threshold: All three parameters extracted correctly

4. **TestScenario9NestedRouterParameterIsolation:** Verifies parameter isolation
   - Assertion: Parameters from different nesting levels don't collide
   - Pass threshold: Each request sees only its own parameters

**Expected Outcome:** 4 tests pass (0 failures)

### Group 4: Boundary Conditions (7 tests)

**Run:**
```bash
go test ./... -v -run "TestEmptyRouterNilHandler|TestPatternMustStartWithSlash|TestWildcardEmptySegment|TestMultipleWildcardsRejected|TestRegexSpecialCharactersInPatternNames|TestURLParamOnMultipleMatches|TestScenario10RegexAnchoringBehavior" -timeout 30s
```

**Quality Gates:**

1. **TestEmptyRouterNilHandler:** Verifies empty router returns 404
   - Assertion: `http.StatusNotFound` on any request to empty router
   - Pass threshold: Exactly 404

2. **TestPatternMustStartWithSlash:** Verifies pattern validation
   - Assertion: `Get("users", ...)` panics (no leading /)
   - Pass threshold: Panic occurs at registration time

3. **TestWildcardEmptySegment:** Verifies wildcard matches empty
   - Assertion: `/files/` captures empty string
   - Pass threshold: URLParam("*") == ""

4. **TestMultipleWildcardsRejected:** Verifies no multiple wildcards
   - Assertion: `/files/*/more/*` panics at registration
   - Pass threshold: Panic occurs

5. **TestRegexSpecialCharactersInPatternNames:** Verifies param names with underscores/hyphens
   - Assertion: `{user_id}` and `{post-id}` both work
   - Pass threshold: Parameters extracted with special char names

6. **TestURLParamOnMultipleMatches:** Verifies correct extraction with multiple params
   - Assertion: `/{year}/{month}/{day}` extracts all three correctly
   - Pass threshold: year=2025, month=03, day=31

7. **TestScenario10RegexAnchoringBehavior:** Verifies regex precision
   - Assertion: `{id:[0-9]{3}}` matches only 3 digits, not 2 or 4
   - Pass threshold: Exact regex matching

**Expected Outcome:** 7 tests pass (0 failures)

### Group 5: Error Handling (3 tests)

**Run:**
```bash
go test ./... -v -run "TestScenario4MethodNotAllowedCorrectly|TestEmptyRouterNilHandler|TestMethodNotAllowedHandler" -timeout 30s
```

**Quality Gates:**

1. **TestScenario4MethodNotAllowedCorrectly:** Verifies 405 vs 404 distinction
   - Assertion: Path exists with GET → DELETE returns 405 (not 404)
   - Assertion: Path doesn't exist → returns 404 (not 405)
   - Pass threshold: Clear distinction between the two error types

2. **TestEmptyRouterNilHandler:** Verifies 404 when no routes registered
   - Assertion: `http.StatusNotFound`
   - Pass threshold: Exactly 404

3. **TestMethodNotAllowedHandler:** Verifies correct Allow header (if applicable)
   - Assertion: DELETE on GET-only route returns 405
   - Pass threshold: Status 405

**Expected Outcome:** 3 tests pass (0 failures)

### Group 6: Concurrency & Performance (1 test)

**Run:**
```bash
go test ./... -v -run "TestScenario6ConcurrentParameterExtraction" -timeout 30s
```

**Quality Gates:**

1. **TestScenario6ConcurrentParameterExtraction:** Verifies no parameter mixing under concurrency
   - Setup: 10 concurrent requests, each with unique parameters
   - Assertion: Each request extracts exactly its own parameters, never another's
   - Pass threshold: All 10 requests return correct results, no mixing

**Expected Outcome:** 1 test passes (0 failures, 0 goroutine leaks)

## Panic Safety Tests

The following tests verify panic handling:

```bash
go test ./... -v -run "Scenario1|Scenario2|Scenario3" -timeout 30s
```

Each test should panic at registration time with a clear error message (none at request time).

**Expected Outcome:** Panics occur at registration, not request handling.

## Summary & Quality Gate Assessment

After all test groups pass, generate a summary:

```
Integration Test Results:
========================
Group 1 (HTTP Request Flow): 9/9 ✓
Group 2 (Middleware Chaining): 5/5 ✓
Group 3 (Subrouter Composition): 4/4 ✓
Group 4 (Boundary Conditions): 7/7 ✓
Group 5 (Error Handling): 3/3 ✓
Group 6 (Concurrency): 1/1 ✓
────────────────────────
TOTAL: 29/29 PASSED

Quality Gates: ALL PASSING
- No 404/405 confusion ✓
- Parameter extraction correct ✓
- Middleware ordering correct ✓
- Subrouter isolation correct ✓
- Panic at registration, not request ✓
- Concurrency safe ✓
```

## When Tests Fail

If any test fails:

1. **Run with verbose output:** `go test -v` to see assertion failures
2. **Check stderr for panics:** Panics should occur at registration, not request handling
3. **Investigate the failure:** Use `t.Logf()` to trace execution
4. **Document in QUALITY.md:** If failure reveals a new scenario, add it
5. **Add regression test:** Ensure the bug doesn't re-occur

## Execution Timeline

- **Group 1:** ~5 seconds
- **Group 2:** ~3 seconds
- **Group 3:** ~3 seconds
- **Group 4:** ~4 seconds
- **Group 5:** ~2 seconds
- **Group 6:** ~10 seconds (concurrency)

**Total:** ~30 seconds

**Recommendation:** Run all groups in parallel if CI supports it:
```bash
go test ./... -v -timeout 30s
```
