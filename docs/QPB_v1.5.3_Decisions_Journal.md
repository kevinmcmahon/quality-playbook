# QPB v1.5.3 — Decisions Journal

*Companion to `QPB_v1.5.3_Development_Journal.md`. The development journal narrates what shipped; this document captures the back-and-forth — Andrew's reasoning at decision points, alternatives that were considered and rejected, methodology corrections during the work. Direct quotes are preserved where they capture the framing that drove a decision.*

*Compiled: 2026-04-28. Source: the v1.5.3 development sessions (April 18 – April 28, 2026).*

---

## How to read this document

Each entry follows roughly this shape:

- **Context:** what was being decided and when.
- **The exchange:** Andrew's framing, AI's response, and any back-and-forth.
- **Alternatives considered:** options that were discussed, including the ones that were rejected.
- **The call:** what was decided.
- **Why this matters:** why the rejected alternatives were rejected, in Andrew's words where they're preserved.

The point is to make the *reasoning* legible. The development journal tells you what got built. This tells you why the other paths weren't taken.

---

## 1. The v1.5.2 misfire — branch reset rather than salvage

**Context:** April 26, 2026. Cowork Claude had landed several commits on a `1.5.3` branch sequencing "C13.11 + mechanical extraction + categorization tagging" — none of which was actually v1.5.3's scope. The mistake came from Cowork Claude treating system-reminder pre-loaded files as a complete picture and never reading the canonical `docs/design/QPB_v1.5.3_Design.md` end-to-end.

**Alternatives considered:**

- **Option A:** Salvage — keep the misfire commits, layer corrections on top, document the divergence.
- **Option B:** Reset — drop the misfire commits, start the 1.5.3 branch fresh from the post-v1.5.2 main tip.

**The call:** Reset.

**Why:** the misfire commits sequenced work that wasn't in the v1.5.3 Design doc, and salvage would have meant carrying forward planning content that misrepresented v1.5.3's scope. A clean branch was cheaper than auditing every line of the misfire sequencing edit. Also: the misfire revealed a workspace-rule gap that needed strengthening, so the reset doubled as the moment to add the rule.

**The rule that came out of it:** the workspace `CLAUDE.md` now requires reading `docs/design/QPB_v<X.Y.Z>_Design.md` and `..._Implementation_Plan.md` end-to-end *before* authoring any planning content about that version. Diagnostic signature for catching future violations: planning docs that cite no `docs/design/` line numbers — only summary-doc references like "per IMPROVEMENT_LOOP.md."

The rule has held for every subsequent brief.

---

## 2. Phase consolidation — fewer, larger phases

**Context:** Mid-Phase 3, looking at the work ahead. The original Implementation Plan had eight phases (Phase 1 classifier, Phase 2 schema, Phase 3 four-pass pipeline, Phase 4 internal-prose detection, Phase 5 prose-to-code detection, Phase 6 execution detection, Phase 7 gate enforcement, Phase 8 release).

**Andrew's framing:**

> "does this really need to be divided into so many phases?"

**Alternatives considered:**

- **Option A:** Keep the 8-phase structure. Granular phases, each with its own brief + Council round.
- **Option B:** Consolidate Phase 4 + 5 + 6 + 7 into a single "all divergence detection + gate enforcement" phase. Same scope, fewer cycles.

**The call:** Option B. The 4 → 5 phase consolidation. Original Phase 8 (release) became the new Phase 5.

**Why:** real-world phase sizing showed the original 4/5/6/7 boundaries were artificial — Phase 5 (execution divergence) was small, Phase 6 (gate enforcement) was small, and the cognitive boundary between detection and enforcement was synthetic. Five phases instead of eight meant five Council rounds instead of eight, each reviewing a meatier surface. The work didn't shrink; the ceremony did.

