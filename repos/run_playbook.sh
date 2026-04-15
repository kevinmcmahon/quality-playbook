#!/bin/bash
# Generate quality artifacts for benchmark repos.
#
# Default: run all phases (1–6) in a single prompt (simulates a fresh Copilot/Claude run).
#
#   ./run_playbook.sh virtio chi httpx gson
#
# Phase-by-phase mode runs each phase as a separate CLI invocation with a clean context
# window and exit gates between phases. Use --phase to select:
#
#   ./run_playbook.sh --phase all virtio               # all 6 phases, one at a time
#   ./run_playbook.sh --phase 1 virtio                 # exploration only
#   ./run_playbook.sh --phase 3 virtio                 # code review only (requires phases 1-2 done)
#
# Phases:
#   1  Explore the codebase → quality/EXPLORATION.md
#   2  Generate quality artifacts → REQUIREMENTS.md, QUALITY.md, tests, protocols
#   3  Code review + regression tests → BUGS.md, patches/
#   4  Spec audit + triage → spec_audits/, triage_probes.sh
#   5  Reconciliation + TDD → writeups/, tdd-results.json, red/green logs
#   6  Verification → quality_gate.sh, phase6-verification.log
#
# Usage:
#   ./run_playbook.sh virtio chi httpx gson              # defaults: all phases, single prompt
#   ./run_playbook.sh --phase all virtio chi             # all phases, one at a time with gates
#   ./run_playbook.sh --phase 1 virtio                   # phase 1 only
#   ./run_playbook.sh --phase 3,4,5 virtio               # phases 3 through 5
#   ./run_playbook.sh --sequential virtio chi             # one repo at a time
#   ./run_playbook.sh --claude --model opus virtio        # Claude CLI instead of Copilot
#   ./run_playbook.sh --next-iteration virtio chi         # iterate on existing quality/ run
#   ./run_playbook.sh --next-iteration --strategy unfiltered virtio  # unfiltered iteration
#
# Options:
#   --parallel       Run all repos concurrently (default: on)
#   --sequential     Run repos one after another
#   --claude         Use claude -p instead of gh copilot
#   --copilot        Use gh copilot (default)
#   --no-seeds       Skip Phase 0/0b (default: on — clean benchmark)
#   --with-seeds     Allow Phase 0/0b seed injection from prior/sibling runs
#   --phase PHASES   Run specific phase(s): 1-6, "all" (phases 1-6 sequentially with gates),
#                    or comma-separated (e.g., "3,4,5"). Omit for single-prompt mode.
#   --next-iteration Iterate on an existing quality/ run (no archive, builds on it)
#   --strategy STR   Iteration strategy: gap (default), unfiltered, parity, adversarial, all
#   --model MODEL    Model (claude: opus, sonnet, …; copilot: gpt-5.4, …)
#   --kill           Kill processes from the current/last parallel run
#
# Environment:
#   QPB_MODEL — Copilot model (default: gpt-5.4; overridden by --model)

set -uo pipefail
source "$(dirname "$0")/_benchmark_lib.sh"

PID_FILE="${SCRIPT_DIR}/.run_pids"

# Defaults: match a typical “open repo in VS Code, one Copilot prompt, full playbook” run.
PARALLEL=true
RUNNER=”copilot”  # “copilot” or “claude”
NO_SEEDS=true     # clean benchmark — skip Phase 0 / sibling seeds
PHASE_MODE=””     # “”: single-prompt; “all”: phases 1-6 sequentially; “1,3,4”: specific phases
NEXT_ITERATION=false  # iterate on existing quality/ run
ITER_STRATEGY=”gap”   # iteration strategy: gap, unfiltered, parity, adversarial, all
CLAUDE_MODEL=””
REPO_NAMES=()
EXPECT_MODEL=false
EXPECT_STRATEGY=false
EXPECT_PHASE=false
for arg in “$@”; do
    if [ “$EXPECT_MODEL” = true ]; then
        CLAUDE_MODEL=”$arg”
        EXPECT_MODEL=false
        continue
    fi
    if [ “$EXPECT_STRATEGY” = true ]; then
        ITER_STRATEGY=”$arg”
        EXPECT_STRATEGY=false
        continue
    fi
    if [ “$EXPECT_PHASE” = true ]; then
        PHASE_MODE=”$arg”
        EXPECT_PHASE=false
        continue
    fi
    case “$arg” in
        --parallel)         PARALLEL=true ;;
        --sequential)       PARALLEL=false ;;
        --claude)           RUNNER=”claude” ;;
        --copilot)          RUNNER=”copilot” ;;
        --no-seeds)         NO_SEEDS=true ;;
        --with-seeds)       NO_SEEDS=false ;;
        --phase)            EXPECT_PHASE=true ;;
        --single-pass)      PHASE_MODE=”” ;;  # back-compat
        --multi-pass)       PHASE_MODE=”all” ;;  # back-compat
        --next-iteration)   NEXT_ITERATION=true ;;
        --strategy)         EXPECT_STRATEGY=true ;;
        --model)            EXPECT_MODEL=true ;;
        --kill)
            if [ -f “$PID_FILE” ]; then
                echo “Killing PIDs from $PID_FILE:”
                while read -r pid repo; do
                    if kill -0 “$pid” 2>/dev/null; then
                        echo “  kill $pid [$repo]”
                        kill “$pid” 2>/dev/null
                        # Also kill any child claude processes
                        pkill -P “$pid” 2>/dev/null
                    else
                        echo “  $pid [$repo] — already exited”
                    fi
                done < “$PID_FILE”
                rm -f “$PID_FILE”
            else
                echo “No PID file found. Falling back to pkill:”
                pkill -f “claude -p” && echo “  Killed claude -p processes” || echo “  No claude -p processes found”
            fi
            exit 0
            ;;
        *)           REPO_NAMES+=(“$arg”) ;;
    esac
