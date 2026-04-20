# Quality Playbook v1.3.5 — Retrospective Design Document

**Version:** 1.3.5
**Status:** Shipped
**Release date:** April 6, 2026
**Author:** Andrew Stellman
**Primary commit:** `6011d45` — *v1.3.5: Add PROGRESS.md as external memory, close spec-audit orphan gap*

---

## What This Version Introduced

Version 1.3.5 introduced `PROGRESS.md`, a structured checkpoint file that the
agent writes and re-reads throughout a Quality Playbook run. PROGRESS.md is the
skill's first true piece of external memory: a single file that persists the
agent's running state — phase completion, artifact inventory, and a cumulative
BUG tracker — to disk after every phase, so nothing is lost when context
pressure, session interruptions, or multi-session runs break the agent's
in-memory view of the world. It also serves as a permanent audit trail once the
run is complete.

The release did one other load-bearing thing. It closed the *spec-audit orphan
gap* — a structural defect in the v1.3.4 pipeline that was discovered while
analyzing runs across eight real-world repositories. In short: confirmed code
bugs found by the spec audit were systematically ending up without regression
tests, because the regression-test loop ran immediately after the code review
and never looped back once the spec audit had produced its findings. Roughly
thirty percent of all confirmed bugs were falling into this gap, and only one
of the eight repositories (httpx) had produced spec-audit regression tests at
all, and that appeared to be incidental rather than prescribed behavior.

Three smaller improvements rounded out the release, each drawn from the v1.3.4
review synthesis (a joint pass by Cursor/GPT-5.4 and Copilot/Sonnet 4.6). The
first was a formal conflict-resolution procedure for cases where the code
review and spec audit disagree about the same finding — one calls it a BUG,
the other calls it a design choice or a false positive — and the reconciliation
step used to silently pick one side. The second was explicit detection of
partial sessions: runs that produce scaffolding (directory structure, empty
templates) without producing the actual review or audit content. These
previously could be mistaken for clean runs with no findings. The third was
provenance headers on any artifact carried over from a previous run, added to
prevent the silent-staleness failure mode observed in the v1.3.4 express and
zod runs, where archival artifacts were being presented as fresh.

The diff is small by line count — 165 insertions across five files — but the
conceptual shift is large. Before v1.3.5, the skill assumed the agent's
working memory would carry state across phases. After v1.3.5, the skill
assumed it would not.

## Why It Was Needed

Quality Playbook runs are long. A full pass through Phase 1 (exploration),
Phase 2 (artifact generation), the code review, the spec audit, the
reconciliation, and the verification benchmarks is not a single short
prompt-response. It is a multi-phase workflow in which earlier phases produce
the inputs that later phases consume.

In a single-session run with plenty of context budget, the agent can hold
enough of that history in working context to connect Phase 4 findings back to
Phase 1 exploration notes. In a long single-session run where context pressure
has been building for tens of thousands of tokens, it can't. In a multi-session
run, it certainly can't — the second session starts with no memory of the
first at all.

The v1.3.4 synthesis surfaced a specific pattern: findings from Phase 1 were
being forgotten by Phase 3. BUG counts quoted in the final completeness report
didn't match the actual number of confirmed bugs in the review artifacts.
Spec-audit bugs were disappearing entirely from the closure-verification
step — not because the spec audit failed to produce them, but because by the
time the agent reached closure verification, it was working from a truncated
picture of what had happened so far. The closure check only saw code-review
bugs, because those were the ones in the agent's immediate recent context.

This is a structural problem, not a prompting problem. No amount of careful
phrasing in the SKILL.md instructions can stop a long-context model from
gradually losing earlier context. The fix has to be external: write state to a
file, and make reading that file a required checkpoint at every phase
boundary. That is what PROGRESS.md is.

There was also a second motivation, visible only in retrospect once the first
was solved. A checkpoint file written at every phase is *also* an audit trail.
It records what the skill did, what it found, and how it resolved each
finding. Users reading a completed PROGRESS.md can reconstruct the run without
re-running it. Developers debugging a failed run can see exactly which phase
produced which artifact and where closure broke down. Across-run comparisons
become trivial: the same file format, from run to run, on the same codebase,
makes regressions and improvements easy to spot. The same file that prevents
state loss during a run becomes a forensic record after it.

The commit message for 6011d45 frames this symmetrically. It describes
PROGRESS.md as a file that "persists state to disk so nothing is lost across
long sessions or multi-session runs" and adds, with equal emphasis, "doubles
as an audit trail for debugging." Both properties were explicit design goals,
not accidents of the implementation.

## PROGRESS.md Design

