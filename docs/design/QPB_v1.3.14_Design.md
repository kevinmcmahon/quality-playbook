# QPB v1.3.14 Design Retrospective

**Version:** 1.3.14
**Status:** Shipped; partially superseded by v1.5.0 (bidirectional traceability reverted)
**Date:** 2026-04-08
**Author:** Andrew Stellman
**Primary commit:** `4bc3699` — "v1.3.14: bidirectional traceability, use-case-grounded integration tests, 7 changes"

---

## What This Version Introduced

Quality Playbook v1.3.14 was a single-file commit — 79 insertions and 9
deletions to `SKILL.md` — but it was one of the most consequential releases
in the skill's design evolution. The commit message called it "seven changes
addressing systemic weaknesses found in the v1.3.13 council review." Two of
those changes were structural and ambitious. The remaining five were
targeted repairs to the requirements pipeline and the artifact contracts
surrounding it.

The two headline changes were bidirectional traceability and use-case-grounded
integration tests. Bidirectional traceability added a reverse check, cast as
"Step 7b" in the requirements pipeline, that asked whether significant code
paths mapped back to requirement conditions — not just whether each requirement
had a source citation. Use-case-grounded integration tests added a new column
to the integration-test matrix that forced every test group either to map to
a named use case (e.g., UC-03) or to be explicitly labeled `[Infrastructure]`.
The two changes were designed to work together: use cases would anchor the
forward direction and the reverse map; integration tests would inherit that
anchoring rather than drifting into framework-centric coverage theater.

The seven changes listed in the commit message, in order, were:

1. An **overview validation gate** — a mandatory self-check that asks whether
   the REQUIREMENTS.md overview actually describes the project the way its
   real users would recognize it, including ecosystem role and real-world
   significance.
2. **Use case derivation from user outcomes** — use cases must be derived from
   the validated overview and gathered documentation, then validated against
   the code, rather than scraped out of source by grouping features into
   categories.
3. **Retirement of the "directional" specificity category** — the old
   `directional` bucket was replaced with two options: `specific` (testable
   against a code location) or `architectural-guidance` (cross-cutting
   properties, not counted in coverage metrics, bounded at 0–3 per project).
4. **Doc source authority tiers** — every requirement's doc-source citation
   now carries an inline `[Tier 1]`, `[Tier 2]`, or `[Tier 3]` prefix, and
   the completeness report must flag the ratio of tiers across the
   requirement set.
5. **Bidirectional traceability (Step 7b)** — a reverse traceability check
   scoped to four specific categories, with a carry-forward rule that forbids
   silent drops of previously derived requirement conditions.
6. **Acceptance criteria span check** — a Phase E gate, running after use
   case finalization, that asks whether the conditions of satisfaction across
   all requirements collectively cover the project's main behaviors.
7. **Integration test use-case traceability column** — every test group in
   the integration test matrix must either name the UC it validates or be
   explicitly labeled `[Infrastructure]`.

The commit message also noted a handful of council edits that were folded in
alongside the seven: gate ordering in Phase E, a Tier 2 clarification that
ties the tier to whether something was written as a "deliberate contract for
callers" rather than as an incidental implementation note, the 0–3 bound on
architectural-guidance requirements, a security-severity rubric, and a
requirement that prior spec audit outputs be read before running the
known-bug-sentinel check.

## Why It Was Needed

v1.3.13 had introduced the TDD verification protocol, spec traceability, and
the doc-source chain. Forward traceability — gathered docs → requirements →
bugs → tests — was present in the skill by the end of v1.3.13. The problem
was that forward traceability did not, on its own, prevent what the commit
message for 4bc3699 calls the "v1.3.13 virtio regression": a real bug that
had been caught in an earlier run was silently dropped from the next run's
requirements, and because nothing compared the new requirement set against
the old one, the regression went undetected until a council review surfaced
it. File-level coverage had been 100% in v1.3.13. Two real bugs still
escaped.

