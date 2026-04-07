# Behavioral Requirements — Quality Playbook v1.3.8
Version: v1.0
Generated: 2026-04-06
Pipeline: contract-extraction v2 with narrative pass
17 requirements derived

## Project overview

The Quality Playbook repository is a specification-first product for AI coding tools. Its primary output is not an executable binary or service; it is a skill package made of Markdown artifacts that tell an AI session how to explore a codebase, derive behavioral requirements, generate tests, run a structured code review, execute a multi-model spec audit, and persist the resulting evidence. The repo therefore has two layers of behavior. The first is the canonical documentation layer: `SKILL.md`, `README.md`, `AGENTS.md`, and the reference files in `references/`. The second is the packaging layer: the `.github/skills/` mirror that users actually copy into target repositories.

The main data flow is documentary rather than computational. A user installs the skill, an AI session reads the skill and reference docs, Phase 1 explores the target codebase and any gathered history, Phase 2 writes quality artifacts, Phases 2b-2d reconcile findings into a single BUG tracker, and Phase 3 verifies that the run left behind structurally complete, internally consistent evidence. In this repo, the most fragile behaviors are the ones that look like "mere documentation": phase lists, install snippets, license statements, field names, and required section headers. If they drift, the skill still looks plausible while downstream executions silently skip steps, miscount bugs, or ship incomplete install instructions.

The repository is also self-referential. The playbook is used to generate a quality system for the playbook itself, so the requirements must cover both the promised behavior of the skill and the quality discipline of its own bootstrap output. `docs_gathered/` materially improves this by recording prior bootstrap reviews, failure modes, and design rationale. Those gathered docs do not replace the in-repo specs, but they sharpen requirements and scenarios around the historical weak spots: BUG tracker orphaning, stale metadata after late edits, insufficient docs validation, and missing skill-integration coverage.

## Use cases

### Use Case 1: Install the skill into a target repository

- **Actor:** Maintainer or AI assistant preparing another repository to use the playbook
- **Preconditions:** The maintainer has this repository checked out and wants to copy the shipped skill package into another project.
- **Steps:**
  1. The actor follows the install instructions for GitHub Copilot or Claude Code.
  2. The actor copies the canonical skill package into the destination repository.
  3. The destination repository receives the skill, references, and required supporting files.
- **Postconditions:** The target repo contains a complete skill package with the files the skill metadata references.
- **Alternative paths:** The actor installs the `.github/skills/` package instead of the root copy; a copy step is omitted; public metadata disagrees with the shipped license file.
- **Requirements:** REQ-001, REQ-017

### Use Case 2: Execute the full playbook with supplemental docs

- **Actor:** AI coding session executing the skill against a project
- **Preconditions:** The target repository contains the installed skill, and `docs_gathered/` may provide supplemental design history.
- **Steps:**
  1. The session prints the mandatory startup banner.
  2. The session explores the codebase and any gathered docs before writing.
  3. The session derives requirements, constitution, tests, and protocols.
  4. The session records checkpoints in `quality/PROGRESS.md`.
- **Postconditions:** A complete quality system exists under `quality/`, with the run state persisted.
- **Alternative paths:** No supplemental docs are present; the repository is specification-primary; the session resumes after interruption.
- **Requirements:** REQ-002, REQ-003, REQ-004, REQ-006, REQ-007, REQ-008, REQ-009

### Use Case 3: Review, track, and close defects

- **Actor:** AI reviewer or maintainer validating the current repository state
- **Preconditions:** Requirements and protocols have been generated.
- **Steps:**
  1. The reviewer runs the three-pass code review.
  2. Confirmed bugs are added to the cumulative BUG tracker.
  3. Regression tests are written or exemptions are recorded.
  4. Reconciliation and terminal-gate arithmetic are completed.
- **Postconditions:** Every confirmed bug has closure evidence and the BUG tracker is authoritative.
- **Alternative paths:** Code review and spec audit disagree; spec audit produces net-new bugs; a bug is fixed during the run.
- **Requirements:** REQ-004, REQ-005, REQ-010, REQ-011, REQ-012, REQ-013

### Use Case 4: Run the integration protocol for a skill repository

- **Actor:** AI session or maintainer validating end-to-end playbook execution
- **Preconditions:** The repository contains generated quality docs and can be exercised via a CLI agent.
- **Steps:**
  1. The actor reads `RUN_INTEGRATION_TESTS.md`.
  2. The actor prepares a clean test repo and installs the skill.
  3. The actor executes the skill through the CLI agent.
  4. The actor structurally verifies the generated artifacts and saved results.
