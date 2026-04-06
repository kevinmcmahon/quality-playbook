# Chi HTTP Router — AI Session Bootstrap

**Read this first.** This file tells you everything you need to know about chi before starting work.

## What Is Chi?

Chi is a lightweight, idiomatic HTTP router for building Go web services. It's designed for composability, modularity, and maintainability—especially for large REST APIs. Chi is used in production at Pressly, Cloudflare, Heroku, and others.

**Key characteristics:**
- **~1000 lines of core code** (tree.go, mux.go, context.go)
- **No external dependencies** — stdlib only (net/http, context, sync)
- **Radix tree router** — Fast O(k) lookup where k is key length
- **Context-based parameter passing** — Uses Go's context package for request-scoped values
- **Composable middleware** — Standard http.Handler interface
- **Sub-routers** — Mount() for composition, Route() for grouping

**GitHub:** https://github.com/go-chi/chi/v5

## Repository Structure

```
/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/
├── chi.go              # Package interface definitions
├── mux.go              # Main router multiplexer (526 lines)
├── tree.go             # Radix tree implementation (877 lines)
├── context.go          # Request routing context (166 lines)
├── chain.go            # Middleware composition (49 lines)
├── middleware/         # 45 middleware files (Recoverer, Logger, Timeout, etc.)
├── mux_test.go         # Mux tests (2071 lines)
├── tree_test.go        # Tree tests (579 lines)
├── context_test.go     # Context tests (104 lines)
├── README.md           # Design goals and examples
├── CHANGELOG.md        # Version history and breaking changes
├── CONTRIBUTING.md     # Contribution guidelines
├── LICENSE             # MIT license
├── go.mod              # Go module definition (go 1.23)
└── _examples/          # Example applications
```

## Setup: Build and Run Tests

### 1. Install Go 1.23+

Chi supports Go 1.20, 1.21, 1.22, 1.23. Verify your version:

```bash
go version
# Expected: go version go1.23.X ...
```

### 2. Navigate to Chi Directory

```bash
cd /sessions/quirky-practical-cerf/mnt/QPB/repos/chi/
```

### 3. Verify Build

```bash
go build ./...
```

Expected: No output (success). If there are errors, something is misconfigured.

### 4. Run Existing Test Suite

```bash
go test ./... -v
```

Expected: All tests pass. If any fail, investigate before making changes.

**Test files:**
- `mux_test.go` — Tests router behavior, middleware, parameter extraction
- `tree_test.go` — Tests radix tree insertion and lookup
- `context_test.go` — Tests request context management
- `pattern_test.go` — Tests pattern parsing and validation
- `path_value_test.go` — Tests path value extraction

### 5. Run New Functional Tests

Chi's quality playbook includes functional tests:

```bash
go test ./quality/... -v
```

Expected: All 29+ tests pass. These test routing, middleware, parameters, and edge cases.

## Key Design Decisions

### 1. Panic-Based Input Validation

Chi validates route patterns at registration time by **panicking** on invalid input:
- Invalid regex: `panic("chi: invalid regexp pattern ...")`
- Duplicate parameters: `panic("chi: ... duplicate param key ...")`
- Wildcard placement: `panic("chi: wildcard '*' must be the last pattern ...")`

**Why:** This is a design choice. Route patterns are hardcoded in application code, not user input. Panics force developers to fix patterns at development time, not runtime.

**Consequence:** If chi is used in a system where routes come from untrusted sources (user-uploaded definitions, dynamic config), panics could crash the server. Mitigated by: (a) documentation that patterns must be trusted, (b) ValidatePattern() function for pre-flight checks.

### 2. Context Pool Reuse

Chi reuses `*Context` objects from `sync.Pool` for performance:

```go
rctx := rctxPool.Get().(*Context)
defer func() {
    rctx.Reset()
    rctxPool.Put(rctx)
}(rctx)
```

**Why:** Creating new Context structs on every request is wasteful. Pooling amortizes allocation cost.

**Safety:** Reset() must fully clear all fields. If a field is added to Context without updating Reset(), cross-request leakage is possible (low probability, catastrophic if it happens). Check context.go:82–96.

### 3. Radix Tree with Node Ordering

Chi uses a **radix tree** (prefix tree) with specific node ordering:
1. **Static nodes** (literal path segments) — searched first
2. **Param nodes** (named parameters `{id}`) — searched second
3. **Regex nodes** (pattern-constrained params) — searched with regex matching
4. **Catchall nodes** (`/*`) — searched last

