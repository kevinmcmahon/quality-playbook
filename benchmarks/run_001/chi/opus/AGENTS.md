# AGENTS.md — chi HTTP Router

## Project Description

Chi is a lightweight, idiomatic, and composable HTTP router for building Go HTTP services. It uses only the Go standard library (`net/http`) with zero external dependencies. Chi implements a Patricia radix trie for high-performance route matching with support for named parameters, regexp parameters, and catch-all wildcards.

**One-sentence summary:** Chi routes HTTP requests to handlers via a radix trie, supporting parameterized URL patterns, composable middleware chains, and sub-router mounting — all using only Go's standard library.

## Setup

```bash
# Chi is a Go library — no build step needed
go mod download
go build ./...
```

**Requirements:**
- Go 1.23 or later (supports the four most recent major Go versions)
- No external dependencies

## Build & Test

```bash
# Run all tests
go test ./...

# Run tests with race detector
go test -race ./...

# Run tests verbosely
go test -v ./...

# Run specific test
go test -v -run TestMuxBasic ./...

# Run quality playbook functional tests (from project root)
go test -v ./quality/
```

## Architecture

### Core Modules (5 files, ~1760 LOC)

| File | Purpose | Complexity |
|------|---------|------------|
| `chi.go` | Package documentation, Router/Routes interfaces, NewRouter() constructor | Low — pure interface definitions |
| `mux.go` | HTTP multiplexer — route registration, middleware management, request dispatch, sub-router mounting | High — orchestrates all routing |
| `tree.go` | Radix trie (Patricia tree) — route insertion, node splitting, multi-dimensional route lookup | Highest — recursive tree traversal with 4 node types |
| `context.go` | Routing context — URL parameter storage, route pattern tracking, context pooling support | Medium — parameter shadowing in nested routers |
| `chain.go` | Middleware chain composition — builds handler chains right-to-left | Low — 50 lines |

### Data Flow

```
HTTP Request
  → Mux.ServeHTTP()     [mux.go:63]   — get Context from sync.Pool
  → Middleware Chain     [chain.go:36] — execute registered middleware
  → Mux.routeHTTP()     [mux.go:441]  — route dispatch
  → tree.FindRoute()    [tree.go:374] — radix trie lookup
  → Handler execution                  — matched handler serves response
  → pool.Put(context)   [mux.go:91]   — return Context to sync.Pool
```

### Middleware Package (29 files)

Built-in middleware in `middleware/` — all use the standard `func(http.Handler) http.Handler` pattern. Key middleware: `recoverer.go` (panic recovery), `logger.go` (request logging), `compress.go` (gzip with sync.Pool), `throttle.go` (rate limiting), `timeout.go` (context deadline), `realip.go` (IP extraction), `basic_auth.go` (authentication).

## Key Design Decisions

1. **Zero external dependencies** — Chi uses only Go's standard library. This is intentional and should not be changed.
2. **sync.Pool for Context reuse** — Reduces allocations per request. Context.Reset() must clear ALL fields.
3. **Panic for configuration errors** — Invalid patterns, nil handlers, middleware-after-routes all panic at startup. This is "fail fast" design, not error handling.
4. **Bit flags for HTTP methods** — `methodTyp` uses bit flags (iota with shift) for efficient method matching. Limited to `strconv.IntSize - 2` total methods.
5. **Right-to-left middleware chain** — Last middleware wraps endpoint first, so first-registered middleware executes first.

## Known Quirks

- `Use()` panics if called after any route registration (middleware ordering invariant)
- `Handle("GET /path", h)` splits on space — matches Go 1.22 ServeMux syntax
- `URLParam()` iterates reverse — returns last-added key match (innermost sub-router wins)
- `RegisterMethod()` modifies global state without synchronization — must be called during init
- `replaceWildcards()` iteratively removes `"/*/"`— preserves wildcards that are part of named segments

## Quality Docs

| File | Purpose |
|------|---------|
| `quality/QUALITY.md` | Quality constitution — 10 fitness-to-purpose scenarios, coverage targets, theater prevention |
| `quality/functional_test.go` | Automated functional tests — spec requirements, scenario tests, boundary tests |
| `quality/RUN_CODE_REVIEW.md` | Code review protocol with 6 focus areas and guardrails |
| `quality/RUN_INTEGRATION_TESTS.md` | Integration test protocol — 9 test groups for full request lifecycle |
| `quality/RUN_SPEC_AUDIT.md` | Council of Three multi-model spec audit with 10 scrutiny areas |

**To run functional tests:**
```bash
go test -v ./quality/
```

**To run a code review:**
Start a new AI session and prompt: "Read quality/RUN_CODE_REVIEW.md and follow its instructions to review tree.go."

**To run the spec audit:**
Start a new AI session and prompt: "Read quality/RUN_SPEC_AUDIT.md and follow its instructions."
