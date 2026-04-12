#!/bin/bash
# Create pristine shallow clones of repos listed in repos.json.
#
# Reads the "repos" section of repos.json (GitHub repos only — kernel subsystems
# are handled by create_clean_kernel.sh). Each clone contains only upstream source
# code — no quality/, no docs_gathered/, no control_prompts/, no AGENTS.md.
#
# Usage:
#   ./create_clean_repos.sh              # All repos in repos.json
#   ./create_clean_repos.sh chi httpx    # Specific repos
#   ./create_clean_repos.sh --benchmark  # Only repos with in_benchmark=true
#   ./create_clean_repos.sh --force chi  # Re-clone even if clean/chi exists
#
# Requires: git, jq
#
# After this, run:
#   ./setup_repos.sh chi httpx    # Creates versioned copies from clean/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLEAN_DIR="${SCRIPT_DIR}/clean"
MANIFEST="${SCRIPT_DIR}/repos.json"

if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: repos.json not found at $MANIFEST"
    exit 1
fi

if ! command -v jq &>/dev/null; then
    echo "ERROR: jq is required. Install with: brew install jq"
    exit 1
fi

FORCE=false
BENCHMARK_ONLY=false
POSITIONAL=()

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=true ;;
        --benchmark) BENCHMARK_ONLY=true ;;
        --help|-h)
            echo "Usage: $0 [--benchmark] [--force] [repo1 repo2 ...]"
            echo "  --benchmark: only clone repos with in_benchmark=true"
            echo "  --force: re-clone even if clean/<repo> already exists"
            echo "  repo names: only clone these specific repos"
            exit 0
            ;;
        *) POSITIONAL+=("$arg") ;;
    esac
done

log() { echo "$(date +%H:%M:%S) $1"; }

# Build the list of repos to process
if [ ${#POSITIONAL[@]} -gt 0 ]; then
    REPOS=("${POSITIONAL[@]}")
else
    if [ "$BENCHMARK_ONLY" = true ]; then
        IFS=$'\n' read -r -d '' -a REPOS < <(jq -r '.repos | to_entries[] | select(.value.in_benchmark == true) | .key' "$MANIFEST" && printf '\0') || true
    else
        IFS=$'\n' read -r -d '' -a REPOS < <(jq -r '.repos | keys[]' "$MANIFEST" | grep -v '^_' && printf '\0') || true
    fi
fi

clone_repo() {
    local name="$1"
    local dest="${CLEAN_DIR}/${name}"

    # Read repo config from manifest
    local url branch pin_commit special_handling
    url=$(jq -r ".repos[\"$name\"].github_url // empty" "$MANIFEST")
    branch=$(jq -r ".repos[\"$name\"].branch // \"main\"" "$MANIFEST")
    pin_commit=$(jq -r ".repos[\"$name\"].pin_commit // empty" "$MANIFEST")
    special_handling=$(jq -r ".repos[\"$name\"].special_handling // empty" "$MANIFEST")

    if [ -z "$url" ] || [ "$url" = "null" ]; then
        log "SKIP $name — no github_url in repos.json"
        return
    fi

    if [ -d "$dest" ] && [ "$FORCE" = false ]; then
        log "EXISTS: $name — use --force to re-clone"
        return
    fi

    if [ -d "$dest" ] && [ "$FORCE" = true ]; then
        log "  Removing existing clean/$name for re-clone..."
        rm -rf "$dest"
    fi

    log "Cloning $name from $url..."

    # Clone
    if [ -n "$pin_commit" ]; then
        # Clone at specific commit — need full fetch then checkout
        git clone --filter=blob:none --no-checkout "$url" "$dest" 2>&1 | tail -1
        git -C "$dest" checkout "$pin_commit" 2>&1 | tail -1
    else
        # Shallow clone of default branch
        git clone --depth 1 --branch "$branch" "$url" "$dest" 2>&1 | tail -1
    fi

    # Record the SHA before removing .git
    local sha
    sha=$(git -C "$dest" rev-parse HEAD)
    rm -rf "$dest/.git"

    # Write provenance file
    cat > "$dest/.clean_checkout" <<PROV
repo: ${name}
url: ${url}
commit: ${sha}
branch: ${branch}
cloned: $(date -u +%Y-%m-%dT%H:%M:%SZ)
script: create_clean_repos.sh
PROV

    # Special handling
    if [ "$special_handling" = "strip_node_modules" ]; then
        rm -rf "$dest/node_modules"
        log "  Stripped node_modules"
    fi

    local size
    size=$(du -sh "$dest" | cut -f1)
    log "  done: $name (${sha:0:12}, ${size})"
}

# --- Main ---

mkdir -p "$CLEAN_DIR"

echo "=== Quality Playbook — Clean Repo Setup ==="
echo "Destination: ${CLEAN_DIR}/"
echo "Repos: ${#REPOS[@]} total"
if [ "$BENCHMARK_ONLY" = true ]; then
    echo "Filter: benchmark repos only"
fi
echo ""

# Check for kernel subsystems in the requested list and warn
for name in "${REPOS[@]}"; do
    is_kernel=$(jq -r ".kernel_subsystems[\"$name\"] // empty" "$MANIFEST")
    if [ -n "$is_kernel" ]; then
        log "SKIP $name — kernel subsystem (use create_clean_kernel.sh instead)"
        continue
    fi

    clone_repo "$name"
done

echo ""
echo "=== Clean repos ready in ${CLEAN_DIR}/ ==="
echo ""
echo "Sizes:"
for name in "${REPOS[@]}"; do
    [ -d "${CLEAN_DIR}/${name}" ] && echo "  ${name}: $(du -sh "${CLEAN_DIR}/${name}" | cut -f1)"
done
