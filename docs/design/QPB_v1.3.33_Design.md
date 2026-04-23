# QPB v1.3.33 Design Retrospective

**Version:** 1.3.33
**Status:** Shipped
**Date:** 2026-04-12
**Author:** Andrew Stellman
**Primary commits:**
- `0cc74f2` — "v1.3.33: unify artifact contract, fix language detection, add strictness modes"
- `46497fd` — "v1.3.33: apply council review fixes to canonical SKILL.md"

---

## What This Version Introduced

Quality Playbook v1.3.33 was the version in which the skill stopped
describing its outputs loosely and started enumerating them. Three changes
landed together under a single release label, each of them small in line
count and consequential in how the skill is reasoned about today.

The first and most durable change was the unified artifact contract. Until
v1.3.33, the artifacts a quality-playbook run was supposed to produce were
spread across prose in SKILL.md, assumptions baked into the terminal gate,
and hard-coded checks inside `quality_gate.sh`. Each of those three sources
held a slightly different opinion about what was mandatory, what was
optional, and where the file should live. v1.3.33 replaced that drift with
a single table — the "Complete Artifact Contract" — listing every artifact
the gate validates, its canonical path, whether it is required, and which
phase produces it. The table became the canonical registry that the gate,
the skill prose, and the autonomous runner all refer back to.

The second change was a language-detection fix in `quality_gate.sh`. The
previous implementation used `ls` with shell globbing to find source files
in the repo, and on projects where source was nested below the top level
— or where a build tree contained vendored copies of a different language
— the detection either missed the real language or picked the wrong one.
v1.3.33 replaced that heuristic with a `find`-based scan that honors a
depth limit and an explicit exclusion list for `vendor/`, `node_modules/`,
`.git/`, and `quality/`. It also added AGC (assembly) as a recognized
language with its own test harness mapping.

The third change was the introduction of strictness modes: `--benchmark`
(the default, used by the internal benchmark harness) and `--general` (a
relaxed profile intended for third-party projects). The modes change the
severity of three specific checks — triage evidence, integration sidecars,
and use case counts — so that projects with legitimate reasons to skip a
given artifact can still pass the gate without either lying to it or
failing it outright.

A follow-up commit, `46497fd`, landed three-quarters of an hour later. It
applied the same three changes to the canonical `SKILL.md` — the
1,494-line file that `setup_repos.sh` actually deploys — after the initial
commit had mistakenly edited a stale 561-line copy in the benchmark
harness. The two-commit shape is itself part of the story of this
release.

## Why It Was Needed

Three pressures converged on v1.3.32 and forced the v1.3.33 rework.

The first was artifact drift. The quality gate had grown by accretion over
the preceding two months. Each new release added one or two new checks to
`quality_gate.sh`, often to catch a failure mode observed in the previous
benchmark run. Each check implicitly declared that some artifact was
mandatory. But the corresponding SKILL.md prose was written at a different
time, often by a different AI collaborator, and there was no single place
a reviewer could go to ask "what is this skill supposed to produce?" When
the v1.3.32 council review was convened, one of its P0 findings was that
the gate and the skill had diverged on the question of which sidecar JSON
files were required and when. The fix was not to pick a side but to write
the contract down.

The second pressure was language detection. The older `ls`-glob approach
had worked adequately on the benchmark repos because they are small,
single-language, and flat. It started breaking once the skill was run on
real codebases with vendor trees, multi-language monorepos, and Go
projects that contained a small Python tooling directory. In one
benchmark run, a Rust project was classified as C because a vendored C
dependency had shallower-path source files than the project's own
`src/*.rs`. The detection logic was also silently broken on shells that
did not have `globstar` enabled — the `**/*.go` pattern there returned
literal `**/*.go` rather than matching files. The symptom was a false
positive "test_functional.py does not match project language" message on
a Go project; the root cause was that no language had been detected at
all. Replacing the glob with `find` closed both problems.

