# Integration Test Protocol: chi

## Working Directory

All commands in this protocol use **relative paths from the project root.** Run everything from the directory containing `go.mod`. Do not `cd` to an absolute path.

## Safety Constraints

- DO NOT modify source code
- DO NOT delete files
- ONLY create files in the test results directory (`quality/results/`)
- If something fails, record it and move on — DO NOT fix it

## Pre-Flight Check

Before running integration tests, verify:
- [ ] Go 1.23+ installed: `go version`
- [ ] Module is valid: `go mod verify`
- [ ] Existing tests pass: `go test ./... -count=1 -timeout 120s`
- [ ] No build errors: `go build ./...`

If any check fails, STOP and report what's missing. Do not skip tests silently when dependencies are unavailable.

## Test Matrix

Chi is a **library** (HTTP router), not a service. Integration tests exercise chi as a component within HTTP servers, testing the full request lifecycle from incoming HTTP request through middleware chain, radix trie matching, URL parameter extraction, handler execution, and response writing.

| # | Test Group | What It Exercises | Method | Pass Criteria |
|---|-----------|-------------------|--------|---------------|
| 1 | Basic routing, all methods | Route registration + request matching for GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, CONNECT, TRACE | `httptest.Server` with chi router | Each method returns 200 with correct handler output |
| 2 | URL parameter extraction | Named params, regexp params, catch-all wildcards across 1-3 nesting levels | Nested `Mount()` + `Route()` with `httptest` | `URLParam()` returns correct value at each nesting level |
| 3 | Middleware chain ordering | 3+ middleware functions with side effects (header injection, context values) | Sequential middleware with observable mutations | Headers and context values present in correct order |
| 4 | Sub-router mounting | `Mount()` with nested routers sharing NotFound/MethodNotAllowed handlers | 3-level deep mounted sub-routers with `httptest` | Custom 404/405 handlers invoked correctly at each level |
| 5 | Concurrent requests | 100+ parallel requests to different routes and same routes | `sync.WaitGroup` + goroutines with `httptest` | All requests return correct responses, no data races |
| 6 | Route pattern matching edge cases | Overlapping prefixes, regexp patterns, trailing slashes, wildcard vs static precedence | `httptest` with carefully ordered route registrations | Each path resolves to the expected handler |
| 7 | Context pool stress test | Rapid request cycling to verify sync.Pool reuse correctness | 1000 sequential requests checking URL params | No stale params from previous requests |
| 8 | 405 Method Not Allowed | Request with wrong method to routes that have specific method handlers | `httptest` with method-specific routes | 405 status, Allow header lists correct methods |
| 9 | Custom middleware with chi.With() | Inline middleware applied to specific routes via `With()` | `httptest` with With()-scoped middleware | Middleware runs only for targeted routes |

## Field Reference Table

Chi is a Go library with no external schemas. The "fields" are HTTP response properties:

### HTTP Response Properties
| Field | Type | Constraints |
|-------|------|-------------|
| `response.StatusCode` | int | 200 for matched routes, 404 for unmatched, 405 for wrong method |
| `response.Body` | string | Handler-specific output, must match registered handler's write |
| `response.Header["Allow"]` | string | Present on 405 responses, comma-separated list of valid methods |
| `chi.URLParam(r, key)` | string | Extracted URL parameter, must match path segment |
| `chi.RouteContext(ctx).RoutePattern()` | string | Collapsed pattern string, wildcards removed from interior |

### URL Parameter Properties (from chi.Context)
| Field | Type | Constraints |
|-------|------|-------------|
| `URLParams.Keys` | []string | Parameter names in registration order |
| `URLParams.Values` | []string | Corresponding parameter values from URL, same length as Keys |
| `routePattern` | string | Full matched pattern, e.g., `/api/{version}/users/{id}` |
| `methodNotAllowed` | bool | True when path matches but method doesn't |
| `methodsAllowed` | []methodTyp | Bit flags for allowed methods on matched path |

