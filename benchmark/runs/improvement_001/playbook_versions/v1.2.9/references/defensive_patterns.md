# Finding Defensive Patterns (Step 5)

Defensive code patterns are evidence of past failures or known risks. Every null guard, try/catch, normalization function, and sentinel check exists because something went wrong — or because someone anticipated it would. Your job is to find these patterns systematically and convert them into fitness-to-purpose scenarios and boundary tests.

## Systematic Search

Don't skim — grep the codebase methodically. The exact patterns depend on the project's language. Here are common defensive-code indicators grouped by what they protect against:

**Null/nil guards:**

| Language | Grep pattern |
|---|---|
| Python | `None`, `is None`, `is not None` |
| Java | `null`, `Optional`, `Objects.requireNonNull` |
| Scala | `Option`, `None`, `.getOrElse`, `.isEmpty` |
| TypeScript | `undefined`, `null`, `??`, `?.` |
| Go | `== nil`, `!= nil`, `if err != nil` |
| Rust | `Option`, `unwrap`, `.is_none()`, `?` |
| C# | `null`, `?.`, `??`, `ArgumentNullException`, `NullReferenceException` |
| Ruby | `nil`, `nil?`, `&.`, `||`, `defined?` |
| Kotlin | `null`, `?.`, `!!`, `?:`, `requireNotNull`, `checkNotNull` |
| PHP | `null`, `is_null()`, `isset()`, `empty()`, `??`, `?->` |

**Exception/error handling:**

| Language | Grep pattern |
|---|---|
| Python | `except`, `try:`, `raise` |
| Java | `catch`, `throws`, `try {` |
| Scala | `Try`, `catch`, `recover`, `Failure` |
| TypeScript | `catch`, `throw`, `.catch(` |
| Go | `if err != nil`, `errors.New`, `fmt.Errorf` |
| Rust | `Result`, `Err(`, `unwrap_or`, `match` |
| C# | `catch`, `throw`, `try {`, `Exception`, `ArgumentException` |
| Ruby | `begin`, `rescue`, `raise`, `ensure` |
| Kotlin | `try`, `catch`, `throw`, `runCatching`, `Result` |
| PHP | `try`, `catch`, `throw`, `Exception` |

**Internal/private helpers (often defensive):**

| Language | Grep pattern |
|---|---|
| Python | `def _`, `__` |
| Java/Scala | `private`, `protected` |
| TypeScript | `private`, `#` (private fields) |
| Go | lowercase function names (unexported) |
| Rust | `pub(crate)`, non-`pub` functions |
| C# | `private`, `protected`, `internal` |
| Ruby | `private`, `protected`, `def _` |
| Kotlin | `private`, `protected`, `internal` |
| PHP | `private`, `protected` |

**Sentinel values, fallbacks, boundary checks:** Search for `== 0`, `< 0`, `default`, `fallback`, `else`, `match`, `switch` — these are language-agnostic.

## What to Look For Beyond Grep

- **Bugs that were fixed** — Git history, TODO comments, workarounds, defensive code that checks for things that "shouldn't happen"
- **Design decisions** — Comments explaining "why" not just "what." Configuration that could have been hardcoded but isn't. Abstractions that exist for a reason.
- **External data quirks** — Any place the code normalizes, validates, or rejects input from an external system
- **Parsing functions** — Every parser (regex, string splitting, format detection) has failure modes. What happens with malformed input? Empty input? Unexpected types?
- **Boundary conditions** — Zero values, empty strings, maximum ranges, first/last elements, type boundaries

## Converting Findings to Scenarios

For each defensive pattern, ask: "What failure does this prevent? What input would trigger this code path?"

The answer becomes a fitness-to-purpose scenario:

```markdown
### Scenario N: [Memorable Name]

**Requirement tag:** [Req: inferred — from function_name() behavior] *(use the canonical `[Req: tier — source]` format from SKILL.md Phase 1, Step 1)*

**What happened:** [The failure mode this code prevents. Reference the actual function, file, and line. Frame as a vulnerability analysis, not a fabricated incident.]

**The requirement:** [What the code must do to prevent this failure.]

**How to verify:** [A concrete test that would fail if this regressed.]
```

