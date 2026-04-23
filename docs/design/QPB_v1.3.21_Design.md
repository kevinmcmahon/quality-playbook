# QPB v1.3.21 Design Retrospective

**Version:** 1.3.21
**Status:** Shipped
**Date:** 2026-04-11
**Author:** Andrew Stellman
**Primary commit:** `169fc01` — "v1.3.21: mechanical verification, contradiction gate, self-contained iteration"

---

## What This Version Introduced

Quality Playbook v1.3.21 is a single release tag that rolls up three successive
increments — v1.3.19, v1.3.20, and v1.3.21 — into one shipped artifact. Read
in isolation, any one of the three would be a useful change. Read together,
they are the release in which the skill stops asking the model to judge its
own work and starts demanding proof that a shell command, a diff, or a
convergence counter can verify. The diff is compact: five files, 169 net
lines added. The philosophical shift is not compact at all.

Three capabilities landed in the tag.

The first is mechanical verification. Any contract or requirement that asserts
a function handles, preserves, or dispatches a set of named constants — feature
bits, enum values, opcode tables, event types, handler registries — must now
be backed by a non-interactive shell pipeline that extracts the actual case
labels from the function body and writes them to
`quality/mechanical/<function>_cases.txt`. The contract may only assert
presence of a constant if a matching `case X:` line appears in that file.
Downstream artifacts — REQUIREMENTS.md, CONTRACTS.md, the code review, the
spec audit — must cite the mechanical file path rather than replacing it with
a hand-maintained list. A companion script, `quality/mechanical/verify.sh`,
re-runs every extraction command and diffs the result against the saved file.
If any artifact fails the diff, it was tampered with and must be regenerated.

The second is the contradiction gate. Before the terminal gate runs at the
end of Phase 2d, the skill now compares executed evidence — mechanical
verification artifacts, regression test results, TDD red-phase outcomes, any
shell output saved during the pipeline — against prose artifacts:
REQUIREMENTS.md, CONTRACTS.md, code reviews, spec audit triage, BUGS.md. If
an executed result says the code is not compliant but a prose artifact says
it is, the executed result wins. The contradictory prose artifact is re-opened
and corrected before closure.

The third is self-contained iteration. A new Phase 0 runs automatically at
the start of every playbook execution when `previous_runs/` exists. It loads
confirmed bugs from prior runs as a seed list, re-executes each seed's
assertion against the current source tree, and injects the seed list into the
code review and spec audit as a known-open baseline. After Phase 3, a
convergence check counts net-new bugs against the seed list and writes a
`## Convergence` section to PROGRESS.md. If net-new bugs is non-zero and the
iteration counter has not reached its limit, the skill archives `quality/`
into `previous_runs/` and restarts from Phase 0. The default limit is five
iterations. A context-window safety valve allows graceful early termination
when output quality starts to degrade.

The release also grows the self-check benchmark set from 22 to 27, adding
benchmarks 23-27 for mechanical artifacts, source-inspection test execution,
the contradiction gate, seed check execution, and convergence tracking.

Supporting changes land in the reference files. `references/defensive_patterns.md`
gains a "mechanical verification artifacts outrank prose lists" rule and an
explicit fabrication warning that documents the v1.3.19 tampering incident.
`references/spec_audit.md` gains the incomplete-council gate for enumeration
checks. `references/verification.md` grows from 22 to 27 benchmarks and adds
a matching six new items to the final quick-checklist. The README is updated
to reflect the new benchmark count and the iteration description. A new
shell script, `run_iterate.sh`, provides shell-level orchestration for the
iteration loop when the skill is driven from outside its automatic path.

## Why It Was Needed

The versions leading up to v1.3.21 had a specific and recurring failure
mode. The skill was being tested against the Linux virtio subsystem, where
a function called `vring_transport_features` uses a switch statement to
enumerate which virtio feature bits the kernel is willing to keep negotiated
with the device. One of those bits, `VIRTIO_F_RING_RESET`, was missing from
the switch. The bug was real, it had an obvious mechanical signature, and
the skill had been built with a two-list enumeration check precisely to find
bugs of this shape.

