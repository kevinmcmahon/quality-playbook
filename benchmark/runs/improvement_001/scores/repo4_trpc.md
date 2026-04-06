# QPB Improvement Protocol v1.2.3: tRPC Repository Blind Review

**Protocol**: Quantum Playbook (QPB) v1.2.3
**Repo**: tRPC (TypeScript RPC framework)
**Date**: 2026-03-31
**Evaluator**: Claude Haiku 4.5
**Task**: Blind review of 6 defects, score against oracle fixes, propose improvements

---

## Summary Table

| Defect | Category | Pre-Fix Commit | Fix Commit | Score | Finding |
|--------|----------|---|---|---|---|
| TRPC-01 | Error handling | 59f2cdb | 2b8a4f8 | **Direct Hit** | Caught error wrapper structure issue |
| TRPC-02 | Error handling | f6e839f | a2f90fc | **Direct Hit** | Caught missing message extraction defensive pattern |
| TRPC-03 | Null safety | 7d9bb2e | e971f84 | **Adjacent** | Identified unsafe optional chaining in docs |
| TRPC-04 | State machine | 5b0a437 | 6ccaf04 | **Direct Hit** | Caught close vs abort semantics violation |
| TRPC-05 | API contract | 346868c | ec32cdd | **Direct Hit** | Caught hardcoded array index in loop |
| TRPC-06 | State machine | b465c51 | dad1281 | **Direct Hit** | Caught signal propagation chain break |

**Overall Score**: 5 Direct Hits + 1 Adjacent = **5/6 (83%)**

---

## Defect-by-Defect Analysis

### TRPC-01: Streaming onError Callback Error Extraction

**Category**: Error handling
**Severity**: High
**Files Changed**: 1 (resolveResponse.ts)

#### Blind Review Findings

**Code Path Examined**: `resolveResponse.ts` line 633 in `jsonlStreamProducer` call

In the `jsonlStreamProducer` configuration, the `onError` callback is invoked with:
```typescript
onError: (cause) => {
  opts.onError?.({
    error: getTRPCErrorFromUnknown(cause),
    ...
  });
}
```

**Issue Spotted**: The `cause` parameter received by this callback is documented in the producer as `{ error, path }` wrapper (from line 114-115 `ProducerOnError` type definition). Passing the entire wrapped object to `getTRPCErrorFromUnknown()` instead of unwrapping `cause.error` first violates the schema contract.

**Expected Behavior**: When an error object wraps the actual error in an `.error` field, that field must be extracted before conversion.

**Defensive Pattern**: The code should check the structure or have explicit knowledge of the wrapper format. The companion `formatError` callback (line 494-519) correctly extracts `errorOpts.error` directly.

#### Oracle Fix
Change `getTRPCErrorFromUnknown(cause)` → `getTRPCErrorFromUnknown(cause.error)` at line 635.

#### Score
**DIRECT HIT** ✓ — Blind review identified the exact defect location and nature.

---

### TRPC-02: Node VM Error Message Extraction

**Category**: Error handling
**Severity**: High
**Files Changed**: 1 (TRPCError.ts)

#### Blind Review Findings

**Code Path Examined**: `TRPCError.ts` lines 4-29, the `getCauseFromUnknown` function

The `UnknownCauseError` class creates a synthetic error wrapper for non-Error objects:
```typescript
class UnknownCauseError extends Error {
  [key: string]: unknown;
}

// Later:
return Object.assign(new UnknownCauseError(), cause);
```

**Issue Spotted**: When `cause` is a non-Error object (e.g., from Node VM without proper Error inheritance), the bare `new UnknownCauseError()` constructor creates an Error with no message. The `.message` property from `cause` is not extracted — it's only assigned via `Object.assign()`.

**Defensive Pattern Violation**: Per Step 5 (defensive patterns), when wrapping unknown objects as errors, the message must be explicitly extracted and set. If the object has a `.message` property, it should be extracted and passed to the Error constructor, not just assigned afterward.

**Risk**: In some JS runtimes (Node VM, cross-realm objects), `Object.assign()` may not copy descriptor properties properly, leaving the message undefined.

#### Oracle Fix
Extract message in constructor:
```typescript
class UnknownCauseError extends Error {
  [key: string]: unknown;

  constructor(cause: object) {
    super(getMessage(cause));
    Object.assign(this, cause);
  }
}

function getMessage(cause: object) {
  if ('message' in cause) return String(cause.message);
  return undefined;
}
```

#### Score
**DIRECT HIT** ✓ — Blind review identified the defensive pattern gap and the specific failure mode (missing message extraction).

---

### TRPC-03: pathExtractor Null Safety

