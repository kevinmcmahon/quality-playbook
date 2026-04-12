#!/bin/bash
# Generate quality artifacts for benchmark repos.
#
# Default (simulates a fresh VS Code + Copilot run: one prompt, full playbook):
#   Copilot, QPB_MODEL or gpt-5.4, parallel repos, single-pass, no Phase 0/0b seeds.
#
#   ./run_playbook.sh virtio chi httpx gson
#
# Opt-in multi-pass mode splits each repo into 4 CLI passes (smaller context per step):
#   Pass 1 (Explore) → Pass 2 (Generate) → Pass 3 (Review/Audit) → Pass 4 (Gate)
#
# Usage:
#   ./run_playbook.sh virtio chi httpx gson              # defaults (see above)
#   ./run_playbook.sh --sequential virtio chi            # one repo at a time
#   ./run_playbook.sh --multi-pass virtio chi            # 4-pass per repo
#   ./run_playbook.sh --claude --model opus virtio       # Claude CLI instead of Copilot
#
# Options:
#   --parallel       Run all repos concurrently (default: on)
#   --sequential     Run repos one after another
#   --claude         Use claude -p instead of gh copilot
#   --copilot        Use gh copilot (default)
#   --no-seeds       Skip Phase 0/0b (default: on — clean benchmark)
#   --with-seeds     Allow Phase 0/0b seed injection from prior/sibling runs
#   --single-pass    One prompt for the entire pipeline (default: on)
#   --multi-pass     Four passes per repo (explore → generate → review → gate)
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
RUNNER="copilot"  # "copilot" or "claude"
NO_SEEDS=true     # clean benchmark — skip Phase 0 / sibling seeds
SINGLE_PASS=true  # one CLI invocation per repo with the full skill
CLAUDE_MODEL=""
REPO_NAMES=()
EXPECT_MODEL=false
for arg in "$@"; do
    if [ "$EXPECT_MODEL" = true ]; then
        CLAUDE_MODEL="$arg"
        EXPECT_MODEL=false
        continue
    fi
    case "$arg" in
        --parallel)     PARALLEL=true ;;
        --sequential)   PARALLEL=false ;;
        --claude)       RUNNER="claude" ;;
        --copilot)      RUNNER="copilot" ;;
        --no-seeds)     NO_SEEDS=true ;;
        --with-seeds)   NO_SEEDS=false ;;
        --single-pass)  SINGLE_PASS=true ;;
        --multi-pass)   SINGLE_PASS=false ;;
        --model)        EXPECT_MODEL=true ;;
        --kill)
            if [ -f "$PID_FILE" ]; then
                echo "Killing PIDs from $PID_FILE:"
                while read -r pid repo; do
                    if kill -0 "$pid" 2>/dev/null; then
                        echo "  kill $pid ($repo)"
                        kill "$pid" 2>/dev/null
                        # Also kill any child claude processes
                        pkill -P "$pid" 2>/dev/null
                    else
                        echo "  $pid ($repo) — already exited"
                    fi
                done < "$PID_FILE"
                rm -f "$PID_FILE"
            else
                echo "No PID file found. Falling back to pkill:"
                pkill -f "claude -p" && echo "  Killed claude -p processes" || echo "  No claude -p processes found"
            fi
            exit 0
            ;;
        *)           REPO_NAMES+=("$arg") ;;
    esac
done

# --model overrides QPB_MODEL for copilot
[ -n "$CLAUDE_MODEL" ] && [ "$RUNNER" = "copilot" ] && MODEL="$CLAUDE_MODEL"

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

echo "=== Quality Playbook — Artifact Generation ==="
echo "Version:  ${VERSION}"
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
echo "Mode:     $([ "$SINGLE_PASS" = true ] && echo "single-pass (one prompt)" || echo "multi-pass (4 CLI passes)")"
echo "Repos:    ${REPO_DIRS[*]##*/}"
echo ""
echo "=== Runner logs (one file per repo — names include this run's RUN_TIMESTAMP) ==="
echo "Each file gets the full prompt and exact shell command before the tool runs. With this script version,"
echo "Copilot stdout is also streamed into the runner log (tee). On older runs, live Copilot output was only in the repo transcript below."
_screen_logs=()
for repo_dir in "${REPO_DIRS[@]}"; do
    _tail_name=$(basename "$repo_dir")
    _log_path="${SCRIPT_DIR}/${_tail_name}-playbook-${RUN_TIMESTAMP}.log"
    _screen_logs+=("$_log_path")
    echo "tail -f $(printf '%q' "$_log_path")"
done
if [ "$SINGLE_PASS" = true ] && [ "$RUNNER" = "copilot" ]; then
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
        script -q "$output_file" claude "${claude_args[@]}" 2>&1
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

# ── Multi-pass prompts ──