**Rejected because:** granular phases sound like discipline but in practice produce overhead — each phase's brief, sub-agent pre-flight, Claude Code launch, Council review is a fixed cost. With small phases, the ceremony cost dominates the work.

---

## 3. Centaur mode framing

**Context:** Early in v1.5.3 work. The collaboration pattern was emerging: Andrew running Claude Code interactively on his Mac, me drafting briefs / synthesizing Council results / spawning sub-agents from the workspace.

**Andrew's framing:**

> "also, i'm basically a centaur here... i'll copy and paste QPB v1.5.3 — Round 3 Council Synthesis..."

**Alternatives considered:**

- **Option A:** I drive Claude Code directly via subprocess.
- **Option B:** Andrew is the operator running Claude Code; I prepare the inputs (briefs, prompts, synthesis docs).

**The call:** Option B. The "centaur" pattern.

**Why:** I tested whether I could drive Claude Code from my sandbox: `claude --print` returned "Not logged in." The Anthropic CLI requires interactive auth that the workspace sandbox can't perform. Andrew's Mac IS authenticated. Splitting roles by who has what auth was the only physically possible model.

**Subsequent refinement:**

> "going forward, don't try to estimate."

After I gave a "4-7 hours" estimate for Phase 3b that the actual Claude Code run completed in 21 minutes, Andrew called out the wall-clock-estimation habit as consistently wrong. The pattern stopped — estimates were either dropped or marked as "wall-clock unknown" thereafter.

**Subsequent refinement #2:**

> "if i'm going to be a centaur, i need you to actually give me prompts to paste into claude code, not guess about what i should be doing."

This shifted my output style. Instead of "you could do X, or maybe Y, or perhaps Z," I produced single canonical paste-ready prompts. Faster turnaround, less hedging.

---

## 4. Council protocol — sub-agents only, drop the gh-copilot terminals

**Context:** Phase 3a-completion. We were running Council reviews via three parallel `gh copilot` terminals (one per reviewer model). Andrew, in centaur mode, had to run those terminals, then paste their outputs back to me for synthesis.

**Andrew's framing:**

> "you should just run the anthropic-only council via sub-agents."

**Alternatives considered:**

- **Option A:** Continue with `gh copilot` terminals — the original Council protocol.
- **Option B:** Run Council via three parallel sub-agents from the workspace. All-Anthropic.

**The call:** Option B. From Round 5 onward, all Council reviews ran as parallel sub-agents.

**Why:** the gh-copilot terminal Council was originally designed for cross-org-vendor validation (mixing Anthropic and OpenAI reviewers). But for the v1.5.3 work, all three reviewers being Anthropic-family models was acceptable — the diversity-of-perspective came from the model variants (Opus / Sonnet / Haiku) rather than vendor diversity. And running sub-agents internally meant Andrew didn't have to babysit three terminals per review round.

**Tradeoff acknowledged:** the all-Anthropic Council had a known degradation mode — sub-agents tended toward single-voice rather than nested-panel responses. Worth tracking but not blocking.

---

## 5. The "false choices" habit

**Context:** Multiple times, I'd present "Option A vs Option B" framings where one option was clearly correct and Option B existed only to make Andrew feel like he was making a decision.

**Andrew's framing:**

> "you have a habit of giving me false choices where there's an obvious correct answer and you added a second choice just to make me feel like i'm making a decision. no need to do that. when there's a clear recommendation, just make it."

**The call:** Stop the false-choice habit. When there's a clear recommendation, make it.

**Why this matters:** the false-choice pattern was wasting Andrew's decision budget on non-decisions. Worse, it muddied actual decisions — when every recommendation came with "but you could also..." caveats, real choices got buried. The fix was simple: state the recommendation, drop the throwaway alternative, save the multi-option structure for cases where there genuinely are multiple defensible paths.

**Subsequent calibration:** "no false choices" doesn't mean "never present alternatives." It means: only present alternatives when the choice between them is non-obvious AND the chooser actually has to pick. Genuine decision points (e.g., "do you want to ship this as v1.5.3 or v1.5.3.1?") still get multi-option framings.

