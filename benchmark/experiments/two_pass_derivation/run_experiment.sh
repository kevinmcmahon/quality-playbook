#!/bin/bash
# Two-Pass Requirement Derivation Experiment
#
# Run from the NSQ repo root (repos/nsq-req-validation/):
#   bash /path/to/experiments/two_pass_derivation/run_experiment.sh [pass1|pass1.5|pass2|all]
#
# Or with an explicit repo path:
#   REPO_ROOT=/path/to/nsq bash run_experiment.sh pass1
#
# The experiment runs against specific pre-fix commits:
#   - Subsystem 1 (config/startup): commit 98fbcd1 (NSQ-36 and NSQ-39 bugs present)
#   - Subsystem 2 (TLS/auth): commit 1d183d9 (NSQ-44 bug present)

set -euo pipefail

# Determine script location (works in both bash and zsh)
if [ -n "${BASH_SOURCE+x}" ] 2>/dev/null; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
elif [ -n "${ZSH_VERSION+x}" ] 2>/dev/null; then
    SCRIPT_DIR="$(cd "$(dirname "${(%):-%x}")" && pwd)"
else
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
fi

EXPERIMENT_DIR="$SCRIPT_DIR"

# Repo root: use REPO_ROOT env var if set, otherwise assume cwd
if [ -z "${REPO_ROOT:-}" ]; then
    # Check if we're in a git repo with nsqd/
    if [ -d "nsqd" ] && git rev-parse --git-dir >/dev/null 2>&1; then
        REPO_ROOT="$(pwd)"
    else
        echo "ERROR: Not in the NSQ repo root. Either cd to repos/nsq-req-validation/ or set REPO_ROOT."
        echo "Usage: cd /path/to/nsq-repo && bash $EXPERIMENT_DIR/run_experiment.sh [pass1|pass1.5|pass2|all]"
        exit 1
    fi
fi

TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

# Pre-fix commits where bugs are present
COMMIT_SUBSYSTEM1="98fbcd1"  # NSQ-36 (no percentile validation) + NSQ-39 (4096 vs 1024)
COMMIT_SUBSYSTEM2="1d183d9"  # NSQ-44 (auth server ignores root CA)

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $1"
}

run_pass1() {
    log "=== PASS 1: Derive Requirements ==="
    log "Repo root: $REPO_ROOT"
    log "Experiment dir: $EXPERIMENT_DIR"

    cd "$REPO_ROOT"

    log "Checking out $COMMIT_SUBSYSTEM1 for documentation reading..."
    git checkout "$COMMIT_SUBSYSTEM1" -- README.md ChangeLog.md nsqd/options.go nsqd/nsqd.go nsqd/guid.go internal/auth/authorizations.go 2>/dev/null || true

    log "Running Pass 1 (requirement derivation)..."

    # Copy prompt to repo root for Copilot CLI access (skip if same dir)
    if [ "$EXPERIMENT_DIR" != "$REPO_ROOT" ]; then
        cp "$EXPERIMENT_DIR/pass1_derive_requirements.md" "$REPO_ROOT/"
    fi

    gh copilot chat -f pass1_derive_requirements.md 2>&1 | tee "$EXPERIMENT_DIR/pass1_output_${TIMESTAMP}.txt"

    # Check if requirements_raw.md was created
    if [ -f "$REPO_ROOT/requirements_raw.md" ]; then
        if [ "$EXPERIMENT_DIR" != "$REPO_ROOT" ]; then
            cp "$REPO_ROOT/requirements_raw.md" "$EXPERIMENT_DIR/"
        fi
        log "Pass 1 complete. Requirements saved to $EXPERIMENT_DIR/requirements_raw.md"
    else
        log "WARNING: requirements_raw.md not found. Check pass1 output."
    fi

    # Restore working tree
    git checkout HEAD -- README.md ChangeLog.md nsqd/options.go nsqd/nsqd.go nsqd/guid.go internal/auth/authorizations.go 2>/dev/null || true
    if [ "$EXPERIMENT_DIR" != "$REPO_ROOT" ]; then
        rm -f "$REPO_ROOT/pass1_derive_requirements.md"
    fi
}

