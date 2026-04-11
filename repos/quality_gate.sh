#!/bin/bash
# Post-run validation gate — script-verified closure for benchmark runs.
#
# Checks every quality artifact for mechanical conformance issues that
# v1.3.21–v1.3.25 relied on model self-attestation to catch.
#
# Usage:
#   ./quality_gate.sh virtio                    # Check current version
#   ./quality_gate.sh --all                     # Check all current-version repos
#   ./quality_gate.sh --version 1.3.26 virtio   # Check specific version
#
# Exit codes:
#   0 — all checks passed
#   1 — one or more checks failed
#
# This script is also copied into each repo at .github/skills/quality_gate.sh
# so the playbook agent can run it as its final Phase 2d step.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FAIL=0
WARN=0
REPO_DIRS=()
VERSION=""
CHECK_ALL=false

# Parse args
EXPECT_VERSION=false
for arg in "$@"; do
    if [ "$EXPECT_VERSION" = true ]; then
        VERSION="$arg"
        EXPECT_VERSION=false
        continue
    fi
    case "$arg" in
        --version) EXPECT_VERSION=true ;;
        --all)     CHECK_ALL=true ;;
        *)         REPO_DIRS+=("$arg") ;;
    esac
done

# Detect version from SKILL.md if not specified
if [ -z "$VERSION" ]; then
    VERSION=$(grep -m1 'version:' "${SCRIPT_DIR}/../SKILL.md" 2>/dev/null | sed 's/.*version: *//' | tr -d ' ')
    [ -z "$VERSION" ] && VERSION=$(grep -m1 'version:' "${SCRIPT_DIR}/../SKILL.md" 2>/dev/null | awk '{print $2}')
fi

fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }
pass() { echo "  PASS: $1"; }
warn() { echo "  WARN: $1"; WARN=$((WARN + 1)); }
info() { echo "  INFO: $1"; }