The third pressure was the all-or-nothing gate. The benchmark harness was
designed to be strict — it was supposed to fail a run that lacked triage
evidence or integration results. But the same script was being copied into
every deployed repository under `.github/skills/quality_gate.sh` so that
end users could validate their own runs. For end users, a failed triage
probe or a missing integration sidecar is often a reasonable choice —
their project may not have a triage story, or integration may not be
runnable on their CI. The strict gate was telling them their run was
broken when it was simply different. A relaxed profile was needed.
Treating every severity ceiling as absolute was both false and
discouraging.

## The Unified Artifact Contract

The contract is a Markdown table inserted into `SKILL.md` immediately
after the "two critical deliverables" paragraph. It lists twenty-three
artifacts. For each it records location, required status, and producing
phase. The required column has three values: "Yes", "If bugs found", and
"Optional". A fourth implicit value — "Yes (benchmark)" — appears on two
entries and is how the strictness distinction is communicated at the
contract level.

The contract's guarantee is simple and almost tautological: if the gate
checks for an artifact, the artifact must appear in the contract, and if
the contract lists an artifact, the skill must instruct its creation.
There is no artifact that the gate checks in silence, and there is no
instruction in the skill that produces an artifact the gate ignores. Both
halves of that guarantee had been violated before v1.3.33.

Two entries deserve individual mention because they had been the source
of ongoing confusion. `quality/results/tdd-results.json` and
`quality/results/integration-results.json` are the two structured sidecar
files the skill produces. Their required-status was ambiguous in v1.3.32:
the gate failed a run that had confirmed bugs but no TDD sidecar, and
warned on a missing integration sidecar, but the skill prose suggested
both were unconditional. The contract resolves this. The TDD sidecar is
"If bugs found" — no bugs means no TDD run to record. The integration
sidecar is "When integration tests run" — gated on whether the protocol
actually executed, not on whether it was generated.

The contract is accompanied by two canonical JSON examples — a full
`tdd-results.json` and a full `integration-results.json` — with field
values drawn from a real benchmark project. Each example is followed by a
sentence listing the allowed enumerated values: `verdict` must be one of
five strings, `recommendation` must be one of three, and `date` must be
ISO 8601. Those constraints are what the gate enforces, and writing them
next to the example means an agent generating the file can see the
contract and the example side by side.

A third note accompanies the contract: the sidecar lifecycle rule. Write
all bug writeups before finalizing `tdd-results.json`, because the
sidecar's `writeup_path` field must point to an existing file, not a
placeholder. Run integration tests and collect results before writing
`integration-results.json`. These are not new constraints — the gate had
been enforcing them since v1.3.27 — but they had never been stated
explicitly in the skill. Writing them down was half the work.

One subtler effect of the contract is that it made the skill's phase
model legible. The "Created In" column lists Phase 2, Phase 2b, Phase 2c,
Phase 2d, or "Throughout" for each artifact. Before the contract, an
agent reading SKILL.md could tell which phase a particular artifact was
discussed in but not where in the overall sequence it should be
produced. The contract's column orders the phases implicitly: Phase 2
produces the broad-spec and protocol files, Phase 2b produces bug
artifacts and code review reports, Phase 2c produces spec audits and
triage probes, and Phase 2d produces the completeness report and the
sidecar JSONs that depend on everything preceding them. The "Throughout"
entry — reserved for `quality/PROGRESS.md` — is the single exception, and
its presence in the contract table makes that exception obvious rather
than ambient.

A final design choice worth noting: the contract is expressed as a
Markdown table rather than as machine-readable YAML or JSON. The decision
was deliberate. The contract is read by agents generating content; it is
not parsed by the gate. The gate has its own hard-coded list of checks,
and the contract exists to keep those checks legible and
cross-referenceable, not to drive them. A machine-readable contract would
have introduced a second source of truth — the gate would either parse
the table (adding code complexity) or duplicate it (reintroducing the
drift the contract was created to eliminate). A Markdown table read by
agents and reviewers turned out to be the right unit of contract for a
skill whose users are language models.