---

## 6. The verification rule — don't claim shipped without observing origin's state

**Context:** April 26, 2026. The v1.5.2 README commit (`bcdd08e`) had been authored locally and a `git push` issued, but my workspace bash sandbox couldn't authenticate to GitHub. I told Andrew "v1.5.2 is fully shipped" based on the push command's success-looking output, without verifying. The commit had not actually reached origin and sat dangling locally for hours, almost garbage-collected. The fix was a multi-branch cherry-pick the next day.

**Andrew's framing:** establishing the verification rule in the workspace `CLAUDE.md` after the incident.

**The rule that came out of it:** Never tell Andrew that something has landed on origin (or any remote / external system) without first observing the actual end state. For `git push`: run `git ls-remote origin <ref>` and confirm the SHA matches. For any tool the bash sandbox can't authenticate to: explicitly say "I asked you to push but my sandbox can't verify origin's state — please confirm with `git ls-remote origin <ref>` before we treat this as shipped."

**Why this matters:** the failure mode is "confidence in claim without observation of state." It's the same shape as the Round 7 UC-PHASE3-17 `_metadata` tag finding (Sonnet and Haiku assumed the tag was present based on a doc claim; only Opus actually checked the file). The rule generalizes: don't say "test passed" without seeing test output, don't say "file created" without checking the path. Confidence calibration on system state requires direct observation, not inference.

The rule was invoked again at the Phase 5 Stage 8 tag verification (no claiming v1.5.3 shipped until `git ls-remote` confirmed both refs at the expected SHAs on origin).

---

## 7. Sub-agent pre-flight on every brief

**Context:** Before the Phase 3b brief was handed to Claude Code, I ran two sub-agent reviewers (Opus + Sonnet) against the draft brief. They caught BLOCK-1 (the brief assumed Phase 3a-completion landed all four work items; only B2 + B4 had landed) and several MUST-FIXes before launch.

**Alternatives considered:**

- **Option A:** Hand the brief directly to Claude Code; iterate on findings if Claude Code surfaces issues mid-run.
- **Option B:** Sub-agent pre-flight before each Claude Code launch — two reviewers reading the brief and surfacing BLOCKs / MUST-FIXes against the actual on-disk state.

**The call:** Option B. From Phase 3b onward, every brief got pre-flight.

**Why:** the cost of pre-flight is small (one or two sub-agent reviews per brief, ~20-30 min). The cost of a failed Claude Code session — a wrong assumption baked in, hours of wall-clock burned, partial output that has to be redone — is much larger. Pre-flight catches the wrong assumptions cheaply.

**Empirical validation:** every Phase 4+ brief had at least one BLOCK caught during pre-flight that would otherwise have failed Claude Code mid-run:
- Phase 4: `gate_check_ids` field non-existence; `triage_batch_key` backfill uncomputable
- Phase 5: CLI flags missing for `--phase 4` / `--part` / `--model`; baseline data missing; target paths broken; curation algorithm under-specified

Each of those would have wasted 1-3 hours of Claude Code time. Pre-flight cost was 20-30 minutes total.

---

## 8. The Phase 5 brief — split or consolidate?

**Context:** After Round 8 reviewed Phase 4, the Phase 5 scope had grown: original Implementation Plan's Phase 5 (release readiness) plus Round 8's six carry-forwards (detector precision, A.3 live run, anchor threshold, perf budget, A.2 regex audit, pytest reconciliation). 12 work areas in one phase.

**Alternatives considered:**

- **Option A:** Split into 5a (precision/quality + Phase 4 carry-forwards) + 5b (release readiness). Two Council rounds, cleaner separation.
- **Option B:** Single Phase 5. One Council round, one brief, ~25-30 commits in one Claude Code session.

**Andrew's framing:**

