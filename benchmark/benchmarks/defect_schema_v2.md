# QPB Defect Entry Schema v2

## Design Rationale

The original defect entries describe bugs as patch notes: "X was broken, fix: Y." This format couples the defect definition to the fix, making it impossible to score reviews that find the same violation using different language. The v2 schema separates the **requirement** (what correct behavior looks like) from the **violation** (how the code fails) and the **fix** (how it was repaired). This lets a scorer match on whether a review identified the *requirement violation*, which is what a quality engineer would do.

## Schema

```json
{
  "id": "NSQ-01",
  "fix_commit": "cfbd287",
  "pre_fix_commit": "1362af17d",
  "files_changed": ["nsqd/channel.go"],

  "requirement": {
    "statement": "A testable statement of what correct behavior looks like, written so that a reviewer reading the code without knowing about the fix could identify the violation.",
    "category": "One of the requirement categories below.",
    "strength": "STRONG | WEAK — WEAK means the requirement is debatable or domain-specific."
  },

  "violation": {
    "description": "How the code violates the requirement. References specific functions, variables, and mechanisms.",
    "location": "Function or code path where the violation occurs.",
    "mechanism": "Short label for the violation mechanism (e.g., 'unsynchronized read after lock release')."
  },

  "original_description": "The original patch-note-style description from the ground truth dataset.",

  "scoring_guidance": {
    "what_a_reviewer_would_say": ["List of phrases a reviewer would use if they found this violation."],
    "not_sufficient": ["Phrases that sound similar but don't identify the specific violation."]
  }
}
```

## Requirement Categories

1. **concurrency** — Shared mutable state must be synchronized. Map/slice access, atomic alignment, lock ordering.
2. **resource-lifecycle** — Resources (connections, file handles, goroutines, buffers) must be created, used, and cleaned up correctly. Includes shutdown ordering, leak prevention, signal handling.
3. **error-handling** — Errors must be propagated, reported accurately, and not swallowed. Error messages must identify the correct entity. Fatal vs. recoverable error classification.
4. **input-validation** — Protocol parameters, configuration values, and user inputs must be validated against domain constraints before use.
5. **api-contract** — Function return values, protocol responses, and negotiated parameters must match their documented or implied contracts.
6. **arithmetic-boundary** — Division by zero, off-by-one indexing, counter overflow, and range calculations must be guarded.
7. **data-integrity** — Accounting invariants, deduplication, serialization correctness, and data structure consistency must be maintained.
8. **security** — Authentication, authorization, and TLS configuration must be applied consistently across all endpoints and connections.
