#!/usr/bin/env bash
# Install or update Quality Playbook skill layouts in a target project.
#
# Usage:
#   install-quality-playbook.sh [--layout auto|all|claude|copilot-flat|copilot-nested] [--dry-run] <target-project-dir>

set -euo pipefail

INSTALLER_VERSION="1.0.0"

usage() {
    cat >&2 <<'EOF'
Usage: install-quality-playbook.sh [--layout auto|all|claude|copilot-flat|copilot-nested] [--dry-run] <target-project-dir>

Layouts:
  auto            Update detected existing layouts; install Claude layout if none exist.
  all             Install/update Claude, Copilot flat, and Copilot nested layouts.
  claude          Install/update .claude/skills/quality-playbook.
  copilot-flat    Install/update .github/skills.
  copilot-nested  Install/update .github/skills/quality-playbook.

Options:
  --dry-run       Print planned creates, replacements, backups, and removals only.
  -h, --help      Show this help.
EOF
}

die() {
    echo "Error: $*" >&2
    exit 1
}

layout="auto"
dry_run=false
target=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --layout)
            [[ $# -ge 2 ]] || die "--layout requires a value"
            layout="$2"
            shift 2
            ;;
        --layout=*)
            layout="${1#--layout=}"
            shift
            ;;
        --dry-run)
            dry_run=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            usage
            die "unknown option: $1"
            ;;
        *)
            if [[ -n "$target" ]]; then
                usage
                die "only one target project directory may be provided"
            fi
            target="$1"
            shift
            ;;
    esac
done

if [[ $# -gt 0 ]]; then
    if [[ -n "$target" ]]; then
        usage
        die "only one target project directory may be provided"
    fi
    target="$1"
    shift
fi

[[ $# -eq 0 ]] || die "unexpected extra arguments"

case "$layout" in
    auto|all|claude|copilot-flat|copilot-nested) ;;
    *)
        usage
        die "unsupported layout: $layout"
        ;;
esac

[[ -n "$target" ]] || { usage; exit 2; }
[[ -d "$target" ]] || die "target directory does not exist: $target"
target="$(cd "$target" >/dev/null 2>&1 && pwd -P)"

# Resolve the playbook source directory, following symlinks without readlink -f
# so the installer works on macOS.
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

[[ -f "$src/SKILL.md" ]] || die "missing source file: $src/SKILL.md"
[[ -f "$src/LICENSE.txt" ]] || die "missing source file: $src/LICENSE.txt"
[[ -d "$src/references" ]] || die "missing source directory: $src/references"
[[ -d "$src/phase_prompts" ]] || die "missing source directory: $src/phase_prompts"
[[ -d "$src/agents" ]] || die "missing source directory: $src/agents"
[[ -f "$src/.github/skills/quality_gate/quality_gate.py" ]] || die "missing source file: $src/.github/skills/quality_gate/quality_gate.py"

qpb_version="$(awk '/^[[:space:]]*version:[[:space:]]*/ { print $2; exit }' "$src/SKILL.md")"
if [[ -z "$qpb_version" ]]; then
    qpb_version="unknown"
fi

manifest_rel=".quality-playbook-install.json"
manifest="$target/$manifest_rel"
backup_root_rel=".quality-playbook-backups"
backup_timestamp=""

installed_paths=()
installed_shas=()
removed_paths=()
selected_layouts=()
backup_paths=()
planned_dirs=()
operation_count=0

layout_prefix() {
    case "$1" in
        claude) echo ".claude/skills/quality-playbook" ;;
        copilot-flat) echo ".github/skills" ;;
        copilot-nested) echo ".github/skills/quality-playbook" ;;
        *) die "internal error: unknown layout: $1" ;;
    esac
}

