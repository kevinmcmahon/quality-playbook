# Code Review: CHI-29 — middleware/url_format.go

## middleware/url_format.go

- **Line 66:** [BUG] **Severity: High.** Nil pointer dereference when `rctx` is nil. The nil-check on line 54 only guards the `path` assignment — if `rctx` is nil but `path` (from `r.URL.Path`) contains a dot, execution falls through to line 66 which writes `rctx.RoutePath = path[:idx]`, panicking on a nil `rctx`. `chi.RouteContext()` (context.go:27-29) returns nil when the route context key is absent from the request context, which happens if the middleware is used outside of a chi router. The guard on line 54 should also protect the write on line 66, e.g. by wrapping lines 58-68 in an `if rctx != nil` block or by adding a nil check before line 66.

- **Line 40:** [BUG] **Severity: Low.** Documentation example has a typo: `case "xml:"` should be `case "xml":`. The trailing colon is inside the string literal, so any user copying this example will have a case branch that never matches the format value `"xml"` — it would only match the literal string `"xml:"`, which the middleware never produces.

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 1     |
| Medium   | 0     |
| Low      | 1     |

- **Total findings:** 2
- **Overall assessment:** FIX FIRST — The nil-pointer dereference on line 66 will panic at runtime if `URLFormat` middleware is used without a chi route context on the request.
