#!/usr/bin/env python3
"""Normalize all defect categories to exactly 14 canonical labels.

Usage:
    python3 tooling/normalize_categories.py [--library PATH]

Defaults assume you're running from the QPB repo root:
    --library  dataset/DEFECT_LIBRARY.md
"""
import argparse
import re
from collections import defaultdict
from pathlib import Path

CANONICAL = [
    "validation gap",
    "error handling",
    "type safety",
    "state machine gap",
    "configuration error",
    "concurrency issue",
    "silent failure",
    "API contract violation",
    "null safety",
    "protocol violation",
    "serialization",
    "security issue",
    "missing boundary check",
    "SQL error",
]
CANONICAL_SET = {c.lower() for c in CANONICAL}
CANONICAL_DISPLAY = {c.lower(): c for c in CANONICAL}

def normalize(raw: str) -> str:
    """Map any raw category string to one of exactly 14 canonical categories."""
    # Strip markdown bold, parenthetical qualifiers, slashes
    clean = raw.strip().replace('**', '').strip()
    clean = re.sub(r'\s*\(.*?\)', '', clean).strip()
    low = clean.lower()

    # Already canonical
    if low in CANONICAL_SET:
        return CANONICAL_DISPLAY[low]

    # Handle compound "X / Y" or "X/Y" — take the first
    if '/' in low:
        first = low.split('/')[0].strip()
        if first in CANONICAL_SET:
            return CANONICAL_DISPLAY[first]

    # Keyword-based mapping (order matters — more specific first)
    rules = [
        # Security
        (["security", "auth", "csrf", "xss", "injection", "credential", "permission",
          "access control", "token handling", "password", "account lock", "session manage",
          "ssl", "tls", "certificate", "cve", "vulnerability", "sanitiz"], "security issue"),

        # SQL / database
        (["sql", "query generation", "query building", "query safety", "dml", "ddl",
          "migration", "schema migration", "activerecord", "database", "sqlite",
          "postgres", "mysql", "migration consistency"], "SQL error"),

        # Concurrency
        (["concurrency", "race", "deadlock", "thread", "parallel", "atomic", "synchron",
          "mutex", "lock", "data race", "race condition", "cache concurrency",
          "web ui/race"], "concurrency issue"),

        # Serialization / encoding / parsing
        (["serial", "deserial", "json", "xml", "encode", "decode", "marshal", "unmarshal",
          "parse", "pars", "format filter", "protobuf", "cbor", "codec", "content decod",
          "encoding", "base64", "yaml", "jsonb", "csv", "binary format",
          "string format", "string pars", "time format", "output format",
          "json type", "json pars", "polymorphism", "descriptor", "reflection",
          "rendering", "css pars", "source map"], "serialization"),

        # Protocol
        (["protocol", "http", "websocket", "rfc", "spec compliance", "mqtt",
          "connection reuse", "form pars", "request routing", "response handl",
          "request handl", "request valid", "request header", "request body",
          "http response", "http content", "http auth", "http header", "http server",
          "http method", "content negotiat", "uri handl", "redirect handl",
          "header handl", "proxy", "streaming", "sse", "longpoll", "backpressure",
          "endpoint"], "protocol violation"),

        # Null safety
        (["null", "nil", "none", "npe", "nullpointer", "optional", "null pointer",
          "uninitialized"], "null safety"),

        # State machine / lifecycle
        (["state machine", "lifecycle", "state manage", "initialization", "init timing",
          "shutdown", "cleanup", "channel lifecycle", "transaction lifecycle",
          "transaction state", "transaction manage", "queue lifecycle", "job lifecycle",
          "job state", "job execution", "coroutine lifecycle", "cache state",
          "entity cache", "entity load", "cron pars", "scheduling", "supervision",
          "peer election", "pruning", "job update", "plugin", "batch operation",
          "unique job", "job iteration", "execution"], "state machine gap"),

        # Configuration / build / dependency / platform
        (["config", "configuration", "setting", "option", "flag", "build",
          "dependency", "platform", "compat", "cross-platform", "portability",
          "windows", "installation", "cli tool", "autoload", "generator",
          "idn", "module", "module resolution", "module loading", "module boundary",
          "module federation", "module api", "module library", "externals",
          "import", "loader", "tree shaking", "web worker", "code generation",
          "asset", "integration", "rails adapter", "rails integration",
          "dependency injection", "php 7", "php 8", "r2dbc", "driver compat",
          "module coupling", "verified route", "presence", "channel test",
          "optimization", "hot module", "css hot", "constants"], "configuration error"),

        # Missing boundary check
        (["boundary", "overflow", "underflow", "limit", "range", "off-by-one",
          "integer overflow", "buffer overflow", "out-of-bound", "recursion limit",
          "arithmetic", "calculation", "accounting", "aggregation"], "missing boundary check"),

        # Type safety
        (["type safety", "type mismatch", "type cast", "type error", "generic",
          "type coercion", "type mapping", "type transform", "type/jsdoc",
          "schema type", "lifetime", "r8/obfusc", "typing"], "type safety"),

        # Silent failure
        (["silent", "swallow", "ignore", "suppress", "lost", "data loss",
          "data corrupt", "api/data"], "silent failure"),

        # API contract
        (["api contract", "contract violation", "breaking change", "api compat",
          "api/debug", "backwards compat", "feature complete",
          "incomplete implement", "api", "cli/api", "concurrency/api",
          "security/api"], "API contract violation"),

        # Error handling (broad — catches resource leaks, crashes, etc.)
        (["error", "exception", "resource leak", "resource cleanup", "resource manage",
          "crash", "reliability", "memory leak", "memory safe", "memory manage",
          "memory alloc", "use-after-free", "i/o", "file i/o", "signal",
          "infinite loop", "loop control", "control flow", "logging",
          "error message", "assertion", "flaky test", "test reliab", "test infra",
          "test environment", "test framework", "test coverage",
          "web ui", "web framework", "middleware", "email confirm",
          "notification", "progress callback", "metrics",
          "dns resolution", "connection handl", "stream handl",
          "event loop", "cluster", "async", "timeout",
          "sort", "regex", "behavior change", "inversion",
          "performance", "scoping", "routing", "routing bug",
          "routing error", "routing tree", "build error",
          "css", "accessibility", "documentation", "lockfile",
          "network", "download", "version constraint",
          "caching", "cache manage", "cache clear",
          "timestamp", "cookie", "delay middleware",
          "logging middleware", "search correct",
          "completion", "shell", "bash", "zsh", "fish", "powershell",
          "help text", "man page", "argument", "output behav",
          "code quality", "general", "edge case", "correctness",
          "logic error", "data structure", "filter express",
          "script", "rule logic", "autofix", "regression",
          "acti", "rails", "path", "core correct",
          "unicode", "query perform"], "error handling"),

        # Validation gap (default fallback for anything left)
        (["valid", "input", "check", "missing", "gap", "testing"], "validation gap"),
    ]

    for keywords, category in rules:
        for kw in keywords:
            if kw in low:
                return CANONICAL_DISPLAY[category.lower()]

    # Hard fallback
    return "validation gap"


