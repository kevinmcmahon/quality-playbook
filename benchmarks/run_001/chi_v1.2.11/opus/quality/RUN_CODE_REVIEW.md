# Code Review Protocol: chi

## Bootstrap (Read First)

Before reviewing, read these files for context:
1. `quality/QUALITY.md` — Quality constitution and fitness-to-purpose scenarios
2. `chi.go` — Router interface definitions, type contracts
3. `mux.go` — Core router implementation, middleware chaining, subrouter mounting
4. `tree.go` — Radix trie implementation, pattern parsing, route matching
5. `context.go` — RouteContext, URL parameter extraction, sync.Pool lifecycle

## What to Check

### Focus Area 1: Radix Trie Route Matching (`tree.go`)

**Where:** `tree.go` — `FindRoute()`, `findRoute()`, `patNextSegment()`, `InsertRoute()`
**What:**
- Boundary conditions in pattern parsing: unbalanced `{}`, empty patterns, adjacent params
- Regex compilation errors: verify `regexp.MustCompile()` is called at registration time, not per-request
- Node type priority: static > regexp > param > catchall — ensure tie-breaking is correct
- Slice bounds: `rctx.routeParams.Values` access after `append` must stay within allocated bounds
**Why:** A routing bug silently sends requests to wrong handlers. Unlike a crash, misrouting produces valid-looking responses with wrong data.

### Focus Area 2: sync.Pool RouteContext Lifecycle (`mux.go`, `context.go`)

**Where:** `mux.go:60-92` (ServeHTTP), `context.go:82-96` (Reset)
**What:**
- Reset completeness: every mutable field on `Context` must be zeroed/sliced
- Pool Get/Put ordering: context must be Put back AFTER handler completes
- No handler retaining context reference past request lifetime
- `[:0]` vs `nil` — ensure capacity preservation for performance
**Why:** Context leak under concurrent load causes cross-request data contamination. One request sees another request's URL parameters.

### Focus Area 3: Middleware Chain Composition (`chain.go`, `mux.go`)

**Where:** `chain.go:36-49` (chain function), `mux.go:236-257` (With), `mux.go:262-268` (Group)
**What:**
- Right-to-left wrapping order in `chain()` — last middleware wraps endpoint first
- `With()` copies parent middlewares correctly (deep copy vs shallow)
- Inline mux `handler` field set correctly for route registration after `With()`
- `updateRouteHandler()` called exactly once, before any route serves
**Why:** Incorrect middleware ordering silently changes request/response transformation. Auth middleware running after response middleware defeats the purpose.

### Focus Area 4: Subrouter Mounting (`mux.go:289-340`)

**Where:** `mux.go` — `Mount()`, `nextRoutePath()`, `updateSubRoutes()`
**What:**
- Wildcard URL param cleared after path consumption (`rctx.URLParams.Values[n] = ""`)
- Mount conflict detection: `findPattern(pattern+"*")` and `findPattern(pattern+"/*")`
- NotFound/MethodNotAllowed handler inheritance from parent to mounted subrouter
- Pattern suffix handling: with and without trailing `/`
**Why:** Incorrect path consumption in nested mounts causes all downstream routes to receive wrong paths, producing cascading 404s for valid requests.

### Focus Area 5: Method Routing and 405 Handling (`mux.go`, `tree.go`)

**Where:** `mux.go:441-485` (routeHTTP), `tree.go` (FindRoute method-specific matching)
**What:**
- `methodNotAllowed` vs `notFound` disambiguation after `FindRoute()`
- Allow header populated with correct methods for 405 responses
- `methodMap` lookup for unsupported methods — what happens with custom methods?
- `RegisterMethod()` overflow check (`strconv.IntSize` limit)
**Why:** RFC 9110 §15.5.6 requires 405 with Allow header when method doesn't match. Returning 404 instead causes API clients to assume the resource doesn't exist.

### Focus Area 6: Defensive Patterns in Middleware (`middleware/*.go`)

**Where:** All middleware files, especially `recoverer.go`, `throttle.go`, `compress.go`
**What:**
- Recoverer: `http.ErrAbortHandler` re-panic, `Connection: Upgrade` header check
- Throttle: channel operations ordering (backlog → token), timer cleanup on all paths
- Compress: wildcard pattern validation, encoder nil check, response writer wrapping
- Content-Type: empty body bypass (`ContentLength == 0`)
**Why:** Middleware bugs affect every request passing through the stack. A Recoverer bug that swallows ErrAbortHandler breaks WebSocket connections. A Throttle leak exhausts all tokens over time.

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific line, do not include the finding.
- **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name.
- **If unsure whether something is a bug or intentional**, flag it as a QUESTION rather than a BUG.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase. If found in a different file, that's a location defect, not a missing feature.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect or could cause failures.
- **Exhaust the sibling set.** When you find a bug in one method of a type, grep for every other method on that type and check them for the same bug pattern.

## Output Format

Save findings to `quality/code_reviews/YYYY-MM-DD-reviewer.md`

For each file reviewed:

### filename.ext
- **Line NNN:** [BUG / QUESTION / INCOMPLETE] Description. Expected vs. actual. Why it matters.

### Summary
- Total findings by severity
- Files with no findings
- Overall assessment: SHIP IT / FIX FIRST / NEEDS DISCUSSION

## Phase 2: Regression Tests

After the review produces BUG findings, write regression tests in `quality/regression_test.go` that reproduce each bug. Each test should fail on the current implementation, confirming the bug is real. Report results as:

| Finding | Test | Result | Confirmed? |
|---------|------|--------|------------|
| [Description] | TestRegression_... | FAILED (expected) / PASSED (unexpected) | YES / NO / NEEDS INVESTIGATION |
