# Quality Constitution: Quality Playbook v1.3.8

## Purpose

The Quality Playbook is a specification-first product. Its users depend on the skill text, protocol references, installation docs, and generated quality artifacts being internally consistent enough that a fresh AI session can execute the playbook cold and leave behind a trustworthy audit trail. For this repository, **fitness for use** means more than "the Markdown renders" — it means the packaged skill, supporting references, and bootstrap docs all agree about what gets installed, what phases must run, how evidence is persisted, and how bugs are closed.

This repo inherits three quality principles directly. **Deming:** the quality bar must be built into the skill and reference docs, not reconstructed ad hoc by each AI session. **Juran:** the product is fit only if downstream agents can install it, execute it, and verify its outputs without inventing missing steps or relaxing the guardrails. **Crosby:** the cost of maintaining these contracts in the docs is far lower than the cost of a self-bootstrap run that silently skips verification, loses BUG tracker entries, or ships inconsistent legal/packaging metadata.

## Coverage Targets

| Subsystem | Target | Why |
|-----------|--------|-----|
| `SKILL.md` / `.github/skills/SKILL.md` | 95% | This file defines the execution contract. Drift here causes silent pipeline skips, especially around `PROGRESS.md`, terminal-gate reconciliation, and verification. |
| `references/review_protocols.md` + `references/spec_audit.md` | 95% | These references encode the closure mandate, docs validation, and skill integration protocol. Weak coverage here permits BUG-orphaning and audit theater. |
| `references/requirements_pipeline.md` + review/refinement refs | 90% | Requirement numbering, versioning, and reconciliation must stay parseable across runs or later sessions cannot trust the derived spec. |
| `README.md` / `AGENTS.md` / `LICENSE.txt` | 90% | These are the public bootstrap surface. Drift in installation steps, phase descriptions, or license terms creates user-visible breakage and compliance risk. |
| `docs_gathered/` and run artifacts | 80% | The gathered docs are supplemental evidence, but they materially improve requirements and audit quality when they are discovered and used correctly. |

## Coverage Theater Prevention

For this repository, fake tests look polished but fail to protect the product:

- Verifying that a Markdown file merely exists without checking the sections and tables that downstream agents rely on.
- Checking only one copy of the skill while ignoring the mirrored `.github/skills/` package that users actually install.
- Asserting that the quality docs mention "testing" or "audit" without checking for the required guardrails such as `## Terminal Gate Verification`, `## Pre-audit docs validation`, or the Field Reference Table.
- Treating `docs_gathered/` as present without proving the skill uses it as supplemental evidence.
- Counting regression tests without proving each one aligns to a concrete BUG or closure rule.

## Fitness-to-Purpose Scenarios

### Scenario 1: Canonical and packaged skill copies diverge

**Requirement tag:** [Req: formal — README.md §Quick start; AGENTS.md §Installing the skill]

**What happened:** The repository ships both canonical root docs and the `.github/skills/` install copy. If those copies drift, a user following the quick-start installs behavior that the root docs no longer describe. For a skill repo, that is equivalent to shipping two different products with the same version label.

**The requirement:** The root skill and reference docs must remain byte-for-byte aligned with the packaged `.github/skills/` mirror.

**How to verify:** Run `python3 -m unittest discover -s quality -p 'test_*.py' -v` and confirm `test_scenario_1_canonical_and_packaged_skill_copies_diverge`, `test_root_and_github_skill_files_are_identical`, and `test_root_and_github_reference_trees_match` pass.

---

### Scenario 2: Public docs advertise the wrong license

**Requirement tag:** [Req: formal — SKILL.md frontmatter `license: Complete terms in LICENSE.txt`; LICENSE.txt]

**What happened:** A spec-first repo cannot afford license drift because users rely on the docs, not a compiled artifact, to know reuse terms. If README claims Apache 2.0 while the shipped `LICENSE.txt` is MIT, downstream adopters inherit contradictory legal guidance and may package the skill under the wrong terms.

**The requirement:** Public-facing metadata must agree with the actual `LICENSE.txt` contents everywhere the repo describes the shipped skill.

**How to verify:** Confirm the functional traceability check `test_scenario_2_public_docs_advertise_the_wrong_license` passes and the regression probe `test_readme_license_text_matches_shipped_license_file` remains in `quality/test_regression.py` until the drift is fixed.

---

### Scenario 3: README still teaches the old phase model

**Requirement tag:** [Req: formal — SKILL.md §Phase 2b/2c/2d and §Phase 3]

**What happened:** The skill now depends on six tracked phases: `1`, `2`, `2b`, `2c`, `2d`, and `3`. If README still summarizes the run as four phases, a downstream operator can stop after audit and never execute reconciliation or verification. That produces clean-looking artifacts with stale BUG counts and no final quality gate.

**The requirement:** Public execution docs must describe the same tracked phase model the skill enforces, including reconciliation and verification.

