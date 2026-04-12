#!/bin/bash
# Post-run validation gate — script-verified closure for benchmark runs.
#
# Mechanically checks artifact conformance issues that model self-attestation
# persistently misses. v1.3.27 adds deep JSON field validation, enum checks,
# summary consistency, and mandatory regression-test patches. v1.3.28 adds
# writeup inline diff validation (every writeup must contain a ```diff block).
# v1.3.31 adds TDD summary shape validation (red_failed, green_failed),
# date validation (reject placeholders/future dates), and cross-run
# contamination detection (version mismatch between directory and SKILL.md).
#
# Usage:
#   ./quality_gate.sh .                          # Check current directory
#   ./quality_gate.sh virtio                     # Check named repo (from repos/)
#   ./quality_gate.sh --all                      # Check all current-version repos
#   ./quality_gate.sh --version 1.3.27 virtio    # Check specific version
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

# Detect version from SKILL.md — try multiple locations
if [ -z "$VERSION" ]; then
    for loc in "${SCRIPT_DIR}/../SKILL.md" "${SCRIPT_DIR}/SKILL.md" ".github/skills/SKILL.md"; do
        if [ -f "$loc" ]; then
            VERSION=$(grep -m1 'version:' "$loc" 2>/dev/null | sed 's/.*version: *//' | tr -d ' ')
            [ -n "$VERSION" ] && break
        fi
    done
fi

fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }
pass() { echo "  PASS: $1"; }
warn() { echo "  WARN: $1"; WARN=$((WARN + 1)); }
info() { echo "  INFO: $1"; }

# Helper: check if a JSON file contains a key at any nesting level
json_has_key() {
    local file="$1" key="$2"
    grep -q "\"${key}\"" "$file" 2>/dev/null
}

# Helper: extract a string value for a key (first occurrence)
json_str_val() {
    local file="$1" key="$2"
    grep -o "\"${key}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$file" 2>/dev/null \
        | head -1 | sed 's/.*: *"\([^"]*\)"/\1/'
}

# Helper: count occurrences of a key in JSON
json_key_count() {
    local file="$1" key="$2"
    grep -c "\"${key}\"" "$file" 2>/dev/null || echo 0
}

