# Code Review: CHI-12

Reviewed files in `/tmp/qpb_v1211_sonnet_CHI-12` following the six focus areas in `RUN_CODE_REVIEW.md`.

---

## middleware/recoverer.go

### Line 24: BUG — `http.ErrAbortHandler` is swallowed, not re-panicked

**Severity: Critical**

```go
// reviewed code
if rvr := recover(); rvr != nil && rvr != http.ErrAbortHandler {
    // ... logging ...
    w.WriteHeader(http.StatusInternalServerError)
}
```

When `rvr == http.ErrAbortHandler`, the combined condition is `false` and the deferred function returns normally — consuming the panic without re-propagating it. The correct behavior (per reference implementation) is to explicitly call `panic(rvr)` after detecting `ErrAbortHandler`:

```go
// correct pattern
if rvr := recover(); rvr != nil {
    if rvr == http.ErrAbortHandler {
        panic(rvr)  // re-panic so net/http can abort the connection
    }
    // ... logging ...
}
```

**Why it matters:** `http.ErrAbortHandler` is Go's net/http mechanism to abort a response mid-stream and close the connection. The server's internal goroutine recovery path checks for this panic value to suppress logging and terminate the connection cleanly. If Recoverer swallows it instead of re-panicking, the server goroutine sees a normal return and may attempt to write further data on a connection the handler intended to abort, silently corrupting the HTTP stream. This is a spec violation per QUALITY.md Scenario 6: "Recoverer must not catch `http.ErrAbortHandler`."

---

### Line 33: BUG — Missing `Connection: Upgrade` guard before writing HTTP 500

**Severity: High**

```go
// reviewed code — no upgrade check
w.WriteHeader(http.StatusInternalServerError)
```

**Expected** (reference implementation):
```go
if r.Header.Get("Connection") != "Upgrade" {
    w.WriteHeader(http.StatusInternalServerError)
}
```

For WebSocket and other upgraded connections, the HTTP handshake has already completed and the connection is no longer speaking HTTP at the time the handler runs. Calling `w.WriteHeader(500)` on an upgraded connection writes HTTP framing bytes into a stream that the remote end is parsing as WebSocket (or another protocol), corrupting the connection.

**Why it matters:** Any handler that upgrades a connection and then panics will have Recoverer write a spurious HTTP 500, injecting invalid bytes into the upgraded stream. This will cause the remote end (browser, WebSocket client) to see a protocol error and close the connection with a confusing status, rather than a clean abort.

---

## middleware/realip.go

### Line 43: BUG — Missing `net.ParseIP()` validation

**Severity: High**

```go
// reviewed code — no IP validation
func realIP(r *http.Request) string {
    var ip string
    if xrip := r.Header.Get(xRealIP); xrip != "" {
        ip = xrip
    } else if xff := r.Header.Get(xForwardedFor); xff != "" {
        i := strings.Index(xff, ", ")
        if i == -1 {
            i = len(xff)
        }
        ip = xff[:i]
    }
    return ip
}
```

The function returns the raw header value without validating it is a valid IP address. `RealIP` then unconditionally sets `r.RemoteAddr = rip` (line 32 of the same file) whenever the return value is non-empty.

**Expected** (reference implementation):
```go
if ip == "" || net.ParseIP(ip) == nil {
    return ""
}
return ip
```

**Why it matters:** An attacker who can influence `X-Real-IP` or `X-Forwarded-For` (e.g., a misconfigured proxy that forwards client-supplied headers) can inject arbitrary strings — `"attacker@example.com"`, `"127.0.0.1, injected"`, or structured attack payloads — as `r.RemoteAddr`. Any downstream IP-based access control, rate limiting, or audit log that reads `r.RemoteAddr` would operate on attacker-controlled data, fully bypassing IP-based security controls. This is the exact vulnerability scenario described in QUALITY.md Scenario 5.

---

### Line 40: BUG — Missing `True-Client-IP` header; wrong priority order

**Severity: Medium**

```go
// reviewed code — only two headers, wrong priority
var xForwardedFor = http.CanonicalHeaderKey("X-Forwarded-For")
var xRealIP = http.CanonicalHeaderKey("X-Real-IP")

func realIP(r *http.Request) string {
    if xrip := r.Header.Get(xRealIP); xrip != "" {
        ip = xrip
    } else if xff := r.Header.Get(xForwardedFor); xff != "" {
        ...
    }
}
```

The `True-Client-IP` header is completely absent. The required priority chain is `True-Client-IP > X-Real-IP > X-Forwarded-For` (documented in QUALITY.md Scenario 5 and the reference implementation).

**Why it matters:** CDN providers (Cloudflare, Akamai) and some reverse proxies set `True-Client-IP` as the authoritative client IP, while `X-Real-IP` may contain an intermediate proxy address. If `True-Client-IP` is ignored, applications behind such CDNs will log, rate-limit, and make access-control decisions based on the CDN's internal IP rather than the actual client IP. This produces incorrect audit logs and broken per-IP rate limiting.

---

## mux.go

### Line 87: QUESTION — `pool.Put(rctx)` is not deferred

**Severity: Low**

```go
mx.handler.ServeHTTP(w, r)
mx.pool.Put(rctx)   // not deferred
```

If `mx.handler.ServeHTTP` panics (and no Recoverer middleware is present, or the panic propagates past it), `pool.Put` is never called. The `RouteContext` is not returned to the pool and is effectively leaked for that request.

This is the same pattern as the reference implementation, so it appears to be a deliberate design choice (presumably on the assumption that Recoverer is present or panics are acceptable to leak). Flagging as a QUESTION rather than a BUG because it matches the reference. If the pool is intended to be unconditionally safe, a `defer mx.pool.Put(rctx)` would be the correct fix.

---

## Files with no findings

- `mux.go` — Focus Areas 1, 4: Use() panic guard (line 97–98), handle() nil check (line 391), ServeHTTP fallback (line 62), inline bypass (line 397–399), Mount() duplicate check (line 286), nextRoutePath() prefix stripping (line 446–452), wildcard param reset (line 307) — all correct.
- `context.go` — Focus Area 3: Reset() zeroes all fields with `[:0]` re-slicing (lines 83–96), called before Routes assignment (mux.go:78–79). Focus Area 6: URLParam iterates backward (line 101), returns "" on miss (line 106), RouteContext uses safe `_, ok` type assertion (line 29). All correct.
- `tree.go` — Focus Area 2: Node type constants enforce Static(0) > Regexp(1) > Param(2) > CatchAll(3) ordering; `findRoute` iterates `children` in type-index order preserving this priority; regexp patterns anchored with `^`/`$` in `patNextSegment` (lines 715–722); cross-segment `/` protected for params (line 441–444). All correct.
- `middleware/timeout.go` — Focus Area 5: `ctx.Err() == context.DeadlineExceeded` check runs inside `defer` after `next.ServeHTTP` returns (lines 37–42); only writes 504 on deadline, not on cancellation. Correct.
- `middleware/throttle.go` — Focus Area 5: `Limit < 1` and `BacklogLimit < 0` panic guards present (lines 44–49); `backlogTokens` capacity is `Limit + BacklogLimit` (line 54). Correct.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 1     |
| High     | 2     |
| Medium   | 1     |
| Low      | 0 (1 QUESTION) |

**Overall assessment: FIX FIRST**

Three of the four bugs are in middleware that users deploy for security and correctness: `Recoverer` silently swallows `ErrAbortHandler` (corrupts HTTP stream on abort), `Recoverer` writes HTTP status on upgraded connections (corrupts WebSocket stream), and `RealIP` skips IP validation (security bypass). These must be fixed before this code is used in production.