PROGRESS.md lives at `quality/PROGRESS.md` — alongside the other quality
artifacts, not in a separate metadata location. This placement is deliberate.
PROGRESS.md is itself a first-class deliverable of the quality system, not a
log file or a scratch pad. The SKILL.md update adds it to the list of
supporting artifacts generated by the pipeline, right at the front of that
list.

It is generated during Phase 1 as the first act of externalizing state. Once
the agent has finished exploring the codebase and before it begins generating
artifacts, it writes the initial PROGRESS.md. From that point on, every phase
ends by re-reading and updating the file, and the next phase begins by
re-reading it again.

### The file structure

The file has five sections, in a deliberate order.

The first section is **run metadata** — when the run started, what project it
targets, which skill version is running, and whether documentation was
provided. This is the header that lets anyone reading PROGRESS.md later know
what kind of run they're looking at. Four lines, fixed format, easy to parse.

The second section is the **phase completion checklist** — a plain Markdown
task list with six entries, one per phase:

1. Phase 1: Exploration
2. Phase 2: Artifact generation
3. Phase 3: Code review plus regression tests
4. Phase 4: Spec audit plus triage
5. Phase 5: Post-review reconciliation plus closure verification
6. Phase 6: Verification benchmarks

Each entry is unchecked initially and gets marked complete with a timestamp as
the run progresses. Because it is a Markdown task list, both humans and agents
can parse it at a glance — agents by reading the file, humans by rendering it.

The third section is the **artifact inventory** — a table with one row per
expected output artifact. The rows cover `QUALITY.md`, `REQUIREMENTS.md`,
`CONTRACTS.md`, `COVERAGE_MATRIX.md`, `COMPLETENESS_REPORT.md`, the functional
tests, the three run-protocol Markdown files (`RUN_CODE_REVIEW.md`,
`RUN_INTEGRATION_TESTS.md`, `RUN_SPEC_AUDIT.md`), and `AGENTS.md`. Each row
tracks status (pending, generated), path, and a free-form notes field. When an
artifact is generated, the row is updated. When an artifact is carried over
from a previous run, the notes column records that fact — which ties directly
into the provenance-header mechanism added in the same release.

The fourth and most important section is the **cumulative BUG tracker** — a
table that accumulates every confirmed BUG found by either the code review or
the spec audit. Each row carries a number, the source (Code Review or Spec
Audit), a file:line reference, a description, a severity, a closure status,
and a pointer to either the regression test that covers it or the exemption
that excuses it.

The design constraint here is strict: *every* confirmed BUG, regardless of
which phase produced it, goes into this single table. This is what makes
closure verification work. The reconciliation phase doesn't have to assemble
findings from three different artifacts and hope it catches them all; it reads
one table and checks that every row has closure. Single source of truth,
single closure check, single mechanism.

There is a fifth, less rigorous section — **exploration summary** — where the
agent records a paragraph or two on architecture, key modules, spec sources,
and any defensive patterns noticed during Phase 1. This is freeform prose, not
a structured table, but it serves a specific purpose: a compact re-priming
note for when the agent re-reads PROGRESS.md mid-run. Rather than scrolling
through the original exploration notes, the agent reads the summary and
refreshes its mental model in a few sentences.

### The update protocol

The update protocol is prescribed phase by phase in SKILL.md. Each phase ends
with a "Checkpoint: Update PROGRESS.md" instruction that spells out exactly
what to change.

After Phase 2 artifact generation, the agent marks Phase 2 complete and fills
in the artifact inventory. The SKILL.md instruction is explicit that the agent
should "set each generated artifact to 'generated' with its file path" — no
room for interpretation.

After the code review (Phase 2b in the v1.3.5 numbering), the agent adds every
confirmed code-review BUG to the cumulative tracker with its regression-test
reference. The source column reads "Code Review" for all entries from this
phase.

After the spec audit and triage (Phase 2c), the agent adds every
spec-audit-confirmed code bug to the same tracker, with source "Spec Audit".
This is the step that closes the orphan gap, and the SKILL.md text is blunt
about it: "This is critical — spec-audit bugs are systematically orphaned if
they aren't added to the same tracker that the closure verification reads."

A follow-up step then writes regression tests for those newly-added entries.
This is the new "post-spec-audit regression tests" step described in the next
section.

After post-review reconciliation (Phase 2d), the agent verifies that every row
in the tracker has closure — either a regression test reference or an explicit
exemption. If any row lacks both, the agent writes the test or exemption
before marking Phase 5 complete.

