# Integration Test Protocol: chi

## Working Directory

All commands in this protocol use **relative paths from the project root.** Run everything from the directory containing `go.mod`. Do not `cd` to an absolute path.

## Safety Constraints

- DO NOT modify source code
- DO NOT delete files
- ONLY create files in the test results directory
- If something fails, record it and move on — DO NOT fix it

## Pre-Flight Check

Before running integration tests, verify:
- [ ] Go installed: `go version` (requires Go 1.23+, per go.mod)
- [ ] Dependencies resolved: `go mod download`
- [ ] Existing tests pass: `go test ./... -count=1`
- [ ] No race conditions in existing tests: `go test -race ./... -count=1`

If any check fails, STOP and report what's missing. Do not skip tests silently.

## Project Type

**Type:** Go HTTP router library (not a service — no external dependencies)
**External Dependencies:** None (stdlib only)
**Test Axes:** route pattern type × HTTP method × middleware stack × concurrency level

## Test Matrix

| # | Test | What It Exercises | Method | Pass Criteria |
|---|------|-------------------|--------|---------------|
| 1 | Static route routing | Basic GET/POST to static paths | `go test -run TestInteg_StaticRoutes` | All methods return correct handler response, correct status codes |
| 2 | Parameterized route routing | Named params `{id}`, regex `{id:[0-9]+}`, wildcard `*` | `go test -run TestInteg_ParamRoutes` | URLParam returns correct values, regex rejects non-matching |
| 3 | Middleware chain ordering | 3-middleware stack with request/response modification | `go test -run TestInteg_MiddlewareOrder` | Middlewares execute in declared order, response reflects all modifications |
| 4 | Subrouter mounting (3 levels) | Mount nested routers, verify path consumption | `go test -run TestInteg_NestedMount` | Each level receives correct path segment, URL params propagate |
| 5 | Concurrent request handling | 100 concurrent requests to parameterized routes | `go test -race -run TestInteg_Concurrent` | Zero data races, each response contains its own parameters |
| 6 | 404 and 405 handling | Unmatched paths and wrong methods | `go test -run TestInteg_ErrorHandling` | 404 for unknown paths, 405 with Allow header for wrong method |
| 7 | Custom error handlers | NotFound and MethodNotAllowed overrides | `go test -run TestInteg_CustomErrors` | Custom handler response body returned |
| 8 | Full middleware stack | Recoverer + Logger + RealIP + custom middleware | `go test -run TestInteg_FullStack` | Panic recovery works, request ID generated, IP extracted |
| 9 | Route pattern traversal | Routes() returns all registered patterns | `go test -run TestInteg_RouteTraversal` | Route count matches registered count, patterns are correct |

## Setup and Teardown

### Setup
```bash
# No external services required — chi is a stdlib-only library
go mod download
go build ./...
```

### Teardown
```bash
# Remove test results
rm -f quality/results/*.md
```

## Execution

### Parallelism Groups

```bash
# Group 1 (parallel — independent tests, no shared state)
go test -v -run "TestInteg_StaticRoutes|TestInteg_ParamRoutes|TestInteg_ErrorHandling" ./... &
go test -v -run "TestInteg_MiddlewareOrder|TestInteg_CustomErrors|TestInteg_RouteTraversal" ./... &
wait

# Group 2 (sequential — race detector requires exclusive execution)
go test -race -v -run "TestInteg_Concurrent" ./... -count=1
go test -race -v -run "TestInteg_FullStack" ./... -count=1
go test -race -v -run "TestInteg_NestedMount" ./... -count=1
```

**Note:** Commands assume POSIX-compatible shell. For Windows without WSL, run each command sequentially.

## Field Reference Table

### Core: HTTP Response
| Field | Type | Constraints |
|-------|------|-------------|
| `StatusCode` | int | 200 for success, 404 for not found, 405 for method not allowed |
| `Body` | []byte | Handler-specific response content |
| `Header("Allow")` | string | Present on 405 responses, comma-separated method list |
| `Header("Content-Type")` | string | Set by handler or middleware |

