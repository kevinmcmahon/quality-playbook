# Quality Playbook v1.3.0 — Retrospective Design Document

**Version:** v1.3.0

**Status:** Shipped

**Date:** 2026-04-04

**Author:** Andrew Stellman

**Primary commit:** `fd90c25` — "v1.3.0: Add requirements pipeline, review protocol, and refinement protocol"

---

## What This Version Introduced

Version 1.3.0 was the first release in the 1.3.x line and represents the point at which requirement
generation in the Quality Playbook stopped being a single monolithic step and became a formal
multi-phase pipeline with its own review and refinement protocols. Three new reference documents
were added under `playbook/references/`, Step 7 of `SKILL.md` was substantially rewritten to
delegate its mechanics to those references, and the skill's artifact inventory expanded from a
single `requirements.md` file into a structured family of files covering contracts, coverage,
completeness, version history, and interactive review.

The commit added three new reference files: `requirements_pipeline.md` at 340 lines,
`requirements_review.md` at 158 lines, and `requirements_refinement.md` at 113 lines. `SKILL.md`
itself was modified with 44 insertions and 22 deletions concentrated almost entirely in Step 7 and
the artifact inventory table near the top of the document. In aggregate the commit introduced 633
insertions against 22 deletions.

Two notable housekeeping changes rode along with the architectural work. The primary requirements
artifact was renamed from `quality/requirements.md` to `quality/REQUIREMENTS.md`, bringing its
casing into line with the other top-level deliverables (`QUALITY.md`, `RUN_CODE_REVIEW.md`,
`RUN_INTEGRATION_TESTS.md`, `RUN_SPEC_AUDIT.md`). A new output directory, `quality/history/`, was
added to hold versioned backups. The artifact inventory in SKILL.md was updated to list the full
set of new files produced by the pipeline — `CONTRACTS.md`, `COVERAGE_MATRIX.md`,
`COMPLETENESS_REPORT.md`, `VERSION_HISTORY.md`, `REVIEW_REQUIREMENTS.md`, and
`REFINE_REQUIREMENTS.md` — in a sentence appended to the existing deliverables table.

Conceptually, this release established three things that persist in the skill through the current
v1.4.5. First, it separated contract discovery from requirement derivation, so that the model
writing formal requirements is reading from an explicit file of behavioral contracts rather than
trying to rediscover them while also composing requirements. Second, it added mechanical
verification — a coverage matrix, a twenty-two-item domain completeness checklist, and a
cross-requirement consistency check — between derivation and the final narrative pass. Third, it
introduced a versioning protocol with automatic backups so that iterative refinement could happen
across multiple models without losing earlier work.

The SKILL.md banner and metadata were updated from v1.2.0 to v1.3.0, reflecting the minor version
bump. The skill's top-level description, the Council of Three audit protocol, the QUALITY.md
generation, the functional test generation, the integration test protocol, and the AGENTS.md
bootstrap all remain unchanged in this release. The change is scoped tightly to Step 7 and to the
new reference material that Step 7 delegates to.

## Why It Was Needed

The immediate predecessor, v1.2.16, restructured Step 7 with per-subsystem requirement derivation
and the seven-field requirement template (summary, user story, implementation note, conditions of
satisfaction, alternative paths, references, specificity). That template was sound, and it survived
into v1.3.0 intact. What changed is the procedure around it.

In v1.2.x the procedure was a single-pass operation. The model read the specs, the source tree,
the ChangeLog, and the chat history, and produced `requirements.md` in one push. The
category-based audit at the end of Step 7 attempted to catch absence bugs by re-reading the output
through five domain lenses — input validation, security policy propagation, API contracts,
resource lifecycle, and a systematic absence-bug template — but the audit ran in the same
attention window as the derivation. The model had to hold every source file, every
contract, every requirement, and every domain question in working memory at once.

Two limitations of the single-pass approach motivated the pipeline. The commit message for
v1.3.0, and the overview section in `requirements_pipeline.md`, both state the first reason
explicitly: single-pass generation runs out of attention after roughly seventy requirements
because the model is simultaneously discovering contracts and writing formal requirements. The
pipeline overview cites a direct comparison on Gson — eighty-one source files, about twenty-one
thousand lines — where single-pass produced forty-eight requirements and the staged pipeline
produced one hundred and ten. That gap made a strong case for separating discovery from
composition and using file-based external memory to hold contract-level detail that would
otherwise have to remain resident in the model's working context.

