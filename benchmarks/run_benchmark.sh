#!/bin/bash
# QPB Benchmark Runner
# Automates playbook generation and targeted code reviews across models and repos
#
# Usage:
#   ./run_benchmark.sh generate <repo> <model>       # Generate playbook
#   ./run_benchmark.sh review <repo> <model> <defect_id>  # Targeted code review
#   ./run_benchmark.sh review-all <repo> <model>     # Review all defects for repo
#   ./run_benchmark.sh status                        # Show progress

set -euo pipefail

BENCHMARK_DIR="/sessions/quirky-practical-cerf/mnt/QPB/benchmarks"
REPOS_DIR="/sessions/quirky-practical-cerf/mnt/QPB/repos"
DATASET="/sessions/quirky-practical-cerf/mnt/QPB/dataset/defects.jsonl"
PLAYBOOK="${BENCHMARK_DIR}/playbook_v1.2.10"
RUN_DIR="${BENCHMARK_DIR}/run_001"

# Model aliases for claude CLI
declare -A MODEL_FLAGS=(
    [opus]="opus"
    [sonnet]="sonnet"
    [haiku]="haiku"
)

log() {
    echo "[$(date '+%H:%M:%S')] $*"
}

# Get defect IDs for a repo prefix
get_defect_ids() {
    local prefix="$1"
    python3 -c "
import json
with open('${DATASET}') as f:
    for line in f:
        d = json.loads(line)
        if d['id'].startswith('${prefix}-'):
            print(d['id'])
"
}

# Get defect details as JSON
get_defect() {
    local defect_id="$1"
    python3 -c "
import json
with open('${DATASET}') as f:
    for line in f:
        d = json.loads(line)
        if d['id'] == '${defect_id}':
            print(json.dumps(d))
            break
"
}

# Get files changed in a defect's fix commit
get_files_changed() {
    local repo_path="$1"
    local pre_fix="$2"
    local fix_commit="$3"
    cd "$repo_path"
    git diff --name-only "$pre_fix" "$fix_commit" 2>/dev/null
}

# Map repo directory name to defect ID prefix
get_prefix() {
    local repo="$1"
    case "$repo" in
        chi) echo "CHI" ;;
        httpx) echo "HX" ;;
        cobra) echo "COB" ;;
        rq) echo "RQ" ;;
        config) echo "CFG" ;;
        zod) echo "ZOD" ;;
        serde) echo "SER" ;;
        axum) echo "AX" ;;
        *) echo "UNKNOWN" ;;
    esac
}

# Generate playbook for a repo with a specific model
cmd_generate() {
    local repo="$1"
    local model="$2"
    local repo_path="${REPOS_DIR}/${repo}"
    local output_dir="${RUN_DIR}/${repo}/${model}"

    if [ ! -d "$repo_path" ]; then
        echo "ERROR: Repo not found: $repo_path"
        exit 1
    fi

    mkdir -p "$output_dir"

    # Make sure repo is at HEAD
    cd "$repo_path"
    git checkout master 2>/dev/null || git checkout main 2>/dev/null
    cd -

    log "Starting playbook generation: ${repo} × ${model}"
    log "Output: ${output_dir}"

    local start_time=$(date +%s)

    claude --model "${MODEL_FLAGS[$model]}" -p "You are running the Quality Playbook v1.2.10 skill.

First, read the skill file at ${PLAYBOOK}/SKILL.md and ALL reference files in ${PLAYBOOK}/references/. Follow the skill's instructions exactly.

Generate a complete quality playbook for the project at ${repo_path}.

Important instructions:
- This is running in headless/batch mode with no user present
- Skip Step 0 (no chat history available)
- Skip Phase 4 interactive improvement loop
- Complete Phases 1-3 fully (Explore, Generate, Verify)
- Save all generated files to ${output_dir}/
- Create the quality/ subdirectory inside ${output_dir}/ for all quality files
- Create AGENTS.md inside ${output_dir}/
- After Phase 3 verification, output a brief summary: files created, test count, scenario count

Do NOT modify the original repo. All output goes to ${output_dir}/." \
        --allowedTools "Bash,Read,Write,Edit,Glob,Grep" \
        > "${output_dir}/generation.stdout" 2>&1

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log "Completed: ${repo} × ${model} in ${duration}s"

    # Record metadata
    cat > "${output_dir}/metadata.json" <<EOF
{
    "repo": "${repo}",
    "model": "${model}",
    "playbook_version": "1.2.10",
    "phase": "generation",
    "duration_seconds": ${duration},
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

    # Quick validation
    local file_count=$(find "$output_dir" -name "*.md" -o -name "*.go" -o -name "*.py" -o -name "*.java" -o -name "*.ts" | wc -l)
    log "Files generated: ${file_count}"
}

# Run targeted code review for a specific defect
cmd_review() {
    local repo="$1"
    local model="$2"
    local defect_id="$3"
    local repo_path="${REPOS_DIR}/${repo}"
    local output_dir="${RUN_DIR}/${repo}/${model}"
    local review_dir="${output_dir}/code_reviews"
    local review_protocol="${output_dir}/quality/RUN_CODE_REVIEW.md"

    mkdir -p "$review_dir"

    # Get defect details
    local defect_json=$(get_defect "$defect_id")
    if [ -z "$defect_json" ]; then
        echo "ERROR: Defect not found: $defect_id"
        exit 1
    fi

    local pre_fix=$(echo "$defect_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['pre_fix_commit'])")
    local fix_commit=$(echo "$defect_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['fix_commit'])")
    local category=$(echo "$defect_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['category'])")
    local description=$(echo "$defect_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['description'])")

    # Get files changed by the fix
    local files_changed=$(get_files_changed "$repo_path" "$pre_fix" "$fix_commit")
    if [ -z "$files_changed" ]; then
        log "WARNING: No files changed for ${defect_id}, skipping"
        return
    fi

    # Filter to source files only (skip test files for review)
    local source_files=$(echo "$files_changed" | grep -v "_test\." | grep -v "test_" | grep -v "/tests/" | grep -v "Test\." || echo "$files_changed")

    log "Reviewing ${defect_id}: ${category} (${model})"
    log "  Pre-fix: ${pre_fix}, files: ${source_files}"

    # Create a worktree for this review (enables parallel reviews across models)
    local worktree_dir="/tmp/qpb_worktree_${repo}_${model}_$$"
    cd "$repo_path"
    git worktree add --quiet --detach "$worktree_dir" "$pre_fix" 2>/dev/null

    local start_time=$(date +%s)

    # Build file list for the prompt
    local file_list=""
    for f in $source_files; do
        if [ -f "$worktree_dir/$f" ]; then
            file_list="${file_list}\n- ${f}"
        fi
    done

    # Run targeted code review against the worktree
    claude --model "${MODEL_FLAGS[$model]}" -p "You are performing a targeted code review.

First, read the code review protocol at ${review_protocol} and understand the guardrails and focus areas.

Then review these specific files in the project at ${worktree_dir}:
$(echo -e "$file_list")

Follow the code review protocol's guardrails exactly:
- Line numbers are mandatory for every finding
- Read function bodies, not just signatures
- If unsure, flag as QUESTION not BUG
- Grep before claiming something is missing

Report ALL bugs you find. For each finding:
- Finding type: BUG / QUESTION / SUGGESTION
- File and line number
- Severity: Critical / High / Medium / Low
- Description of what's wrong

Save your findings to ${review_dir}/${defect_id}_review.md" \
        --allowedTools "Read,Write,Grep,Glob" \
        > "${review_dir}/${defect_id}.stdout" 2>&1

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Clean up worktree
    cd "$repo_path"
    git worktree remove --force "$worktree_dir" 2>/dev/null || rm -rf "$worktree_dir"

    log "  Completed in ${duration}s"

    # Record metadata
    cat > "${review_dir}/${defect_id}_meta.json" <<EOF
{
    "defect_id": "${defect_id}",
    "model": "${model}",
    "category": "${category}",
    "pre_fix_commit": "${pre_fix}",
    "fix_commit": "${fix_commit}",
    "files_reviewed": "$(echo $source_files | tr '\n' ',')",
    "duration_seconds": ${duration},
    "description": $(echo "$description" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip()))")
}
EOF
}