- **Postconditions:** The integration protocol proves the skill can run end-to-end and leave behind complete artifacts.
- **Alternative paths:** No external docs are provided; a skill run partially completes; field names are copied incorrectly from memory.
- **Requirements:** REQ-014, REQ-015

### Use Case 5: Run a Council-of-Three spec audit

- **Actor:** Maintainer or AI session performing a spec/code divergence audit
- **Preconditions:** Requirements exist and the repository has current source plus optional gathered docs.
- **Steps:**
  1. Three independent auditors read the code and specs.
  2. The triage validates any gathered docs before using them as evidence.
  3. Findings are merged by agreement level and verified when models disagree.
- **Postconditions:** Confirmed code bugs, spec bugs, design choices, and documentation gaps are classified with an auditable baseline.
- **Alternative paths:** One auditor times out; stale docs are discovered; a finding relies on an inferred requirement and needs review.
- **Requirements:** REQ-003, REQ-012, REQ-013

### Use Case 6: Refine the generated requirements over time

- **Actor:** Maintainer or follow-up AI model improving the playbook
- **Preconditions:** A baseline `quality/` directory exists with versioned requirements.
- **Steps:**
  1. The actor reviews requirements or runs a cross-model audit.
  2. Feedback is recorded in `quality/REFINEMENT_HINTS.md`.
  3. A refinement pass backs up the current state, updates the requirements, and logs the change.
- **Postconditions:** Requirements evolve without losing traceability or version history.
- **Alternative paths:** No actionable feedback exists; a requirement must be sharpened instead of added; a user-directed removal is requested.
- **Requirements:** REQ-007, REQ-008, REQ-016

## Cross-cutting concerns

- **Mirror integrity:** Root docs and `.github/skills/` are one shipped product.
- **Closure integrity:** BUG tracker math, regression tests, and reconciliation must all agree.
- **Evidence provenance:** `docs_gathered/`, review reports, and carried-over artifacts must stay auditable.
- **Metadata accuracy:** Public license, phase descriptions, and install steps must match the actual shipped skill.
- **Spec-first execution:** Functional tests and integration checks validate structural promises in documents, not just code paths.

## Requirements

### REQ-001: Canonical and packaged skill files must stay synchronized
- **Summary:** The root skill/reference files and the `.github/skills/` package must describe the same shipped behavior.
- **User story:** As a maintainer installing the playbook into another repo, I expect the packaged copy to match the canonical docs **so that** installation does not silently change the product.
- **Implementation note:** The repository keeps a mirrored `.github/skills/` tree alongside the root skill and reference docs.
- **Conditions of satisfaction:**
  - `SKILL.md` and `.github/skills/SKILL.md` contain identical content.
  - Every file under `references/` matches its `.github/skills/references/` counterpart.
  - Generated tests compare both trees rather than trusting one copy.
- **Alternative paths:** Installing from the root docs or from the packaged mirror must yield the same skill content.
- **References:** README.md:17-31; AGENTS.md:27-45; `.github/skills/`
- **Specificity:** specific

### REQ-002: Full playbook execution must begin with the mandated startup banner and run the complete flow
- **Summary:** The `execute` path must print the exact startup banner and then run exploration, generation, review, audit, reconciliation, and verification.
- **User story:** As a user executing the skill, I expect a clear declaration of the full workflow **so that** I can tell the run is doing more than generating test stubs.
- **Implementation note:** The startup banner and full-flow promise are encoded in the top of `SKILL.md`.
- **Conditions of satisfaction:**
  - The mandatory banner text appears exactly once in the skill preamble.
  - The execute entry point explicitly describes full pipeline execution.
  - The flow includes post-review reconciliation and verification, not just review and audit.
- **Alternative paths:** Partial entry points may exist, but "execute" must still map to the full flow.
- **References:** SKILL.md:13-30; SKILL.md:60-85
- **Specificity:** specific

### REQ-003: Exploration must use both in-repo specs and validated supplemental history
- **Summary:** Phase 1 must treat `README.md`, `AGENTS.md`, root Markdown specs, and validated `docs_gathered/` evidence as requirement sources.
- **User story:** As a maintainer relying on prior run history, I expect the playbook to incorporate that evidence carefully **so that** scenarios and audits reflect real failure history instead of guesswork.
- **Implementation note:** `SKILL.md` and `spec_audit.md` explicitly describe supplemental-doc use and validation.
- **Conditions of satisfaction:**
  - The exploration phase calls out `docs_gathered/` when present.
  - The spec audit triage validates 2-3 factual claims from supplemental docs before trusting them.
  - If no supplemental docs exist, the absence is recorded explicitly rather than ignored.