The second limitation was less about raw completeness and more about iteration and trust. Once
requirements were generated under v1.2.x, there was no structured way to review them, no mechanism
to capture reviewer feedback in a way the model could re-read on a later pass, and no convention
for running a second model over the output to find what the first one missed. The skill already
advocated multi-model thinking — the Council of Three spec audit had been in the skill for
several versions — but Step 7 itself didn't expose a multi-model surface. A user who wanted a
second opinion on requirements had to run the whole Step 7 again from scratch rather than
targeting the known gaps. v1.3.0 closes that hole by defining a review protocol, a refinement
protocol, and a hints file (`REFINEMENT_HINTS.md`) that acts as the handoff between them.

A third pressure was scale. The playbook had been used on projects of widely different sizes,
and v1.2.x gave no explicit guidance on how to handle a codebase with several hundred or a few
thousand source files beyond generic subsystem advice. v1.3.0 bakes the scaling decision into
Phase A of the pipeline with explicit thresholds — one hundred source files or fewer, one hundred
and one to three hundred, more than three hundred — and explicit instructions for each band,
including a directive to tell the user when to scope the pipeline to a single subsystem at a time.
The large-project instruction is quoted verbatim in the reference: "This project has N source
files. For best results, run the requirements pipeline separately for each major subsystem."

A fourth, subtler pressure was that v1.2.x gave no mechanism for versioning. Each time Step 7 was
re-run, the previous output was overwritten. There was no way to diff two runs, no record of which
model had produced which version, and no way to distinguish an initial run from a refinement pass.
v1.3.0 introduces a major.minor version scheme, a `VERSION_HISTORY.md` file with per-version
provenance, and `quality/history/vX.Y/` snapshot directories that preserve the entire `quality/`
tree at each version change.

## The Requirements Pipeline

The five-phase pipeline is defined in `playbook/references/requirements_pipeline.md` and
referenced from Step 7 of `SKILL.md`. SKILL.md no longer carries the detailed derivation
procedure that v1.2.16 embedded; its Step 7 now opens with the instruction "Read
`references/requirements_pipeline.md` for the complete five-phase pipeline, domain checklist, and
versioning protocol," and then summarizes the five phases in place. Step 7 in v1.3.0 still holds
the seven-field requirement template and the "do not cap the requirement count" discipline, so the
SKILL.md surface remains self-contained enough to be useful standalone, but the procedural detail
lives in the reference.

The pipeline produces six artifacts in `quality/`: `CONTRACTS.md`, `REQUIREMENTS.md`,
`COVERAGE_MATRIX.md`, `COMPLETENESS_REPORT.md`, `VERSION_HISTORY.md`, and `REFINEMENT_HINTS.md`.
The last of these is created during the review phase rather than the pipeline itself, but the
pipeline reference lists it as part of the family because the review and refinement protocols
are conceptually part of the same workflow. Versioned backups go in `quality/history/vX.Y/`.

**Phase A — Contract extraction.** The model reads every in-scope source file and lists every
behavioral contract it sees or believes should exist. Contracts are categorized as METHOD (what a
public method guarantees about return value, side effects, exceptions, thread safety), NULL (what
happens when null is passed, returned, or stored), CONFIG (what effect a configuration option has
at its boundaries), ERROR (what exceptions are thrown, when, and with what diagnostic
information), INVARIANT (properties that must always hold), COMPAT (behaviors preserved for
backward compatibility), ORDER (whether output or iteration order is stable, documented, or
undefined), LIFECYCLE (resource creation and cleanup, initialization sequencing), and THREAD
(thread-safety guarantees or requirements). The output is `quality/CONTRACTS.md`.

