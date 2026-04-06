# Integration Test Protocol: chi

## Working Directory

All commands in this protocol use **relative paths from the chi module root** (the directory containing `go.mod`). Run everything from that directory. Do not `cd` to an absolute path.

```
# Chi module root — all commands run from here:
# /path/to/chi/   (wherever you cloned go-chi/chi)
```

## Project Type and Dependencies

**Project type:** Go HTTP router library — no external service dependencies. Chi is a pure Go library with zero external package dependencies (only Go stdlib). Integration tests exercise the router end-to-end with real HTTP requests through `net/http/httptest`.

**External dependencies:** None. Tests are fully self-contained.

**Test axes:**
1. Route type × HTTP method (static, named param, regexp, wildcard × GET/POST/PUT/DELETE/...)
2. Middleware composition × scope (global, group, inline, subrouter-inherited)
3. Pattern edge cases × routing outcome (match, not-found, method-not-allowed)
4. Concurrent request handling × context pool safety
5. Custom error handlers × propagation scope (root → subrouter)

## Pre-Flight Check

Before running tests, verify the environment:

```bash
# Verify Go version (requires 1.23+)
go version

# Verify the chi module resolves
go list ./...

# Run the built-in test suite to establish baseline
go test ./... -count=1 -timeout 60s
```

If `go test ./...` fails before you've made any changes, there is a pre-existing issue. Do not proceed until the baseline is clean.

**Expected baseline output:**
```
ok  	github.com/go-chi/chi/v5	(some time)
ok  	github.com/go-chi/chi/v5/middleware	(some time)
```

## Execution UX

When an agent runs this protocol, follow three phases:

**Phase 1 — Pre-run preview:** Before executing any tests, print the list of test groups about to run:
```
About to run:
  [1] Core router integration tests (go test ./... -run TestIntegration)
  [2] Middleware integration tests (go test ./middleware/... -run TestIntegration)
  [3] Concurrent routing safety (go test -race ./... -run TestConcurrent)
  [4] Existing test suite (go test ./... -count=1)
Continue? [y/N]
```

**Phase 2 — Progress updates:** One line per test group as it completes:
```
✓ Core router integration (0.3s, 12 passed)
✗ Middleware integration (FAILED — see output)
⧗ Concurrent routing safety (running...)
```

**Phase 3 — Summary:** After all groups complete, print the summary table (see Post-Run Verification section).

## Test Groups

### Group 1: Core Router Integration

Exercises the complete routing lifecycle: route registration → HTTP request → handler execution → response. Run from the chi module root.

```bash
go test -v -run "TestMux|TestRouter|TestRoute" ./... -count=1 -timeout 30s
```

**Pass criteria:**
- All tests pass (0 failures, 0 errors)
- Each test that checks a status code asserts the exact value (200, 404, 405)
- URLParam assertions check the actual parameter value, not just non-empty

**Quality gates:**
| Behavior | Expected Result |
|----------|----------------|
| GET /static | 200 with correct body |
| GET /users/{id} | 200, URLParam("id") == request value |
| GET /users/abc (regexp `\d+`) | 404 |
| POST to GET-only route | 405 with Allow header containing "GET" |
| GET to unregistered path | 404 |
| Wildcard /files/* | 200, wildcard captures everything after /files/ |

---

### Group 2: Middleware Integration

Exercises middleware composition: stack order, group isolation, inline (With), subrouter inheritance.

```bash
go test -v -run "TestMiddleware|TestUse|TestWith|TestGroup|TestChain" ./... -count=1 -timeout 30s
```

**Pass criteria:**
- Middleware executes in registration order (first Use() call = outermost, executes first)
- Group middleware does NOT fire for routes outside the group
- With() middleware fires only for its specific endpoint
- Subrouter inherits parent NotFound handler when none is set

**Quality gates — Middleware Field Reference Table:**

| Behavior | Assertion |
|----------|-----------|
| Middleware order | Execution order matches `Use()` order (index 0 first) |
| Group isolation | Group middleware counter == 0 for non-group routes |
| With() isolation | Inline middleware counter == 0 for non-With() routes |
| NotFound propagation | Custom NotFound fires for subrouter 404s when subrouter has no custom handler |
| MethodNotAllowed propagation | Custom MethodNotAllowed fires for subrouter 405s when subrouter has no custom handler |

---

### Group 3: Concurrent Request Safety

Exercises the `sync.Pool` context reuse under concurrent load. This test runs with the race detector enabled.

```bash
go test -v -race -run "TestMuxBasic|TestConcurrent" ./... -count=1 -timeout 60s
```

**Pass criteria:**
- Race detector reports no data races
- All concurrent requests receive correct responses (no cross-request param leakage)

**Why this matters:** chi reuses `*Context` objects from a `sync.Pool`. If `Reset()` misses any field, or if `ServeHTTP` has a race between putting context back to the pool and a handler still reading it, the race detector will catch it.

**Quality gates:**
| Behavior | Expected Result |
|----------|----------------|
| 100 concurrent GET /users/{id} requests | All responses contain correct id value |
| No race detector errors | `go test -race` exits 0 |

```bash
# Run with explicit concurrency:
go test -v -race -count=3 -parallel 8 ./... -timeout 60s 2>&1 | grep -E "PASS|FAIL|DATA RACE"
```

---

### Group 4: Pattern Registration Edge Cases

Exercises all panic guards at route registration time. These tests verify that chi fails fast and loud on misconfiguration.

```bash
go test -v -run "TestPanic|TestInvalid|TestDuplicate" ./... -count=1 -timeout 10s
```

**Pass criteria:**
- Each panic guard fires with a descriptive message
- No panic fires for valid configurations
- Recovered panics contain the expected message substring

**Quality gates — Panic Guard Reference Table:**

| Guard | Trigger | Expected Panic Message Substring |
|-------|---------|-----------------------------------|
| Late middleware | `Use()` after `Get()` | `"all middlewares must be defined before routes on a mux"` |
| Non-slash pattern | `Get("noslash", ...)` | `"routing pattern must begin with '/"` |
| Invalid HTTP method | `Method("FROBNICATE", ...)` | `"http method is not supported"` |
| Nil mount handler | `Mount("/api", nil)` | `"nil handler"` |
| Nil route function | `Route("/api", nil)` | `"nil subrouter"` |
| Duplicate mount | Two `Mount("/api", ...)` calls | `"existing path"` |
| Wildcard not last | `Get("/api/*/x", ...)` | `"wildcard"` |
| Duplicate param key | `Get("/{id}/{id}", ...)` | `"duplicate param key"` |
| Invalid regexp | `Get("/{id:[invalid}", ...)` | `"invalid regexp"` |
| Missing `}` | `Get("/{id", ...)` | `"closing delimiter"` |