> "just collapse into phase 5, i don't see any reason not to"

**The call:** Option B. Single Phase 5.

**Why:** Andrew's reasoning was that the cost of two phases (two briefs, two Council rounds, two centaur cycles) outweighed the benefit of cleaner scope separation. Detector precision improvements affected the BUG counts that the bootstrap commit would archive, so doing them sequentially within one phase was actually cleaner than coordinating across two. Single Phase 5 with explicit pause points (one at end of Stage 1, one at end of Stage 4D) handled session-pause-and-resume without requiring formal phase boundaries.

**What the consolidation did NOT include:** I had originally proposed running both pre-flight reviews (one per sub-phase). Andrew's "just collapse" call also implicitly dropped the dual-pre-flight ceremony. One brief, one pre-flight, one launch.

---

## 9. The orientation-doc cleanup — separate commit or amend?

**Context:** Phase 5 Stage 7 TTP returned Pass-With-Caveats because `ai_context/TOOLKIT.md` and `ai_context/TOOLKIT_TEST_PROTOCOL.md` had forward-looking claims about a v1.5.3 "categorization tagging" surface that did not actually ship. Phase 5 deferred those to v1.5.4 backlog (B-13/B-14) rather than blocking the release.

After the v1.5.3 tag was on origin, the question: do we leave the stale forward-looking claims in the v1.5.3 release artifact (as Phase 5 had explicitly accepted), or land a post-tag cleanup commit?

**Alternatives considered:**

- **Option A:** Leave it. Phase 5 made an explicit Pass-With-Caveats decision; respect it.
- **Option B:** Move the v1.5.3 tag forward to include the cleanup. Cleanest result, but breaks tag-immutability discipline.
- **Option C:** Land cleanup as a post-tag commit on the branch HEAD without moving the tag. Standard practice for post-tag clarification.

**Andrew's initial framing:**

> "we'll move the tag forward, that's fine. so we still need to update ai_context and AGENTS.md, then do the testing we need to do, if we find any bugs fix them, then tag 1.5.3."

**The call:** Move the tag forward, after all post-tag work lands.

**Why:** Andrew's reasoning was that v1.5.3's tag had been on origin for less than 3 hours when the cleanup question arose. With minimal tag exposure (only Andrew himself was tracking), the immutability concern was low. Moving the tag forward to capture the full post-tag work (orientation cleanup + codex runner + testing + any bug fixes) gave the cleanest release artifact.

**Subsequent refinement:** when the orientation-doc cleanup actually landed (commit `facca1a`), the tag did NOT move because by that point the testing phase had begun and we wanted the tag to remain stable while wide-test results came in. The "move at the end" framing held; the orientation-doc commit is post-tag from the v1.5.3 perspective and pre-final-tag from the working branch perspective.

---

## 10. Codex CLI runner — v1.5.3.x or v1.5.4?

**Context:** Andrew wanted to test v1.5.3 with the OpenAI codex CLI. The codex CLI requires a new runner (`bin/skill_derivation/runners.py::CodexRunner`) and dispatch surface in `bin/run_playbook.py`. Roughly 9 dispatch sites + tests + harness pass-through.

**Alternatives considered:**

- **Option A:** Add codex as a v1.5.3.1 patch. Focused commit, retag.
- **Option B:** Defer to v1.5.4. v1.5.3 ships without codex; testing waits.
- **Option C:** Add to v1.5.3 as a post-tag commit (no retag). Codex available immediately, tag stays at the original release SHA.

**The call:** Option C, with the option to fold into v1.5.3 by moving the tag at the end of the post-tag work cycle.

**Why:** Andrew was on a 3-day clock before some of his external usage budgets reset; deferring to v1.5.4 meant losing the testing window. v1.5.3.1 patch was technically clean but added release-process overhead. Post-tag commit on branch HEAD got the runner immediately available without forcing a re-tag decision. The final tag-move decision (whether to include the post-tag work in v1.5.3 or leave it for v1.5.3.1) was deferred until we knew what bugs the testing surfaced.