The council review that followed v1.3.13 was the forcing function for
v1.3.14. The review pointed out that the skill was generating overviews that
read like "someone only read the source code and never used the software."
Use cases, in turn, were being derived from the code rather than from the
project's user base, which meant that integration tests built on those use
cases would validate code paths rather than user outcomes. The specificity
field — specifically the `directional` option — had become a catch-all for
requirements that couldn't be made testable; it hid coverage gaps behind
plausible-sounding guidance language. And the doc-source field, while it
recorded a citation, did not distinguish between an authoritative protocol
spec and a paragraph lifted from a troubleshooting README.

The bidirectional traceability idea emerged from the virtio regression. If
forward traceability could miss a condition that had been present in a prior
run, something had to look the other way — from code paths back to
requirement conditions — and something had to compare runs against each
other. Step 7b was the answer to the first half. The carry-forward rule was
the answer to the second.

One more pressure came from integration tests. In v1.3.13, the integration
test protocol produced matrices that looked reasonable on their face but
tended to validate infrastructure rather than user outcomes. A matrix that
showed twelve passing test groups could still leave every user-recognizable
behavior untested, because no single mechanism linked a test group to the
outcome it was supposed to protect. The fix could not be applied only at
the integration-test layer; it required the use-case layer to carry enough
weight to be worth mapping tests against. That, in turn, required overviews
and use cases to be something other than restatements of the code.
v1.3.14's architecture reflects this dependency: gates were added to the
overview and use cases first, and only then were integration tests asked to
anchor to them.

## The Bidirectional Traceability Design

Step 7b was added to the requirements pipeline immediately after Step 7a
(the existing forward completeness check) and was explicitly scheduled to
run after Phase E completed — that is, after the overview validation gate,
use case derivation, and acceptance criteria span check had all produced
final artifacts. The timing mattered: the reverse traceability check
depended on both finalized requirements and finalized use cases. Running it
earlier would have produced false positives against material the pipeline
was still going to add.

The mechanism operated at path, branch, and helper granularity rather than
at file level. The commit diff is explicit on this point: "file-level
coverage was 100% in v1.3.13 and still missed two real bugs. The question is
not 'does this file map to some requirement?' but 'does this significant
branch map to a requirement clause that states what must be preserved
here?'" That framing narrowed the scope of the check in a useful way. The
skill was not being asked to audit every branch in the tree; it was being
asked to confirm that specific categories of branch were covered.

Four categories were enumerated. The first was **alternative paths already
named in requirements**. A requirement saying "the system handles both X and
Y" was declared incomplete unless it also carried an explicit symmetry
condition stating what invariant held across both paths. MSI-X vs INTx
fallback, admin queue present vs absent, sync vs async — all of these were
called out in the diff as the kinds of alternative path that had to be
accompanied by a symmetry statement.

The second category covered **helpers that translate public constants into
runtime behavior**. The canonical example in the diff was
`vring_transport_features()`, a virtio helper that whitelists feature bits.
Codec registry lookups and feature flag gates were also named. A helper of
this kind, the design said, must have a helper-specific requirement
enumerating the expected preserved or translated values — not a general
requirement about "feature negotiation" that glosses over the actual
whitelist.

The third category was **capability negotiation and fallback logic**.
Protocol version negotiation, feature detection, and graceful degradation
all had to have requirements covering both the negotiated-up and
negotiated-down paths. A requirement that covered only the happy path was
not sufficient.

The fourth category, and the one most directly tied to the virtio
regression, was **functions named in prior BUGS.md, VERSION_HISTORY.md, or
spec audit outputs**. These were called "known bug class sentinels." If a
previous run had found a bug in a specific function, a future run had to
show explicit re-check evidence for that function. The diff even specified
where the evidence could come from: prior spec audit outputs in
`quality/spec_audits/` had to be read before the sentinel check ran, because
cross-model findings from council reviews were considered a high-value
source of known bug surfaces.

Orphaned paths — significant code paths in any of the four categories that
lacked requirement coverage — produced a "coverage gap" marker in the
completeness report. Gaps had to be resolved, either by adding requirement
conditions or by providing explicit justification, before the completeness
report could declare requirements sufficient.

