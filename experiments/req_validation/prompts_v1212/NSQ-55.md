git checkout 3ee16a5

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
- nsqd/protocol_v2.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_v1212/NSQ-55_review.md

git checkout master
