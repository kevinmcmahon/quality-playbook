"""bin/skill_derivation/ — QPB v1.5.3 Phase 3 four-pass skill-derivation pipeline.

The four-pass generate-then-verify architecture (Pass A naive coverage,
Pass B mechanical citation extraction, Pass C formal REQ production, Pass D
coverage audit) produces skill-shaped requirements from SKILL.md prose plus
reference files for Skill and Hybrid projects. Code projects bypass this
pipeline and continue to use the v1.5.0 divergence model unchanged.

See `~/Documents/QPB/docs/design/QPB_v1.5.3_Design.md` "Design — Skill-
Specific Derivation Pipeline" for the architectural rationale and
`~/Documents/QPB/docs/design/QPB_v1.5.3_Implementation_Plan.md` Phase 3
"Per-Pass Execution Protocol" for the disk-as-ledger contract every pass
follows.

Module naming note: this directory is `bin/skill_derivation/` rather than
`bin/phase3/` to avoid collision with the Quality Playbook's own internal
Phase 3 (Code Review and Regression Tests, per SKILL.md). The on-disk
artifact directory remains `quality/phase3/` for parity with the
Implementation Plan's literal text.
"""
