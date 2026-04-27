# Benchmark Protocol

Last updated: 2026-04-27 (v1.5.3 release — added skill-target guidance below)

The playbook tunes against real repos. For tuning signals to be honest, each benchmark run has to start from the same blank slate — no prior findings, no sibling runs, no pre-existing `quality/` artifacts to anchor on. This file is the checklist.

## The contamination risk

Agents running the playbook are smart enough to look around. If a sibling directory next to the target contains a prior playbook run, the agent can read its `EXPLORATION.md`, `BUGS.md`, and `quality/` artifacts and reuse findings instead of discovering them independently. This defeats the benchmark.

Concretely, we have already observed Codex notice a sibling run on its own. Other agents (Claude Code, Copilot) will too.

## Run layout

```
repos/
  clean/              ← pristine sources, never modified, never run against directly
  runs/
    {target}-{version}-{runner}-{yyyymmdd-hhmmss}/
      {target}/       ← freshly copied from clean/, the only sibling in this dir
      run.log         ← captured stdout/stderr
      NOTES.md        ← optional: anything the operator wants to record
```

The target checkout lives **alone** inside its run directory. No other repos, no prior runs, no scratch files.

## Pre-run checklist

Before kicking off any benchmark run:

1. **Copy the target fresh from `repos/clean/`** into a new empty run directory under `repos/runs/`. Never run the playbook against `repos/clean/{target}` itself, and never against an existing run directory.
2. **Verify there are no siblings.** `ls` the run directory's parent should show only this run, not peer runs for the same target or other targets.
3. **Verify no pre-existing `quality/` folder** inside the target. If SKILL.md is installed, that's fine; the playbook expects it. But `quality/`, `EXPLORATION.md`, `BUGS.md`, etc. must not exist yet.
4. **Confirm SKILL.md version** in the target matches the version you intend to benchmark. `.github/skills/SKILL.md` is the canonical location.
5. **Seeds off.** The runner defaults to `--no-seeds`; if you invoke an agent directly, the prompt should not reference prior runs.

## During the run

- Capture stdout/stderr to `run.log` in the run directory.
- Do not add files to the run directory while the agent is working. Let it own the space.
- If the run hits a rate limit or other interruption, record that in `NOTES.md` — it's signal for capacity planning, not just a nuisance.

## After the run

Each run produces two kinds of data:

1. **Bugs found** — the direct quality signal. Compare against prior runs and cross-agent runs for the same target.
2. **Friction points** — places the agent paused, asked for clarification, or appeared to miss something the protocol should have caught. This is the tuning signal, and it feeds back into the two adjustable axes:
   - `references/exploration_patterns.md` — what requirements Phase 1 elicits
   - `references/defensive_patterns.md` — what defensive code the grep sweep surfaces

Capture friction in `NOTES.md` or in a dedicated `RUN_SUMMARY.md` inside `quality/`.

## Cross-agent runs

When running the same target in multiple agents (e.g., httpx in Codex while chi runs in Copilot), each agent gets its own run directory. Never share a run directory across agents — their artifact conventions differ, and one agent reading another's in-progress work is the worst kind of contamination.

## Current benchmark set

### Code targets (v1.5.0 divergence pipeline)

- **bootstrap** — the playbook against QPB itself, with gathered documentation seeding REQUIREMENTS.md (Hybrid project per Phase 0 classifier; runs both the v1.5.0 code path and the v1.5.3 skill-derivation path)
- **chi** (Go, ~74 source files) — baseline, well-understood
- **cobra** (Go) — second Go library for cross-project comparison
- **virtio** (C, kernel code) — systems-level coverage, defensive-code heavy
- **express** (JavaScript) — language diversity, web-framework shape
- **clean/casbin** (Go, v1.5.3 first-time target) — added to the v1.5.3 cross-target validation matrix

### Pure-Skill targets (v1.5.3 skill-derivation pipeline only)

- **anthropic-skills/skills/skill-creator** — meta-skill (485-line SKILL.md + references/schemas.md)
- **anthropic-skills/skills/pdf** — focused single-purpose skill (314-line SKILL.md, no references/)
- **anthropic-skills/skills/claude-api** — API skill (262-line SKILL.md, no references/)

These three classify as Skill (high confidence) under the v1.5.3
classifier; they exercise the four-pass skill-derivation pipeline
end-to-end without firing any of the v1.5.0 Code-project gates.

### Cross-version (optional)

- **quality-playbook-1.4.5** — older QPB self with SKILL.md present; useful for v1.5.3 Phase 4 internal-prose detection against an evolved spec

### Next batch candidates, not yet run

- **httpx** (Python, ~23 source files) — smallest, fastest feedback
- **serde** (Rust, ~58 source files) — closest size match to chi
- **gson** (Java, ~120 source files) — JVM coverage

Add rows here when new targets enter the benchmark.

## v1.5.3 skill-target run procedure

Skill / Hybrid targets use the v1.5.3 skill-derivation CLI rather
than `bin/run_playbook.py`:

```bash
# 1. Classify (writes <target>/quality/project_type.json)
python3 -m bin.classify_project --target <target> --write

# 2. Phase 3 four-pass derivation (Pass A LLM-driven; B/C/D mechanical)
python3 -m bin.skill_derivation --phase 3 --pass all --runner claude --pace-seconds 0 <target>

# 3. Phase 4 divergence detection (mechanical for A.1/A.2/B; Hybrid-only LLM for A.3)
python3 -m bin.skill_derivation --phase 4 --part all <target>

# 4. (Hybrid only) Phase 4 Part A.3 LLM-driven prose-to-code
python3 -m bin.skill_derivation --phase 4 --part a3 --runner claude --pace-seconds 0 <target>
```

Output artifacts land under `<target>/quality/phase3/` (the same
directory holds Phase 3 four-pass + Phase 4 divergence outputs).
The contamination-risk discipline above still applies — never run
against `repos/clean/<target>` directly; copy fresh into a run
directory under `repos/runs/`.