## Converting Findings to Boundary Tests

Each defensive pattern also maps to a boundary test. **Assertions must check actual values, not just presence.** Presence-only assertions (assertNotNull, toBeDefined, is_ok) are insufficient — verify the system produced correct output despite the boundary condition.

```python
# Python (pytest)
def test_defensive_pattern_name(fixture):
    """[Req: inferred — from function_name() guard] guards against X."""
    input_data = {**fixture, "field": None}  # Trigger defensive code path
    result = process(input_data)
    # Assert specific output: not just that result exists, but what it contains
    assert result["status"] == "handled", "should use default when field is None"
    assert result["fallback_value"] == "default", "should apply fallback"
```

```java
// Java (JUnit 5)
@Test
@DisplayName("[Req: inferred — from methodName() guard] guards against X")
void testDefensivePatternName() {
    fixture.setField(null);  // Trigger defensive code path
    var result = process(fixture);
    // Assert the specific outcome, not just that it didn't throw
    assertEquals("HANDLED", result.getStatus(), "should handle null field gracefully");
    assertEquals("default_value", result.getValue(), "should apply default when null");
}
```

```scala
// Scala (ScalaTest)
// [Req: inferred — from methodName() guard]
"defensive pattern: methodName()" should "guard against X" in {
  val input = fixture.copy(field = None)  // Trigger defensive code path
  val result = process(input)
  // Assert the specific output value, not just that it's defined
  result.status should equal ("HANDLED")
  result.value should equal ("default")
}
```

```typescript
// TypeScript (Jest)
test('[Req: inferred — from functionName() guard] guards against X', () => {
    const input = { ...fixture, field: null };  // Trigger defensive code path
    const result = process(input);
    // Assert specific output values
    expect(result.status).toBe('HANDLED');
    expect(result.value).toBe('default');
});
```

```go
// Go (testing)
func TestDefensivePatternName(t *testing.T) {
    // [Req: inferred — from FunctionName() guard] guards against X
    fixture.Field = nil  // Trigger defensive code path
    result, err := Process(fixture)
    if err != nil {
        t.Fatalf("expected graceful handling, got error: %v", err)
    }
    // Assert the specific output, not just that it succeeded
    if result.Status != "HANDLED" {
        t.Errorf("expected status HANDLED, got %s", result.Status)
    }
    if result.Value != "default" {
        t.Errorf("expected value 'default', got %s", result.Value)
    }
}
```

```rust
// Rust (cargo test)
#[test]
fn test_defensive_pattern_name() {
    // [Req: inferred — from function_name() guard] guards against X
    let input = Fixture { field: None, ..default_fixture() };
    let result = process(&input);
    // Assert the specific output value
    assert_eq!(result.status, "HANDLED", "should handle null field");
    assert_eq!(result.value, "default", "should apply default");
}
```

```csharp
// C# — boundary test from defensive pattern
[TestFixture]
public class BoundaryTests
{
    [Test]
    public void TestNullGuardOnCriticalField()
    {
        // Defensive pattern found: null check on config.ConnectionString
        var config = new AppConfig { ConnectionString = null };
        Assert.Throws<ArgumentNullException>(() => new DatabaseService(config));
    }

    [Test]
    public void TestRetryExhaustion()
    {
        // Defensive pattern found: retry loop with max attempts
        var service = new UnreliableService(alwaysFail: true);
        var result = service.ExecuteWithRetry(maxAttempts: 3);
        Assert.That(result.Success, Is.False);
        Assert.That(result.Attempts, Is.EqualTo(3));
    }
}
```

```ruby
# Ruby (RSpec) — boundary test from defensive pattern
RSpec.describe "Boundary tests" do
  it "raises on nil required field" do
    # Defensive pattern found: nil check on config[:api_key]
    config = { api_key: nil, endpoint: "https://api.example.com" }
    expect { Client.new(config) }.to raise_error(ArgumentError, /api_key/)
  end

  it "handles retry exhaustion gracefully" do
    # Defensive pattern found: retry block with max attempts
    service = UnreliableService.new(always_fail: true)
    result = service.execute_with_retry(max_attempts: 3)
    expect(result).not_to be_success
    expect(result.attempts).to eq(3)
  end
end
```