done

# --model overrides QPB_MODEL for copilot
[ -n “$CLAUDE_MODEL” ] && [ “$RUNNER” = “copilot” ] && MODEL=”$CLAUDE_MODEL”

# --next-iteration is not compatible with --phase (iteration uses its own single prompt)
if [ “$NEXT_ITERATION” = true ] && [ -n “$PHASE_MODE” ]; then
    echo “ERROR: --next-iteration is not compatible with --phase. Iteration uses a single prompt.”
    exit 1
fi

# Validate --phase
if [ -n “$PHASE_MODE” ] && [ “$PHASE_MODE” != “all” ]; then
    # Validate comma-separated phase numbers
    IFS=',' read -ra _phases <<< “$PHASE_MODE”
    for p in “${_phases[@]}”; do
        case “$p” in
            1|2|3|4|5|6) ;;
            *) echo “ERROR: Invalid phase '${p}'. Must be 1-6 or 'all'.”; exit 1 ;;
        esac
    done
fi

# Validate --strategy
case “$ITER_STRATEGY” in
    gap|unfiltered|parity|adversarial|all) ;;
    *) echo “ERROR: Unknown strategy '${ITER_STRATEGY}'. Must be one of: gap, unfiltered, parity, adversarial, all”; exit 1 ;;
esac

# --strategy without --next-iteration is a no-op but warn
if [ “$NEXT_ITERATION” = false ] && [ “$ITER_STRATEGY” != “gap” ]; then
    echo “WARNING: --strategy is ignored without --next-iteration”
fi

VERSION=$(detect_skill_version)
[ -z "$VERSION" ] && echo "ERROR: Can't detect version from SKILL.md" && exit 1

if [ "$RUNNER" = "copilot" ]; then
    require_copilot
else
    if ! command -v claude &>/dev/null; then
        echo "ERROR: 'claude' CLI not found. Install from https://docs.anthropic.com/claude-code"
        exit 1
    fi
fi

REPO_DIRS=()
while IFS= read -r line; do
    [ -n "$line" ] && REPO_DIRS+=("$line")
