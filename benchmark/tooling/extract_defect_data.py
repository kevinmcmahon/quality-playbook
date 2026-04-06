#!/usr/bin/env python3
"""Extract local git data for all QPB defects: commit message, files changed, diff summary.

Usage:
    python3 tooling/extract_defect_data.py [--library PATH] [--repos PATH] [--output PATH]

Defaults assume you're running from the QPB repo root:
    --library  dataset/DEFECT_LIBRARY.md
    --repos    repos/
    --output   tooling/defect_data.json
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from collections import defaultdict

parser = argparse.ArgumentParser(description="Extract git data for QPB defects")
parser.add_argument("--library", type=Path, default=Path("dataset/DEFECT_LIBRARY.md"),
                    help="Path to DEFECT_LIBRARY.md")
parser.add_argument("--repos", type=Path, default=Path("repos"),
                    help="Path to directory containing cloned repos")
parser.add_argument("--output", type=Path, default=Path("tooling/defect_data.json"),
                    help="Output path for extracted JSON data")
args = parser.parse_args()

LIBRARY = args.library
REPOS_DIR = args.repos
OUTPUT = args.output

# Map prefix -> (repo_dir_name, github_owner_repo)
PREFIX_MAP = {
    "GH": ("cli", "cli/cli"),
    "CURL": ("curl", "curl/curl"),
    "RLS": ("rails", "rails/rails"),
    "ZK": ("zookeeper", "apache/zookeeper"),
    "MT": ("MassTransit", "MassTransit/MassTransit"),
    "PYD": ("pydantic", "pydantic/pydantic"),
    "WP": ("webpack", "webpack/webpack"),
    "ESL": ("eslint", "eslint/eslint"),
    "NJ": ("Newtonsoft.Json", "JamesNK/Newtonsoft.Json"),
    "OK": ("okhttp", "square/okhttp"),
    "AX": ("axum", "tokio-rs/axum"),
    "SER": ("serde", "serde-rs/serde"),
    "TRPC": ("trpc", "trpc/trpc"),
    "ZOD": ("zod", "colinhacks/zod"),
    "COB": ("cobra", "spf13/cobra"),
    "CHI": ("chi", "go-chi/chi"),
    "RQ": ("rq", "rq/rq"),
    "RG": ("ripgrep", "BurntSushi/ripgrep"),
    "CFG": ("config", "lightbend/config"),
    "HF": ("Hangfire", "HangfireIO/Hangfire"),
    "NSQ": ("nsq", "nsqio/nsq"),
    "PRI": ("prisma", "prisma/prisma"),
    "CAL": ("calcom", "calcom/cal.com"),
    "JF": ("jellyfin", "jellyfin/jellyfin"),
    "GB": ("gitbucket", "gitbucket/gitbucket"),
    "LN": ("log4net", "apache/logging-log4net"),
    "KFK": ("kafka", "apache/kafka"),
    "FIN": ("finatra", "twitter/finatra"),
    "AKK": ("akka", "akka/akka"),
    "HX": ("httpx", "encode/httpx"),
    "FA": ("fastapi", "tiangolo/fastapi"),
    "RED": ("redis", "redis/redis"),
    "JQ": ("jq", "jqlang/jq"),
    "EXP": ("express", "expressjs/express"),
    "LAR": ("laravel", "laravel/framework"),
    "GUZ": ("guzzle", "guzzle/guzzle"),
    "CMP": ("composer", "composer/composer"),
    "DEV": ("devise", "heartcombo/devise"),
    "SK": ("sidekiq", "sidekiq/sidekiq"),
    "KT": ("ktor", "ktorio/ktor"),
    "EXD": ("Exposed", "JetBrains/Exposed"),
    "KS": ("kotlinx.serialization", "Kotlin/kotlinx.serialization"),
    "NATS": ("nats.rs", "nats-io/nats.rs"),
    "QK": ("quarkus", "quarkusio/quarkus"),
    "VAP": ("vapor", "vapor/vapor"),
    "NIO": ("swift-nio", "apple/swift-nio"),
    "PHX": ("phoenix", "phoenixframework/phoenix"),
    "ECT": ("ecto", "elixir-ecto/ecto"),
    "OB": ("oban", "oban-bg/oban"),
    "EQ": ("edgequake", "raphaelmansuy/edgequake"),
    "AS": ("agentscope-java", "alibaba/AgentScope"),
    # Legacy prefixes from initial mining rounds
    "P": ("spring-petclinic", "spring-projects/spring-petclinic"),
    "G": ("gson", "google/gson"),
    "J": ("javalin", "javalin/javalin"),
    "O": ("octobatch", "andrewstellman/octobatch"),
}


def git_cmd(repo_dir, *args):
    """Run a git command and return stdout."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print(f"  WARNING: git command failed in {repo_dir}: {e}", file=sys.stderr)
        return ""


def extract_issue_refs(msg):
    """Extract issue/PR numbers from commit message."""
    refs = []
    # Patterns: Closes #123, Fixes #123, Resolves #123, (#123), #123
    for m in re.finditer(r'(?:Closes|Fixes|Resolves|Refs?|See)\s*:?\s*#(\d+)', msg, re.I):
        refs.append(int(m.group(1)))
    for m in re.finditer(r'\(#(\d+)\)', msg):
        refs.append(int(m.group(1)))
    # JIRA-style: ZOOKEEPER-1234, KAFKA-1234
    for m in re.finditer(r'([A-Z]+-\d+)', msg):
        jira = m.group(1)
        if not jira.startswith(('Co-', 'SHA-')):
            refs.append(jira)
    # "from user/branch" pattern in GitHub merge commits
    for m in re.finditer(r'from\s+\S+/(\S+)', msg):
        pass  # branch names aren't issue numbers
    return refs


