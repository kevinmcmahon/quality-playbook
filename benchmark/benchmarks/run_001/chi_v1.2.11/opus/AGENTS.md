# AGENTS.md — chi

## Project Description

Chi is a lightweight, idiomatic HTTP router for Go. It is 100% compatible with the standard `net/http` library and has zero external dependencies. Chi provides a composable middleware stack, URL pattern matching with named parameters, regex constraints, and wildcards, plus subrouter mounting for modular API design.

## Setup

```bash
# Clone and verify
go mod download
go build ./...
```

**Requirements:** Go 1.23+ (per go.mod)

## Build & Test

```bash
# Run all tests
go test ./...

# Run with race detector (recommended for any concurrency changes)
go test -race ./...

# Run specific package tests
go test -v ./middleware/...

# Run with coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## Architecture Overview

```
chi/
├── chi.go          # Router and Routes interface definitions
├── mux.go          # Mux implementation: routing, middleware chain, subrouter mounting
├── tree.go         # Radix trie: pattern parsing, route insertion, route finding
├── context.go      # RouteContext: URL params, route patterns, sync.Pool lifecycle
├── chain.go        # Middleware chaining utility
├── middleware/      # 40+ middleware implementations
│   ├── recoverer.go    # Panic recovery
│   ├── throttle.go     # Rate limiting
│   ├── compress.go     # Response compression
│   ├── realip.go       # Client IP extraction
│   ├── strip.go        # Trailing slash handling
│   ├── logger.go       # Request logging
│   └── ...
└── _examples/       # Usage examples
```

### Core Data Flow

1. **Request arrives** → `Mux.ServeHTTP()` in mux.go
2. **RouteContext obtained** from `sync.Pool` (or reused from parent router)
3. **Context reset** → `Reset()` clears all fields, preserves slice capacity
4. **Middleware chain executes** → right-to-left wrapping, left-to-right execution
5. **Route matched** → `tree.FindRoute()` traverses radix trie
6. **URL params extracted** → added to `RouteContext.URLParams`
7. **Handler executes** → writes response
8. **Context returned** to sync.Pool for reuse

### Key Design Decisions

- **sync.Pool for RouteContext:** Reduces GC pressure under high-throughput. `Reset()` uses `[:0]` slicing (not nil) to preserve backing array capacity.
- **Radix trie routing:** O(k) lookup where k = pattern length. Node types: static, regexp, param, catchall.
- **Panic at registration time:** Invalid patterns, nil handlers, middleware-after-routes all panic during setup, not during request serving. This is intentional — fail fast during initialization.
- **Inline mux for With()/Group():** Creates a lightweight mux that shares the parent's tree but has its own middleware stack. This enables per-route middleware without copying the entire tree.

### Known Quirks

- `Use()` panics if called after any route is registered — middleware must be defined first
- `RegisterMethod()` uses bit flags — maximum number of custom methods is limited by `int` size
- Adjacent URL parameters without a delimiter (`{id}{name}`) are not supported
- Wildcards (`*`) must be the final element in a pattern
- `Handle("METHOD /pattern", handler)` supports space-separated method+pattern parsing

## Quality Docs

All quality playbook files are in the `quality/` directory:

| File | Purpose |
|------|---------|
| `quality/QUALITY.md` | Quality constitution — fitness-to-purpose scenarios, coverage targets, theater prevention |
| `quality/functional_test.go` | Automated functional tests — spec requirements, scenario tests, boundary tests |
| `quality/RUN_CODE_REVIEW.md` | Code review protocol with guardrails |
| `quality/RUN_INTEGRATION_TESTS.md` | Integration test protocol with test matrix |
| `quality/RUN_SPEC_AUDIT.md` | Council of Three multi-model spec audit protocol |
| `quality/code_reviews/` | Code review output directory |
| `quality/spec_audits/` | Spec audit output directory |
| `quality/results/` | Test results output directory |

### Quick Start

```bash
# Run functional tests
go test -v ./quality/...

# Run with race detector
go test -race -v ./quality/...

# Run a code review
# Read quality/RUN_CODE_REVIEW.md and follow its instructions

# Run a spec audit (Council of Three)
# Read quality/RUN_SPEC_AUDIT.md and follow its instructions
```
