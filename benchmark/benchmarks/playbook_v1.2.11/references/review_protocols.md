# Review Protocols (Files 3 and 4)

## File 3: Code Review Protocol (`RUN_CODE_REVIEW.md`)

### Template

```markdown
# Code Review Protocol: [Project Name]

## Bootstrap (Read First)

Before reviewing, read these files for context:
1. `quality/QUALITY.md` — Quality constitution and fitness-to-purpose scenarios
2. [Main architectural doc]
3. [Key design decisions doc]
4. [Any other essential context]

## What to Check

### Focus Area 1: [Subsystem/Risk Area Name]

**Where:** [Specific files and functions]
**What:** [Specific things to look for]
**Why:** [What goes wrong if this is incorrect]

### Focus Area 2: [Subsystem/Risk Area Name]

[Repeat for 4–6 focus areas, mapped to architecture and risk areas from exploration]

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific line, do not include the finding.
- **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name.
- **If unsure whether something is a bug or intentional**, flag it as a QUESTION rather than a BUG.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase. If found in a different file, that's a location defect, not a missing feature.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect or could cause failures.
- **Exhaust the sibling set.** When you find a bug in one method of a type, grep for every other method on that type and check them for the same bug pattern. When you find a boundary condition that breaks one call site, check every other call site that processes the same kind of input. The most common miss pattern: finding a bug once and not checking whether the same bug appears in sibling methods, sibling call sites, or sibling test fixtures.

## Output Format

Save findings to `quality/code_reviews/YYYY-MM-DD-reviewer.md`

For each file reviewed:

### filename.ext
- **Line NNN:** [BUG / QUESTION / INCOMPLETE] Description. Expected vs. actual. Why it matters.

### Summary
- Total findings by severity
- Files with no findings
- Overall assessment: SHIP IT / FIX FIRST / NEEDS DISCUSSION
```

### Phase 2: Regression Tests for Confirmed Bugs

After the code review produces findings, write regression tests that reproduce each BUG finding. This transforms the review from "here are potential bugs" into "here are proven bugs with failing tests."

**Why this matters:** A code review finding without a reproducer is an opinion. A finding with a failing test is a fact. Across multiple codebases (Go, Rust, Python), regression tests written from code review findings have confirmed bugs at a high rate — including data races, cross-tenant data leaks, state machine violations, and silent context loss. The regression tests also serve as the acceptance criteria for fixing the bugs: when the test passes, the bug is fixed.

**How to generate regression tests:**

1. **For each BUG finding**, write a test that:
   - Targets the exact code path and line numbers from the finding
   - Fails on the current implementation, confirming the bug exists
   - Uses mocking/monkeypatching to isolate from external services
   - Includes the finding description in the test docstring for traceability

