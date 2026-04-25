# Quality Playbook — Improvement Loop

> This document is the canonical reference for **how the Quality Playbook is improved over time**. It is meta — it describes how we change the playbook between releases, what evidence we require before a change ships, and how we measure whether a release is better than the one before. The playbook's own internal mechanisms are described in `TOOLKIT.md` and `SKILL.md`.

## The methodology: benchmark-driven calibration

The Quality Playbook is a quality engineering tool, and it is itself engineered through the same discipline it advocates. Each release goes through a Plan-Do-Check-Act loop with **benchmark recovery against pinned ground truth** as the Check step.

1. **Plan.** A defect or improvement candidate is identified — from a Council-of-Three review, from an empirical regression observed in benchmark output, or from an adopter report. A hypothesis is formed: which lever (regex, prompt, gate, schema, finalization step, iteration strategy) is wrong, and what change should improve which axis (process compliance, outcome recall, or both).

2. **Do.** The change is implemented. Source edits go through Claude Code with a written brief. Docs-only edits to orientation files (TOOLKIT.md, IMPROVEMENT_LOOP.md, TOOLKIT_TEST_PROTOCOL.md, README.md, DEVELOPMENT_CONTEXT.md) may be applied directly per the workspace AGENTS.md carve-out. Every code-bearing change is reviewed by a Council-of-Three nested panel before merge; every docs change is reviewed by the Toolkit Test Protocol before release.

3. **Check.** The new release is run against the pinned benchmark repositories with known v1.4.5 ground-truth bug counts. Both axes are evaluated:
   - **Process compliance.** `quality_gate.py` passes against each benchmark output. Artifacts have the right shape; no template sentinels; TDD logs present (or `NOT_RUN` with reason); requirements pipeline produced citations; finalization summary present in PROGRESS.md.
   - **Outcome recall.** Bug counts on each benchmark repo, broken out by iteration strategy, compared to the prior release. Recall against ground truth is preserved or improved.

4. **Act.** If both axes pass, ship. If either regresses, the change is reverted or further iterated before the release lands.

## The two axes

The playbook is verified along two axes that must both succeed:

**Process compliance** — Does the run produce artifacts that conform to the expected shape? This is what `quality_gate.py` measures: BUGS.md heading format, regression-test patches, TDD logs, requirements pipeline output, mechanical extraction integrity, finalization summary in PROGRESS.md, writeup hydration completeness.

**Outcome recall** — Does the run actually find the bugs we know are there? This is what benchmark recovery measures: number of confirmed bugs against pinned repos with known ground-truth bug counts, by iteration strategy.

Both axes can fail independently. The most pernicious failure mode is **pass-process / fail-recall** — the run produces all the right artifacts and gates green while finding zero real bugs. This was historically observed when an under-powered code-generation model was used (see TOOLKIT.md "Cursor" entry). It cannot be detected by the gate alone; only benchmark recovery exposes it.

The opposite mode — **fail-process / pass-recall** — is rare but possible (the run finds real bugs but produces malformed artifacts that fail the gate). When it happens, the bugs are still useful but the release is not shippable until the artifacts are corrected.

The two-axes framing is the canonical vocabulary for QPB improvement. It is *not* the same as external syntheses of the playbook's design space (e.g., "structured coverage ↔ freeform discovery" + "recall ↔ evidentiary rigor") — those describe the playbook's internal mechanisms, not the methodology used to improve them.

## Pinned benchmarks

The Check step uses three pinned benchmark repos with known v1.4.5 ground-truth bug counts:

- `chi-1.5.1` — Go web framework
- `virtio-1.5.1` — Linux kernel C
- `express-1.5.1` — Node.js

Each is pinned to a specific upstream commit so the ground truth is stable across QPB releases. The bugs found in v1.4.5 form the recovery baseline: a v1.5.2 run on `chi-1.5.1` should find at least as many of the v1.4.5 confirmed bugs as v1.4.5 itself did (recall preservation), with new findings being net improvement.

When a new pinned benchmark version is created (e.g., `chi-1.6.0`), the v1.4.5 ground truth from the older pin is imported as the starting recall floor.

The benchmark repos cover three ecosystems with substantively different failure modes — Go HTTP routing, kernel-C transport variants, JavaScript parser laxity — so a regression that only manifests in one ecosystem is still observable.

## Levers

The tunable parameters that improvement work changes:

- **Prompts** — `SKILL.md`, `references/*.md`, agent-facing prompts in `bin/run_playbook.py`
- **Gates** — `quality_gate.py` checks (regex, schema, completeness, evidence)
- **Schemas** — `schemas.md`, JSON shapes, INDEX verdicts
- **Iteration strategies** — gap, unfiltered, parity, adversarial mechanism definitions
- **Finalization** — orchestrator-side post-run / post-iteration finalization (introduced v1.5.2)
- **Mechanical extraction** — what the playbook extracts mechanically vs. relies on the model for
- **Synthesis docs** — `TOOLKIT.md`, BUGS.md formatting, writeup hydration
- **Categorization** — confidence/material tagging on confirmed bugs (planned v1.5.3)