done < <(resolve_repos "$VERSION" "${REPO_NAMES[@]}")
[ ${#REPO_DIRS[@]} -eq 0 ] && echo "ERROR: No repos found." && exit 1

# One timestamp per script invocation so parallel children agree on log paths with the parent.
export RUN_TIMESTAMP=$(date '+%Y%m%d-%H%M%S')

# Show the installed skill version from the first resolved repo (more accurate than root SKILL.md)
DISPLAY_VERSION="$VERSION"
if [ ${#REPO_DIRS[@]} -gt 0 ]; then
    _repo_ver=$(detect_repo_skill_version "${REPO_DIRS[0]}")
    [ -n "$_repo_ver" ] && DISPLAY_VERSION="$_repo_ver"
fi

echo "=== Quality Playbook — Artifact Generation ==="
echo "Version:  ${DISPLAY_VERSION}"
echo "Runner:   ${RUNNER}"
if [ "$RUNNER" = "copilot" ]; then
    echo "Model:    ${MODEL}"
elif [ -n "$CLAUDE_MODEL" ]; then
    echo "Model:    ${CLAUDE_MODEL}"
else
    echo "Model:    (default)"
fi
echo "No seeds: ${NO_SEEDS}  (Phase 0/0b skipped when true)"
echo "Parallel: ${PARALLEL}"
if [ "$NEXT_ITERATION" = true ]; then
    echo "Mode:     next-iteration (strategy: ${ITER_STRATEGY}, builds on existing quality/)"
elif [ -n "$PHASE_MODE" ]; then
    echo "Mode:     phase-by-phase (${PHASE_MODE}) — separate session per phase with exit gates"
else
    echo "Mode:     single-prompt (all phases in one session)"
fi
echo "Repos:    ${REPO_DIRS[*]##*/}"
echo ""
echo "=== Runner logs (one file per repo — names include this run's RUN_TIMESTAMP) ==="
echo "Each file gets the full prompt and exact shell command before the tool runs."
if [ "$RUNNER" = "claude" ]; then
    echo "For Claude: live output goes to the output.txt file via script(1). The runner log gets a copy after the run."
else
    echo "For Copilot: stdout is streamed into the runner log via tee."
fi
_screen_logs=()
for repo_dir in "${REPO_DIRS[@]}"; do
    _tail_name=$(basename "$repo_dir")
    _log_path="${SCRIPT_DIR}/${_tail_name}-playbook-${RUN_TIMESTAMP}.log"
    if [ "$RUNNER" = "claude" ]; then
        # For Claude, live output is in the output.txt file written by script(1)
        _live_path="${repo_dir}/control_prompts/playbook_run.output.txt"
        _screen_logs+=("$_live_path")
        echo "tail -f $(printf '%q' "$_live_path")"
    else
        _screen_logs+=("$_log_path")
        echo "tail -f $(printf '%q' "$_log_path")"
    fi
done
if [ -z "$PHASE_MODE" ] && [ "$RUNNER" = "copilot" ]; then
    echo ""
    echo "=== Single-pass Copilot raw transcript per repo (canonical live stream before tee-to-runner-log; still written for reference) ==="
    for repo_dir in "${REPO_DIRS[@]}"; do
        echo "tail -f $(printf '%q' "${repo_dir}/control_prompts/playbook_run.output.txt")"
    done
fi
_screen_session="qpb-${RUN_TIMESTAMP}"
# macOS /usr/bin/screen errors with "$TERM too long - sorry." when TERM exceeds a small limit
# (e.g. some IDE terminals). Force a short TERM for the whole chain.
_qpb_screen_term="${QPB_SCREEN_TERM:-xterm}"
_screen_one="( export TERM=$(printf '%q' "$_qpb_screen_term"); "
_screen_one+=$(printf 'screen -dmS %q tail -f %q' "$_screen_session" "${_screen_logs[0]}")
for ((i = 1; i < ${#_screen_logs[@]}; i++)); do
    _screen_one+=$(printf ' && screen -S %q -X screen tail -f %q' "$_screen_session" "${_screen_logs[$i]}")
done
_screen_one+=$(printf ' && screen -r %q' "$_screen_session")
_screen_one+=" )"
echo ""
echo "=== One command: Screen (one window per repo — Ctrl-a n / Ctrl-a p to cycle; Ctrl-a d to detach) ==="
echo "${_screen_one}"
echo "Override TERM for Screen only: QPB_SCREEN_TERM=xterm-256color ./run_playbook.sh ..."
echo "If that session name is already in use: screen -S $(printf '%q' "$_screen_session") -X quit"
echo "Fewer panes: run fewer repo names, or remove one or more \"&& screen -S ... -X screen ...\" segments from the line above."
echo "Interleaved in one terminal (no Screen): tail -f $(printf '%q ' "${_screen_logs[@]}")"
echo ""

# ── Run a single prompt against a repo ──
# log_file: repo-level runner log (append command + full prompt before each exec)
run_prompt() {
    local repo_dir="$1" prompt="$2" pass_name="$3" output_file="$4" log_file="$5"

    {
        echo ""
        echo "================================================================================"
        echo "PLAYBOOK RUNNER — pass: ${pass_name}"
        echo "Working directory: ${repo_dir}"
        echo "Tool transcript (raw stdout/stderr): ${output_file}"
        echo "(Copilot output is also appended to this runner log below so one tail -f shows everything.)"
        echo "================================================================================"
        if [ "$RUNNER" = "claude" ]; then
            echo "SHELL COMMAND (exact invocation — cwd is repo root):"
            if [ -n "$CLAUDE_MODEL" ]; then
                echo "  script -q $(printf '%q' "$output_file") claude --model $(printf '%q' "$CLAUDE_MODEL") -p $(printf '%q' "$prompt") --dangerously-skip-permissions"
            else
                echo "  script -q $(printf '%q' "$output_file") claude -p $(printf '%q' "$prompt") --dangerously-skip-permissions"
            fi
        else
            echo "SHELL COMMAND (exact invocation — cwd is repo root):"
            echo "  $(printf '%q' "$COPILOT") -p $(printf '%q' "$prompt") --model $(printf '%q' "$MODEL") --yolo"
            echo ""
            echo "Readable form (prompt may be long):"
            echo "  ${COPILOT} -p <PROMPT> --model ${MODEL} --yolo"
        fi
        echo ""
        echo "--- BEGIN PROMPT (${#prompt} bytes) ---"
        printf '%s\n' "$prompt"
        echo "--- END PROMPT ---"
        echo ""
    } >>"$log_file"

    cd "$repo_dir"
    if [ "$RUNNER" = "claude" ]; then
        local claude_args=(-p "$prompt" --dangerously-skip-permissions)
        [ -n "$CLAUDE_MODEL" ] && claude_args=(--model "$CLAUDE_MODEL" "${claude_args[@]}")
        # Write directly to file via script(1) — no pipe, so no buffering.
        # macOS script: script -q <outfile> <command...>
        # Linux script: script -q -c "<command>" <outfile>
        # Detect which form to use:
        if script -q /dev/null true 2>/dev/null; then
            # macOS form: script -q <file> <command...>
            script -q "$output_file" claude "${claude_args[@]}"
        else
            # Linux form: script -q -c "command" <file>
            script -q -c "claude $(printf '%q ' "${claude_args[@]}")" "$output_file"
        fi
        # Append the captured output to the runner log for post-hoc review
        cat "$output_file" >> "$log_file" 2>/dev/null
    else
        # Tee: same stream → control_prompts transcript (canonical) + runner log (so tail -f *.log shows live output)
        {
            echo ""
            echo "--- BEGIN gh copilot stdout/stderr (streaming) ---"
        } >>"$log_file"
        $COPILOT -p "$prompt" --model "$MODEL" --yolo 2>&1 | tee "$output_file" | tee -a "$log_file" >/dev/null
        {
            echo ""
            echo "--- END gh copilot stdout/stderr ---"
        } >>"$log_file"
    fi
    cd "$SCRIPT_DIR"
}

# ── Per-phase prompts (one per phase, each runs in its own session) ──

phase1_prompt() {
    local seed_instruction=""
    if [ "$NO_SEEDS" = true ]; then
        seed_instruction="Skip Phase 0 and Phase 0b entirely — do not look for previous_runs/ or sibling versioned directories. This is a clean benchmark run. Start directly at Phase 1."
    fi

    cat <<PROMPT
You are a quality engineer. Read the skill at .github/skills/SKILL.md — but ONLY the sections up through Phase 1 (stop at the "---" line before "Phase 2"). Also read the reference files in .github/skills/references/ that are relevant to exploration.

${seed_instruction}

Execute Phase 1: Explore the codebase. The docs_gathered/ directory contains gathered documentation — read it to supplement your exploration.

When Phase 1 is complete, write your full exploration findings to quality/EXPLORATION.md. This file must contain:
- Domain and stack identification
- Architecture map (key modules, entry points, data flow)
- Existing test inventory
- Specification summary (from docs_gathered/ and any inline docs)
- Quality risks identified
- Skeleton/dispatch/state-machine analysis (if applicable)
- Testable requirements derived (REQ-NNN format)
- Use cases derived (UC-NN format)

Also initialize quality/PROGRESS.md with the run metadata and mark Phase 1 complete.

IMPORTANT: Do NOT proceed to Phase 2. Your only job is exploration and writing findings to disk. Write thorough, detailed findings — the next phase will read EXPLORATION.md to generate artifacts, so everything important must be captured in that file.
PROMPT
}

phase2_prompt() {
    cat <<PROMPT
You are a quality engineer continuing a phase-by-phase quality playbook run. Phase 1 (exploration) is already complete.

Read these files to get context:
1. quality/EXPLORATION.md — your Phase 1 findings (requirements, risks, architecture)
2. quality/PROGRESS.md — run metadata and phase status
3. .github/skills/SKILL.md — read the Phase 2 section (from "Phase 2: Generate the Quality Playbook" through the "Checkpoint: Update PROGRESS.md after artifact generation" section). Also read the reference files cited in that section.

Execute Phase 2: Generate all quality artifacts. Use the exploration findings in EXPLORATION.md as your source — do not re-explore the codebase from scratch. Generate:
- quality/QUALITY.md (quality constitution)
- quality/CONTRACTS.md (behavioral contracts)
- quality/REQUIREMENTS.md (with REQ-NNN and UC-NN identifiers from EXPLORATION.md)
- quality/COVERAGE_MATRIX.md
- Functional tests (quality/test_functional.*)
- quality/RUN_CODE_REVIEW.md (code review protocol)
- quality/RUN_INTEGRATION_TESTS.md (integration test protocol)
- quality/RUN_SPEC_AUDIT.md (spec audit protocol)
- quality/RUN_TDD_TESTS.md (TDD verification protocol)
- quality/COMPLETENESS_REPORT.md (baseline, without verdict)
- If dispatch/enumeration contracts exist: quality/mechanical/ with verify.sh and extraction artifacts. Run verify.sh immediately and save receipts.

Update PROGRESS.md: mark Phase 2 complete, update artifact inventory.

IMPORTANT: Do NOT proceed to Phase 3 (code review). Your job is artifact generation only. The next phase will execute the review protocols you generated.
PROMPT
}

phase3_prompt() {
    cat <<PROMPT
You are a quality engineer continuing a phase-by-phase quality playbook run. Phases 1–2 are complete.

Read these files to get context:
1. quality/PROGRESS.md — run metadata, phase status, artifact inventory
2. quality/EXPLORATION.md — Phase 1 findings (especially the "Candidate Bugs for Phase 2" section)
3. quality/REQUIREMENTS.md — derived requirements and use cases
4. quality/CONTRACTS.md — behavioral contracts
5. .github/skills/SKILL.md — read the Phase 3 section ("Phase 3: Code Review and Regression Tests"). Also read .github/skills/references/review_protocols.md.

Execute Phase 3: Code Review + Regression Tests.
Run the 3-pass code review per quality/RUN_CODE_REVIEW.md. For every confirmed bug:
- Add to quality/BUGS.md with ### BUG-NNN heading format
- Write a regression test (xfail-marked)
- Generate quality/patches/BUG-NNN-regression-test.patch (MANDATORY for every confirmed bug)
- Generate quality/patches/BUG-NNN-fix.patch (strongly encouraged)
- Write code review reports to quality/code_reviews/
- Update PROGRESS.md BUG tracker

Mark Phase 3 (Code review + regression tests) complete in PROGRESS.md.

IMPORTANT: Do NOT proceed to Phase 4 (spec audit). The next phase will run the spec audit with a fresh context window.
PROMPT
}

phase4_prompt() {
    cat <<PROMPT
You are a quality engineer continuing a phase-by-phase quality playbook run. Phases 1–3 are complete.

Read these files to get context:
1. quality/PROGRESS.md — run metadata, phase status, BUG tracker
2. quality/REQUIREMENTS.md — derived requirements
3. quality/BUGS.md — bugs found in Phase 3 (code review)
4. .github/skills/SKILL.md — read the Phase 4 section ("Phase 4: Spec Audit and Triage"). Also read .github/skills/references/spec_audit.md.

Execute Phase 4: Spec Audit + Triage.
Run the spec audit per quality/RUN_SPEC_AUDIT.md. Produce:
- Individual auditor reports at quality/spec_audits/YYYY-MM-DD-auditor-N.md (one per auditor)
- Triage synthesis at quality/spec_audits/YYYY-MM-DD-triage.md
- Executable triage probes at quality/spec_audits/triage_probes.sh
- Regression tests and patches for any net-new spec audit bugs
- Update BUGS.md and PROGRESS.md BUG tracker with any new findings

Mark Phase 4 (Spec audit + triage) complete in PROGRESS.md.

IMPORTANT: Do NOT proceed to Phase 5 (reconciliation). The next phase will handle reconciliation and TDD.
PROMPT
}

phase5_prompt() {
    cat <<PROMPT
You are a quality engineer continuing a phase-by-phase quality playbook run. Phases 1–4 are complete.

Read these files to get context:
1. quality/PROGRESS.md — run metadata, phase status, cumulative BUG tracker
2. quality/BUGS.md — all confirmed bugs from code review and spec audit
3. quality/REQUIREMENTS.md — derived requirements
4. .github/skills/SKILL.md — read the Phase 5 section ("Phase 5: Post-Review Reconciliation and Closure Verification"). Also read .github/skills/references/requirements_pipeline.md, .github/skills/references/review_protocols.md, and .github/skills/references/spec_audit.md.

Execute Phase 5: Reconciliation + TDD + Closure.

1. Run the Post-Review Reconciliation per references/requirements_pipeline.md. Update COMPLETENESS_REPORT.md.
2. Run closure verification: every BUG in the tracker must have either a regression test or an explicit exemption.
3. Write bug writeups at quality/writeups/BUG-NNN.md for EVERY confirmed bug. Each writeup MUST include an inline fix diff in a \`\`\`diff code block — this is gate-enforced.
4. Run the TDD red-green cycle: for each confirmed bug, run the regression test against unpatched code → quality/results/BUG-NNN.red.log. If a fix patch exists, run against patched code → quality/results/BUG-NNN.green.log. If the test runner is unavailable, create the log with NOT_RUN on the first line.
5. Generate sidecar JSON: quality/results/tdd-results.json and quality/results/integration-results.json (schema_version "1.1", canonical fields: id, requirement, red_phase, green_phase, verdict, fix_patch_present, writeup_path).
6. If mechanical verification artifacts exist, run quality/mechanical/verify.sh and save receipts.
7. Run terminal gate verification, write it to PROGRESS.md.

Mark Phase 5 complete in PROGRESS.md.

IMPORTANT: Do NOT skip writeup inline diffs or TDD logs. The next phase runs quality_gate.sh which will FAIL on missing patches, missing diffs, or missing TDD logs.
PROMPT
}

phase6_prompt() {
    cat <<PROMPT
You are a quality engineer doing the verification phase of a quality playbook run. Phases 1–5 are complete.

Read .github/skills/SKILL.md — the Phase 6 section ("Phase 6: Verify"). Follow the incremental verification steps (6.1 through 6.5).

Step 6.1: If quality/mechanical/verify.sh exists, run it. Record exit code.
Step 6.2: Run quality_gate.sh:
  bash .github/skills/quality_gate.sh .
Read the output carefully. For every FAIL result, fix the issue:
- Missing regression-test patches: generate quality/patches/BUG-NNN-regression-test.patch
- Missing inline diffs in writeups: add a \`\`\`diff block
- Non-canonical JSON fields: fix tdd-results.json (use 'id' not 'bug_id', etc.)
- Missing files: create them
After fixing all FAILs, run quality_gate.sh again. Repeat until 0 FAIL.
Save final output to quality/results/quality-gate.log.

Step 6.3: Run functional tests if a test runner is available.
Step 6.4: File-by-file verification checklist (read one file at a time, check, move on).
Step 6.5: Metadata consistency check.

Append each step's result to quality/results/phase6-verification.log.
Mark Phase 6 complete in PROGRESS.md.
PROMPT
}

# ── Single-pass prompt (default: one invocation ≈ user running full playbook in Copilot) ──

single_pass_prompt() {
    local seed_instruction=""
    if [ "$NO_SEEDS" = true ]; then
        seed_instruction=" Skip Phase 0 and Phase 0b — start directly at Phase 1."
    fi

    echo "Read the quality playbook skill at .github/skills/SKILL.md and execute the quality playbook for this project.${seed_instruction}"
}

# ── Iteration prompt (builds on an existing quality/ run) ──

iteration_prompt() {
    local strategy="$1"

    echo "Read the quality playbook skill at .github/skills/SKILL.md and run the next iteration using the ${strategy} strategy."
}

# ── Next-strategy cycle ──

next_strategy() {
    case "$1" in
        gap)          echo "unfiltered" ;;
        unfiltered)   echo "parity" ;;
        parity)       echo "adversarial" ;;
        adversarial)  echo "" ;;  # cycle complete
        *)            echo "gap" ;;
    esac
}

ALL_STRATEGIES=(gap unfiltered parity adversarial)

# ── Exit gates — check prerequisites before running each phase ──

check_phase_gate() {
    local repo_dir="$1" phase="$2" log_file="$3"
    local q="${repo_dir}/quality"

    case "$phase" in
        1)
            # Phase 1 has no prerequisites (it's the start)
            return 0
            ;;
        2)
            # Phase 2 requires EXPLORATION.md from Phase 1
            if [ ! -f "${q}/EXPLORATION.md" ]; then
                logboth "$log_file" "$(log "  GATE FAIL Phase 2: quality/EXPLORATION.md missing — run Phase 1 first")"
                return 1
            fi
            local elines
            elines=$(wc -l < "${q}/EXPLORATION.md" 2>/dev/null || echo 0)
            if [ "$elines" -lt 80 ]; then
                logboth "$log_file" "$(log "  GATE WARN Phase 2: EXPLORATION.md is only ${elines} lines (expected 80+)")"
            fi
            return 0
            ;;
        3)
            # Phase 3 (code review) requires Phase 2 artifacts
            local missing=()
            for f in REQUIREMENTS.md QUALITY.md CONTRACTS.md RUN_CODE_REVIEW.md; do
                [ ! -f "${q}/${f}" ] && missing+=("$f")
            done
            if [ ${#missing[@]} -gt 0 ]; then
                logboth "$log_file" "$(log "  GATE FAIL Phase 3: missing ${missing[*]} — run Phase 2 first")"
                return 1
            fi
            return 0
            ;;
        4)
            # Phase 4 (spec audit) requires Phase 2 artifacts + code review output
            if [ ! -f "${q}/REQUIREMENTS.md" ]; then
                logboth "$log_file" "$(log "  GATE FAIL Phase 4: REQUIREMENTS.md missing — run Phase 2 first")"
                return 1
            fi
            if [ ! -f "${q}/RUN_SPEC_AUDIT.md" ]; then
                logboth "$log_file" "$(log "  GATE FAIL Phase 4: RUN_SPEC_AUDIT.md missing — run Phase 2 first")"
                return 1
            fi
            if [ ! -d "${q}/code_reviews" ] || [ -z "$(ls -A "${q}/code_reviews" 2>/dev/null)" ]; then
                logboth "$log_file" "$(log "  GATE WARN Phase 4: no code_reviews/ — Phase 3 may not have run")"
            fi
            return 0
            ;;
        5)
            # Phase 5 (reconciliation) requires bugs from review and/or audit
            if [ ! -f "${q}/PROGRESS.md" ]; then
                logboth "$log_file" "$(log "  GATE FAIL Phase 5: PROGRESS.md missing")"
                return 1
            fi
            if [ ! -f "${q}/BUGS.md" ] && [ ! -d "${q}/spec_audits" ]; then
                logboth "$log_file" "$(log "  GATE WARN Phase 5: no BUGS.md and no spec_audits/ — Phases 3-4 may not have run")"
            fi
            return 0
            ;;
        6)
            # Phase 6 (verification) requires Phase 5 outputs
            if [ ! -f "${q}/PROGRESS.md" ]; then
                logboth "$log_file" "$(log "  GATE FAIL Phase 6: PROGRESS.md missing")"
                return 1
            fi
            return 0
            ;;
    esac
}

# ── Run one phase for a repo ──

run_one_phase() {
    local repo_dir="$1" phase="$2" log_file="$3"
    local repo_name total_phases
    repo_name=$(basename "$repo_dir")
    total_phases=$(echo "$PHASE_LIST" | tr ',' ' ' | wc -w | tr -d ' ')
    local phase_idx
    phase_idx=$(echo "$PHASE_LIST" | tr ',' '\n' | grep -n "^${phase}$" | head -1 | cut -d: -f1)

    # Check exit gate
    if ! check_phase_gate "$repo_dir" "$phase" "$log_file"; then
        return 1
    fi

    local prompt output_file
    prompt=$(eval "phase${phase}_prompt")
    output_file="${repo_dir}/control_prompts/phase${phase}.output.txt"

    logboth "$log_file" "$(log "  Phase ${phase}/${total_phases} ($(phase_label "$phase")): ${repo_name}")"
    run_prompt "$repo_dir" "$prompt" "phase${phase}" "$output_file" "$log_file"

    # Post-phase summary
    case "$phase" in
        1)
            local elines
            elines=$(wc -l < "${repo_dir}/quality/EXPLORATION.md" 2>/dev/null || echo 0)
            logboth "$log_file" "$(log "  Phase 1 complete: ${elines} lines in EXPLORATION.md")"
            ;;
        2)
            local p2_missing=()
            for artifact in quality/REQUIREMENTS.md quality/QUALITY.md quality/CONTRACTS.md; do
                [ ! -f "${repo_dir}/${artifact}" ] && p2_missing+=("$artifact")
            done
            if [ ${#p2_missing[@]} -gt 0 ]; then
                logboth "$log_file" "$(log "  WARN Phase 2: missing ${p2_missing[*]}")"
            else
                logboth "$log_file" "$(log "  Phase 2 complete: core artifacts generated")"
            fi
            ;;
        3)
            local nbugs npatches
            nbugs=$(grep -c '### BUG-' "${repo_dir}/quality/BUGS.md" 2>/dev/null || echo 0)
            npatches=$(ls "${repo_dir}/quality/patches/" 2>/dev/null | wc -l | tr -d ' ')
            logboth "$log_file" "$(log "  Phase 3 complete: ${nbugs} bugs, ${npatches} patches")"
            ;;
        4)
            local nauditors
            nauditors=$(ls "${repo_dir}/quality/spec_audits/"*auditor* 2>/dev/null | wc -l | tr -d ' ')
            logboth "$log_file" "$(log "  Phase 4 complete: ${nauditors} auditor reports")"
            ;;
        5)
            local nwriteups nred
            nwriteups=$(ls "${repo_dir}/quality/writeups/" 2>/dev/null | wc -l | tr -d ' ')
            nred=$(ls "${repo_dir}/quality/results/BUG-"*.red.log 2>/dev/null | wc -l | tr -d ' ')
            logboth "$log_file" "$(log "  Phase 5 complete: ${nwriteups} writeups, ${nred} TDD red-phase logs")"
            ;;
        6)
            local gate_result="unknown"
            if [ -f "${repo_dir}/quality/results/quality-gate.log" ]; then
                gate_result=$(tail -1 "${repo_dir}/quality/results/quality-gate.log" 2>/dev/null)
            fi
            logboth "$log_file" "$(log "  Phase 6 complete: ${gate_result}")"
            ;;
    esac
}

phase_label() {
    case "$1" in
        1) echo "Explore" ;;
        2) echo "Generate" ;;
        3) echo "Code Review" ;;
        4) echo "Spec Audit" ;;
        5) echo "Reconciliation" ;;
        6) echo "Verification" ;;
    esac
}

# ── Run one repo (phase-by-phase) ──

run_one_phased() {
    local repo_dir="$1"
    local repo_name ts log_file
    repo_name=$(basename "$repo_dir")
    ts="${RUN_TIMESTAMP:-$(date '+%Y%m%d-%H%M%S')}"
    log_file="${SCRIPT_DIR}/${repo_name}-playbook-${ts}.log"

    # Docs gate
    if [ ! -d "${repo_dir}/docs_gathered" ] || [ -z "$(ls -A "${repo_dir}/docs_gathered" 2>/dev/null)" ]; then
        log "SKIP: ${repo_name} — docs_gathered/ is missing or empty"
        return 1
    fi

    # Archive previous run only if Phase 1 is in the list (starting fresh)
    if echo "$PHASE_LIST" | grep -q '\b1\b'; then
        if [ -d "${repo_dir}/quality" ]; then
            local archive_dir="${repo_dir}/previous_runs/${ts}"
            mkdir -p "$archive_dir"
            cp -a "${repo_dir}/quality" "$archive_dir/quality"
            rm -rf "${repo_dir}/quality" "${repo_dir}/control_prompts"
        fi
    fi

    mkdir -p "${repo_dir}/control_prompts"

    logboth "$log_file" "$(log "Starting playbook (phases: ${PHASE_LIST}): ${repo_name} (runner=${RUNNER})")"

    # Run each phase in sequence
    local IFS=','
    for phase in $PHASE_LIST; do
        if ! run_one_phase "$repo_dir" "$phase" "$log_file"; then
            logboth "$log_file" "$(log "ABORT: Phase ${phase} gate failed for ${repo_name}")"
            return 1
        fi
    done
    unset IFS

    logboth "$log_file" "$(log "Playbook complete (phases: ${PHASE_LIST}): ${repo_name}")"

    # Final artifact check
    local missing=()
    for artifact in quality/REQUIREMENTS.md quality/CONTRACTS.md quality/COVERAGE_MATRIX.md \
                    quality/COMPLETENESS_REPORT.md quality/PROGRESS.md quality/QUALITY.md \
                    quality/RUN_CODE_REVIEW.md quality/RUN_INTEGRATION_TESTS.md \
                    quality/RUN_SPEC_AUDIT.md quality/RUN_TDD_TESTS.md; do
        [ ! -f "${repo_dir}/${artifact}" ] && missing+=("$artifact")
    done
    [ -z "$(find_functional_test "$repo_dir")" ] && missing+=("functional test")

    if [ ${#missing[@]} -gt 0 ]; then
        logboth "$log_file" "$(log "WARNING: Missing: ${missing[*]}")"
    else
        logboth "$log_file" "$(log "All artifacts present")"
    fi

    cleanup_repo "$repo_dir"
}

# ── Run one repo (single-pass legacy) ──

run_one_singlepass() {
    local repo_dir="$1"
    local repo_name ts log_file output_file
    repo_name=$(basename "$repo_dir")
    ts="${RUN_TIMESTAMP:-$(date '+%Y%m%d-%H%M%S')}"
    log_file="${SCRIPT_DIR}/${repo_name}-playbook-${ts}.log"

    # Docs gate
    if [ ! -d "${repo_dir}/docs_gathered" ] || [ -z "$(ls -A "${repo_dir}/docs_gathered" 2>/dev/null)" ]; then
        log "SKIP: ${repo_name} — docs_gathered/ is missing or empty"
        return 1
    fi

    local prompt pass_label
    if [ "$NEXT_ITERATION" = true ]; then
        # Iteration mode: require existing quality/ directory, don't archive
        if [ ! -f "${repo_dir}/quality/EXPLORATION.md" ]; then
            log "SKIP: ${repo_name} — no quality/EXPLORATION.md to iterate on"
            return 1
        fi
        prompt=$(iteration_prompt "$ITER_STRATEGY")
        pass_label="iteration-${ITER_STRATEGY}"
        logboth "$log_file" "$(log "Starting iteration (${ITER_STRATEGY}): ${repo_name} (runner=${RUNNER}, building on existing quality/)")"
    else
        # Fresh run: archive previous quality/ and start clean
        if [ -d "${repo_dir}/quality" ]; then
            local archive_dir="${repo_dir}/previous_runs/${ts}"
            mkdir -p "$archive_dir"
            cp -a "${repo_dir}/quality" "$archive_dir/quality"
            rm -rf "${repo_dir}/quality" "${repo_dir}/control_prompts"
        fi
        prompt=$(single_pass_prompt)
        pass_label="full"
        logboth "$log_file" "$(log "Starting playbook (single-pass): ${repo_name} (runner=${RUNNER})")"
    fi

    mkdir -p "${repo_dir}/control_prompts"
    output_file="${repo_dir}/control_prompts/playbook_run.output.txt"

    run_prompt "$repo_dir" "$prompt" "$pass_label" "$output_file" "$log_file"

    logboth "$log_file" "$(log "Playbook complete: ${repo_name}")"

    # Artifact check
    local missing=()
    for artifact in quality/REQUIREMENTS.md quality/CONTRACTS.md quality/COVERAGE_MATRIX.md \
                    quality/COMPLETENESS_REPORT.md quality/PROGRESS.md quality/QUALITY.md \
                    quality/RUN_CODE_REVIEW.md quality/RUN_INTEGRATION_TESTS.md \
                    quality/RUN_SPEC_AUDIT.md quality/RUN_TDD_TESTS.md; do
        [ ! -f "${repo_dir}/${artifact}" ] && missing+=("$artifact")
    done
    [ -z "$(find_functional_test "$repo_dir")" ] && missing+=("functional test")

    if [ ${#missing[@]} -gt 0 ]; then
        logboth "$log_file" "$(log "WARNING: Missing: ${missing[*]}")"
    else
        logboth "$log_file" "$(log "All artifacts present")"
    fi

    cleanup_repo "$repo_dir"
}

# ── Dispatch ──

# Expand PHASE_MODE into PHASE_LIST (comma-separated phase numbers)
PHASE_LIST=""
if [ -n "$PHASE_MODE" ]; then
    if [ "$PHASE_MODE" = "all" ]; then
        PHASE_LIST="1,2,3,4,5,6"
    else
        PHASE_LIST="$PHASE_MODE"
    fi
fi

run_one() {
    if [ -n "$PHASE_LIST" ]; then
        run_one_phased "$1"
    else
        run_one_singlepass "$1"
    fi
}

# ── Strategy: all — loop through gap → unfiltered → parity → adversarial ──

if [ "$ITER_STRATEGY" = "all" ] && [ "$NEXT_ITERATION" = true ]; then
    repo_args=""
    for repo_dir in "${REPO_DIRS[@]}"; do
        repo_args="${repo_args} $(basename "$repo_dir" | sed 's/-[0-9].*//')"
    done
    repo_args=$(echo "$repo_args" | xargs)

    echo "=== Running all iteration strategies: gap → unfiltered → parity → adversarial ==="
    echo ""

    for strategy in "${ALL_STRATEGIES[@]}"; do
        echo "══════════════════════════════════════════════════════════"
        echo "  Strategy: ${strategy}"
        echo "══════════════════════════════════════════════════════════"
        echo ""

        # Count bugs before this strategy
        before_bugs=0
        for repo_dir in "${REPO_DIRS[@]}"; do
            n=$(ls "${repo_dir}/quality/writeups/BUG-"*.md 2>/dev/null | wc -l)
            before_bugs=$((before_bugs + n))
        done

        # Re-invoke ourselves for this single strategy (pass --claude if set)
        local _runner_flag=""
        [ "$RUNNER" = "claude" ] && _runner_flag="--claude"
        _ALL_RUNNING=true "$0" $_runner_flag --next-iteration --strategy "$strategy" $repo_args

        # Count bugs after
        after_bugs=0
        for repo_dir in "${REPO_DIRS[@]}"; do
            n=$(ls "${repo_dir}/quality/writeups/BUG-"*.md 2>/dev/null | wc -l)
            after_bugs=$((after_bugs + n))
        done

        gained=$((after_bugs - before_bugs))
        echo ""
        echo "  Strategy ${strategy}: ${before_bugs} → ${after_bugs} bugs (+${gained})"

        if [ "$gained" -eq 0 ]; then
            echo "  No new bugs found — stopping early (diminishing returns)."
            break
        fi
        echo ""
    done

    echo ""
    echo "=== All-strategy run complete ==="
    print_summary "${REPO_DIRS[@]}"
    exit 0
fi

if [ "$PARALLEL" = true ]; then
    PIDS=()
    : > "$PID_FILE"  # truncate
    for repo_dir in "${REPO_DIRS[@]}"; do
        run_one "$repo_dir" &
        pid=$!
        PIDS+=($pid)
        echo "$pid $(basename "$repo_dir")" >> "$PID_FILE"
    done
    echo "PIDs written to $PID_FILE — stop with: ./run_playbook.sh --kill"
    echo ""
    FAILED=0
    for i in "${!PIDS[@]}"; do
        wait "${PIDS[$i]}" || FAILED=$((FAILED + 1))
    done
    rm -f "$PID_FILE"
    echo ""
    echo "=== Parallel run complete. ${FAILED} failures out of ${#REPO_DIRS[@]} repos. ==="
else
    for repo_dir in "${REPO_DIRS[@]}"; do
        run_one "$repo_dir"
        echo ""
    done
fi

print_summary "${REPO_DIRS[@]}"

# ── Suggested next command ──

suggest_next_command() {
    # Use the original arg names the user passed in, not the resolved directory names.
    # This way "virtio" stays "virtio", not "virtio-1.3.47" or "virtio-quality-playbook".
    local repo_names="${REPO_NAMES[*]}"

    # Include --claude if this run used it
    local runner_flag=""
    [ "$RUNNER" = "claude" ] && runner_flag=" --claude"

    if [ "$NEXT_ITERATION" = true ]; then
        local next
        next=$(next_strategy "$ITER_STRATEGY")
        if [ -n "$next" ]; then
            echo "────────────────────────────────────────────────────────"
            echo "Next iteration suggestion:"
            echo "  ./run_playbook.sh${runner_flag} --next-iteration --strategy ${next} ${repo_names}"
            echo "────────────────────────────────────────────────────────"
        else
            echo "────────────────────────────────────────────────────────"
            echo "Iteration cycle complete (gap → unfiltered → parity → adversarial)."
            echo "To start fresh:  ./run_playbook.sh${runner_flag} ${repo_names}"
            echo "────────────────────────────────────────────────────────"
        fi
    else
        echo "────────────────────────────────────────────────────────"
        echo "Next iteration suggestion:"
        echo "  ./run_playbook.sh${runner_flag} --next-iteration --strategy gap ${repo_names}"
        echo "────────────────────────────────────────────────────────"
    fi
}

# Don't print suggestion for individual strategies within an 'all' run
if [ "${_ALL_RUNNING:-false}" != true ]; then
    suggest_next_command
fi