The four-category scoping was the design's central bet. An unscoped reverse
traceability check — "does every branch in the tree map to some
requirement?" — was already known to be intractable, both because it would
produce an impossible amount of work and because the resulting map would
largely consist of trivial mappings that added no evidentiary value. The
four categories were chosen because they were the places where, in
practice, significant behavior had historically hidden. Alternative paths
hid invariants. Constant-whitelist helpers hid contracts. Capability
negotiation hid fallback behavior. Prior bug locations hid reintroduced
regressions. A reverse traceability check scoped to those four places was
believed to be both feasible for an LLM to execute and high-yield against
the class of failure v1.3.13 had exhibited.

The **carry-forward rule** closed the remaining hole. When a prior run's
REQUIREMENTS.md existed in the quality directory, the pipeline was required
to read it and check whether any conditions from the prior version had been
dropped. If conditions were dropped, the pipeline had to either re-derive
them with updated justification or document why the condition was no longer
relevant. The commit diff is blunt about why this rule existed: silent drops
were "the direct cause of the v1.3.13 virtio regression where a previously
learned requirement was lost."

Taken together, Step 7b and the carry-forward rule gave the skill a symmetric
traceability model. Forward links ran from gathered docs to requirements to
bugs to tests. Reverse links ran from four categories of significant code
path back to requirement clauses, and from each run's requirement set back
to the prior run's requirement set. A requirement condition was no longer
allowed to disappear silently.

## Use-Case-Grounded Integration Tests

The integration test protocol in prior versions had asked for a test matrix
with pass criteria, cross-variant consistency, and component boundaries, but
it had not required each test group to name the user outcome it validated.
In practice, integration tests trended toward infrastructure scaffolding —
build validation, race detection, compatibility checks — and toward
re-running existing unit tests under slightly different names. v1.3.14 made
that drift mechanically visible.

The test matrix gained a **use-case traceability column**. Every test group
had to do one of two things. It could map to a use case and describe how the
test exercised the user outcome from that use case. Or it had to be labeled
`[Infrastructure]` in the traceability column. The label was not a
deprecation — infrastructure tests still had value — but it meant those
tests did not count toward use-case coverage.

After generating the matrix, the skill was required to check whether every
use case in REQUIREMENTS.md had at least one integration test mapped to it.
Uncovered use cases were flagged as gaps. The diff also included a specific
instruction that integration tests mapped to use cases should exercise the
end-to-end behavior described in the use case rather than running existing
unit tests that happened to touch the same code paths. The example in the
diff is worth preserving in full: if a use case says "Developer authenticates
and follows redirects without leaking secrets," the integration test should
perform a redirect across domains with auth headers and verify they are
stripped — not just run `pytest -k auth`.

This anchoring only worked because use cases themselves had been repaired in
the same commit. The overview validation gate forced the project overview
to reflect real-world significance; the use case derivation gate forced use
cases to be derived from that overview plus gathered documentation, then
validated against the code. Use cases that were code-grounded but not
user-recognizable were supposed to be revised. Use cases that were
user-recognizable but not code-grounded were supposed to be revised or
removed. Only after that two-way validation passed did the acceptance
criteria span check run, and only after that did Step 7b run. The whole
chain was meant to ensure that by the time integration tests were being
generated, the use cases they mapped to were something a real user would
recognize, not a reshuffled view of the codebase.

The use case derivation gate also carried an explicit prompt that the
pipeline was required to ask itself: "Based on this project's overview,
gathered documentation, and known user base, what are the 5–7 most
important things real users do with this software?" The number 5–7 was a
deliberate choice. Fewer than five use cases tended to collapse distinct
outcomes into generic categories; more than seven tended to split a single
outcome into artificially narrow subcases. The diff names the actors the
pipeline was allowed to treat as plausible: end-user developers, system
administrators, kernel maintainers, protocol peers, integrators, and
automated consumers. Use cases whose actors did not appear on that list
were treated as a signal that the overview had not properly identified who
depended on the project.