# Review all defects for a repo with a model
cmd_review_all() {
    local repo="$1"
    local model="$2"
    local prefix=$(get_prefix "$repo")

    log "Starting review-all: ${repo} (${prefix}-*) × ${model}"

    local defect_ids=$(get_defect_ids "$prefix")
    local total=$(echo "$defect_ids" | wc -l)
    local current=0

    for defect_id in $defect_ids; do
        current=$((current + 1))
        log "[${current}/${total}] ${defect_id}"

        # Skip if already reviewed
        local review_file="${RUN_DIR}/${repo}/${model}/code_reviews/${defect_id}_review.md"
        if [ -f "$review_file" ]; then
            log "  Already reviewed, skipping"
            continue
        fi

        cmd_review "$repo" "$model" "$defect_id"
    done

    log "Completed review-all: ${repo} × ${model} (${total} defects)"
}

# Show progress
cmd_status() {
    echo "=== QPB Benchmark Status ==="
    echo ""
    for repo_dir in "${RUN_DIR}"/*/; do
        [ -d "$repo_dir" ] || continue
        local repo=$(basename "$repo_dir")
        echo "Repo: ${repo}"
        for model_dir in "${repo_dir}"/*/; do
            [ -d "$model_dir" ] || continue
            local model=$(basename "$model_dir")
            local has_playbook="no"
            local test_count=0
            local review_count=0

            [ -f "${model_dir}/quality/QUALITY.md" ] && has_playbook="yes"
            test_count=$(grep -c "func Test\|def test_\|it(" "${model_dir}/quality/"* 2>/dev/null | tail -1 | cut -d: -f2 || echo 0)
            review_count=$(ls "${model_dir}/code_reviews/"*_review.md 2>/dev/null | wc -l || echo 0)

            echo "  ${model}: playbook=${has_playbook}, tests=${test_count}, reviews=${review_count}"
        done
        echo ""
    done
}

# Main dispatch
case "${1:-}" in
    generate)
        cmd_generate "${2:?repo required}" "${3:?model required}"
        ;;
    review)
        cmd_review "${2:?repo required}" "${3:?model required}" "${4:?defect_id required}"
        ;;
    review-all)
        cmd_review_all "${2:?repo required}" "${3:?model required}"
        ;;
    status)
        cmd_status
        ;;
    *)
        echo "Usage:"
        echo "  $0 generate <repo> <model>            # Generate playbook"
        echo "  $0 review <repo> <model> <defect_id>  # Review one defect"
        echo "  $0 review-all <repo> <model>           # Review all defects"
        echo "  $0 status                              # Show progress"
        echo ""
        echo "Models: opus, sonnet, haiku"
        echo "Repos: chi, httpx, cobra, rq, config"
        exit 1
        ;;
esac