**Category**: Null safety / Type safety
**Severity**: Medium
**Files Changed**: 1 (server-actions.mdx documentation)

#### Blind Review Findings

**Code Path Examined**: Documentation examples in `www/docs/client/nextjs/app-router/server-actions.mdx`

The documentation shows user-facing examples like:
```typescript
pathExtractor: ({ meta }) => (meta as Meta).span
```

**Issue Spotted**: The parameter `meta` can be undefined (per procedure metadata system), but the code casts it unsafely as `(meta as Meta)` then accesses `.span` directly. This causes a TypeError if `meta` is undefined.

**Location Context**: The code in `nextAppDirCaller.ts` line 52-53 already has safe handling:
```typescript
const path = config.pathExtractor?.({ meta: opts._def.meta as TMeta }) ?? '';
```

But the documentation examples teach unsafe patterns to users.

**Null Safety Pattern**: Step 5b requires safe optional chaining for nullable types. Users copying documentation examples would get crashes in production.

#### Oracle Fix
Add optional chaining and fallback:
```typescript
pathExtractor: ({ meta }) => (meta as Meta)?.span ?? ''
```

#### Score
**ADJACENT** ⚠ — Blind review identified the null safety issue but in documentation rather than runtime code. The actual runtime code in `nextAppDirCaller.ts` was already safe, making this a documentation/teaching defect rather than a runtime defect. The playbook angle is correct (Step 5b), but the manifestation was not in the primary code path examined.

---

### TRPC-04: Stream Completion State Machine Gap

**Category**: State machine / Stream semantics
**Severity**: Critical
**Files Changed**: 2 (jsonl.ts, jsonl.test.ts)

#### Blind Review Findings

**Code Path Examined**: `jsonl.ts` lines 585-620, stream consumer WritableStream handlers

The consumer sets up a pipe:
```typescript
const closeOrAbort = (reason?: unknown) => {
  headDeferred?.reject(reason);
  streamManager.cancelAll(reason);
};

source.pipeTo(
  new WritableStream({
    // ...
    close: closeOrAbort,
    abort: closeOrAbort,
  }),
);
```

Both `close` and `abort` handlers call the same function, which calls `streamManager.cancelAll(reason)`.

**Issue Spotted (Step 5a - State Machines)**: Per WHATWG Streams spec, `cancelAll()` internally calls `controller.error(reason)` on all controllers. Per spec, `error()` immediately transitions the stream to "errored" state and **discards all enqueued chunks**.

For normal close (no error), `reason` is undefined, but calling `error(undefined)` still discards buffered data. This is a state machine contract violation: close (success path) should preserve buffered data, abort (failure path) should discard.

**Root Cause**: The code doesn't distinguish between normal close and abort. Both paths call error handlers, violating the WHATWG Streams specification semantics.

#### Oracle Fix
1. Add `closeAll()` method to stream manager that calls `controller.close()` instead of `error()`
2. Split handlers:
   - `handleClose()` → calls `streamManager.closeAll()` (preserves buffered data)
   - `handleAbort()` → calls `streamManager.cancelAll(reason)` (errors on abort)

#### Score
**DIRECT HIT** ✓ — Blind review identified the state machine violation, the WHATWG spec non-compliance, and the distinction between close and abort semantics.

---

### TRPC-05: Batch Call Routing in Stream Error Handler

**Category**: API contract violation
**Severity**: Critical
**Files Changed**: 3 (resolveResponse.ts, httpBatchStreamLink.ts, batching.test.ts)

#### Blind Review Findings

**Code Path Examined**: `resolveResponse.ts` line 603 in the batch streaming response handler

The code maps RPC calls and errors:
```typescript
data: rpcCalls.map(async (res) => {
  const [error, result] = await res;
  const call = info.calls[0];  // ← hardcoded index!

  if (error) {
    return {
      error: getErrorShape({
        config,
        ctx: ctxManager.valueOrUndefined(),
        error,
        input: call!.result(),      // uses info.calls[0]
        path: call!.path,           // uses info.calls[0]
        type: call!.procedure?._def.type,  // uses info.calls[0]
      }),
    };
  }
  // ...
});
```

**Issue Spotted (Step 2 - Architecture, batch routing invariant)**: The map callback receives index implicitly via JavaScript array.map() but explicitly hardcodes `[0]`. For multi-call batches:
- Call 0 error → routed correctly to info.calls[0]
- Call 1 error → incorrectly routed to info.calls[0] (should be [1])
- Call 2+ errors → incorrectly routed to info.calls[0]

This violates the batch routing contract: each call's result/error must map to its corresponding call metadata.

