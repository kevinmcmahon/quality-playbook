# Integration Test Protocol: NSQ

## Working Directory

All commands in this protocol use **relative paths from the project root.** Run everything from the directory containing `go.mod`. Do not `cd` to an absolute path.

## Safety Constraints

- DO NOT modify source code
- DO NOT delete data files outside of test directories
- ONLY create files in `./quality/results/`
- If something fails, record it and move on — DO NOT fix it

## Pre-Flight Check

Before running integration tests, verify:

- [ ] Go 1.17+ installed: `go version`
- [ ] NSQ builds cleanly: `go build ./...`
- [ ] Existing tests pass: `go test ./... -count=1 -timeout 120s`
- [ ] Ports 4150 (TCP), 4151 (HTTP), 4160 (lookupd TCP), 4161 (lookupd HTTP) are available: `lsof -i :4150,:4151,:4160,:4161`
- [ ] Temporary data directory writable: `mkdir -p /tmp/nsq-integration-test && touch /tmp/nsq-integration-test/.probe && rm /tmp/nsq-integration-test/.probe`

If any check fails, STOP and report what's missing. Do not skip tests silently.

## Test Matrix

| # | Test | What It Exercises | Method | Pass Criteria |
|---|------|-------------------|--------|---------------|
| 1 | Single message publish + consume | Full PUB → SUB → FIN lifecycle | TCP protocol | Consumer receives message with matching body and valid ID |
| 2 | Multi-publish batch | MPUB with 100 messages | TCP protocol | All 100 messages delivered to subscriber, `message_count` = 100 |
| 3 | Deferred publish | DPUB with 500ms delay | TCP protocol | Message delivered after 500ms ± 200ms, not before |
| 4 | Disk overflow | Publish 200 msgs with MemQueueSize=10 | TCP protocol + disk | All 200 messages delivered, `backend_depth` shows disk usage |
| 5 | Topic fan-out | Publish to topic with 3 channels | TCP + HTTP API | Each channel receives all messages independently |
| 6 | Consumer requeue | REQ with 200ms timeout | TCP protocol | Message redelivered after timeout, `Attempts` incremented |
| 7 | Message timeout | Let in-flight message expire | TCP protocol | Message redelivered after `MsgTimeout`, `timeout_count` incremented |
| 8 | Pause/unpause topic | HTTP API pause + unpause | HTTP API | Messages stop flowing when paused, resume within 1s of unpause |
| 9 | nsqlookupd registration | nsqd → lookupd registration | TCP + HTTP API | Topic appears in lookupd `/topics` and `/lookup?topic=X` within 5s |
| 10 | Graceful shutdown | Publish msgs, shutdown nsqd, restart | Process lifecycle | Metadata restored, all non-in-flight messages recoverable |
| 11 | Ephemeral channel lifecycle | Create #ephemeral channel, subscribe, disconnect | TCP protocol | Channel deleted after last consumer disconnects |
| 12 | Channel empty | Publish 50 msgs, empty channel via HTTP | HTTP API | Channel depth = 0, messages not recoverable |
| 13 | Compression (Snappy) | IDENTIFY with snappy=true, PUB, SUB | TCP protocol | Messages delivered correctly through Snappy compression |
| 14 | Max consumers limit | Set MaxChannelConsumers=2, connect 3 | TCP protocol | Third connection rejected with error, first two continue working |
| 15 | Stats endpoint | Publish messages, query /stats | HTTP API | Stats JSON contains correct topic/channel counts and message metrics |

## Field Reference Table

### nsqd HTTP API `/stats` Response

| Field | Type | Constraints |
|-------|------|-------------|
| `version` | string | Matches nsqd version |
| `health` | string | `"OK"` when healthy |
| `start_time` | integer | Unix timestamp > 0 |
| `topics` | array | Array of topic objects |
| `topics[].topic_name` | string | Non-empty string |
| `topics[].depth` | integer | >= 0 |
| `topics[].backend_depth` | integer | >= 0 |
| `topics[].message_count` | integer | >= 0 |
| `topics[].message_bytes` | integer | >= 0 |
| `topics[].paused` | boolean | true/false |
| `topics[].e2e_processing_latency` | object | Latency percentiles |
| `topics[].channels` | array | Array of channel objects |
| `topics[].channels[].channel_name` | string | Non-empty string |
| `topics[].channels[].depth` | integer | >= 0 |
| `topics[].channels[].backend_depth` | integer | >= 0 |
| `topics[].channels[].in_flight_count` | integer | >= 0 |
| `topics[].channels[].deferred_count` | integer | >= 0 |
| `topics[].channels[].message_count` | integer | >= 0 |
| `topics[].channels[].requeue_count` | integer | >= 0 |
| `topics[].channels[].timeout_count` | integer | >= 0 |
| `topics[].channels[].client_count` | integer | >= 0 |
| `topics[].channels[].paused` | boolean | true/false |
| `topics[].channels[].clients` | array | Array of client objects |

