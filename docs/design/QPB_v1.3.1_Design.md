# Quality Playbook v1.3.1 — Retrospective Design Document

**Version:** 1.3.1
**Status:** Shipped
**Date:** April 4, 2026
**Author:** Andrew Stellman

---

## What This Version Introduced

Version 1.3.1 was a consolidation release. It followed immediately on the heels of
v1.3.0, which had introduced the five-phase requirements pipeline as a structured
way to turn a pile of source code into a coherent set of testable requirements.
v1.3.0 made the pipeline work end-to-end. v1.3.1 turned it from something that
worked once into something that worked reliably on the kinds of codebases users
were actually running it against.

Four changes shipped under the v1.3.1 label, across two commits made on the same
day.

The first change, landed in commit `4c0e98f`, raised the scaling gate thresholds
that govern how the pipeline handles projects of different sizes. The trigger was
a full pipeline run against Google's Gson library. The Gson run produced
benchmark data that showed the existing thresholds were far too conservative, and
the commit rewrote them using that data as the empirical basis.

The second change, landed later the same day in commit `16b246d`, introduced a
self-refinement loop between Phase D (completeness check) and Phase E (narrative
pass) of the requirements pipeline. The loop runs up to three iterations, reading
the completeness report the previous phase wrote, closing the gaps that report
identified, and re-running the checks. It short-circuits when a single iteration
makes fewer than three changes — a diminishing-returns signal rather than a hard
count.

The third change, also in commit `16b246d`, made the three-pass code review
protocol mandatory rather than advisory. A new "Execution requirements" section
in `review_protocols.md` spelled out what each pass does, required distinct
output sections for each pass with specific headers, added scoping guidance for
codebases with more than fifty requirements, and introduced a self-check the
agent must run before declaring the review finished.

The fourth change, again in commit `16b246d`, expanded the Phase 4 improvement
menu from three paths to five. Interactive requirements review and multi-model
refinement were elevated to first-class improvement paths alongside the existing
review-and-harden, guided Q&A, and chat-history-mining options. The "additional
documentation sources" path was broadened beyond AI chat exports to include
Slack, Teams, email threads, tickets, design documents, and forum archives.
`REQUIREMENTS.md` was moved to the first position in the artifacts summary
table, replacing `QUALITY.md` as the top-billed output.

These four changes are tightly connected even though they touched different
parts of the skill. They all address the same underlying problem: v1.3.0 could
produce a requirements document, but the baseline the pipeline produced on its
first pass was not yet the document the user ultimately wanted. The pipeline
needed a disciplined way to close the gap between first draft and usable
artifact. The review protocols needed to actually execute all three passes
rather than collapsing them into one. And the improvement menu needed to lead
with requirements work, because by v1.3.1 requirements had become the
centerpiece artifact of the skill.

## Why It Was Needed

The v1.3.0 pipeline was a proof of concept that had just become a real tool.
Running it against real codebases surfaced three categories of problem. All
three fed into v1.3.1.

The first category was pipeline output quality. Phase D of the pipeline — the
completeness check — did a good job of identifying gaps. It applied a domain
checklist, ran a testability audit, and looked for cross-requirement consistency
issues. But identifying gaps and closing gaps are different operations. In
v1.3.0, Phase D would write a `COMPLETENESS_REPORT.md` listing missing
requirements, vague conditions, and numeric inconsistencies, and then the
pipeline would move straight to the narrative pass.

The gaps flagged in the report were visible to the model but not acted on. Users
reading the final `REQUIREMENTS.md` would see the gap list and wonder why the
pipeline had not filled them in — the model had already noticed the problem and
then moved on. The instinct in v1.3.0 had been that finding the gap was the hard
part. In practice, finding the gap was only half the work. Closing the gap was
the other half, and the pipeline had no place for it.

The second category was review protocol discipline. The three-pass code review
protocol documented three distinct lenses — structural bugs, requirement
verification, cross-requirement consistency — but the output of a review often
collapsed them. An agent running the protocol would produce a single blended
findings list rather than three clearly labeled sections. Pass 2 in particular,
which ties findings back to specific requirement numbers with SATISFIED or
VIOLATED verdicts, was the pass most likely to get absorbed into a generic
"issues found" list.

