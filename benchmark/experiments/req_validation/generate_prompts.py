#!/usr/bin/env python3
"""Generate prompts for the requirements validation experiment.

4 conditions × 16 defects = 64 prompts.

Conditions:
  A. control — generic review (same as original benchmark)
  B. specific — precise testable requirements per defect
  C. abstract — higher-abstraction requirements (what the playbook would generate)
  D. v1.2.12 — focus-area-based review protocol
"""

import os
import json

EXPERIMENT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Defect metadata ──────────────────────────────────────────────────────────
# Each entry: (defect_id, pre_fix_commit, files_to_review, specific_req, abstract_req)

DEFECTS = [
    {
        "id": "NSQ-04",
        "pre_fix": "ac1627bba",
        "files": ["nsqd/nsqd.go", "nsqd/tcp.go"],
        "specific": (
            "NSQD.Exit() must close ALL active TCP connections (both producer and consumer), "
            "not just close the listener. Goroutines blocked on conn.Read() will hang indefinitely "
            "if the connection is not explicitly closed. Check that Exit() iterates over active "
            "connections and closes each one."
        ),
        "abstract": (
            "Graceful shutdown must release all held resources. When a server stops, every active "
            "connection must be closed — stopping the listener alone is insufficient if existing "
            "connections remain open."
        ),
    },
    {
        "id": "NSQ-12",
        "pre_fix": "6774510b9",
        "files": ["nsqd/channel.go", "nsqd/topic.go"],
        "specific": (
            "When --mem-queue-size=0 and the topic/channel is not ephemeral, no memory channel "
            "should be created. An unbuffered channel (make(chan *Message, 0)) is not equivalent "
            "to 'no channel' — it blocks on every send. The implementation must skip memory "
            "channel creation entirely and route to the backend disk queue."
        ),
        "abstract": (
            "Configuration values of zero must mean 'disabled/none', not 'zero-sized'. When a "
            "capacity parameter is set to 0, the feature should be bypassed entirely rather than "
            "creating a zero-capacity resource that blocks."
        ),
    },
    {
        "id": "NSQ-14",
        "pre_fix": "62c385896",
        "files": ["nsqd/protocol_v2.go"],
        "specific": (
            "When a REQ command specifies a timeout outside the valid range [0, MaxReqTimeout], "
            "the server must clamp the value to the valid range and continue processing. It must "
            "NOT send E_INVALID (a fatal protocol error) that disconnects the client. Out-of-range "
            "parameters are a recoverable condition, not a protocol violation."
        ),
        "abstract": (
            "Protocol commands with out-of-range numeric parameters should produce recoverable "
            "errors or clamped values, not fatal errors that terminate the connection. Clients "
            "should not be disconnected for providing values outside an allowed range."
        ),
    },
    {
        "id": "NSQ-19",
        "pre_fix": "e8e1040d4",
        "files": ["nsqd/protocol_v2.go"],
        "specific": (
            "When a client negotiates deflate compression via IDENTIFY, the server must use the "
            "client's requested deflate level, clamped to the configured --max-deflate-level. "
            "If the client requests level 3 and max is 9, the server must use 3 — not substitute "
            "a default of 6. Check the IDENTIFY handler's deflate level logic."
        ),
        "abstract": (
            "Protocol negotiation must honor the client's requested parameters within configured "
            "bounds. The server must not substitute defaults when the client provides a valid "
            "value within the allowed range."
        ),
    },
    {
        "id": "NSQ-22",
        "pre_fix": "9faeb4a84",
        "files": ["internal/protocol/tcp_server.go"],
        "specific": (
            "TCPServer must track all spawned per-connection handler goroutines using a WaitGroup "
            "or equivalent, and wait for them to complete during shutdown. Currently, the server "
            "returns from its serve loop without waiting for handlers, allowing goroutines to "
            "access freed resources."
        ),
        "abstract": (
            "Server shutdown must wait for all spawned handler goroutines to complete before "
            "returning. Goroutines that outlive their parent server can access freed resources "
            "and cause data races."
        ),
    },
    {
        "id": "NSQ-33",
        "pre_fix": "51b270f",
        "files": ["nsqadmin/http.go"],
        "specific": (
            "All mutating admin endpoints in nsqadmin must call isAuthorizedAdminRequest() before "
            "processing. Check that tombstoneNodeForTopicHandler has the same authorization check "
            "as the other admin mutation handlers (delete topic, delete channel, pause, unpause)."
        ),
        "abstract": (
            "All mutating endpoints must enforce authorization consistently. If some admin "
            "endpoints check permissions but others skip the check, unauthenticated users can "
            "perform administrative operations through the unguarded endpoints."
        ),
    },
    {
        "id": "NSQ-36",
        "pre_fix": "cb83885",
        "files": ["nsqd/nsqd.go", "nsqd/options.go"],
        "specific": (
            "E2E processing latency percentile configuration values must be validated at parse "
            "time to be in the range (0, 1.0]. Values like 0, negative numbers, or values > 1.0 "
            "(e.g. 100.0) must be rejected with a clear error at startup. Check whether the "
            "config parsing validates this constraint."
        ),
        "abstract": (
            "Configuration values with domain-specific constraints must be validated at parse "
            "time, not silently accepted. Percentile values, ratios, and other bounded parameters "
            "must be range-checked before use."
        ),
    },
    {
        "id": "NSQ-37",
        "pre_fix": "c4e2add",
        "files": ["internal/clusterinfo/types.go"],
        "specific": (
            "Producer.HTTPAddress() and TCPAddress() must use net.JoinHostPort() to produce "
            "valid host:port strings for both IPv4 and IPv6. Using fmt.Sprintf(\"%s:%d\") "
            "produces ambiguous addresses for IPv6 (e.g. '::1:4150' instead of '[::1]:4150')."
        ),
        "abstract": (
            "Network address formatting must produce valid strings for both IPv4 and IPv6. "
            "Any code constructing host:port strings must use the standard library's address "
            "formatting functions rather than string concatenation."
        ),
    },
    {
        "id": "NSQ-39",
        "pre_fix": "98fbcd1",
        "files": ["nsqd/nsqd.go", "nsqd/guid.go"],
        "specific": (
            "Worker ID validation must reject values >= 1024 (2^10). The GUID format uses "
            "a 10-bit worker ID field (nodeIDBits=10), so valid IDs are [0, 1023]. If "
            "validation accepts [0, 4096), IDs 1024-4095 will silently produce GUID collisions "
            "because the upper bits are truncated."
        ),
        "abstract": (
            "Validation ranges for configuration parameters must match the actual bit width or "
            "storage capacity of the field they populate. Accepting values wider than the "
            "destination field causes silent truncation or collision."
        ),
    },
    {
        "id": "NSQ-41",
        "pre_fix": "77a46db",
        "files": ["nsqd/nsqd.go", "nsqd/options.go"],
        "specific": (
            "When -tls-required is set to true, the -tls-client-auth-policy flag must not "
            "silently override or downgrade that setting. If an operator explicitly sets "
            "-tls-required=true but doesn't set -tls-client-auth-policy, the TLS requirement "
            "must be preserved. Check the flag interaction logic in New()."
        ),
        "abstract": (
            "When multiple configuration flags control related security behavior, one flag must "
            "not silently override another. The interaction between security flags must preserve "
            "explicit operator intent."
        ),
    },
    {
        "id": "NSQ-42",
        "pre_fix": "47034fb",
        "files": ["nsqadmin/http.go"],
        "specific": (
            "nsqadmin node list links must bracket IPv6 addresses when constructing URLs. "
            "Without brackets, URLs like http://::1:4171/stats produce broken links. Check "
            "all places where node addresses are embedded in HTML links or URLs."
        ),
        "abstract": (
            "URL construction in web interfaces must handle IPv6 addresses correctly. "
            "Addresses embedded in URLs must be properly formatted for all address families."
        ),
    },
    {
        "id": "NSQ-44",
        "pre_fix": "1d183d9",
        "files": ["internal/auth/authorizations.go", "nsqd/nsqd.go"],
        "specific": (
            "The HTTP client used for nsqauth (auth server) requests must use the TLS "
            "configuration from --tls-root-ca-file, not the system default CAs. If a custom "
            "root CA is configured for the cluster, auth requests must use that same CA. "
            "Check whether the auth HTTP client's TLS config includes the configured RootCAs."
        ),
        "abstract": (
            "Outbound TLS connections must use the configured certificate authority, not system "
            "defaults. When a service is configured with a custom CA, all outbound TLS connections "
            "from that service must honor that configuration."
        ),
    },
    {
        "id": "NSQ-47",
        "pre_fix": "d3d0bbf",
        "files": ["nsqd/nsqd.go", "nsqd/tcp.go", "nsqd/protocol_v2.go"],
        "specific": (
            "NSQD.Exit() must close all active TCP client connections (consumer connections, "
            "not just producer connections). Clients remaining connected after shutdown prevent "
            "clean process exit. Check whether Exit() reaches consumer connections or only "
            "producer connections."
        ),
        "abstract": (
            "Graceful shutdown must close all active connections across all connection types. "
            "If different client types connect through different paths, shutdown must reach all "
            "of them."
        ),
    },
    {
        "id": "NSQ-48",
        "pre_fix": "5ea1012",
        "files": ["apps/nsq_to_file/file_logger.go"],
        "specific": (
            "FileLogger.Close() must flush and close the GZIP writer before syncing or closing "
            "the underlying file. If the file is synced first, buffered data in the GZIP writer "
            "is lost. Check the ordering of operations in Close() — gzip.Close() must come "
            "before file.Sync()."
        ),
        "abstract": (
            "Layered resource cleanup must flush higher-level wrappers before lower-level ones. "
            "When a compressed stream wraps a file, the compressor must be flushed before the "
            "file is synced or closed."
        ),
    },
    {
        "id": "NSQ-50",
        "pre_fix": "29114b3",
        "files": ["apps/nsq_to_file/nsq_to_file.go"],
        "specific": (
            "OS signal channels passed to signal.Notify() must be buffered with capacity >= 1. "
            "Go's signal package documentation states: 'the caller must ensure that c has "
            "sufficient buffer space.' An unbuffered channel drops signals that arrive while "
            "the receiver is not in a select."
        ),
        "abstract": (
            "Channels used for OS signal notification must be buffered. The Go standard library "
            "contract for signal.Notify requires the channel to have buffer space; unbuffered "
            "channels silently drop signals."
        ),
    },
    {
        "id": "NSQ-55",
        "pre_fix": "3ee16a5",
        "files": ["nsqd/protocol_v2.go"],
        "specific": (
            "The IDENTIFY response must return the actual negotiated msg_timeout value, not the "
            "server's default MsgTimeout. If a client requests a specific msg_timeout in IDENTIFY, "
            "and the server accepts it, the response JSON must contain that client-requested "
            "value so the client knows what timeout is in effect."
        ),
        "abstract": (
            "Protocol negotiation responses must confirm actual negotiated values, not defaults. "
            "When a client requests a specific parameter and the server accepts it, the response "
            "must reflect the agreed value."
        ),
    },
]