check_repo() {
    local repo_dir="$1"
    local repo_name
    repo_name=$(basename "$repo_dir")
    local q="${repo_dir}/quality"

    echo ""
    echo "=== ${repo_name} ==="

    # --- File existence (benchmark 40) ---
    echo "[File Existence]"
    for f in BUGS.md REQUIREMENTS.md QUALITY.md PROGRESS.md COVERAGE_MATRIX.md COMPLETENESS_REPORT.md; do
        if [ -f "${q}/${f}" ]; then
            pass "${f} exists"
        else
            fail "${f} missing"
        fi
    done

    # Code reviews dir
    if [ -d "${q}/code_reviews" ] && [ -n "$(ls ${q}/code_reviews/*.md 2>/dev/null)" ]; then
        pass "code_reviews/ has .md files"
    else
        fail "code_reviews/ missing or empty"
    fi

    # Spec audits
    if [ -d "${q}/spec_audits" ]; then
        local triage_count auditor_count
        triage_count=$(ls ${q}/spec_audits/*triage* 2>/dev/null | wc -l | tr -d ' ')
        auditor_count=$(ls ${q}/spec_audits/*auditor* 2>/dev/null | wc -l | tr -d ' ')
        if [ "$triage_count" -gt 0 ]; then
            pass "spec_audits/ has triage file (${triage_count})"
        else
            fail "spec_audits/ missing triage file"
        fi
        if [ "$auditor_count" -gt 0 ]; then
            pass "spec_audits/ has auditor files (${auditor_count})"
        else
            fail "spec_audits/ missing individual auditor files"
        fi
    else
        fail "spec_audits/ directory missing"
    fi

    # --- BUGS.md heading format (benchmark 39) ---
    echo "[BUGS.md Heading Format]"
    if [ -f "${q}/BUGS.md" ]; then
        local correct_headings wrong_headings
        correct_headings=$(grep -cE '^### BUG-[0-9]+' "${q}/BUGS.md" || true)
        correct_headings=${correct_headings:-0}
        # Match "## BUG-" but NOT "### BUG-" (exclude triple-hash)
        wrong_headings=$(grep -E '^## BUG-[0-9]+' "${q}/BUGS.md" | grep -cvE '^### BUG-' || true)
        wrong_headings=${wrong_headings:-0}
        local bold_headings bullet_headings
        bold_headings=$(grep -cE '^\*\*BUG-[0-9]+' "${q}/BUGS.md" || true)
        bold_headings=${bold_headings:-0}
        bullet_headings=$(grep -cE '^- BUG-[0-9]+' "${q}/BUGS.md" || true)
        bullet_headings=${bullet_headings:-0}

        if [ "$correct_headings" -gt 0 ] && [ "$wrong_headings" -eq 0 ] && [ "$bold_headings" -eq 0 ] && [ "$bullet_headings" -eq 0 ]; then
            pass "All ${correct_headings} bug headings use ### BUG-NNN format"
        else
            if [ "$wrong_headings" -gt 0 ]; then
                fail "${wrong_headings} bug heading(s) use ## instead of ### (benchmark 39)"
            fi
            if [ "$bold_headings" -gt 0 ]; then
                fail "${bold_headings} bug heading(s) use **BUG- format"
            fi
            if [ "$bullet_headings" -gt 0 ]; then
                fail "${bullet_headings} bug heading(s) use - BUG- format"
            fi
            if [ "$correct_headings" -eq 0 ] && [ "$wrong_headings" -eq 0 ]; then
                # Could be a zero-bug run
                if grep -qE '(No confirmed|zero|0 confirmed)' "${q}/BUGS.md" 2>/dev/null; then
                    pass "Zero-bug run — no headings expected"
                else
                    warn "No BUG-NNN headings found in BUGS.md"
                fi
            fi
        fi
    else
        fail "BUGS.md missing — cannot check heading format"
    fi

    # --- TDD sidecar JSON schema (benchmark 14) ---
    echo "[TDD Sidecar JSON Schema]"
    local bug_count=0
    if [ -f "${q}/BUGS.md" ]; then
        bug_count=$(grep -cE '^###? BUG-[0-9]+' "${q}/BUGS.md" 2>/dev/null || echo 0)
    fi

    if [ "$bug_count" -gt 0 ]; then
        if [ -f "${q}/results/tdd-results.json" ]; then
            pass "tdd-results.json exists (${bug_count} bugs)"
            # Check required root keys
            local json_file="${q}/results/tdd-results.json"
            for key in schema_version skill_version date project bugs summary; do
                if grep -q "\"${key}\"" "$json_file" 2>/dev/null; then
                    pass "tdd-results.json has '${key}'"
                else
                    fail "tdd-results.json missing required key '${key}'"
                fi
            done
            # Check schema_version value
            local sv
            sv=$(grep -o '"schema_version"[[:space:]]*:[[:space:]]*"[^"]*"' "$json_file" 2>/dev/null | head -1 | sed 's/.*"\([^"]*\)"/\1/')
            if [ "$sv" = "1.1" ]; then
                pass "schema_version is '1.1'"
            elif [ -n "$sv" ]; then
                fail "schema_version is '${sv}', expected '1.1'"
            fi
        else
            fail "tdd-results.json missing (${bug_count} bugs require it, benchmark 28)"
        fi
    else
        info "Zero bugs — tdd-results.json not required"
    fi

    # Integration sidecar
    if [ -f "${q}/results/integration-results.json" ]; then
        local ij="${q}/results/integration-results.json"
        for key in schema_version skill_version date project recommendation groups summary; do
            if grep -q "\"${key}\"" "$ij" 2>/dev/null; then
                pass "integration-results.json has '${key}'"
            else
                fail "integration-results.json missing required key '${key}'"
            fi
        done
    fi

    # --- Use cases in REQUIREMENTS.md ---
    echo "[Use Cases]"
    if [ -f "${q}/REQUIREMENTS.md" ]; then
        local uc_section uc_ids
        uc_section=$(grep -ciE '(use case|fitness.to.purpose|UC-[0-9])' "${q}/REQUIREMENTS.md" || true)
        uc_section=${uc_section:-0}
        uc_ids=$(grep -cE 'UC-[0-9]+' "${q}/REQUIREMENTS.md" || true)
        uc_ids=${uc_ids:-0}
        if [ "$uc_section" -gt 0 ]; then
            pass "REQUIREMENTS.md has use case content (${uc_section} lines)"
            if [ "$uc_ids" -gt 0 ]; then
                pass "Found ${uc_ids} canonical UC-NN identifiers"
            else
                warn "No canonical UC-NN identifiers (use case content exists but not in UC-01 format)"
            fi
        else
            fail "REQUIREMENTS.md has no use case content"
        fi
    else
        fail "REQUIREMENTS.md missing"
    fi

    # --- Terminal Gate in PROGRESS.md ---
    echo "[Terminal Gate]"
    if [ -f "${q}/PROGRESS.md" ]; then
        if grep -qiE '^##? Terminal [Gg]ate' "${q}/PROGRESS.md" 2>/dev/null; then
            pass "PROGRESS.md has Terminal Gate section"
        else
            fail "PROGRESS.md missing Terminal Gate section"
        fi
    fi

    # --- Mechanical verification (if applicable) ---
    echo "[Mechanical Verification]"
    if [ -d "${q}/mechanical" ]; then
        if [ -f "${q}/mechanical/verify.sh" ]; then
            pass "verify.sh exists"
            if [ -f "${q}/results/mechanical-verify.log" ] && [ -f "${q}/results/mechanical-verify.exit" ]; then
                local exit_code
                exit_code=$(cat "${q}/results/mechanical-verify.exit" 2>/dev/null | tr -d '[:space:]')
                if [ "$exit_code" = "0" ]; then
                    pass "mechanical-verify.exit is 0"
                else
                    fail "mechanical-verify.exit is '${exit_code}', expected 0"
                fi
            else
                fail "Verification receipt files missing (mechanical-verify.log and/or mechanical-verify.exit)"
            fi
        else
            fail "mechanical/ directory exists but verify.sh missing (benchmark 27)"
        fi
    else
        info "No mechanical/ directory (not applicable for this project)"
    fi

    # --- Fix patches for confirmed bugs ---
    echo "[Fix Patches]"
    if [ "$bug_count" -gt 0 ]; then
        local patch_count=0
        if [ -d "${q}/patches" ]; then
            patch_count=$(ls ${q}/patches/*.patch 2>/dev/null | wc -l | tr -d ' ')
        fi
        if [ "$patch_count" -gt 0 ]; then
            pass "${patch_count} fix patch(es) for ${bug_count} bug(s)"
        else
            warn "0 fix patches for ${bug_count} confirmed bug(s)"
        fi
    fi

    # --- Writeups for confirmed bugs (benchmark 30) ---
    echo "[Bug Writeups]"
    if [ "$bug_count" -gt 0 ]; then
        local writeup_count=0
        if [ -d "${q}/writeups" ]; then
            writeup_count=$(ls ${q}/writeups/BUG-*.md 2>/dev/null | wc -l | tr -d ' ')
        fi
        if [ "$writeup_count" -ge "$bug_count" ]; then
            pass "${writeup_count} writeup(s) for ${bug_count} bug(s)"
        elif [ "$writeup_count" -gt 0 ]; then
            warn "${writeup_count} writeup(s) for ${bug_count} bug(s) — incomplete"
        else
            fail "No writeups for ${bug_count} confirmed bug(s) (benchmark 30)"
        fi
    fi

    # --- Version stamp consistency (benchmark 26) ---
    echo "[Version Stamps]"
    local skill_version=""
    if [ -f "${repo_dir}/.github/skills/SKILL.md" ]; then
        skill_version=$(grep -m1 'version:' "${repo_dir}/.github/skills/SKILL.md" 2>/dev/null | sed 's/.*version: *//' | tr -d ' ')
    fi
    if [ -n "$skill_version" ]; then
        if [ -f "${q}/PROGRESS.md" ]; then
            local pv
            pv=$(grep -m1 'Skill version:' "${q}/PROGRESS.md" 2>/dev/null | sed 's/.*Skill version: *//' | tr -d ' ')
            if [ "$pv" = "$skill_version" ]; then
                pass "PROGRESS.md version stamp matches (${skill_version})"
            elif [ -n "$pv" ]; then
                fail "PROGRESS.md version '${pv}' != SKILL.md '${skill_version}'"
            else
                warn "PROGRESS.md missing 'Skill version:' field"
            fi
        fi
        # Check tdd-results.json skill_version
        if [ -f "${q}/results/tdd-results.json" ]; then
            local tv
            tv=$(grep -o '"skill_version"[[:space:]]*:[[:space:]]*"[^"]*"' "${q}/results/tdd-results.json" 2>/dev/null | head -1 | sed 's/.*"\([^"]*\)"/\1/')
            if [ "$tv" = "$skill_version" ]; then
                pass "tdd-results.json skill_version matches (${skill_version})"
            elif [ -n "$tv" ]; then
                fail "tdd-results.json skill_version '${tv}' != SKILL.md '${skill_version}'"
            fi
        fi
    fi

    echo ""
}

# Resolve repos
if [ "$CHECK_ALL" = true ]; then
    for dir in "${SCRIPT_DIR}/"*-"${VERSION}"/; do
        [ -d "$dir/quality" ] && REPO_DIRS+=("$dir")
    done
else
    # Resolve short names to dirs
    resolved=()
    for name in "${REPO_DIRS[@]}"; do
        if [ -d "$name" ]; then
            resolved+=("$name")
        elif [ -d "${SCRIPT_DIR}/${name}-${VERSION}" ]; then
            resolved+=("${SCRIPT_DIR}/${name}-${VERSION}")
        elif [ -d "${SCRIPT_DIR}/${name}" ]; then
            resolved+=("${SCRIPT_DIR}/${name}")
        else
            echo "WARNING: Cannot find repo '${name}'"
        fi
    done
    REPO_DIRS=("${resolved[@]}")
fi

if [ ${#REPO_DIRS[@]} -eq 0 ]; then
    echo "Usage: $0 [--version V] [--all | repo1 repo2 ...]"
    exit 1
fi

echo "=== Quality Gate — Post-Run Validation ==="
echo "Version: ${VERSION}"
echo "Repos:   ${#REPO_DIRS[@]}"

for repo_dir in "${REPO_DIRS[@]}"; do
    check_repo "$repo_dir"
done

echo ""
echo "==========================================="
echo "Total: ${FAIL} FAIL, ${WARN} WARN"
if [ "$FAIL" -gt 0 ]; then
    echo "RESULT: GATE FAILED — ${FAIL} check(s) must be fixed"
    exit 1
else
    echo "RESULT: GATE PASSED"
    exit 0
fi
