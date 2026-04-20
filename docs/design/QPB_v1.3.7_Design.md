# QPB v1.3.7 Design Retrospective

**Version:** 1.3.7
**Status:** Shipped
**Date:** 2026-04-06
**Author:** Andrew Stellman
**Primary commit:** `be954a4` — "v1.3.7: Enforceable terminal gate, metadata consistency checks, test framework alignment"

---

## What This Version Introduced

Quality Playbook v1.3.7 was a small-looking commit with an outsized effect on
the skill's later trajectory. The diff touched only two files —
`README.md` and `playbook/SKILL.md` — and added a net 19 lines of SKILL.md
content. But those lines changed the character of the skill more than any
single release before it.

Three things landed together.

First, the terminal gate became enforceable. Before v1.3.7, the gate at the
end of Phase 2d was a script the agent was supposed to say aloud: a mandatory
print statement that announced the BUG tracker counts and whether code review
and spec audit findings reconciled. It was mandatory in tone but not in
artifact. In v1.3.7, the gate's output also had to be written into a named
section of PROGRESS.md — `## Terminal Gate Verification` — placed
immediately after the BUG tracker table. The PROGRESS.md template was updated
to reserve that section as a placeholder so a reviewer, human or another
agent, could confirm without reading session logs that the gate had actually
run.

Second, the skill grew its first metadata consistency checks. A new subsection
of the Phase 3 verification instructs the agent to re-read PROGRESS.md and
COMPLETENESS_REPORT.md and compare their claims against the actual filesystem.
The requirement count in COMPLETENESS_REPORT.md must match the number of
`REQ-NNN` entries in REQUIREMENTS.md. The `With docs` field in PROGRESS.md
must match whether `docs_gathered/` contains files. The Terminal Gate
Verification section must be present and filled in. No stale
pre-reconciliation text may remain in COMPLETENESS_REPORT.md after the
post-review reconciliation step has run. A matching self-check was added
inside the terminal gate itself, making `With docs` the first piece of
artifact metadata the skill ever verified against ground truth.

Third, regression tests were aligned with the functional test framework. The
skill now specifies that regression tests written in `quality/test_regression.*`
must use the same framework as `test_functional.*`. If functional tests use
pytest, regression tests use pytest with `@pytest.mark.xfail(strict=True)`. If
functional tests use unittest, regression tests use unittest with
`@unittest.expectedFailure`. This closed a cross-language hole that had been
producing mixed-framework test suites on polyglot projects.

The commit also corrected a stale Phase 5 reference in the terminal gate
language to Phase 2d. That change looks clerical, but it mattered in practice.
Agents were reasoning their way around the gate by deciding the gate applied
to a phase they weren't in. An incorrect phase label is a legible excuse. The
correct label removed the excuse.

Taken together, the four changes are modest in line count and large in
consequence. They are the first commit in which the skill's design
philosophy becomes visibly mechanical rather than advisory, and they set the
pattern that nearly every subsequent v1.3.2x release extends.

## Why It Was Needed

The pre-v1.3.7 terminal gate had been introduced in v1.3.5 as a response to a
specific, repeatable failure mode. After the spec audit, agents would confirm
new bugs, report them in the narrative output, and then forget to add those
bugs to the PROGRESS.md BUG tracker. A significant fraction of confirmed bugs
— the v1.3.5 bootstrap data cited thirty to fifty percent — were being
orphaned. The tracker, which was supposed to be the ground truth artifact,
had become a subset of the findings rather than a superset.

The v1.3.5 fix was to require the agent to print a reconciliation statement at
the end of Phase 2d:

> "BUG tracker has N entries. N have regression tests, N have exemptions, N
> are unresolved. Code review confirmed M bugs. Spec audit confirmed K code
> bugs (L net-new). Expected total: M + L."

If the counts didn't reconcile, the agent had to stop and fix the tracker
before marking the phase complete.

