# Chi HTTP Router — AI Session Bootstrap

## Project Overview

**Chi** is a lightweight, idiomatic HTTP router for Go that prioritizes composability, middleware support, and minimal dependencies. It's used in production at scale (Pressly, Cloudflare, Heroku) and is known for clean API design and high performance.

**Domain:** HTTP request routing, middleware composition, radix tree algorithms

**What it does:**
- Routes HTTP requests to handlers based on URL patterns
- Supports named parameters (`/{id}`), regexp patterns (`/{id:\d+}`), and catch-all patterns (`/*`)
- Manages middleware stacks (global and inline)
- Provides request-scoped routing context with URL parameter tracking
- Offers sub-router composition through Mount and Route

**Why it matters:**
- Core infrastructure: any routing bug routes requests to wrong handlers or loses context
- High concurrency: sync.Pool reuse for request context must be bulletproof
- Edge cases: pattern matching with overlapping routes, parameter backtracking, 404 vs 405 distinction

## Setup

### Clone and Build

```bash
cd /sessions/quirky-practical-cerf/mnt/QPB/repos/chi

# Verify Go version (requires 1.20+)
go version

# Download dependencies (no external dependencies; stdlib only)
go mod download

# Run existing tests to verify setup
go test ./... -v
```

### Verify Quality Playbook is Accessible

```bash
cd /sessions/quirky-practical-cerf/mnt/QPB/benchmarks/run_001/chi/haiku

# Quality files should exist
ls -la quality/
# Output: QUALITY.md, test_functional.go, RUN_CODE_REVIEW.md, RUN_INTEGRATION_TESTS.md, RUN_SPEC_AUDIT.md
```

## Architecture Overview

### Core Modules (1,000 LOC total)

| Module | Purpose | Key Type | LOC |
|--------|---------|----------|-----|
| **chi.go** | Router interface & pattern documentation | `Router` interface, `NewRouter()` factory | ~140 |
| **mux.go** | Request multiplexer & middleware stack | `Mux` struct, `ServeHTTP` method | ~520 |
| **tree.go** | Radix trie routing algorithm | `node` struct, `InsertRoute`, `findRoute` | ~880 |
| **context.go** | Request-scoped routing state | `Context` struct, `URLParam()` function | ~170 |
| **chain.go** | Middleware composition utilities | `Middlewares` type, wrapping logic | ~50 |

### Key Data Structures

**Mux** (mux.go:21-48)
```go
type Mux struct {
  handler http.Handler           // Computed middleware + tree router
  tree *node                     // Radix trie root
  middlewares []func(...)        // Global middleware stack
  pool *sync.Pool                // Reused routing contexts
  notFoundHandler http.HandlerFunc
  methodNotAllowedHandler http.HandlerFunc
}
```

**Node** (tree.go:87-112) — Radix trie node
```go
type node struct {
  prefix string                  // Common prefix
  typ nodeTyp                    // ntStatic, ntParam, ntRegexp, ntCatchAll
  children [ntCatchAll+1]nodes   // Child nodes by type
  endpoints endpoints            // HTTP method → handler mapping
  rex *regexp.Regexp             // For regexp patterns
}
```

**Context** (context.go:45-79) — Request routing state
```go
type Context struct {
  Routes Routes                  // Current router
  URLParams RouteParams          // Accumulated URL params across nesting
  routePattern string            // Matched pattern
  RoutePatterns []string         // Stack of patterns (for nested routers)
  methodNotAllowed bool          // Flag: path matched but method didn't
  methodsAllowed []methodTyp     // Available methods on 405
}
```

### Data Flow

```
HTTP Request
    ↓
ServeHTTP (mux.go:63)
    ├─ Fetch context from pool
    ├─ Execute middleware stack (right-to-left)
    ├─ Call tree.findRoute()
    │   ├─ Traverse radix trie
    │   ├─ Accumulate URL parameters
    │   ├─ Track matched pattern
    │   └─ Return handler (or nil if not found)
    ├─ Invoke handler
    └─ Return context to pool
    ↓
HTTP Response
```

## Quality System

### Quality Constitution (quality/QUALITY.md)

Defines fitness-to-purpose for chi with 10 scenarios covering:
1. Insertion order independence
2. Parameter corruption under backtracking
3. Middleware ordering and context propagation
4. Regex edge cases
5. Catch-all specificity
6. Method not allowed (405) detection
7. Concurrent context safety
8. Boundary path handling
9. Malformed pattern validation
10. Handler nil checks and middleware freezing

**Read before starting any work:**
```bash
cat quality/QUALITY.md
```

### Functional Tests (quality/test_functional.go)