- **Alternative paths:** Runs without docs still complete; runs with questionable docs downgrade claims that rely on them.
- **References:** SKILL.md:99-114; README.md:61-63; `references/spec_audit.md`:68-82
- **Specificity:** specific

### REQ-004: Run state must be persisted in PROGRESS.md with the tracked phase model
- **Summary:** Every run must persist metadata, phase checkpoints, artifact inventory, and the BUG tracker in `quality/PROGRESS.md`.
- **User story:** As a reviewer reading artifacts after a long run, I expect a single authoritative checkpoint log **so that** I can audit what happened without trusting session memory.
- **Implementation note:** `SKILL.md` defines the template and phase list for `PROGRESS.md`.
- **Conditions of satisfaction:**
  - `PROGRESS.md` includes started time, project, skill version, and correct `With docs` metadata.
  - The tracked phases are exactly `1`, `2`, `2b`, `2c`, `2d`, and `3`.
  - The artifact inventory and exploration summary are populated as the run proceeds.
- **Alternative paths:** If a run resumes, the existing `PROGRESS.md` remains authoritative and is updated rather than replaced.
- **References:** SKILL.md:262-324; SKILL.md:436-443; SKILL.md:525-532
- **Specificity:** specific

### REQ-005: BUG tracker closure arithmetic must be enforced before completion
- **Summary:** The cumulative BUG tracker and terminal-gate statement must reconcile code-review and spec-audit findings before Phase 2d can complete.
- **User story:** As a maintainer consuming a bootstrap run, I expect every confirmed bug to be accounted for **so that** no finding disappears between review, audit, and verification.
- **Implementation note:** `SKILL.md` encodes tracker updates in Phases 2b-2d and mandates a persisted terminal-gate statement.
- **Conditions of satisfaction:**
  - Every confirmed code-review bug enters the BUG tracker with closure status.
  - Every confirmed spec-audit code bug also enters the same tracker.
  - The terminal-gate statement is printed and written under `## Terminal Gate Verification`.
  - If counts do not match `M + L`, the run must stop and reconcile.
- **Alternative paths:** A bug may be `confirmed open`, `fixed`, or `exempt`, but it may not be untracked.
- **References:** SKILL.md:445-488; `references/review_protocols.md`:158-183
- **Specificity:** specific

### REQ-006: The quality constitution must encode scenario-backed standards
- **Summary:** `quality/QUALITY.md` must define coverage targets, coverage-theater rules, and scenario/test mappings grounded in this repository's real risks.
- **User story:** As a future AI session, I expect a repository-specific quality bar **so that** I do not rationalize away the hard parts of this spec-first product.
- **Implementation note:** The constitution template requires scenario-backed rationale and explicit requirement tags.
- **Conditions of satisfaction:**
  - Coverage targets cite concrete risks in the QPB repo.
  - Every scenario includes a canonical `[Req: tier — source]` tag.
  - Every scenario maps to at least one automated test.
- **Alternative paths:** If a scenario cannot be automated, the file must say why and route it to the Human Gate.
- **References:** `references/constitution.md`:22-79,137-160
- **Specificity:** specific

### REQ-007: Behavioral requirements must be derived through the documented five-phase pipeline
- **Summary:** The playbook must generate contracts, requirements, coverage, completeness, and narrative outputs using the documented pipeline and canonical REQ heading format.
- **User story:** As a reviewer depending on traceability, I expect requirements to be generated systematically **so that** every contract can be traced forward into review and tests.
- **Implementation note:** `requirements_pipeline.md` defines the phases, heading format, and output files.
- **Conditions of satisfaction:**
  - `CONTRACTS.md`, `REQUIREMENTS.md`, `COVERAGE_MATRIX.md`, and `COMPLETENESS_REPORT.md` are all generated.
  - Every requirement heading uses `### REQ-NNN: Title`.
  - Requirements include summary, user story, implementation note, conditions, alternative paths, references, and specificity.
- **Alternative paths:** Large-repo scoping may narrow the source set, but the pipeline structure still applies.
- **References:** `references/requirements_pipeline.md`:9-18,90-123,297-318
- **Specificity:** specific

