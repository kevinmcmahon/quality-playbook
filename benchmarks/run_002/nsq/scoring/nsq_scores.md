# NSQ Benchmark Scores — v1.2.10 Playbook, Opus 4.6

**Date:** 2026-04-01
**Repo:** nsq (Go message queue platform)
**Defects:** 58 total
**Model:** claude-opus-4.6

## Results Summary

| Score | Count | Percentage |
|-------|-------|------------|
| DIRECT HIT | 21 | 36% |
| ADJACENT | 8 | 14% |
| MISS | 25 | 43% |
| NO REVIEW | 4 | 7% |

**Direct + Adjacent: 29/58 = 50%**

## Detailed Scores

### Batch 1: NSQ-01 through NSQ-20

| ID | Score | Reason |
|----|-------|--------|
| NSQ-01 | DIRECT HIT | Identifies unguarded len(c.clients) read at line 441, exact race |
| NSQ-02 | DIRECT HIT | Identifies data races on inFlightMessages and deferredMessages |
| NSQ-03 | ADJACENT | Identifies mutex guard issues but not flush() iteration race |
| NSQ-04 | MISS | Does not identify missing TCP connection cleanup in Exit() |
| NSQ-05 | DIRECT HIT | Identifies copy-paste error in error message (TCPAddress vs HTTPAddress) |
| NSQ-06 | ADJACENT | Identifies error-handling in lookup sync but not infinite retry bug |
| NSQ-07 | DIRECT HIT | Identifies PutMessages undercounting messageCount on partial failure |
| NSQ-08 | MISS | Does not identify getMemStats nil pointer return issue |
| NSQ-09 | ADJACENT | Identifies lock-timing issues but not the pre-allocation bug |
| NSQ-10 | DIRECT HIT | Identifies missing deduplication in GetLookupdTopicProducers |
| NSQ-11 | ADJACENT | Identifies aggregation bugs but not JSON deserialization issue |
| NSQ-12 | MISS | Does not identify mem-queue-size=0 unbuffered channel blocking |
| NSQ-13 | DIRECT HIT | Identifies Close() nil check missing on lp.conn |
| NSQ-14 | MISS | Does not identify REQ timeout validation rejection |
| NSQ-15 | ADJACENT | Identifies PutMessageDeferred missing exitMutex but not specific RequeueMessage bug |
| NSQ-16 | DIRECT HIT | Identifies in-flight timeout started before confirming send success |
| NSQ-17 | MISS | Does not identify messagePump/RemoveClient buffered channel race |
| NSQ-18 | NO REVIEW | Timed out |
| NSQ-19 | MISS | Does not identify deflate level logic inversion |
| NSQ-20 | MISS | Does not identify 64-bit atomic alignment on 32-bit platforms |

### Batch 2: NSQ-21 through NSQ-40

| ID | Score | Reason |
|----|-------|--------|
| NSQ-21 | MISS | |
| NSQ-22 | ADJACENT | Found listener cleanup issues instead of WaitGroup tracking |
| NSQ-23 | NO REVIEW | Timed out |
| NSQ-24 | ADJACENT | Found listener leaks instead of os.Exit pattern issue |
| NSQ-25 | MISS | |
| NSQ-26 | MISS | |
| NSQ-27 | DIRECT HIT | Identifies SpreadWriter division by zero |
| NSQ-28 | MISS | |
| NSQ-29 | MISS | |
| NSQ-30 | DIRECT HIT | Identifies GenerateID infinite loop |
| NSQ-31 | MISS | |
| NSQ-32 | MISS | |
| NSQ-33 | DIRECT HIT | Identifies missing auth check |
| NSQ-34 | DIRECT HIT | Identifies variable scope issue |
| NSQ-35 | DIRECT HIT | Identifies break statement misbehavior |
| NSQ-36 | NO REVIEW | Timed out |
| NSQ-37 | MISS | |
| NSQ-38 | MISS | |
| NSQ-39 | MISS | |
| NSQ-40 | DIRECT HIT | Identifies timestamp truncation |

### Batch 3: NSQ-41 through NSQ-58

| ID | Score | Reason |
|----|-------|--------|
| NSQ-41 | MISS | Doesn't identify TLS flag override bug |
| NSQ-42 | NO REVIEW | Timed out |
| NSQ-43 | ADJACENT | Identifies Handlebars scope bug but not channel rate calculation |
| NSQ-44 | NO REVIEW | No review file — likely no changed source files |
| NSQ-45 | DIRECT HIT | Identifies unsynchronized map iteration in Topic.exit() |
| NSQ-46 | DIRECT HIT | Identifies file handle not closed in TestConfigFlagParsing |
| NSQ-47 | MISS | Doesn't identify missing tcpServer.Close() in NSQD.Exit() |
| NSQ-48 | DIRECT HIT | Identifies Close() calling Sync() before closing GZIP writer |
| NSQ-49 | ADJACENT | Identifies bugs in same file but not specific Close() ordering |
| NSQ-50 | DIRECT HIT | Identifies unbuffered signal channels issue |
| NSQ-51 | DIRECT HIT | Identifies data race on c.clients map in exit() |
| NSQ-52 | DIRECT HIT | Identifies data race on c.clients map in inFlightWorker |
| NSQ-53 | MISS | Doesn't identify deadlock issue with clientMsgChan |
| NSQ-54 | DIRECT HIT | Identifies Remove() calling Pop() after manipulation corrupting heap |
| NSQ-55 | MISS | Doesn't identify MsgTimeout response bug |
| NSQ-56 | MISS | Doesn't identify parameter parsing validation bug |
| NSQ-57 | MISS | Doesn't identify missing messagePump notification for channels |
| NSQ-58 | DIRECT HIT | Identifies GC pause percentile formula and circular buffer issues |

## Analysis

### Strong Areas (high hit rate)
- **Data races / concurrency**: NSQ-01, NSQ-02, NSQ-45, NSQ-51, NSQ-52 — all detected. The playbook's concurrency focus area works well for Go.
- **Resource leaks / cleanup**: NSQ-13, NSQ-46, NSQ-48 — Close() and cleanup bugs caught.
- **Logic errors**: NSQ-05 (copy-paste), NSQ-07 (counting), NSQ-27 (div-by-zero), NSQ-30 (infinite loop), NSQ-34 (scope), NSQ-35 (break).

### Weak Areas (high miss rate)
- **Protocol-level state machine bugs**: NSQ-14 (REQ timeout), NSQ-17 (messagePump race), NSQ-53 (deadlock) — all missed
- **Configuration/flag handling**: NSQ-19 (deflate level), NSQ-41 (TLS flag), NSQ-56 (parameter parsing) — all missed
- **Platform-specific**: NSQ-20 (32-bit alignment) — missed
- **Cleanup ordering in Exit()**: NSQ-04, NSQ-47 — both missed

### Missed Defect Categories

| Category | Missed | Total in Category | Miss Rate |
|----------|--------|-------------------|-----------|
| Protocol state machine | 3 | 3 | 100% |
| Configuration/flag handling | 3 | 3 | 100% |
| Cleanup ordering in Exit() | 2 | 3 | 67% |
| Channel/queue semantics | 3 | 5 | 60% |