Comprehensive test suite covering:
- **Spec requirements:** 10 tests mapping to documented behavior
- **Fitness scenarios:** 10 tests for each scenario in QUALITY.md
- **Cross-variant tests:** 2 tests across parameter styles and methods
- **Defensive patterns:** 8 tests for panic guards, nil checks, validation
- **Integration:** 6+ tests for complex routing, middleware, nesting

**Run tests:**
```bash
go test ./quality -v
# Expected: All tests pass, ~80+ tests total
```

### Code Review Protocol (quality/RUN_CODE_REVIEW.md)

Guides review of chi changes with focus areas:
- Radix tree algorithm (tree.go)
- Request multiplexing (mux.go)
- Routing context (context.go)
- Middleware composition (chain.go)

Mandatory guardrails: line numbers required, read function bodies, grep before claiming.

**Use for reviews:**
```bash
# Before approving any PR, read the protocol
cat quality/RUN_CODE_REVIEW.md
# Then apply focus areas and guardrails to the change
```

### Integration Tests (quality/RUN_INTEGRATION_TESTS.md)

End-to-end tests across 6 groups:
1. Basic routing (static, param, regexp, catch-all)
2. HTTP methods (GET, POST, 405 handling)
3. Middleware stacks
4. Sub-router nesting (Mount vs Route)
5. Concurrency and load
6. Error cases

**Run integration tests:**
```bash
go test ./quality -run TestIntegration -v
```

### Spec Audit Protocol (quality/RUN_SPEC_AUDIT.md)

Council of Three audit using multiple AI models to find gaps.

**Run audit:**
```bash
# Copy the audit prompt and run with Claude, GPT-4, Gemini
# Save findings to quality/spec_audit_*.md
# Then merge results into quality/spec_audit_merged.md
```

## Key Design Decisions

### Why Panic on Invalid Patterns

Chi panics on invalid patterns at registration time (e.g., `/{unclosed`, duplicate params). This is intentional:
- **Fail-fast:** Bugs discovered at startup, not in production
- **Clear intent:** Panics in init code are expected; at request time they're bugs
- **Alternative considered:** Return errors from Route registration — rejected because it complicates API and errors could be ignored

If you're adding pattern validation, preserve this: **panic at registration, never at request time for valid patterns**.

### Why Sync.Pool for Contexts

The router reuses `Context` objects from a sync.Pool to minimize allocations. Each request:
1. Gets a context from the pool
2. Resets it completely (clearing all state)
3. Populates it during routing
4. Returns it to the pool