### REQ-008: Completeness assessment must remain consistent with later review findings
- **Summary:** The completeness report must reconcile code-review and spec-audit findings and retain exactly one authoritative verdict.
- **User story:** As a maintainer using the requirements as a quality gate, I expect the completeness verdict to reflect later evidence **so that** a "complete" report never coexists with uncovered review findings.
- **Implementation note:** The requirements pipeline defines a mandatory post-review reconciliation step.
- **Conditions of satisfaction:**
  - The initial completeness report cites covered domains and testability concerns.
  - A `## Post-Review Reconciliation` section maps every review/audit finding to covered or missing requirements.
  - The final document contains one authoritative verdict, not competing pre- and post-review verdicts.
- **Alternative paths:** If new requirements are added during reconciliation, counts and references must be refreshed everywhere.
- **References:** `references/requirements_pipeline.md`:197-277
- **Specificity:** specific

### REQ-009: Functional tests must verify real repository behavior without theater
- **Summary:** The generated functional suite must verify actual QPB artifacts using spec, scenario, and boundary groups with self-contained setup.
- **User story:** As a maintainer running the generated suite, I expect the tests to validate real skill contracts **so that** passing tests mean the documentation product is structurally trustworthy.
- **Implementation note:** The repo has no pre-existing executable test suite, so the quality suite becomes the primary automated safety net.
- **Conditions of satisfaction:**
  - `quality/test_functional.py` groups tests into spec requirements, fitness scenarios, and boundaries/edge cases.
  - Tests operate on actual repository files, not placeholder helpers.
  - Cross-variant checks compare both canonical and packaged file sets where applicable.
  - The suite runs cleanly under the chosen Python test runner.
- **Alternative paths:** If a behavior is only testable through a regression probe, it belongs in `test_regression.py`, not the passing functional suite.
- **References:** `references/functional_tests.md`:5-30,65-145,217-312
- **Specificity:** specific

### REQ-010: Every confirmed bug must have executable closure evidence
- **Summary:** Confirmed bugs must produce executable regression tests aligned to the cited code path or carry an explicit exemption.
- **User story:** As a reviewer handing findings to the next session, I expect closure evidence to be executable **so that** bugs are facts, not opinions.
- **Implementation note:** The review protocol defines closure mandate, expected-failure conventions, and alignment checks.
- **Conditions of satisfaction:**
  - `quality/test_regression.py` uses executable tests, not prose placeholders.
  - Each BUG row cites a regression test or exemption reason.
  - Regression tests assert desired correct behavior and use expected-failure markers when the bug remains open.
- **Alternative paths:** If a bug is fixed during the run, the regression test can pass and the closure status becomes `fixed (test passes)`.
- **References:** `references/review_protocols.md`:132-189,202-257
- **Specificity:** specific

### REQ-011: Code review must run as three isolated passes with traceable evidence
- **Summary:** The code review protocol must separate structural review, requirement verification, and cross-requirement consistency, and each pass must cite evidence.
- **User story:** As a maintainer relying on review output, I expect each pass to do one job well **so that** structural issues, intent violations, and contradictions do not blur together.
- **Implementation note:** `review_protocols.md` describes distinct pass scopes and mandatory guardrails.
- **Conditions of satisfaction:**
  - Pass 1 uses line-numbered structural findings only.
  - Pass 2 cites code evidence for each requirement or requirement group.
  - Pass 3 evaluates at least one shared concept across requirements.
  - A combined summary merges findings with severity and status.
- **Alternative paths:** If a pass has no findings, it still explains what was checked.
- **References:** `references/review_protocols.md`:19-131
- **Specificity:** specific

### REQ-012: Spec audit triage must establish an auditable factual baseline
- **Summary:** The Council-of-Three audit must validate supplemental docs, log council participation, and resolve factual disputes with verification probes.
- **User story:** As a maintainer comparing three audit reports, I expect the triage to show why a finding is trustworthy **so that** agreement, disagreement, and stale evidence are visible instead of implicit.
- **Implementation note:** `spec_audit.md` defines the definitive prompt, docs validation, confidence downgrades, and verification probes.
- **Conditions of satisfaction:**
  - Triage includes `## Pre-audit docs validation`.
  - Triage logs the effective council size and fresh participation.
  - Single-auditor findings are not promoted without verification when council size is reduced.
  - The triage categorizes confirmed findings as code bugs, spec bugs, design choices, documentation gaps, missing tests, or wrong inferred requirements.
- **Alternative paths:** When `docs_gathered/` is absent, the triage explicitly states that auditors relied on in-repo specs and code only.
- **References:** `references/spec_audit.md`:14-126
- **Specificity:** specific

