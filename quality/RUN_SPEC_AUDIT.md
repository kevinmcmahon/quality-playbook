# Spec Audit Protocol: Quality Playbook v1.3.8

## Context files to read

1. `quality/QUALITY.md`
2. `quality/REQUIREMENTS.md`
3. `README.md`
4. `AGENTS.md`
5. `SKILL.md`
6. `references/review_protocols.md`
7. `references/spec_audit.md`
8. `references/requirements_pipeline.md`
9. `docs_gathered/` (all relevant bootstrap reviews and design history)

## The definitive audit prompt

Use the following prompt unchanged with three independent AI models:

> Act as the Tester. Read the actual repository files and compare them against the specifications listed above.
>
> **Rules:**
> - ONLY list defects.
> - For EVERY defect, cite exact file and line numbers.
> - Before claiming missing, grep the repo.
> - Before claiming a behavior exists, read the relevant paragraph or section body.
> - Classify each finding as MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM.
> - Preserve the requirement confidence tag from `quality/QUALITY.md` or `quality/REQUIREMENTS.md`.
>
> **This repository is specification-primary.** Treat drift in README, AGENTS, `SKILL.md`, the reference docs, or the packaged `.github/skills/` mirror as functional defects when it changes how the skill is installed, interpreted, or audited.

## Project-specific scrutiny areas

1. **Packaged skill completeness:** Read `README.md`, `AGENTS.md`, and `.github/skills/`. Do the install snippets copy every shipped file the packaged skill depends on?
2. **Public metadata consistency:** Compare README/AGENTS claims about version, phases, and licensing against `SKILL.md` and `LICENSE.txt`.
3. **Tracker closure integrity:** Read `SKILL.md` Phase 2b-2d and verify that the generated `quality/` artifacts actually satisfy those closure requirements.
4. **Docs baseline trustworthiness:** Use `docs_gathered/` as evidence, but verify its factual claims against the live repo before promoting them.
5. **Integration protocol fidelity:** Check whether `RUN_INTEGRATION_TESTS.md` reflects the required skill integration section and field-table discipline.
6. **Mirror consistency:** Confirm the root docs and `.github/skills/` mirror are truly equivalent.

## Pre-audit docs validation

Before triaging audit findings, validate 2-3 claims from `docs_gathered/`:

| Claim source | Claim | Verification against current repo | Result |
|--------------|-------|-----------------------------------|--------|
| `docs_gathered/qpb-1.3.6-bootstrap-review-cursor.md` | The skill requires a persisted `## Terminal Gate Verification` section in `PROGRESS.md` | `SKILL.md` lines 474-488 explicitly require the section and persisted count statement | Accurate |
| `docs_gathered/qpb-1.3.6-bootstrap-review-copilot.md` | The six tracked phases are `1`, `2`, `2b`, `2c`, `2d`, and `3` | `SKILL.md` lines 279-285 define exactly those phases | Accurate |
| `docs_gathered/qpb-1.3.6-bootstrap-review-cowork.md` | `docs_gathered/` improves requirement depth and closure coverage when used explicitly | Current repo contains bootstrap-review evidence and the live skill instructs agents to use supplemental docs in Phase 1 | Accurate but context-dependent |

If any future claim fails validation, downgrade findings that rely on it to NEEDS REVIEW.

## Running the audit

1. Run three independent auditors with the definitive prompt.
2. Save the reports to:
   - `quality/spec_audits/2026-04-06-gpt-5.4.md`
   - `quality/spec_audits/2026-04-06-claude-sonnet-4.6.md`
   - `quality/spec_audits/2026-04-06-claude-opus-4.6.md`
3. Merge findings in a triage file: `quality/spec_audits/2026-04-06-triage.md`

## Triage rules

- Log the effective council size explicitly.
- "All three" = highest confidence.
- "Two of three" = high confidence.
- "One only" = needs verification via a verification probe.
- Do not silently reuse stale reports from older runs.

### Verification probe

When auditors disagree on a factual claim, give a fresh model the disputed claim plus the cited lines and ask for ground truth only. Use the probe to resolve whether the code/docs actually diverge.

## Categorize each confirmed finding

Use one of:

- **Real code bug**
- **Spec bug**
- **Design decision**
- **Documentation gap**
- **Missing test**
- **Inferred requirement wrong**

Every confirmed **Real code bug** must be added to `quality/PROGRESS.md` and mapped to `quality/test_regression.py`.