2. **Name the test file** `quality/test_regression.*` using the project's language:
   - Python: `quality/test_regression.py`
   - Go: `quality/regression_test.go` (or in the relevant package's test directory)
   - Rust: `quality/regression_tests.rs` or a `tests/regression_*.rs` file in the relevant crate
   - Java: `quality/RegressionTest.java`
   - TypeScript: `quality/regression.test.ts`
   - C#: `quality/RegressionTest.cs` or `quality/Regression_YYYYMMDD_Test.cs` (NUnit)
   - Ruby (RSpec): `quality/regression_spec.rb` or `quality/regression_YYYYMMDD_spec.rb` (RSpec)
   - Ruby (Minitest): `quality/test_regression.rb`
   - Kotlin: `quality/RegressionTest.kt` or `quality/Regression_YYYYMMDD_Test.kt` (JUnit 5)
   - PHP: `quality/RegressionTest.php` or `quality/Regression_YYYYMMDD_Test.php` (PHPUnit)
   - Scala: `quality/RegressionSpec.scala` or `quality/Regression_YYYYMMDD_Spec.scala` (ScalaTest)

3. **Each test should document its origin:**
   ```
   # Python example
   def test_webhook_signature_raises_on_malformed_input():
       """[BUG from 2026-03-26-reviewer.md, line 47]
       Webhook signature verification raises instead of returning False
       on malformed signatures, risking 500 instead of clean 401."""

   // Go example
   func TestRestart_DataRace_DirectFieldAccess(t *testing.T) {
       // BUG from 2026-03-26-claude.md, line 3707
       // Restart() writes mutex-protected fields without acquiring the lock
   }
   ```

4. **Run the tests and report results** as a confirmation table:
   ```
   | Finding | Test | Result | Confirmed? |
   |---------|------|--------|------------|
   | Webhook signature raises on malformed input | test_webhook_signature_... | FAILED (expected) | YES — bug confirmed |
   | Queued messages deleted before processing | test_message_queue_... | FAILED (expected) | YES — bug confirmed |
   | Thread active check fails open | test_is_thread_active_... | PASSED (unexpected) | NO — needs investigation |
   ```

5. **If a test passes unexpectedly**, investigate — either the finding was a false positive, or the test doesn't exercise the right code path. Report as NEEDS INVESTIGATION, not as a confirmed bug.

**Language-specific tips:**

- **Go:** Use `go test -race` to confirm data race findings. The race detector is definitive — if it fires, the race is real.
- **Rust:** Use `#[should_panic]` or assert on specific error conditions. For atomicity bugs, assert on cleanup state after injected failures.
- **Python:** Use `monkeypatch` or `unittest.mock.patch` to isolate external dependencies. Use `pytest.raises` for exception-path bugs.
- **Java:** Use Mockito or similar to isolate dependencies. Use `assertThrows` for exception-path bugs.
- **C#:** Use Moq or NSubstitute for mocking. Use `Assert.Throws<T>` for exception-path bugs. For async bugs, use `Assert.ThrowsAsync<T>`.
- **Ruby:** Use RSpec mocks/stubs (`allow`/`expect`) or Minitest mocks. Use `expect { }.to raise_error` for exception-path bugs.
- **Kotlin:** Use MockK for mocking. Similar to Java JUnit patterns but with Kotlin syntax.
- **PHP:** Use PHPUnit mocks or Mockery. Use `$this->expectException()` for exception-path bugs.

**Save the regression test output** alongside the code review: if the review is at `quality/code_reviews/2026-03-26-reviewer.md`, the regression tests go in `quality/test_regression.*` and the confirmation results go in the review file as an addendum or in `quality/results/`.

### Why These Guardrails Matter

These four guardrails often improve AI code review quality by reducing vague and hallucinated findings:

1. **Line numbers** force the model to actually locate the issue, not just describe a general concern
2. **Reading bodies** prevents the common failure of assuming a function works based on its name
3. **QUESTION vs BUG** reduces false positives that waste human time
4. **Grep before claiming missing** prevents the most common AI review hallucination: claiming something doesn't exist when it's in a different file

The "no style changes" rule keeps reviews focused on correctness. Style suggestions dilute the signal and waste review time.

---

## File 4: Integration Test Protocol (`RUN_INTEGRATION_TESTS.md`)

Integration tests exercise the full system end-to-end against real dependencies. A protocol that only tests local validation and config parsing is a unit test suite in disguise — it will miss the bugs that actually matter in production: connection failures, serialization mismatches, timeout behavior, incorrect output under real data, and resource cleanup failures.

The key to a great integration test protocol is understanding what makes *this project* work end-to-end, then designing tests that exercise exactly that. The general principles below apply to every project; the worked examples show how to instantiate them for different domains.

### General Principles

These five principles made integration test protocols effective across diverse projects. Every generated protocol should address all five, adapted to the project's domain.

**1. Combinatorial Test Matrix.** Identify the project's independent axes of variation and test across their combinations. Ask: "What are the dimensions that, if I only tested one value of each, I'd miss real bugs?"

**2. Pre-Flight Dependency Checks.** Before burning test time, verify every external dependency is reachable and correctly configured. This includes services, credentials, data fixtures, and environment prerequisites. If anything is missing, stop and tell the user — don't skip tests silently.

**3. Parallelism Grouping.** Structure independent tests for concurrent execution. Identify which tests share resources (and must run sequentially) vs. which are independent (and can run in parallel). Script the parallelism with actual commands — don't just describe it.

**4. Domain-Specific Quality Gates.** Generic pass/fail criteria ("output exists") miss domain-specific correctness issues. Derive quality gates from the code itself: read validation rules, schema constraints, and generation logic during exploration, then turn them into specific assertions with expected values.

**5. Multi-Level Post-Run Verification.** A run that completes without errors may still be wrong. Verify at every level: process exited cleanly, state is terminal, output data exists and parses, content has correct field values, domain-specific quality checks pass.

### Integration Test Design UX: Present the Plan First

**This is critical for a good user experience.** Before writing the full protocol, present an overview of how the integration tests would work and give the user a chance to adjust.

When generating the integration test protocol, follow this sequence:

**Step 1: Present the integration test plan.**

After exploration, before writing the protocol file, show the user:

```
## Integration Test Plan for [Project Name]

Based on my exploration, here's how I'd structure the integration tests:

**Project type:** [e.g., REST API service, message queue consumer, data pipeline, CLI tool]
**External dependencies:** [list what the tests will exercise]
**Test axes:** [the combinatorial dimensions]

| # | Test Group | What It Exercises | Dependencies | Est. Duration |
|---|-----------|-------------------|--------------|---------------|
| 1 | [group] | [description] | [services needed] | ~Xm |
| 2 | [group] | [description] | [services needed] | ~Xm |
| ... | | | | |

**Setup required:** [what needs to be running/available]
**Teardown:** [how tests clean up after themselves]
**Total estimated time:** ~Xm

Does this look right? Would you like to adjust the test groups,
add/remove dependencies, or change the scope?
```

**Step 2: Incorporate feedback.** If the user says "we don't need to test against the staging database" or "add a test for the webhook endpoint," adjust before writing the protocol.

**Step 3: Generate the full protocol file.** Only after the user confirms the plan.

This prevents the common failure mode where the agent generates a complete 200-line protocol that tests the wrong things, then has to rewrite it. Showing the plan first costs one extra exchange and saves significant rework.

### Template

```markdown
# Integration Test Protocol: [Project Name]

## Working Directory

All commands in this protocol use **relative paths from the project root.** Run everything from the directory containing this file's parent (the project root). Do not `cd` to an absolute path or a parent directory — if a command starts with `cd /some/absolute/path`, it's wrong. Use `./scripts/`, `./pipelines/`, `./quality/`, etc.

## Safety Constraints

[If this protocol runs with elevated permissions:]
- DO NOT modify source code
- DO NOT delete files
- ONLY create files in the test results directory
- If something fails, record it and move on — DO NOT fix it

## Pre-Flight Check

Before running integration tests, verify:
- [ ] [Dependencies installed — specific command]
- [ ] [External services reachable — specific checks]
- [ ] [Test fixtures / seed data exist — specific paths]
- [ ] [Clean state — specific cleanup if needed]

If any check fails, STOP and report what's missing. Do not skip
tests silently when dependencies are unavailable.

## Test Matrix

| # | Test | What It Exercises | Method | Pass Criteria |
|---|------|-------------------|--------|---------------|
| 1 | [Happy path] | [End-to-end primary flow] | [Command] | [Specific expected result] |
| 2 | [Variant A] | [Alternative path/config] | [Command] | [Expected result] |
| 3 | [Boundary] | [Edge case or failure mode] | [Command] | [Expected behavior] |
| 4 | [Cross-component] | [Module A output → Module B input] | [Command] | [Expected result] |

## Setup and Teardown

### Setup
[Commands to provision test infrastructure — start services, create
test databases, seed data, etc.]

### Teardown
[Commands to stop services, drop test databases, remove temp files.
Teardown must run even if tests fail.]

## Execution

### Parallelism Groups

[Group independent tests for concurrent execution. Script it:]

```bash
# Group 1 (parallel — no shared resources)
./run_test_a.sh &
./run_test_b.sh &
wait

# Group 2 (sequential — shares database)
./run_test_c.sh
./run_test_d.sh
```

**Note:** These commands assume POSIX-compatible shell (bash, sh,
zsh). For Windows without WSL, document PowerShell equivalents or
note that a POSIX environment is required.

## Quality Gates

[Domain-specific assertions derived from the code — not generic
"output exists" checks. Reference the Field Reference Table.]

## Post-Run Verification

For each test run, verify at these levels:
1. **Process:** Clean exit, no crashes, log file exists
2. **State:** Run reached terminal state (not stuck in progress)
3. **Data:** Output files exist and parse correctly
4. **Content:** Sample records have expected fields with valid values
5. **Domain:** Project-specific quality checks pass

## Execution UX (How to Present When Running This Protocol)

When an AI agent runs this protocol, communicate in three phases:

### Phase 1: The Plan
Before running anything, show what's about to happen:

| # | Test | What It Checks | Est. Time |
|---|------|---------------|-----------|
| 1 | [Test name] | [One-line description] | ~30s |
| 2 | [Test name] | [One-line description] | ~2m |

**Total:** N tests, estimated M minutes

This gives the user a chance to say "skip test 4" or "don't run
the live API tests" before anything starts.

### Phase 2: Progress
One-line status updates as each test runs:
✓ Test 1: [name] — PASS (0.3s)
✗ Test 2: [name] — FAIL: [one-line error]
⧗ Test 3: [name]... running

### Phase 3: Results
Summary table with recommendation:

| # | Test | Result | Time | Notes |
|---|------|--------|------|-------|
| 1 | ... | ✓ PASS | 0.3s | |
| 2 | ... | ✗ FAIL | 45s | [brief reason] |

**Passed:** N/M | **Failed:** K/M
**Recommendation:** SHIP IT / FIX FIRST / NEEDS INVESTIGATION

## Reporting

Save to `quality/results/YYYY-MM-DD-integration.md`
```

### Adaptation Prompts: "What Does This Look Like for Your Project?"

During exploration, answer these questions to adapt the general principles to the specific project. The answers drive the test matrix design.

**Identifying the test axes:**
- What are the project's external dependencies? (APIs, databases, message queues, file systems, hardware)
- Does the project have multiple execution modes? (batch/realtime, sync/async, different backends)
- Does the project support multiple configurations that change behavior? (providers, formats, protocols)
- What are the independent dimensions? (Each unique combination of axis values is a potential test.)

**Identifying setup/teardown needs:**
- Can dependencies be provisioned locally? (Docker containers, embedded databases, mock servers)
- What state needs to exist before tests run? (seed data, config files, running services)
- What cleanup is required after tests? (stop containers, drop databases, remove temp files)
- Does teardown need to run even on test failure? (Almost always yes.)

**Identifying quality gates:**
- What does "correct output" look like beyond "no errors"? Read validation rules, schema constraints, business logic.
- Are there distribution requirements? (e.g., "all category values should appear," "response times under 500ms")
- Are there existing verification scripts or quality check functions? (Use them directly.)

**Identifying parallelism constraints:**
- Which tests share external resources? (Same database, same API rate limit, same port)
- Which tests are fully independent? (Different services, different data, no shared state)
- What's the rate limit situation? (API quotas, connection pool limits, service throttling)

### Worked Example 1: REST API Service

**Project:** A REST API with authentication, CRUD endpoints, and webhook notifications.

**Test axes:** endpoint group × auth state × payload variant

**Pre-flight:**
```bash
# Start the API server
./scripts/start_test_server.sh --port 9090 --config test.env
# Wait for health check
curl --retry 5 --retry-delay 2 http://localhost:9090/health
# Verify test database is clean
./scripts/reset_test_db.sh
```

**Test matrix:**

| # | Test | What It Exercises | Pass Criteria |
|---|------|-------------------|---------------|
| 1 | Create resource (valid) | POST /api/resources with valid payload | 201, response body matches schema, resource retrievable via GET |
| 2 | Create resource (invalid) | POST /api/resources with missing required field | 400, error message specifies missing field |
| 3 | Auth flow | POST /auth/login → use token → GET /api/protected | 200 with token, 200 with valid data, 401 without token |
| 4 | Webhook delivery | Create resource → verify webhook POST received | Webhook endpoint received POST within 5s, payload matches event schema |
| 5 | Pagination | GET /api/resources?page=1&limit=10 with 25 seed records | Returns 10 items, `total` = 25, `next` link valid |
| 6 | Concurrent writes | 10 parallel POST requests | All succeed or fail gracefully, no data corruption, final count correct |

**Field Reference Table:**

| Field | Type | Constraints |
|-------|------|-------------|
| `status` | integer | 200 for success, 4xx/5xx for errors |
| `body.id` | string (UUID) | Non-null for created resources |
| `body.name` | string | Matches request input |
| `headers.content-type` | string | Must be `application/json` |
| `error.message` | string | Present only on error responses |

**Quality gates:**
- Every 2xx response body validates against the endpoint's JSON Schema
- Error responses include `error.code` and `error.message` fields
- Webhook payloads contain `event_type`, `resource_id`, and `timestamp`
- Response time for all endpoints < 500ms under single-client load

**Teardown:**
```bash
./scripts/stop_test_server.sh
./scripts/reset_test_db.sh
```

### Worked Example 2: Message Queue / Streaming Pipeline

**Project:** A Kafka-based event processor that consumes events, transforms them, and writes results to a database.

**Test axes:** event type × serialization format × consumer group configuration

**Pre-flight:**
```bash
# Start local Kafka (e.g., via Docker)
docker compose -f docker-compose.test.yml up -d kafka zookeeper
# Wait for Kafka to be ready
./scripts/wait_for_kafka.sh --timeout 30
# Create test topics
kafka-topics.sh --create --topic test-events --partitions 3 \
  --bootstrap-server localhost:9092
kafka-topics.sh --create --topic test-results --partitions 3 \
  --bootstrap-server localhost:9092
# Start the processor
./scripts/start_processor.sh --config test.env &
PROCESSOR_PID=$!
sleep 5  # Allow consumer group to stabilize
```

**Test matrix:**

| # | Test | What It Exercises | Pass Criteria |
|---|------|-------------------|---------------|
| 1 | Single event, happy path | Publish 1 event → consume → verify DB write | Result row exists, fields match transformation rules |
| 2 | Batch throughput | Publish 100 events rapidly | All 100 processed within 30s, no duplicates in DB |
| 3 | Poison pill handling | Publish 1 malformed event between 2 valid ones | Malformed event sent to DLQ, valid events processed normally |
| 4 | Consumer restart | Kill processor mid-batch, restart | Resumes from last committed offset, no duplicate processing |
| 5 | Schema evolution | Publish event with new optional field | Processor handles gracefully, field stored or ignored per config |

**Field Reference Table:**

| Field | Type | Constraints |
|-------|------|-------------|
| `event_id` | string (UUID) | Unique per event |
| `payload` | object | Matches published schema |
| `status` | string | One of: pending, processing, completed, failed |
| `retry_count` | integer | 0 ≤ value ≤ max_retries |

**Quality gates:**
- DB row count matches published event count (minus DLQ entries)
- DLQ contains exactly the malformed events, with error reason attached
- No duplicate `event_id` values in the results table
- Consumer lag returns to 0 within 60s after each batch

**Teardown:**
```bash
kill $PROCESSOR_PID 2>/dev/null
kafka-topics.sh --delete --topic test-events --bootstrap-server localhost:9092
kafka-topics.sh --delete --topic test-results --bootstrap-server localhost:9092
docker compose -f docker-compose.test.yml down -v
```

### Worked Example 3: Database-Backed Application

**Project:** A Python application with PostgreSQL, running migrations, complex queries, and transaction logic.

**Test axes:** migration version × data volume × transaction scenario

**Pre-flight:**
```bash
# Start test database
docker run -d --name test-pg -p 5433:5432 \
  -e POSTGRES_DB=testdb -e POSTGRES_PASSWORD=test postgres:16
# Wait for readiness
until pg_isready -h localhost -p 5433; do sleep 1; done
# Run migrations
DATABASE_URL=postgresql://postgres:test@localhost:5433/testdb \
  ./scripts/migrate.sh --target latest
# Seed test data
./scripts/seed_test_data.sh --profile integration --count 500
```

**Test matrix:**

| # | Test | What It Exercises | Pass Criteria |
|---|------|-------------------|---------------|
| 1 | Migration roundtrip | Migrate up to latest, then down to base, then up again | No errors, schema matches expected state after each direction |
| 2 | Complex query correctness | Run the reporting query against 500 seeded records | Results match independently calculated expected values |
| 3 | Transaction rollback | Trigger error mid-transaction | No partial writes, all-or-nothing behavior confirmed |
| 4 | Concurrent updates | 10 parallel updates to same record | Final state consistent, no lost updates, version/lock mechanism works |
| 5 | Connection pool exhaustion | Run N+1 concurrent connections (N = pool size) | Graceful queuing or clear error, no silent failures |
| 6 | Large result set | Query returning 10,000+ rows | Completes within timeout, memory usage stays bounded, pagination works |

**Field Reference Table:**

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | integer/UUID | Auto-generated, unique |
| `created_at` | timestamp | Set on insert, immutable |
| `updated_at` | timestamp | Updated on every write |
| `version` | integer | Incremented on update (optimistic locking) |

**Quality gates:**
- Zero orphaned records after transaction rollback tests
- Query results match expected aggregates (sum, count, avg) within floating-point tolerance
- Connection pool returns to baseline size after exhaustion test
- No `IDLE IN TRANSACTION` sessions left after any test

**Teardown:**
```bash
docker stop test-pg && docker rm test-pg
```

### Worked Example 4: CLI Tool / Data Pipeline

**Project:** A command-line tool that reads input files, transforms data through multiple stages, and produces output files.

**Test axes:** input format × pipeline stage × data volume × error condition

**Pre-flight:**
```bash
# Verify the tool is built
./build.sh && ./mytool --version
# Prepare test fixtures
cp -r ./test_fixtures/integration/ /tmp/integration-test/
# Verify fixture integrity
sha256sum -c ./test_fixtures/integration/checksums.sha256
```

**Test matrix:**

| # | Test | What It Exercises | Pass Criteria |
|---|------|-------------------|---------------|
| 1 | Happy path, small input | 10-record CSV → full pipeline → output JSON | Output has 10 records, all fields populated, values match transform rules |
| 2 | Happy path, large input | 10,000-record CSV → full pipeline | Completes within 60s, output record count matches input, no truncation |
| 3 | Malformed input row | CSV with 1 bad row among 100 good | 100 output records (bad row skipped or in error log), clear error message |
| 4 | Multiple input formats | Same data as CSV, TSV, and JSON → pipeline | All three produce identical output |
| 5 | Pipeline interruption | Kill process mid-run, restart | Resumes from checkpoint or restarts cleanly, no corrupted output |
| 6 | Empty input | Zero-record file → pipeline | Clean exit with code 0, empty output file (not crash or hang) |

**Field Reference Table:**

| Field | Type | Constraints |
|-------|------|-------------|
| `exit_code` | integer | 0 for success, non-zero for error |
| `stdout` | string | Contains expected output format |
| `stderr` | string | Empty on success, error message on failure |
| `output_file` | file path | Exists after successful run |

**Quality gates:**
- Output file is valid JSON/CSV (parseable, no truncation, proper closing brackets)
- Record count: `output_count == input_count - error_count`
- Transform correctness: spot-check 3 records against manually calculated expected values
- Exit code: 0 for success, non-zero for handled errors, never silent failure
- Stderr: errors go to stderr (not swallowed), normal output goes to stdout

**Teardown:**
```bash
rm -rf /tmp/integration-test/
```

### Adapting to Your Project

Most real projects are hybrids. A web application might have a REST API (Example 1), a background job processor consuming from a queue (Example 2), a PostgreSQL database (Example 3), and a CLI tool for data import (Example 4). In that case, the integration test protocol combines elements from multiple examples:

- The pre-flight starts all services (database, queue, API server)
- The test matrix has groups for each subsystem
- Parallelism groups respect shared dependencies (API tests and queue tests can run in parallel if they use separate databases, but must be sequential if they share one)
- Teardown stops everything in reverse order

The four worked examples cover the most common integration archetypes. Projects outside these patterns (real-time collaboration, ML training pipelines, game engines, embedded systems, desktop GUI applications) should still follow the five general principles above — the adaptation prompts will guide you to the right test matrix even without a matching worked example. Start from whichever example is closest, then modify based on what the adaptation prompts reveal about the project's actual dependencies and failure modes.

The worked examples above are starting points. The agent should adapt them based on what it finds during exploration — the actual services, the actual schemas, the actual failure modes. The goal is that running this protocol exercises the full system under real-world conditions, catching issues that local-only testing would miss.

### Deriving Quality Gates from Code

Generic pass/fail criteria ("all units validated") miss domain-specific correctness issues. Derive project-specific quality checks from the code itself:

1. **Read validation rules.** If the project validates output (schema validators, assertion functions, business rule checks), those rules define what "correct" looks like. Turn them into quality gates: "field X must satisfy condition Y for all output records."

2. **Read schema constraints.** If schemas define enums, ranges, or patterns, the quality gate verifies output stays within those constraints and that the distribution is non-degenerate (not 100% one value when multiple are valid).

3. **Read generation/transform logic.** Understand what the pipeline produces. If there are 3 event types, the quality gate is: "all 3 types must appear in output with sufficient sample size." If a transform multiplies a value by 1.1, verify the output values.

4. **Read existing quality checks.** Search for scripts or functions that already verify output quality (e.g., `integration_checks.py`, validation scripts). Reference or call them directly from the protocol.

For each major subsystem or pipeline, the integration protocol should have a dedicated "Quality Gates" section listing 2–4 specific checks with expected values derived from the exploration above. Every check must reference a specific field and acceptable value range — not generic "output exists."

### The Field Reference Table (Required Before Writing Quality Gates)

**Why this exists:** AI models confidently write wrong field names even when they've read the schemas. This happens because the model reads the schema during exploration, then writes the protocol hours (or thousands of tokens) later from memory. Memory drifts: `document_id` becomes `doc_id`, `sentiment_score` becomes `sentiment`, `float 0-1` becomes `int 0-100`. The protocol looks authoritative but the field names are hallucinated. When someone runs the quality gates against real data, they fail — and the user loses trust in the entire generated playbook.

**The fix is procedural, not instructional.** Don't just tell yourself to "cross-check later" — build the reference table FIRST, then write quality gates by copying from it.

Before writing any quality gate that references output field names, build a **Field Reference Table** by re-reading each schema file:

```
## Field Reference Table (built from schemas, not memory)

### Subsystem: UserService
Schema: src/schemas/user.json
| Field | Type | Constraints |
|-------|------|-------------|
| user_id | string | UUID format |
| email | string | RFC 5322 |
| role | string | enum: ["admin", "member", "viewer"] |

### Subsystem: OrderPipeline
Schema: src/schemas/order_output.json
| Field | Type | Constraints |
|-------|------|-------------|
| order_id | string | — |
| total_amount | number | min: 0 |
| status | string | enum: ["pending", "confirmed", "shipped"] |
...
```

**The process:**
1. **Re-read each schema file IMMEDIATELY before writing each table row.** Do not write any row from memory. The file read and the table row must be adjacent — read the file, write the row, read the next file, write the next row. If you read all schemas earlier in the conversation, that doesn't count — you must read them AGAIN here because your memory of field names drifts over thousands of tokens.
2. **Copy field names character-for-character from the file contents.** Do not retype them. `document_id` is not `doc_id`. `sentiment_score` is not `sentiment`. `classification` is not `category`. Even small differences break quality gates.
3. **Include ALL fields from the schema, not just the ones you think are important.** If the schema has 8 required fields, the table has 8 rows. If you wrote fewer rows than the schema has fields, you skipped fields.
4. Write quality gates by copying field names from the completed table.
5. After writing, count fields: if the quality gates mention a field that isn't in the table, you hallucinated it. Remove it.

This table is an intermediate artifact — include it in the protocol itself (as a reference section) so future protocol users can verify field accuracy.

### Calibrating Scale

The number of records/iterations per integration test matters:

- **Too few (1–3):** Fast and cheap, but misses concurrency bugs, distribution checks fail, and pipeline logic untested at realistic scale.
- **Too many (1,000+):** Expensive and slow for a test protocol. Appropriate for load testing but not for integration verification.
- **Right range:** Enough to exercise the system meaningfully. Guidelines:
  - If the project has batching logic, use a count that spans at least 2 batches
  - If the project has distribution checks, use at least 5–10× the number of categories
  - If the project has fan-out/expansion, use enough input to produce a non-trivial output set
  - For database tests, seed enough data that queries exercise indexes (not just sequential scans)

When in doubt, 10–100 records is usually the right range — enough to catch real issues without excessive cost.

### Post-Run Verification Depth

A run that completes without errors may still be wrong. For each integration test run, verify at multiple levels:

1. **Process-level:** Did the process exit cleanly? Check log files for completion messages, not just exit codes.
2. **State-level:** Is the system in the expected state? Check databases, queues, file systems for expected artifacts.
3. **Data-level:** Does output data exist and parse correctly? Read actual output files or query result tables.
4. **Content-level:** Do output records have the expected fields populated with reasonable values? Spot-check 2–3 records.
5. **Quality-level:** Do the domain-specific quality gates pass? Run any existing quality check scripts.
6. **Resource-level:** Are resources cleaned up? No zombie processes, no leaked connections, no orphaned containers.

Include all applicable levels in the generated protocol's post-run checklist. The common failure is stopping at level 1 (process completed) without checking levels 3–5.