That gate helped, but it didn't solve the problem. It had a structural
weakness. The print statement vanished into the session log. A reviewer
opening the `quality/` directory a week later had no way to confirm the gate
had run. Worse, during long runs, agents were sometimes compressing or
paraphrasing the statement, or skipping it entirely when context pressure was
high. The gate was mandatory only in prose. Nothing mechanical depended on it.
If the agent decided not to print the statement, no later step would notice
the absence.

The batch 1 runs that produced the input to this commit made the cost visible.
Seven repos — qpb, zram, virtio, httpx, javalin, serde, zod — had been run
on v1.3.6. The bootstrap run, QPB reviewing its own repo, found six bugs,
including a pattern where tracker discipline slipped precisely at the
reconciliation step the gate was supposed to protect. An advisory gate
enforces itself only against agents who were going to follow it anyway.
Agents who were already cutting corners found the advisory gate easy to cut
too.

The metadata consistency problem had a similar shape. Agents were writing
`With docs: yes` into PROGRESS.md early in the run, then proceeding without
`docs_gathered/` actually containing anything. COMPLETENESS_REPORT.md would
quote a requirement count that had been accurate at one point but had drifted
after later phases added REQs. The pre-reconciliation section of
COMPLETENESS_REPORT.md, which the post-review step was supposed to replace,
was instead being left in place — producing a document that contradicted
itself.

None of these were hallucinations in the strict sense. They were stale claims,
carried forward by the agent's tendency to edit additively rather than to
overwrite. The v1.3.6 runs showed this happening often enough to be treated as
a systemic issue rather than per-run carelessness. The pattern was consistent
across agents, across models, and across repos. Something about the
instruction surface was producing the drift, and no amount of reminding was
going to fix it.

The regression test framework problem was simpler. On polyglot projects, or on
Python projects where the agent had picked pytest for functional tests without
committing to pytest for regression tests, the two test files would drift. A
regression test written in unittest style against a pytest-based suite
wouldn't integrate into the same test runner. The output looked correct at the
file level and failed at the pipeline level. The fix — bind regression test
framework choice to functional test framework choice — was small but
load-bearing.

All three issues shared a quality worth naming. They were not cases where the
agent couldn't do the right thing. They were cases where the agent could do
the right thing but couldn't be relied on to do it. The remedy in each case
was the same in outline: make the right thing mechanical, and make failures to
do it visible after the fact.

## The Enforceable Terminal Gate

The change to the gate's enforcement model is worth examining carefully
because it set a precedent that the skill would return to many times in later
versions.

### From speech act to persistence act

Before v1.3.7, the gate was a speech act. The agent was instructed to "state
aloud (print to the user)" a specific sentence with specific counts. If the
counts didn't match, the agent was instructed to stop. The design assumed that
the act of computing and stating the counts would surface any discrepancy,
and the agent's own reasoning would catch the mismatch. This is a plausible
design if you treat the agent as a disciplined collaborator who will not skip
a mandatory step. It is a weak design if you treat the agent as a process
running under context pressure, token budget pressure, and user-facing
pressure to appear done.

After v1.3.7, the gate is a persistence act. The agent still prints the
statement, but it also writes that statement into a named PROGRESS.md section.
The named section exists as a placeholder in the template from the start of
the run, so its absence or emptiness at the end of the run is detectable by
anyone — including a later Phase 3 verification step, which v1.3.7 also
introduced as a consistency check on whether the Terminal Gate Verification
section is present and filled in.

### The exact diff

The relevant change in the SKILL.md diff is concentrated in one block. The
pre-v1.3.7 instruction read:

> Re-read `quality/PROGRESS.md`. Count the BUG tracker entries. Then state
> aloud (print to the user):
>
> > "BUG tracker has N entries. ... Expected total: M + L."

The post-v1.3.7 instruction reads:

> Re-read `quality/PROGRESS.md`. Count the BUG tracker entries. Then:
>
> 1. Print the following statement to the user (this is mandatory, not
>    optional):
>
>    > "BUG tracker has N entries. ... Expected total: M + L."
>
> 2. Write the same statement into PROGRESS.md under a new
>    `## Terminal Gate Verification` section (immediately after the BUG
>    tracker table). This persists the gate into the artifact so reviewers
>    can verify it without reading session logs.
>
> 3. Verify the `With docs` metadata field in PROGRESS.md matches reality:
>    if `docs_gathered/` exists and contains files, it should say `yes`;
>    otherwise `no`. Fix it if wrong.