After the verification benchmarks (Phase 3 in the original SKILL.md numbering,
Phase 6 in PROGRESS.md's numbering), the agent writes a final summary line in
the prescribed format: "Run complete. N BUGs found (N from code review, N
from spec audit). N regression tests written. N exemptions granted."

### The read-before-write discipline

The explicit instruction to *re-read* PROGRESS.md before each phase, not just
write to it, is what makes the system work. Writing alone would still leave
the agent relying on in-memory state for decisions — the write would just be a
dead-letter record, a copy of what the agent already had.

Reading restores the accurate picture before any decision is made. The
SKILL.md text makes this explicit at each phase boundary: "Before starting the
code review, re-read PROGRESS.md to refresh your context on what was generated
and what the exploration found." And again before reconciliation: "Re-read
`quality/PROGRESS.md` — specifically the cumulative BUG tracker. This is the
authoritative list of all findings across both code review and spec audit."

The word "authoritative" in that second instruction is doing real work. It
tells the agent: whatever you think you remember about findings so far, the
file is the source of truth. If the file disagrees with your memory, trust
the file.

## The Spec-Audit Orphan Gap

The orphan gap was a process defect, not a bug in any individual protocol.
The code review protocol in v1.3.4 had a robust closure mandate: every
confirmed BUG must have either a regression test or an explicit exemption.
The spec audit protocol produced a triage report that categorized each
finding. Both protocols worked in isolation. But the sequence in which they
ran guaranteed that the spec-audit findings would miss the closure mandate.

The sequence went like this. The code review ran first. Immediately after,
the agent wrote regression tests for every confirmed code-review BUG — that
satisfied the closure mandate for code-review findings. Then the spec audit
ran, producing its own set of findings and a triage report. The reconciliation
phase followed, but the reconciliation was scoped to updating the completeness
report, not to writing new regression tests. And by that point, the code
review's regression-test loop had already ended.

The spec audit's confirmed code bugs appeared in the triage report and
nowhere else. They never entered the regression test file.

The empirical evidence was stark. Across eight v1.3.4 runs on real
repositories, spec-audit findings accounted for roughly thirty percent of all
confirmed bugs, and only the httpx run had produced spec-audit regression
tests at all. Seven out of eight repos silently dropped a third of their bug
findings. The skill was producing thorough triage reports and then
structurally ignoring them when it came time to write tests.

### The three-part fix

The v1.3.5 fix was threefold.

First, the closure mandate in `references/review_protocols.md` was extended
explicitly to cover spec-audit confirmed code bugs. Same conventions, same
regression-test format, same expected-failure markers, same citation format
but pointing at the spec-audit triage report instead of the code review. The
new reference text spells out the procedure: "After spec audit triage, read
the triage summary for findings classified as 'Real code bug.' For each,
write a regression test in `quality/test_regression.*` using the same format
as code review regression tests. Use the spec audit report as the source
citation: `[BUG from spec_audits/YYYY-MM-DD-triage.md]`."

Second, a new step was inserted between spec-audit triage and reconciliation:
"post-spec-audit regression tests." This step reads the triage report, finds
every "Real code bug" classification, writes a regression test for each, and
records the test reference back in PROGRESS.md. If the spec audit produced no
confirmed code bugs, the step is skipped — but PROGRESS.md records that
explicitly, so the audit trail shows the decision was made rather than
forgotten. The difference between "no bugs to test" and "forgot to check"
matters, and the explicit-no-op record is how the skill distinguishes them.

Third — and this is where PROGRESS.md does the structural work — both
code-review BUGs and spec-audit BUGs now flow through the same cumulative
tracker. The reconciliation phase's closure check reads that one tracker and
enforces the mandate uniformly. There is no longer a path by which a
confirmed bug can be found and then forgotten. The tracker is append-only
across phases, and the closure check is a row-by-row sweep. What is
discoverable at sweep time is what was written to the tracker, and the
SKILL.md contract says everything confirmed must be written.

### The conflict-resolution sub-fix

The conflict-resolution procedure is the related sub-fix. When the code
review and spec audit disagree about the same finding — one calls it a BUG,
the other calls it a design choice or a false positive — the reconciliation
used to silently pick one side or defer resolution entirely.

v1.3.5 formalized the resolution. The agent identifies the factual claim at
the center of the disagreement (what does the code actually do?), deploys a
verification probe (give a model the disputed claim and the relevant source
code, ask it to report ground truth), and records the resolution in the
Post-Review Reconciliation section of `COMPLETENESS_REPORT.md`. The
resolution format is prescribed:

