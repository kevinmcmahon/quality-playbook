# Requirements Refinement Protocol: Quality Playbook v1.3.8

## How to use

This protocol updates `quality/REQUIREMENTS.md` based on `quality/REFINEMENT_HINTS.md`. It is model-agnostic and is designed for repeated passes with different AI tools.

## Before starting

1. Read `quality/REFINEMENT_HINTS.md`.
2. Read `quality/REQUIREMENTS.md`.
3. Read `quality/CONTRACTS.md`.
4. Read `quality/VERSION_HISTORY.md`.

## Step 1: Backup and version

1. Read the current version from `quality/VERSION_HISTORY.md`.
2. Copy the current quality files to `quality/history/vX.Y/`.
3. Bump the minor version (`v1.0` -> `v1.1`).
4. Update the version stamp at the top of `quality/REQUIREMENTS.md`.

## Step 2: Process feedback

Categorize each hint as one of:

- **Gap — missing requirement**
- **Gap — missing condition**
- **Gap — missing use case coverage**
- **Sharpening — vague condition**
- **Correction — wrong content**
- **Cross-model audit finding**
- **Removal (user-directed only)**

## Step 3: Make changes

Rules:

1. Do not delete or weaken requirements unless the user explicitly directs a removal.
2. Do not renumber existing requirements.
3. Add new requirements at the end of the appropriate section using the next REQ number.
4. Every change must trace back to a specific hint.

## Step 4: Report changes

Append a refinement report to `quality/REFINEMENT_HINTS.md`:

```markdown
## Refinement Pass — v1.1
Date: YYYY-MM-DD
Model: [model]

### Changes made
- REQ-018 (NEW): ...
- REQ-017: sharpened installation completeness conditions ...

### Feedback items not addressed
- "[quoted hint]" — reason: ...

### Summary
Added N new requirements, modified N existing requirements, updated N use cases.
Total requirements: N (was N).
```

## Step 5: Update version history

Add a new row to `quality/VERSION_HISTORY.md` documenting the version, date, model, author, requirement count, and summary.

## Step 6: Refresh completeness

If changes affect covered domains or cross-artifact gaps, update `quality/COMPLETENESS_REPORT.md` to cite the new or modified REQ numbers.

## Multi-model refinement note

This repository benefits from model diversity. Prior `docs_gathered/` reviews show that different auditors catch different documentation drifts. Run this protocol with multiple models until new passes stop adding substantive requirements.
