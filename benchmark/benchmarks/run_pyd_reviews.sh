#!/bin/bash
# Self-contained PYD review runner
# Runs all 55 defects sequentially, writing progress to a file
set -uo pipefail

REVIEW_PROTOCOL="/sessions/quirky-practical-cerf/mnt/QPB/benchmarks/run_002/pyd/opus/quality/RUN_CODE_REVIEW.md"
REVIEW_DIR="/sessions/quirky-practical-cerf/mnt/QPB/benchmarks/run_002/pyd/opus/code_reviews"
REPO="/sessions/quirky-practical-cerf/mnt/QPB/repos/pydantic"
DATASET="/sessions/quirky-practical-cerf/mnt/QPB/dataset/defects.jsonl"
PROGRESS="/tmp/qpb_pyd_progress.txt"

echo "$(date): Starting PYD reviews" > "$PROGRESS"

DEFECTS=$(python3 -c "
import json
with open('${DATASET}') as f:
    for line in f:
        d = json.loads(line)
        if d['id'].startswith('PYD-'):
            print(d['id'])
")

TOTAL=$(echo "$DEFECTS" | wc -l)
DONE=0

for DEFECT_ID in $DEFECTS; do
    REVIEW_FILE="${REVIEW_DIR}/${DEFECT_ID}_review.md"

    if [ -f "$REVIEW_FILE" ]; then
        DONE=$((DONE + 1))
        echo "$(date): SKIP ${DEFECT_ID} (exists) [${DONE}/${TOTAL}]" >> "$PROGRESS"
        continue
    fi

    COMMIT_INFO=$(python3 -c "
import json, subprocess
with open('${DATASET}') as f:
    for line in f:
        d = json.loads(line)
        if d['id'] == '${DEFECT_ID}':
            pre = d['pre_fix_commit']
            fix = d['fix_commit']
            result = subprocess.run(['git', 'diff', '--name-only', pre, fix],
                                  capture_output=True, text=True, cwd='${REPO}')
            files = result.stdout.strip()
            print(f'{pre}|{files}')
            break
")

    PRE_FIX=$(echo "$COMMIT_INFO" | cut -d'|' -f1)
    ALL_FILES=$(echo "$COMMIT_INFO" | cut -d'|' -f2-)

    FILE_LIST=""
    while IFS= read -r f; do
        [ -z "$f" ] && continue
        FILE_LIST="${FILE_LIST}
- ${f}"
    done <<< "$ALL_FILES"

    if [ -z "$FILE_LIST" ]; then
        DONE=$((DONE + 1))
        echo "$(date): SKIP ${DEFECT_ID} (no files) [${DONE}/${TOTAL}]" >> "$PROGRESS"
        continue
    fi

    WORKTREE="/tmp/qpb_wt_opus_${DEFECT_ID}"
    cd "$REPO"
    git worktree remove --force "$WORKTREE" 2>/dev/null || true
    git worktree add --quiet --detach "$WORKTREE" "$PRE_FIX" 2>/dev/null

    echo "$(date): START ${DEFECT_ID} [${DONE}/${TOTAL}]" >> "$PROGRESS"

    timeout 600 claude --model opus -p "You are performing a targeted code review.

First, read the code review protocol at ${REVIEW_PROTOCOL} and understand the guardrails and focus areas.

Then review these specific files in the project at ${WORKTREE}:
${FILE_LIST}

Follow the code review protocol guardrails exactly:
- Line numbers are mandatory for every finding
- Read function bodies, not just signatures
- If unsure, flag as QUESTION not BUG
- Grep before claiming something is missing
- Do NOT suggest style changes, refactors, or improvements

Report ALL bugs you find. Save findings to ${REVIEW_FILE}" \
    --allowedTools "Read,Write,Grep,Glob" > "${REVIEW_DIR}/${DEFECT_ID}.stdout" 2>&1 || true

    cd "$REPO"
    git worktree remove --force "$WORKTREE" 2>/dev/null || true

    DONE=$((DONE + 1))
    if [ -f "$REVIEW_FILE" ]; then
        LINES=$(wc -l < "$REVIEW_FILE")
        echo "$(date): DONE ${DEFECT_ID} (${LINES} lines) [${DONE}/${TOTAL}]" >> "$PROGRESS"
    else
        echo "$(date): FAIL ${DEFECT_ID} [${DONE}/${TOTAL}]" >> "$PROGRESS"
    fi
done

echo "$(date): COMPLETE ${DONE}/${TOTAL}" >> "$PROGRESS"