append_selected_layout() {
    selected_layouts[${#selected_layouts[@]}]="$1"
}

detect_layout() {
    local candidate="$1"
    local prefix
    prefix="$(layout_prefix "$candidate")"

    [[ -f "$target/$prefix/SKILL.md" ]] ||
        [[ -d "$target/$prefix/references" ]] ||
        [[ -f "$target/$prefix/quality_gate.py" ]] ||
        [[ -f "$target/$prefix/quality_gate.sh" ]]
}

select_layouts() {
    case "$layout" in
        auto)
            detect_layout "claude" && append_selected_layout "claude"
            detect_layout "copilot-flat" && append_selected_layout "copilot-flat"
            detect_layout "copilot-nested" && append_selected_layout "copilot-nested"
            if [[ ${#selected_layouts[@]} -eq 0 ]]; then
                append_selected_layout "claude"
            fi
            ;;
        all)
            append_selected_layout "claude"
            append_selected_layout "copilot-flat"
            append_selected_layout "copilot-nested"
            ;;
        *)
            append_selected_layout "$layout"
            ;;
    esac
}

sha_file() {
    shasum -a 256 "$1" | awk '{ print $1 }'
}

json_escape() {
    local value="$1"
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    value="${value//$'\n'/\\n}"
    printf '%s' "$value"
}

manifest_checksum() {
    local rel="$1"
    [[ -f "$manifest" ]] || return 1

    awk -v wanted="$rel" '
        BEGIN { in_files = 0; path = ""; found = 0 }
        /"installed_files"[[:space:]]*:/ { in_files = 1; next }
        in_files && /"removed_stale_files"[[:space:]]*:/ { exit }
        in_files && /"path"[[:space:]]*:/ {
            line = $0
            sub(/^.*"path"[[:space:]]*:[[:space:]]*"/, "", line)
            sub(/".*$/, "", line)
            path = line
        }
        in_files && /"sha256"[[:space:]]*:/ {
            line = $0
            sub(/^.*"sha256"[[:space:]]*:[[:space:]]*"/, "", line)
            sub(/".*$/, "", line)
            if (path == wanted) {
                print line
                found = 1
                exit
            }
            path = ""
        }
        END { if (!found) exit 1 }
    ' "$manifest"
}

record_operation() {
    operation_count=$((operation_count + 1))
    if [[ "$dry_run" == true ]]; then
        echo "Would $1"
    else
        echo "$2"
    fi
}

ensure_dir() {
    local rel="$1"
    local dest="$target/$rel"
    local planned

    [[ "$rel" != "." ]] || return 0
    if [[ -d "$dest" ]]; then
        return 0
    fi
    if [[ -e "$dest" || -L "$dest" ]]; then
        die "expected directory but found file: $rel"
    fi

    if [[ "$dry_run" == true ]]; then
        for planned in ${planned_dirs[@]+"${planned_dirs[@]}"}; do
            [[ "$planned" == "$rel" ]] && return 0
        done
        planned_dirs[${#planned_dirs[@]}]="$rel"
    fi

    record_operation "create directory: $rel" "Created directory: $rel"
    if [[ "$dry_run" != true ]]; then
        mkdir -p "$dest"
    fi
}

ensure_backup_timestamp() {
    if [[ -z "$backup_timestamp" ]]; then
        backup_timestamp="$(date -u '+%Y%m%dT%H%M%SZ')"
    fi
}

backup_file() {
    local rel="$1"
    local source_file="$target/$rel"
    local backup_rel
    local backup_file_path

    ensure_backup_timestamp
    backup_rel="$backup_root_rel/$backup_timestamp/$rel"
    backup_file_path="$target/$backup_rel"

    backup_paths[${#backup_paths[@]}]="$backup_rel"
    record_operation "backup local edit: $rel -> $backup_rel" "Backed up local edit: $rel -> $backup_rel"

    if [[ "$dry_run" == true ]]; then
        return 0
    fi

    mkdir -p "$(dirname "$backup_file_path")"
    if [[ -L "$source_file" ]]; then
        cp -P "$source_file" "$backup_file_path"
    else
        cp -p "$source_file" "$backup_file_path"
    fi
}

should_backup_before_change() {
    local rel="$1"
    local dest="$target/$rel"
    local tracked_sha=""
    local current_sha=""

    [[ -f "$manifest" ]] || return 1
    [[ -e "$dest" || -L "$dest" ]] || return 1
    [[ -f "$dest" || -L "$dest" ]] || return 1

    tracked_sha="$(manifest_checksum "$rel" 2>/dev/null || true)"
    if [[ -z "$tracked_sha" ]]; then
        return 0
    fi

    current_sha="$(sha_file "$dest" 2>/dev/null || true)"
    [[ "$current_sha" != "$tracked_sha" ]]
}

append_installed_file() {
    installed_paths[${#installed_paths[@]}]="$1"
    installed_shas[${#installed_shas[@]}]="$2"
}

install_file() {
    local source_file="$1"
    local rel="$2"
    local make_executable="${3:-false}"
    local dest="$target/$rel"
    local source_sha
    local dest_sha=""
    local parent_rel

    source_sha="$(sha_file "$source_file")"
    parent_rel="$(dirname "$rel")"
    ensure_dir "$parent_rel"

    if [[ -e "$dest" || -L "$dest" ]]; then
        if [[ ! -f "$dest" && ! -L "$dest" ]]; then
            die "expected file but found directory: $rel"
        fi

        dest_sha="$(sha_file "$dest" 2>/dev/null || true)"
        if [[ "$dest_sha" == "$source_sha" && ! -L "$dest" ]]; then
            :
        else
            if should_backup_before_change "$rel"; then
                backup_file "$rel"
            fi
            record_operation "replace file: $rel" "Replaced file: $rel"
            if [[ "$dry_run" != true ]]; then
                rm -f "$dest"
                cp "$source_file" "$dest"
            fi
        fi
    else
        record_operation "create file: $rel" "Created file: $rel"
        if [[ "$dry_run" != true ]]; then
            cp "$source_file" "$dest"
        fi
    fi

    if [[ "$make_executable" == true ]]; then
        if [[ "$dry_run" == true ]]; then
            if [[ -e "$dest" && ! -x "$dest" ]]; then
                record_operation "set executable bit: $rel" "Set executable bit: $rel"
            fi
        else
            chmod +x "$dest"
        fi
    fi

    append_installed_file "$rel" "$source_sha"
}

remove_file() {
    local rel="$1"
    local dest="$target/$rel"

    [[ -e "$dest" || -L "$dest" ]] || return 0
    if [[ ! -f "$dest" && ! -L "$dest" ]]; then
        die "expected removable file but found directory: $rel"
    fi

    if should_backup_before_change "$rel"; then
        backup_file "$rel"
    fi

    record_operation "remove stale file: $rel" "Removed stale file: $rel"
    removed_paths[${#removed_paths[@]}]="$rel"

    if [[ "$dry_run" != true ]]; then
        rm -f "$dest"
    fi
}

remove_empty_reference_dirs() {
    local refs_rel="$1"
    local refs_dir="$target/$refs_rel"
    local dir

    [[ "$dry_run" != true ]] || return 0
    [[ -d "$refs_dir" ]] || return 0

    while IFS= read -r dir; do
        [[ "$dir" != "$refs_dir" ]] || continue
        rmdir "$dir" 2>/dev/null || true
    done < <(find "$refs_dir" -depth -type d 2>/dev/null)
}

prepare_owned_subdir() {
    local prefix="$1"
    local subdir="$2"
    local source_dir="$3"
    local refs_rel="$prefix/$subdir"
    local refs_dir="$target/$refs_rel"
    local existing
    local rel
    local file_name

    if [[ -d "$refs_dir" ]]; then
        while IFS= read -r existing; do
            rel="${existing#$target/}"
            file_name="${rel#$refs_rel/}"
            if [[ ! -f "$source_dir/$file_name" ]]; then
                remove_file "$rel"
            fi
        done < <(find "$refs_dir" \( -type f -o -type l \) -print 2>/dev/null | sort)
        remove_empty_reference_dirs "$refs_rel"
    fi

    ensure_dir "$refs_rel"
}

install_owned_subdir() {
    local prefix="$1"
    local subdir="$2"
    local source_dir="$3"
    local source_file
    local source_prefix="$source_dir/"
    local file_name

    prepare_owned_subdir "$prefix" "$subdir" "$source_dir"

    while IFS= read -r source_file; do
        file_name="${source_file#$source_prefix}"
        install_file "$source_file" "$prefix/$subdir/$file_name" false
    done < <(find "$source_dir" -type f -print | sort)
}

install_references() {
    install_owned_subdir "$1" "references" "$src/references"
}

install_phase_prompts() {
    install_owned_subdir "$1" "phase_prompts" "$src/phase_prompts"
}

install_layout() {
    local selected="$1"
    local prefix

    prefix="$(layout_prefix "$selected")"
    echo "Layout: $selected ($prefix)"

    install_file "$src/SKILL.md" "$prefix/SKILL.md" false
    install_file "$src/LICENSE.txt" "$prefix/LICENSE.txt" false
    install_references "$prefix"
    install_phase_prompts "$prefix"
    remove_file "$prefix/quality_gate.sh"
    install_file "$src/.github/skills/quality_gate/quality_gate.py" "$prefix/quality_gate.py" true
}

install_agents() {
    local agents_rel="agents"
    local agents_dir="$target/$agents_rel"
    local existing
    local rel
    local name
    local source_file

    if [[ -d "$agents_dir" ]]; then
        while IFS= read -r existing; do
            rel="${existing#$target/}"
            name="$(basename "$existing")"
            if [[ ! -f "$src/agents/$name" ]]; then
                remove_file "$rel"
            fi
        done < <(find "$agents_dir" -maxdepth 1 \( -type f -o -type l \) -name 'quality-playbook*.agent.md' -print 2>/dev/null | sort)
    fi

    ensure_dir "$agents_rel"
    while IFS= read -r source_file; do
        name="$(basename "$source_file")"
        install_file "$source_file" "$agents_rel/$name" false
    done < <(find "$src/agents" -maxdepth 1 -type f -name 'quality-playbook*.agent.md' -print | sort)
}

write_manifest() {
    local manifest_tmp="$manifest.tmp.$$"
    local index
    local rel
    local sha
    local selected

    {
        echo "{"
        echo "  \"installer_version\": \"$(json_escape "$INSTALLER_VERSION")\","
        echo "  \"quality_playbook_version\": \"$(json_escape "$qpb_version")\","
        echo "  \"installed_at\": \"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\","
        echo "  \"selected_layouts\": ["
        index=0
        for selected in ${selected_layouts[@]+"${selected_layouts[@]}"}; do
            if [[ $index -gt 0 ]]; then
                echo ","
            fi
            printf '    "%s"' "$(json_escape "$selected")"
            index=$((index + 1))
        done
        echo ""
        echo "  ],"
        echo "  \"installed_files\": ["
        index=0
        while [[ $index -lt ${#installed_paths[@]} ]]; do
            rel="${installed_paths[$index]}"
            sha="${installed_shas[$index]}"
            if [[ $index -gt 0 ]]; then
                echo ","
            fi
            printf '    {"path": "%s", "sha256": "%s"}' "$(json_escape "$rel")" "$(json_escape "$sha")"
            index=$((index + 1))
        done
        echo ""
        echo "  ],"
        echo "  \"removed_stale_files\": ["
        index=0
        for rel in ${removed_paths[@]+"${removed_paths[@]}"}; do
            if [[ $index -gt 0 ]]; then
                echo ","
            fi
            printf '    "%s"' "$(json_escape "$rel")"
            index=$((index + 1))
        done
        echo ""
        echo "  ]"
        echo "}"
    } > "$manifest_tmp"

    mv "$manifest_tmp" "$manifest"
}

layout_list() {
    local index=0
    local selected
    for selected in ${selected_layouts[@]+"${selected_layouts[@]}"}; do
        if [[ $index -gt 0 ]]; then
            printf ', '
        fi
        printf '%s' "$selected"
        index=$((index + 1))
    done
}

select_layouts

if [[ "$dry_run" == true ]]; then
    echo "Dry run for Quality Playbook install into: $target"
else
    echo "Installing Quality Playbook into: $target"
fi
echo "Selected layouts: $(layout_list)"

for selected in ${selected_layouts[@]+"${selected_layouts[@]}"}; do
    install_layout "$selected"
done

install_agents
ensure_dir "reference_docs/cite"

if [[ "$dry_run" == true ]]; then
    record_operation "write manifest: $manifest_rel" "Wrote manifest: $manifest_rel"
else
    write_manifest
    echo "Wrote manifest: $manifest_rel"
fi

if [[ $operation_count -eq 0 ]]; then
    echo "No file changes needed."
fi

echo ""
if [[ "$dry_run" == true ]]; then
    echo "Dry run complete; no files changed."
else
    echo "Installed Quality Playbook."
    echo "  layouts:  $(layout_list)"
    echo "  manifest: $manifest_rel"
    if [[ ${#backup_paths[@]} -gt 0 ]]; then
        echo "  backups:  $backup_root_rel/$backup_timestamp"
    fi
fi
