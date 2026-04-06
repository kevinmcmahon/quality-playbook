#!/bin/bash
# Sequential review runner for a single model
# Usage: ./run_reviews.sh <repo> <model>
# Writes progress to /tmp/qpb_progress_<model>.txt

set -euo pipefail

BENCHMARK_DIR="/sessions/quirky-practical-cerf/mnt/QPB/benchmarks"
REPOS_DIR="/sessions/quirky-practical-cerf/mnt/QPB/repos"
DATASET="/sessions/quirky-practical-cerf/mnt/QPB/dataset/defects.jsonl"

repo="$1"
model="$2"
progress_file="/tmp/qpb_progress_${model}.txt"

# Map repo to prefix
case "$repo" in
    chi) prefix="CHI" ;;
    httpx) prefix="HX" ;;
    cobra) prefix="COB" ;;
    rq) prefix="RQ" ;;
    config) prefix="CFG" ;;
    *) echo "Unknown repo: $repo"; exit 1 ;;
esac

output_dir="${BENCHMARK_DIR}/run_001/${repo}/${model}"
review_dir="${output_dir}/code_reviews"
review_protocol="${output_dir}/quality/RUN_CODE_REVIEW.md"
repo_path="${REPOS_DIR}/${repo}"

mkdir -p "$review_dir"

# Get all defect IDs
defect_ids=$(python3 -c "
import json
with open('${DATASET}') as f:
    for line in f:
        d = json.loads(line)
        if d['id'].startswith('${prefix}-'):
            print(d['id'])
")

total=$(echo "$defect_ids" | wc -l)
current=0

echo "0/${total}" > "$progress_file"

for defect_id in $defect_ids; do
    current=$((current + 1))

    # Skip if already reviewed
    if [ -f "${review_dir}/${defect_id}_review.md" ]; then
        echo "${current}/${total} SKIP ${defect_id}" >> "$progress_file"
        continue
    fi

    # Get defect details
    defect_json=$(python3 -c "
import json
with open('${DATASET}') as f:
    for line in f:
        d = json.loads(line)
        if d['id'] == '${defect_id}':
            print(json.dumps(d))
            break
")

    pre_fix=$(echo "$defect_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['pre_fix_commit'])")
    fix_commit=$(echo "$defect_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['fix_commit'])")
    category=$(echo "$defect_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['category'])")
    description=$(echo "$defect_json" | python3 -c "import json,sys; print(json.load(sys.stdin)['description'])")

    # Get files changed
    cd "$repo_path"
    files_changed=$(git diff --name-only "$pre_fix" "$fix_commit" 2>/dev/null || true)

    if [ -z "$files_changed" ]; then
        echo "${current}/${total} NOFILES ${defect_id}" >> "$progress_file"
        continue
    fi

    # Filter to source files
    source_files=$(echo "$files_changed" | grep -v "_test\." | grep -v "test_" | grep -v "/tests/" | grep -v "Test\." || echo "$files_changed")

    # Create worktree
    worktree_dir="/tmp/qpb_wt_${repo}_${model}_${defect_id}"
    cd "$repo_path"
    git worktree add --quiet --detach "$worktree_dir" "$pre_fix" 2>/dev/null || {
        echo "${current}/${total} WTFAIL ${defect_id}" >> "$progress_file"
        continue
    }

    # Build file list
    file_list=""
    for f in $source_files; do
        if [ -f "$worktree_dir/$f" ]; then
            file_list="${file_list}
- ${f}"
        fi
    done

    start_time=$(date +%s)

    echo "${current}/${total} RUNNING ${defect_id}" > "$progress_file"

    # Run review
    claude --model "$model" -p "You are performing a targeted code review.

First, read the code review protocol at ${review_protocol} and understand the guardrails and focus areas.

Then review these specific files in the project at ${worktree_dir}:
${file_list}

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
        > "${review_dir}/${defect_id}.stdout" 2>&1 || true

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Clean up worktree
    cd "$repo_path"
    git worktree remove --force "$worktree_dir" 2>/dev/null || rm -rf "$worktree_dir"

    # Record metadata
    cat > "${review_dir}/${defect_id}_meta.json" <<METAEOF
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
METAEOF

    # Check if review was created
    if [ -f "${review_dir}/${defect_id}_review.md" ]; then
        echo "${current}/${total} DONE ${defect_id} ${duration}s" >> "$progress_file"
    else
        echo "${current}/${total} NOREVIEW ${defect_id} ${duration}s" >> "$progress_file"
    fi
done

echo "COMPLETE ${current}/${total}" >> "$progress_file"