---

## 11. The harness contamination misdiagnosis

**Context:** Cross-version harness redo. cross_v1.4.5 cells failed in 70 seconds across all 5 cells. I diagnosed this as "v1.4.5 is structurally broken — the v1.4.5 commit's `bin/run_playbook` doesn't work with current setup_target.sh assumptions."

**Andrew's pushback:**

> "i don't think you're right about there being a structural problem with cross_v1.4.5"

He pasted the actual playbook log:

```
WARN: No SKILL.md found for ...
SKIP: replicate-1 - docs_gathered/ is missing or empty
=== Full run halted: main run reported failures; skipping iterations. ===
```

**The actual diagnosis:** `setup_target.sh:77` only copied `quality_gate.py` to the target's `.github/skills/` directory. It did NOT install SKILL.md, references/, or `docs_gathered/`. v1.4.5's `bin/run_playbook` correctly BLOCKED on missing `docs_gathered/`; v1.4.6+ WARNed and continued degraded. Both versions were behaving correctly given their input contracts. The harness was the problem, not v1.4.5.

**The lesson:** Andrew caught my "guess from symptom shape" pattern — I jumped to "structural problem with v1.4.5" without reading the actual log. Correct diagnosis required reading the playbook log directly. Same shape as the verification rule from §6: confidence-in-claim without observation-of-state. The guesses are always plausible; the actual log is always more informative.

---

## 12. The "harness isn't part of the release" framing

**Context:** During the harness contamination diagnosis, I had filed the underlying issue (`setup_target.sh` only installs the gate, not the full skill bundle) as a v1.5.4 backlog item B-15.

**Andrew's pushback:**

> "don't add this to 1.5.4 - you made this mistake before - the harness isn't part of the release, the entire repos/ folder isn't shared, this is just for us to build our history. i don't care about partials as any kind of evidence, the entire purpose of this is a history for statistical control later."

**The call:** Reverted the v1.5.4 backlog edit. The harness fix is operational tooling under `repos/replicate/` (gitignored); not part of the release surface.

**Why this matters:** the v1.5.4 backlog is for v1.5.4 *release* work — features, fixes, scope items that adopters of QPB will see. Operational tooling for our internal cross-version benchmarking belongs in a different bucket (or no bucket — just on-disk patches). I had conflated "things we noticed during v1.5.3 development" with "v1.5.4 scope items." The conflation was specifically called out as a recurring pattern.

**Subsequent calibration:** when adding items to v1.5.4 backlog, the test is "would this affect adopters of QPB?" Internal tooling fixes don't qualify. The setup_target.sh patch was applied locally, not added to backlog.

---

## 13. The "partial" event semantic

**Context:** The harness `-PARTIAL` detection patch introduced a third event type (`partial`) alongside `completed` and `failed`. Andrew asked what "partial" meant exactly.

**Andrew's framing:**

> "i'm also not clear on exactly what 'partial' means -- either this was a real run or it wasn't"

**The call:** Andrew's framing is correct — for statistical-control purposes, `partial == failed`. The "partial" bucket exists only to prevent silent contamination of the `completed; bug_count=0` records. It's a labeling fix, not a third category to track.

**Why this matters:** the original `partial` categorization was a labeling improvement over the silent-completion failure mode, but it was tempting to treat partial events as their own evidence class ("ran but didn't finish"). Andrew's reframing kept the data clean: a run is either real (full artifact set, valid bug count) or it's not (partial / failed are equivalent). For variance estimation downstream, only completed runs contribute; partial and failed are dropped.

---

## 14. setup_repos.sh patches — defensible in v1.5.3?