```kotlin
// Kotlin — boundary test from defensive pattern
class BoundaryTests {
    @Test
    fun `null guard on critical field throws`() {
        // Defensive pattern found: requireNotNull on config.connectionString
        val config = AppConfig(connectionString = null)
        assertThrows<IllegalArgumentException> {
            DatabaseService(config)
        }
    }

    @Test
    fun `retry exhaustion returns failure`() {
        // Defensive pattern found: retry loop with max attempts
        val service = UnreliableService(alwaysFail = true)
        val result = service.executeWithRetry(maxAttempts = 3)
        assertFalse(result.success)
        assertEquals(3, result.attempts)
    }
}
```

```php
// PHP — boundary test from defensive pattern
class BoundaryTest extends TestCase
{
    public function testNullGuardOnCriticalField(): void
    {
        // Defensive pattern found: null check on $config['api_key']
        $config = ['api_key' => null, 'endpoint' => 'https://api.example.com'];
        $this->expectException(\InvalidArgumentException::class);
        new Client($config);
    }

    public function testRetryExhaustion(): void
    {
        // Defensive pattern found: retry loop with max attempts
        $service = new UnreliableService(alwaysFail: true);
        $result = $service->executeWithRetry(maxAttempts: 3);
        $this->assertFalse($result->isSuccess());
        $this->assertEquals(3, $result->getAttempts());
    }
}
```

## State Machine Patterns

State machines are a special category of defensive pattern. When you find status fields, lifecycle phases, or mode flags, trace the full state machine — see SKILL.md Step 5a for the complete process.

**How to find state machines:**

| Language | Grep pattern |
|---|---|
| Python | `status`, `state`, `phase`, `mode`, `== "running"`, `== "pending"` |
| Java | `enum.*Status`, `enum.*State`, `.getStatus()`, `switch.*status` |
| Scala | `sealed trait.*State`, `case object`, `status match` |
| TypeScript | `status:`, `state:`, `Status =`, `switch.*status` |
| Go | `Status`, `State`, `type.*Phase`, `switch.*status` |
| Rust | `enum.*State`, `enum.*Status`, `match.*state` |
| C# | `enum.*Status`, `enum.*State`, `switch.*status`, `.Status`, `.State` |
| Ruby | `@status`, `@state`, `attr_accessor :status`, `case.*when.*status` |
| Kotlin | `enum.*Status`, `enum.*State`, `sealed class.*State`, `when.*status` |
| PHP | `$status`, `$state`, `$this->status`, `match.*$status` (PHP 8) |

**For each state machine found:**

1. List every possible state value (read the enum or grep for assignments)
2. For each handler/consumer that checks state, verify it handles ALL states
3. Look for states you can enter but never leave (terminal state without cleanup)
4. Look for operations that should be available in a state but are blocked by an incomplete guard

**Converting state machine gaps to scenarios:**

```markdown
### Scenario N: [Status] blocks [operation]

**Requirement tag:** [Req: inferred — from handler() status guard]

**What happened:** The [handler] only allows [operation] when status is "[allowed_states]", but the system can enter "[missing_state]" status (e.g., due to [condition]). When this happens, the user cannot [operation] and has no workaround through the interface.

**The requirement:** [operation] must be available in all states where the user would reasonably need it, including [missing_state].

**How to verify:** Set up a [entity] in "[missing_state]" status. Attempt [operation]. Assert it succeeds or provides a clear error with a workaround.
```

## Missing Safeguard Patterns

Search for operations that commit the user to expensive, irreversible, or long-running work without adequate preview or confirmation:

| Pattern | What to look for |
|---|---|
| Pre-commit information gap | Operations that start batch jobs, fan-out expansions, or API calls without showing estimated cost, scope, or duration |
| Silent expansion | Fan-out or multiplication steps where the final work count isn't known until runtime, with no warning shown |
| No termination condition | Polling loops, watchers, or daemon processes that check for new work but never check whether all work is done |
| Retry without backoff | Error handling that retries immediately or on a fixed interval without exponential backoff, risking rate limit floods |

