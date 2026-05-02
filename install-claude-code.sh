#!/usr/bin/env bash
# Compatibility wrapper for the canonical Quality Playbook installer.
#
# Usage:
#   install-claude-code.sh [--dry-run] <target-project-dir>

set -euo pipefail

# Resolve the source directory, following symlinks without readlink -f so this
# works from symlinked locations on macOS.
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
installer="$src/install-quality-playbook.sh"

if [[ ! -x "$installer" ]]; then
    echo "Error: canonical installer not found or not executable: $installer" >&2
    exit 1
fi

for arg in "$@"; do
    case "$arg" in
        --layout|--layout=*)
            echo "Error: install-claude-code.sh always uses --layout claude" >&2
            exit 2
            ;;
    esac
done

exec "$installer" --layout claude "$@"