Without Pass 2 producing its own distinct output, the traceability story of the
playbook fell apart. The whole point of having generated requirements was to be
able to cite them during review — to be able to look at a change and say "this
violates REQ-042" rather than "this looks wrong." When the three-pass structure
was implicit, agents would sometimes collapse it and the citation discipline
would collapse with it. The protocol needed an enforcement mechanism, and the
cheapest enforcement mechanism available was to mandate the output shape and
check it afterward.

The third category was scaling. The scaling gate in the SKILL.md file and the
requirements pipeline reference was set too conservatively. v1.3.0 had picked
round numbers: `≤100` files proceed normally, `101–300` focus on core
subsystems, `>300` recommend per-subsystem runs. The numbers had seemed
defensible at the time because no one had actually run the pipeline against a
large project and measured what happened.

The Gson benchmark revealed the numbers were wrong. Gson has about 81 source
files, well under the 100-file threshold, and the pipeline produced 110
requirements with full coverage on a single run. The result showed the model
could happily handle projects much larger than 100 files in one pass. The
existing thresholds were pushing users into unnecessary subsystem scoping for
projects that could be handled whole. A user with a 200-file project would be
told to scope to core subsystems even though the pipeline could in fact produce
a clean result for the full project.

On top of the output-quality and scaling issues, the improvement menu had
structural problems of its own. v1.3.0 offered three paths: review and harden
individual items, guided Q&A, and mining chat history. Those three paths had
been designed before the requirements pipeline existed, when the centerpiece
output of the skill was `QUALITY.md`. After v1.3.0, `REQUIREMENTS.md` was the
centerpiece, and the improvement menu did not reflect that. There was no
first-class path for reviewing the generated requirements, and there was no
first-class path for refining them with a different model. Those were the two
most valuable things a user could do after an initial pipeline run, and they
were not in the menu.

## The Self-Refinement Loop

The self-refinement loop sits between Phase D and Phase E of the requirements
pipeline and runs up to three iterations. It is the feature that gives v1.3.1
most of its practical value.

Each iteration starts by reading the `COMPLETENESS_REPORT.md` that Phase D just
wrote. The report contains three categories of finding. GAP entries flag
behavioral domains that are under-covered or entirely missing from the
requirements. Testability issues flag requirements whose conditions of
satisfaction are too vague to verify — "responds quickly" rather than "responds
within 500ms at p95." Consistency issues flag cases where two requirements
contradict each other, for instance by specifying overlapping numeric ranges or
incompatible guarantees.

The iteration makes targeted changes to `REQUIREMENTS.md` based on those
findings. For a GAP, the model either adds a new requirement using the
seven-field template or adds conditions of satisfaction to an existing
requirement that turns out to cover the domain after all. For a testability
issue, the model sharpens the condition — replacing qualitative language with
specific, verifiable criteria. For a consistency issue, the model resolves the
conflict, typically by picking one of the two constraints and updating the other
requirement to match.

After the fixes, all three checks — domain completeness, testability audit, and
cross-requirement consistency — run again and write updated results to
`COMPLETENESS_REPORT.md`. The report for iteration N replaces the report for
iteration N-1 so the file always reflects the current state.

The loop includes a short-circuit rule. After each iteration, the model counts
how many requirements were added or modified. If that delta drops below three
changes, the loop stops. Three iterations is the hard ceiling, but diminishing
returns usually stop the loop earlier. The short-circuit is intentionally loose:
it does not require zero changes or a clean report, only that the current
iteration made fewer than three changes. The reasoning is that an iteration
making one or two changes is making changes in the noise — the gaps it is
closing are small, and the remaining issues are either not worth another full
iteration or are the kind of gap that self-refinement cannot close anyway.

