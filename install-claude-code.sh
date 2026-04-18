#!/usr/bin/env bash
# Install the Quality Playbook skill (and orchestrator agent) into a target
# project directory for use with Claude Code.
#
# Usage: ./install-claude-code.sh <target-project-dir>

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <target-project-dir>" >&2
    exit 2
fi

target="$1"

if [[ ! -d "$target" ]]; then
    echo "Error: target directory does not exist: $target" >&2
    exit 1
fi

# Resolve the playbook source directory (where this script actually lives,
# following symlinks so this works from ~/tools or anywhere on PATH).
resolved="$(readlink -f "${BASH_SOURCE[0]}")"
src="$(dirname "$resolved")"

if [[ ! -d "$src" ]]; then
    cat >&2 <<EOF
Error: quality-playbook source directory not found: $src

This script expects to live inside a clone of the quality-playbook repo
(alongside SKILL.md, references/, and agents/). Clone it with:

    git clone https://github.com/andrewstellman/quality-playbook.git

Then either run the script from the clone directly, or symlink it onto
your PATH, e.g.:

    ln -s /path/to/quality-playbook/install-claude-code.sh ~/tools/install-quality-playbook
EOF
    exit 1
fi

for required in SKILL.md LICENSE.txt references agents/quality-playbook-claude.agent.md; do
    if [[ ! -e "$src/$required" ]]; then
        echo "Error: missing source file: $src/$required" >&2
        exit 1
    fi
done

skill_dir="$target/.claude/skills/quality-playbook"
agent_dir="$target/.claude/agents"

mkdir -p "$skill_dir/references" "$agent_dir"

cp "$src/SKILL.md" "$skill_dir/SKILL.md"
cp "$src/LICENSE.txt" "$skill_dir/LICENSE.txt"
cp "$src/references/"* "$skill_dir/references/"
cp "$src/agents/quality-playbook-claude.agent.md" "$agent_dir/"

echo "Installed Quality Playbook into: $target"
echo "  skill: $skill_dir"
echo "  agent: $agent_dir/quality-playbook-claude.agent.md"
echo ""
echo "Next: open Claude Code in '$target' and say \"Run the full playbook\"."