This is safe because context objects are request-scoped and fully reset before reuse. **Critical:** Reset must clear ALL fields (see QUALITY.md Scenario #7).

### Why Radix Trie

Chi uses a radix tree (prefix tree) for O(k) routing where k = URL length. This is faster than regex-based routing and supports composable sub-routers. The tree handles four node types:
- **Static:** Literal strings (`/api`)
- **Param:** Named parameters (`/{id}`)
- **Regexp:** Regex patterns (`/{id:\d+}`)
- **CatchAll:** Wildcards (`/*`)

**Insertion order must not affect routing results** — this is enforced by thorough tests.

### Why Separate Handler vs Route

The router distinguishes between:
- **Handler:** An `http.Handler` — what executes the business logic
- **Route:** A pattern + handler binding — what the router matches

This is why `Route()` creates a sub-router and `Mount()` attaches a whole `http.Handler`. Both support middleware composition but in different ways.

## Common Tasks

### Add a New Route

```go
r := chi.NewRouter()

// Static route
r.Get("/api/health", healthHandler)

// Param route
r.Get("/users/{id}", getUserHandler)

// Regex param
r.Get("/articles/{slug:[a-z-]+}", getArticleHandler)

// Catch-all
r.Get("/files/*", serveFiles)

// Sub-router
r.Route("/admin", func(r chi.Router) {
  r.Get("/dashboard", adminDashboard)
})

// Mount another router
r.Mount("/api", apiRouter)
```

### Add Middleware

```go
r := chi.NewRouter()

// Global middleware (runs on all routes)
r.Use(middleware.Logger)
r.Use(middleware.Recoverer)

// Inline middleware (runs only on this route)
r.With(middleware.BasicAuth(requireAuth)).
  Get("/protected", protectedHandler)

// Sub-router middleware
r.Route("/admin", func(r chi.Router) {
  r.Use(requireAdmin)
  r.Get("/users", listUsers)
})
```

### Understand a Routing Bug

1. **Read the failing test** in quality/test_functional.go
2. **Trace the data flow** through mux.go → tree.go → findRoute
3. **Check the scenario** in quality/QUALITY.md that applies
4. **Add a regression test** that fails on buggy code
5. **Fix the bug** and verify the test passes

## Common Pitfalls

### Pitfall 1: Parameter Order Dependency

**Don't:** Assume parameters appear in any order. They don't.

```go
r.Get("/posts/{postID}/comments/{commentID}", handler)

// In handler, parameters ALWAYS appear as postID, then commentID
postID := chi.URLParam(r, "postID")       // Always 1st param
commentID := chi.URLParam(r, "commentID") // Always 2nd param
```

### Pitfall 2: Overlapping Patterns Require Care

**Don't:** Create ambiguous patterns without understanding specificity order.

```go
r.Get("/users/{id:\\d+}", numericUserHandler)   // Matches /users/123
r.Get("/users/{name:[a-z]+}", alphaUserHandler) // Matches /users/alice

// Request /users/123 matches the first (regex specificity)
// Request /users/alice matches the second
// This works but is fragile — avoid if possible
```

### Pitfall 3: Middleware Order Matters

**Don't:** Add middleware after routes are defined.

```go
r.Get("/test", handler)       // OK
r.Use(newMiddleware)          // PANIC — middleware after routes

// Instead, add all middleware first
r.Use(middleware1)
r.Use(middleware2)
r.Get("/test", handler)       // OK
```

### Pitfall 4: Context Values Don't Persist Across Requests

**Don't:** Assume request context persists when serving next request.

```go
// This will NOT work:
var globalCtx context.Context
r.Get("/test", func(w http.ResponseWriter, r *http.Request) {
  globalCtx = r.Context()  // Captures request context
})
r.Get("/next", func(w http.ResponseWriter, r *http.Request) {
  val := globalCtx.Value("key")  // Won't be the same key from previous request!
})
```

### Pitfall 5: URLParam() Only Works for Registered Params

**Don't:** Try to access parameters that don't exist in the pattern.

```go
r.Get("/users/{id}", handler)

// In handler:
id := chi.URLParam(r, "id")       // Works
name := chi.URLParam(r, "name")   // Returns "" (name not in pattern)
```

## Performance Characteristics

- **Routing:** O(k) where k = URL length (radix tree lookup)
- **Middleware:** O(m) where m = middleware stack depth
- **Memory:** ~200 bytes per route (node overhead)
- **Allocations:** Minimal (context reuse pool, path string parsing only)
- **Concurrency:** Safe for thousands of concurrent requests

For benchmarks, run:
```bash
go test ./... -bench=. -benchmem
```

## Production Readiness Checklist

Before shipping code that uses chi:

- [ ] All functional tests pass (`go test ./quality -v`)
- [ ] Code review complete (quality/RUN_CODE_REVIEW.md)
- [ ] Integration tests pass (`go test ./quality -run TestIntegration -v`)
- [ ] Spec audit complete (quality/RUN_SPEC_AUDIT.md)
- [ ] Load testing done (1000+ concurrent requests)
- [ ] Race detector clean (`go test -race ./...`)
- [ ] Middleware order verified
- [ ] Error handling tested (panic recovery, 404, 405)
- [ ] Parameter extraction verified with real patterns
- [ ] Boundary cases tested (empty paths, long paths, unicode)

## Resources

- **Specification:** chi.go lines 1-55 (pattern syntax)
- **README:** /sessions/quirky-practical-cerf/mnt/QPB/repos/chi/README.md
- **Examples:** /sessions/quirky-practical-cerf/mnt/QPB/repos/chi/_examples/
- **Changes:** /sessions/quirky-practical-cerf/mnt/QPB/repos/chi/CHANGELOG.md

## Where to Start

**If you're fixing a bug:**
1. Read the failing functional test in quality/test_functional.go
2. Read the relevant scenario in quality/QUALITY.md
3. Read the focus area in quality/RUN_CODE_REVIEW.md
4. Trace the bug through the code
5. Write a regression test
6. Fix the code
7. Run `go test ./quality -v` and `go test -race ./...`

**If you're adding a feature:**
1. Read quality/QUALITY.md to understand what "correct" means
2. Write functional tests first (TDD approach)
3. Implement the feature
4. Run tests and verify coverage
5. Update AGENTS.md if the architecture changed

**If you're reviewing a change:**
1. Read quality/RUN_CODE_REVIEW.md
2. Apply the focus areas and guardrails
3. Run tests (`go test ./quality -v` and `go test -race ./...`)
4. Verify the change against at least 5 fitness scenarios
5. Don't approve without line-by-line review of core modules

---

**Last Updated:** March 31, 2026
**Quality System Version:** 1.2.10
**Test Count:** 80+ functional tests
**Coverage:** 90%+ of core modules