**How to verify:** Confirm the functional traceability check `test_scenario_3_readme_still_teaches_the_old_phase_model` passes and the regression probe `test_readme_phase_summary_mentions_six_tracked_phases_and_verification` remains in `quality/test_regression.py` until README reflects the tracked phase model.

---

### Scenario 4: Install snippets omit required package files

**Requirement tag:** [Req: formal — `.github/skills/LICENSE.txt`; README.md §Quick start; AGENTS.md §Installing the skill]

**What happened:** The installed skill references `LICENSE.txt`, and the packaged skill directory ships that file. If the quick-start snippets copy only `SKILL.md` and `references/`, downstream repos receive an incomplete package. The skill still looks installed, but one of its declared files is missing from the target tree.

**The requirement:** Installation instructions must copy every file the packaged skill depends on, including `LICENSE.txt`.

**How to verify:** Confirm the functional traceability check `test_scenario_4_install_snippets_omit_required_package_files` passes and the regression probe `test_install_instructions_copy_required_license_file` remains in `quality/test_regression.py` until install snippets copy `LICENSE.txt`.

---

### Scenario 5: Spec-audit bugs disappear between phases

**Requirement tag:** [Req: formal — SKILL.md §Phase 2c and §Phase 2d]

**What happened:** Earlier self-bootstrap runs showed a recurring failure mode: spec audit found real bugs, but they never reached the cumulative BUG tracker or regression suite. The result looked complete because the triage doc existed, yet 30-50% of confirmed bugs were effectively orphaned from closure verification.

**The requirement:** Every confirmed code bug from code review **and** spec audit must enter the same BUG tracker and carry closure evidence before Phase 2d can complete.

**How to verify:** Confirm `test_scenario_5_spec_audit_bugs_disappear_between_phases` passes and `quality/PROGRESS.md` contains a populated BUG tracker plus matching terminal-gate arithmetic.

---

### Scenario 6: Stale supplemental docs skew the audit baseline

**Requirement tag:** [Req: formal — `references/spec_audit.md` §Pre-audit docs validation]

**What happened:** `docs_gathered/` is intentionally powerful: it lets auditors read prior reviews, design decisions, and incident history. If a stale or wrong gathered document is treated as authoritative without validation, the Council of Three becomes more confident for the wrong reasons and can promote documentation drift into false defects.

**The requirement:** Every spec-audit triage must validate 2-3 concrete claims from `docs_gathered/` against current source before using those docs as audit evidence.

**How to verify:** Confirm `test_scenario_6_stale_supplemental_docs_skew_the_audit_baseline` passes and `quality/spec_audits/2026-04-06-triage.md` includes `## Pre-audit docs validation` with concrete claim-by-claim checks.

---

### Scenario 7: Partial sessions masquerade as successful runs

**Requirement tag:** [Req: formal — `references/spec_audit.md` §Detecting partial sessions and carried-over artifacts]

**What happened:** Long self-bootstrap runs create scaffolding early. If a session dies after creating empty review or audit files, later readers can mistake those artifacts for evidence that the review actually ran. That produces "clean" runs whose only success was directory creation.

**The requirement:** Partial sessions and carried-over artifacts must be labeled as failed or stale, never reported as clean zero-finding runs.

**How to verify:** Confirm `test_scenario_7_partial_sessions_masquerade_as_successful_runs` passes and generated review/audit files contain substantive content instead of empty templates.

---

### Scenario 8: Integration quality gates hallucinate artifact fields

**Requirement tag:** [Req: formal — `references/review_protocols.md` §The Field Reference Table]

**What happened:** For a documentation-heavy repo, the most common integration failure is not a crash — it is a structurally plausible protocol that names the wrong fields or omits the skill-specific integration section entirely. The protocol looks impressive, but every downstream execution step is off by one missing column or stale heading.

**The requirement:** The integration protocol must build a Field Reference Table from the actual artifact templates and include the skill/LLM integration section for this repository class.

**How to verify:** Confirm `test_scenario_8_integration_quality_gates_hallucinate_artifact_fields` and `test_integration_protocol_contains_field_reference_table` pass.

## AI Session Quality Discipline

1. Read `quality/QUALITY.md` and `quality/REQUIREMENTS.md` before editing the skill or references.
2. Treat the root docs and `.github/skills/` package as one product; never update one without verifying the other.
3. When a BUG is confirmed, add executable closure evidence before ending the session.
4. Never mark verification complete without reading `quality/PROGRESS.md` and reconciling the terminal-gate counts.
5. Use `docs_gathered/` as evidence, not decoration: validate it, cite it, and keep its influence auditable.
6. Update this file whenever a new documentation-drift or audit-integrity failure mode is discovered.

## The Human Gate

- Final judgment on legal/licensing intent if documentation history and the license file genuinely disagree.
- Decisions to weaken or remove quality gates that would materially change the skill's promised review rigor.
- Whether a lower-confidence gathered document should remain in `docs_gathered/` as an audit source.
- Tone and article-framing choices in README prose that affect communication but not functional correctness.
