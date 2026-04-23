# Quality Playbook v1.3.29 — Design Retrospective

**Version:** 1.3.29

**Status:** Shipped

**Date:** 2026-04-12

**Author:** Andrew Stellman

**Primary commit:** `f6d9e67` — "v1.3.29: multi-pass architecture for context-limited models"

**Follow-on refinement:** `9e43190` — "v1.3.30: multi-pass execution is internal to the skill, not external scripts"

---

## What This Version Introduced

Version 1.3.29 introduced the **multi-pass architecture** — a way to run the
Quality Playbook across several sequential passes rather than in a single
monolithic prompt.

Each pass has a focused purpose, a smaller context footprint, and hands off its
findings to the next pass through files written to disk. The skill stops
needing to hold every phase of the work in working memory at once. Instead,
each pass loads only what it needs, writes its output, and the next pass picks
up from there.

This is a foundational architectural change. It reshaped how the skill thinks
about context management, how phases are bounded, and what "state" means across
the run. It persisted through every subsequent version.

The six-phase architecture that ships today is a direct descendant of the
four-pass split introduced here. Each phase is essentially a pass, with
file-based handoff between them, and with the contract that the model does not
need to carry the entire skill in working memory simultaneously.

The commit also introduced the first formal specification for
`quality/EXPLORATION.md`, the handoff file between the exploration pass and the
artifact-generation pass. EXPLORATION.md became the template for every later
handoff artifact — a structured Markdown file written by one pass, read by the
next, used to cross a context boundary without losing fidelity.

The single-pass mode was preserved as a legacy path behind a `--single-pass`
flag on the runner script, so interactive human-driven use was not disrupted.
The intent was deliberate. Multi-pass was not a mandate; it was a capability
the skill gained. Interactive users who did not need the context headroom could
keep running the skill the old way. Context-limited environments — the ones
that had failed in testing — got a path that would actually complete.

## Why It Was Needed

The trigger was a concrete, measurable failure.

Version 1.3.28 had been run across eight representative repositories on the
`copilot/gpt-5.4` endpoint. Three of the eight — chi, cobra, and javalin —
failed to complete. The other five did complete, and they completed well.

The failure signature was unambiguous. It was not a correctness problem. The
five repos that did finish produced excellent output: 100% conformance on
heading format, 100% conformance on JSON structure, 100% conformance on inline
diff formatting. Quality was fine where the run finished at all. What was
missing was completion itself.

The commit message names the cause directly: "the 168KB SKILL.md exceeds
effective working memory."

By v1.3.28, SKILL.md had grown to 168 KB. That is a lot of instruction to keep
resident in working memory while simultaneously doing everything else the skill
asks the model to do in a single session.

In a single-pass execution, the model is asked to hold: the full skill, the
accumulated exploration findings about the target codebase, the partially
generated artifacts, the in-flight reasoning about requirements and use cases,
the code review pass, the spec audit, the TDD verification, and the
reconciliation step. All of that coexists in one working context.

"Effective working memory" is doing real work in that phrasing. It is not the
same as context window size. A model can have a 200K token context window and
still degrade in performance when the active instruction set, the accumulated
findings, the partially-generated artifacts, and the in-flight reasoning all
have to coexist.

The relevant constraint is not "does it fit." The relevant constraint is "can
the model reason coherently across all of it at once." For context-limited
models — GPT-4-8k being the canonical example, but the problem generalizes to
any model under memory pressure — the answer was no.

There was also a ceiling effect on the other side. The five repos that did
complete had been run on endpoints with more headroom, and they produced
excellent output. That mattered. It told the owner that the content of the
skill was working; the quality benchmarks were being met wherever the run
finished. The problem was localized to completion on tighter endpoints, not to
any deficiency in the instructions themselves.

The old design assumed one pass. One prompt, one continuous session, all
phases reasoned about together. That assumption was never strictly necessary;
it was just the simplest thing.

When it stopped working for three-eighths of the test repos, it had to change.

## The Multi-Pass Design

The v1.3.29 design splits the playbook's execution into four sequential passes,
each with a narrowly scoped prompt and a well-defined input and output.

### Pass 1 — Explore

The model runs Phase 1 only. It explores the codebase from scratch.

It identifies the domain and stack. It maps the architecture. It catalogs
existing tests. It reads specifications in `docs_gathered/`. It identifies
quality risks. It analyzes skeletons and dispatch tables. It derives
requirements (REQ-001 through REQ-NNN). It derives use cases (UC-01 through
UC-NN).

When it is done, it does not proceed to generate artifacts. It writes
everything it learned to `quality/EXPLORATION.md` and stops.