The structural change is visible in the shift from a single unordered
imperative to a numbered three-step list with a persistence step in the
middle. The print step survives, but it is now step one of three rather than
the whole gate. The central new step is the write-to-artifact step. The third
step is the `With docs` self-check, a direct response to a specific failure
mode observed in the v1.3.6 runs.

### Three emergent properties

Three properties emerge from this shift.

The first is durability. The gate's output now lives in an artifact, not a
transcript. Reviewers operating on the `quality/` directory after the fact
can confirm the gate ran. The information is not lost to log rotation, to
session compression, or to a user scrolling past it. If a run is revisited
weeks later, the gate's output is still present at a known location. This
turns out to matter for the review protocols that later releases of the skill
built on top of it.

The second is verifiability. Because the PROGRESS.md template now contains
the `## Terminal Gate Verification` section as a reserved placeholder, any
run that completes without populating it produces a visibly incomplete
document. An automated check — and the metadata consistency check added in
the same commit is the first such check — can read the file and test whether
the section is empty. The gate is no longer enforced only by the agent's
self-discipline. It's enforced by a downstream step that fails if the gate
didn't produce its artifact.

The third is compositionality. Once the gate writes a structured section,
other steps can read from it. A later verification step can pull the reported
counts out of PROGRESS.md and compare them to the BUG tracker table that
lives a few lines above. A reviewer consolidating across multiple runs can
extract gate verification data without re-running the skill. The gate has
become a data source, not just a checkpoint.

### The commit's own framing

