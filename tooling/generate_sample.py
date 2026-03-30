#!/usr/bin/env python3
"""Generate a complete sample per-repo description file for CURL (first 5 defects).
This tests the full format before scaling up."""
import json
import subprocess
from pathlib import Path

DATA_FILE = Path("tooling/defect_data.json")
REPOS_DIR = Path("repos")

with open(DATA_FILE) as f:
    all_data = json.load(f)

# Get CURL defects sorted by number
curl_ids = sorted(
    [k for k in all_data if k.startswith("CURL-")],
    key=lambda x: int(x.split("-")[1])
)

# Build output for first 5
output_lines = []
for defect_id in curl_ids[:5]:
    d = all_data[defect_id]

    output_lines.append(f"### {defect_id} | {d['title']} | {d['category']} | {d['severity']}")
    output_lines.append("")

    # Fix and pre-fix SHAs
    output_lines.append(f"**Fix commit**: `{d['fix_sha']}`")
    output_lines.append(f"**Pre-fix commit**: `{d['pre_fix_sha']}`")
    output_lines.append(f"**GitHub**: https://github.com/{d['github_repo']}/commit/{d['fix_sha']}")

    # Issue/PR references
    if d['issue_refs']:
        refs = []
        for ref in d['issue_refs']:
            if ref.isdigit():
                refs.append(f"https://github.com/{d['github_repo']}/pull/{ref}")
            else:
                if 'ZOOKEEPER' in ref or 'KAFKA' in ref:
                    refs.append(f"https://issues.apache.org/jira/browse/{ref}")
                else:
                    refs.append(ref)
        # Deduplicate
        seen = set()
        unique_refs = []
        for r in refs:
            if r not in seen:
                seen.add(r)
                unique_refs.append(r)
        output_lines.append(f"**Issue/PR**: {', '.join(unique_refs)}")
    output_lines.append("")

    # Files changed
    output_lines.append("**Files changed**:")
    for f_name in d['files_changed']:
        output_lines.append(f"- `{f_name}`")
    output_lines.append("")

    # Commit message
    output_lines.append("**Commit message**:")
    output_lines.append("```")
    output_lines.append(d['commit_message'])
    output_lines.append("```")
    output_lines.append("")

    # Diff summary (from our existing description in DEFECT_LIBRARY)
    output_lines.append(f"**Defect summary**: {d['description']}")
    output_lines.append("")

    # Git diff stat
    if d['diff_stat']:
        output_lines.append("**Diff stat**:")
        output_lines.append("```")
        output_lines.append(d['diff_stat'])
        output_lines.append("```")
        output_lines.append("")

    output_lines.append(f"**Playbook angle**: {d['playbook_angle']}")
    output_lines.append("")

    # Placeholder for GitHub issue text (to be fetched)
    output_lines.append("**Original issue description**: *(to be fetched from GitHub)*")
    output_lines.append("")
    output_lines.append("---")
    output_lines.append("")

print('\n'.join(output_lines))