### nsqlookupd HTTP API `/lookup` Response

| Field | Type | Constraints |
|-------|------|-------------|
| `channels` | array | Array of channel name strings |
| `producers` | array | Array of producer objects |
| `producers[].remote_address` | string | IP:port format |
| `producers[].hostname` | string | Non-empty |
| `producers[].broadcast_address` | string | Non-empty |
| `producers[].tcp_port` | integer | > 0 |
| `producers[].http_port` | integer | > 0 |
| `producers[].version` | string | Semver format |

### Metadata File (`nsqd.dat`) Format

| Field | Type | Constraints |
|-------|------|-------------|
| `version` | string | Non-empty |
| `topics` | array | Array of topic metadata |
| `topics[].name` | string | Non-empty, valid topic name |
| `topics[].paused` | boolean | true/false |
| `topics[].channels` | array | Array of channel metadata |
| `topics[].channels[].name` | string | Non-empty, valid channel name |
| `topics[].channels[].paused` | boolean | true/false |

## Setup

```bash
# Build nsqd and nsqlookupd
go build -o /tmp/nsq-integration-test/nsqd ./apps/nsqd
go build -o /tmp/nsq-integration-test/nsqlookupd ./apps/nsqlookupd

# Start nsqlookupd
/tmp/nsq-integration-test/nsqlookupd \
  --tcp-address 127.0.0.1:4160 \
  --http-address 127.0.0.1:4161 \
  > /tmp/nsq-integration-test/lookupd.log 2>&1 &
LOOKUPD_PID=$!
sleep 1

# Verify lookupd is running
curl -s http://127.0.0.1:4161/ping | grep -q "OK" || { echo "lookupd failed to start"; kill $LOOKUPD_PID; exit 1; }

# Start nsqd with integration test config
/tmp/nsq-integration-test/nsqd \
  --tcp-address 127.0.0.1:4150 \
  --http-address 127.0.0.1:4151 \
  --lookupd-tcp-address 127.0.0.1:4160 \
  --data-path /tmp/nsq-integration-test/data \
  --mem-queue-size 10 \
  --msg-timeout 2s \
  > /tmp/nsq-integration-test/nsqd.log 2>&1 &
NSQD_PID=$!
sleep 2

# Verify nsqd is running
curl -s http://127.0.0.1:4151/ping | grep -q "OK" || { echo "nsqd failed to start"; kill $NSQD_PID $LOOKUPD_PID; exit 1; }
```

## Teardown

```bash
# Stop nsqd and nsqlookupd
kill $NSQD_PID 2>/dev/null
kill $LOOKUPD_PID 2>/dev/null
wait $NSQD_PID 2>/dev/null
wait $LOOKUPD_PID 2>/dev/null

# Clean up data
rm -rf /tmp/nsq-integration-test/
```

**Teardown must run even if tests fail.** Use `trap` in a wrapper script:
```bash
trap 'kill $NSQD_PID $LOOKUPD_PID 2>/dev/null; rm -rf /tmp/nsq-integration-test/' EXIT
```

## Execution

### Parallelism Groups

```bash
# Group 1 (parallel — independent message operations)
# Tests 1, 2, 3 can run in parallel on different topics
./quality/scripts/test_single_pub.sh &
./quality/scripts/test_multi_pub.sh &
./quality/scripts/test_deferred_pub.sh &
wait

# Group 2 (sequential — requires specific nsqd config)
# Tests 4, 8, 10, 14 require specific configurations
./quality/scripts/test_disk_overflow.sh
./quality/scripts/test_pause_unpause.sh
./quality/scripts/test_graceful_shutdown.sh
./quality/scripts/test_max_consumers.sh

# Group 3 (parallel — lookupd interactions)
./quality/scripts/test_lookupd_registration.sh &
./quality/scripts/test_stats_endpoint.sh &
wait

# Group 4 (sequential — channel lifecycle)
./quality/scripts/test_topic_fanout.sh
./quality/scripts/test_consumer_requeue.sh
./quality/scripts/test_msg_timeout.sh
./quality/scripts/test_ephemeral_channel.sh
./quality/scripts/test_channel_empty.sh
./quality/scripts/test_snappy_compression.sh
```

