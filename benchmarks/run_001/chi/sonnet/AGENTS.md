# AGENTS.md — chi

## Project Description

**chi** is a lightweight, idiomatic, and composable HTTP router for building Go HTTP services. It is a pure Go library with zero external dependencies (only the standard library). Chi implements the `net/http` interface directly, so any standard middleware or handler works with it.

Chi routes requests using a Patricia Radix trie built for URL path routing. It supports named URL parameters (`{name}`), regexp-constrained parameters (`{id:\\d+}`), and catch-all wildcards (`*`). Request-scoped context (Go's `context.Context`) carries URL parameters and route pattern metadata across the handler chain.

**One-sentence summary:** Chi routes HTTP requests to Go handlers using a radix trie, extracts URL parameters into request context, and composes middleware chains without external dependencies.

## Repository Layout

```
chi/
├── chi.go          # Router and Routes interfaces (the contract)
├── mux.go          # Mux struct — route registration, middleware, ServeHTTP
├── tree.go         # Patricia Radix trie — route insertion and lookup
├── context.go      # Context struct — URL params, route pattern assembly
├── chain.go        # Middleware chain construction
├── mux_test.go     # Integration tests for the Mux
├── tree_test.go    # Unit tests for the trie
├── context_test.go # Tests for RoutePattern and context operations
├── pattern_test.go # Tests for patNextSegment pattern parsing
├── go.mod          # Module: github.com/go-chi/chi/v5, requires Go 1.23
├── middleware/     # Optional middleware package (Logger, Recoverer, etc.)
└── _examples/      # Example servers (rest, fileserver, etc.)
```

## Setup

```bash
# No external dependencies. Just:
go build ./...
go test ./...
```

Requires Go 1.23 or later (chi supports the four most recent Go major versions).

## Build and Test Commands

```bash
# Run all tests:
go test ./...

# Run tests with verbose output:
go test -v ./...

# Run tests with race detector (critical for chi — uses sync.Pool):
go test -race ./...

# Run specific test:
go test -v -run TestMuxBasic ./...

# Generate coverage profile:
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out

# Run benchmarks:
go test -bench=. -benchmem ./...
```

## Key Design Decisions

1. **Panic-at-registration, not at request-time.** Chi validates route configurations (pattern syntax, method names, duplicate mounts, nil handlers, late middleware) at registration time and panics immediately. This surfaces configuration bugs during server initialization rather than under live traffic.

2. **sync.Pool for route contexts.** `Mux.ServeHTTP` reuses `*Context` objects from a pool. `Context.Reset()` must zero all fields before returning a context to the pool. The race detector (`go test -race`) is the best tool for catching pool-safety violations.

3. **Middleware registered before routes.** Once the first route is registered, `mx.handler` is compiled (the full middleware + trie chain). Subsequent `Use()` calls panic. This ensures the middleware stack is complete and ordered correctly.

4. **Sub-routers share the URL param stack.** When a request traverses a `Mount()`ed subrouter, the parent's captured URL params (`rctx.URLParams`) are preserved. The subrouter appends its own params to the same slice. Both parent and child params are accessible via `chi.URLParam()` from any handler in the chain.

5. **No external dependencies.** Chi intentionally depends only on Go stdlib. This is a core feature — any middleware in the `net/http` ecosystem is compatible. Check `go.mod` before adding any import.

## Known Quirks

- **Method registration order matters for benchmarks, not behavior.** The methodMap is a fixed bit-set. Custom methods added via `RegisterMethod()` consume additional bits; the limit is `strconv.IntSize - 2` total methods.
- **`RoutePattern()` removes intermediate wildcards.** When using nested `Mount()`/`Route()`, each level appends `/*` to the pattern stack. `RoutePattern()` iteratively removes `/*/ ` from the middle of the pattern. The final wildcard at the end of the pattern is preserved.
- **`RawPath` takes priority over `Path` for routing.** If `r.URL.RawPath` is non-empty, chi uses it as the routing path. This matters for percent-encoded paths.
- **`Handle()` parses "METHOD path" from a single string.** `r.Handle("GET /ping", handler)` is equivalent to `r.Method("GET", "/ping", handler)`. This is a convenience but can be surprising.

## Quality Docs

This project has a quality playbook in `quality/`:

| File | Purpose |
|------|---------|
| `quality/QUALITY.md` | Quality constitution — coverage targets (tree.go: 90%, mux.go: 85%), 10 fitness-to-purpose scenarios, theater prevention |
| `quality/functional_test.go` | 38 automated functional tests — spec requirements, fitness scenarios, boundary cases |
| `quality/go.mod` | Go module for functional tests (uses replace directive to point to local chi repo) |
| `quality/RUN_CODE_REVIEW.md` | Code review protocol with 6 focus areas and guardrails |
| `quality/RUN_INTEGRATION_TESTS.md` | Integration test protocol — 5 test groups, parallel execution, race detector |
| `quality/RUN_SPEC_AUDIT.md` | Council of Three spec audit — 10 scrutiny areas, copy-pasteable prompt |
| `quality/code_reviews/` | Saved code review outputs |
| `quality/spec_audits/` | Saved spec audit outputs |
| `quality/results/` | Coverage profiles and test results |

### Running the Functional Tests

```bash
cd quality/
go test -v ./...
```

(The `quality/go.mod` uses a `replace` directive pointing to the local chi repo. Adjust the relative path if you've moved the quality directory.)

> **Note:** The functional tests were generated but not executed — Go was not available in the environment where the quality playbook was produced. Manual verification confirmed: correct package name (`chi_quality_tests`), correct import path (`github.com/go-chi/chi/v5` with replace directive), all referenced exported symbols exist in chi (`Context`, `NewRouteContext`, `RouteContext`, `URLParam`, `NewRouter`, `Router`, `Find`, `Match`, `RoutePatterns`). Run `go test -v ./...` from the `quality/` directory to execute and validate all 40 tests.

### Starting an AI Session

Read `quality/QUALITY.md` first. The 10 fitness-to-purpose scenarios describe the most important invariants to preserve. Before ending any session:

1. Run `go test ./...` from the chi module root — all tests must pass
2. Run `go test -race ./...` — no data races
3. Confirm no panic guards were removed or weakened