## The Other Changes

The five remaining changes from the seven were smaller in scope but
materially affected the pipeline's behavior.

The **overview validation gate** was a short self-check inserted after the
overview was written but before use case derivation began. It asked four
questions, the most load-bearing of which was whether a developer who used
the project daily would say "yes, that's what it is and why it matters."
The diff gave specific examples — Cobra mapping to kubectl, Hugo, and the
GitHub CLI; Express powering millions of Node.js API servers; Zod feeding
form validation and tRPC; Serde as the default Rust serialization layer —
as a check against overviews that read like library summaries lifted from
source comments.

**Retiring the `directional` specificity category** was a targeted repair.
The old bucket had become a dumping ground for requirements the pipeline
could not make testable. v1.3.14 replaced it with a binary choice:
`specific` requirements counted toward coverage metrics and had to be
testable against a code location; `architectural-guidance` requirements
captured cross-cutting properties like "remain lightweight and
stdlib-compatible" or "no_std support" and did not count toward coverage.
The 0–3 bound on architectural-guidance requirements, added as a council
edit, was intended to prevent the new bucket from becoming the old bucket
under a different name. Anything that would previously have been classified
as directional had to be reclassified — either made testable, or admitted
as architectural guidance, with no middle option.

The **doc source authority tiers** added a single-character change to every
requirement's doc-source field: an inline `[Tier N]` prefix. Tier 1 was
canonical — official API docs, published specs, language or protocol
standards. Tier 2 was strong secondary — design documents, well-maintained
READMEs, Javadoc/docstrings that defined public API contracts, formal
locking annotations and safety invariants that documented caller-facing
contracts. The council edit on Tier 2 mattered here: the test was whether
something was "written as a deliberate contract for callers," not whether it
happened to describe behavior. Tier 3 was weak secondary — changelogs,
issue summaries, source comments, test files, migration guides. Requirements
backed only by Tier 3 sources had to be tagged `[Req: inferred]` with a
note explaining why no stronger source existed, and the completeness report
had to flag the ratio of tiers across the whole requirement set. This was
the first time the skill measured documentation quality as a first-class
metric rather than treating every citation as equivalent.

The **acceptance criteria span check** was a Phase E gate that ran after use
cases were finalized and validated against code. It asked whether the
conditions of satisfaction across all requirements collectively spanned the
project's main behaviors. For each use case, at least one requirement's
conditions of satisfaction had to be traceable to it, and at least one
linked requirement had to be `specific` rather than `architectural-guidance`.
Use cases that had no linked specific requirements indicated a gap. When
gaps were found, the pipeline had to either add new requirements, sharpen
existing conditions, or revise the use case if it did not reflect what the
requirements actually protected. The results were recorded in the
completeness report.

Finally, a small but important severity calibration was added to the code
review protocol. Credential leakage, authentication bypass, and
injection-class bugs were declared always high severity regardless of
assessed likelihood. Authorization header exposure across trust boundaries
— specifically cross-domain redirects — was declared to be credential
leakage by definition. When in doubt about security-relevant severity, the
skill was instructed to default to high. This was the "security-severity
rubric" named in the council edits.

## Why It Was Later Reverted (v1.5.0 Context)

Bidirectional traceability did not survive into v1.5.0. The reverse
traceability check and the carry-forward rule were both part of what v1.5.0
explicitly set aside in favor of a one-way REQ → UC traceability model. The
honest explanation is that bidirectional links proved too brittle for LLMs
to maintain consistently across runs.

The difficulty was not with the design in the abstract. The four-category
scoping was careful, the carry-forward rule was precise, and both had a
clear motivating failure (the virtio regression) behind them. The difficulty
was operational. Each run had to produce a requirement set, map each
requirement forward to its doc source, map each requirement back to its
covering code paths across four categories, and compare the new requirement
set against the prior run's requirement set to prevent silent drops. The
agent running the skill had to maintain consistency in both directions
simultaneously, every time, and had to do so against a moving target as the
pipeline's own artifacts evolved mid-run. In practice, one side of the map
would be well-maintained and the other would drift. Sometimes the forward
links were clean but the reverse scan missed a category. Sometimes the
reverse scan was thorough but a condition silently vanished from the
forward map anyway, because the carry-forward read did not always surface
cleanly against a reshuffled requirement ordering.