The guidance accompanying the loop is explicit about its limitations. The
v1.3.1 pipeline reference calls out that this is self-refinement — the same
model checking its own work. It catches gaps the model can recognize once they
are pointed out. Uncovered domains, vague conditions, numeric inconsistencies
between requirements — all of these are visible to the model in the
completeness report, and the model can fix them once they are visible. What the
loop does not catch are blind spots the model does not recognize as gaps. If
the model failed to think of a whole class of behavior in Phase B, it will
likely fail to think of it in Phase D, and the self-refinement loop will not
surface it.

That ceiling is acknowledged rather than hidden. The pipeline reference names
the tools that exist for breaking through it: the cross-model review and
refinement protocols, which bring in a different model with different blind
spots, and human review, which brings in context the model cannot infer. The
loop is positioned as the first, cheapest gap-closing pass in a layered system,
not as a substitute for the later layers. By the time a user has run the
pipeline, they have a self-refined baseline. If they want to push further, they
know which tools exist for doing so, and the improvement menu leads them to
those tools directly.

One subtle design choice is that the loop runs before Phase E, not after. Phase
E is the narrative pass — project overview, use cases with traceability,
category narratives, reordering for top-down flow, and renumbering the
requirements sequentially. Running refinement after Phase E would invalidate
the narrative structure every time requirements were added or renumbered, and
would require re-running the narrative work each time.

Running the loop before Phase E means the narrative is built on top of a
settled requirement set. The user sees a document that reads as a coherent
whole rather than a baseline document with a gap list stapled to the end. The
use case traceability in Phase E references requirement numbers that will stay
stable because no more additions are coming. The category narratives describe
the requirements as they actually are, not as they were before refinement.

Another subtle design choice is that the loop writes to
`COMPLETENESS_REPORT.md` in place rather than producing a separate report per
iteration. An earlier version of the design contemplated per-iteration reports
for traceability. In practice, the value of per-iteration reports is low:
users care about the final state, not the path through it, and keeping the
report clean makes the pipeline output easier to read. The iteration history is
still reconstructible from the git-tracked `quality/history/vX.Y/` backups that
the pipeline writes, so nothing is lost.

## The Three-Pass Mandate

The three-pass review protocol had existed before v1.3.1, but the commit made
execution of all three passes a protocol-level requirement rather than an
implicit expectation. Before v1.3.1, the protocol described three passes and
trusted the agent to run all three. After v1.3.1, the protocol requires three
labeled sections in the output file, specifies what each must contain, and tells
the agent to self-check the output before finishing.

The three lenses are documented side by side in the new "Execution requirements"
section so the distinction between them is unavoidable. Pass 1 finds structural
bugs — race conditions, null hazards, resource leaks — the kind of finding that
comes from reading the code carefully and applying general software engineering
judgment. Pass 2 finds requirement violations — missing behavior, spec
deviations, specific REQ-NNN citations with SATISFIED or VIOLATED verdicts — the
kind of finding that comes from cross-referencing the code against the
generated requirements. Pass 3 finds cross-requirement contradictions —
inconsistent ranges, conflicting guarantees, overlapping conditions — the kind
of finding that comes from stepping back from individual requirements and
looking at the set as a system.

None of these lenses subsumes the others. A structural bug is not a requirement
violation, a requirement violation is not a contradiction between requirements,
and a contradiction between requirements is not a structural bug. The protocol
in v1.3.1 is now explicit that consolidating passes is not allowed. If the
agent tries to produce a single merged findings list, the output fails the
protocol's own self-check.

To make that mandate enforceable, the protocol specifies the exact section
headers the output file must use. The headers are `## Pass 1: Structural
Review`, `## Pass 2: Requirement Verification`, `## Pass 3: Cross-Requirement
Consistency`, and `## Combined Summary`. If a pass would be empty, the agent
writes the header and "No findings" rather than skipping it. That small change
turns the three-pass structure from a suggestion into a checkable artifact
shape. An auditor reading the review file can tell immediately whether all
three passes ran. A downstream tool parsing the review file can find Pass 2
findings reliably. A future version of the protocol can add enforcement around
the headers without breaking compatibility, because the headers are now part of
the protocol rather than part of the agent's stylistic choices.