run_pass1_5() {
    log "=== PASS 1.5: Filter Requirements ==="

    if [ ! -f "$EXPERIMENT_DIR/requirements_raw.md" ]; then
        log "ERROR: requirements_raw.md not found. Run pass1 first."
        exit 1
    fi

    cd "$REPO_ROOT"

    # Copy files to repo root (skip if same dir)
    if [ "$EXPERIMENT_DIR" != "$REPO_ROOT" ]; then
        cp "$EXPERIMENT_DIR/requirements_raw.md" "$REPO_ROOT/"
        cp "$EXPERIMENT_DIR/pass1_5_filter_requirements.md" "$REPO_ROOT/"
    fi

    log "Running Pass 1.5 (requirement filtering)..."
    gh copilot chat -f pass1_5_filter_requirements.md 2>&1 | tee "$EXPERIMENT_DIR/pass1_5_output_${TIMESTAMP}.txt"

    if [ -f "$REPO_ROOT/requirements_filtered.md" ]; then
        if [ "$EXPERIMENT_DIR" != "$REPO_ROOT" ]; then
            cp "$REPO_ROOT/requirements_filtered.md" "$EXPERIMENT_DIR/"
        fi
        log "Pass 1.5 complete. Filtered requirements saved to $EXPERIMENT_DIR/requirements_filtered.md"
    else
        log "WARNING: requirements_filtered.md not found. Check pass1.5 output."
    fi

    if [ "$EXPERIMENT_DIR" != "$REPO_ROOT" ]; then
        rm -f "$REPO_ROOT/requirements_raw.md" "$REPO_ROOT/pass1_5_filter_requirements.md"
    fi
}

run_pass2() {
    log "=== PASS 2: Verify Requirements Against Code ==="

    if [ ! -f "$EXPERIMENT_DIR/requirements_filtered.md" ]; then
        log "ERROR: requirements_filtered.md not found. Run pass1 and pass1.5 first."
        exit 1
    fi

    cd "$REPO_ROOT"

    log "Checking out subsystem 1 files at $COMMIT_SUBSYSTEM1..."
    git checkout "$COMMIT_SUBSYSTEM1" -- nsqd/nsqd.go nsqd/options.go nsqd/guid.go 2>/dev/null || true

    log "Checking out subsystem 2 files at $COMMIT_SUBSYSTEM2..."
    git checkout "$COMMIT_SUBSYSTEM2" -- internal/auth/authorizations.go 2>/dev/null || true

    # Copy files to repo root (skip if same dir)
    if [ "$EXPERIMENT_DIR" != "$REPO_ROOT" ]; then
        cp "$EXPERIMENT_DIR/requirements_filtered.md" "$REPO_ROOT/"
        cp "$EXPERIMENT_DIR/pass2_verify_requirements.md" "$REPO_ROOT/"
    fi

    log "Running Pass 2 (requirement verification)..."
    gh copilot chat -f pass2_verify_requirements.md 2>&1 | tee "$EXPERIMENT_DIR/pass2_output_${TIMESTAMP}.txt"

    if [ -f "$REPO_ROOT/verification_report.md" ]; then
        if [ "$EXPERIMENT_DIR" != "$REPO_ROOT" ]; then
            cp "$REPO_ROOT/verification_report.md" "$EXPERIMENT_DIR/"
        fi
        log "Pass 2 complete. Report saved to $EXPERIMENT_DIR/verification_report.md"
    else
        log "WARNING: verification_report.md not found. Check pass2 output."
    fi

    # Restore working tree
    git checkout HEAD -- nsqd/nsqd.go nsqd/options.go nsqd/guid.go internal/auth/authorizations.go 2>/dev/null || true
    if [ "$EXPERIMENT_DIR" != "$REPO_ROOT" ]; then
        rm -f "$REPO_ROOT/requirements_filtered.md" "$REPO_ROOT/pass2_verify_requirements.md"
    fi
}

case "${1:-all}" in
    pass1)
        run_pass1
        ;;
    pass1.5)
        run_pass1_5
        ;;
    pass2)
        run_pass2
        ;;
    all)
        run_pass1
        echo ""
        run_pass1_5
        echo ""
        run_pass2
        ;;
    *)
        echo "Usage: $0 [pass1|pass1.5|pass2|all]"
        exit 1
        ;;
esac

log "Done."
