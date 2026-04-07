# Requirements Review Protocol: Quality Playbook v1.3.8

## How to use

This protocol helps you review `quality/REQUIREMENTS.md` for completeness and accuracy. It is self-contained: read the requirements, this protocol, and `quality/REFINEMENT_HINTS.md`, then walk through the use cases and linked REQ numbers.

**Before starting:** Read the Project Overview, Use Cases, and Cross-cutting Concerns sections in `quality/REQUIREMENTS.md`.

### Choose a review mode

1. **Mode 1 — Self-guided review.** Pick use cases that need the most scrutiny.
2. **Mode 2 — Fully guided review.** Walk the use cases in order.
3. **Mode 3 — Cross-model audit.** A different model checks whether every domain marked COVERED in `quality/COMPLETENESS_REPORT.md` is actually covered by the cited requirements.

All progress and feedback are tracked in `quality/REFINEMENT_HINTS.md`.

## Mode 1: Self-guided review

Present the use cases from `quality/REQUIREMENTS.md` as a numbered checklist:

1. Use Case 1: Install the skill into a target repository
2. Use Case 2: Execute the full playbook with supplemental docs
3. Use Case 3: Review, track, and close defects
4. Use Case 4: Run the integration protocol for a skill repository
5. Use Case 5: Run a Council-of-Three spec audit
6. Use Case 6: Refine the generated requirements over time

For the selected use case:

1. Show actor, preconditions, steps, postconditions, and alternative paths.
2. List the linked REQ numbers.
3. Ask whether any linked requirement is missing, too weak, or wrong.
4. Record feedback in `quality/REFINEMENT_HINTS.md`.
5. Mark the use case reviewed in the Review Progress checklist.

## Mode 2: Fully guided review

Walk Use Cases 1-6 sequentially.

For each use case:

1. Show the use case summary.
2. Show each linked requirement in full.
3. Ask what is missing, overstated, or unclear.
4. Record feedback in `quality/REFINEMENT_HINTS.md`.
5. Mark the use case reviewed before moving on.

After all use cases, review the cross-cutting concerns:

- Mirror integrity
- Closure integrity
- Evidence provenance
- Metadata accuracy
- Spec-first execution

Ask whether any of these concerns need new requirements or sharper conditions of satisfaction.

## Mode 3: Cross-model audit

Read `quality/COMPLETENESS_REPORT.md` and verify that each covered domain is actually supported by the cited REQ numbers.

Specifically check:

1. **Package/mirror integrity** — Do REQ-001 and REQ-017 really cover both mirror sync and installation completeness?
2. **Execution lifecycle** — Do REQ-002, REQ-004, and REQ-005 really cover the six-phase lifecycle and terminal gate?
3. **Audit baseline** — Do REQ-003, REQ-012, and REQ-013 distinguish validated docs, effective council handling, and stale artifacts?
4. **Integration accuracy** — Do REQ-014 and REQ-015 truly cover both relative-path execution and skill-specific integration checks?
5. **Versioned refinement** — Does REQ-016 cover both review tracking and version history/backups?

Write findings to `quality/REFINEMENT_HINTS.md` under a `## Cross-Model Audit` heading with:

- Verified domains
- Gaps found
- Orphaned requirements
- Use cases that mention behavior without a linked requirement

## Expected REFINEMENT_HINTS updates

When using this protocol, add entries like:

- `REQ-017: install snippets still miss a packaged file`
- `Use Case 4: integration protocol should mention saved result filenames`
- `Cross-Model Audit: metadata accuracy cites REQ-017 correctly`

The output of this review is not a new requirements file. It is actionable feedback for `quality/REFINE_REQUIREMENTS.md`.