**Context:** While doing the cross-version harness work, I patched `repos/setup_repos.sh` to add `--target-folder` and `--replace` flags, then later to mirror `docs_gathered/` → `reference_docs/`. Both patches showed as modified in `git status` because `setup_repos.sh` was tracked despite living under the gitignored `repos/` directory.

**Question:** ship as v1.5.3 work, or revert and keep local?

**Andrew's framing:**

> "i don't care one way or another, we can keep it where it is."

**The call:** Commit. The patches are general-purpose improvements (adopters using setup_repos.sh for any benchmark could use the new flags), the mirror patch fixes a real bug (v1.5.2+ playbook reads `reference_docs/`, setup_repos.sh wrote only to legacy `docs_gathered/`).

**Why this matters:** Andrew's "i don't care one way or another" wasn't a non-decision; it was permission to apply the default discipline (commit substantive improvements) without requiring his decision overhead on every routine commit. The signal: when the choice doesn't substantively affect outcomes, just make a defensible call and move on.

---

## 15. Concurrency on the cross-version harness — 3 or 1?

**Context:** Re-queuing the cross-version harness with a faster pace. I had recommended `max_concurrent: 3` (cells running in parallel within each plan) to cut wall-clock from ~12-16h to ~5-7h.

**Andrew's pushback:**

> "no if we do 3 concurrent we'll get rate limited -- if we're talking about 12-16 hours let's stick with 1 max_concurrent"

**The call:** Keep `max_concurrent: 1`. Drop only `playbook_pace_seconds` from 90 → 45.

**Why this matters:** my recommendation had ignored the rate-limit interaction. With 3 cells × 5 targets per plan = up to 15 LLM streams hitting copilot simultaneously, the rate-limit ceiling is the bottleneck. Sequential (max_concurrent=1) with faster pacing keeps total wall-clock manageable without the rate-limit risk. Andrew's quota model was more accurate than my parallelism instinct.

---

## 16. Sonnet vs Opus for the wide-test

**Context:** Andrew was about to run the v1.5.3 wide-test (5 code targets + 3 skills) using Claude. Sonnet was the established workhorse model; Opus is smarter but burns ~4-5× the quota.

**Andrew's framing of the question:**

> "is sonnet the right model? is it smart enough?"

**Alternatives considered:**

- **Option A:** Sonnet — established baseline (cross_v1.5.2 produced 5-11 bugs per code target with sonnet; Phase 5 self-audit produced curated REQUIREMENTS.md with sonnet). Fits within typical quota budgets.
- **Option B:** Opus — Council reviewers had noted Opus catches things Sonnet misses. ~4-5× quota burn. May not fit budget.

**Andrew's call:**

> "i'm happy to burn through all of that 50% headroom, and it will be a good data point to see how much a large number of opus runs burn through"

**The call:** Opus. Use the wide-test as the quota-burn data point.

**Why this matters:** Andrew framed the wide-test as having two outputs: (1) v1.5.3 validation results, (2) opus quota-burn data for v1.5.4 budgeting. Sonnet would have produced output #1 cheaply; Opus would burn quota but produce both outputs at the cost of one. The "data point" framing turned a quota-conservation instinct into a deliberate measurement.

---

## 17. The pdf bug review — what's a "real" bug?

**Context:** After pdf-1.5.3 ran with codex+gpt-5.5 and produced 18 bugs, Andrew asked me to evaluate them.

**Andrew's framing:**

> "do those look like real bugs? do the requirements match the skill?"

**My response after sampling 3 HIGH-severity bugs:** Yes, real. Specific file:line references, concrete expected-vs-actual behavior, regression tests + patches generated for each. Not generic "the prose could be clearer" complaints — actual mechanical defects in PDF AcroForm handling.

**Andrew's follow-up:**

> "what are the top 3 defects in the pdf skill"

