# Code Review Protocol: chi

## Bootstrap (Read First)

Before reviewing any code, read these files to establish context:

1. `quality/QUALITY.md` — Quality constitution: coverage targets, fitness-to-purpose scenarios, theater prevention
2. `README.md` — Project overview, routing syntax, middleware patterns, and design philosophy
3. `chi.go` — The Router and Routes interfaces — this is the contract all implementations must satisfy
4. `go.mod` — Module path (`github.com/go-chi/chi/v5`) and Go version requirements

## What to Check

### Focus Area 1: Patricia Radix Trie — `tree.go`

**Where:** `tree.go` — functions `InsertRoute`, `addChild`, `findRoute`, `patNextSegment`, `patParamKeys`, `findPattern`, `setEndpoint`, `FindRoute`

**What to look for:**
- `patNextSegment`: verify it correctly handles all four segment types (static, param, regexp, catch-all). Confirm the panic at tree.go:697 fires when `*` appears before `{`, and at tree.go:750 when `*` is not the final character.
- `patParamKeys`: verify duplicate key detection at tree.go:765 — does the loop check the *full* accumulated keys list, or only the most-recently-added key?
- `addChild`: verify the regexp compilation error handling — does `regexp.Compile` failure at tree.go:258 propagate correctly? Is the regexp anchored (`^...$`) before compilation?
- `FindRoute`: verify that `rctx.URLParams.Keys` and `rctx.URLParams.Values` are always appended in the same order. If keys are appended from `h.paramKeys` but values are appended from `rctx.routeParams.Values` separately, verify their lengths match before append.
- `findRoute` catch-all branch (tree.go:496-500): for ntCatchAll, the value is `search` (entire remaining path). Confirm the empty-path case — what happens when `search == ""`?

**Why:** The trie is chi's core differentiator. A misrouted request in production silently serves wrong data. Pattern parsing bugs affect every project built on chi.

---

### Focus Area 2: Mux Registration Guards — `mux.go`

**Where:** `mux.go` — functions `Use`, `Method`, `Mount`, `Route`, `handle`, `ServeHTTP`, `routeHTTP`

**What to look for:**
- `Use()` at mux.go:101: the check `if mx.handler != nil` — does this work correctly for inline muxes (`mx.inline == true`)? An inline mux's `mx.handler` is set to `routeHTTP` at handle-time (mux.go:429). Does calling `Use()` on an inline mux after a route is registered also panic?
- `Mount()` at mux.go:296-299: the `findPattern` check looks for `pattern+"*"` and `pattern+"/*"`. Verify both checks are needed — what pattern would only trigger one but not the other?
- `routeHTTP` at mux.go:444-458: the `routePath` selection logic. When both `r.URL.RawPath` and `r.URL.Path` are non-empty, `RawPath` takes priority. This is important for percent-encoded paths — verify this order matches Go's `net/http` URL parsing behavior.
- `nextRoutePath` at mux.go:487-494: relies on `rctx.routeParams.Keys[nx] == "*"` being the last entry. What if a subrouter has no wildcard — can `nx` be negative? The `nx >= 0` check guards this.
- `ServeHTTP` at mux.go:71-74: when a routing context already exists from a parent router (`rctx != nil`), `mx.handler.ServeHTTP` is called directly without resetting or re-fetching from pool. Verify this is intentional and doesn't bypass middleware.

**Why:** Registration-time panics are a feature, not a bug — they surface configuration mistakes at startup. If any panic guard fires in the wrong condition, or fails to fire in the right condition, it either crashes valid configurations or silently misroutes.

---

### Focus Area 3: Context and URL Parameter Handling — `context.go`

**Where:** `context.go` — functions `URLParam`, `URLParamFromCtx`, `RouteContext`, `RoutePattern`, `Reset`, `replaceWildcards`

**What to look for:**
- `URLParam` at context.go:101-107: the backward search (`k := len(x.URLParams.Keys) - 1; k >= 0; k--`). This returns the *last* matching key when duplicates exist. Verify this is intentional for subrouter shadowing — and that `patParamKeys` (tree.go:765) prevents duplicates within a single pattern.
- `Reset()` at context.go:82-96: verify ALL fields are zeroed. List the fields of `Context` struct (context.go:46-79) and check each one: `Routes`, `parentCtx`, `RoutePath`, `RouteMethod`, `URLParams.Keys/Values`, `routeParams.Keys/Values`, `routePattern`, `RoutePatterns`, `methodsAllowed`, `methodNotAllowed`. If any field is missing from Reset(), a pooled context carries stale state.
- `RoutePattern()` at context.go:123-134: the trailing slash cleanup (`strings.TrimSuffix(routePattern, "//")` then `strings.TrimSuffix(routePattern, "/")`). Verify that `"/"` itself is not trimmed — the check `if routePattern != "/"` guards this, but confirm the order of operations.
- `replaceWildcards` at context.go:139-144: the iterative `strings.Contains` + `strings.ReplaceAll` loop. Verify termination: it stops when no `"/*/"`remains. What about `/*/` at the very beginning or end of the pattern? Those should not match `"/*/"`  (needs leading and trailing `/`).

**Why:** A corrupted URL param (e.g., leaking from a previous pooled context) produces security-relevant bugs — a request to `/users/123` could see params from a previous request to `/orders/456`.

---

### Focus Area 4: Middleware Chain — `chain.go` and `mux.go`

**Where:** `chain.go` — `chain()`, `Chain()`, `ChainHandler`; `mux.go` — `updateRouteHandler()`