Phase A is explicitly framed as discovery rather than judgment: "list everything, even if it seems
obvious." Expected density is five to fifteen contracts for a two-hundred-line file and twenty to
forty for a one-thousand-line file, and the phase rules call out that finding fewer than three
contracts in a file with real logic means you are skipping things. The rules also mandate
including internal files because the public API depends on them, including "should exist"
contracts (things the code doesn't do but should, based on its domain), and reading the code
rather than only the Javadoc or docstrings — with explicit instructions to list both when
documentation and code disagree.

A scaling check runs at the very start of Phase A. The model counts the source files in the
project, excluding tests, generated code, vendored dependencies, and build artifacts. For small
projects (one hundred files or fewer) the model proceeds normally and extracts contracts from
every file. For medium projects (one hundred and one to three hundred files) the model focuses on
the three-to-five core subsystems identified in Phase 1 Step 2 of the playbook, extracts contracts
from those modules and their internal dependencies, and records the scope in the CONTRACTS.md
header. For large projects (more than three hundred files) the model recommends that the user
scope the pipeline to one subsystem at a time and explains that a single pipeline run across the
full codebase will miss contracts due to context limits. If the user insists on full-project scope
anyway, the pipeline honors the request but warns that coverage will be thinner.

**Phase B — Requirement derivation.** The model reads CONTRACTS.md plus project documentation and
writes `quality/REQUIREMENTS.md` using the seven-field template inherited from v1.2.16. The work
breaks into four sub-steps: group related contracts by behavioral concern (not by file); enrich
each group with user-facing intent drawn from GitHub issues, user guides, troubleshooting docs,
and design docs; write the formal requirements; then check for orphan contracts and either add
them to existing requirements' conditions of satisfaction or create new requirements to cover
them.

The key discipline here is that each individual contract from Phase A that was grouped into a
requirement becomes a condition of satisfaction on that requirement. The model is instructed not
to modify CONTRACTS.md (it's read-only input to B), not to cap requirement counts, to ensure
every contract maps to at least one requirement, and to avoid merging unrelated contracts just
because they sit in the same class. The rule "one requirement per distinct behavioral concern"
forbids the convenience merge of "thread safety" with "null handling" when they happen to
coexist.

**Phase C — Coverage verification.** The model cross-references every contract in CONTRACTS.md
against every requirement in REQUIREMENTS.md and produces `quality/COVERAGE_MATRIX.md` with
categories for fully covered, partially covered, and uncovered contracts. The definition of
"covered" is strict: a contract is covered only if a requirement's conditions of satisfaction
explicitly test the behavior. It is not covered if it is only tangentially mentioned, implied
but not stated, or if a different aspect of the same file is covered but this specific contract
is not.

Where gaps exist, REQUIREMENTS.md is updated to close them — either by adding missing conditions
to existing requirements or by creating new requirements — and the matrix is regenerated. The
loop runs up to three iterations. It terminates when the uncovered count reaches zero or when
three iterations have run, whichever comes first.

**Phase D — Completeness check.** This is the adversarial pass. Three checks run against the
current REQUIREMENTS.md. The first is a twenty-two-item domain completeness checklist covering
null handling, type coercion, primitive-versus-wrapper semantics, generic types, thread safety,
error diagnostics, resource management, backward compatibility, security, encoding, date and
time, collections, enums, polymorphism, tree-model mutation, configuration composition, entry
points, output escaping, built-in type handler contracts, field and property serialization
ordering, identity contracts (toString, equals, hashCode), and input validation. Each item must
either cite specific REQ-NNN numbers that cover it or be flagged as a gap.

The checklist is framed as a minimum rather than a ceiling — if the model notices a domain not
listed that should have requirements for this project's domain, it is instructed to add it. A
few of the items are worth highlighting because they catch absence bugs that a purely
documentation-driven pass would miss. The "entry points" item demands that every distinct public
entry point (string-based, stream-based, tree-based, standalone parsing, multi-value parsing)
has its own contract, with N ways to start a read or write implying N sets of contracts. The
"built-in type handler contracts" item demands that each built-in handler for a standard library
type states what it promises about format, precision, normalization, and round-trip fidelity.
The "identity contracts" item requires explicit contracts for toString, hashCode, and equals on
public model types because users depend on them for comparison, logging, and collection key usage.

The second Phase D check is a testability audit. For each requirement, the model asks whether its
conditions of satisfaction are actually testable — whether a reviewer can write a concrete test
case from each condition, whether pass/fail is unambiguous, and whether the condition covers
failure modes, not just the happy path. The third check is a cross-requirement consistency check
that compares pairs of requirements referencing the same concept. Do ranges agree? Do
null-handling rules agree? Do thread-safety guarantees conflict with lifecycle contracts? Do
configuration defaults match across requirements?

The phase emits `quality/COMPLETENESS_REPORT.md` with a COMPLETE or INCOMPLETE verdict.
Crucially, the reference instructs the model to be adversarial — "assume previous passes were
imperfect" — and to verify, for each domain marked COVERED, that the cited requirements actually
address the checklist item. The instruction is explicit: "don't just check the box." After the
report is written, the model fixes what it can (adding requirements for domain gaps, sharpening
vague conditions, resolving consistency issues).

**Phase E — Narrative pass.** The last phase restructures REQUIREMENTS.md into a document a human
can read top to bottom. Before Phase E starts, the model is instructed to save a backup to
`REQUIREMENTS_pre_narrative.md` so that the structural change is reversible. The phase has six
sub-steps.

E.1 adds a project overview at the top: four hundred to six hundred words of connected prose
explaining what the software is, who uses it and why, how data flows through the major
components, and the design philosophy. E.2 adds six to eight use cases in the style of Applied
Software Project Management (Stellman & Greene). Each use case has a name, actor,
preconditions, numbered steps, postconditions, alternative paths, and a list of the REQ-NNN
numbers it exercises. E.3 adds a cross-cutting concerns section that documents architectural
invariants spanning multiple categories — threading model, null contract, error philosophy,
backward compatibility strategy, configuration composition — each as prose paragraphs that
reference specific requirements. E.4 augments existing category sections with two-to-four
sentence narratives before the first requirement of each category. E.5 reorders categories from
user-facing (entry points, configuration) to infrastructure (error handling, backward
compatibility), folding any catch-all sections into proper categories. E.6 renumbers all
requirements REQ-001 through REQ-N following document order and updates all internal
cross-references.

The phase's rules prohibit deleting, merging, or weakening any existing requirement, prohibit
adding new requirements in this pass, require the overview and use cases to be written from the
user's perspective, and require use cases to cite specific REQ numbers. Narrative work is
explicitly separated from derivation work.

The pipeline ends with the versioning protocol. Version numbers use a major.minor scheme. Major
bumps are reserved for structural changes (a new pipeline architecture, a new narrative pass,
major scope expansion) and are always made by the user. Minor bumps happen automatically on each
pipeline run or refinement pass. Before each version change the entire `quality/` directory is
snapshotted into `quality/history/vX.Y/`, so every version becomes a complete diffable snapshot
that users can compare against any other version. `VERSION_HISTORY.md` carries a markdown table
with columns for version, date, model, author, requirement count, and summary. The "Author"
column records provenance — "Quality Playbook" for automated pipeline runs, a person's name for
manual edits, a model name for refinement passes — so the history itself is self-describing.

## The Review Protocol

The review protocol is defined in `playbook/references/requirements_review.md` and is generated
into the target project as `quality/REVIEW_REQUIREMENTS.md`. It offers three modes, each of which
can be run with any model because the protocol is self-contained and reads from the files in
`quality/`. Before any mode starts, the user is instructed to confirm that REQUIREMENTS.md exists
and that they have read its Project Overview and Use Cases sections.

**Mode 1 — Self-guided review.** The model reads REQUIREMENTS.md, presents the user with a
numbered list of use cases, checks REFINEMENT_HINTS.md for prior review progress (use cases
already reviewed are marked `[x]`), and lets the user pick which use case to examine. On
selection, the model shows the use case (actor, steps, postconditions, alternative paths), lists
the linked REQ-NNN numbers, and asks whether to drill into any of them or move on. Drilling into
a requirement reveals the full seven-field structure — summary, user story, conditions of
satisfaction, alternative paths — and asks whether it captures the right behavior. Feedback is
recorded in REFINEMENT_HINTS.md under the use case heading. After each use case is reviewed the
file is marked `[x]` in REFINEMENT_HINTS.md and the model returns to the use case list. The
protocol also prompts the user to consider cross-cutting concerns or requirements not linked to
any use case. Mode 1 is for users who already know which parts of the project need scrutiny.

**Mode 2 — Fully guided review.** Same mechanics as Mode 1, but starting at Use Case 1 and
proceeding sequentially rather than asking the user to choose. For each use case the model
presents the overview, walks through each linked requirement one by one, records any feedback,
and marks the use case reviewed. After all use cases are done, the model presents the cross-
cutting concerns section and asks whether anything about threading, null handling, errors,
backward compatibility, or configuration composition is missing or wrong, and whether there are
requirements the user expected to see that are not present. The final step is a summary of all
hints collected. Mode 2 is the thorough first-pass review.

**Mode 3 — Cross-model audit.** The model reads COMPLETENESS_REPORT.md and REQUIREMENTS.md, and
for each domain in the completeness report it verifies that the cited REQ-NNN numbers actually
address the domain checklist item. If a citation is wrong — for example, if the report claims
REQ-100 and REQ-101 cover entry points but those requirements are actually about pretty printing
— Mode 3 flags it as a gap. Mode 3 also looks for orphaned requirements not linked to any use
case, alternative paths in use cases whose error and edge cases have no corresponding
requirements, and cross-cutting concerns whose cited requirements don't actually cover the stated
concern.

Mode 3 findings go into REFINEMENT_HINTS.md under a `## Cross-Model Audit` heading with three
sub-sections: verified domains (CONFIRMED), gaps found, and orphaned requirements. Mode 3 is
explicitly intended to be run with a different model from the one that generated the
requirements, so it functions as a second-opinion pass that compensates for a single model's
blind spots. The closing step is to present findings to the user and ask which gaps should be
addressed in a refinement pass.

All three modes write to a shared `quality/REFINEMENT_HINTS.md` file. That file has a defined
shape: a review progress section with `[x]`/`[ ]` checkboxes for each use case, a cross-cutting
concerns section with the same checkbox format (threading model, null contract, error philosophy,
backward compatibility, configuration composition), per-use-case feedback under `### Use Case N`
headings, a cross-model audit section if Mode 3 ran, and a freeform additional-hints section for
user feedback not tied to a specific use case. The hints file is the explicit handoff to the
refinement protocol.

## The Refinement Protocol

The refinement protocol is defined in `playbook/references/requirements_refinement.md` and is
generated into the target project as `quality/REFINE_REQUIREMENTS.md`. It is a six-step
structured process for applying review feedback to requirements, and it can be run repeatedly,
with different models, until the user hits diminishing returns. The protocol header calls this
out directly: "You can run this protocol multiple times with different models. Each run backs up
the current version, makes targeted improvements, bumps the minor version, and logs the changes.
Run as many models as you want until you hit diminishing returns."

The protocol starts by reading REFINEMENT_HINTS.md (the feedback to address), REQUIREMENTS.md
(the current state to update), CONTRACTS.md (for contract-level detail when adding new
conditions), and VERSION_HISTORY.md (to determine the current version number).

**Step 1 — Backup and version.** The current version number is read from VERSION_HISTORY.md.
All files in `quality/` are copied to `quality/history/vX.Y/` at the current version number. The
minor version is bumped (v1.2 becomes v1.3). The version stamp at the top of REQUIREMENTS.md is
updated. Backup happens before any changes, so the protocol is always reversible.

**Step 2 — Process feedback.** Each item in REFINEMENT_HINTS.md is categorized. Six categories
are defined: gap — missing requirement (a behavioral contract or domain area has no requirement;
create a new requirement using the seven-field template); gap — missing condition (an existing
requirement doesn't cover a specific scenario; add a condition of satisfaction); gap — missing
use case coverage (a use case doesn't link to a requirement governing one of its steps; add the
REQ-NNN to the use case's Requirements line); sharpening — vague condition (a condition of
satisfaction is too vague to test; rewrite with concrete pass/fail criteria); correction —
wrong content (a requirement states something incorrect; fix the specific field); and
cross-model audit finding (a domain was marked COVERED but the cited requirements don't actually
address it; add the missing requirements).

A seventh category — removal — is treated separately and with care. Removal is user-directed
only: "The user explicitly states a requirement is incorrect and should be removed (e.g., 'REQ-047
is incorrect because X — remove it'). Only process removals when the hint clearly comes from the
user, not from an automated pass." Every removal is logged with its reason in the change report.

**Step 3 — Make changes.** For each feedback item the protocol specifies the surgical action. New
requirements are added at the end of the appropriate category section with the next available
REQ number. Modifications edit only the specific field flagged; requirements not called out in
hints are left alone. Use case updates add newly created REQ numbers to the relevant use case's
Requirements line. Cross-cutting concerns are updated if new requirements affect them.

The phase is constrained by four explicit rules. Do not delete or weaken existing requirements
during automated refinement — every requirement that exists today must exist after refinement
with at least the same conditions of satisfaction, unless the user has explicitly marked it for
removal with a reason. Do not renumber existing requirements; new ones get the next available
number. This preserves traceability across versions. Do not restructure the document; the
narrative pass already established the structure, and refinement is surgical. Every change must
be traceable to a specific feedback item, so the protocol does not permit drive-by edits that
were not asked for.

**Step 4 — Report changes.** The protocol appends a `## Refinement Pass — v[new version]` section
to REFINEMENT_HINTS.md with date, model, changes made (each tied to the quoted feedback item it
addresses), feedback items not addressed (with reasons), and a summary of totals (new
requirements added, existing requirements modified, use cases updated, total requirement count).
This section becomes the input for the next pass.

**Step 5 — Update version history.** A row is added to VERSION_HISTORY.md with the new version
number, date, model, author, requirement count, and a brief summary of changes.

**Step 6 — Update completeness report.** If new requirements now fill previously flagged domain
gaps, the relevant entries in COMPLETENESS_REPORT.md are updated to cite the new REQ numbers, so
the completeness verdict stays current.

The protocol also defines how multiple passes interact. Each pass follows the same six steps,
reading the now-expanded REFINEMENT_HINTS.md (which includes prior pass reports). Subsequent
passes focus on items marked "not addressed" by earlier passes plus any new hints the user or a
fresh audit has added. The user can edit REFINEMENT_HINTS.md directly between passes, and a new
Mode 3 cross-model audit from the review protocol can be run at any point to find new gaps that
earlier refinements missed. The combined pattern is a review → refine → review → refine cycle
that converges on completeness across multiple models.

## How It Fits Today

The pipeline architecture introduced in v1.3.0 is still the backbone of requirement generation
in v1.4.5. The five phases (contract extraction, derivation, coverage verification, completeness
check, narrative pass), the file-based external memory handoff between phases, the twenty-two-item
domain checklist, the scaling gate, and the versioning protocol with `quality/history/vX.Y/`
backups all remain. The split between review (`REVIEW_REQUIREMENTS.md`) and refinement
(`REFINE_REQUIREMENTS.md`) with REFINEMENT_HINTS.md as the shared handoff is unchanged. The
artifact family that v1.3.0 introduced — CONTRACTS.md, REQUIREMENTS.md, COVERAGE_MATRIX.md,
COMPLETENESS_REPORT.md, VERSION_HISTORY.md, REFINEMENT_HINTS.md, REVIEW_REQUIREMENTS.md,
REFINE_REQUIREMENTS.md — still defines the output of a full pipeline run.

The constraints introduced in v1.3.0 persist as durable rules. Do not cap requirement counts.
Do not renumber existing requirements during refinement because renumbering breaks traceability
across versions. Do not delete or weaken existing requirements during automated refinement; only
user-directed removal is permitted, and it must be logged with a reason. Do not restructure the
document during refinement because the narrative pass already established the structure. These
rules were specific design choices in v1.3.0, and they have not been relaxed.

Subsequent releases have added around this architecture rather than replacing it: refinements to
specific phases, additional guidance in the domain checklist, more detail in the pipeline
documentation, and tighter integration with the code review protocol's verification and
consistency passes. But the core idea — that requirements are generated by a pipeline of
discrete phases with file-based handoffs and a formal versioning protocol, and that review and
refinement are separate, model-agnostic protocols that close the loop — is the v1.3.0
contribution.

## Provenance

This document is derived from the authoritative git record of the v1.3.0 release.

- **Commit:** `fd90c25efdc6f5afd022a6d6ecf559562943c5b4`
- **Commit title:** "v1.3.0: Add requirements pipeline, review protocol, and refinement protocol"
- **Date:** 2026-04-04
- **Author:** Andrew Stellman
- **Co-authored-by:** Claude Opus 4.6
- **Files changed:**
  - `playbook/SKILL.md` — 44 insertions, 22 deletions (Step 7 rewrite, version bump to 1.3.0, artifact inventory expansion, requirements.md renamed to REQUIREMENTS.md)
  - `playbook/references/requirements_pipeline.md` — 340 lines, new file
  - `playbook/references/requirements_refinement.md` — 113 lines, new file
  - `playbook/references/requirements_review.md` — 158 lines, new file
  - Totals: 633 insertions, 22 deletions
- **Predecessor:** `a61591e` — "v1.2.16: Restructure Step 7 requirement template with user stories and conditions of satisfaction"

Supplementary chat context from the "Convert quality playbook to open-source skill" conversations
in `AI Chat History/` (dated 2026-03-13 and 2026-03-28) predates this commit and was not relied on
for specific claims in this document. Where the git record and chat history would disagree, the
git record controls.