## Setup and Teardown

### Setup
Chi is a pure Go library with zero external dependencies. No infrastructure needed.
```bash
go mod verify
go build ./...
```

### Teardown
No teardown needed — `httptest.Server` instances are closed with `defer ts.Close()` in each test.

## Execution

### Parallelism Groups

```bash
# Group 1 (parallel — independent test groups)
go test -v -run "TestIntegration_BasicRouting" -count=1 &
go test -v -run "TestIntegration_URLParams" -count=1 &
go test -v -run "TestIntegration_MiddlewareChain" -count=1 &
wait

# Group 2 (parallel — independent test groups)
go test -v -run "TestIntegration_SubRouterMount" -count=1 &
go test -v -run "TestIntegration_RouteEdgeCases" -count=1 &
go test -v -run "TestIntegration_MethodNotAllowed" -count=1 &
wait

# Group 3 (sequential — stress tests)
go test -v -run "TestIntegration_ConcurrentRequests" -count=1 -race
go test -v -run "TestIntegration_ContextPoolStress" -count=1 -race
```

## Quality Gates

1. **Routing correctness:** Every registered route returns the expected handler's output body, not another handler's output
2. **Parameter accuracy:** `URLParam()` returns the exact path segment for each named parameter, not a stale or shifted value
3. **Middleware ordering:** Side effects from middleware appear in registration order (first registered = first executed)
4. **405 compliance:** Wrong-method requests return 405 (not 404), and the Allow header lists all registered methods for that pattern
5. **Concurrency safety:** With `-race` flag, zero data race detections across 100+ concurrent requests
6. **Pool correctness:** After 1000 sequential requests, no request sees URL parameters from a previous request

## Post-Run Verification

For each test run, verify at these levels:
1. **Process:** `go test` exits with code 0, no panics in output
2. **State:** All test assertions passed (no `FAIL` in output)
3. **Data:** Response bodies contain expected handler outputs, not empty or wrong-handler outputs
4. **Content:** URL parameters extracted from responses match the path segments in the request URL
5. **Domain:** Allow headers on 405 responses list exactly the methods registered for that route pattern
6. **Resource:** No goroutine leaks (use `-count=1` to prevent test caching masking leaks)

## Execution UX (How to Present When Running This Protocol)

### Phase 1: The Plan
Before running anything, show what's about to happen:

| # | Test | What It Checks | Est. Time |
|---|------|---------------|-----------|
| 1 | Basic routing | All HTTP methods route correctly | ~2s |
| 2 | URL params | Named, regexp, catch-all params | ~2s |
| 3 | Middleware chain | Execution order correctness | ~1s |
| 4 | Sub-router mount | Handler propagation, path trimming | ~2s |
| 5 | Concurrent requests | Race condition safety | ~5s |
| 6 | Route edge cases | Prefix overlap, trailing slashes | ~2s |
| 7 | Context pool stress | sync.Pool reuse correctness | ~3s |
| 8 | 405 handling | Method Not Allowed + Allow header | ~1s |
| 9 | With() middleware | Inline middleware scoping | ~1s |

**Total:** 9 tests, estimated ~20 seconds

### Phase 2: Progress
```
✓ Test 1: Basic routing — PASS (1.8s)
✓ Test 2: URL params — PASS (2.1s)
✗ Test 3: Middleware chain — FAIL: wrong header order
⧗ Test 4: Sub-router mount... running
```

### Phase 3: Results
Summary table with recommendation:

| # | Test | Result | Time | Notes |
|---|------|--------|------|-------|
| 1 | Basic routing | ✓ PASS | 1.8s | |
| ... | | | | |

**Passed:** N/9 | **Failed:** K/9
**Recommendation:** SHIP IT / FIX FIRST / NEEDS INVESTIGATION

## Reporting

Save to `quality/results/YYYY-MM-DD-integration.md`
