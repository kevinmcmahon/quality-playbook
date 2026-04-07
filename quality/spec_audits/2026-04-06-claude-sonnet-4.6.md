# Spec Audit Report — Claude Sonnet 4.6

Date: 2026-04-06
Model: Claude Sonnet 4.6
Effective council slot: 1/3

## Scope
- `SKILL.md`, `README.md`, `AGENTS.md`, root references, packaged mirror, and generated `quality/` artifacts

## Findings

### BUG 1 — README license claim is inconsistent with the shipped license text
- **Evidence:** `README.md:5,77,87`; `LICENSE.txt:1`

### BUG 2 — README phase summary omits the tracked `2b` / `2c` / `2d` / verification lifecycle
- **Evidence:** `README.md:33,53-59`; `SKILL.md:282-285`

### BUG 3 — Install instructions do not copy `LICENSE.txt`
- **Evidence:** `README.md:17-28`; `AGENTS.md:32-42`

### BUG 4 — SKILL frontmatter says "six quality artifacts" although the body enumerates seven files
- **Evidence:** `SKILL.md:3,42`

## Improvement notes not promoted as code bugs
- Several Phase 2c/2d artifacts were incomplete at audit time (empty `quality/spec_audits/`, placeholder terminal gate, unchecked phase completion); these were run-state gaps that disappear once the playbook finishes.
- One regression-test source citation depended on the spec-audit triage file existing; once Phase 2c writes that file, the citation becomes valid.
