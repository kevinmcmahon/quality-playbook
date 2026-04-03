# Task: Filter Requirements to Nontrivial and Testable Subset

You are a quality engineer reviewing a set of derived requirements. Your goal is to filter out requirements that are trivially satisfied, too vague to test, or redundant — keeping only the nontrivial, specific, testable requirements that would be worth verifying against the codebase.

## Input

Read the file `requirements_raw.md` in the current directory. This contains requirements derived from NSQ's documentation for two subsystems:

1. **NSQD Configuration and Startup** (nsqd/nsqd.go, nsqd/options.go, nsqd/guid.go)
2. **TLS and Authentication Path** (nsqd/nsqd.go, internal/auth/authorizations.go)

## Filtering Criteria

**KEEP** a requirement if:
- It makes a specific, testable claim about what the code must do
- It involves a constraint that could plausibly be violated (not something the language or type system enforces automatically)
- It involves a numeric range, bit width, field encoding, or security policy where getting it wrong would produce silent incorrect behavior
- It describes a property that must hold across multiple files or components (cross-cutting concern)
- It describes a security configuration that must propagate to a specific connection or operation

**REMOVE** a requirement if:
- It's a truism that Go's type system or compiler already enforces (e.g., "string fields must contain strings")
- It's so vague that you couldn't write a test for it (e.g., "the system should be robust")
- It's redundant with another requirement that says the same thing more specifically
- It describes behavior that's already enforced by the standard library with no application-level code needed
- It's about code style, naming, or documentation rather than functional correctness

## Instructions

1. Read all requirements from `requirements_raw.md`
2. For each requirement, decide KEEP or REMOVE with a one-line rationale
3. Produce a filtered list containing only the KEEP requirements, organized by subsystem and category
4. For each kept requirement, preserve the original text, documentation citation, and specificity rating

## Output

Save the filtered requirements to `requirements_filtered.md` in the current directory. Format:

```
# Filtered Requirements

## Subsystem 1: NSQD Configuration and Startup

### Input Validation
- [REQ-1] <requirement text> (Source: <citation>) [specific/directional]
...

### API Contracts
- [REQ-N] <requirement text> (Source: <citation>) [specific/directional]
...

## Subsystem 2: TLS and Authentication Path

### Security Policy Propagation
- [REQ-M] <requirement text> (Source: <citation>) [specific/directional]
...
```

Number each requirement sequentially (REQ-1, REQ-2, ...) for reference in the verification pass.