**Why:** This ordering allows longest-prefix matching (static `/users/admin` before param `/{id}`) and efficient regex handling.

**Consequence:** Route insertion order should not affect matching, but subtle insertion logic (tailSort() at tree.go:793–798) is complex. If you modify tree insertion, test carefully.

### 4. Middleware-Before-Routes Enforcement

Chi panics if middleware is registered after routes:

```go
r.Get("/", handler)      // Sets mx.handler
r.Use(middleware)        // Panics: "middlewares must be defined before routes"
```

**Why:** Middleware wraps the entire handler. If registered after routes, the order is ambiguous.

**Consequence:** Middleware must be registered first. This is enforced strictly and is a common gotcha for new users.

## Architecture Overview

### Request Flow

1. **Handler registration** (Get, Post, Mount, etc.)
   - Patterns are parsed and validated (panics on error)
   - Routes inserted into radix tree

2. **Request arrives** (http.Handler.ServeHTTP)
   - Get or create Context from pool
   - Call middleware chain
   - Find route in tree
   - Extract URL parameters
   - Call handler

3. **Response sent**
   - Handler writes to ResponseWriter
   - Context reset and returned to pool

### Key Modules

| Module | Lines | Purpose |
|--------|-------|---------|
| `mux.go` | 526 | Router multiplexer, handler registry, middleware management |
| `tree.go` | 877 | Radix tree implementation, route insertion, pattern matching |
| `context.go` | 166 | Context management, URL parameter extraction |
| `chain.go` | 49 | Middleware composition helpers |
| `chi.go` | 137 | Package-level interfaces (Router, Routes, etc.) |

### Data Structures

**Mux** (router):
- `handler http.Handler` — Computed handler chain (mux + middlewares)
- `tree *node` — Radix tree root
- `middlewares []func(http.Handler) http.Handler` — Middleware stack
- `pool *sync.Pool` — Reusable Context objects

**Context** (request routing):
- `Routes Routes` — Reference to router
- `RoutePath, RouteMethod string` — Overrides for subrouter routing
- `URLParams RouteParams` — All accumulated parameters
- `RoutePatterns []string` — Stack of matched patterns

**Node** (tree node):
- `children [4]nodes` — Child arrays (static, param, regex, catchall)
- `endpoints endpoints` — Method → handler mapping
- `rex *regexp.Regexp` — Compiled regex (for regex nodes)
- `prefix string` — Common prefix
- `typ nodeTyp` — Node type (static/param/regex/catchall)

## Quality Documentation

Read these files to understand chi's quality requirements:

**`quality/QUALITY.md`** — Quality constitution
- What quality means for chi (fitness for production use)
- Coverage targets by module with rationale
- Fitness-to-purpose scenarios (10 detailed architectural vulnerabilities)
- AI session quality discipline

**`quality/test_functional.go`** — Functional tests
- 29 tests covering: spec requirements, fitness scenarios, defensive patterns
- Tests routing, middleware, parameters, error handling, concurrency
- Run: `go test ./quality/... -v`

**`quality/RUN_CODE_REVIEW.md`** — Code review protocol
- How to review chi's core modules (tree.go, mux.go, context.go)
- Focus areas with line number references
- Guardrails to prevent hallucinated findings
- Regression test template

**`quality/RUN_INTEGRATION_TESTS.md`** — Integration test protocol
- End-to-end test matrix (6 test groups, 29 tests)
- Quality gates and verification criteria
- Expected results

**`quality/RUN_SPEC_AUDIT.md`** — Council of Three spec audit
- Multi-model audit protocol (3 independent auditors)
- 10 scrutiny areas (ReDoS, panic safety, context pools, HTTP compliance, etc.)
- Triage process and consolidated reporting

## Common Tasks

### Add a New Route

```go
r := chi.NewRouter()

// Middleware first (required)
r.Use(middleware.Logger)
r.Use(middleware.Recoverer)

// Routes after
r.Get("/", homeHandler)
r.Get("/users/{id}", getUserHandler)
r.Post("/users", createUserHandler)

http.ListenAndServe(":3000", r)
```

### Extract URL Parameters

```go
r.Get("/users/{userID}/posts/{postID}", func(w http.ResponseWriter, r *http.Request) {
    userID := chi.URLParam(r, "userID")    // "123"
    postID := chi.URLParam(r, "postID")    // "456"
    fmt.Fprintf(w, "User %s, Post %s\n", userID, postID)
})
```