The critical design choice in Pass 1 is the stopping point. A naive design
would have the model keep going — once you have explored, why not generate?
The reason is memory pressure. By the end of Phase 1, the model's working
context is dense with exploration detail. If it proceeds immediately to
generation, it either drops exploration context implicitly (which risks losing
fidelity) or carries it (which leaves no room for the generation work). A
deliberate stop, with a written handoff, resolves this.

### Pass 2 — Generate

A fresh pass begins.

It reads `quality/EXPLORATION.md` — not the codebase, not the full skill
history, just the structured findings — and uses that as the basis for
generating the nine playbook artifacts: the quality constitution, functional
tests, code review protocol, consolidated bug report, TDD verification
protocol, integration testing protocol, spec audit, AI bootstrap file, and so
on.

Because the exploration work is already on disk and summarized, this pass does
not need to re-explore. It can focus its working memory on generation.

The point of restarting with a fresh pass is not theatrical. It is functional.
The model's working context at the start of Pass 2 is: the skill, the
exploration findings (summarized, not raw), and nothing else. That is enough
to generate good artifacts. It is not enough to also hold every intermediate
reasoning step from Phase 1, and that is by design.

### Pass 3 — Review

Another fresh pass.

It reads the artifacts that Pass 2 produced and performs the review-oriented
work: the code review pass, the spec audit (Council of Three), the TDD
verification, and the reconciliation step that catches contradictions where two
individually-correct pieces of code disagree at the interface.

Again, this pass does not need to carry exploration or generation context — it
reads the artifacts it is reviewing and goes.

The reconciliation step is particularly worth noting. Reconciliation catches
interface-level contradictions: places where Module A and Module B each look
correct in isolation, but their combined behavior violates a spec. This kind
of finding is easier to produce in a review-focused pass than in a
generation-focused one, because the review pass is already oriented around
reading artifacts against each other.

### Pass 4 — Gate

The final pass runs `quality_gate.sh`, collects the FAILs, fixes them, and
saves the log.

This is the enforcement pass — the one that verifies the run met its own
standards and corrects anything that did not.

The gate is small but load-bearing. Without it, a multi-pass run could finish
with silent failures hiding inside otherwise-clean artifacts. The gate
explicitly verifies that the output meets the conformance checks (headings,
JSON, diffs, version stamps, cross-references) that the earlier passes were
supposed to produce correctly.

### Handoff Through Files

Between passes, everything persists on disk. This is the defining property of
the architecture.

`quality/EXPLORATION.md` is the handoff from Pass 1 to Pass 2.

The generated artifacts themselves — REQUIREMENTS.md, CONTRACTS.md, BUGS.md,
the test files, and the rest — are the handoff from Pass 2 to Pass 3.

`quality/PROGRESS.md` is updated continuously across all passes as the
cumulative tracker. Most importantly, it holds the cumulative BUG list, so
that no finding is orphaned just because it was produced in a phase that did
not end up being the one to write the final report.

The core invariant of the design is simple: **the model never needs the entire
skill in working memory at once.** Each pass has its own prompt, scoped to its
phase, and it loads only the files relevant to that phase from disk.

### Changes to SKILL.md

The SKILL.md changes in this commit were focused.

A new section, "Multi-pass execution," was added after Phase 0 to explain the
mode. It described the sequential-pass structure, the handoff-through-files
approach, and the context-limited-model motivation.

A new subsection, "Write exploration findings to disk," was added at the end of
Phase 1 as a checkpoint. This subsection made the handoff requirement
unmistakable — the model does not leave Phase 1 without writing EXPLORATION.md.

A full EXPLORATION.md template was specified, with required sections for:

- Domain and Stack (language, framework, build system, deployment target)
- Architecture (key modules with file paths, entry points, data flow, layering)
- Existing Tests (framework, count, coverage areas, gaps)
- Specifications (what `docs_gathered/` contains, key spec sections, behavioral
  rules)
- Quality Risks (top risks identified, ordered by severity)
- Skeletons and Dispatch (state machines, dispatch tables, feature registries,
  with file:line citations)
- Derived Requirements (REQ-001 through REQ-NNN, each with spec basis and tier)
- Derived Use Cases (UC-01 through UC-NN, each with actor, trigger, expected
  outcome)
- Notes for Artifact Generation (anything the next phase needs to know —
  naming conventions, test patterns, framework quirks)

The template is prescriptive because the next pass depends on finding the
information in a predictable structure. If Pass 1 freestyles the output
format, Pass 2 has to do extra work to parse it, and the whole handoff
discipline erodes.

The runner script `repos/run_playbook.sh` received the bulk of the
implementation work — roughly 297 lines of changes — rewritten around the
four-pass structure, with the legacy single-pass path preserved behind
`--single-pass` for interactive human use.