The protocol also adds scoping guidance for codebases with more than fifty
requirements. In that regime, Pass 2 does not need to verify every requirement
against every file. Instead, Pass 2 focuses on the requirements most relevant
to the files being reviewed — the requirements that reference those files or
that govern the behavioral domain those files implement. The goal is depth on
the files under review, not breadth across the whole requirement set.

Without this guidance, an agent reviewing a five-file pull request against a
two-hundred-requirement codebase faces a bad choice. It can try to cite every
requirement, which produces a bloated and shallow review that dilutes the real
findings. It can give up on traceability altogether and revert to a pass-1-style
review without requirement citations. Neither is what the protocol wants. The
v1.3.1 scoping guidance resolves the dilemma by telling the agent exactly how to
narrow Pass 2's focus without abandoning its distinct purpose.

Finally, the protocol adds a self-check the agent must run before declaring the
review finished. After writing all three passes and the combined summary, the
agent verifies three things. First, all three pass sections must exist in the
output, with their required headers. Second, Pass 2 must reference specific
REQ-NNN numbers with SATISFIED or VIOLATED verdicts — not generic "requirements
are satisfied" language, but specific citations with verdicts. Third, Pass 3
must identify at least one shared concept between requirements, even if the
conclusion is that the requirements are consistent. The Pass 3 check exists
because an empty Pass 3 is usually a sign that the agent did not actually
examine cross-requirement consistency — it skipped the pass rather than
confirming consistency.

If any check fails, the agent goes back and completes the missing pass rather
than shipping an incomplete review. That final guardrail is what turns "three
passes are mandatory" from documentation into behavior. Without the self-check,
the protocol is advisory even when it claims to be mandatory. With the
self-check, the agent cannot finish the protocol without actually running all
three passes and producing output that shows it did.

## Gson-Calibrated Gates

The second v1.3.1 commit, `4c0e98f`, is short — five lines changed across two
files — but it matters more than its size suggests. It is the first example in
the Quality Playbook of a threshold being moved because a real benchmark run
contradicted the original guess.

The scaling gate is the mechanism the pipeline uses to decide how to handle
projects of different sizes. On small projects, the pipeline extracts contracts
from every source file. On medium projects, it focuses on a few core
subsystems. On large projects, it tells the user to run the pipeline separately
for each subsystem. The break points between these regimes are the scaling
gate thresholds, and they determine which regime a given project falls into
when the pipeline starts up.

v1.3.0 set those thresholds at `≤100`, `101–300`, and `>300` source files.
Those numbers were plausible but not measured. They reflected an intuition that
the model would start to lose fidelity somewhere around a hundred files as
context pressure mounted, and that subsystem scoping would become necessary
somewhere past three hundred. The intuition had been reasonable but it had not
been tested.

When the pipeline was run against Gson, which has roughly 81 source files, it
produced 110 requirements with full coverage in a single pass. That result was
important for two reasons. First, the raw number — 110 requirements — showed
that Gson, despite being comfortably under the 100-file ceiling, was actually a
fairly substantial extraction target. The pipeline was not just handling a
toy. Second, the coverage was full: every contract identified in Phase A was
traced to at least one requirement by the end of Phase E, and the
completeness check did not flag systemic gaps. The pipeline handled a
real-world, 81-file, open-source Java library without losing fidelity.

That result demonstrated the model could handle substantially more than 100
files at once without losing contracts to context limits. The v1.3.0 thresholds
were conservative by a factor of roughly three. v1.3.1 accordingly raised the
thresholds: `≤300` source files now proceed normally, `301–500` focus on core
subsystems, and `>500` get the recommendation to scope per subsystem. The
labels were renamed to match — "Standard project," "Large project," and "Very
large project" — replacing "Small," "Medium," and "Large." The rename
acknowledges that a 200-file project is no longer exceptional for the pipeline;
it is the standard case.

The Gson result itself is called out in the reference document as the
empirical basis. The threshold text now reads, in part, "Projects in this range
have been tested end-to-end (e.g., Gson at ~81 source files produced 110
requirements with full coverage)." The citation matters. A future maintainer
reading the threshold can see exactly which benchmark set it, and a future
benchmark that contradicts the current threshold has a concrete reference point
to argue against.

