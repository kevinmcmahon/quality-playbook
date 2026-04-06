#!/bin/bash
# Requirements Validation Experiment
# 4 conditions × 16 defects = 64 runs via Copilot CLI
#
# Conditions:
#   control  — generic review prompt (baseline)
#   specific — precise testable requirements per defect
#   abstract — higher-abstraction requirements (what the playbook would generate)
#   v1212    — v1.2.12 focus-area-based review protocol
#
# Usage:
#   cd <nsq-repo-root>
#   bash /path/to/run_experiment.sh [condition]
#
# If [condition] is specified, only that condition runs (control|specific|abstract|v1212).
# Otherwise all four conditions run.
#
# Prerequisites:
#   - gh copilot must be installed and working
#   - Must be run from the NSQ repo root (the one with nsqd/, nsqadmin/, etc.)
#   - All review output dirs must exist (the script creates them)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/experiment_progress.txt"

CONDITIONS="${1:-control specific abstract v1212}"

# Verify gh copilot
if ! gh copilot --help &>/dev/null; then
    echo "ERROR: 'gh copilot' not available. Install with: gh extension install github/gh-copilot"
    exit 1
fi

COPILOT="gh copilot"
echo "Using: $COPILOT"
echo "$(date): Starting requirements validation experiment" > "$LOG_FILE"
echo "$(date): Conditions: $CONDITIONS" >> "$LOG_FILE"

# Defect IDs in order
DEFECTS=(NSQ-04 NSQ-12 NSQ-14 NSQ-19 NSQ-22 NSQ-33 NSQ-36 NSQ-37 NSQ-39 NSQ-41 NSQ-42 NSQ-44 NSQ-47 NSQ-48 NSQ-50 NSQ-55)

for condition in $CONDITIONS; do
    prompt_dir="${SCRIPT_DIR}/prompts_${condition}"
    review_dir="${SCRIPT_DIR}/reviews_${condition}"
    output_dir="${SCRIPT_DIR}/outputs_${condition}"

    mkdir -p "$review_dir" "$output_dir"

    echo ""
    echo "=== Condition: ${condition} ==="
    echo "$(date): === Starting condition: ${condition} ===" >> "$LOG_FILE"

    for did in "${DEFECTS[@]}"; do
        prompt_file="${prompt_dir}/${did}.md"
        output_file="${output_dir}/${did}.output.txt"

        if [[ ! -f "$prompt_file" ]]; then
            echo "WARN: Missing prompt ${prompt_file}"
            continue
        fi

        # Skip if already completed
        if [[ -f "$output_file" ]] && ! grep -q "command not found" "$output_file" 2>/dev/null; then
            lines=$(wc -l < "$output_file")
            if [[ "$lines" -gt 5 ]]; then
                echo "$(date): SKIP ${condition}/${did} (output exists, ${lines} lines)" | tee -a "$LOG_FILE"
                continue
            fi
        fi

        echo "$(date): START ${condition}/${did}" | tee -a "$LOG_FILE"

        if $COPILOT -p "Read and execute the instructions in ${prompt_file}" \
            --model gpt-5.4 \
            --yolo \
            > "$output_file" 2>&1; then
            lines=$(wc -l < "$output_file")
            echo "$(date): DONE ${condition}/${did} (${lines} lines)" | tee -a "$LOG_FILE"
        else
            echo "$(date): FAIL ${condition}/${did} (exit $?)" | tee -a "$LOG_FILE"
        fi

        # Brief pause to avoid rate limiting
        sleep 2
    done

    echo "$(date): === Completed condition: ${condition} ===" >> "$LOG_FILE"
done

echo ""
echo "$(date): EXPERIMENT COMPLETE" | tee -a "$LOG_FILE"

# Summary
echo ""
echo "=== Summary ==="
for condition in $CONDITIONS; do
    output_dir="${SCRIPT_DIR}/outputs_${condition}"
    total=$(ls "${output_dir}"/*.output.txt 2>/dev/null | wc -l)
    echo "${condition}: ${total}/16 outputs"
done