def extract_defect(prefix, defect_id, fix_sha, pre_fix_sha, severity, category, description, playbook_angle, repo_dir, github_path):
    """Extract full defect data from git."""
    # Commit message
    commit_msg = git_cmd(repo_dir, "log", "--format=%B", fix_sha, "-1")

    # Files changed
    files = git_cmd(repo_dir, "diff-tree", "--no-commit-id", "--name-only", "-r", fix_sha)
    files_list = [f for f in files.split('\n') if f.strip()] if files else []

    # Diff stat
    diff_stat = git_cmd(repo_dir, "diff", "--stat", f"{pre_fix_sha}..{fix_sha}")

    # Diff (abbreviated for large diffs)
    diff = git_cmd(repo_dir, "diff", f"{pre_fix_sha}..{fix_sha}")
    diff_lines = len(diff.split('\n')) if diff else 0

    # Issue references
    issue_refs = extract_issue_refs(commit_msg)

    # Build GitHub issue URLs
    issue_urls = []
    for ref in issue_refs:
        if isinstance(ref, int):
            # Could be issue or PR - we'll try both
            issue_urls.append(f"https://github.com/{github_path}/issues/{ref}")
            issue_urls.append(f"https://github.com/{github_path}/pull/{ref}")
        elif isinstance(ref, str):
            # JIRA-style - construct URL based on project
            if 'ZOOKEEPER' in ref:
                issue_urls.append(f"https://issues.apache.org/jira/browse/{ref}")
            elif 'KAFKA' in ref:
                issue_urls.append(f"https://issues.apache.org/jira/browse/{ref}")

    return {
        "id": defect_id,
        "prefix": prefix,
        "fix_sha": fix_sha,
        "pre_fix_sha": pre_fix_sha,
        "severity": severity,
        "category": category,
        "description": description,
        "playbook_angle": playbook_angle,
        "commit_message": commit_msg,
        "files_changed": files_list,
        "file_count": len(files_list),
        "diff_stat": diff_stat,
        "diff_lines": diff_lines,
        "issue_refs": [str(r) for r in issue_refs],
        "issue_urls": issue_urls,
        "github_repo": github_path,
    }


# Parse DEFECT_LIBRARY
print("Parsing DEFECT_LIBRARY.md...")
content = LIBRARY.read_text()
defects = []
skipped = 0

for line in content.split('\n'):
    m = re.match(r'^\| ([A-Z]+)-(\d+)\s*\|', line)
    if not m or line.count('|') < 8:
        continue

    parts = line.split('|')
    prefix = m.group(1)
    num = m.group(2)
    defect_id = f"{prefix}-{num}"

    if prefix not in PREFIX_MAP:
        skipped += 1
        continue

    repo_name, github_path = PREFIX_MAP[prefix]
    repo_dir = REPOS_DIR / repo_name

    if not repo_dir.exists():
        skipped += 1
        continue

    issue_ref = parts[2].strip()  # Issue/PR number (e.g., "#2068"), not a title
    fix_sha = parts[3].strip().strip('`')
    pre_fix_sha = parts[4].strip().strip('`')
    severity = parts[5].strip()
    category = parts[6].strip()
    description = parts[7].strip()
    playbook_angle = parts[8].strip() if len(parts) > 8 else ""

    defects.append({
        "defect_id": defect_id,
        "prefix": prefix,
        "issue_ref": issue_ref,
        "fix_sha": fix_sha,
        "pre_fix_sha": pre_fix_sha,
        "severity": severity,
        "category": category,
        "description": description,
        "playbook_angle": playbook_angle,
        "repo_name": repo_name,
        "github_path": github_path,
    })

print(f"Found {len(defects)} defects, skipped {skipped}")

# Group by prefix
by_prefix = defaultdict(list)
for d in defects:
    by_prefix[d["prefix"]].append(d)

print(f"Across {len(by_prefix)} prefixes")

# Extract git data for all defects
print("Extracting git data...")
results = {}
for i, d in enumerate(defects):
    repo_dir = REPOS_DIR / d["repo_name"]
    data = extract_defect(
        d["prefix"], d["defect_id"], d["fix_sha"], d["pre_fix_sha"],
        d["severity"], d["category"], d["description"], d["playbook_angle"],
        repo_dir, d["github_path"]
    )
    data["issue_ref"] = d["issue_ref"]
    results[d["defect_id"]] = data

    if (i + 1) % 100 == 0:
        print(f"  Processed {i+1}/{len(defects)}...")

# Save
with open(OUTPUT, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nSaved {len(results)} defects to {OUTPUT}")

# Stats
has_refs = sum(1 for d in results.values() if d["issue_refs"])
has_files = sum(1 for d in results.values() if d["files_changed"])
has_msg = sum(1 for d in results.values() if d["commit_message"])
print(f"  With issue refs: {has_refs}/{len(results)}")
print(f"  With files changed: {has_files}/{len(results)}")
print(f"  With commit message: {has_msg}/{len(results)}")

# Show issue refs breakdown
ref_counts = defaultdict(int)
for d in results.values():
    if d["issue_refs"]:
        ref_counts["has_refs"] += 1
    else:
        ref_counts["no_refs"] += 1
    for url in d["issue_urls"]:
        if "github.com" in url:
            ref_counts["github"] += 1
        elif "jira" in url:
            ref_counts["jira"] += 1

print(f"\nIssue URL types:")
for k, v in sorted(ref_counts.items()):
    print(f"  {k}: {v}")
