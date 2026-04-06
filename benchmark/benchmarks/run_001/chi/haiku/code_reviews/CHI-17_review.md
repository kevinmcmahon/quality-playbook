# Code Review: middleware/recoverer.go

## Summary
Reviewed the `Recoverer` middleware which recovers from panics, logs them, and returns HTTP 500 responses. Found one significant bug affecting the pretty-stack formatting logic, and one minor issue with error handling.

---

## Findings

### 1. BUG: Unreachable code in decorateLine due to early TrimSpace
- **File & Line:** middleware/recoverer.go, lines 102-109
- **Severity:** Medium
- **Description:**

The `decorateLine` function calls `strings.TrimSpace(line)` at line 102, which removes all leading whitespace including tabs. However, at line 108, the code checks `if strings.HasPrefix(line, "\t")`. This condition can never be true because:

1. Line 102: `line = strings.TrimSpace(line)` removes all leading whitespace
2. The outer if-condition at line 103 checks: `strings.HasPrefix(line, "\t") || strings.Contains(line, ".go:")`
3. We only reach the else-block at line 107 if NEITHER condition is true
4. Therefore, `strings.HasPrefix(line, "\t")` at line 108 is guaranteed to be false

The code at lines 108-109 is unreachable dead code:
```go
if strings.HasPrefix(line, "\t") {
    return strings.Replace(line, "\t", "      ", 1), nil
}
```

**Impact:** The intended formatting for indented lines (replacing leading tabs with spaces) is never executed. All non-source, non-function-call lines get 4 spaces prepended (line 111) regardless of their original indentation structure.

**Root Cause:** `TrimSpace` was likely added to normalize input, but it eliminates the leading tabs that the subsequent logic was designed to detect and format.

---

### 2. QUESTION: Missing error handling for stderr write
- **File & Line:** middleware/recoverer.go, line 48
- **Severity:** Low
- **Description:**

In the `PrintPrettyStack` function, the call to `os.Stderr.Write(out)` at line 48 does not check for errors:

```go
if err == nil {
    os.Stderr.Write(out)  // error ignored
} else {
    // print stdlib output as a fallback
    os.Stderr.Write(debugStack)  // error also ignored
}
```

Both branches ignore potential write errors. While this is fallback error-handling code (not critical path), it could mask issues where stderr is unavailable or the write fails.

**Note:** This is low severity since there is no programmatic recovery possible if stderr fails, but it's worth noting for completeness.

---

## Guardrail Compliance

✓ Line numbers provided for all findings
✓ Read complete function bodies (Recoverer, decorateLine, parse, PrintPrettyStack)
✓ Traced data flow through control paths
✓ Verified with Grep before flagging issues
✓ No style suggestions, only correctness issues reported

---

## Recommendation

**Fix the BUG:** Either:
1. Remove the `TrimSpace` call and check for tabs before trimming, OR
2. Remove the tab-checking logic if normalization is required

The current code has dead code that indicates a logic error in the stack formatting pipeline.
