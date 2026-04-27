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

# Resolve the playbook source directory (where this script actually lives),
# following symlinks so this works from ~/tools or anywhere on PATH. Avoid
# readlink -f because macOS readlink does not support it.
script="${BASH_SOURCE[0]}"
while [[ -L "$script" ]]; do
    script_dir="$(cd -P "$(dirname "$script")" >/dev/null 2>&1 && pwd)"
    link="$(readlink "$script")"
    if [[ "$link" == /* ]]; then
        script="$link"
    else
        script="$script_dir/$link"
    fi
done
src="$(cd -P "$(dirname "$script")" >/dev/null 2>&1 && pwd)"

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

for required in SKILL.md references agents .github/skills/quality_gate/quality_gate.py; do
    if [[ ! -e "$src/$required" ]]; then
        echo "Error: missing source file: $src/$required" >&2
        exit 1
    fi
done

skill_dir="$target/.claude/skills/quality-playbook"
agents_dir="$target/agents"
reference_docs_dir="$target/reference_docs"

# Clean-and-replace: wipe anything we own so stale files from a previous
# install can't contradict the new upstream content. User state — the
# generated quality/ directory and AGENTS.md at the target root — is
# untouched.
removed_skill=false
if [[ -d "$skill_dir" ]]; then
    rm -rf "$skill_dir"
    removed_skill=true
fi

removed_agents=()
if [[ -d "$agents_dir" ]]; then
    while IFS= read -r -d '' f; do
        removed_agents+=("$f")
        rm -f "$f"
    done < <(find "$agents_dir" -maxdepth 1 -name 'quality-playbook*.agent.md' -print0 2>/dev/null)
fi

mkdir -p "$skill_dir/references"
mkdir -p "$agents_dir"
mkdir -p "$reference_docs_dir/cite"

cp "$src/SKILL.md" "$skill_dir/SKILL.md"
cp "$src/references/"* "$skill_dir/references/"
cp "$src/agents/"* "$agents_dir/"
cp "$src/.github/skills/quality_gate/quality_gate.py" "$skill_dir/quality_gate.py"
chmod +x "$skill_dir/quality_gate.py"

echo "Installed Quality Playbook into: $target"
echo "  skill:  $skill_dir"
echo "  agents: $agents_dir"
echo "  gate:   $skill_dir/quality_gate.py"
echo "  docs:   $reference_docs_dir"
if [[ "$removed_skill" = true ]] || [[ ${#removed_agents[@]} -gt 0 ]]; then
    echo ""
    echo "Replaced from previous install:"
    [[ "$removed_skill" = true ]] && echo "  - $skill_dir (wiped and recreated)"
    for f in ${removed_agents[@]+"${removed_agents[@]}"}; do
        echo "  - $f"
    done
fi
echo ""
echo "Next: open Claude Code in '$target' and say \"Read SKILL.md and run the quality playbook on this project.\""
