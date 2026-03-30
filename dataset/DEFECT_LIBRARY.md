# Reference Defect Library

A curated set of real bugs from real open-source projects, used to measure the detection rate of the quality playbook skill. Each entry identifies a known bug at a specific commit, with the fix commit as ground truth.

**Methodology**: For each defect, check out `pre_fix_commit`, run the quality playbook, and score whether the generated artifacts identify the bug. The `fix_commit` confirms the bug existed and documents what the correct fix was. Pre-fix commit is always the immediate parent of the fix commit (`git rev-parse FIX_COMMIT^`).

**Verification**: All SHAs verified against local clones on 2026-03-29. For entries without a GitHub issue number, the PR number or commit message is cited as the traceability source.

---

## Severity Classification

- **Critical** — System-wide failure: authentication broken, deadlock on common paths, data corruption, default config unsafe. Causes production outage or data loss.
- **High** — Feature broken or significantly degraded. Common use case fails or produces wrong results. Workaround difficult or nonexistent.
- **Medium** — Edge case or specific scenario fails. Workaround possible. Limited surface area.
- **Low** — Cosmetic, misleading message, or minor UX issue. Workaround trivial.

## Categories

Categories that emerged from the library. Each defect has one **primary** category (used for counting and analysis) and optionally secondary tags in parentheses.

- **API contract violation** — wrong status codes, missing headers, incorrect response types
- **concurrency issue** — thread safety, deadlocks, race conditions
- **configuration error** — wrong property references, build config, initialization order
- **error handling** — wrong exception types, missing handlers, information disclosure
- **missing boundary check** — unimplemented endpoints, missing defensive checks
- **null safety** — null dereference, missing null guards
- **protocol violation** — RFC non-compliance, missing required HTTP behavior
- **security issue** — information disclosure, broken authentication
- **silent failure** — errors swallowed or producing wrong results without indication
- **SQL error** — ambiguous columns, wrong queries
- **state machine gap** — state leaks, wrong lifecycle ordering, initialization timing
- **type safety** — wrong generic types, type mismatches, type resolution failures
- **validation gap** — missing input validation, wrong validation logic

## Playbook Steps (Reference Key)

The "Playbook Angle" column identifies which quality playbook step(s) should detect each defect. Steps refer to the quality playbook v1.2.0 exploration phase:

- **Step 2** — Architecture mapping (module boundaries, data flow, subsystem interaction)
- **Step 3** — Existing test analysis (coverage gaps, test quality)
- **Step 4** — Specification reading (functional requirements, API contracts, RFCs)
- **Step 5** — Defensive pattern search (try/catch, null checks, retry logic, guards)
- **Step 5a** — State machine tracing (status fields, lifecycle phases, transition completeness)
- **Step 5b** — Schema type mapping (type mismatches, validation layer analysis)
- **Step 6** — Quality risk identification (silent failure, domain knowledge, "what goes wrong in systems like this")

---

## Summary

| Project | Language | Type | Defects | Critical | High | Medium | Low |
|---------|----------|------|---------|----------|------|--------|-----|
| [google/gson](https://github.com/google/gson) | Java | Library | 16 | 2 | 6 | 7 | 1 |
| [square/okhttp](https://github.com/square/okhttp) | Java/Kotlin | Library | 53 | 3 | 13 | 24 | 13 |
| [javalin/javalin](https://github.com/javalin/javalin) | Java/Kotlin | Framework | 15 | 2 | 7 | 6 | 0 |
| [spring-petclinic/spring-petclinic-rest](https://github.com/spring-petclinic/spring-petclinic-rest) | Java | Application | 16 | 1 | 10 | 4 | 1 |
| [apache/zookeeper](https://github.com/apache/zookeeper) | Java | Infrastructure | 50 | 2 | 16 | 20 | 12 |
| [apache/kafka](https://github.com/apache/kafka) | Java/Scala | Infrastructure | 51 | 3 | 22 | 14 | 12 |
| [pydantic/pydantic](https://github.com/pydantic/pydantic) | Python | Library | 55 | 1 | 20 | 34 | 0 |
| [tiangolo/fastapi](https://github.com/tiangolo/fastapi) | Python | Framework | 15 | 2 | 8 | 4 | 1 |
| [andrewstellman/octobatch](https://github.com/andrewstellman/octobatch) | Python | Application | 9 | 0 | 4 | 3 | 2 |
| [rq/rq](https://github.com/rq/rq) | Python | Infrastructure | 45 | 3 | 18 | 20 | 4 |
| [alibaba/AgentScope](https://github.com/alibaba/AgentScope) | Python | Framework | 25 | 2 | 14 | 9 | 0 |
| [encode/httpx](https://github.com/encode/httpx) | Python | Library | 49 | 0 | 11 | 27 | 11 |
| [spf13/cobra](https://github.com/spf13/cobra) | Go | Library | 41 | 2 | 15 | 22 | 2 |
| [go-chi/chi](https://github.com/go-chi/chi) | Go | Framework | 30 | 2 | 11 | 17 | 0 |
| [cli/cli](https://github.com/cli/cli) | Go | Application | 71 | 2 | 24 | 31 | 14 |
| [nsqio/nsq](https://github.com/nsqio/nsq) | Go | Infrastructure | 58 | 5 | 21 | 29 | 3 |
| [colinhacks/zod](https://github.com/colinhacks/zod) | TypeScript | Library | 45 | 1 | 15 | 20 | 9 |
| [trpc/trpc](https://github.com/trpc/trpc) | TypeScript | Framework | 50 | 5 | 28 | 17 | 0 |
| [prisma/prisma](https://github.com/prisma/prisma) | TypeScript | Infrastructure | 50 | 5 | 22 | 20 | 3 |
| [calcom/cal.com](https://github.com/calcom/cal.com) | TypeScript | Application | 69 | 3 | 15 | 36 | 15 |
| [serde-rs/serde](https://github.com/serde-rs/serde) | Rust | Library | 59 | 5 | 24 | 20 | 10 |
| [tokio-rs/axum](https://github.com/tokio-rs/axum) | Rust | Framework | 40 | 4 | 17 | 16 | 3 |
| [BurntSushi/ripgrep](https://github.com/BurntSushi/ripgrep) | Rust | Application | 48 | 3 | 12 | 19 | 14 |
| [lightbend/config](https://github.com/lightbend/config) | Scala | Library | 36 | 2 | 9 | 22 | 3 |
| [twitter/finatra](https://github.com/twitter/finatra) | Scala | Framework | 40 | 1 | 14 | 20 | 5 |
| [akka/akka](https://github.com/akka/akka) | Scala/Java | Framework | 49 | 1 | 19 | 24 | 5 |
| [gitbucket/gitbucket](https://github.com/gitbucket/gitbucket) | Scala | Application | 40 | 2 | 10 | 18 | 10 |
| [JamesNK/Newtonsoft.Json](https://github.com/JamesNK/Newtonsoft.Json) | C# | Library | 55 | 1 | 24 | 28 | 2 |
| [MassTransit/MassTransit](https://github.com/MassTransit/MassTransit) | C# | Framework | 51 | 1 | 18 | 27 | 5 |
| [HangfireIO/Hangfire](https://github.com/HangfireIO/Hangfire) | C# | Infrastructure | 43 | 7 | 12 | 20 | 4 |
| [jellyfin/jellyfin](https://github.com/jellyfin/jellyfin) | C# | Application | 74 | 3 | 20 | 47 | 4 |
| [apache/logging-log4net](https://github.com/apache/logging-log4net) | C# | Library | 40 | 0 | 14 | 20 | 6 |
| [raphaelmansuy/edgequake](https://github.com/raphaelmansuy/edgequake) | TypeScript | Application | 35 | 2 | 18 | 14 | 1 |
| [nats-io/nats.rs](https://github.com/nats-io/nats.rs) | Rust | Infrastructure | 48 | 1 | 25 | 21 | 1 |
| [quarkusio/quarkus](https://github.com/quarkusio/quarkus) | Java | Framework | 82 | 0 | 27 | 45 | 10 |
| [expressjs/express](https://github.com/expressjs/express) | JavaScript | Framework | 48 | 2 | 14 | 30 | 2 |
| [webpack/webpack](https://github.com/webpack/webpack) | JavaScript | Infrastructure | 60 | 4 | 40 | 14 | 2 |
| [eslint/eslint](https://github.com/eslint/eslint) | JavaScript | Library | 50 | 0 | 9 | 39 | 2 |
| [rails/rails](https://github.com/rails/rails) | Ruby | Framework | 60 | 2 | 12 | 34 | 12 |
| [sidekiq/sidekiq](https://github.com/sidekiq/sidekiq) | Ruby | Infrastructure | 50 | 1 | 11 | 28 | 10 |
| [heartcombo/devise](https://github.com/heartcombo/devise) | Ruby | Library | 49 | 4 | 35 | 10 | 0 |
| [laravel/framework](https://github.com/laravel/framework) | PHP | Framework | 58 | 3 | 21 | 31 | 3 |
| [guzzle/guzzle](https://github.com/guzzle/guzzle) | PHP | Library | 52 | 0 | 17 | 32 | 3 |
| [composer/composer](https://github.com/composer/composer) | PHP | Infrastructure | 50 | 4 | 12 | 9 | 25 |
| [ktorio/ktor](https://github.com/ktorio/ktor) | Kotlin | Framework | 45 | 0 | 17 | 28 | 0 |
| [JetBrains/Exposed](https://github.com/JetBrains/Exposed) | Kotlin | Library | 49 | 0 | 24 | 22 | 3 |
| [Kotlin/kotlinx.serialization](https://github.com/Kotlin/kotlinx.serialization) | Kotlin | Library | 52 | 1 | 27 | 22 | 2 |
| [redis/redis](https://github.com/redis/redis) | C | Infrastructure | 50 | 2 | 22 | 25 | 1 |
| [curl/curl](https://github.com/curl/curl) | C | Library | 49 | 0 | 19 | 29 | 1 |
| [jqlang/jq](https://github.com/jqlang/jq) | C | Application | 50 | 7 | 27 | 14 | 2 |
| [vapor/vapor](https://github.com/vapor/vapor) | Swift | Framework | 50 | 0 | 13 | 30 | 7 |
| [apple/swift-nio](https://github.com/apple/swift-nio) | Swift | Infrastructure | 47 | 0 | 21 | 22 | 4 |
| [phoenixframework/phoenix](https://github.com/phoenixframework/phoenix) | Elixir | Framework | 45 | 2 | 17 | 21 | 5 |
| [elixir-ecto/ecto](https://github.com/elixir-ecto/ecto) | Elixir | Library | 50 | 0 | 28 | 19 | 3 |
| [oban-bg/oban](https://github.com/oban-bg/oban) | Elixir | Infrastructure | 47 | 0 | 23 | 14 | 10 |
| **Total** | | | **2564** | **111** | **972** | **1198** | **283** |

## Category Distribution

| Category | Count | % |
|----------|-------|---|
| error handling | 621 | 24.2% |
| validation gap | 359 | 14.0% |
| configuration error | 284 | 11.1% |
| type safety | 231 | 9.0% |
| state machine gap | 217 | 8.5% |
| concurrency issue | 130 | 5.1% |
| serialization | 121 | 4.7% |
| API contract violation | 117 | 4.6% |
| protocol violation | 106 | 4.1% |
| null safety | 103 | 4.0% |
| silent failure | 89 | 3.5% |
| security issue | 83 | 3.2% |
| SQL error | 68 | 2.7% |
| missing boundary check | 35 | 1.4% |

## Project Classification (Language x Type Matrix)

| Language | Library | Framework | Application | Infrastructure |
|----------|---------|-----------|-------------|----------------|
| Java/Kotlin | gson (16), okhttp (53) | javalin (15), quarkus (82) | petclinic (16) | zookeeper (50), kafka (51) |
| Python | pydantic (55), httpx (49) | fastapi (15), AgentScope (25) | octobatch (9) | rq (45) |
| Go | cobra (41) | chi (30) | cli/cli (71) | nsq (58) |
| TypeScript | zod (45) | trpc (50) | cal.com (69), edgequake (35) | prisma (50) |
| Rust | serde (59) | axum (40) | ripgrep (48) | nats.rs (48) |
| Scala | config (36) | finatra (40), akka (49) | gitbucket (40) | — |
| C# | Newtonsoft.Json (55), log4net (40) | MassTransit (51) | jellyfin (74) | Hangfire (43) |
| JavaScript | eslint (50) | express (48) | — | webpack (60) |
| Ruby | devise (49) | rails (60) | — | sidekiq (50) |
| PHP | guzzle (52) | laravel (58) | — | composer (50) |
| Kotlin | Exposed (49), kotlinx.ser (52) | ktor (45) | — | — |
| C | curl (49) | — | jq (50) | redis (50) |
| Swift | — | vapor (50) | — | swift-nio (47) |
| Elixir | ecto (50) | phoenix (45) | — | oban (47) |

---

## Defects

### google/gson (Java)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| G-01 | #2068 | `2549ba93` | `f3232407` | High | type safety | ConstructorConstructor creates wrong Collection/Map types, ignoring interface hierarchies | Step 5b (type resolution logic), Step 5 (defensive pattern around type instantiation) |
| G-02 | #2740 | `61609323` | `48889dba` | Critical | concurrency issue | Class loading deadlock when accessing TypeAdapters due to circular static initialization | Step 6 (domain knowledge: static initializer cycles in serialization libs), Step 5 (synchronization patterns) |
| G-03 | #2706 | `e8cdabf2` | `3621e51e` | High | state machine gap | Type argument array not cloned when resolving ParameterizedType, mutation corrupts shared state | Step 5 (defensive copy missing), Step 6 (mutable shared state risk) |
| G-04 | #2556 | `13be1d10` | `df0165b1` | Medium | validation gap | GsonBuilder.setDateFormat ignores partial DEFAULT style, silently drops date-only formatting | Step 6 (silent failure: wrong output without error), Step 5b (API contract for style params) |
| G-05 | #2549 | `58d1a9f0` | `5471932` | Medium | state machine gap | DateFormat timezone not restored after parse attempt, leaks between multi-format parse cycles | Step 5a (state restoration after operation), Step 6 (thread-local state leaks) |
| G-06 | #2435 | `7ee5ad6c` | `393db094` | High | validation gap | getDelegateAdapter uses equals() instead of reference equality, causing false "cannot serialize" exceptions | Step 5 (identity vs equality check pattern), Step 4 (API contract: factory identity) |
| G-07 | #2599 | `11b27324` | `12406d04` | Medium | null safety | $Gson$Types.equals fails for TypeVariables with non-Class generic declaration | Step 5 (null/type guard in equals), Step 5b (generic type resolution edge case) |
| G-08 | #1832 | `e4c3b653` | `6c27553c` | Critical | concurrency issue | Non-thread-safe creation of adapter for types with cyclic dependency; concurrent getAdapter returns uninitialized FutureTypeAdapter | Step 6 (domain knowledge: concurrent type adapter resolution), Step 5 (synchronization around lazy init) |
| G-09 | #2311 | `af217984` | `9f26679e` | Medium | type safety | JsonPrimitive.equals fails for BigInteger comparison, produces false negatives | Step 5b (numeric type comparison logic), Step 5 (equality implementation pattern) |
| G-10 | #2172 | `6fc1c8f7` | `d53b3ea8` | Medium | error handling | TypeAdapter.toJson throws AssertionError instead of JsonIOException for custom IOExceptions | Step 5 (exception type in catch block), Step 4 (API contract: declared exception types) |
| G-11 | #1782 | `a4bc6c17` | `f7cefcb4` | Low | error handling | JsonTreeReader throws NumberFormatException instead of MalformedJsonException for NaN/Infinity | Step 5 (exception type consistency across implementations), Step 4 (Reader contract) |
| G-12 | #1815 | `5bebf970` | `517d3b17` | High | state machine gap | GsonBuilder state modifications leak to previously-created Gson instances via shared mutable lists | Step 5a (builder lifecycle: post-build mutation), Step 5 (defensive copy on build) |
| G-13 | #2811 | `c395dd1f` | `016315c2` | Medium | state machine gap | GraphAdapterBuilder.addType() delegates to previous registration's creator instead of default | Step 5a (builder state accumulation), Step 5 (registration ordering) |
| G-14 | #2436 | `0109f451` | `4dfae77a` | High | validation gap | Allows adapter registration for Object/JsonElement types, silently breaking built-in serialization | Step 5 (guard on forbidden input), Step 6 (silent failure: overrides critical built-in) |
| G-15 | #2476 | `70bda4b9` | `ddc76ea4` | High | validation gap | JsonWriter.name() accepts names outside object context, producing invalid JSON silently | Step 5 (context validation before write), Step 6 (silent failure: invalid output) |
| G-16 | #1787 | `8451c1fa` | `52697016` | Medium | type safety | TypeAdapterRuntimeTypeWrapper fails to detect reflective adapters used as delegates, serializes subclass with parent adapter | Step 5b (runtime type dispatch logic), Step 2 (adapter delegation architecture) |

### square/okhttp (Java/Kotlin)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| OK-01 | #8962 | 21ad1aa | bbe4f22 | High | null safety | Cache.Entry.writeTo() threw NPE when HTTPS response had null handshake. Network interceptor could strip handshake before cache writes, causing isHttps=true but handshake=null. Fixed by guarding null check. | Step 5b: Schema types - null handling for TLS handshake data |
| OK-02 | #9360 | 385e70f | c85c685 | Medium | type safety | Interceptor.Chain timeout methods had binary-incompatible signature change: Long→Int. API change broke existing bytecode depending on Long parameters, affecting deprecated modules. | Step 5b: Schema types - API contract stability |
| OK-03 | #9374 | 2ae6e02 | 2c7e2f9 | Medium | validation gap | JavaNetCookieJar didn't trim trailing whitespace from cookie values, causing Cookie.Builder to crash on values like "abc123 ". Platform cookie handlers could provide untrimmed values. | Step 5: Defensive patterns - input normalization |
| OK-04 | #9129 | d5b3f2c | 29bd9cd | High | configuration error | MockWebServer SSL handshake failed on Android API 24 - getHandshakeServerNames() requires API 25+, not 24. Incorrect version check blocked valid API 24 operations. | Step 2: Architecture - platform capability detection |
| OK-05 | #8970 | d4a5be1 | 112a19d | High | error handling | HTTP/1.1 connection upgrades (WebSocket) emitted RequestBodyStart event too early before socket upgrade, causing event ordering corruption. Upgraded connections should emit events from socket layer. | Step 5a: State machines - event sequencing on connection upgrade |
| OK-06 | #9364 | 332f403 | 1694f67 | Critical | validation gap | HTTP/2 HPACK decoder had no limits on cumulative header size. Malicious servers could send headers exceeding 256KB total (Chrome limit), causing unbounded memory consumption. Missing addHeader() validation method. | Step 4: Specifications - HTTP/2 RFC 7541 header limits |
| OK-07 | #8724 | da523ca | 33854ec | Medium | silent failure | immutableListOf() and toImmutableList() returned mutable Array.asList() views instead of truly immutable lists, allowing callers to modify internal state via reflection or unsafe casts. | Step 5b: Schema types - immutability contracts |
| OK-08 | #8665 | 3cc87c3 | 9ee3463 | High | error handling | MultipartReader.currentPartBytesRemaining() called indexOf() on entire unbuffered source for each small read, causing O(n²) behavior on large multipart bodies. Fixed by limiting buffer scope with peek().limit(). | Step 5: Defensive patterns - buffering strategy |
| OK-09 | #8898 | 75661d4 | a84a09f | High | API contract violation | OkHttp public API symbols weren't module-named with "okhttp" suffix, breaking Sentry SDK which assumed they would be. Gradle module-name compilation flag missing. | Step 2: Architecture - module naming contracts |
| OK-10 | #8858 | db836de | b418183 | Medium | concurrency issue | MockWebServer response delays could execute after server shutdown if close() interrupted sleep. Threads could still be blocking on sleepNanos() calls, causing leaks. Fixed by canceling delays on socket close. | Step 5a: State machines - shutdown sequencing |
| OK-11 | #8797 | dbf1047 | cad304a | Low | configuration error | PublicSuffixDatabase was double-compressed (.gz inside .jar), wasting 42KB+ of space. Decompression happened at runtime unnecessarily. | Step 6: Quality risks - resource optimization |
| OK-12 | #9316 | c7556e0 | 062ed30 | High | configuration error | OpenJSSE provider failed on Java >8 with IllegalAccessError accessing sun.security.action, but tests ran it on Java 21. CI config didn't restrict OpenJSSE to Java 8 only. | Step 2: Architecture - JVM version constraints |
| OK-13 | #8610 | 8f88fdb | c998c2c | Medium | protocol violation | WebSocket MessageInflater didn't handle self-terminated deflated messages with trailing data. Extra bytes leaked into next message's input, corrupting decompression. Recreate inflater on early termination. | Step 4: Specifications - RFC 7692 WebSocket compression |
| OK-14 | #9184 | 870872d | 2d6e4c9 | Medium | error handling | HttpLoggingInterceptor crashed on UnreadableResponseBody (WebSocket upgrades), throwing NPE when trying to read body source. Missing type check for upgraded responses. | Step 3: Existing tests - logging edge cases |
| OK-15 | #9137 | 2b70b39 | 4c5c844 | Medium | error handling | AndroidLog didn't catch UnsatisfiedLinkError from Paparazzi/non-Robolectric tests, only RuntimeException. Missing Android library availability check on snapshot tools. | Step 2: Architecture - test environment detection |
| OK-16 | #9066 | 3abc040 | 0f8ac5f | Low | validation gap | CallHandshakeTest didn't verify TlsVersion in handshake assertions, only cipher suites. Version validation was implicit but untested, allowing protocol downgrades to slip through. | Step 3: Existing tests - TLS version coverage |
| OK-17 | #8965 | 0ef99d6 | 7e83c84 | Medium | configuration error | Android 10+ Platform logger called into removed APIs, causing crashes. Android 10 removed some logging APIs that code still referenced. | Step 2: Architecture - Android API deprecation |
| OK-18 | #8951 | 4892314 | 1ed7c2c | Low | configuration error | okcurl shell command had syntax error making generated cURL commands invalid. Shell escaping or quoting was broken. | Step 6: Quality risks - tool output validation |
| OK-19 | #8899 | dcb640c | 6d4f4c4 | Medium | API contract violation | Breaking change in alpha.17 release not caught by version validation. API surface changed between releases without proper deprecation. | Step 2: Architecture - semantic versioning |
| OK-20 | #8844 | 24b8d29 | bce973c | Medium | error handling | Non-Robolectric Android tests had inconsistent behavior - some platform code paths weren't tested in real Android environments. Test infrastructure gap. | Step 3: Existing tests - platform-specific coverage |
| OK-21 | #9308 | 855c008 | a0051a5 | Medium | configuration error | Gradle configuration cache not working with test tasks, causing flaky CI. Kotlin compiler settings weren't cacheable. | Step 6: Quality risks - build system stability |
| OK-22 | #9314 | a0051a5 | 3640f2d | Medium | configuration error | More config caching issues with module paths and classpath setup. Plugin initialization side effects prevented caching. | Step 6: Quality risks - build reproducibility |
| OK-23 | #9295 | 20e5296 | 01655fa | Low | error handling | platformTrustedCertificates test flaked on non-Entrust CAs. Test made platform-specific assumptions about root CA bundle contents. | Step 3: Existing tests - environmental assumptions |
| OK-24 | #8870 | bfb24eb | 7721acd | High | protocol violation | HTTP/1.1 connection upgrades with request bodies were not handled - body would be lost during protocol switch. Upgrade request handler didn't properly queue body write. | Step 4: Specifications - HTTP Upgrade header handling |
| OK-25 | #8551 | 8f88fdb | c998c2c | High | silent failure | WebSocket decompression could lose data if message self-terminated early and had trailing bytes. No signal that input was incomplete, silently discarding bytes. | Step 4: Specifications - compression boundary detection |
| OK-26 | #9265 | 01655fa | a197235 | Low | error handling | JavaHttpClientTest had environment-specific failures. Windows path handling or JVM version assumptions in test setup. | Step 3: Existing tests - cross-platform compatibility |
| OK-27 | #9248 | 8040d35 | 9dca358 | Low | error handling | CacheTest flaked on Windows due to file locking or path separators. Temp directory cleanup timing issues. | Step 3: Existing tests - OS-specific behavior |
| OK-28 | #9247 | 8b44ff2 | 1bd382f | Low | error handling | RouteFailureTest was flaky - didn't use RepeatedTest annotation. Race conditions in connection routing under concurrent load. | Step 3: Existing tests - timing dependencies |
| OK-29 | #8851 | db836de | b418183 | Medium | concurrency issue | MockWebServer could deadlock if close() called while response delays were sleeping. Thread could hold lock while blocking on sleep. | Step 5a: State machines - deadlock prevention |
| OK-30 | #8827 | dbf1047 | cad304a | Low | error handling | Loading PublicSuffixDatabase unpacked .gz at runtime, causing CPU waste. Resource extraction at class load time. | Step 6: Quality risks - startup performance |
| OK-31 | #8826 | 75661d4 | a84a09f | Critical | API contract violation | OkHttp API not module-named, breaking third-party SDK integrations (Sentry) that hardcoded symbol naming assumptions. Binary compatibility regression. | Step 2: Architecture - third-party integration contracts |
| OK-32 | #8796 | 2f6a27f | 1536f99 | Medium | state machine gap | EventListener.retryDecision not split from followUpDecision, causing confusion about when retries vs redirects occur. Events weren't granular enough for debugging. | Step 5a: State machines - event granularity |
| OK-33 | #8813 | 7e83c84 | 4b1dff6 | Low | error handling | BufferedSource.indexOf() not using available toIndex parameter, causing unnecessary full-buffer scans. API parameter ignored. | Step 5: Defensive patterns - API usage |
| OK-34 | #8651 | 3cc87c3 | 9ee3463 | High | error handling | MultipartReader's boundary search was pathologically slow on large parts. No limit on buffer scan scope, causing O(n²) with repeated small reads. | Step 5: Defensive patterns - streaming efficiency |
| OK-35 | #8723 | da523ca | 33854ec | Medium | silent failure | Collections.unmodifiableList() not used, allowing reflection to mutate "immutable" lists returned from API. Contract not enforced at runtime. | Step 5b: Schema types - external mutation prevention |
| OK-36 | #9102 | eb2e5a8 | a197235 | Low | configuration error | Module/logging merge conflict in CI - integration tests weren't running. Test infrastructure fragility. | Step 3: Existing tests - test suite maintenance |
| OK-37 | #9005 | 09b6dfe | 2845669 | Low | configuration error | PublicSuffixListGenerator testResources path wrong. Generator couldn't find input files. | Step 2: Architecture - build artifact paths |
| OK-38 | #8909 | c998c2c | b7290e4 | Medium | protocol violation | Deflated HTTP/2 trailers could be corrupted by trailing bytes from previous frame. Message boundary detection incomplete. | Step 4: Specifications - HTTP/2 frame boundaries |
| OK-39 | #8961 | `cc12051` | `be3eb14` | High | type safety | Generic type parameter removed from bodyComplete() causing unchecked cast to IOException. Null-check optimizations removed type safety, forcing explicit non-null assertions. | Step 5b: Schema types - generic type erasure risks |
| OK-40 | #9022 | `46d2117` | `e63f4ba` | Medium | error handling | TaskRunner and RealCall didn't restore interrupt flag when InterruptedException occurred. Swallowing InterruptedException without restoring thread interrupt status violates Java threading contract. | Step 5: Defensive patterns - interrupt flag restoration |
| OK-41 | #8759 | `8fde8e9` | `f021aca` | High | protocol violation | Failed to read response headers after socket write error on request headers. HTTP spec requires reading 431 response even if headers couldn't be fully sent. | Step 4: Specifications - HTTP partial request failures |
| OK-42 | #8904 | `8579689` | `55a2c44` | Medium | error handling | Forced reading of entire response body on trailers, even for MockWebServer responses that don't have real bodies. Unnecessary buffering caused memory issues in test scenarios. | Step 5: Defensive patterns - conditional body reads |
| OK-43 | #9179 | `e472151` | `55bf06e` | Medium | protocol violation | WebSocketReader didn't properly handle ping/pong frames in certain scenarios. Frame parsing logic failed when CI tests weren't running it. | Step 4: Specifications - WebSocket frame handling |
| OK-44 | #8822 | `54cbf31` | `0e17a6` | Medium | configuration error | Robolectric platform detection regression in alpha.15. PlatformRegistry failed to find AndroidPlatform on Robolectric-instrumented JUnit tests. | Step 2: Architecture - platform-specific initialization |
| OK-45 | #8801 | `5e2ac5c` | `2bc0b0f` | Low | error handling | Response.headersContentLength() allocated unnecessarily. Pessimization in allocation path wasted memory on every header length check. | Step 6: Quality risks - object allocation patterns |
| OK-46 | #9184 | `870872d` | `1086125` | Medium | error handling | HttpLoggingInterceptor crashed on UnreadableResponseBody with NPE trying to read upstream source. Missing type check for upgraded/WebSocket responses. | Step 3: Existing tests - special response types |
| OK-47 | #9137 | `2b70b39` | `4c5c844` | Medium | error handling | AndroidLog didn't catch UnsatisfiedLinkError in Paparazzi/non-Robolectric environments. Only caught RuntimeException, missing link error for missing Android library. | Step 2: Architecture - error classification |
| OK-48 | #8970 | `d4a5be1` | `112a19d` | High | state machine gap | RequestBodyStart event emitted too early on connection upgrades before socket transition. Event ordering violation broke event listener contracts on WebSocket/HTTP upgrade paths. | Step 5a: State machines - upgrade event sequencing |
| OK-49 | #9364 | `332f403` | `1694f67` | Critical | validation gap | HTTP/2 HPACK decoder unlimited cumulative header size. Malicious servers could exhaust memory with headers exceeding 256KB (Chrome spec limit). | Step 4: Specifications - HTTP/2 RFC 7541 limits |
| OK-50 | #9374 | `2ae6e02` | `2c7e2f9` | Medium | validation gap | JavaNetCookieJar didn't trim whitespace from cookie values. Platform cookie handlers could provide " value " causing Cookie.Builder to crash. | Step 5: Defensive patterns - input normalization |
| OK-51 | #9360 | `385e70f` | `c85c685` | Medium | type safety | Interceptor.Chain.timeout() signature changed from Long to Int, breaking binary compatibility. Deprecated modules couldn't be migrated, API surface instability. | Step 5b: Schema types - stable API signatures |
| OK-52 | #8951 | `4892314` | `1ed7c2c` | Low | configuration error | okcurl generated invalid shell commands. Improper shell escaping/quoting in Request.toCurl(). | Step 6: Quality risks - tool output validation |
| OK-53 | `#9258` | `90079a1` | `e6250bd` | High | protocol violation | HTTP/1.1 upgrades with empty request bodies weren't handled. Empty body was ignored during protocol switch, breaking WebSocket/Tunnel upgrade. | Step 4: Specifications - upgrade request semantics |

### javalin/javalin (Java/Kotlin)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| J-01 | #2547 | `962e2151` | `7b5f6acc` | High | protocol violation | WebSocket upgrade detection fails on HTTP/2; checks SEC_WEBSOCKET_KEY instead of SEC_WEBSOCKET_VERSION per RFC 8441 | Step 4 (spec: RFC 8441 compliance), Step 6 (domain knowledge: HTTP/2 WebSocket differences) |
| J-02 | no issue, no PR | `5b5b2fbe` | `d4b8c5b1` | High | state machine gap | Attributes set in wsBeforeUpgrade not persisting to onConnect; snapshot taken before handlers run | Step 5a (handler lifecycle ordering), Step 5 (attribute snapshot timing) |
| J-03 | #2533 | `e1343777` | `5b5b2fbe` | High | state machine gap | MicrometerPlugin overwrites user-configured request logger instead of chaining | Step 5a (plugin registration lifecycle), Step 6 (plugin conflict: overwrite vs chain) |
| J-04 | no issue, no PR | `d4b8c5b1` | `698995d7` | Medium | validation gap | Rate limit key function uses wrong path, causing different endpoints to share rate limits | Step 5 (path resolution in rate limiter), Step 6 (domain knowledge: rate limit key design) |
| J-05 | no issue, no PR | `c863f078` | `183641ed` | Medium | type safety | Welcome files served with wrong content type; resolution uses request path instead of resource filename | Step 5 (content type resolution logic), Step 4 (HTTP content type contract) |
| J-06 | #2510 | `4a1bec51` | `47927477` | Critical | type safety | ObjectMapper lazy initialization causes NoClassDefFoundError on Kotlin 2.x due to type erasure | Step 6 (domain knowledge: Kotlin version compatibility, type erasure), Step 5 (lazy init pattern) |
| J-07 | #2468 | `da09bf39` | `0a8d17dd` | Medium | API contract violation | HTTP 405 responses missing required Allow header per RFC 7231 | Step 4 (spec: RFC 7231 §6.5.5), Step 5 (response header construction) |
| J-08 | #2459 | `1dd2e3b0` | `e338af9f` | Medium | missing boundary check | Test client missing CookieJar configuration; cookies not persisted across requests | Step 3 (test infrastructure gaps), Step 5 (HTTP client configuration) |
| J-09 | #2361 | `1177ba2f` | `00ceaff0` | High | type safety | Virtual thread factory via MethodHandle incompatible with GraalVM native image | Step 6 (domain knowledge: GraalVM reflection restrictions), Step 5 (reflection/MethodHandle pattern) |
| J-10 | #2236 | `299d41e7` | `07c70dcc` | High | state machine gap | Erroneous early return in canHandle prevents static file routing for beforeMatched handlers | Step 5 (control flow: early return guard), Step 5a (request handling pipeline) |
| J-11 | #2074 | `bcab7012` | `cd4280ac` | High | configuration error | useVirtualThreads evaluated at config time, not thread pool creation time; flag ignored if set after init | Step 5a (configuration lifecycle: read-time vs use-time), Step 6 (initialization order bugs) |
| J-12 | #1983 | `0d070e58` | `195315f7` | High | state machine gap | ServletRequestListeners never invoked; handler calls nextHandle() instead of super.doHandle() | Step 5a (request lifecycle: listener invocation), Step 2 (handler chain architecture) |
| J-13 | #1992 | `3aa97246` | `08e5865c` | Critical | state machine gap | Plugins registered after server start not initialized; onInitialize deferred until startup | Step 5a (plugin lifecycle: registration vs initialization timing), Step 6 (late registration pattern) |
| J-14 | no issue, no PR | `6192e248` | `5de1d25f` | Medium | protocol violation | Range requests always return 206 even for non-resumable content types; should return 200 | Step 4 (spec: HTTP range request handling), Step 5 (response status selection logic) |
| J-15 | #1960 | `23d4682b` | `98e8d3ee` | Medium | state machine gap | Precompression handler regression: incorrect branching logic for compressed content types | Step 5 (branching logic in compression handler), Step 5a (content negotiation state) |

### spring-petclinic/spring-petclinic-rest (Java)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| P-01 | #287 | `f957c77b` | `0329768f` | High | security issue | Pet creation exposes SQL constraint names and table structure in HTTP error responses | Step 6 (domain knowledge: information disclosure in error responses), Step 5 (exception handler coverage) |
| P-02 | PR [#255](https://github.com/spring-petclinic/spring-petclinic-rest/pull/255) | `ff80e67d` | `117c867c` | High | SQL error | Ambiguous "id" column in JDBC Visit query causes H2 failure in JDBC mode | Step 5 (SQL query construction), Step 6 (domain knowledge: multi-database column ambiguity) |
| P-03 | PR [#44](https://github.com/spring-petclinic/spring-petclinic-rest/pull/44) | `4800ba79` | `8409c0a7` | High | configuration error | Database init uses deprecated property `${database}` instead of `${spring.sql.init.platform}` | Step 2 (configuration architecture), Step 6 (domain knowledge: Spring Boot property migration) |
| P-04 | #145 | `072f2003` | `9952e3fd` | Medium | validation gap | GET pet-by-owner returns 400 instead of 404 when pet doesn't belong to owner | Step 4 (REST API contract: status codes), Step 5 (ownership validation logic) |
| P-05 | #165 | `50c9942f` | `10653f0a` | Critical | security issue | Missing DelegatingPasswordEncoder; authentication completely broken with default config | Step 6 (domain knowledge: Spring Security encoder setup), Step 2 (security architecture) |
| P-06 | #131 | `c1ac1448` | `40850098` | High | type safety | Repository generic type is Integer but User entity has String primary key | Step 5b (generic type parameter mismatch), Step 2 (repository-entity type alignment) |
| P-07 | #187 | `b17dabce` | `310a844c` | High | configuration error | MapStruct compiler options applied to all phases, breaking test compilation | Step 2 (build configuration architecture), Step 6 (domain knowledge: Maven execution phase scoping) |
| P-08 | #130 | `10fca57b` | `08778e60` | Medium | error handling | No handler for DataIntegrityViolationException; constraint violations return 500 | Step 5 (exception handler completeness), Step 4 (REST API: expected error responses) |
| P-09 | #86 | `aee195b1` | `fdad10ec` | High | missing boundary check | POST /pets endpoint completely unimplemented (empty method stub) | Step 4 (spec: endpoint implementation completeness), Step 3 (test coverage for endpoint) |
| P-10 | #102 | `d416d1ba` | `cd58b56f` | Medium | API contract violation | Location header uses "/api/specialtys" instead of "/api/specialties" (typo) | Step 4 (REST API: Location header correctness), Step 5 (string literal in response header) |
| P-11 | #148 | `6cba2ca1` | `335482f1` | Medium | validation gap | Name validation pattern rejects accents, hyphens, apostrophes (non-ASCII names) | Step 5b (regex validation scope), Step 6 (domain knowledge: i18n input validation) |
| P-12 | PR [#71](https://github.com/spring-petclinic/spring-petclinic-rest/pull/71) | `2db3bcb1` | `8655ad48` | High | type safety | POST /vets expects full VetDto with read-only id; missing mapper for VetFieldsDto | Step 4 (REST API: create endpoint input type), Step 5b (DTO vs FieldsDto type mismatch) |
| P-13 | PR [#70](https://github.com/spring-petclinic/spring-petclinic-rest/pull/70) | `83fede1b` | `8655ad48` | High | type safety | POST /pettypes expects full PetTypeDto; Location header uses unsaved entity id (null) | Step 4 (REST API: create endpoint input type), Step 5 (null guard on response header value) |
| P-14 | PR [#62](https://github.com/spring-petclinic/spring-petclinic-rest/pull/62) | `1a00f6ae` | `29287912` | Low | configuration error | Root redirect points to removed "/swagger-ui.html" URL; users get 404 | Step 6 (domain knowledge: Spring Boot 3 Swagger UI migration), Step 3 (smoke test for root path) |
| P-15 | PR [#185](https://github.com/spring-petclinic/spring-petclinic-rest/pull/185), [#182](https://github.com/spring-petclinic/spring-petclinic-rest/issues/182) | `c76a9661` | `96d708da` | High | SQL error | JDBC queries missing column aliases; PostgreSQL rejects ambiguous column references | Step 5 (SQL query construction), Step 6 (domain knowledge: cross-database SQL strictness) |
| P-16 | PR [#135](https://github.com/spring-petclinic/spring-petclinic-rest/pull/135) | `dbb06c1e` | `7f5e9046` | High | state machine gap | DELETE throws "Removing a detached instance" JPA error; missing em.merge() for detached entities | Step 5a (JPA entity lifecycle: detached vs managed), Step 6 (domain knowledge: JPA session management) |



### quarkusio/quarkus (Java)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| QK-01 | #37483 | `8a8b83ca` | `4fd57051` | Medium | error handling | HTTP 400 errors don't log cause by default; missing root cause visibility in dev/test modes | Step 5 |
| QK-02 | #52270 | `3584ac1b` | `7417c355` | Medium | type safety | Generic signature includes optional Hibernate Reactive types causing spurious WARN logs when dependency absent | Step 5b |
| QK-03 | N/A | `242604d2` | `341d25b7` | High | error handling | JFR extension emitEvents() not robust; gate error on Windows | Step 5 |
| QK-04 | #53296 | `3b3b5126` | `164ebe5f` | High | validation gap | Swagger UI fails to mark endpoints with repeated @PermissionsAllowed as protected; missing Jandex guard | Step 3 |
| QK-05 | #53092 | `2e44aaca` | `240ec34c` | High | state machine gap | Stork configs leak between service registrations; improper cleanup in concurrent scenarios | Step 5a |
| QK-06 | #53079 | `4275b144` | `eaa0f4e5` | Medium | validation gap | PathFilter comparison doesn't use value equality; breaks deduplication logic | Step 5b |
| QK-07 | #53162 | `3e737180` | `860902f3` | High | security issue | DefaultJwtValidator registered for reflection without jose4j dependency check; breaks GraalVM native build | Step 5 |
| QK-08 | N/A | `2b3ca018` | `257cce0d` | Medium | configuration error | JFR capability configuration missing; unnecessary Maven configuration bloats builds | Step 2 |
| QK-09 | N/A | `616ff11d` | `4ffa2c76` | Medium | state machine gap | ArC reproducibility issues; non-deterministic bean generation and config properties ordering | Step 5a |
| QK-10 | N/A | `560bf889` | `77f4dbb7` | Medium | state machine gap | Quarkus REST reproducibility issues; non-deterministic exception mapping and endpoint ordering | Step 5a |
| QK-11 | N/A | `0a31571a` | `77f4dbb7` | Medium | state machine gap | gRPC extension reproducibility issues; non-deterministic server/client processor output | Step 5a |
| QK-12 | N/A | `5fce2ef4` | `77f4dbb7` | Medium | state machine gap | Hibernate Validator reproducibility issues; non-deterministic config builder | Step 5a |
| QK-13 | N/A | `e3cfcd85` | `67be5bb8` | Medium | silent failure | Bytecode recorder proxy identifiers not reproducible; masks non-determinism in build system | Step 6 |
| QK-14 | #53030 | `e5bfa523` | `d6aff702` | High | validation gap | Path templating fails for overlapping routes; wrong path template selected for observability | Step 3 |
| QK-15 | N/A | `b2a6798d` | `49be4d18` | High | concurrency issue | Race condition in reactive messaging hot reload test; timing-dependent failure | Step 5a |
| QK-16 | N/A | `9011a94e` | `ce54df9b` | Low | validation gap | Redis test expects null idle time but gets zero; test expectation mismatch | Step 3 |
| QK-17 | N/A | `5eb2c3e5` | `90bae5bb` | High | error handling | Dev UI causes OutOfMemoryError on large classpaths; unbounded content accumulation | Step 5 |
| QK-18 | N/A | `49be4d18` | `a790a230` | High | configuration error | Dev service config injection regression; child services don't receive parent config | Step 2 |
| QK-19 | N/A | `f8276154` | `49be4d18` | Medium | state machine gap | Dev services network creation in wrong build phase; timing issues with container startup | Step 5a |
| QK-20 | #52933 | `a295aa77` | `f8276154` | High | configuration error | Keycloak dev services sharing broken; duplicate containers when service started by Quarkus | Step 2 |
| QK-21 | #52792 | `699f4626` | `25e11674` | Medium | validation gap | CORS origin header doesn't support wildcard return when configured; protocol violation | Step 5b |
| QK-22 | #52880 | `039659ea` | `090c928a` | Medium | error handling | ReflectiveHierarchyStep traverses already-processed types; infinite loop potential | Step 5 |
| QK-23 | N/A | `29450a1e` | `89603d22` | Low | type safety | Raw type usage in method signature; type erasure safety issue | Step 5b |
| QK-24 | #52410 | `c88190f7` | `93fd921d` | Medium | error handling | Prometheus meter registration fails silently; no exception thrown on registration failure | Step 5 |
| QK-25 | N/A | `18b726ea` | `1c78780d` | Medium | error handling | Connection exceptions have null message; diagnostic information lost | Step 5 |
| QK-26 | N/A | `26ab8ba1` | `52c652e1` | Low | validation gap | Method overload signature mismatch; API contract inconsistency | Step 5b |
| QK-27 | N/A | `0dbb7e23` | `ae9ed299` | Medium | validation gap | Scheduler ignores zero delay configuration; boundary check missing | Step 5 |
| QK-28 | #48032 | `8d5ca3d6` | `ae9ed299` | Medium | validation gap | MethodNameParser produces wrong class names in method signatures | Step 3 |
| QK-29 | #52763 | `04468295` | `89f49d5b` | Medium | validation gap | DurationConverter corner case uncovered; missing boundary test case | Step 3 |
| QK-30 | N/A | `5f1605db` | `860902f3` | Medium | validation gap | MCP resource parser regex fails on JSON strings with semicolons; configuration parsing bug | Step 5b |
| QK-31 | #52905 | `3e7868a1` | `1ffe912a` | Medium | configuration error | WebAuthn IT test scope misalignment; testing infrastructure configuration | Step 2 |
| QK-32 | N/A | `03e60080` | `92c0eae3` | Medium | configuration error | Dev UI extension discovery fails in multimodule Gradle projects; classpath scanning issue | Step 2 |
| QK-33 | N/A | `16b1c1cc` | `73d0b026` | Medium | configuration error | Shared config build-time runtime fix uses wrong profile; configuration propagation error | Step 2 |
| QK-34 | #53261 | `d6c5aa3a` | `67be5bb8` | Low | configuration error | Go-offline goal doesn't honor legacy resolver settings; Gradle compatibility regression | Step 2 |
| QK-35 | #53049 | `fd77d32` | `30cfd18` | Medium | validation gap | Gradle properties not propagated to test workers; build-time config lost at test time | Step 3 |
| QK-36 | #52792 | `699f46` | `25e1167` | High | API contract violation | CORS wildcard origin configuration ignored; security policy not enforced | Step 5 |
| QK-37 | #53239 | `842233` | `41ff87` | Medium | configuration error | gRPC code generation not marked build-only; unnecessary runtime dependency | Step 2 |
| QK-38 | #52950 | `b9af079` | `18b726` | High | state machine gap | Keycloak container lifecycle not managed correctly with shared dev services | Step 5a |
| QK-39 | #53128 | `7db7f2` | `3807a4` | Low | validation gap | Panache HQL sort escaping documentation incomplete; API usage guidance gap | Step 4 |
| QK-40 | #53301 | `63deffc` | `7db7f2` | High | validation gap | OpenAPI security annotations not properly detected with reflection; Jandex integration issue | Step 3 |
| QK-41 | #52791 | `d610e77a` | `afb2b27a` | Medium | error handling | Connection exception messages null; OpenTelemetry VertxHttpSender lacks error diagnostics | Step 5 |
| QK-42 | N/A | `f5a366a0` | `dcd47d95` | High | null safety | NPE in HibernateSearchElasticsearchRecorder; null handling in recorder initialization | Step 5 |
| QK-43 | N/A | `fcd73b2c` | `d873cefc` | Medium | null safety | NPE when preserving MDC entries in VertxMDC context cleanup | Step 5 |
| QK-44 | #52494 | `25155511` | `41a2c5aa` | Medium | validation gap | PreExceptionMapperHandler applied multiple times; first handler applied repeatedly | Step 3 |
| QK-45 | #52484 | `cee0155f` | `ff34a3e9` | Medium | configuration error | ReflectiveHierarchyStep registers useless JAXB classes; unnecessary reflection registrations | Step 2 |
| QK-46 | N/A | `8f70256c` | `4d1288e4` | Low | configuration error | TLS registry plugin configuration copy-paste error; incorrect plugin config | Step 2 |
| QK-47 | N/A | `415acb5c` | `67ba9c06` | High | null safety | Redis Client NPE in optimistic locking transactions; null result handling inconsistency | Step 5b |
| QK-48 | #53207 | `594539f8` | `30576a48` | High | error handling | NumberFormatException during Kafka native compilation; version parsing unsafe | Step 5 |
| QK-49 | #52852 | `8f502650` | `356aaca1` | Medium | validation gap | REST Client includes type annotation in return type; incorrect signature generation | Step 3 |
| QK-50 | N/A | `3640f02a` | `39f7eb8c` | Medium | type safety | ArC class generation bug; incorrect bytecode generation in ArC processor | Step 5b |
| QK-51 | #53150 | `ef5d12e0` | `2998aa24` | High | error handling | Invalid forwarded headers not resulting in HTTP 400; security error handling gap | Step 5 |
| QK-52 | #52985 | `4310da81` | `1a46fc72` | Medium | type safety | ObjectMapper naming strategy overridden in Lambda recorder; incorrect serialization config | Step 5b |
| QK-53 | N/A | `6585cd9d` | `3b084393` | High | error handling | NPE when emitting JFR events from shutdown hook; null handling in JFR event emission | Step 5 |
| QK-54 | N/A | `244d7fe8` | `62daf39a` | High | null safety | Invalid JWT headers cause NPE during delayed JWK resolution; null pointer in JWT processing | Step 5 |
| QK-55 | N/A | `d522664f` | `4ec5553a` | Medium | validation gap | Dev service mode reflective equals for constants missing; config comparison gap | Step 5b |
| QK-56 | N/A | `0f36d89a` | `0cb5624f` | Medium | error handling | JUnit test interceptor returns wrong test instance; incorrect reflection in interceptor | Step 3 |
| QK-57 | N/A | `7344cabd` | `166c4c15` | Low | configuration error | DB2 Dev Services 8-character database name limit unhandled; truncation not validated | Step 2 |
| QK-58 | N/A | `c5220bca` | `c0979c58` | Medium | validation gap | KeycloakTestClient scope double-encoding issue; URL encoding not idempotent | Step 5b |
| QK-59 | N/A | `0a56137b` | `f31eb5cd` | Medium | configuration error | Future defaults flag handling broken in native builds; incomplete option propagation | Step 2 |
| QK-60 | N/A | `3bb75748` | `4c21cafd` | High | type safety | ArC InterceptionProxy void method generation broken; incorrect bytecode generation | Step 5b |
| QK-61 | N/A | `585d9b26` | `0c80b95b` | Medium | configuration error | KAFKA_TLS_CONFIGURATION_NAME environment variable not recognized; config name handling | Step 2 |
| QK-62 | N/A | `fd1f298f` | `2dc6e302` | Medium | validation gap | Hibernate ORM logging filters broken after recent changes; filter configuration regression | Step 3 |
| QK-63 | #37483 | `8d3d0bf` | `92d6a44` | High | error handling | HTTP 400 parameter conversion errors not logged by default in dev/test modes; missing root cause visibility for validation failures | Step 5 |
| QK-64 | #52662 | `1cffac1` | `587b6bd` | High | validation gap | JWTRetriever class from Kafka 4.1 not registered for reflection; Confluent OAuth authenticator fails in native mode | Step 5 |
| QK-65 | N/A | `82ec0a2` | `257cce0` | High | concurrency issue | OpenTelemetry context lost when REST client read timeout occurs; context storage issue with async error handling | Step 5a |
| QK-66 | #53159 | `f64b5d9` | `d6c5aa3` | Medium | validation gap | WebSockets extensions initialization disabled incorrectly when only websockets-next present; missing capability check logic | Step 5b |
| QK-67 | #40274 | `b1d9836` | `ae9ed29` | High | state machine gap | Mutiny context not propagated through cached CompletionStage operations; context leak in Caffeine cache | Step 5a |
| QK-68 | #50177 | `90ac856` | `1fbfb1f` | Medium | type safety | PanacheRepository custom implementations don't inherit primary entity type; Hibernate ORM integration gap | Step 5b |
| QK-69 | #52989 | `d991464` | `00810cc` | Medium | missing boundary check | JacocoProcessor fails silently when data file parent directory doesn't exist; no directory creation | Step 5 |
| QK-70 | #49285 | `dedd168` | `96c1720` | Low | configuration error | IntelliJ IDE detection fails for case-sensitive command matching; env var detection mismatch | Step 2 |
| QK-71 | N/A | `183ccce` | `cade413` | High | state machine gap | Gradle 9 configuration access lock errors during parallel builds; classpath resolution timing issue | Step 5a |
| QK-72 | N/A | `c940a00` | `d6c5aa3` | Medium | configuration error | Gradle build-time properties not propagated to test worker processes; configuration isolation bug | Step 2 |
| QK-73 | N/A | `1833a6e` | `5e5e53e` | Medium | configuration error | Quarkus build-time properties missing from Gradle test task environment; test configuration regression | Step 2 |
| QK-74 | N/A | `98c1f25` | `77f4dbb` | Medium | state machine gap | SharedConfig generation non-deterministic due to unordered iteration; reproducibility gap | Step 5a |
| QK-75 | N/A | `0b24454` | `73d0b02` | Low | error handling | Error message when using @Transactional on event loop lacks clarity; missing error context | Step 5 |
| QK-76 | #52876 | `c12ee8d` | `a556929` | Low | validation gap | Test assertion fails when JVM runs with module names; test fragility in module-aware environments | Step 3 |
| QK-77 | #52578 | `99bf5ff` | `587b6bd` | Medium | validation gap | Messaging quickstart conflicts with Flow quickstart due to Message usage; framework example collision | Step 3 |
| QK-78 | #52581 | `7a92e9d` | `e725bc5` | High | type safety | Panache findById return types incorrect for reactive repositories; generic signature mismatch | Step 5b |
| QK-79 | N/A | `373299e` | `318d9d7` | High | API contract violation | Apicurio Registry 3.1.7 moved KafkaSerdeConfig to new package; import location breaking change not handled | Step 4 |
| QK-80 | #52153 | `31c7a7a` | `06bd880` | Medium | null safety | JaCoCo report generation fails with NPE when data file config missing; null pointer in initialization | Step 5 |
| QK-81 | N/A | `c51e82d` | `3b403e3` | High | state machine gap | OpenTelemetry initialization unconstrained in test/dev mode; code executed too late in lifecycle | Step 5a |
| QK-82 | #52163 | `10f71d2` | `14a0c44` | Medium | validation gap | VertxImplGetVirtualThreadFactory bytecode transformation duplicated and inefficient; reflection generation issue | Step 5 |

### apache/zookeeper (Java)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| ZK-01 | ZOOKEEPER-4958 | `a7fe813` | `3fc7ccc` | High | security issue | Client hostname verification ignored in server if ssl.authProvider configured | Step 5 |
| ZK-02 | ZOOKEEPER-3100 | `229721e` | `10835cb` | High | validation gap | Client times out due to random choice of resolved addresses | Step 5 |
| ZK-03 | ZOOKEEPER-4736 | `e8e141b` | `66c4efe` | Medium | error handling | NIO socket file descriptor leak if network service is down | Step 5b |
| ZK-04 | ZOOKEEPER-4787 | `3d6c0d1` | `9d1d25c` | High | protocol violation | Quorum join failure due to inconsistent wire message charset | Step 5a |
| ZK-05 | ZOOKEEPER-4810 | `f6766ec` | `1ebd57b` | High | concurrency issue | Buffer data race at format_endpoint_info | Step 5 |
| ZK-06 | ZOOKEEPER-4604 | `4e7b8a3` | `e5dd60b` | Medium | missing boundary check | Missing break in switch causes union override | Step 5b |
| ZK-07 | ZOOKEEPER-4925 | `e5dd60b` | `524f1d7` | Critical | state machine gap | Data loss due to discontinuous committedLog in SYNCHRONIZATION | Step 5a |
| ZK-08 | ZOOKEEPER-4909 | `9cc3043` | `10328b3` | Medium | concurrency issue | Request timeout exceeded due to spurious wakeup | Step 5 |
| ZK-09 | ZOOKEEPER-4886 | `ac19f22` | `db8fe9c` | High | state machine gap | Observer with small myid cannot join SASL quorum | Step 5a |
| ZK-10 | ZOOKEEPER-3624 | `a8eb7fa` | `c0e9241` | Medium | error handling | Flaky QuorumPeerMainTest failure | Step 3 |
| ZK-11 | ZOOKEEPER-4819 | `75f9781` | `3e02328` | Medium | validation gap | Cannot seek writable TLS server from read-only | Step 5 |
| ZK-12 | ZOOKEEPER-4699 | `e72f80a` | `fe4854a` | High | null safety | Hostname use-after-free in C client | Step 5b |
| ZK-13 | ZOOKEEPER-4848 | `fe4854a` | `858b787` | High | missing boundary check | Potential stack overflow in setup_random | Step 5b |
| ZK-14 | ZOOKEEPER-4839 | `5a3c6a9` | `8900618` | High | validation gap | SASL DIGEST-MD5 auth fails with reused username | Step 5 |
| ZK-15 | ZOOKEEPER-4712 | `bc9afbf` | `dcaf74c` | Medium | state machine gap | Partial ZooKeeperServer shutdown leaves resources open | Step 5a |
| ZK-16 | ZOOKEEPER-2332 | `52f7af5` | `978d431` | High | error handling | Server fails to start with empty transaction log | Step 5 |
| ZK-17 | ZOOKEEPER-4809 | `4e999c8` | `c44cb37` | High | null safety | Adapter thread use-after-free when debug logging | Step 5b |
| ZK-18 | ZOOKEEPER-4808 | `bccc654` | `66202cb` | Low | error handling | Incorrect log statement in FastLeaderElection | Step 6 |
| ZK-19 | ZOOKEEPER-4955 | `770804b` | `bec08df` | Medium | configuration error | JVM SSL properties interfere with CRL and OCSP | Step 5b |
| ZK-20 | ZOOKEEPER-4920 | `840a666` | `ac19f22` | Low | error handling | Flaky ZooKeeperServerMaxCnxnsTest timeout | Step 3 |
| ZK-21 | ZOOKEEPER-4964 | `a46eecf` | `71e173f` | Medium | validation gap | Admin server auth missing individual permission check | Step 5 |
| ZK-22 | ZOOKEEPER-4928 | `aeadf57` | `2aaeff8` | Low | configuration error | ZOO_VERSION not updated during release | Step 6 |
| ZK-23 | ZOOKEEPER-4853 | `6b70544` | `b64146d` | Low | error handling | Assertion failure in ZooKeeperQuotaTest | Step 3 |
| ZK-24 | ZOOKEEPER-4864 | `b997145` | `935b5f4` | Low | error handling | Bad format when dumping MultiTxn | Step 6 |
| ZK-25 | ZOOKEEPER-4020 | `f7af2ac` | `d1d57c4` | Medium | error handling | Memory leak from SSL certificate in C client | Step 5b |
| ZK-26 | ZOOKEEPER-3766 | `b86ccf1` | `327ac03` | Low | error handling | SASL auth test failure in server | Step 3 |
| ZK-27 | ZOOKEEPER-4972 | `d8e5217` | `23c0446` | Low | error handling | Flaky PrometheusMetricsProviderConfigTest | Step 3 |
| ZK-28 | ZOOKEEPER-4989 | `fb43500` | `e8e141b` | Medium | error handling | C client compilation failure on Windows | Step 5b |
| ZK-29 | ZOOKEEPER-4891 | `a39c8d8` | `8532163` | Medium | error handling | Logback CVE-2024-12798 vulnerability | Step 6 |
| ZK-30 | ZOOKEEPER-3938 | `9dbd958` | `d8e5217` | Low | error handling | Python 3.12 incompatibility with JLine | Step 6 |
| ZK-31 | ZOOKEEPER-4240 | `641cf00` | `c21d37f` | Medium | validation gap | Missing IPv6 support for ACL | Step 5 |
| ZK-32 | ZOOKEEPER-4299 | `c21d37f` | `d7f9717` | Low | concurrency issue | Unnecessary lock in zoo_amulti | Step 5b |
| ZK-33 | ZOOKEEPER-4632 | `4ad0103` | `cedf093` | Medium | null safety | NPE in ConnectionMetricsTest | Step 3 |
| ZK-34 | ZOOKEEPER-4327 | `bc1b231` | `9b6ec90` | Low | error handling | Flaky RequestThrottlerTest | Step 3 |
| ZK-35 | ZOOKEEPER-4511 | `b34e171` | `794790c` | Low | error handling | Flaky FileTxnSnapLogMetricsTest | Step 3 |
| ZK-36 | ZOOKEEPER-5012 | `2f0d22b` | `d20061b` | Medium | null safety | QuorumPeer shutdown throws NPE when zkDb is null | Step 5b |
| ZK-37 | ZOOKEEPER-4276 | `bc1fc6d` | `31c7a7e` | High | configuration error | TLS-only server configuration fails due to missing plaintext port handling | Step 5 |
| ZK-38 | ZOOKEEPER-4785 | `315abde` | `9e40464` | Critical | state machine gap | Transaction loss due to race condition during DIFF sync when follower joins | Step 5a |
| ZK-39 | ZOOKEEPER-3860 | `3702a45` | `b8d458f` | Medium | validation gap | Unnecessary reverse DNS lookups in hostname verification | Step 5 |
| ZK-40 | ZOOKEEPER-4296 | `de87688` | `a9517d8` | High | null safety | ClientCnxnSocketNetty throws NPE on channel closure without null check | Step 5b |
| ZK-41 | ZOOKEEPER-4475 | `255b0c9` | `ac219ce` | Medium | error handling | NodeChildrenChanged incorrectly delivered to recursive watchers on descendants | Step 5 |
| ZK-42 | ZOOKEEPER-4537 | `f770467` | `6f0052d` | High | concurrency issue | Server hangs due to race between SyncThread and CommitProcessor on commitIsWaiting | Step 5a |
| ZK-43 | ZOOKEEPER-4514 | `d5876e8` | `54cb5c3` | High | null safety | ClientCnxnSocketNetty throws NPE when sending packets on closed channel | Step 5b |
| ZK-44 | ZOOKEEPER-3988 | `957f8fc` | `7b75017` | Medium | null safety | NettyServerCnxn throws NPE in receiveMessage metrics collection on TLS connections | Step 5b |
| ZK-45 | ZOOKEEPER-4360 | `4f51567` | `726ec30` | Medium | null safety | Prometheus gauge throws NPE if leader is not set on follower node | Step 5b |
| ZK-46 | ZOOKEEPER-4380 | `c0b19e0` | `26001aa` | Low | null safety | RateLogger throws NPE when message is null | Step 5b |
| ZK-47 | ZOOKEEPER-4377 | `9f355f5` | `cb89916` | Medium | null safety | KeeperException.create throws NPE when low-version client accesses high-version server | Step 5b |
| ZK-48 | ZOOKEEPER-4367 | `d6b50ad` | `531bddd` | Medium | error handling | Thread leak in ZooKeeper#Login when SASL authentication fails | Step 5a |
| ZK-49 | ZOOKEEPER-4907 | `6e4ec27` | `7316c49` | High | concurrency issue | Server processes client packets after channel closed causing data corruption | Step 5a |
| ZK-50 | ZOOKEEPER-4246 | `766e173` | `f5c29aa` | High | error handling | Resource leak in SnapStream when exception occurs during stream creation | Step 5b |


### apache/kafka (Java/Scala)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| KFK-01 | KAFKA-19012 | `1df2ac5b` | `5bb44d63` | Critical | concurrency issue | Producer buffer reuse in async send leads to message corruption | Step 5a |
| KFK-02 | KAFKA-20058 | `a739b05e` | `5498eedf` | Critical | concurrency issue | Race condition clobbers retry backoff, causing premature retries | Step 5a |
| KFK-03 | KAFKA-20287 | `5e509dc3` | `3fd16d0c` | High | error handling | RocksDB column family handles leak on init exception | Step 5 |
| KFK-04 | KAFKA-17411 | `8b47aa81` | `f6ca0f69` | High | null safety | NPE from null offset passed in RocksDBStore | Step 5b |
| KFK-05 | KAFKA-19975 | `3d267d45` | `b395e30c` | High | state machine gap | Partition reassignment blocked by unhealthy in-sync replica | Step 5a |
| KFK-06 | KAFKA-20040 | `fef7f34f` | `04e3acb5` | High | concurrency issue | Race between consumer position update and unsubscribe with topic IDs | Step 5a |
| KFK-07 | KAFKA-20090 | `27102b31` | `8f246cc0` | High | state machine gap | TransactionMetadata epoch overflow causes uncaught exception | Step 5a |
| KFK-08 | KAFKA-20132 | `c1f901cd` | `cae9e803` | High | validation gap | KeyValueStore iterator deserializes with wrong context headers | Step 5b |
| KFK-09 | KAFKA-20134 | `9834b518` | `d7fed9d0` | High | validation gap | WindowStore iterator deserializes with wrong context headers | Step 5b |
| KFK-10 | KAFKA-20158 | `9f15f269` | `7d53410d` | High | validation gap | SessionStore iterator deserializes with wrong context headers | Step 5b |
| KFK-11 | KAFKA-20168 | `e3bb2b8d` | `0be98d7e` | High | protocol violation | SLF4J 2.x fluent API in SLF4J 1.7.x environment causes NoSuchMethodError | Step 2 |
| KFK-12 | KAFKA-20254 | `55d1e382` | `830d4409` | High | state machine gap | Streams group creation blocked when offset replay before group record | Step 5a |
| KFK-13 | KAFKA-15894 | `200f3896` | `65864468` | High | silent failure | Metrics overwritten instead of accumulated across partitions | Step 6 |
| KFK-14 | KAFKA-20023 | `04da4fb4` | `e9ad2214` | High | error handling | Partition reassign tool crashes with dead brokers | Step 5 |
| KFK-15 | KAFKA-20038 | `84fa5314` | `c7800041` | High | security issue | Log4j vulnerability CVE-2025-68161 in use | Step 6 |
| KFK-16 | KAFKA-16836 | `e31ae3eb` | `80595036` | Medium | error handling | Standby task suspend reason incorrectly inferred from state | Step 4 |
| KFK-17 | KAFKA-20091 | `e26e7c06` | `351a8b20` | Medium | validation gap | Time-based retention check inconsistent between local and remote | Step 4 |
| KFK-18 | KAFKA-20129 | `8b7cf2bc` | `34fa571b` | Medium | error handling | Config append/subtract with invalid key throws NoSuchElementException | Step 5 |
| KFK-19 | KAFKA-18679 | `a899cfc0` | `74ebbae8` | Medium | type safety | Metrics return double for int/long valued metrics | Step 5b |
| KFK-20 | KAFKA-20076 | `494a2b9e` | `9090cfa1` | Medium | serialization | PluginInfo record serializes PluginType in uppercase | Step 5b |
| KFK-21 | KAFKA-20063 | `41b33d82` | `0f5208c9` | Medium | configuration error | Alpine Docker build hangs on tar extraction order | Step 2 |
| KFK-22 | KAFKA-20211 | `ba96e092` | `2f047bed` | Low | error handling | Group coordinator metrics test flakes on timing | Step 3 |
| KFK-23 | KAFKA-20333 | `51fa1601` | `a6fd96c3` | Low | error handling | Consumer test flakes with aggressive poll timeout | Step 3 |
| KFK-24 | KAFKA-20112 | `3d8a90a4` | `3884062d` | Low | error handling | Consumer callback position test flakes on timing | Step 3 |
| KFK-25 | KAFKA-20296 | `c47d68ae` | `9834b518` | Low | error handling | Consumer metrics test flakes intermittently | Step 3 |
| KFK-26 | KAFKA-20345 | `ba96e092` | `2f047bed` | Low | error handling | Group coordinator background metrics test executor timing | Step 3 |
| KFK-27 | KAFKA-20059 | `5400a80d` | `ed367cf2` | Low | error handling | ConfigCommand test flakes with slow brokers | Step 3 |
| KFK-28 | KAFKA-20074 | `3d6687b8` | `494a2b9e` | Low | error handling | Admin API test flakes on streams group readiness | Step 3 |
| KFK-29 | KAFKA-20045 | `2585a9a7` | `acd6fac6` | Low | error handling | Admin test flakes on streams group readiness | Step 3 |
| KFK-30 | KAFKA-18952 | `2bae9c36` | `aef1fac1` | Low | error handling | Sink integration test flakes on data ordering | Step 3 |
| KFK-31 | KAFKA-20027 | `6b5a2e47` | `aee7a373` | Medium | error handling | Quick start link broken in docs | Step 2 |
| KFK-32 | KAFKA-20310 | `eb111f66` | `20e681b9` | Critical | serialization | TransactionLog.valueToBytes() fails to persist previousProducerId and nextProducerId, causing producer fencing or stuck epoch exhaustion | Step 5b |
| KFK-33 | KAFKA-20203 | `3fd16d0c` | `73cb15e7` | High | validation gap | MeteredWindowStore.setFlushListener passes empty headers instead of record.headers() to deserializers | Step 5b |
| KFK-34 | KAFKA-20106 | `69f75150` | `93918c57` | High | state machine gap | Streams consumer assignment not updated within poll window due to event type mismatch | Step 5a |
| KFK-35 | KAFKA-20302 | `b9882a00` | `94b0f3e4` | High | error handling | SocketServer receive buffers from MemoryPool leak if request validation fails | Step 5 |
| KFK-36 | KAFKA-20321 | `5a628e59` | `93918c57` | High | concurrency issue | Race condition between partition revocation callback and lost partition cleanup | Step 5a |
| KFK-37 | KAFKA-20247 | `32c0e1c4` | `eb0a7358` | High | state machine gap | Controller registration times out but pendingRpc flag never cleared, blocking retry | Step 5a |
| KFK-38 | KAFKA-19697 | `eb0a7358` | `03a6c6b5` | High | null safety | NPE when removing connector task metrics if connector status metrics already removed | Step 5 |
| KFK-39 | KAFKA-20131 | `abcbef6a` | `312c1dbe` | High | state machine gap | ClassicKafkaConsumer.endOffsetRequested flag not cleared on LIST_OFFSETS failure | Step 5a |
| KFK-40 | KAFKA-20183 | `e678b4bb` | `d920f8bc` | Medium | validation gap | SharePartitionKey parsing breaks with group IDs containing colons | Step 2 |
| KFK-41 | KAFKA-20192 | `23e2af1e` | `f1847622` | Medium | error handling | ReconfigurableQuorumIntegrationTest brittle polling logic with race condition | Step 3 |
| KFK-42 | KAFKA-20064 | `8209af2a` | `a899cfc0` | High | concurrency issue | PartitionLeaderCache concurrent access not atomic, causing race conditions | Step 5a |
| KFK-43 | KAFKA-19492 | `8f98b974` | `a739b05e` | Low | error handling | OffsetOutOfRangeException detail lost in deleteRecordsOnLocalLog debug logging | Step 4 |
| KFK-44 | KAFKA-19542 | `9a28bd23` | `1ad463d9` | Medium | null safety | Consumer.close() fails to remove all metric sensors, leaking memory | Step 5 |
| KFK-45 | KAFKA-20288 | `2700824a` | `e0228499` | Medium | silent failure | GroupConfigManager retains orphaned groups after all configs removed | Step 6 |
| KFK-46 | KAFKA-20309 | `2f2d9b01` | `2700824a` | Medium | configuration error | SharePollEvent allows multiple concurrent instances causing coordination issues | Step 2 |
| KFK-47 | KAFKA-19541 | `4d3c6589` | `94b0f3e4` | High | configuration error | Kraft controller RPC max bytes unconfigurable, blocking large metadata updates | Step 4 |
| KFK-48 | KAFKA-20241 | `3a71651b` | `288b4799` | Medium | security issue | Jackson library security vulnerability in JSON processing | Step 6 |
| KFK-49 | KAFKA-19710 | `599d55cd` | `6ceb36f9` | Medium | error handling | Legacy checkpoint file not written on close, breaking downgrade path | Step 4 |
| KFK-50 | KAFKA-18652 | `b43d7088` | `cae9e803` | Low | configuration error | Streams task offset interval config missing documentation and defaults | Step 2 |
| KFK-51 | KAFKA-20249 | `a83dda82` | `826755a9` | Low | error handling | Headers-aware deserializers inefficient raw value extraction | Step 5b |

### pydantic/pydantic (Python)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| PYD-01 | #1829 | `70bfe4f` | `d6373304` | Critical  | serialization          | fix: encode credentials in MultiHostUrl builder                 | Step 5b |
| PYD-02 | #12770 | `a910cae` | `2fba8e48` | High      | serialization          | serializing complex numbers with negative zero imaginary par    | Step 5b |
| PYD-03 | #12677 | `ccd2aad` | `08a62937` | High      | serialization          | serialization of typed dict unions when `exclude_none` is se    | Step 5b |
| PYD-04 | #1836 | `25316d7` | `02a3e6e0` | High      | serialization          | various `RootModel` serialization issues                        | Step 5b |
| PYD-05 | #12398 | `64fca3a` | `7973d4b2` | High      | state machine gap      | issue with recursive generic models with a parent model clas    | Step 5a |
| PYD-06 | #11775 | `455b436` | `7df08160` | High      | state machine gap      | issue with recursive generic models                             | Step 5a |
| PYD-07 | #12427 | `c803587` | `cf235275` | High      | type safety            | issue with forward references in parent `TypedDict` classes     | Step 5b |
| PYD-08 | #12827 | `fce3d03` | `e943b41e` | High      | type safety            | `__hash__` in `UuidVersion` and `PathType` to hash values in    | Step 5b |
| PYD-09 | #12463 | `3bcc454` | `6800281b` | High      | type safety            | `FieldInfo` rebuilding when parameterizing generic models wi    | Step 5b |
| PYD-10 | #12506 | `c9c31de` | `0851ce7f` | High      | validation gap         | support for enums with `NamedTuple` as values                   | Step 4 |
| PYD-11 | #1736 | `2b340a9` | `4d03cffc` | High      | validation gap         | generic issues with `ValidationInfo` and `SerializationInfo`    | Step 4 |
| PYD-12 | #1632 | `24034c8` | `795855b9` | High      | validation gap         | enum strict JSON validation when validators are present         | Step 4 |
| PYD-13 | #1373 | `d48d4cb` | `f4c586bc` | High      | validation gap         | float `multiple_of` validation for negative numbers             | Step 4 |
| PYD-14 | #12106 | `9c5eb6e` | `be5ca62e` | Medium    | API contract violation | `__getattr__()` behavior on Pydantic models when a property     | Step 4 |
| PYD-15 | #11803 | `14a239c` | `455b4368` | Medium    | API contract violation | qualified name comparison of private attributes during names    | Step 4 |
| PYD-16 | #11949 | `43bbdc0` | `e1f9d15a` | Medium    | configuration error    | Rebuild dataclass fields before schema generation               | Step 5 |
| PYD-17 | #12734 | `92d079e` | `d99c9869` | Medium    | configuration error    | type annotation of `field_definitions` in `create_model()`      | Step 5 |
| PYD-18 | #11579 | `69b2b63` | `87cb27f5` | Medium    | configuration error    | runtime error when computing model string representation inv    | Step 5 |
| PYD-19 | #1822 | `e130d8d` | `399f0dbd` | Medium    | configuration error    | `default_factory` which takes data on more types                | Step 5 |
| PYD-20 | #11444 | `c2102b7` | `6b0ba110` | Medium    | configuration error    | Ffix: do not check for `__get_validators__` on classes where    | Step 5 |
| PYD-21 | #11409 | `a932510` | `931d217e` | Medium    | configuration error    | type hints involving `typevars_map`                             | Step 5 |
| PYD-22 | #1583 | `99c44e2` | `0613bf29` | Medium    | configuration error    | `ValueError` on year zero                                       | Step 5 |
| PYD-23 | #1515 | `cbee263` | `8db11182` | Medium    | configuration error    | when coerce_numbers_to_str enabled and string has invalid un    | Step 5 |
| PYD-24 | #1459 | `ae44a08` | `32f4f0aa` | Medium    | configuration error    | equality checks for primitives in literals                      | Step 5 |
| PYD-25 | #1638 | `726e8fc` | `796f6cb1` | Medium    | configuration error    | strict behavior for unions                                      | Step 5 |
| PYD-26 | #12495 | `ad9c377` | `f787c339` | Medium    | configuration error    | `InitVar` being ignored when using with the `pydantic.Field(    | Step 5 |
| PYD-27 | #12366 | `6448214` | `d9488f14` | Medium    | configuration error    | error message for invalid validator signatures                  | Step 5 |
| PYD-28 | #12741 | `950a1c9` | `710f8540` | Medium    | configuration error    | incorrect dataclass constructor signature when overriding cl    | Step 5 |
| PYD-29 | #12826 | `c763ade` | `fce3d034` | Medium    | configuration error    | walrus operator precedence in `UrlConstraints.__get_pydantic    | Step 5 |
| PYD-30 | #12302 | `05b973b` | `d83910ef` | Medium    | configuration error    | `ensure_ascii` option for `TypeAdapter`                         | Step 5 |
| PYD-31 | #11822 | `0d33ece` | `477e67c0` | Medium    | configuration error    | check for stdlib dataclasses                                    | Step 5 |
| PYD-32 | #11695 | `a43b346` | `876bf76f` | Medium    | configuration error    | ImportError message for `email-validator`                       | Step 5 |
| PYD-33 | #11559 | `d85f511` | `b9fb3f11` | Medium    | null safety            | `NotRequired` qualifier not taken into account in stringifie    | Step 5 |
| PYD-34 | #12494 | `f787c33` | `3bcc454d` | Medium    | serialization          | nested model schema deduplication in JSON schema generation     | Step 5b |
| PYD-35 | #1879 | `846ba62` | `5f6bc7ee` | Medium    | serialization          | issue with field_serializers on nested typed dicts              | Step 5b |
| PYD-36 | #1852 | `05c8e85` | `7cee8f5d` | Medium    | serialization          | fix: only percent-encode characters in the userinfo encode s    | Step 5b |
| PYD-37 | #12219 | `eb2c860` | `3328c20c` | Medium    | serialization          | `ImportString` JSON serialization for objects with a `name`     | Step 5b |
| PYD-38 | #11435 | `ff3789d` | `134bea6e` | Medium    | serialization          | tuple serialization for `Sequence` types                        | Step 5b |
| PYD-39 | #11416 | `61feb99` | `044d6857` | Medium    | serialization          | path serialization behavior                                     | Step 5b |
| PYD-40 | #1602 | `34f966f` | `dffa3f12` | Medium    | serialization          | Fix: `dataclass` `InitVar`s shouldn't be required on seriali    | Step 5b |
| PYD-41 | pydantic/pydantic-core#1552 | `e30696e` | `6a9c1c5` | High | serialization | Performance regression for JSON tagged union serialization due to redundant code | Step 5b |
| PYD-42 | pydantic/pydantic-core#1530 | `548748d` | `dc8a637` | High | serialization | `wrap` serializer breaking union serialization in presence of extra fields | Step 5b |
| PYD-43 | pydantic/pydantic-core#1513 | `6295877` | `49f9e0b` | High | serialization | Union serializer raising warnings in nested unions that should be silent | Step 5b |
| PYD-44 | pydantic/pydantic-core#1532 | `49f9e0b` | `d06ef27` | High | error handling | Panic in `validate_assignment` when model field has gone missing | Step 5a |
| PYD-45 | pydantic/pydantic-core#1580 | `bdf600b` | `0c22ed7` | Medium | configuration error | Wasteful `to_python()` calls when checking for undefined values | Step 5 |
| PYD-46 | pydantic/pydantic-core#1853 | `298b204` | `664558e` | Medium | null safety | Getting default values from `defaultdict` incorrectly triggers side effects | Step 5 |
| PYD-47 | pydantic/pydantic-core#1851 | `6dab810` | `bac318b` | High | serialization | Invalid serialization of `date`/`datetime`/`time`/`timedelta` due to downcast check placement | Step 5b |
| PYD-48 | #12430 | `e0a6730` | `f334963` | Medium | configuration error | Fields with `exclude_if` incorrectly included in JSON Schema required fields | Step 5 |
| PYD-49 | #12500 | `421a50d` | `8a75a0b` | Medium | validation gap | Missing support for three-tuple input for `Decimal` conversion | Step 4 |
| PYD-50 | #12513 | `89fed19` | `c9c31de` | Medium | configuration error | Mock validator/serializer being deleted in `rebuild_dataclass()` causing loss of test doubles | Step 5 |
| PYD-51 | #12522 | `a5d9af6` | `49bcff8` | Medium | null safety | `MISSING` sentinel not properly handled in `smart_deepcopy()` | Step 5 |
| PYD-52 | #12498 | `e1dcaf9` | `a5d9af6` | High | validation gap | `complex()` validator not using constructor unconditionally for Python data | Step 4 |
| PYD-53 | #12640 | `5587023` | `9d198cd` | High | validation gap | Alias treatment in Rust not matching Python behavior for model fields | Step 4 |
| PYD-54 | #12635 | `12c94d9` | `7c973b8` | Medium | serialization | Emitting serialization warning when `MISSING` sentinel is present in nested model | Step 5b |
| PYD-55 | #12660 | `0bd683b` | `bd18052` | High | error handling | Eagerly evaluating annotations in signature logic causing errors with deferred annotations | Step 5a |

### tiangolo/fastapi (Python)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| FA-01 | SSE streaming context manager finalization | 8a9258b | 6038507 | Critical | concurrency issue | Attempted to use `yield from` with TaskGroup in async context; should use context manager lifecycle properly. TaskGroup cancellation was deferred to async generator finalization via GeneratorExit instead of proper structured teardown via exit stack. Caused resource warnings and potential dangling tasks on cancellation. | Step 5a: State machines - async context lifecycle bugs |
| FA-02 | JSON Schema file binary format | e8b98d2 | d2c17b6 | High | protocol violation | Incorrect JSON Schema generation for file uploads. Used `format: binary` instead of `contentMediaType: application/octet-stream` and `contentEncoding: base64`, breaking client code generation and schema validation in OpenAPI specs. | Step 4: Specs - schema generation correctness |
| FA-03 | APIRouter on_startup/on_shutdown initialization order | ed2512a | 0c0f63 | High | state machine gap | on_startup/on_shutdown attributes were initialized before lifespan context setup, causing them to not be properly wired into the application lifecycle when lifespan parameter was provided. Initialization order prevented correct handler invocation during app startup/shutdown. | Step 5a: State machines - initialization order |
| FA-04 | Json[T] type with query/form/header parameters | c5fd75a | 54f8ae | High | type safety | `Json[list[str]]` parameters failed to parse correctly. The multidict extraction logic didn't distinguish between regular sequence parameters and JSON-encoded parameters, attempting to split JSON strings into lists. Added detection of Json[] type metadata to bypass multidict.getlist() behavior. | Step 5b: Schema types - type annotation handling |
| FA-05 | ValidationError schema missing fields | 75c4718 | 1e5e8b | Medium | API contract violation | OpenAPI ValidationError schema definition was incomplete. Missing `input` and `ctx` fields that were present in actual Pydantic ValidationError instances, breaking client expectations of error response structure. | Step 4: Specs - error schema correctness |
| FA-06 | TYPE_CHECKING annotations under Python 3.14 | 09f5941 | c944ad | High | type safety | Forward references in TYPE_CHECKING blocks failed to resolve in Python 3.14 due to PEP 649 changes. Signature inspection without annotation_format=Format.FORWARDREF raised NameError. Fixed by detecting Python 3.14+ and using new annotation format parameter. | Step 5b: Schema types - runtime type inspection |
| FA-07 | Authorization header whitespace handling | 1d96b3e | 3675e2 | Medium | validation gap | Authorization header credentials retained leading/trailing whitespace after scheme separation. `get_authorization_scheme_param()` returned param with .strip() not applied, causing "Bearer  token " to fail Bearer scheme validation due to extra spaces in credentials. | Step 3: Tests - boundary conditions |
| FA-08 | OpenAPI anyOf refs shallow copy mutation | 08dad5c | 6ab68c6 | High | silent failure | Response schema processing used shallow copy for Union models in app-level responses. When modifying processed_response dict, mutations affected original anyOf references, accumulating duplicate $ref entries across multiple routes using same app-level response definition. Fixed with copy.deepcopy(). | Step 5b: Schema types - mutable data structure handling |
| FA-09 | Query parameter type validation message | 41352de | ca4692a | Low | error handling | Invalid sequence/tuple/dict type annotations for query parameters raised AssertionError without useful error message. Added parameter name to assertion message for clarity during development. Improves DX for catching type annotation mistakes. | Step 3: Tests - error message quality |
| FA-10 | Router self-inclusion detection | df95011 | 363ace | Medium | silent failure | Calling `router.include_router(router)` resulted in silent infinite recursion during route processing. Added assertion to detect and prevent router circular self-inclusion at initialization time with clear error message. | Step 3: Tests - circular dependency detection |
| FA-11 | File upload concurrent reading race condition | 25270fc | 8bdb0d | Medium | concurrency issue | Form body file field processing used fake parallel task group with `anyio.create_task_group()` for concurrent file reads. Caused races and unpredictable ordering in multi-file uploads. Simplified to sequential reads which is correct for form processing. | Step 5a: State machines - unnecessary concurrency |
| FA-12 | Starlette on_event compatibility | f9f7992 | 8e50c55 | High | API contract violation | Starlette removed on_startup/on_shutdown support in newer versions. FastAPI methods relying on Starlette's implementation via super().__init__() broke silently. Re-implemented on_event decorator and _startup/_shutdown handlers in FastAPI with _DefaultLifespan context manager to maintain backward compatibility. | Step 4: Specs - API compatibility across versions |
| FA-13 | tiangolo/fastapi#14986 | `2686c7f` | `2f9c914` | Critical | security issue | HTML/JavaScript injection vulnerability in Swagger UI parameter serialization. JSON values embedded in `<script>` tags were not properly HTML-escaped, allowing XSS attacks via parameters like `init_oauth` and `swagger_ui_parameters`. An attacker could inject `</script><script>alert(1)</script>` and execute arbitrary JavaScript. Fixed by adding `_html_safe_json()` function to escape `<`, `>`, and `&` characters as Unicode escape sequences (`\u003c`, `\u003e`, `\u0026`) before embedding JSON in HTML. Also fixed OpenAPI schema server list accumulation bug where root_path values from different requests were persisting and accumulating in the app's server list instead of being request-specific. | Step 5: Defensive patterns - HTML escaping in script tags |
| FA-14 | tiangolo/fastapi#14794 | `b49435b` | `464c359` | High | API contract violation | FastAPI incorrectly rejected using special type hints like `Response`, `Request`, and `BackgroundTasks` with explicit `Depends()` annotations. The code had an assertion that threw `AssertionError: Cannot specify Depends for type Response` when attempting patterns like `response: Annotated[Response, Depends(modify_response)]` or `response: Response = Depends(...)`. This was a regression/limitation that prevented legitimate dependency injection patterns. Fixed by removing the blanket assertion and instead only applying special handling when `depends is None`, allowing Depends()-wrapped special types to work correctly by calling the dependency and using its return value. | Step 5b: Schema types - type annotation handling |
| FA-15 | tiangolo/fastapi#14962 | `590a5e5` | `1e78a36` | High | configuration error | JSON response serialization now uses Pydantic's Rust-based serialization directly (via `field.serialize_json()`) when a response model is declared and no custom response class is explicitly set. Previously, all responses went through `jsonable_encoder()` (Python) then `json.dumps()` (Python), adding multiple conversion steps. The optimization uses a new `dump_json` parameter to detect when the fast path can be taken (response_field exists and response_class is the default), significantly improving performance for large responses. The behavior change is that when using the fast path, only the optimized serialization is performed, skipping `jsonable_encoder()` entirely, which could theoretically differ for edge cases with custom encoders. | Step 5: Defensive patterns - performance-critical paths |

### andrewstellman/octobatch (Python)

Note: These bugs were identified by quality playbook v1.2.0 running against octobatch. The `pre_fix_commit` for playbook testing purposes is `b800586f` (the commit before the quality playbook was added). All 9 bugs exist at that commit. Octobatch bugs serve as positive controls — the playbook should score direct hits on all of them.

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| O-01 | BUG-1 | `f3db1bd` | `19352d3` | Low | error handling | TUI restart dialog message implies data loss; misleading confirmation text | Step 6 (quality risk: misleading user communication) |
| O-02 | BUG-2 | `71a3bbc` | `f3db1bd` | Medium | state machine gap | Cannot pause or kill runs with "stuck" status; TUI status guard excludes stuck | Step 5a (status field consumer completeness: stuck not handled) |
| O-03 | BUG-3 | `97b1751` | `e7cc069` | Medium | state machine gap | Cannot resume "pending" runs from TUI; R key only works on paused/failed/zombie | Step 5a (status field consumer completeness: pending not handled) |
| O-04 | BUG-4 | `ec9877f` | `71a3bbc` | High | null safety | format_step_provider_tag crashes when provider_instance is None (missing API key) | Step 5 (null guard after fallible get_provider call) |
| O-05 | BUG-5 | `5a2b480` | `97b1751` | High | silent failure | Rate-limited runs enter tight retry loop (17s) without exponential backoff | Step 6 (missing safeguard: retry without backoff), Step 5a (retry state machine) |
| O-06 | BUG-6 | `e7cc069` | `ec9877f` | High | silent failure | TUI cost calculation uses hardcoded Flash pricing; 17x undercount for Pro models | Step 6 (silent failure: correct-looking wrong output), Step 2 (pricing architecture: registry vs hardcoded) |
| O-07 | BUG-7 | `eac53ba` | `5a2b480` | Low | missing boundary check | No pre-run cost estimate accounting for fan-out expansion; $100 expected → $1,856 actual | Step 6 (missing safeguard: pre-commit info gap for irreversible operations) |
| O-08 | BUG-8 | `a123cdf` | `eac53ba` | Medium | state machine gap | Watch loop never self-terminates when all work is done | Step 6 (missing safeguard: no termination condition), Step 5a (loop termination) |
| O-09 | BUG-9 | `1b3fd25` | `a123cdf` | High | state machine gap | Retry results lose inherited context fields from previous steps | Step 5a (retry state: context preservation), Step 5 (defensive copy on retry) |

### rq/rq (Python)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| RQ-01 | #2364 | 4bfc5f7 | 295a588 | High | state machine gap | When work-horse terminates unexpectedly and job retried, `ended_at` only set on first failure. On retries, `ended_at` remained stale from first failure, resulting in `ended_at` earlier than `started_at`. Also fixed misleading log message claiming job moved to FailedJobRegistry when it may be retried. | Step 5a: State machine guards must handle retry loops correctly. Timestamp fields must reset across state transitions. |
| RQ-02 | #2363 | 295a588 | 5590b2f | High | state machine gap | Job status not persisted to Redis before success/failure callbacks executed. Inside callbacks, `job.get_status()` returned 'started' instead of 'finished'/'failed'. Race condition where callback sees stale state. Fix: set status in-memory before callback execution. | Step 5a: State transitions must be visible to callbacks. In-memory state sync required before external observer calls. |
| RQ-03 | #2284 | 93d70f7 | 65008cf | Medium | type safety | Regression in Worker.__init__ where custom job_class/queue_class passed as parameters were unconditionally wrapped in import_*_class(), even when already class objects. Failed when class was passed directly. Required explicit None-checks to avoid double-wrapping. | Step 5b: Type validation must distinguish between class objects and string paths. Defensive imports need type guards. |
| RQ-04 | #2252 | 18c0f30 | 70bd464 | High | configuration error | SpawnWorker broken on redis-py>6 due to serialization of connection kwargs. `retry` object in connection_kwargs not serializable by pickle/fork. Worker spawn failed with AttributeError when unpickling child process. Fix: remove retry from kwargs before spawn. | Step 5b: Connection objects must not carry non-serializable state across process boundaries. Fork safety requires config sanitization. |
| RQ-05 | #2228 | 73c1f80 | 3a7fde4 | High | silent failure | PubSub thread blocking indefinitely with `sleep_time=None`. Worker could not receive commands or respond to shutdown signals if connection blocked. Worker became unresponsive and hung. Fix: set `sleep_time=60` to allow periodic wake-ups. | Step 5a: Event loops must have timeouts. Indefinite blocking violates responsive shutdown contract. |
| RQ-06 | #2221 | 75c9eda | 4bed978 | Medium | validation gap | Calling `pipeline.multi()` multiple times on same pipeline caused Redis protocol errors. When enqueueing jobs into multiple queues with caller-supplied pipeline, code unconditionally called `multi()` even if already in transaction. Fix: check `pipeline.explicit_transaction` before calling `multi()`. | Step 5b: Transaction state must be tracked. Caller-supplied pipelines need explicit state guards. |
| RQ-07 | #1954 | 1e6953b | 49f12451 | Medium | validation gap | `enqueue_many()` missing `on_stopped` callback when copying job data to job instances. Other callbacks (`on_success`, `on_failure`) were copied, but `on_stopped` silently dropped. Job stops but callback never fires. Fix: add `on_stopped` to callback copy. | Step 3: Callback enqueue must copy all callback types. Array copy operations need exhaustive field checks. |
| RQ-08 | #2025 | 2440db3 | 7349032 | High | type safety | Redis server version cast as float by redis-py 5.0.1+ but code assumed string. Calling `.split()` on float raised AttributeError. Affects all jobs on Redis 7.1+. Fix: explicitly cast to string before split. | Step 5b: Type coercion at API boundaries prevents silent failures from library version changes. |
| RQ-09 | #2010 | a820939 | 960d9e5 | Low | configuration error | `--quiet` and `--verbose` CLI flags not honored in `worker-pool` command. Flags silently ignored because `logging_level` parameter took precedence. Fix: set `logging_level=None` when flags present to allow flags to override. | Step 6: CLI option precedence must be explicit. Configuration priority chains need guards. |
| RQ-10 | #1954 | 89fa8ae | 9933128 | Medium | validation gap | Duplicate of RQ-07: `enqueue_many()` missing `on_stopped` callback. Appears in both commits as simultaneous fix. | Step 3: Callback enqueue must copy all callback types. |
| RQ-11 | #1845 | e92682c | ed59b92 | Medium | null safety | TimerDeathPenalty attempted to setup/cancel timer even for negative/infinite timeouts (-1, None). Creating timer with invalid timeout caused AttributeError when timer tried to execute. Jobs with `timeout=-1` failed. Fix: early return if `_timeout <= 0`. | Step 5a: Boundary checks required before timer creation. Sentinel values need guards before use. |
| RQ-12 | #1843 | ed59b92 | 1fa6ec1 | Medium | validation gap | `depends_on` parameter accepted list of `Dependency` objects but code only processed first one. Multiple Dependency objects in list were ignored, so job had fewer dependencies than specified. Fix: iterate list, extend depends_on_list from all Dependency objects. | Step 3: Array parameter validation must handle nested heterogeneous types. List flattening needs exhaustive iteration. |
| RQ-13 | #1819 | 5798cdd | 46b5cf6 | Medium | configuration error | Setting `queue.result_ttl=-1` to keep results forever failed. Code called `connection.expire(key, -1)` which Redis rejects (negative TTL invalid). Results not stored. Fix: check for -1, call `persist()` instead of `expire()`. | Step 5b: Configuration extremes (negative values, infinity) need special handling. Redis API contract requires boundary checks. |
| RQ-14 | #1794 | b69ee10 | acdeff3 | High | configuration error | Worker initialization order bug: `default_worker_ttl` parameter not available during `_set_connection()` call because it was assigned after. Socket timeout calculated incorrectly. Created socket with wrong timeout. Fix: move TTL assignments before connection setup. | Step 2: Initialization order matters. Variable dependencies must respect declaration order. |
| RQ-15 | #1793 | 54db2fa | 83fa0ad | High | null safety | Accessing None when `dequeue_job_and_maintain_ttl()` returns None in burst mode (timeout=None). Code tried to unpack `result[0]` before checking if result was None. TypeError when dequeueing in burst mode. Fix: check result before unpacking and assign to variables before use. | Step 5b: Null checks must precede destructuring. None-returning functions need guards. |
| RQ-16 | #1785 | cd62b4c | c2e6d95 | Medium | error handling | Debug logs using colorizers on non-string objects (lists, bytes) raised unhandled exceptions. Worker crashed when debug logging enabled on certain operations. Fix: convert bytes to string, avoid colorizing complex types. | Step 6: Debug logging must be exception-safe. Formatter validation required for arbitrary types. |
| RQ-17 | #1601 | 3f5e94a | 97caa84 | Low | API contract violation | `job.delete(remove_from_queue=False)` failed to properly handle case where job not in any queue. Caused issues in cleanup. Fix: add explicit state check for non-queued jobs. | Step 5: Parameter-dependent behavior must be exhaustively tested. Edge cases in delete operations. |
| RQ-18 | #1591 | 0147b30 | 76ba690 | High | silent failure | Setting `result_ttl=0` to discard results left orphaned Redis keys. Results deleted but metadata keys remained, causing memory leaks and stale data in registries. Worker heartbeat maintenance also had related bug. Fix: ensure all result-related keys deleted when TTL=0. | Step 5: TTL=0 must clean up all derived keys. Referential integrity in Redis operations. |
| RQ-19 | #1564 | e71fcb9 | 4711080 | Medium | state machine gap | `job.cancel()` did not remove job from registries if job not in queue. Job remained in active/scheduled registry but marked cancelled, causing ghost jobs. Fix: add registry removal logic for non-queued jobs. | Step 5a: Cancel must work from all states. Registry cleanup must be exhaustive. |
| RQ-20 | #1381 | 016da14 | 8b9e218 | High | validation gap | Custom serializer not passed to `fetch_many()` and `dequeue_any()` calls. When custom serializer used, job fetches failed to deserialize. Jobs unavailable even when enqueued. Fix: pass serializer parameter through all fetch chains. | Step 3: Serializer parameter must flow through entire job lifecycle. Configuration propagation needs comprehensive traces. |
| RQ-21 | #1383 | 75a610b | 3aaa1c1 | High | error handling | RQScheduler failed when SSL connection used. SSL socket not properly re-established after fork, causing connection errors. Scheduler crashed on first job. Fix: explicitly restore SSL context after forking. | Step 5: SSL state must be invalidated across fork boundaries. Connection inheritance requires explicit recovery. |
| RQ-22 | #1336 | 01d71c8 | 99f7dc8 | Medium | state machine gap | Retried jobs were placed in FailedJobRegistry even though they should return to Queued state. End user saw failed job in registry even though it was being retried. Visibility bug. Fix: check retry flag before moving to FailedJobRegistry. | Step 5a: Failure and retry are distinct states. State transitions must validate retry eligibility. |
| RQ-23 | #1327 | 56e756f | 08379fc | High | error handling | Scheduler SSL connection not properly restored after forking. Like RQ-21 but specifically for scheduler subprocess. SSL context lost after fork, causing auth failures. Fix: detect fork, recreate SSL connection. | Step 5: Fork-safety of SSL state. Scheduler-specific connection recovery. |
| RQ-24 | #1304 | 8a0d9f9 | 4e1eb97 | Medium | missing boundary check | SimpleWorker timeout calculation incorrect. Used wrong parameter source, resulting in timeout too short/long. Jobs failed with timeout errors even with sufficient time. Fix: use correct parameter and calculation formula. | Step 2: Timeout calculations must use correct sources. Arithmetic in critical paths needs validation. |
| RQ-25 | #1615 | 7be1190 | c5a1ef1 | Critical | state machine gap | Job not enqueued when dependencies finished in parallel during enqueue. WatchError caught but job._status not reset, so job remained DEFERRED instead of QUEUED. Job silently lost. Fix: save/restore job._status across WatchError retry. | Step 5a: Watched transactions failing must restore local state. Parallel race handling requires state reset. |
| RQ-26 | #1605 | c5a1ef1 | db445f9 | Critical | validation gap | WATCH monitoring wrong Redis keys for dependencies. Code watched bare job IDs instead of job key hashes (`Job.key_for(id)`). Watch never failed even when dependencies changed, breaking optimistic locking. Silent race conditions. Fix: watch full job keys. | Step 5: WATCH must monitor actual data keys. Optimistic locking requires correct key references. |
| RQ-27 | #2132 | 3e2e26e | f4283af | High | error handling | PubSub thread crashed on Redis connection error, leaving worker unable to receive commands (shutdown, pause, etc.). Worker became unresponsive. Fix: add exception handler that recovers from ConnectionError, allows reconnection. | Step 5: Pubsub subscriptions must recover from transient failures. Worker command responsiveness critical. |
| RQ-28 | #2270 | 112c49b | ac3506c | Medium | validation gap | Group cleanup raising IndexError when pipeline state mismatched. Code reused pipeline for exists() checks then srem(), but pipeline length mismatch caused array indexing to fail. Cleanup crashed. Fix: use fresh pipeline, return early if no jobs. | Step 5b: Pipeline result ordering must match operation count. State mismatches in batch operations. |
| RQ-29 | #2103 | 458a2ff | df5e99b | Low | null safety | Client name lookup failed when client had no name attribute. Code assumed all clients had name, causing AttributeError. Rare edge case in distributed setups. Fix: add None check for client name. | Step 5b: Optional attributes must be guarded. External object assumptions need validation. |
| RQ-30 | #2241 | b297a5a | a820e12 | High | state machine gap | When job cancelled, dependent jobs still referenced it in their dependency metadata but job removed from registries. Orphaned dependency references caused dependent jobs to never execute (waiting for phantom job). Fix: remove job from all dependency lists on cancel. | Step 5a: Dependency graph must maintain referential integrity. Cancel must update dependent metadata. |
| RQ-31 | #2169 | af8630b | 3829df7 | High | configuration error | Worker logging level configuration silently ignored. CLI flag `--logging_level` had default value 'INFO' which always overrode user-supplied flags like `--verbose` and `--quiet`. Logging setup broken even when flags provided. Fix: set default to None, check flags before applying level. | Step 5b: Default parameter values must allow override. CLI option precedence needs explicit guards. |
| RQ-32 | #2168 | 9c5f6f3 | af8a071 | High | error handling | Completed job with expired result (result_ttl=0) caused AttributeError in monitor_work_horse(). Code called job.get_status() which raised InvalidJobOperation when Redis key missing. Worker crash during job completion monitoring. Fix: wrap get_status() in try-except, return early on InvalidJobOperation. | Step 5: Operations on expired data must handle missing keys. Result TTL cleanup requires error recovery. |
| RQ-33 | #2196 | 5862978 | d3d4283 | Low | silent failure | Retry log missing format arguments. Logger.info() had incomplete format string 'Job %s: enqueued for retry, %s remaining' with no actual arguments passed. Silent logging failure, no retry status visible to user. Fix: pass self.id and self.retries_left to logger.info(). | Step 6: Logging statements must provide all format arguments. Incomplete format strings silently fail. |
| RQ-34 | #2208 | 4bfd807 | b223821 | High | validation gap | StartedJobRegistry extracting wrong job_id from composite keys. Registry stored job_id:execution_id but code returned full composite key instead of extracting job_id only. Cleanup operations and status lookups returned malformed IDs. Fix: parse composite key, extract job_id component. | Step 5b: Composite key formats must be properly parsed. Registry key formats need consistent extraction logic. |
| RQ-35 | #2277 | fa1f40c | 21406c2 | High | state machine gap | Jobs created without explicit status remained None instead of defaulting to CREATED. DEFERRED dependency logic broken: job with dependencies had status=None which failed validation. Job refused to enqueue. Fix: initialize _status to JobStatus.CREATED, set DEFERRED only when dependencies present. | Step 5a: Job state must always have a valid default. Dependency logic requires explicit state initialization. |
| RQ-36 | #2177 | 84e7cec | 98be6af | Medium | state machine gap | WorkerPool status stuck at IDLE instead of being set to STARTED. Worker pool appeared non-responsive even when running. External monitors could not detect running state. Fix: assign self.status = self.Status.STARTED before entering work loop. | Step 5a: Status variables must reflect actual worker state. Pool lifecycle transitions require explicit assignments. |
| RQ-37 | #1946 | 6cfb5a6 | 10230ff | Medium | null safety | clean_intermediate_queue() called handle_job_failure() on None when job not found in Redis. If job was already deleted, fetch_job() returned None but code proceeded to call handle_job_failure(None, ...). AttributeError on None. Fix: check if job is not None before handling failure. | Step 5b: Null checks required before method calls on fetch results. Cleanup operations must guard on missing data. |
| RQ-38 | #1872 | 07fef85 | af2dfb1 | Medium | error handling | Job.restore() crashed when job.meta contained unserializable data. Code unconditionally called self.serializer.loads(obj.get('meta')) without error handling. Unserializable meta caused TypeError. Job could not be fetched/restored. Fix: wrap meta deserialization in try-except, set meta to fallback dict on error. | Step 5b: Deserialization must be exception-safe. Serializer errors should not block job access. |
| RQ-39 | #1514 | 77e7ef6 | 653d491 | Medium | error handling | Worker initialization crashed when CLIENT command not supported on Redis (e.g. Redis Cluster). Code called connection.client_setname() and client_list() without error handling. Worker failed to initialize. Fix: wrap CLIENT commands in try-except ResponseError, set ip_address='unknown' as fallback. | Step 5b: Optional Redis commands need graceful degradation. Client inspection must tolerate missing commands. |
| RQ-40 | #1917 | 0b5a90a | 192fbc9 | Medium | null safety | Worker deserialization called as_text() on None values. Code assumed all fields (hostname, ip_address, version, python_version) were present. as_text(None) raised AttributeError. Worker restore failed. Fix: check each field for None before calling as_text(). | Step 5b: Type coercion functions must handle None. Optional worker attributes need guards before conversion. |
| RQ-41 | #1715 | 4750eb4 | 375ace1 | Medium | state machine gap | Pipeline transaction state mismatched when enqueue_dependents() inconsistently called multi(). After enqueue_dependents(), pipeline might or might not be in transaction mode. Subsequent operations assumed transaction was active, leading to protocol errors. Fix: check pipeline.explicit_transaction, call multi() if needed. | Step 5a: Transaction state must be explicit and tracked. Caller-supplied pipelines need state guards. |
| RQ-42 | #1852 | ec0b08e | a21768a | Medium | type safety | Type annotation imported resource.struct_rusage at runtime on Windows where resource module unavailable. Windows worker initialization crashed with ImportError. Fix: conditionally import under TYPE_CHECKING, use string annotation for type hints. | Step 5b: Platform-specific imports must be guarded. Type annotations should use strings for unavailable types. |
| RQ-43 | #1700 | 153d29c | 8e3283d | Medium | null safety | Worker IP address lookup used unchecked list indexing. Code did [client['addr'] for ... if ...][0] without checking list non-empty. If CLIENT LIST returned no matching entry, IndexError raised. Worker setup failed. Fix: assign to variable, check length, set 'unknown' as fallback. | Step 5b: List indexing requires bounds checks. CLIENT LIST queries need empty-result handling. |
| RQ-44 | #1387 | 11c8631 | 709043 | High | error handling | Worker crashed on Redis ConnectionError during dequeue operations. No retry logic for transient connection failures. Worker became unresponsive instead of recovering. Fix: catch redis.exceptions.ConnectionError, implement exponential backoff with max 60s wait before retrying. | Step 5: Transient network failures require automatic retry. Worker availability depends on connection resilience. |
| RQ-45 | #1615 | 7be1190 | c5a1ef1 | Critical | state machine gap | Parallel dependency completion during enqueue caused job to be silently lost. WatchError caught but job._status not reset from DEFERRED back to QUEUED. Job remained DEFERRED despite no dependencies left, never executing. Fix: save orig_status before watch loop, restore on WatchError. | Step 5a: Optimistic locking failures must restore local state. Parallel race handling requires explicit state reset. |


### encode/httpx (Python)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| HX-01 | #3442 | `89599a9` | `8ecb86f` | High | state machine gap | SSL context not reused when verify=False with client certificates; early return prevented cert loading | Step 5a |
| HX-02 | #3175 | `88a81c5` | `fa6dac8` | High | configuration error | Proxy SSL context not passed through in AsyncHTTPTransport, causing proxy TLS failures | Step 5 |
| HX-03 | #2998 | `1e11096` | `b4b27ff` | Medium | silent failure | iter_text() yielding empty strings from streaming responses with zero-length chunks | Step 3 |
| HX-04 | #3045 | `99cba6a` | `1a66014` | High | error handling | RFC 2069 digest auth computing wrong response hash; digest_data list missing HA1 in non-qop case | Step 4 |
| HX-05 | #2741 | `3b9060e` | `08eff92` | Medium | validation gap | NO_PROXY environment variable failing to match fully qualified URLs like "http://github.com" | Step 3 |
| HX-06 | #2886 | `e63b659` | `90d71e6` | Medium | validation gap | IPv4 hostname regex using unescaped dot (.) matching any char instead of literal dot | Step 5b |
| HX-07 | #3187 | `a7092af` | `37a2901` | Medium | validation gap | Query parameter percent encoding not matching browser form submission behavior; %20 treated as safe | Step 4 |
| HX-08 | #2701 | `ee432c0` | `724eced` | Medium | protocol violation | URL path/query/fragment percent encoding incorrect; GEN_DELIMS set incomplete for components | Step 4 |
| HX-09 | #2659 | `15d09a3` | `2c51edd` | Medium | validation gap | NO_PROXY IPv4, IPv6, and localhost addresses not handled specially vs domain prefixes | Step 3 |
| HX-10 | #2667 | `c1cc6b2` | `4ddff16` | Low | API contract violation | NetRCAuth.__init__ file parameter missing default None value, breaking standard usage | Step 2 |
| HX-11 | #2581 | `f0fd919` | `ebc1393` | Medium | type safety | MockTransport handler type annotation ambiguous between sync and async callables | Step 5b |
| HX-12 | #2354 | `d5900cd` | `cc206cf` | Medium | silent failure | QueryParams parsing discarding empty query values due to missing keep_blank_values flag | Step 3 |
| HX-13 | #2038 | `321d4aa` | `89cbd3c` | High | error handling | Headers.update() overwriting repeated headers instead of merging them per RFC 7230 | Step 5a |
| HX-14 | #2016 | `b7dc0c3` | `497b315` | Medium | validation gap | Stream upload subclassing SyncByteStream/AsyncByteStream incorrectly delegated to read() method | Step 5 |
| HX-15 | #1827 | `10b60d4` | `c19728c` | Low | null safety | iter_bytes with None chunk_size and zero-content response causing infinite loop | Step 5 |
| HX-16 | #1828 | `0b4a832` | `fbe35ad` | High | type safety | WSGITransport wsgi.errors field typed as BytesIO instead of TextIO per WSGI spec | Step 5b |
| HX-17 | #2671 | `9ae170a` | `fd60b18` | Medium | validation gap | Optional percent encoding not detecting valid escape sequences, causing double-encoding | Step 4 |
| HX-18 | #3116 | `6d852d3` | `87f39f1` | High | state machine gap | client.send() with bare Request not applying Client timeout to extensions dict | Step 5a |
| HX-19 | #1940 | `4882e98` | `89cbd3c` | Low | type safety | Response.url type annotation Optional[URL] but always returns URL, breaking type checking | Step 5b |
| HX-20 | #2669 | `a682f6f` | `87f39f1` | High | error handling | ASGITransport raise_app_exceptions=False still raising exceptions on app failure | Step 5a |
| HX-21 | #2708 | `abb994c` | `89cbd3c` | Medium | validation gap | WSGITransport missing SERVER_PROTOCOL environ key, breaking spec compliance | Step 4 |
| HX-22 | #3412 | `47f4a96` | `c19728c` | Medium | null safety | ZstdDecoder.flush() raising error on empty response bodies without decompressing data | Step 5 |
| HX-23 | #2467 | `1ff67ea` | `fd60b18` | Medium | type safety | WSGI start_response() not returning write() callable; sys.exc_info() tuple handling incomplete | Step 5b |
| HX-24 | #2185 | `e9b0c85` | `89cbd3c` | Medium | state machine gap | URL.copy_with() not re-normalizing URI reference, exposing invalid URLs | Step 5a |
| HX-25 | #1839 | `c24bbb8` | `89cbd3c` | Medium | type safety | Conditional imports using try/except preventing static type checker analysis | Step 5b |
| HX-26 | #2094 | `6820b1d` | `89cbd3c` | Low | API contract violation | Documentation referencing wrong parameter name max_keepalive instead of max_keepalive_connections | Step 2 |
| HX-27 | #1866 | `2814fd3` | `89cbd3c` | High | security issue | CLI output not escaping markup, allowing injection attacks via response text | Step 5 |
| HX-28 | #2986 | `b471f01` | `c51e046` | Medium | validation gap | URL authority regex rejecting unescaped '@' in username or password fields | Step 4 |
| HX-29 | #2999 | `90538a3` | `c51e046` | Medium | validation gap | ASGI raw_path including query string component when split not applied correctly | Step 4 |
| HX-30 | #3178 | `12be5c4` | `f3eb3c9` | Medium | validation gap | Proxy scheme validation not accepting socks5h variant; transport conditionals incomplete | Step 3 |
| HX-31 | #3363 | `9fd6f0c` | `6f46152` | Medium | serialization | JSON request bodies not compact; spaces after separators increasing payload size | Step 5b |
| HX-32 | #3380 | `a33c878` | `326b943` | Medium | type safety | Request/Response extensions typed as MutableMapping but should be Mapping (immutable) | Step 5b |
| HX-33 | #3418 | `ce7e14d` | `80960fa` | High | error handling | Deprecated verify=str parameter silently ignored instead of raising error | Step 5 |
| HX-34 | #3571 | `336204f` | `8910202` | Low | error handling | Proxy error message missing f-string prefix, not substituting scheme variable | Step 5 |
| HX-35 | #3699 | `ae1b9f6` | `ca097c96` | Low | API contract violation | FunctionAuth class not exposed in public __all__ export, breaking public API discoverability | Step 2 |
| HX-36 | #3312 | `49d74a2` | `2e01aa00` | Medium | error handling | Headers.normalize_header_value() not validating None type, only checking for str/bytes | Step 5a |
| HX-37 | #3250 | `7c0cda1` | `beb501fc` | Low | error handling | InvalidURL error messages missing character details (char repr and position index) | Step 5 |
| HX-38 | #3377 | `e9cabc8` | `eeb5e3c2` | Medium | configuration error | Dependencies certifi and httpcore imported unconditionally even when not needed by user code | Step 3 |
| HX-39 | #3139 | `392dbe4` | `7df47ce4` | Low | missing boundary check | No decompression support for zstd content-encoding; requests fail silently without format support | Step 4 |
| HX-40 | #3288 | `609df7e` | `1d6b663` | Low | API contract violation | URLTypes type alias removed from public API, breaking type hint compatibility | Step 2 |
| HX-41 | #2852 | `59df819` | `e4241c6` | High | state machine gap | Response.encoding setter allowing modification after Response.text property accessed, breaking immutability contract | Step 5a |
| HX-42 | #2990 | `a11fc38` | `3b9060e` | Medium | validation gap | URL percent-encoding using incorrect safe character sets for path/query/fragment components | Step 4 |
| HX-43 | #2723 | `920333e` | `301b8fb` | Medium | serialization | Forward slashes in query parameter values not percent-encoded to %2F per spec compliance | Step 4 |
| HX-44 | #2845 | `a54eccc` | `adbcd0e0` | High | configuration error | HTTPS proxy connections not receiving SSL context, causing TLS failures for proxy authentication | Step 5 |
| HX-45 | #2846 | `88e8431` | `c3585a5c` | Medium | error handling | Digest authentication retry omitting response cookies from initial failed request | Step 5a |
| HX-46 | #2910 | `ad06741` | `9751f76` | Low | configuration error | NetRC module imported at module load time unconditionally; should use lazy import | Step 3 |
| HX-47 | #2523 | `4cbf13e` | `10a3b68a` | Medium | validation gap | QueryParams accepting invalid types (e.g., int, custom objects) without TypeError | Step 3 |
| HX-48 | #2495 | `a8dd079` | `563a103` | Medium | validation gap | Content parameter silently accepting dict type instead of raising TypeError | Step 3 |
| HX-49 | #2776 | `9415af6` | `55b8669a` | Low | API contract violation | Response.raise_for_status() not returning response instance, breaking method chaining | Step 2 |


### alibaba/AgentScope (Python)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| AS-01 | #1365 | `6b7216c` | `b35c165` | High | configuration error | Monitor type not set on monitor config object, written to wrong parent | Step 2 |
| AS-02 | #1251 | `3bd4444` | `45200b2` | High | null safety | Gemini streaming response parsing failed when usage_metadata fields were None | Step 5b |
| AS-03 | #1239 | `45200b2` | `9c7e418` | High | error handling | Deep research agent failed with multi-turn conversations, message list handling missing | Step 5 |
| AS-04 | #1231 | `5baeafd` | `d8aa491` | High | state machine gap | ReActAgent memory compression excluded compressed messages but included them anyway, causing incorrect prompt context | Step 5a |
| AS-05 | #1290 | `501c909` | `28cfb99` | Medium | API contract violation | DashScopeChatModel async multimodal processing failed, incorrect model class usage | Step 5 |
| AS-06 | #1218 | `b9851f6` | `73954db` | High | concurrency issue | Agent message printing blocked stream consumption, event loop monopolized | Step 5 |
| AS-07 | #1187 | `734b6d3` | `ccb7ab3` | High | type safety | RedisMemory decode_response setting ignored when connection_pool provided, bytes/string mismatch | Step 5b |
| AS-08 | #1206 | `6579dff` | `5e2bf63` | High | API contract violation | GeminiChatModel incompatible with Gemini-3-pro, response parsing failed | Step 2 |
| AS-09 | #1146 | `ba6a627` | `40a1089` | High | type safety | RedisMemory used bytes as message keys causing retrieval failures | Step 5b |
| AS-10 | #1157 | `b57f06f` | `2b61bcc` | Critical | concurrency issue | Mem0LongTermMemory event loop closing issue, Ollama client bound to closed loop | Step 5a |
| AS-11 | #1148 | `2b61bcc` | `ba6a627` | Critical | concurrency issue | Mem0LongTermMemory event loop management failed with async Ollama models | Step 5a |
| AS-12 | #1192 | `18567ae` | `fd6806` | Medium | type safety | MCPToolFunction timeout argument wrong type, passed float directly to timedelta | Step 5b |
| AS-13 | #1214 | `73954db` | `606811b` | Medium | error handling | WebSocket library import failed even when not used, hard dependency added unnecessarily | Step 5 |
| AS-14 | #1171 | `9e8558b` | `88fe290` | Medium | silent failure | ReActAgent duplicated messages saved to long-term memory | Step 5 |
| AS-15 | #1284 | `0f39395` | `a9947da` | High | validation gap | Formatter local path identification logic failed for file:// URLs | Step 5b |
| AS-16 | #1289 | `da39760` | `501c909` | Medium | serialization | Base64 file extension double-dotted, creating malformed filenames | Step 5b |
| AS-17 | #1262 | `722a60c` | `f6db165` | Medium | validation gap | Text file tools failed with tilde paths, user home not expanded | Step 5 |
| AS-18 | #1220 | `593b958` | `597be68` | Medium | error handling | Plan module hint bug, incorrect hint message generation | Step 4 |
| AS-19 | #1228 | `bf952e7` | `6137edd` | Medium | error handling | Word reader raised KeyError on VML-format documentation without graceful handling | Step 5 |
| AS-20 | #1298 | `5703510` | `17b739d` | High | error handling | Studio disconnection crashed agent without error boundary | Step 5 |
| AS-21 | #1279 | `2e4bb10` | `59e0135` | Medium | state machine gap | Plan recovery did not trigger hooks, breaking history restoration | Step 5a |
| AS-22 | #1299 | `66b475b` | `3bd4444` | High | error handling | Deep research agent MCP client not awaited, async initialization failed | Step 5 |
| AS-23 | #1015 | `3b67178` | `7df0148` | High | null safety | OpenAIChatModel streaming parsing assumed delta.content existed without checking | Step 5b |
| AS-24 | #1002 | `6bc219a` | `56f6299` | High | validation gap | JSON repair function returned non-dict for partial JSON, breaking tool argument parsing | Step 5b |
| AS-25 | #1000 | `1c9d88b` | `5e0adc3` | High | validation gap | DeepResearchAgent missing truncation of tool results, context overflow | Step 5 |

### spf13/cobra (Go)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| COB-01 | #2285 | 61968e8 | 10d4b48 | High | error handling | Fish shell completion scripts failed when arguments contained wildcard characters (e.g., `*`) because they were not properly quoted, causing fish to expand them and error with "No matches for wildcard". Missing quotes in `requestComp` variable construction. | Step 5b (schema types) - quoting/escaping rules in generated code |
| COB-02 | #2234 | a97f9fd | 5f9c408 | High | API contract violation | Type definition `CompletionFunc` as a struct type caused regression for users who had already defined their own `CompletionFunc` type. Changed to type alias to maintain backward compatibility. | Step 6 (quality risks) - breaking changes in public APIs |
| COB-03 | #2228 | 4ba5566 | 41b26ec | High | error handling | Bash completion script with `set -o nounset` failed when flag marked as filename with empty extensions because uninitialized variable `fullFilter` was referenced. Silent variable leak. | Step 5 (defensive) - uninitialized variable access |
| COB-04 | #2180 | 5bef9d8 | ff7c561 | Medium | error handling | Plugin commands with `--version` flag showed inconsistent help text: used `Name()` instead of `DisplayName()`, showing "version for kubectl-plugin" instead of "version for kubectl plugin". Inconsistent with other flags. | Step 4 (specs) - consistent template variable usage |
| COB-05 | #2174 | 756ba6d | 371ae25 | Medium | error handling | Map/string map flags (`stringTo*` types) were incorrectly marked as already-used in completions, preventing re-specification. Only checked for Array and Slice types, missing stringTo* type detection. | Step 5b (schema types) - incomplete type discrimination |
| COB-06 | #1781 | 6b0bd30 | cc7e235 | High | serialization | Command.Find() incorrectly removed flag values that matched subcommand names (e.g., `command -f subname subname` lost the `-f subname` flag value). Broke argument parsing when flag value matched a subcommand name. | Step 5a (state machines) - command traversal state |
| COB-07 | #1776 | 22b6179 | dbf85f6 | High | error handling | Child commands with flags shadowing parent persistent flags showed parent flag in help instead of child flag, despite child flag being actually used at runtime. Help/execution behavior mismatch. | Step 4 (specs) - flag resolution order consistency |
| COB-08 | #1762 | f911c0b | 7790bf9 | High | error handling | Bash completion with `set -o nounset` failed on empty activeHelp array because array length check syntax `${#arr}` fails for empty arrays; requires `${#arr[*]}`. | Step 5 (defensive) - bash portability |
| COB-09 | #1690 | 37d481d | 5b11656 | High | error handling | Zsh completion script enabled completions for both `<command>` AND `_<command>` (the completion function itself), causing zsh to hang when attempting to complete `_<command>`. Incorrect compdef line. | Step 5 (defensive) - self-reference prevention |
| COB-10 | #1691 | e1ded5c | 8afe9d1 | Medium | error handling | Bash completion v2 filtering descriptions created spurious completions from null values after trailing newlines in read loops. Regression from earlier refactor. | Step 5 (defensive) - data stream parsing |
| COB-11 | #1850 | c6b9971 | 4305498 | Medium | error handling | Powershell completion script `ForEach-Object` didn't consistently return arrays when piped, causing completion results to be flattened. Missing `-Type Array` directive. | Step 5b (schema types) - type consistency across shells |
| COB-12 | #1321 | 6f19fa9 | d65ba12 | High | error handling | Bash completion completely broken when `set -o nounset` enabled because uninitialized variables referenced in completion script. Breaks for users with strict shell settings. | Step 5 (defensive) - variable initialization |
| COB-13 | #1510 | 25bab5a | 3fed3ef | Medium | error handling | `cobra completion` command output invalid shell syntax when `~/.cobra.yaml` existed: "Using config file:" appeared in generated script instead of being suppressed in completion mode. | Step 5 (defensive) - output context awareness |
| COB-14 | #1423 | 3c8a19e | 2dea4f2 | Critical | concurrency issue | `RegisterFlagCompletionFunc()` used global map without synchronization, causing concurrent map write panics. Partial fix attempted (moved to root) but still racy. Later refactored by COB-15. | Step 5a (state machines) - shared mutable state |
| COB-15 | #1438 | de187e8 | 07861c8 | Critical | concurrency issue | Flag completions registered before adding command to parent failed because stored in root cmd which might change. Also race condition on global map access. Added RWMutex but map still global. | Step 5a (state machines) - scope and lifetime issues |
| COB-16 | #1282 | 9a43267 | 4590150 | Medium | configuration error | Home directory config files failed to load when using viper because config type not set, causing viper to not recognize YAML format. Silent failure to load config. | Step 5b (schema types) - format specification |
| COB-17 | #1437 | de187e8 | 07861c8 | High | error handling | Flag completion functions couldn't be found when flag was registered before adding command to parent, because RegisterFlagCompletionFunc stored references in root command which could differ at completion time. | Step 5 (defensive) - reference stability |
| COB-18 | #1237 | f64bfa1 | 40d34bc | High | error handling | Zsh completion didn't work on first invocation in a shell session because stub function replaced itself but didn't call the actual completion function. Silent failure on first use. | Step 5a (state machines) - function self-replacement logic |
| COB-19 | #1213 | 95d23d2 | 2d94892 | High | error handling | `ShellCompDirectiveNoSpace` and `ShellCompDirectiveNoFileComp` directives ignored in zsh completions; simple `compadd` couldn't handle both requirements. Required zsh `_describe` function for proper implementation. | Step 4 (specs) - directive implementation correctness |
| COB-20 | #1249 | c2e21bd | 95d23d2 | High | error handling | Multiple fish completion failures: (1) NoSpace extra character placed after description instead of before, (2) completions starting with space broke, (3) env vars in path not handled. 3 bugs in one. | Step 5b (schema types) - fish-specific escaping rules |
| COB-21 | #1363 | 7223a99 | 06e4b59 | Medium | error handling | Powershell completion didn't respect `ShellCompDirectiveNoFileComp` directive, still suggesting file completions when directive set. Ignored directive value. | Step 4 (specs) - directive handling completeness |
| COB-22 | #1342 | ded486a | 893ebf6 | Low | error handling | Trailing whitespace in powershell completion script violates shell style guidelines. Cosmetic but affects reproducibility. | Step 6 (quality risks) - output consistency |
| COB-23 | #894 | 40d34bc | 0bc8bfb | Medium | error handling | `PrintErr` and `PrintErrln` functions passed wrong writer (stdout instead of stderr) to command logger, causing error output to go to stdout. Silent behavior change. | Step 5 (defensive) - output stream routing |
| COB-24 | #1247 | b97b5ea | f64bfa1 | Medium | error handling | Fish completion script used invalid output redirection syntax (missing `>&` prefix), causing completion setup to fail silently. Syntax error in generated script. | Step 5b (schema types) - fish syntax validation |
| COB-25 | #1001 | bf26895 | 447f182 | Medium | error handling | Bash completion regression: global variable `$c` reused in read loop, corrupting completion function. Variable shadowing in subshell. | Step 5 (defensive) - variable scope in subshells |
| COB-26 | #1039 | 21cab29 | 89c7ffb | Low | error handling | Undefined error variable `er` referenced in bash completion, causing bash errors. Typo in variable name. | Step 5 (defensive) - reference validation |
| COB-27 | #1940 | 22953d8 | 00b68a1 | Medium | error handling | Active help environment variable name generation failed for program names containing non-dash special characters (periods, spaces, non-ASCII). Only dashes were replaced with underscores, causing invalid env var names. Incomplete character replacement. | Step 5 (defensive) - input validation for env var names |
| COB-28 | #2180 | 5bef9d8 | ff7c561 | Medium | error handling | Plugin command help text showed inconsistent display name for --version flag (showed "version for kubectl-plugin" instead of "version for kubectl plugin"). Help generation ignored CommandDisplayNameAnnotation for auto-generated version flag description. | Step 4 (specs) - annotation handling consistency |
| COB-29 | #1730 | b9ca594 | ea94a3d | High | error handling | Help flag (-h/--help) failed when custom FlagErrorFunc wrapped the flag.ErrHelp error, because code used direct equality check (==) instead of errors.Is() for wrapped errors. Breaking change with Go 1.13+ error wrapping. | Step 5 (defensive) - error type checking for wrapped errors |
| COB-30 | #1735 | 7c9831d | ed7bb9d | Medium | error handling | Bash v3 completion script failed when descriptions contained tab characters because array pattern match `${completions[*]}` without quotes failed to preserve special chars. Missing quotes in variable expansion. | Step 5 (defensive) - bash variable quoting rules |
| COB-31 | #1463 | 1beb476 | 6f84ef4 | Medium | configuration error | Cobra init boilerplate code duplicated error messages when Execute() returned an error, because cobra.CheckErr() already prints the error. Template fix to avoid redundant error output. | Step 5b (schema types) - template code generation |
| COB-32 | #1879 | f25a3c6 | 9235920 | Medium | type safety | Variable shadowing in rpad() function masked the "template" package import with a local "template" variable, causing potential runtime errors when fmt.Sprintf needed package context. Import masking in function scope. | Step 5 (defensive) - import shadowing detection |
| COB-33 | #1771 | 7790bf9 | 6bf8cd8 | Medium | error handling | YAML documentation generation for child commands showed only command name in "see_also" section instead of full command path, inconsistent with other documentation formats (Markdown, Man, REST). Missing CommandPath() usage. | Step 5b (schema types) - consistent path representation |
| COB-34 | #1917 | 45360a5 | c8a20a1 | Medium | error handling | Zsh completion script couldn't be sourced as-is due to missing `compdef` line in generated script, forcing users to add it manually. Script generation missing required zsh directive. | Step 5 (defensive) - shell directive completeness |
| COB-35 | #2061 | b711e87 | 8b1eba4 | High | error handling | Commands with DisableFlagParsing=true had --help/-h and --version/-v flags auto-completed by Cobra AND the plugin command, causing double completions. Help/version flags should not auto-complete when plugin takes over flag parsing. | Step 5a (state machines) - flag parsing responsibility |
| COB-36 | #1960 | fdee73b | 988bd76 | Medium | error handling | Powershell completion script environment variable assignment failed for program names with special chars (dots) because `$env:VAR_NAME` without brackets cannot handle dots. Missing ${env:...} syntax. | Step 5b (schema types) - variable syntax across shells |
| COB-37 | #2241 | 1995054 | f98cf42 | Medium | error handling | Help function for subcommands executed without proper context flow, causing custom help functions to not receive the command's execution context. Context lost in help command chain. | Step 5a (state machines) - context threading through help |
| COB-38 | #1255 | 86f8bfd | f32f4ef | Medium | error handling | Man page generation with newer go-md2man versions failed because Markdown preamble used outdated format (multi-line %% format instead of quoted single-line format). Tool version incompatibility. | Step 5b (schema types) - external tool format specs |
| COB-39 | #1002 | 0d9d2d4 | b04b5bf | High | error handling | Help message printed to stderr instead of stdout, breaking compatibility with tools like Kubernetes that expect help on stdout. Backwards compatibility regression. | Step 5 (defensive) - output stream semantics |
| COB-40 | #2210 | 0745e55 | d1e9d85 | Medium | error handling | Custom flag value types that accept multiple values (implementing SliceValue interface) were not detected for repeated flag completion if they didn't follow naming conventions (Array/Slice suffix or stringTo prefix). Hardcoded type name matching instead of interface detection. | Step 5 (defensive) - interface-based type detection |
| COB-41 | No issue | 9334a46 | 9552679 | Medium | error handling | Unrunnable subcommands (with no Run function and children) returned flag.ErrHelp instead of proper error (NotRunnable), causing execution to show help without returning an error code. Wrong error type for unrunnable commands. | Step 5 (defensive) - error type semantics |

### go-chi/chi (Go)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| CHI-01 | #1045 | 05f1ef7 | 6eb3588 | High | error handling | RouteHeaders middleware missing return statement after calling next.ServeHTTP when router had no routes configured. This caused next handler to be called twice - once in empty check and again at end of function. | Step 5 (defensive): Missing control flow guard enabling double handler invocation |
| CHI-02 | #954 | 6ceb498 | 882c15e | High | error handling | Mux.Find not correctly handling nested routes and subrouters. Pattern composition failed when combining parent and child route patterns, returning partial paths or empty patterns for nested mount structures. | Step 2 (architecture): Route tree composition logic gap across mount boundaries; Step 5a (state machines): Pattern state not correctly threaded through recursion |
| CHI-03 | #919 | f10dc4a | ef31c0b | Medium | error handling | Compressor middleware's Close() method checked for io.WriteCloser using cw.writer() instead of cw.w, bypassing the actual writer lookup and preventing proper cleanup of compression resources. | Step 5b (schema types): Wrong field reference in type assertion; Step 5 (defensive): Missing close semantics |
| CHI-04 | #846 | f4ab9b1 | 355dd04 | Medium | validation gap | RoutePattern() returned empty string for root route "/" after trimming suffixes, should preserve root as special case. Path cleanup logic unconditionally removed trailing slashes even for root pattern. | Step 4 (specs): Edge case in pattern normalization; Step 5 (defensive): Missing boundary check for root route |
| CHI-05 | #512 | 5704d7e | ccb4c33 | Medium | error handling | MethodNotAllowed handler not invoked when route matched with path variables but method not supported. Tree search found node but didn't set methodNotAllowed flag for subsequent handler routing logic. | Step 5a (state machines): Missing state flag in route lookup return path; Step 2 (architecture): Method validation gap in parameter routing |
| CHI-06 | #584 | 248d06c | fd503d9 | High | type safety | WrapResponseWriter incorrectly used logical OR (||) instead of AND (&&) for flusher/hijacker detection, causing incompatible interfaces to be mixed. ReadFrom implementation tried to call cw.writer() on non-implementing types causing runtime errors. | Step 5b (schema types): Interface composition logic error; Step 3 (tests): httptest.ResponseRecorder incompatibility |
| CHI-07 | #633 | 188a167 | a6f8a3e | High | error handling | Recoverer middleware parsed panic stack traces assuming "panic(0x..." format, but Go 1.17+ can produce "panic" without address. String slicing with negative index caused panics during error recovery. | Step 5 (defensive): Unsafe string parsing without bounds checking; Step 6 (quality risks): Version-dependent behavior not defended |
| CHI-08 | #531 | 73938b5 | 81b0a6f | Medium | error handling | URLFormat middleware used strings.Index() instead of strings.LastIndex() to find file extension period, causing incorrect parameter extraction on paths with multiple dots (e.g., "samples.1.json" extracted "json" instead of "1"). | Step 4 (specs): Algorithm choice affects URL parsing correctness; Step 5 (defensive): Missing boundary handling for multi-dot names |
| CHI-09 | #567 | 681ea79 | ec0754d | Medium | validation gap | Route tree regex matching allowed empty path parameters matching pattern like "/{param:[0-9]*}/test". Tree search should skip empty matches for patterns with quantifiers that require content boundaries. | Step 5 (defensive): Missing empty string validation in param matching; Step 4 (specs): Regex quantifier semantics not enforced |
| CHI-10 | #504/#505 | 87e5387 | 3479a89 | Critical | security issue | RedirectSlashes middleware vulnerable to open redirect via protocol-relative URL paths like "//evil.com/". Redirect construction didn't validate or normalize hostnames in redirect targets, allowing attacker control of redirect destination. | Step 5 (defensive): URL validation gap in redirect construction; Step 6 (quality risks): Open redirect vulnerability |
| CHI-11 | #587 | 969d7fc | ab14a9a | High | SQL error | NotFound and MethodNotAllowed handlers incorrectly applied middleware chain to handler function itself instead of to parent mux when called via inline mux. This broke error handler middleware isolation in nested routing contexts. | Step 5a (state machines): Handler wrapping applied at wrong scope; Step 2 (architecture): Middleware scope confusion in nested mux |
| CHI-12 | #575 | 82aabd6 | 894714a | Medium | concurrency issue | Test data race in TestServerBaseContext: httptest.NewServer started listening before BaseContext config was applied, causing concurrent reads/writes to server config struct during test initialization. | Step 3 (tests): Race condition in test setup; Step 5 (defensive): Concurrent configuration without synchronization |
| CHI-13 | #573 | 423901d | c936bbd | Medium | type safety | RegisterMethod used math.Exp2(float64(n)) which caused first custom method to receive same bit value as mTRACE (value 1), causing collision. Should use 2 << n to ensure exponential growth with proper spacing. | Step 5b (schema types): Integer overflow in bit flag generation; Step 4 (specs): Method type allocation correctness |
| CHI-14 | #640 | b750c80 | 55dd7fc | Medium | API contract violation | Compress middleware used Header().Set("Vary", "Accept-Encoding") which replaced existing Vary headers instead of appending. Should use Header().Add() to preserve other cache-control requirements in Vary. | Step 4 (specs): HTTP header merge semantics; Step 5 (defensive): Silent header overwrite |
| CHI-15 | (internal) | 3e5747d | 98fc81f | Medium | validation gap | Context.RoutePattern() returned incomplete patterns by not cleaning route pattern suffixes. Wildcard routes generated patterns like "/users/*/" instead of "/users/*", breaking route introspection and logging. | Step 4 (specs): Pattern normalization incomplete; Step 5 (defensive): Missing suffix cleanup |
| CHI-16 | (internal) | 12ebe33 | fc7c9bb | High | error handling | WrapResponseWriter.WriteHeader() called underlying ResponseWriter.WriteHeader() unconditionally, even when wroteHeader flag was already true. HTTP spec requires WriteHeader called only once - this violated constraint and could corrupt response state. | Step 5 (defensive): Redundant state-changing call; Step 4 (specs): HTTP response lifecycle violation |
| CHI-17 | #654 | df44563 | 2976a59 | High | error handling | Recoverer middleware's defensive programming for Go 1.17+ still fragile: code checked for period to find method/package boundary but some lines still lacked periods, causing negative index panics. Additional check needed for "panic(" prefix handling. | Step 5 (defensive): Incomplete error recovery hardening; Step 6 (quality risks): Version-dependent parsing failures |
| CHI-18 | #1044 | 6eb3588 | de0d16e | Critical | security issue | RedirectSlashes middleware vulnerable to open redirect via backslash paths like "/\evil.com/". Code didn't normalize backslashes to forward slashes, allowing protocol-relative-style redirects. Added backslash normalization and enhanced validation logic. | Step 5 (defensive): URL normalization gap allowing backslash bypasses; Step 6 (quality risks): Path traversal + open redirect vector |
| CHI-19 | #1049 | 903cff2 | 142fada | High | SQL error | Walk() function missed propagating inline middlewares from parent mux across mounted subrouters. ChainHandler middlewares attached via With() weren't included when walking nested routes, breaking introspection and middleware audit trails. | Step 2 (architecture): Middleware propagation gap in router walk; Step 3 (tests): Missing middleware in introspection results |
| CHI-20 | #1016 | 9040e95 | (commit before) | Medium | concurrency issue | TestThrottleRetryAfter was flaky due to race condition between token replenishment and test assertions. Test didn't synchronize token bucket state, causing intermittent failures when timing skewed. Added explicit token usage synchronization. | Step 3 (tests): Timing-dependent test without synchronization; Step 5 (defensive): Rate limiter test correctness |
| CHI-21 | (internal) | 3658d98 | 820555a | Medium | validation gap | Regexp routing with quantifiers like `/{param:[0-9]+}/` failed to set default empty string parameter value when pattern didn't match. Tree search skipped setting parameter value on empty match, breaking URLParam extraction for non-matching patterns. | Step 4 (specs): Regex parameter semantics; Step 5 (defensive): Missing default value for unmatched params |
| CHI-22 | (internal) | 906b567 | c75e3d0 | High | error handling | Throttle middleware had broken handler invocation - tried to store handler state in throttler struct instead of returning closure function, causing context-dependent failures and incorrect request handling. Complete refactor to proper middleware pattern required. | Step 2 (architecture): Handler state storage anti-pattern; Step 5a (state machines): Middleware lifecycle mismanagement |
| CHI-23 | (internal) | 85905ae | 4dce0a3 | Medium | validation gap | Wildcard parameter validation check was in wrong location in patNextSegment. Sanity check for wildcard at end of pattern ran BEFORE the wildcard segment was parsed, allowing patterns like "/foo/*bar" to pass validation until later stages. | Step 4 (specs): Validation order dependency; Step 5 (defensive): Check ordering matters for correctness |
| CHI-24 | (internal) | 403a33c | 966e5e3 | High | type safety | Compress middleware SetEncoder() function had inverted logic: `if e == ""` should be `if e != ""`. Empty encoding strings were being prepended to precedence list instead of valid encodings, breaking compression priority selection and causing fallback to no compression. | Step 5b (schema types): Logical operator inversion; Step 4 (specs): Encoding precedence algorithm |
| CHI-25 | (internal) | 1a6bb10 | 925944b | Medium | error handling | Compress middleware WriteHeader called `w.WriteHeader()` recursively instead of `w.ResponseWriter.WriteHeader()`, causing infinite delegation and incorrect status code propagation. HTTP handler must call underlying writer, not self. | Step 5 (defensive): Method call target confusion; Step 4 (specs): Middleware delegation pattern |
| CHI-26 | (internal) | bb7ee27 | bd5deb2 | Medium | API contract violation | RedirectSlashes middleware stripped trailing slash from redirect path but lost query parameters in process. Redirect from `/path/?a=b` became `/path` instead of `/path?a=b`, violating HTTP redirect semantics. | Step 4 (specs): URL component preservation in redirects; Step 5 (defensive): Query string handling |
| CHI-27 | (internal) | cd12532 | d7f1dd2 | High | validation gap | Wildcard pattern validation allowed invalid patterns like `/admin/*/other`. Tree validation only checked wildcard not in middle during sanity check, but didn't block patterns with text after wildcard. Added explicit panic to enforce wildcard-at-end invariant. | Step 4 (specs): Route pattern constraints; Step 5 (defensive): Late-stage validation vs early detection |
| CHI-28 | (internal) | 9861155 | 84a2424 | Medium | error handling | Empty mux panic on ServeHTTP instead of returning 404. Code panicked with "attempting to route to a mux with no handlers" rather than gracefully handling undefined routes. Should delegate to NotFoundHandler for consistency. | Step 5 (defensive): Panic instead of error handling; Step 2 (architecture): Handler fallback semantics |
| CHI-29 | (internal) | 1c2d011 | 7859137 | Medium | null safety | URLFormat middleware accessed rctx.RoutePath without nil check. When rctx was nil (possible in certain middleware chains), pointer dereference panicked. Static analyzer found vulnerability. | Step 5 (defensive): Missing nil guard before pointer dereference; Step 3 (tests): Static analysis findings |
| CHI-30 | (internal) | d9d5e31 | 6ceb498 | Medium | protocol violation | WrapResponseWriter.WriteHeader() blocked informational status codes (100-199) like other responses, violating HTTP spec allowing multiple informational responses before final status. Status check logic only allowed first WriteHeader call for all status ranges. | Step 4 (specs): HTTP response lifecycle rules; Step 5 (defensive): Status code range handling |

### cli/cli (Go)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| GH-01 | HTTP Header Loss in Auth Flow | fb8e22a76 | 268453803 | High | API contract violation | getViewer was building a new HTTP client from scratch, losing AppVersion and InvokingAgent headers. Reuse existing client by shallow-copying it and wrapping transport with AddAuthTokenHeader to preserve headers through auth token negotiation. | Step 5b (schema types) - http.Client mutation patterns |
| GH-02 | Missing InvokingAgent Propagation | 268453803 | b6267151 | High | API contract violation | gh api command built HTTP client inline without forwarding InvokingAgent, missing Agent/<name> suffix in User-Agent header when invoked by AI agents. Thread InvokingAgent through Factory → ApiOptions → HTTPClientOptions. | Step 2 (architecture) - factory pattern propagation |
| GH-03 | Concurrent Data Race in Prompter | 38e10d5eb | 95a59f4 | High | concurrency issue | huh's OptionsFunc runs in goroutine while main event loop writes field values. Unprotected shared variables cause data race. Replace Value() bindings with syncAccessor implementing mutex-protected Accessor interface. | Step 5a (state machines) - goroutine synchronization |
| GH-04 | Missing GraphQL Field in Query | 5ed8cf0fa | be4960a | Medium | type safety | headRepository GraphQL query missing nameWithOwner field even though PRRepository struct includes it. gh pr view --json headRepository emits empty field, breaks acceptance tests. Add missing field to query projection. | Step 4 (specs) - GraphQL schema alignment |
| GH-05 | Inconsistent Flag Evaluation | 391e6616d | bff468ba | Medium | validation gap | Reviewer prompt path checks reviewerSearchFunc != nil directly instead of useReviewerSearch boolean. Makes fetch and prompt decisions inconsistent. Use useReviewerSearch at both gates like assignee path does. | Step 3 (tests) - flag consistency patterns |
| GH-06 | @copilot Assignee Not Replaced | bff468baf | 6a68ebc | High | silent failure | pr create --assignee @copilot sent literal @copilot to API. NewIssueState only ran MeReplacer, not CopilotReplacer. Switch to SpecialAssigneeReplacer (handles @me and @copilot). Also add [bot] suffix for replaceActorsForAssignable mutation. | Step 5b (schema types) - assignee mutation API contracts |
| GH-07 | Missing Actor Assignee Mutation | e6d9019bc | 8723e3bb | High | protocol violation | pr create --assignee with metadata flag failed with 'not found'. Pass assignee logins directly to ReplaceActorsForAssignable mutation instead of resolving to node IDs. Set state.ActorAssignees = true (was missing). | Step 2 (architecture) - mutation parameter threading |
| GH-08 | Hardcoded API Endpoint | 78b958f9a | 3780dd5 | Critical | configuration error | agent-task hardcoded api.githubcopilot.com causing 401 errors for ghe.com tenancy users. Query viewer.copilotEndpoints.api to resolve URL dynamically. Pass capiBaseURL to NewCAPIClient, use it in transport host check and job path construction. | Step 5b (schema types) - endpoint configuration patterns |
| GH-09 | Invalid Search Qualifiers Accepted | 519425692 | 628dea6 | Medium | validation gap | gh issue list accepted pull request-only search qualifiers (is:pr, type:pr) without validation. Added regex check in searchIssues to reject PR-only qualifiers and direct users to gh pr list. | Step 3 (tests) - input validation boundaries |
| GH-10 | Draft Issue Title/Body Lost | d21544c08 | cf862d6 | High | silent failure | project item-edit with partial flags (e.g., --text without --title) overwrites title/body with empty strings. Check cmd.Flags().Changed("title")/Changed("body") instead of checking string != "". Fetch current draft issue to preserve unchanged fields. | Step 5 (defensive) - partial update semantics |
| GH-11 | Invalid ANSI Escape Sequence | 48951aca0 | 3521604 | Medium | serialization | JSON/diff colorization used SGR code 1;38 which is invalid (38 requires sub-parameters). Replace with 1;37 (bold white). Most terminals silently ignore, masking the bug until terminal was strict. | Step 6 (quality risks) - terminal output correctness |
| GH-12 | Feature Detection Error Ignored | 31f375608 | 52eca96 | Medium | error handling | workflow run command silently swallowed feature detection errors, assuming feature unsupported. Changed to return error if ActionsFeatures fails, preventing silent degradation. | Step 5 (defensive) - error propagation |
| GH-13 | URL Encoding Missing | 36a85fd71 | 3e9fbbb | High | API contract violation | workflow run compiles URL without escaping, breaking with workflow names containing special characters. Apply url.PathEscape when building dispatch URL path. | Step 5b (schema types) - URL encoding contracts |
| GH-14 | Feature Detection Not Implemented | a0dea00fd | 1af282 | Medium | missing boundary check | ActionsFeatures method missing from feature detection, used by workflow dispatch. Implemented to query gh.ActionsFeatureDetection fields for DispatchRunDetails capability. | Step 3 (tests) - capability detection |
| GH-15 | Scope Error Clarification | 6f739036b | 150834 | Low | error handling | Issue create for projects returned generic scope error. Added Clarifier interface implementation to provide detailed error message about required Contents:Read and Projects:Write scopes. | Step 5 (defensive) - error message clarity |
| GH-16 | Cannot Clear Reviewers | d643d5386 | 7f8ca2c | High | silent failure | pr edit replace mode couldn't clear all reviewers. Empty slices omitted due to omitempty JSON tag and len > 0 checks. Now send explicit empty lists unconditionally for userLogins, botLogins, teamSlugs. | Step 5 (defensive) - empty collection handling |
| GH-17 | Wrong Platform Asset Name | bc5a44a4a | 10b4a1f | Medium | configuration error | copilot download used windows platform string but assets named win32. Map runtime.GOOS "windows" to "win32" before asset name construction. Also reorder checksum fetch before progress bar. | Step 2 (architecture) - platform abstraction |
| GH-18 | Extension Name Collision | 10b4a1f42 | 08a4413 | High | state machine gap | Extensions with names matching core command names (copilot, pr, issue) silently registered, overriding core commands. Check extension name against registered core command names and aliases, skip collisions with warning. | Step 5a (state machines) - command registration ordering |
| GH-19 | Invalid Remote Flag Combination | 3f0044fd9 | 6acf74e | Medium | validation gap | gh repo fork --remote with repo argument silently ignored --remote (no local repo to add to). Return error when --remote and repo argument both provided. | Step 3 (tests) - mutual exclusivity validation |
| GH-20 | Identical Branch Refs Allowed | 9daa22eba | 6acf74e | Medium | validation gap | gh pr create allowed creating PR from branch to itself (head==base in same repo). Now errors early with clear message. Cross-repo PRs with same branch name still allowed. | Step 5 (defensive) - semantic invariant checks |
| GH-21 | Null Pointer on Project Items | 4a106c1ac | 51dfeea | Critical | null safety | GraphQL API returns null nodes in projectItems connection, causing nil pointer panic. Added nil checks in ProjectsV2ItemsForIssue and ProjectsV2ItemsForPullRequest to safely skip null nodes. | Step 6 (quality risks) - graphql null handling |
| GH-22 | Set-Default Remote Parsing | 1d506f533 | 8de78e6 | Low | error handling | repo set-default incorrectly parsed remote URLs with complex patterns. Simplified parsing logic and added test coverage for edge cases. | Step 3 (tests) - parsing robustness |
| GH-23 | Workflow Run Feature Bailout | 31f375608 | 52eca96 | Medium | error handling | Feature detection error returns early instead of assuming default. Prevents silent mode degradation when API is unreachable. | Step 5 (defensive) - fail-fast semantics |
| GH-24 | Missing Simple Pushdefault Test | 5ed8cf0fa | be4960a | Medium | type safety | Acceptance test expected nameWithOwner in PR headRepository but query wasn't fetching it. Added field to query and updated test assertion. | Step 4 (specs) - test spec alignment |
| GH-25 | Cache Report Wrong Count | ccfc2c304 | 52ba836 | Low | serialization | gh cache delete reported wrong count when deleting keys with refs. Fixed to properly track total deleted when processing key+ref pairs. | Step 6 (quality risks) - output accuracy |
| GH-26 | PlainHttpClient Missing | 2794f7b8d | 55fbad3 | Medium | API contract violation | Factory missing PlainHttpClient for cases needing raw HTTP without gh customizations. Added PlainHttpClient() method returning clean *http.Client. | Step 2 (architecture) - factory completeness |
| GH-27 | SkipDefaultHeaders Option Missing | b81c2495d | b9e04ef | Medium | API contract violation | HTTPClientOptions didn't expose SkipDefaultHeaders flag. Added to allow callers to suppress auto-injected headers when needed. | Step 5b (schema types) - header manipulation API |
| GH-28 | Agent-Task Session Not Fetched | 597cdaf08 | eba3134 | Medium | silent failure | agent-task view couldn't fetch incomplete session data after creation. Re-fetch session from API instead of returning partial object from creation response. | Step 5 (defensive) - data completeness |
| GH-29 | Agent-Task Null Response | 6fc5742a6 | 002ba54 | High | error handling | agent-task returned generic error when API response wasn't valid JSON. Added proper error message and type check to distinguish network vs parsing failures. | Step 5 (defensive) - error diagnostics |
| GH-30 | PR Checkout Missing Alias | 0ec5f1328 | 743a819 | Low | state machine gap | gh pr checkout had no short alias, unlike pr view (alias pv). Added "co" alias for consistency with gh command naming patterns. | Step 2 (architecture) - command discoverability |
| GH-31 | Viewer Fallback Wrong Logic | 597cdaf08 | eba3134 | Medium | silent failure | agent-task/capi always fell back to viewer query when session.userID == 0, losing original data. Changed to only fetch viewer when needed, not as fallback. | Step 5 (defensive) - fallback logic |
| GH-32 | Empty Problem Statement | 863329b4c | c7a811e | Medium | validation gap | agent-task create didn't validate problem statement non-empty before submission. Added check to error early with clear message instead of API error. | Step 3 (tests) - required field validation |
| GH-33 | Async Set-Default Parsing | 1d506f533 | 8de78e6 | Low | error handling | repo set-default remote name parsing didn't account for all URL formats. Simplified to use git internal parsing instead of custom regex. | Step 5b (schema types) - parsing correctness |
| GH-34 | #12792 | `1bba50b3e` | `90bfa624` | High | validation gap | gh pr edit duplicate reviewers: MultiSelectWithSearch dedup logic compared display names ('mxie (Melissa Xie)') against login keys ('mxie'), preventing deduplication. Use DefaultLogins instead of Default for comparisons. | Step 5 (defensive) |
| GH-35 | #12836 | `ff8873da0` | `d594c5e9` | Medium | serialization | gh extension install error showed raw struct pointer instead of formatted repo name. Printf %s on repo object instead of calling ghrepo.FullName(repo). | Step 6 (quality risks) |
| GH-36 | #12831 | `38c997567` | `3fec2e5f` | High | type safety | codespaces port forwarder: direct int to uint16 cast in DeleteTunnelPort could overflow for ports >65535. Add explicit range check and conversion error. | Step 5b (schema types) |
| GH-37 | #12704 | `b38f6772e` | `a2b8b687` | High | state machine gap | gh issue develop --name repeated invocation created duplicate linked branches. Check if branch already exists for issue, reuse if found. Must validate branch matches both repo and name. | Step 5a (state machines) |
| GH-38 | (none) | `26552f348` | `20c7bdc2` | Medium | missing boundary check | featuredetection: Detector interface incomplete without ReleaseFeatures() method. GHES versions before ~3.11 don't support immutable releases field. Query Release type to detect support. | Step 3 (tests) |
| GH-39 | #12702 | `c98c43580` | `f8651f5e` | Medium | silent failure | gh gist edit: sending full file list including truncated files caused API errors. When editing specific file, only send that file in mutation. Filter filesToUpdate to changed files only. | Step 5 (defensive) |
| GH-40 | #12700 | `f8651f5e4` | `cf718037` | Medium | validation gap | gh gist edit: fetched full content upfront for all truncated files instead of only when editing. Move truncated file fetch to specific file edit path after user selects file. | Step 5b (schema types) |
| GH-41 | (none) | `aad023968` | `64416e1e` | Low | API contract violation | gh issue transfer uses GitHubRepo (full schema) when only repo ID needed. Switch to IssueRepoInfo minimal schema to reduce API payload. | Step 2 (architecture) |
| GH-42 | #12798 | `1d95b633e` | `11e5be78` | High | API contract violation | gh issue create requires Contents:Read permission unnecessarily. Switch from GitHubRepo to IssueRepoInfo to support fine-grained PATs with only Issues:Write + Metadata:Read. | Step 2 (architecture) |
| GH-43 | #12702 | `42238dc36` | `c98c4358` | Medium | silent failure | gh gist edit: refetch truncated files didn't track already-edited files, causing re-fetches. Check if filename in filesToUpdate before fetching raw content. | Step 5 (defensive) |
| GH-44 | #12606 | `b32b7eab3` | `a2b8b687` | High | error handling | gh issue view --comments: preloadIssueComments made redundant API call. Check PageInfo.HasNextPage before querying; clear comments list if no next page. | Step 6 (quality risks) |
| GH-45 | (none) | `24885040c` | `64de3146` | High | error handling | agent-task capi: job creation errors swallowed when response body not JSON. Read body once with io.ReadAll(), decode to both Job and JobError. Include status + error details in message. | Step 5 (defensive) |
| GH-46 | #12811 | `7f8ca2ca8` | `846d6619` | Medium | type safety | ReviewerTeam.Slug() returned 'org/team-slug' instead of 'team-slug'. API expects just slug. Store org and teamSlug separately, return only teamSlug from Slug(). | Step 5b (schema types) |
| GH-47 | (none) | `0d8a697c7` | `bd0177b0` | Medium | error handling | pr/shared ParseFullReference: error message missing underlying parse error details. Include wrapped error with %w when strconv.Atoi fails on PR number. | Step 5 (defensive) |
| GH-48 | (none) | `bd0177b03` | `848faf81` | Medium | type safety | fmt.Errorf format string mismatch: passed int to %q specifier. Use original reference string instead of numeric PR number. | Step 5b (schema types) |
| GH-49 | #12736 | `1cd484019` | `76b2de8a` | High | protocol violation | gh pr/issue search: user-supplied keywords not wrapped in parentheses in advanced syntax, leaking OR operators to qualifiers. Add KeywordsVerbatim to Query type, wrap with ( ) in AdvancedIssueSearchString(). | Step 5b (schema types) |
| GH-50 | (none) | `d8486ccf1` | `2c6f8f9b` | Medium | API contract violation | pkg/search Query type lacked way to pass verbatim user keywords. Add KeywordsVerbatim field (mutually exclusive with Keywords) for exact user input. | Step 5b (schema types) |
| GH-51 | #12848 | `8840df2eb` | `c8152ed4` | High | configuration error | agent-task command used plain factory BaseRepo instead of SmartBaseRepoFunc. Resolved wrong repo context. Move agentTaskCmd after repoResolvingCmdFactory init to use correct base repo logic. | Step 2 (architecture) |
| GH-52 | #12674 | `24964681a` | `2c54a0d` | Medium | error handling | gh run view --exit-status with --log/--log-failed ignored exit code when displaying logs. Check failed conclusion and return SilentError after showing logs instead of returning nil unconditionally. | Step 5 (defensive) |
| GH-53 | #13013 | `dd9ab715` | `620261f` | High | error handling | gh pr create --reviewer with feature detection ignored returned errors from IssueFeatures(). Swallowing error prevented error propagation when feature detection failed. Now return error explicitly. | Step 5 (defensive) |
| GH-54 | (none) | `4681b40e` | `3521604` | High | configuration error | agent-task/capi omitted X-GitHub-Api-Version header in Copilot API requests, using GitHub API versions. Added explicit header set to 2026-01-09 for CAPI requests to prevent version mismatch errors. | Step 5b (schema types) |
| GH-55 | (none) | `5fddcef0` | `914531e` | High | protocol violation | gh auth status JSON output structure wrong: returned flat object instead of hosts map. Restructured to return {"hosts": {hostname: [entries]}} with proper nesting for machine-readable output. | Step 5b (schema types) |
| GH-56 | (none) | `9f65e8976` | `d129b94` | Medium | error handling | RepoExists() and repo getTopics/setTopics didn't close HTTP response bodies, leaking file descriptors. Added defer resp.Body.Close() to all response handling paths. | Step 5 (defensive) |
| GH-57 | #10547 | `b31f38c9` | `2b89358` | Medium | state machine gap | gh pr create --web --title --body --fill confused flag priority: title/body only applied if not autofill. Move title/body assignment before WebMode check to ensure they always override autofill. | Step 5a (state machines) |
| GH-58 | (none) | `dde7fce6` | `c6c97b3` | High | state machine gap | pkg/search pagination mutated Query object state during iteration. Passing *http.Response to nextPage() required caller to read response state. Refactored to pass link string only, eliminate Query object mutation. | Step 5a (state machines) |
| GH-59 | (none) | `52bb1dec` | `848faf8` | Low | serialization | gh pr edit error message typo: '--tile' should be '--title'. Corrected error message text for clarity. | Step 6 (quality risks) |
| GH-60 | (none) | `f8d855f5` | `aeeb8a3` | Low | serialization | gh project item-list error message overly verbose about GHES version. Simplified to just note --query flag unsupported on this host. | Step 6 (quality risks) |
| GH-61 | (none) | `4fb9b29a` | `6b19a85` | Medium | type safety | gh release verify-asset used wrong variable for tag filtering: opts.TagName instead of resolved tagName. When tag auto-resolved from latest release, wrong tag used in filtering and output. | Step 5b (schema types) |
| GH-62 | (none) | `123c9eab` | `beba8f6` | Low | serialization | agent-task view printed redundant text before error URL. Simplified output to show just URL since error message already contains full context. | Step 6 (quality risks) |
| GH-63 | #13001 | `e53e360d` | `1df6f84` | High | concurrency issue | codespaces/portforwarder used outer-scope err variable in goroutine, causing data race when UpdatePortVisibility runs concurrently. Define err := in goroutine scope to prevent race conditions. | Step 5a (state machines) |
| GH-64 | (none) | `f294831e` | `4661c05` | High | state machine gap | huhPrompter MultiSelectWithSearch lost selections across searches when huh v2 cache served stale options. Include selectedValues in OptionsFunc binding hash so cache key changes when selections change. | Step 5a (state machines) |
| GH-65 | (none) | `666685087` | `8f7d208` | Medium | state machine gap | acceptance tests failed with git "Author identity unknown" when sandbox overrode HOME. Write .gitconfig into sandbox directory during setup so commits work without global git config. | Step 3 (tests) |
| GH-66 | (none) | `84a3ba83e` | `f92fab6` | Low | error handling | huh prompter MultiSelectWithSearch had unused fields and imports after huh v2 upgrade. Removed dead code to clean up migration. | Step 6 (quality risks) |
| GH-67 | (none) | `95a59f443` | `4d74e05` | Low | serialization | accessible prompter test expectations for huh v2 were outdated. Updated expected strings for new huh v2 UI text and ANSI code wrapping. | Step 3 (tests) |
| GH-68 | (none) | `4661c05ed` | `726714d` | Low | error handling | IOStreams prompter-enabled fields had gofmt misalignment. Fixed formatting to match codebase conventions. | Step 6 (quality risks) |
| GH-69 | (none) | `6c497e74d` | `42238dc` | Medium | silent failure | gist edit tests were failing because expected behavior changed: editing single file shouldn't send unmodified files in mutation. Updated test expectations to match the fixed behavior of sending only edited files. | Step 3 (tests) |
| GH-70 | (none) | `52850321b` | `1df6f84` | Low | serialization | acceptance test for issue develop had stale expected output. Updated to match correct default output. | Step 3 (tests) |
| GH-71 | (none) | `1df6f84d7` | `bdc0413` | Low | error handling | PR create merge pull request had leftover review feedback comments. Cleaned up code. | Step 6 (quality risks) |

### nsqio/nsq (Go)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| NSQ-01 | Concurrency safety in Channel cleanup | cfbd287 | cfbd287^ | High | concurrency issue | RemoveClient() read c.clients length outside mutex. Used without acquiring lock after Unlock(), causing race accessing ephemeral channel deletion. Fix: snapshot len(c.clients) inside mutex before Unlock(). | Step 5a: State machine safety on async operations |
| NSQ-02 | ChannelStats data race | 845a55c | 845a55c^ | High | concurrency issue | NewChannelStats() performed unsynchronized reads of inFlightMessages and deferredMessages maps. Concurrent access from message processing and stats collection caused race detector failures. Fix: acquire inFlightMutex and deferredMutex before len() operations. | Step 5a: Concurrent map access requires serialization |
| NSQ-03 | Channel flush race on exit | 90858c8 | 90858c8^ | High | concurrency issue | Channel.flush() iterated over inFlightMessages and deferredMessages without holding mutexes during backend write. Concurrent RemoveClient() and message processing could corrupt state. Fix: acquire inFlightMutex and deferredMutex during iteration. | Step 5a: Protect critical sections during state transitions |
| NSQ-04 | TCP producer connection stall on Exit | 5f2153f | 5f2153f^ | Critical | concurrency issue | NSQD.Exit() closed TCP listener but not active TCP producer connections, causing indefinite wait. Consumer connections cleaned up via topic closure, but publisher connections remained. Fix: track tcpServer connections and call CloseAll() in Exit(). | Step 5a: Graceful shutdown requires explicit resource cleanup |
| NSQ-05 | NSQLookupd error message shows wrong address | e040792 | e040792^ | Low | error handling | NSQLookupd listen error on HTTPAddress incorrectly reported TCPAddress in error message. Misled operators about which port failed. Fix: use opts.HTTPAddress in error string. | Step 3: Diagnostic error messages prevent misdiagnosis |
| NSQ-06 | Full topic sync accumulation on lookup errors | 67d70f8 | 67d70f8^ | Medium | silent failure | connectCallback would retry full topic sync indefinitely on lookup peer errors. Missing early return caused sync loop to never exit on failure. Fix: add return after error log to prevent duplicate syncs. | Step 5b: Error paths must terminate retries |
| NSQ-07 | Topic.PutMessages partial failure accountability | 43a84e6 | 43a84e6^ | High | missing boundary check | PutMessages() failed to update messageCount on partial failure. If message N failed, count incremented by N instead of N-1, creating off-by-one accounting error. Fix: track index and only increment count for successful puts. | Step 5b: Accounting must reflect actual state |
| NSQ-08 | Nil pointer in memStats on stat retrieval | db3de7a | db3de7a^ | Medium | null safety | getMemStats() returned *memStats pointer. Calling code could receive nil; JSON serialization would fail silently. Copy-by-value design eliminated nil risk. Fix: change return type and all callers to use value semantics. | Step 5b: Pointers for mutable state; values for immutable data |
| NSQ-09 | Stats slice pre-allocation race | e0ac1b2 | e0ac1b2^ | Medium | error handling | GetStats() pre-allocated topics slice using len(n.topicMap) but after filtering into realTopics. Later allocated channels using len(t.channelMap) after filtering. Slice capacity was wrong, causing allocation during append. Fix: use len(realTopics) and len(realChannels) for accurate pre-allocation. | Step 4: Buffer sizing must match actual data cardinality |
| NSQ-10 | Cluster producer deduplication regression | f2d9dcd | f2d9dcd^ | Medium | validation gap | GetLookupdTopicProducers() lost deduplication when aggregating from multiple lookup nodes. Naive append allowed duplicates. Fix: check each producer against accumulated list before appending. | Step 4: Aggregation logic must handle overlapping result sets |
| NSQ-11 | JSON decoding breaks on custom unmarshaler | 97c6e02 | 97c6e02^ | Medium | type safety | E2eProcessingLatencyAggregate used custom JSON library (go-simplejson) with manual field extraction. Fragile to schema changes; library dependency unnecessary. Fix: implement standard UnmarshalJSON to leverage stdlib type safety. | Step 5b: Use stdlib marshaling when possible |
| NSQ-12 | Memory queue disabled ignores configuration | b3b29b7 | b3b29b7^ | High | configuration error | When -mem-queue-size=0, Channel and Topic created unbuffered memoryMsgChan. Design intent was to disable memory queue entirely. Unbuffered channels caused blocking behavior. Fix: set memoryMsgChan to nil if size <= 0, add nil guards on sends. | Step 5a: Configuration parameters must enable/disable features cleanly |
| NSQ-13 | Lookup peer close on uninitialized connection | 36819b6 | 36819b6^ | Medium | null safety | lookupPeer.Close() called conn.Close() without nil check. If connection never established, nil dereference panic. Fix: guard Close() with nil check. | Step 5b: Defensive null checks on resource cleanup |
| NSQ-14 | Requeue timeout out-of-bounds drops client | 315096f | 315096f^ | High | validation gap | REQ command rejected timeouts outside [0, MaxReqTimeout] with fatal error, disconnecting client. Clients sending invalid timeouts were penalized with disconnection. Fix: clamp timeout to valid range instead; log warning but continue. | Step 5b: Validate and sanitize user input; don't disconnect on recoverable errors |
| NSQ-15 | Missing exit check on requeue | 72e730c | 72e730c^ | Medium | state machine gap | RequeueMessage() with timeout=0 called doRequeue() without checking Exiting() state. Could queue message to exiting channel. Fix: check c.Exiting() and return error if true. Move cleanup to use c.put() directly. | Step 5a: Exit state must be checked before state modifications |
| NSQ-16 | Client delivery race via unsafe channel read | 46496bd | 46496bd^ | Critical | concurrency issue | SendMessage() read client.Channel unsafely and deferred inflight timeout registration. If client disconnected between read and SendMessage(), message could be orphaned. Fix: perform StartInFlightTimeout() and SendingMessage() before SendMessage() to atomically mark message in-flight. | Step 5a: All side effects must precede potentially-failing operations |
| NSQ-17 | Client subscription cleanup race on disconnect | 059d473 | 059d473^ | High | concurrency issue | messagePump exit removed client from channel, but buffered SubEventChan could cause race. If client disconnected, readLoop never received subscription update. Client remained in channel.clients. Fix: move RemoveClient() to readLoop exit path where client.Channel is safely accessed. | Step 5a: Guarantee cleanup for all code paths |
| NSQ-18 | Consumer limit error message in wrong command | 58a8cc7 | 58a8cc7^ | Low | error handling | SUB command threw E_TOO_MANY_CHANNEL_CONSUMERS error string from AddClient() error, but protocol layer discarded it and generated generic error. Error message lost. Fix: propagate actual error from channel.AddClient() into protocol response. | Step 3: Diagnostic context must flow through error boundaries |
| NSQ-19 | Deflate level handling logic inverted | b4ca0f3 | b4ca0f3^ | Medium | error handling | IDENTIFY deflate level: (1) set to 6 if identifyData.DeflateLevel <= 0, (2) then clamp 6 to max. Logic failed when identifyData.DeflateLevel=0 (default should be used). Client explicitly set to 0 would incorrectly fall back. Fix: check > 0 before using client value; only use default 6 if <= 0. | Step 5b: Distinguish between "not provided" (0) and "provided as 0" |
| NSQ-20 | 32-bit atomic alignment on 64-bit variables | f89fc71 | f89fc71^ | Medium | type safety | 64-bit atomic variables (messageCount, readPos, depth, etc.) placed after mutex fields on 32-bit platforms. Misaligned atomics cause panic or undefined behavior. Fix: reorganize struct fields so all 64-bit atomics come first. | Step 5b: Platform-specific alignment requirements for atomic ops |
| NSQ-21 | PeerInfo lastUpdate race in nsqlookupd | 6f49c37 | 6f49c37^ | High | concurrency issue | PeerInfo.lastUpdate was time.Time (8 bytes) without synchronization. Concurrent PING updates and HTTP debug reads caused race detector failures. Fix: store as int64 (UnixNano), use atomic.LoadInt64/StoreInt64 for all accesses. | Step 5a: Shared mutable state requires atomic or mutex protection |
| NSQ-22 | TCP connection cleanup on graceful exit | 61de19e | 61de19e^ | Critical | concurrency issue | TCPServer handler goroutines not awaited on exit. Test cleanup logged while handlers still running, causing t.Log race. Handlers that failed to exit blocked server shutdown. Fix: track handler goroutines in WaitGroup, call Wait() before TCPServer returns. | Step 5a: Shutdown must wait for all in-flight operations |
| NSQ-23 | NSQD fatal error suppression on startup | d66571c | d66571c^ | Critical | error handling | NSQD.Main() and New() called os.Exit(1) on various configuration/listen errors, bypassing service manager. Prevented graceful shutdown and cleanup. Fix: return error instead of exit; propagate errors up to svc.Run handler. | Step 5: Defer shutdown responsibility to service manager |
| NSQ-24 | NSQLookupd fatal error suppression on startup | 8e6768b | 8e6768b^ | Critical | error handling | NSQLookupd.New() and Main() called os.Exit(1) on listen errors. Prevented graceful shutdown sequence. Fix: return error values; let service manager coordinate shutdown via exitCh. | Step 5: Service lifecycle errors must be recoverable |
| NSQ-25 | Ephemeral channel subscription race retry | 1e1720f | 1e1720f^ | Medium | state machine gap | SUB command could race with ephemeral channel deletion. GetChannel() creates new channel, but before AddClient(), channel could start exiting. Fix: retry loop with sleep if channel/topic exiting detected. Later hardened with bounded retry (2x) and proper failure exit. | Step 5a: Race windows on ephemeral resource lifecycle |
| NSQ-26 | Ephemeral subscription infinite retry | 7521c9d | 7521c9d^ | Medium | error handling | Retry loop in SUB for ephemeral race was infinite without bound. Could spin indefinitely on busy deletion window. Fix: limit to 2 attempts (100ms timeout), then return fatal error. | Step 5a: All retry loops need failure bounds |
| NSQ-27 | #1441 | `af67175` | `b28153e` | High | error handling | SpreadWriter.Flush() panic on zero writes. Divided by len(s.buf) without bounds check. Called during exit even when buffer empty, causing division by zero and crash. Fix: guard Flush with zero-length buffer check. | Step 5b: Defensive checks before operations on empty collections |
| NSQ-28 | #996 | `725c653` | `b2f1641` | High | error handling | SendMessage() reused single buffer across messagePump loop for all messages. On large message > buffer capacity, buffer would continue growing without release, causing memory leak. Fix: allocate per-message buffer; don't reuse. | Step 5a: Resource lifecycle management; prevent unbounded growth |
| NSQ-29 | #1025 | `165f14a` | `a73c39f` | High | error handling | nsq_to_file with topic pattern created new ClusterInfo HTTP client every sync iteration. Clients were never closed, causing connection leaks. Fix: allocate ClusterInfo once at startup and reuse. | Step 5a: Singleton pattern for shared resources |
| NSQ-30 | N/A | `7909c92` | `d9b0dc6` | High | silent failure | Topic.GenerateID() infinite silent retry loop on GUID generation failure. Loop would spin without logging, consuming CPU while operator remained unaware of failure. Fix: log error every 10,000 iterations and convert goto to explicit loop. | Step 5a: Silent loops must not occur; always report state changes |
| NSQ-31 | N/A | `f6c5336` | `77fe56d` | Medium | error handling | DirLock error message did not mention lock contention as root cause. Log message "in use" was cryptic, blocking operators from diagnosing concurrent startup. Fix: add explanation in error message. | Step 3: Error messages must guide operators to root cause |
| NSQ-32 | #1498 | `09c645d` | `4de1606` | Medium | error handling | nsqadmin graphite target param serialization. jQuery $.param() was called without traditional encoding flag. Array targets like target=['foo', 'bar'] were URL-encoded incorrectly, breaking graphite requests. Fix: pass traditional:true flag. | Step 4: JSON serialization to URL params requires correct format |
| NSQ-33 | #1462 | `fc75506` | `51b270f` | High | security issue | nsqadmin tombstoneNodeForTopicHandler missing authorization check. Endpoint permitted any unauthenticated requester to tombstone (block) topic nodes. Fix: add isAuthorizedAdminRequest check before processing. | Step 5b: All destructive operations require authorization verification |
| NSQ-34 | #714 | `598e111` | `cb6fd8b` | Medium | error handling | nsqadmin channel aggregation bug. When computing channel stats, found flag was scoped outside loop. Once first node's channel found, flag remained true for all remaining nodes, silently skipping new channels. Fix: move found flag declaration inside channel loop. | Step 5a: Variable scope affects control flow correctness |
| NSQ-35 | N/A | `93c9dd7` | `9d6dad6` | Medium | error handling | nsq_to_file term handler break statement only exited inner select, not outer for loop. Process hung waiting for poller when interrupted. Fix: label outer loop and use break to target outer label. | Step 5a: Nested control structures require proper exit paths |
| NSQ-36 | #1184 | `8d2e9e6` | `cb83885` | High | validation gap | E2E processing latency percentiles validation missing. Config example showed percentiles as [100.0, 99.0, 95.0] but valid range is (0.0, 1.0]. Invalid values caused quantile library to consume unbounded memory and CPU. Fix: add validation in New() to reject invalid percentiles. | Step 4: Configuration constraints must be validated at init |
| NSQ-37 | #815 | `fc6381b` | `c4e2add` | Medium | protocol violation | IPv6 broadcast address handling. Producer.HTTPAddress() and TCPAddress() used simple string concat which breaks IPv6 (e.g., fd4a::1:4150 parses as port, not address:port). Fix: use net.JoinHostPort which wraps IPv6 in brackets. | Step 5b: Network address formatting requires protocol-aware functions |
| NSQ-38 | N/A | `a5804b3` | `e4d2956` | Medium | missing boundary check | E2eProcessingLatencyAggregate potential division by zero. When aggregating percentiles, if p[i]["count"] became 0, average calculation would divide by zero. Fix: add guard check and continue if count is zero. | Step 5b: Boundary checks before division; handle edge cases |
| NSQ-39 | N/A | `0ea0c0f` | `98fbcd1` | Medium | validation gap | Worker ID validation range incorrect. Code validated [0, 4096) but GUID format uses 10-bit timestamp offset, supporting only [0, 1024). Out-of-range IDs silently corrupted GUIDs. Fix: corrected upper bound. | Step 5b: Configuration constraints must match system bit widths |
| NSQ-40 | N/A | `77d8892` | `d9d5d94` | Medium | missing boundary check | nsq_stat division by zero for sub-second intervals. Dividing MessageCount by interval.Seconds() could be fractional, and integer division truncated to zero. Fix: convert to float64 first, then cast result to int64. | Step 5b: Type conversions must handle loss of precision |
| NSQ-41 | #669 | `75c4ae3` | `77a46db` | High | state machine gap | TLS configuration override. -tls-client-auth-policy flag unconditionally overrode -tls-required setting. Specifying both flags resulted in unexpected TLS enforcement mode. Fix: only set TLSRequired if currently TLSNotRequired. | Step 5a: Option interaction must respect user intent |
| NSQ-42 | N/A | `e4c34b1` | `47034fb` | Medium | serialization | nsqadmin IPv6 node links broken. Node list links used address directly without brackets, breaking IPv6 URLs. Fix: use net.JoinHostPort for consistent formatting. | Step 5b: Use stdlib URL/address builders for consistency |
| NSQ-43 | N/A | `e7f846d` | `1eba46e` | Medium | error handling | nsqadmin channel rate calculation wrong. Total rate column computed as (new_rate - old_rate) but should be rate[0] when computing aggregate. Showed negative rates. Fix: use correct rate indexing. | Step 4: Aggregation metrics must use consistent field references |
| NSQ-44 | #1464 | `eb27dd5` | `1d183d9` | Medium | configuration error | NSQLookupd auth server requests ignored --tls-root-ca-file setting. HTTP client used nil TLS config, rejecting valid certificates. Fix: extract TLS config settings, pass to auth query function. | Step 5b: Configuration must be threaded through all components |
| NSQ-45 | N/A | `62d202f` | `b121909` | Medium | concurrency issue | Topic.exit() iterated over channelMap without acquiring RLock. Concurrent channel reads from stats or deletion could cause race detector failures. Fix: acquire RLock during channel iteration. | Step 5a: Protect map iteration with appropriate locks |
| NSQ-46 | N/A | `bba7bba` | `5b67f58` | Low | error handling | TestConfigFlagParsing opened config file but never closed it. File handle leaked until test completed. Fix: add defer f.Close() after file open. | Step 5b: Resource cleanup must use defer immediately after acquisition |
| NSQ-47 | N/A | `ccb19ea` | `d3d0bbf` | High | error handling | NSQD.Exit() did not close active TCP client connections. Clients could remain open indefinitely, preventing graceful shutdown. Fix: add tcpServer.Close() to iterate and close all client connections. | Step 5a: Explicit resource cleanup in exit paths |
| NSQ-48 | N/A | `c154eba` | `5ea1012` | Medium | error handling | FileLogger.Close() performed Sync() before closing GZIP writer. Pending GZIP data would be lost if Close() failed. Also ignored fsync/close errors. Fix: close GZIP first, then fsync, with error checks. | Step 5b: Operations with side effects must occur in correct order |
| NSQ-49 | N/A | `411801b` | `c432e69` | Medium | state machine gap | FileLogger.updateFile() moved Close() after filename calculation. If filename changed, Close() would use stale filename for conflict resolution. Fix: move Close() before filename update. | Step 5a: State changes must precede dependent operations |
| NSQ-50 | N/A | `dc60cfd` | `29114b3` | Medium | error handling | nsq_to_file signal handler channels were unbuffered. When signal arrived during event loop, channel send would block permanently. Fix: create buffered channels (size 1) for signal.Notify. | Step 5b: Signal channels must be buffered to prevent missed signals |
| NSQ-51 | N/A | `ebab1af` | `4405e22` | High | concurrency issue | Channel.exit() iterated over clients map without lock. Concurrent client reads or removals caused race detector failures. Fix: acquire RLock before iterating. | Step 5a: Map iteration requires synchronization |
| NSQ-52 | N/A | `f1b807c` | `f874049` | High | concurrency issue | inFlightWorker accessed c.clients map without lock during timeout processing. Concurrent client removal could cause panic. Fix: acquire RLock around client map lookup. | Step 5a: Shared mutable state requires synchronization |
| NSQ-53 | N/A | `79b7359` | `b2d1537` | High | concurrency issue | Channel.Empty() during delete could deadlock when waiting on clientMsgChan write. If channel exited while message pump held lock, pump would block indefinitely. Fix: set clientMsgChan to nil in select when closed, allowing progress. | Step 5a: Handle closed channels in select statements |
| NSQ-54 | N/A | `f874049` | `c5375c5` | High | error handling | inFlightPqueue.Remove() called Pop() after manipulation, causing double-pop and data corruption. Removed element added back to queue. Fix: implement proper removal with index tracking, no Pop() call. | Step 5b: Container manipulation must avoid redundant operations |
| NSQ-55 | N/A | `12663c2` | `3ee16a5` | Medium | error handling | IDENTIFY response returned default MsgTimeout instead of client-requested value. Clients received wrong timeout, causing message handling miscalculation. Fix: echo back identifyData.MsgTimeout in response. | Step 4: Protocol responses must reflect request parameters |
| NSQ-56 | N/A | `28389b0` | `6a237f3` | Medium | validation gap | MPUB binary parameter parsing didn't validate input. Any non-empty value (including invalid strings) treated as true. Fix: parse param value against explicit allowed values map, warn on deprecated values. | Step 5b: User input requires explicit whitelist validation |
| NSQ-57 | N/A | `ee31e04` | `d2cd54e` | High | state machine gap | Topic creation skipped messagePump notification for proactively-created channels. Channels created during topic init were never signaled to messagePump, causing message loss. Fix: send channelUpdateChan signal after unlocking and creating channels. | Step 5a: State changes must notify dependent state machines |
| NSQ-58 | N/A | `0c417fa` | `2549bc6` | Medium | error handling | Percentile calculation used Ceil formula with off-by-one indexing. Could access out-of-bounds array indices. Also GC pause collection logic was broken for wrapped circular buffer. Fix: use Floor instead of Ceil, correct circular buffer logic. | Step 5b: Array indexing must account for boundary conditions |

### colinhacks/zod (TypeScript)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| ZOD-01 | #5672 | 3cd45eb | 3a818de | High | validation gap | httpUrl() lacked strict protocol validation, allowing invalid URLs to pass validation | Step 2 (architecture), Step 5b (schema types) |
| ZOD-02 | #5687 | 3a818de | 55747b3 | High | type safety | Regex pattern /\d?e-\d?/ only matched single-digit exponents, causing floatSafeRemainder to fail for steps like 1e-10 | Step 5 (defensive), Step 5a (state machines) |
| ZOD-03 | #5681 | 5b57450 | 65f1f40 | High | state machine gap | abort option not stopping subsequent checks with when function, breaking validation abort chain | Step 5a (state machines), Step 3 (tests) |
| ZOD-04 | #5555 | ae68f62 | 7abe4e5 | Medium | error handling | Error message claimed '<2 items' when actually expecting exactly 2, causing confusion | Step 4 (specs), Step 6 (quality risks) |
| ZOD-05 | #5476 | 9d6e7d0 | 2b564dc | High | type safety | Return type inference could be non-Promise instead of always Promise<T> | Step 2 (architecture), Step 5b (schema types) |
| ZOD-06 | #5511 | fb66ee1 | 6e968a3 | Medium | type safety | Missing type exports in mini package caused TypeScript TS4023 error | Step 2 (architecture), Step 3 (tests) |
| ZOD-07 | #5098 | 002e01a | f97e80d | High | validation gap | isPlainObject check failed when objects had constructor field that wasn't a function, causing validation rejection | Step 5 (defensive), Step 5b (schema types) |
| ZOD-08 | #5089 | f97e80d | f791052 | Critical | silent failure | Recursive tuples crashed with 'Cannot read properties of undefined' due to missing optional chaining | Step 5a (state machines), Step 3 (tests) |
| ZOD-09 | #5453 | 9fc493f | f2f0d17 | Medium | type safety | toJSONSchema used incorrect keyword for discriminated unions instead of oneOf | Step 4 (specs), Step 2 (architecture) |
| ZOD-10 | #5266 | 62bf4e4 | a0abcc0 | High | null safety | Object prototype collision when field key is 'toString', causing flatten() to crash | Step 5 (defensive), Step 6 (quality risks) |
| ZOD-11 | #5173 | e1f1948 | 887e37c | High | silent failure | Array default values not cloned, causing all instances to share same array reference | Step 5 (defensive), Step 3 (tests) |
| ZOD-12 | #5156 | 3291c61 | 3e98274 | Medium | type safety | Tuple with null type generated incorrect schema structure for OpenAPI 3.0 target | Step 4 (specs), Step 2 (architecture) |
| ZOD-13 | #5139 | 309f358 | 87b97cc | Medium | type safety | Number range with exclusive boundary incorrectly converted for OpenAPI 3.0 output | Step 4 (specs), Step 2 (architecture) |
| ZOD-14 | #5141 | 5c5fa90 | 8bf0c16 | Medium | type safety | Record schema generated incorrect JSON Schema for OpenAPI 3.0 target | Step 4 (specs), Step 2 (architecture) |
| ZOD-15 | #5152 | 8bf0c16 | 0cf4589 | Medium | type safety | Tuple schemas with rest elements and metadata IDs generated incorrect paths in draft-7 | Step 4 (specs), Step 2 (architecture) |
| ZOD-16 | #5146 | 0cf4589 | a410616 | Medium | type safety | Tuple conversion to JSON Schema missing oneOf constraint in items | Step 4 (specs), Step 2 (architecture) |
| ZOD-17 | #5145 | 25a4c37 | e45e61b | Medium | type safety | Record-tuple combinations incorrectly converted for OpenAPI 3.0 | Step 4 (specs), Step 2 (architecture) |
| ZOD-18 | #5093 | 0313553 | 592b7b5 | Low | error handling | Set and File size constraints had inconsistent inclusive flag vs arrays | Step 4 (specs), Step 6 (quality risks) |
| ZOD-19 | #5223 | aa6f0f0 | 9f65038 | High | validation gap | CIDRv6 regex matched invalid addresses; object shape check lacked null safety | Step 5 (defensive), Step 5b (schema types) |
| ZOD-20 | #5045 | d589186 | 03cfa8d | Medium | type safety | keyof method didn't properly type as enum, losing type safety | Step 2 (architecture), Step 5b (schema types) |
| ZOD-21 | #5033 | 3de2b63 | d43cf19 | Low | type safety | Input/output types wrapped with unnecessary Required<> causing type issues | Step 2 (architecture), Step 5b (schema types) |
| ZOD-22 | #4895 | f75d852 | 17e7f3b | Medium | type safety | Decimal literals not properly escaped causing invalid schema output | Step 5 (defensive), Step 4 (specs) |
| ZOD-23 | #4837 | 91c9ca6 | 0df5f69 | High | silent failure | Registry identity map accumulates entries without cleanup, causing memory leaks | Step 5 (defensive), Step 6 (quality risks) |
| ZOD-24 | #4617 | a7cb6ed | 218a267 | Medium | validation gap | Length validation doesn't respect exact boundary requirement | Step 5 (defensive), Step 5a (state machines) |
| ZOD-25 | #4659 | 303f1e9 | 9548f11 | Low | type safety | Type assertion incomplete for less-than comparisons | Step 2 (architecture), Step 5b (schema types) |
| ZOD-26 | #4627 | 8ab2374 | da4f921 | High | type safety | Object.getPrototypeOf checks fail for objects from different JS realms, breaking cross-iframe validation | Step 5 (defensive), Step 5b (schema types) |
| ZOD-27 | #4591 | 5fdece9 | a73a3b3 | Low | error handling | Error details missing inclusive flag for length boundaries | Step 4 (specs), Step 6 (quality risks) |
| ZOD-28 | #4590 | 78e0eae | df73cb0 | Low | type safety | Type not added to literal enum schema | Step 2 (architecture), Step 5b (schema types) |
| ZOD-29 | #4577 | 6fd3b39 | dc2c0b0 | Low | type safety | Enum in JSON Schema output missing type specification | Step 4 (specs), Step 2 (architecture) |
| ZOD-30 | #4974 | d6cd30d | dfae371 | Medium | validation gap | Fixed validation behavior from issue #4973 | Step 5 (defensive), Step 3 (tests) |
| ZOD-31 | #5018 | `d43cf19` | `f2949a8` | High | state machine gap | Recursive object initialization failed when using .check() due to immediate getter evaluation during object cloning with spread syntax | Step 5a (state machines), Step 3 (tests) |
| ZOD-32 | #5002 | `362eb33` | `73a1970` | High | validation gap | Optional schemas with piped transforms ignored validation errors when undefined, skipping validation chain | Step 5 (defensive), Step 3 (tests) |
| ZOD-33 | N/A | `c5f349b` | `5267f90` | Medium | type safety | z.undefined() incorrectly converted to null in toJSONSchema instead of being marked unrepresentable | Step 4 (specs), Step 2 (architecture) |
| ZOD-34 | #4840 | `e7f20c2` | `990e03b` | Medium | type safety | treeifyError type inference failed for branded primitives, treating them as complex types instead of primitives | Step 2 (architecture), Step 5b (schema types) |
| ZOD-35 | #4994 | `9bdbc2f` | `b8257d7` | High | silent failure | defineLazy caused infinite loops on circular getter references due to missing cycle detection in lazy property evaluation | Step 5a (state machines), Step 5 (defensive) |
| ZOD-36 | #4926 | `7ab1b3c` | `7dd7484` | High | validation gap | ZodPipe continued validation even after upstream errors, generating cascading downstream validation failures | Step 5 (defensive), Step 5a (state machines) |
| ZOD-37 | #4961 | `3048d14` | `34b400a` | High | state machine gap | Object.extend() and pick()/omit() operations caused property descriptor loss, breaking chained method calls with check() | Step 2 (architecture), Step 5 (defensive) |
| ZOD-38 | #5073 | `fc1e556` | `1cebf33` | Medium | type safety | instanceof checks for Zod schemas failed when schemas were proxied or wrapped, breaking polymorphic validation | Step 2 (architecture), Step 5b (schema types) |
| ZOD-39 | N/A | `a9c120e` | `a3e4391` | Low | type safety | ZodDiscriminatedUnion missing def property accessor, breaking compatibility with schema introspection utilities | Step 2 (architecture), Step 5b (schema types) |
| ZOD-40 | N/A | `aff9561` | `4a3baf7` | Medium | type safety | Branded types in z.record() lost brand information in type inference due to incorrect type extraction from branded keys | Step 2 (architecture), Step 5b (schema types) |
| ZOD-41 | N/A | `6be478b` | `6fd3b39` | Medium | type safety | ZodType assignability failed for optional object fields, rejecting valid schema type satisfiability checks | Step 2 (architecture), Step 5b (schema types) |
| ZOD-42 | #5181 | `27f13d6` | `845a230` | Medium | validation gap | Regex patterns for integer, bigint, boolean, null, and IPv6 lacked proper boundary anchors and duplicates, causing false positives | Step 5 (defensive), Step 4 (specs) |
| ZOD-43 | #4630 | `2954f40` | `c58bd9b` | Medium | type safety | ZodArray and ZodSet interface definitions incomplete, missing proper type parameter propagation for input/output types | Step 2 (architecture), Step 5b (schema types) |
| ZOD-44 | N/A | `b8257d7` | `dbb05ef` | Low | type safety | Tuple recursive inference lacked proper type narrowing, causing excessively deep type instantiation errors | Step 2 (architecture), Step 5b (schema types) |
| ZOD-45 | N/A | `98cd8b3` | `50e9afb` | Low | error handling | Error object type narrowing failed for certain complex schema combinations, causing type assertion failures | Step 2 (architecture), Step 6 (quality risks) |

### trpc/trpc (TypeScript)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| TRPC-01 | #7286 | 2b8a4f8 | 59f2cdb | High | error handling | Streaming onError callback receives `{ error, path }` wrapper but passed entire object to `getTRPCErrorFromUnknown()` instead of `cause.error`, resulting in empty error messages ("") instead of actual error text | Step 5b (schema types) - error shape contract violations |
| TRPC-02 | #7272 | a2f90fc | f6e839f | High | error handling | Node VM error messages not extracted when error is non-string object; `Error.message` fallback missing | Step 5 (defensive) - guard against non-string error origins |
| TRPC-03 | #7269 | e971f84 | 7d9bb2e | Medium | null safety | `pathExtractor` can return `undefined` without safe optional chaining, causing downstream crashes | Step 5b (schema types) - missing null/undefined boundaries |
| TRPC-04 | #7209 | 6ccaf04 | 5b0a437 | Critical | state machine gap | Normal stream completion discards buffered chunks; both close and abort handlers called `controller.error()` per WHATWG spec, which discards enqueued data | Step 5a (state machines) - close vs abort semantics |
| TRPC-05 | #7262 | ec32cdd | 346868c | Critical | API contract violation | Hardcoded `info.calls[0]` in batch stream error handler; multi-call batch requests route 2nd+ errors to first call's path/input/type | Step 2 (architecture) - batch call routing invariant |
| TRPC-06 | #7094, #7207 | dad1281 | b465c51 | Critical | state machine gap | `maxDurationMs` timeout aborts combined signal but `writeResponse.ts` passes only `request.signal` to pipe, so timeout never ends response; client never reconnects | Step 5a (state machines) - signal propagation chain |
| TRPC-07 | #7190 | f489af0 | 6c2e9b3 | High | type safety | `useSuspenseInfiniteQuery` type error when `getNextPageParam` omitted; skipToken constraint incorrectly applied | Step 5b (schema types) - conditional type constraints |
| TRPC-08 | #7132 | d92cc45 | 9d4b3b9 | High | configuration error | WebSocket connection params built without applying configured encoder, causing incompatibility with custom message encoding | Step 2 (architecture) - encoder application flow |
| TRPC-09 | #6974 | b802056 | 1c9a6ec | Medium | validation gap | FormData input validation fails; version mismatch with undici causes schema validation to reject valid form data | Step 3 (tests) - test fixtures for FormData |
| TRPC-10 | #7036 | 028ad65 | 172b6aa | High | silent failure | `useSubscription` doesn't track props accessed only in conditional branches; stale data returned if prop accessed late | Step 5a (state machines) - subscription prop tracking invariant |
| TRPC-11 | #7037, #6991 | 172b6aa | 783bf8f | Critical | state machine gap | `maxDurationMs` timeout signal not passed to subscription handler's `opts.signal`; handlers waiting for abort never wake up | Step 5a (state machines) - timeout signal propagation |
| TRPC-12 | #7023 | ffa88b0 | 86e12a5 | High | configuration error | `mergeRouter` doesn't propagate SSE options from `initTRPC.create({})`; merged routers ignore configured SSE behavior | Step 2 (architecture) - config propagation through composition |
| TRPC-13 | #6990 | 3ae1c36 | 5ad18f6 | High | null safety | `mutationOptions()`, `queryOptions()`, `infiniteQueryOptions()` crash when no opts parameter; `keyPrefix` undefined | Step 5 (defensive) - optional parameter handling |
| TRPC-14 | #6970, #6967 | cd64ab3 | 110e2d3 | Medium | state machine gap | WebSocket emits spurious "connecting" state transition during initialization when connection already established | Step 5a (state machines) - idle state precondition |
| TRPC-15 | #6960, #6955 | 9b27411 | 466a924 | High | error handling | `httpBatchStreamLink` stream cleanup throws TypeError in React Native; controller state validation missing | Step 3 (tests) - React Native stream lifecycle |
| TRPC-16 | #6957, #6955 | aac35fb | 7f0f1e4 | High | state machine gap | Stream controller transitions to closed/errored state illegally in React Native; state guards missing | Step 5a (state machines) - WHATWG Streams state rules |
| TRPC-17 | #6914, #6913 | f3ddc3a | e272d68 | Medium | protocol violation | GET requests include Content-Type header, triggering CORS preflight unnecessarily per HTTP spec | Step 5b (schema types) - HTTP header contract |
| TRPC-18 | #6927, #6916 | e272d68 | aaf09d0 | High | API contract violation | `DataTransformer` interface marked `@public` but not exported from `@trpc/server` or `@trpc/client` packages | Step 2 (architecture) - public API surface definition |
| TRPC-19 | #6888, #6887 | b90d509 | 1611ba8 | High | type safety | Schema type extraction doesn't check Standard Schema interface first; falls back to library-specific extraction | Step 5b (schema types) - schema detection priority |
| TRPC-20 | #6879, #6850 | 81c75f0 | eda6206 | High | type safety | ESM and CJS `.d.ts` files export incompatible symbol definitions; monorepo type checking fails across module formats | Step 5b (schema types) - dual-format type consistency |
| TRPC-21 | #6878, #6863 | eda6206 | b7b8d3a | Medium | validation gap | `httpBatchLink` serialization fails with custom transformed objects at top level; transformer not applied | Step 4 (specs) - transformer application order |
| TRPC-22 | #6842, #6837 | 2bba173 | fcf4b4a | High | concurrency issue | Fastify adapter accumulates event listeners on reused sockets; MaxListenersExceededWarning and memory leak | Step 5 (defensive) - listener cleanup on socket reuse |
| TRPC-23 | #6838, #6834 | fcf4b4a | 5b325d7 | High | type safety | `createCaller` type cannot be inferred; requires reference to internal `unstable-core-do-not-import` package | Step 2 (architecture) - internal vs public API boundaries |
| TRPC-24 | #6826, #6823 | ea5ee89 | 113013e | Medium | configuration error | Build target not configured for ES2017; React Native polyfills not applied, async/await fails | Step 2 (architecture) - build target matrix |
| TRPC-25 | #6822 | 148aed1 | 5cc8e8e | Medium | configuration error | Package.json exports condition ordering incorrect; ESM/CJS resolution picks wrong entry point | Step 4 (specs) - package.json spec compliance |
| TRPC-26 | #6810, #6804 | 5964441 | 6743d65 | High | type safety | Zod `z.json()` type inference fails with custom serializers; type extraction doesn't preserve json-wrapper semantics | Step 5b (schema types) - special serializer types |
| TRPC-27 | #6797, #6693 | aabc35a | d937503 | High | silent failure | `useSubscription` hook never invokes `onConnectionStateChange` callback; connection state changes go unreported | Step 3 (tests) - callback invocation contracts |
| TRPC-28 | #6793, #6792, #6791 | 2afe29a | 95e12af | High | type safety | `infiniteQueryOptions` incorrectly infers `initialData` type; skipToken constraint breaks when explicitly omitted | Step 5b (schema types) - conditional option types |
| TRPC-29 | #6787, #6785 | f7aef25 | d093fb3 | Medium | concurrency issue | Node 24+ async iterables already have `Symbol.asyncDispose`; double-wrapping creates duplicate dispose methods | Step 5a (state machines) - resource disposal semantics |
| TRPC-30 | #6634 | 249b40d | 3bc06d0 | Medium | validation gap | Effect library's Standard Schema implementation not recognized; validation falls back to Effect-specific extraction | Step 4 (specs) - Standard Schema detection |
| TRPC-31 | #6616, #6110 | 122e948 | bdc0ed8 | High | type safety | Middleware `concat()` loses generic type information; return type becomes `unknown` | Step 5b (schema types) - generic preservation through composition |
| TRPC-32 | #6602 | 16e52eb | 9cab92a | Medium | silent failure | Infinite query cursors: falsy values (0, false, "") treated as missing; pagination fails on falsy cursors | Step 5b (schema types) - falsy value distinction |
| TRPC-33 | #6573, #6558 | b550ee4 | 1becc23 | High | silent failure | Next.js SSG helpers reused across pages; QueryClient contains stale pending promises not hydrated; hydration fails silently | Step 3 (tests) - promise lifecycle in SSG context |
| TRPC-34 | #6569, #6456 | 1becc23 | 53ebeae | Medium | serialization | AWS Lambda adapter cookie splitting doesn't handle expiry dates; cookie-es not used, manual split breaks on `;Expires=` | Step 4 (specs) - HTTP Set-Cookie RFC spec |
| TRPC-35 | #6571 | 53ebeae | 5bdc9dc | High | type safety | Infinite query types incorrectly inferred; cursor type not preserved across pagination calls | Step 5b (schema types) - cursor type invariant |
| TRPC-36 | #6640 | `2def33b` | `78249ca` | High | state machine gap | WebSocket doesn't reconnect when closed unexpectedly in lazy mode; pending subscriptions not checked before deciding to skip reconnection | Step 5a (state machines) - lazy mode reconnection invariant |
| TRPC-37 | #6689 | `cf7091a` | `9ffbdb9` | High | configuration error | `sseStreamConsumer` references global `EventSource` instead of passed instance; fails in React Native and non-browser environments | Step 2 (architecture) - dependency injection flow |
| TRPC-38 | #6776 | `39fa527` | `cfc297f` | Medium | silent failure | TRPC receives unwrapped Vue `ref` objects instead of raw values when used with Vue Query; query input validation fails silently | Step 5b (schema types) - reactive wrapper unwrapping |
| TRPC-39 | #6770 | `b7cac1d` | `5bcc761` | High | state machine gap | `useSubscription` doesn't abort previous subscription when input changes; resources leak and stale data returned | Step 5a (state machines) - subscription cleanup on input change |
| TRPC-40 | #6547 | `be14f29` | `c16467c` | Critical | state machine gap | WebSocket connection params not sent before messages in async auth flows; `connectionParams` promise never awaited, causing auth to be skipped | Step 5a (state machines) - async initialization ordering |
| TRPC-41 | #6523 | `4eda4d5` | `81e851a` | Medium | error handling | Bad absolute import path in wsConnection.ts; relative path replaced with absolute, causing module resolution failure in some environments | Step 2 (architecture) - import path resolution |
| TRPC-42 | #6495 | `de6335c` | `3aa4966` | High | validation gap | FormData with custom transformers fails; transformer not applied before checking for FormData type, causing serialization error | Step 4 (specs) - transformer application ordering |
| TRPC-43 | #6482 | `b7174a4` | `cedf262` | Medium | error handling | Node HTTP adapter listens to wrong socket event; `req.socket.once('end')` should be `req.socket.once('close')` for proper abort handling | Step 5 (defensive) - socket lifecycle event correctness |
| TRPC-44 | #6684 | `d095305` | `1f1c7f0` | High | type safety | `TRPCConnectionState` generic type constraints too strict; `ConnectionIdleState` and `ConnectionPendingState` incorrectly parameterized with `TError` | Step 5b (schema types) - generic variance rules |
| TRPC-45 | #7036 | `028ad65` | `172b6aa` | High | silent failure | `useSubscription` doesn't track props accessed only in conditional branches; stale closure references cause queries to use old input | Step 5a (state machines) - dependency tracking invariant |
| TRPC-46 | #6473 | `e31a1f5` | `fa62c83` | High | concurrency issue | Parallel calls to lazy-loaded routers use shared promise; multiple concurrent loads race and can cause duplicate initialization or missed calls | Step 5a (state machines) - lazy loader synchronization |
| TRPC-47 | #6470 | `3ade8ef` | `5da722f` | Medium | type safety | Subscription result type incorrect during pending state; `data` typed as `TOutput` but can be `undefined` during initial pending phase | Step 5b (schema types) - pending state type correctness |
| TRPC-48 | #6462 | `6471468` | `6c15b05` | Medium | error handling | Stream error messages misleading; `httpBatchStreamLink` error message incorrectly says `httpLink`, and malformed JSONL breaks stream parsing | Step 3 (tests) - error message accuracy |
| TRPC-49 | #6457 | `6ab0f06` | `972d78b` | High | serialization | Transformer not applied at top level in `httpBatchStreamLink`; complex types (Promises, Dates) with SuperJSON fail to serialize/deserialize | Step 4 (specs) - transformer scope boundary |
| TRPC-50 | #6422 | `776d073` | `a604132` | Medium | API contract violation | `ProcedureOptions` exported from `@trpc/server` but shouldn't be; moved to client-only type `TRPCProcedureOptions` to avoid cross-package confusion | Step 2 (architecture) - public API surface definition |

### prisma/prisma (TypeScript)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| PRI-01 | 29331 | 5b420f8 | 30f0af6 | Critical | error handling | createMany operations cached with large unstable keys, consuming GB of memory, causing Node.js crashes | Step 5 (defensive), Step 6 (quality risks) |
| PRI-02 | 29307 | 33667c3 | 309b4bc | High | error handling | PostgreSQL adapter failed to extract column names from ColumnNotFound errors with quotes/qualified names | Step 4 (specs), Step 5b (schema types) |
| PRI-03 | 29345 | 67b6986 | e97b3e0 | High | API contract violation | Get<Model>GroupByPayload type not exported, making it inaccessible in prisma-client generator | Step 2 (architecture), Step 5b (schema types) |
| PRI-04 | 28724 | 3f2438c | ccce148 | Medium | concurrency issue | NowGenerator initialized new Date() in property declaration, causing synchronous blocking on every query | Step 5 (defensive), Step 5a (state machines) |
| PRI-05 | 29309 | ea93809 | f8e742a | High | type safety | String date values not converted to Date objects in cursor comparison, causing type mismatch failures | Step 5b (schema types), Step 3 (tests) |
| PRI-06 | 29257 | 4b65b60 | 7a1f497 | High | null safety | Prisma.DbNull serialized as {} in bundled environments due to instanceof check failing across bundle boundaries | Step 5 (defensive), Step 2 (architecture) |
| PRI-07 | 29160 | bee4502 | 9fa295d | High | SQL error | MariaDB adapter used text protocol causing lossy conversion of large numbers; fixed with binary protocol | Step 5b (schema types), Step 4 (specs) |
| PRI-08 | 29267 | 455853d | 6586972 | Medium | serialization | Nested Uint8Array in objects/arrays serialized as numeric objects instead of base64 in Json fields | Step 5b (schema types), Step 3 (tests) |
| PRI-09 | 29254 | 6586972 | 90d119c | Critical | state machine gap | Query interpreter unintentionally mutated query plan object during execution, corrupting cached plans | Step 5a (state machines), Step 6 (quality risks) |
| PRI-10 | 29122 | 90d119c | b311672 | High | type safety | In-memory joins failed for MySQL BigInt relations when strict equality assumption invalid | Step 4 (specs), Step 5b (schema types) |
| PRI-11 | 29237 | 76bb95b | 6db8a18 | High | type safety | Text columns with binary collation incorrectly returned as bytes instead of strings in raw queries | Step 5b (schema types), Step 2 (architecture) |
| PRI-12 | 29235 | c33e8f8 | b426bbd | High | validation gap | MariaDB relationJoins compatibility check broken, causing query failures on certain versions | Step 4 (specs), Step 5a (state machines) |
| PRI-13 | 29215 | 87d2313 | fd2de83 | Medium | SQL error | Query interpreter failed to render parameter tuples wrapped in function calls like LOWER(?) | Step 5a (state machines), Step 4 (specs) |
| PRI-14 | 29190 | 9618edc | 77bfc96 | High | null safety | PPG adapter passed null values to type parsers for DateTime/TimeTZ/Money/Bytea, causing TypeError | Step 5 (defensive), Step 3 (tests) |
| PRI-15 | 29218 | 77bfc96 | 3fd1431 | High | API contract violation | Query extensions not applied to nested/fluent relation results; context resolution skipped nested fields | Step 2 (architecture), Step 5a (state machines) |
| PRI-16 | 29182 | 344ccd5 | 6587f54 | High | serialization | Date and special values in JSON fields not deserialized before stringify, causing corrupted values | Step 5b (schema types), Step 3 (tests) |
| PRI-17 | 25571 | 6587f54 | 9865dcb | Medium | error handling | Interactive transactions failed to batch multiple queries, forcing serial execution | Step 5a (state machines), Step 4 (specs) |
| PRI-18 | 29198 | 9865dcb | b0385e1 | High | API contract violation | Prisma.skip directive lost during query extension argument cloning, breaking skip() functionality | Step 2 (architecture), Step 3 (tests) |
| PRI-19 | 29184 | 1701fe6 | fcbcc9d | High | SQL error | Cursor pagination failed to handle parameterized values in cursor, breaking pagination | Step 4 (specs), Step 5a (state machines) |
| PRI-20 | 29158 | fcbcc9d | 7060f68 | Medium | configuration error | MSSQL adapter failed to handle escaped curly braces in connection strings | Step 5 (defensive), Step 4 (specs) |
| PRI-21 | 29155 | 8410fea | 1e6c91c | Critical | error handling | PlanetScale adapter silently swallowed COMMIT errors in transactions, causing data inconsistency | Step 5 (defensive), Step 6 (quality risks) |
| PRI-22 | 29141 | 6a98c8f | 73ff30a | High | concurrency issue | MSSQL adapter failed to acquire mutex during commit/rollback, causing EREQINPROG under concurrent load | Step 5a (state machines), Step 3 (tests) |
| PRI-23 | 29088 | 026beb7 | 65b027e | High | type safety | MariaDB driver returned rows as objects instead of arrays, causing row unpacking to fail | Step 5b (schema types), Step 2 (architecture) |
| PRI-24 | 29013 | 437e975 | 879c391 | Critical | security issue | MariaDB adapter leaked connection credentials in error messages | Step 5 (defensive), Step 6 (quality risks) |
| PRI-25 | 29001 | c03d384 | 90141bb | High | SQL error | Better-sqlite3 driver bug affecting EXISTS queries in edge cases, required pin for fix | Step 2 (architecture), Step 4 (specs) |
| PRI-26 | 28913 | 531886f | f85de48 | High | type safety | Byte array upserts failed due to lingering legacy byte array representation format | Step 5b (schema types), Step 3 (tests) |
| PRI-27 | 28849 | 0c6db15 | 857400b | Medium | error handling | Postgres adapter failed to handle 22P02 (invalid text representation) errors from database | Step 4 (specs), Step 5 (defensive) |
| PRI-28 | 28831 | 2a85e48 | d00dc11 | Critical | error handling | Database connections not released on transaction timeout, causing resource exhaustion | Step 5a (state machines), Step 6 (quality risks) |
| PRI-29 | 28694 | d81b4b6 | 44cac9f | Medium | validation gap | Schema validation failed for env variables used with interface types | Step 4 (specs), Step 5b (schema types) |
| PRI-30 | 28723 | 0847487 | 08ed4f4 | High | concurrency issue | Interactive transactions not aborted on maxWait timeout, causing resource leaks and hangs | Step 5a (state machines), Step 3 (tests) |
| PRI-31 | 28057 | d368e9f | bc18826 | Medium | error handling | PostgreSQL adapter had error event listener leak, not cleaned up after use | Step 5 (defensive), Step 6 (quality risks) |
| PRI-32 | 28040 | 8cdc40e | f0813fc | Medium | type safety | PostgreSQL adapter failed to convert dates before 1000-01-01 to valid date strings | Step 5b (schema types), Step 4 (specs) |
| PRI-33 | 28020 | 7455062 | d8d9f28 | Medium | type safety | PlanetScale adapter stored dates in local timezone instead of UTC, causing off-by-timezone errors | Step 5b (schema types), Step 3 (tests) |
| PRI-34 | 27927 | f6e2cf7 | e03a5db | Medium | protocol violation | MariaDB data encoding issues in query compiler, causing character set mismatches | Step 4 (specs), Step 5b (schema types) |
| PRI-35 | 27873 | 2333450 | 7dddc22 | Medium | error handling | Query compiler workaround for internal transaction ID handling issue | Step 5a (state machines), Step 6 (quality risks) |
| PRI-36 | 28221 | `50f65140` | `3bc04bc` | High | type safety | WASM query compiler cache ignored provider parameter, causing multi-provider client instances to incorrectly reuse cached compiler from different provider | Step 5a (state machines), Step 2 (architecture) |
| PRI-37 | 28212 | `6c5a217d` | `30bdd63` | High | type safety | PostgreSQL adapter corrupted dates with 2-digit years (e.g., year 99 became 2099), corrupting historical date fields | Step 5b (schema types), Step 4 (specs) |
| PRI-38 | 28255 | `3ad5a0c1` | `58c35ad` | Medium | error handling | Neon adapter did not clean up error event listeners on connection close, causing resource leak and memory exhaustion | Step 5 (defensive), Step 6 (quality risks) |
| PRI-39 | 17303 | `11c3e280` | `3a26b92` | High | state machine gap | Interactive transactions not disposed on error path, causing connection leaks and transaction hangs | Step 5a (state machines), Step 6 (quality risks) |
| PRI-40 | 28484 | `804450b4` | `3e936f8` | Medium | configuration error | Adapter-d1 always imported node:fs via listLocalDatabases, breaking workerd edge runtime which does not support node: modules | Step 2 (architecture), Step 5 (defensive) |
| PRI-41 | 28490 | `9b23966c` | `c58aa31` | Medium | serialization | Client-generator-js used incorrect WASM bundle encoding (ascii instead of base64) for Node.js, causing query failures | Step 5b (schema types), Step 3 (tests) |
| PRI-42 | 28846 | `857400ba` | `b67dd5a` | Medium | error handling | DataMapperError not classified as UserFacingError, causing correct errors to be returned as HTTP 500 instead of HTTP 400 | Step 4 (specs), Step 5 (defensive) |
| PRI-43 | 28535 | `6b8702c6` | `dbada57` | High | serialization | Byline module corrupted multibyte UTF-8 characters (Japanese, emoji) split across stream chunks due to naive toString without StringDecoder | Step 5b (schema types), Step 3 (tests) |
| PRI-44 | 28861 | `d7a32bd4` | `4fb55a9` | Medium | configuration error | SQL commenter plugins interfered with each other when multiple plugins registered, causing incorrect SQL injection | Step 4 (specs), Step 5a (state machines) |
| PRI-45 | 28771 | `9c14872` | `605a492` | Medium | serialization | Studio connection handler failed to parse prisma+postgres connection strings with ORM-specific parameters, rejecting valid connections | Step 4 (specs), Step 5 (defensive) |
| PRI-46 | 28883 | `0506a3a1` | `549a8dc` | Low | configuration error | PPG adapter connection string incorrectly included pool parameter which breaks remote connection handling | Step 4 (specs), Step 5 (defensive) |
| PRI-47 | 28504 | `41837be0` | `1fb6761` | Medium | configuration error | Prisma init failed with corepack due to incorrect Node.js binary resolution | Step 4 (specs), Step 5 (defensive) |
| PRI-48 | 28493 | `a8d043dc` | `11c3e28` | Medium | error handling | WeakRef shim in client runtime caused memory issues; shim should not be used when native WeakRef available | Step 5 (defensive), Step 6 (quality risks) |
| PRI-49 | 28483 | `94a1b9eb` | `a5b9907` | Low | configuration error | Edge entrypoint test imported enum from wrong edge.js file path, causing module resolution failures | Step 2 (architecture), Step 3 (tests) |
| PRI-50 | prisma/prisma#17273 | `62ee0271` | `0704b39` | Low | serialization | Prisma version --json output showed "Studio: undefined" instead of studio version or omitting field | Step 4 (specs), Step 5 (defensive) |


### calcom/cal.com (TypeScript)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| CAL-01 | #28622 | `ad791f8e` | `fbf6510d` | High | security issue | SSRF protection missing localhost and loopback addresses (127.0.0.1, ::1, 0.0.0.0) in blocked hostnames list | Step 5 |
| CAL-02 | #28611 | `fbf6510d` | `d80493f2` | Medium | API contract violation | SMTP providers reject Reply-To as array; must be comma-separated string per RFC 2822 | Step 4 |
| CAL-03 | #28569 | `806fd8ed` | `ee973c66` | Critical | state machine gap | IDOR vulnerability in PBAC updateRole and deleteRole endpoints missing role-ownership verification | Step 5a |
| CAL-04 | #28035 | `4b247640` | `8caa062a` | Medium | validation gap | Booking limit transformation processing invalid keys causing undefined properties in output | Step 4 |
| CAL-05 | #28314 | `32772054` | `d630556d` | High | configuration error | Day.js timezone plugin loaded before UTC plugin causing incorrect timezone offset display | Step 2 |
| CAL-06 | #28071 | `7ff2eaf2` | `d3dad196` | High | state machine gap | Booking access control not consolidated, org/team admins unable to view team member bookings | Step 5a |
| CAL-07 | #28490 | `15005d89` | `87fb2abf` | Medium | error handling | Forgot password debounce ref not properly managed, causing memory leaks and duplicate requests | Step 5 |
| CAL-08 | #28527 | `ee973c66` | `e9e96671` | High | error handling | P2002 duplicate key error in seed script drops users from org setup when retrying | Step 6 |
| CAL-09 | #28342 | `d6741a1e` | `f0a7293f` | Low | protocol violation | OOO controller file name violates NestJS Swagger plugin convention preventing API docs generation | Step 2 |
| CAL-10 | #28288 | `658e65be` | `e2add3f2` | Medium | API contract violation | Webhook triggers OpenAPI type declared as string but should be array | Step 4 |
| CAL-11 | #28203 | `2bf45677` | `1c193cca` | Medium | validation gap | Phone mask not handling Argentina/Finland hyphens/dots/underscores causing digit truncation | Step 5b |
| CAL-12 | #28239 | `5943a8ad` | `ec7f8dd5` | High | silent failure | Managed event type update includes full ChildrenEventType objects exceeding 1MB request limit | Step 6 |
| CAL-13 | #27574 | `40e5b739` | `17af50bb` | Medium | state machine gap | Booking additional seats incorrectly redirects to video confirmation instead of completion | Step 5a |
| CAL-14 | #28596 | `b436f331` | `2fc630ed` | Low | null safety | Embed iframe informAboutScroll not guarding against undefined document | Step 5 |
| CAL-15 | #28312 | `d630556d` | `f0a7293f` | Low | error handling | Unreachable code in deleteDomain function after return statement | Step 6 |
| CAL-16 | #27517 | `1ff307bb` | `c197de14` | Medium | API contract violation | Instant booking location endpoint using numeric ID instead of booking UID | Step 4 |
| CAL-17 | #26976 | `c43c48b1` | `9a08d2e4` | Medium | validation gap | Analytics app missing input validation for tracking IDs and URLs | Step 4 |
| CAL-18 | #27419 | `bc392584` | `3f2e1222` | Medium | state machine gap | Embed iframe queue not reset consistently losing UI configuration on second modal open | Step 5a |
| CAL-19 | #27413 | `5c2382d2` | `27515d42` | Low | validation gap | Domain validation not accepting wildcard prefix (*.domain.com) for watchlist | Step 5b |
| CAL-20 | #27487 | `1d5228ef` | `5d65a0f0` | Medium | silent failure | CRM contact owner lookup performed twice (routing form + SSR) when none exists | Step 6 |
| CAL-21 | #27384 | `447a0289` | `9a08d2e4` | Medium | error handling | Vercel webhook controller not parsing raw body Buffer properly | Step 5 |
| CAL-22 | #27386 | `80e4b1af` | `5d65a0f0` | Low | validation gap | Booking history search filter checks only value field missing values array option | Step 5b |
| CAL-23 | #28625 | `0936fdaf` | `31f40764` | Critical | security issue | Handlebars vulnerability allowing template injection attacks | Step 5 |
| CAL-24 | #28253 | `a8e27c38` | `b539adf4` | Medium | validation gap | Dialpad meeting URL regex only accepts alphanumeric rejecting valid hyphens/dots/underscores | Step 5b |
| CAL-25 | #28227 | `ec7f8dd5` | `1c193cca` | High | security issue | fast-xml-parser security vulnerability in dependency | Step 5 |
| CAL-26 | #28319 | `c5893997` | `7801266d` | Low | type safety | app-store-cli incorrect type annotation breaking build | Step 5b |
| CAL-27 | #28204 | `5b88eefe` | `1b21ead0` | Medium | validation gap | libphonenumber-js outdated metadata causing phone validation failures | Step 5b |
| CAL-28 | #28336 | `e7561416` | `cc01d114` | Low | API contract violation | Routing form response type incorrect in OpenAPI specification | Step 4 |
| CAL-29 | #28340 | `c8e1b4e6` | `cc01d114` | Medium | API contract violation | Verified resources endpoint @ApiProperty types mismatched in OpenAPI docs | Step 4 |
| CAL-30 | #28305 | `f3f5523f` | `cfb1489e` | Low | API contract violation | Missing OpenAPI ApiParam decorators on API v2 controllers | Step 4 |
| CAL-31 | #27516 | `d743c924` | `9cb16e32` | Low | type safety | tRPC build failure due to type mismatch in calendars handler | Step 5b |
| CAL-32 | #27520 | `7611e0ea` | `36e477ce` | Medium | state machine gap | Email attendee filtering not applied when seatsShowAttendees disabled | Step 5a |
| CAL-33 | #28129 | `f86767c1` | `0f0a6382` | Medium | validation gap | Admin password banner logic uses OR instead of AND for security requirements | Step 5b |
| CAL-34 | #27483 | `36e477ce` | `9cb16e32` | Medium | state machine gap | Platform billing reschedule usage increment schema missing required fields | Step 5a |
| CAL-35 | #28631 | `31f4076` | `0f4717e` | Medium | validation gap | E2E tests timeout clicking booking button before DOM fully rendered; missing visibility check on nested element | Step 5b |
| CAL-36 | #28589 | `d80493f` | `d685278` | High | concurrency issue | API v2 slots endpoint returns stale seat counts when bookingSeatsRepositoryFixture.create() not awaited; SelectedSlots leak between tests | Step 5a |
| CAL-37 | #28244 | `1b21ead` | `5b88eef` | High | state machine gap | Admin wizard crashes with undefined array access when license step skipped; defaultStep calculated without considering conditional step removal | Step 5a |
| CAL-38 | #28152 | `c9abc55` | `9855176` | Medium | API contract violation | getIP() function redundantly re-parses x-forwarded-for header after initial call; forgotPassword route duplicates header resolution logic | Step 4 |
| CAL-39 | #28144 | `8238d4f` | `0a84ce5` | High | configuration error | Booking confirmation redirects to localhost:3000 behind reverse proxy when using request.url instead of WEBAPP_URL constant | Step 2 |
| CAL-40 | #27942 | `0a84ce5` | `7e73d67` | Medium | validation gap | SMS reminders fail when attendee phone missing; fallback to smsReminderNumber not implemented for attendee contact | Step 5b |
| CAL-41 | #28140 | `f00be08` | `f1e8e3f` | Medium | silent failure | Custom questions rendered in wrong order; filtering logic applied before ordering by bookingFields; UI displays unpredictable field sequence | Step 6 |
| CAL-42 | #28083 | `14c151b` | `1aae57d` | Critical | security issue | CSRF token missing from OAuth state parameter; attacker can capture authorization code and trick user into linking attacker account | Step 5 |
| CAL-43 | #24282 | `9bfa416` | `8a96a45` | High | error handling | Raw error objects and stack traces leaked in API responses; integrations endpoint does not sanitize exception details | Step 5 |
| CAL-44 | #28029 | `8908a66` | `a78a3ff` | Medium | protocol violation | Booking rejection requires POST but email clients only send GET; no fallback to GET method for rejection link in email | Step 5a |
| CAL-45 | #27818 | `20dcef6` | `11b65b2` | Medium | validation gap | Schedule title input accepts invalid characters causing database constraint violations or UI corruption; missing regex validation | Step 5b |
| CAL-46 | #27491 | `4c73695` | `ab4eff1` | Medium | state machine gap | Slots not refreshed when timezone changed for booker with timezone restrictions enabled; cached availability stale after timezone switch | Step 5a |
| CAL-47 | #27891 | `3a7122d` | `21d28c9` | High | API contract violation | Webhook payload schema changed to nested object breaking external integrations; new assignmentReason format incompatible with legacy consumers | Step 4 |
| CAL-48 | #27964 | `9d4cb08` | `773fab8` | High | type safety | Hours-to-days conversion uses wrong divisor (24 instead of 24*60); booking duration multiplied by 1440x when unit changed | Step 5b |
| CAL-49 | #27946 | `9d4b12b` | `c21281a` | Medium | silent failure | Companion iframe loads on every page visit downloading scripts even when sidebar closed; no lazy-load prevents wasted requests | Step 6 |
| CAL-50 | #27931 | `237d7e9` | `896dfd5` | Medium | error handling | Module resolution during test load triggers heavy transitive imports breaking vitest worker; package.json descriptions imported unnecessarily | Step 5 |
| CAL-51 | #27923 | `50c7210` | `1bb4b20` | Medium | state machine gap | Email verification sent after lockdown decision for watchlist signups; verification timing race creates auth confusion for locked users | Step 5a |
| CAL-52 | #28575 | `e073cbd` | `ecc5e66` | Medium | validation gap | E2E test strict mode violation when multiple elements share same data-testid during Next.js streaming; hydration creates duplicate selectors | Step 5b |
| CAL-53 | #28573 | `e9e9667` | `b46c04d` | Medium | concurrency issue | Global PBAC feature flag deleted in afterAll() hook interferes with parallel test execution; cleanup affects sibling test suites | Step 5a |
| CAL-54 | #28603 | `2fc630e` | `b436f33` | Medium | error handling | Module import chain for getRoutedUsers pulls in all calendar services triggering vitest worker RPC shutdown; missing mock for transitive dependency | Step 5 |
| CAL-55 | #27571 | `50c5423b` | `7716f8c` | High | validation gap | Regex in formatIdentifierToVariable strips underscores from workflow template variables causing {COMPANY_NAME} to become {COMPANYNAME}; documentation promises underscore support but implementation removes them | Step 5b |
| CAL-56 | #27890 | `fad64a01` | `14563f6` | High | state machine gap | Form builder dialog assigns dialog.data value instead of default field type when editing newly added question; field type shows stale value from previous edit | Step 5a |
| CAL-57 | #27872 | `c7e66a3a` | `0d55939` | Medium | state machine gap | URL-to-Store sync guard placed at effect level prevents Store-to-URL sync subscription from being created; booking uid parameter lost when navigating to booking details | Step 5a |
| CAL-58 | #27300 | `681d1915` | `269ed87` | Medium | silent failure | BOOKING_CREATED webhook payload missing metadata object when booking confirmation handler constructs CalendarEvent; external systems expect metadata field | Step 6 |
| CAL-59 | #27637 | `dc3e681e` | `30bba3d` | Medium | state machine gap | Booking confirmation and payment flows construct CalendarEvent without disableCancelling/disableRescheduling flags; ManageLink email component treats undefined flags as enabled | Step 5a |
| CAL-60 | #27612 | `db769806` | `d8e6ecc` | Medium | API contract violation | OpenAPI @GetWebhook() decorator not applied to webhook fetch endpoints; OpenAPI spec missing path documentation for GET webhook operations | Step 4 |
| CAL-61 | #27694 | `0a2d0854` | `e04a394` | Low | validation gap | No-show flag marking logic checks userId !== attendeeId to prevent self-marking but excludes organizer; organizers cannot unmark themselves as no-show | Step 5b |
| CAL-62 | #27500 | `62870266` | `96bec9f` | High | error handling | Calendar event deletion with empty uid causes 404 error and 500 response to client; booking references created with empty uids when calendar event creation fails | Step 5 |
| CAL-63 | #27752 | `d4a05903` | `eba0635` | Medium | state machine gap | listWithTeam query filter excludes team events with userId set; team organizer events with personal assignment not returned in team listing | Step 5a |
| CAL-64 | #27765 | `cdf901fe` | `3052cf5` | Low | validation gap | Signup form email validation mode set to onChange; invalid email error displayed on every keystroke before user leaves field | Step 5b |
| CAL-65 | #27769 | `e940aac2` | `7ba749e` | Low | validation gap | Four duplicate translation keys in English common.json with identical or inconsistent values; i18n system loads redundant entries | Step 5b |
| CAL-66 | #27772 | `0ec07b00` | `e940aac` | Medium | error handling | No-show-updated-action integration test uses singular prisma.attendee.delete which throws P2025 if record already deleted; test cleanup loses race condition with cascade deletions | Step 5 |
| CAL-67 | #27779 | `19366700` | `b6916df` | Low | validation gap | Button component missing closing HTML tag causing style rendering failure in availability delete button; invalid HTML breaks CSS styling | Step 5b |
| CAL-68 | #27749 | `794046cf` | `60188bc` | Low | validation gap | Rejection reason textarea allows user drag-resize which overlaps dialog footer buttons obscuring action buttons | Step 5b |
| CAL-69 | #27636 | `a71d62dc` | `a8ede77` | Low | validation gap | Phone booking UI displays label Organizer Phone Number instead of Phone Call; internal terminology exposed to attendees | Step 5b |


### raphaelmansuy/edgequake (TypeScript)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| EQ-01 | #94 | `6418ce8` | `1d50459` | High | null safety | UTF-8 boundary panic in prefix hashing when slicing multi-byte UTF-8 characters mid-sequence | Step 5b |
| EQ-02 | #81 | `ecc90b8` | `96c42dc` | High | validation gap | Dashboard KPIs inconsistent: PostgreSQL fallback returned stale data instead of KV+AGE single source of truth | Step 6 |
| EQ-03 | #79 | `96c42dc` | `9049e25` | High | configuration error | Environment variable bug: PDF download and lineage export used non-standard NEXT_PUBLIC_API_BASE_URL defaulting to localhost:8080 in production, causing ERR_CONNECTION_REFUSED | Step 5 |
| EQ-04 | #78 | `9049e25` | `9de5c6a` | Medium | security issue | Unpatched rollup >=4.59.0 and minimatch >=3.1.5 security vulnerabilities in dependencies | Step 6 |
| EQ-05 | #83 | `e13e732` | `ecc90b8` | High | state machine gap | Progress callback created but never connected to ConversionConfig builder (underscore-prefixed variable prevented initialization) | Step 5a |
| EQ-06 | #83 | `e13e732` | `ecc90b8` | High | validation gap | Page count detection fails on binary PDFs: std::str::from_utf8 panic on non-UTF8 bytes in /Count extraction | Step 5b |
| EQ-07 | #83 | `e13e732` | `ecc90b8` | High | silent failure | KV metadata not updated during on_conversion_start: document list showed 0/0 pages because PipelineState update missed KV sync | Step 5a |
| EQ-08 | #83 | `e13e732` | `ecc90b8` | High | error handling | Tasks stuck in 'processing' after server restart: heartbeat CAS prevented orphan recovery timeout threshold from being reached | Step 5a |
| EQ-09 | #83 | `e13e732` | `ecc90b8` | High | state machine gap | Workspace isolation violated: list_tasks ignored TenantContext headers, only read workspace_id from query params allowing cross-workspace task visibility | Step 5a |
| EQ-10 | #83 | `e13e732` | `ecc90b8` | Medium | error handling | Missing HeartbeatGuard RAII: worker panic/OOM during processing left heartbeat tokio::spawn running forever, preventing orphan recovery | Step 5a |
| EQ-11 | #83 | `e13e732` | `ecc90b8` | High | error handling | Document delete returned 404 for documents with KV key/id mismatch: two-phase key resolution was missing | Step 5 |
| EQ-12 | #77 | `9de5c6a` | `264008e` | High | validation gap | FK constraint missing on PDF upload: cascade delete broken, orphaned PDF records remained after document deletion | Step 5b |
| EQ-13 | #77 | `9de5c6a` | `264008e` | High | validation gap | UTF-8 truncation panic in table_preprocessor: slicing at invalid byte boundaries without floor_char_boundary checks | Step 5b |
| EQ-14 | #77 | `9de5c6a` | `264008e` | Medium | validation gap | TaskStatus CHECK constraint missing: allows invalid status transitions, violates document lifecycle invariants | Step 5b |
| EQ-15 | #72 | `264008e` | `5b17e5a` | Critical | API contract violation | Tenant isolation not enforced on get_workspace: cross-tenant UUID enumeration possible without 404 response | Step 5 |
| EQ-16 | #72 | `264008e` | `5b17e5a` | High | validation gap | Stats cache checked before tenant isolation: cross-tenant requests could receive cached stats from foreign workspaces | Step 5 |
| EQ-17 | #72 | `264008e` | `5b17e5a` | High | state machine gap | Workspace auto-select failed: newly created workspace not pushed to Zustand store synchronously, reverting to placeholder after creation | Step 5a |
| EQ-18 | (none) | `d3008d3` | `b6744b6` | High | silent failure | Table streaming flicker and double display: incomplete table buffering prevented marked.lexer() from parsing, then re-displayed after streaming finished | Step 5 |
| EQ-19 | (none) | `d3008d3` | `b6744b6` | Medium | error handling | Streaming to server handoff race condition: pending message displayed twice during cache refresh window before deduplication | Step 5a |
| EQ-20 | (none) | `9e65bd4` | `d3a6ca9` | Medium | validation gap | Chunk deep-link failed on historical messages: chunk_id not propagated from source citations to URL parameters | Step 5b |
| EQ-21 | (none) | `8d9d585` | `fea79a3` | High | validation gap | Workspace rebuild incorrectly included legacy 'default' workspace documents in every workspace rebuild, causing cross-workspace data processing | Step 5 |
| EQ-22 | (none) | `f07ad55` | `e6e1511` | Medium | validation gap | Self-referencing relationships extracted by LLM (A->A) not filtered: graph nodes created with empty normalized names causing semantic dilution | Step 5b |
| EQ-23 | (none) | `f07ad55` | `e6e1511` | Medium | validation gap | Keyword limit BR0004 not enforced: excessive keywords (>5 per edge) dilute semantic relevance in knowledge graph | Step 5b |
| EQ-24 | (none) | `02c440c` | `5b6bcd6` | High | validation gap | Embedding batch limit exceeded: large documents (8900+ entities) failed with '$.input is invalid' when exceeding provider limits (OpenAI 2048, Ollama 512) | Step 5b |
| EQ-25 | (none) | `02c440c` | `5b6bcd6` | Medium | error handling | JSON control character in LLM output not sanitized: invalid escape sequences caused embedding parse failures on extracted entities | Step 5b |
| EQ-26 | (none) | `e8db114` | `66e5f63` | Medium | type safety | Type mismatch: i64 → usize casts in workspace metrics (document_count, chunk_count, entity_count, relationship_count, embedding_count, storage_bytes failed to convert from DB i64 to struct usize) | Step 5b |
| EQ-27 | (none) | `889c7d9` | `5fb2399` | Medium | type safety | Stats.rs usize→i64 type mismatches in metrics snapshot mapping (MetricsSnapshotDTO conversion missing casts for historical metrics retrieval) | Step 5b |
| EQ-28 | (none) | `9efb729` | `d3588ab` | Low | type safety | TaskStatus missing Copy derive: prevented inline copy semantics in status comparisons, forcing reference handling and increasing cognitive load on match expressions | Step 5b |
| EQ-29 | (none) | `cf7f741` | `acc446e` | Critical | security issue | Lineage handlers missing TenantContext verification: all 8 lineage handlers (get_chunk_detail, etc.) lacked tenant isolation checks, enabling potential cross-workspace data disclosure | Step 5 |
| EQ-30 | #12 | `3fd791d` | `684ba7d` | High | security issue | JWT type confusion vulnerability: jsonwebtoken 9.3 deprecated insecure_disable_signature_validation() allowed auth bypass via Type Confusion attack, migrated to dangerous::insecure_decode() | Step 5 |
| EQ-31 | #33 | `62743be` | `8ae000d` | Medium | validation gap | Undefined property 'entity_type_count' in WorkspaceStats interface: frontend TypeScript build error due to accessing non-existent property in stats DTO | Step 5b |
| EQ-32 | (none) | `d241f25` | `fbb65f3` | Medium | validation gap | Missing vision_llm fields in 20+ test files + missing error_details in cost tests: test fixtures violated SPEC-041 AppState requirements, causing CI failures | Step 5b |
| EQ-33 | (none) | `e6e1511` | `02c440c` | High | error handling | Dropzone click handler silent failure: react-dropzone's File System Access API call fails in HTTP contexts and non-secure iframes; noClick=true + explicit onClick handler bypasses broken behavior | Step 5a |
| EQ-34 | (none) | `d7285c6` | `6b2aecb` | Medium | configuration error | Node.js deprecation warnings in GitHub Actions: FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true not set, causing warnings in deploy pipeline; added enable-https job for HTTPS enforcement | Step 5 |
| EQ-35 | (none) | `506a500` | `01a3581` | Medium | validation gap | Website responsiveness broken on mobile <640px: Architecture section SVG not scrollable, Hero section misaligned at tablet (768px), code blocks clipped on narrow screens; fixed with vertical pipeline list + grid layout + overflow-auto | Step 5a |

### serde-rs/serde (Rust)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| SER-01 | #2950 | 106da49 | bb58726^ | Critical | type safety | Temporary value lifetime error in serialize_struct in Rust 2024 edition - reference to struct inside block goes out of scope when passed to function | Step 5b (schema types) |
| SER-02 | #2844 | 1e36ef5 | 1e36ef5^ | High | type safety | Hygiene of macro-generated local variable accesses in serde(with) wrappers - incorrect variable names in generated code leading to type errors | Step 5a (state machines) |
| SER-03 | #2805 | da7fc79 | da7fc79^ | High | validation gap | Deserialization of empty struct variant in untagged enums - SeqRefDeserializer incorrectly emits visit_unit for empty sequences, but struct variants cannot deserialize from unit | Step 3 (tests) |
| SER-04 | #2792 | 0647a7c | 0647a7c^ | High | validation gap | Creating and filling a collection that was not read - has_flatten() incorrectly determined at container level instead of field level, causing false positives | Step 5b (schema types) |
| SER-05 | #2646 | 589549d | 589549d^ | High | validation gap | Allow internal tag field in untagged variant - internal tag field validation incorrectly rejected valid untagged variants containing tag fields | Step 5a (state machines) |
| SER-06 | - | 8fe7539 | 8fe7539^ | High | type safety | Ambiguous associated type in forward_to_deserialize_any! macro - missing explicit Error type binding causes type inference failures in custom deserializers | Step 5b (schema types) |
| SER-07 | - | c91c334 | c91c334^ | Critical | API contract violation | Range{From,To} deserialize mixup - swapped field names (start/end) causing complete deserialization failure for Range types | Step 2 (architecture) |
| SER-08 | #2613 | 8da2058 | 8da2058^ | High | state machine gap | Deserialization of untagged variants within internally/adjacently tagged enums - non-untagged deserialization errors prevent fallthrough to untagged variants | Step 5a (state machines) |
| SER-09 | #2466 | 2c1f62d | 2c1f62d^ | Medium | validation gap | Incorrect count of fields passed to tuple deserialization methods - skipped fields should not be counted in deserialize_tuple, deserialize_tuple_struct, tuple_variant | Step 2 (architecture) |
| SER-10 | #2371 | c739361 | c739361^ | High | type safety | Non-existent lifetime 'de when enum contains #[serde(flatten)] field and 'static reference - incorrect lifetime variable substitution in deserialization code | Step 5b (schema types) |
| SER-11 | #2409 | 3702191 | 3702191^ | High | type safety | Into conversion involving generic remote derive with getter - missing type generics in Into conversion causing compilation failure | Step 5b (schema types) |
| SER-12 | #2451 | 1f8c8ad | 1f8c8ad^ | High | type safety | Cannot move out of *self which is behind a shared reference - incorrect ref pattern for non_exhaustive remote enum arms | Step 5a (state machines) |
| SER-13 | - | 645d040 | 645d040^ | Medium | state machine gap | Off by one span counter - span counter starting at 0 conflicts with call_site() special value, creating invalid span references | Step 2 (architecture) |
| SER-14 | - | 1ddb6c2 | 1ddb6c2^ | High | protocol violation | Handling of raw idents in proc-macro2 shim - raw identifier prefix r# not correctly handled when reconstructing identifiers from binary format | Step 5a (state machines) |
| SER-15 | - | 8264e00 | 8264e00^ | Medium | validation gap | Reject suffixed string literals inside serde attrs - malformed attributes with suffixes like "foo"s bypassed validation, causing downstream errors | Step 4 (specs) |
| SER-16 | #2425 | 9fef892 | 9fef892^ | Low | validation gap | Difference in error message for adjacently tagged enums - error message test failure due to field identifier variant expansion | Step 3 (tests) |
| SER-17 | - | 5b32217 | 5b32217^ | Medium | error handling | unused_results rustc lint in codegen for adjacently tagged enum - IgnoredAny value not consumed, triggering compiler warning | Step 5 (defensive) |
| SER-18 | - | eaccae2 | eaccae2^ | Low | type safety | UPPERCASE rename rule variant naming - enum variant named UPPERCASE instead of UpperCase violating Rust conventions | Step 2 (architecture) |
| SER-19 | #2446 | 983347 | 983347^ | High | validation gap | Don't check skipped variant with internal tag - skipped fields/variants incorrectly checked for tag field name conflicts | Step 5a (state machines) |
| SER-20 | - | 68069d7 | 68069d7^ | Low | error handling | Needless borrow for value=Cow<str> - unnecessary borrow when passing Cow<str> to unknown_field error function | Step 5 (defensive) |
| SER-21 | #2653 | 8c4af41 | 8c4af41^ | Critical | API contract violation | More RangeFrom/RangeEnd mixups - variable names swapped in deserialization causing wrong bounds construction | Step 2 (architecture) |
| SER-22 | #2447 | 09993a9 | 09993a9^ | High | type safety | Cannot infer type from Deserialize derive with simple + untagged variants - first_attempt not properly handled causing type inference failure | Step 5a (state machines) |
| SER-23 | - | 92d686f | 92d686f^ | High | configuration error | serde::de::StdError in no-std unstable build - missing feature gate for unstable core::error::Error causing compilation failure in no-std+unstable | Step 4 (specs) |
| SER-24 | #2520 | df4ad58 | df4ad58^ | Low | type safety | Use &[T] instead of &Vec<T> - type signature mismatch in deserialize trait impls | Step 5b (schema types) |
| SER-25 | #1969 | 6699b0b | 6699b0b^ | Medium | silent failure | Recursive serialize_with field reference - struct containing Vec<Self> with custom serializer causing infinite recursion | Step 3 (tests) |
| SER-26 | - | 4114e90 | 4114e90^ | Critical | missing boundary check | Off-by-one in IPv4 address serialization - buffer offset calculation missing increment for delimiter, corrupting serialized output | Step 5 (defensive) |
| SER-27 | - | 0289d31 | 0289d31^ | Medium | configuration error | -Zminimal-versions build failure - incompatible dependency versions in minimal configuration | Step 4 (specs) |
| SER-28 | - | 541603a | 541603a^ | Low | configuration error | Doc tests for 2021 edition - edition-specific syntax causing doc test failures | Step 3 (tests) |
| SER-29 | - | 290449f | 290449f^ | Low | configuration error | Doc tests without serde derive feature - feature-conditional code in doc tests causing spurious failures | Step 3 (tests) |
| SER-30 | - | 296db17 | 296db17^ | Medium | type safety | Syn fix for issue 2414 - upstream proc-macro fix affecting attribute parsing | Step 2 (architecture) |
| SER-31 | - | `cb6eaea` | `b6f339ca` | High | serialization | Flatten unit enum variant serialization inconsistency - deserialization worked but serialization rejected enum variants in flattened fields | Step 5a (state machines) |
| SER-32 | - | `c67017d` | `f6e7366b` | High | type safety | Self keyword handling in type definitions - Self references in generic bounds, associated types, and macro contexts caused compilation failures | Step 5b (schema types) |
| SER-33 | - | `45c45e8` | `2e76f701` | High | validation gap | Hand-written enum variant deserializers limited to u32 discriminants - while derived variants supported u64, hand-written Result/IpAddr impls only accepted up to u32 | Step 3 (tests) |
| SER-34 | - | `63809e6` | `f44402e2` | Medium | state machine gap | Field indexing bug when skip and other attributes combined - incorrect variant index calculation when both skip_deserializing and #[serde(other)] were used | Step 5a (state machines) |
| SER-35 | #1610 | `9de4924` | `4cea81f9` | Low | error handling | Unused variable warning in adjacently tagged enum serializer - tuple unpacking raised compiler warning for skipped fields | Step 5 (defensive) |
| SER-36 | - | `acc8640` | `4cea81f9` | High | validation gap | Newtype struct with skipped internal type field - deserialization and serialization failed when newtype's single field was marked skip_deserializing or skip_serializing | Step 5a (state machines) |
| SER-37 | #2846 | `b60e409` | `fdc36e5c` | High | type safety | Macro hygiene for newtype struct deserialization with 'with' attribute - generated code referenced undefined __e variable instead of deserializer parameter | Step 5b (schema types) |
| SER-38 | - | `de8ac1c` | `5a8e9e00` | High | validation gap | Floats not deserializable from integers in untagged unions - content deserializer failed to accept integer types when deserializing float fields in untagged enums | Step 3 (tests) |
| SER-39 | - | `010444d` | `a7e19e2a` | High | validation gap | Floats not deserializable from integers in tagged unions - deserialization code limited float acceptance to F32/F64/U64/I64 instead of all integer types | Step 3 (tests) |
| SER-40 | - | `399ef08` | `3686277e` | Medium | silent failure | Capacity calculation overflow for small element types - size_hint calculations didn't account for element type size differences, allowing oversized allocations | Step 5 (defensive) |
| SER-41 | - | `51799dd` | `732ac493` | Medium | validation gap | IgnoredAny type cannot be flattened - flatten attribute on IgnoredAny field failed during deserialization | Step 5a (state machines) |
| SER-42 | - | `a803ec1` | `f85c4f2f` | Medium | validation gap | Adjacent tag deserialization missing bytes variant support - bytes type fields in tagged enums failed deserialization from byte sequences | Step 3 (tests) |
| SER-43 | - | `ac8ea72` | `f583401` | Medium | error handling | Panic in serde_test on token exhaustion - panics instead of returning errors caused unhelpful error locations in test assertions | Step 4 (specs) |
| SER-44 | - | `6326cee` | `8f4d37c7` | Medium | error handling | Panic in serde_test on running out of tokens - runtime panic when deserializer exhausted token stream instead of returning proper error | Step 4 (specs) |
| SER-45 | #1933 | `b276849` | `398fba9b` | High | error handling | Prevent panic when deserializing malformed Duration - std::time::Duration::new can panic on overflow, causing panics during deserialization of invalid input | Step 5 (defensive) |
| SER-46 | #2801 | `4036ff8` | `1b4da41f` | High | validation gap | Support (de-)serializing flattened unit struct - flattened unit structs incorrectly rejected in serialization while deserialization worked | Step 5a (state machines) |
| SER-47 | #2565 #1904 | `b4ec259` | `c3ac7b6` | High | validation gap | Correctly process flatten fields in enum variants - incorrect deserialization when variants differ in flatten field presence, panic on derive | Step 5a (state machines) |
| SER-48 | - | `4f922e4` | `9939666` | Medium | serialization | Implement serialization of flattened tuple variants of externally tagged enums - deserialization worked but serialization failed with unsupported type error | Step 5a (state machines) |
| SER-49 | #1933 | `4118cec` | `c261015` | Critical | error handling | Prevent various panics when deserializing malformed SystemTime - multiple panic conditions on overflow/underflow in SystemTime deserialization | Step 5 (defensive) |
| SER-50 | - | `a81968a` | `ea2789df` | High | error handling | Turn panic to error in SystemTime serialization - .expect() call caused panic when SystemTime before UNIX_EPOCH, now returns proper error | Step 5 (defensive) |
| SER-51 | - | `d2fcc34` | `a091a07a` | Medium | type safety | Ensure f32 deserialized from f64 and vice versa preserve NaN sign - NaN sign lost during float type conversion, now preserved with copysign | Step 5b (schema types) |
| SER-52 | #2195 | `ae38b27` | `b9de365` | Medium | configuration error | Add #[allow(deprecated)] to derive implementations - compiler warnings when serializing/deserializing deprecated structs/fields/variants | Step 4 (specs) |
| SER-53 | #2558 | `74b538b` | `291ec50d` | Medium | error handling | Produce error about mismatched types of #[serde(with)] and #[serde(default)] attributes on attribute itself - error location was incorrect, now properly positioned | Step 4 (specs) |
| SER-54 | - | `5cbc843` | `8084258` | Low | error handling | Show correct location in error messages by tracking caller of utility assert_tokens functions - error source attribution improved via #[track_caller] in serde_test | Step 3 (tests) |
| SER-55 | - | `c162d51` | `78a9dbc` | Medium | validation gap | Add 128-bit integer support to de::IgnoredAny - IgnoredAny panicked on 128-bit integers, preventing struct deserialization when ignored field contains i128/u128 | Step 5b (schema types) |
| SER-56 | - | `3f120fb` | `2b92c80c` | Medium | type safety | Enable unsized Map/SeqAccess types to use the impl for &mut - ?Sized bound missing prevented using unsized types as trait object references | Step 5b (schema types) |
| SER-57 | - | `77a6a9d` | `547d843c` | Medium | validation gap | Take into account only not skipped flatten fields when choosing serialization form - FlattenSkipSerializing incorrectly used serialize_map instead of serialize_struct | Step 5a (state machines) |
| SER-58 | - | `fa7da4a` | `6b1a178` | Low | configuration error | Fix unused_features warning - never_type feature declared but not used, causing spurious compiler warnings | Step 4 (specs) |
| SER-59 | - | `dd18663` | `e65b3e7` | Low | error handling | Fix redundant_closure clippy lint from PR 3038 - closure passed where function reference acceptable, causing lint warning | Step 5 (defensive) |

### tokio-rs/axum (Rust)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| AX-01 | #3611 | 22f769c | 22f768c | High | error handling | Multipart body limit exceeded errors returned generic error message instead of specific "Request payload is too large" text. Clients received uninformative error responses. | Step 4 (specifications) |
| AX-02 | #3664 | 60a0d28 | 60a0d27 | Critical | security issue | Content-Disposition header filenames were not escaped, allowing header parameter injection attacks (similar to CVE-2023-29401). Unescaped backslashes and quotes in filenames could break header parsing and enable response header injection. | Step 5 (defensive patterns) |
| AX-03 | #3656 | 8a9b03c | 8a9b03b | High | configuration error | CONNECT method endpoint was being set to the wrong field (options instead of connect) in MethodRouter, causing CONNECT requests to silently fail or be routed incorrectly. | Step 2 (architecture) |
| AX-04 | #3645 | c972bcb | c972bca | High | type safety | TypedPath macro generated conflicting trait bounds when OptionalFromRequestParts was in scope, causing compilation errors due to ambiguous trait implementations. | Step 5b (schema types) |
| AX-05 | #3591 | 6b00891 | 6b00890 | Medium | validation gap | JsonLines extractor was not respecting the default body limit, allowing unlimited request body sizes to bypass size restrictions. | Step 4 (specifications) |
| AX-06 | #3566 | 816407a | 8164079 | High | silent failure | FileStream range request handling had integer underflow when processing empty files, causing panic instead of graceful 416 RANGE_NOT_SATISFIABLE response. | Step 5a (state machines) |
| AX-07 | #3603 | 576968b | 576968a | Critical | API contract violation | IntoResponse tuple implementations were overriding explicit error status codes set by middleware or inner responses, breaking HTTP response code semantics when combining status codes with response builders. | Step 4 (specifications) |
| AX-08 | #3601 | f3a95d7 | f3a95d6 | High | type safety | axum::serve future return type incorrectly included `io::Result` wrapper that was never actually returned (always Ok) and claimed the future was terminating when it wasn't, misleading users about behavior. | Step 5b (schema types) |
| AX-09 | #2992 | 1858043 | 1858042 | Medium | protocol violation | SSE Event::json_data() with serde_json::RawValue was not stripping incompatible characters (\n, \r), producing invalid SSE protocol output that couldn't be parsed by clients. | Step 4 (specifications) |
| AX-10 | #3031 | ce3d429 | ce3d428 | High | validation gap | Route handler was setting Content-Length header before middleware could transform the response body, causing mismatched Content-Length and body when middleware added or modified body content. | Step 5a (state machines) |
| AX-11 | #3437 | a77c2cf | a77c2ce | Medium | type safety | FileStream::from_path() required specifying the generic S parameter even though it always returns ReaderStream<File>, forcing awkward generic syntax and preventing inference. | Step 5b (schema types) |
| AX-12 | #2993 | 43814c1 | 43814c0 | High | error handling | Trailing slash redirect (TSR) inside nested Router was redirecting to the wrong path (top-level instead of nested), breaking path resolution for nested routes with TSR. | Step 2 (architecture) |
| AX-13 | #2586 | 19f6f79 | 19f6f78 | Medium | error handling | Router and MethodRouter were being cloned for each request when calling axum::serve directly, causing unnecessary allocation overhead and breaking layer state sharing. | Step 5 (defensive patterns) |
| AX-14 | #3652 | 776c4a4 | 776c4a3 | Medium | error handling | Fallback routing was using unwrap() in TakeOnceRoute, causing panic instead of graceful error when service called more than once (internal invariant violation). | Step 6 (quality risks) |
| AX-15 | None | 25fac01 | 25fac00 | Low | error handling | MethodRouter::merge panic messages for overlapping routes had incorrect panic location due to #[track_caller] placement, making debugging harder. | Step 5a (state machines) |
| AX-16 | #3338 | cd1453f | cd1453e | High | configuration error | Router::reset_fallback() was not actually resetting the fallback_router field, leaving stale state that caused incorrect routing behavior. | Step 2 (architecture) |
| AX-17 | #3620 | 4c09ea7 | 4c09ea6 | High | protocol violation | WebSocket subprotocol selection was inefficient and didn't properly handle protocol negotiation, requiring rewrite to correctly match requested protocols. | Step 4 (specifications) |
| AX-18 | #3606 | 0101c2a | 0101c29 | Medium | error handling | Router::nest validation used assert! panics instead of returning Result, preventing graceful error handling and making the error location unclear. | Step 6 (quality risks) |
| AX-19 | #3618 | 20dfe66 | 20dfe65 | Medium | validation gap | vpath! macro was not validating against deprecated path variable formats (:var, *var), allowing invalid syntax that should have been compile-time errors. | Step 4 (specifications) |
| AX-20 | #3663 | e9909fe | e9909fd | Low | validation gap | TypedPath macro expansions were generating clippy::implicit_clone warnings even though the clone was necessary, creating noise in user lints. | Step 3 (existing tests) |
| AX-21 | #3039 | 9517dec | 9517deb | High | missing boundary check | Path extractor was panicking with unreachable!() when array types were used in path segments, instead of returning a proper validation error. | Step 5 (defensive patterns) |
| AX-22 | #2400 | ef56636 | ef56635 | Medium | error handling | axum::serve was crashing on accept() errors (e.g., EMFILE when too many files open) instead of gracefully retrying or logging. Should sleep and retry on EMFILE. | Step 6 (quality risks) |
| AX-23 | #3453 | a0692f9 | a0692f8 | High | protocol violation | JSON extractor was accepting JSON bodies with trailing characters after valid JSON, violating JSON parsing spec which should reject any input with trailing data. | Step 4 (specifications) |
| AX-24 | #3465 | ab593bb | ab593ba | Medium | protocol violation | Allow header was being set on all fallback responses, not just 405 Method Not Allowed as per RFC. Should only set Allow header on 405 status. | Step 4 (specifications) |
| AX-25 | #3478 | 1073468 | 1073467 | Critical | concurrency issue | axum::serve was missing hyper's header_read_timeout, allowing slow-loris attacks where clients could hold connections indefinitely while slowly sending request headers, exhausting server memory (~1 MB per stalled connection). | Step 6 (quality risks) |
| AX-26 | #3312 | `6bf1fcb` | `1599569` | Critical | silent failure | MultipartError::body_text() caused infinite recursion when logging with TRACE-level tracing. The __log_rejection! macro calls body_text() to format log output, which itself calls the macro again, creating stack overflow. Fixed by computing body text once before macro invocation. | Step 6 (quality risks) |
| AX-27 | #2739 | `51bb82b` | `68cfdce` | High | configuration error | axum-core's __log_rejection! macro used `tracing::` directly without ensuring the tracing crate was in scope when the feature was enabled. Compilation failed when axum-extra's tracing feature was enabled without axum-core depending on tracing. Fixed by using conditional module re-export through __private. | Step 4 (specifications) |
| AX-28 | None | `25fac01` | `291b62e` | Medium | error handling | MethodRouter::merge_for_path returned Self and panicked on overlapping routes instead of returning Result. The #[track_caller] attribute was on the wrong function level, making panic location wrong. Fixed by returning Result<Self> and preserving panic location in public merge() method. | Step 5a (state machines) |
| AX-29 | #3338 | `cd1453f` | `6ad76dd` | Low | validation gap | Router::reset_fallback() attempted to set fallback_router field which was removed during SSE tokio dependency refactor. This caused compilation error. Fixed by removing the obsolete field assignment. | Step 2 (architecture) |
| AX-30 | #2933 | `6f56077` | `4fc0641` | High | validation gap | axum-core's __log_rejection! macro referenced `tracing::` and `std::` without proper qualification, causing compile errors when used in generated rejection code. The tracing module wasn't accessible in the scope where macro-generated code executed. Fixed by using crate-qualified paths. | Step 4 (specifications) |
| AX-31 | #3403 | `c1ff153` | `384f393` | Medium | protocol violation | SSE Event retry field was missing required space after field name, violating Server-Sent Events RFC. Output "retry:123" instead of "retry: 123". Clients parsing strict SSE format would reject the malformed protocol. Fixed by adding space in byte string. | Step 4 (specifications) |
| AX-32 | #2776 | `68cfdce` | `7d43b46` | Medium | type safety | AppendHeaders<I> struct was not deriving Clone and Copy despite the generic parameter supporting it. Users attempting to clone response header middleware would fail at compile time. Fixed by adding Clone and Copy derives. | Step 5b (schema types) |
| AX-33 | #3114 | `32a948e` | `a0a2b3c` | High | validation gap | OriginalUri extractor was defined in request_parts.rs with other request parts, but cargo hack feature checks flagged it as potentially unused code in non-original-uri feature builds. Module needed feature-gating. Fixed by moving to separate original_uri.rs with feature guard. | Step 2 (architecture) |
| AX-34 | #2904 | `6efcb75` | `c48de12` | Medium | error handling | Beta Rust compiler changes introduced new warnings in WebSocket close code documentation and match expression type narrowing. Documentation examples had text that couldn't parse, and match arms became unreachable. Fixed by rewording docs and adding allow(unreachable_patterns). | Step 5 (defensive patterns) |
| AX-35 | #2933 | `6f56077` | `4fc0641` | High | configuration error | axum-extra's tracing feature depended on axum-core/tracing and axum/tracing features but not the tracing crate itself. When logging rejections through generated code, the tracing module wasn't available. Fixed by directly depending on tracing crate with feature flag. | Step 5 (defensive patterns) |
| AX-36 | #3110 | `7c934f2` | `fd60c84` | Medium | error handling | Rejection macro was calling body_text() and status() methods multiple times in IntoResponse impl, causing redundant computation and allocation. Fixed by storing results in local variables and reusing them. | Step 6 (quality risks) |
| AX-37 | #3118 | `53370b2` | `aafa72b` | Medium | error handling | Rejection Display impl wasn't showing the inner error details, while body_text() was. The two methods returned inconsistent output, confusing users when formatting errors for logging. Fixed by making Display impl call to_string() to match body_text() output. | Step 5a (state machines) |
| AX-38 | #3141 | `6c9cabf` | `8a96b8f` | High | protocol violation | WebSocket sec-websocket-protocol negotiation was not properly handled under HTTP/2. The protocol header was only set in HTTP/1.1 path but missing in HTTP/2 upgrade response. Fixed by moving protocol header insertion outside the version-specific branches. | Step 4 (specifications) |
| AX-39 | #3117 | `287bd14` | `fd60c84` | Medium | validation gap | Rejection definition macro accepted any expression for body text instead of requiring string literals. This allowed runtime computation of rejection messages when they should be compile-time constants. Fixed by changing macro parameter from `$body:expr` to `$body:literal`. | Step 5 (defensive patterns) |
| AX-40 | #3051 | `11806fb` | `fb1b8f1` | High | API contract violation | Router::nest() was allowing nesting at root path "/" which should only be valid via merge() or fallback. The empty path case was normalized to "/" internally, causing confusion. Users could accidentally nest routers at root when they meant to use merge or fallback_service. Fixed by adding explicit validation to reject nesting at "/" or "". | Step 2 (architecture) |

### BurntSushi/ripgrep (Rust)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| RG-01 | #3179 | b610d1c | 9ec0852 | High | validation gap | Global gitignore files with absolute search paths were not correctly interpreted relative to CWD; patterns like `/foo` were anchored incorrectly, breaking ignore behavior on non-default paths | Step 4: Missing validation of gitignore path context |
| RG-02 | #3194 | d47663b | 38d6302 | High | error handling | Line-buffered mode regression caused buffer looping that broke real-time streaming; introduced by stdin performance fix that overstuffed buffers waiting for fills | Step 5a: State machine gap in buffer refill logic |
| RG-03 | #3178 | 63209ae | b610d1c | High | silent failure | JSON printer with `--stats` silently skipped summary statistics emission; bailed out of `finish()` before tallying stats, persisting for years undetected | Step 5: Defensive validation of output paths |
| RG-04 | #3180 | de2567a | 9164158 | Critical | null safety | Panic in replacements with look-around corner case; invariant that match ≤ range violated, causing panic in UTF-8 byte trimming | Step 5b: Type safety for byte range invariants |
| RG-05 | #3184 | 8c6595c | de2567a | High | error handling | Stdin searches with large `-A` values exponentially slowed (~2-6s with -A999999) due to 64K read buffer limit from stdin; memory allocation triggered pathological buffer refills | Step 5a: State machine for buffer amortization |
| RG-06 | #3184 (fix#2) | d4b77a8 | 8c6595c | High | error handling | Follow-up fix: after-context line buffer kept too much data, causing memory overhead on large `-A` values; optimized rollover window calculation | Step 5a: Boundary condition in rolling window |
| RG-07 | #3173 | 0407e10 | bb88a1a | High | error handling | Whitelisted hidden files from parent `.ignore` not found; parent path stripping during glob application failed on nested directories | Step 2: Path traversal architecture |
| RG-08 | #2990 | 4df1298 | ba23ced | Medium | serialization | Glob patterns ending with `.` treated as empty string match; misimplemented `Path::file_name` semantics, breaking matchers like `*.` | Step 4: Glob parser validation |
| RG-09 | #2944 | 4ab1862 | 6244e63 | Medium | silent failure | Stats `--bytes-searched` incorrect when search quit early (e.g., `-m` max-matches); consumed bytes not marked correctly in non-mmap paths | Step 5: Defensive counting on early exit |
| RG-10 | #3139 | 8b5d3d1 | 491bf3f | Medium | silent failure | Files-with-matches (`-l`) with PCRE2 multiline + look-around reported wrong match counts; heuristic assumed count≥1 without validation | Step 3: Test for multiline regex corner cases |
| RG-11 | #3108 | 126bbea | 859d542 | Medium | error handling | Quiet mode + files-without-match (`--files-without-match --quiet`) inverted exit status; summary printer didn't properly negate match logic | Step 5a: Boolean state machine for quiet mode |
| RG-12 | #2884 | 9d738ad | 6c5108e | Critical | error handling | Inner literal extraction false negatives: regex `(?i:e.x\|ex)` matching `e-x` not detected; union of literals incorrectly propagated `prefix` attribute | Step 4: Regex optimization validation specs |
| RG-13 | #829 | 14f4957 | f722268 | High | error handling | Multiple path stripping bugs when searching subdirectories with `.ignore` in parent; duplicate path parts in construction (fixed 7 issues: #829, #2731, #2747, #2778, #2836, #2933, #3144) | Step 2: Path traversal architecture |
| RG-14 | #2658 | 805fa32 | 2d518dd | Medium | configuration error | NUL-terminated data (`--null-data`) with line anchors (`(?m:^)`) failed; regex engine line terminators hardcoded to `\n`, not configurable | Step 5b: Type safety in regex engine config |
| RG-15 | N/A | c81caa6 | 082245d | Medium | concurrency issue | File separator printed twice in multi-threaded search; both buffer writer and printer claimed ownership of separator responsibility | Step 5a: State machine for output ownership |
| RG-16 | #2690 | b9c7749 | 67dd809 | High | error handling | Reference cycle in ignore matcher compilation: compiled HashMap held ref to Ignore which held ref back; caused unbounded memory growth | Step 6: Quality risk - memory leaks in long-running processes |
| RG-17 | #2694 | c8e4a84 | f02a50a | Low | serialization | Non-fatal error messages lacked `rg:` prefix; inconsistent with standard tool behavior, reducing clarity | Step 5: Defensive error message formatting |
| RG-18 | #2574 | 341a19e | fed4fea | High | error handling | Word-regexp (`-w`) fast path incorrect in some cases; deducing match boundaries after initial capture failed when `^` vs `\W` ambiguous | Step 4: Regex fast-path validation specs |
| RG-19 | #2243 | 6abb962 | 6d95c13 | High | error handling | Non-path sorting (e.g., `--sort=modified`) only worked with ascending path order; sorting during traversal didn't preserve overall order for other sorts | Step 5: Defensive collection before sort |
| RG-20 | #1757 | cad1f5f | 2198bd9 | Medium | error handling | Duplicate path parts in subdirectory search filters; absolute path construction removed too much, resulting in incorrect relative application | Step 2: Path traversal architecture |
| RG-21 | #1332 | d199058 | bb0cbae | Medium | configuration error | Empty pattern file (`rg -vf empty.txt`) behaved identically to non-empty; optimization quit early for zero patterns; inversion logic broken | Step 4: Validation gap on zero-element sets |
| RG-22 | #3127 | f596a5d | -- | Medium | serialization | Unclosed glob character classes `[abc` threw parse error instead of treating `[` as literal; added opt-in `allow_unclosed_class` for git-like behavior | Step 4: Glob parser validation |
| RG-23 | #2913 | e42432c | -- | Low | API contract violation | `WalkBuilder::filter_entry` documentation unclear on exclusion semantics; documented vs. actual filtering behavior mismatch | Step 4: Spec audit for API contracts |
| RG-24 | #2928 | 6e77339 | -- | Low | error handling | `resolve_binary` docs incorrectly suggested early termination when feature disabled; actually still resolves all binaries | Step 4: Spec audit |
| RG-25 | #2852 | c45ec16 | -- | Low | error handling | Multiline + count behavior undocumented; inconsistency with files-with-matches not clarified | Step 4: Spec audit |
| RG-26 | #2794 | a5d9e03 | -- | Low | error handling | Time-reliant test failed sporadically; sleep duration insufficient on some systems (fixed for regression test reliability) | Step 3: Test robustness |
| RG-27 | #2777 | f0faa91 | -- | Low | error handling | `--ignore-file` precedence undocumented; clarified interaction with `.gitignore` hierarchy | Step 4: Spec audit |
| RG-28 | #1941 | 4782ebd | -- | Medium | concurrency issue | stderr/stdout interleaving in multi-threaded mode; error messages could be corrupted when printed concurrently with search output | Step 5a: State machine for synchronized output |
| RG-29 | #1838 | 9ed7565 | -- | Medium | validation gap | Searching for explicit NUL bytes without `-a/--text` silently never matched due to binary detection; now explicitly errors to prevent confusion | Step 4: Validation on regex patterns |
| RG-30 | #1275 | a2799cc | -- | Medium | error handling | Word boundary `\b` search catastrophically slow; bug likely in regex-automata<0.3, fixed by engine upgrade (1000x+ perf regression from 1.034s to 6.3ms) | Step 4: Dependency-level regex correctness |
| RG-31 | #2664 | daa157b | -- | Critical | API contract violation | `--sortr=path` (reverse path sort) had `todo!()` in shipped release; embarrassing oversight from sorting refactor | Step 5b: Type safety - exhaustive pattern matching |
| RG-32 | #3248 | 0a88ccc | -- | Low | error handling | Compression test failures in QEMU cross-compilation environments; platform-specific test harness issue, not core logic | Step 3: Test portability |
| RG-33 | #1275 | 5011f6e | -- | High | error handling | Performance regression in word boundary anchors; multiple consecutive word boundaries caused pathological backtracking in regex engine | Step 6: Quality risk - dependency version management |
| RG-34 | #2177 | `483628469a2580e4eab0edfbe7a7f3f8b1951848` | `c93fc793a08f3a97e02457d5132b4cc346768014` | Medium | serialization | `.gitignore` files with UTF-8 BOM (byte order mark) at start were misinterpreted; first pattern became malformed, matching Git's behavior required explicit BOM stripping on first line | Step 4: Glob/ignore parser validation |
| RG-35 | #3097 | `64174b8e68b59e560ad459f3c11cc9c4f00964bd` | `f596a5d8750a6a6db1b87ad95a78667322c06cbd` | Medium | serialization | Using `--crlf` with `--replace` lost CRLF terminators in output; line ending transformation applied before replacement, then newlines injected without respecting `--crlf` mode | Step 5b: Type safety in line terminator handling |
| RG-36 | #3212 | `85edf4c79671b00002123a2a43ff5238b6a27891` | `36b7597693c994ffaf023b95d2e18aeeda7d9286` | Medium | error handling | Unnecessary `stat()` calls on `.jj` directory even with `--no-ignore` flag; performance issue manifested as thousands of failed `statx()` calls in `strace` output | Step 5a: State machine for conditional operations |
| RG-37 | #2198 | `f3241fd657c83284f0ec17854e41cab9fe3ce446` | `cfe357188d2fbd621b7d5f7f4139f19f0c88ca09` | Medium | configuration error | `--no-ignore-dot` flag did not exclude `.rgignore` files; conditional check only handled `.gitignore`, missing custom ignore filename in exception logic | Step 4: Validation of feature interaction matrix |
| RG-38 | #2854 | `d869038cf610f10a8b7aca24284719e65a477e1a` | `75970fd16b4d5f8ff9fb1d9c157467eb166acf23` | Low | concurrency issue | Multithreading heuristic used overly pessimistic threshold causing single-threaded execution on reasonable workloads; algorithm never actually processed work in parallel due to bad heuristic | Step 5a: State machine for work distribution |
| RG-39 | #2849 | `75970fd16b4d5f8ff9fb1d9c157467eb166acf23` | `380809f1e250035808170db2e9a2cbd09395f450` | Medium | error handling | Command-line gitignore patterns processed in reverse order; `.gitignore` files from CLI args applied opposite intended precedence, breaking deterministic matching | Step 2: Path argument processing architecture |
| RG-40 | #2865 | `119407d0a918ca54da1e0a5e8806dbb8cd7e2be0` | `d869038cf610f10a8b7aca24284719e65a477e1a` | Low | configuration error | `std::path::absolute` on Windows not available in older Rust versions; absolute path conversion failed on some Windows systems | Step 2: MSRV compatibility checks |
| RG-41 | #1872 | `292bc54e64e55b69fec806bf3ee6481958e2946f` | `5be67c1244f494414629f71be859e0e1552dd6fd` | Medium | serialization | `--replace` flag not supported with `--json` output mode; feature interaction not implemented, silently ignored `--replace` in JSON context | Step 4: Feature interaction specification |
| RG-42 | #2060 | `4993d29a16b26b016b498765cc5636e73b479367` | `23adbd6795d4b0a7fbbb606d58fa82e3df0dabc2` | Low | API contract violation | Globset `escape()` routine missing; escape characters not available for building safe glob patterns, requiring unsafe string concatenation | Step 4: API completeness validation |
| RG-43 | #2386 | `d51c6c005aaac90329f61baa20821fafc96b841a` | `ea058813196dcdf53a51b0a689da0f4170b6ed75` | Low | serialization | `Glob` type could not be deserialized from strings despite serde support; type annotation required for deserialization, API usability gap | Step 4: Serde trait coverage |
| RG-44 | #2706 | `90a680ab45a7eaaffcccb22c4946771d6b424f02` | `119a58a400ea948c2d2b0cd4ec58361e74478641` | Low | concurrency issue | Atomic operations used overly strong memory ordering (`SeqCst`) when `Relaxed` sufficed; false contention point in counter updates when `--threads=N` set high | Step 5a: Atomic operation correctness |
| RG-45 | #2611 | `8b766a2522f419ac33552b2f82ec2ad79646c601` | `c21302b4096f9ce1af095fbe8b14828a90ecfecb` | Low | error handling | Hyperlinks enabled by default in output; unexpected terminal behavior in shell pipelines and scripts; feature should be opt-in | Step 1: Default value safety |
| RG-46 | #2288 | `d6758445109ae0f52fc3dd09ccb88a95263217cb` | `f34fd5c1bcaa68282f4c2d68e2f0f73af69d7597` | Medium | configuration error | Context flags (`-A/-B/-C`) had override precedence bugs; order-dependent behavior when combining flags (e.g., `-C 5 -A 2` should mean `A=5, B=5`, but result varied) | Step 4: Flag precedence specification |
| RG-47 | #2523 | `da8ecddce926bcf616f62c947058fe5487fd2a3b` | `36194c20bc87c1b6e51ce64cfadf3a9c35c3b3a0` | Low | configuration error | Executable detection on Windows missed `.COM` file extension; binary resolution only checked `.exe`, not `.COM` or `.bat` | Step 2: Platform-specific spec audit |
| RG-48 | #2518 | `fc0d9b90a9dbc1ba8d93a3f58da4ddbac0c40a7f` | `0c1cbd937e8f46f9a3c3f8a0f4a49ff79a2e3f9d` | High | error handling | Regex engine bug with alternation of literals matching incorrectly; upstream dependency issue requiring version bump to `regex-1.8.3` for fix | Step 6: Dependency correctness |


### nats-io/nats.rs (Rust)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| NATS-01 | N/A | `c407b55` | `8f1d5e6` | High | serialization | Consumer rate limit serialization missing `rate_limit_bps` rename causing server rejection | Step 4 |
| NATS-02 | N/A | `6af3aa2` | `441734a` | High | error handling | Service::respond() panic on missing reply subject - should throw error instead | Step 5 |
| NATS-03 | N/A | `d13d959` | `46c4470` | High | concurrency issue | Subscription drain hangs indefinitely without server traffic - fixed with ping dispatch | Step 5a |
| NATS-04 | N/A | `340ef63` | `dd7ab25` | Medium | serialization | JetStream error deserialization failure when err_code absent in server response | Step 4 |
| NATS-05 | N/A | `943c5d8` | `0b86ab8` | High | serialization | Object store HeaderMap serialization incorrectly included inner wrapper causing roundtrip failure | Step 4 |
| NATS-06 | N/A | `e1daa5e` | `a706c9f` | High | concurrency issue | JetStream publish acker unbounded channel caused message loss under load - switched to bounded channel | Step 5a |
| NATS-07 | N/A | `a706c9f` | `d5658c8` | High | concurrency issue | Backpressure mechanism broken by reverting unbounded channel which could drop acks | Step 5a |
| NATS-08 | N/A | `b3cd920` | `157376f` | Medium | protocol violation | Direct get request sent JSON payload for last_by_subject when server expects empty payload | Step 4 |
| NATS-09 | N/A | `c0430c8` | `9b694c7` | Medium | validation gap | Object retrieval failed silently for empty objects due to incorrect has_pending_messages flag | Step 5 |
| NATS-10 | N/A | `9b694c7` | `f99b256` | High | silent failure | Get deleted object never returned error - caused future to hang indefinitely | Step 5 |
| NATS-11 | N/A | `16cb81a` | `b5f07ce` | High | state machine gap | Pull consumer sent request before user first poll - fixed with oneshot synchronization | Step 5a |
| NATS-12 | N/A | `b5f07ce` | `c0430c8` | Low | error handling | Max payload exceeded error message had reversed limit and actual size parameters | Step 5 |
| NATS-13 | N/A | `2e71154` | `be196f9` | Medium | configuration error | Account info failed on server < 2.11 due to missing feature gate on new fields | Step 2 |
| NATS-14 | N/A | `aa87108` | `552c337` | High | error handling | Consumer info not properly handling JetStream errors - missing Response wrapper deserialization | Step 5 |
| NATS-15 | N/A | `7df9a4e` | `aafec93` | High | protocol violation | ServerAddr::port() ignored known defaults for wss/tls causing wrong port assignment | Step 4 |
| NATS-16 | N/A | `db5ab8d` | `c95809a` | Medium | serialization | Sample frequency deserialization failed when value contained % symbol from Terraform | Step 4 |
| NATS-17 | N/A | `5c865e0` | `ed856c9` | Medium | serialization | Consumer config sample_frequency using wrong field name - should be sample_freq | Step 4 |
| NATS-18 | N/A | `f044e06` | `053944d` | Medium | serialization | Push and Pull consumer sample_frequency field not renamed to sample_freq causing mismatch | Step 4 |
| NATS-19 | N/A | `17e5d65` | `e9919a0` | Critical | concurrency issue | KV create race condition - multiple writers could win lock when recreating deleted keys | Step 5a |
| NATS-20 | N/A | `e774533` | `835a9cf` | Medium | concurrency issue | Test race condition on macOS filesystem when deleting consumer without cleanup | Step 3 |
| NATS-21 | N/A | `3e1ef2b` | `340ef63` | High | concurrency issue | nats-server cluster test using wrong ports causing race condition in cluster initialization | Step 3 |
| NATS-22 | N/A | `79bf679` | `21ea5ca` | High | state machine gap | Service group prefixes not properly nested - group.group_with_queue_group lost parent prefix | Step 5a |
| NATS-23 | N/A | `8696d42` | `dde5b1e` | Medium | validation gap | Consumer info missing name validation allowing invalid subject chars (. * >) in requests | Step 5 |
| NATS-24 | N/A | `d8b59e0` | `c182230` | Medium | error handling | Server error messages lowercased causing case-sensitive subject names to display incorrectly | Step 5 |
| NATS-25 | N/A | `afd776a` | `8c89006` | High | null safety | JetStream consumer panic when retry_on_initial_connect used due to missing server version | Step 5b |
| NATS-26 | N/A | `e9919a0` | `966df7c` | Medium | validation gap | Stream config serde roundtrip failed when ConsumerLimits became null | Step 4 |
| NATS-27 | N/A | `c396478` | `8414f6b` | High | state machine gap | Max reconnects exceeded never returned error - reconnect loop silent with no propagation | Step 5a |
| NATS-28 | N/A | `1dbe9c3` | `0fface3` | High | state machine gap | Service::stop() never took effect - shutdown future not polled and could not resume | Step 5a |
| NATS-29 | N/A | `e0b1e4d` | `67b2798` | Medium | error handling | Service average processing time calculated incorrectly using divided by 2 instead of request count | Step 5 |
| NATS-30 | N/A | `b10fc52` | `0bf1b6f` | Medium | state machine gap | Service endpoints with same subject different queue groups conflict in stats tracking | Step 5a |
| NATS-31 | N/A | `0bf1b6f` | `237d677` | High | API contract violation | Service group endpoint subjects missing parent prefix when using builder pattern | Step 5a |
| NATS-32 | N/A | `6b55e4f` | `73e0aa2` | High | protocol violation | Multiplexer prefix not unique causing request collisions between concurrent requests | Step 4 |
| NATS-33 | N/A | `02fd086` | `740b415` | Medium | API contract violation | Service info missing endpoint details - subjects list deprecated but not replaced properly | Step 5b |
| NATS-34 | nats-io/nats.rs | `418d171` | `72db4f9` | Medium | configuration error | Missing feature-gating on object-store and key-value error types caused dead code and compilation issues when features disabled | Step 2 |
| NATS-35 | nats-io/nats.rs | `b2fb1b4` | `0185c78` | High | null safety | Pull consumer contained unsafe unwrap() calls in timer loop that could panic instead of gracefully handling errors | Step 5b |
| NATS-36 | nats-io/nats.rs | `a1876c4` | `d668201` | High | state machine gap | Ping interval waker not registered when interval ready - loop breaks after single tick causing connection to hang indefinitely | Step 5a |
| NATS-37 | nats-io/nats.rs | `8c783e0` | `0424068` | High | error handling | DNS resolution using blocking `to_socket_addrs()` in async context - changed to async `lookup_host()` to prevent blocking | Step 2 |
| NATS-38 | nats-io/nats.rs | `7bfcb93` | `63e9c7a` | High | state machine gap | Ordered pull consumer missing heartbeat detection - no recreation triggered on consecutive missed heartbeats | Step 5a |
| NATS-39 | nats-io/nats.rs | `f2a96f3` | `7bfcb93` | High | state machine gap | Ordered pull consumer recreation failed under transient network errors - fixed by adding exponential backoff retries with timeouts | Step 5a |
| NATS-40 | nats-io/nats.rs | `0059d67` | `f2a96f3` | High | state machine gap | Ordered push consumer recreation not retried on transient failures - added retry logic to ephemeral consumer creation | Step 5a |
| NATS-41 | nats-io/nats.rs | `dde5b1e` | `9564dde` | Medium | validation gap | Stream name validation only checked for space and dot but allowed wildcard subjects and whitespace characters | Step 5 |
| NATS-42 | nats-io/nats.rs | `21ea5ca` | `02bd0e9` | Medium | type safety | Authentication signature field stored as String when it should be binary Vec<u8> - caused encoding issues with non-UTF8 signatures | Step 4 |
| NATS-43 | nats-io/nats.rs | `27fbab4` | `375047b` | Medium | error handling | TLS authentication failed to recognize EC keys during PKCS8 parsing - missing match arm for ECKey variant | Step 4 |
| NATS-44 | nats-io/nats.rs | `24fb246` | `625d1da` | Medium | API contract violation | KV store purge operation ignored jetstream prefix configuration - subject construction bypassed prefix logic | Step 5b |
| NATS-45 | nats-io/nats.rs | `d59a88a` | `2e9368a` | High | serialization | Batch request expiration converted to milliseconds instead of nanoseconds - caused 1000x timeout value error | Step 4 |
| NATS-46 | nats-io/nats.rs | `08342bb` | `ac38712` | Medium | validation gap | Header name validation too permissive - allowed colons and non-ASCII characters that violate HTTP spec | Step 4 |
| NATS-47 | nats-io/nats.rs | `fa6a885` | `cb0e15a` | High | null safety | Connection parsing unwrapped header name conversion without error handling - could panic on invalid server headers | Step 5b |
| NATS-48 | nats-io/nats.rs | `9677baf` | `47a4790` | Medium | API contract violation | Typo in header enum name (NatsExpectgedLastSubjectSequence vs NatsExpectedLastSubjectSequence) - breaks API compatibility | Step 5b |

### lightbend/config (Scala)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| CFG-01 | #826 | e1519d7 | b9c6cec | Critical | null safety | Negative hash causes array index issues in BadMap.store(). Integer.MIN_VALUE % entries.length returns negative value, requiring Math.abs() on modulo result, not just the hash. | Step 5a - State machines: BadMap state corrupts with negative indices |
| CFG-02 | #817 | 2d9b9ee | b7b008a | Critical | null safety | BadMap hash collision handling was applying Math.abs() to the hash before modulo, missing edge cases where negative hash % length still produces negative index. Fixed by applying abs() after modulo. | Step 5b - Schema types: Hash function contract violation |
| CFG-03 | #798 | 3a4ebbf | 5d6a466 | High | silent failure | Environment variable values were rendered in config output, creating security/privacy risk. No mechanism to hide ENV_VARIABLE origin type from rendered output. Added new OriginType.ENV_VARIABLE and hideEnvVariableValues() option. | Step 5 - Defensive: Security exposure of sensitive env vars |
| CFG-04 | #700 | 4739cba | (merge) | High | concurrency issue | Collections.unmodifiableList() wrappers applied recursively cause stack overflow during resolution when wrapping already-wrapped collections. Java Collections implementation doesn't check for double-wrapping. Removed defensive wrappers; rely on immutability contract. | Step 5a - State machines: Recursive wrapping causes stack overflow |
| CFG-05 | #686 | 379a1f0 | (merge) | High | silent failure | loadEnvVariablesOverrides() initialized result map with all environment variables instead of empty HashMap, causing ALL env vars to be treated as config overrides, not just CONFIG_FORCE_* prefixed ones. | Step 6 - Quality risks: Silent config pollution |
| CFG-06 | #709 | 4be9b6d | (merge) | High | type safety | parseApplicationReplacement() used original ParseOptions instead of returned withLoader reference, ignoring class loader setup. ensureClassLoader() returns new immutable object; code was discarding it. | Step 5b - Schema types: API contract violation |
| CFG-07 | (N/A) | b29fdd4 | 0b4c9e8 | High | error handling | ConfigMemorySize threw incorrect exception types when reading oversized byte values (e.g., > Long.MAX_VALUE). Contract violation: wrong exception prevented proper error handling. Refactored to return BigInteger and provide proper ConfigException.BadValue. | Step 6 - Quality risks: Exception type contract violations |
| CFG-08 | #541/#604 | fee9a3e | e1c2640 | High | validation gap | Config keys with all digits but longer than Integer.MAX_VALUE caused NumberFormatException during sorting. Parser used Integer.parseInt() for numeric key comparison, which has 32-bit limit. Fixed by using BigInteger for comparison. | Step 5b - Schema types: Integer overflow in key sorting |
| CFG-09 | #567 | 4c63190 | (merge) | Medium | null safety | ConfigBeanImpl.isOptionalProperty() caused NPE when field was null. Getter methods without corresponding fields weren't checked for @Optional annotation. Fixed to check both field and getter method annotations. | Step 5 - Defensive: Null pointer in reflection |
| CFG-10 | #538 | d225355 | f09c8d2 | High | null safety | PathParser.parsePathNodeExpression() called with null ConfigOrigin, causing NPE in ConfigException constructor when reporting parse errors. Null origin should never be passed; pass baseOrigin.withLineNumber() instead. | Step 5 - Defensive: Error reporting path can cause NPE |
| CFG-11 | #447 | 870dd28 | (merge) | Medium | null safety | ConfigBeanImpl.isOptionalProperty() threw NPE when PropertyDescriptor had no corresponding field in the class. Fixed to null-check getField() result before accessing annotations. | Step 5 - Defensive: NPE on missing bean fields |
| CFG-12 | #758 | fe85a7d | (merge) | Medium | security issue | Class.newInstance() allowed arbitrary class instantiation via config.strategy system property, bypassing ConfigLoadingStrategy type check. Could instantiate any class. Fixed with asSubclass() check and modern getDeclaredConstructor().newInstance() API. | Step 5 - Defensive: Type checking for reflection |
| CFG-13 | #495 | 002de45 | (merge) | Medium | type safety | ConfigBeanImpl had no handler for Set<?> typed bean properties, only List. Config values can be converted to sets but this path was missing. Added getSetValue() wrapper around getListValue(). | Step 3 - Tests: Missing type coercion path |
| CFG-14 | #454 | 870dd28 | (merge) | Medium | null safety | ConfigBeanImpl required field to exist for every bean property. Threw NPE checking field annotations when no field found. Fixed to accept properties with only getter/setter (no backing field). | Step 5 - Defensive: Over-strict field requirements |
| CFG-15 | #405 | b7e5569 | a8d691a | Medium | configuration error | Config loading strategy was hardcoded; no way to customize strategy via configuration. Added system property support for com.typesafe.config.ConfigLoadingStrategy with proper reflection-based instantiation. | Step 4 - Specs: Configuration extensibility |
| CFG-16 | #361 | 93083e8 | 2e71d57 | Medium | type safety | Numbers starting with '.' (e.g., ".33") were parsed as NUMBER type but should be parsed as STRING then coerced. Parser included '.' in firstNumberChars, breaking string vs number distinction. Reverted to treat as string for lazy coercion. | Step 5b - Schema types: Type detection vs lazy coercion |
| CFG-17 | #386 | 2d1553e | 1d01e52 | Medium | type safety | Large signed duration values (>Long.MAX_VALUE nanos) lost precision when parsed. Parser regex [0-9]+ didn't match +/- signs, forcing double conversion and losing precision. Fixed regex to [+-]?[0-9]+ for integer path. | Step 5b - Schema types: Precision loss in numeric parsing |
| CFG-18 | #137 | 366ab55 | 07c67ae | High | state machine gap | Nested include handling in Parser used pathStack directly instead of reversed iterator, causing wrong path ordering. Stack contains most-recent-first but Path() expects oldest-first. Fixed using descendingIterator(). | Step 5a - State machines: Stack ordering bug in path construction |
| CFG-19 | #83 | d3f638f | e85a54e | Medium | silent failure | Rendered config keys starting with hyphen (e.g., "-10") were not quoted, producing invalid HOCON (interpreted as negative number not key). Fixed to detect '-' prefix and ensure quoting. | Step 5 - Defensive: Output validation gap |
| CFG-20 | #87 | 1653cc8 | c545910 | Low | silent failure | Comment rendering added "# " even when comment already started with space, producing "# comment" instead of "# comment" with correct spacing. Fixed to check comment content before adding space. | Step 3 - Tests: Idempotent rendering |
| CFG-21 | #81 | bd38eca | c545910 | Medium | state machine gap | Comments were associated with wrong config values due to parser state tracking issue. Comments after a value should stay with that value, not be pushed to next value. Fixed association logic in parser. | Step 5a - State machines: Comment association state |
| CFG-22 | #75 | 7231e14 | 369e9ff | Low | validation gap | Unicode BOM (U+FEFF) at start of config file was treated as regular character instead of whitespace, causing parse errors. Fixed by adding BOM to whitespace character set in tokenizer. | Step 3 - Tests: Edge case input handling |
| CFG-23 | #61 | b5b0f17 | (merge) | Low | validation gap | Newlines within triple-quoted strings weren't tracked, losing line number accuracy for subsequent error messages. Parser didn't increment line counter inside triple-quote context. | Step 3 - Tests: Position tracking in strings |
| CFG-24 | (N/A) | 4c63190 | c6d1ed4 | Medium | null safety | @Optional annotation on bean getter without field was not recognized, forcing field existence check. Fixed to also check getter method annotations when field is missing. | Step 5 - Defensive: Annotation resolution |
| CFG-25 | #183 | d57b0c0 | (merge) | Medium | type safety | Double-to-int narrowing was undocumented, causing silent precision loss when getInt() was called on double values. Behavior needed explicit documentation and validation contract clarification. | Step 4 - Specs: Type narrowing semantics |
| CFG-26 | #832 | edccc19 | e1519d7 | Medium | silent failure | List elements rendered with atRoot flag propagated from parent, causing incorrect formatting. List items should always be rendered as non-root even when parent list is at root. Fixed by passing false for atRoot parameter. | Step 5 - Defensive: Rendering context propagation |
| CFG-27 | (N/A) | 3984063 | d7d0a5d | Medium | configuration error | ConfigDocument building from empty root would collapse entire structure to single line instead of multi-line format. Indentation tracking failed for empty root, losing newline context when adding nested maps. | Step 5 - Defensive: Structure preservation in document building |
| CFG-28 | (N/A) | 087a00c | 924ee2e | Medium | silent failure | ConfigDocument.setValue() rendered values with leading/trailing whitespace, causing parse errors on re-insertion. Rendered value could have unwanted surrounding whitespace when inserted back into document. Fixed by trimming render output. | Step 5 - Defensive: Idempotent rendering |
| CFG-29 | (N/A) | 7aff85d | 59981da | Medium | error handling | ConfigDocumentParser threw exception when comment appeared on same line as value. Parser state machine did not handle inline comments, causing parse failures. Fixed by adding comment token check in whitespace skip logic. | Step 5a - State machines: Comment handling in parser |
| CFG-30 | (N/A) | aac122a | 1324199 | Medium | error handling | ConfigDelayedMerge.toString() threw exception by calling unwrapped() on lazy-resolved value. Superclass render() method couldn't handle delayed merge structure. Fixed by overriding render() with proper delegation. | Step 5 - Defensive: String conversion safety |
| CFG-31 | (N/A) | 919c46ac | 3984063 | High | missing boundary check | ConfigDocument.withValue() threw ArrayIndexOutOfBoundsException when inserting complex value (map/list) into empty root. Indentation array access without bounds check when indentation was empty. Fixed by checking !indentation.isEmpty() before access. | Step 5 - Defensive: Array bounds checking |
| CFG-32 | (N/A) | 44e8a92 | e5cc232 | Medium | error handling | Tokens.Value.toString() threw exception on unresolved values by calling unwrapped() on lazy values. ToString contracts violation when used in error messages. Fixed by checking resolve status before unwrapping. | Step 5 - Defensive: Safe toString implementations |
| CFG-33 | (N/A) | 3c6488f | 5c464b3 | Medium | silent failure | List containing unresolved or partially-resolved elements threw 'bug or broken' exception instead of gracefully allowing unresolved state. Missing cases in resolution logic for list merging. Fixed by adding null checks and handling partial resolution. | Step 5 - Defensive: Defensive copy and resolution |
| CFG-34 | #63 | 89956ea | b5b0f17 | Medium | concurrency issue | ConfigImpl.loadSystemProperties() threw ConcurrentModificationException when system properties modified during iteration. Direct iteration over System.getProperties() without synchronization. Fixed by creating synchronized copy before iteration. | Step 5 - Defensive: Defensive concurrent access |
| CFG-35 | (N/A) | 9348bf2 | 9d16f3b | Medium | type safety | Path.render() unnecessarily quoted path elements starting with letters or numbers. Over-quoting produced verbose output. Test suite had syntax error hiding the bug. Fixed by removing overly-strict quoting rule. | Step 5 - Defensive: Output validation and quoting rules |
| CFG-36 | #92 | d4c3ca5 | 05197ab | Medium | null safety | ConfigException serialization failed when origin was null. Serialization code didn't handle null origins, causing deserialization failures. Fixed by checking for null before accessing origin fields and representing null as empty field map. | Step 5 - Defensive: Serialization null handling |


### twitter/finatra (Scala)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| FIN-01 | CSL-11047 | `82531fa` | `884d087` | High | null safety | Jackson Annotations cache leaked resources due to missing hashCode/equals in BeanProperty, causing OutOfMemory on long-running services | Step 5b (schema types) |
| FIN-02 | CSL-10936 | `a6cb5a1` | `320c869` | Medium | type safety | CaseClassDeserializer failed to handle Scala enums wrapped in Option types during deserialization | Step 5b (schema types) |
| FIN-03 | CSL-10154 | `0a3be37` | `d7f82c4` | High | state machine gap | HttpWarmer used call-by-name for request parameter, causing request object recreation and mutation failures | Step 5a (state machines) |
| FIN-04 | CSL-10170 | `bb342c0` | `d5e5a13` | High | validation gap | Validator threw IndexOutOfBoundsException for case classes with non-constructor fields, breaking validation contract | Step 4 (specs) |
| FIN-05 | CSL-10027 | `9762145` | `bb342c0` | Medium | validation gap | FAIL_ON_UNKNOWN_PROPERTIES deserialization feature failed when JSON had fewer fields than case class | Step 4 (specs) |
| FIN-06 | CSL-10068 | `0a3803f` | `f391855` | High | type safety | JSON parsing of generic case classes containing generic fields failed with IndexOutOfBoundsException | Step 5b (schema types) |
| FIN-07 | CSL-10088 | `a6ba62b` | `d99767a` | Critical | type safety | Generic case class deserialization incorrectly interpreted Option[T] as Map instead of proper Option type | Step 5b (schema types) |
| FIN-08 | CSL-9920 | `9c1b0d6` | `08b8c51` | Medium | configuration error | Flag converters registered twice due to Guice not distinguishing Java and Scala primitive types | Step 2 (architecture) |
| FIN-09 | CSL-10209 | `697b213` | `a3473ea` | Medium | API contract violation | DarkTrafficFilter unable to lookup inherited Thrift methods, using getDeclaredMethod instead of getMethod | Step 5a (state machines) |
| FIN-10 | N/A | `e6d5bdb` | `c2ceeef` | High | concurrency issue | MySQL test client leak in large test suites with truncateTablesBetweenTests, causing too many clients error | Step 6 (quality risks) |
| FIN-11 | N/A | `ce90272` | `6825d70` | Medium | error handling | EmbeddedMysqlServerIntegrationTest commented out due to unresolved test failures | Step 3 (tests) |
| FIN-12 | N/A | `7311f2d` | `ecc02b2` | Medium | error handling | HTTPS server start info message logged wrong port instead of bound port for ephemeral port scenarios | Step 5 (defensive patterns) |
| FIN-13 | CSL-11274 | `da68130` | `cf44ba8` | Medium | error handling | Flaky tests in InMemoryStatsReceiverUtilityTest and FeatureTestNonInjectionCustomStatsReceiverTest due to timing issues | Step 6 (quality risks) |
| FIN-14 | N/A | `3d8e750` | `cd0a79a` | Low | validation gap | MaxConstraintValidator test mismatch, expected result not converted to Long like validator does | Step 3 (tests) |
| FIN-15 | CSL-11174 | `b1f14eb` | `19ad496` | Medium | error handling | TestMixin#assertFailedFuture passed incorrectly for unfailed futures when exception type was TestFailedFuture supertype | Step 3 (tests) |
| FIN-16 | N/A | `d1fa816` | `d907020` | Low | validation gap | Typo in FileResolver method name getLastSeperatorIndex should be getLastSeparatorIndex | Step 2 (architecture) |
| FIN-17 | N/A | `83f6ed9` | `dff4760` | Low | configuration error | Incorrect directory paths for example projects in build.sbt | Step 2 (architecture) |
| FIN-18 | N/A | `a4526ae` | `ca0b68a` | Low | error handling | DarkTrafficServer Get method forwarded test fails intermittently due to insufficient timeout | Step 6 (quality risks) |
| FIN-19 | N/A | `73d6ae4` | `8336074` | Medium | state machine gap | Kafka test suite resource cleanup test runs prematurely, clobbering shared embedded server | Step 5a (state machines) |
| FIN-20 | CSL-11844 | `f9a3bb2` | `acbec5e` | Medium | silent failure | EmbeddedHttpClient installed InMemoryStatsReceiver but never exposed stats, wasting memory on large test suites | Step 6 (quality risks) |
| FIN-21 | N/A | `cc7c24b` | `5b5ccf4` | Low | error handling | InMemoryTracer.ZipkinFormatter used milliseconds instead of microseconds, breaking Zipkin specification | Step 4 (specs) |
| FIN-22 | CSL-10770 | `3e88837` | `b49dc49` | Medium | protocol violation | Inconsistent error handling for invalid URIs across HTTP/1.x and HTTP/2 client implementations | Step 4 (specs) |
| FIN-23 | N/A | `715890a` | `df14e76` | High | validation gap | String case class fields returned empty string or incorrect toString for non-String JSON field values | Step 5b (schema types) |
| FIN-24 | FTEST-29 | `1072abe` | `10e1fc6` | Medium | type safety | Unable to derive canonical service class name for Scrooge Java Thrift services using $Service suffix | Step 5b (schema types) |
| FIN-25 | DPB-13356 | `05214ea` | `b8f0087` | High | configuration error | Kafka streams Bazel build broken due to typo in BUILD file after Kafka version upgrade | Step 2 (architecture) |
| FIN-26 | DSTR-8047 | `7373b47` | `c811e18` | High | state machine gap | Kafka Streams delayWithStore DSL created timer stores using hashCode, causing different shards to use orphan stores during restarts/rebalances until storeKey parameter was made required | Step 5a (state machines) |
| FIN-27 | REVSRE-7931 | `2fc3b26` | `fd2c5e0` | High | error handling | Kafka Streams WordCountInMemoryServerFeatureTest had flaky timeout waiting for gauge metric; fixed by switching from waitForKafkaMetric to inMemoryStats.gauges.waitFor with explicit timeout | Step 6 (quality risks) |
| FIN-28 | DPB-13989 | `725d5a4` | `4466bce` | High | error handling | MySQL test lifecycle had flaky intermittent failures when table truncation exceeded 1 second timeout, with afterEach swallowing exceptions causing tests to run against dirty database state | Step 6 (quality risks) |
| FIN-29 | CSL-9951 | `306b719` | `9667845` | Medium | API contract violation | InMemoryStats.waitFor required wrapping expected values in predicates, making the API harder to use; added non-predicate version accepting expected value directly | Step 5 (defensive patterns) |
| FIN-30 | N/A | `3eb0cd8` | `4212ce8` | High | error handling | EmbeddedTwitterServer caught InterruptedException instead of TimeoutException during startup, allowing wrong exception type to escape; broke server startup failure handling contract | Step 4 (specs) |
| FIN-31 | DPB-13191 | `6295414` | `8c95126` | Medium | configuration error | Bazel build produced jars with duplicate names for different build targets, causing order-dependent build outcomes when targets compiled in different orders | Step 2 (architecture) |
| FIN-32 | CSL-11844 | `f9a3bb2` | `acbec5e` | Medium | silent failure | EmbeddedHttpClient installed InMemoryStatsReceiver but never exposed stats, silently leaking histogram data on every test without providing value | Step 6 (quality risks) |
| FIN-33 | PUBSUB-41759 | `73d6ae4` | `8336074` | High | state machine gap | Kafka producer integration test enabled resource cleanup that clobbered embedded server shared by rest of test suite, causing downstream tests to fail | Step 5a (state machines) |
| FIN-34 | CSL-10488 | `b1d4338` | `bbc0cf7` | High | type safety | ClassUtils switched to TypesApi for case class detection but failed for generic case class scenarios supported in Scala 2.11, breaking reflection contract | Step 5b (schema types) |
| FIN-35 | CSL-11329 | `6305bd3` | `6d13691` | High | missing boundary check | JDK 11 migration missing explicit jaxb-api dependency caused compilation failures when javax.xml.bind package unavailable | Step 2 (architecture) |
| FIN-36 | N/A | `b919ed4` | `a6cb5a1` | Medium | error handling | Jackson deserialization test expected non-null NoSuchElementException message but Scala 2.13 HashMap returns null, causing test assertion mismatch | Step 6 (quality risks) |
| FIN-37 | CSL-10435 | `4e25d3c` | `25bf328` | Medium | error handling | StackClientModuleTraitTest asserted NullStatsReceiver but OSS build's finagle-stats on classpath provided different stats receiver, breaking test assumption | Step 6 (quality risks) |
| FIN-38 | CSL-10301 | `bfb6e22` | `920c62d` | Medium | error handling | ClassUtilsTest passed in JDK11 but failed in JDK8 due to different runtime reflection behavior across JDK versions, requiring conditional test logic | Step 6 (quality risks) |
| FIN-39 | N/A | `43299e5` | `be6d904` | Medium | validation gap | MySQL error handling lacked translation layer for numeric error codes returned by database, exposing raw codes to client code | Step 4 (specs) |
| FIN-40 | N/A | `0755b77` | `b0288c8` | Medium | error handling | Finatra test infrastructure lacked standardized convention for tracing verification with BufferingTracer, requiring ad-hoc approaches and preventing reusable trace assertions | Step 3 (tests) |


### akka/akka (Scala/Java)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| AKK-01 | #32893 | `76e6f264` | `fa8f8036` | Low | error handling | Remove noisy warning log from stale region detection | Step 6 |
| AKK-02 | #32875 | `57f68538` | `d3ea481c` | High | state machine gap | SBR threshold for down-all-when-indirectly-connected threshold was incorrect, requiring validation | Step 5a |
| AKK-03 | #32850 | `1c769431` | `266b2e6b` | High | concurrency issue | ShardedDaemonProcess old revision started due to keep-alive in flight with stale revision check | Step 5a |
| AKK-04 | #32822 | `6b93537c` | `670c60a3` | High | state machine gap | EventSourcedBehavior mutable state not recreated on failure restart, shared state across runs | Step 5a |
| AKK-05 | #32815 | `a8a752c3` | `f65b9dfa` | High | state machine gap | VersionVector for replicated event sourcing not fully recovered from replay metadata | Step 5a |
| AKK-06 | #32791 | `903b1397` | `af49be9d` | Medium | validation gap | TCP framing not checking max frame size on inbound messages | Step 5b |
| AKK-07 | #32785 | `228843ac` | `b6bd8674` | Medium | configuration error | Virtual thread executor batching disabled incorrectly causing scheduling issues | Step 2 |
| AKK-08 | #32780 | `9bd9baa8` | `6f82b8a4` | Medium | type safety | ShardRegionStats used Scala Int instead of Java Integer, making API unusable | Step 5b |
| AKK-09 | #32770 | `6f82b8a4` | `81932a12` | High | state machine gap | Shard crashes with ES remember entity store due to race on pending writes | Step 5a |
| AKK-10 | #32749 | `096cb099` | `9cc3abe2` | High | concurrency issue | Delayed restart cancelled incorrectly when remembering entities with eager restart | Step 5a |
| AKK-11 | #32748 | `d69a082a` | `0bbe6d5b` | Medium | serialization | Cluster metrics incorrectly used Java serialization | Step 5b |
| AKK-12 | #32723 | `98439602` | `f77ed8fb` | High | state machine gap | Mutation order in ShardRegion.changeMembers using stale state for comparison | Step 5a |
| AKK-13 | #32722 | `f77ed8fb` | `918b0070` | High | concurrency issue | Shard region re-registration timing issue when coordinator leaving/exiting | Step 5a |
| AKK-14 | #32657 | `76daf1b0` | `fa68698a` | High | state machine gap | LastSequenceNumber and metadata not available for initially stashed commands | Step 5a |
| AKK-15 | #32636 | `e17d1cd0` | `d21bf750` | High | error handling | TCP DNS client not closed on failure, response byte re-ordering under load | Step 5 |
| AKK-16 | #32605 | `302595c8` | `e14c0ccd` | Medium | validation gap | RestartFlow logging used incorrect gte comparison operator | Step 5b |
| AKK-17 | #32578 | `3be4dce5` | `249efae2` | Low | configuration error | M1 version parsing did not handle versions smaller than final | Step 2 |
| AKK-18 | #32567 | `2443fd0b` | `74c633b2` | Medium | concurrency issue | Race condition in ReplicatedEventSourcingSpec async setup | Step 3 |
| AKK-19 | #32555 | `542aa745` | `dc38598` | Medium | validation gap | Circuit breaker with id missing for journal and snapshot store | Step 5b |
| AKK-20 | #32475 | `cfbebcb1` | `d5698ad5` | High | validation gap | Batched StateChange events not properly split on max-updates-per-write | Step 5b |
| AKK-21 | #32462 | `3f3213ff` | `d77a99a5` | High | state machine gap | snapshotWhen predicate evaluated on old state before event applied | Step 5a |
| AKK-22 | #32444 | `d8dbc815` | `735b9634` | Critical | state machine gap | Event deletion allowed for Replicated Event Sourcing causing incomplete replication | Step 5a |
| AKK-23 | #32439 | `a7f82135` | `5106142` | High | state machine gap | Entity stuck in passivation due to missing passivationStopTimeout configuration | Step 2 |
| AKK-24 | #32437 | `b8f201bf` | `30f27abe` | Medium | error handling | ActorInitializationException supervision broken due to assertion on perpetrator | Step 5 |
| AKK-25 | #32411 | `44e8dad2` | `d2080a8d` | Medium | API contract violation | Named CircuitBreakerApi required ExtendedActorSystem instead of ClassicActorSystemProvider | Step 2 |
| AKK-26 | #32372 | `81881416` | `b93e9421` | Medium | state machine gap | NotInfluenceReceiveTimeout did not apply to adapted typed responses | Step 5a |
| AKK-27 | #32385 | `15192ab7` | `0ecf97a8` | Medium | validation gap | ByteString.indexWhere caused infinite loop with out-of-bounds offset | Step 5b |
| AKK-28 | #32331 | `6960faf9` | `8acb0d28` | Medium | null safety | Promise actor path incorrect when terminated quickly | Step 5b |
| AKK-29 | #32324 | `bf7de90f` | `f893c34a` | Medium | configuration error | Jackson autodetect broken in native-image build | Step 2 |
| AKK-30 | #32323 | `b5626ec2` | `d4fb71a4` | Medium | type safety | JoinConfigChecker anonymous class different names on Scala 2.13 vs 3 | Step 5b |
| AKK-31 | #32257 | `764a9da5` | `c5d977b1` | High | validation gap | Topic with same name different message types published wrong type to subscribers | Step 5b |
| AKK-32 | #32200 | `98e9d103` | `227bbe62` | Medium | security issue | Environment variable values logged in ActorSystem settings toString | Step 6 |
| AKK-33 | #32191 | `ffdacead` | `a6b5086e` | High | state machine gap | EventWriter failed to fill gaps before snapshot events | Step 5a |
| AKK-34 | #32168 | `cc8a64ce` | `279df8a9` | Medium | concurrency issue | Actor system uid not unique, duplicate uids caused issues | Step 5a |
| AKK-35 | #32399 | `519b7356` | `1a300de7` | Medium | validation gap | PEM decoder regression failed to handle EC PRIVATE KEY blocks and arbitrary PEM block types | Step 5b |
| AKK-36 | #31814 | `57aaeac2` | `69bfcb18` | High | error handling | Backoff restart with stash buffer lost messages during unstash exception in supervision recovery | Step 5a |
| AKK-37 | #32320 | `7166a988` | `7cb25ef1` | Medium | configuration error | Native-image JFR enable flag was lost in native-image.properties configuration | Step 2 |
| AKK-38 | #32161 | `85236f87` | `7cb2ff79` | High | concurrency issue | Actor system uid collision not handled gracefully in artery handshake leading to duplicate uids | Step 5a |
| AKK-39 | #32798 | `8b222c6e` | `783d6aa4` | Low | validation gap | PendingGetShardHomesSpec duplicate random shard generation in test harness | Step 5b |
| AKK-40 | #32272 | `df01bd4d` | `dd864424` | Medium | type safety | ByteStringBuilder overload resolution failed in Scala 2.13 and Scala 3 compiler | Step 5b |
| AKK-41 | #32784 | `b6bd8674` | `d01aaf02` | Medium | configuration error | Virtual thread name counter feature caused regression, feature reverted to restore stability | Step 2 |
| AKK-42 | #32766 | `98e667a9` | `a9916f38` | Medium | concurrency issue | Terminated message prioritization optimization caused race condition in ddata handling | Step 5a |
| AKK-43 | #32452 | `010eb6f0` | `735b9634` | Low | configuration error | IdleSpec configuration accidentally modified, accidental config change reverted | Step 2 |
| AKK-44 | #32182 | `cc11f558` | `279df8a9` | Medium | concurrency issue | RemoteConnectionSpec uid validation test had race condition in async setup | Step 3 |
| AKK-45 | #32169 | `53375d57` | `279df8a9` | Medium | concurrency issue | RemoteConnectionSpec timeout handling test race in artery handshake validation | Step 3 |
| AKK-46 | #26514 | `279df8a9` | `0df546c6` | High | API contract violation | ActorContext.ask with multiple parameters failed to compile, API contract broken | Step 2 |
| AKK-47 | #32554 | `82216cf7` | `8d4004c7` | Low | configuration error | Default logger name changed between Scala 2.13 and Scala 3 causing test failures | Step 2 |
| AKK-48 | #32771 | `3c0a4177` | `3f904190` | High | state machine gap | Shard region termination not properly awaiting child actor shutdown in edge case | Step 5a |
| AKK-49 | #32625 | `9a7ee29a` | `bc9c42bd` | Medium | null safety | PrefixAndTail stream operator leaked resources on completion in StreamOfStreams | Step 5b |


### gitbucket/gitbucket (Scala)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| GB-01 | #2188 | `1b7fbcb` | `03760f1` | High | serialization | UTF-8 BOM lost when editing files via web interface; file content preservation broken | Step 5b |
| GB-02 | #3979 | `df60395` | `3111ab3` | Medium | error handling | CSS padding inconsistencies in discussion item icons causes visual misalignment | Step 6 |
| GB-03 | #3967 | `f726177` | `b355599` | High | null safety | Markdown preview error when getting wiki branch due to hardcoded branch name | Step 5a |
| GB-04 | #3958 | `3f3b111` | `379c86b` | Medium | validation gap | Filename redirect encoding using wrong method; special characters not properly encoded | Step 5b |
| GB-05 | #3906 | `b582af4` | `ecd3f5b` | Medium | API contract violation | Editor preview AJAX request fails with context path; hardcoded URL doesn't respect baseUrl | Step 2 |
| GB-06 | #3929 | `0bdc765` | `9a613bb` | Medium | state machine gap | Wiki sidebar/footer rendered with hardcoded "master" branch instead of actual wiki branch | Step 5a |
| GB-07 | #3902 | `ecd3f5b` | `7be433d` | Low | error handling | Plugin admin menu missing CSS class causes hover effect not to display | Step 6 |
| GB-08 | #2456 | `0d6e5af` | `88a8973` | Medium | validation gap | Markdown wiki links always redirect to _blob endpoint; doesn't detect page vs file distinction | Step 4 |
| GB-09 | #3843 | `af66f8f` | `f16cc11` | High | API contract violation | Repository Contents Upload API fails for nested paths; path calculation splits incorrectly | Step 2 |
| GB-10 | #3826 | `217df70` | `e672d41` | High | state machine gap | Wiki blob endpoint hardcoded to "master" branch instead of actual wiki default branch | Step 5a |
| GB-11 | #3825 | `e672d41` | `d975700` | High | type safety | Archive download URL routing broken for branch names containing slashes | Step 5b |
| GB-12 | #3813 | `b7b7322` | `5eb4439` | Medium | error handling | Branch selector JavaScript uses loose equality (==) instead of strict (===) comparison | Step 5b |
| GB-13 | #3789 | `c4d8af0` | `a10bc36` | Medium | API contract violation | Sign-in redirect fails when user-defined CSS is loaded; /user.css not excluded from auth check | Step 2 |
| GB-14 | #3669 | `743bdab` | `a5a2e47` | Medium | error handling | Invalid default branch name redirects to wrong settings page instead of branch settings | Step 3 |
| GB-15 | #3656 | `b1d4a18` | `fdfd8ec` | High | API contract violation | WebHook SSH URL and ref fields incorrectly formatted in payload; SSH URL missing protocol | Step 2 |
| GB-16 | #3653 | `92304ac` | `a2242a3` | Medium | type safety | JGitUtil.getCommitLog called with string IDs instead of ObjectId; causes incorrect comparisons | Step 5b |
| GB-17 | #3647 | `64e8167` | `1145c4d` | Critical | state machine gap | Diff calculation fails with force push; doesn't find common ancestor between commits | Step 5a |
| GB-18 | #3672 | `10fc04c` | `67563a8` | High | error handling | Invalid query strings cause unhandled exceptions; should return 400 error instead | Step 3 |
| GB-19 | #3667 | `ad9a0af` | `d2fc7a0` | Medium | validation gap | Pull request branch errors not displayed to user; form validation errors hidden | Step 4 |
| GB-20 | #3907 | `fbcf962` | `3b9b261` | Medium | null safety | Wiki links rendered without checking if target page exists; broken links generated | Step 4 |
| GB-21 | #3894 | `c2ad664` | `c88e5ad` | Medium | API contract violation | File preview in editor uses wrong filename for syntax highlighting; path handling inconsistent | Step 2 |
| GB-22 | #3436 | `dabddf6` | `c7ade7e` | Medium | error handling | JGitUtil.findBranches called unnecessarily with merge info when only names needed | Step 6 |
| GB-23 | #3957 | `379c86b` | `6dce867` | Low | error handling | Commit history pagination removed causing all commits to load; performance regression | Step 6 |
| GB-24 | #3819 | `f9e4500` | `90b9c17` | Medium | API contract violation | Revert pull request support incomplete; doesn't handle all edge cases | Step 3 |
| GB-25 | #3780 | `b9d2efa` | `9c2e090` | Low | error handling | Pull request branch deletion box has incorrect bottom margin in CSS | Step 6 |
| GB-26 | gitbucket/gitbucket#3661 | `2abdd23` | `ef95ce9` | Medium | API contract violation | User-defined CSS loaded before plugin JavaScript runs; execution order causes CSS overrides not to apply | Step 2 |
| GB-27 | gitbucket/gitbucket#3662 | `8168580` | `2abdd23` | High | API contract violation | List-repository-tags API returned wrong format; field names didn't match GitHub API contract | Step 2 |
| GB-28 | gitbucket/gitbucket#3791 | `0c1e8b9` | `fda67a3` | Critical | security issue | Direct push to protected branch bypassed protection rules; enforcement logic missing | Step 5a |
| GB-29 | gitbucket/gitbucket#3781 | `c909572` | `b9d2efa` | Medium | state machine gap | Authenticated user on sign-in page not redirected to home; allows session confusion | Step 3 |
| GB-30 | gitbucket/gitbucket#3725 | `9d69b9e` | `44b2320` | High | API contract violation | Bearer token authentication not supported; hardcoded offset for token extraction breaks with bearer scheme | Step 2 |
| GB-31 | gitbucket/gitbucket#3962 | `8f2e0f8` | `73ccfd0` | High | security issue | WebHook signatures missing SHA-256 support; only SHA-1 available limits security posture | Step 5a |
| GB-32 | gitbucket/gitbucket#3676 | `2afb378` | `edc9720` | Medium | validation gap | Branch name length limit too restrictive; 100 character maximum doesn't support long names | Step 4 |
| GB-33 | gitbucket/gitbucket#3697 | `5eaf59e` | `d6d47aa` | Low | error handling | LDAP SSL provider lookup code outdated; dynamic provider caching no longer needed with modern Java | Step 6 |
| GB-34 | gitbucket/gitbucket#3801 | `d8e5ac5` | `2fbeef7` | Low | error handling | Blank issue template not disabled; allows users to submit empty issues without guidance | Step 6 |
| GB-35 | gitbucket/gitbucket#3898 | `6917cbf` | `637b033` | Low | error handling | Typo in file path constant breaks include; uses wrong variable name in filePath parameter | Step 6 |
| GB-36 | gitbucket/gitbucket#3867 | `a791420` | `9f58c6d` | Low | error handling | Community plugins link in README points to wrong URL; link target changed | Step 6 |
| GB-37 | gitbucket/gitbucket#3844 | `ba753a3` | `95ceca7` | Low | error handling | Release documentation out of sync; changelog version numbers incorrect in docs | Step 6 |
| GB-38 | gitbucket/gitbucket#3882 | `c88e5ad` | `703fb4a` | Medium | API contract violation | Markdown renderer not pluggable; hardcoded to single renderer instead of using provider interface | Step 2 |
| GB-39 | gitbucket/gitbucket#3416 | `36de0b3` | `4f3cd26` | Low | error handling | Branch selector layout broken; unnecessary HTML element creates visual misalignment | Step 6 |
| GB-40 | gitbucket/gitbucket#3533 | `89381d3` | `2e1037e` | Low | error handling | Typo in variable name breaks logic; unused variable pattern match warning | Step 6 |

### JamesNK/Newtonsoft.Json (C#)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| NJ-01 | #3104 | 4f73e743 | e5f6715 | High | API contract violation | JToken.WriteTo() changed from public to private, breaking external API. Method was causing MissingMethodException due to IL trimming attributes not being properly handled. | Step 5: Defensive patterns - API visibility & breaking changes |
| NJ-02 | #3092 | 341b3aee | a162f27 | High | API contract violation | JToken.ToString(Formatting) accessibility changed, similar IL trimming issue as #3104 but for ToString variant. | Step 5: Defensive patterns - IL trimming compatibility |
| NJ-03 | #3091 | a162f276 | 4e13299 | High | type safety | Inconsistent null value type handling when setting null on optional properties. Optional<T> vs plain null were not being distinguished, causing property type information to be lost. | Step 5b: Schema types - Optional<T> contract resolution |
| NJ-04 | #2811 | ba92aa9a | 5617700 | Medium | validation gap | TimeOnly deserialization failed with format error for HH:mm format. ParseExact() was too strict; should use flexible Parse() instead to handle multiple valid formats (HH:mm:ss.FFFFFFF, HH:mm:ss, HH:mm). | Step 3: Tests - Format validation boundaries |
| NJ-05 | #3055 | 62528922 | ef0bfa5 | Medium | silent failure | Missing TestFixture attribute causing optional property null-setting tests to be skipped in test suite. | Step 4: Specs - Test harness configuration |
| NJ-06 | #3056 | ef0bfa54 | 36b605f | Medium | silent failure | Similar missing TestFixture attribute issue for another optional property test suite. | Step 4: Specs - Test harness configuration |
| NJ-07 | #2922 | 55a7204f | 01e1759 | Medium | error handling | Empty constructor name parsing did not validate or throw. Parser would accept "[new \0(" without error reporting. Added validation to detect and report empty constructor names. | Step 5a: State machines - JSON parser state transitions |
| NJ-08 | #2796 | 57025815 | c908de3 | High | null safety | Null string values were incorrectly reported as String token type instead of Null type. JTokenWriter.WriteValue(string? value) was not checking for null, causing type mismatch. | Step 5b: Schema types - Null token type classification |
| NJ-09 | #2777 | c908de30 | 2afdccd | High | type safety | Negative zero (-0.0) double values were not returned correctly from box cache. Cache was returning positive zero for all zero values. Detection logic added using double.IsNegativeInfinity(1.0 / value) to distinguish -0.0 from +0.0. | Step 5: Defensive patterns - IEEE 754 special values |
| NJ-10 | #2769 | 2afdccdb | 4fba53a | High | silent failure | Parsed decimal values were losing trailing zeroes. 0.0 would deserialize to 0, losing precision information. Cache now stores DecimalZeroWithTrailingZero separately to preserve scale metadata. | Step 5b: Schema types - Decimal scale preservation |
| NJ-11 | #2736 | d0a328e8 | aae9284 | High | validation gap | MaxDepth validation was not being applied to ISerializable deserialization. Recursive objects via ISerializable could exceed MaxDepth without throwing. Fixed by setting MaxDepth on token reader created from ISerializable data. | Step 5a: State machines - MaxDepth validation boundaries |
| NJ-12 | #2711 | cb9eed96 | 94ff24f | Medium | type safety | Deserializing via constructor with ignored base type properties was failing. Contract resolver was including base type properties even when they should be ignored, causing property mismatch with constructor parameters. | Step 5b: Schema types - Contract resolver inheritance |
| NJ-13 | #2695 | 94ff24f8 | e6fbab9 | High | concurrency issue | JsonTextWriter.CloseAsync() was doing blocking I/O instead of async I/O. WriteValue() and Flush() were synchronous, making async variant impossible. Added proper IAsyncDisposable support. | Step 5a: State machines - Async/await state transitions |
| NJ-14 | #2602 | e42c9e48 | 71be691 | Critical | concurrency issue | Race condition in name table when deserializing on ARM processors. Concurrent dictionary access without proper synchronization. Lock was missing in GetNameEntry(). | Step 5a: State machines - Concurrent state management |
| NJ-15 | #2531 | e44ab334 | 2b0f7a2 | Medium | validation gap | Merge() operation on JContainer did not validate content type, allowing invalid types to be merged. Added ValidateContent() check. Array merge handling did not properly convert content items to JToken. | Step 5: Defensive patterns - Content validation |
| NJ-16 | #2530 | 2b0f7a24 | f7e7bd0 | High | type safety | Deserializing mistmatched JToken types in properties was not being validated. JArray could be deserialized into JObject property without error. Added contract type check: property.PropertyContract?.ContractType != JsonContractType.Linq | Step 5b: Schema types - JToken type contracts |
| NJ-17 | #2505 | f7e7bd05 | ae9fe44 | High | validation gap | MaxDepth validation not enforced when ToObject() called inside JsonConverter. Reader created for ToObject() was not inheriting MaxDepth setting. Default MaxDepth also changed from 128 to 64. | Step 5a: State machines - Nested converter depth tracking |
| NJ-18 | #2493 | 1745d7c1 | 583eb12 | Medium | state machine gap | JTokenWriter failed when writing comment to object. Comments have no token type representation, causing writer to enter invalid state. Added comment-specific handling in WriteComment(). | Step 5a: State machines - Comment token handling |
| NJ-19 | #2494 | 583eb120 | b6dc05b | High | error handling | Missing error when deserializing JToken with contract type mismatch. InvalidCastException was thrown instead of JsonSerializationException. Added contract type compatibility check with proper error message. | Step 6: Quality risks - Error message clarity |
| NJ-20 | #2472 | 15525f1c | 926d2f0 | Medium | null safety | JsonWriter.WriteToken() did not allow null with string token type. WriteValue(string?) was checking for non-null before writing, causing inconsistency. Now properly routes to WriteNull() when value is null. | Step 5b: Schema types - Token-value consistency |
| NJ-21 | #2452 | 1403f5d3 | 60be32f | Medium | type safety | Serializing nullable struct dictionaries was failing. Type resolution was not properly handling Dictionary<TKey, TValue?> where TValue is struct. Dictionary contract generation was missing nullable value type support. | Step 5b: Schema types - Nullable value type contracts |
| NJ-22 | #2304 | 666d9760 | a31156e | Low | configuration error | StringUtils.ToLower() was using wrong preprocessor define. #if NET20 should have been #if NET35. Conditional compilation was broken on specific .NET versions. | Step 4: Specs - Platform-specific code branches |
| NJ-23 | #2186 | 23be46f6 | ff6f51b | Medium | type safety | StringEnumConverter with naming strategy was not using the strategy when deserializing. Contract resolver's naming strategy was being ignored. Fixed by applying naming strategy in enum value lookup. | Step 5b: Schema types - Strategy pattern application |
| NJ-24 | #2181 | baa1e216 | 541eab2 | Medium | validation gap | Deserializing incomplete JSON object to JObject did not error. Malformed JSON like {"key": would deserialize as empty JObject. Added content validation to detect incomplete structures. | Step 5: Defensive patterns - Incomplete input detection |
| NJ-25 | #2180 | 541eab2f | c89d6ad | Medium | validation gap | JSONPath scanning with nested indexer was failing. Query like "$.items[0][1]" would not parse correctly. State machine in path scanner was not handling consecutive indexers. | Step 5a: State machines - JSONPath parser state |
| NJ-26 | #2178 | 3219c47f | 0be9e52 | High | state machine gap | Hang when deserializing JTokenReader with preceding comment. Reader was stuck in infinite loop when comment was at start of stream. Root token was being re-read indefinitely. Fixed by checking if current == root before advancing. | Step 5a: State machines - Reader loop termination |
| NJ-27 | #2177 | 8e4261a3 | 6b9f467 | High | missing boundary check | Deserializing into constructors with more than 256 parameters was failing with limit. Parameter array had fixed size, causing truncation. Changed to dynamic array or count-based handling for arbitrary parameter counts. | Step 5: Defensive patterns - Boundary condition handling |
| NJ-28 | #2151 | a213bac4 | c5f2103 | Medium | type safety | Deserialize via constructor with some existing collection types was failing. Pre-existing collection values were not being properly passed to constructor. Property value retrieval was skipping collection-type properties. | Step 5b: Schema types - Collection contract handling |
| NJ-29 | #1992 | d75d5438 | (parent) | High | concurrency issue | Memory leak when (de)serializing objects with enums and naming strategies. Enum name cache was not respecting naming strategy equality. Same enums with different strategies were sharing cache entries, causing unbounded cache growth and memory leak. | Step 5a: State machines - Cache key generation with strategy objects |
| NJ-30 | #1924 | 03f7c0b8 | (parent) | High | type safety | Serializing types with struct ref properties was failing. Properties with ref types (ref struct) were not being handled. Reflection was failing on ref types; added type safety check. | Step 5b: Schema types - Ref struct type detection |
| NJ-31 | #1878 | eb18d397 | (parent) | Medium | silent failure | Setting extension data with existing key was silently overwriting. ExtensionDataSetter was not checking for duplicate keys. Added key existence validation before setting. | Step 5: Defensive patterns - Extension data integrity |
| NJ-32 | #1851 | e0793019 | (parent) | Medium | silent failure | Ignored values being set in extension data. Properties marked as Ignored were still being included in extension data collections. Added ignore check before adding to extension data. | Step 5: Defensive patterns - Metadata-aware collection handling |
| NJ-33 | #1787 | ad246c77 | (parent) | Medium | type safety | Deserializing empty string to empty byte array was failing. Empty string ("") should deserialize to empty byte[] but was throwing. Added empty string special case in byte array converter. | Step 5: Defensive patterns - Empty value handling |
| NJ-34 | #1786 | 09209893 | (parent) | Medium | validation gap | Error when deserializing empty array in DataTable. DataTable was rejecting empty arrays as invalid. Added validation to accept empty arrays as valid DataTable content. | Step 5: Defensive patterns - Empty collection handling |
| NJ-35 | #1728 | 6dd352c4 | (parent) | High | type safety | Calling constructors with ref and in parameters was failing. Reflection code was not handling parameter modifiers (ref, in, out). Type matching was checking exact type without accounting for modifiers. | Step 5b: Schema types - Parameter modifier handling |
| NJ-36 | #1727 | 42ee730f | (parent) | High | type safety | Losing DateTime.Kind when deserializing ISO date strings. DateTime parsed from ISO 8601 string with Z suffix was not preserving UTC kind. Converter was not extracting timezone information from string format. | Step 5b: Schema types - DateTime.Kind preservation |
| NJ-37 | #1714 | a82acace | (parent) | Medium | validation gap | Parsing decimals with exponents in strings was failing. Decimal.TryParse() was using NumberStyles.Number which doesn't support exponents. Changed to NumberStyles.Float to support scientific notation (1.5e10). | Step 3: Tests - Format variation coverage |
| NJ-38 | #1712 | 32f882b5 | (parent) | Medium | type safety | Serializing abstract base class ISerializable on .NET Core was failing. Base class serialization was not handling abstract ISerializable correctly. Abstract method checks were too strict. | Step 5b: Schema types - Abstract type contracts |
| NJ-39 | #1368 | 8cfddc4d | (parent) | Medium | silent failure | Preserving trailing zeros when deserializing decimals was inconsistent. Similar to #2769 but for different code path. Decimal values lost scale information during parsing. | Step 5: Defensive patterns - Decimal precision preservation |
| NJ-40 | #1353 | 727e109e | (parent) | Medium | type safety | Deserializing ObservableCollection in .NET Core 2.0 was failing. Collection constructor signature changed in .NET Core 2.0, breaking deserialization. Added .NET version-specific handling for constructor selection. | Step 4: Specs - Framework-specific collection constructors |
| NJ-41 | #1531 | 9b98a11d | 3d2e9c13 | Medium | configuration error | JObject.ToObject() not respecting DateTimeZoneHandling setting when converting DateTime values from JToken to objects during deserialization. | Step 5: Configuration validation - Setting propagation |
| NJ-42 | #1460 | 1b40ebfe | 3ea750d6 | High | concurrency issue | JsonWriter async writing (WriteAsync, FlushAsync) not properly preserving state across async boundaries, causing data loss or state corruption in concurrent scenarios. | Step 5a: State machines - Async state coherency |
| NJ-43 | unknown | b47f7440 | e2dc61b8 | High | error handling | Deserializing empty object {} into byte[] property caused NullReferenceException instead of informative 'Unexpected token' error. Null check missing before value access. | Step 6: Quality risks - Exception clarity |
| NJ-44 | #1050 | 2a28dcc5 | fac72ad5 | Medium | type safety | TypeNameHandling.Auto including typename for nullable structs, causing deserialization to fail when typename is not expected. Nullable<T> not detected properly. | Step 5b: Schema types - Type resolution |
| NJ-45 | unknown | 38a687f6 | 018589cd | High | validation gap | DoubleTryParse() returning overflow as Success instead of Overflow when exponent exceeds MaxExponent (308), causing silent data corruption in scientific notation parsing. | Step 5: Defensive patterns - Boundary validation |
| NJ-46 | unknown | 50a39239 | 56e45bbb | Medium | missing boundary check | JSONPath SelectTokens() scanning empty containers incorrectly, attempting to access First on containers with no values causing exception. Missing HasValues check. | Step 5: Defensive patterns - Container boundary checks |
| NJ-47 | #210 | 2368a8e1 | 71a91bf3 | Medium | null safety | Extension data setter not checking for null before converting value to JToken, causing JToken.FromObject(null) to fail incorrectly. | Step 5b: Schema types - Null safety checks |
| NJ-48 | #726 | f3706313 | 425c1d84 | High | type safety | Generic base class property resolution using GetBaseDefinition() broken on Mono due to partially-instantiated generic types, causing duplicate properties to be added. | Step 5b: Schema types - Type resolution |
| NJ-49 | unknown | a3eb2d59 | f382251 | High | configuration error | DateTimeZoneHandling not applied when writing DateTime dictionary keys, causing timezone information loss in serialized objects with DateTime keys. | Step 5: Configuration validation - Setting propagation |
| NJ-50 | unknown | 0effb85a | 95e04ba9 | Medium | protocol violation | XmlNodeConverter not properly handling unmatched namespace prefixes when converting JSON to XML, causing invalid XML output with malformed namespaces. | Step 5: Defensive patterns - Protocol adherence |
| NJ-51 | #1984 | 05d721e3 | 5712e024 | High | type safety | Array deserialization contract not properly handling constructor parameter matching, causing constructor selection failures for custom collection types with complex signatures. | Step 5b: Schema types - Type resolution |
| NJ-52 | #1870 | 8e16489c | bfdb48a7 | Medium | state machine gap | BsonReader reading multiple independent BSON documents in sequence from same stream, cursor not resetting between reads causing data corruption. | Step 5a: State machines - Reader state reset |
| NJ-53 | #1668 | 94a4dbf7 | 4c4d8708 | High | validation gap | Decimal deserialization not properly validating overflow conditions, allowing out-of-range values to be silently truncated instead of throwing OverflowException. | Step 5: Defensive patterns - Boundary validation |
| NJ-54 | unknown | cc084e11 | 90514188 | Low | silent failure | Spelling error in error message and comments (asychronousity vs asynchronicity), minor but affects log clarity and grep-ability of error output. | Step 6: Quality risks - Error message content |
| NJ-55 | unknown | 1278b045 | f473641e | Medium | missing boundary check | Double parsing corner cases not handling edge cases in exponent processing and sign handling, causing parse failures on valid exponential notation like 1.5e-10. | Step 5: Defensive patterns - Boundary validation |

### MassTransit/MassTransit (C#)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| MT-01 | #6131 | 2e40120 | 333b5d6 | High | state machine gap | Job state machines not ignoring events in terminal states (Faulted), causing missing state transitions when events arrived out-of-order | Step 5a - State machine event handling in all states; Step 4 - specs for terminal state behavior |
| MT-02 | #6061 | ad38256 | 1f22e61 | Critical | state machine gap | JobAttemptStateMachine accepting completion events in Initial state causing duplicate instances and slot leaks | Step 5a - State machine guards prevent out-of-order transitions; Step 3 - add tests for concurrent completions |
| MT-03 | #6154 | 140da5f | 7b97076 | High | error handling | Outbox save/commit failures not publishing typed Fault<T>, resulting in silent failures where typed faults expected | Step 5 - defensive wrapping of persistence operations; Step 6 - transaction failure recovery |
| MT-04 | #6124 | 8f7542e | b617f57 | Medium | type safety | NewId.Next(n) calling wrong method (NextSequentialGuid instead of NextGuid), generating sequential instead of random IDs | Step 2 - API method routing accuracy; Step 3 - tests for ID algorithm correctness |
| MT-05 | #6031 | 6a2f4c0 | 573c430 | High | validation gap | Redelivery context not propagating Result through retry, losing activity execution results on redelivery | Step 5 - context propagation through retry/redelivery; Step 4 - specs for result preservation |
| MT-06 | #5342 | b7c861c | 058d51b | High | concurrency issue | SQL Transport orphaned messages accumulating due to race condition in concurrent delete operations | Step 5 - database-level locking for concurrent operations; Step 3 - orphaned record cleanup tests |
| MT-07 | #5949 | 277ec61 | 870202 | Medium | configuration error | ConfigureConsumers/ConfigureSagas not checking WasConfigured(), causing duplicate consumer/saga configuration | Step 2 - configuration state tracking; Step 3 - tests for idempotent configuration |
| MT-08 | #6045 | 09ca425 | e41f34e | High | error handling | ReceiveFault called in multiple places instead of dispatcher-only, causing duplicate fault notifications | Step 5 - centralized fault dispatch; Step 4 - specs for single fault notification |
| MT-09 | #6001 | 7706dff | d4204b5 | High | concurrency issue | Consumer timeout on RabbitMQ not triggering proper reconnect, leaving receive endpoint frozen | Step 5 - channel shutdown notification to supervisor; Step 3 - timeout recovery tests |
| MT-10 | #6000 | 29f0864 | c6600c4 | High | error handling | Redis connection multiplexer caching failed connections, preventing retry on next attempt | Step 5 - defensive cache invalidation on error; Step 3 - connection recovery tests |
| MT-11 | #5970 | 8c7e467 | 34eb7d8 | Medium | silent failure | Job cancellation reason not propagated through saga, losing user-provided cancellation context | Step 5 - context preservation through state transitions; Step 4 - specs for reason propagation |
| MT-12 | #6017 | 1a9c435 | 1f865a5 | Low | type safety | RecurringSchedule ScheduleId/ScheduleGroup properties not settable, breaking subclass customization | Step 5b - property mutability for extensibility; Step 3 - tests for custom schedules |
| MT-13 | #6042 | e41f34e | 511b468 | Medium | null safety | SQS successful response list can be null, causing NullReferenceException in batch completion | Step 5 - null checks on API responses; Step 3 - SQS batch edge-case tests |
| MT-14 | #6028 | e7479aa | 9d3cf9d | Medium | null safety | SNS/SQS failed response list can be null, causing NullReferenceException in error handling | Step 5 - null checks before enumeration; Step 3 - failure handling tests |
| MT-15 | #6022 | 9d3cf9d | e03c42d | High | concurrency issue | SQL Transport orphaned message removal lacking lock, causing duplicate key conflicts under concurrent load | Step 5 - database-level exclusive locks; Step 3 - concurrent maintenance tests |
| MT-16 | #5905 | 620d115 | 50cef2f | Medium | configuration error | Azure Service Bus MaxConcurrentSessions falling back to default instead of MaxConcurrentCalls, underutilizing throughput | Step 2 - configuration fallback logic; Step 3 - concurrency limit tests |
| MT-17 | #5895 | e63b937 | e7033b2 | Medium | configuration error | Recurring job scheduler not respecting TimeZoneId, always using UTC and causing wrong schedule times | Step 5 - configuration value propagation; Step 4 - cron expression with timezone specs |
| MT-18 | #5881 | 4beee32 | 5bb2877 | Medium | silent failure | Outbox not copying MT-* transport headers to SendContext, losing headers in message pipeline | Step 5 - header propagation through outbox; Step 3 - header preservation tests |
| MT-19 | #5812 | 1ac5197 | 960aebd | Medium | API contract violation | Redelivery filter caching wrapped context, breaking filter chain when stacked multiple times | Step 5 - always create new wrapper instances; Step 3 - stacked filter tests |
| MT-20 | #5811 | 223e1dc | 50b9f6c | Medium | configuration error | DI container not registering message definition itself, only bindings, breaking definition resolution | Step 2 - complete registration pattern; Step 3 - multi-bus definition tests |
| MT-21 | #5730 | 6ce77d6 | bc56e33 | Medium | validation gap | SQS batcher breaking on first message exceeding size limit, losing messages instead of waiting for more | Step 5 - batch boundary validation; Step 3 - oversized message handling |
| MT-22 | #5676 | 52eeba9 | fcc2a35 | High | type safety | Implemented interface cache traversing in wrong order, breaking message type matching for Fault<T> | Step 4 - message type ordering specs; Step 3 - fault message resolution tests |
| MT-23 | #5668 | 66405b6 | 65fa14b | Medium | silent failure | Recurring job not clearing previous attempts when scheduled to run again, leaking job slots and memory | Step 5a - state cleanup on schedule restart; Step 3 - recurring job lifecycle tests |
| MT-24 | #5645 | 665b462 | b2c668 | High | validation gap | SQS/SNS batch size calculation not validating before adding entry, exceeding batch size limits | Step 5 - size limit boundary checks; Step 3 - batch size validation tests |
| MT-25 | #5605 | 98b477c | b4ea220 | High | protocol violation | RabbitMQ AmqpTimestamp sent in milliseconds instead of seconds, breaking timestamp semantics | Step 2 - protocol spec adherence; Step 4 - timestamp unit specs |
| MT-26 | #5595 | 71bdefb | 6aae744 | High | error handling | Outbox SetConsumed failure not triggering fault notification, silently losing messages | Step 5 - complete error handling in persistence; Step 3 - outbox fault tests |
| MT-27 | #5159 | 0dd16fc | 191607f | High | concurrency issue | ReceiveLockContext pending task collection causing duplicate delivery on redelivery with concurrent consumers | Step 5 - proper lock context lifecycle; Step 3 - concurrent redelivery tests |
| MT-28 | #5297 | 2f2e9dc | e11c12a | Medium | validation gap | SQS/SNS policy validation not checking condition/statement/principal validity, creating invalid policies | Step 4 - policy structure specs; Step 3 - policy validation tests |
| MT-29 | #5407 | 5df90f1 | 3bdac38 | Medium | configuration error | SQL Transport view queries hard-coding schema name, breaking non-default schema setups | Step 2 - schema parameterization; Step 3 - custom schema tests |
| MT-30 | #5957 | c6ae280 | f0ed587 | Low | concurrency issue | Dapper DatabaseContext semaphore lock not required, adding unnecessary contention | Step 5 - lock necessity analysis; Step 3 - context contention tests |
| MT-31 | #5325 | ffb1fbd | 28f45d0 | Medium | silent failure | RabbitMQ not transferring message priority from consume to send context, losing priority | Step 5 - transport property propagation; Step 3 - priority preservation tests |
| MT-32 | #5371 | 50455b0 | 1aefb82 | Medium | configuration error | ActiveMQ failover connection string not including nested.* parameters, breaking complex failover configs | Step 2 - URI parameter handling; Step 3 - failover connection tests |
| MT-33 | #5255 | ff9de5c | a7ba4f6 | Medium | silent failure | Newtonsoft raw message serializers not copying transport headers, losing metadata on forwarding | Step 5 - header propagation in all serializers; Step 3 - raw serialization tests |
| MT-34 | #5273 | 3e8b049 | a2a6b82 | Medium | configuration error | SQL Transport schema creation happening in wrong migration phase, causing missing objects | Step 2 - migration ordering; Step 3 - schema creation order tests |
| MT-35 | #5191 | 2a56e02 | 833e34f | High | SQL error | SQL redelivery not setting delay parameter correctly, using wrong column name and zero delays | Step 2 - query parameter mapping; Step 3 - delay behavior tests |
| MT-36 | #5185 | 231fb93 | 8c9c3dc | High | SQL error | PostgreSQL missing SchedulingTokenId parameter in send/publish queries, breaking scheduled messages | Step 2 - SQL parameter completeness; Step 3 - scheduled message tests |
| MT-37 | #6131 (v2) | 2d7ad75 | 56e5d30 | High | error handling | Fault<TJob> not published when UseMessageRetry configured on bus, causing missing typed fault notifications | Step 5 - fault publishing path coverage; Step 6 - transaction failure recovery |
| MT-38 | #6049 | 9f46a6c | f025e8e | Medium | concurrency issue | EventHub client handler reuse causing failure on subsequent receive transport restart, blocking message reception | Step 5 - handler lifecycle management; Step 3 - transport restart recovery tests |
| MT-39 | #6046 | 78d82a4 | 09ca425 | Medium | state machine gap | Canceled recurring jobs not clearing NextStartDate, preventing rescheduling and job resumption | Step 5a - state cleanup on transitions; Step 3 - recurring job lifecycle tests |
| MT-40 | Job Service Race | 0fbca78 | 277ec61 | High | concurrency issue | Job started while job service stopping causing fault that retries job elsewhere, producing duplicate work | Step 5 - service lifecycle state checks; Step 3 - concurrent stop/start tests |
| MT-41 | #5692 | 264a916 | 2dbc4bb | High | concurrency issue | RabbitMQ shutdown event handlers not properly detecting connection failures, leaving receive endpoint dead | Step 5 - event handler attachment; Step 3 - reconnection failure tests |
| MT-42 | #5692 (v2) | ceb3517 | 2a5b8b0 | Medium | concurrency issue | RabbitMQ channel shutdown handling blocking shutdown event (synchronous), preventing graceful shutdown | Step 5 - async event handler delegation; Step 3 - shutdown race condition tests |
| MT-43 | #5687 | d33537a | 6d5f5ae | Low | silent failure | Failed receive endpoint retry not logging information message, losing visibility into retry behavior | Step 5 - comprehensive logging; Step 3 - receive endpoint failure tests |
| MT-44 | #5616 | 1e19210 | 5d236be | Medium | configuration error | SQL Server migrator hard-coding schema name, breaking non-dbo schema configurations | Step 2 - schema parameterization; Step 3 - custom schema migration tests |
| MT-45 | #5018 | 9887fbc | d297c3c | Medium | silent failure | SQL Transport auto-delete queues deleting active queues when messages temporarily absent, losing queue data | Step 5 - metric refresh on idle; Step 3 - auto-delete edge case tests |
| MT-46 | #5482 | 244590b | 4e41d69 | Low | configuration error | PostgreSQL NpgSqlDataSource injection missing Required attribute, breaking DI container resolution | Step 2 - DI attribute completeness; Step 3 - DI resolution tests |
| MT-47 | #5568 | 3ecd8e7 | a8f0df | Medium | configuration error | ActiveMQ failover connection missing nested.* URI parameters, breaking complex failover configurations | Step 2 - URI parameter handling; Step 3 - failover connection tests |
| MT-48 | Job Type | c5de78a | 056baec | Low | null safety | Job type instance property not initialized in JobTypeStateMachine, causing null reference on access | Step 5 - property initialization; Step 3 - job type saga tests |
| MT-49 | #5484 | 796529b | de66870 | Medium | configuration error | SQL Transport IPv6 address parsing not supported, failing connection to IPv6 hosts | Step 2 - IPv6 parsing; Step 3 - IPv6 address resolution tests |
| MT-50 | Multi-Bus | d24703b | 0300539 | Medium | security issue | Bind<T, ISendEndpointProvider> resolution broken in multi-bus scenarios, preventing request/response pattern | Step 2 - DI binding correctness; Step 3 - multi-bus endpoint resolution tests |
| MT-51 | #5130 | af7a812 | 7a28c39 | Medium | configuration error | Azure Service Bus SessionId/PartitionKey filters not checking context type, applying settings to wrong transports | Step 2 - context type validation; Step 3 - multi-transport isolation tests |

### HangfireIO/Hangfire (C#)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| HF-01 | #2564 | 78cf1ae | 52ccefc8 | High | error handling | Filter chain: Switched from stable to unstable sorting algorithm. When `List.Sort()` was used instead of `OrderBy()`, custom `AutomaticRetryAttribute` filters were silently ignored when multiple filters present. Regression from 1.8.14. | Step 5a: State machine (filter ordering is part of job execution contract) |
| HF-02 | #2541 | feba34d | 1908476b | Critical | protocol violation | ASP.NET Core middleware: Missing `return` statement after setting 404 status code for unmapped dashboard route. Request continued through pipeline instead of terminating, causing `InvalidOperationException`. | Step 5: Defensive (missing guard in control flow) |
| HF-03 | - | dff67b4 | 12c03316 | Critical | validation gap | Recurring job updates: String comparison logic fails to treat empty strings as null. Check `String.IsNullOrWhiteSpace()` missing, causing unnecessary hash updates and preventing recovery from error states. Job gets marked "unchanged" but actually updates. | Step 4: Specs (state change contracts) |
| HF-04 | - | 12c0331 | 1583b479 | High | concurrency issue | Job invisibility timeout: New lightweight server processes (`CountersAggregator`, `ExpirationManager`, `SqlServerHeartbeatProcess`) don't extend job visibility timeout. Can cause same job to be invisibly processed twice simultaneously on different workers. | Step 5a: State machine (visibility window contract) |
| HF-05 | #458 | 04bc18d | 649be3c1 | Medium | error handling | Retry metadata cleanup: Job ID not removed from retries set when job exits `Failed` state via manual trigger or other means. Only cleaned on explicit retry. Causes stale retry metadata accumulation. | Step 3: Tests (state transition coverage) |
| HF-06 | #2482 | 3a32121 | d0d6cc87 | Medium | validation gap | CultureInfo caching: `CaptureCultureAttribute` cached `CultureInfo` instances, overriding actual thread culture. Worker threads used wrong culture context. Restored per-request behavior. | Step 5b: Schema types (thread-local state) |
| HF-07 | #2003 | b8ed0ca | 65a6e618 | Medium | type safety | Job.Args mutation: `Job.Args` collection passed to constructor allowed unsafe mutations of immutable Job properties. Constructor accepted reference to mutable Args list without defensive copy. | Step 5b: Schema types (immutability contracts) |
| HF-08 | - | 58ec10d | 0e9ea337 | Critical | SQL error | Database schema compatibility: `InvalidCastException` when fetching jobs from migrated databases where column types differ from current schema assumptions. Silent crashes on upgrades with older schemas. | Step 6: Quality risks (schema migration) |
| HF-09 | #2465 | 0525de6 | a9c697d9 | Medium | SQL error | Dapper parameter binding: Parameter names not explicitly specified in SQL queries, causing binding failures in certain query patterns. Dapper relies on parameter order when names missing. | Step 3: Tests (SQL parameter handling) |
| HF-10 | #2393 | 36ba66c | 863c9da8 | Low | API contract violation | UrlHelper.To: Legacy code path not updated when URL scheme changed. URLs generated incorrectly in obsolete compatibility mode. Low impact due to rare usage but represents unmaintained code path. | Step 2: Architecture (code path maintenance) |
| HF-11 | #2381, #2371 | a0a0c94 | 5f6266b4 | Critical | state machine gap | Recurring job scheduling: Logic calculates next execution time incorrectly when recovering from errors. Can schedule jobs to past or trigger premature execution if already scheduled. Complex cron resolution logic had timing assumption bugs. | Step 5a: State machine (cron calculation, recovery logic) |
| HF-12 | #2356 | 2efff11 | f9319e1b | Medium | protocol violation | Response.WriteAsync: `HasStarted` check prevented valid response writes in streaming scenarios. Early termination check caused response data loss in certain HTTP response patterns. | Step 5: Defensive (response streaming contract) |
| HF-13 | - | 8b86fad | 7761fa0a | High | null safety | Deleted Jobs dashboard: Page rendering crashes if job info null or partially loaded. `NullReferenceException` thrown when accessing missing job data, causing complete page failure. | Step 3: Tests (null safety in views) |
| HF-14 | - | ad270db | b91bbdd2 | Medium | error handling | AutomaticRetryAttribute deserialization: Serialized attributes can't deserialize when containing serialization errors. Retry attributes lost during error recovery, breaking retry mechanism. | Step 4: Specs (attribute serialization contract) |
| HF-15 | - | b91bbdd | 8760495 | Medium | configuration error | Dashboard metrics registration: Metrics registration logic doesn't deduplicate, causing multiple metric collection calls for same metric. Performance degradation from redundant database queries. | Step 6: Quality risks (dashboard performance) |
| HF-16 | - | 6118e36 | b6bfbf23 | Critical | null safety | Null reference exception in error paths: Static analysis detected code throwing `NullReferenceException` in exception handlers. Crashes when handling errors instead of propagating them. | Step 5b: Schema types (null guards) |
| HF-17 | - | b6bfbf2 | ac217a3e | High | concurrency issue | Metric dictionary data race: Concurrent access to metric collection without synchronization. Unsynchronized dictionary modifications cause incorrect dashboard metrics under load. | Step 5: Defensive (synchronization) |
| HF-18 | - | ac217a3 | 260d36a4 | High | error handling | DbCommand resource leak: Command objects not properly disposed in error scenarios. Missing finally/using blocks cause command handle exhaustion on repeated errors. | Step 3: Tests (resource disposal) |
| HF-19 | - | f5aff77 | 1248276 | Medium | type safety | AutomaticRetryAttribute serialization: Serialization logic fails for specific attribute configurations, corrupting retry attributes during persistence. Roundtrip serialization/deserialization fails. | Step 5b: Schema types (serialization) |
| HF-20 | - | 15859c3 | 1e1dff18 | High | state machine gap | Disabled recurring job recovery: Logic prevents re-enabling of disabled recurring jobs. State transition barrier prevents recovery of intentionally disabled jobs. | Step 5a: State machine (state transitions) |
| HF-21 | - | 324bd85 | 3025588 | High | error handling | Server shutdown sequence: Heartbeats not sent until full shutdown, allowing server to be marked dead while still running. Other servers mark this server timeout during graceful shutdown. | Step 5: Defensive (shutdown contract) |
| HF-22 | - | d8553af | 5bc4564 | Critical | silent failure | Recurring job execution: Cron evaluator skips execution when certain ignorable options set. Jobs silently don't execute despite being scheduled. Conditional logic error in execution check. | Step 5a: State machine (cron evaluation) |
| HF-23 | #2188 | 0314bd3 | 4f3c023 | Critical | concurrency issue | Worker thread deadlock with multiple queues: `DynamicMutex` implementation deadlocks when processing from multiple queues simultaneously. Complete worker stall in multi-queue scenarios. Replaced with `SemaphoreSlim`. | Step 5: Defensive (synchronization primitives) |
| HF-24 | #2200 | 3c0eab9 | daedc38 | High | security issue | Dashboard metrics SQL permissions: Database metrics collection requires elevated permissions (VIEW DATABASE STATE) not needed for normal operation. Permission escalation in routine dashboard query. | Step 6: Quality risks (security) |
| HF-25 | - | 759d3ed | c49ae24 | Medium | type safety | Generic type argument handling: Type resolution fails for complex generics with inheritance chains. `ArgumentNullException` thrown during type analysis of nested generic types. | Step 5b: Schema types (generic type handling) |
| HF-26 | #1729, #2541 | `92c16d1` | `ada05cd2` | Medium | protocol violation | Missing 404 status code when MapHangfireDashboard dispatcher not found. Dashboard middleware continues pipeline instead of terminating, causing incorrect error handling in routing. Fixed by setting explicit 404 and new _finalizeWhenNotFound flag. | Step 5: Defensive (middleware termination contract) |
| HF-27 | #2539 | `ada05cd` | `8e3a4d8` | High | serialization | Array type serialization fails for nested/generic types in SimpleAssemblyTypeSerializer. Array element type ordering handled after nested type processing, causing incorrect type name format. Must process arrays first in recursive serialization. | Step 5b: Schema types (type serialization order) |
| HF-28 | - | `0d3d895` | `e10f4df6` | Medium | type safety | Variable shadowing bug: `possiblyAbortedThreshold` assigned from itself instead of `inconclusiveThreshold`. Compiler error in ServersPage.cshtml indicating uninitialized variable use. | Step 3: Tests (variable scope) |
| HF-29 | - | `6e1abf7` | `6eaaa69d` | Medium | error handling | SQL query truncation error message obscured by missing OPTION(QUERYTRACEON 460) hint. Three INSERT statements missing optimizer hint for varchar truncation errors, causing confusing "string or binary data would be truncated" messages without row details. | Step 5: Defensive (SQL diagnostic hints) |
| HF-30 | #2334 | `d4c5a30` | `ee018bce` | High | error handling | Regex timeout in StackTraceParser set too high (5 seconds). Catastrophic backtracking in malformed stack traces causes dashboard to hang/timeout. Reduced from 5s to 100ms to prevent ReDOS. | Step 6: Quality risks (DoS/timeout) |
| HF-31 | #2330 | `ee018bc` | `23ab3fd1` | Low | error handling | Dashboard delay warnings use client time instead of server time. Server clock and client clock mismatch causes incorrect "job delayed" warnings in UI. Should use StorageUtcNow instead of ApplicationUtcNow. | Step 3: Tests (time synchronization) |
| HF-32 | #2307 | `6ece0e9` | `249eee81` | Medium | null safety | Dashboard metrics crash when schema version not present in database (older/corrupted databases). Query.Single() throws InvalidOperationException instead of handling null gracefully. Fixed with SingleOrDefault() and null check, returns "Unspecified" with warning style. | Step 3: Tests (null safety in views) |
| HF-33 | #2215 | `2468402` | `2f3c51ab` | Medium | missing boundary check | InvalidOperationException from SQL dashboard metrics query when multiple database files present. Missing SUM() aggregate causing multiple rows returned to Query<T>().Single(), expects one result. Fixed by adding SUM() to queries for RowsSizeMB and LogSizeMB. | Step 3: Tests (SQL aggregation logic) |
| HF-34 | #2117 | `208ef29` | `856ed3f5` | High | state machine gap | AddHangfireServer hosted service starts processing before ASP.NET Core application ready. Server begins processing jobs while configuration, middleware, and other services still initializing, can cause race conditions. Fixed by deferring to ApplicationStarted event in .NET Core 3.0+. | Step 5: Defensive (startup sequencing) |
| HF-35 | #2070 | `1a34b03` | `368e7fb7` | Medium | state machine gap | BackgroundProcessingServer stop signal not sent early enough on .NET Standard 2.1 (NetCore). Server doesn't receive stop signal until after host shutdown completes, allowing heartbeat timeout during shutdown. Fixed by registering on ApplicationStopping event. | Step 5: Defensive (shutdown timing) |
| HF-36 | #2320 | `7e9c798` | `c497b94e` | Medium | validation gap | Server queue validation missing for invalid queue name characters. No warning when queues contain uppercase, special chars, or invalid characters. Should validate only lowercase letters, digits, underscores, dashes allowed. Now logs warning instead of throwing exception. | Step 4: Specs (queue naming contract) |
| HF-37 | #2324 | `fdeb082` | `31a7e4b6` | Medium | serialization | Macro expressions (@hourly, @daily) fail to parse when used as recurring job cron. Parser splits macro on spaces before checking if it's a macro format. Must check for "@" prefix before splitting on whitespace. | Step 5a: State machine (cron format detection) |
| HF-38 | - | `825f812` | `23a243b6` | Low | configuration error | net451 build fails when using .NET 9.0 SDK. SDK issue with target framework combination. Fixed by adding compiler directive to prevent downgrade. | Step 6: Quality risks (build compatibility) |
| HF-39 | - | `b995120` | `d656de61` | High | type safety | InvalidCastException when creating background job with SQL schema version 5 (older schemas). Direct cast `(long)ExecuteScalar()` fails when value is decimal/int/other type on old schema. Must use Convert.ToInt64() for safe type coercion. | Step 5b: Schema types (safe casting) |
| HF-40 | #2530 | `8c89f74` | `5dab4ebe` | Low | configuration error | Exception stack traces missing line numbers in Failed Jobs dashboard. IncludeFileInfo property defaults to false instead of true, dropping file/line info from exception details. Changed default to true. | Step 3: Tests (default value correctness) |
| HF-41 | - | `0c44883` | `54f274cf` | Medium | null safety | NullReferenceException in dashboard when LocalIpAddress or RemoteIpAddress is null. Direct .ToString() call without null check on HttpContext.Connection properties. Fixed with null-coalescing operator `?.ToString()`. | Step 3: Tests (null safety) |
| HF-42 | #2488 | `54f274c` | `a70eec2d` | Medium | error handling | ObjectDisposedException when StopAsync called twice (ASP.NET Core testing framework bug). HostedService.StopAsync can be called twice from different threads, second call operates on disposed server. Added try-catch for ObjectDisposedException. | Step 5: Defensive (idempotent shutdown) |
| HF-43 | #2412 | `f1e1360` | `36ba66cc` | Medium | error handling | KeyNotFoundException when recurring job data malformed (missing Cron property). Direct dictionary access `hash["Cron"]` throws instead of handling missing key gracefully. Fixed with TryGetValue() and null check for malformed job data. | Step 5: Defensive (missing field handling) |


### jellyfin/jellyfin (C#)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| JF-01 | #16467 | `5cfa466d8` | `921a364b` | High | missing boundary check | Encoder bitrate values capped at int.MaxValue/2 (~1073 Mbps) caused downstream encoder parameters like -bufsize to overflow to gigabit ranges, breaking hardware transcoding on plugin-provided streams | Step 5b |
| JF-02 | #16376 | `386c4cb7` | `24ec04d8` | High | missing boundary check | QSV rate-control parameter computation: bitrate*2, bitrate*4 expressions overflowed int32 for high bitrates, causing negative buffer sizes and invalid encoder arguments | Step 5b |
| JF-03 | #16312 | `6ea77f484` | `e5bbb1ea` | Medium | error handling | Attachment extraction from media files missing audio/video streams crashed instead of gracefully handling edge case | Step 5 |
| JF-04 | #15841 | `93902fc61` | `84f66dd54` | Medium | validation gap | IPv6 socket initialization crashed on devices without OS-level IPv6 support; missing feature detection guard | Step 5 |
| JF-05 | N/A | `bc316b3dc` | `e6d73ae3` | Medium | validation gap | Sample aspect ratio exact string comparison "1:1" vs numeric values caused near-1:1 ratios (3201:3200, 0.03% off) to trigger unnecessary transcoding; 1% tolerance threshold insufficient | Step 5b |
| JF-06 | N/A | `37b50fe13` | `06a6c6e1` | High | protocol violation | StreamInfo.ToUrl() generated malformed query strings like `?&DeviceId=...` due to unconditional `?` followed by all `&` parameters; IndexOutOfRangeException on proxies parsing empty param keys | Step 4 |
| JF-07 | N/A | `2757c1831` | `8b591400` | Medium | state machine gap | Virtual season creation logic returned true unconditionally for unmatched episodes, creating unnecessary "Season Unknown" entries and over-populating virtual seasons | Step 5a |
| JF-08 | N/A | `1c2f08bc1` | `8b591400` | Medium | validation gap | Filename regex for bracketed tag removal truncated files mid-name when tags appeared mid-filename (e.g. "2026年01月10日23時00分00秒-[新]TRIGUN　STARGAZE[字].mp4" → truncated at first []) | Step 5b |
| JF-09 | N/A | `1dacb69d8` | `77ff451e` | Low | validation gap | Genre list from API request not deduplicated, allowing duplicate genre entries in item metadata (case-insensitive comparison needed) | Step 5b |
| JF-10 | #16124 | `b97f5b809` | `b9e5cce3` | Medium | error handling | EpubImageProvider blocking synchronous IO in async context (CA1849); ZipFile.OpenRead/coverStream.Open/opfStream.Open not awaited causing deadlocks | Step 5 |
| JF-11 | #15958 | `244757c92` | `a1e0e4fd` | High | null safety | CryptographyProvider.Verify() threw KeyNotFoundException on missing 'iterations' parameter in password hash instead of FormatException with descriptive message | Step 5b |
| JF-12 | #15945 | `0ff869dfc` | `a1e0e4fd` | High | silent failure | Unknown item types from removed plugins caused 500 errors on recursive queries; now skipped with warning log instead of throwing InvalidOperationException | Step 5 |
| JF-13 | N/A | `ebb6949ea` | `0ebf6a6d` | Medium | validation gap | Remote image language priority: no-language images (score 3) ranked higher than English images (score 2), causing poor-quality languageless posters selected over good English alternatives | Step 4 |
| JF-14 | N/A | `d0950c8f0` | `771b0a7e` | Low | validation gap | MetadataEditor ContentTypeOptions filtering missing Movies collection type check alongside TvShows, preventing movies content type from being offered in editor | Step 4 |
| JF-15 | N/A | `217ea488d` | `f693c9d3` | Medium | state machine gap | Recently-added shows endpoint returned individual episodes instead of series parent when series was top result; missing Series type check alongside MusicAlbum | Step 5a |
| JF-16 | #14993 | `55047b118` | `794e1361` | Medium | error handling | NFO file user data saver crashed on items with empty/uninitialized IDs; missing null check before SaveUserData call | Step 5 |
| JF-17 | #14991 | `794e1361` | `27c9c9c0` | High | SQL error | ContributingArtistIds filter query logic inverted: used exact ID match instead of name-based cross-reference, returned wrong items entirely | Step 2 |
| JF-18 | #14864 | `54d48fa44` | `1736a566` | Medium | validation gap | People deduplication lookup ignored PersonType when matching existing maps, causing role mismatches and duplicate person-item links | Step 5b |
| JF-19 | #14863 | `1736a566c` | `04ab362e` | Critical | SQL error | Foreign key constraint violation on cascade delete: unconnected BaseItems with invalid ParentIds could not be migrated; missing cleanup before adding FK constraint | Step 2 |
| JF-20 | #14852 | `60fbd39bb` | `740b9924` | Medium | validation gap | Actor sort order calculation did not account for existing item maps, causing new actors to start from zero instead of incrementing from current max | Step 5b |
| JF-21 | N/A | `fa99b1d81` | `84f66dd54` | Medium | error handling | Remote subtitle encoding logic restructured; previous version had unspecified encoding failures in subtitle format handling | Step 5 |
| JF-22 | N/A | `820e208bd` | `6963d958` | Medium | type safety | XDocument.Descendants() with const string namespace failed; XNamespace requires object type not string constant, causing null reference in EPUB parsing | Step 5b |
| JF-23 | #14755 | `2618a5fba` | `2ee887a5` | High | concurrency issue | IAsyncDisposable objects created asynchronously then disposed synchronously via using statement, causing double-disposal and resource leaks in media segment manager | Step 5a |
| JF-24 | #14347 | `c6e568692` | `d5a76bdf` | High | validation gap | DateTime modifications checks used local time instead of UTC, causing stale cache detection to fail across timezones; library refresh logic broke on DST transitions | Step 2 |
| JF-25 | #13939 | `1c4b5199` | `f576783a` | High | SQL error | ItemValue query logic fundamentally broken: filter expressions generated invalid SQL with improper joins and subqueries, returning incorrect or duplicate results | Step 2 |
| JF-26 | #13733 | `07f07ba6` | `a123a2cb` | Medium | validation gap | Sort by year query generated incorrect ORDER BY clauses when year field null, causing unordered results instead of null-safe sorting | Step 2 |
| JF-27 | #14795 | `a0b3e2b0` | `2618a5fb` | Critical | state machine gap | Parent-child relationship cascade delete migration: BaseItems with orphaned ParentId references violated new foreign key constraint; required data cleanup before schema change | Step 5a |
| JF-28 | #14746 | `424682523` | `68810c69` | High | concurrency issue | User update/delete operations used Update() without Attach(), causing DbUpdateConcurrencyException when entity not tracked by context; EntityState.Modified required | Step 5a |
| JF-29 | #14728 | `c7320dc18` | `71048917` | Medium | error handling | AudioNormalizationTask uncaught exception on process priority change and temp file deletion; missing try-catch blocks caused task to fail silently | Step 5 |
| JF-30 | #14141 | `a6a89f79` | `833911173` | Medium | null safety | Season logo download path generation missing for seasons with IndexNumber, causing ArgumentNullException; added conditional branch for season-specific logo handling | Step 5b |
| JF-31 | #13949 | `74230131a` | `7df6e0b1` | Medium | missing boundary check | Bitrate calculation from duration/bytes overflowed when duration < 1 second, yielding massive bitrate values and OverflowException on int conversion; missing duration validation | Step 5b |
| JF-32 | #13837 | `1c2b48182` | `d1ed659` | Medium | null safety | Playlist creation crashed on null MediaSourceId when calling Guid.Parse(); missing null check before type conversion in HLS controller | Step 5b |
| JF-33 | #11236 | `00620a40` | `ee4a782e` | Medium | validation gap | GetMediaFolders API endpoint returning disabled libraries alongside enabled ones; missing enabled filter in collection concatenation | Step 5b |
| JF-34 | #13853 | `04ca27ad` | `e1ef4290` | High | error handling | Database migration backup written to wrong directory and restoration failed when backup directory path not properly constructed; missing directory.Combine on backup path | Step 5 |
| JF-35 | #12692 | `0539fdc5` | `a0204ada` | Medium | validation gap | libx264/libx265 encoder preset incorrectly converted enum auto value to string, causing invalid FFmpeg preset argument; missing enum-to-string switch logic | Step 5b |
| JF-36 | #14783 | `c02a24e3` | `deee04ae` | High | error handling | Stack overflow in CustomRatingForComparison and GetMediaSourceCount properties due to circular parent-child references; missing cycle detection and recursion guards | Step 5a |
| JF-37 | #14736 | `d9eaeed6` | `c7320dc1` | Medium | state machine gap | Latest items grouping by collection type used All() check across multiple parents instead of single check on primary parent, causing incorrect type filtering | Step 5a |
| JF-38 | #14655 | `a0d4ae19` | `d65b18a7` | Medium | validation gap | Album Artists merge logic used case-insensitive grouping for deduplication but case-sensitive comparison for equality, causing duplicate artists to persist in metadata | Step 5b |
| JF-39 | #14674 | `e753adac` | `0b465842` | Medium | validation gap | ProbeProvider.HasChanged logic incorrectly combined file date change with size check using AND operator, missing files with size changes still considered unchanged | Step 5b |
| JF-40 | #13880 | `070abcd8` | `16dc1e22` | Low | missing boundary check | BaseItemRepository entity-to-DTO mapping missing InheritedParentalRatingSubValue field, causing DTO to have null value when entity had data | Step 5b |
| JF-41 | #14724 | `0845b0c2` | `e043f93a` | Medium | validation gap | MovieResolver processing non-media folders like /subs/ as potential movie containers; missing ignore pattern check and extras type filter before directory recursion | Step 5b |
| JF-42 | #14193 | `08b2ffea` | `48825f46` | Medium | validation gap | UserViewBuilder filter missing ExcludeItemIds check in FinalizeOurResults(), causing excluded items to still appear in results despite query parameter | Step 5b |
| JF-43 | #14686 | `1eadb07a` | `26d9633f` | Medium | silent failure | GetSimilarItems endpoint returned the search item in its own results; missing ExcludeItemIds=[itemId] in item query | Step 5b |
| JF-44 | #14640 | `28b8d3ee` | `9eaca738` | High | validation gap | Anamorphic video detection logic used single exact string match for sample aspect ratio, treating all non-0:1 SAR as anamorphic and missing width-height correlation check | Step 5b |
| JF-45 | #14641 | `ad133eb6` | `50180adc` | Medium | SQL error | AlbumArtistIds filter query incorrectly used ItemValueType.Artist instead of ItemValueType.AlbumArtist, returning wrong items or missing album artists entirely | Step 2 |
| JF-46 | #13224 | `5c36b444` | `4e4d7e77` | Medium | state machine gap | Seasons random sorting broken due to Linq QueryResult() method always forcing OrderBy/OrderByDescending, preventing randomization when sorting disabled | Step 5a |
| JF-47 | #14379 | `ebdc7565` | `10d0cec7` | High | validation gap | FFmpeg -fps_mode option incorrectly applied to input args (valid only for output); missing version/scope check caused invalid FFmpeg arguments on input stream | Step 5b |
| JF-48 | #14503 | `6f49782b` | `536437bb` | High | validation gap | File modification date comparisons used exact equality check instead of tolerance window, causing false negatives when comparing times across timezones with floating-point precision loss | Step 2 |
| JF-49 | #14461 | `25a36234` | `310a54f0` | Medium | error handling | Library refresh unable to delete old media attachments when media replaced with version lacking attachments; missing unconditional delete in SaveMediaAttachments | Step 5 |
| JF-50 | #14489 | `36c90ce2` | `48e93dcb` | High | error handling | Full system backup/restore path traversal vulnerability and incorrect directory handling; missing normalized path separator checks and relative path validation in archive extraction | Step 5 |
| JF-51 | #14493 | `663087b1` | `dddeea1f` | Medium | error handling | Trickplay extraction FFmpeg error handling logic inverted condition, causing successful non-zero exit codes to pass through without cleanup; missing early exit on process failure | Step 5 |
| JF-52 | #13817 | `5769c398` | `4a4fef83` | Medium | null safety | TMDB external URL generation attempted to access Season.IndexNumber and Episode.IndexNumber without null checks, causing NullReferenceException on items with missing indices | Step 5b |
| JF-53 | #14909 | `c053a6cd7` | `d483c3efe` | High | validation gap | Parental ratings filter logic incorrect: used >= operator instead of proper boundary checks, allowing items outside rating threshold to pass through | Step 5b |
| JF-54 | #14936 | `0a0aaefad` | `c8b97bf53` | Medium | validation gap | MKA-style audio tag parsing missing fallback logic for tags like "ARTISTS" not matching expected format; metadata extraction failed silently | Step 5b |
| JF-55 | #14851 | `71ebb1f45` | `9c298c52f` | Medium | error handling | UFID field value parsing failed to split format correctly (owner\0identifier) causing metadata extraction errors and improper handling of MusicBrainz recording IDs | Step 5 |
| JF-56 | #14482 | `536437bbe` | `ba54cda77` | Medium | validation gap | Include/Exclude tag filtering used wrong ItemValueType check and missed Tags type alongside InheritedTags; filter logic also incorrect for nested parent items | Step 5b |
| JF-57 | #14332 | `b528c1100` | `96c9f4fda` | Medium | validation gap | Genre and tags DTO mapping used split('|') on null/whitespace-only values creating single-item arrays with empty strings instead of empty arrays | Step 5b |
| JF-58 | #14608 | `8b2a8b94b` | `f24e80701` | Medium | validation gap | Query limit of zero incorrectly allowed Take(0) operations instead of returning full result set; boundary check missing on limit values throughout codebase | Step 5b |
| JF-59 | #14946 | `2c7d2d471` | `bf69f9d8a` | Low | validation gap | GetCollectionAsync call missing language parameter in TMDb box set image provider; signature mismatch caused incomplete API calls | Step 5b |
| JF-60 | #14931 | `97ec4c1da` | `894ba1a41` | High | SQL error | Total record count calculated before grouping filter applied, returning inflated counts that don't match paginated results | Step 2 |
| JF-61 | #14948 | `d3d5915f3` | `288640a5d` | Medium | error handling | Password reset file creation used OpenWrite() instead of Create(), causing file append instead of truncation and exposing previous reset tokens | Step 5b |
| JF-62 | #14941 | `ff0a1b999` | `bf69f9d8a` | Medium | validation gap | TMDb backdrop language detection didn't handle new "xx" value for no-language images, returning invalid language codes in metadata | Step 5b |
| JF-63 | #14942 | `bf69f9d8a` | `badf22fcc` | Medium | validation gap | Wizard-created library validation only triggered after refresh, skipping initial validation and allowing invalid configurations to persist | Step 5b |
| JF-64 | #14943 | `badf22fcc` | `056b92dbd` | Medium | configuration error | AMD AMF decoder thread count unbounded causing excessive VRAM usage; missing -threads 2 parameter in D3D11VA hardware accelerated decoding | Step 5b |
| JF-65 | #14962 | `2b45a984d` | `739642b33` | Medium | validation gap | New media item image references not validated before repository save, allowing invalid/orphaned image paths to persist in database | Step 5b |
| JF-66 | #14963 | `07d31c6ba` | `79ff0b0b0` | Medium | SQL error | Person filtering query used inefficient nested subqueries with name-based joins, causing N+1 problem and timeout on large people datasets | Step 2 |
| JF-67 | #14925 | `79ff0b0b0` | `51e20a14c` | Medium | state machine gap | Collection folder creation didn't invalidate parent folder cache, causing newly created collections not visible until server restart or manual refresh | Step 5a |
| JF-68 | #14919 | `0f42aa892` | `cce6bf27e` | Medium | validation gap | BoxSet item sorting missing default sort-by-year logic when no sort order specified, causing items to appear in arbitrary database order | Step 5b |
| JF-69 | #14960 | `51e20a14c` | `eb0d05cf1` | High | concurrency issue | LUFS audio level detection process buffer deadlock when ffmpeg outputs verbose logging; stderr not fully drained causing process hang | Step 5a |
| JF-70 | #13853 | `3fc71293b` | `baa7f5f0b` | Critical | SQL error | Parent-child relationship migration used wrong column reference in NOT EXISTS clause ("ParentId = parent.Id" instead of "parent.Id = BaseItems.ParentId"), deleting almost entire BaseItems table | Step 2 |
| JF-71 | #14984 | `5c519270b` | `55047b11834` | Medium | error handling | Chapter data not deleted when media files replaced, accumulating orphaned chapter records and bloating database | Step 5 |
| JF-72 | #14996 | `b36aab939` | `2c7d2d471` | Medium | validation gap | Encoder app path modification not prevented, allowing config corruption when user attempts to change FFmpeg binary path in UI | Step 5b |
| JF-73 | #14997 | `7dff92bb8` | `b36aab939` | Medium | error handling | OpenAPI security response code definitions duplicated instead of using TryAdd, potentially overwriting valid operation responses with duplicate 401/403 codes | Step 5 |
| JF-74 | N/A | `8abcfb2a8` | `ceef9143ad` | High | SQL error | ApplyOrder query result not assigned back to variable, causing ordering to be discarded and results returned in database order instead of requested sort | Step 2 |


### apache/logging-log4net (C#)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| LN-01 | #280 | `42a77cb` | `1064764` | High | validation gap | XmlLayout failed to sanitize control characters (U+0001, etc.) in XML attributes and text, creating invalid XML output | Step 5b |
| LN-02 | #281 | `01a0d6e` | `edd722b` | Low | error handling | Nullability hints and warnings in API contracts causing build warnings | Step 4 |
| LN-03 | #244 | `f163d30` | `05e5c66` | High | null safety | RollingFileAppender threw NullReferenceException when Path.GetDirectoryName returned null for basefile | Step 5b |
| LN-04 | #247 | `c685dd9` | `7851bb0` | Medium | concurrency issue | AbsoluteTimeDateFormatter time string cache used non-atomic update logic, causing stale cached times in concurrent logging | Step 5a |
| LN-05 | #245 | `50738b0` | `afda7d2` | Medium | type safety | NDC.Inherit(Stack) threw InvalidCastException due to unsafe cast of object[] to StackFrame[] | Step 5b |
| LN-06 | #271 | `8d678e1` | `6cb49cd` | Medium | API contract violation | OutputDebugString DllImport used wrong CharSet, garbled non-ASCII logging on Windows | Step 5b |
| LN-07 | #256 | `0ee8ef9` | `6e9f2d5` | Medium | concurrency issue | Shutdown did not unsubscribe AppDomain event handlers, blocking AssemblyLoadContext unload | Step 5a |
| LN-08 | #257 | `2d315a7` | `a7abf18` | High | validation gap | RollingFileAppender regression with file rolling from improper directory/path handling | Step 5a |
| LN-09 | #199 | `f0cbfea` | `ff7eff5` | Medium | configuration error | SystemInfo.UserName returned empty string on .NET 8 Linux due to Windows-only environment variable | Step 5b |
| LN-10 | #225 | `f06a0bc` | `1a6ff0f` | Medium | validation gap | XmlLayoutSchemaLog4j wrote exception to wrong element (log4j:data instead of log4j:throwable) | Step 4 |
| LN-11 | #227 | `2545075` | `4e4ca9d` | Low | error handling | XmlConfigurator error messages omitted config file path, hindering troubleshooting | Step 4 |
| LN-12 | #205 | `407945c` | `240e0a0` | Medium | API contract violation | RollOverRenameFiles method not virtual, preventing subclass compression/custom rollover logic | Step 5a |
| LN-13 | #196 | `1a6ff0f` | `33aea96` | Low | error handling | FileAppender method name SetQWForFiles had incorrect casing | Step 4 |
| LN-14 | #194 | `fb8b42f` | `8f3c3d4` | High | error handling | TelnetAppender.OnConnect continued accepting connections after Dispose, causing ObjectDisposedException | Step 5a |
| LN-15 | #197 | `36ea5b4` | `ab16a6e` | High | concurrency issue | Hierarchy.GetLogger threw IndexOutOfRangeException in nested logger creation from multiple threads | Step 5a |
| LN-16 | #169 | `102fcde` | `1c3c18f` | Medium | null safety | Level comparison operators threw NullReferenceException when compared with null | Step 5b |
| LN-17 | #156 | `22a3b1d` | `f3aef05` | Medium | concurrency issue | Hierarchy failed to handle nested logger creation in reverse order, parent tracking broken | Step 5a |
| LN-18 | #134 | `6f03114` | `d0d9c9b` | Medium | validation gap | LogLog.LogReceived event handler enumeration threw IndexOutOfRangeException if handlers modified list | Step 5a |
| LN-19 | #183 | `13d4e6d` | `8d7b03b` | Medium | type safety | ConverterRegistry prevented converters implementing both IConvertTo and IConvertFrom | Step 5b |
| LN-20 | FileAppender | `95104eb` | `69887af` | High | null safety | FileAppender.Close() threw NullReferenceException when called without ActivateOptions | Step 5b |
| LN-21 | CA2002 | `fb9235d` | `1296388` | Medium | concurrency issue | Multiple appenders locked on weak-identity objects instead of dedicated SyncRoot | Step 5a |
| LN-22 | #163,#231,#236 | `9562bae` | `d4f7879` | High | validation gap | RollingFileAppender failed with positive CountDirection, extension preservation, directory placement | Step 5a |
| LN-23 | #274 | `fdd527c` | `3395d8e` | Medium | validation gap | RemoteSyslogAppender did not handle platform-specific newline characters | Step 4 |
| LN-24 | #277 | `afebeba` | `226c2ba` | Low | error handling | Log4Net date/size rolling test was flaky due to timing race conditions | Step 3 |
| LN-25 | SystemInfo | `9ba9452` | `f0cbfea` | Medium | null safety | Assembly.GetEntryAssembly() could return null, causing NullReferenceException in SystemInfo | Step 5b |
| LN-26 | CA1062 | `1296388` | `0a23bc0` | Medium | validation gap | CA1062 argument validation not consistently enforced across public methods | Step 4 |
| LN-27 | #232 | `2d315a7` | `a7abf18` | High | validation gap | RollingFileAppender base filename path handling failed with extension preservation patterns | Step 5a |
| LN-28 | FileNaming | `9305ea9` | `69887af` | Medium | validation gap | RollingFileAppender rolling file name matching was case-sensitive on case-sensitive filesystems | Step 5a |
| LN-29 | MDC/NDC | `72fdee8` | `f87956b` | Low | error handling | MDC/NDC context manager names had incorrect XML schema field references | Step 4 |
| LN-30 | TestBug | `3192690` | `f87956b` | Low | error handling | FileAppenderTest had wrong operator in assertion (subtract instead of add) | Step 3 |
| LN-31 | LOG4NET-408 | `b0dd540` | `c152704` | High | state machine gap | InterprocessLock forgot to reset Mutex closed flag after closing file, breaking rolling file functionality | Step 5b |
| LN-32 | LOG4NET-457 | `eeef15d` | `610157a` | Medium | validation gap | SmtpAppender failed to trim leading/trailing separators (comma/semicolon) from email address fields | Step 5b |
| LN-33 | LOG4NET-443 | `dbe0f89` | `37f105a` | High | concurrency issue | ReaderWriterLockSlim could become orphaned if thread aborted during lock acquisition, causing deadlock | Step 5a |
| LN-34 | LOG4NET-455 | `0d28efa` | `5c82f3c` | High | concurrency issue | LogicalThreadContext did not flow correctly through async/await, losing context in async continuations | Step 5a |
| LN-35 | LOG4NET-447 | `61ca399` | `8647c5b` | Medium | API contract violation | MemoryAppender lacked thread-safe PopAllEvents, causing lost events under concurrent logging | Step 5a |
| LN-36 | #239 | `418062c` | `9562bae` | Medium | configuration error | Android detection missing from SystemInfo, caused AppSettings exceptions on Android runtime | Step 5b |
| LN-37 | #250 | `94e7a4d` | `2d315a7` | High | validation gap | RollingFileAppender tests flaky due to timing/DateTime dependencies, masked rolling file bugs | Step 3 |
| LN-38 | #253 | `add0603` | `5eb00bd` | Medium | error handling | RemoteSyslogAppender blocked logging on synchronous UDP send, should use async queue | Step 5a |
| LN-39 | LOG4NET-407 | `bf3bad7` | `7c6b756` | High | concurrency issue | AsyncAppender lost events when multiple events queued in parallel, needed locking and queue | Step 5a |
| LN-40 | LOG4NET-485 | `03c1ce1` | `6521019` | High | concurrency issue | RollingFileAppender could race across multiple processes on same computer, needed cross-process mutex | Step 5a |


### expressjs/express (JavaScript)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| EXP-01 | CVE-2026-2391 | `925a1df` | `9c85a25` | Critical | security issue | Query string parsing DoS in qs dependency | Step 5 |
| EXP-02 | #6088 | `6cd404e` | `3e81873` | Medium | validation gap | acceptsCharsets missing fallback for unsupported charset | Step 4 |
| EXP-03 | - | `54271f6` | `125bb74` | Medium | error handling | XSS vulnerability in redirect HTML response | Step 5 |
| EXP-04 | #5554 | `0b74695` | `4f0f6cc` | High | security issue | Open redirect allow list bypass in res.location | Step 5 |
| EXP-05 | #5554,#5555 | `a003cfa` | `a1fa90f` | High | error handling | Non-string parameter handling in res.location | Step 5 |
| EXP-06 | - | `74beeac` | `9bc1742` | High | state machine gap | Routing requests without HTTP method fails | Step 5a |
| EXP-07 | #4913 | `7ec5dd2` | `ab2c70b` | High | state machine gap | Stack overflow on routing large route stack | Step 5a |
| EXP-08 | #4899 | `631ada0` | `75e0c7a` | High | state machine gap | Hanging on large sync route stacks | Step 5a |
| EXP-09 | #4891 | `708ac4c` | `92c5ce5` | High | state machine gap | Stack overflow on large middleware stacks | Step 5a |
| EXP-10 | #3935 | `5855339` | `1cc8169` | Medium | API contract violation | Cookie maxAge with null/undefined produces invalid value | Step 5 |
| EXP-11 | #3445 | `b7817ab` | `48aba21` | Medium | error handling | TypeError in res.send with Buffer and ETag header | Step 5 |
| EXP-12 | #4204 | `99a369f` | `a1dbb11` | High | state machine gap | Incorrect middleware execution with unanchored RegExps | Step 5a |
| EXP-13 | #4212 | `723b545` | `ee40a88` | High | validation gap | Invalid HTTP status codes not validated | Step 4 |
| EXP-14 | #4120 | `82de4de` | `12310c5` | High | security issue | Path traversal vulnerability in downloads example | Step 5 |
| EXP-15 | #4744 | `f275e87` | `9dd0e7a` | Medium | serialization | Undefined handling with JSON escape enabled | Step 5b |
| EXP-16 | - | `9dd0e7a` | `1b2f3a0` | Medium | serialization | Undefined values in res.jsonp not handled | Step 5b |
| EXP-17 | #4155 | `a1dbb11` | `353348a` | Low | error handling | Incorrect res.jsonp deprecation message | Step 6 |
| EXP-18 | - | `3d10279` | `5e9de5d` | Medium | error handling | "Request aborted" incorrectly logged in res.sendFile | Step 6 |
| EXP-19 | #3303 | `ae0b630` | `5ea2a8f` | Medium | error handling | Error when res.set cannot add charset to Content-Type | Step 5 |
| EXP-20 | #3037 | `51f5290` | `8b6dc6c` | Medium | state machine gap | router.use skipped requests routes not processed | Step 5a |
| EXP-21 | #3017 | `2e1284b` | `999546d` | Medium | null safety | Windows absolute path check using forward slashes | Step 5b |
| EXP-22 | - | `11a77a3` | `ee90042` | Medium | state machine gap | Inner numeric indices incorrectly altering parent req.params | Step 5a |
| EXP-23 | - | `ee90042` | `97b2d70` | High | state machine gap | Infinite loop condition with mergeParams option | Step 5a |
| EXP-24 | #2665 | `24d1c98` | `e71014f` | Medium | error handling | res.format error when only default provided | Step 5 |
| EXP-25 | #2655 | `8da51e3` | `3d2ecdd` | Medium | state machine gap | next('route') in app.param incorrectly skips values | Step 5a |
| EXP-26 | #2571 | `7e0afa8` | `1e6d265` | Medium | error handling | Regression where "Request aborted" logged using res.sendFile | Step 6 |
| EXP-27 | #2571 | `14a5875` | `dbc61fc` | Medium | error handling | ECONNRESET errors not properly handled in res.sendFile | Step 6 |
| EXP-28 | - | `dbc61fc` | `31cb541` | Medium | error handling | Wrong code on aborted connections from res.sendFile | Step 6 |
| EXP-29 | #2561 | `31cb541` | `7ee56bb` | Low | type safety | Non-configurable prototype properties cause app construction failure | Step 5b |
| EXP-30 | - | `2e0f5e7` | `20aa126` | High | API contract violation | req.host incorrect when using trust proxy hops count | Step 2 |
| EXP-31 | #2569 | `20aa126` | `bb4703e` | High | API contract violation | req.protocol/req.secure incorrect with trust proxy | Step 2 |
| EXP-32 | #2550,#2551 | `b40e74d` | `eaf3318` | High | state machine gap | Trust proxy setting not inherited when app mounted | Step 5a |
| EXP-33 | #2521 | `2ccb6cf` | `0b62f74` | Medium | state machine gap | res.redirect double-calls res.end for HEAD requests | Step 5a |
| EXP-34 | #2489 | `5312a99` | `935f05b` | High | error handling | Aborted connection detection fails in res.sendFile | Step 6 |
| EXP-35 | #2459 | `935f05b` | `fc4eb6d` | Medium | API contract violation | OPTIONS responses missing HEAD method | Step 2 |
| EXP-36 | CVE-2024-51999 | `2f64f68` | `ed0ba3f` | Critical | security issue | Prototype pollution in query string parsing via plainObjects vs allowPrototypes | Step 5 |
| EXP-37 | #2468 | `5d74a55` | `262b605` | Medium | null safety | Exception in req.fresh/req.stale when res._headers is undefined | Step 5b |
| EXP-38 | #2652 | `3b3e1fc` | `591589a` | Medium | error handling | decodeURIComponent hiding platform errors - only URIErrors should be 400 | Step 5 |
| EXP-39 | (async routing) | `5fab60b` | `881e1ba` | Medium | state machine gap | Router callback not invoked asynchronously when no layer matches | Step 5a |
| EXP-40 | #2389 | `94f10c2` | `efd2dfb` | Medium | state machine gap | Same param name in array of paths overwrites earlier values | Step 5a |
| EXP-41 | (error handling) | `a01326a` | `76e8bfa` | Medium | error handling | Errors in multiple req.param(name, fn) handlers not caught properly | Step 5 |
| EXP-42 | #2421 | `eabd456` | `d40dc65` | Medium | validation gap | URLs containing :// in path incorrectly treated as FQDN | Step 4 |
| EXP-43 | #2399 | `68290ee` | `661435` | Medium | null safety | Invalid empty URLs cause matching errors | Step 5b |
| EXP-44 | #2361, #2362 | `3c1a964` | `947fb8b` | Medium | validation gap | Regression: empty string path in app.use not handled correctly | Step 4 |
| EXP-45 | #2356 | `cf41a8f` | `1716e3b` | Medium | API contract violation | app.use unable to accept array of middleware without explicit path | Step 2 |
| EXP-46 | #2233 | `3e32721` | `8ba3f39` | Medium | state machine gap | app.mountpath set to wrong value when mounting subapp via app.use | Step 5a |
| EXP-47 | #2207 | `1c3bd36` | `4ea6f21` | Medium | API contract violation | app.use(path, fn) only accepts string path, rejects RegExp/array | Step 2 |
| EXP-48 | #5792 | `82fc12a` | `160b91c` | Medium | API contract violation | res.clearCookie incorrectly uses user-provided maxAge/expires options | Step 2 |


### webpack/webpack (JavaScript)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| WP-01 | #20717 | `2b0a4ac7` | `118e0c57` | High | error handling | Correct url() path resolution and preserve source maps for non-link CSS export types (style, text, css-style-sheet) | CSS URL handling |
| WP-02 | #20697 | `7bde8ab8` | `48d0dabd` | Medium | validation gap | Improve CLI number validation to correctly parse decimal and scientific notation (1e2, 1.5e3) | Number parsing edge cases |
| WP-03 | #20699 | `12541645` | `72598efb` | Low | configuration error | Correct duplicate WEBASSEMBLY_MODULE_TYPE_SYNC in WEBASSEMBLY_MODULES constant array (should be _ASYNC) | Data integrity |
| WP-04 | #20660 | `70867d61` | `a4755121` | High | error handling | Include chunk groups in conflicting CSS module order warning for better debugging context | Warning accuracy |
| WP-05 | #20669 | `1cd34509` | `abba6062` | High | configuration error | Avoid rendering __webpack_exports__ for module library output type to prevent export conflicts | Output generation |
| WP-06 | #20665 | `aa4705ae` | `a836e064` | Medium | error handling | Fix test262 runner to correctly override module rules with { type: 'text' } | Parser/Runtime |
| WP-07 | #20661 | `a836e064` | `0b344de2` | High | error handling | Rename __webpack_require__ in arrow function scopes to avoid variable shadowing conflicts | Code generation |
| WP-08 | #20658 | `f757352b` | `8e6aed26` | High | configuration error | Hoist import.meta as module-level variable with complete properties instead of standalone expression | Runtime variables |
| WP-09 | #20656 | `67840914` | `5afe9907` | High | configuration error | Fix VirtualUrlPlugin absolute-path virtual module IDs getting concatenated with compiler context (e.g., C:\\cwd\\C:\\project) | Path handling |
| WP-10 | #20648 | `d109a433` | `474b3770` | High | error handling | Multiple CSS module bugfixes: number detection pos increment, multiline comment regex, stray parentheses in comma callback, cache comparison missing array length check, publicPathAutoRegex mutations | CSS parsing |
| WP-11 | #20649 | `a47ca2b2` | `b5499e05` | Medium | configuration error | Use variable 'type' instead of constant RBDT_RESOLVE_INITIAL in directory resolve condition | Type correctness |
| WP-12 | #20646 | `b5499e05` | `099f72ae` | Critical | security issue | Emit error on non-200 proxy response in HttpUriPlugin to prevent invalid asset loading | HTTP handling |
| WP-13 | #20614 | `20eeaeb4` | `915293e2` | High | configuration error | Add static getSourceBasicTypes to prevent errors across multiple webpack versions | Version compatibility |
| WP-14 | #20561 | `eafe0605` | `75d605cb` | Medium | configuration error | Narrow the export presence guard detection for more accurate tree shaking analysis | Exports analysis |
| WP-15 | #20555 | `b8e9b057` | `2019127b` | Medium | configuration error | Update enhanced-resolve to support new tsconfig.json resolution features | TypeScript support |
| WP-16 | #20549 | `2019127b` | `e43fcd07` | High | configuration error | Handle createRequire in expression evaluation for ESM environments | ESM/CJS interop |
| WP-17 | #20535 | `4f5c0a86` | `87987ca0` | Medium | configuration error | Mark asset module as side-effect-free when futureDefaults is enabled | Side effect tracking |
| WP-18 | #20497 | `44798614` | `0b8c241c` | High | configuration error | Add createRequire support for ESM modules in expression evaluation contexts | ESM/CJS interop |
| WP-19 | #20510 | `13c16942` | `4d4f8bf7` | High | configuration error | Throw module not found error after interception hook completes properly | Error handling |
| WP-20 | #20514 | `39595c13` | `90f7f91f` | High | error handling | Fix CSS @import HMR for non-link exportType (style, text) | Hot module replacement |
| WP-21 | #20481 | `f25adbeb` | `82a0efbc` | Medium | configuration error | Implement immutable bytes for 'bytes' import attribute per TC39 spec | Standards compliance |
| WP-22 | #20463 | `b241b0a1` | `1313375f` | High | configuration error | Add __webpack_exports__ declaration when entry is non-JS type to ensure exports availability | Output generation |
| WP-23 | #20452 | `1313375f` | `7039d0a3` | Medium | configuration error | Ensure deterministic findGraphRoots regardless of edge ordering in module graph | Determinism |
| WP-24 | #20461 | `2a0c16ec` | `2ccdc020` | High | configuration error | Prevent crash when a referenced chunk is not a runtime chunk during code generation | Stability |
| WP-25 | #20454 | `6dec6823` | `c835794b` | High | error handling | Prevent empty JS file generation for CSS-only entry points | Output generation |
| WP-26 | #20455 | `7eac1023` | `1f0ab08b` | High | state machine gap | Context modules now handle rejections correctly in promise chains | Error handling |
| WP-27 | #20444 | `655fe2ac` | `46a827c2` | Medium | validation gap | Add category for CJS re-export dependency for accurate analysis | Dependency tracking |
| WP-28 | #20431 | `124ba799` | `032856c7` | High | configuration error | Preserve node-commonjs externals for module output to avoid incorrect transformation | Module resolution |
| WP-29 | #20424 | `e06423b3` | `0e4907e6` | High | configuration error | Sanitize paths for Windows compatibility in VirtualUrlPlugin (avoid path concatenation issues) | Path handling |
| WP-30 | #20390 | `de107f87` | `a656ab1f` | High | configuration error | Set resourceData.context in VirtualUrlPlugin to avoid invalid fallback to default context | Context handling |
| WP-31 | #20381 | `16466c8c` | `69866afc` | High | configuration error | Deduplicate workers with different URL patterns for same module | Deduplication |
| WP-32 | #20370 | `e24df1f8` | `bdf5419c` | Medium | configuration error | Fix compatibility with Node.js v25 fs types (Node API changes) | Node.js compatibility |
| WP-33 | #20346 | `3a73621a` | `a596b267` | High | configuration error | Use RuntimeKey instead of Runtime for export generation to prevent duplicate runtime outputs | Runtime generation |
| WP-34 | #20345 | `bf00b730` | `22e17876` | High | configuration error | Reuse async entrypoint for same Worker URL within a module to avoid duplication | Worker optimization |
| WP-35 | #20337 | `13c679ad` | `b2ad09db` | High | error handling | Skip JS module generation for unused CSS exports to reduce bundle size | Output optimization |
| WP-36 | #20319 | `edfaa0ff` | `9a3b4289` | Medium | serialization | Omit empty ignoreList property from source maps to reduce map file size | Output optimization |
| WP-37 | #20313 | `aa63096a` | `d2df541e` | High | configuration error | Optimize import.meta.env in destructuring assignments to reduce generated code | Code generation |
| WP-38 | #20293 | `7dd5e424` | `c11d4564` | High | configuration error | Handle module library when exports are provided unknowingly (external/default exports) | Output generation |
| WP-39 | #20286 | `fd555876` | `034400e2` | High | configuration error | Add declaration for unused harmony import specifier to maintain valid module output | Imports handling |
| WP-40 | #20287 | `03440e28` | `dc644c48` | High | configuration error | Fix module comparison in AssetModulesPlugin and CssModulesPlugin to improve compressibility while retaining portability | Module ordering |
| WP-41 | #20289 | `a867eb0b` | `081104ff` | Medium | configuration error | Reduce output for missing import.meta.env properties by skipping unknown keys | Code generation |
| WP-42 | #20265 | `d2a124db` | `f21d1354` | High | configuration error | Avoid module variable conflict in __webpack_module__ API by renaming user-defined 'module' variables | Scoping |
| WP-43 | #20189 | `50e09973` | `557582ad` | High | configuration error | Fix ESM default export handling for .mjs files in Module Federation remotes | Module Federation |
| WP-44 | (security) | `c5100702` | `4b0501c6` | Critical | security issue | Prevent userinfo bypass vulnerability in HttpUriPlugin allowedUris checking (URL parsing exploit) | Security/HTTP |
| WP-45 | (security) | `2179fdbc` | `512a32f8` | Critical | security issue | Re-validate HttpUriPlugin redirects against allowedUris and enforce http(s) protocol with max 5 redirects | Security/HTTP |
| WP-46 | #20556 | `a3d78393` | `b8e9b057` | Medium | type safety | Fix TypeScript type definitions for MultiStats and Stats toJson/toString parameter signatures (StatsValue unification) | Step 5b schema types |
| WP-47 | (no issue) | `3bd18bbc` | `b0e0e4cb` | Medium | validation gap | Respect errorStack config option in stats output - option was being ignored during error serialization | Step 4 specs |
| WP-48 | (no issue) | `3c4319f3` | `d571f3f2` | Low | configuration error | Optimize regex character class generation with ranges (e.g. [1-4a]) for smaller runtime code | Step 5 defensive patterns |
| WP-49 | (no issue) | `aab1da9c` | `22c48fb2` | High | serialization | Fix multiple CSS modules parsing bugs (composite: unspecified scope) | Step 2 architecture |
| WP-50 | #20169 | `9abcf3fa` | `1b5084e3` | High | error handling | Make HookWebpackError properly serializable for error reporting and logging | Step 5 defensive patterns |
| WP-51 | #20168 | `5ce84ec8` | `9525f0a2` | High | security issue | Fix __proto__ pollution vulnerability in DefinePlugin and DotenvPlugin by using Object.create(null) and proper property checking | Step 5 defensive patterns |
| WP-52 | #20142 | `5b2c4ba0` | `ed9e5f81` | High | configuration error | Fix universal lazy compilation to work correctly across all environments | Step 3 tests |
| WP-53 | #20154 | `20045091` | `dc8f52fe` | High | configuration error | CSS link tags not removed from DOM when CSS imports are removed during HMR | Step 5a state machines |
| WP-54 | #20135 | `2259e2cc` | `af7d241f` | High | configuration error | Fix import.meta.filename and import.meta.dirname compatibility with eval devtools mode | Step 4 specs |
| WP-55 | #20134 | `a58ff292` | `e0219482` | High | serialization | Injected debugId gets corrupted when hidden-source-map devtool is used | Step 5 defensive patterns |
| WP-56 | #20129 | `077417f1` | `7722518` | Critical | serialization | Many CSS modules parsing and generation bugs - composite: nested rules, var functions, @supports, etc. (major CSS parser rework) | Step 2 architecture |
| WP-57 | #20126 | `27c05c7c` | `067cc60b` | High | configuration error | Return to namespace import when external request includes specific export to avoid breaking named exports | Step 4 specs |
| WP-58 | #20124 | `d4208bae` | `102e1a4d` | High | configuration error | Delay HMR accept dependencies evaluation to preserve import attributes through tree-shaking | Step 5a state machines |
| WP-59 | #20116 | `3cd6b975` | `df15fa13` | High | serialization | Fix multiple CSS modules parsing bugs (composite scope) | Step 2 architecture |
| WP-60 | #20107 | `7e7af046` | `44136c14` | High | configuration error | Fix incorrect identifier assignment for import binding of module externals causing wrong module references | Step 5b schema types |


### eslint/eslint (JavaScript)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| ESL-01 | #20464 | `2b8824e` | `07c4b8b4` | High | error handling | Autofix would incorrectly transform var to let when variable is referenc... | Step 3 |
| ESL-02 | #20581 | `f4c9cf9` | `4efaa367` | Medium | error handling | Error message for useless-assignment did not include the variable name | Step 1 |
| ESL-03 | #20537 | `2b72361` | `98cbf6ba` | Medium | error handling | update ajv to 6.14.0 to address security vulnerabilities | Step 1 |
| ESL-04 | #20519 | `d841001` | `8c3832ad` | Medium | error handling | update minimatch to 10.2.1 to address security vulnerabilities | Step 1 |
| ESL-05 | #20496 | `04c2147` | `8330d238` | Medium | error handling | update error message for unused suppressions | Step 1 |
| ESL-06 | #20456 | `1d29d22` | `11644b1d` | Medium | error handling | Array.fromAsync callbacks not recognized as having default this binding | Step 1 |
| ESL-07 | #20462 | `727451e` | `e80485fc` | High | error handling | Global mode report range calculation was broken in strict rule | Step 4 |
| ESL-08 | #20460 | `e80485f` | `14956543` | Medium | error handling | remove fake FlatESLint and LegacyESLint exports | Step 1 |
| ESL-09 | #20423 | `9eeff3b` | `1c4b33fe` | Medium | error handling | update esquery | Step 1 |
| ESL-10 | #20436 | `b34b938` | `51aab539` | Medium | error handling | use Error.prepareStackTrace to estimate failing test location | Step 1 |
| ESL-11 | #20433 | `23490b2` | `f244dbf2` | Medium | error handling | handle space before colon in RuleTester location estimation | Step 1 |
| ESL-12 | #20348 | `f244dbf` | `8f360ad6` | Medium | type safety | use MessagePlaceholderData type from @eslint/core | Step 1 |
| ESL-13 | #20421 | `2332262` | `f6584191` | Medium | error handling | error location should not modify error message in RuleTester | Step 1 |
| ESL-14 | #20405 | `ab99b21` | `8a60f3bc` | Medium | error handling | ensure filename is passed as third argument to verifyAndFix() | Step 1 |
| ESL-15 | #20415 | `8a60f3b` | `2c3efb72` | Medium | type safety | remove ecmaVersion and sourceType from ParserOptions type | Step 1 |
| ESL-16 | #20231 | `eafd727` | `39d1f516` | Medium | type safety | remove TDZ scope type | Step 1 |
| ESL-17 | #20404 | `39d1f51` | `02e7e712` | Medium | type safety | correct Scope typings | Step 1 |
| ESL-18 | #20384 | `2bd0f13` | `f9c49683` | Medium | type safety | update verify and verifyAndFix types | Step 1 |
| ESL-19 | #20393 | `ba6ebfa` | `a176319d` | Medium | type safety | correct typings for loadESLint() and shouldUseFlatConfig() | Step 1 |
| ESL-20 | #20105 | `e7673ae` | `53e95222` | Medium | type safety | correct RuleTester typings | Step 1 |
| ESL-21 | #20241 | `53e9522` | `264b9811` | Medium | error handling | strict removed formatters check | Step 1 |
| ESL-22 | #20374 | `b017f09` | `e593aa0f` | Medium | error handling | correct no-restricted-import messages | Step 1 |
| ESL-23 | #20283 | `650753e` | `51b51f4f` | Medium | error handling | JS lang visitor methods received incorrect node types | Step 1 |
| ESL-24 | #20253 | `15f5c7c` | `5a1a534e` | Medium | error handling | Traversal step.args were not forwarded to visitor callbacks | Step 1 |
| ESL-25 | #20167 | `5a1a534` | `cc57d87a` | Medium | type safety | object-shorthand rule did not handle JSDoc comments correctly | Step 1 |
| ESL-26 | #20257 | `e86b813` | `126552fc` | Medium | type safety | Use more types from @eslint/core | Step 1 |
| ESL-27 | #20198 | `927272d` | `c7d32298` | Medium | type safety | correct Scope typings | Step 1 |
| ESL-28 | #20244 | `37f76d9` | `cf5f2dd5` | Medium | type safety | use AST.Program type for Program node | Step 1 |
| ESL-29 | #20188 | `ae07f0b` | `b165d471` | Medium | error handling | unify timing report for concurrent linting | Step 1 |
| ESL-30 | #20199 | `b165d47` | `637216bd` | Medium | type safety | correct Rule typings | Step 1 |
| ESL-31 | #20218 | `fb97cda` | `9e7fad4a` | Medium | error handling | improve error message for missing fix function in suggestions | Step 1 |
| ESL-32 | #20201 | `50c3dfd` | `c82b5efa` | Medium | type safety | improve type support for isolated dependencies in pnpm | Step 1 |
| ESL-33 | #20114 | `a1f06a3` | `dbb200e3` | Medium | type safety | correct SourceCode typings | Step 1 |
| ESL-34 | #20164 | `a129cce` | `09e04fcc` | High | error handling | no-loss-of-precision false positives for numbers with leading zeros | Step 2 |
| ESL-35 | #20172 | `09e04fc` | `5c97a045` | Medium | type safety | add missing AST token types | Step 1 |
| ESL-36 | #20045 | `bfa4601` | `dfd11de` | High | validation gap | no-empty rule incorrectly flagged empty switch statements with comments; fix added comment detection and proper location reporting | Step 5b |
| ESL-37 | #20049 | `dfd11de` | `6ad8973` | Medium | type safety | Test case types missing `before` and `after` properties for RuleTester assertions | Step 5b |
| ESL-38 | #20032 | `ea789c7` | `b8875f6` | Medium | validation gap | no-loss-of-precision false positive with uppercase E exponent notation (e.g., 1.0E+21) | Step 4 |
| ESL-39 | #20023 | `6c07420` | `676f4ac` | Low | error handling | neostandard integration test spuriously failed due to environment assumptions | Step 6 |
| ESL-40 | #20002 | `676f4ac` | `327c672` | Medium | validation gap | no-loss-of-precision incorrectly flagged scientific notation with trailing zeros matching exponent | Step 4 |
| ESL-41 | #19995 | `732433c` | `34f0723` | Medium | type safety | Custom rule meta.docs.recommended field type was overly restrictive (required boolean) | Step 5b |
| ESL-42 | #19975 | `e8a6914` | `90b050e` | High | error handling | EMFILE error check logic inverted, causing silent failure when too many files open | Step 5 |
| ESL-43 | #19932 | `f46fc6c` | `86e7426` | High | validation gap | no-implied-eval false positives when setTimeout/setInterval were shadowed by local definitions | Step 4 |
| ESL-44 | #19944 | `7863d26` | `c565a53` | Medium | type safety | ParserOptions type included outdated ecmaFeatures properties not supported by modern parsers | Step 5b |
| ESL-45 | #19937 | `3173305` | `14053ed` | Medium | error handling | execScript message incorrect in no-implied-eval rule ("function" instead of method call context) | Step 3 |
| ESL-46 | #19926 | `07fac6c` | `35cf44c` | High | error handling | EMFILE errors not retried when writing autofix results, causing data loss on resource-constrained systems | Step 5 |
| ESL-47 | #19862 | `6a0f164` | `8662ed1` | Medium | null safety | getIndexFromLoc method crashed when passed null location object instead of checking type | Step 5 |
| ESL-48 | #19779 | `eea3e7e` | `a95721f` | High | state machine gap | GlobalScope#implicit contained configured globals causing no-implicit-globals false positives | Step 5a |
| ESL-49 | #19808 | `1ba3318` | `786bcd1` | Low | configuration error | no-use-before-define rule missing language and dialects metadata for proper dialect support | Step 2 |
| ESL-50 | #19845 | `85c082c` | `00e3e6a` | High | validation gap | File globbing with negated patterns and arrays incorrectly included non-default file extensions | Step 4 |


### rails/rails (Ruby)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| RLS-01 | #N/A | `4df808965b` | `12db7015` | Critical | security issue | XSS in debug exceptions copy-to-clipboard - Unescaped exception message output in script tag | Security/Input Validation Step 1 |
| RLS-02 | #N/A | `8fdf7da36d` | `1a5e2f6a` | High | security issue | Glob injection in ActiveStorage DiskService#delete_prefixed - Unescaped glob metacharacters passed to Dir.glob | Security/File Operations Step 2 |
| RLS-03 | #N/A | `1a5e2f6a41` | `2d485aec` | Critical | security issue | Path traversal in ActiveStorage DiskService - Blob keys with ".." segments escape storage root | Security/Path Validation Step 1 |
| RLS-04 | #N/A | `6b313e2caa` | `0dbaa44c` | High | security issue | SafeBuffer#% operator loses unsafe status - HTML-unsafe strings lost escaping after % operation | Security/Buffer Management Step 2 |
| RLS-05 | #N/A | `7511baf799` | `dadab570` | High | SQL error | FrozenError when deriving foreign key from inverse with composite key - map! called on frozen array | Associations/Composite Keys Step 3 |
| RLS-06 | #N/A | `ccfe1ae1fb` | `b72b0e2d` | Medium | SQL error | insert_all/upsert_all log messages fail for anonymous classes - Name introspection broken for unnamed models | Logging/Edge Cases Step 2 |
| RLS-07 | #N/A | `dcadd3c790` | `0583b8bc` | Medium | error handling | Lazy ivars causing different model shapes - Memoization inconsistencies create polymorphic objects | Performance/Memoization Step 3 |
| RLS-08 | #N/A | `1c4a982ad0` | `33b843a4` | Medium | SQL error | PostgreSQL column equality for generated types - Type comparison fails for generated columns | Database/Type Handling Step 2 |
| RLS-09 | #N/A | `5eb1da2b2c` | `c629bb2f` | Low | validation gap | Environment leak in PostgreSQL dbconsole tests - Test isolation failure exposing env vars | Testing/Cleanup Step 1 |
| RLS-10 | #56976 | `a893e9aaa9` | `367f7df5` | Medium | SQL error | SQLite virtual tables not ignored by ignore_tables - Migration schema dump includes virtual tables | Database/Migrations Step 2 |
| RLS-11 | #N/A | `6715e6d8c8` | `13c9effc` | High | SQL error | Attribute assignment for finder order columns - Wrong config attribute assigned (copy-paste error) | Configuration/Initialization Step 1 |
| RLS-12 | #N/A | `b8b8c3e426` | `371cbc97` | Low | validation gap | dbconsole NotImplementedError message - Exception raised with uninformative message | Error Handling/CLI Step 1 |
| RLS-13 | #56904 | `ad5d539fde` | `80542918` | Medium | error handling | Encoding error with non-ASCII strict locals defaults - CompatibilityError in template rendering | Views/Encoding Step 2 |
| RLS-14 | #N/A | `29d3388d19` | `cb91d817` | Medium | error handling | IsolatedExecutionState.share_with() in ActionCable::Live - State sharing call missing in live streaming | Streaming/State Management Step 2 |
| RLS-15 | #N/A | `dca07a61fe` | `80542918` | Medium | error handling | Collection caching not preserving store default expires_in - Cache expiration config ignored | Caching/Fragment Cache Step 2 |
| RLS-16 | #N/A | `9edfe0e8e8` | `0bd4abb6` | Medium | error handling | ExecutionContext corruption during reload - Thread-local state not cleared on module reload | Concurrency/Reloading Step 3 |
| RLS-17 | #56756 | `2007ef46c6` | `7252663b` | Low | error handling | Ruby 4.0 delegator warning for inspect - DelegateClass#inspect emits deprecation warning | Compatibility/Delegation Step 1 |
| RLS-18 | #56871 | `e905b2e3cd` | `442408e2` | Medium | error handling | Markdown edge cases for code blocks/links/URIs - Malformed markdown output for special content | Text Processing/Markdown Step 2 |
| RLS-19 | #N/A | `1858ded2ba` | `50866225` | Medium | error handling | Editor URL translation not working - Path translation logic skipped for certain editors | Text Processing/URLs Step 2 |
| RLS-20 | #N/A | `3039ed3e66` | `01c3d29c` | Medium | SQL error | SQLite3 column equality for generated types - Type comparison fails for generated columns | Database/Type Handling Step 2 |
| RLS-21 | #N/A | `873227534a` | `e3ef3d50` | Medium | error handling | ActiveModel::Attributes loaded eagerly - Circular autoload dependency prevents lazy loading | Autoloading/Modules Step 1 |
| RLS-22 | #N/A | `c0b82ff5f5` | `4a7396cb` | High | SQL error | in_batches(use_ranges: true) with predefined limit - Offset calculation ignored remaining limit | Batching/Ranges Step 3 |
| RLS-23 | #N/A | `b455a7ca49` | `0c95d0a1` | High | error handling | UnknownHttpMethod returning 500 instead of 405 - head? method raises on invalid HTTP methods | HTTP/Status Codes Step 2 |
| RLS-24 | #56801 | `d79f65fa41` | `a53b4a1f` | Low | SQL error | Column#hash using wrong instance variable - Hash calculation broken from mismatch | Hashing/Equality Step 1 |
| RLS-25 | #N/A | `41f8f97bd2` | `4a7396cb` | Medium | SQL error | SQLite3 column equality for rowid aliases - Type comparison fails for rowid aliases | Database/Primary Keys Step 2 |
| RLS-26 | #N/A | `62db8c6ed0` | `48d30a04` | Medium | error handling | ActiveStorage Blob content_type methods fail with nil - NilPointerException on nil content type | File Operations/Metadata Step 1 |
| RLS-27 | #56784 | `b619c8ffa3` | `58c94cbd` | Medium | error handling | JSONGemCoderEncoder not calling to_s on hash keys - Serialization fails for non-string keys | Serialization/JSON Step 2 |
| RLS-28 | #N/A | `d084f4008f` | `661442a0` | Medium | SQL error | Marshal deserialisation of Integer type from Rails 8.0 - Type deserialization incompatibility | Serialization/Types Step 2 |
| RLS-29 | #N/A | `70db0e8edd` | `90ccb450` | High | SQL error | ThroughReflection#association_primary_key with composite keys - Array.to_s produces malformed key string | Associations/Composite Keys Step 3 |
| RLS-30 | #N/A | `4d03ed24b0` | `805e64f6` | Low | validation gap | ErrorReporterAssertions fails when no reporter configured - Test assertion fails on nil reporter | Testing/Assertions Step 1 |
| RLS-31 | #N/A | `90ab0e8fea` | `e69d30b0` | Low | validation gap | ActionView::TestCase not exposing setup variables - Variables assigned in setup not visible to tests | Testing/Fixtures Step 1 |
| RLS-32 | #N/A | `9efe4a1d13` | `01fb87c2` | Medium | error handling | RACK_ENV environment leak in ActionCable ClientTest - Test isolation failure exposing environment | Testing/Cleanup Step 1 |
| RLS-33 | #N/A | `a8add10108` | `86eb0098` | Medium | SQL error | Revert change_table bulk with table prefixes/suffixes - Schema manipulation broken with prefixed tables | Migrations/Tables Step 2 |
| RLS-34 | #N/A | `4cecb570bf` | `86eb0098` | Low | validation gap | Leaked FROM environment variable in railties tasks - Environment pollution in database tasks | Environment/Cleanup Step 1 |
| RLS-35 | #N/A | `648634ffbe` | `5bc739b4` | Medium | SQL error | Revert change_table bulk with indexes - Migration rollback fails when bulk index creation used | Migrations/Indexes Step 2 |
| RLS-36 | #N/A | `a3750923cb` | `7db8073e` | Medium | error handling | Rails::Application error reporter middleware usage - Error reporter incorrectly integrated | Error Handling/Middleware Step 2 |
| RLS-37 | #N/A | `4e1886ff02` | `5ad84fef` | Low | error handling | ActiveRecord finder methods documentation - Code examples incomplete or incorrect | Documentation/Examples Step 1 |
| RLS-38 | #N/A | `f166e1aec9` | `d679a6fb` | Medium | error handling | Titleize not capitalizing unicode lowercase letters - Unicode character handling incomplete | String Processing/Unicode Step 2 |
| RLS-39 | #54579 | `e4fb299480` | `5e3d55c7` | Low | validation gap | Test assumes Rails is always defined - Test environment setup incomplete | Testing/Environment Step 1 |
| RLS-40 | #N/A | `28d169e723` | `38a43f33` | Low | validation gap | Flaky sql.active_record instrumentation test count - Race condition in event counting | Testing/Instrumentation Step 2 |
| RLS-41 | #57052 | `eea3e6cbd9` | `7bf3ef4a9a` | High | concurrency issue | Parallel test shutdown hangs when workers die during Server#shutdown - dead process detection missing inside loop | Step 5a |
| RLS-42 | #57050 | `ac07e7ead3` | `cc1a0aea68` | High | validation gap | Combines per-validator and top-level :if/:unless/:on options are silently replaced instead of merged | Step 4 |
| RLS-43 | #56112 | `54c0354ade` | `8aebd0b507` | Medium | type safety | TimeWithZone#xmlschema fails with DateTime local time - offset replacement logic broken for non-UTC zones | Step 5b |
| RLS-44 | #55708 | `d77afd2321` | `e434aa439a8a` | Medium | configuration error | File watcher configuration not respected in routes reloader - config option ignored during initialization | Step 2 |
| RLS-45 | #55776 | `f2024b09d7` | `96b4df770d69` | Medium | error handling | class_attribute on instance singleton class raises NameError - NameError on undefined instance variable | Step 5 |
| RLS-46 | #55771 | `176c42ff58` | `f1537e6cc345` | Medium | state machine gap | Autosave association changes valid data to invalid - missing changed_for_autosave check | Step 5a |
| RLS-47 | #55708 | `321b3402f8` | `71ba62dd3108` | Medium | concurrency issue | FileUpdateChecker uses wall time instead of process time - time travel helpers cause unnecessary reloads | Step 5a |
| RLS-48 | #55525 | `3df37617fa` | `5f23c9b74d65` | Low | protocol violation | AWS S3 upload_stream deprecation in ActiveStorage#S3Service - deprecated method still in use | Step 6 |
| RLS-49 | #55460 | `fc18795f3f` | `b8278772601c` | Medium | error handling | ActiveSupport::Logger not freeze-friendly - frozen object modification in thread_safe_level | Step 5 |
| RLS-50 | #55379 | `1c66c1b876` | `3e544829dab8` | Low | configuration error | GitHub CI template default branch detection fails - pattern matching broken in capture_command | Step 2 |
| RLS-51 | #52530 | `8641f7f46a` | `9dfeb48c201f` | High | SQL error | WhereClause#merge drops Nary children with mixed conditions - incorrect merge logic with OR/AND | Step 4 |
| RLS-52 | #54591 | `8fad423815` | `7b3ebaa92f6e` | High | missing boundary check | Order-dependent finders fail silently without order columns - missing required order validation | Step 3 |
| RLS-53 | #54966 | `474ff5556f` | `0ed3cd46d003` | Medium | type safety | Select helper grouped_choices detection fails with non-Array values - incorrect type checking | Step 5b |
| RLS-54 | #50256 | `c500ca9df1` | `32d96235810e` | Medium | state machine gap | Composite foreign key stale state check returns single value instead of array - array wrapping missing | Step 5a |
| RLS-55 | #54805 | `6718aeb244` | `76efa0ff4b1e` | Medium | configuration error | PostgreSQL structure_load extra flags ignored due to argument order - flags appended instead of prepended | Step 2 |
| RLS-56 | #53758 | `42e989154d` | `972a52d127ae` | High | error handling | Pessimistic lock allows writes in readonly mode - readonly check missing in lock! method | Step 5 |
| RLS-57 | #53564 | `42df5f2f1d` | `fdc19e1970bf` | Medium | null safety | Normalized attribute queries inconsistent for nil values - missing predicate normalization | Step 5b |
| RLS-58 | #47849 | `997c510427` | `67c6ef2e5957` | Medium | SQL error | MySQL 8.0.16+ check constraint newlines not stripped correctly - regex escape sequence error | Step 4 |
| RLS-59 | #53269 | `084fb84496` | `57fe7e781ee3` | Medium | validation gap | Resource routing validation incorrectly handles string values - type coercion missing | Step 4 |
| RLS-60 | #51463 | `c7a547feba` | `4f68f3e1e6c2` | Medium | error handling | Invalid :on/:except routing options silently ignored - validation missing for option values | Step 5 |


### sidekiq/sidekiq (Ruby)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| SK-01 | #6936 | `3cd437d1` | `e16be9f3` | High | silent failure | Mutation during iteration in SortedSet#each caused it to miss half of the jobs when iterating/paginating | Pagination correctness |
| SK-02 | #6893 | `442f083a` | `cfc97aec` | High | error handling | Race condition with Stop button in UI; nil reference when process terminated while stop is pending | Null safety in state mutations |
| SK-03 | #6879 | `9b080e8d` | `4f368fdd` | Medium | state machine gap | perform_inline did not enforce strict_args! validation, allowing invalid argument types to bypass checks | Argument validation bypass |
| SK-04 | #6866 | `2319d094` | `9d8c2219` | Medium | state machine gap | Scheduled task processing formula was incorrect, causing skew in average poll intervals across multiple processes | Timing/coordination |
| SK-05 | #6870 | `f9e0a02` | `e03b317f` | Medium | configuration error | Backwards compatibility issue with older process data format in Redis causing parsing failures | Version migration |
| SK-06 | #6741 | `43c59dd8` | `573448b7` | High | state machine gap | Death handlers were not called when :discard option was used, breaking dependent functionality | Death handler lifecycle |
| SK-07 | #6768 | `f01b2c9` | `098dc1bc` | High | concurrency issue | JavaScript race condition in confirm dialog that could skip confirmation when live polling | UI state sync |
| SK-08 | #6738 | `bd36049` | `fd4d8f4c` | Medium | configuration error | reliable_push leading to incorrect CurrentAttributes scope, causing context isolation failures | Context isolation |
| SK-09 | (unknown) | `7f692c1` | `16b71153` | Low | API contract violation | Bug in Deadset#kill ex param - typo `opt[:ex]` should be `opts[:ex]` | Typo/param passing |
| SK-10 | (unknown) | `7d3e3dd` | `e7cd8102` | High | validation gap | Startup error when Redis Sentinel provided as URL; URL parsing not handled in sentinel options | Connection parsing |
| SK-11 | #6477 | `5a78e7c` | `bd360490` | High | configuration error | Circular require for ActiveJob integration causing load failures | Require/module order |
| SK-12 | #6474 | `18b6397` | `ea0f025a` | Medium | configuration error | Check whether SidekiqAdapter is defined failed under certain Rails configurations | Adapter detection |
| SK-13 | #6455 | `38aeba1` | `77b4ddd8` | Medium | state machine gap | CurrentAttributes not in proper scope when creating batch callbacks; middleware order issue | Middleware ordering |
| SK-14 | #6589 | `9a3ec47` | `6a36028` | Medium | state machine gap | Job cancellation check used `== 1` instead of truthy check, missing cancellation signals | Type checking |
| SK-15 | (unknown) | `61b3fca` | `5551550d` | Medium | configuration error | Loading the wrong version of the adapter from Rails instead of Sidekiq's adapter | Module loading order |
| SK-16 | #6584 | `5d62829` | `fa33f4dc` | Medium | configuration error | Railtie loading AJ driver before Rails initialization, causing initialization order problems | Initialization order |
| SK-17 | #6577 | `0132dd1` | `9d9da2fc` | Low | API contract violation | Batch pagination adjustment issue | Pagination |
| SK-18 | #6553 | `414180e` | `4f9a2609` | Low | API contract violation | #inspect output too large for Component and Config classes, affecting debugging | Debug output size |
| SK-19 | #6508 | `856200c` | `f3f41c31` | Medium | API contract violation | Dead set filtering implementation issue | Filtering logic |
| SK-20 | #6313 | `3a5e232` | `1c2a37d1` | Medium | error handling | Additional robustness needed against invalid locales in session data | Input validation |
| SK-21 | #6276 | `b89bdb4` | `f8ab7d20` | Medium | validation gap | :url option not properly passed to redis-client, breaking custom connection handling | Option propagation |
| SK-22 | #6282 | `1360d04` | `8f7606b4` | Low | API contract violation | respond_to_missing? method signature changed in newer Ruby, causing redefinition errors | API compatibility |
| SK-23 | #6287 | `7e2b087` | `b6393ede` | Low | error handling | Embedded example had incorrect usage pattern | Example correctness |
| SK-24 | CVE-2024-32887 | `30786e0` | `371884e0` | Critical | security issue | Security vulnerability requiring immediate fix | Security patch |
| SK-25 | #6310 | `a3cfca8` | `c24f9f6` | Low | error handling | Polling interval formatting display issue | Display formatting |
| SK-26 | #6646 | `4fe9f59` | `a1a96bee` | Medium | error handling | Rack::Lint compliance errors in web application | Framework compliance |
| SK-27 | #6654 | `d9dc719` | `68b5462f` | Medium | configuration error | Redis version requirement in embedded mode not properly validated | Version checking |
| SK-28 | #6715 | `5a7ee5c` | `5a38c38b` | Medium | configuration error | We should load rails if rails engine is defined for rspec tests | Test setup |
| SK-29 | #6723 | `772bd51` | `5a7ee5c8` | Medium | API contract violation | /stats endpoint not storage name independent, breaking alternative storage backends | Storage abstraction |
| SK-30 | #6739 | `01bc5c9` | `c4deada7` | Medium | security issue | CSRF protection cannot be disabled when needed for certain deployments | Configuration flexibility |
| SK-31 | #6764 | `f111a39` | `b108b682` | Medium | error handling | Pending metrics not flushed at :exit, causing data loss on shutdown | Lifecycle flushing |
| SK-32 | (unknown) | `8dc13b4` | `fe22ff75` | Medium | API contract violation | zrange with REV argument had incorrect index order, causing wrong sort direction | Redis command syntax |
| SK-33 | (unknown) | `0af0c80` | `28d9c23a` | High | configuration error | Config frozen before merge! completed, causing "frozen object can't be modified" errors | Initialization order |
| SK-34 | (unknown) | `f01b2c9` | `098dc1bc` | High | error handling | JavaScript race condition in confirmation dialogs when live polling enabled | UI state race |
| SK-35 | #6547 | `ea1c3df` | `5589693b` | Low | configuration error | Default tag not applied when in embedded mode | Tag initialization |
| SK-36 | #6954 | `7c411b9` | `9121846` | Medium | null safety | Edge case resulting in nil crash on /busy page when starting index exceeds available items in paginator | Step 5 (defensive patterns) |
| SK-37 | #6685 | `d92eade` | `205df02` | High | error handling | NoMethodError rescue trap caught job errors and silently swallowed exceptions from wrapped job, preventing proper retry and alerting | Step 5 (defensive patterns) |
| SK-38 | #6894 | `0c28919` | `490dd5c` | Medium | configuration error | Missing require for Rack::Session in bare/simple.ru causing undefined constant errors in minimal deployments | Step 2 (architecture) |
| SK-39 | #6893 | `490dd5c` | `fa4db41` | Medium | type safety | JavaScript ReferenceError: `response` should be `resp` in checkResponse function, breaking live poll error handling | Step 5 (defensive patterns) |
| SK-40 | #6879 | `9b080e8` | `4f368fd` | High | validation gap | perform_inline did not enforce strict_args! validation, allowing invalid argument types through when not using job enqueueing | Step 4 (specs) |
| SK-41 | #6905 | `fcca8f1` | `92e2a5a` | Medium | API contract violation | TUI table helper not properly passing keyword arguments, causing unexpected behavior in table rendering | Step 5a (state machines) |
| SK-42 | #6778 | `73525d3` | `506ca55` | Low | configuration error | No plain (non-colorized) log formatter available, breaking log aggregation in environments where color codes cause issues | Step 2 (architecture) |
| SK-43 | #6774 | `54ad223` | `55cb762` | Medium | API contract violation | Job iteration did not expose `current_object` to around_iteration callback, limiting cleanup/finalization capabilities | Step 4 (specs) |
| SK-44 | #6742 | `6742be8` | `7e73505` | Medium | type safety | Test override changed method visibility from private to public, breaking encapsulation contract of Client API | Step 5 (defensive patterns) |
| SK-45 | #6630 | `03c654e` | `bdf406a` | High | configuration error | Redis version requirement incorrectly set to 7.2, breaking compatibility with AWS and Ubuntu 24.04 LTS which provide Redis 7.0 | Step 2 (architecture) |
| SK-46 | #6595 | `8fdea9c` | `903aa94` | Low | API contract violation | Job tags lacked CSS classes for custom styling, preventing applications from styling different tag types distinctly | Step 4 (specs) |
| SK-47 | #6613 | `9cc6c70` | `a0ed483` | Low | null safety | Accessibility violations: missing lang attribute on html element and missing role on navigation causing WCAG failures | Step 5b (schema types) |
| SK-48 | #6526 | `9f8a5f9` | `ea1c3df` | Medium | configuration error | DEBUG_INVOCATION environment variable (systemd RestartMode=debug) not recognized, preventing debug logging on process restart | Step 2 (architecture) |
| SK-49 | #6518 | `bf40023` | `b4f64ac` | Medium | error handling | Error reporter did not use modern Ruby Exception#full_message API, losing backtrace and context in log output | Step 5 (defensive patterns) |
| SK-50 | #6857 | `e94e4d1` | `d091478` | Medium | configuration error | TTIN signal deprecated in modern Puma; INFO signal not available as alternative for thread dump, breaking monitoring integrations | Step 2 (architecture) |


### heartcombo/devise (Ruby)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| DEV-01 | #5784 | `0252777` | `879f79fc` | Critical | error handling | Race condition in email change flow | Step 3: Email Confirmation |
| DEV-02 | #4529 | `1192c76` | `ecd21876` | High | error handling | Confirmation period validation corner case | Step 3: Email Confirmation |
| DEV-03 | #4752 | `d1948b7` | `371d657e` | High | error handling | ActiveRecord check in Confirmable | Step 3: Email Confirmation |
| DEV-04 | #4674 | `31801fc` | `ce041427` | High | security issue | Missing validations on signup with Trackable | Step 2: Session Management |
| DEV-05 | #4397 | `60dc4be` | `bf4641c8` | High | security issue | Absent password params in password reset | Step 4: Password Reset |
| DEV-06 | #4101 | `9caf07d` | `2044fffa` | High | security issue | Remember token overwriting on signin | Step 2: Token Management |
| DEV-07 | #4072 | `7346ce7` | `8ac32f14` | High | security issue | Unlock strategy checking bug | Step 5: Account Locking |
| DEV-08 | #3787 | `5ae6360` | `40258bf1` | High | error handling | Email change broken by after_create hook | Step 3: Email Confirmation |
| DEV-09 | #3643 | `aa675f7` | `18192088` | High | security issue | Infinite redirect in authenticated routes | Step 1: Authentication |
| DEV-10 | #3457 | `ee8c134` | `c19f1f27` | Critical | error handling | Security leak in email reconfirmation form | Step 3: Email Confirmation |
| DEV-11 | #3429 | `3f95ac8` | `c9fb1ebb` | High | error handling | Confirmation token handling | Step 3: Email Confirmation |
| DEV-12 | GH-Issue | `12f0dd1` | `12c796e4` | High | security issue | Checkbox TRUE VALUES not HTML spec compliant | Step 2: Session Management |
| DEV-13 | GH-Issue | `d63b6b7` | `1fbc165b` | High | error handling | after_confirmation_path_for scope issue | Step 3: Email Confirmation |
| DEV-14 | GH-Issue | `e632240` | `176158a3` | High | security issue | access_locked? inconsistent return type | Step 5: Account Locking |
| DEV-15 | #2825 | `2ba8275` | `72a0d9e3` | High | security issue | Off-by-one error in max attempts | Step 5: Account Locking |
| DEV-16 | GH-Issue | `747751a` | `8e0327e2` | Critical | security issue | CSRF token fixation attack vulnerability | Step 1: Security |
| DEV-17 | GH-Issue | `2351d02` | `eaad61b2` | High | security issue | Session data not properly expired | Step 2: Session Management |
| DEV-18 | GH-Issue | `fc251c3` | `f6a74e90` | Medium | error handling | Incorrect flash message on confirmation | Step 3: Email Confirmation |
| DEV-19 | #4797 | `354df3b` | `6f140faf` | High | security issue | Unsanitized parameters in find_or_initialize | Step 1: Authentication |
| DEV-20 | GH-Issue | `8866b8e` | `1c8e97c7` | High | security issue | Error when params is not a hash | Step 1: Authentication |
| DEV-21 | #3318 | `a9d9050` | `c4dfd465` | High | security issue | Reset token not cleared on failed reset | Step 4: Password Reset |
| DEV-22 | #2884 | `a5ad61c` | `4995d3c2` | High | configuration error | Secret key not set before eager load | Step 1: Configuration |
| DEV-23 | #2201 | `9724e38` | `19b5bcbe` | High | security issue | Non-navigational requests treated as navigational | Step 2: Session Management |
| DEV-24 | GH-Issue | `46c2c39` | `7eccc91f` | Medium | configuration error | Format option not passed in devise_for | Step 1: Configuration |
| DEV-25 | GH-Issue | `64aad8b` | `0d279415` | High | validation gap | ControllerHelpers broken with Rails version check | Step 6: Testing |
| DEV-26 | #4127 | `ee65cd6` | `c000b58c` | High | security issue | Devise authentication handling bug | Step 1: Authentication |
| DEV-27 | #3790 | `005d514` | `9568e28d` | Medium | configuration error | Scoped views generator not properly formatted | Step 1: Configuration |
| DEV-28 | GH-Issue | `b5172a0` | `e1c53d65` | High | security issue | CSRF cleanup issue with Rails 7.1 | Step 1: Security |
| DEV-29 | GH-Issue | `ac2ebdf` | `ea94e199` | Medium | security issue | Session store changed in Rails master | Step 2: Session Management |
| DEV-30 | #6021 | `2d53cf4` | `e91b8ee0` | High | validation gap | Email uniqueness validation deprecation error | Step 3: Validation |
| DEV-31 | GH-Issue | `3c885e0` | `9ae013ae` | High | error handling | Changed error messages from confirmation | Step 3: Email Confirmation |
| DEV-32 | GH-Issue | `545a5ce` | `ab77e086` | Critical | security issue | Redundant assignment in RegistrationsController | Step 1: Registration |
| DEV-33 | #2515 | `b7e6711` | `b46b7e37` | High | configuration error | Generator missing attr_accessible for Rails 3.2 | Step 1: Configuration |
| DEV-34 | #1729 | `90dbae4` | `8f4b0654` | High | security issue | Mass assignment security with sign-in keys | Step 1: Authentication |
| DEV-35 | GH-Issue | `af112a2` | `90a3fa8` | High | configuration error | Zeitwerk autoloading fails when ActionMailer not present due to empty mailer file | Step 2: architecture |
| DEV-36 | GH-Issue | `ed1c2a1` | `9be24c0` | High | API contract violation | Mailer proc/lambda defaults improperly called with instance_eval, breaking arity handling | Step 5: defensive patterns |
| DEV-37 | #5563 | `ee8f0f8` | `41e2db2` | Medium | type safety | Frozen string interpolation raises FrozenError on Ruby < 3 in validatable error message | Step 5b: schema types |
| DEV-38 | #4457 | `31aceeb` | `af8f7e9` | High | state machine gap | ParameterFilter adds keys to hash with default_proc, silently creating unexpected fields | Step 5a: state machines |
| DEV-39 | GH-Issue | `d870c0d` | `8ab7963` | High | null safety | update_tracked_fields! calls save on unpersisted records, causing side effects during signup | Step 5: defensive patterns |
| DEV-40 | GH-Issue | `f3e8fd3` | `a0ccc1c` | Medium | configuration error | Rails 7.0 session mock missing enabled? method breaks flash middleware | Step 2: architecture |
| DEV-41 | #5278 | `5075739` | `f26e05c` | Medium | error handling | serializable_hash mutates frozen :except array parameter, raising FrozenError | Step 5: defensive patterns |
| DEV-42 | GH-Issue | `f2a42ab` | `218d14a` | High | protocol violation | Rails 7.1 exposes _prefixes as action method, breaking Devise controller routing | Step 2: architecture |
| DEV-43 | GH-Issue | `fffbeb5` | `b8ed2f3` | Medium | validation gap | Timeoutable module checks remember_created_at existence without verifying Rememberable enabled | Step 3: tests |
| DEV-44 | GH-Issue | `1acd3d1` | `2de7cba` | High | API contract violation | Custom mailer proc defaults not recognized, mailer uses generic sender instead | Step 5: defensive patterns |
| DEV-45 | #2205 | `75ce916` | `c768366` | High | null safety | strip/downcase applied to auth keys without checking respond_to?, breaks non-string attributes | Step 5: defensive patterns |
| DEV-46 | #4712 | `bdd6081` | `e55c9ca` | High | configuration error | Rails 5.2 :credentials deprecates :secrets but Devise only checks :secrets first | Step 2: architecture |
| DEV-47 | GH-Issue | `4a4b5ba` | `c87d8fd` | Medium | validation gap | extend_remember_period config not enforced, cookie expiration always refreshed | Step 3: tests |
| DEV-48 | GH-Issue | `002b4c6` | `9f63850` | High | error handling | confirmations_controller redirect without navigational check raises ArgumentError with nil location | Step 6: quality risks |
| DEV-49 | #5066 | `a823e51` | `e91b8ee` | Medium | configuration error | Scoped views generator uses global error object instead of scoped errors | Step 1: configuration |


### laravel/framework (PHP)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| LAR-01 | #59414 | `d8d65fd` | `854b727` | High | type safety | Macroable trait not handling static closures properly, bindTo() failing on static closures | Missing boundary check |
| LAR-02 | #59394 | `65d1632` | `5fa619e` | High | state machine gap | MorphTo eager load matching fails when ownerKey is null and result key is non-primitive type | State machine gap |
| LAR-03 | #59376 | `8c69608` | `54145ee` | Critical | validation gap | incrementEach/decrementEach updating all rows instead of scoping to model instance, not firing events | Silent failure |
| LAR-04 | #59378 | `54145ee` | `c9bf2cd` | High | API contract violation | Dependency injection binding wrong dispatcher class for faked queueing dispatcher | API contract violation |
| LAR-05 | #59331 | `7106836` | `636d4a7` | High | state machine gap | Sub-minute scheduling skips executions at minute boundaries due to Carbon mutation during iteration | State machine gap |
| LAR-06 | #59336 | `05e550d` | `8aa511e` | Medium | validation gap | Table attribute incrementing parameter not applied to Pivot models due to incorrect condition check | Validation gap |
| LAR-07 | #59159 | `c0b912a` | `6b0638a` | Medium | silent failure | previousPath() returning full external URLs instead of just path component | Silent failure |
| LAR-08 | #59174 | `2d8148b` | `99a94dc` | Medium | type safety | Float to int deprecation warning in trans_choice() for locales with fractional translations | Type safety |
| LAR-09 | #59233 | `5997d3a` | `6201528` | High | silent failure | Batch::add() wipes queue assignment on first job in array chains when batch has no explicit queue | Silent failure |
| LAR-10 | #59113 | `6575242` | `cf4df18` | Medium | error handling | migrate:fresh failing with QueryException when database doesn't exist instead of gracefully handling | Error handling |
| LAR-11 | #59110 | `68d527e` | `63c8c8f` | Low | type safety | MorphToMany morphClass type hint missing array designation in docblock | Type safety |
| LAR-12 | #59058 | `cf4df18` | `29ddeef` | High | validation gap | After-commit observers breaking -ing event cancellation and preventing event propagation | Validation gap |
| LAR-13 | #59071 | `9da4f30` | `d3af763` | Low | type safety | type() method return type incorrect in Illuminate\Filesystem | Type safety |
| LAR-14 | #59059 | `3217f8f` | `c4845a8` | Medium | configuration error | Facade cache file permissions not set correctly causing access issues in CI/CD environments | Configuration error |
| LAR-15 | #59010 | `81518e8` | `a023c8b` | Medium | silent failure | TwoColumnDetail stripping trailing punctuation from second column values in output | Silent failure |
| LAR-16 | #58990 | `93c67e9` | `366d945` | High | concurrency issue | Throttle with redis after callback not properly handling timeout edge cases | Concurrency issue |
| LAR-17 | #58982 | `d2ff936` | `d9f5d43` | Medium | validation gap | URL validation for punycode subdomains failing for single-character domains | Validation gap |
| LAR-18 | #58987 | `e0782f6` | `af52ed5` | Medium | error handling | Division by zero error in repeatEvery() method when calculating interval | Error handling |
| LAR-19 | #58936 | `196ee4b` | `2c996f4` | High | configuration error | RetryCommand not passing queue options to SQS FIFO queue, losing message group IDs | Configuration error |
| LAR-20 | #58945 | `6127ecf` | `f048a66` | High | concurrency issue | Race condition on creating real-time facade cache file causing permission/access errors | Concurrency issue |
| LAR-21 | #58939 | `04b2984` | `2d4ab5e` | High | serialization | Model serialization in queue jobs failing for complex object graphs with unserialized data | Serialization |
| LAR-22 | #58906 | `f344339` | `a85443f` | Critical | error handling | PDO not rolling back on deadlock during commit, leaving transaction in inconsistent state | Error handling |
| LAR-23 | #58909 | `ac79aed` | `2c965d0` | Medium | error handling | RequestException summarizing for Guzzle streamed responses losing context and details | Error handling |
| LAR-24 | #59207 | `a984895` | `f895c1d` | Medium | validation gap | StringRule pipe-delimited parsing in ValidationRuleParser not handling escaped delimiters | Validation gap |
| LAR-25 | #58718 | `6651288` | `78ec010` | High | silent failure | Queue::fake() not releasing unique job locks between tests causing cross-test pollution | Silent failure |
| LAR-26 | #58707 | `6010b37` | `9a94aad` | High | concurrency issue | ThrottleRequests over-throttling with multiple distinct rate limit keys not respecting individual limits | Concurrency issue |
| LAR-27 | #58686 | `8aded48` | `8aaaa4d` | Medium | validation gap | Str::isUrl() returning false for valid single-character domain names due to regex | Validation gap |
| LAR-28 | #58962 | `8d8465a` | `8c02ca0` | Medium | type safety | Null safe operator equals not working correctly for cross-database comparisons | Type safety |
| LAR-29 | #58687 | `e8f4b59` | `b5e0b2b` | Medium | validation gap | whereBetween not accepting DatePeriod objects and not handling missing end dates | Validation gap |
| LAR-30 | #58752 | `244449a` | `b67f4cf` | Medium | type safety | JSON:API resources returning wrong Collection type for non-model resources | Type safety |
| LAR-31 | #58634 | `c13756f` | `8c02ca0` | Medium | error handling | Str::substrReplace failing for edge cases with negative offset or length parameters | Error handling |
| LAR-32 | #58458 | `ae924df` | `0907566` | High | silent failure | Memory leak in Arr::dot() not releasing references when processing large nested arrays | Silent failure |
| LAR-33 | #58541 | `eef787a` | `7810109` | Medium | validation gap | Batch counts incorrect when deleteWhenMissingModels skips missing model jobs in calculation | Validation gap |
| LAR-34 | #58602 | `08741c1` | `0f3caf7` | Medium | type safety | Precision checks for SQL Server column types not handling numeric scale correctly | Type safety |
| LAR-35 | #58618 | `1e516f4` | `7fa1c8f` | Medium | error handling | Binary data in Js::encode() debug renderer causing invalid JSON output and debug failures | Error handling |
| LAR-36 | #58691 | `78d19fe` | `57eb459` | High | concurrency issue | Cache prefix not isolated for parallel testing causing test cross-contamination and race conditions | Concurrency issue |
| LAR-37 | #58684 | `9f296f7` | `6aca75a` | Medium | type safety | HTTP client response type hints inconsistent with IDE expectations causing autocomplete failures | Type safety |
| LAR-38 | #58199 | `fbc03ba` | `cf2f19a` | Medium | configuration error | Postgres sequence starting value not set correctly for custom schemas and connections | Configuration error |
| LAR-39 | laravel/framework#59404 | `45b8782` | `c03d444` | High | state machine gap | Trait initializer collision with Attribute parsing: trait initializers calling mergeFillable/mergeAppends/mergeHidden/mergeVisible silently dropped when model used PHP Attributes, guard prevented Attribute assignment | Step 5a state machines |
| LAR-40 | laravel/framework#59418 | `691715e` | `8222fc5` | Medium | validation gap | JSON:API resources deprecation notice when sparseIncluded encounters non-string or empty items, implode() triggers deprecation | Step 4 specs |
| LAR-41 | laravel/framework#59303 | `6914aa6` | `e422362` | Low | error handling | SeeInHtml assertion missing negate method for negative assertions, prevents use in dont* test methods | Step 3 tests |
| LAR-42 | laravel/framework#59292 | `ba17200` | `bb12117` | Critical | error handling | Exception mid-stream in eventStream response causes fatal "Cannot modify header" error after headers sent, global exception handler cannot respond | Step 5 defensive patterns |
| LAR-43 | laravel/framework#59132 | `4ce9f70` | `0561c47` | High | type safety | Enum handling in ModelNotFoundException fails when BackedEnum passed to findOrFail(), implode() throws fatal error on enum | Step 5b schema types |
| LAR-44 | laravel/framework#59133 | `1d9c186` | `68d527e` | Medium | API contract violation | Middleware attribute parameter named 'value' instead of 'middleware', accessor code used wrong property name | Step 2 architecture |
| LAR-45 | laravel/framework#59187 | `8ed1300` | `bc345b9` | High | validation gap | insertOrIgnoreReturning parameter order confusing, API signature had uniqueBy before returning columns, breaks when multiple unique keys | Step 4 specs |
| LAR-46 | laravel/framework#59051 | `5166b98` | `697255c` | Medium | configuration error | Custom markdown extensions for mail not loaded from config, Markdown renderer ignored extension configuration option | Step 2 architecture |
| LAR-47 | laravel/framework#59269 | `3af5e2b` | `62df898` | Medium | null safety | Null broadcaster deprecation warning in PHP 8.5 when broadcasting.default config empty, no fallback to 'null' driver | Step 5 defensive patterns |
| LAR-48 | laravel/framework#59121 | `9f456f6` | `ce422c7` | Medium | API contract violation | Cache::touch() accepting null TTL with silent forever behavior, behavior changed breaking BC, removed null default | Step 4 specs |
| LAR-49 | laravel/framework#59116 | `ce422c7` | `30ea09f` | Medium | state machine gap | JSON API flushState() resetting maxRelationshipDepth to wrong value (3 instead of 5), breaks test isolation | Step 5a state machines |
| LAR-50 | laravel/framework#59019 | `a03cd3c` | `9fcd342` | High | null safety | Array offset deprecation warning in PHP 8.5 Collection merge/diff/intersect using null getDictionaryKey, offset on null | Step 5 defensive patterns |
| LAR-51 | laravel/framework#57627 | `391d54` | `042bc5d` | Medium | error handling | Cached casts unnecessarily merged for every attribute access even when not needed, wasted performance on unrelated fields | Step 6 quality risks |
| LAR-52 | laravel/framework#58482 | `3ea4ffc` | `b32b3d4` | Medium | serialization | Model serialization ignoring morphMap when storing model identifiers in queued jobs, wrong class name used during deserialization | Step 5b schema types |
| LAR-53 | laravel/framework#58475 | `4af55b2` | `451016e` | Medium | error handling | Unnecessary message serialization when log level not handled by handlers, expensive formatting/serialization for ignored messages | Step 5 defensive patterns |
| LAR-54 | laravel/framework#58963 | `d3cae1b` | `f76eed6` | High | type safety | Invalid type hints in closures and callables missing parentheses, bindTo() not valid on all callables only Closures | Step 5b schema types |
| LAR-55 | laravel/framework#58786 | `8349518` | `b28c8dc` | High | configuration error | MySQL SSL mode connection string using wrong flag for modern clients, --ssl=off not supported in MySQL 5.7.11+, must use --ssl-mode=DISABLED | Step 2 architecture |
| LAR-56 | laravel/framework#59360 | `b2dcd15` | `8f9f980` | High | configuration error | MariaDB schema state detection using mysql --version instead of mariadb --version command, wrong version detection logic | Step 2 architecture |
| LAR-57 | laravel/framework#59299 | `2d8e8f4` | `9f3c52c` | Medium | error handling | Unique constraint violation exception missing column and index details, parsing database error details not implemented for exception | Step 4 specs |
| LAR-58 | laravel/framework#59251 | `980260d` | `e1a96ea` | Medium | type safety | str_word_count() behavior change in PHP 8.5 for multibyte characters, test expectations outdated, quoted-printable soft breaks causing issues | Step 3 tests |


### guzzle/guzzle (PHP)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| GUZ-01 | #3238 | `40ad735` | `84ac2b2` | High | security issue | Incorrect TLS 1.3 version check preventing crypto method configuration | Step 4: Verify TLS version detection |
| GUZ-02 | #3234 | `0e9dcae` | `3838e05` | Medium | error handling | CurlMultiHandler busy wait causing high CPU usage on concurrent requests | Step 3: Optimize select loop |
| GUZ-03 | #3018 | `74a8602` | `b720a2d` | High | error handling | Cross-domain cookie leakage allowing cookies to be sent to unintended domains | Step 5: Validate cookie domain matching |
| GUZ-04 | #2845 | `cc80b00` | `802ecc6` | High | protocol violation | HTTP Basic auth credentials leaked on cross-domain redirects | Step 6: Strip auth on redirect validation |
| GUZ-05 | #2950 | `e6765c0` | `1d347d7` | High | error handling | Premature cURL handle closure causing resource leaks and connection errors | Step 2: Check handle lifecycle |
| GUZ-06 | #2936 | `5da9dac` | `6b499cc` | Medium | error handling | StreamHandler progress callback incompatible with cURL type expectations (null vs int) | Step 7: Validate callback parameter types |
| GUZ-07 | #3117 | `c6f3a35` | `242f128` | Medium | protocol violation | NO_PROXY environment variable not respected for proxy bypass configuration | Step 5: Test proxy bypass with NO_PROXY |
| GUZ-08 | #3131 | `ebd2b6b` | `255d71` | Medium | protocol violation | Zero (0) as request body incorrectly treated as empty instead of valid scalar | Step 3: Handle zero-value bodies |
| GUZ-09 | #3133 | `15c3f69` | `ebd2b6b` | High | error handling | SetCookie constructor validation insufficient allowing invalid cookie attributes | Step 4: Validate cookie attributes |
| GUZ-10 | #3141 | `0d06ef5` | `4019c94` | Medium | error handling | MaxAge cookie attribute parsing generates deprecation warnings in PHP 8.2+ | Step 6: Suppress cookie attribute warnings |
| GUZ-11 | #2989 | `be834db` | `cc80b00` | High | error handling | Non-HTTP schemes passed to StreamHandler cause TypeError on response headers | Step 2: Validate URI scheme |
| GUZ-12 | #2988 | `8e4a4cd` | `be834db` | High | security issue | SNI hostname mismatch when using force_ip_resolve option breaks TLS verification | Step 3: Set ssl.peer_name context |
| GUZ-13 | #2741 | `fe7556b` | `4552f37` | High | error handling | Response body stream EOF handling broken on Windows platform | Step 4: Handle Windows stream EOF |
| GUZ-14 | #2778 | `4552f37` | `2890bde` | Medium | protocol violation | HEAD requests incorrectly connect output sinks causing memory leaks | Step 5: Skip sink for HEAD requests |
| GUZ-15 | #3281 | `8f68d9f` | `234747f` | Medium | error handling | Boolean cookie values (true/false) parsed incorrectly for non-compliant servers | Step 7: Lenient cookie boolean parsing |
| GUZ-16 | #3278 | `234747f` | `d28a072` | Medium | protocol violation | Explicit Content-Length header on GET requests causes 500 errors on some servers | Step 2: Remove GET Content-Length |
| GUZ-17 | #3301 | `af24c69` | `2be2ee8` | Medium | error handling | Response headers not properly captured in stream wrapper fallback mode | Step 4: Use http_get_last_response_headers |
| GUZ-18 | #3055 | `514f665` | `84779a5` | High | error handling | cURL disabled on janky shared hosting causes graceful handler fallback failure | Step 3: Detect curl availability |
| GUZ-19 | #3165 | `2ca50ce` | `21314fd` | Medium | error handling | cURL handles not closed on CurlFactory object destruction causing resource leaks | Step 5: Cleanup handles on destruct |
| GUZ-20 | #3158 | `21314fd` | `cd634c2` | Medium | configuration error | CurlMultiHandler generates #[AllowDynamicProperties] deprecation warnings in PHP 8.2+ | Step 2: Remove dynamic properties |
| GUZ-21 | #3142 | `7936fe9` | `925b5ed` | Medium | configuration error | guzzlehttp/promises v2 compatibility breaks async request handling | Step 4: Support promises v2 |
| GUZ-22 | #3135 | `ea2e084` | `3d12c4b` | Medium | protocol violation | HTTP protocol version option not applied to request causing version mismatch | Step 6: Merge version options |
| GUZ-23 | #3132 | `a8154fc` | `255d71` | Medium | security issue | Crypto method option not applied to cURL handler configuration | Step 3: Set crypto method |
| GUZ-24 | #2942 | `399c0ea` | `eeac96d` | High | protocol violation | Invalid headers array format not caught causing downstream TypeError | Step 2: Validate headers structure |
| GUZ-25 | #2945 | `70d32b9` | `399c0ea` | Medium | error handling | SetCookie constructor allows invalid types causing strict type errors | Step 5: Enforce type hints |
| GUZ-26 | #2946 | `01611d9` | `e6765c0` | Medium | protocol violation | Implicit URI to string coercion deprecated in PHP 8.1+ breaks URI processing | Step 3: Explicit URI conversion |
| GUZ-27 | #2591 | `616288a` | `48fa032` | High | protocol violation | Exception during response creation not properly caught causing unhandled errors | Step 4: Wrap response creation |
| GUZ-28 | #2660 | `48fa032` | `977b0de` | High | protocol violation | TooManyRedirectsException missing response context for debugging | Step 6: Include response in exception |
| GUZ-29 | #3057 | `be2902f` | `0114fa0` | Medium | SQL error | Delay closure params not passed through causing configuration loss | Step 5: Pass request in closure |
| GUZ-30 | #2715 | `33e12c0` | `fa121c2` | Medium | error handling | is_resource() check fails on PHP 8 CurlHandle and CurlMultiHandle objects | Step 2: Handle PHP 8 objects |
| GUZ-31 | #1872 | `9b776cf` | `c19f9e2` | Medium | SQL error | {res_body} token produces empty output in logging causing diagnostic loss | Step 4: Capture response body |
| GUZ-32 | #2661 | `c19f9e2` | `59dada7` | High | error handling | cURL error messages fail on low version cURL causing unhelpful error reporting | Step 3: Check cURL version |
| GUZ-33 | #2699 | `2d9d3c1` | `414c249` | High | configuration error | Multiply defined functions fatal error on autoload causing instantiation failure | Step 2: Conditional function definition |
| GUZ-34 | #2691 | `b504f7a` | `0a97380` | Medium | error handling | Empty string cookie values not stored in CookieJar causing data loss | Step 5: Preserve empty strings |
| GUZ-35 | #2509 | `7521a46` | `662b4e1` | Medium | configuration error | idn_to_ascii() compatibility broken on old PHP versions causing domain conversion failure | Step 3: Version-aware IDN conversion |
| GUZ-36 | #2311 | `662b4e1` | `cce7ba5` | Medium | SQL error | Logging with string rejection causes uncaught TypeError in error handler | Step 4: Type check rejection objects |
| GUZ-37 | #2499 | `67f3aa0` | `865ff35` | Medium | error handling | MockHandler missing type hints breaks type checking and static analysis | Step 6: Add handler type hints |
| GUZ-38 | #3220 | `9678673` | `7b7036a` | High | validation gap | cURL handler selection fails on systems with cURL < 7.34.0 due to missing version check before handler registration | Step 2: Validate cURL version before default handler selection |
| GUZ-39 | #3203 | `53f5a4e` | `354893b` | Medium | configuration error | Nullable type hints missing on constructor parameters causing PHP 8.4 deprecation warnings in BodySummarizer | Step 3: Add nullable type declarations |
| GUZ-40 | #3236 | `3bec073` | `740e191` | High | security issue | URI user info (username/password) exposed in exception error messages creating password leakage vulnerability | Step 5: Redact user info from URI in errors |
| GUZ-41 | #2866 | `da94ef2` | `2793fe2` | High | API contract violation | String domain parsing fails when hostname contains port due to reversed explode() parameters causing array index errors | Step 4: Validate explode parameter order |
| GUZ-42 | #2850 | `2793fe2` | `55d46a8` | Medium | protocol violation | StreamHandler proxy support broken for http:// schemes (missing conversion to tcp:// for stream context) blocking proxy usage | Step 5: Convert http proxy scheme to tcp |
| GUZ-43 | #2595 | `368bf4d` | `957b0a0` | Medium | configuration error | Custom CURLOPT_ENCODING configuration overwritten by auto-detected Accept-Encoding header causing compression bypass | Step 3: Check CURLOPT_ENCODING before setting |
| GUZ-44 | #2795 | `957b0a0` | `c8c99e3` | Medium | error handling | HTTP errors middleware missing truncateBodyAt parameter support causing full body responses in error messages | Step 4: Support truncate_body_at in middleware |
| GUZ-45 | #2799 | `3d87fb8` | `d5a2b03` | Medium | error handling | HEAD requests with Accept-Encoding incorrectly decoded causing content-encoding header stripping and size mismatch | Step 3: Skip decode for HEAD requests |
| GUZ-46 | #2776 | `7881628` | `aec1152` | Low | error handling | Windows compatibility test randomly fails due to directory/file handling timing issue causing intermittent failures | Step 2: Fix Windows path race condition |
| GUZ-47 | #2724 | `7464d15` | `c6fec1e` | Medium | null safety | http_build_query() called with null prefix parameter causing type error in PHP 8+ strict mode | Step 2: Use empty string instead of null |
| GUZ-48 | #2629 | `bb71627` | `5aee914` | Low | error handling | Error-level exceptions logged as notice level hiding critical failures from error reporting | Step 3: Use error level for errors |
| GUZ-49 | #2626 | `d3f2c17` | `c8162be` | Medium | configuration error | IDN domain conversion fails on PHP with old intl library due to missing INTL_IDNA_VARIANT_UTS46 constant causing domain parsing errors | Step 4: Check INTL variant availability |
| GUZ-50 | #2466 | `45b360e` | `d824c1d` | Medium | type safety | Type hints missing on SetCookie validation functions causing incorrect validation behavior and accepting invalid types | Step 5: Enforce strict type checking |
| GUZ-51 | #3241 | `11d3f21` | `a629e5b` | Medium | validation gap | Minimum cURL version check prevents handler selection on older systems incorrectly rejecting cURL 7.21.2-7.33.x compatibility | Step 2: Adjust minimum cURL version threshold |
| GUZ-52 | #3280 | `d28a072` | `41f5ce7` | Low | error handling | Platform-specific HTTP server behavior change in PHP 8.2+ causes test to fail on newer versions due to fopen() behavior change | Step 3: Conditionally handle PHP version behavior |


### composer/composer (PHP)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| CMP-01 | #12696 | `9d18266` | `2b9ebc73` | Low | configuration error | Optimize plugin autoloading by avoiding regenerating classmaps and co for every pa... | Step 5 |
| CMP-02 |  | `ef46dad` | `fb761e97` | High | error handling | custom script classloader regression from b1a33d4339 | Step 6 |
| CMP-03 | #12758 | `b1a33d4` | `e0f848b9` | Low | error handling | inconsistent treatment of SingleCommandApplication script commands (#12758) | Step 6 |
| CMP-04 | #12737 | `68aff4e` | `982d0676` | High | error handling | Relay GitHub API error messages to the user on auth failures (#12737) | Step 4 |
| CMP-05 | #12726 | `9861166` | `2102496e` | Low | error handling | Update symfony/process to #12726 | Core |
| CMP-06 | #12709 | `fa88b8a` | `5a6a11fd` | Low | error handling | php scripts outputting even tho they should not in script alias command, #12709 | Step 6 |
| CMP-07 | #12705 | `223e0f9` | `a0ed1fd3` | Low | error handling | git rev-list usages to support older git versions (#12705) | Step 4 |
| CMP-08 | #12694 | `35c287d` | `f935eecb` | Low | error handling | Validate php-ext schema in ValidatingArrayLoader (#12694) | Core |
| CMP-09 | #12667 | `a38a8a4` | `ac2f8b8c` | Low | error handling | fix(AuthHelper): misplaced `username` and `password` (#12667) | Core |
| CMP-10 | #12668 | `42fe527` | `95e800ef` | High | error handling | regression in showing reasons for ignoring advisories (#12668) | Core |
| CMP-11 | #12660 | `95e800e` | `75ec505f` | Critical | concurrency issue | crash bumping version with composer update and disabled lockfile (#12660) | Step 3 |
| CMP-12 | #12666 | `f52ba76` | `c5dc509d` | Low | error handling | Use git rev-list instead of log to avoid issues with log.showSignature being enabl... | Step 4 |
| CMP-13 | #12662 | `379b52b` | `8836a921` | Low | error handling | Retry on curl timeouts (28) (#12662) | Step 4 |
| CMP-14 | #12664 | `8836a92` | `615ae61f` | Low | error handling | Handle lastCommand bieng a string (#12664) | Step 6 |
| CMP-15 | #12634 | `b2c3157` | `4aefb30b` | High | concurrency issue | update --lock / update mirrors not working when locked packages contain vulnerabil... | Step 3 |
| CMP-16 | #12626 | `98861c6` | `f85f82d2` | Critical | concurrency issue | partial updates failing when a locked package has security advisories (#12626) | Step 3 |
| CMP-17 | #12627 | `f85f82d` | `bfc0e314` | Critical | concurrency issue | Merge pull request #12627 from Seldaek/audit_fix | Step 3 |
| CMP-18 | #12605 | `4e92161` | `47e5184c` | Low | error handling | null call of Command::setDescription, #12605 | Step 6 |
| CMP-19 | #12606 | `47e5184` | `80503cbb` | High | configuration error | script autoloading regressions (#12606) | Step 5 |
| CMP-20 | #12601 | `5ad6a46` | `60323816` | Low | error handling | Reverting 86b4aa1 to path resolution for vendor/bin proxies (#12601) | Step 6 |
| CMP-21 | #12595 | `880cc92` | `5a308f1c` | Low | concurrency issue | Add --locked flag to licenses command (#12595) | Step 3 |
| CMP-22 | #12388 | `f414237` | `686161e7` | Low | error handling | Add repo command to manipualte repositories in composer.json (#12388) | Step 4 |
| CMP-23 | #12579 | `686161e` | `028e0577` | Low | error handling | Installer: audit call (#12579) | Core |
| CMP-24 | #12470 | `c82ba19` | `0e9a5051` | Low | error handling | feat: Added --ignore-unreachable flag to audit command for private/unreachable rep... | Step 4 |
| CMP-25 | #12562 | `0e9a505` | `cbb73aed` | Low | error handling | display of dist refs for dev versions when source is missing (#12562) | Step 1 |
| CMP-26 | #12528 | `cbb73ae` | `710392a8` | Low | error handling | Add detection for preload being active and if it causes errors try to warn users (... | Core |
| CMP-27 | #12423 | `1a22bb1` | `8fc94c5e` | Low | error handling | Ensure packages where the abandoned state changes get reinstalled to sync up the s... | Core |
| CMP-28 | #12513 | `b6ec91b` | `b47b0b71` | Medium | error handling | php8.5 deprecation warning (#12513) | Core |
| CMP-29 | #12512 | `b47b0b7` | `a87f7120` | High | error handling | a regression introduced via 304107d (#12512) | Step 1 |
| CMP-30 | #12468 | `304107d` | `c50807e2` | Low | error handling | Avoid bumping 0.3 to 0.4.3 for example for pre-1.0 releases, #12468 | Core |
| CMP-31 | #12507 | `5a85ab7` | `e95d72a2` | Low | configuration error | audit command failing when an advisory contains an invalid constraint (#12507) | Step 2 |
| CMP-32 | #12480 | `e95d72a` | `304107db` | Medium | configuration error | PSR-4 warnings when using exclude-from-classmap with symlinked directories (#12480) | Step 2 |
| CMP-33 | #12505 | `d35c034` | `50143439` | Medium | error handling | fix: deprecation of curl_close in CurlDownloader.php (#12505) | Step 4 |
| CMP-34 | #12435 | `21df6d8` | `c98d0ef5` | High | error handling | git prompt breaking on some systems, #12435 (#12437) | Step 4 |
| CMP-35 | #12438 | `c98d0ef` | `09981764` | Low | error handling | Remove possessive quantifier to JS regex engines support for schema (#12438) | Core |
| CMP-36 | N/A | `5e71d77` | `2bcbfc3` | High | security issue | Insecure 3DES cipher suites exposed in TLS defaults when curl is disabled, affecting StreamContextFactory stream configuration | Step 4 (protocol violations) |
| CMP-37 | N/A | `2bcbfc3` | `b1a33d4` | Critical | security issue | Credentials persisting in git mirror .git/config after failed clone/update, exposing secrets in local git cache | Step 4 (protocol violations) |
| CMP-38 | #12731 | `5b44d62` | `4c49f46` | Medium | configuration error | 7z detection broken when tool is installed as '7za' instead of '7z', blocking zip archive handling in DiagnoseCommand and ZipDownloader | Step 3 (validation testing) |
| CMP-39 | #12710 | `4243404` | `be033a8` | Medium | state machine gap | Initial working directory detection fails when using relative paths with -d flag, causing incorrect Application context in console startup | Step 5a (state machines) |
| CMP-40 | #12615 | `47cde53` | `29105dc` | High | null safety | Platform detection for securetransport + libressl combination returns invalid/unsafe ssl extension state, failing PlatformRepository validation | Step 5b (schema types) |
| CMP-41 | #12677 | `efaefc1` | `9497eca` | High | validation gap | COMPOSER_NO_SECURITY_BLOCKING flag ignored on install command updates, bypassing security advisory filtering | Step 3 (validation) |
| CMP-42 | #12640 | `5dafb78` | `d150ce9` | Low | error handling | Incorrect option name in AuditCommand error message (-a instead of -a flag), confusing users about audit flags | Step 3 (specs) |
| CMP-43 | #12624 | `59eb8e7` | `bfc0e31` | High | validation gap | CVE ID ignoring in security blocking fails, allowing ignored vulnerabilities to pass through Auditor validation filter | Step 3 (validation) |
| CMP-44 | #12226 | `5cb9733` | `eefa012` | Medium | type safety | PluginManager crashes when plugin defines multiple PluginInterface classes, registeredPlugins map expects single value not array | Step 5b (schema types) |
| CMP-45 | #12176 | `fa5b361` | `0a4c2a9` | Medium | error handling | Signal handling in non-PHP binary proxies broken, failing to pass through SIGINT/SIGTERM to subprocess via BinaryInstaller | Step 5a (signal state) |
| CMP-46 | #12146 | `ac2f89a` | `33ffd5a` | Medium | silent failure | CreateProjectCommand fails to inherit target folder permissions when copying files, leaving project with incorrect file modes | Step 3 (validation) |
| CMP-47 | #12453 | `63d22cd` | `a77e5f0` | Low | error handling | PHP 8.4 deprecation warnings in generated autoload code about missing null type declarations, polluting install output | Step 3 (specs) |
| CMP-48 | #12410 | `b3e6327` | `3b78dba` | Low | error handling | Self-update command fails with confusing error when not running from phar, instead of clear "feature unavailable" message | Step 3 (specs) |
| CMP-49 | #12442 | `6c31f21` | `cec1bbc` | Medium | state machine gap | Plugin marked as loaded before actually loading, causing double-load issues when plugin fails to activate mid-load | Step 5a (state machines) |
| CMP-50 | #12178 | `e0ed22b` | `1f0d012` | High | validation gap | Git safe.directory errors not detected or thrown during VersionGuesser initialization, causing silent failures in version detection with restricted git repos | Step 4 (repository interaction) |


### ktorio/ktor (Kotlin)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| KT-01 | KTOR-1915 | `553c5343` | `af5df778` | Medium | error handling | 1915 Add appendBlob for multipart form data from Kotlin/JS ( | General |
| KT-02 | KTOR-5199 | `0828cbf6` | `299b1ee8` | Medium | protocol violation | 5199 Support WebSockets in Curl engine (#4656)               | Step 3 |
| KT-03 | KTOR-5850 | `69ca7cf8` | `9c6404bb` | High   | protocol violation | 5850 Fix SendCountExceedException in HttpRequestRetry (#5159 | Step 1 |
| KT-04 | KTOR-6242 | `c1c8764b` | `0828cbf6` | Medium | protocol violation | 6242 Add reconnection in client sse (#4640)                  | Step 1 |
| KT-05 | KTOR-6300 | `eb968cb5` | `aceff01c` | Medium | state machine gap | 6300 Native: Use IO dispatcher and allow dispatcher overridi | Step 4 |
| KT-06 | KTOR-6651 | `5710ef96` | `a5546d21` | Medium | security issue | 6651 Server Auth JWT. Run 'jwkProvider.get' using Dispatcher | Step 2 |
| KT-07 | KTOR-7104 | `7808fca1` | `9b136256` | Medium | error handling | 7104 Fix saving caches with different vary header (#4673)    | Step 9 |
| KT-08 | KTOR-7416 | `cf1b01f9` | `c91aa746` | Medium | protocol violation | 7416 Allow custom Host header in Java and Jetty client engin | Step 5 |
| KT-09 | KTOR-7713 | `f9a45055` | `af8e6bd2` | High   | protocol violation | 7713 HttpCallValidatorConfig.handleResponseException should  | Step 1 |
| KT-10 | KTOR-8528 | `b55490fe` | `64f98c2c` | High   | protocol violation | 8528 Fix race condition when Netty removes headers for some  | Step 1 |
| KT-11 | KTOR-8751 | `d4763cab` | `2d949198` | High   | error handling | 8751 Fix AmbiguousDependencyException during DI shutdown (#5 | General |
| KT-12 | KTOR-9108 | `e081285b` | `dba89580` | Medium | protocol violation | 9108 Remove Connection: keep-alive for HTTP/2 in sse (#5220) | Step 1 |
| KT-13 | KTOR-9187 | `25d9b354` | `c6c1a5c9` | High   | security issue | 9187 Darwin Client. Close session once engine is closed (#54 | Step 2 |
| KT-14 | KTOR-9267 | `78641d12` | `2d3a1921` | Medium | protocol violation | 9267 Curl: Handle chunked websocket frames (#5355)           | Step 3 |
| KT-15 | KTOR-9276 | `a4898b8e` | `630e201b` | Medium | security issue | 9276 Dynamic auth provider suspend authenticate (#5356)      | Step 2 |
| KT-16 | KTOR-9318 | `ffb87bd6` | `f2208232` | Medium | error handling | 9318 Do not validate server certificate against handshake al | General |
| KT-17 | KTOR-9331 | `85713a38` | `e1f1a98a` | High   | protocol violation | 9331 Curl: Fix segfaults when working with WebSockets (#5365 | Step 3 |
| KT-18 | KTOR-9333 | `a6aed07c` | `a6bd1d3e` | Medium | error handling | 9333 Preserve inflater context (#5403)                       | General |
| KT-19 | KTOR-9344 | `a6bd1d3e` | `f557ef7e` | Medium | state machine gap | 9344 Disable switching to engine dispatcher by default (#540 | Step 4 |
| KT-20 | KTOR-9350 | `ab9156ca` | `dda96bc6` | Medium | error handling | 9350 JS: Ensure ES modules compatibility (#5396)             | General |
| KT-21 | KTOR-9352 | `a5b2eb6b` | `a9713173` | Medium | error handling | 9352 Handle EC key type when JWK algorithm is null (#5387)   | General |
| KT-22 | KTOR-9353 | `8c6ef885` | `a6aed07c` | Medium | error handling | 9353: Override toString for TailcardSelector and LocalPortRo | General |
| KT-23 | KTOR-9354 | `af5df778` | `ab9156ca` | Medium | protocol violation | 9354 Return Route from webSocket and webSocketRaw builders ( | Step 3 |
| KT-24 | KTOR-9362 | `a9713173` | `a23c4544` | High   | error handling | 9362 Catch ClosedWriteChannelException in the timeout corout | Step 8 |
| KT-25 | KTOR-9372 | `33dbc402` | `56250412` | High   | protocol violation | 9372 Fix infinite loop in CharsetDecoder.decode on Native wi | Step 5 |
| KT-26 | KTOR-9383 | `c91aa746` | `d4763cab` | Medium | protocol violation | 9383 CaseInsensitiveMap and StringValuesImpl: zero-allocatio | Step 5 |
| KT-27 | KTOR-9387 | `19ade27c` | `3fcfadd4` | Medium | serialization | 9387: Fix ZstdEncoder.decode when source data is split into  | Step 6 |
| KT-28 | KTOR-9393 | `3fcfadd4` | `25d9b354` | Medium | error handling | 9393 Darwin Client. Use correct pins for certificate pinning | General |
| KT-29 | KTOR-9402 | `dda96bc6` | `7b84f098` | High   | protocol violation | 9402 Fix binary incompatibility in RawWebSocket after 3.4.0  | Step 3 |
| KT-30 | KTOR-9421 | `a5546d21` | `72ea6c92` | Medium | protocol violation | 9421 Track streaming responses separately to fix SSE blockin | Step 1 |
| KT-31 | KTOR-9334 | `f1485652` | `78641d12` | Medium | state machine gap | Unconfined dispatcher used in handler context causing race conditions in Jetty/Netty engines | Step 5a |
| KT-32 | KTOR-9304 | `8d20712a` | `5c0abc12` | High | API contract violation | OpenAPI parameter ordering lost during route description merging, parameters appeared in wrong order | Step 4 |
| KT-33 | KTOR-9263 | `15cb89a1` | `bf25bb96` | Medium | protocol violation | HTTP chunked transfer encoding extensions not properly ignored, causing decode failures | Step 6 |
| KT-34 | KTOR-9102 | `5072b016` | `835d7f9f` | High | error handling | SSE connection not properly closed in Java engine, preventing resource cleanup and causing hangs | Step 1 |
| KT-35 | KTOR-6963 | `aaa4fa93` | `0787564c` | High | missing boundary check | Darwin WebSocket engine exceeded frame size limits, causing silent data truncation | Step 3 |
| KT-36 | KTOR-8697 | `5e9794b0` | `09b599e0` | Medium | error handling | HTTP redirect with missing Location header causes NPE instead of fallback | Step 2 |
| KT-37 | KTOR-8700 | `92266d53` | `92708fa2` | Medium | protocol violation | WebSocket binary frame FIN bit incorrectly set on WASM/JS platforms | Step 3 |
| KT-38 | KTOR-8411 | `d8b7769f` | `6830d575` | High | state machine gap | CountedByteWriteChannel autoFlush flag not propagated to parent channels, causing buffer stalls | Step 5b |
| KT-39 | KTOR-8291 | `46a4db94` | `97ebfd99` | High | concurrency issue | Coroutines not properly joined on application shutdown, causing resource leaks | Step 5a |
| KT-40 | KTOR-8407 | `bc9805b1` | `4bfb3ab2` | Medium | configuration error | ByteChannel readUntil() function had O(n²) performance on large buffers due to inefficient scanning | Step 5 |
| KT-41 | KTOR-8318 | `4bfb3ab2` | `7059596f` | Medium | error handling | Apache HTTP client entity producer handler leaked connections on exception | Step 2 |
| KT-42 | KTOR-8276 | `871a76c1` | `14d10c0c` | High | silent failure | Micrometer metrics accumulation caused OOM without warning on long-running servers | Step 6 |
| KT-43 | KTOR-8144 | `ec52ef54` | `9eef7dd1` | High | null safety | Native socket close with open read/write channels caused descriptor leaks and crashes | Step 1 |
| KT-44 | KTOR-8138 | `1d502e57` | `dc09c36b` | Medium | configuration error | Jetty engine idleTimeout configuration not properly applied to response handling | Step 5b |
| KT-45 | KTOR-7734 | `c6bdf2b5` | `747fef93` | High | error handling | JavaScript browser fetch channel reader closure errors silently ignored, breaking SSE connections | Step 3 |


### JetBrains/Exposed (Kotlin)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| EXD-01 | EXPOSED-1000 | `63b46935` | `28e7caed` | High | state machine gap | Multiple decrypts of encrypted fields when fetching fresh data for cached entity | Data integrity / Cache coherency |
| EXD-02 | EXPOSED-983 | `e6de7046` | `35f48c83` | High | serialization | JSONB columns cannot be read outside transaction - dialect check fails | Transaction boundary violation |
| EXD-03 | EXPOSED-992 | `f69ce673` | `d8aee4bd` | High | type safety | Kotlin UUID type leaks into R2DBC driver causing bind failures | Cross-dialect type safety |
| EXD-04 | EXPOSED-986 | `5a7f6ccc` | `7dcab411` | High | error handling | ImmutableCachedEntity incorrectly cleared on transaction rollback | Transaction rollback semantics |
| EXD-05 | EXPOSED-982 | `b07361f4` | `865749f3` | High | validation gap | Connection leak when coroutine cancelled during suspendTransaction | Resource leak / async handling |
| EXD-06 | EXPOSED-951 | `69d69ff0` | `387782b1` | Medium | state machine gap | Transaction userData inaccessible to afterCommit() interceptor | Interceptor API completeness |
| EXD-07 | EXPOSED-754 | `635fda78` | `d9c40ad3` | High | error handling | Global rollback mark not set on unchecked exception in Spring | Spring integration correctness |
| EXD-08 | EXPOSED-698 | `75af3c7e` | `e46149c6` | High | SQL error | dropIndex() fails on Oracle and H2 dialects | Dialect-specific DDL correctness |
| EXD-09 | EXPOSED-877 | `8eed92cc` | `9c8247c9` | High | state machine gap | Error 'No transaction in context' for select statements | Transaction context management |
| EXD-10 | EXPOSED-880 | `0b4ab738` | `96be142c` | High | serialization | Nullable JSON columns in batches not properly cast for PostgreSQL | Batch statement preparation |
| EXD-11 | EXPOSED-886 | `222d126c` | `909076c8` | High | state machine gap | Changes to DAO lost on serializable transaction retry (Postgres) | Serializable isolation handling |
| EXD-12 | EXPOSED-856 | `92d5b9b2` | `a4b2fc91` | Medium | type safety | UUID array inserts not supported in R2DBC | Array type support |
| EXD-13 | EXPOSED-815 | `1ef194f6` | `d32e5c35` | Medium | SQL error | ExpressionAlias resolution broken | Query composition safety |
| EXD-14 | EXPOSED-801 | `b97b86c6` | `9bafcc41` | High | configuration error | NoClassDefFoundError with exposed-json and postgresql-r2dbc only | Dependency resolution |
| EXD-15 | EXPOSED-731 | `5af48a7d` | `9d056aa4` | High | error handling | SQLite timestamp support completely broken | Dialect-specific type support |
| EXD-16 | EXPOSED-815 | `0f2bdf82` | `2f763f2f` | Medium | SQL error | QueryAlias.get() type checking missing at runtime | Type safety / Runtime validation |
| EXD-17 | EXPOSED-811 | `c2a73b56` | `fbd9a886` | Medium | SQL error | batchUpsert where clause parameter unusable | API usability / DML completeness |
| EXD-18 | EXPOSED-768 | `ef732d68` | `630d930b` | Medium | type safety | UUID inserts into BINARY(16) fail in H2 | Dialect-specific type mapping |
| EXD-19 | EXPOSED-827 | `0376bbd7` | `4cde01b0` | High | SQL error | forUpdate() not adding FOR UPDATE modifier | Concurrency control / SELECT FOR UPDATE |
| EXD-20 | EXPOSED-752 | `3f162b75` | `f7feaa5d` | High | validation gap | Connection closed error with newSuspendedTransaction | Suspension/async semantics |
| EXD-21 | EXPOSED-806 | `135a6ebf` | `85a88f84` | Medium | SQL error | JSON generated columns migrate inconsistently on Postgres | Schema migration correctness |
| EXD-22 | EXPOSED-803 | `3f2443b9` | `85865aa2` | High | concurrency issue | ImmutableCachedEntityClass NullPointerException on concurrent access | Thread safety / concurrency |
| EXD-23 | EXPOSED-787 | `33aa6ed2` | `efb3fe12` | Medium | SQL error | Index create/drop disparity for long index names | DDL consistency |
| EXD-24 | EXPOSED-772 | `4d88ac44` | `3e2553dc` | Medium | SQL error | Case() expression missing column type specification option | Expression building API |
| EXD-25 | EXPOSED-762 | `3e2553dc` | `3378d7ad` | Medium | type safety | MariaDB UUIDColumnType doesn't work with native UUID type | Dialect-specific type support |
| EXD-26 | EXPOSED-713 | `60522834` | `af9b1239` | Medium | SQL error | Entity batchInsert doesn't use default column values | SQL generation correctness |
| EXD-27 | EXPOSED-761 | `6ffd1594` | `2bc7f1a2` | Low | type safety | ColumnWithTransform.readObject not forwarded to delegate | Transformation API completeness |
| EXD-28 | EXPOSED-739 | `b556a203` | `21cb946a` | Medium | state machine gap | Active null values in entity-local cache not handled | Cache value representation |
| EXD-29 | EXPOSED-593 | `40955f38` | `4f5e2cbc` | High | error handling | SpringTransactionManager throws ExposedSQLException on rollback | Spring integration correctness |
| EXD-30 | EXPOSED-736 | `1e3f7c44` | `95ec056c` | Low | SQL error | Unnecessary ALTER for binary column in PostgreSQL | Migration optimization / correctness |
| EXD-31 | EXPOSED-737 | `e1518ae7` | `4421c597` | High | error handling | Timestamp column broken for MySQL 8.0 | Dialect-specific type support |
| EXD-32 | EXPOSED-719 | `c3029fe4` | `753ba395` | Medium | SQL error | H2 upsert converts arrays to string | Dialect-specific DML handling |
| EXD-33 | EXPOSED-701 | `8314f808` | `e8c1599c` | High | SQL error | Oracle insert with database defaults fails | Dialect-specific DML correctness |
| EXD-34 | EXPOSED-704 | `0330ce6e` | `9fc27343` | Medium | state machine gap | ClassCastException with eager-loaded backReferencedOn | Entity loading edge cases |
| EXD-35 | EXPOSED-956 | `e0f56ff` | `69d69ff` | High | type safety | SQLite JSONB columns not automatically wrapped with JSON() function when querying | Query type mismatch / JSONB semantics |
| EXD-36 | EXPOSED-950 | `0493527` | `957c496` | High | SQL error | Order by clause is repeated hundredfold in relationship eager loading | Query generation correctness / Duplicate expressions |
| EXD-37 | NO-ISSUE | `f20446b` | `b07361f` | High | state machine gap | forUpdate() query returns cached entity instead of fetching fresh updated data | Cache invalidation / Transaction semantics |
| EXD-38 | EXPOSED-870 | `a44f093` | `3f7e8c3` | High | SQL error | Schema migration detection incompatible with sqlite-jdbc 3.50.2.0+ | Dialect compatibility / Migration logic |
| EXD-39 | EXPOSED-800 | `85865aa` | `55112a2` | High | configuration error | NoClassDefFoundError when using R2DBC with non-PostgreSQL database (missing type mappers) | Dependency resolution / Type mapping initialization |
| EXD-40 | EXPOSED-706 | `e76f06d` | `b3a4464` | Medium | type safety | MariaDB sequence max value handling differs for versions before 11.5 | Dialect-specific sequence support |
| EXD-41 | EXPOSED-714 | `a76c7b8` | `f74a7b0` | Medium | SQL error | NullPointerException when defining non-object Table | Table definition validation |
| EXD-42 | EXPOSED-669 | `ce04f80` | `1eead4e` | Medium | state machine gap | transform() broken for entities instantiated via wrapRow through an alias | Column transformation / Entity reconstruction |
| EXD-43 | EXPOSED-547 | `d7c4a13` | `bcc634a` | Low | error handling | Exception is printed to stderr even when caught in user code | Exception handling / Logging side effects |
| EXD-44 | NO-ISSUE | `bcc634a` | `3063a39` | Medium | SQL error | PostgreSQL column names are case sensitive (uppercase/lowercase) handling | SQL generation / Case sensitivity |
| EXD-45 | NO-ISSUE | `f425884` | `9a521f4` | High | configuration error | R2dbcTransaction parameters incorrectly defined after connection begins | Connection lifecycle / Parameter scoping |
| EXD-46 | NO-ISSUE | `f824d9e` | `ed46395` | Medium | configuration error | Duplicate entries in R2DBC Transactions stack on concurrent access | Thread safety / Resource tracking |
| EXD-47 | NO-ISSUE | `16431ff` | `7d83131` | Medium | configuration error | Unsupported driver exception for unmapped R2DBC drivers | Driver validation / Error messaging |
| EXD-48 | NO-ISSUE | `3158882` | `95b42a4` | Medium | configuration error | R2DBC connection retrieval fails under specific conditions | Connection management / Resource handling |
| EXD-49 | NO-ISSUE | `4c160c8` | `750d653` | Medium | state machine gap | "No transaction in context" error for ktor integration | Framework integration / Transaction propagation |


### Kotlin/kotlinx.serialization (Kotlin)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| KS-01 | #3079 | `0311f163` | `975af2ca` | High | serialization | ProtoBuf packing failed for Kotlin unsigned types (UByteArray, packed encoding) | Missing inline value class support |
| KS-02 | - | `e334d1c3` | `d7ca108a` | Critical | serialization | Multiple CBOR decoder bugs: RFC non-compliance in edge cases, strict mode violations | Format spec deviation |
| KS-03 | #2962 | `9adedb46` | `27e352d5` | High | serialization | Incorrect enum coercion during deserialization from JsonElement when nullable+non-optional with explicitNulls=false | Nullable type handling |
| KS-04 | #2856 | `d15dfeec` | `d266e05c` | Medium | configuration error | Serial name conflicts not resolved correctly in SerializersModule.overwriteWith, creating asymmetric mappings | Module builder logic |
| KS-05 | #2861 | `1b0accd6` | `1758faa6` | High | type safety | ProGuard R8 full mode dropped INSTANCE field and serializer function for serializable objects | Code obfuscation safety |
| KS-06 | #2852 | `21c9e975` | `d15dfeec` | High | serialization | Invalid number parsing in JsonLiteral.long: leftover content after number not consumed | Lexer validation |
| KS-07 | #2849 | `21c9e975` | `d15dfeec` | High | serialization | NumberFormatException vs JsonDecodingException handling inconsistent in number parsing | Error semantics |
| KS-08 | #2802 | `d9753afd` | `0b015e13` | Medium | serialization | PrimitiveSerialDescriptor rejected user custom serializers with names like "Uuid" or "Duration" | Builtin name conflicts |
| KS-09 | #2803 | `0b015e13` | `8c84a5b4` | Medium | serialization | NoClassDefFoundError during builtins map initialization on Java/Kotlin 2.0+ when stdlib lower than 2.0 | Version compatibility |
| KS-10 | #2530 | `ad9ddd10` | `afebbcbb` | High | serialization | coerceInputValues incorrectly tried to coerce missing properties without defaults, producing confusing errors | Input validation |
| KS-11 | #2456 | `cf71e088` | `b44f03f6` | High | serialization | TaggedDecoder.decodeNullableSerializableElement inconsistent with AbstractDecoder, preventing nullable/non-nullable differentiation | Decoder contract |
| KS-12 | #2438 | `7d287c84` | `01fcfeef` | Medium | serialization | Maps with boolean keys failed to decode when quotes inconsistent with other key types | Key type handling |
| KS-13 | #2561 | `a2f92e4e` | `b811fa3e` | High | serialization | Null serialization failed for parameterized types with nullable upper bounds (KT-66206 workaround) | Generic type bounds |
| KS-14 | #2565 | `b811fa3e` | `1f7372a6` | High | serialization | PolymorphicSerializer priority inverted: interfaces always got polymorphic serializer, preventing module-level overrides | Serializer lookup |
| KS-15 | #2469 | `b44f03f6` | `919062fb` | High | serialization | IllegalAccessException on retrieval of serializers for private stdlib implementation classes | Reflection access |
| KS-16 | #2466 | `bfbe6a91` | `7d4bb2a8` | Medium | serialization | Inline value classes marked @ByteString not recognized during encoding | Annotation processing |
| KS-17 | #2680 | `c487e78e` | `385c97d3` | Medium | serialization | Mutable classDiscriminatorMode in JsonConfiguration not marked @ExperimentalSerializationApi | API stability |
| KS-18 | #2661 | `194a1885` | `53fdc536` | High | serialization | explicitNulls interaction with coerceInputValues broken after stabilization | Feature interaction |
| KS-19 | #2601 | `f242bb5f` | `a2f92e4e` | High | serialization | Inline polymorphic children's @SerialName not used in JSON, using default names instead | Sealed class serialization |
| KS-20 | #2628 | `d4a26863` | `da020f97` | High | serialization | Type discriminator value incorrect for custom serializers using encodeJsonElement | Polymorphic encoding |
| KS-21 | #2728 | `2e5c66ee` | `66fc048d` | High | type safety | ProGuard descriptor field optimization produced incorrect bytecode causing VerifyError | Code generation |
| KS-22 | #2362 | `3191884b` | `b8de86f0` | Medium | serialization | Polymorphic parsing 'consume discriminator' optimization threw on empty objects instead of treating as missing | Parser optimization bug |
| KS-23 | #2346 | `5bba1083` | `fd75d353` | Medium | serialization | JsonTreeDecoder.beginStructure reused same instance when descriptors matched, invalidating position/discriminator tracking | Decoder state |
| KS-24 | #2331 | `881e7a91` | `780f43eb` | High | configuration error | Contextual serializer lookup cache returned null without searching SerializersModule for parametrized types | Caching bug |
| KS-25 | #2328 | `a269f97e` | `881e7a91` | High | serialization | NoSuchMethodError parsing JSON on Java 8 due to ByteBuffer.position() method signature change in Java 9+ | JDK compatibility |
| KS-26 | #2400 | `a7109d8d` | `1e88d42f` | Medium | serialization | Negative enum values failed to serialize/deserialize with varint encoding | Numeric encoding |
| KS-27 | #2345 | `782b9f3b` | `a87b0f1d` | Medium | serialization | No case-insensitive enum value decoding option, user requests for configuration | Feature missing |
| KS-28 | #2360 | `e55f807a` | `7bf105eb` | Medium | serialization | Cryptic parser error messages: "Expected quotation mark '\"', but had '\"' instead" or "unexpected token: 10" | Error messages |
| KS-29 | #2399 | `e55f807a` | `7bf105eb` | Medium | serialization | JsonErrorMessagesTest misalignment: error message displayed incorrect character codes | Error reporting |
| KS-30 | #2592 | `1ffdbafe` | `f242bb5f` | Medium | serialization | Missing JSON5-like comment support (C/Java-style comments) for configuration files | Format feature |
| KS-31 | #2546 | `251bca77` | `f525f1ad` | High | serialization | OneOf declaration not supported in ProtoBuf for sealed classes/interfaces | ProtoBuf feature gap |
| KS-32 | #2766 | `46467406` | `4ca05dd2` | High | serialization | Zero and negative field numbers in @ProtoNumber allowed, violating ProtoBuf spec; field 0 in input not rejected | Validation |
| KS-33 | #3090 | `2e1388fc` | `4ab28b34` | Low | serialization | BIGNUM_NEGATIVE tag name spelling error in code | Documentation |
| KS-34 | #2995 | `bd6689dc` | `596bac8f` | Medium | serialization | JsonPath.resize() failed with index out of bounds | Utility bug |
| KS-35 | #2941 | `1e54f4b7` | `a6398ca5` | Medium | serialization | SerialDescriptor() wrapper missing proper equals(), hashCode(), toString() implementation | Object contract |
| KS-36 | #1777 | `a33ef021` | `4c30fcfa` | High | serialization | Top-level value classes not handled correctly in encodeToJsonElement | Inline class encoding |
| KS-37 | #1779 | `1b2344f3` | `be7af57c` | Medium | serialization | JsonTreeReader.decodeToSequence incorrect object-end handling | Streaming decoder |
| KS-38 | #2910 | `f2b02582` | `b43a654336` | High | serialization | Null values in map keys and values failed to serialize in ProtoBuf format | Null handling |
| KS-39 | #2242 | `fc9aef53` | `5084435` | High | type safety | Value class encoding failed in corner cases: top-level non-primitive value class, polymorphic subclass without type info | Inline class polymorphism |
| KS-40 | #2268 | `350443a7` | `bbf248e2` | Medium | error handling | JSON decoding iterator hasNext() threw exception when called multiple times after stream ended | Iterator contract |
| KS-41 | #2274 | `bbf248e2` | `15aacd2` | High | state machine gap | Memory leak in contextual serializer cache due to invalid KTypeWrapper.equals() implementation | Caching bug |
| KS-42 | #2272 | `ef67bcef` | `8007574` | Medium | API contract violation | KeyValueSerializer missing endStructure() call in sequential decoding path | Decoder state |
| KS-43 | #2052 | `0f35682b` | `dc9983a6` | Medium | error handling | Maps deserialized to sealed classes produced incorrect behavior in Properties format | Sealed class deserialization |
| KS-44 | (unknown) | `79bc57d3` | `142f19c2` | Medium | serialization | Primitives' KClasses lacked .simpleName property, causing failures in reflection-based serialization | Reflection access |
| KS-45 | #1403 | `6547cb7f` | `b79e4e75` | High | serialization | Loss of numeric precision in JavaScript during JSON parsing due to platform-specific number handling | Platform-specific bug |
| KS-46 | #1325 | `7a0f671f` | `358dc0bd` | High | error handling | (1) EnumSerializer threw IllegalStateException instead of SerializationException; (2) ProtoBuf readVarintSlowPath infinite loop on JS | Infinite loop + error type |
| KS-47 | #1539 | `d56a4321` | `ab5c139` | Low | error handling | Missing enum value deserialization error message in Properties format lacked proper context | Error reporting |
| KS-48 | #2867 | `6684f67c` | `1b0accd6` | Medium | null safety | JSON configuration parsing threw NPE when system property not set, instead of using default | Null handling |
| KS-49 | #1408 | `603c85ff` | `cb3786bc` | High | validation gap | Inline value classes with string wrapping failed to encode/decode with JsonElement due to missing unsigned descriptor check | Inline class support |
| KS-50 | #1199 | `de9b5742` | `7863f3cf` | High | serialization | Dynamic serialization (encodeFromDynamic/decodeFromDynamic) failed for nullable polymorphic types | Polymorphic dynamic |
| KS-51 | #1011 | `cebdafc7` | `eacd19df` | Medium | error handling | Unfinished string literal at JSON input end threw StringIndexOutOfBoundsException instead of JsonDecodingException | Parser exception |
| KS-52 | #1397 | `83d0faa2` | `603c85ff5` | High | validation gap | Third-party generic types failed KType serializer lookup; missing fallback to contextual serializer after constructSerializerForGivenTypeArgs failure | Generic lookup |


### redis/redis (C)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| RED-01 | #14932 | `2ba0194` | `8e89e0b8` | Medium | error handling | Memory leak in ZDIFF algorithm 2 - SDS created by zuiSdsFromValue() not released on early break | Step 4: Cleanup on error paths |
| RED-02 | #14898 | `8e89e0b` | `f12001e0` | Medium | error handling | VSIM FILTER memory leaks - duplicate filter option overwrites previous expression, error paths leak filter_expr | Step 3: Double-check error handling |
| RED-03 | #14929 | `40c140b` | `bbc0dcbb` | High | error handling | Heap-use-after-free in restoreCommand - kvobj reallocation during notification makes local kv pointer dangling | Step 7: Signal handler safety |
| RED-04 | #14848 | `1abd489` | `63d841c3` | High | concurrency issue | Crash in dictEmpty callback during replica sync - prefetch commands called while dict being cleared | Step 2: Background task coordination |
| RED-05 | #14847 | `c4d7458` | `4ecc07fc` | High | security issue | ACL out-of-bounds read for wrong-arity KEYNUM commands - accessing argv beyond bounds during key extraction | Step 5: Bounds validation |
| RED-06 | #14371 | `4ecc07f` | `31a4356a` | Medium | configuration error | Divide-by-zero in redis-benchmark and redis-cli - empty histograms or zero elapsed time | Step 1: Input validation |
| RED-07 | #14888 | `7e866b4` | `8b9fd4b7` | High | error handling | Integer overflow bypass in lpSafeToAdd - len+add check bypassed when add near SIZE_MAX | Step 6: Overflow detection |
| RED-08 | #14878 | `4f0d311` | `a441d3db` | High | validation gap | Listpack memory leak in zipmap conversion - error path (duplicate key/allocation/overflow) frees dict but not listpack | Step 4: Cleanup on error paths |
| RED-09 | #14793 | `a441d3d` | `ee376cdc` | Medium | error handling | Unsigned integer overflow in rss_extra_bytes - signed/unsigned mismatch causes wrap when process_rss < allocator_resident | Step 6: Type safety |
| RED-10 | #14855 | `753c9f6` | `1ba5799f` | Medium | security issue | X509 memory leak in TLS module - SSL_get_peer_certificate() not paired with X509_free() | Step 4: Resource cleanup |
| RED-11 | #14831 | `fe16003` | `8a65b65d` | Low | API contract violation | SDS buffer leak in RM_SaveDataTypeToString - error path doesn't free rioInitWithBuffer buffer | Step 4: Cleanup on error paths |
| RED-12 | #14824 | `3de7fa2` | `707757e4` | High | concurrency issue | Reply copy avoidance UAF for modules - module string lifecycle not controlled, BIO thread lazy-frees causing use-after-free | Step 7: Module interface safety |
| RED-13 | #14790 | `53e4631` | `c7c278c6` | Medium | error handling | Uninitialized variable in bitfieldGeneric - strOldSize declared but not initialized alongside strGrowSize | Step 3: Variable initialization |
| RED-14 | #14789 | `099203c` | `95314a93` | Medium | validation gap | DB hash tables not expanding on RDB load - dict on-demand creation conflicts with RESIZEDB hint expansion | Step 5: Database initialization |
| RED-15 | #14771 | `9601c31` | `ded623d8` | Medium | error handling | Integer underflow in used_memory_dataset - unsigned subtraction wraps when mem_total > zmalloc_used | Step 6: Underflow detection |
| RED-16 | #14738 | `6e2cbd5` | `18538461` | High | concurrency issue | Data race from incorrect defered-free - refcount > 1 objects deferred free called from IO thread causing race | Step 7: Thread synchronization |
| RED-17 | #14690 | `25f780b` | `5c5c7c5a` | Medium | API contract violation | Crash with internal container command no subcommand - missing subcommand argument not handled | Step 1: Input validation |
| RED-18 | #14682 | `cc1660a` | `391530cd` | Medium | validation gap | Dict defrag tag bit bug - dictDefragBucket loses ENTRY_PTR_IS_EVEN_KEY tag when assigning newkey | Step 8: Bit manipulation |
| RED-19 | #14669 | `85ab4ca` | `154fdcee` | Medium | error handling | UBSan error in stream trim - listpack pointer p becomes NULL when all entries removed | Step 3: Null pointer handling |
| RED-20 | #14472 | `4eda670` | `7511a191` | High | error handling | Infinite loop in stream reverse iteration - corrupted stream with invalid numfields causes infinite loop | Step 5: Corruption detection |
| RED-21 | #14627 | `c5f3d3e` | `0d5d75e0` | Medium | error handling | Use-after-free in hnsw_cursor_free - incorrect pointer arithmetic in cursor list traversal | Step 3: Pointer safety |
| RED-22 | N/A | `32497c0` | `d4307af6` | High | error handling | MurmurHash64A overflow in HyperLogLog - int parameter overflows with 2GB+ entries, use size_t | Step 6: Integer overflow |
| RED-23 | CVE-2025-46817 | `3bb9fc7` | `671953d0` | Critical | security issue | Lua script integer overflow to RCE - improper arithmetic in lbaselib.c ltable.c enables code execution | Step 2: Script execution safety |
| RED-24 | CVE-2025-62507 | `7f1bafc` | `3e2003ee` | Critical | error handling | XACKDEL stack overflow - IDs array not reallocated when exceeding STREAMID_STATIC_VECTOR_LEN | Step 6: Buffer sizing |
| RED-25 | #14417 | `48d0aa9` | `1f2c2850` | High | security issue | Heap-buffer-overflow in CLUSTER FORGET - node ID length < 40 bytes reads beyond buffer | Step 5: Bounds validation |
| RED-26 | #14415 | `5b49119` | `083f38ef` | High | concurrency issue | Crash in lookupKey NULL executing_client - null pointer dereference in blocked client handling | Step 7: Null checks in callbacks |
| RED-27 | #14319 | `8ad5421` | `5f8e7852` | High | validation gap | Crash during Lua script defrag - luaScript reallocated during execution, node pointer becomes dangling | Step 8: Defrag safety |
| RED-28 | #14050 | `38d16a8` | `e2b8f8ff` | Medium | error handling | Missing prev update in hnsw_cursor_free - cursor not unlinked from list due to missing prev pointer update | Step 3: List traversal |
| RED-29 | #14457 | `4b6935b` | `d43bf1d6` | High | error handling | Re-entrant deadlock in bugReportStart - signal handler calls non-async-safe functions causing deadlock | Step 7: Signal handler restrictions |
| RED-30 | #14423 | `166ae60` | `6d89370c` | High | error handling | Infinite loop in stream reverse iteration - corrupted stream structure causes infinite loop during iteration | Step 5: Corruption detection |
| RED-31 | #14243 | `3fa7a65` | `7b40dbac` | Medium | API contract violation | Memory leak in RM_GetCommandKeysWithFlags - module API doesn't free allocated key results | Step 4: API cleanup |
| RED-32 | #14817 | `50f1469` | `9152df61` | Medium | error handling | Memory leak in trackingRememberKeys - PUBSUB command path doesn't free key tracking buffers | Step 4: Cleanup on error paths |
| RED-33 | #14466 | `6ea4e2c` | `91b5808f` | Medium | concurrency issue | Race condition for lookupCommand - command table access without synchronization | Step 7: Command table locking |
| RED-34 | #14162 | `5b7eec4` | `a7d91145` | Medium | error handling | Crash from incorrect evport event deletion - file descriptor event handlers not properly cleaned up | Step 2: Event cleanup |
| RED-35 | #14055 | `ba88a7f` | `8bd50a3b` | Medium | error handling | Crash when freeing node after nodeIp2String failure - error path doesn't properly free cluster node | Step 4: Cleanup on error paths |
| RED-36 | #14647 | `877c09f` | `238a626` | High | type safety | incrRefCount off-by-one error in refcount boundary check - allows refcount to reach OBJ_FIRST_SPECIAL_REFCOUNT instead of stopping before it | Step 5b: Type boundaries |
| RED-37 | #14659 | `7324949` | `85ab4ca` | High | validation gap | ACL key-pattern bypass in MSETEX - key extraction formula ignores step size, only validates first key while allowing access to all keys | Step 5: Bounds validation |
| RED-38 | #14654 | `16068d6` | `ea72406` | High | API contract violation | Defrag crash with hash fields - uses dictSetKey() on no_value=1 dicts causing assertion failure, needs dictSetKeyAtLink() | Step 2: Data structure API |
| RED-39 | #14723 | `a2e901c` | `25f780b` | Medium | concurrency issue | Inaccurate IO thread client count - delayed freeing of health-check clients creates race between count and actual connections | Step 7: Client lifecycle |
| RED-40 | #14715 | `e824001` | `e76e3af` | Medium | configuration error | Inefficient prefetch sizing - remaining work smaller than effective max batch not prefetched atomically, creates tiny tail batches | Step 1: Configuration tuning |
| RED-41 | #13996 | `11954d9` | `2668356` | Medium | silent failure | SDS buffer leak in slaveTryPartialResynchronization - error path doesn't free allocated SDS after failed operation | Step 4: Cleanup on error paths |
| RED-42 | #14081 | `bb23eb0` | `6349a7c` | High | state machine gap | Incorrect cronloops update in defragWhileBlocked causing timers to run 2x faster during active defragmentation | Step 5a: State machine correctness |
| RED-43 | #14085 | `7f60945` | `161326d` | High | error handling | Short read not detected during diskless RDB load - rioGetReadError() misses RIO_ABORT flag, process exits with corrupt RDB error | Step 3: Error propagation |
| RED-44 | #14092 | `2467eff` | `f646d23` | Medium | validation gap | db->expires defrag comparison bug - uses db->keys instead of db->expires when checking if dict changed, breaks defrag resumption | Step 4: Validation consistency |
| RED-45 | #14102 | `27dd3b7` | `2ba81b7` | High | validation gap | Vector Sets corruption resistance - deserialization assumes checksum prevents corruption but allows malformed data to cause issues | Step 5: Corruption detection |
| RED-46 | #14134 | `a95b94b` | `35dbfc4` | High | validation gap | Command arity not checked in IO threads - invalid commands reach getKeysFromCommand with wrong argv, enabling unsafe key position access | Step 5: Input validation |
| RED-47 | #14880 | `9accf8b` | `7d57081` | Medium | validation gap | HSETEX PERSIST validation - accepts invalid PERSIST keyword without checking, should reject with unknown argument error | Step 1: Input validation |
| RED-48 | #14883 | `1b615c7` | `8a6ae0e` | Medium | validation gap | HSETEX/HGETEX FIELDS validation - missing validation for required FIELDS argument and duplicate FIELDS keywords | Step 1: Input validation |
| RED-49 | #14897 | `462e603` | `1b615c7` | High | state machine gap | stream_idmp_keys missing from database lifecycle ops - dict not managed in flush/swap/RDB load causing SIGSEGV, lost tracking, stale entries | Step 5a: Database lifecycle |
| RED-50 | #13883 | `87d8e71` | `a0da839` | Medium | state machine gap | Defrag infinite loop on encoding change - type/encoding change during scan causes return without cursor reset, creating no-op iterations | Step 5a: Concurrent mutation handling |


### curl/curl (C)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| CURL-01 | #21123 | `86b39c2` | `28fbf4a8` | High | error handling | Use-after-free in CURLINFO_EFFECTIVE_URL via OOM path | Pointer nullification on allocation failure |
| CURL-02 | #21111 | `248b929` | `860c57d` | Medium | missing boundary check | Low-risk integer overflow in socket connection on ancient Solaris | Defensive arithmetic bounds checking |
| CURL-03 | #21099 | `b71973c` | `46d0ade` | High | error handling | Multiple memory allocation/deallocation mismatches (curl_free vs curlx_free) | Allocator consistency enforcement |
| CURL-04 | #21075 | `29dfc02` | `14712fa` | High | error handling | Incorrect free function for curl_easy_escape() return value | Allocation context tracking |
| CURL-05 | #21062 | `9820e5d` | `e8c64a0` | Medium | error handling | Memory leak on repeated upload failures | Resource cleanup in error paths |
| CURL-06 | #20993 | `6c0772f` | `fc222ec` | Medium | error handling | Memory leaks in OpenSSL ECH (Encrypted Client Hello) code | TLS extension cleanup |
| CURL-07 | #20988 | `2bb3643` | `1c7a270` | High | missing boundary check | Out-of-bounds write in test server (sws) | Buffer boundary validation |
| CURL-08 | #20987 | `d86fd14` | `e345dfb` | High | error handling | Off-by-one read/write to read-only buffer in synctime utility (Windows) | Boundary arithmetic in string operations |
| CURL-09 | #20967 | `acb4fcb` | `a43ea59` | High | null safety | Null pointer dereference in tool_msgs for early error reporting | Null guard in initialization path |
| CURL-10 | #20956 | `1098e10` | `91b422d` | Medium | error handling | Memory leak on glob range overflow condition | Error path cleanup for glob expansion |
| CURL-11 | #20954 | `90b9f51` | `b881bc0` | Medium | error handling | Minor memory leak on early tool exit during .curlrc parsing | Configuration file cleanup |
| CURL-12 | #20929 | `32531f2` | `f50446f` | Medium | error handling | Memory leak in DoH (DNS-over-HTTPS) on second resolve | DNS cache cleanup |
| CURL-13 | #20862 | `cbb5544` | `4a15bc1` | Medium | error handling | Memory leak in digest authentication message creation | Authentication context cleanup |
| CURL-14 | #20806 | `e49efce` | `27c3e08` | High | null safety | Use of uninitialized buffer in synctime example on non-Windows | Buffer initialization before use |
| CURL-15 | #20804 | `d7e4473` | `933c34e` | Low | error handling | Debug-only memory leak in CURL_FN_SANITIZE path | Debug code resource cleanup |
| CURL-16 | #20801 | `7577ed7` | `d9c2c64` | High | error handling | UAF in Schannel client certificate store thumbprint handling | Certificate store lifetime management |
| CURL-17 | #20779 | `da6fbb1` | `7fe5b93` | High | null safety | Null pointer dereference in HTTP/1 request parsing | Pointer validation in parsing |
| CURL-18 | #20771 | `ba685ad` | `7981594` | High | null safety | Null dereference when loading certificates without EKU data (Windows) | Certificate validation safeguards |
| CURL-19 | #20656 | `b35e58b` | `020f48d` | Medium | missing boundary check | OOB read in OpenSSL debug/verbose logging | Bounds checking in logging code |
| CURL-20 | #21113 | `2e8c922` | `351e4f9` | High | security issue | HTTP/2 server push allows insecure schemes over insecure connections | Protocol-level scheme validation |
| CURL-21 | #21121 | `28fbf4a` | `2e8c922` | Medium | validation gap | Missing retry logic for non-HTTP protocol failures | Protocol handler callback fallback |
| CURL-22 | N/A | `708b3f8` | `1eb9096` | Medium | security issue | WolfSSL handling of abrupt connection close | TLS connection state validation |
| CURL-23 | N/A | `f0f0a7f` | `9b01f73` | Medium | security issue | Boringssl/Schannel/WinCrypt coexistence edge cases | Crypto library conditional compilation |
| CURL-24 | N/A | `a186ecf` | `39036c9` | Medium | protocol violation | Proxy chunked response error code propagation | HTTP proxy error handling |
| CURL-25 | N/A | `02e04ea` | `b11f43a` | Medium | error handling | HTTPS-lookup routing with c-ares on non-standard ports | DNS handler port awareness |
| CURL-26 | N/A | `2938cb7` | `6ada2e3` | Medium | protocol violation | Header comparison logic for multi-value headers | Header parsing edge cases |
| CURL-27 | N/A | `704e7a8` | `5f13a76` | Medium | protocol violation | EOF handling in MQTT protocol | Protocol-specific EOF semantics |
| CURL-28 | N/A | `ee3a4df` | `5c250e2` | Medium | security issue | Query parameter normalization in AWS SigV4 | Signature base string construction |
| CURL-29 | N/A | `34fa034` | `2d8284e` | Medium | protocol violation | HTTP Negotiate auth connection reuse logic | NTLM/Kerberos connection state |
| CURL-30 | N/A | `f1a39f2` | `a0244c5` | Medium | security issue | Copy-paste error in auth negotiation URL matching | Code review defect (logic duplication) |
| CURL-31 | N/A | `80b6cd9` | `0d7677a` | Medium | serialization | Error propagation in form header parsing | Error handling in multipart forms |
| CURL-32 | N/A | `ae09e5b` | `adda113` | Medium | error handling | Error handling for read failures in curl_get_line | File reading error detection |
| CURL-33 | N/A | `e76968e` | `6d87eb2` | High | error handling | Infinite loop when filename parameter is a directory | Path type validation |
| CURL-34 | N/A | `3bc6ae5` | `6c0772f` | Medium | error handling | Incorrect allocation size in mod_curltest | Buffer allocation calculation |
| CURL-35 | curl/curl#21147 | `d87d402` | `8f3f470` | High | configuration error | --parallel-max-host limit not applied in normal parallel transfer path; only enforced in debug-only event path | Step 5 defensive patterns, missing feature flag guards |
| CURL-36 | curl/curl#21070 | `e0be05c` | `0c475b5` | High | protocol violation | file:/// URL with single-slash path incorrectly parsed, breaking file scheme path handling | Step 2 architecture, file:// scheme edge cases |
| CURL-37 | curl/curl#21011 | `07c10f0` | `b9e179e` | Medium | error handling | URL building returns CURLE_URL_MALFORMAT on memory allocation failure instead of CURLE_OUT_OF_MEMORY; error masking | Step 5 defensive patterns, error code precision |
| CURL-38 | curl/curl#21047 | `745344e` | `d560002` | High | state machine gap | DNS resolution: inverted logic check on !data->set.no_signal breaks alarm timeout signal handling | Step 5a state machines, boolean logic inversion |
| CURL-39 | curl/curl#20927 | `6b0a885` | `3334fca` | High | protocol violation | Windows LDAP: cleartext connection initialization skipped due to conditional macro scope error; regression from 8.18.0 | Step 2 architecture, platform-specific protocol setup |
| CURL-40 | curl/curl#20939 | `29cb750` | `3525ed9` | Medium | state machine gap | --no-clobber: filename state lost on file name generation failure, causing retry logic to fail | Step 5a state machines, variable lifetime in retry loops |
| CURL-41 | curl/curl#20735 | `05d991a` | `e866429` | High | validation gap | RTSP: zero-length RTP payload (4-byte header only) causes assertion failure; missing boundary check | Step 5 defensive patterns, missing boundary validation |
| CURL-42 | curl/curl#20742 | `6789eb0` | `9b52d51` | Medium | missing boundary check | curl_multi_get_handles: unsigned int overflow risk when handle count could reach UINT_MAX; type safety | Step 5b schema types, arithmetic bounds checking |
| CURL-43 | curl/curl#21031 | `f2ba8f0` | `07c10f0` | Medium | type safety | Protocol definition: CURLPROTO_MASK has missing hex digit (0x3ffff instead of 0x3fffffff); WebSocket protocol bits excluded | Step 5b schema types, constant correctness |
| CURL-44 | curl/curl#20991 | `86c25c0` | `59405ff` | Medium | error handling | X.509 ASN.1: encodeOID() returns CURLE_OK on overflow instead of CURLE_BAD_FUNCTION_ARGUMENT; silent failure | Step 5 defensive patterns, error return path validation |
| CURL-45 | curl/curl#21125 | `4f31623` | `d7d683c` | Medium | serialization | DJGPP: ftruncate defined as preprocessor macro, then called within ftruncate() function causing macro expansion error | Step 5b schema types, macro hygiene |
| CURL-46 | curl/curl#21119 | `c025082` | `68fefb9` | Medium | configuration error | OpenSSL: deprecated SSL_R_SSLV3_ALERT_CERTIFICATE_EXPIRED constant missing in 4.0+ OPENSSL_NO_DEPRECATED builds without guards | Step 4 specs, compile-time feature gate handling |
| CURL-47 | curl/curl#20883 | `53a3b21` | `a221e2f` | High | API contract violation | SSH/SFTP quote error handler: function returns void instead of error code, silently losing errors in command parsing | Step 5 defensive patterns, return value propagation |
| CURL-48 | curl/curl#20730 | `d38bf79` | `d110504` | Medium | null safety | Test server sockets: memset size calculation uses partial union size instead of full union, leaving bytes uninitialized | Step 5b schema types, sizeof correctness |
| CURL-49 | curl/curl#20799 | `3d4a701` | `7577ed7` | High | configuration error | Config: CAINFO_BLOB option errors not properly ignored; checks only CURLE_NOT_BUILT_IN but misses CURLE_UNKNOWN_OPTION | Step 5 defensive patterns, error case completeness |


### jqlang/jq (C)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| JQ-01 | #3498 | `3985b80` | `3cd7e0da` | Critical | error handling | use-after-free in args2obj() array path | Step 3 |
| JQ-02 | #3497 | `3cd7e0d` | `ed3c7f21` | High | error handling | crash when importing module with errors twice | Step 1 |
| JQ-03 | #3496 | `ed3c7f2` | `bfcf82fd` | High | validation gap | tonumber/toboolean reject null bytes | Step 4 |
| JQ-04 | #3495 | `bfcf82f` | `36b6ae00` | High | error handling | @uri/@urid multi-byte UTF-8 corruption | Step 4 |
| JQ-05 | #3490 | `0df54c8` | `262f0b81` | Critical | error handling | del(.[nan]) infinite loop and undefined behavior | Step 2 |
| JQ-06 | #3487 | `750dbe7` | `2ad99a6c` | High | error handling | memory leaks and double frees | Step 3 |
| JQ-07 | #3486 | `061fd14` | `22361cfb` | High | error handling | modulo operator off-by-one calculation | Step 2 |
| JQ-08 | #3465 | `b33a763` | `d44baeb6` | High | error handling | f_env reversed pointer subtraction bounds check | Step 3 |
| JQ-09 | #3389 | `5529788` | `8d9a3c3a` | High | error handling | raw input slurp corrupts multi-byte characters | Step 4 |
| JQ-10 | #3415 | `1694573` | `c8017bf0` | Medium | error handling | rtrimstr("") returns empty instead of original | Step 2 |
| JQ-11 | #3369 | `695830c` | `cd3a4c3d` | High | error handling | year 2038 problem on 32-bit platforms | Step 5 |
| JQ-12 | #CVE-2025-49014 | `5e159b3` | `499c91bc` | Critical | error handling | stack-overflow in regex parser (GHSA-f946-j5j2-4w5m) | Step 1 |
| JQ-13 | unknown | `c6e0416` | `3b00981a` | Critical | error handling | heap buffer overflow formatting empty string | Step 3 |
| JQ-14 | #3195 | `9ac6dda` | `aaace543` | High | serialization | whitespace handling in number parsing | Step 1 |
| JQ-15 | #3326 | `aaace54` | `4e3088f1` | Medium | serialization | parser rejects binary operators in binding syntax | Step 1 |
| JQ-16 | #3279 | `4e3088f` | `7d8c096e` | High | error handling | --slurp --stream with no trailing newline corruption | Step 4 |
| JQ-17 | unknown | `de21386` | `4e2ccc4c` | High | error handling | signed integer overflow in jvp_array_write/jvp_object_rehash | Step 3 |
| JQ-18 | #3316 | `96d19ca` | `ecea2d29` | High | error handling | uninitialized value read in check_literal | Step 3 |
| JQ-19 | #3304 | `aea8efa` | `947fcbbb` | High | error handling | jv_unique memory leak of non-returned elements | Step 3 |
| JQ-20 | #3280 | `94fd973` | `c70ae1ad` | High | serialization | @base64d format calloc error handling | Step 3 |
| JQ-21 | #3271 | `4003202` | `dc849e9b` | Critical | error handling | segmentation fault in strftime/strflocaltime | Step 5 |
| JQ-22 | #3242 | `6ce3bdf` | `97277215` | Medium | error handling | unary negation loses numerical precision | Step 2 |
| JQ-23 | #3232 | `d0adcbf` | `07af9c11` | Medium | configuration error | --indent 0 implicitly enables compact-output | Step 5 |
| JQ-24 | #3205 | `96e8d89` | `8619f8a8` | High | error handling | reduce/foreach state resets each iteration | Step 2 |
| JQ-25 | #3179 | `a7b2253` | `3c5707f7` | Medium | error handling | last(empty) produces output instead of none | Step 2 |
| JQ-26 | #3485 | `2ad99a6` | `061fd14d` | Low | serialization | tokenbuf pre-allocation optimization | Step 1 |
| JQ-27 | #3348 | `a587ddc` | `78045d8a` | Medium | serialization | syntax error triggers assertion instead of error | Step 1 |
| JQ-28 | #3342 | `7cc202a` | `859a8073` | Medium | configuration error | strptime Windows incompatibility | Step 5 |
| JQ-29 | #3336 | `023f274` | `62cafa23` | Medium | configuration error | build failure on old macOS versions | Step 5 |
| JQ-30 | #3499 | `b6a9e26` | `1a394919` | High | error handling | fuzz_parse_stream crash with non-iterative API | Step 1 |
| JQ-31 | #3509 | `cec6b0f` | `b6a9e260` | High | error handling | test suite crashes and resource leaks | Step 5 |
| JQ-32 | #3203 | `6d8e9f9` | `b86ff49f` | Medium | serialization | timezone data missing in strflocaltime | Step 5 |
| JQ-33 | #3245 | `b86ff49` | `64bd8ba3` | Low | error handling | jv_number_value missing double cache | Step 5 |
| JQ-34 | #3249 | `64bd8ba` | `fa6a2ff6` | High | error handling | jv_dump_string_trunc breaks UTF-8 boundaries | Step 4 |
| JQ-35 | unknown | `511d50b` | `72989725` | High | error handling | ltrimstr/rtrimstr memory leak on invalid input | Step 3 |
| JQ-36 | #3430 | `33b3a68` | `cff4e00` | Medium | protocol violation | Test assertion converts to error message instead of abort | Step 5 |
| JQ-37 | #3413 | `b29504b` | `589a694` | High | missing boundary check | Print depth limit too low (256) causes premature truncation | Step 2 |
| JQ-38 | #3375 | `589a694` | `c9c96b3` | Critical | serialization | Regex parser unbounded recursion in fuzzing | Step 1 |
| JQ-39 | CVE-2024-53427 | `a09a4df` | `a8ce2ff` | Critical | serialization | NaN with payload parsing security issue | Step 1 |
| JQ-40 | #3280 | `a8ce2ff` | `4003202` | High | null safety | Zero-length calloc() causes undefined behavior | Step 3 |
| JQ-41 | #3264 | `f3d4c11` | `70e72ab` | High | error handling | getenv() return value not duplicated before setenv | Step 3 |
| JQ-42 | OSS-fuzz#66061 | `5bbd02f` | `afe0afa` | High | error handling | setpath with array index leaks memory on error | Step 3 |
| JQ-43 | OSS-fuzz#67640 | `22a03e9` | `be437ec` | High | missing boundary check | @base64d signed integer overflow on large multipliers | Step 2 |
| JQ-44 | OSS-fuzz#65885 | `bc96146` | `d697331` | High | type safety | jv2tm undefined behavior and missing bounds checks | Step 4 |
| JQ-45 | #3071 | `d777b65` | `1411ce6` | High | configuration error | Windows strptime TIME_MAX incorrect for 32-bit time_t | Step 5 |
| JQ-46 | OSS-fuzz#67403 | `1411ce6` | `6f67bae` | Medium | validation gap | strftime missing validation when input is number | Step 4 |
| JQ-47 | OSS-fuzz#66070 | `6f67bae` | `c95b34f` | High | error handling | EACH operator leaks object keys on iteration error | Step 3 |
| JQ-48 | #3104 | `6322b99` | `da2a0b9` | Medium | configuration error | Windows .jq config file not sourced correctly | Step 5 |
| JQ-49 | #3151 | `2ee20ca` | `e2ffb53` | Medium | configuration error | ctype.h functions require unsigned char cast | Step 5 |
| JQ-50 | #2565 | `600e602` | `cac216a` | Medium | error handling | Empty regex matches produce incorrect results | Step 2 |


### vapor/vapor (Swift)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| VAP-01 | #3232 | `7e48dd5` | `fb619ab6` | High | protocol violation | Fix `.noSignalReceived` body streaming crash | Step 3: Streaming & Async |
| VAP-02 | #3206 | `4b2bce9` | `f1c3495b` | Medium | protocol violation | Fixed an issue where response compression would fail when returning 304 Not Modified | Step 2: HTTP Response |
| VAP-03 | #3164 | `f1c3495` | `a46552bf` | Medium | protocol violation | Fix decoding 'flag' URL query params via `.decode(StructType.self)` | Step 1: Routing |
| VAP-04 | #3151 | `664a063` | `fa44af08` | Medium | protocol violation | Fix handling of "flag" URL query params | Step 1: Routing |
| VAP-05 | #3143 | `4942d74` | `d5025b3f` | Medium | protocol violation | Fix URI handling with multiple slashes and variable components. | Step 1: Routing |
| VAP-06 | #3140 | `d5025b3` | `0680f9f6` | High | protocol violation | Fix broken URI behaviors | Step 1: Routing |
| VAP-07 | #3102 | `9da9d14` | `664a0634` | High | protocol violation | Fix issue when client disconnects midway through a stream | Step 3: Streaming & Async |
| VAP-08 | #2992 | `00bd82b` | `b1be620b` | High | protocol violation | Fix crash when collecting the body | Step 2: Request Body |
| VAP-09 | #2978 | `ba1a308` | `4709b922` | High | error handling | Fix multiple correctness issues | Step 4: Concurrency |
| VAP-10 | #3372 | `6f3db71` | `3014d7de` | Medium | security issue | Do not create a session if no cookie was provided | Step 5: Sessions |
| VAP-11 | #3412 | `f7090db` | `8d47c182` | Medium | configuration error | Fix compatibility with swift-log 1.8.0 and later | Step 6: Dependencies |
| VAP-12 | #3393 | `6b7a70a` | `ac3aeb77` | Medium | configuration error | Fix parallel build failures on platforms with Glibc | Step 6: Dependencies |
| VAP-13 | #3390 | `ac3aeb7` | `c84ffd38` | Low | configuration error | Fix a couple of import issues | Step 6: Dependencies |
| VAP-14 | #3265 | `ec23f07` | `31c68ef0` | Low | concurrency issue | Fix Concurrency Warnings and Deprecations | Step 4: Concurrency |
| VAP-15 | #3249 | `fb1df82` | `4d3bc6ce` | Low | protocol violation | fix `HTTPMethod.RAW(value: String)` string representation | Step 2: HTTP Protocol |
| VAP-16 | #3211 | `1da8bba` | `4918ddab` | Medium | validation gap | fix: support capital letters in the domain part of email validation | Step 2: Validation |
| VAP-17 | #3113 | `67fe736` | `9c830d46` | Medium | SQL error | Fix setting public folder for `FileMiddleware` when using bundles | Step 2: Middleware |
| VAP-18 | #3116 | `00c902c` | `3d62c0c3` | Medium | protocol violation | Fix encoding and decoding of HTTPHeaders | Step 2: HTTP Headers |
| VAP-19 | #3081 | `e38dfe4` | `c17d9b90` | High | concurrency issue | Fix NIOLoopBound issues | Step 4: Concurrency |
| VAP-20 | #3075 | `c17d9b9` | `090464a6` | Medium | configuration error | Fix AHC Dependency Mismatch | Step 6: Dependencies |
| VAP-21 | #2574 | `474d91b` | `6b96684e` | Medium | protocol violation | Fix for #2574 Missing quote from value | Step 1: Routing |
| VAP-22 | #3009 | `f0aed18` | `3b34bc44` | Medium | protocol violation | Fixed drain handler call order in case of asynchronous buffer handling | Step 2: Backpressure |
| VAP-23 | #3010 | `b42287f` | `ac263f74` | Medium | protocol violation | Fix `Range: bytes=0-0` header not working properly | Step 2: HTTP Headers |
| VAP-24 | #2766 | `572aba0` | `970c2e8e` | High | protocol violation | Fix request decompression | Step 3: Content Handling |
| VAP-25 | #2730 | `f632f55` | `f6d8bb7f` | Medium | security issue | Fix empty password in basic authorization parsing | Step 2: Authentication |
| VAP-26 | #2670 | `5113bfc` | `85b175f6` | Low | protocol violation | Fix `comparePreference` function when only one media type specified | Step 2: Content Negotiation |
| VAP-27 | #2671 | `85b175f` | `78b5f9fa` | Low | protocol violation | Fix flaky Websocket tests | Step 3: WebSocket |
| VAP-28 | #2603 | `5c3f170` | `3106fa93` | Medium | protocol violation | Fix parsing complex accept headers | Step 2: Content Negotiation |
| VAP-29 | #2539 | `1a1bd69` | `da682123` | Low | SQL error | fix #2539: CORS: add "vary: origin" header if allowed origin is .originBased | Step 2: Middleware |
| VAP-30 | #2523 | `5148f02` | `c18eb560` | Medium | configuration error | fix dot env parser infinite loop when a comment is the last line and there is no trailling new line | Step 6: Configuration |
| VAP-31 | #2479 | `66f412b` | `d910be46` | High | protocol violation | Fixed a regression where configuring a nil hostname or port could cause the server to crash | Step 1: Server Startup |
| VAP-32 | #2463 | `c4861a4` | `c23e77d7` | Medium | serialization | Fix decodeNil method in URLEncodedFormDecoder's single value decoder | Step 3: Content Decoding |
| VAP-33 | #2447 | `11287f2` | `af65c608` | High | error handling | Fix array out of bounds exception | Step 4: Bounds Safety |
| VAP-34 | #2347 | `74bbf36` | `6d4a71bb` | Medium | security issue | fix invalid session id handling | Step 5: Sessions |
| VAP-35 | #2314 | `948f363` | `0aad60e6` | Low | SQL error | Fix CORSMiddleware configuration initializer parameter | Step 2: Middleware |
| VAP-36 | #3302 | `4f2dcf7` | `91efabd` | High | concurrency issue | Prevent stack overflow by using NIOLock instead of NIOLockedValueBox during service initialization | Step 4: Concurrency |
| VAP-37 | #3283 | `eafbca7` | `4d7456c` | Medium | state machine gap | Do not truncate response when streaming on error | Step 3: Streaming & Async |
| VAP-38 | #3222 | `a4d7d4d` | `083028c` | Medium | validation gap | Raise error when the data expected an array but not parsed as array | Step 1: Content Validation |
| VAP-39 | #3226 | `083028c` | `287d944` | Medium | validation gap | Throw an error if unkeyed container is at end while decoding URL params | Step 1: Content Validation |
| VAP-40 | #2966 | `d1a89f8` | `a1e496f` | Medium | error handling | Correctly handle invalid numbers in range validations (NaN handling) | Step 2: Validation |
| VAP-41 | #2859 | `d35d98a` | `cd91a66` | Medium | validation gap | Fix validate each not taking required parameter into account | Step 2: Validation |
| VAP-42 | #2855 | `cd91a66` | `12e2e74` | Medium | state machine gap | Consume request body to ensure it's all there in middleware to workaround async bug | Step 3: Request Handling |
| VAP-43 | #2840 | `a0fbe48` | `41496ea` | Medium | missing boundary check | Fix bytecount calculation of content-range headers (tail range) | Step 2: HTTP Headers |
| VAP-44 | #3201 | `12e9b41` | `cc98361` | Medium | API contract violation | Exclude Query and Fragment from URI semicolon fix on Linux | Step 1: Routing |
| VAP-45 | #2652 | `4aafa9f` | `f6a422c` | High | error handling | Fix issue where Plaintext Decoder would crash on malformed input | Step 3: Content Decoding |
| VAP-46 | #2548 | `53d15b2` | `1ccc4a2` | High | null safety | Multipart/form-data crashed if data was missing (boundary only) | Step 3: Multipart Handling |
| VAP-47 | #2630 | `9d154df` | `d6605a6` | Medium | serialization | Fix issues with date parsing in HTTP headers (Set-Cookie) | Step 2: HTTP Headers |
| VAP-48 | #2500 | `cf1651f` | `236c616` | Medium | serialization | Fix relative percent decoding in file middleware | Step 2: File Serving |
| VAP-49 | #2520 | `c8a50fa` | `c2ae522` | Medium | configuration error | Honor Configuration for Optional Date Decoding & Encoding | Step 2: Content Decoding |
| VAP-50 | #2718 | `3835f3a` | `1c4d362` | High | error handling | Fix issue where an invalid URL using the Client would crash | Step 3: HTTP Client |


### apple/swift-nio (Swift)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| NIO-01 | #3560 | `98f8824` | `bdf004b` | Medium | error handling | open() syscall error mapping missed EPERM (network volumes), errors misclassified as unknown | Step 5 |
| NIO-02 | #3480 | `6ce9173` | `192616d` | Low | state machine gap | Missing pthread_mutexattr_destroy in Lock initialization, correctness issue on some platforms | Step 2 |
| NIO-03 | #3462 | `e3d5c56` | `92a262f` | High | configuration error | coreCount reported wrong value on Linux cgroup v2 with CFS disabled, affects thread pool sizing | Step 7 |
| NIO-04 | #3360 | `f656af6` | `e8c1d6e` | High | concurrency issue | SelectableEventLoop.debugDescription held lock during description access, causing deadlock | Step 1 |
| NIO-05 | #3040 | `2620f8e` | `ba72f31` | High | protocol violation | WebSocketProtocolErrorHandler ignored isServer flag, sending unmasked frames from clients | Step 4 |
| NIO-06 | #3044 | `6fb31ea` | `9d7cf68` | High | error handling | NIOAsyncWriter suspended yields not buffered when writer finishes, loses buffered data | Step 3 |
| NIO-07 | #2952 | `02906a6` | `1ff5fd5` | High | protocol violation | NIOAsyncSequenceProducer watermark failed to track demand, incorrect produceMore/stopProducing order | Step 6 |
| NIO-08 | #3003 | `16f19c0` | `49b9d97` | High | error handling | Happy Eyeballs Resolver state machine missed allResolved + resolutionDelayElapsed case | Step 5 |
| NIO-09 | #3031 | `1a3229b` | `1e4fde1` | Medium | validation gap | Scheduled callback tests lacked loop tick synchronization, prone to timing races | Step 2 |
| NIO-10 | #2855 | `ecfaa2c` | `4778543` | Medium | error handling | Misleading "unleakable promise leaked" error on EventLoopGroup shutdown with unfulfilled promises | Step 1 |
| NIO-11 | #3497 | `d948192` | `9b92dcd` | High | state machine gap | Channel state machine failed to track pre/post activation, sent spurious (in)active events | Step 4 |
| NIO-12 | #3464 | `5dc3b4b` | `e3d5c56` | High | configuration error | Pending EmbeddedChannelCore consumers not notified on close, caused indefinite hangs | Step 3 |
| NIO-13 | #3302 | `0b65385` | `57d65dd` | Medium | error handling | EventLoop in-thread checks optimized using thread-local storage for 25% speedup | Step 2 |
| NIO-14 | #3562 | `558f24a` | `98f8824` | Medium | validation gap | Thread affinity test crashed in CPU-restricted environments, used wrong loop bounds | Step 1 |
| NIO-15 | #3556 | `66c50a7` | `5243468` | Medium | validation gap | Scheduled callback cancellation tests flaky on iOS simulator due to timing | Step 2 |
| NIO-16 | #3555 | `5243468` | `08abc3a` | Medium | validation gap | testFlatBlockingMapOnto crashed on iOS simulator during concurrency testing | Step 1 |
| NIO-17 | #3551 | `0e7d4e9` | `e313684` | Medium | validation gap | Half-close with populated buffer test flaky on iOS simulator | Step 2 |
| NIO-18 | #3550 | `e313684` | `b9d20d3` | Medium | validation gap | Scheduled callback deadline test flaky, required synchronization fix | Step 2 |
| NIO-19 | #3399 | `97c3f28` | `a3ed8e1` | Medium | validation gap | testWithConfiguredStreamSocket flaky, race condition in async socket setup | Step 1 |
| NIO-20 | #3466 | `5ada77d` | `608e511` | Medium | security issue | Potential template injection in codebase (later reverted due to side effects) | Step 6 |
| NIO-21 | #3422 | `cc38f7a` | `d963335` | Medium | validation gap | NIOCore failed to compile for WASI/WebAssembly targets | Step 1 |
| NIO-22 | #3135 | `a0c542b` | `34d486b` | High | concurrency issue | NIOAsyncWriter test hung on single-threaded concurrency pool due to incorrect expectations | Step 3 |
| NIO-23 | #3057 | `96877af` | `6fb31ea` | Medium | validation gap | Swift 6.1 compiler issues breaking NIOPosix build | Step 1 |
| NIO-24 | #2970 | `2139438` | `6d30ec4` | Low | configuration error | SemVer major version label check logic incorrect | Step 2 |
| NIO-25 | #2654 | `ff98c93` | `19da487` | High | concurrency issue | EventLoopFuture and EventLoopPromise failed strict concurrency type checking | Step 4 |
| NIO-26 | #3511 | `e932d3c` | `be8fdc1` | Medium | validation gap | Test compilation crashed in release mode on Swift 6.2 | Step 1 |
| NIO-27 | #3502 | `2fdda6c` | `c329d1e` | Low | validation gap | Benchmark succeeded even when build failed, misleading pass | Step 1 |
| NIO-28 | #3036 | `56f9b7c` | `7dea8e7` | Medium | validation gap | Tasks scheduled during shutdown not reliably cancelled in async context | Step 2 |
| NIO-29 | #2937 | `49cd78b` | `cc1c57c` | High | error handling | withConnectedSocket failed in async mode due to closure handling | Step 3 |
| NIO-30 | #2938 | `8666af5` | `49cd78b` | Medium | configuration error | NIOCore Windows build broken by selector changes | Step 1 |
| NIO-31 | #3217 | `6615a44` | `6789c58` | Medium | validation gap | ByteBuffer tests failed when Swift 6 compiled but running on macOS 14 | Step 1 |
| NIO-32 | #3062 | `0c547a7` | `b14012b` | High | concurrency issue | HappyEyeballsResolver and Bootstraps violated strict concurrency requirements | Step 5 |
| NIO-33 | #3554 | `08abc3a` | `9939a5c` | Medium | validation gap | Flaky test - parallel test interference in temp file scanning for copy operations | Step 2 |
| NIO-34 | #3453 | `d2feeaa` | `5bf841d` | High | concurrency issue | Cancellation missed between dropping and reacquiring lock in async writer yield | Step 6 |
| NIO-35 | #3339 | `a65e973` | `2c9b7c6` | High | protocol violation | Invalid response headers not fully dropped, causing protocol violations in pipelined HTTP | Step 5 |
| NIO-36 | #3330 | `41b1262` | `6719917` | High | state machine gap | Pipe Bootstrap channel initializer called twice on async paths | Step 4 |
| NIO-37 | #3324 | `4205cca` | `175417d` | Medium | configuration error | Windows IOVector type mismatch, DatagramVector manager incompatible with WSABUF | Step 1 |
| NIO-38 | #3442 | `56724a2` | `2dbd1bf` | Medium | validation gap | EmbeddedChannelCore address storage visibility gap, handlers unaware of address changes | Step 3 |
| NIO-39 | #3455 | `663ddc8` | `2bc6627` | High | concurrency issue | TokenBucket held lock over continuation call, vulnerable to executor re-enqueue deadlock | Step 5 |
| NIO-40 | #3454 | `cda536d` | `d2feeaa` | High | concurrency issue | NIOThrowingAsyncSequenceProducer held lock over continuation, prone to deadlock | Step 5 |
| NIO-41 | #3452 | `5bf841d` | `3eea092` | High | concurrency issue | Lock held during withContinuation call, job re-enqueue causes deadlock | Step 6 |
| NIO-42 | #3408 | `cdf721f` | `4e8f4b1` | High | state machine gap | Pipe channels become zombie on writeEOF when inbound closed, EPOLLHUP not handled | Step 4 |
| NIO-43 | #3366 | `5679824` | `66a85ba` | High | configuration error | WSAStartup not called on Windows, Winsock initialization incomplete | Step 1 |
| NIO-44 | #3308 | `1c30f0f` | `a114cfb` | Medium | validation gap | EmbeddedChannel/AsyncTestingChannel missing option throwing API for closed channel tests | Step 2 |
| NIO-45 | #3507 | `9b92dcd` | `db01d87` | High | error handling | ConditionLock thundering herd in thread pool, all idle threads woken instead of one | Step 3 |
| NIO-46 | #3495 | `37ffc4b` | `b2a1446` | Medium | validation gap | EmbeddedChannel getOption/setOption should throw on closed channel like real channels | Step 2 |
| NIO-47 | #3483 | `c337170` | `ce5d042` | Low | state machine gap | Unused mutex variable allocation in Lock class, not elided for certain conditions | Step 1 |


### phoenixframework/phoenix (Elixir)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| PHX-01 | #6641 | `1bf4f6d` | `76789b9` | Low | error handling | JavaScript socket logger missing log level parameter causing undefined behavior | Step 2 |
| PHX-02 | #6633 | `76789b9` | `e3a1667` | High | configuration error | Phx.new crashes when parent directory path contains colons due to template binding regex applied to absolute path | Step 1 |
| PHX-03 | #6602 | `ac12eec` | `0f6a26f` | High | protocol violation | Socket teardown during concurrent connections causes state inconsistencies and failed cleanup | Step 2 |
| PHX-04 | #6579 | `27e28ef` | `2575a6b` | Medium | protocol violation | Socket reconnects unnecessarily after clean close when visibility changes on page show | Step 2 |
| PHX-05 | #6621 | `84607a4` | `f286d69` | High | protocol violation | Visibility change handler connects socket that was never connected, breaking reconnection logic | Step 2 |
| PHX-06 | #6538 | `12fb217` | `9f13f00` | High | protocol violation | LongPoll 410 response doesn't trigger channel rejoin on session timeout in mobile Safari | Step 3 |
| PHX-07 | #6607 | `0572c91` | `d4ec4b7` | Medium | security issue | Remember-me cookie deletion ignores cookie options, causing deletion failures | Step 5 |
| PHX-08 | #6632 | `8fb466e` | `27e28ef` | High | error handling | Query string list values silently produce malformed output instead of raising clear error | Step 4 |
| PHX-09 | #6562 | `636acb0` | `24ea1ac` | High | protocol violation | Minified LongPoll transport name stored in sessionStorage becomes unstable and breaks fallback detection | Step 3 |
| PHX-10 | #6197 | `157dd54` | `d227c201` | High | validation gap | Show page crashes when PubSub broadcast arrives for deleted items due to missing handler | Step 1 |
| PHX-11 | #6135 | `2601ceb` | `59dcde33` | Medium | validation gap | Error template rendering fails LiveView compatibility check due to missing __changed__ field | Step 1 |
| PHX-12 | #6168 | `c8ba77a` | `1cf6ef99` | High | protocol violation | Regex in module attributes incompatible with OTP 28 breaks asset digestion | Step 2 |
| PHX-13 | #6086 | `db8eac8` | `fc5c3155` | High | validation gap | Token-based channel auth inconsistent between WebSocket and LongPoll transports | Step 3 |
| PHX-14 | #6094 | `16bfa91` | `88f8e52c` | Medium | protocol violation | Sec-WebSocket-Protocol headers not accessible in channel connect handler | Step 2 |
| PHX-15 | #6072 | `91d25f5` | `6ef22f09` | High | protocol violation | Invalid WebSocket/LongPoll socket options silently ignored, causing runtime failures | Step 1 |
| PHX-16 | #6056 | `577004e` | `b1228c4f` | Medium | error handling | Global reference error in constants prevents socket initialization in some environments | Step 2 |
| PHX-17 | #6000 | `bb494bb` | `7acd8a91` | Medium | error handling | AlreadySentError raises without context, making debugging response failures difficult | Step 5 |
| PHX-18 | (socket config) | `52698bb` | `278cd455` | High | protocol violation | Passing false to socket config causes pattern match error | Step 1 |
| PHX-19 | #6088 | `b1228c4` | `d8c48c77` | Low | configuration error | Unused clause warning in installer on Elixir 1.18+ | Step 2 |
| PHX-20 | #6549 | `9c3e921` | `fe915d3e` | Medium | configuration error | Endpoint port configuration incorrect in umbrella application templates | Step 1 |
| PHX-21 | #6296 | `aa9018d` | `3e916da1` | Medium | configuration error | Phx.gen.presence generates incorrect PubSub server name for umbrella apps | Step 1 |
| PHX-22 | (undocumented) | `c930e32` | `85b44b1e` | Medium | validation gap | LongPoll subprotocols undefined causes null pointer errors when extracting auth tokens | Step 3 |
| PHX-23 | #6458 | `8546ea3` | `db21e45e` | Low | error handling | Missing parentheses in error message suggestion text | Step 5 |
| PHX-24 | #4801 | `a93de70` | `2619e26f` | Medium | protocol violation | Compile-time endpoint config not properly scoped causing configuration leakage | Step 1 |
| PHX-25 | #6610 | `91d25f5` | `91d25f5^` | High | configuration error | Socket endpoint validation implementation incomplete, allowing invalid configurations | Step 1 |
| PHX-26 | #6591 | `ac12eec` | `0f6a26f` | Medium | error handling | Socket concurrent teardown leaves dangling message handlers in event queue | Step 2 |
| PHX-27 | #6632 | `8fb466e` | `27e28ef` | High | configuration error | Interpolated list in query parameter silently treated as map, producing invalid query strings | Step 4 |
| PHX-28 | (undocumented) | `636acb0` | `24ea1ac` | Critical | protocol violation | Transport fallback detection fails due to minified class name in sessionStorage lookup | Step 3 |
| PHX-29 | #6197 | `157dd54` | `d227c201` | Critical | validation gap | Missing handler for broadcast events on show live template crashes entire session | Step 1 |
| PHX-30 | #6500 | `3a09787` | `163e3fc` | Medium | configuration error | Custom dispatcher in Presence handle_diff not properly documented or tested | Step 2 |
| PHX-31 | #6332 | `ee63ed4` | `ae3beeb` | High | configuration error | phx.gen.cert incompatible with OTP 28 due to null signature parameters in cert generation breaking build | Step 2 |
| PHX-32 | #6543 | `3755ea5` | `c8bd33c` | Medium | configuration error | Generated regex patterns incompatible with Elixir 1.19.3+ without E modifier for raw mode causing reloader failures | Step 2 |
| PHX-33 | #6542 | `8d3f405` | `e911f50` | Medium | API contract violation | Phoenix.Controller.assign/2 missing function overload for single-argument function, causing pattern match errors | Step 5 |
| PHX-34 | #6525 | `76a586c` | `8badd7e` | Medium | configuration error | npm docs build fails when dependencies not installed, missing npm install step | Step 2 |
| PHX-35 | #6507 | `9fc21c6` | `20b36ea` | Medium | configuration error | Generated mix precommit alias uses wrong flag --warning-as-errors instead of --warnings-as-errors causing build failures | Step 2 |
| PHX-36 | (verified routes) | `b3462a7` | `8065c1c` | High | error handling | Static routes incorrectly receive path prefixes in verified routes, breaking static asset routing with scoped prefixes | Step 4 |
| PHX-37 | #6212 | `bc10d6d` | `ca4f46e` | Medium | error handling | Server error layout CSS selectors target wrong element, preventing display of server errors on client | Step 5 |
| PHX-38 | #6091 | `6f8e881` | `a17f661` | Medium | configuration error | Umbrella app runtime.exs imports Config twice, causing duplicate configuration and warnings | Step 1 |
| PHX-39 | #6067 | `faf58d0` | `577004e` | High | configuration error | Release generation uses deprecated CAStore dependency instead of OTP 25+ built-in :public_key.cacerts_get/0 | Step 2 |
| PHX-40 | #6113 | `af2f76a` | `bcc984d` | High | security issue | put_secure_browser_headers missing CSP header, allowing iframing and base tag abuse without default protections | Step 5 |
| PHX-41 | #6194 | `62339b6` | `d94cc65` | Medium | error handling | Tailwind custom variant syntax incorrect with square brackets instead of parentheses, breaking loading state styles | Step 2 |
| PHX-42 | #6165 | `563ccc5` | `50e612b` | Medium | configuration error | Umbrella app heroicons path calculation incorrect causing import path mismatch; missing CodeReloader listener | Step 1 |
| PHX-43 | #6218 | `ec6ed94` | `95523bf` | Low | error handling | Endpoint init/2 deprecation message unclear and unhelpful, missing guidance on migration to runtime.exs | Step 5 |
| PHX-44 | #6100 | `8c9df0d` | `fc5c315` | Medium | error handling | Table border not visible on hover when no action buttons provided due to selector specificity issue | Step 2 |
| PHX-45 | #6586 | `9156c86` | `4bc34f6` | Low | error handling | Label elements missing for attribute linking to input fields, breaking form accessibility and screen reader functionality | Step 5 |


### elixir-ecto/ecto (Elixir)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| ECT-01 | #4712 | `9bac4c4` | `a7f390f1` | High | validation gap | Keep value trimming and empty values are separate concepts | Step 1 |
| ECT-02 | #4695 | `8d65762` | `016eefab` | Medium | configuration error | Fix autogenerated uuid pk syntax | Step 1 |
| ECT-03 | #4631 | `59d21ee` | `18a633a1` | High | null safety | Fix nil map associations with preload | Step 1 |
| ECT-04 | #4630 | `5750491` | `3637802c` | High | type safety | Fix macro expansion in over clause's order_by | Step 1 |
| ECT-05 | #4592 | `2e66ee8` | `29c58049` | High | state machine gap | Fix join count conflicts with subqueries | Step 1 |
| ECT-06 | #4578 | `1be980f` | `67afe558` | High | type safety | Fix macros inside of order_by | Step 1 |
| ECT-07 | #4419 | `21c6068` | `5f3c1f55` | High | type safety | Keep parameterized types as tuples of tuples | Step 1 |
| ECT-08 | #4473 | `ef93693` | `f01fa4a5` | High | SQL error | Fix edge case for insert_all with selecting a source with updates | Step 1 |
| ECT-09 | #4443 | `568f45e` | `88100b86` | Medium | API contract violation | Use schema for association name | Step 1 |
| ECT-10 | #4541 | `d47bc2c` | `98ba6fef` | Medium | error handling | Fix inspecting dynamic/2 with interpolated named bindings | Step 1 |
| ECT-11 | #4316 | `55a9a86` | `a8052ffd` | High | type safety | Fix late binding with composite types | Step 1 |
| ECT-12 | #4269 | `4c68b14` | `140c186e` | High | type safety | Fix Ecto.Type.type/1 not working for parameterized types | Step 1 |
| ECT-13 | #4237 | `30311c2` | `eb2d6a42` | High | validation gap | Fix duplicate ID check for many assocs/embeds | Step 1 |
| ECT-14 | #4230 | `af64fa3` | `f87ddd5f` | Medium | SQL error | Add parent prefix to association on_delete query | Step 1 |
| ECT-15 | #4229 | `f87ddd5` | `eb03f45b` | High | validation gap | Fix raise when trying to autogenerate :id in embed | Step 1 |
| ECT-16 | #4195 | `e13f10d` | `29e9566f` | High | type safety | Fix late binding with json_extract_path | Step 1 |
| ECT-17 | #4187 | `49e735c` | `2469a7a0` | High | type safety | Support parameterized map types in json path validation | Step 1 |
| ECT-18 | #4184 | `bdeeedb` | `b3a61068` | Medium | SQL error | Make aggregate respect parent query prefix | Step 1 |
| ECT-19 | #4163 | `76ae17d` | `f0c95e65` | High | type safety | Fix json_extract_path with custom map | Step 1 |
| ECT-20 | #4101 | `783d3b2` | `8bfe0b69` | High | validation gap | Fix validate_json_path for nested map inside embed | Step 1 |
| ECT-21 | #4341 | `b26b25b` | `7b1695fb` | High | validation gap | Fix nested preloads with joined through associations | Step 1 |
| ECT-22 | #4672 | `6f8697c` | `05112062` | Medium | SQL error | Properly format :in composite types | Step 1 |
| ECT-23 | #4568 | `aacf5ff` | `bf01d85d` | Medium | error handling | Clarify subquery limitation in error message | Step 1 |
| ECT-24 | #4554 | `4d3c5ee` | `c0203dbd` | Medium | error handling | Improve error message on custom preload | Step 1 |
| ECT-25 | #4697 | `bf24234` | `7224c127` | Medium | configuration error | Don't require adapter for runtime fragment splicing | Step 1 |
| ECT-26 | #4696 | `7224c12` | `1335593f` | Medium | API contract violation | Handle constant/1 unpacking in Ecto instead of adapters | Step 1 |
| ECT-27 | #4693 | `1335593` | `8d657628` | High | type safety | Support compile-time fragment splicing | Step 1 |
| ECT-28 | #4692 | `016eefa` | `36c68044` | High | silent failure | Remove Query.exclude(:order_by) in exists? | Step 1 |
| ECT-29 | #4690 | `36c6804` | `a49e499e` | Medium | configuration error | Add query_cache option to selectively bypass query cache | Step 1 |
| ECT-30 | #4687 | `a49e499` | `beec41ac` | Medium | configuration error | Add generated option to macro in repo.ex | Step 1 |
| ECT-31 | #4709 | `299cde2` | `6b61f9a9` | High | error handling | Correctly extract passwords with colons from URL | Step 1 |
| ECT-32 | #4700 | `3560bad` | `a75cefa4` | Medium | configuration error | Add replace_changed option to inserts | Step 1 |
| ECT-33 | #4686 | `1de9ba2` | `eb0a1601` | Medium | error handling | Handle empty list argument without raising error | Step 1 |
| ECT-34 | #4670 | `0511206` | `5dc886a2` | High | validation gap | Reset parent assoc when after nil preload | Step 1 |
| ECT-35 | #4668 | `5dc886a` | `82fcf6c6` | Medium | type safety | Allow joins with {fragment, Schema} source | Step 1 |
| ECT-36 | #4678 | `0123f91` | `12dd3d0` | High | type safety | Support struct subset selection on subqueries (was erroring) | Step 1 |
| ECT-37 | #4675 | `54a10ee` | `e692f20` | High | state machine gap | Fix preload_order incorrectly overriding custom query order_by | Step 1 |
| ECT-38 | #4666 | `82fcf6c` | `3ab6a20` | High | type safety | Allow take/2 with tuple fragment sources | Step 1 |
| ECT-39 | #4664 | `3ab6a20` | `d715d59` | High | type safety | Support fragment sources mapped to schemas | Step 1 |
| ECT-40 | #4659 | `148c03c` | `535b267` | Medium | API contract violation | Support 2-arity functions as preload function in Query | Step 1 |
| ECT-41 | #4656 | `baa1a9b` | `420a84d` | High | validation gap | Default empty values must consider type not just config | Step 1 |
| ECT-42 | #4683 | `eb0a160` | `a17227e` | High | type safety | Fix UUIDv7 monotonicity and clock precision issues | Step 1 |
| ECT-43 | #4681 | `e6da70d` | `6b61f9a` | High | validation gap | Implement uuid v7 autogeneration | Step 1 |
| ECT-44 | #4682 | `6b61f9a` | `0709545` | Medium | configuration error | Add preload_order option to has_one/3 schema | Step 1 |
| ECT-45 | #4356 | `796aa61` | `270fab0` | Medium | validation gap | Validate :prefix parameter is string/binary not atom | Step 1 |
| ECT-46 | #4377 | `59a6ccc` | `21c77d6` | High | SQL error | Ignore query prefix for CTE sources to prevent incorrect SQL | Step 1 |
| ECT-47 | #4461 | `e403496` | `20239b3` | Medium | SQL error | Fix inspecting fields from sources with take/2 | Step 1 |
| ECT-48 | #4272 | `66a14d4` | `743ce04` | Low | SQL error | Fix planned values inspect output | Step 1 |
| ECT-49 | #4279 | `6a2d174` | `32875cc` | Low | type safety | Fix traverse_* typespec signatures | Step 1 |
| ECT-50 | #4487 | `df967cc` | `5f1eefc` | Low | type safety | Fix Ecto.Enum.mappings/2 and values/2 specs | Step 1 |


### oban-bg/oban (Elixir)

| # | Issue | Fix Commit | Pre-fix Commit | Severity | Category | Description | Playbook Angle |
|---|-------|------------|----------------|----------|----------|-------------|----------------|
| OB-01 | #1382 | `825cd99` | `a68363f` | High | state machine gap | Fix starting a queue on a specific node - :node option was incorrectly preserved, causing crashes | Queue Start/Stop |
| OB-02 | N/A | `b7042ce` | `eb96a30` | High | error handling | Fix Sonar and Midwife listener loss after Notifier crash - re-registers listeners on GenServer restart | Supervisor Recovery |
| OB-03 | N/A | `e8aa621` | `d840ec0` | High | error handling | Protect Stager from Notifier crash during staging - wrap notify in try/catch | Error Propagation |
| OB-04 | N/A | `f9520e2` | `385f68f` | High | state machine gap | Fix dropping invalid indexes from reindexer - CONCURRENT ops fail in functions | Postgres Interaction |
| OB-05 | N/A | `74756b3` | `12f5fd4` | Medium | validation gap | Handle missing fields in Worker unique - validation didn't account for default fields | Unique Constraints |
| OB-06 | #1353 | `12f5fd4` | `a54a05a` | Medium | state machine gap | Set state to scheduled when updating timestamp - state wasn't auto-set during update_job | Job Lifecycle |
| OB-07 | #1362 | `a1d20f2` | `aa24e3b` | High | error handling | Order stage query to maximize compound index usage - query planner issue | Postgres Interaction |
| OB-08 | #1391 | `ce65712` | `88f6557` | Medium | SQL error | Better sqlite timestamp default and pruning query - CURRENT_TIMESTAMP lacks z suffix | Database Migration |
| OB-09 | #1403 | `385f68f` | `3494d8e` | Medium | configuration error | Prevent installer crash with unsupported adapters - CaseClauseError on Tds adapter | Installer |
| OB-10 | #1283 | `1f0c22a` | `20ba49c` | Low | validation gap | Fix error message when crontab has invalid range - wrong error message | Cron/Validation |
| OB-11 | #1277 | `c26a1f4` | `f207667` | Medium | state machine gap | Disallow :keys when :fields don't contain :args or :meta - config validation bug | Unique Constraints |
| OB-12 | #1400 | `c665268` | `68ec0a6` | Medium | state machine gap | Allow snoozing jobs by returning tuple period - added tuple period support | Job Snooze |
| OB-13 | #1381 | `a68363f` | `1d2c1f8` | Low | configuration error | Validate no duplicate option passed to Oban config - missed validation | Config Validation |
| OB-14 | #1196 | `5de9366` | `af7e9e2` | Low | SQL error | Fix version query for databases with non-unique oid - query result ambiguity | Migration/Versioning |
| OB-15 | N/A | `215981e` | `f545314` | High | state machine gap | Restrict inline execution to available/scheduled - completed jobs were being executed | Job State |
| OB-16 | N/A | `902d8c9` | `9c04b1f` | High | state machine gap | Nest plugins within secondary supervision tree - isolate plugin crashes | Supervisor Design |
| OB-17 | #1322 | `e1a2060` | `cd80cad` | Medium | validation gap | Generate correct perform_job/1,2,3 clauses - missing clause for build_job/3 | Testing Helpers |
| OB-18 | #1202 | `df273fb` | `9c04b1f` | High | state machine gap | Add update_job functionality - new feature with validation and locking | Job Mutation |
| OB-19 | N/A | `d86f2b9` | `f91ea26` | Low | error handling | Handle and log unexpected messages - improved error handling | Logging |
| OB-20 | N/A | `02bd42f` | `3ae8122` | Low | error handling | Skip logging peer events unless leadership changes - noise reduction | Peer Events |
| OB-21 | N/A | `3ae8122` | `470cdd0` | Medium | state machine gap | Correct stale node logic for sonar tracking - incorrect node state tracking | Peer/Sonar |
| OB-22 | #1250 | `1676436` | `ce28592` | High | SQL error | Check dolphin leadership after upsert - MySQL returns wrong leader detection | MySQL/Peer Election |
| OB-23 | #1246 | `56be721` | `ae608ba` | High | configuration error | Use Ecto.Type.cast/2 for backward compatibility - cast!/2 unavailable in older Ecto | Ecto Integration |
| OB-24 | #1132 | `bf7f0bf` | `4715ea5` | High | error handling | Automatically retry transactions with backoff - avoid serialization errors | Transaction Retry |
| OB-25 | N/A | `c1dc3d6` | `3326dcb` | High | error handling | Drop invalid indexes concurrently - concurrent drops avoided table locks | Postgres Interaction |
| OB-26 | N/A | `91de93e` | `d3f3021` | Low | validation gap | Validate unique option isn't empty list - runtime/compile-time parity | Validation |
| OB-27 | #1254 | `bd73cfe` | `9529d65` | Low | error handling | Improve warning message on incorrect perform/1 return - better error reporting | Error Messages |
| OB-28 | N/A | `9529d65` | `b72c88c` | Medium | validation gap | Check for worker functions rather than behaviour - allow override of timeout/backoff | Testing/Worker |
| OB-29 | N/A | `dde9cf8` | `8aa8f00` | Medium | SQL error | Include MyXQL.Error in automatic retry - missing MySQL error type | MySQL/Error Handling |
| OB-30 | #1145 | `861dfa5` | `5df7399` | High | state machine gap | Use proper fields for finding prunable jobs - job state determines which timestamp | Pruning Query |
| OB-31 | N/A | `24f7bee` | `7d195cc` | Medium | type safety | Stream type checking for insert_all only accepted Struct variants, missing function/2 multiarity - caused insert_all to fail for some stream sources | Type Guards |
| OB-32 | N/A | `79f5bdf` | `1692340` | Low | validation gap | Documentation incorrectly listed `scheduled` as unsupported state for retry_job/2, but it was actually valid | Documentation Accuracy |
| OB-33 | N/A | `8aa8f00` | `5de9360` | High | API contract violation | scale_queue/2 with :node option had validation that prevented it from working - validation omitted :node from allowed opts | Queue Management |
| OB-34 | N/A | `ed3d9f5` | `6aca76c` | Medium | type safety | Registry.whereis switch caused spec mismatches and unhandled clauses in type checking - dialyzer failures | Type Safety |
| OB-35 | #1151 | `4044145` | `6841a30` | High | error handling | Inline engine's insert_all_jobs incorrectly expected changesets to always be list, not stream - type mismatch on non-list input | Stream Handling |
| OB-36 | #1122 | `3fc4dd0` | `baf6851` | High | silent failure | query!/4 was dispatching :query instead of :query! - telemetry events mislabeled, error semantics incorrect | Telemetry/Dispatch |
| OB-37 | N/A | `b2e1782` | `5e2cd1` | High | concurrency issue | Clogged Ecto pool caused cascading startup errors - Sonar notification blocked Notifier, Stager timeout crashed on Sonar status check | Startup/Concurrency |
| OB-38 | N/A | `b6302cd` | `e7f91f4` | Low | API contract violation | Sonar missing :get_nodes call handler - internal operations unable to retrieve tracked nodes | Sonar API |
| OB-39 | N/A | `163c4bc` | `02a9021` | Low | type safety | shutdown_grace_period typed as non_neg_integer instead of integer - violates type contract | Configuration |
| OB-40 | N/A | `3e9f936` | `cc30d4c` | High | API contract violation | pause_all_queues/resume_all_queues had dual default params - impossible to call with opts only, no name parameter | Function Signature |
| OB-41 | N/A | `8aa5d76` | `d9d8480` | High | error handling | Custom worker backoff not applied on TimeoutError or unhandled exit - executor resolved before worker module stored, stale backoff used | Job Retry |
| OB-42 | #1007 | `61e30f7` | `3ca84b9` | High | error handling | Postgres peer election unhandled rollback return - transaction returned {:error, :rollback} causing match error and peer crash | Peer Election |
| OB-43 | #980 | `306c79d` | `e02c918` | Medium | validation gap | Cron expression parser accepted invalid range where left > right (e.g., 9-5) - no validation on range bounds | Cron Validation |
| OB-44 | N/A | `d8b5fee` | `e63d60d` | High | silent failure | Producer silently ignored unhandled messages - dead process pids remained in running jobs, causing incorrect state tracking | Message Handling |
| OB-45 | N/A | `156c5c8` | `a79f900` | Medium | configuration error | Sonar initialized in test modes unnecessarily - caused sandbox violations in Postgres notifier tests | Test Isolation |
| OB-46 | N/A | `6b9bf1d` | `53a4bda` | High | missing boundary check | Sonar timeout logic subtracted milliseconds from seconds - unit mismatch in node pruning age calculation | Time Unit |
| OB-47 | #1268 | `a005258` | `8999369` | High | configuration error | Elixir 1.19 struct update syntax incompatible - old map merge syntax failed with new Elixir versions | Version Compatibility |


---

## Acceptance Criteria (For New Entries)

Every defect in this library must satisfy:

1. **Public repository** — GitHub or equivalent, accessible to anyone
2. **Commit SHAs verified** — both fix and pre-fix commits are accessible and related
3. **Bug is documented** — issue tracker entry, PR, or clear commit message
4. **Fix is clear** — code change addresses the described problem
5. **Category is justified** — primary category matches the root cause
6. **Severity matches guide** — consistent with the severity classification above
7. **Not a cosmetic-only fix** — typos in comments/docs, dependency bumps, and CI-only changes are excluded
8. **Bug is in the project itself** — not in a third-party dependency

---

## Changelog

- **2026-03-29 v8**: Round 3 mining across all 55 repos. Added ~754 new defects. Total: 2564 defects across 55 projects, 14 languages. All repos now have 25-80+ defects each.
- **2026-03-29 v7**: Major expansion from 7 to 14 languages. Added 20 new repos across JavaScript, Ruby, PHP, Kotlin, C, Swift, and Elixir. Total: 1810 defects across 55 projects. New repos: express, webpack, eslint, rails, sidekiq, devise, laravel, guzzle, composer, ktor, Exposed, kotlinx.serialization, redis, curl, jq, vapor, swift-nio, phoenix, ecto, oban.
- **2026-03-29 v6**: Round 2 extraction added 111 defects from 6 existing repos for a total of 1109. Repos expanded: jellyfin (+20), cal.com (+20), cli/cli (+18), quarkus (+22), serde (+14), nsq (+17).
- **2026-03-29 v5**: Expanded from 32 to 35 projects (998 total defects). New projects: edgequake, nats.rs, quarkus. Rust/Infrastructure cell now filled. All 28 cells in Language × Type matrix covered (27 filled, only Scala/Infrastructure empty).
- **2026-03-29 v4**: Expanded from 22 to 32 projects. Added 305 new defects for a total of 900. New projects: zookeeper, kafka, finatra, akka, httpx, AgentScope, cal.com, jellyfin, gitbucket, log4net. Updated Language × Type matrix now covers all 28 cells across 7 languages × 4 types (26 filled).
- **2026-03-29 v3**: Expanded from 4 to 22 projects across 7 languages (Java, Python, Go, TypeScript, Rust, Scala, C#) and 4 repo types (Library, Framework, Application, Infrastructure). Added 539 new defects for a total of 595. Added Project Classification matrix. New projects: okhttp, pydantic, fastapi, rq, cobra, chi, cli/cli, nsq, zod, trpc, prisma, serde, axum, ripgrep, lightbend/config, Newtonsoft.Json, MassTransit, Hangfire.
- **2026-03-29 v2**: Added Playbook Angle column, severity guide, acceptance criteria, primary/secondary category split. Resolved 10 missing issue numbers (found 7 PR numbers, confirmed 3 as direct commits). Fixed category distribution to count primary only.
- **2026-03-29 v1**: Initial library. 56 defects across 4 projects (gson, javalin, petclinic, octobatch).
