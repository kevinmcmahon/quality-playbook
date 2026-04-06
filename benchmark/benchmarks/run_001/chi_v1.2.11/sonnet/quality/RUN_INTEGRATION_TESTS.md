# Integration Test Protocol: chi

## Working Directory

All commands in this protocol must be run from the repository root:

```
/path/to/chi/
```

Never `cd` to an absolute path. Use `./` relative paths throughout.

## Project Type: Library / CLI Tool

chi is a Go HTTP routing library with no external service dependencies (no database, no message queue, no external API). Integration testing for chi focuses on:

1. **End-to-end request routing** — real HTTP requests through a live `httptest.Server`
2. **Middleware stack composition** — multiple middlewares chained together, real timing
3. **Sub-router composition** — mounted routers, route groups, inline middlewares
4. **Concurrent correctness** — pool reuse correctness under concurrent load
5. **Full test suite** — all existing tests continue to pass

## Execution UX

When running this protocol, an agent must:

**Phase 1 — Before executing anything:** Display the test plan:

```
Integration Test Plan for chi:
  Group A: Core routing (8 tests) — ~5s
  Group B: Middleware integration (6 tests) — ~10s
  Group C: Sub-router composition (4 tests) — ~5s
  Group D: Concurrent correctness (2 tests) — ~15s
  Group E: Full existing test suite — ~30s
  Total estimated time: ~65s
Proceed? [Y/n]
```

**Phase 2 — During execution:** One-line progress per test group:

```
⧗  Group A: Core routing...
✓  Group A: PASSED (8/8 tests, 0 failures)
⧗  Group B: Middleware integration...
✓  Group B: PASSED (6/6 tests, 0 failures)
```

**Phase 3 — After all groups:** Summary table with recommendation (see end of this file).

## Setup

No external services required. chi has no dependencies beyond Go stdlib.

Prerequisites:
- Go 1.23 or later (check with `go version`)
- Module dependencies: `go mod download` (no external deps for core — only Go stdlib)

Verify setup:
```bash
go version
go mod verify
```

## Field Reference Table

chi's "schema" is its routing patterns and response fields. These are the observable fields in integration test assertions:

| Field | Source | Type | Valid Values / Constraints |
|-------|--------|------|---------------------------|
| HTTP status code | `httptest.ResponseRecorder.Code` | int | 200, 201, 204, 400, 404, 405, 415, 429, 500, 504 |
| Response body | `httptest.ResponseRecorder.Body.String()` | string | Exact match or prefix match |
| URL param value | `chi.URLParam(r, key)` | string | Non-empty string for matched param; `""` for miss |
| RoutePattern | `chi.RouteContext(ctx).RoutePattern()` | string | `/path/{param}` form; no trailing slash unless root |
| Allow header | `w.Header().Get("Allow")` | string | Comma-separated HTTP methods for 405 responses |
| X-Request-Id | `w.Header().Get("X-Request-Id")` | string | `hostname/random-NNNNNN` format |
| RemoteAddr | `r.RemoteAddr` | string | IP or IP:port format |
| Retry-After | `w.Header().Get("Retry-After")` | string | Integer seconds (when RetryAfterFn configured) |

## Test Groups

### Group A: Core Routing

**Purpose:** Verify that real HTTP requests route to the correct handler with correct URL params.

**Setup:** `httptest.NewServer(r)` — creates a real HTTP server on a random port.

**Tests:**

```bash
go test -v -run TestIntegration_CoreRouting ./quality/
```

**Test matrix:**

| Route | Request | Expected Status | Expected Body / Param |
|-------|---------|----------------|----------------------|
| `GET /` | `GET /` | 200 | "root" |
| `GET /users/{id}` | `GET /users/42` | 200 | URLParam "id" = "42" |
| `GET /users/{id}` | `GET /users/` | 404 | — |
| `POST /items` | `GET /items` | 405 | Allow header contains "POST" |
| `GET /files/*` | `GET /files/a/b/c` | 200 | wildcard captures "a/b/c" |
| `GET /date/{y:\\d{4}}/{m:\\d{2}}` | `GET /date/2024/03` | 200 | params extracted |
| `GET /date/{y:\\d{4}}/{m:\\d{2}}` | `GET /date/24/03` | 404 | regexp rejects short year |
| No route | `GET /nonexistent` | 404 | — |

**Pass criteria:** All 8 request/response pairs match expected status and body/param exactly.

---

### Group B: Middleware Integration

**Purpose:** Verify middleware composition, ordering, and edge cases with a real HTTP server.

```bash
go test -v -run TestIntegration_Middleware ./quality/
```

**Test matrix:**

| Middleware | Scenario | Expected Outcome |
|------------|----------|-----------------|
| `RequestID` | No incoming ID | Response uses generated ID matching `host/random-NNNNNN` pattern |
| `RequestID` | Incoming `X-Request-Id: abc` | Context contains `"abc"` |
| `RealIP` | `X-Real-IP: 10.0.0.1` | `r.RemoteAddr` = `"10.0.0.1"` |
| `RealIP` | `X-Real-IP: not-an-ip` | `r.RemoteAddr` unchanged |
| `Timeout(50ms)` | Handler sleeps 200ms | Status 504 |
| `Recoverer` + panic | Handler panics with `"boom"` | Status 500; no propagation |

