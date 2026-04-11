#!/bin/bash
# Generate quality artifacts for benchmark repos.
#
# Usage:
#   ./run_playbook.sh chi cobra httpx                    # Sequential, copilot
#   ./run_playbook.sh --parallel chi cobra httpx         # Parallel, copilot
#   ./run_playbook.sh --claude --parallel chi cobra httpx # Parallel, claude
#
# Options:
#   --parallel       Run all repos concurrently
#   --claude         Use claude -p instead of gh copilot (no --yolo needed)
#   --copilot        Use gh copilot (default)
#   --no-seeds       Skip Phase 0/0b (seed injection) for clean benchmark runs
#   --model MODEL    Model to use (claude: opus, sonnet, haiku; copilot: gpt-5.4, etc.)
#   --kill           Kill all processes from the current/last parallel run
#
# Environment:
#   QPB_MODEL — model for gh copilot (default: gpt-5.4; overridden by --model)

set -uo pipefail
source "$(dirname "$0")/_benchmark_lib.sh"

PID_FILE="${SCRIPT_DIR}/.run_pids"

PARALLEL=false
RUNNER="copilot"  # "copilot" or "claude"
NO_SEEDS=false
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
        --parallel)  PARALLEL=true ;;
        --claude)    RUNNER="claude" ;;
        --copilot)   RUNNER="copilot" ;;
        --no-seeds)  NO_SEEDS=true ;;
        --model)     EXPECT_MODEL=true ;;
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
echo "No seeds: ${NO_SEEDS}"
echo "Parallel: ${PARALLEL}"
echo "Repos:    ${REPO_DIRS[*]##*/}"
echo ""

run_one() {
    local repo_dir="$1"
    local repo_name timestamp log_file output_file
    repo_name=$(basename "$repo_dir")
    timestamp=$(date '+%Y%m%d-%H%M%S')
    log_file="${SCRIPT_DIR}/${repo_name}-playbook-${timestamp}.log"

    # Docs gate
    if [ ! -d "${repo_dir}/docs_gathered" ] || [ -z "$(ls -A "${repo_dir}/docs_gathered" 2>/dev/null)" ]; then
        log "SKIP: ${repo_name} — docs_gathered/ is missing or empty"
        return 1
    fi

    # Archive previous run
    if [ -d "${repo_dir}/quality" ]; then
        local archive_dir="${repo_dir}/previous_runs/${timestamp}"
        mkdir -p "$archive_dir"
        cp -a "${repo_dir}/quality" "$archive_dir/quality"
        rm -rf "${repo_dir}/quality" "${repo_dir}/control_prompts"
    fi

    mkdir -p "${repo_dir}/control_prompts"
    output_file="${repo_dir}/control_prompts/playbook_run.output.txt"

    local prompt="Read the quality playbook skill at .github/skills/SKILL.md and its reference files in .github/skills/references/. Execute the quality playbook for this project. Additional documentation for this project has been gathered in docs_gathered/ — read it during Phase 1 exploration to supplement the codebase and improve the quality of requirements, scenarios, and tests. IMPORTANT: Before marking Phase 2d complete, run 'bash .github/skills/quality_gate.sh .' and fix any FAIL results. Save the output to quality/results/quality-gate.log."

    if [ "$NO_SEEDS" = true ]; then
        prompt="${prompt} IMPORTANT: Skip Phase 0 and Phase 0b entirely — do not look for previous_runs/ or sibling versioned directories. This is a clean benchmark run testing independent bug discovery. Start directly at Phase 1."
    fi

    logboth "$log_file" "$(log "Starting playbook: ${repo_name} (runner=${RUNNER})")"

    cd "$repo_dir"
    if [ "$RUNNER" = "claude" ]; then
        local claude_args=(-p "$prompt" --dangerously-skip-permissions)
        [ -n "$CLAUDE_MODEL" ] && claude_args=(--model "$CLAUDE_MODEL" "${claude_args[@]}")
        script -q "$output_file" claude "${claude_args[@]}" 2>&1
    else
        $COPILOT -p "$prompt" --model "$MODEL" --yolo > "$output_file" 2>&1
    fi
    cd "$SCRIPT_DIR"

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