**Converting missing safeguards to scenarios:**

```markdown
### Scenario N: No [safeguard] before [operation]

**Requirement tag:** [Req: inferred — from init_run()/start_watch() behavior]

**What happened:** [Operation] commits the user to [consequence] without showing [missing information]. In practice, a [example] fanned out from [small number] to [large number] units with no warning, resulting in [cost/time consequence].

**The requirement:** Before committing to [operation], display [safeguard] showing [what the user needs to see].

**How to verify:** Initiate [operation] and assert that [safeguard information] is displayed before the point of no return.
```

## Comprehensive Defect Category Detection

The playbook addresses 14 defect categories, covered in the following sections and subsections:

1. Null/Nil Guards (grep table, Systematic Search)
2. Exception/Error Handling (grep table, Systematic Search)
3. Internal/Private Helpers (grep table, Systematic Search)
4. Sentinel Values, Fallbacks, Boundary Checks (Systematic Search)
5. State Machine Gaps (grep table, State Machine Patterns section)
6. Missing Safeguards (Missing Safeguard Patterns section)
7. Concurrency Issues (grep table below)
8. SQL Errors (grep table below)
9. Security Issues (grep table below)
10. Serialization Bugs (grep table below)
11. API Contract Violations (grep table below)
12. Protocol Violations (grep table below)
13. Async/Sync Parity, Context Propagation Loss, Field Label Drift, Truth Fragmentation, and Callback Concurrency (grep tables below)
14. Generated and Invisible Code Defects (detection guidance in SKILL.md Step 5d — no grep table; requires manual inspection of build pipelines, code generators, and generated output files)

Beyond the patterns covered in the main sections above, search for these additional categories using language-specific grep patterns and domain knowledge:

### Concurrency Issues

**Grep patterns:**

| Language | Patterns |
|---|---|
| Python | `threading`, `Thread`, `Lock`, `RLock`, `Condition`, `asyncio`, `await`, `@asyncio`, `concurrent.futures` |
| Java | `synchronized`, `volatile`, `AtomicReference`, `Thread`, `ReentrantLock`, `CountDownLatch`, `Semaphore` |
| Scala | `synchronized`, `concurrent`, `Future`, `Promise` |
| TypeScript | `Promise`, `async`, `await`, `Promise.all`, `.then()`, callback patterns |
| Go | `goroutine`, `go `, `chan`, `mutex`, `sync.Mutex`, `atomic` |
| Rust | `thread::spawn`, `crossbeam`, `tokio::task`, `mutex`, `Arc<Mutex` |
| C# | `Task`, `Thread`, `lock`, `async`, `await`, `Semaphore`, `ReaderWriterLock` |
| Ruby | `Thread`, `Mutex`, `ConditionVariable`, `Fiber`, `Thread.safe?` |
| Kotlin | `Thread`, `Runnable`, `synchronized`, `@Volatile`, `Future`, `launch`, `async` |
| PHP | `pcntl_fork`, `Swoole\Coroutine`, async patterns; note: PHP typically single-threaded per request |

**What to look for:** Race conditions, deadlocks, data races. In particular: shared mutable state accessed from multiple goroutines/threads (Go/Rust), missing synchronization primitives, blocking operations on event loops, unbounded queue growth.

### SQL Errors

**Grep patterns:**

