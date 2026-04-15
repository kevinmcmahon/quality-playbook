#!/bin/bash
# Update existing anthropic/skills PR #659 with quality-playbook v1.4.0
set -euo pipefail

QPB=~/Documents/QPB

# Find skills repo — check common locations
SKILLS=""
for candidate in ~/Documents/AI/skills ~/Documents/skills ~/Projects/skills ~/Code/skills; do
    if [ -d "$candidate/.git" ]; then
        SKILLS="$candidate"
        break
    fi
done

if [ -z "$SKILLS" ]; then
    echo "ERROR: Can't find anthropic/skills repo. Set SKILLS= to the path and rerun."
    exit 1
fi

cd "$SKILLS"
echo "=== Using skills repo at $SKILLS ==="

# Check out the branch backing PR #659
gh pr checkout 659

# Copy updated files
mkdir -p community/quality-playbook/references community/quality-playbook/agents
cp "$QPB/SKILL.md" community/quality-playbook/SKILL.md
cp "$QPB/LICENSE.txt" community/quality-playbook/LICENSE.txt
cp "$QPB/repos/quality_gate.sh" community/quality-playbook/quality_gate.sh
cp "$QPB/references/"* community/quality-playbook/references/
cp "$QPB/agents/"* community/quality-playbook/agents/

# Commit and push to update the PR
git add community/quality-playbook/
git commit -m "Update quality-playbook to v1.4.0 with orchestrator agents"
git push

echo "=== PR #659 updated ==="