It did not find the bug.

In v1.3.17, the model running the playbook wrote a requirement asserting
that `VIRTIO_F_RING_RESET` was preserved. The code review copied the claim.
Three spec auditors inherited it. The triage accepted it. The bug remained.
No human or model in the chain had opened the file and read line 3527 to
check whether the claim was true. The contamination chain was discovered
only after the run completed and someone eventually compared the switch
statement against the header.

In v1.3.18, the skill added a rule requiring code-side enumeration lists to
carry per-item line numbers, so an auditor could not cite "`case X:`" without
naming the line it appears on. The rule helped but did not close the failure.
A regression test was generated with the correct assertion
(`assert "case VIRTIO_F_RING_RESET:" in func`) but the test was marked
`run=False` and never executed. The assertion was present. The check was
inert. The bug remained.

The pattern is general: the skill kept generating prose artifacts that
asserted code presence, then using those prose artifacts as evidence that
the code was compliant. Judgment-based verification could not break the loop.
Every artifact was written by the same model that had already decided the
claim was plausible. What was missing was a step the model could not talk
its way around — a shell command that reads bytes, a diff that either
matches or does not.

v1.3.21 is the release in which that step becomes mandatory.

A related failure mode motivated the iteration work. The virtio cross-version
testing showed that playbook runs were not merely missing bugs they should
have caught — they were finding different bugs on different runs of the same
codebase. A first run would land on BUG-001 and BUG-004. A second run,
against the same source, would land on BUG-005 and BUG-006 and miss the
others. The model was not converging on the truth through repetition; it
was sampling from a distribution. Without machinery to aggregate across
samples, the skill's output was effectively a lottery. The convergence loop
exists to replace the lottery with an explicit, counted accumulation.

## Mechanical Verification

The mechanical verification subsystem has three parts: the extraction
artifact, the integrity check, and the normative/descriptive language rule.

The extraction artifact is a text file at
`quality/mechanical/<function>_cases.txt` produced by a non-interactive
shell pipeline. The canonical example in the SKILL.md update is an `awk`
range expression that isolates a function body, piped into a `grep` that
matches case labels:

```
awk '/void vring_transport_features/,/^}$/' drivers/virtio/virtio_ring.c \
  | grep -E '^\s*case\s+' > quality/mechanical/vring_transport_features_cases.txt
```

The pipeline is chosen for a specific property: it reads file bytes, prints
matches, and cannot hallucinate. If the function body does not contain
`case VIRTIO_F_RING_RESET:`, the pipeline cannot print it. Contracts that
reference the function's coverage must cite the artifact path. Hand-written
lists are non-conformant. A contract line asserting "function preserves
constant X" is forbidden unless the mechanical file contains a matching
`case X:` line. If the constant appears in a spec or header but not in the
mechanical output, the contract records it explicitly as absent, with the
phrase `[NOT IN CODE]` and a pointer to both the header definition and the
function's line range.

The integrity check exists because the first version of this mechanism
revealed a new failure mode. In v1.3.19 testing, the model executed the
correct extraction command but wrote its own expected output to the file
instead of letting the shell redirect capture the pipeline's output. The
fabricated file included a hallucinated `case VIRTIO_F_RING_RESET:` line
that the real command does not produce. The artifact existed, the contract
cited it, and the bug was still missed. The integrity check closes this
loop. `quality/mechanical/verify.sh` is generated alongside the artifacts.
It re-runs each extraction pipeline into a variable, compares the variable
to the saved file, and exits non-zero on any mismatch. Phase 3 executes
`bash quality/mechanical/verify.sh` as a mandatory step. If any artifact
diff is non-empty, the benchmark fails and the artifact must be regenerated
by re-running the extraction command — not by editing the file to match.