In total the commit touched three files: README.md (+1/-1), SKILL.md (+49/-6),
and `repos/run_playbook.sh` (+278/-19), for 328 insertions and 26 deletions.

## v1.3.30 Refinement — Multi-Pass as Internal

Version 1.3.30 followed v1.3.29 within about an hour — 76 minutes, to be
precise. It did not change the architecture. It clarified a subtlety that the
first version of the multi-pass section left ambiguous.

The clarification is this: **multi-pass execution is internal to the skill,
not external orchestration.**

The ambiguity was real. When you describe a system as "four sequential passes,
each with its own prompt and its own context," a reader can easily conclude
that the way to execute it is to run four separate `claude -p` invocations, or
to wrap the skill in an external shell script that calls the model four times,
or to build some orchestration layer that coordinates the passes from outside.

That interpretation is wrong, and v1.3.30 made that explicit.

### The Corrected Text

The corrected text states it directly:

> The playbook handles multi-pass execution internally — you run all phases
> yourself in a single session, using files on disk as the context bridge
> between phases. Do not use external shell scripts, separate `claude -p`
> invocations, or any other external orchestration to split the work across
> multiple sessions. The skill is self-contained: one session, one invocation,
> all phases.

This is a small edit in terms of bytes — the v1.3.30 diff is 22 lines changed
in SKILL.md — but a large edit in terms of intent.

### Why the Distinction Matters

"Multi-pass" in this design is a discipline for managing working memory within
a single agentic session. It is not a pipeline of independent model calls.

The model, in one session, moves through the phases. At each phase boundary
it performs a deliberate "write then read" cycle: finish the current phase,
write everything the next phase will need to disk, then explicitly read those
files back before starting the next phase.

The act of writing and then re-reading is what lets the model drop the previous
phase's working context and load the next phase's context fresh, without the
cognitive overhead of holding both simultaneously.

That cycle is the actual mechanism. It is doing the work that external
orchestration would otherwise do, but from inside the session. The model is
its own context-management layer.

### Why Not External Orchestration

External orchestration would mean the skill is not self-contained. Users would
need a wrapper script, an orchestrator, or some piece of infrastructure outside
the skill file itself to make it work.

That would undermine the whole value of a skill. A skill is a single
self-describing artifact the model can follow. If completing a run required
the user to set up a multi-process orchestration pipeline, the skill would stop
being a skill and start being a system.

There is also a more practical concern. Separate `claude -p` invocations lose
more than they gain. Each invocation pays the cost of re-reading the skill,
re-interpreting its instructions, and re-establishing its context. The savings
on working memory have to be weighed against the overhead of repeated startup.
In practice, the write-then-read cycle inside a single session is cheaper and
more reliable than spawning new sessions.

v1.3.30 formalized the constraint: the skill runs in one session, one
invocation. The passes are a pattern inside that session, not a decomposition
across sessions.

### Expanded Handoff File List

The refinement also expanded the list of handoff files to make the pattern
concrete:

- `quality/EXPLORATION.md` — Phase 1 writes this, Phase 2 reads it.
- `quality/PROGRESS.md` — Updated after every phase. Cumulative BUG tracker
  ensures no finding is lost.
- Generated artifacts (REQUIREMENTS.md, CONTRACTS.md, etc.) — Phase 2 writes
  these, Phases 2b–2d read them to run reviews, audits, and reconciliation.

Naming these files out loud gave the model explicit anchors for the
write-then-read cycle. Ambiguity about "what exactly gets written between
phases" could otherwise degrade the discipline over time.

Taken together, v1.3.29 and v1.3.30 define the architecture: **split the work
into passes, use files as the context bridges, and keep the whole thing inside
a single session.**

## How It Fits Today

The multi-pass architecture is not a historical artifact. It is how the skill
still works.

In v1.4.5, the current six-phase architecture is a direct extension of the
four-pass design. Each phase is essentially a pass: it has a scoped prompt, a
defined input (usually files on disk), defined outputs (also files on disk),
and a deliberate boundary where the model writes findings, drops context, and
loads what it needs for the next phase.

### What Has Stayed the Same

The specific handoff files introduced in v1.3.29 are still there.

EXPLORATION.md is still written by Phase 1 and read by Phase 2. Its structure
has grown, but the purpose is unchanged.

PROGRESS.md is still the cumulative tracker. Its BUG list is still the
guarantee that no finding is orphaned across phase boundaries.

The generated artifacts (REQUIREMENTS.md, CONTRACTS.md, BUGS.md, the test
files, the spec audit) still serve as the handoff medium from generation into
review.