### Core: RouteContext
| Field | Type | Constraints |
|-------|------|-------------|
| `URLParams.Keys` | []string | Parameter names from route pattern |
| `URLParams.Values` | []string | Corresponding parameter values from request path |
| `RoutePath` | string | Remaining path for subrouter routing |
| `RouteMethod` | string | HTTP method for routing (may override request method) |
| `RoutePatterns` | []string | Pattern stack across subrouter hierarchy |
| `methodNotAllowed` | bool | True when path matches but method doesn't |
| `methodsAllowed` | []methodTyp | Methods that do match the path |

### Middleware: Throttle
| Field | Type | Constraints |
|-------|------|-------------|
| `Limit` | int | Must be > 0, panics otherwise |
| `BacklogLimit` | int | Must be >= 0, panics on negative |
| `BacklogTimeout` | time.Duration | Default 60s |
| `StatusCode` | int | Default 429 (TooManyRequests) |

## Quality Gates

1. **Route correctness:** Every parameterized route returns the exact URL parameter value from the request path — character-for-character match, not just non-empty.
2. **Middleware ordering:** When 3 middlewares append "A", "B", "C" to a header, the final header value is "A,B,C" in declaration order.
3. **Concurrency safety:** `go test -race` produces zero DATA RACE warnings across 100 concurrent requests.
4. **Error disambiguation:** POST to a GET-only route returns 405 (not 404), and the Allow header contains "GET".
5. **Subrouter isolation:** A URL parameter set at mount level 1 is still accessible at mount level 3 via `URLParam()`.
6. **Panic recovery:** A panicking handler behind Recoverer middleware returns 500, not connection reset.
7. **Pattern completeness:** `Routes()` returns entries for every registered route pattern including mounted subrouter routes.

## Post-Run Verification

For each test run, verify at these levels:
1. **Process:** `go test` exits with code 0, no panics in output
2. **Race:** `go test -race` reports no data races
3. **Coverage:** Each test exercises the code path it claims to (check with `-coverprofile`)
4. **Correctness:** Response bodies contain exact expected values, not just non-empty strings
5. **Edge cases:** Empty paths, root paths, trailing slashes all handled correctly

## Execution UX (How to Present When Running This Protocol)

### Phase 1: The Plan
Before running anything, show what's about to happen:

| # | Test | What It Checks | Est. Time |
|---|------|---------------|-----------|
| 1 | Static routes | Basic routing correctness | ~2s |
| 2 | Param routes | URL parameter extraction | ~2s |
| 3 | Middleware order | Chain composition | ~2s |
| 4 | Nested mount | Subrouter path consumption | ~3s |
| 5 | Concurrent | Race condition safety | ~5s |
| 6 | Error handling | 404/405 disambiguation | ~2s |
| 7 | Custom errors | Handler overrides | ~2s |
| 8 | Full stack | Complete middleware chain | ~3s |
| 9 | Route traversal | Pattern enumeration | ~2s |

**Total:** 9 tests, estimated ~25 seconds

### Phase 2: Progress
One-line status updates as each test runs:
```
✓ Test 1: Static routes — PASS (1.2s)
✓ Test 2: Param routes — PASS (0.8s)
✗ Test 3: Middleware order — FAIL: wrong execution order
⧗ Test 4: Nested mount... running
```

### Phase 3: Results
Summary table with recommendation:

| # | Test | Result | Time | Notes |
|---|------|--------|------|-------|
| 1 | Static routes | ✓ PASS | 1.2s | |
| ... | ... | ... | ... | |

**Passed:** N/9 | **Failed:** K/9
**Recommendation:** SHIP IT / FIX FIRST / NEEDS INVESTIGATION

## Reporting

Save to `quality/results/YYYY-MM-DD-integration.md`
