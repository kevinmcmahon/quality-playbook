# Behavioral Contract Extraction
Generated: 2026-04-06
Scope: Canonical root docs (`SKILL.md`, `README.md`, `AGENTS.md`, `LICENSE.txt`) plus `references/*.md`; `.github/skills/` is treated as the packaged mirror of the same product.
Source files analyzed: 14
Total contracts extracted: 41

## Summary by category
- METHOD: 13
- CONFIG: 5
- ERROR: 8
- INVARIANT: 9
- COMPAT: 2
- LIFECYCLE: 4

### README.md (5 contracts)
1. [METHOD] Quick-start installation copies the skill and reference files into GitHub Copilot and Claude Code skill directories.
2. [INVARIANT] The public description positions the playbook as a complete quality system grounded in requirements, review, and audit.
3. [LIFECYCLE] The documented run sequence explains how a full playbook execution progresses across phases.
4. [COMPAT] The repository structure section defines the expected shipped package layout.
5. [INVARIANT] Public metadata such as version and license must match the shipped files.

### AGENTS.md (3 contracts)
1. [METHOD] New AI sessions should bootstrap themselves by reading the skill and reference docs.
2. [CONFIG] Install snippets for Claude Code and GitHub Copilot use canonical relative skill paths.
3. [INVARIANT] AGENTS.md must describe the current repository layout and point sessions at the right quality context.

### SKILL.md (8 contracts)
1. [METHOD] The skill must start by printing the exact mandatory startup banner.
2. [METHOD] The `execute` entry point must run the entire playbook, not a partial subset.
3. [LIFECYCLE] Phase 1 must finish exploration before artifact generation starts.
4. [INVARIANT] `quality/PROGRESS.md` is the authoritative external memory for the run.
5. [ERROR] The terminal gate must stop the run if BUG tracker arithmetic does not reconcile.
6. [ERROR] The `With docs` metadata field must match actual `docs_gathered/` presence.
7. [METHOD] Phase 3 verification must check tests, metadata consistency, and stale text cleanup.
8. [METHOD] Phase 4 presentation must include a summary table, quick-start prompts, and improvement menu.

### references/constitution.md (2 contracts)
1. [INVARIANT] Every QUALITY.md scenario must map to at least one automated test and carry a requirement tag.
2. [INVARIANT] Coverage targets must justify themselves with project-specific risks, not generic percentages.

### references/functional_tests.md (3 contracts)
1. [METHOD] Functional tests are organized into spec requirements, fitness scenarios, and boundaries/edge cases.
2. [ERROR] Placeholder tests and setup-dependent phantom fixtures are forbidden.
3. [CONFIG] Cross-variant coverage and self-contained setup are expected defaults.

### references/requirements_pipeline.md (4 contracts)
1. [METHOD] The requirements pipeline runs in five phases: extraction, derivation, coverage, completeness, and narrative.
2. [INVARIANT] Requirement headings use the canonical `### REQ-NNN: Title` format.
3. [LIFECYCLE] Version history, backups, and refinement state persist across runs.
4. [ERROR] After review/audit, completeness must be refreshed against those findings before final verdict.

### references/requirements_review.md (1 contract)
1. [METHOD] Interactive requirement review records progress and feedback in `quality/REFINEMENT_HINTS.md`.

### references/requirements_refinement.md (2 contracts)
1. [METHOD] Refinement passes back up the current quality set, bump minor version, and apply only traceable changes.
2. [LIFECYCLE] Every refinement updates `VERSION_HISTORY.md` and reports handled vs. unhandled feedback.

### references/review_protocols.md (5 contracts)
1. [METHOD] Code review runs as three isolated passes with distinct scopes.
2. [ERROR] Every confirmed BUG needs executable regression closure or an explicit exemption.
3. [ERROR] Regression tests must assert desired behavior, not the current broken behavior.
4. [METHOD] Integration protocols use relative paths, explicit execution UX, and deep post-run verification.
5. [METHOD] Skill/LLM repositories require a dedicated skill integration test section.

### references/spec_audit.md (5 contracts)
1. [METHOD] Every triage includes `## Pre-audit docs validation`, even without supplemental docs.
2. [ERROR] Effective council size downgrades confidence and forbids silently reusing stale auditor outputs.
3. [METHOD] Verification probes resolve factual disagreements instead of majority vote.
4. [ERROR] Partial sessions must be marked as failed, not misreported as zero-finding runs.
5. [ERROR] Carried-over artifacts need provenance headers when they are not regenerated.

### references/schema_mapping.md (1 contract)
1. [CONFIG] Boundary tests must mutate fixtures with schema-accepted values so defensive code, not validation, is exercised.

### references/defensive_patterns.md (1 contract)
1. [METHOD] Defensive patterns, state machines, and missing safeguards must be translated into scenarios and boundary tests.

### references/verification.md (1 contract)
1. [INVARIANT] Final verification must reconcile test counts, scenario coverage, field-table accuracy, and metadata consistency.

### LICENSE.txt (1 contract)
1. [COMPAT] The repository's shipped license terms are defined by `LICENSE.txt` and should not be contradicted elsewhere.
