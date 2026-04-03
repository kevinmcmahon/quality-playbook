# Code Review: middleware/url_format.go

## Summary
Reviewed the URLFormat middleware that extracts file extensions from request paths and modifies the routing path accordingly. Found 2 bugs and verified related components.

---

## Findings

### 1. BUG: Multiple dots in filename causes wrong format extraction
- **File:** middleware/url_format.go
- **Line:** 56
- **Severity:** High
- **Description:**

  The code uses `strings.Index(path[base:], ".")` to find the extension separator, but this finds the FIRST dot after the last slash, not the LAST dot. For paths with multiple dots in the filename, this produces incorrect results.

  **Example trace for path `/articles/1.2.json`:**
  - Line 55: `base = strings.LastIndex(path, "/")` → 9
  - Line 56: `idx = strings.Index(path[9:], ".")` → finds first dot in "/1.2.json" → position 2 relative to substring
  - Line 59: `idx += base` → 2 + 9 = 11
  - Line 60: `format = path[12:]` → **"2.json"** ✗ (WRONG - should be "json")
  - Line 63: `rctx.RoutePath = path[:11]` → "/articles/1"

  **Impact:** Requests to `/articles/1.2.json` will have format set to "2.json" instead of "json", causing format-based rendering logic to fail silently.

  **Fix:** Change line 56 from `strings.Index` to `strings.LastIndex`:
  ```go
  idx := strings.LastIndex(path[base:], ".")
  ```

---

### 2. BUG: Example code contains syntax error
- **File:** middleware/url_format.go
- **Line:** 40
- **Severity:** Medium
- **Description:**

  The example code in the documentation shows an incorrect case statement:
  ```go
  case "xml:"
  ```

  This matches the string literal `"xml:"` (with colon), but the middleware extracts format without the colon. For paths like `/articles/1.xml`, the format value is `"xml"` (without colon), so this case will never match.

  **Impact:** Users copying the example code will write switch cases that don't match the extracted format values, leading to all requests falling through to the default case.

  **Fix:** Change line 40 to:
  ```go
  case "xml":
  ```

---

## Verification Checklist

✓ **Read complete function bodies** — Traced entire URLFormat handler (lines 47-72)
✓ **Mapped against fitness scenarios:**
  - Scenario #5 (Catch-all specificity): Format extraction specificity affected by multiple-dot bug
  - Scenario #8 (Boundary paths): Code handles empty paths, paths with single segments correctly, but fails on multiple-dot filenames
✓ **Line numbers mandatory** — All findings include exact line numbers
✓ **Grepped before claiming missing** — Verified contextKey is defined in middleware.go (not a bug)

---

## Files Verified

- `middleware/middleware.go` — contextKey type is properly defined (lines 17-23)
- `middleware/url_format.go` — No compile errors; contextKey correctly used on line 14

---

## No Further Issues

- Context lifecycle correctly handles routing context modification (line 62-63)
- Request context wrapping correctly preserves routing context changes (line 67)
- Nil checks not required for this middleware pattern
- No state leakage between requests (new context created for each request)