**Pass criteria:** All 6 scenarios match expected outcome. No goroutine leaks.

---

### Group C: Sub-Router Composition

**Purpose:** Verify that mounted sub-routers receive correct paths and that error handlers propagate.

```bash
go test -v -run TestIntegration_SubRouter ./quality/
```

**Test matrix:**

| Setup | Request | Expected |
|-------|---------|----------|
| `Mount("/api", sub)`, sub has `GET /users/{id}` | `GET /api/users/99` | 200, id="99" |
| `Mount("/api", sub)` with custom NotFound on parent | `GET /api/unknown` | 404, body="custom-404" |
| `Route("/v1", fn)`, fn registers `GET /items` | `GET /v1/items` | 200 |
| Nested mount: parent mounts sub at `/a`, sub mounts subsub at `/b`, subsub has `GET /c` | `GET /a/b/c` | 200 |

**Pass criteria:** All 4 requests reach expected handlers with correct params and status codes.

---

### Group D: Concurrent Correctness

**Purpose:** Verify that sync.Pool RouteContext reuse does not leak params between concurrent requests.

```bash
go test -v -run TestIntegration_ConcurrentCorrectness ./quality/
```

**Tests:**

1. **Param isolation under concurrent load:** Fire 100 concurrent requests to `GET /users/{id}` with different IDs. Each request handler reads its own `URLParam(r, "id")` and writes it to the response. Verify no response contains a different ID than was requested.

2. **No data race under `-race`:** Run the basic routing tests with the race detector enabled.

```bash
go test -race -run TestIntegration_ConcurrentCorrectness ./quality/
```

**Pass criteria:**
- Test 1: All 100 responses contain exactly the requested ID. Zero cross-contamination.
- Test 2: Zero data race warnings from the race detector.

---

### Group E: Full Existing Test Suite

**Purpose:** Verify that new quality files did not break any existing tests.

```bash
go test ./... 2>&1
```

Run all packages in parallel where possible:

```bash
go test ./... &
wait
```

**Pass criteria:**
- `ok` status for all packages: `chi`, `chi/middleware`
- Zero test failures
- Zero build errors

---

## Execution Script (POSIX Shell)

```bash
#!/bin/sh
set -e

echo "=== chi Integration Tests ==="
echo ""

echo "--- Group A: Core Routing ---"
go test -v -run TestIntegration_CoreRouting ./quality/ && echo "✓ Group A PASSED" || echo "✗ Group A FAILED"

echo ""
echo "--- Group B: Middleware Integration ---"
go test -v -run TestIntegration_Middleware ./quality/ && echo "✓ Group B PASSED" || echo "✗ Group B FAILED"

echo ""
echo "--- Group C: Sub-Router Composition ---"
go test -v -run TestIntegration_SubRouter ./quality/ && echo "✓ Group C PASSED" || echo "✗ Group C FAILED"

echo ""
echo "--- Group D: Concurrent Correctness ---"
go test -race -run TestIntegration_ConcurrentCorrectness ./quality/ && echo "✓ Group D PASSED" || echo "✗ Group D FAILED"

echo ""
echo "--- Group E: Full Existing Test Suite ---"
go test ./... && echo "✓ Group E PASSED" || echo "✗ Group E FAILED"

echo ""
echo "=== Integration Test Complete ==="
```

Save to `./quality/run_integration.sh`, then: `chmod +x ./quality/run_integration.sh && ./quality/run_integration.sh`

## Deep Post-Run Verification

After all groups pass:

1. **Process exit:** `go test ./...` must exit 0.
2. **Race detector:** `go test -race ./...` must produce zero data race reports.
3. **No goroutine leaks:** After the concurrent test, verify no hanging goroutines (test should complete within 30 seconds).
4. **Build clean:** `go build ./...` must produce no errors or warnings.
5. **Resource cleanup:** `httptest.Server.Close()` must be called in all integration tests — verify with `defer s.Close()`.

## Teardown

No external resources to clean up. `httptest.Server` instances must be closed after each test group:

```go
s := httptest.NewServer(router)
defer s.Close()
```

## Summary Table Template

After all groups complete, present:

| Group | Tests | Passed | Failed | Duration | Status |
|-------|-------|--------|--------|----------|--------|
| A: Core Routing | 8 | — | — | — | — |
| B: Middleware | 6 | — | — | — | — |
| C: Sub-Router | 4 | — | — | — | — |
| D: Concurrent | 2 | — | — | — | — |
| E: Full Suite | all | — | — | — | — |

**Recommendation:** SHIP IT (all pass) / FIX FIRST (any failures) / NEEDS INVESTIGATION (flaky)