**Note:** Commands assume POSIX-compatible shell. For Windows without WSL, use `go test` directly instead of shell scripts.

## Quality Gates

1. **Message delivery completeness:** Every published message must be consumed exactly once per channel. `published_count == consumed_count` per channel.
2. **Message body integrity:** Consumed message body must match published body byte-for-byte.
3. **Timeout accuracy:** Deferred/requeued messages must be delivered within ±200ms of their scheduled time.
4. **Stats consistency:** `message_count` in `/stats` must equal the number of published messages. `depth + in_flight_count + finished_count == message_count`.
5. **Metadata durability:** After graceful shutdown and restart, all non-ephemeral topics and channels must be present in metadata.
6. **Ephemeral cleanup:** Ephemeral channels must not appear in metadata and must be deleted when the last consumer disconnects.
7. **Lookupd accuracy:** Topics registered in nsqlookupd must match topics on the nsqd instance within `lookupd-poll-interval` (default 60s, use shorter for tests).
8. **Resource cleanup:** After teardown, no nsqd or nsqlookupd processes remain. No files in the data path (except intentionally preserved ones).

## Post-Run Verification

For each test run, verify at these levels:

1. **Process:** nsqd and nsqlookupd exit cleanly (exit code 0), log files contain no FATAL or ERROR entries
2. **State:** All topics/channels reach expected state (paused, deleted, or active as specified)
3. **Data:** Messages delivered match messages published (count and content)
4. **Content:** Spot-check 3 messages from each test: verify ID format (16 bytes hex), body content, timestamp > 0, attempts >= 1
5. **Domain:** Stats endpoint values are internally consistent (see quality gates above)
6. **Resource:** No zombie processes, no leaked temp files, data directory cleaned

## Execution UX (How to Present When Running This Protocol)

### Phase 1: The Plan

Before running anything, show:

| # | Test | What It Checks | Est. Time |
|---|------|---------------|-----------|
| 1 | Single publish + consume | Basic PUB/SUB/FIN lifecycle | ~5s |
| 2 | Multi-publish batch | MPUB with 100 messages | ~5s |
| 3 | Deferred publish | DPUB timing accuracy | ~3s |
| 4 | Disk overflow | Backend queue fallback | ~10s |
| 5 | Topic fan-out | Multi-channel distribution | ~5s |
| 6 | Consumer requeue | REQ message redelivery | ~3s |
| 7 | Message timeout | In-flight timeout handling | ~5s |
| 8 | Pause/unpause | Topic pause behavior | ~5s |
| 9 | Lookupd registration | Discovery service integration | ~10s |
| 10 | Graceful shutdown | Metadata persistence across restart | ~15s |
| 11 | Ephemeral channel | Auto-deletion on disconnect | ~5s |
| 12 | Channel empty | Queue drain via HTTP API | ~3s |
| 13 | Snappy compression | Compressed message delivery | ~5s |
| 14 | Max consumers | Connection limit enforcement | ~3s |
| 15 | Stats endpoint | HTTP stats correctness | ~3s |

**Total:** 15 tests, estimated ~90 seconds

### Phase 2: Progress

```
✓ Test 1: Single publish + consume — PASS (2.1s)
✓ Test 2: Multi-publish batch — PASS (3.4s)
✓ Test 3: Deferred publish — PASS (1.8s)
⧗ Test 4: Disk overflow... running
```

### Phase 3: Results

| # | Test | Result | Time | Notes |
|---|------|--------|------|-------|
| 1 | Single publish | ✓ PASS | 2.1s | |
| 2 | Multi-publish | ✓ PASS | 3.4s | |
| ... | ... | ... | ... | ... |

**Passed:** N/15 | **Failed:** K/15
**Recommendation:** SHIP IT / FIX FIRST / NEEDS INVESTIGATION

## Reporting

Save to `quality/results/YYYY-MM-DD-integration.md`
