# Task: Verify Code Against Derived Requirements

You are a quality engineer performing a requirements verification audit. You have a list of testable requirements derived from documentation. Your job is to check whether the source code satisfies each requirement. This is a pure verification pass — you are NOT doing a general code review, NOT looking for other bugs, NOT evaluating code quality. Your only job is: for each requirement, does the code satisfy it or not?

## Input

Read the file `requirements_filtered.md` in the current directory. This contains numbered requirements (REQ-1, REQ-2, ...) organized by subsystem.

## Source Files to Check

### Subsystem 1: NSQD Configuration and Startup
- `nsqd/nsqd.go` — NSQD initialization (New function), configuration validation, startup
- `nsqd/options.go` — Configuration struct, defaults, field types
- `nsqd/guid.go` — GUID generation, bit layout, worker ID encoding

### Subsystem 2: TLS and Authentication Path
- `nsqd/nsqd.go` — TLS configuration setup (buildTLSConfig and related functions)
- `internal/auth/authorizations.go` — Auth server HTTP client, authorization queries

## Instructions

For each requirement in `requirements_filtered.md`:

1. **Find the relevant code.** Identify the specific file(s) and line(s) where this requirement should be implemented.

2. **Assess satisfaction.** One of:
   - **SATISFIED**: The code implements this requirement correctly. Quote the specific code that satisfies it.
   - **VIOLATED**: The code does NOT satisfy this requirement. Explain exactly what's wrong — what the code does vs. what the requirement says it should do. Quote the specific code that violates it.
   - **PARTIALLY SATISFIED**: Some aspects are implemented but others are missing. Explain what's covered and what's not.
   - **NOT ASSESSABLE**: The requirement can't be checked from these files alone (e.g., it depends on code in other files not listed here).

3. **For violations, assess severity.** What would happen if this requirement is not met? Silent data corruption? Security bypass? Startup crash? Incorrect behavior under specific inputs?

## Output Format

Save your verification report to `verification_report.md` in the current directory. Format:

```
# Requirements Verification Report

## Subsystem 1: NSQD Configuration and Startup

### REQ-1: <requirement text>
**Status**: SATISFIED / VIOLATED / PARTIALLY SATISFIED / NOT ASSESSABLE
**Evidence**: <specific code quote with file and line>
**Analysis**: <explanation>
[If VIOLATED] **Severity**: <impact description>

### REQ-2: ...
...

## Subsystem 2: TLS and Authentication Path

### REQ-M: ...
...

## Summary

| Requirement | Status | Severity |
|------------|--------|----------|
| REQ-1 | SATISFIED | — |
| REQ-2 | VIOLATED | High — ... |
| ... | ... | ... |

Total: X satisfied, Y violated, Z partially satisfied, W not assessable
```

Be precise. Quote actual code. If a requirement is satisfied, show the code that satisfies it. If violated, show what the code does instead and explain why it doesn't meet the requirement.