## Language Detection Fix

The fix is a straightforward substitution in `quality_gate.sh`. The
eleven lines of `ls`-glob detection were replaced with nine lines of
`find`-based detection plus one new language (`agc`) and one new test
harness mapping.

The old approach looked like this for each candidate language:

```bash
elif ls "${repo_dir}"/*.py "${repo_dir}"/**/*.py 2>/dev/null | head -1 | grep -q . ; then
    detected_lang="py"
```

The `**/*.py` pattern requires `globstar` to be enabled, which is a
bash-only option and not default even there. On `/bin/sh`, on macOS's
default bash, and in CI containers using dash, the glob returns the
literal pattern. The `head -1 | grep -q .` idiom then passes vacuously on
the literal string, producing a false positive. Or the pattern silently
matches nothing and the next `elif` gets its turn with a different
language, which is how a Rust project got classified as C.

The replacement uses `find` with three guardrails: a `-maxdepth 3` limit
to keep the scan cheap, an explicit exclusion list for directories that
are not part of the project (`vendor/`, `node_modules/`, `.git/`,
`quality/`), and `-print -quit` to bail out on the first match. The
exclusion list matters particularly for Go and Rust, where vendored C
dependencies are common and would otherwise poison detection.

```bash
find_exclude="-not -path '*/vendor/*' -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/quality/*'"
if eval "find '${repo_dir}' -maxdepth 3 ${find_exclude} -name '*.go' -print -quit" | grep -q .; then
    detected_lang="go"
```

The fix also added AGC — the Apollo Guidance Computer assembly language
used in one of the benchmark repositories — as a detected language with
its test harness extensions set to `py sh`, since AGC code can only be
exercised via an external simulator driven from Python or shell. The AGC
case is also the template for future additions: an assembly or DSL
project cannot have tests "in its own language," so the valid-extension
table for that language lists the harness languages instead.

A related change in the same commit extended the test-file-extension
check to cover `test_regression.*` in addition to `test_functional.*`.
The older check validated only the functional test, on the theory that if
a run had generated test_functional.py on a Go project, the regression
test would almost certainly be wrong too. The new check removes the
reliance on that theory and validates both files independently.

The valid-extension table itself also expanded. The existing languages
retained their existing mappings — Go accepts `.go`, Python accepts `.py`,
Java accepts `.java`, Kotlin accepts `.kt`, Rust accepts `.rs`,
TypeScript accepts `.ts` and `.js` (since a TS project may compile to JS
for its tests), JavaScript accepts the same pair, Scala accepts `.scala`,
and C accepts `.c`, `.py`, and `.sh` because C projects commonly use
Python or shell-driven test harnesses. AGC joined the list with `.py`
and `.sh` for the same reason. The pattern — assembly and lower-level
languages accept higher-level harness languages — is now the template
for adding any future non-testable-in-itself language.

A final observation about the detection logic: it uses `eval` to run the
`find` command, because the exclusion list is assembled as a single
string rather than an array. `eval` is a security concern in general, but
the only interpolated value is `${repo_dir}` which is already controlled
by the caller, and the exclusion list is a literal string. The choice was
made to keep the detection compact — nine lines instead of thirty — at
the cost of a construct that would need to be revisited if the gate ever
accepted untrusted input.

## Strictness Modes

The strictness-modes feature is implemented as a single global variable,
`STRICTNESS`, that defaults to `"benchmark"` and can be switched to
`"general"` by passing `--general`. The flag also accepts `--benchmark`
explicitly, which makes the default selectable for clarity. The
`STRICTNESS` value is then consulted at three specific decision points
inside `check_repo`.

