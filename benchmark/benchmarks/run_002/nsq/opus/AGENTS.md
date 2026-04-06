# AGENTS.md — NSQ

## Project Description

NSQ is a realtime distributed messaging platform written in Go, designed to operate at scale with billions of messages per day. It provides a decentralized topology with no single points of failure and guarantees at-least-once message delivery.

**Key components:**
- **nsqd** — The daemon that receives, queues, and delivers messages to clients
- **nsqlookupd** — Manages topology metadata and serves client discovery requests
- **nsqadmin** — Web UI for real-time cluster administration

## Quick Start

```bash
# Build all binaries
make

# Run tests
go test ./...

# Run tests with race detector
go test -race ./...

# Start nsqlookupd
./build/nsqlookupd

# Start nsqd (connects to lookupd)
./build/nsqd --lookupd-tcp-address=127.0.0.1:4160

# Start nsqadmin (requires Node.js 16.x for static assets)
./build/nsqadmin --lookupd-http-address=127.0.0.1:4161
```

## Build & Test Commands

| Command | Purpose |
|---------|---------|
| `go build ./...` | Build all packages |
| `go test ./...` | Run all tests |
| `go test -race ./...` | Run all tests with race detector |
| `go test -v ./nsqd/` | Run nsqd tests with verbose output |
| `go test -v ./nsqlookupd/` | Run nsqlookupd tests |
| `go vet ./...` | Static analysis |

## Architecture Overview

```
Publisher → [TCP/HTTP] → nsqd → Topic → Channel(s) → Consumer(s)
                           ↕
                       nsqlookupd (discovery)
                           ↕
                       nsqadmin (web UI)
```

### Data Flow
1. Publisher sends message to nsqd via TCP (PUB/MPUB/DPUB) or HTTP
2. nsqd routes message to a Topic
3. Topic's `messagePump()` goroutine distributes message to all Channels
4. Each Channel delivers to one connected Consumer
5. Consumer acknowledges with FIN (finished) or REQ (requeue)

### Key Modules

| Module | Path | Responsibility |
|--------|------|---------------|
| NSQD core | `nsqd/nsqd.go` | Server lifecycle, topic management, metadata persistence |
| Topic | `nsqd/topic.go` | Message distribution to channels via messagePump() |
| Channel | `nsqd/channel.go` | Consumer management, in-flight/deferred message tracking |
| Protocol V2 | `nsqd/protocol_v2.go` | TCP binary protocol, client state machine |
| Client V2 | `nsqd/client_v2.go` | Per-connection state, compression, heartbeats |
| Message | `nsqd/message.go` | Message struct, serialization/deserialization |
| Options | `nsqd/options.go` | Configuration with defaults |
| Lookup | `nsqlookupd/registration_db.go` | Producer registration, tombstoning |
| Internal/test | `internal/test/` | Test assertions (Equal, Nil, NotNil), FakeNetConn |

### Key Design Decisions

1. **Memory-first, disk-backed:** Messages go to in-memory channels (default 10,000 capacity). Overflow goes to disk via `go-diskqueue`. This provides low-latency delivery with durability for overflow.

2. **No ordering guarantees:** NSQ deliberately provides no message ordering. This enables horizontal scaling without coordination overhead.

3. **Atomic state via Go primitives:** Exit flags use `atomic.CompareAndSwapInt32`, counters use `atomic.AddUint64`, options use `atomic.Value`. 64-bit atomic fields must be placed first in structs for 32-bit platform alignment.

4. **Protocol V2 state machine:** Clients progress through states: `stateInit` → `stateConnected` (after IDENTIFY) → `stateSubscribed` (after SUB) → `stateClosing` (after CLS or disconnect). Each command validates the required state.

5. **Ephemeral topics/channels:** Names ending in `#ephemeral` are not persisted to disk and auto-delete when the last consumer disconnects.

6. **Topology-aware consumption (experimental):** When enabled via `experiments` config, messages are preferentially delivered to consumers in the same zone/region as the producer.

### Known Quirks

- **SUB skips stateConnected:** The SUB command transitions directly from `stateInit` to `stateSubscribed`, bypassing `stateConnected`. Clients that SUB without IDENTIFY get default configuration (no heartbeat customization, no compression).
- **isLoading flag:** During startup metadata loading, `isLoading` is set to prevent `PersistMetadata()` from running. Creating topics during this window won't trigger metadata persistence.
- **Message copy in messagePump:** Only the first channel gets the original `*Message`; all others get copies. This means the first channel's message has the original timestamp while copies have new ones.
- **PersistMetadata is not atomic:** The metadata write does not use a temp-file + rename pattern, so a crash mid-write could corrupt `nsqd.dat`.

## Quality Docs

| File | Purpose |
|------|---------|
| `quality/QUALITY.md` | Quality constitution — coverage targets, 10 fitness-to-purpose scenarios |
| `quality/functional_test.go` | Automated functional tests (spec, scenario, and boundary tests) |
| `quality/RUN_CODE_REVIEW.md` | Code review protocol with 8 focus areas and guardrails |
| `quality/RUN_INTEGRATION_TESTS.md` | Integration test protocol — 15 tests covering full message lifecycle |
| `quality/RUN_SPEC_AUDIT.md` | Council of Three multi-model spec audit with 10 scrutiny areas |

### Running Quality Checks

```bash
# Run functional tests (from the nsqd package directory since tests use package-internal access)
# Note: functional_test.go is in the nsqd package and should be placed in the nsqd/ directory to run
cp quality/functional_test.go nsqd/quality_functional_test.go
go test -v -run "TestSpec_|TestScenario|TestBoundary_" ./nsqd/ -timeout 120s
rm nsqd/quality_functional_test.go

# Run a code review
# Read quality/RUN_CODE_REVIEW.md and follow its instructions

# Run integration tests
# Read quality/RUN_INTEGRATION_TESTS.md and follow its instructions

# Start a spec audit (Council of Three)
# Read quality/RUN_SPEC_AUDIT.md and paste the prompt into three AI tools
```

## Dependencies

- Go 1.17+
- `github.com/nsqio/go-diskqueue` v1.1.0 — Persistent message queue storage
- `github.com/nsqio/go-nsq` v1.1.0 — NSQ client library (used in tests)
- `github.com/golang/snappy` v0.0.4 — Snappy compression
- `github.com/BurntSushi/toml` v1.3.2 — TOML config parsing
- `github.com/julienschmidt/httprouter` v1.3.0 — HTTP routing
- Node.js 16.x — Required for nsqadmin static asset building
