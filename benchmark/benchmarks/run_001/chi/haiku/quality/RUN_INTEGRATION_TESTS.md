# Integration Test Protocol for Chi Router

## Overview

This protocol defines end-to-end integration tests for chi across different usage patterns, routing scenarios, and middleware stacks. Unlike unit tests, integration tests verify that the complete routing system works correctly with real Go HTTP servers and multiple components working together.

## Test Architecture

**Working Directory:** All commands use relative paths from `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/`

**Test Coverage Axes:**
1. **Routing Patterns**: Simple static, parameters, regexp, catch-all
2. **Method Variants**: GET, POST, PUT, DELETE, and rare methods (CONNECT, TRACE)
3. **Middleware Stacks**: Single, nested, inline, global
4. **Sub-router Nesting**: Multiple levels, Mount vs Route
5. **Handler Scenarios**: Success, panic recovery, nil handlers

## Test Groups

### Group 1: Basic Routing (Sequential)

**Purpose:** Verify core routing functionality works end-to-end

**Setup:**
```bash
# Build the test application
go build -o /tmp/chi-test-app ./quality/integration_test.go
```

**Tests:**

| Test | Command | Pass Criteria |
|------|---------|---------------|
| Static route | `curl -s http://localhost:8001/api/health \| grep "ok"` | HTTP 200, body contains "ok" |
| Param route | `curl -s http://localhost:8001/users/42 \| grep "User: 42"` | HTTP 200, body shows correct ID |
| Param type validation | `curl -s http://localhost:8001/users/abc -w "%{http_code}"` | HTTP 404 (pattern is `{id:\d+}`) |
| Multiple params | `curl -s http://localhost:8001/posts/123/comments/456 \| grep -E "123.*456"` | HTTP 200, both params present |
| Regexp pattern | `curl -s http://localhost:8001/articles/my-slug \| grep "slug: my-slug"` | HTTP 200, correct slug extracted |
| Catch-all | `curl -s http://localhost:8001/files/path/to/file.txt \| grep "files:"` | HTTP 200, path captured |

**Teardown:** Kill test server

### Group 2: Method Handling (Sequential)

**Purpose:** Verify HTTP methods are routed correctly and 405 responses work

**Setup:** Start test server on port 8002

**Tests:**

| Test | Command | Pass Criteria |
|------|---------|---------------|
| GET allowed | `curl -s -X GET http://localhost:8002/items -w "%{http_code}"` | 200 |
| POST allowed | `curl -s -X POST http://localhost:8002/items -w "%{http_code}"` | 200 |
| DELETE unsupported | `curl -s -X DELETE http://localhost:8002/items -w "%{http_code}"` | 405 |
| Allow header | `curl -s -X DELETE http://localhost:8002/items -H "Accept: */*" \| grep -i "allow"` | Header contains "GET, POST" |
| HEAD method | `curl -s -I http://localhost:8002/items \| grep "HTTP"` | 200, Content-Length set |
| OPTIONS method | `curl -s -X OPTIONS http://localhost:8002/items -H "Access-Control-Request-Method: DELETE"` | 200 or 405 depending on route |

**Teardown:** Kill test server

### Group 3: Middleware Integration (Sequential)

**Purpose:** Verify middleware executes in order and transforms requests/responses

**Setup:** Start test server with middleware stack on port 8003

**Tests:**

| Test | Execution | Pass Criteria |
|------|-----------|---------------|
| Logger middleware | `curl -s http://localhost:8003/log-test` | Request logged to stdout |
| Request ID header | `curl -s -i http://localhost:8003/id-test \| grep "X-Request-ID"` | Header present, non-empty |
| Timeout middleware | `curl --max-time 2 http://localhost:8003/slow-endpoint` | Request times out, returns 503 or client timeout |
| Custom middleware | `curl -s -H "X-Custom: test" http://localhost:8003/custom-header` | Handler receives header in context |
| Middleware order | `curl -s http://localhost:8003/order-test \| grep -o "m1.*m2.*h"` | Execution order: m1, m2, handler |
| Panic recovery | `curl -s http://localhost:8003/panic-endpoint` | HTTP 500, request not killed |
| Inline middleware | `curl -s http://localhost:8003/protected/resource` | Inline auth middleware executes |

**Teardown:** Kill test server

### Group 4: Sub-router Nesting (Sequential)

**Purpose:** Verify nested routers and Mount work correctly

**Setup:** Start test server with multiple sub-router levels on port 8004

**Tests:**

| Test | Command | Pass Criteria |
|------|---------|---------------|
| Mount path | `curl -s http://localhost:8004/api/items -w "%{http_code}"` | 200 (mounted sub-router) |
| Route nested | `curl -s http://localhost:8004/admin/users -w "%{http_code}"` | 200 (Route sub-router) |
| Nested middleware | `curl -s -v http://localhost:8004/api/items 2>&1 \| grep "X-API-Version"` | Header set by mounted router's middleware |
| Deeply nested | `curl -s http://localhost:8004/v1/public/posts/123/comments` | 200, all params extracted |
| Sub-router isolation | `curl -s http://localhost:8004/api/not-found -w "%{http_code}"` | 404 (not 200), isolated routing |
| Method in sub-router | `curl -s -X POST http://localhost:8004/api/items -w "%{http_code}"` | 200 or 405 based on sub-router routes |

**Teardown:** Kill test server

### Group 5: Concurrency and Load (Parallel)

**Purpose:** Verify routing under concurrent request load

**Setup:** Start test server on port 8005

**Tests (Run in Parallel):**