check_repo() {
    local repo_dir="$1"
    local repo_name
    repo_name=$(basename "$repo_dir")
    local q="${repo_dir}/quality"

    # Handle "." as current directory
    [ "$repo_dir" = "." ] && repo_dir="$(pwd)" && repo_name=$(basename "$repo_dir") && q="${repo_dir}/quality"

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
        [ "$triage_count" -gt 0 ] && pass "spec_audits/ has triage file" || fail "spec_audits/ missing triage file"
        [ "$auditor_count" -gt 0 ] && pass "spec_audits/ has ${auditor_count} auditor file(s)" || fail "spec_audits/ missing individual auditor files"
    else
        fail "spec_audits/ directory missing"
    fi

    # --- BUGS.md heading format (benchmark 39) ---
    echo "[BUGS.md Heading Format]"
    local bug_count=0
    if [ -f "${q}/BUGS.md" ]; then
        local correct_headings wrong_headings
        correct_headings=$(grep -cE '^### BUG-[0-9]+' "${q}/BUGS.md" || true)
        correct_headings=${correct_headings:-0}
        wrong_headings=$(grep -E '^## BUG-[0-9]+' "${q}/BUGS.md" 2>/dev/null | grep -cvE '^### BUG-' || true)
        wrong_headings=${wrong_headings:-0}
        local bold_headings bullet_headings
        bold_headings=$(grep -cE '^\*\*BUG-[0-9]+' "${q}/BUGS.md" || true)
        bold_headings=${bold_headings:-0}
        bullet_headings=$(grep -cE '^- BUG-[0-9]+' "${q}/BUGS.md" || true)
        bullet_headings=${bullet_headings:-0}

        bug_count=$correct_headings

        if [ "$correct_headings" -gt 0 ] && [ "$wrong_headings" -eq 0 ] && [ "$bold_headings" -eq 0 ] && [ "$bullet_headings" -eq 0 ]; then
            pass "All ${correct_headings} bug headings use ### BUG-NNN format"
        else
            [ "$wrong_headings" -gt 0 ] && fail "${wrong_headings} heading(s) use ## instead of ###"
            [ "$bold_headings" -gt 0 ] && fail "${bold_headings} heading(s) use **BUG- format"
            [ "$bullet_headings" -gt 0 ] && fail "${bullet_headings} heading(s) use - BUG- format"
            if [ "$correct_headings" -eq 0 ] && [ "$wrong_headings" -eq 0 ]; then
                if grep -qE '(No confirmed|zero|0 confirmed)' "${q}/BUGS.md" 2>/dev/null; then
                    pass "Zero-bug run — no headings expected"
                else
                    # Count wrong-format headings as bugs for patch check
                    bug_count=$((wrong_headings + bold_headings + bullet_headings))
                    warn "No ### BUG-NNN headings found in BUGS.md"
                fi
            else
                bug_count=$((correct_headings + wrong_headings + bold_headings + bullet_headings))
            fi
        fi
    else
        fail "BUGS.md missing"
    fi

    # --- TDD sidecar JSON — deep validation (benchmarks 14, 41) ---
    echo "[TDD Sidecar JSON]"
    if [ "$bug_count" -gt 0 ]; then
        local json_file="${q}/results/tdd-results.json"
        if [ -f "$json_file" ]; then
            pass "tdd-results.json exists (${bug_count} bugs)"

            # Required root keys
            for key in schema_version skill_version date project bugs summary; do
                json_has_key "$json_file" "$key" && pass "has '${key}'" || fail "missing root key '${key}'"
            done

            # schema_version value
            local sv
            sv=$(json_str_val "$json_file" "schema_version")
            [ "$sv" = "1.1" ] && pass "schema_version is '1.1'" || fail "schema_version is '${sv:-missing}', expected '1.1'"

            # Per-bug required fields — check that canonical field names exist
            for field in id requirement red_phase green_phase verdict fix_patch_present writeup_path; do
                local fcount
                fcount=$(json_key_count "$json_file" "$field")
                if [ "$fcount" -ge "$bug_count" ]; then
                    pass "per-bug field '${field}' present (${fcount}x)"
                elif [ "$fcount" -gt 0 ]; then
                    warn "per-bug field '${field}' found ${fcount}x, expected ${bug_count}"
                else
                    fail "per-bug field '${field}' missing entirely"
                fi
            done

            # Check for wrong field names (common model errors)
            for bad_field in bug_id bug_name status phase result; do
                if json_has_key "$json_file" "$bad_field"; then
                    fail "non-canonical field '${bad_field}' found (use standard field names)"
                fi
            done

            # Summary must include confirmed_open, red_failed, green_failed
            for skey in confirmed_open red_failed green_failed; do
                if json_has_key "$json_file" "$skey"; then
                    pass "summary has '${skey}'"
                else
                    fail "summary missing '${skey}' count"
                fi
            done

            # Date validation — must be real ISO 8601, not placeholder
            local tdd_date
            tdd_date=$(json_str_val "$json_file" "date")
            if [ -n "$tdd_date" ]; then
                if echo "$tdd_date" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
                    # Check for placeholder
                    if [ "$tdd_date" = "YYYY-MM-DD" ] || [ "$tdd_date" = "0000-00-00" ]; then
                        fail "tdd-results.json date is placeholder '${tdd_date}'"
                    else
                        # Check not in the future
                        local today
                        today=$(date +%Y-%m-%d)
                        if [[ "$tdd_date" > "$today" ]]; then
                            fail "tdd-results.json date '${tdd_date}' is in the future"
                        else
                            pass "tdd-results.json date '${tdd_date}' is valid"
                        fi
                    fi
                else
                    fail "tdd-results.json date '${tdd_date}' is not ISO 8601 (YYYY-MM-DD)"
                fi
            else
                fail "tdd-results.json date field missing or empty"
            fi

            # Verdict enum validation — allowed: "TDD verified", "red failed", "green failed", "confirmed open"
            local bad_verdicts
            bad_verdicts=$(grep -oE '"verdict"[[:space:]]*:[[:space:]]*"[^"]*"' "$json_file" 2>/dev/null \
                | sed 's/.*: *"\(.*\)"/\1/' \
                | grep -cvE '^(TDD verified|red failed|green failed|confirmed open|deferred)$' || true)
            bad_verdicts=${bad_verdicts:-0}
            [ "$bad_verdicts" -eq 0 ] && pass "all verdict values are canonical" || fail "${bad_verdicts} non-canonical verdict value(s)"

        else
            fail "tdd-results.json missing (${bug_count} bugs require it)"
        fi
    else
        info "Zero bugs — tdd-results.json not required"
    fi

    # --- Integration sidecar JSON — deep validation ---
    echo "[Integration Sidecar JSON]"
    local ij="${q}/results/integration-results.json"
    if [ -f "$ij" ]; then
        for key in schema_version skill_version date project recommendation groups summary uc_coverage; do
            json_has_key "$ij" "$key" && pass "has '${key}'" || fail "missing key '${key}'"
        done

        # Recommendation enum
        local rec
        rec=$(json_str_val "$ij" "recommendation")
        case "$rec" in
            SHIP|"FIX BEFORE MERGE"|BLOCK) pass "recommendation '${rec}' is canonical" ;;
            *) [ -n "$rec" ] && fail "recommendation '${rec}' is non-canonical (must be SHIP/FIX BEFORE MERGE/BLOCK)" || fail "recommendation missing" ;;
        esac
    else
        warn "integration-results.json not present"
    fi

    # --- Use cases in REQUIREMENTS.md (benchmark 43) ---
    echo "[Use Cases]"
    if [ -f "${q}/REQUIREMENTS.md" ]; then
        local uc_ids
        uc_ids=$(grep -cE 'UC-[0-9]+' "${q}/REQUIREMENTS.md" || true)
        uc_ids=${uc_ids:-0}
        if [ "$uc_ids" -ge 5 ]; then
            pass "Found ${uc_ids} canonical UC-NN references"
        elif [ "$uc_ids" -gt 0 ]; then
            warn "Only ${uc_ids} UC-NN references (expected 5+)"
        else
            fail "No canonical UC-NN identifiers in REQUIREMENTS.md"
        fi
    else
        fail "REQUIREMENTS.md missing"
    fi

    # --- Terminal Gate in PROGRESS.md ---
    echo "[Terminal Gate]"
    if [ -f "${q}/PROGRESS.md" ]; then
        grep -qiE '^#+ *Terminal' "${q}/PROGRESS.md" 2>/dev/null \
            && pass "PROGRESS.md has Terminal Gate section" \
            || fail "PROGRESS.md missing Terminal Gate section"
    fi

    # --- Mechanical verification (if applicable) ---
    echo "[Mechanical Verification]"
    if [ -d "${q}/mechanical" ]; then
        if [ -f "${q}/mechanical/verify.sh" ]; then
            pass "verify.sh exists"
            if [ -f "${q}/results/mechanical-verify.log" ] && [ -f "${q}/results/mechanical-verify.exit" ]; then
                local exit_code
                exit_code=$(cat "${q}/results/mechanical-verify.exit" 2>/dev/null | tr -d '[:space:]')
                [ "$exit_code" = "0" ] && pass "mechanical-verify.exit is 0" || fail "mechanical-verify.exit is '${exit_code}', expected 0"
            else
                fail "Verification receipt files missing"
            fi
        else
            fail "mechanical/ exists but verify.sh missing"
        fi
    else
        info "No mechanical/ directory"
    fi

    # --- Patches for confirmed bugs (benchmark 44) ---
    echo "[Patches]"
    if [ "$bug_count" -gt 0 ]; then
        local reg_patch_count=0 fix_patch_count=0
        if [ -d "${q}/patches" ]; then
            reg_patch_count=$(ls ${q}/patches/BUG-*-regression*.patch 2>/dev/null | wc -l | tr -d ' ')
            fix_patch_count=$(ls ${q}/patches/BUG-*-fix*.patch 2>/dev/null | wc -l | tr -d ' ')
        fi

        if [ "$reg_patch_count" -ge "$bug_count" ]; then
            pass "${reg_patch_count} regression-test patch(es) for ${bug_count} bug(s)"
        elif [ "$reg_patch_count" -gt 0 ]; then
            fail "Only ${reg_patch_count} regression-test patch(es) for ${bug_count} bug(s)"
        else
            fail "No regression-test patches (quality/patches/BUG-NNN-regression-test.patch required for each bug)"
        fi

        if [ "$fix_patch_count" -gt 0 ]; then
            pass "${fix_patch_count} fix patch(es)"
        else
            warn "0 fix patches (fix patches are optional but strongly encouraged)"
        fi

        # Total patch count for summary
        local total_patches=$((reg_patch_count + fix_patch_count))
        info "Total: ${total_patches} patch file(s) in quality/patches/"
    fi

    # --- Writeups for confirmed bugs (benchmark 30) ---
    echo "[Bug Writeups]"
    if [ "$bug_count" -gt 0 ]; then
        local writeup_count=0 writeup_diff_count=0
        if [ -d "${q}/writeups" ]; then
            writeup_count=$(ls ${q}/writeups/BUG-*.md 2>/dev/null | wc -l | tr -d ' ')
            # Check each writeup for inline diff (section 6 requirement)
            for wf in ${q}/writeups/BUG-*.md; do
                [ -f "$wf" ] || continue
                if grep -q '```diff' "$wf" 2>/dev/null; then
                    writeup_diff_count=$((writeup_diff_count + 1))
                fi
            done
        fi
        if [ "$writeup_count" -ge "$bug_count" ]; then
            pass "${writeup_count} writeup(s) for ${bug_count} bug(s)"
        elif [ "$writeup_count" -gt 0 ]; then
            warn "${writeup_count} writeup(s) for ${bug_count} bug(s) — incomplete"
        else
            fail "No writeups for ${bug_count} confirmed bug(s)"
        fi

        # Inline diff check — every writeup must have a ```diff block (section 6 "The fix")
        if [ "$writeup_count" -gt 0 ]; then
            if [ "$writeup_diff_count" -ge "$writeup_count" ]; then
                pass "All ${writeup_diff_count} writeup(s) have inline fix diffs"
            elif [ "$writeup_diff_count" -gt 0 ]; then
                fail "Only ${writeup_diff_count}/${writeup_count} writeup(s) have inline fix diffs (all require section 6 diff)"
            else
                fail "No writeups have inline fix diffs (section 6 'The fix' must include a \`\`\`diff block)"
            fi
        fi
    fi

    # --- Version stamp consistency (benchmark 26) ---
    echo "[Version Stamps]"
    local skill_version=""
    for loc in "${repo_dir}/.github/skills/SKILL.md" "${repo_dir}/SKILL.md"; do
        if [ -f "$loc" ]; then
            skill_version=$(grep -m1 'version:' "$loc" 2>/dev/null | sed 's/.*version: *//' | tr -d ' ')
            [ -n "$skill_version" ] && break
        fi
    done
    if [ -n "$skill_version" ]; then
        if [ -f "${q}/PROGRESS.md" ]; then
            local pv
            pv=$(grep -m1 'Skill version:' "${q}/PROGRESS.md" 2>/dev/null | sed 's/.*Skill version: *//' | tr -d ' ')
            [ "$pv" = "$skill_version" ] && pass "PROGRESS.md version matches (${skill_version})" \
                || { [ -n "$pv" ] && fail "PROGRESS.md version '${pv}' != '${skill_version}'" || warn "PROGRESS.md missing Skill version field"; }
        fi
        if [ -f "${q}/results/tdd-results.json" ]; then
            local tv
            tv=$(json_str_val "${q}/results/tdd-results.json" "skill_version")
            [ "$tv" = "$skill_version" ] && pass "tdd-results.json skill_version matches" \
                || { [ -n "$tv" ] && fail "tdd-results.json skill_version '${tv}' != '${skill_version}'"; }
        fi
    else
        warn "Cannot detect skill version from SKILL.md"
    fi

    # --- Cross-run contamination detection ---
    echo "[Cross-Run Contamination]"
    if [ -n "$skill_version" ] && [ -n "$VERSION" ]; then
        # Check if the repo directory name contains a version that doesn't match the skill
        local dir_version
        dir_version=$(echo "$repo_name" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | tail -1)
        if [ -n "$dir_version" ] && [ "$dir_version" != "$skill_version" ]; then
            fail "Directory version '${dir_version}' != skill version '${skill_version}' — possible cross-run contamination"
        else
            pass "No version mismatch detected"
        fi
    fi

    # Check for artifacts referencing a different version in gate log or tdd-results
    if [ -f "${q}/results/tdd-results.json" ] && [ -n "$skill_version" ]; then
        local json_sv
        json_sv=$(json_str_val "${q}/results/tdd-results.json" "skill_version")
        if [ -n "$json_sv" ] && [ "$json_sv" != "$skill_version" ]; then
            fail "tdd-results.json skill_version '${json_sv}' != SKILL.md '${skill_version}' — stale artifacts from prior run?"
        fi
    fi

    echo ""
}

# Resolve repos
if [ "$CHECK_ALL" = true ]; then
    for dir in "${SCRIPT_DIR}/"*-"${VERSION}"/; do
        [ -d "$dir/quality" ] && REPO_DIRS+=("$dir")
    done
elif [ ${#REPO_DIRS[@]} -eq 1 ] && [ "${REPO_DIRS[0]}" = "." ]; then
    # Running from inside a repo
    REPO_DIRS=("$(pwd)")
else
    resolved=()
    for name in "${REPO_DIRS[@]}"; do
        if [ -d "$name/quality" ]; then
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
    echo "Usage: $0 [--version V] [--all | repo1 repo2 ... | .]"
    exit 1
fi

echo "=== Quality Gate — Post-Run Validation ==="
echo "Version: ${VERSION:-unknown}"
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
