# Code Review Protocol: chi

## Bootstrap (Read First)

Before reviewing, read these files for context:

1. `quality/QUALITY.md` — Quality constitution and fitness-to-purpose scenarios
2. `README.md` — Project overview, design philosophy, routing syntax
3. `chi.go` — Router and Routes interface definitions
4. `mux.go` — Mux implementation (route registration, ServeHTTP, middleware management)
5. `context.go` — RouteContext, URLParam, RoutePattern
6. `tree.go` — Radix trie insert and routing logic

## What to Check

### Focus Area 1: Mux State Machine (handler nil vs non-nil)

**Where:** `mux.go` — `Use()` (line ~101), `handle()` (line ~417), `updateRouteHandler()` (line ~511), `ServeHTTP()` (line ~63)

**What:**
- Verify that `Use()` panics with the exact message "all middlewares must be defined before routes" when called after any route is registered
- Verify that `handle()` calls `updateRouteHandler()` only once (when `mx.handler == nil`)
- Verify that `ServeHTTP()` falls back to `NotFoundHandler()` when `mx.handler == nil`
- Verify that the `inline` flag correctly bypasses the `handler == nil` check in `handle()`

**Why:** If the state machine is broken — e.g., if `Use()` silently succeeds after routes — middleware registered late will not apply. This produces endpoints that appear protected but are not. The bug is silent and only caught by runtime observation.

---

### Focus Area 2: Radix Trie Node Type Priority

**Where:** `tree.go` — `FindRoute()`, `addChild()`, node type constants (`ntStatic`, `ntRegexp`, `ntParam`, `ntCatchAll`)

**What:**
- Verify that static segments take priority over param segments (e.g., `/article/near` must match before `/article/{id}`)
- Verify that param segments take priority over catch-all `*`
- Verify that regexp patterns correctly use `Go RE2` syntax and that `/` is never matched by `\d+` or other non-wildcard patterns
- Verify that `patNextSegment()` correctly identifies all four node types
- Check the `Sort()` call on child nodes — verify sorting order enforces static > regexp > param > catchAll

**Why:** Wrong priority order silently routes to the wrong handler. A `/article/near` request hitting `{id}` instead of `near` would extract "near" as a numeric ID and propagate it to the database layer — producing a query error or data leak, not a 404.

---

### Focus Area 3: RouteContext Reset and Pool Reuse

**Where:** `mux.go:ServeHTTP()` (lines ~81–91), `context.go:Reset()` (lines ~82–95)

**What:**
- Verify that every field in `RouteContext` listed in `Reset()` is also zeroed (not just some)
- Verify that `Reset()` uses slice re-slicing (`[:0]`) not reassignment (`= nil`) for all slices — reassignment would discard the underlying array and defeat the pooling purpose
- Verify that `rctx.Reset()` is called BEFORE `rctx.Routes = mx` and before the request is processed — a Reset after processing would lose routing data
- Verify that `pool.Put(rctx)` is called unconditionally after `ServeHTTP`, including on panics (check for `defer` usage)

**Why:** A RouteContext that isn't fully reset will leak URL parameters from a previous request into the current one. Under concurrent load (when pool reuse occurs), this produces `/users/alice` receiving the `id` of a prior request's `/users/bob` — a data leak that only manifests under traffic and is invisible in sequential tests.

---

### Focus Area 4: Mount() Path Stripping and Sub-Router Isolation

**Where:** `mux.go:Mount()` (lines ~289–340), `mux.go:nextRoutePath()` (lines ~487–494)

**What:**
- Verify that `nextRoutePath()` correctly strips the mount prefix by reading the last wildcard param
- Verify that after stripping, the sub-router receives a path starting with `/`
- Verify that the wildcard param reset (`rctx.URLParams.Values[n] = ""`) runs after the path is shifted, not before
- Verify that `Mount()` on a pattern that already has a mounted handler panics (check both `pattern+"*"` and `pattern+"/*"` in `findPattern`)
- Verify that `NotFound` and `MethodNotAllowed` handlers propagate from parent to sub-router when the sub-router's handlers are nil

**Why:** Incorrect path stripping causes every sub-router route to return 404. Missing duplicate detection allows silent overwrite of sub-router registrations. Failure to propagate error handlers means the sub-router uses Go's default 404 (different from the application's custom 404), creating UX inconsistency.

---

### Focus Area 5: Middleware Edge Cases

**Where:**
- `middleware/recoverer.go` — `ErrAbortHandler` re-panic (line ~27), WebSocket Upgrade check (line ~39)
- `middleware/timeout.go` — `ctx.Err() == context.DeadlineExceeded` guard (line ~38)
- `middleware/realip.go` — `net.ParseIP()` validation (line ~52), header priority order (lines ~44–51)
- `middleware/throttle.go` — panic guards (lines ~45–49), token channel sizing (line ~67)

**What:**
- In `Recoverer`: confirm `http.ErrAbortHandler` is compared with `==` (not type assertion), and that re-panic occurs before any response is written
- In `Recoverer`: confirm that `w.WriteHeader(500)` is guarded by the `Connection != "Upgrade"` check
- In `Timeout`: confirm the deferred function checks `ctx.Err() == context.DeadlineExceeded` AFTER `next.ServeHTTP` returns (not before) — checking before would always see nil
- In `RealIP`: confirm the priority is `True-Client-IP` > `X-Real-IP` > `X-Forwarded-For`, and that only the first IP from `X-Forwarded-For` is used
- In `Throttle`: confirm that `backlogTokens` capacity = `Limit + BacklogLimit`, not just `BacklogLimit`

**Why:** Each of these is a subtle correctness issue. Swallowing `ErrAbortHandler` corrupts the HTTP stream. Writing 504 on client cancel floods alerting. Using the wrong IP header priority leaks internal network addresses. Over-sizing the backlog channel silently raises the effective request limit.

---

### Focus Area 6: URL Parameter Extraction Correctness

**Where:** `context.go:URLParam()` (line ~101), `tree.go:FindRoute()` param extraction

**What:**
- Verify that `URLParam()` iterates backward and returns the last match (not first)
- Verify that `URLParam()` returns `""` for a missing key (not panics)
- Verify that `URLParamFromCtx()` nil-checks the context before calling `RouteContext()`
- Verify that `RouteContext()` uses a type assertion with the `, ok` pattern (not bare assertion) — a bare assertion on a context without `RouteCtxKey` would panic

**Why:** URLParam with first-match semantics would break sub-router param override (inner routers couldn't shadow outer params). A bare type assertion in RouteContext() would panic on any context not created by chi — breaking `r.Use()` with standard library adapters.

---

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific line, do not include the finding.
- **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name.
- **If unsure whether something is a bug or intentional**, flag it as a QUESTION rather than a BUG.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase. If found in a different file, that's a location defect, not a missing feature.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect or could cause failures.
- **Exhaust the sibling set.** When you find a bug in one method of a type, grep for every other method on that type and check them for the same bug pattern. When you find a boundary condition that breaks one call site, check every other call site that processes the same kind of input.

## Output Format

Save findings to `quality/code_reviews/YYYY-MM-DD-reviewer.md`

For each file reviewed:

### filename.ext
- **Line NNN:** [BUG / QUESTION / INCOMPLETE] Description. Expected vs. actual. Why it matters.

### Summary
- Total findings by severity
- Files with no findings
- Overall assessment: SHIP IT / FIX FIRST / NEEDS DISCUSSION