Each release's release notes name which levers it touched.

## Council-of-Three review

Every code-bearing change to QPB source goes through a Council-of-Three nested panel review (3 outer × 3 inner = 9 perspectives) before merge. The protocol is documented in the workspace `AGENTS.md` (Council-of-Three Invocation section), including the CLI form, working-directory discipline, and acceptance checks against fabrication.

Docs-only changes to orientation files use the Toolkit Test Protocol (`TOOLKIT_TEST_PROTOCOL.md`) instead, which is purpose-built for documentation review through reader personas.

## Bug categorization (planned for v1.5.3)

A future addition to BUGS.md will tag each confirmed bug along a confidence/material dimension. The categorization is a tagging pass at the end of synthesis, not a new gate. Adopters can prioritize which findings to triage first based on the tag.

The four tiers, in descending evidentiary strength:

- **standout** — bugs an experienced engineer would describe as "huh, didn't see that." Earned, not required in every run. Most valuable for open-source upstream submissions and showcase findings. A run can ship with zero standouts; a run cannot promote a finding to standout without explicit justification in the bug record.
- **confirmed** — solid evidence, normal severity, the run's reliable findings. These are the default tier for bugs that pass the standard evidentiary bar.
- **probable** — code-path trace supports the finding but evidence is partial; an experienced reviewer would likely accept after a closer look. Worth surfacing but not load-bearing.
- **candidate** — adversarial-iteration findings with the lower evidentiary bar; flagged as worth review but not promoted. Often correct, but the "is this actually wrong or is it a design choice?" question is genuinely open.

The standout tier is the most consequential change for adopters who plan to submit upstream PRs. A standout bug should answer "what would a senior maintainer of this project say if shown this finding?" — surprise plus actionable specificity is the test.

## Measurement and statistical control

The playbook is currently **instrumented and trend-aware**, not yet **under statistical control** in the formal SPC / CMMI level 4 sense.

What this means today:
- Per-release benchmark runs are recorded with bug counts by iteration strategy.
- Trend analysis across releases is possible (does v1.5.2 find more bugs than v1.5.1 on chi-1.5.1?).
- Gate failures and process compliance metrics are captured per run.

What this does NOT mean today:
- We do not have within-version variance estimates (we typically run each benchmark once per release; ≥3-5 re-runs per version are needed to estimate variance).
- We do not have control charts with statistically meaningful ±3σ limits (you typically want 20-30 stable observations within a single process to compute control limits; we have ~30 observations spread across 4-5 versions).
- We do not yet declare any metric to be "in statistical control."

The trajectory:

- **v1.5.x–v1.6.x:** Add `metrics/` directory; emit per-run JSON records with operational definitions of each metric; build a trend dashboard.
- **v1.6.x–v1.7.x:** Run each benchmark 3 times per version-bump to build within-version variance estimates.
- **v1.7+:** Once 6-12 months of consistent data have accumulated, evaluate whether control charts on key metrics (bugs per benchmark per strategy, gate pass rate, false-positive rate, recall against ground truth) have sufficient statistical power to be meaningful.

The discipline is inspired by Watts Humphrey's PSP/TSP work at SEI and the CMMI level 4 ("quantitatively managed") definition. That discipline took years for SEI to instrument and is rare even at large software organizations that explicitly target it. The honest framing for QPB today is "moving toward statistical control" with a multi-year horizon. Overclaiming today undermines the credibility of the eventual claim.

### Operational definitions (work-in-progress)

For metrics to be meaningful across releases, they need stable operational definitions. Drafted definitions:

- **Bug count (per repo per release per strategy)** — number of `### BUG-NNN` headings in `BUGS.md` after the named iteration strategy, after gate-pass, after categorization. Bugs found in baseline phases count toward the baseline; bugs found in iteration N count toward iteration N.
- **Process gate pass** — `quality_gate.py` exits 0 against the full repo at end-of-run, before any manual remediation. Soft warnings are logged but do not affect pass/fail.
- **False positive rate** — bugs that, on manual review of a sampled subset, are not actual defects. Requires manual sampling; cannot be computed automatically. Expressed as a confidence interval given the sample size.
- **Recall against ground truth** — fraction of v1.4.5-confirmed bugs in the pinned benchmark that are recovered by the current release. Computed automatically by ID matching against the v1.4.5 BUGS.md.
- **Run cost** — total token usage across all phases, plus wall-clock time. Captured per phase in PROGRESS.md.
- **Within-version variance** — standard deviation of bug count across N re-runs of the same release on the same pinned benchmark. Requires ≥3 re-runs per version; not yet collected systematically.

These definitions will be formalized in `metrics/SCHEMA.md` when the metrics pipeline is built.
