# Quality Playbook v1.2.15 — Design Retrospective

**Version:** v1.2.15 (with refinement v1.2.16)
**Status:** Shipped
**Date:** April 2–3, 2026 (v1.2.15); April 3, 2026 (v1.2.16)
**Author:** Andrew Stellman
**Document type:** Retrospective design doc

---

*This document describes the design of Quality Playbook v1.2.15 — the first tagged open-source release of the skill — and the v1.2.16 refinement that shipped the following day. It is written after the fact, from the git history, as part of a retrospective series documenting the skill's design evolution.*

---

## What This Version Introduced

v1.2.15 is the first tagged open-source release of the Quality Playbook. Before this release, the playbook existed as an internal system inside Octobatch — a collection of protocols (QUALITY.md, RUN_CODE_REVIEW.md, RUN_INTEGRATION_TESTS.md, RUN_SPEC_AUDIT.md, AGENTS.md) that had been iterated on against the Octobatch codebase and a second project (pbprdf) before being extracted into a portable generator. v1.2.15 is the version that crossed the threshold: it packaged the generator as an Anthropic Skill, added the missing piece that turned it from "good structural review" into "review that catches intent violations," and shipped the benchmark infrastructure needed to prove the skill was actually working.

The core additions, stated plainly, were three.

First, a new Step 7 in Phase 1 that derives testable behavioral requirements from the codebase before any review artifacts are generated. Step 7 is structured as three sub-phases — elicitation (7a), per-subsystem derivation (7b), and verification (7c) — and the requirements it produces land in a new generated file, `quality/REQUIREMENTS.md`, which feeds directly into the code review protocol. The structure borrows from the standard SRS workflow described in Stellman & Greene's *Applied Software Project Management*, Chapter 6.

Second, a restructured code review protocol that runs as three distinct passes — structural review, per-requirement verification, and cross-requirement consistency — rather than as a single omnibus pass. Each pass has a narrowly-defined job and is not allowed to wander into the other passes' territory. This is the source of the playbook's pass-by-pass coverage claims. A one-sentence anti-rationing instruction was added to Pass 1 to address a measured v1.2.14 failure mode where Pass 1 self-rationed attention because it "knew" later passes were coming.

