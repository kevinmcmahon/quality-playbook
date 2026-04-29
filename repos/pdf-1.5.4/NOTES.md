# Vendored snapshot — Anthropic 'pdf' skill (v1.5.4 test)

Vendored copy of the Anthropic 'pdf' skill for QPB v1.5.4 Phase 3 Stage 1
wide-test (the pivotal classifier-redesign validation).

- **Source:** `/var/folders/7x/zj29dyln53q3x1zngmf39q_h0000gn/T/claude-hostloop-plugins/1991b33c9352b9c6/skills/pdf/`
- **Copied:** 2026-04-29
- **Why vendored:** same as repos/schedule etc. (see those NOTES.md).
- **Companion target:** repos/pdf-1.5.3/ retains the v1.5.3 wide-test result
  for the categorical bug-count comparison (v1.5.3: 12 bugs, 1 category-A;
  v1.5.4 should produce ≥3 category-A per Design Part 1 success criterion 1c).
- **Install layout:** `.github/skills/` carries QPB SKILL.md, references/,
  LICENSE.txt, and quality_gate.py per setup_repos.sh:196-200. SKILL.md
  metadata version is 1.5.3 (the canonical SKILL.md is not bumped until
  Implementation Plan Phase 10 release prep; v1.5.4 development runs
  against the v1.5.3-stamped skill).
- **Curated docs:** `docs_gathered/` and `reference_docs/` mirrored from
  repos/pdf-1.5.3/ so the wide-test runs with the same external-spec context
  that produced the v1.5.3 12-bug result. Apples-to-apples comparison.