# ── v1.2.12 prompt template ──────────────────────────────────────────────────
# Simplified from the full RUN_CODE_REVIEW.md — we include the relevant focus
# areas and guardrails, but scoped to the specific files.

V1212_TEMPLATE = """\
git checkout {commit}

You are performing a structured code review following the NSQ v1.2.12 quality protocol.

## Context
Read README.md before reviewing. NSQ is a realtime distributed messaging platform.

## Focus Areas (check all that apply to the files under review)

1. **Protocol v2 startup and state transitions**: Verify IDENTIFY, AUTH, SUB, RDY, FIN, REQ, CLS, and heartbeat transitions respect client state, negotiated timeouts, compression/TLS behavior, and ready-count bounds. Read IOLoop(), Exec(), and messagePump() bodies.

2. **Topic/channel fanout, pause, and backlog behavior**: Check that topic pause toggles delivery correctly, fanout copies messages to all channels, and put/FinishMessage/RequeueMessage/TouchMessage keep ownership and queue invariants intact.

3. **Metadata persistence and restart integrity**: Verify metadata writes use temp-file-plus-rename, restart paths recreate paused topics/channels accurately, and shutdown closes listeners, topics, channels, and worker goroutines.

4. **Discovery registration, tombstones, and inactivity filtering**: Audit producer registration add/remove/tombstone/filter. Confirm topic-scoped tombstones stay scoped, disconnections drop live producers but not topology skeletons.

5. **Partial upstream failures in the admin plane**: Check every place that handles clusterinfo.PartialErr. Verify good data preserved, warnings surfaced, aggregations don't silently drop or mislabel partial results.

6. **HTTP validation and config mutation safety**: Verify topic/channel name validation, max-body checks, defer bounds, action parsing, CIDR checks, and config option mutations.

7. **Auth, ACL, and security-adjacent controls**: Check that auth state, TLS requirements, admin header gating, and security-sensitive config propagate through all sibling methods and endpoints.

## Guardrails
- Line numbers are mandatory. If you cannot cite a specific line, do not include the finding.
- Read function bodies, not just signatures.
- If unsure whether something is a bug or intentional, classify as QUESTION.
- Grep before claiming something is missing.
- Do not suggest style-only changes — only flag correctness, safety, or reliability issues.
- Check validation failure modes, not just validation existence.
- Enumerate all resource types in shutdown paths.

## Files to review
{files_list}

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to {review_path}

git checkout master
"""