The commit's phrasing captures the design intent precisely: "This persists
the gate into the artifact so reviewers can verify it without reading session
logs." That sentence is the hinge between advisory and mechanical gates. It
is the earliest place in the SKILL.md where the skill's own documentation
explains why an instruction is structured the way it is, rather than simply
issuing the instruction. The rationale is load-bearing — it tells later
authors (the skill's own agents) that the persistence is not decorative, and
that edits which preserve the print-aloud step while dropping the
write-to-artifact step are not valid simplifications.

### The Phase 2d label correction

The correction of the stale "Phase 5" reference to "Phase 2d" in the gate
header is worth one additional note. Before the correction, the gate read
"Terminal gate (mandatory before marking Phase 5 complete)." The skill had
restructured its phases in an earlier release, and Phase 5 no longer existed.
An agent reading the gate header could reason: this gate is about Phase 5, I
am currently in Phase 2d, therefore this gate doesn't apply to me. The
reasoning is wrong — the gate was unambiguously about the phase the agent
was in — but the header invited it. Correcting the header to "Phase 2d"
closed the invitation. This is an instance of a broader design principle: an
agent-facing instruction must not contain a label that can be used as a
conscientious excuse for non-compliance.

## Metadata Consistency Checks

The new Phase 3 Metadata Consistency Check subsection takes a different
approach from the terminal gate. Where the gate forces the agent to write an
artifact, the consistency check forces the agent to re-read the artifacts it
has already written and compare them against one another and against the
filesystem.

### What the check catches

The check lists four specific comparisons.

The requirement count in COMPLETENESS_REPORT.md must match the actual
`REQ-NNN` count in REQUIREMENTS.md, including any requirements added during
the run. Requirement counts drift because the agent commits to a count early
— often quoting it in COMPLETENESS_REPORT.md's opening summary — and then
adds requirements later without updating the summary. The summary is valid at
the moment it is written and stale by the end of the run.

The `With docs` field in PROGRESS.md must match the actual state of
`docs_gathered/`. The `With docs` field drifts because the agent decides at
run start whether docs will be present, writes the field, and then doesn't
revisit it when the planned docs don't materialize. The metadata field
describes an intention rather than a state.

The Terminal Gate Verification section must exist and be filled in. The
section is empty precisely in the runs where the gate didn't run. The check
catches the absence that the terminal gate's persistence step is supposed to
prevent, and provides a second line of defense when the first line has been
skipped.

No stale pre-reconciliation text may remain in COMPLETENESS_REPORT.md after
reconciliation. Stale pre-reconciliation text appears because the agent's
default mode of editing is append rather than overwrite, and a reconciliation
step that adds new verdicts without removing old ones produces a
self-contradicting document. The instruction to "replace" is interpreted as
"add, leaving the old content in place." The check catches the outcome
rather than trying to further instruct the behavior.

### The check is cleanup, not gating

The Metadata Consistency Check is not a gate in the terminal-gate sense. It
doesn't block completion if it fails. Its instruction is "If any metadata is
stale, fix it now." It's a cleanup step with a specific checklist.

But it's a cleanup step that runs against artifacts rather than against
memory, and its checklist is concrete enough that an agent executing it can
either comply or visibly fail to comply. A run that finishes with stale
requirement counts is now producing artifacts that fail their own
self-check, which makes the failure diagnosable after the fact.

This is a deliberate design choice. A gate that blocked on metadata drift
would introduce a failure mode where the run halted because of a cosmetic
inconsistency, and agents would learn to work around the gate by being less
specific in their metadata. A cleanup step that fixes the drift without
halting preserves the agent's ability to complete the run while still
catching the common cases of drift before the artifacts are delivered.

### The belt-and-suspenders With docs check

The inclusion of a second `With docs` check inside the terminal gate itself
— step three of the revised Phase 2d gate — is a belt-and-suspenders
decision. The field is checked twice because it's the field most likely to be
wrong, and catching it at the terminal gate means the Phase 3 consistency
check has one fewer thing to catch.

The duplication is not accidental. It reflects a prioritization: the `With
docs` field is visible in the PROGRESS.md summary and is the one metadata
field most likely to be consulted by a reviewer or by a later run. An
incorrect value for this field has outsized consequences because decisions
get made based on it. The other fields in the consistency check — requirement
counts, stale reconciliation text, terminal gate section presence — are less
consequential in downstream use but more commonly wrong, so they are caught
at the single later checkpoint.

## Test Framework Alignment

The test framework alignment change is the smallest of the three and the most
mechanical.

### The bind

The pre-v1.3.7 instruction for regression tests was:

> Write regression tests in `quality/test_regression.*` that reproduce each
> confirmed bug.

The v1.3.7 instruction adds:

> Use the same test framework as `test_functional.*` — if functional tests
> use pytest, regression tests use pytest (with
> `@pytest.mark.xfail(strict=True)`); if functional tests use unittest,
> regression tests use unittest (with `@unittest.expectedFailure`).

This is a bind. The regression test framework is determined by the functional
test framework. The agent no longer has to make a choice at
regression-test-generation time, and cannot produce a mixed suite by
accident.

### Why the bind matters

The reason it matters is subtle. When regression tests diverge in framework
from functional tests, each file looks correct in isolation. A
`test_regression.py` with pytest fixtures looks like valid pytest. A
`test_functional.py` with `unittest.TestCase` classes looks like valid
unittest. But when the CI step runs "the test suite," it uses one runner, and
the other file either fails to collect or is silently skipped.

The failure mode is invisible at the level of individual file review. It's
only visible at the level of the test pipeline. Because the skill's output was
being reviewed file-by-file more often than it was being run end-to-end, the
divergence was slipping through. The review protocol itself — read each
generated file, check it for correctness — could not catch the bug. The bug
lived in the relationship between files, not in any single file.

### The xfail / expectedFailure detail

The xfail/expectedFailure detail is also important. Regression tests
reproduce bugs. They're expected to fail until the bug is fixed, at which
point they flip to passing. Without the xfail marker, a regression test that
fails turns the whole suite red, which makes the suite useless as a pass/fail
signal.

With the marker, a failing regression test is an expected result, and a
regression test that unexpectedly passes is a signal that the bug has been
fixed. The `strict=True` variant of `xfail` adds the further property that an
unexpected pass becomes a test failure — so the CI reports precisely when a
regression test has flipped, rather than treating the flip as a silent good
outcome.

Binding the regression framework to the functional framework also binds the
correct marker syntax, which the agent was previously having to infer.
Inference over two framework families was producing roughly the error rate
you would expect: a meaningful fraction of runs had the wrong marker, and
those runs had regression tests that did not report their status correctly to
CI.

## Philosophical Shift

The three changes in v1.3.7 share a direction. They move the skill toward
mechanical verification and away from advisory guidance. This shift is small
in this commit, but it's the first time the shift is explicit rather than
incidental, and it's the direction the skill has been moving in ever since.

### Advisory vs mechanical

An advisory gate says: the agent should do X. It relies on the agent's
willingness and ability to comply. It works well for tasks the agent
naturally wants to do, and it works poorly for tasks the agent naturally
skips — which in practice means the tasks where the advisory gate matters
most. The v1.3.5 terminal gate was advisory. It helped when agents intended
to reconcile. It didn't help when agents intended to appear finished.

A mechanical gate says: the agent's output must contain Y, and Y is
checkable. The agent can still refuse to produce Y, but the refusal is now
visible. A downstream step — human or automated — can test for Y's presence
and fail the run if Y is missing. The v1.3.7 terminal gate is mechanical.
Writing into a named PROGRESS.md section is a concrete artifact check. The
Metadata Consistency Check compares two concrete artifacts and the
filesystem. The test framework alignment removes a choice point in favor of a
deterministic derivation.

### Why the shift became necessary

This change in philosophy matters because the skill was running into the
limits of what agents could be instructed to do reliably. Prose instructions
that say "make sure X" work at about the rate you'd expect from prose
instructions: often enough to be noticeable, not often enough to be
trustworthy. By the time v1.3.7 shipped, the pattern was clear across the
bootstrap runs. Every reliable piece of skill behavior was backed by an
artifact the skill would write and something downstream would read. Every
unreliable piece was backed by an instruction that asked the agent to
remember.

The shift is not a rejection of prose instructions. Prose instructions remain
the medium in which the skill is expressed. The shift is a recognition that
prose instructions cannot be the only layer of enforcement. A prose
instruction that writes an artifact is stronger than a prose instruction
alone, because the artifact provides a second witness to whether the
instruction was followed.

### The v1.3.2x extension

The versions that followed v1.3.7 extended this pattern. The v1.3.2x series
— subsequent point releases not covered in this retrospective — introduced
more mechanical gates around specific artifacts: BUG tracker closure status
vocabulary, pre-audit docs validation, reconciliation replacement rather than
append. Each of those is a recognizable cousin of the v1.3.7 terminal gate
and metadata consistency check. They share the same structural commitment: a
named artifact section, a placeholder in the template, a downstream check
that reads the section and verifies its contents.

v1.3.7 is not where mechanical verification was invented in the skill —
earlier versions had mechanical elements. But it's the first commit where the
philosophy is legible as a philosophy. The commit message itself names all
three changes in a single line and frames them as of a piece: "Enforceable
terminal gate, metadata consistency checks, test framework alignment." The
word "enforceable" is doing work. It marks the shift from a gate that was
mandatory in tone to a gate that is mandatory in substance.

### The general principle

The pattern that emerges from v1.3.7 can be stated as a principle. For any
instruction that matters, the skill should arrange for the instruction's
outcome to be written to a known location where a later step can check it.
Instructions that don't produce artifacts are fragile. Instructions that
produce artifacts at known locations can be verified, composed, and extended.

The principle has cost. Every artifact requires a template slot, a writing
step, and a checking step. It bloats the skill's surface area. It makes the
skill more work to modify, because any change to an artifact's structure
propagates to its readers.

But the alternative — the advisory model — has a worse cost. The advisory
model works at whatever compliance rate the agent's discipline produces,
which varies from run to run and from model to model. The mechanical model
works at whatever compliance rate the skill's own check produces, which is
uniform. Uniform compliance is what a quality skill needs to offer. Variable
compliance is what it is trying to replace.

## How It Fits Today

In v1.4.5, the current stable line at the time of this writing, the terminal
gate introduced in v1.3.7 is foundational.

### What persists unchanged

The `## Terminal Gate Verification` section in PROGRESS.md remains a required
artifact. The Phase 3 Metadata Consistency Check remains in place, extended
but not replaced by additional checks. The regression test framework
alignment rule persists without modification — it turned out to be stable
and has not needed iteration.

The regression test framework alignment is notable for having aged the best.
It was a small fix for a narrow problem, and it has not needed revision. The
subsequent expansion of the skill to cover more languages — Java, Scala,
TypeScript, Go, Rust — has reused the same pattern: the regression framework
follows the functional framework, whatever the functional framework is in the
target language. The rule generalized without modification. This is an
unusual outcome for a skill rule. Most rules get revised.

### What has been extended

What's changed since v1.3.7 is the surrounding infrastructure. There are now
more mechanical gates, more named artifact sections, and more cross-artifact
consistency checks. The Terminal Gate Verification section has become one of
several required sections rather than the only required one. The Metadata
Consistency Check has been extended to cover additional fields that v1.3.7 did
not anticipate. The overall structure — placeholder sections reserved in
templates, downstream steps reading from named sections, artifact self-checks
at phase boundaries — is now the skill's default mode of operation, and
v1.3.7 is where that mode first became explicit.

The terminal gate and the metadata consistency check have both been extended
but not replaced. v1.3.7 was a foundational commit in the sense that
structural reforms are foundational. The original structure is visible under
later layers, and the later layers would not fit without it. A reviewer
reading v1.4.5's Phase 2d gate will recognize the v1.3.7 shape immediately:
the print-and-persist pattern, the named PROGRESS.md section, the downstream
verifiability. The details have grown. The structure has not changed.

### Why it keeps working

The v1.3.7 pattern keeps working for a specific reason. It treats the agent
as an untrusted writer rather than a trusted author. An untrusted writer
produces artifacts; a trusted author is expected to remember. The skill's
infrastructure can verify artifacts. It cannot verify memory. Designing
against the weaker assumption has produced a skill that continues to work as
models change, as context windows change, and as the particular failure
modes of particular agents shift. The structural commitment survives changes
that would invalidate a discipline-based design.

This is the quiet legacy of v1.3.7. It is not the specific artifacts it added
— several of those have been superseded or subsumed. It is the stance it
took toward enforcement. Every subsequent release of the skill has made
enforcement more concrete, more artifact-backed, more mechanically checkable.
v1.3.7 is where that direction became deliberate.

## Provenance

### Git

- **Commit:** `be954a4` — "v1.3.7: Enforceable terminal gate, metadata
  consistency checks, test framework alignment"
- **Author:** Andrew Stellman, co-authored with Claude Opus 4.6
- **Date:** 2026-04-06 15:25:11 -0400
- **Files changed:** two. `README.md` (+1 / -1) and `playbook/SKILL.md`
  (+26 / -7).
- **Net change:** 27 additions, 8 deletions, 19 net new lines in SKILL.md.

### Chat

The earliest review session of v1.3.7 output is
`Cowork-2026-04-06-Review Quality Playbook v1.3.7 results.md`, opened the
same day the commit landed (2026-04-06 21:19 UTC, roughly six hours after
the commit). The handoff message in that session records the batch 1 results
across seven repos — qpb-1.3.7, zram-1.3.7, virtio-1.3.7, httpx-1.3.7,
javalin-1.3.7, serde-1.3.7, zod-1.3.7 — and flags the terminal gate
enforcement and metadata consistency as the specific process rules to
evaluate in the review. That session is the empirical ground against which
v1.3.7's design was tested and from which the v1.3.8 changes were
subsequently synthesized.

### Authority

This document treats the git commit message and diff as authoritative. Chat
history was consulted only for context on the rollout and review, not for
design claims. Where chat history and git diverged, git was followed.