```
### Conflicts resolved
- [finding description]: Code review said [X], spec audit said [Y].
  Verification probe: [what the code actually does].
  Resolution: [BUG CONFIRMED / FALSE POSITIVE / DESIGN CHOICE]. [Explanation.]
```

If the resolution confirms a BUG, the finding gets a regression test. If the
resolution overturns a BUG, the corresponding regression test is cleaned up
per the "Cleaning up after spec audit reversals" section of
`review_protocols.md`, either deleted or relocated to a separate
`quality/design_behavior_tests.*` file that documents intentional behavior.
The BUG tracker entry in PROGRESS.md is updated either way.

The principle stated in the reference is explicit and worth quoting: "Do not
resolve conflicts by defaulting to one source. Neither the code review nor
the spec audit is automatically more authoritative — they use different
methods (structural reading vs. spec comparison) and have different blind
spots. The verification probe is the tiebreaker."

This is a small architectural commitment with large consequences. It means
the skill treats both of its major analytical passes as fallible, and it
invests in a third mechanism — the probe — specifically for resolving
disagreements between them. Later versions build on this: the idea of using
targeted probes as a tiebreaking mechanism shows up in other contexts as the
skill matures.

## How It Fits Today

PROGRESS.md is still core in v1.4.5. The cumulative BUG tracker remains the
single list that the closure-verification step reads. The phase-completion
checklist is still the canonical signal that a run is or isn't complete. The
artifact inventory is still how carried-over artifacts are tracked alongside
freshly generated ones. The idea that the agent externalizes state to disk
and re-reads it before each phase — that long runs cannot assume in-memory
continuity — has become an architectural assumption throughout later versions
of the skill. It shows up, in various forms, in every major subsequent
release.

The orphan-gap closure also held. Once the cumulative tracker was the single
source of truth for closure, later versions did not need to re-solve the
problem. Additional sources of findings introduced in later versions — for
example, integration-test failures, completeness-report recommendations, and
user-requested investigations — all route their confirmed bugs into the same
tracker with their own `Source` label, and the closure mandate applies
uniformly. The design generalized cleanly.

The secondary improvements have aged equally well. The partial-session
detection check still runs before marking any phase complete; a
`quality/code_reviews/` directory that contains only scaffolding files is
still classified as FAILED rather than as a clean run with no findings. The
SKILL.md instruction — "A partial session is not a 'clean run with no
findings' — it's a failed run that needs to be re-executed" — is still on the
books. Provenance headers on carried-over artifacts are still mandatory and
are how users reading a completed quality directory can distinguish fresh
results from archival ones.

The conflict-resolution procedure, too, has remained intact. Later versions
added more occasions on which a verification probe might be warranted, but
the core rule — that neither source defaults to authoritative and the probe
is the tiebreaker — is unchanged.

If v1.3.4 was the version that taught the skill to close its own findings,
v1.3.5 is the version that taught the skill to remember what it found. Both
lessons are permanent. The small-diff, large-concept nature of this release
is itself instructive: changing the skill's fundamental assumption about
memory required only 165 inserted lines, because the mechanism is a single
structured file and a discipline around reading and writing it. The skill's
architecture was ready for external memory; it only needed the file and the
protocol.

## Provenance

This retrospective is grounded in the primary commit:

- **Commit:** `6011d45` — *v1.3.5: Add PROGRESS.md as external memory, close spec-audit orphan gap*
- **Author:** Andrew Stellman
- **Date:** Mon Apr 6 00:36:58 2026 -0400
- **Co-author:** Claude Opus 4.6
- **Files changed:** `README.md`, `playbook/SKILL.md`, `playbook/references/requirements_pipeline.md`, `playbook/references/review_protocols.md`, `playbook/references/spec_audit.md`
- **Scope:** 165 insertions, 4 deletions across five files

The PROGRESS.md template described in the Design section is the one
introduced verbatim by this commit in `playbook/SKILL.md` under the
"Checkpoint: Initialize PROGRESS.md" subsection. The orphan-gap statistics
(roughly thirty percent of findings, one of eight repositories producing
spec-audit regression tests) are drawn from the v1.3.4 review-synthesis
rationale recorded in the same commit, in the "Why this is a separate step"
explanation added to `playbook/references/review_protocols.md`. The
conflict-resolution quotation ("Do not resolve conflicts by defaulting to one
source...") is verbatim from `playbook/references/requirements_pipeline.md`
as modified by this commit. The partial-session and provenance-header
language is verbatim from the additions to `playbook/references/spec_audit.md`
under the "Detecting partial sessions and carried-over artifacts" heading.

Git is authoritative for this document. Where chat history or external
recollection would conflict with the commit, the commit wins.
