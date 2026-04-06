# Code Review: CHI-08 — middleware/url_format.go

## middleware/url_format.go

### Finding 1
- **Line 52:** [BUG] `URLFormat` reads `r.URL.Path` directly instead of checking `rctx.RoutePath` first. Other chi middleware that modifies the routing path (`StripSlashes` at strip.go:17-20, `CleanPath` at clean_path.go:16-22) follows the pattern of checking `rctx.RoutePath` first and falling back to `r.URL.Path` (or `r.URL.RawPath`). Because `URLFormat` skips this check, if it is composed after any middleware that has already set `rctx.RoutePath` (e.g., `StripSlashes` or `CleanPath`), it will ignore their path modifications and operate on the original request URL instead. This breaks middleware composition — the extension stripping will be applied to the wrong path, and the resulting `rctx.RoutePath` will overwrite the previous middleware's path correction.
- **Severity:** Medium
- **Type:** BUG

### Finding 2
- **Line 54:** [BUG] The outer guard `strings.Index(path, ".") > 0` uses `> 0` instead of `>= 0`. This means a path where the dot appears at index 0 (e.g., a relative path like `.hidden`) would skip extension parsing entirely. While HTTP paths normally start with `/` making index-0 dots unlikely, the inner check on line 56 (`strings.Index(path[base:], ".")`) independently validates the dot position relative to the last slash, so the outer guard is both redundant and subtly stricter than the inner logic. If `rctx.RoutePath` were used (per Finding 1) and a previous middleware set it to a value without a leading slash, this guard would incorrectly skip valid extensions.
- **Severity:** Low
- **Type:** QUESTION

### Finding 3
- **Line 40:** [BUG] Doc comment example has `case "xml:"` (with a trailing colon inside the string literal) instead of `case "xml":` (colon outside the string as the Go case label terminator). A user copying this example verbatim would get a switch case that never matches, since the middleware stores `"xml"` (without colon) as the format value. The correct line should be `case "xml":`.
- **Severity:** Low
- **Type:** BUG

### Finding 4
- **Line 52-63:** [QUESTION] The middleware uses `r.URL.Path` (decoded path) but does not consider `r.URL.RawPath` (percent-encoded original). The router at mux.go:418-419 prefers `r.URL.RawPath` when it is set. If a request has percent-encoded characters (causing `RawPath` to differ from `Path`), the middleware will strip the extension from the decoded path and set `RoutePath`, which the router will then use for matching. This changes the routing behavior for encoded URLs — the router would normally match against the encoded path, but now matches against the decoded-and-trimmed path. Compare with `CleanPath` (clean_path.go:18-19) which correctly checks `r.URL.RawPath` first.
- **Severity:** Medium
- **Type:** QUESTION

## Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 0     |
| Medium   | 2     |
| Low      | 2     |

- **Total findings:** 4
- **Files reviewed:** middleware/url_format.go

**Overall assessment:** NEEDS DISCUSSION — The middleware works correctly in isolation for common cases, but has inconsistencies with the rest of the chi middleware ecosystem around `RoutePath` handling and `RawPath` awareness. These should be resolved to ensure reliable middleware composition.