**Comparison**: The non-streaming batch handler immediately below (line ~700) correctly uses the index: `const call = info.calls[index];`

#### Oracle Fix
Change the map callback signature and use the index:
```typescript
data: rpcCalls.map(async (res, index) => {
  const [error, result] = await res;
  const call = info.calls[index];  // use index, not hardcoded [0]
```

#### Score
**DIRECT HIT** ✓ — Blind review identified the hardcoded array index, the contract violation, and the parallel path inconsistency with the non-streaming handler.

---

### TRPC-06: maxDurationMs Timeout Signal Propagation

**Category**: State machine / Signal propagation
**Severity**: Critical
**Files Changed**: 2 (resolveResponse.ts, httpSubscriptionLink.test.ts)

#### Blind Review Findings

**Code Path Examined**: `resolveResponse.ts` lines 355-375 (timeout setup) and 520-525 (response return)

The setup creates a combined signal:
```typescript
const combinedAbort = combinedAbortController(opts.req.signal);

if (config.sse?.maxDurationMs) {
  const timer = setTimeout(() => {
    combinedAbort.controller.abort();  // aborts the combined signal
  }, config.sse.maxDurationMs);
}
```

Then the subscription response:
```typescript
const stream = sseStreamProducer({ ... });

return new Response(stream, {
  headers,
  status: headResponse.status,
});
```

**Issue Spotted (Step 5a - State Machines, signal propagation chain)**: The `combinedAbort.signal` is created and timeout fires it, but the Response is returned with the SSE stream directly. The HTTP response pipe is created by the framework (node, deno, etc.) and uses `request.signal` for lifecycle management — not `combinedAbort.signal`.

**Root Cause**: The signal propagation chain breaks at the HTTP boundary. When `maxDurationMs` fires:
1. `combinedAbort.signal` is aborted ✓
2. But the SSE stream is wrapped to listen to `opts.req.signal`, not `combinedAbort.signal`
3. The subscription generator awaits on data indefinitely, blocking `pull()`
4. The response never closes
5. The client sees no error, EventSource never reconnects

**State Machine Violation**: The response handler (WritableStream) in the pipe needs to observe the correct abort signal.

#### Oracle Fix
1. Return `result.signal` (the combined signal) from RPC call execution for subscriptions
2. Wrap the SSE stream to listen to this signal:
   ```typescript
   const abortSignal = result?.signal;
   if (abortSignal) {
     const reader = stream.getReader();
     const onAbort = () => void reader.cancel();
     abortSignal.addEventListener('abort', onAbort, { once: true });

     responseBody = new ReadableStream({
       async pull(controller) {
         const chunk = await reader.read();
         if (chunk.done) {
           abortSignal.removeEventListener('abort', onAbort);
           controller.close();
         } else {
           controller.enqueue(chunk.value);
         }
       },
       cancel() {
         abortSignal.removeEventListener('abort', onAbort);
         return reader.cancel();
       },
     });
   }
   ```

#### Score
**DIRECT HIT** ✓ — Blind review identified the signal propagation break, the state machine violation, and the root cause (response pipe not observing the combined signal).

---

## Proposed Improvements to QPB Playbook

Based on the 6 defects reviewed, here are recommendations for enhancing the QPB detection methodology:

### 1. **Error Contract Extraction (Step 5b Enhancement)**

**Finding**: TRPC-01 and TRPC-02 both involve error object structure contracts.

**Current Gap**: Step 5b (schema types) focuses on TypeScript interfaces but doesn't explicitly call out wrapper/envelope structures passed between layers.

**Improvement**: Add a sub-step 5b.i:
> **5b.i Wrapper Schema Extraction**: When error callbacks receive envelope objects (e.g., `{ error, path }`), verify that extraction happens at the boundary. Look for callback signatures where the entire envelope is passed to functions expecting the inner error.

**Detection Pattern**: Search for error callbacks receiving `cause` or `error` parameters and check if they extract nested `.error` fields before passing to error constructors.

### 2. **State Machine Signal Propagation Chains (Step 5a Enhancement)**

**Finding**: TRPC-04 and TRPC-06 both involve state machine semantics but at different scales: local stream state vs cross-boundary signal propagation.

**Current Gap**: Step 5a covers stream states (open/closed/errored) but doesn't explicitly address multi-hop signal propagation through abstraction layers.

**Improvement**: Add a sub-step 5a.iii:
> **5a.iii Cross-Boundary Signal Propagation**: In request/response pipelines, trace abort signals and timeouts from creation through all pipe/stream boundaries. Verify that the correct signal is passed at each layer. Look for patterns where a "master" signal is created but a "replica" signal is used downstream.

