# Vendored snapshot — Anthropic 'pdf' skill (v1.5.4 wide-test target)

Vendored copy of the v1.5.3-era pdf skill content for QPB v1.5.4 Phase 3
Stage 1 wide-test (the pivotal classifier-redesign validation).

- **Source:** `repos/pdf-1.5.3/` (excluding .github/, quality/, .git/, *.log)
- **Copied:** 2026-04-29
- **Why the v1.5.3 source, not the current Anthropic plugin source:** the
  current plugin source has uppercase FORMS.md / REFERENCE.md (Anthropic
  appears to have renamed and fixed the case-mismatch that was v1.5.3's
  BUG-013). Using the v1.5.3 lowercase content keeps the experiment
  apples-to-apples: the only variable changing between v1.5.3 and v1.5.4
  wide-tests is the QPB pipeline, not the skill content.
- **Companion target:** repos/pdf-1.5.3/ retains the v1.5.3 wide-test
  result for the categorical bug-count comparison
  (v1.5.3: 12 bugs / 1 category-A; v1.5.4 target: ≥3 category-A per
  Design Part 1 success criterion 1c).
- **QPB install:** `.github/skills/` carries the current QPB SKILL.md,
  references/, LICENSE.txt, and quality_gate.py per setup_repos.sh:196-200.
  SKILL.md metadata still stamps version 1.5.3 — Implementation Plan
  Phase 10 (release prep) bumps the stamp; v1.5.4 development runs
  against the v1.5.3-stamped skill. The wide-test exercises the v1.5.4
  pipeline code (run_playbook.py, role_map.py, quality_gate.py) via the
  harness, not the SKILL.md metadata stamp.
