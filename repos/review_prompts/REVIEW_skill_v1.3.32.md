# Council Review: Quality Playbook Skill v1.3.32

**Date:** 2026-04-12
**File:** `SKILL.md` (1,494 lines)
**Supporting files:** `repos/quality_gate.sh`, `references/` directory (verification.md, functional_tests.md, review_protocols.md, spec_audit.md, integration_tests.md)

## Purpose of This Review

This is a review of the **skill itself** — the SKILL.md specification and its supporting infrastructure — not a review of benchmark run results. We want to know: is this skill well-designed? Are there contradictions, gaps, ambiguities, or structural problems that would cause models to produce poor output?

## What This Skill Does

The Quality Playbook skill takes any codebase and generates a complete quality system: requirements, functional tests, code review protocols, bug reports with patches, TDD verification, integration testing, spec audits, and an AI bootstrap file. It runs in phases (exploration → artifact generation → review/audit → verification → convergence check) and is designed to be self-contained in a single session.

## Version History Context

The skill has been through 30+ iterations driven by benchmark testing against 8 open-source repos (chi, cobra, express, gson, httpx, javalin, serde, virtio) across multiple languages (Go, JavaScript, Java, Python, Rust, C, Kotlin). Each version addressed specific failure modes discovered in benchmarks. Key milestones:

- **v1.3.24:** Mechanical verification immutability, forbidden probe pattern
- **v1.3.25:** Artifact file-existence gate, benchmark isolation
- **v1.3.26:** Script-verified closure gate, sidecar JSON validation
- **v1.3.27:** Deep JSON validation, mandatory regression-test patches
- **v1.3.28:** Gate-enforced writeup inline diffs
- **v1.3.29:** Multi-pass architecture, EXPLORATION.md handoff
- **v1.3.30:** Self-contained execution (no external orchestration)
- **v1.3.31:** EXPLORATION.md depth, TDD summary shape, date validation, cross-run contamination detection
- **v1.3.32 (this version):** Test file extension validation, minimum UC count, triage executable evidence

## Your Review Tasks

### 1. Structural Coherence

Read the full SKILL.md. Does it flow logically? Are the phases well-ordered? Are there sections that contradict each other, or instructions that are impossible to follow given what earlier sections require? Is there unnecessary repetition that could confuse a model?

Specific things to check:
- Does the multi-pass execution section (lines 96-111) clearly describe when to use EXPLORATION.md vs keeping context in memory?
- Do the Phase 2 sub-phases (2a through 2d) have clear entry/exit criteria?
- Is the convergence check (Phase 3) well-defined enough that a model could implement it correctly?

### 2. Instruction Clarity

For each major instruction in SKILL.md, assess: would a model reading this for the first time know exactly what to do? Flag any instructions that are:
- **Ambiguous** — could be interpreted in multiple valid ways
- **Under-specified** — missing critical details a model would need
- **Over-specified** — so detailed they become confusing or contradictory
- **Buried** — important instructions hidden in the middle of paragraphs where a model might miss them

### 3. Gate and Validation Design

The skill has multiple validation gates:
- Mechanical verification (Phase 2a)
- quality_gate.sh (Phase 2d)
- Self-check benchmarks (Phase 3)
- Sidecar JSON post-write validation
- Convergence check

Are these gates well-placed? Do they catch the right failure modes? Are there gaps where a model could produce bad output that no gate catches? Are there gates that are too strict (causing false failures) or too lenient?

Review `quality_gate.sh` specifically:
- Is the test file extension detection robust enough?
- Is the UC count threshold (5) appropriate?
- Is the triage evidence check (warn, not fail) at the right severity?
- Does the cross-run contamination check handle edge cases (repos with hyphens in names, repos without version suffixes)?

### 4. Sidecar JSON Schemas

The skill defines two JSON schemas: `tdd-results.json` and `integration-results.json`. Review them for:
- Are all fields necessary?
- Are there fields that should exist but don't?
- Are the enum values well-chosen?
- Is the "copy the template verbatim" instruction realistic for models?

### 5. Reference File Architecture

The skill splits content between SKILL.md and reference files in `references/`. Is this split well-designed? Are there things in SKILL.md that should be in references (to reduce SKILL.md size)? Are there things in references that are so critical they should be in SKILL.md (to ensure models see them)?

### 6. Scalability and Generalization

The skill was developed primarily against 8 specific repos. Are there design decisions that are over-fitted to those repos? Would the skill work well on:
- Very small projects (single-file utilities)?
- Very large monorepos?
- Projects with no existing tests?
- Projects with no specifications (only source code)?
- Projects in languages not yet tested (Swift, Kotlin Multiplatform, Elixir)?

### 7. Token Efficiency

At 1,494 lines, the skill is large. Is there content that could be removed without losing capability? Are there sections that repeat the same instruction in different words? Could any sections be compressed without loss of clarity?

### 8. Risk Assessment

What are the most likely ways this skill fails in practice? For each failure mode, is there a gate that catches it? Rank the top 5 failure modes by likelihood and severity.

### 9. v2.0 Readiness

The goal is a v2.0 release where the skill reliably produces a complete, conformant quality system on any codebase without human intervention. Based on your review, what's blocking v2.0? What changes would you prioritize?

### 10. Recommended Changes

Provide specific, actionable recommendations. For each:
- **Priority:** P0 (blocking), P1 (important), P2 (nice to have)
- **What:** The specific change
- **Why:** What failure mode it addresses
- **Where:** File and approximate location

## Files to Read

1. **`SKILL.md`** — the full skill specification (primary review target)
2. **`repos/quality_gate.sh`** — the mechanical validation gate
3. **`references/verification.md`** — the 45+ benchmark checklist
4. **`references/functional_tests.md`** — functional test generation guide
5. **`references/review_protocols.md`** — code review protocol details
6. **`references/spec_audit.md`** — spec audit and triage process
7. **`references/integration_tests.md`** — integration test protocol details

Start with SKILL.md (the complete read), then quality_gate.sh, then skim the references to understand how the split works.