Third, a benchmark harness (`benchmarks/`) with cross-repo validation experiments, scored runs against seven external repositories plus a held-out repo, and scored council reviews from Cursor and GitHub Copilot, all organized so the next iteration could be measured against the last. The harness is the piece that lets the playbook be improved empirically rather than by assertion. Validation culminated in a confirmed bug found in Gson (PR #2999), demonstrating that the three-pass design catches real defects in a major open-source project.

The commit that brought all of this together is `209c4bc` ("v1.2.15: Add requirement derivation, three-pass review, and benchmark validation"), which changed 771 files and added more than 110,000 lines — most of those lines are benchmark results, not playbook text. The playbook SKILL.md itself grew to 829 lines (commit `b73f1c5`), and the companion `review_protocols.md` reference grew to 691 lines (commit `c9bd74a`).

Two smaller commits followed within the same day: `bcbc011` carried forward the unchanged reference files (constitution, defensive_patterns, functional_tests, schema_mapping, spec_audit, verification, council_review_prompt, LICENSE) to complete the v1.2.15 skill bundle, and `c9bd74a` added the anti-rationing instruction to Pass 1 and documented the control comparison that justified it.

The decision to carry forward the other reference files unchanged is itself informative. The v1.2.15 changes are surgical — they restructure the parts of the playbook that the v1.2.14 benchmarks showed were underperforming, and they leave the rest alone. This is the style of change a mature skill undergoes, not the sweeping rewrites characteristic of early development.

v1.2.16 shipped the day after (`a61591e`) as a targeted refinement of the Step 7 requirement template, and it belongs in the same design era — this document covers both.

The three-pass review protocol and the requirement derivation step are joined at the hip. Neither works without the other. Without Step 7's requirements, Passes 2 and 3 have nothing to check. Without Passes 2 and 3, Step 7's requirements have nowhere to go. Shipping them together — with the benchmark evidence to back them up — is what makes v1.2.15 a coherent version rather than a grab bag of changes.

## Why It Was Needed

The playbook was working, but it had a ceiling.

Structural code review — reading code and spotting anomalies using the model's own knowledge of race conditions, null pointer hazards, resource leaks, off-by-one errors, and type mismatches — catches about 65% of real defects. That number isn't a guess; the v1.2.14 benchmark runs produced it by scoring playbook output against known defect sets across multiple repositories.

The remaining ~35% are what the v1.2.15 commit message calls "intent violations": absence bugs (code that should exist but doesn't), cross-file contradictions (each file correct in isolation, but they disagree about a shared constraint), and design gaps (a feature that was never built). No amount of careful code reading finds these, because there is nothing wrong with the code that is there. You need to know what the code is supposed to do, then check whether it does it.

The open-source framing sharpened the problem. As an internal Octobatch tool, the playbook could assume context — Andrew knew what Octobatch was supposed to do, and the review protocols were tuned to that project. As an Anthropic Skill dropped into an arbitrary codebase, the playbook had no such assumption. It needed to recover the intent of whatever project it was pointed at, and it needed to do so reliably enough that an AI with no prior context could run the review and get useful output.

The chat history captures the framing clearly: the skill must "explore a codebase from scratch — understanding its architecture, specs, and domain — then generate complete quality infrastructure." The lineage from internal practice to skill is also clear in the chat: quality practices were first developed during Octobatch's AI-driven development, then codified into protocols that shipped with Octobatch v1.0 on February 24, 2026, then extracted into a portable playbook iterated against the pbprdf project, and finally converted into a skill. v1.2.15 is the endpoint of that third stage — the transition from portable playbook to Anthropic-compatible skill.

Two specific findings from v1.2.14 shaped the v1.2.15 response.

First, when v1.2.14 attempted requirement derivation across a whole 14,000-line codebase in a single pass, it produced 16 requirements, almost all of which simply restated what specific functions do ("POST /pub must enqueue a message and return OK"). These are design statements dressed up as requirements, and they do not survive the first refactor. When the same derivation was re-run per-subsystem on focused file sets, it produced requirements that caught real cross-file bugs invisible to structural review. The difference is scope: a whole-project scan skims the most visible code paths; a per-subsystem scan forces the model to read every file carefully and reason about intent. v1.2.15's Step 7b restructures derivation around that finding — it replaces the single-pass whole-project scan with a per-subsystem loop driven by explicit category guidance.

Second, when v1.2.14's review passes ran in sequence, the first pass (structural review) implicitly self-rationed — the model knew Passes 2 and 3 were coming and held back findings it thought "belonged" in later passes. This was measurable against the control runs in `runs/improvement_001/`. The fix in `c9bd74a` is a single sentence added to Pass 1 of `review_protocols.md`: "Be thorough and exhaustive. Do not save anything for later." Tiny intervention, real effect.

v1.2.15 addressed both findings directly, and then shipped the benchmark machinery so future claims like "~65% structural coverage" or "anti-rationing improved Pass 1 yield" could be checked rather than asserted. Shipping the benchmarks with the skill is a deliberate choice — it commits the project to empirical rather than rhetorical evidence for every subsequent change.

The "first open-source release" framing also meant that the skill needed to be legible to people who had never heard of Octobatch. A user opening the skill for the first time should be able to read the SKILL.md, understand what the skill does and why, and run it without calling the author. This put pressure on every section of the SKILL.md to justify itself, and several of the additions in v1.2.15 (the explicit "why this matters" paragraphs, the example cases, the embedded citations to Stellman & Greene) exist to make the skill self-explanatory.

## The Design

The v1.2.15 playbook is a four-phase workflow:

1. **Phase 1: Explore the Codebase** — Steps 0 through 7, ending with the new requirement derivation in Step 7. Nothing gets written to disk during exploration; the playbook reads, maps, traces, and derives.
2. **Phase 2: Generate the Quality Playbook** — produces the six deliverable files (QUALITY.md, functional tests, RUN_CODE_REVIEW.md, RUN_INTEGRATION_TESTS.md, RUN_SPEC_AUDIT.md, AGENTS.md).
3. **Phase 3: Verify** — runs the self-check benchmarks defined in `references/verification.md`, fails loudly if anything is off.
4. **Phase 4: Present, Explore, Improve** — an interactive loop with the user.

Three of the v1.2.15 innovations land in Phase 1 (Step 7 requirement derivation), Phase 2 (three-pass review in RUN_CODE_REVIEW.md), and the new `benchmarks/` tree (evidence for the coverage claims). Phases 2 and 3 were restructured around the new requirements file; Phase 4 is carried forward from earlier versions.

The phase boundaries matter. Phase 1 produces no deliverables on disk — it reads and derives. Phase 2 produces the six generated files. Phase 3 runs the verification benchmarks and fails loudly if anything is off. Phase 4 hands control back to the user. The boundaries are enforced by phase transition gates written into the SKILL.md as completion criteria, and the v1.2.15 SKILL.md shipped these gates as explicit sections (lines 449 and 464 of the generated SKILL.md).

The "do not write anything to disk during Phase 1" rule is important. If the skill writes files during exploration, it creates pressure to treat early drafts as deliverables — the output is there, so surely it's done. Keeping Phase 1 entirely read-and-derive forces the skill to complete its exploration before any artifact is committed, which prevents a class of premature-optimization failures.

### Step 7: Requirement Derivation as a Three-Sub-Phase Process

Step 7 sits at the end of Phase 1's exploration arc. By the time the skill reaches Step 7, it has already asked about development history (Step 0), identified domain and specs (Step 1), mapped the architecture and identified subsystems (Step 2), read the existing tests (Step 3), read the specifications (Step 4), read function signatures and real data (Step 4b), found the skeletons (Step 5), traced state machines (Step 5a), mapped schema types (Step 5b), audited parallel code paths and context propagation (Step 5c), checked generated and invisible code (Step 5d), and identified quality risks (Step 6).

Everything found during those steps — specs, ChangeLog entries, config structs, source comments, defensive patterns, chat history — gets distilled into a set of testable requirements in Step 7. The SKILL.md states the claim directly: "This is the most important step for the code review protocol."

Step 7 was restructured around the standard requirements engineering workflow from Stellman & Greene's *Applied Software Project Management* (Chapter 6): elicit needs first, document behavior second, verify for defects third. This was the structural anchor. The playbook needed a principled reason for the three sub-phases — not just "try harder" — and borrowing from a textbook the author literally wrote was the cleanest available source.

**Step 7a — Elicitation.** Before writing any requirements, the skill produces a *discussion summary*: an internal working document (not a deliverable) that captures purpose, users and operational context, known business rules, design decisions and their rationale, and known risks and past failures.

The sources are READMEs, deployment scripts, config structs, ADRs, commit messages, issue trackers, chat history from Step 0, and defensive code patterns from Step 5. The point of the discussion summary is to prevent the single most common failure mode: writing requirements that describe what the code does instead of what it is supposed to do.

The distinction from Stellman & Greene is explicit in the SKILL.md: requirements describe *behavior* (what the software must do, independent of implementation), not *design* (specific functions, endpoints, or data structures). The canonical example in the SKILL.md makes this concrete. "POST /pub must enqueue a message" is design — it names an endpoint. "A producer must be able to publish a message to a named topic, and that message must be delivered to every subscribed channel" is behavior — it describes what the system does without constraining how. Requirements at the behavior level survive refactoring; requirements at the design level break whenever code is reorganized.

**Step 7b — Per-Subsystem Derivation.** For each subsystem identified in Step 2 (architecture mapping), the skill reads the full focused file set — typically 3–8 files per subsystem — and derives behavioral requirements category by category. Not just the main module: the options/config, the tests, the utilities it depends on. For a subsystem of 5 files totaling 1,500 lines, read all of them.

Seven categories are checked for every subsystem, with explicit instructions not to skip categories that seem inapplicable without confirming they don't apply:

- **Input validation boundaries** — for every parameter the subsystem accepts (config fields, protocol parameters, API inputs), state the valid range and what must happen when input is outside it. Include both explicit constraints (documented ranges) and implicit constraints (a length field backed by int32 has a maximum of 2^31-1, whether documented or not).
- **Security policy propagation** — for every security credential or policy the subsystem consumes (TLS certs, CA files, auth tokens, encryption settings), trace whether it propagates to all connection paths. If the subsystem configures TLS for inbound connections, do outbound connections also use the configured CA?
- **API contracts and wire-format constraints** — for every bit layout, encoding format, field width, or protocol negotiation, state the constraints that must be consistent across all files.
- **Resource lifecycle** — for every resource the subsystem creates (listeners, connections, goroutines, file handles, buffers), state what must happen during shutdown.
- **Data integrity and consistency** — for every piece of mutable shared state, state the consistency invariants.
- **Operational contracts** — for every operator-facing control (pause, health check, graceful shutdown), state what the operator should observe and when.
- **Error handling contracts** — for every error path, state whether the error should be fatal or recoverable, and what the caller should observe.

Each requirement is written against a template. In v1.2.15, the template had four fields: Summary, Rationale, References, and Specificity (with Specificity being either "specific" — testable at one code location — or "directional" — guides audit across locations).

The rationale field is the lever: it forces the requirement to state *why*, not just *what*. The SKILL.md carries an example that makes the distinction sharp: "IDENTIFY bodies must respect MaxBodySize" can be satisfied by any validation, but "IDENTIFY bodies must be bounded because an unbounded allocation on untrusted input lets a single malicious client crash the process" tells the reviewer exactly what failure mode to check for, and it can't be argued down.

After documenting derived requirements, Step 7b adds a domain-knowledge pass: for each category, ask what requirements *should* exist for a system of this type even if the documentation doesn't mention them.

A messaging system should validate message sizes. A TLS system should propagate CA configuration. A system with persistent state should handle corruption on reload. A system that accepts connections should limit concurrent connections. These requirements come from domain knowledge, not from reading the specific project's docs — and they catch the absence bugs that code-reading alone misses.

The SKILL.md is emphatic about not filtering:

> Keep all requirements. Do not filter out "obvious" or "trivial" requirements. Experiments show that filtering is counterproductive — the cost of checking an extra requirement is low, and the cost of missing a bug because you pruned the requirement that would have caught it is high.

Directional requirements ("all outbound connections must use the configured CA") are explicitly flagged as especially valuable for the cross-requirement consistency check even though they seem vague. The directional/specific distinction is the playbook's acknowledgement that not every requirement is checkable at a single code location, and that this is fine — some requirements are audit-across-files checks rather than point checks.

**Step 7c — Requirement Verification.** Before recording the final requirements, the skill inspects each one against an SRS-style checklist adapted from Stellman & Greene:

- *Clarity* — is the requirement clear and unambiguous? Could two reviewers interpret it differently?
- *Completeness* — does it specify what happens in both the normal case and the error case?
- *Testability* — can you write a concrete test or review check that would detect a violation?
- *Behavioral focus* — does it describe behavior or design? If it names a specific function or endpoint, rewrite it to describe the behavior instead.
- *Consistency* — does it contradict any other requirement?
- *Rationale present* — does it explain why the requirement matters?

Requirements that fail clarity or testability are removed. Requirements that describe design are rewritten as behavior. Redundant requirements are merged. The output lands in `quality/REQUIREMENTS.md` (uppercase, matching the other review artifacts — a small rename from v1.2.14's `requirements.md` that was worth the churn for consistency).

The SKILL.md also shipped a requirement count calibration: for a medium project (5–15 core source files, 3–5 subsystems), expect 30–60 requirements. Fewer than 20 almost always means the derivation was too shallow — either subsystems were skipped, categories were not checked systematically, or requirements describe implementation rather than behavior. This calibration was set against the v1.2.14 evidence (16 requirements from a whole-project scan was clearly wrong) and was explicitly removed in v1.2.16 after further evidence showed the number capped yield rather than signaling completeness.

### The Three-Pass Code Review

The review protocol (File 3: `quality/RUN_CODE_REVIEW.md`) was split into three passes, each with a narrowly-defined job. The division isn't arbitrary — each pass catches a class of bugs the others cannot.

**Pass 1 — Structural Review.** Read the code and spot anomalies. No requirements, no focus areas — just the model's own knowledge of code correctness. Race conditions, null pointer hazards, resource leaks, off-by-one errors, type mismatches. This is what every AI code review tool already does well, and the playbook keeps it intact rather than re-inventing it.

The v1.2.15 SKILL.md anchors the coverage claim here: "Pass 1 catches ~65% of real defects." The mandatory guardrails (line numbers required, read function bodies not just signatures, grep before claiming a pattern is absent) are retained from earlier versions. What changed in v1.2.15 is the anti-rationing instruction, discussed below — a tiny addition with measurable effect.

**Pass 2 — Requirement Verification.** For each testable requirement in `quality/REQUIREMENTS.md`, check whether the code satisfies it. Either show the code that satisfies it or explain specifically why it doesn't. This is a pure verification pass — the reviewer's only job is "does the code satisfy this requirement?"

Not a general review. Not looking for other bugs. Just verification. The narrow scope is the point: Pass 2 catches bugs that structural review misses because the code that *is* there is correct; the bug is what's missing or what doesn't match the spec. This is where the absence bugs and design-gap bugs surface.

**Pass 3 — Cross-Requirement Consistency.** Compare pairs of requirements that reference the same field, constant, range, or security policy. For each pair, verify that their constraints are mutually consistent. Do numeric ranges match bit widths? Do security policies propagate to all connection types? Do validation bounds in one file agree with encoding limits in another?

Pass 3 catches contradictions where two individually-correct pieces of code disagree about a shared constraint — cross-file arithmetic bugs and design gaps where a security configuration doesn't propagate to all connection paths. These bugs are invisible to both structural review and per-requirement verification because each requirement is satisfied individually; the bug only appears when you compare them.

The three-pass structure isn't novel in the abstract — "review from different angles" is an old idea. What matters in the v1.2.15 design is the commitment to keeping the passes separated and narrowly scoped. Every pass has a job it is allowed to do and jobs it is not allowed to do. This is the only way to get quantifiable pass-by-pass coverage claims, and the only way to diagnose where the review is weak when it misses a bug.

### The Anti-Rationing Instruction

Commit `c9bd74a` is small but load-bearing. It added a single explicit instruction to Pass 1 of `review_protocols.md`: "Be thorough and exhaustive. Do not save anything for later."

The commit message is blunt about why: "Addresses v1.2.14 finding where Pass 1 self-rationed attention because it knew Passes 2 and 3 were coming." The same commit added the v1.2.14 control comparison evidence to the "Why Three Passes" section — the rationale isn't a guess; the control runs are on disk.

This was the first clear instance of a pattern that recurs throughout the playbook's evolution: the model's behavior in one pass is shaped by its knowledge of the surrounding workflow, and ignoring that dynamic produces worse output than addressing it directly. The instruction is trivially short, but without it Pass 1 underperforms measurably.

The broader lesson is that prompt engineering in a multi-pass workflow is not just about the current pass — it is about how the current pass reasons about the passes around it. v1.4.3's orchestrator-hardening work extends this insight from the review passes to the orchestrator itself.

The anti-rationing fix also illustrates why the benchmark harness is essential. Without `runs/improvement_001/`, there would be no way to distinguish "Pass 1 is self-rationing" from "Pass 1 is finding everything it can and the remaining 35% just isn't visible to structural review." The control comparison in v1.2.14 makes the diagnosis possible, and the one-line fix in `c9bd74a` is the response. Diagnose, fix, re-measure — the playbook's development process mirrors the review discipline it teaches.

### Benchmark Validation

v1.2.15 shipped the benchmark infrastructure that v1.2.14 and earlier versions had been building toward.

The `benchmarks/` directory carries the experiment design (`EXPERIMENT.md`), the defect schema (`defect_schema_v2.md`), and curated defect sets for multiple repositories — `nsq_defects_v2.json` alone is over 1,200 lines of catalogued defects, each tagged with its source, category, and severity.

Inside `runs/improvement_001/` the commit captures the entire improvement sweep: every playbook version from v1.2.0 through v1.2.9 preserved as a complete frozen skill (SKILL.md plus references plus LICENSE), plus scored runs against seven external repositories — repo1_cli, repo2_axum, repo3_httpx, repo4_trpc, repo5_newtonsoft, repo6_serde, repo7_phoenix — plus a held-out okhttp repo, plus scored council reviews against four external skills (agent governance, CodeQL, eval-driven development, secret scanning), plus the `SKILLS_EXPERIMENT_SUMMARY.md` that consolidates the results.

The held-out okhttp repository matters. Holding a repository out of the improvement loop and scoring against it only at the end is what prevents the playbook from overfitting to the repos that drove the iteration. This is basic experiment design, but shipping it alongside the skill commits the project to treating playbook development the way anyone would treat a model — train on one set, validate on another, report both.

The council review scoring (Cursor, GitHub Copilot, and multiple reruns) is the other half of the benchmark story. The Council of Three spec-audit protocol (`RUN_SPEC_AUDIT.md`) had been part of the playbook since earlier versions, and v1.2.15 produced scored runs showing how the playbook's generated audit compared against Cursor's and Copilot's independent reviews. The comparison is what lets the skill's output be placed on the same scale as commercially-available AI review tools — something that was not possible before v1.2.15 shipped the scoring machinery.

The Gson documentation enrichment experiment is called out in the v1.2.15 commit message as the validation milestone. Running the three-pass review against Gson found a confirmed bug: duplicate key detection failed when the first value was null. This became PR #2999 against the Gson repo.

This wasn't just "the skill produced output"; it was "the skill found a real bug in a major open-source project," which is the strongest available evidence that the three-pass design does what the design claims. v1.2.16's commit message returns to the same experiment to validate the restructured template — on Gson, the seven-field template produced 70 requirements (up from 48 with the four-field template) in a single pass, and the conditions-of-satisfaction field explicitly enumerated the null-first-value edge case that Pass 2 then confirmed was unhandled.

Taken together, the benchmark corpus that ships in v1.2.15 is the first time the playbook could answer the question "has the latest change improved or regressed the skill?" with something other than intuition. Every subsequent version in the repo's history carries forward some form of the same harness.

The benchmark infrastructure also enables a form of version archaeology. Because each playbook version from v1.2.0 through v1.2.9 is preserved as a frozen skill bundle, it is possible to re-run any of those versions against the current defect corpus and ask "what would this older version catch today?" This is not a hypothetical capability — the improvement sweep files in `runs/improvement_001/scores/` are exactly these re-run results, with each version scored against the held-out repositories.

### Phase 2 Integration with the New Requirements File

The requirement derivation work in Step 7 only pays off if the generated review artifacts actually use it. Phase 2 of the v1.2.15 playbook was updated so that the generated `RUN_CODE_REVIEW.md` references `quality/REQUIREMENTS.md` as a first-class input — not just an additional document to consult, but the spine of Passes 2 and 3.

The Phase 3 verification checklist (File 13 in `references/verification.md`) was also updated to check that `RUN_CODE_REVIEW.md` lists the bootstrap files, references `quality/REQUIREMENTS.md`, and contains all three passes. An AI with no prior context should be able to read the generated review protocol and perform a useful code review. If any of those checks fail, Phase 3 fails and Phase 2 has to be redone.

The filename rename (`requirements.md` → `REQUIREMENTS.md`) threads through both commits `b73f1c5` and `c9bd74a` because it touches both the SKILL.md's description of Step 7 output and the `review_protocols.md` bootstrap section that tells the review protocol where to find requirements.

## Pivotal Choices

Several decisions in v1.2.15 shaped later versions, and a few of them were revisited within days.

### Behavior over design in requirements

Forbidding requirements that name specific functions or endpoints was a strong stance, and it held. Every subsequent version of the playbook continues to separate behavioral requirements (what the system must do) from structural artifacts (how the code is organized).

This is the cleanest line between specification work and implementation work, and the playbook takes it seriously. It also aligns the playbook with a tradition that long predates AI code review — the same distinction shows up in IEEE 830 and in every serious treatment of requirements engineering. The playbook is not inventing here; it is adopting.

The practical consequence is that a Pass 2 reviewer who finds a requirement has been violated can point at an observable behavior, not at a specific function's absence. "The system does not limit inbound message size" is reviewable even if the code has been refactored across files since the requirement was written. "`handleIDENTIFY` does not call `validateSize`" is not.

### Rationale as a mandatory field

Requiring a rationale for every requirement — not optional, not best-effort — was the choice that made Pass 2 actually work. Without rationale, "the code satisfies the requirement" becomes a coin flip: any plausible-looking code can be claimed to satisfy a rationale-less requirement. With rationale, the reviewer has a concrete failure mode to check for.

The rationale also prevents requirements from being argued down. A reviewer presented with a requirement that just says "IDENTIFY bodies must respect MaxBodySize" can be talked into "well, there's no explicit check but the connection read size would limit it in practice." A reviewer presented with a rationale — "because an unbounded allocation on untrusted input lets a single malicious client crash the process" — has to produce the evidence that the specific failure mode cannot occur. The burden shifts in the right direction.

This pattern — forcing the *why* to be written down alongside the *what* — recurs throughout the playbook's later evolution. The bootstrap self-audits, the challenge gate, the condition-of-satisfaction fields in v1.2.16 all extend the same discipline.

### Narrow pass scopes

The commitment to keeping Pass 1, Pass 2, and Pass 3 from bleeding into each other — each with its own SKILL.md paragraph stating what the pass does and does not do — is what makes pass-by-pass coverage measurement possible.

If Pass 2 is allowed to also report structural bugs, there is no way to know whether a bug found in Pass 2 came from the requirement check or from the reviewer lapsing back into structural mode. If the passes run together, the "~65% structural / ~35% intent" decomposition becomes unmeasurable. Later versions tighten this further, but the original discipline is in v1.2.15.

There is a secondary benefit: narrow scopes make each pass easier to evaluate. When a bug is missed, the question "which pass should have caught this?" has a clear answer, and the fix lands in that pass's protocol rather than being sprinkled across the whole review document.

### Filename case conventions

The rename from `requirements.md` to `REQUIREMENTS.md` looks trivial but it's a signal: the playbook treats the generated artifacts as first-class files with consistent naming (`QUALITY.md`, `RUN_CODE_REVIEW.md`, `RUN_INTEGRATION_TESTS.md`, `RUN_SPEC_AUDIT.md`, `REQUIREMENTS.md`, `AGENTS.md`). All the generated top-level files are uppercase; the reference files under `references/` stay lowercase. The naming split mirrors the file's role — top-level files are deliverables a human or AI will use directly, reference files are skill-internal.

Small things like this accumulate into a playbook that feels coherent rather than accreted. The cost of the rename is almost zero; the cost of inconsistent naming shows up as confusion six months later when someone asks "why is this one lowercase?"

### Keep all requirements, don't filter

The SKILL.md explicitly instructs against pruning "obvious" or "trivial" requirements. The reasoning is stated: the cost of checking an extra requirement is low, the cost of missing a bug because you pruned the requirement that would have caught it is high. This is a bias the skill needs to fight against, and stating it in the SKILL.md is the intervention.

The instinct to filter is strong because "obvious" requirements look like noise in the generated file. The playbook's response is that the signal-to-noise ratio of the file is not the right metric — what matters is whether Pass 2 catches bugs, and Pass 2 catches more bugs when the requirements list is longer. The cost of a longer REQUIREMENTS.md is paid in review time, not in review quality.

### The 30–60 requirement calibration, later removed

v1.2.15 set a range of 30–60 requirements for a medium project as a sanity check. v1.2.16 (commit `a61591e`) removed the cap entirely, after evidence from Gson showed that a richer template produced 70 requirements in a single pass and that the higher count included the specific edge case (null first value in duplicate key detection) that caught the real bug.

The lesson embedded in the v1.2.16 commit message — "the goal is completeness, not hitting a number" — is one of the reasons later versions avoid numeric targets for generated artifacts. Calibrations are useful for catching gross under- or over-generation, but they drift into targets once they are written down, and once they are targets they stop being diagnostic.

This is one of the few cases where a v1.2.15 decision was actively walked back rather than extended. It is worth noting in the retrospective because it shows the playbook's ability to revise itself when the evidence disagrees with the written spec — a quality that depends directly on the benchmark harness that v1.2.15 itself shipped.

### v1.2.16 as a Same-Era Refinement

v1.2.16 shipped the day after v1.2.15 and belongs in the same design era. Its single change (commit `a61591e`) expands the per-requirement template from 3 fields (summary, rationale, specificity) to 7 fields:

- summary
- user story with mandatory "so that" clause
- implementation note (renamed from rationale)
- conditions of satisfaction
- alternative paths
- references
- specificity

The mandatory "so that" clause in the user story and the conditions-of-satisfaction block are the two fields that matter most.

The "so that" clause forces the requirement author to state the business value, which is a check against requirements that look plausible but serve no one. A requirement like "The system must validate X as a user so that an attacker cannot crash the process by submitting malformed X" cannot be written if the author cannot identify the "so that" — which means it cannot be written at all if it is not actually valuable.

Conditions of satisfaction force the author to state the concrete observable outcomes that indicate the requirement is met — which is what Pass 2 actually verifies against. A Pass 2 reviewer reading a requirement with conditions of satisfaction has an explicit checklist; a Pass 2 reviewer reading a requirement without them has to invent the checklist on the fly, which is where misses come from.

Conditions of satisfaction, in particular, is where the Gson bug was caught: the template's condition "duplicate key detection works when the first value is null" was an explicit edge case listed in the generated requirements, and Pass 2 then checked whether the code satisfied that condition. The edge case only appeared because the template forced the enumeration; a summary-plus-rationale template would likely have produced a generic "duplicate keys are detected" requirement that Pass 2 would have marked as satisfied.

This is the characteristic v1.2.15/v1.2.16 pattern: the skill's output quality is a function of the structure it is forced to produce. Changing the structure — adding a rationale field, adding conditions of satisfaction, forcing per-subsystem derivation — changes what the model pays attention to, and what the model pays attention to determines which bugs the review finds. The skill is not asking the model to "try harder"; it is asking the model to produce a different shape of artifact, and the different shape is what contains the new bug-finding capability.

v1.2.15 and v1.2.16 together are the pair that turned requirement derivation from a useful idea into a discipline that reliably catches bugs.

For most readers of this retrospective, it is reasonable to think of v1.2.15 and v1.2.16 as a single release — one establishing the structure, the other tuning the template. The two commits landed inside 26 hours of each other, both carry the same author, and both are validated against the same Gson experiment. Later releases (v1.3.x, v1.4.x) refer back to "the v1.2.15 design" without distinguishing which of the two commits a given element came from, which is how this retrospective treats them as well.

## How It Fits Today

The current playbook (v1.4.5 at the time of writing, with v1.5.0 and v1.5.1 designed but not yet all of it implemented) still runs on the bones laid down in v1.2.15. The three-pass review is still the review. Behavioral requirements are still the bridge between exploration and review. The benchmark harness in `benchmarks/` is still how claims about coverage are validated rather than asserted. The Stellman & Greene requirements engineering frame (elicit, derive, verify) is still the structure of Step 7. The uppercase-filename convention is still in force.

What has changed since v1.2.15 is scaffolding around the core rather than the core itself.

The orchestrator-hardening work (v1.4.3, v1.4.4) built explicit protocols for how a Claude Code session drives the skill, solving a class of problems — single-context collapse, subprocess spawning confusion — that hadn't been visible at v1.2.15 because the skill was being run by its author who knew how it was supposed to behave. When the skill landed in the hands of users without that author context, the orchestrator behaviors that v1.2.15 left implicit became the dominant source of failure.

The challenge gate for false-positive detection (v1.4.3, commit `3045952`) is a fourth review pass that catches bugs the three-pass pipeline hallucinates; it augments the v1.2.15 design rather than replacing it. The three-pass pipeline is optimized for coverage (finding as many real bugs as possible), and the challenge gate adds precision (filtering out the false positives that a high-coverage pipeline inevitably produces).

The bootstrap self-audit work (v1.4.0 onward) closed the loop by running the playbook against itself and logging the bugs it finds in its own implementation — a practice that would have been impossible without v1.2.15's commitment to measurable output. The recent commits (`d6828a5`, `8c89b6e`, `9a2e90b`, `9b3fc82`) document a steady stream of self-audit findings being fixed, which is the behavior of a skill that has reached a level of maturity where it can be audited by its own protocols.

Some v1.2.15 decisions were walked back. The 30–60 requirement count calibration was removed in v1.2.16 and did not return. The four-field requirement template was replaced by the seven-field template in v1.2.16 and has continued to evolve. The single SKILL.md monolith has been broken up in later versions, with language-specific functional test patterns extracted and then (in v1.4.3's `477aeaf`) re-folded back into the core after the extraction proved counterproductive. These are revisions, not reversals — the direction of each change is consistent with the v1.2.15 design philosophy, which treats the playbook as something that should be measured and adjusted rather than argued about.

The lineage from v1.2.15 to the current skill is legible in the version-numbered reference directories still preserved in `benchmarks/playbook_v1.2.0/` through `benchmarks/playbook_v1.2.10/` and `runs/improvement_001/playbook_versions/`. Any reader who wants to understand how a specific part of the current playbook came to be written the way it is can walk the version history forward from the v1.2.15 baseline and see which change landed when.

The playbook's current behavior is recognizably the v1.2.15 design extended, not a reinvention. If a v1.2.15-era user returned to the current skill, they would find the Step 7 structure, the three-pass review, and the benchmark harness all where they left them, with additional scaffolding around them. That is the strongest evidence that the v1.2.15 design was correct at the core — the core has not had to be redone.

## Provenance

Primary sources are the git commits on this repository.

The v1.2.15 commits, in chronological order:

- `b73f1c5` (April 2, 2026, 16:41) — Quality Playbook v1.2.15: restructure Step 7 with per-subsystem requirement derivation. Adds the 829-line SKILL.md with the new Step 7 structure, the Stellman & Greene citation, the seven requirement categories, the four-field template, and the requirement count calibration.
- `c9bd74a` (April 2, 2026, 16:42) — v1.2.15: update review_protocols.md and add Pass 1 anti-rationing instruction. Adds the 691-line review_protocols.md reference, the one-sentence anti-rationing instruction, and the v1.2.14 control comparison evidence in the "Why Three Passes" section.
- `bcbc011` (April 2, 2026, 16:43) — v1.2.15: add remaining reference files and license. Carries forward constitution, defensive_patterns, functional_tests, schema_mapping, spec_audit, verification, council_review_prompt, and LICENSE unchanged from v1.2.14 to complete the v1.2.15 skill bundle.
- `209c4bc` (April 3, 2026, 13:40) — v1.2.15: Add requirement derivation, three-pass review, and benchmark validation. The 771-file, 110,131-line commit that adds the full `benchmarks/` tree, the `runs/improvement_001/` improvement sweep with v1.2.0 through v1.2.9 preserved as frozen skills, seven scored external repositories plus held-out okhttp, four scored council reviews, the SKILLS_EXPERIMENT_SUMMARY, updated tooling (assemble_v8.py, extract_defect_data.py, generate_sample.py), and new defect data for four additional repositories.

The v1.2.16 refinement commit:

- `a61591e` (April 3, 2026, 18:10) — v1.2.16: Restructure Step 7 requirement template with user stories and conditions of satisfaction. A 15-line diff in `playbook/SKILL.md` that expands the per-requirement template from 3 to 7 fields and removes the requirement count cap, validated on Gson (48 → 70 requirements, conditions-of-satisfaction field catches the null-first-value edge case that surfaces PR #2999).

The v1.2.15 SKILL.md is preserved at `runs/improvement_001/playbook_versions/v1.2.15/SKILL.md` and the companion references are in the adjacent directory. The benchmark harness, scored runs, and experiment summaries from this era are preserved under `benchmarks/` and `runs/improvement_001/scores/`.

Supplementary context on the "why" — specifically the decision to package the playbook as an Anthropic Skill for the `anthropics/skills` GitHub repo and the three-stage lineage (Octobatch practices → v1.0 protocols → extracted playbook → skill) — is drawn from the Cowork session `AI Chat History/Cowork-2026-03-13-Convert quality playbook to open-source skill-1.md`. Where git and chat disagree, git is authoritative.

Claims in this document about the ~65% structural-review coverage and the v1.2.14 whole-project-scan failure mode (16 shallow requirements) are cited in the SKILL.md itself and in the commit messages for `b73f1c5` and `209c4bc`. The v1.2.14 control comparison evidence that motivated the anti-rationing instruction is referenced in commit `c9bd74a`'s message and lives in `runs/improvement_001/`. The Gson PR #2999 validation is referenced in both the `209c4bc` and `a61591e` commit messages.

All file paths in this document are relative to the Quality Playbook repository root unless otherwise noted.

This retrospective was written after v1.5.0 and v1.5.1 had already been designed, which means the "How It Fits Today" section is written with hindsight not available at v1.2.15's release. That hindsight is what retrospectives are for, and the presence of the later design documents in `AI-Driven Development/Quality Playbook/` provides additional reference material for anyone following the design arc in order.
