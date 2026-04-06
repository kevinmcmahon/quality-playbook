# Code Review: middleware/url_format.go (CHI-29)

## File: middleware/url_format.go

### Finding 1: Negative Slice Index Panic - Path Without Slash

**Type:** BUG
**Line:** 59-60
**Severity:** Critical

**Description:**
When a path contains a dot (extension) but no forward slash character, the code panics with "runtime error: slice bounds out of range".

```go
59:     base := strings.LastIndex(path, "/")
60:     idx := strings.LastIndex(path[base:], ".")
```

If `path` is a value like `"articles.json"` (no "/" character):
- Line 59: `base` becomes `-1` (not found)
- Line 60: `path[-1:]` is an invalid slice expression and causes a runtime panic

While HTTP request paths typically start with `/`, this middleware could be called in edge cases or tests where this doesn't hold. The code must handle this gracefully.

**Root Cause:** No validation that `base >= 0` before slicing.

**Impact:** Any request with a dotted filename in an unusual path context (or outside chi's normal routing) will crash the middleware, affecting all requests through that handler.

---

### Finding 2: Nil Pointer Dereference When RouteContext is Nil

**Type:** BUG
**Line:** 66
**Severity:** High

**Description:**
The code modifies `rctx.RoutePath` without checking if `rctx` is nil, even though `rctx` can be nil as shown by the nil check on line 54.

```go
53:  rctx := chi.RouteContext(r.Context())
54:  if rctx != nil && rctx.RoutePath != "" {
55:      path = rctx.RoutePath
56:  }
...
66:      rctx.RoutePath = path[:idx]
```

If `chi.RouteContext(r.Context())` returns nil (middleware used outside a chi router, or context not properly initialized):
1. The nil check passes on line 54 (skipped because `rctx == nil`)
2. If a format is found (lines 58-65), line 66 attempts `rctx.RoutePath = ...` causing a nil pointer panic

**Root Cause:** Assignment to `rctx.RoutePath` on line 66 lacks nil guard despite earlier evidence that rctx can be nil.

**Impact:** In edge cases where the middleware is used without a proper chi RouteContext, requests with extractable formats will panic.

---

### Finding 3: Syntax Error in Example Code

**Type:** BUG
**Line:** 40
**Severity:** Low

**Description:**
Example code contains a syntax error that would not compile.

```go
40:  case "xml:"
```

Should be:
```go
case "xml":
```

The colon is inside the string literal (`"xml:"`) instead of being the case label separator (`:` after the quote). This inconsistency with line 38's `case "json":` syntax and line 42's `default:` will confuse users reading the documentation example.

**Root Cause:** Typo in documentation example.

**Impact:** Users copying the example code will get a compilation error or unintended behavior (matching `"xml:"` instead of `"xml"`).

---

## Summary

- **1 Critical BUG:** Negative slice index panic (line 59-60)
- **1 High BUG:** Nil pointer dereference (line 66)
- **1 Low BUG:** Example syntax error (line 40)

**Recommended Actions:**
1. Add bounds check: `if base < 0 { base = 0 }` or handle missing slash case separately
2. Add nil check before line 66: `if rctx != nil { rctx.RoutePath = path[:idx] }`
3. Fix example on line 40: change `case "xml:"` to `case "xml":`
