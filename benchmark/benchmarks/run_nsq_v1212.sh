#!/bin/bash
# NSQ full benchmark with v1.2.12 generated protocol
# Tests all 57 defects (excluding NSQ-42) against the v1.2.12 generated RUN_CODE_REVIEW.md
set -uo pipefail

REVIEW_DIR="/sessions/quirky-practical-cerf/mnt/QPB/benchmarks/run_002/nsq/opus_v1212/code_reviews"
REPO="/sessions/quirky-practical-cerf/mnt/QPB/repos/nsq"
DATASET="/sessions/quirky-practical-cerf/mnt/QPB/dataset/defects.jsonl"
PROGRESS="/tmp/qpb_nsq_v1212_progress.txt"
REVIEW_PROTOCOL="/sessions/quirky-practical-cerf/mnt/QPB/benchmarks/run_002/nsq/opus_v1212/quality/RUN_CODE_REVIEW.md"

mkdir -p "$REVIEW_DIR"

# Get all NSQ defect IDs except NSQ-42
DEFECTS=$(python3 -c "
import json
with open('${DATASET}') as f:
    for line in f:
        d = json.loads(line)
        if d['id'].startswith('NSQ-') and d['id'] != 'NSQ-42':
            print(d['id'])
")

TOTAL=$(echo "$DEFECTS" | wc -l | tr -d ' ')
DONE=0

echo "$(date): Starting NSQ v1.2.12 benchmark (${TOTAL} defects)" > "$PROGRESS"

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

    WORKTREE="/tmp/qpb_wt_v1212_${DEFECT_ID}"
    cd "$REPO"
    git worktree remove --force "$WORKTREE" 2>/dev/null || true
    git worktree add --quiet --detach "$WORKTREE" "$PRE_FIX" 2>/dev/null

    echo "$(date): START ${DEFECT_ID} [${DONE}/${TOTAL}]" >> "$PROGRESS"

    timeout 480 /usr/local/bin/claude --model opus -p "Targeted code review. Review these files at ${WORKTREE}:
${FILE_LIST}

First read the review protocol at ${REVIEW_PROTOCOL} for focus areas and guardrails.

Key guardrails:
- Line numbers mandatory for every finding
- Read function bodies, not just signatures
- Flag uncertain findings as QUESTION not BUG
- No style changes — only bugs and correctness issues
- Check validation failure modes, not just validation existence
- Enumerate all resource types in Exit()
- Audit configuration parameter completeness

For each finding: BUG/QUESTION, file, line number, severity (Critical/High/Medium/Low), description.
Save to ${REVIEW_FILE}" \
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