### Use Regex Patterns

```go
r.Get("/articles/{id:[0-9]+}", func(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")  // Only matches digits
    w.Write([]byte("Article " + id))
})
```

### Mount Sub-routers

```go
apiRouter := chi.NewRouter()
apiRouter.Get("/status", statusHandler)

r := chi.NewRouter()
r.Mount("/api", apiRouter)  // /api/status available

http.ListenAndServe(":3000", r)
```

### Group Routes with Middleware

```go
r.Route("/admin", func(admin chi.Router) {
    admin.Use(requireAuth)  // Only applies to routes in this group
    admin.Get("/dashboard", dashboardHandler)
    admin.Post("/users", createUserHandler)
})
```

### Wildcard Routes

```go
r.Get("/files/*", func(w http.ResponseWriter, r *http.Request) {
    path := chi.URLParam(r, "*")  // "dir/subdir/file.pdf"
    serveFile(path)
})
```

## Known Issues & Limitations

### 1. Regex Denial of Service (ReDoS)

Chi doesn't protect against ReDoS patterns. A route like `{id:(?:.*)*}` could hang a goroutine.

**Mitigation:** Assume route patterns are trusted (hardcoded, not user-supplied). If using dynamic routes, validate patterns before registration.

### 2. Panic-Based Error Handling

Invalid patterns panic at runtime. If patterns come from untrusted sources, provide ValidatePattern() wrapper.

**Mitigation:** Document that patterns must be trusted. In systems with dynamic routes, catch panics and return errors.

### 3. Context Pool Complexity

Context reset is intricate. If a new field is added without updating Reset(), cross-request leakage is possible.

**Mitigation:** When modifying Context struct, update Reset() immediately. Add tests to verify no cross-request leakage.

## Testing Strategy

### For New Features

1. **Write unit tests** in `xxx_test.go` alongside the feature
2. **Use table-driven tests** for multiple input variations
3. **Test edge cases:** empty inputs, boundary values, concurrent access
4. **Run full test suite:** `go test ./...` must pass

### For Bug Fixes

1. **Write a test that reproduces the bug** (should fail before fix)
2. **Apply the fix**
3. **Verify the test passes** (should pass after fix)
4. **Ensure no regressions:** `go test ./...` must pass

### For Code Review

Follow `quality/RUN_CODE_REVIEW.md` for a structured code review with focus areas and guardrails.

## Before Ending Your Session

Complete this checklist:

- [ ] Read quality/QUALITY.md — understand fitness requirements
- [ ] Run `go test ./...` — all tests pass
- [ ] Run `go test ./quality/...` — functional tests pass
- [ ] If modifying code: add tests and regression tests
- [ ] If finding a bug: document in QUALITY.md with evidence
- [ ] Output a Quality Compliance Checklist before exiting

**Quality Compliance Checklist:**

```
Chi Router Quality Compliance — [Date/Time]

✓ Code changes complete
✓ All tests pass (go test ./... )
✓ Functional tests pass (go test ./quality/... )
✓ New tests added for new features
✓ No new quality risks introduced
✓ QUALITY.md scenarios still valid
✓ Code review completed (RUN_CODE_REVIEW.md)
✓ No panics leak to request handling

Ready for deployment: YES / NO
Reasons if NO: [...]
```

## References

- **README:** `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/README.md`
- **CHANGELOG:** `/sessions/quirky-practical-cerf/mnt/QPB/repos/chi/CHANGELOG.md`
- **Go Context:** https://golang.org/pkg/context/
- **HTTP Spec:** RFC 7230–7235
- **Radix Trees:** https://en.wikipedia.org/wiki/Radix_tree

## Questions?

If something is unclear:
1. Check the README and examples in `_examples/`
2. Read the relevant test file (mux_test.go, tree_test.go, etc.)
3. Search the codebase: `grep -r "concept" ./`
4. Read the code comments (chi is well-commented)

## Quick Links

- **Build:** `go build ./...`
- **Test:** `go test ./... -v`
- **Quality tests:** `go test ./quality/... -v`
- **Code coverage:** `go test -cover ./...`
- **Run example:** `go run _examples/rest/main.go`

---

**Last updated:** 2025-03-31
**Playbook version:** v1.2.11
**Model:** Haiku 4.5
**Phase:** Complete (Phases 1-3)