The normative/descriptive language rule governs how contracts and
requirements talk about code. Normative language ("must preserve," "should
handle") is allowed for expected behavior regardless of what the code
currently does. Descriptive language ("preserves," "handles") is allowed
only when a mechanical artifact confirms the claim. A requirement that
says "the implementation preserves VIRTIO_F_RING_RESET" without a
confirming artifact is non-conformant. The correct form is "the
implementation must preserve VIRTIO_F_RING_RESET" together with a citation
of the mechanical check result showing whether the constant is currently
present or absent. The rule forces the prose artifacts to tell the truth
about their own evidence — they can state an intention, or they can report
a verified fact, but they cannot conflate the two.

Benchmark 23 verifies that every relevant contract has a mechanical
artifact and that `verify.sh` passes. Benchmark 24 verifies that source-
inspection regression tests actually execute. The `run=False` failure from
v1.3.18 is now banned by name: any test whose purpose is source-structure
verification — string presence in function bodies, case label existence,
enum extraction, generated-code shape checks — must execute. These tests
read repository files and perform string matches; they are safe,
deterministic, and fast. A source-inspection test with `run=False` is
called out as "the worst possible state: the correct check exists but is
inert." The benchmark greps `quality/test_regression.*` for `run=False`
and equivalent skip mechanisms and fails if it finds any.

## The Contradiction Gate

The contradiction gate is benchmark 25 and a new step inside Phase 2d, the
post-review reconciliation phase. It runs before the terminal gate and
before Phase 3 closure.

The gate divides the artifacts produced during a playbook run into two
categories. Executed evidence includes mechanical verification artifacts
in `quality/mechanical/`, regression test results from `test_regression.*`
runs, TDD traceability red-phase results, and any shell command output
saved during the pipeline. Prose artifacts include REQUIREMENTS.md,
CONTRACTS.md, code reviews, spec audit triage, and BUGS.md. The gate's
rule is a strict ordering: executed evidence outranks prose artifacts at
closure.

The gate looks for three specific contradictions. First, if any
`quality/mechanical/*` file shows a constant as absent, no prose artifact
may claim it is present — the assertion must be rewritten or the artifact
re-opened. Second, if any regression test with `xfail` actually fails
(reported as XFAIL because the strict expected-failure assertion fired),
BUGS.md may not claim that bug is "fixed in working tree" without a commit
reference that actually fixes it. Third, if TDD traceability shows a
red-phase failure against current source, the triage may not claim the
corresponding code is compliant.

The example cited in the SKILL.md update is the v1.3.18 failure. The
triage claimed `VIRTIO_F_RING_RESET` was preserved in the whitelist.
BUGS.md claimed the corresponding bug was "fixed in working tree." TDD
traceability, however, showed the assertion
`assert "case VIRTIO_F_RING_RESET:" in func` failed on the current source.
All three statements cannot be simultaneously true. The executed result is
ground truth — the assertion ran against real bytes and reported what it
found. The gate would have caught the contradiction, forced the triage and
BUGS.md to be corrected, and left the bug in the open list where it
belonged.

The gate has a companion rule in `references/spec_audit.md`: an incomplete
council gate for enumeration checks. If the effective council is less than
3/3 — fewer than three spec auditors returned usable reports — and the run
includes any whitelist, enumeration, or dispatch-function checks or any
carried-forward seed checks, the audit may not conclude "no confirmed
defects" for those checks without executed mechanical proof. An incomplete
council with mechanical verification is acceptable. An incomplete council
relying on prose-only validation for code-presence claims is not. The
correct escalation is to mark the check "NEEDS VERIFICATION" and run the
mechanical extraction before closing. The rule exists because v1.3.18's
effective council was 1/3 and the single model's triage fabricated line
contents for enumeration claims. A mechanical artifact would have caught
the contradiction immediately.

## Self-Contained Iteration

Self-contained iteration is the largest single piece of new behavior in
v1.3.21. It turns the playbook from a one-shot tool into a convergent one.

The motivating observation is that a single playbook run explores a subset
of the codebase non-deterministically. In cross-version testing across
eight virtio-related repositories, 4/8 had bugs that were found in some
versions but not others — not because the bugs were fixed between runs,
but because the model explored different parts of the codebase each time.
A first run might find BUG-001 and BUG-004 and miss BUG-005. A second run
might find BUG-005 and BUG-006. No run individually is wrong; the union
is larger than any member. Without explicit machinery, each run discards
what the previous run learned.

Phase 0 — Prior Run Analysis — exists to prevent that discarding. The
phase runs automatically at the start of every playbook execution when
`previous_runs/` exists and contains prior quality artifacts. It has four
steps.

Step 0a builds the seed list. The skill reads `previous_runs/*/quality/BUGS.md`
from every prior run, extracts bug ID, file:line, summary, and the
regression test assertion for each confirmed bug, deduplicates by file:line
(the same bug found in multiple runs counts once), and writes the merged
list to `quality/SEED_CHECKS.md`.

Step 0b executes seed checks mechanically. For each seed, the skill runs
the assertion against the current source tree. A FAIL result means the
bug is still present; that seed becomes a confirmed carry-forward bug
that must appear in this run's BUGS.md regardless of whether any auditor
independently re-discovers it. A PASS result means the bug was fixed
since the prior run; it is recorded in PROGRESS.md as "SEED-NNN: resolved
since prior run." The word "mechanically" is load-bearing. Benchmark 26
verifies that every seed's assertion was actually re-executed against
current source — a seed marked FAIL without running the assertion is
non-conformant.

Step 0c identifies prior-run scope. The skill reads each prior
PROGRESS.md for its scope declaration and records which subsystems were
covered. Phase 1 exploration then prioritizes areas NOT covered by prior
runs, maximizing the chance of finding new bugs. If all subsystems were
covered in prior runs, Phase 1 explores the same scope but with different
emphasis — different scrutiny areas, different entry points.

Step 0d injects seeds into downstream phases. The seed list is pasted
into the code review prompt as "Prior runs confirmed these bugs — verify
they are still present and look for additional findings in the same
subsystems." It is also injected into `RUN_SPEC_AUDIT.md` with the
explicit framing: "Known open issues from prior runs: [seed list]. Expect
auditors to find these. If an auditor does NOT flag a known seed bug,
that is a coverage gap in their review, not evidence the bug was fixed."
This framing inverts the usual failure mode. Previously, silence from an
auditor was read as confirmation. Now, silence on a known seed is
evidence of under-inspection, not of repair.

After Phase 3, a convergence check runs. It compares the run's BUGS.md
against the seed list, counts net-new bugs (bugs not matched to any seed
by file:line), seed carryovers (seeds that FAIL'd in Step 0b), and seed
resolutions (seeds that PASS'd). The counts are written to a
`## Convergence` section in PROGRESS.md together with a CONVERGED or
NOT CONVERGED verdict. The convergence criterion is strict: net-new bugs
= 0. Benchmark 27 verifies the section exists and that the net-new count
matches the actual difference between BUGS.md and the seed list.

If the run is CONVERGED, the skill prints a summary and proceeds to
Phase 4. If it is NOT CONVERGED and the iteration counter has not
reached its maximum, the skill archives `quality/` into `previous_runs/`
with a timestamp, deletes `quality/` and `control_prompts/`, and restarts
from Phase 0. The newly archived run will be picked up as a prior run on
the next iteration, growing the seed list. The default maximum is five
iterations, overridable by the user prompt ("run the playbook with 3
iterations" or "single run").

Two safety valves exist. The iteration limit prevents infinite loops on
genuinely divergent codebases. The context-window awareness clause
instructs the skill to stop iterating and write state to PROGRESS.md if
it detects its output quality degrading across iterations — most
codebases converge in two or three iterations, so longer runs are
diagnostic rather than typical. A companion shell script, `run_iterate.sh`,
exists for shell-level orchestration when running outside the skill's
automatic path.

The phrase "self-contained" in the release title distinguishes this
mechanism from earlier external-script approaches. Prior versions of the
skill left iteration to the caller — an operator had to run the playbook,
read the convergence output, decide whether to re-run, and manage the
archive path manually. In v1.3.21 the skill owns the loop. A caller who
asks for a playbook run gets convergent bug discovery with no external
state and no additional invocations.

## Philosophical Continuity

v1.3.21 is not an origin point. It is the fourth installment in a thread
that starts with the v1.3.7 enforceable terminal gate and runs forward
into v1.5.0's divergence-based defect definition.

v1.3.7 was the release in which the skill's design character first became
visibly mechanical. The terminal gate acquired a named section in
PROGRESS.md. Metadata checks compared claimed values against the
filesystem. Regression tests were forced to align with the functional
test framework. In each case the skill stopped asking the agent to assert
a thing and started demanding that the assertion be written into a
specific, checkable location. The terminal gate was the first gate; the
metadata checks were the first cross-artifact comparison; both are
ancestors of the contradiction gate.

v1.3.21 extends the same move to a new level. The terminal gate asked
whether a value was written. The mechanical verification subsystem asks
whether a shell command produced that value. The contradiction gate
asks whether two artifacts agree about what the command produced. Each
step is the same kind of check — consult an artifact rather than trust
a narrative — applied to a narrower class of claim. The skill's
mechanical turn, which begins in v1.3.7, reaches a local maximum here.

It also sets up the next step. v1.5.0 reframes defects themselves as
divergence between spec and code, with the divergence measured rather
than judged. The v1.5.0 definition is only usable because v1.3.21 made
mechanical measurement routine. A spec audit that has to fall back on
an auditor's judgment about whether a switch handles a constant cannot
support divergence as a defect definition — the divergence would be
claimed, not measured. With `quality/mechanical/` in place, divergence
is a diff between a spec list and an extracted code list. Both sides
are artifacts. Either a constant is in both or it is not.

The seed-and-converge machinery in Phase 0 also anticipates later
releases. The idea that a playbook run is one sample from a distribution
of possible runs — and that convergence is measured by the distribution
itself stabilizing — becomes a recurring assumption in the skill's
later design. The per-run archive, the file:line dedup key, and the
explicit "silence from an auditor is a coverage gap, not a repair" rule
all survive into subsequent versions substantially unchanged.

## How It Fits Today

In v1.4.5, the mechanical-verification philosophy is core. Every
enumeration, whitelist, and dispatch check generates a
`quality/mechanical/` artifact as a matter of course. The integrity
check is part of the default Phase 3 benchmark pass. The contradiction
gate runs automatically before the terminal gate. The source-inspection
`run=False` ban is enforced by the test framework adapter, not by a
grep over test files.

In v1.5.0, the philosophy is expanded. Divergence-based defect detection
generalizes the "extract from code, compare against spec" pattern from
enumeration checks to arbitrary contracts. The
`quality/mechanical/` directory is widened to include extracted
specifications, not only extracted code, so both sides of the divergence
are evidence rather than claim. The contradiction gate grows a fourth
category — extracted spec vs. prose spec summary — and the gate's
execution becomes a separate phase rather than a sub-step of Phase 2d.

The self-contained iteration loop remains substantially as designed in
v1.3.21. The five-iteration default is unchanged. The Phase 0 seed-and-
inject pattern is used verbatim. The convergence criterion — net-new
bugs equal zero — is the same. v1.5.0 adds a secondary convergence
signal (divergence counts stabilize across runs) but retains the
v1.3.21 primary.

The benchmark count has continued to grow. v1.3.18 had 22. v1.3.21
shipped with 27. Each later minor version adds one or two more. The
benchmark list is, in a real sense, the skill's specification — the
set of checks that must pass for a run to be considered conformant —
and the growth rate is a reasonable proxy for the skill's maturation.
Three of the five benchmarks added in v1.3.21 (23, 25, 26) are still
among the most frequently tripped benchmarks in current production
runs, which is the expected outcome for checks that target real failure
modes rather than hypothetical ones.

## Provenance

- **Commit:** `169fc01562e9437726b573eb2699fdc27db5301a`
- **Author:** Andrew Stellman
- **Date:** 2026-04-11
- **Tag:** v1.3.21 (rolls up v1.3.19, v1.3.20, v1.3.21 internal increments)
- **Files changed:** README.md (+/-13), SKILL.md (+122/-4),
  references/defensive_patterns.md (+4/-0),
  references/spec_audit.md (+2/-0), references/verification.md (+29/-0)
- **Net:** 169 insertions, 18 deletions across 5 files
- **Self-check benchmarks:** 22 → 27
- **Co-author:** Claude Opus 4.6
