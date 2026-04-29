# Vendored snapshot — Anthropic 'schedule' skill

This directory is a vendored copy of the Anthropic 'schedule' skill for QPB
v1.5.4 Phase 3 wide-test validation.

- **Source:** `/var/folders/7x/zj29dyln53q3x1zngmf39q_h0000gn/T/claude-hostloop-plugins/1991b33c9352b9c6/skills/schedule/`
- **Copied:** 2026-04-29
- **Why vendored, not symlinked:** the canonical source path lives under
  `/var/folders/.../T/claude-hostloop-plugins/<short-hash>/` — a
  per-session macOS temp directory that gets purged by the OS and uses
  a session-specific hash. Symlinking would dangle the next time the
  skill plugin loads. v1.5.4 validation wants a reproducible target;
  vendoring is the right trade.
- **Refresh:** to pick up upstream Anthropic updates, re-run the copy
  step in Phase 3 Stage 0 of `QPB_v1.5.4_Phase3_Brief.md`.

This NOTES.md is metadata for the QPB harness, not part of the skill
itself. Phase 1 role-tagging should classify it as `docs`.