The review phases — code review, spec audit, TDD verification, reconciliation
— still each operate as their own pass, reading the artifacts under review
rather than carrying generation context.

The gate is still the final enforcement pass.

### What Has Grown

More phases, more artifacts, more specific handoff patterns. The six-phase
structure exists because each of the original passes has been refined and
sometimes split.

But the underlying discipline is unchanged. The model never holds everything
in working memory. It always offloads to disk at phase boundaries. Every
phase reads what it needs and nothing more.

This is why the skill can grow — more phases, more artifacts, more analyses —
without running out of headroom on context-limited models. The architecture
was designed so that adding a phase does not cost linear working memory; it
costs one more file on disk and one more write-then-read boundary.

### The Cultural Effect

There is also a cultural effect of the multi-pass design that is worth noting.

Because the architecture forces every phase to produce a concrete handoff
artifact, the skill's output has become more legible.

A user who wants to inspect what the skill did can read EXPLORATION.md to see
what the skill learned about their codebase. They can read PROGRESS.md to see
what happened when. They can read the generated artifacts to see the results.

The architecture is evident in the outputs. You can see the passes in the
files on disk. Multi-pass made the skill not just more reliable, but more
transparent.

This legibility has downstream value. When something goes wrong — a finding
that looks off, an artifact that feels incomplete, a bug that was classified
strangely — the user (or the model on a re-run) can read the intermediate
files and reconstruct what the skill was "thinking" at each stage. That is
much harder with a monolithic single-pass run, where the intermediate state
never leaves working memory.

### The Durable Insight

The foundational insight of v1.3.29 — that working memory is the real
constraint, and that files on disk are the right place to put everything you
don't currently need to reason about — has held up.

Every subsequent version has leaned harder on that insight rather than away
from it.

Later additions to the skill (the Council of Three spec audit, the regression
test generation inside code review, the integration testing protocol, the
heading-conformance gate) have all been slotted in as additional passes or as
refinements within existing passes. None of them required revisiting the core
architecture, because the core architecture was designed to accommodate
growth.

That is the test of a foundational design choice: it does not need to be
redone as the system evolves. v1.3.29 passed that test.

## Provenance

### Primary Commit

**Commit:** `f6d9e677151ef5c615383cc7405093fff61b4317`

**Title:** *v1.3.29: multi-pass architecture for context-limited models*

**Date:** 2026-04-12 00:05:49 -0400

**Author:** Andrew Stellman

**Co-Authored-By:** Claude Opus 4.6

**Files changed:**

- README.md (+1 / -1) — version bump
- SKILL.md (+49 / -6) — multi-pass execution section, EXPLORATION.md template,
  "Write exploration findings to disk" checkpoint
- `repos/run_playbook.sh` (+278 / -19) — four-pass rewrite with
  `--single-pass` legacy flag

**Totals:** 328 insertions, 26 deletions across 3 files.

**Motivating evidence cited in the commit message:** v1.3.28 test run on
`copilot/gpt-5.4` across eight repositories, with 3/8 (chi, cobra, javalin)
failing to complete due to the 168 KB SKILL.md exceeding effective working
memory. The 5 repos that completed showed excellent conformance (100% on
heading format, JSON, and inline diffs), isolating the failure mode to
completion rather than quality.

### Follow-on Refinement

**Commit:** `9e43190eba25b37963adb845cdc9cde596430f3e`

**Title:** *v1.3.30: multi-pass execution is internal to the skill, not
external scripts*

**Date:** 2026-04-12 01:22:04 -0400 (approximately 76 minutes after v1.3.29)

**Author:** Andrew Stellman

**Co-Authored-By:** Claude Opus 4.6

**Files changed:**

- SKILL.md (+15 / -7)

A single-file clarification establishing that the multi-pass architecture runs
within one session, using files as context bridges, with no external
orchestration layer. The refinement also expanded the explicit list of handoff
files and introduced the "write then read" cycle description that is still in
the skill today.

### Relationship Between the Two

v1.3.29 is the architectural change. v1.3.30 is the interpretive guardrail.

Together these two commits define the multi-pass architecture as it exists in
the skill today: a discipline for managing working memory across phases through
deliberate file-based handoff inside a single self-contained session.

The fact that v1.3.30 arrived 76 minutes after v1.3.29 — rather than days or
weeks later — is itself a useful signal. The author recognized the ambiguity
almost immediately and corrected it before anyone could build the wrong
external tooling on top of the wrong interpretation. That speed is part of why
the architecture landed cleanly and why later versions did not have to unwind
a misunderstanding.

The architecture has been stable since. That stability is the evidence that
v1.3.29, clarified by v1.3.30, got the design right.