The first decision point is triage evidence. Triage probes
(`spec_audits/triage_probes.sh`) and the probe-assertion form inside
`mechanical/verify.sh` are the two ways a run can demonstrate that its
bug triage produced executable evidence rather than a narrative
summary. In benchmark mode, a run with no triage evidence fails the
gate. In general mode, the same finding is a warning. The rationale is
that benchmark projects are expected to exercise the full triage
pipeline as part of the skill's evaluation; user projects may reasonably
defer triage or omit it entirely.

The second decision point is the integration sidecar. In benchmark
mode, a missing `integration-results.json` is a warning (the gate still
passes). In general mode, it is an informational message. The pattern
is the same — the stricter profile treats absence as notable, the
relaxed profile treats it as expected.

The third decision point is the use-case count threshold, and it is
the most interesting of the three because it combines strictness with
size awareness. The gate counts source files in the repository using
the same find-based scan as the language detection. If the count is
less than five, the threshold drops from five use cases to three. On
top of that, in benchmark mode a shortfall is a hard fail; in general
mode, it is a warning. The size-aware threshold is the acknowledgement
that a real three-file library may legitimately have only three
discrete user-facing outcomes, and demanding five from it was
forcing the agent to either fabricate use cases or fail the gate. The
strictness dimension is independent: even on a small project, the
benchmark harness wants the threshold enforced strictly.

The gate's opening banner was updated to print the strictness value
alongside the version, which turned out to be important for
reproducibility. Benchmark logs from v1.3.33 forward record whether a
run was strict or relaxed, which means a failure can be matched against
the right threshold later.

A question considered but rejected during the design: should strictness
be a richer axis — perhaps three levels, or per-check configuration via
a JSON file? The two-level answer was chosen because the cases that
actually came up in practice were bimodal. The benchmark harness wanted
every check strict. End users wanted the three specific checks
(triage, integration, UC count) relaxed and the rest kept strict. There
was no observed use case for a "strict triage, relaxed UC count"
configuration or vice versa. Adding a config file would have created
surface area without solving any problem that had been reported.

A related design note: strictness is a gate-level concern, not a
skill-level concern. The skill itself does not know which mode it is
running under. It always produces every artifact it can produce and
instructs agents toward the strict path. The gate is the only place
the `--general` relaxation takes effect. This separation keeps the
skill's instructions consistent across benchmark and user contexts —
the skill does not try to produce a different shape of output based on
where it thinks it is running. The gate then accepts or rejects that
output according to the profile it was invoked with.

## The Council Review Cycle

v1.3.33 had a two-commit landing. The first commit, `0cc74f2`, applied
every substantive change — `quality_gate.sh`, `create_clean_repos.sh`,
and what its author believed to be `SKILL.md`. Forty-nine minutes later,
the second commit, `46497fd`, applied the same SKILL.md changes to the
file that `setup_repos.sh` actually deploys.

The first commit's SKILL.md edit had gone to a stale 561-line copy in
the benchmark subdirectory `quality-playbook-benchmark/`. That copy had
been kept in sync with the canonical file by hand for several releases,
and drift had accumulated — by v1.3.32 it was hundreds of lines behind
and was no longer the file the skill-installer deployed. The author
edited the wrong file because both files existed, both were named
`SKILL.md`, and grep-based navigation surfaced the stale copy first. The
gate script and the manifest loader were fine; the user-facing skill
definition was stale.

The fix in `46497fd` did three things. It applied the v1.3.33 SKILL.md
content — version stamp, artifact contract, sidecar examples,
autonomous fallback, size-aware UC threshold — to the canonical
`SKILL.md`. It replaced the duplicate under `.github/skills/SKILL.md`
with a symbolic link back to the canonical file. And it replaced the
duplicate `.github/skills/references/` directory with a symbolic link
to the canonical `references/` directory, after syncing four files
that had drifted. The symbolic links are the key insight: the next
time someone edits the canonical file, the deployed copy follows
automatically, and the drift class that caused this release's two-commit
landing is structurally eliminated.