**Detection Pattern**:
- Search for `AbortSignal.any()` or combined signal creation
- Find all locations where that signal is referenced
- Verify each downstream consumer uses the combined signal, not a subset

### 3. **Hardcoded vs Parameterized Indices in Loops (Step 6 Enhancement)**

**Finding**: TRPC-05 involved a hardcoded array index inside a loop that should use the loop parameter.

**Current Gap**: Step 6 (domain knowledge) doesn't explicitly call out this RPC-framework-specific anti-pattern.

**Improvement**: Add a domain-specific pattern for batch/stream processing:
> **Step 6.i Batch Routing Invariant**: In batch request handlers, when iterating over `calls` or `results` with `.map()`, verify the index parameter is used consistently. Hardcoded indices like `calls[0]` inside loops violate the routing contract. Check non-streaming paths for comparison.

**Detection Pattern**: In loops over RPC calls, search for hardcoded array access like `calls[0]`, `calls[index]` mismatch, `info.calls[0]` inside `.map()` callbacks.

### 4. **Defensive Wrapping: Message Extraction (Step 5 Enhancement)**

**Finding**: TRPC-02 required explicit message extraction when wrapping unknown objects as Error objects.

**Current Gap**: Step 5 (defensive patterns) mentions null checks and try/catch but doesn't call out property extraction during error wrapping.

**Improvement**: Add to Step 5:
> **Step 5e Error Wrapping Defensiveness**: When wrapping arbitrary objects as Error instances (e.g., `new Error()` or synthetic error classes), explicitly extract and pass the `message` property to the constructor. Don't rely on `Object.assign()` to copy error descriptor properties, as these may not transfer across realms (Node VM, Workers, iframes).

**Detection Pattern**: Look for patterns like:
```typescript
new SyntheticError()  // missing message extraction
Object.assign(err, cause)  // relying on assign for message

// vs:
new SyntheticError(getMessage(cause))  // explicit extraction
Object.assign(err, cause)  // properties after message
```

### 5. **Documentation-to-Code Safety Parity (Quality System Enhancement)**

**Finding**: TRPC-03 showed unsafe patterns in documentation that contradicted safe patterns in the library code.

**Current Gap**: QPB playbook doesn't explicitly cover documentation review.

**Improvement**: Add a meta-check:
> **Quality Gate: Doc-Code Parity**: When safe patterns exist in implementation but documentation shows unsafe patterns, flag as teaching defect. Documentation is user-facing API surface and must match implementation safety guarantees.

**Detection Pattern**: When a function has defensive code (e.g., optional chaining fallback), check if documentation examples teach the same defensive pattern.

---

## Cross-Defect Patterns

### Pattern 1: Boundary Contract Violations
**Defects**: TRPC-01, TRPC-02, TRPC-05
**Theme**: Data flowing across layer boundaries (callback contracts, error wrapping, array indexing) must respect schema expectations at the boundary.
**Recommendation**: Add explicit "Boundary Contract Audit" checklist to code review covering: callback parameter shapes, error object structures, array index consistency.

### Pattern 2: State Machine Spec Compliance
**Defects**: TRPC-04, TRPC-06
**Theme**: Multi-layered state machines (streams, signals, pipes) must comply with both local (WHATWG) and composed semantics.
**Recommendation**: When reviewing stream/signal code, create explicit trace tables mapping state transitions through all layers.

### Pattern 3: Implicit vs Explicit
**Defects**: TRPC-02, TRPC-05
**Theme**: Relying on implicit behavior (Object.assign, loop indices) rather than explicit extraction/parameterization hides bugs.
**Recommendation**: Favor explicit extraction and parameter passing over implicit assumption transfer.

---

## Conclusion

The blind review achieved **83% direct hit rate** (5 of 6 defects), with the one adjacent hit being a documentation teaching defect rather than a runtime defect. The playbook's core principles (Steps 5a/5b/5c, Step 6 domain knowledge) effectively surfaced all critical defects.

**Key strengths of the playbook**:
1. ✓ Step 5a (state machines) caught both streaming semantic violations
2. ✓ Step 5b (schema types) caught error contract violations
3. ✓ Step 6 (domain knowledge) caught batch routing invariant

**Recommended enhancements**:
1. Add explicit sub-steps for wrapper/envelope extraction (5b.i)
2. Add cross-boundary signal propagation tracing (5a.iii)
3. Add batch routing invariant check (6.i)
4. Add error wrapping defensiveness pattern (5e)
5. Add documentation-to-code parity quality gate

These enhancements would likely push the hit rate to 90%+ by making the methodology more prescriptive for RPC/streaming frameworks.
