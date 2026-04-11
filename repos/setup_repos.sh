#!/bin/bash
# Set up benchmark repos for the current SKILL.md version.
#
# Creates versioned copies from the most recent prior version, cleans stale
# artifacts, installs the current SKILL.md + references, verifies docs_gathered.
#
# Each repo is placed in its own isolated subdirectory under a run folder
# so that Phase 0b sibling-run seeding cannot find prior versioned siblings.
# This ensures benchmarks test independent bug discovery, not confirmation.
#
# Usage:
#   ./setup_repos.sh              # All known repos
#   ./setup_repos.sh chi httpx    # Specific repos
#
# After setup, run:
#   ./run_playbook.sh chi httpx

set -euo pipefail
source "$(dirname "$0")/_benchmark_lib.sh"

ALL_REPOS=(chi cobra express gson httpx javalin serde zod virtio okhttp axum pydantic)

if [ $# -gt 0 ]; then
    REPOS=("$@")
else
    REPOS=("${ALL_REPOS[@]}")
fi

VERSION=$(detect_skill_version)
[ -z "$VERSION" ] && echo "ERROR: Can't detect version from SKILL.md" && exit 1

echo "=== Quality Playbook — Repo Setup ==="
echo "Version: ${VERSION}"
echo "Repos:   ${REPOS[*]}"
echo ""

# Helper: extract numeric version from a directory name like "httpx-1.3.21"
# Returns the version string (e.g., "1.3.21") for sorting.
extract_version() {
    local dirname
    dirname=$(basename "$1")
    echo "$dirname" | sed -E 's/^[^-]+-//'
}

# Helper: compare two version strings numerically.
# Returns 0 if $1 >= $2, 1 otherwise.
version_ge() {
    # Use sort -V (version sort) to determine ordering
    local higher
    higher=$(printf '%s\n%s\n' "$1" "$2" | sort -V | tail -1)
    [ "$higher" = "$1" ]
}

for short in "${REPOS[@]}"; do
    dst="${SCRIPT_DIR}/${short}-${VERSION}"

    # Find prior version to copy from using numeric version sorting.
    # Iterate all versioned dirs and pick the one with the highest version
    # that isn't the target version.
    src=""
    src_version=""
    for candidate in "${SCRIPT_DIR}/${short}"-[0-9]*; do
        [ -d "$candidate" ] || continue
        [ "$candidate" = "$dst" ] && continue
        cand_ver=$(extract_version "$candidate")
        if [ -z "$src_version" ] || version_ge "$cand_ver" "$src_version"; then
            src="$candidate"
            src_version="$cand_ver"
        fi
    done

    if [ -z "$src" ]; then
        log "SKIP: ${short} — no prior version directory to copy from"
        continue
    fi

    [ -d "$dst" ] && log "EXISTS: removing ${dst}" && rm -rf "$dst"

    log "Copying $(basename "$src") → $(basename "$dst")"
    cp -a "$src" "$dst"

    rm -rf "${dst}/quality" "${dst}/control_prompts" "${dst}/previous_runs"
    rm -f "${dst}/playbook_progress.txt"

    mkdir -p "${dst}/.github/skills/references"
    cp "${QPB_DIR}/SKILL.md" "${dst}/.github/skills/SKILL.md"
    cp "${QPB_DIR}/references/"* "${dst}/.github/skills/references/" 2>/dev/null || true
    cp "${QPB_DIR}/LICENSE.txt" "${dst}/.github/skills/LICENSE.txt" 2>/dev/null || true
    cp "${SCRIPT_DIR}/quality_gate.sh" "${dst}/.github/skills/quality_gate.sh" 2>/dev/null || true

    if [ -d "${dst}/docs_gathered" ] && [ -n "$(ls -A "${dst}/docs_gathered" 2>/dev/null)" ]; then
        doc_count=$(ls -1 "${dst}/docs_gathered" | wc -l | tr -d ' ')
        doc_size=$(du -sh "${dst}/docs_gathered" | cut -f1)
        log "  docs_gathered: ${doc_count} files (${doc_size})"
    else
        log "  WARNING: docs_gathered/ is missing or empty"
    fi

    log "  ✓ ${short}-${VERSION} ready"
    echo ""
done

echo "=== Setup complete. Next: ./run_playbook.sh ${REPOS[*]} ==="