This is a small change but a meaningful precedent. It establishes that the
playbook's numeric thresholds are not invariants. They are calibration points,
and calibration is done by running real projects through the pipeline and
adjusting the gates based on what the data shows. The Gson calibration made
the playbook more useful on real work by raising the standard-project ceiling
threefold, and it set the pattern that later versions would follow for other
thresholds — scaling gates, iteration caps, scoping thresholds, and others.

The habit of citing the specific benchmark in the threshold text makes it easy
for a future maintainer to understand why the numbers are what they are. It
also makes it easy to revise the numbers when new benchmarks contradict the
old ones, because the argument for revision is concrete. Someone proposing to
raise the `≤300` threshold further could bring a specific benchmark —
"library X with 400 files produced Y requirements with full coverage" — and the
existing threshold text tells them exactly what kind of evidence to bring.

## Phase 4 UX Improvements

The Phase 4 improvement menu expanded from three paths to five in v1.3.1. That
is the change with the most visible effect on a user running the skill, because
Phase 4 is where the user interacts with the skill most directly — it is the
menu they see after the initial pipeline run completes.

The v1.3.0 menu had three options. Review and harden individual items. Guided
Q&A with three to five targeted questions. Review development history by
mining exported AI chat folders. Those three options covered useful ground,
but they were organized around the pre-v1.3.0 view of the skill in which
`QUALITY.md` was the centerpiece artifact. The v1.3.0 release had shifted the
centerpiece to `REQUIREMENTS.md` without updating the improvement menu to
match.

The v1.3.1 menu leads with two new options. The first is interactive
requirements review, which points the user to `quality/REVIEW_REQUIREMENTS.md`
for a guided walkthrough of the generated requirements organized by use case.
The user can pick specific use cases to drill into, walk through all of them
sequentially, or invoke a cross-model audit where a different model fact-checks
the completeness report. The second is multi-model refinement, which points
the user to `quality/REFINE_REQUIREMENTS.md`. Each refinement pass backs up
the current version, reads feedback from `REFINEMENT_HINTS.md`, makes targeted
improvements, bumps the minor version, and logs changes in
`VERSION_HISTORY.md`. The user can run this pass with Claude, GPT, Gemini, or
any other model, and each pass catches different blind spots.

The three original options remain but are reordered and refined. "Review and
harden individual items" is now path 3, renamed to "Review and harden other
items" to make clear that it applies to scenarios, tests, and protocol
sections — not requirements, which now have dedicated paths of their own.
"Guided Q&A" is now path 4, unchanged in substance. "Review development
history" is now path 5, renamed to "Feed in additional documentation sources"
and substantially broadened. Where the v1.3.0 version referred specifically to
"exported AI chat history (Claude, Gemini, ChatGPT exports, Claude Code
transcripts)," the v1.3.1 version lists chat history alongside Slack and Teams
channels, email threads, Jira and Linear tickets, GitHub issues, design
documents and architecture decision records, meeting notes, newsgroup posts,
forum discussions, and mailing list archives. The scope of "intent sources"
the skill considers has opened up, and the menu text tells the user that tools
like Claude Cowork, GitHub Copilot, and OpenClaw can help gather these sources
into a folder for the skill to consume.

Alongside the menu expansion, the artifacts summary table was reordered.
`REQUIREMENTS.md` moved to the first position, replacing `QUALITY.md` as the
top-billed output. The row's confidence annotation was updated to reflect the
new pipeline behavior: "Medium — solid baseline from 5-phase pipeline, improves
with refinement passes." That phrasing does two things. It tells the user that
the pipeline output is a baseline rather than a final document, and it tells
the user that the refinement passes are the mechanism for improving it. The
summary table is the first thing a user sees after the pipeline finishes, and
the confidence text now sets the right expectation from the first look.

## How It Fits Today

The four changes from v1.3.1 are still in the skill in v1.4.5.

