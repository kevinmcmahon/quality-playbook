# Code Review: CHI-29 — middleware/url_format.go

**Reviewer:** Claude Sonnet
**Date:** 2026-03-31
**File reviewed:** `middleware/url_format.go`

---

## middleware/url_format.go

### Line 66: BUG — Nil pointer dereference when rctx is nil

- **Finding type:** BUG
- **Severity:** High
- **Line:** 66

**Description:**
`rctx.RoutePath = path[:idx]` is executed unconditionally inside the `if idx > 0` block. However, `rctx` can be nil — the nil guard at line 54 only protects the *read* of `rctx.RoutePath` (setting `path = rctx.RoutePath`), not the subsequent *write* on line 66. If `rctx == nil` (e.g., `URLFormat` is composed with a plain `net/http` handler, or placed before chi sets up its routing context), and the request URL contains a dot (e.g., `/articles/1.json`), line 66 panics with a nil pointer dereference.

**Expected:** When `rctx == nil`, the format extension should still be extracted and stored in the context, but `r.URL.Path` should be updated instead of `rctx.RoutePath` (matching the pattern used by `strip.go` lines 25–29).

**Actual:** Server panics on any request whose path contains a dot when chi's routing context is absent.

**Comparison evidence:** `middleware/strip.go:25–29` shows the correct idiom:
```go
if rctx == nil {
    r.URL.Path = newPath
} else {
    rctx.RoutePath = newPath
}
```
`url_format.go` performs no such guard before line 66.

---

### Line 40: BUG — Typo in example code makes sample uncompilable

- **Finding type:** BUG
- **Severity:** Low
- **Line:** 40

**Description:**
The godoc example includes `case "xml:"` (colon inside the string literal). The correct Go switch-case syntax is `case "xml":` (colon outside the string). As written, the case matches the literal string `"xml:"`, which is never returned by the middleware (the middleware strips the dot and returns the bare extension, e.g. `"xml"` not `"xml:"`). Code copied from this example would silently never match the XML branch.

**Expected:** `case "xml":`
**Actual:** `case "xml:"` — colon is inside the string, making the case both a syntax oddity and a logical dead branch when compared against the middleware's actual output.

---

## Summary

| Severity | Count | Type  |
|----------|-------|-------|
| High     | 1     | BUG   |
| Low      | 1     | BUG   |

**Total:** 2 findings (2 BUG, 0 QUESTION, 0 SUGGESTION)

**Overall assessment: FIX FIRST**

The High severity nil pointer dereference (line 66) will panic any server using `URLFormat` outside chi's routing context (or in a composition where chi's context isn't yet populated), on any request path containing a dot. The pattern for fixing this is already established in `strip.go`.