---

### Group 5: Existing Test Suite (Full Regression)

Run chi's complete built-in test suite to ensure no regressions.

```bash
go test ./... -count=1 -timeout 120s -v 2>&1 | tail -20
```

**Pass criteria:**
- All existing tests pass (0 failures, 0 errors)
- Output ends with `ok github.com/go-chi/chi/v5`
- Output ends with `ok github.com/go-chi/chi/v5/middleware`

---

## Parallel Execution

Groups 1, 2, and 4 are independent and can run concurrently. Group 3 (race detector) must run separately because the race detector adds overhead that can cause flakiness under high parallelism.

```bash
# Run Groups 1, 2, 4 in parallel:
go test -v -run "TestMux|TestRouter|TestRoute" ./... -count=1 &
go test -v -run "TestMiddleware|TestUse|TestWith|TestGroup|TestChain" ./... -count=1 &
go test -v -run "TestPanic|TestInvalid|TestDuplicate" ./... -count=1 &
wait

# Then run Group 3 (race) sequentially:
go test -v -race ./... -count=1 -timeout 60s

# Then run Group 5 (full suite) for final confirmation:
go test ./... -count=1 -timeout 120s
```

## Post-Run Verification

After all test groups complete, verify at multiple levels:

### Level 1: Process Exit
```bash
echo "Exit code: $?"
# Expected: 0 for all groups
```

### Level 2: Test Count
```bash
go test ./... -count=1 -v 2>&1 | grep -c "--- PASS"
# Expected: matches the number of tests in the suite
```

### Level 3: No Data Races
```bash
go test -race ./... -count=1 2>&1 | grep -c "DATA RACE"
# Expected: 0
```

### Level 4: Coverage (optional)
```bash
go test ./... -coverprofile=quality/results/coverage.out
go tool cover -func=quality/results/coverage.out | grep -E "^github.com/go-chi/chi/v5/(mux|tree|context|chain)"
```

**Expected coverage targets (see QUALITY.md):**
- `tree.go`: ≥ 90%
- `mux.go`: ≥ 85%
- `context.go`: ≥ 85%
- `chain.go`: ≥ 80%

## Summary Table (Print After Each Run)

```
| Group | Tests | Passed | Failed | Errors | Duration | Result |
|-------|-------|--------|--------|--------|----------|--------|
| 1: Core router | N | N | 0 | 0 | ~Xs | PASS/FAIL |
| 2: Middleware | N | N | 0 | 0 | ~Xs | PASS/FAIL |
| 3: Race detector | N | N | 0 | 0 | ~Xs | PASS/FAIL |
| 4: Panic guards | N | N | 0 | 0 | ~Xs | PASS/FAIL |
| 5: Full suite | N | N | 0 | 0 | ~Xs | PASS/FAIL |
```

**Recommendation:** If any group has failures → FIX FIRST. If all groups pass → SHIP IT.

## Teardown

Chi has no external infrastructure to tear down. The test processes exit cleanly. No cleanup required.
