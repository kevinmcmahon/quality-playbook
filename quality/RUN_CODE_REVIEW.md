# Code Review Protocol: Quality Playbook v1.3.8

## Bootstrap (Read First)

Before reviewing, read these files:

1. `quality/QUALITY.md`
2. `quality/REQUIREMENTS.md`
3. `README.md`
4. `AGENTS.md`
5. `SKILL.md`
6. `references/review_protocols.md`
7. `references/spec_audit.md`

This repository is specification-primary. Review the Markdown product as if it were executable logic: installation instructions, phase definitions, legal metadata, and required section headers are functional behavior.

## Scope for this repository

Prioritize these files and their packaged mirrors:

- `README.md`
- `AGENTS.md`
- `SKILL.md`
- `references/review_protocols.md`
- `references/spec_audit.md`
- `references/requirements_pipeline.md`
- `.github/skills/` mirror files when checking packaging consistency

## Pass 1: Structural Review

Read the files and report anything that looks structurally wrong.

### Guardrails

- **Line numbers are mandatory.**
- **Read the full paragraph or section, not just headings.**
- **If unsure, use QUESTION instead of BUG.**
- **Grep before claiming something is missing.**
- **Do not suggest style changes.**

### What to look for in this repo

- Packaging omissions (a copied skill that references files the install docs never copy)
- Contradictory public metadata (license, version, repository layout)
- Phase/state drift between README, AGENTS, and `SKILL.md`
- Required protocol sections that are described in one file but absent from another

## Pass 2: Requirement Verification

Read `quality/REQUIREMENTS.md`. For each REQ, verify whether the current repository satisfies it.

### Output format

For each requirement or tightly related requirement group:

#### REQ-NNN: Title
- **Status:** SATISFIED / VIOLATED / PARTIALLY SATISFIED / NOT ASSESSABLE
- **Evidence:** `file:line` — short quoted evidence
- **Analysis:** What the repository does versus what the requirement demands
- **Severity:** Only for VIOLATED or PARTIALLY SATISFIED items

### Repository-specific focus

- REQ-001 and REQ-017: packaging, install snippets, public metadata
- REQ-004 and REQ-005: tracked phase model and terminal-gate persistence
- REQ-012 and REQ-013: audit baseline, effective council, and stale artifact handling
- REQ-014 and REQ-015: integration protocol accuracy for a skill repo

## Pass 3: Cross-Requirement Consistency

Compare requirement pairs that share a concept:

1. **Packaging completeness:** REQ-001 vs REQ-017
2. **Run-state integrity:** REQ-004 vs REQ-005
3. **Audit evidence trustworthiness:** REQ-003 vs REQ-012 vs REQ-013
4. **Integration correctness:** REQ-009 vs REQ-014 vs REQ-015

For each shared concept:

- Summarize what each requirement claims
- Cite the code/docs that implement or violate those claims
- State whether the requirements remain mutually consistent

## Regression tests

Every confirmed BUG must map to `quality/test_regression.py` with one of:

- `REGRESSION TEST: test_name`
- `EXEMPTION: [reason]`

Regression tests in this repo use `unittest.expectedFailure` and must assert the desired correct behavior, not the current broken state.

## Combined summary

When saving the review results:

- Merge the findings from all three passes
- Count confirmed BUGs, QUESTIONS, and inconsistencies
- Verify every BUG has closure evidence
- Save the review to `quality/code_reviews/YYYY-MM-DD-review.md`

For this repo, a strong review is expected to find documentation/packaging defects that are invisible to style-only linting.