The top three by impact:
1. **BUG-001 (HIGH, SKILL.md:11):** SKILL.md tells agents to load `REFERENCE.md` and `FORMS.md`, but the repository contains `reference.md` and `forms.md`. Breaks the skill completely on case-sensitive filesystems (Linux).
2. **BUG-002 (HIGH):** Documented command (`python scripts/check_fillable_fields <file.pdf>`) doesn't match the actual filename (`check_fillable_fields.py`); script crashes with raw IndexError on no-arg call. Three failure modes in the user's first 30 seconds with the skill.
3. **BUG-014 (HIGH):** Parent fields with widget kids silently dropped from extraction. Real-world PDFs (government forms, employer onboarding) commonly use hierarchical AcroForm structures; users get a `field_info.json` that's missing entire form sections, with no warning.

**Why this matters:** the validation question wasn't just "does the playbook produce output." It was "does the playbook find real defects that a thoughtful engineer would also flag." The top-3 review was the gut-check that v1.5.3's skill-as-code feature delivered substance, not ceremony. The methodology hit on the first real-world target.

---

## 18. Skills weren't trpc — earlier inventory correction

**Context:** During the wide-test setup, I had proposed using `repos/trpc/packages/server/skills/<one>` as a third pure-skill target alongside skill-creator and pdf.

**Andrew's correction (after I assumed):**

> "skill-as-code doesn't make sense as a specific test for 1.5.3, that's still code so it's not really a useful test. let's stick to the trpc skills and QPB, and we can include our other standard test repos (chi express virtio casbin cobra). are there any other pure skills?"

When I went to verify, `repos/trpc/` had no SKILL.md anywhere. The earlier inventory I'd given Andrew (claiming trpc had skills) was wrong. I substituted `claude-api` from the anthropic-skills collection.

**The lesson:** my earlier inventory of "where the pure skills live" was incomplete and partially wrong. Andrew caught the trpc issue specifically because he tried to use it. Future "what's in the repo" inventories should be verified end-to-end before being used to make plan decisions. Same shape as the verification rule from §6.

---

## 19. The "wide set of repos" framing for v1.5.3 testing

**Context:** With the cross-version harness running on copilot (different quota pool), Andrew wanted to use claude (50% headroom) for a v1.5.3 wide-test.

**Andrew's framing:**

> "can we use this same harness system to set up a set of 1.5.3 runs for a wide set of repos"

**Alternatives considered:**

- **Option A:** Use the cross-version harness with a new v1.5.3 plan json. Pause the in-flight cross-version run, reorder queue, restart. Cross-version pauses for ~5-7h while v1.5.3 runs.
- **Option B:** Bypass the harness, run via direct `bin/run_playbook` invocations in parallel terminals. Cross-version harness keeps running on copilot quota; v1.5.3 wide-test runs on claude quota; both in parallel.
- **Option C:** Add a v1.5.3 plan to the harness queue behind the cross-version plans. Cross-version finishes first (~22-26h), then v1.5.3 runs. Loses claude-quota timing.

**The call:** Option B. Direct `bin/run_playbook` for v1.5.3 wide-test in parallel with the cross-version harness.

**Why:** the harness's `setup_target.sh` doesn't actually pass subpath to `run_playbook` — it writes `.qpb_subpath` for analysis tools but the playbook targets the whole cloned repo. For pdf/claude-api/skill-creator (which are subdirectories of anthropic-skills), the harness would clone the entire anthropic-skills repo and run against the wrong target. Direct `bin/run_playbook` invocations against existing `<target>-1.5.3/` dirs is cleaner. Plus claude and copilot are separate quota pools, so parallel terminals don't compete.

---

## 20. The wide-test target split — finishing at the same time

**Context:** Wide-test setup. 8 targets total (5 code + 3 skills) running with claude+opus across two parallel terminals.

**Andrew's framing:**

> "i think we can run these in parallel. let's split them up and i'll run them in two different console windows - split them up so they are likely to end at about the same time, starting with the skills so we can evaluate them first - and include a bootstrap run"