The two-commit shape also illustrates the council review discipline the
skill has adopted for major changes. v1.3.32's council review surfaced
the P0 and P1 findings that drove v1.3.33's substantive work. v1.3.33's
own council review — conducted between `0cc74f2` and `46497fd` — was
what caught the wrong-file edit. Council review has become an expected
step after a substantive commit, not a pre-merge check. The commit lands,
a council of AI reviewers assesses it, and a follow-up commit (or a
decision to defer) closes the loop. The discipline does not prevent
mistakes; it catches them inside the same release.

## How It Fits Today

The three v1.3.33 changes have aged well.

The unified artifact contract persists intact through v1.4.5 and v1.5.0.
Each subsequent release has added entries to it — `COMPLETENESS_REPORT.md`
was promoted from optional to required in v1.3.40, the mechanical
verification receipt pair (`mechanical-verify.log` and `.exit`) was added
in the same release, and the contract is the first section the gate and
the skill prose both reference. New gate checks are written by first
adding a row to the contract table and then writing the check against it;
new skill instructions are written by finding the row in the contract
table first and then writing the instruction to produce the artifact
listed there. The contract has become the skill's spine.

The strictness modes are still used. The benchmark runner still defaults
to `--benchmark`, and the deployed `.github/skills/quality_gate.sh` still
recognizes `--general`. The set of checks that are tuned by strictness has
grown — v1.4.0 added completeness-report strictness, v1.4.3 added a
relaxed profile for the metadata consistency pass — but the mechanism is
the same single `STRICTNESS` variable consulted at specific decision
points inside `check_repo`. No third profile has been needed.

The language-detection fix has needed no further revision. AGC remains
the only exotic language in the detection list; new mainstream languages
(Swift was considered for v1.4.2) can be added by appending a find clause
and a valid-extension mapping. The size-aware UC threshold that rode in
with this release has been tuned once — v1.4.0 raised the "small"
boundary from five source files to seven — but its shape is the same
pair of inequalities introduced in v1.3.33.

The two-commit landing pattern has been repeated four times since.
Releases v1.3.40, v1.4.0, v1.4.5, and v1.5.0 all shipped a substantive
first commit and a council-review fix commit within a few hours. The
symbolic-link structure put in place by `46497fd` means that subsequent
releases no longer risk the particular wrong-file drift that prompted
it; later follow-ups have targeted content issues, not deployment issues.

## Provenance

**Primary commits:**
- `0cc74f2` — "v1.3.33: unify artifact contract, fix language detection, add strictness modes" (2026-04-12 12:53:05 -0400). Touches `repos/quality_gate.sh` (+92 lines, gross) and `repos/create_clean_repos.sh` (+212 lines, refactor to manifest-driven loader).
- `46497fd` — "v1.3.33: apply council review fixes to canonical SKILL.md" (2026-04-12 13:22:28 -0400). Touches `SKILL.md` (+87 / −6), adds symbolic links under `.github/skills/`, and syncs four drifted reference files.

**Net SKILL.md changes landed in v1.3.33:** version bump from 1.3.32 to
1.3.33 in metadata, banner, attribution stamps, and sidecar examples; the
Complete Artifact Contract table; two canonical sidecar JSON examples
with field-value constraints; the Step 0 autonomous fallback paragraph
for benchmark and single-pass mode; and the revised size-aware
use-case-count instruction under the Phase 3 verification section.

**Net `quality_gate.sh` changes landed in v1.3.33:** find-based language
detection replacing ls-glob; AGC language and test-harness mapping;
regression test file extension validation; `--benchmark` / `--general`
strictness flag handling; size-aware UC threshold computation; strictness
banner line in the gate's startup output.

**Council review outcome:** P0 and P1 items from the v1.3.32 review were
addressed by `0cc74f2`. The v1.3.33 review itself surfaced the stale-file
error that `46497fd` corrected and recommended the symbolic-link
structure that `46497fd` introduced.