# --- Main ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize QPB defect categories")
    parser.add_argument("--library", type=Path, default=Path("dataset/DEFECT_LIBRARY.md"),
                        help="Path to DEFECT_LIBRARY.md")
    args = parser.parse_args()
    LIBRARY = args.library

    content = LIBRARY.read_text()
    lines = content.split('\n')
    changes = 0
    before_dist = defaultdict(int)
    after_dist = defaultdict(int)

    new_lines = []
    for line in lines:
        m = re.match(r'^(\| [A-Z]+-\d+\s*)', line)
        if m and line.count('|') >= 8:
            parts = line.split('|')
            if len(parts) >= 8:
                raw_cat = parts[6].strip()
                before_dist[raw_cat] += 1
                normalized = normalize(raw_cat)
                after_dist[normalized] += 1
                if raw_cat != normalized:
                    parts[6] = f' {normalized} '
                    line = '|'.join(parts)
                    changes += 1
        new_lines.append(line)

    content = '\n'.join(new_lines)

    # Rebuild category distribution table
    total = sum(after_dist.values())
    cat_table = "## Category Distribution\n\n| Category | Count | % |\n|----------|-------|---|\n"
    for cat, count in sorted(after_dist.items(), key=lambda x: -x[1]):
        pct = 100.0 * count / total if total > 0 else 0
        cat_table += f"| {cat} | {count} | {pct:.1f}% |\n"

    cat_start = content.find('## Category Distribution')
    cat_end = content.find('\n## Project Classification')
    content = content[:cat_start] + cat_table + content[cat_end:]

    LIBRARY.write_text(content)

    print(f"Normalized {changes} rows out of {total}")
    print(f"Before: {len(before_dist)} distinct categories")
    print(f"After:  {len(after_dist)} distinct categories")
    print()
    print("=== FINAL DISTRIBUTION ===")
    for cat, count in sorted(after_dist.items(), key=lambda x: -x[1]):
        pct = 100.0 * count / total
        print(f"  {count:4d} ({pct:5.1f}%)  {cat}")

    # Verify no non-canonical survived
    remaining = set(after_dist.keys()) - {CANONICAL_DISPLAY[c] for c in CANONICAL_SET}
    if remaining:
        print(f"\nWARNING: {len(remaining)} non-canonical categories remain: {remaining}")
    else:
        print(f"\nAll {total} rows now use exactly 14 canonical categories.")