### REQ-013: Partial sessions and carried-over artifacts must remain visible as stale state
- **Summary:** Generated review and audit artifacts must distinguish fresh substantive output from partial or carried-over scaffolding.
- **User story:** As a reviewer reading old artifacts, I expect provenance to stay visible **so that** I do not mistake an interrupted run for a clean pass.
- **Implementation note:** `spec_audit.md` explicitly calls out partial-session detection and provenance headers.
- **Conditions of satisfaction:**
  - Empty or template-only review/audit outputs are treated as failed phases, not "no findings."
  - Carried-over artifacts get provenance headers when reused.
  - The generated playbook mentions this check in the audit and completeness materials.
- **Alternative paths:** If all artifacts are generated fresh in the current run, no provenance headers are needed.
- **References:** `references/spec_audit.md`:141-166
- **Specificity:** specific

### REQ-014: Integration protocols must remain executable from the project root
- **Summary:** `RUN_INTEGRATION_TESTS.md` must use relative paths, explicit pre-flight checks, execution UX, and saved results paths.
- **User story:** As an AI session asked to run the integration protocol, I expect a root-relative, copy-pasteable checklist **so that** execution does not depend on machine-specific paths or tacit knowledge.
- **Implementation note:** The integration protocol template emphasizes working directory rules, plan/progress/results UX, and saved outputs.
- **Conditions of satisfaction:**
  - Commands are written relative to the project root.
  - Pre-flight, test matrix, progress reporting, results, and recommendation sections exist.
  - The protocol saves results under `quality/results/`.
- **Alternative paths:** Manual verification steps may supplement automation, but they do not replace explicit pass criteria.
- **References:** `references/review_protocols.md`:276-399
- **Specificity:** specific

### REQ-015: Skill repositories must include a skill/LLM integration section and field reference table
- **Summary:** Because QPB is a skill repo, its integration protocol must include the dedicated skill-execution section and build quality gates from artifact templates rather than memory.
- **User story:** As a maintainer validating the playbook end-to-end, I expect a protocol that actually runs the skill through a CLI agent **so that** the real execution path is tested instead of simulated.
- **Implementation note:** `review_protocols.md` adds a special section for skills and LLM-automated tools.
- **Conditions of satisfaction:**
  - `RUN_INTEGRATION_TESTS.md` contains a Field Reference Table built from actual artifact templates.
  - The protocol includes the skill integration test matrix and structural verification commands.
  - Quality gates reference real artifact fields such as PROGRESS metadata and BUG tracker columns.
- **Alternative paths:** Supplemental docs comparison may be optional, but the core skill execution and structural verification are mandatory.
- **References:** `references/review_protocols.md`:463-586; `references/verification.md`:81-92
- **Specificity:** specific

### REQ-016: Requirement review and refinement must preserve traceability across versions
- **Summary:** The generated review/refinement workflow must track feedback, back up prior versions, and record changes in version history.
- **User story:** As a maintainer improving the playbook over time, I expect refinements to be versioned and reviewable **so that** improvements do not erase the path that led to them.
- **Implementation note:** `requirements_pipeline.md`, `requirements_review.md`, and `requirements_refinement.md` define the files and flow.
- **Conditions of satisfaction:**
  - `REVIEW_REQUIREMENTS.md`, `REFINE_REQUIREMENTS.md`, `REFINEMENT_HINTS.md`, and `VERSION_HISTORY.md` all exist.
  - Refinement instructions require backups under `quality/history/vX.Y/`.
  - Feedback is tracked separately from the requirements document itself.
- **Alternative paths:** If no refinement is in progress, the files still advertise the protocol and current version.
- **References:** `references/requirements_pipeline.md`:349-427; `references/requirements_review.md`:1-157; `references/requirements_refinement.md`:1-113
- **Specificity:** specific

### REQ-017: Public metadata and installation guidance must match the shipped package
- **Summary:** README, AGENTS, and other bootstrap docs must accurately describe the current license, execution model, and package contents of the shipped skill.
- **User story:** As a user adopting the playbook from public docs, I expect those docs to be truthful **so that** I do not install an incomplete package or follow an outdated workflow.
- **Implementation note:** The public bootstrap surface is split across README, AGENTS, and the package files they describe.
- **Conditions of satisfaction:**
  - Public license statements agree with `LICENSE.txt`.
  - Public phase summaries agree with the tracked phase model in `SKILL.md`.
  - Install instructions copy every shipped file the packaged skill references, including `LICENSE.txt`.
- **Alternative paths:** High-level prose may summarize the workflow, but it must not erase required tracked phases or contradict package contents.
- **References:** README.md:5-33,71-87; AGENTS.md:27-45; LICENSE.txt:1-21; SKILL.md:279-285,474-488
- **Specificity:** specific