# ── Control prompt template ───────────────────────────────────────────────────

CONTROL_TEMPLATE = """\
git checkout {commit}

Review the following files for bugs. Be thorough — read every function body, check boundary conditions, trace error paths, look for race conditions and resource leaks. Report only real bugs, not style issues.

Files to review:
{files_list}

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to {review_path}

git checkout master
"""


# ── Specific requirements prompt template ─────────────────────────────────────

SPECIFIC_TEMPLATE = """\
git checkout {commit}

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
{requirement}

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
{files_list}

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to {review_path}

git checkout master
"""


# ── Abstract requirements prompt template ─────────────────────────────────────

ABSTRACT_TEMPLATE = """\
git checkout {commit}

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
{requirement}

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
{files_list}

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to {review_path}

git checkout master
"""


def generate_all():
    for defect in DEFECTS:
        did = defect["id"]
        commit = defect["pre_fix"]
        files_list = "\n".join(f"- {f}" for f in defect["files"])

        # A. Control
        prompt = CONTROL_TEMPLATE.format(
            commit=commit,
            files_list=files_list,
            review_path=f"reviews_control/{did}_review.md",
        )
        write_prompt("prompts_control", did, prompt)

        # B. Specific requirements
        prompt = SPECIFIC_TEMPLATE.format(
            commit=commit,
            requirement=defect["specific"],
            files_list=files_list,
            review_path=f"reviews_specific/{did}_review.md",
        )
        write_prompt("prompts_specific", did, prompt)

        # C. Abstract requirements
        prompt = ABSTRACT_TEMPLATE.format(
            commit=commit,
            requirement=defect["abstract"],
            files_list=files_list,
            review_path=f"reviews_abstract/{did}_review.md",
        )
        write_prompt("prompts_abstract", did, prompt)

        # D. v1.2.12 focus areas
        prompt = V1212_TEMPLATE.format(
            commit=commit,
            files_list=files_list,
            review_path=f"reviews_v1212/{did}_review.md",
        )
        write_prompt("prompts_v1212", did, prompt)

    print(f"Generated {len(DEFECTS) * 4} prompts across 4 conditions")


def write_prompt(condition_dir, defect_id, content):
    path = os.path.join(EXPERIMENT_DIR, condition_dir, f"{defect_id}.md")
    with open(path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    generate_all()
