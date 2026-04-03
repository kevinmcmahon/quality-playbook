# AGENTS.md — chi

## What This Project Does

`chi` is a lightweight, idiomatic HTTP router for Go, built on `net/http` and the `context` package. It routes HTTP requests using a radix trie, supports URL parameters (named, regexp, and wildcard), and provides a composable middleware system. Used in production at Cloudflare, Heroku, and others. No external dependencies — stdlib only.

```
go get -u github.com/go-chi/chi/v5
```

## Quick Start

```go
r := chi.NewRouter()
r.Use(middleware.Logger)
r.Use(middleware.Recoverer)
r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")
    w.Write([]byte("user: " + id))
})
http.ListenAndServe(":3000", r)
```

## Setup

```bash
go mod download   # no external deps for core; stdlib only
go build ./...
go test ./...
```

Requirements: Go 1.23 or later (chi supports the four most recent major Go versions).

## Build and Test Commands

```bash
# Run all tests
go test ./...

# Run with race detector (recommended for concurrent code changes)
go test -race ./...

# Run specific package
go test -v ./middleware/

# Run a specific test
go test -v -run TestMuxBasic .

# Run functional tests
go test -v ./quality/
```

## Architecture Overview

| File/Package | Purpose |
|---|---|
| `chi.go` | `Router` and `Routes` interface definitions |
| `mux.go` | `Mux` — main router: route registration, `ServeHTTP`, middleware management |
| `tree.go` | Radix trie: route insertion, URL pattern matching, 4 node types |
| `context.go` | `RouteContext`, `URLParam`, `RoutePattern`, `RouteParams` |
| `chain.go` | Middleware chaining (`Chain()`, `ChainHandler`) |
| `middleware/` | ~20 optional middlewares (Logger, Recoverer, Timeout, RealIP, Throttle, etc.) |

### Core Data Flow

```
HTTP Request
  → Mux.ServeHTTP (gets RouteContext from sync.Pool, calls Reset())
  → middleware chain (Use() stack)
  → Mux.routeHTTP (looks up route in radix trie)
  → endpoint handler (URLParam, RoutePattern available)
  → response written
  → RouteContext returned to pool
```

### URL Pattern Types (tree.go)

| Type | Example | Matches |
|---|---|---|
| `ntStatic` | `/users/list` | Exact string |
| `ntParam` | `/users/{id}` | Any chars up to next `/` |
| `ntRegexp` | `/users/{id:[0-9]+}` | Regexp match (Go RE2, no `/`) |
| `ntCatchAll` | `/files/*` | Rest of path including `/` |

Priority order: static > regexp > param > catch-all.

### Mux State Machine

The `Mux` has two states: **open** (`handler == nil`) and **locked** (`handler != nil`).

- Transition: first call to `handle()` or `With()` locks the mux
- In **open** state: `Use()` can add middleware, routes can be registered
- In **locked** state: routes can be added to the tree, but `Use()` panics
- No backward transition (no reset)

**Critical:** Always register all `Use()` middlewares before any routes on a Mux.

## Key Design Decisions

1. **sync.Pool for RouteContext** — reduces allocations under load. `Reset()` must zero all fields before reuse (see QUALITY.md Scenario 2).

2. **Last-wins for duplicate URL params** — `URLParam()` iterates backward. Inner sub-routers can override outer router params.

3. **Inline mux (Group/With)** — shares the parent's radix trie but has its own middleware stack. The `inline` flag bypasses the handler-nil state machine check.

4. **Panic on misconfiguration** — chi panics at registration time (not request time) for invalid patterns, duplicate mounts, nil handlers, and bad method names. This forces configuration errors to be caught at startup.

5. **No `/` matching by regexp** — the regexp node type uses Go RE2 but `tree.go` ensures `/` is never captured by non-wildcard segments.

## Known Quirks

- `r.Use()` after `r.Get(...)` panics with "all middlewares must be defined before routes on a mux". This is intentional.
- `Mount()` at a duplicate pattern panics. Both `pattern+"*"` and `pattern+"/*"` forms are checked.
- `Recoverer` re-panics `http.ErrAbortHandler` — this is intentional (don't recover WebSocket aborts).
- `Timeout` middleware only writes 504 on `context.DeadlineExceeded`, not on client disconnect.
- `RealIP` header priority: `True-Client-IP` > `X-Real-IP` > `X-Forwarded-For`. Only valid IPs accepted (via `net.ParseIP`).
- `RoutePattern()` trims trailing slashes (except root `/`). Read QUALITY.md Scenario 4 for sub-router path stripping behavior.

## Quality Docs

| File | Purpose |
|---|---|
| `quality/QUALITY.md` | Quality constitution — 10 fitness-to-purpose scenarios, coverage targets |
| `quality/functional_test.go` | Automated functional tests (Go, same-package, `go test ./quality/`) |
| `quality/RUN_CODE_REVIEW.md` | Code review protocol — 6 focus areas, guardrails |
| `quality/RUN_INTEGRATION_TESTS.md` | Integration test protocol — 5 test groups, concurrent correctness |
| `quality/RUN_SPEC_AUDIT.md` | Council of Three spec audit — 10 scrutiny areas |
| `quality/code_reviews/` | Saved code review findings |
| `quality/spec_audits/` | Saved spec audit findings |
| `quality/results/` | Test run results |

**Start every session by reading `quality/QUALITY.md`.**

Run the functional tests before any commit:

```bash
go test -v ./quality/
```

Run the full test suite before any PR:

```bash
go test -race ./...
```
