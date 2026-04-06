# Code Review: middleware/recoverer.go

## File: middleware/recoverer.go

---

## Finding 1: BUG - Negative Slice Index Panic in Package Parsing (if branch)

**Type:** BUG
**File:** middleware/recoverer.go
**Line:** 129-131
**Severity:** High

**Description:**

Lines 129-131 contain a critical bug where `strings.Index()` can return -1, leading to a runtime panic:

```go
idx = strings.Index(pkg, ".")
method = pkg[idx:]           // Line 130: panics if idx == -1
pkg = pkg[0:idx]             // Line 131: panics if idx == -1
```

When `pkg` does not contain a dot (e.g., a bare function name like "main" instead of "main.func"), `strings.Index()` returns -1. Go's slice operations do not accept negative indices: `pkg[-1:]` and `pkg[0:-1]` will panic with "invalid slice index -1".

**Consequence:** The Recoverer middleware itself panics when attempting to pretty-print a malformed stack trace, defeating the purpose of recovering from panics. Instead of gracefully logging the panic, the middleware crashes.

---

## Finding 2: BUG - Negative Slice Index Panic in Method Parsing (else branch)

**Type:** BUG
**File:** middleware/recoverer.go
**Lines:** 135-137
**Severity:** High

**Description:**

Lines 135-137 have the same negative index vulnerability:

```go
idx = strings.Index(method, ".")
pkg += method[0:idx]         // Line 136: panics if idx == -1
method = method[idx:]        // Line 137: panics if idx == -1
```

When `method` does not contain a dot, `strings.Index()` returns -1, causing panics in the slice operations.

**Consequence:** Same as Finding 1—the Recoverer middleware panics instead of handling malformed stack traces gracefully.

---

## Finding 3: BUG - Slice Bounds Underflow in Stack Processing

**Type:** BUG
**File:** middleware/recoverer.go
**Line:** 76
**Severity:** Medium

**Description:**

Line 76 assumes `len(lines) >= 2` when removing the last 2 elements:

```go
lines = lines[0 : len(lines)-2]  // Line 76
```

However, in the loop on line 73-79:

```go
for i := len(stack) - 1; i > 0; i-- {
    lines = append(lines, stack[i])       // Line 74: append 1 element
    if strings.HasPrefix(stack[i], "panic(0x") {
        lines = lines[0 : len(lines)-2]   // Line 76: remove 2 elements
        break
    }
}
```

On the first iteration (when `i == len(stack) - 1`), only one element is appended before the check on line 75. If the panic line is the very last element of the stack, `len(lines) == 1` when line 76 executes. This results in `lines[0:-1]`, which panics with "invalid slice index -1".

**Consequence:** Stack traces where the panic line is the final element will cause a panic in the pretty printer.

---

## Summary

- **Total Bugs Found:** 3
- **Critical Issues:** 2 (negative slice indices)
- **Recommendations:**
  1. Check `idx >= 0` before using it in slice operations (lines 129, 136-137)
  2. Check `len(lines) >= 2` before removing 2 elements (line 76)
