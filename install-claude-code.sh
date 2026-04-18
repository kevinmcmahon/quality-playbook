#!/usr/bin/env bash
# Install the Quality Playbook skill into a target project directory for use
# with Claude Code. Mirrors the install steps documented in README.md Step 2.
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
(alongside SKILL.md and references/). Clone it with:

    git clone https://github.com/andrewstellman/quality-playbook.git

Then either run the script from the clone directly, or symlink it onto
your PATH, e.g.:

    ln -s /path/to/quality-playbook/install-claude-code.sh ~/tools/install-quality-playbook
EOF
    exit 1
fi

for required in SKILL.md references; do
    if [[ ! -e "$src/$required" ]]; then
        echo "Error: missing source file: $src/$required" >&2
        exit 1
    fi
done

skill_dir="$target/.claude/skills/quality-playbook"

mkdir -p "$skill_dir/references"

cp "$src/SKILL.md" "$skill_dir/SKILL.md"
cp "$src/references/"* "$skill_dir/references/"

echo "Installed Quality Playbook into: $target"
echo "  skill: $skill_dir"
echo ""
echo "Next: open Claude Code in '$target' and say \"Read SKILL.md and run the quality playbook on this project.\""