pass1_prompt() {
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

IMPORTANT: Do NOT proceed to Phase 2. Your only job is exploration and writing findings to disk. Write thorough, detailed findings — the next pass will read EXPLORATION.md to generate artifacts, so everything important must be captured in that file.
PROMPT
}

pass2_prompt() {
    cat <<PROMPT
You are a quality engineer continuing a multi-pass quality playbook run. Phase 1 (exploration) is already complete.

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

IMPORTANT: Do NOT proceed to Phase 2b (code review). Your job is artifact generation only. The next pass will execute the review protocols you generated.
PROMPT
}

pass3_prompt() {
    cat <<PROMPT
You are a quality engineer continuing a multi-pass quality playbook run. Phases 1-2 are complete.

Read these files to get context:
1. quality/PROGRESS.md — run metadata, phase status, artifact inventory
2. quality/EXPLORATION.md — Phase 1 findings
3. quality/REQUIREMENTS.md — derived requirements and use cases
4. quality/CONTRACTS.md — behavioral contracts
5. .github/skills/SKILL.md — read Phase 2b, Phase 2c, and Phase 2d sections (from "Phase 2b: Code Review" through the end of Phase 2d). Also read .github/skills/references/review_protocols.md, .github/skills/references/spec_audit.md, and .github/skills/references/verification.md.

Execute Phases 2b through 2d:

**Phase 2b — Code Review + Regression Tests:**
Run the 3-pass code review per quality/RUN_CODE_REVIEW.md. For every confirmed bug:
- Add to BUGS.md with ### BUG-NNN heading format
- Write a regression test (xfail-marked)
- Generate quality/patches/BUG-NNN-regression-test.patch (MANDATORY for every confirmed bug)
- Generate quality/patches/BUG-NNN-fix.patch (strongly encouraged)
- Update PROGRESS.md BUG tracker

**Phase 2c — Spec Audit + Triage:**
Run the spec audit per quality/RUN_SPEC_AUDIT.md. Produce individual auditor reports AND triage synthesis. Write regression tests for any net-new spec audit bugs. Generate patches for those too.

**Phase 2d — Reconciliation + Closure:**
- Sync triage findings to BUGS.md
- Run closure verification (every BUG has regression test or exemption)
- Write bug writeups at quality/writeups/BUG-NNN.md for EVERY confirmed bug. Each writeup MUST include an inline fix diff in a \`\`\`diff code block — this is gate-enforced.
- Generate sidecar JSON: quality/results/tdd-results.json and quality/results/integration-results.json (use schema_version "1.1", canonical field names: id, requirement, red_phase, green_phase, verdict, fix_patch_present, writeup_path)
- Run terminal gate verification, write it to PROGRESS.md
- Mark Phase 2d complete

IMPORTANT: Do NOT skip patch generation or writeup inline diffs. The next pass runs quality_gate.sh which will FAIL on missing patches or missing diffs.
PROMPT
}

pass4_prompt() {
    cat <<PROMPT
You are a quality engineer doing the final conformance pass of a multi-pass quality playbook run. Phases 1 through 2d are complete.

Run this command from the project root:
  bash .github/skills/quality_gate.sh .

Read the output carefully. For every FAIL result, fix the issue:
- Missing regression-test patches: generate quality/patches/BUG-NNN-regression-test.patch for each confirmed bug
- Missing inline diffs in writeups: add a \`\`\`diff block to the writeup's fix section
- Non-canonical JSON fields: fix field names in tdd-results.json (use 'id' not 'bug_id', etc.)
- Missing confirmed_open in summary: add it to tdd-results.json summary
- Missing files: create them

After fixing all FAILs, run quality_gate.sh again. Repeat until it reports 0 FAIL.

Save the final quality_gate.sh output to quality/results/quality-gate.log.

Then read .github/skills/references/verification.md and spot-check 5 benchmarks from the list against the generated artifacts. Note any issues in quality/results/quality-gate.log as comments.
PROMPT
}

# ── Single-pass prompt (default: one invocation ≈ user running full playbook in Copilot) ──

single_pass_prompt() {
    local seed_instruction=""
    if [ "$NO_SEEDS" = true ]; then
        seed_instruction=" IMPORTANT: Skip Phase 0 and Phase 0b entirely — do not look for previous_runs/ or sibling versioned directories. This is a clean benchmark run testing independent bug discovery. Start directly at Phase 1."
    fi

    echo "Read the quality playbook skill at .github/skills/SKILL.md and its reference files in .github/skills/references/. Execute the quality playbook for this project. Additional documentation for this project has been gathered in docs_gathered/ — read it during Phase 1 exploration to supplement the codebase and improve the quality of requirements, scenarios, and tests. IMPORTANT: Before marking Phase 2d complete, run 'bash .github/skills/quality_gate.sh .' and fix any FAIL results. Save the output to quality/results/quality-gate.log.${seed_instruction}"
}

# ── Run one repo (multi-pass) ──

run_one_multipass() {
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

    # Archive previous run
    if [ -d "${repo_dir}/quality" ]; then
        local archive_dir="${repo_dir}/previous_runs/${ts}"
        mkdir -p "$archive_dir"
        cp -a "${repo_dir}/quality" "$archive_dir/quality"
        rm -rf "${repo_dir}/quality" "${repo_dir}/control_prompts"
    fi

    mkdir -p "${repo_dir}/control_prompts"

    logboth "$log_file" "$(log "Starting playbook (multi-pass): ${repo_name} (runner=${RUNNER})")"

    # ── Pass 1: Explore ──
    logboth "$log_file" "$(log "  Pass 1/4 (Explore): ${repo_name}")"
    local p1_prompt p1_output
    p1_prompt=$(pass1_prompt)
    p1_output="${repo_dir}/control_prompts/pass1_explore.output.txt"
    run_prompt "$repo_dir" "$p1_prompt" "explore" "$p1_output" "$log_file"

    if [ ! -f "${repo_dir}/quality/EXPLORATION.md" ] && [ ! -f "${repo_dir}/quality/PROGRESS.md" ]; then
        logboth "$log_file" "$(log "  FAIL Pass 1: no exploration output — aborting ${repo_name}")"
        return 1
    fi
    logboth "$log_file" "$(log "  Pass 1 complete: $(wc -l < "${repo_dir}/quality/EXPLORATION.md" 2>/dev/null || echo 0) lines in EXPLORATION.md")"

    # ── Pass 2: Generate ──
    logboth "$log_file" "$(log "  Pass 2/4 (Generate): ${repo_name}")"
    local p2_prompt p2_output
    p2_prompt=$(pass2_prompt)
    p2_output="${repo_dir}/control_prompts/pass2_generate.output.txt"
    run_prompt "$repo_dir" "$p2_prompt" "generate" "$p2_output" "$log_file"

    local p2_missing=()
    for artifact in quality/REQUIREMENTS.md quality/QUALITY.md quality/PROGRESS.md; do
        [ ! -f "${repo_dir}/${artifact}" ] && p2_missing+=("$artifact")
    done
    if [ ${#p2_missing[@]} -gt 0 ]; then
        logboth "$log_file" "$(log "  WARN Pass 2: missing ${p2_missing[*]}")"
    else
        logboth "$log_file" "$(log "  Pass 2 complete: core artifacts generated")"
    fi

    # ── Pass 3: Review + Audit + Reconciliation ──
    logboth "$log_file" "$(log "  Pass 3/4 (Review): ${repo_name}")"
    local p3_prompt p3_output
    p3_prompt=$(pass3_prompt)
    p3_output="${repo_dir}/control_prompts/pass3_review.output.txt"
    run_prompt "$repo_dir" "$p3_prompt" "review" "$p3_output" "$log_file"

    logboth "$log_file" "$(log "  Pass 3 complete: $(ls "${repo_dir}/quality/writeups/" 2>/dev/null | wc -l | tr -d ' ') writeups, $(ls "${repo_dir}/quality/patches/" 2>/dev/null | wc -l | tr -d ' ') patches")"

    # ── Pass 4: Conformance Gate ──
    logboth "$log_file" "$(log "  Pass 4/4 (Gate): ${repo_name}")"
    local p4_prompt p4_output
    p4_prompt=$(pass4_prompt)
    p4_output="${repo_dir}/control_prompts/pass4_gate.output.txt"
    run_prompt "$repo_dir" "$p4_prompt" "gate" "$p4_output" "$log_file"

    local gate_result="unknown"
    if [ -f "${repo_dir}/quality/results/quality-gate.log" ]; then
        gate_result=$(tail -1 "${repo_dir}/quality/results/quality-gate.log" 2>/dev/null)
    fi
    logboth "$log_file" "$(log "  Pass 4 complete: ${gate_result}")"

    logboth "$log_file" "$(log "Playbook complete (multi-pass): ${repo_name}")"

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

    # Archive previous run
    if [ -d "${repo_dir}/quality" ]; then
        local archive_dir="${repo_dir}/previous_runs/${ts}"
        mkdir -p "$archive_dir"
        cp -a "${repo_dir}/quality" "$archive_dir/quality"
        rm -rf "${repo_dir}/quality" "${repo_dir}/control_prompts"
    fi

    mkdir -p "${repo_dir}/control_prompts"
    output_file="${repo_dir}/control_prompts/playbook_run.output.txt"

    local prompt
    prompt=$(single_pass_prompt)

    logboth "$log_file" "$(log "Starting playbook (single-pass): ${repo_name} (runner=${RUNNER})")"

    run_prompt "$repo_dir" "$prompt" "full" "$output_file" "$log_file"

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

run_one() {
    if [ "$SINGLE_PASS" = true ]; then
        run_one_singlepass "$1"
    else
        run_one_multipass "$1"
    fi
}

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
