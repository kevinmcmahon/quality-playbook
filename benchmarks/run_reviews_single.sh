#!/bin/bash
# Run targeted code reviews for a single model against all defects for a repo
# Usage: ./run_reviews_single.sh <model> <repo_prefix> <repo_path> <review_protocol> <review_dir>
#
# Runs sequentially to avoid overwhelming Claude Code. Uses git worktrees for isolation.

set -euo pipefail

MODEL="$1"
REPO_PREFIX="$2"
REPO_PATH="$3"
REVIEW_PROTOCOL="$4"
REVIEW_DIR="$5"
DATASET="/sessions/quirky-practical-cerf/mnt/QPB/dataset/defects.jsonl"
PROGRESS_FILE="/tmp/qpb_progress_${MODEL}_${REPO_PREFIX}.txt"

echo "Starting reviews: model=${MODEL} repo=${REPO_PREFIX}" | tee "$PROGRESS_FILE"

# Get defect list
DEFECTS=$(python3 -c "
import json
with open('${DATASET}') as f:
    for line in f:
        d = json.loads(line)
        if d['id'].startswith('${REPO_PREFIX}-'):
            print(d['id'])
")

TOTAL=$(echo "$DEFECTS" | wc -l)
DONE=0
SKIPPED=0

for DEFECT_ID in $DEFECTS; do
    REVIEW_FILE="${REVIEW_DIR}/${DEFECT_ID}_review.md"

    # Skip if already done
    if [ -f "$REVIEW_FILE" ]; then
        DONE=$((DONE + 1))
        echo "SKIP ${DEFECT_ID} (already done) [${DONE}/${TOTAL}]" | tee -a "$PROGRESS_FILE"
        continue
    fi

    # Get commit info and files
    COMMIT_INFO=$(python3 -c "
import json, subprocess
with open('${DATASET}') as f:
    for line in f:
        d = json.loads(line)
        if d['id'] == '${DEFECT_ID}':
            pre = d['pre_fix_commit']
            fix = d['fix_commit']
            result = subprocess.run(['git', 'diff', '--name-only', pre, fix],
                                  capture_output=True, text=True, cwd='${REPO_PATH}')
            files = result.stdout.strip()
            print(f'{pre}|{fix}|{files}')
            break
")

    PRE_FIX=$(echo "$COMMIT_INFO" | cut -d'|' -f1)
    FIX_COMMIT=$(echo "$COMMIT_INFO" | cut -d'|' -f2)
    ALL_FILES=$(echo "$COMMIT_INFO" | cut -d'|' -f3)

    # Include both source and test files (lesson from CHI-12)
    FILE_LIST=""
    while IFS= read -r f; do
        [ -z "$f" ] && continue
        FILE_LIST="${FILE_LIST}
- ${f}"
    done <<< "$ALL_FILES"

    if [ -z "$FILE_LIST" ]; then
        echo "SKIP ${DEFECT_ID} (no files) [${DONE}/${TOTAL}]" | tee -a "$PROGRESS_FILE"
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    # Create worktree
    WORKTREE="/tmp/qpb_wt_${MODEL}_${DEFECT_ID}"
    cd "$REPO_PATH"
    git worktree remove --force "$WORKTREE" 2>/dev/null || true
    git worktree add --quiet --detach "$WORKTREE" "$PRE_FIX" 2>/dev/null

    echo "REVIEW ${DEFECT_ID} [${DONE}/${TOTAL}] files:${FILE_LIST}" | tee -a "$PROGRESS_FILE"

    # Run review
    claude --model "$MODEL" -p "You are performing a targeted code review.

First, read the code review protocol at ${REVIEW_PROTOCOL} and understand the guardrails and focus areas.

Then review these specific files in the project at ${WORKTREE}:
${FILE_LIST}

Follow the code review protocol guardrails exactly:
- Line numbers are mandatory for every finding
- Read function bodies, not just signatures
- If unsure, flag as QUESTION not BUG
- Grep before claiming something is missing
- Do NOT suggest style changes, refactors, or improvements

Report ALL bugs you find. For each finding:
- Finding type: BUG / QUESTION / SUGGESTION
- File and line number
- Severity: Critical / High / Medium / Low
- Description of what is wrong

Save your findings to ${REVIEW_FILE}" \
    --allowedTools "Read,Write,Grep,Glob" > "${REVIEW_DIR}/${DEFECT_ID}.stdout" 2>&1 || true

    # Clean up worktree
    cd "$REPO_PATH"
    git worktree remove --force "$WORKTREE" 2>/dev/null || true

    DONE=$((DONE + 1))

    if [ -f "$REVIEW_FILE" ]; then
        LINES=$(wc -l < "$REVIEW_FILE")
        echo "DONE ${DEFECT_ID} (${LINES} lines) [${DONE}/${TOTAL}]" | tee -a "$PROGRESS_FILE"
    else
        echo "FAIL ${DEFECT_ID} (no output) [${DONE}/${TOTAL}]" | tee -a "$PROGRESS_FILE"
    fi
done

echo "COMPLETE: ${DONE}/${TOTAL} done, ${SKIPPED} skipped" | tee -a "$PROGRESS_FILE"
