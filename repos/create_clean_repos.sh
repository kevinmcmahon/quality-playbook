#!/bin/bash
# Create pristine shallow clones of all benchmark repos in clean/.
#
# Each clone contains only upstream source code — no quality/, no docs_gathered/,
# no control_prompts/, no AGENTS.md. The docs_gathered/ directory is maintained
# separately in repos/docs_gathered/<repo>/ and copied in by setup_repos.sh.
#
# Pin to exact commits so benchmark runs are reproducible. These are the same
# commits used since the earliest benchmark versions.
#
# Usage:
#   ./create_clean_repos.sh              # All repos
#   ./create_clean_repos.sh chi httpx    # Specific repos
#
# Requires: git
#
# After this, run:
#   ./setup_repos.sh chi httpx    # Creates versioned copies from clean/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLEAN_DIR="${SCRIPT_DIR}/clean"

# --- Repo definitions ---
# Format: name|url|commit|branch|special_handling
REPO_DEFS=(
    "chi|https://github.com/go-chi/chi.git||main|"
    "cobra|https://github.com/spf13/cobra.git|61968e893eee2f27696c2fbc8e34fa5c4afaf7c4|main|"
    "express|https://github.com/expressjs/express.git||master|strip_node_modules"
    "gson|https://github.com/google/gson.git||main|"
    "httpx|https://github.com/encode/httpx.git|b5addb64f0161ff6bfe94c124ef76f6a1fba5254|master|"
    "javalin|https://github.com/javalin/javalin.git||main|"
    "serde|https://github.com/serde-rs/serde.git|fa7da4a93567ed347ad0735c28e439fca688ef26|master|"
    "virtio|https://github.com/torvalds/linux.git|bfe62a454542cfad3379f6ef5680b125f41e20f4|master|linux_virtio_extract"
)

# Parse a repo definition string
parse_def() {
    local def="$1"
    REPO_NAME=$(echo "$def" | cut -d'|' -f1)
    REPO_URL=$(echo "$def" | cut -d'|' -f2)
    REPO_COMMIT=$(echo "$def" | cut -d'|' -f3)
    REPO_BRANCH=$(echo "$def" | cut -d'|' -f4)
    REPO_SPECIAL=$(echo "$def" | cut -d'|' -f5)
}

log() { echo "$(date +%H:%M:%S) $1"; }

clone_repo() {
    local name="$1" url="$2" commit="$3" branch="$4" special="$5"
    local dest="${CLEAN_DIR}/${name}"

    if [ -d "$dest" ]; then
        log "EXISTS: ${name} — remove clean/${name} to re-clone"
        return
    fi

    log "Cloning ${name} from ${url}..."

    if [ "$special" = "linux_virtio_extract" ]; then
        clone_virtio "$name" "$url" "$commit" "$branch" "$dest"
        return
    fi

    # Standard shallow clone
    if [ -n "$commit" ]; then
        # Clone at specific commit — need full fetch then checkout
        git clone --filter=blob:none --no-checkout "$url" "$dest" 2>&1 | tail -1
        git -C "$dest" checkout "$commit" 2>&1 | tail -1
    else
        # Shallow clone of default branch
        git clone --depth 1 --branch "$branch" "$url" "$dest" 2>&1 | tail -1
    fi

    # Remove .git to save space — we have the commit SHA recorded above
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
    if [ "$special" = "strip_node_modules" ]; then
        rm -rf "$dest/node_modules"
        log "  Stripped node_modules"
    fi

    local size
    size=$(du -sh "$dest" | cut -f1)
    log "  ✓ ${name} ready (${sha:0:12}, ${size})"
}

clone_virtio() {
    local name="$1" url="$2" commit="$3" branch="$4" dest="$5"

    # Sparse checkout of just the virtio-related files from the Linux kernel
    local tmpdir="${CLEAN_DIR}/.virtio_tmp"
    rm -rf "$tmpdir"

    log "  Sparse checkout of Linux kernel virtio subsystem..."
    git clone --filter=blob:none --no-checkout --sparse "$url" "$tmpdir" 2>&1 | tail -1

    cd "$tmpdir"
    git sparse-checkout set drivers/virtio include/linux/virtio*.h include/uapi/linux/virtio*.h
    if [ -n "$commit" ]; then
        git checkout "$commit" 2>&1 | tail -1
    else
        git checkout "$branch" 2>&1 | tail -1
    fi

    local sha
    sha=$(git rev-parse HEAD)
    cd "$SCRIPT_DIR"

    # Extract just the virtio files into clean destination
    mkdir -p "$dest"
    cp -a "$tmpdir/drivers" "$dest/"
    cp -a "$tmpdir/include" "$dest/"

    # Strip large files that blow up the context window
    rm -f "$dest/drivers/virtio/MAINTAINERS" 2>/dev/null
    rm -f "$dest/CREDITS" "$dest/.mailmap" "$dest/Makefile" 2>/dev/null
    rm -rf "$dest/Documentation" 2>/dev/null

    # Remove .git and temp
    rm -rf "$tmpdir"

    # Write provenance file
    cat > "$dest/.clean_checkout" <<PROV
repo: ${name}
url: ${url}
commit: ${sha}
branch: ${branch}
cloned: $(date -u +%Y-%m-%dT%H:%M:%SZ)
script: create_clean_repos.sh
note: Sparse checkout of drivers/virtio/ + include/linux/virtio*.h + include/uapi/linux/virtio*.h
      Large files stripped: MAINTAINERS, CREDITS, .mailmap, Makefile, Documentation/
PROV

    local size
    size=$(du -sh "$dest" | cut -f1)
    log "  ✓ ${name} ready (${sha:0:12}, ${size}, kernel virtio extract)"
}

# --- Main ---

ALL_NAMES=()
for def in "${REPO_DEFS[@]}"; do
    parse_def "$def"
    ALL_NAMES+=("$REPO_NAME")
done

if [ $# -gt 0 ]; then
    REQUESTED=("$@")
else
    REQUESTED=("${ALL_NAMES[@]}")
fi

mkdir -p "$CLEAN_DIR"

echo "=== Quality Playbook — Clean Repo Setup ==="
echo "Destination: ${CLEAN_DIR}/"
echo "Repos:       ${REQUESTED[*]}"
echo ""

for req in "${REQUESTED[@]}"; do
    found=false
    for def in "${REPO_DEFS[@]}"; do
        parse_def "$def"
        if [ "$REPO_NAME" = "$req" ]; then
            clone_repo "$REPO_NAME" "$REPO_URL" "$REPO_COMMIT" "$REPO_BRANCH" "$REPO_SPECIAL"
            found=true
            break
        fi
    done
    if [ "$found" = false ]; then
        log "WARNING: Unknown repo '${req}' — add it to REPO_DEFS in this script"
    fi
done

echo ""
echo "=== Clean repos ready in ${CLEAN_DIR}/ ==="
echo ""
echo "Sizes:"
for req in "${REQUESTED[@]}"; do
    [ -d "${CLEAN_DIR}/${req}" ] && echo "  ${req}: $(du -sh "${CLEAN_DIR}/${req}" | cut -f1)"
done
echo ""
echo "Next: ./setup_repos.sh ${REQUESTED[*]}"