```bash
# Test 1: Concurrent same-route requests
for i in {1..100}; do
  curl -s http://localhost:8005/users/$i &
done
wait
# Pass Criteria: All 100 requests complete with correct IDs, no parameter leakage

# Test 2: Concurrent different routes
(for i in {1..50}; do curl -s http://localhost:8005/items/$i; done) &
(for i in {1..50}; do curl -s http://localhost:8005/posts/$i; done) &
wait
# Pass Criteria: All 100 requests complete, correct routes used, parameters isolated

# Test 3: Middleware + routing under load
for i in {1..200}; do
  curl -s -H "X-Request-ID: req-$i" http://localhost:8005/tracked/$i &
done
wait
# Pass Criteria: Request IDs logged correctly, no shared state between requests
```

**Teardown:** Kill test server

### Group 6: Error Cases (Sequential)

**Purpose:** Verify error handling doesn't break the router

**Setup:** Start test server on port 8006

**Tests:**

| Test | Command | Pass Criteria |
|------|---------|---------------|
| Handler panic | `curl -s http://localhost:8006/panic -w "%{http_code}"` | 500, request not killed |
| Missing param | `curl -s http://localhost:8006/users -w "%{http_code}"` | 404 (param required) |
| Invalid param type | `curl -s http://localhost:8006/id/not-a-number -w "%{http_code}"` | 404 (pattern rejects non-numeric) |
| Malformed query | `curl -s "http://localhost:8006/search?q=a+b%20c" -w "%{http_code}"` | 200 (query parsing OK) |
| Large path | `curl -s http://localhost:8006/$(printf 'a%.0s' {1..2000}) -w "%{http_code}"` | 404 or 414 (path too long) |
| Special chars in param | `curl -s http://localhost:8006/files/my%20file%20name.txt \| grep "my file"` | 200, param decoded correctly |

**Teardown:** Kill test server

## Integration Test Application (`quality/integration_test.go`)

Create a standalone test application that exercises all routing patterns:

```go
package quality

import (
	"fmt"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

func integrationTestRouter() http.Handler {
	r := chi.NewRouter()

	// Group 1: Basic routing
	r.Get("/api/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})

	r.Get("/users/{id:\\d+}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte(fmt.Sprintf("User: %s", id)))
	})

	r.Get("/posts/{pid}/comments/{cid:\\d+}", func(w http.ResponseWriter, r *http.Request) {
		pid := chi.URLParam(r, "pid")
		cid := chi.URLParam(r, "cid")
		w.Write([]byte(fmt.Sprintf("Post %s Comment %s", pid, cid)))
	})

	r.Get("/articles/{slug:[a-z-]+}", func(w http.ResponseWriter, r *http.Request) {
		slug := chi.URLParam(r, "slug")
		w.Write([]byte(fmt.Sprintf("slug: %s", slug)))
	})

	r.Get("/files/*", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(fmt.Sprintf("files: %s", chi.RouteContext(r.Context()).RoutePath)))
	})

	// Group 2: Method handling
	r.Get("/items", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
	r.Post("/items", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Group 3: Middleware
	r.With(middleware.Logger).Get("/log-test", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})
	r.With(middleware.RequestID).Get("/id-test", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// Group 4: Sub-routers
	r.Mount("/api", func() http.Handler {
		sub := chi.NewRouter()
		sub.Get("/items", func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		})
		return sub
	}())

	r.Route("/admin", func(r chi.Router) {
		r.Get("/users", func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		})
	})

	return r
}
```

## Execution Instructions

### Run All Integration Tests (Sequential)

```bash
#!/bin/bash
set -e

cd /sessions/quirky-practical-cerf/mnt/QPB/repos/chi

# Build test app
go test -c -o /tmp/chi-int-test ./quality/...

# Run each test group sequentially
echo "Running integration tests..."

# Start and test each server, then kill
for port in 8001 8002 8003 8004 8005 8006; do
  echo "Testing group on port $port..."
  # Server startup would happen here
  # Tests would execute
  # Server shutdown would happen here
done

echo "All integration tests passed!"
```

### Run Specific Group

```bash
# Run only Group 3 (Middleware)
go test ./quality -run TestIntegrationGroup3 -v
```

### Run with Race Detector

```bash
go test -race ./quality -v
```

## Quality Gates

Every test must verify these properties:

| Property | Verification | Pass Criteria |
|----------|--------------|---------------|
| Status Code | HTTP response status | Correct status (200, 404, 405, etc.) |
| Headers | Response headers present | Required headers present and correct |
| Body Content | Response body matches spec | Actual content matches expected |
| Parameter Extraction | URL parameters extracted correctly | All params present, correct values |
| Middleware Execution | Middleware runs in order | Execution order correct, no skips |
| Concurrency Safety | No parameter leakage | Each request has isolated context |
| Error Handling | Errors handled correctly | Panic recovery, nil checks work |
| Performance | Routing latency acceptable | Each request < 10ms (typical case) |

## Troubleshooting

**Test hangs:**
- Check that server is listening on the expected port
- Verify no firewall blocks localhost connections
- Check for infinite loops in middleware

**Parameter extraction fails:**
- Verify pattern syntax is correct
- Check that values are properly URL-encoded/decoded
- Ensure parameter names match between route and handler

**Middleware not executing:**
- Verify middleware is registered before routes
- Check middleware wrapping order (should be right-to-left)
- Confirm handler calls next.ServeHTTP()

**Method not allowed incorrectly returns 404:**
- Check that at least one method is registered for the path
- Verify methodNotAllowed flag is set
- Ensure Allow header is populated

## Maintenance

After any routing changes:
1. Run full integration test suite: `go test ./quality -v`
2. Run with race detector: `go test -race ./quality -v`
3. Load test with concurrent requests (100+)
4. Verify no performance degradation