**What to look for:**
- `chain()` at chain.go:36-49: wraps `middlewares[len-1](endpoint)` first, then iterates backward. This means middleware index 0 executes *first* (outermost wrapper). Verify this matches the documented behavior ("middleware stack for any Mux will execute before searching for a matching route") — i.e., `r.Use(mw1); r.Use(mw2)` means `mw1` executes before `mw2`.
- `With()` at mux.go:236-257: copies parent middleware slice before appending. Verify `copy(mws, mx.middlewares)` uses the correct source length — if `len(mx.middlewares) == 0`, `copy` with a zero-length slice is a no-op, which is correct.
- `ChainHandler.ServeHTTP` at chain.go:30-32: calls `c.chain.ServeHTTP(w, r)` — not `c.Endpoint.ServeHTTP`. `c.chain` is the full middleware-wrapped handler. Verify `c.Endpoint` is only used for introspection (docgen), not for serving.

**Why:** Middleware order bugs are silent: auth middleware added first executing after logging middleware reverses security posture. Execution order must match registration order.

---

### Focus Area 5: Subrouter Context Propagation — `mux.go` Mount/Route

**Where:** `mux.go` — `Mount()` `mountHandler` closure, `nextRoutePath()`, `NotFound()`, `MethodNotAllowed()` propagation

**What to look for:**
- `mountHandler` closure at mux.go:309-321: shifts `rctx.RoutePath` using `nextRoutePath()`, then resets the wildcard URLParam to `""`. Verify that resetting `rctx.URLParams.Values[n]` to `""` doesn't lose the captured wildcard value that the parent needed — the subrouter creates a fresh context-derived path for its own routing without discarding the parent's captured parameters.
- `NotFound()` at mux.go:201-212: propagates to subrouters via `updateSubRoutes`. Verify the guard `if subMux.notFoundHandler == nil` — this prevents overwriting an explicitly set subrouter NotFound handler. Verify the inline mux case (`mx.inline && mx.parent != nil`) chains the inline middleware stack around the not-found handler.
- `updateSubRoutes()` at mux.go:497-504: iterates over `mx.tree.routes()` and casts `r.SubRoutes.(*Mux)`. Verify the `ok` check — non-`*Mux` subrouters (e.g., `http.HandlerFunc` mounted directly) are silently skipped without propagating the NotFound handler. Is this intentional?

**Why:** Missing propagation of NotFound/MethodNotAllowed handlers to subrouters produces inconsistent 404 behavior — subrouters return Go's default 404 text instead of the application's custom error page.

---

### Focus Area 6: Regex and Pattern Parsing — `tree.go` patNextSegment

**Where:** `tree.go` — `patNextSegment()` lines 685-753, `addChild()` regexp compilation lines 254-261

**What to look for:**
- Anonymous regexp parameter at chi.go:40 (`{:\\d+}` — empty name before colon): verify `patNextSegment` handles an empty key before `:`. The `key, rexpat, isRegexp := strings.Cut(key, ":")` — if `key == ""` and `isRegexp == true`, the param key is `""`. Does `FindRoute` store an empty-string key in `routeParams.Keys`? Does `URLParam(r, "")` return something meaningful?
- The closing delimiter loop at tree.go:706-718 tracks `cc` (curly-brace open/close count). Verify nested braces: pattern `/{id:{\\d+}}` — does `cc` correctly reach 0 at the outer `}`?
- `patNextSegment` panic at tree.go:696: checks `ws < ps` (wildcard before param). What if `ws == ps`? That would mean `*` and `{` at the same position, which is impossible, but confirm.
- Regexp anchor injection at tree.go:737-744: adds `^` prefix and `$` suffix if missing. Verify this doesn't double-anchor a regexp that already has them — the `if rexpat[0] != '^'` check handles the prefix, `if rexpat[len-1] != '$'` handles the suffix.

**Why:** Pattern parsing is invoked once at registration. Silent misparse means every request to that route is affected. Anonymous regexp params and deeply-nested patterns are unusual but documented.

---

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific file:line for a finding, do not include it.
- **Read function bodies, not just signatures.** Don't assume a function is correct based on its name — read the body.
- **If unsure whether something is a bug or intentional design**, flag it as QUESTION, not BUG.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase first. Many behaviors are split across `mux.go`, `tree.go`, and `context.go`.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect, produce wrong behavior, or could cause failures.
- **Do NOT suggest adding comments or documentation** unless the absence of documentation is itself a correctness concern.

## Output Format

Save findings to `quality/code_reviews/YYYY-MM-DD-[reviewer].md`

For each file reviewed:

### filename.go
- **Line NNN:** [BUG / QUESTION / INCOMPLETE] Description. Expected: what should happen. Actual: what happens. Why it matters.

### Summary
- Total findings by severity (BUG / QUESTION / INCOMPLETE)
- Files with no findings
- Overall assessment: SHIP IT / FIX FIRST / NEEDS DISCUSSION

## Phase 2: Regression Tests

After the code review produces BUG findings, write `quality/regression_test.go` in the chi module directory with tests that:
- Target the exact code path and line numbers from the BUG finding
- Fail on the current implementation, confirming the bug is real
- Include the finding description in the test comment

Run with `go test -v -run TestRegression ./...` from the chi module root.

Report results as:
| Finding | Test | Result | Confirmed? |
|---------|------|--------|------------|
| [description] | TestRegression_[name] | FAILED/PASSED | YES/NO/NEEDS INVESTIGATION |