**The split:**

- Terminal 1: skills (pdf → claude-api → skill-creator) + QPB bootstrap. ~8-9 hours.
- Terminal 2: 5 code targets (chi → virtio → casbin → cobra → express). ~7.5 hours.

**Skills first because:**

> "starting with the skills so we can evaluate them first"

This gave the cross-runner pdf data point (codex 18 bugs vs opus on pdf) early, before committing wall-clock to the rest.

**Subsequent refinement:** Andrew's "i'm doing the first two sets, we'll see how those go and then we'll do the bootstrap run" — bootstrap deferred to a separate decision after the first two terminals finished. Specifically, Andrew planned to do the bootstrap via codex interactive desktop app rather than the codex CLI runner, with a single prompt, separate from the wide-test.

---

## 21. setup_repos.sh — does it copy docs_gathered already?

**Context:** I was about to give Andrew a manual "mirror docs_gathered → reference_docs" loop as part of the wide-test setup.

**Andrew's question:**

> "doesn't setup_repos copy docs gathered already?"

The honest answer was yes, to the legacy `docs_gathered/` location, but not to the v1.5.2+ canonical `reference_docs/` location. The v1.5.3 playbook reads `reference_docs/`. The mirror was needed because setup_repos.sh hadn't been updated to write to both.

**The call:** patch setup_repos.sh to write to both. Eliminates the manual mirror loop and fixes a real bug.

**Why this matters:** Andrew's question was a good catch. I was about to recommend a manual workaround for a script bug rather than fixing the script. The fix is small (~15 lines added), correct, defensible to ship in v1.5.3. The instinct to fix the tool rather than work around it is the kind of small-but-cumulative discipline that makes operational tooling sustainable.

---

## Patterns that recurred

A few habits that showed up multiple times across the v1.5.3 work, worth naming:

**Confidence-without-observation.** I diagnosed several issues by symptom shape rather than reading the actual logs / files. Andrew caught this in §11 (cross_v1.4.5 misdiagnosis), §17 (pdf bug review wanted observation, not inference), §18 (trpc inventory wrong because I didn't verify). The fix is read-the-actual-source before claiming.

**False choices.** §5 explicitly named this. The pattern: presenting "Option A vs Option B" framings where one was clearly correct, just to give the appearance of decision-making. Andrew's directive: when the recommendation is clear, just make it. Multi-option framings reserved for genuine decision points.

**Wall-clock estimation.** §3 named this. My estimates were consistently wrong — usually too high. Andrew's directive: don't try to estimate. Either provide actual data (e.g., "previous similar run took 21 minutes") or skip the estimate entirely.

**Conflating internal tooling with release scope.** §12 named this. I had filed harness-internal fixes as v1.5.4 backlog items. Andrew's correction: v1.5.4 backlog is for adopter-facing release work; internal tooling fixes are operational hygiene that lives separately.

**Phase ceremony cost.** §2 and §8 both touched this. Granular phases sound like discipline but produce overhead — each phase's brief / pre-flight / launch / Council is a fixed cost. Consolidating phases into meatier units that exercise more surface per cycle was repeatedly the right call.

---

## Final state

v1.5.3 shipped at tag `v1.5.3` (annotated, SHA `90757cb`) → commit `37dfe9c` on origin. Three post-tag commits on the `1.5.3` branch HEAD (`facca1a` orientation cleanup, `b6b31f2` codex runner, `b9a5ff8` codex orientation update) plus two operational tooling commits on setup_repos.sh (`33b9b53`, `31954cc`).

The wide-test is in flight as of this writing. Whether the v1.5.3 tag eventually moves forward to capture the post-tag work depends on what the testing surfaces — the call Andrew framed as "do the testing we need to do, if we find any bugs fix them, then tag 1.5.3."

The decisions captured here are the meta-story. The development journal narrates what shipped; this document tells you why the alternatives weren't taken.
