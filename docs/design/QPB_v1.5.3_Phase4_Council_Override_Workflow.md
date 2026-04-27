# QPB v1.5.3 — Phase 4 Council Override Workflow

*Round 1 carry-forward, settled by Phase 4 brief DQ-4-1: when a
Phase 4 reviewer believes the Phase 1 classification is wrong, the
override path is to re-run `bin/classify_project` with the
`--override` flag plus a written rationale. No post-hoc edits to
`project_type.json` by hand; no separate "amendment" tool. The
re-run path is the documented protocol because it preserves the
heuristic's evidence on disk alongside the override.*

## When this applies

A Phase 4 reviewer reads `quality/project_type.json` and
`quality/phase3/pass_d_council_inbox.json` and forms an opinion that
Phase 1's classification is wrong. Examples:

- Phase 1 classified the target as `Code`, but `pass_c_formal.jsonl`
  shows ≥1 REQ with `source_type=skill-section` (the four-pass
  pipeline was somehow run despite Code classification — this
  shouldn't happen, but if it does, the Council overrides to
  `Hybrid` to triangulate the cross-cutting evidence).
- Phase 1 classified as `Hybrid` because SKILL.md sits alongside
  code, but the code is purely incidental (e.g., a single shim file)
  and Council judges the project pure-Skill.
- Phase 1 classified as `Skill` because SKILL.md prose dominates,
  but the Council notes the project ships a runtime binary and
  reclassifies as `Hybrid`.

## Command form

```sh
python3 -m bin.classify_project \
    --target <repo_dir> \
    --override <code|skill|hybrid> \
    --override-rationale "<one-paragraph rationale>" \
    --write
```

Arguments:

- `--target` — same as the heuristic-only invocation; points at the
  target repo.
- `--override` — one of `code`, `skill`, `hybrid` (case-insensitive).
  Normalizes to `Code`/`Skill`/`Hybrid` before being recorded.
- `--override-rationale` — required when `--override` is set; free-
  text explanation that ends up in `project_type.json` for audit.
- `--write` — required to update `quality/project_type.json` (omit
  for a dry-run print to stdout).

Validation:

- `--override` without `--override-rationale` fails with a clear
  argparse error.
- `--override-rationale` without `--override` fails (no orphan
  rationales).

## Expected `project_type.json` shape post-override

```json
{
  "schema_version": "1.1",
  "classification": "Hybrid",
  "rationale": "Override applied: <rationale text> (heuristic suggested: 'Skill')",
  "confidence": "high",
  "evidence": {
    "skill_md_present": true,
    "skill_md_path": "SKILL.md",
    "skill_md_word_count": 1234,
    "total_code_loc": 5678,
    "code_languages": ["Python", "Shell"],
    "confidence_reason": "override-applied"
  },
  "classified_at": "2026-04-27T...",
  "classifier_version": "1.0",
  "override_applied": true,
  "override_rationale": "<the text passed via --override-rationale>"
}
```

The `evidence` block records what the heuristic found *before* the
override; the `rationale` and `override_rationale` fields capture
the override decision. This lets a future reviewer reconstruct
both signals when auditing the classification.

## Downstream re-runs after an override

Different override transitions imply different re-run scopes:

| From → To | Re-run scope |
|---|---|
| `Code` → `Skill` or `Hybrid` | Phase 3 must re-run (the four-pass pipeline only runs for Skill/Hybrid; Code targets skip Phases 3-4 entirely). Phase 4 then re-runs against the new Phase 3 output. |
| `Skill` ↔ `Hybrid` | Phase 3 may stay, but Phase 4 Part A.3 (LLM-driven prose-to-code) flips on/off based on the classification, so Phase 4 must re-run. Phase 4 Part C's `check_hybrid_cross_cutting_reqs` only fires for Hybrid; reclassifying flips the gate. |
| `Skill` or `Hybrid` → `Code` | The four-pass pipeline output (`quality/phase3/`) becomes irrelevant; Phase 4's skill-project gate checks SKIP for Code. The Phase 3 artifacts can stay on disk for audit but the gate ignores them. |

The `check_project_type_consistency` gate check (Phase 4 Part C)
verifies `override_applied=true` carries a non-empty
`override_rationale`. If a manual edit corrupts the file (e.g., sets
`override_applied=true` with empty rationale), the gate fails the
target until the file is regenerated via the re-run path above.

## Why re-run, not amend

The Round 1 carry-forward question was whether to support an in-place
"amend" command (`python3 -m bin.classify_project --amend ...`). The
Phase 4 brief DQ-4-1 settled on re-run-with-override because:

1. `classify_project()` already takes `override` / `override_rationale`
   parameters; the only gap was CLI exposure (Sonnet pre-flight
   MUST-FIX 1, fixed in Phase 4 commit 12/17).
2. Re-running re-derives the heuristic evidence under the current
   repo state. An amend command would have to choose between
   preserving stale evidence and silently re-deriving, both
   surprising.
3. There's no parallel "amend" command anywhere else in the
   pipeline; every phase artifact is regenerated from scratch on
   re-run.

A future v1.5.4 / v1.6.0 may revisit this if Council overrides
become frequent enough to warrant a dedicated workflow tool. For
now, re-run is the documented protocol.

## Audit trail

When the override lands in `project_type.json`, it's available to:

- The Phase 4 gate (`check_project_type_consistency`).
- The Phase 5 release-readiness audit (consumes
  `project_type.json` to render the final manifest).
- Future Council rounds reviewing a target's history.

The override is durable on disk; revisiting the classification later
just means re-running `classify_project` again with the desired
`--override` value.