v1.5.0's reframing — defect as divergence between documented intent and
code implementation — also changed what traceability needed to do.
Bidirectional links had been load-bearing in a model where requirements
were synthesized from mixed sources and had to be defended against drift.
In the v1.5.0 model, documented intent comes from formal documents with
mechanically verifiable citations; code is the other artifact; the skill's
job is to compare them. Reverse traceability, in that model, is less
important than citation validity. One-way traceability from requirement to
use case is enough scaffolding, and the tier system plus the citation
schema carry the evidentiary weight that Step 7b had been trying to carry.

This is worth stating plainly. Bidirectional traceability was not
wrongheaded — it was designed in direct response to a real regression, and
it caught that class of regression when it worked. The reversal happened
because "when it worked" was not often enough, and because the replacement
model made the feature redundant rather than merely unreliable. Designs
evolve. v1.3.14's Step 7b was the right move for the skill as it stood in
April 2026, and v1.5.0's removal of Step 7b is the right move for the skill
as it stands now. Both of those statements can be true.

## How It Fits Today

Use-case-grounded integration tests survived the v1.5.0 reframing and
remain a core feature. The integration test matrix still requires a
use-case traceability column, and every test group still has to either map
to a use case or be labeled `[Infrastructure]`. The rule that integration
tests mapped to use cases must exercise end-to-end behavior rather than
re-running unit tests is still in force. Of v1.3.14's seven changes, this
is the one that has carried forward with the least modification.

The overview validation gate and the use case derivation gate also survived
in spirit, though the exact wording has been refactored alongside the
v1.5.0 formal/informal document split. The retirement of the `directional`
specificity category is permanent — the binary `specific` vs
`architectural-guidance` split is still in place. The doc-source authority
tiers were absorbed into, and extended by, the v1.5.0 five-tier requirement
model, which added explicit categories for source-of-truth code (Tier 3),
informal documentation (Tier 4), and pure inference (Tier 5).

The acceptance criteria span check still runs in Phase E.

The bidirectional traceability check (Step 7b) and the carry-forward rule
are the two pieces that v1.5.0 removes. Silent drops are now addressed by
the citation schema — a requirement that cannot cite a surviving formal
passage fails validation, which catches the drop in a different way than
the carry-forward comparison did. The reverse traceability categories are
no longer enumerated; the skill relies on the divergence-detection model to
surface missing coverage rather than on a scoped branch audit.

v1.3.14 is therefore both a shipped release and a partial ancestor. Its
contract-like integration tests, its binary specificity field, its tier
concept, and its gated Phase E all live on. Its signature headline feature
— bidirectional traceability — does not.

## Provenance

- **Git commit:** `4bc3699cfd54471c61dfa5b3d8120343a0ee28c1`
- **Author:** Andrew Stellman
- **Date:** 2026-04-08 19:12:00 -0400
- **Subject:** "v1.3.14: bidirectional traceability, use-case-grounded integration tests, 7 changes"
- **Co-author:** Claude Opus 4.6
- **Diff size:** `SKILL.md` only — 79 insertions, 9 deletions
- **Neighboring commits:** `2af5320` (v1.3.13: TDD verification protocol, spec-traceability, doc-source chain) immediately before; v1.5.0 (formal/informal split and defect-as-divergence reframing) later superseded Step 7b
- **Commit message source of truth:** the seven-change list and the council-edit notes are taken verbatim from the commit message body
- **Diff source of truth:** all design quotes in this document ("file-level coverage was 100%...", "deliberate contract for callers", "lost requirement") are drawn directly from the SKILL.md diff in `4bc3699`