| Language | Patterns |
|---|---|
| Python | `sql`, `SQL`, `query`, `execute`, `fetchall`, `Connection`, `cursor`, `SELECT`, `INSERT`, `UPDATE` |
| Java | `PreparedStatement`, `Statement`, `ResultSet`, `Connection`, `SELECT`, `INSERT`, `UPDATE`, `sql` |
| Scala | `sql`, `query`, `execute`, `ResultSet` |
| TypeScript/JavaScript | `query`, `sql`, `SELECT`, `INSERT`, `UPDATE`, `execute`, database driver names |
| Go | `Query`, `Exec`, `sql.DB`, `rows.Scan`, `sql.*` |
| Rust | `sqlx`, `diesel`, `sql`, `query`, `execute` |
| C# | `SqlCommand`, `SqlParameter`, `ExecuteQuery`, `SELECT`, `INSERT`, `UPDATE`, `SqlConnection` |
| Ruby | `execute`, `query`, `SELECT`, `INSERT`, `UPDATE`, `ActiveRecord`, `sql` |
| Kotlin | `query`, `execute`, `SQL`, `SELECT`, `INSERT`, `UPDATE`, `SQLiteDatabase` |
| PHP | `mysqli`, `PDO`, `query`, `execute`, `SELECT`, `INSERT`, `UPDATE`, `$_COOKIE` in queries |

**What to look for:** SQL injection (string concatenation in queries), missing parameterized queries, incorrect type conversions in result processing, assumption that query succeeds without error handling, improper escaping of user input.

### Security Issues

**Grep patterns:**

| Language | Patterns |
|---|---|
| Python | `password`, `secret`, `token`, `auth`, `decrypt`, `encrypt`, `hash`, `ssl`, `tls`, `https` |
| Java | `SecureRandom`, `MessageDigest`, `Cipher`, `KeyStore`, `Certificate`, `password`, `token` |
| Scala | `SecureRandom`, `Cipher`, `password`, `token` |
| TypeScript | `crypto`, `password`, `secret`, `token`, `hash`, `jwt`, `cookie` |
| Go | `crypto`, `hash`, `rand.Reader`, `tls`, `password`, `token` |
| Rust | `crypto`, `hash`, `password`, `secret`, `tls` |
| C# | `RNGCryptoServiceProvider`, `SHA256`, `password`, `token`, `SecureString`, `DataProtectionScope` |
| Ruby | `SecureRandom`, `password`, `secret`, `token`, `OpenSSL` |
| Kotlin | `SecureRandom`, `Cipher`, `MessageDigest`, `password`, `token` |
| PHP | `password_hash`, `password_verify`, `random_bytes`, `hash`, `openssl`, `token`, `session` |

**What to look for:** Hardcoded credentials, weak hash functions, missing input validation (especially headers and user-provided data), missing TLS/SSL verification, exposure of sensitive data in logs or error messages, use of pseudorandom instead of cryptographic random.

### Serialization Bugs

**Grep patterns:**

| Language | Patterns |
|---|---|
| Python | `json.loads`, `json.dumps`, `pickle`, `yaml`, `serialize`, `deserialize`, `__dict__` |
| Java | `ObjectInputStream`, `ObjectOutputStream`, `Serializable`, `readObject`, `writeObject`, `gson`, `jackson` |
| Scala | `Serializable`, `json`, `serialize`, `deserialize` |
| TypeScript | `JSON.parse`, `JSON.stringify`, `serialize`, `deserialize` |
| Go | `json.Marshal`, `json.Unmarshal`, `gob`, `Encode`, `Decode` |
| Rust | `serde`, `Serialize`, `Deserialize`, `to_string`, `from_str` |
| C# | `JsonConvert`, `JsonSerializer`, `XmlSerializer`, `DataContractSerializer`, `BinaryFormatter` |
| Ruby | `JSON.parse`, `JSON.dump`, `Marshal`, `yaml`, `serialize`, `deserialize` |
| Kotlin | `json`, `JSON.parse`, `JSON.stringify`, `Parcelable`, `Serializable` |
| PHP | `json_encode`, `json_decode`, `serialize`, `unserialize` |

**What to look for:** Field omission when serializing (new fields not included in serialized output), type mismatch during deserialization, assumption that deserialized data is valid (missing re-validation), version mismatches between serializers, loss of precision in numeric conversions.

### API Contract Violations

**Grep patterns:** Search for HTTP client/server code, API calls, and protocol implementations. Look for:

| Language | Patterns |
|---|---|
| Python | `requests`, `http`, `api`, `endpoint`, `method`, `response.status_code`, `headers` |
| Java | `HttpClient`, `HttpRequest`, `URL`, `URLConnection`, `REST`, `@GetMapping`, `@PostMapping` |
| Scala | `http`, `api`, `request`, `response` |
| TypeScript | `fetch`, `axios`, `HttpClient`, `api`, `endpoint`, `headers` |
| Go | `http.Get`, `http.Post`, `http.NewRequest`, `response.StatusCode` |
| Rust | `reqwest`, `http`, `Client`, `Request` |
| C# | `HttpClient`, `HttpRequest`, `HttpResponse`, `StatusCode`, `api` |
| Ruby | `Net::HTTP`, `RestClient`, `http`, `api`, `endpoint`, `headers` |
| Kotlin | `okhttp`, `retrofit`, `HttpClient`, `api`, `request`, `response` |
| PHP | `cURL`, `file_get_contents`, `stream_context_create`, `http_response_code`, `headers` |

**What to look for:** Assuming API response format without validation, ignoring HTTP status codes, missing error response handling, assumption that endpoint exists without fallback, version mismatches between client and API, missing required headers.

### Protocol Violations

**Grep patterns:** Search for code implementing or consuming protocols (HTTP, WebSocket, gRPC, AMQP, custom protocols):

| Language | Patterns |
|---|---|
| Python | `socket`, `websocket`, `grpc`, `http.server`, `protocol`, `handshake`, `ssl.wrap_socket` |
| Java | `Socket`, `ServerSocket`, `WebSocket`, `Channel`, `Protocol`, `Handshake`, `gRPC` |
| Scala | `Socket`, `Channel`, `Protocol`, `Akka.IO`, `http4s` |
| TypeScript | `WebSocket`, `ws`, `socket.io`, `grpc`, `protocol`, `handshake` |
| Go | `net.Conn`, `net.Listener`, `grpc`, `websocket`, `protocol`, `Handshake` |
| Rust | `tokio::net`, `tungstenite`, `tonic`, `Protocol`, `handshake` |
| C# | `Socket`, `TcpClient`, `WebSocket`, `gRPC`, `Protocol`, `Handshake`, `SignalR` |
| Ruby | `TCPSocket`, `WebSocket`, `grpc`, `protocol`, `handshake` |
| Kotlin | `Socket`, `WebSocket`, `OkHttp`, `gRPC`, `Protocol`, `Ktor` |
| PHP | `socket_create`, `Ratchet`, `WebSocket`, `stream_socket`, `protocol` |

**What to look for:** Non-conformance to RFC specifications, incomplete handshakes, missing protocol version checks, incorrect state transitions, malformed message construction, assumption that protocol steps succeed without verification.

### Async/Sync Parity

Covered in detail in SKILL.md Step 5d. Search for pairs of async/sync implementations (common in HTTP clients, database drivers, file I/O):

| Language | Patterns |
|---|---|
| Python | `async def`, `await`, `asyncio`, `concurrent.futures` (paired synchronous versions) |
| Java | `CompletableFuture`, `Future`, `@Async` vs synchronous methods |
| Scala | `Future`, `IO`, `Task` vs synchronous counterparts, `Await.result` |
| TypeScript | `async`, `await`, `Promise` vs callback-based or synchronous APIs |
| Go | `go` keyword, goroutines vs blocking calls |
| Rust | `tokio::task::spawn`, `tokio::runtime` vs synchronous counterparts |
| C# | `async Task`, `Task.Run`, `ConfigureAwait`, `GetAwaiter().GetResult()` vs synchronous methods |
| Ruby | `Async`, `Concurrent::Future`, `Thread`, `Fiber` vs synchronous methods |
| Kotlin | `suspend fun`, `launch`, `async`, `runBlocking`, `withContext` vs non-suspend functions |
| PHP | `Swoole\Coroutine`, `ReactPHP\Promise`, `Amp\Promise`, `Generator` yield vs synchronous |

**What to look for:** Different parameter lists between sync/async versions, missing configuration options in async variant, different error handling strategies, incomplete context propagation.

### Context Propagation Loss

Covered in detail in SKILL.md Step 5c. Search for code that receives objects as parameters (HTTP clients, database connections, configuration bundles) and creates new instances:

| Language | Patterns |
|---|---|
| Python | `__init__`, `cls(`, factory methods, `copy()`, `deepcopy()`, `new_session()`, `Session()` |
| Java | `new Builder()`, `newInstance()`, factory methods, `clone()`, `.build()` |
| Scala | `.copy(`, `new`, factory `apply()` methods, companion objects |
| TypeScript | `new`, `Object.create`, `Object.assign`, factory functions, `create*()` |
| Go | `New*()`, `&Type{}`, factory functions inside methods that receive the same type |
| Rust | `::new()`, `::default()`, `::from()`, `Clone::clone`, builder patterns |
| C# | `new`, factory methods, `Clone()`, `Create*()`, `IServiceProvider`, builder patterns |
| Ruby | `.new`, `dup`, `clone`, factory methods, `initialize` in context of existing object |
| Kotlin | constructor calls, `copy()` (data classes), factory methods, builder patterns |
| PHP | `new`, `clone`, factory methods, `__construct` in context of existing object |

**What to look for:** Verify the new instance preserves headers, tokens, SSL context, timeout settings from the original parameter. Trace whether context like request headers, credentials, or connection pools are copied or lost.

### Field Label Drift

Covered in detail in SKILL.md Step 5c. Search for positional data extraction:

| Language | Patterns |
|---|---|
| Python | `parts[N]`, `row[N]`, `split()[N]`, `columns[N]`, tuple unpacking `a, b, c = line.split()` |
| Java | `parts[N]`, `row.get(N)`, `columns[N]`, `split("...")[N]`, `.getColumn(N)` |
| Scala | `parts(N)`, `row(N)`, `split("...")(N)`, pattern matching tuple extraction |
| TypeScript | `parts[N]`, `row[N]`, `columns[N]`, destructuring `const [a, b, c] = line.split()` |
| Go | `parts[N]`, `row[N]`, `fields[N]`, `strings.Split()[N]` |
| Rust | `parts[N]`, `row[N]`, `.nth(N)`, iterator `.next()` chains for positional extraction |
| C# | `parts[N]`, `row[N]`, `columns[N]`, `Split()[N]`, tuple deconstruction |
| Ruby | `parts[N]`, `row[N]`, `split[N]`, parallel assignment `a, b, c = line.split` |
| Kotlin | `parts[N]`, `row[N]`, `split("...")[N]`, destructuring declarations |
| PHP | `$parts[N]`, `$row[N]`, `explode()[N]`, `list($a, $b, $c) = explode(...)` |

**What to look for:** Variable names that don't match current column positions (data formats evolve, but variable names persist). CSV parsers, Markdown table readers, fixed-position parsers.

### Truth Fragmentation

Covered in detail in SKILL.md Step 5c. Search for canonical value definitions:

| Language | Patterns |
|---|---|
| Python | String literals in `list`, `dict`, `set` definitions; `Enum` classes; module-level constants |
| Java | `enum` values, `static final String`, `Map.of()`, `Set.of()`, `Arrays.asList()` |
| Scala | `sealed trait`/`case object` hierarchies, `val` constants, `Set(...)` definitions |
| TypeScript | `enum`, `as const`, `type ... =`, union types, `readonly` arrays |
| Go | `const` blocks, `var` slices/maps of strings, `iota` enums |
| Rust | `enum` variants, `const` strings, `static` arrays, `match` arms |
| C# | `enum` values, `const string`, `static readonly`, `HashSet<string>`, `Dictionary` literals |
| Ruby | `CONSTANT` arrays/hashes, `Symbol` sets, `freeze` patterns, module constants |
| Kotlin | `enum class` values, `companion object` constants, `setOf()`, `listOf()` |
| PHP | `const`, `define()`, class constants, `enum` (PHP 8.1+), static arrays |

**What to look for:** Identical values defined separately in multiple locations — when one is updated and the others aren't, the system produces inconsistent results. Use `grep -r "literal_value" .` to find all occurrences of canonical values.

### Callback Concurrency

Covered in detail in SKILL.md Step 5c. Search for library callbacks:

| Language | Patterns |
|---|---|
| Python | `callback=`, `on_event`, `add_done_callback`, `register`, `signal.signal`, decorator-based handlers |
| Java | `Callback`, `Listener`, `Observer`, `Consumer<>`, `BiConsumer<>`, `@EventHandler`, lambda callbacks |
| Scala | `onComplete`, `onSuccess`, `onFailure`, `foreach` on Future, Akka message handlers |
| TypeScript | `addEventListener`, `on(`, callback parameters, `.subscribe`, `.then()`, event emitter patterns |
| Go | `func` parameters (callback functions), `http.HandleFunc`, channel receive in goroutines |
| Rust | `Fn`, `FnMut`, `FnOnce` trait bounds, closure captures, `tokio::spawn` with captured state |
| C# | `event`, `EventHandler`, `Action<>`, `Func<>`, `delegate`, `+=` event subscription |
| Ruby | `&block`, `yield`, `Proc.new`, `lambda`, `on_*` method patterns, `Observer` pattern |
| Kotlin | `lambda` parameters, `suspend` callbacks, `Flow.collect`, `Channel.consumeEach`, `setOn*Listener` |
| PHP | `callable`, `Closure`, `array_walk`, event dispatcher patterns, `spl_autoload_register` |

**What to look for:** Read the library documentation to determine whether callbacks execute synchronously or asynchronously. Trace whether the callback captures mutable state that the main code path also modifies.

## Defensive Patterns vs. Missing Safeguards — Important Distinction

Not all defensive code patterns produce tests. Understanding which ones do is critical:

**Defensive Patterns (Existing Code) → Boundary Tests:**

Defensive patterns are visible in the codebase: null guards, try/catch blocks, normalization functions, fallbacks, sentinel checks. Each one is evidence of a past failure. They produce **boundary tests** because the test exercises the existing defensive code path. When you write a test that triggers a null guard, you're testing that the code handles null values correctly. Examples:

- `if (x == null) { return default_value; }` → write a test that passes null and assert you get default_value
- `try { parse() } catch (e) { log_error() }` → write a test that triggers invalid input and assert the error is logged
- `if (length == 0) { return empty_list; }` → write a test with zero-length input and assert you get an empty list

**Missing Safeguards (Absent Code) → Spec Audit Findings:**

Missing safeguards are code that *should* be there but isn't: a missing null check, missing input validation, missing rate limiting, missing confirmation before expensive operations. These do NOT produce boundary tests — they produce **quality findings** and **spec audit discoveries** because there's no code path to test. When you discover that a function accepts user input without validation, you're finding a gap in the code, not testing a defensive pattern. Examples:

- No null check on a required field → this is a spec audit finding, not a boundary test
- No rate limiting on expensive operations → this is a missing safeguard finding
- No confirmation before fan-out expansion → this is an architectural gap finding

When you write `test_no_rate_limit()`, the test would fail because the code path never exists — "code path never reached" error. This is not a meaningful test; it's an architectural finding that belongs in QUALITY.md scenarios or spec audit results.

**How to handle missing safeguards:**

1. **During Phase 1 exploration:** Document them in your notes. They inform your risk scenarios and QUALITY.md content.
2. **In QUALITY.md:** Include them as architectural vulnerability scenarios (Fitness-to-purpose section).
3. **In spec audit (RUN_SPEC_AUDIT.md):** Flag them as requirements that aren't implemented.
4. **Do NOT write boundary tests for them** — tests that exercise non-existent code paths are broken tests.

## Minimum Bar

You should find at least 2–3 defensive patterns per source file in the core logic modules (the 3–5 modules identified in Step 2 as most complex or fragile). If you find fewer, read function bodies more carefully — not just signatures and comments.

For a medium-sized project (5–15 source files, of which 3–5 are core logic), expect to find 15–30 defensive patterns across the core modules. A project with 15 source files doesn't need 45 patterns — focus depth on the core logic where bugs matter most. Each pattern should produce at least one boundary test. Additionally, trace at least one state machine if the project has status/state fields, and check at least one long-running operation for missing safeguards.