The self-refinement loop is still the gap-closing layer that sits between
initial completeness checking and narrative pass. Later versions added more
layers around it — cross-model refinement protocols, interactive requirements
review, more sophisticated refinement hints — but the in-pipeline
self-refinement loop is the first and cheapest of those layers, and it still
runs on every pipeline invocation. The design choice to cap it at three
iterations and short-circuit below three changes per iteration has held up.
Longer loops were contemplated and tried in practice; they did not meaningfully
improve output quality, and they added runtime for marginal benefit. The
v1.3.1 numbers turned out to be the right numbers.

The three-pass mandate is also still in place. The specific section headers
defined in v1.3.1 — `## Pass 1: Structural Review`, `## Pass 2: Requirement
Verification`, `## Pass 3: Cross-Requirement Consistency`, and `## Combined
Summary` — are the headers every review still uses today. The scoping guidance
added in v1.3.1, focus Pass 2 on the requirements relevant to the files under
review once the project exceeds fifty requirements, has become more important
as the playbook has been run against larger projects. The self-check at the
end of the review is unchanged in spirit and has been the template for similar
self-check patterns added to other protocols since.

The Phase 4 improvement menu has continued to evolve. Later versions extended
it further, but the structural shift v1.3.1 made — elevating requirements
review and multi-model refinement to first-class improvement paths and putting
`REQUIREMENTS.md` at the top of the artifacts summary — is the arrangement the
skill has kept. The improvement menu in v1.4.5 is a descendant of the
five-option menu, not the three-option one.

The Gson-calibrated thresholds remained stable through subsequent versions,
and the practice of citing benchmark results in the threshold text has spread.
Several thresholds introduced after v1.3.1 reference specific projects and
specific results as justification. The habit of calibration-by-benchmark that
v1.3.1 established is now how the playbook sets numeric gates, and the Gson
citation in the scaling gate text is still there as the first example.

Perhaps the most durable effect of v1.3.1 is conceptual rather than textual.
v1.3.0 had introduced a linear pipeline — extract, derive, cover, complete,
narrate. v1.3.1 turned it into a pipeline with a feedback loop inside it, and
then put the three-pass review mandate around the whole artifact set as an
outer check. The skill stopped being a one-shot generator and became a
disciplined producer-and-verifier. Every version since v1.3.1 has added more
producers and more verifiers, but the shape of the system — produce, check,
refine, check again, then ship — was set by v1.3.1.

## Provenance

Two commits composed this release.

Commit `4c0e98f`, "v1.3.1: Raise scaling gate thresholds based on Gson
results," dated April 4, 2026, 09:40 EDT. It touched `playbook/SKILL.md` and
`playbook/references/requirements_pipeline.md`. It bumped the version metadata
and banner from 1.3.0 to 1.3.1 and rewrote the scaling gate thresholds from
`≤100 / 101–300 / >300` to `≤300 / 301–500 / >500`, citing the Gson run as the
empirical basis. Five lines changed across two files.

Commit `16b246d`, "v1.3.1: Self-refinement loop, three-pass mandate, and Phase
4 UX improvements," dated April 4, 2026, 13:10 EDT. It touched
`playbook/SKILL.md`, `playbook/references/requirements_pipeline.md`, and
`playbook/references/review_protocols.md`. It added the self-refinement loop
between Phase D and Phase E in the pipeline reference, added the execution
requirements section to the review protocols, expanded the Phase 4 improvement
menu from three paths to five, and moved `REQUIREMENTS.md` to the top of the
summary table in SKILL.md. Forty-three lines changed in SKILL.md, sixteen in
the pipeline reference, fourteen in the review protocols — fifty-nine
insertions and fourteen deletions across three files.

Together these two commits changed roughly sixty lines of text across three
files. That small footprint is disproportionate to their effect on how the
skill actually behaves in practice. They converted the v1.3.0 pipeline from a
linear produce-and-ship assembly line into a disciplined loop-and-verify
pipeline. They made the review protocol's three-pass structure real rather than
aspirational. And they set the precedent that thresholds move when benchmarks
say they should, not before and not after.
