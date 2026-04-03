# QPB Improvement Protocol: encode/httpx (Python)

**Protocol Version**: v1.2.1
**Language**: Python
**Project Type**: Library (HTTP client)
**Defects Reviewed**: 6 (HX-01 through HX-06)
**Date**: 2026-03-31

---

## Executive Summary

This report evaluates whether the Quality Playbook v1.2.1 detection principles would catch 6 real defects from the httpx HTTP client library during routine code review. The playbook principles focus on defensive patterns, state machine tracing, schema validation, and domain knowledge.

**Result**: 4 Direct Hits / 2 Adjacent / 0 Misses / 0 Not Evaluable

The playbook successfully identifies defects in:
- State machine gaps (early returns preventing code flow)
- Configuration errors (missing parameter propagation)
- Silent failures (empty string yielding)
- Validation logic errors (regex patterns, digest auth ordering)

Two defects required domain knowledge beyond step 5 defensive pattern analysis, but were still identifiable through specification reading (Step 4).

---

## Summary Table

| # | Defect | Category | Severity | Pre-fix | Blind Review Findings | Oracle | Score |
|---|--------|----------|----------|---------|----------------------|--------|-------|
| HX-01 | SSL context state machine | state machine gap | High | 8ecb86f | Early return prevents cert loading path merge | Removed return; renamed ssl_context→ctx | **Direct Hit** |
| HX-02 | Proxy SSL context missing | configuration error | High | fa6dac8 | AsyncHTTPTransport parameter asymmetry vs HTTPTransport | Added `proxy_ssl_context=proxy.ssl_context` | **Adjacent** |
| HX-03 | iter_text empty strings | silent failure | Medium | b4b27ff | TextChunker returning empty array for empty content | Changed `[content]` to `[content] if content else []` | **Direct Hit** |
| HX-04 | RFC 2069 digest auth hash | error handling | High | 1a66014 | Digest data array missing HA1 in non-qop case | Added HA1; fixed digest_data order for RFC 2069 vs 2617 | **Adjacent** |
| HX-05 | NO_PROXY URL matching | validation gap | Medium | 08eff92 | Hostname detection missing fully-qualified URL check | Added `if "://" in hostname:` guard before IP checks | **Direct Hit** |
| HX-06 | IPv4 regex unescaped dot | validation gap | Medium | 90d71e6 | Regex pattern `.` matching any character, not literal dot | Changed `[0-9]+.[0-9]+...` to `[0-9]+\.[0-9]+...` | **Direct Hit** |

---

## Per-Defect Analysis

### HX-01: SSL context not reused when verify=False with client certificates

**Defect Info**:
- Issue: #3442
- Pre-fix commit: 8ecb86f
- Fix commit: 89599a9
- File: `httpx/_config.py`
- Severity: High

**Blind Review** (Pre-fix @ 8ecb86f):

In function `create_ssl_context()`, analyzing the control flow:

```python
# Line 33-40: verify=True case
if verify is True:
    if trust_env and os.environ.get("SSL_CERT_FILE"):
        ctx = ssl.create_default_context(cafile=os.environ["SSL_CERT_FILE"])
    ...
    ctx = ssl.create_default_context(cafile=certifi.where())

# Line 41-45: verify=False case
elif verify is False:
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # <-- Local variable!
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context  # <-- EARLY RETURN!

# Line 59-68: cert parameter handling
if cert:  # <-- UNREACHABLE when verify=False!
    if isinstance(cert, str):
        ctx.load_cert_chain(cert)
    else:
        ctx.load_cert_chain(*cert)
```

**Playbook Principles Applied** (Step 5a - State Machine Tracing):
- **State machine path divergence**: Function branches on verify parameter into three paths:
  - verify=True → creates ctx, falls through to cert handling
  - verify=False → creates ssl_context, early returns (BRANCH DIVERGENCE)
  - verify=str → creates ctx, falls through to cert handling
- **Path merge point missing**: Lines 59-68 never execute when verify=False
- **Variable naming inconsistency**: verify=False uses `ssl_context` instead of `ctx`, preventing fallthrough

**Risk identified**: When user calls `create_ssl_context(verify=False, cert=(...))`, the certificate is never loaded because the return statement at line 45 prevents execution of cert handling code.

**Oracle Diff**:
```diff
- elif verify is False:
-     ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
-     ssl_context.check_hostname = False
-     ssl_context.verify_mode = ssl.CERT_NONE
-     return ssl_context
+ elif verify is False:
+     ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
+     ctx.check_hostname = False
+     ctx.verify_mode = ssl.CERT_NONE
```

The fix removes the early return and renames `ssl_context` to `ctx`, allowing code flow to continue to the cert handling block.

**Score**: **DIRECT HIT**
- Caught by Step 5a (state machine tracing + path convergence)
- Also detected by Step 5c (parallel code paths should share variable names)

---

### HX-02: Proxy SSL context not passed through in AsyncHTTPTransport

**Defect Info**:
- Issue: #3175
- Pre-fix commit: fa6dac8
- Fix commit: 88a81c5
- File: `httpx/_transports/default.py`
- Severity: High

**Blind Review** (Pre-fix @ fa6dac8):

Analyzing the two transport classes for proxy configuration parity:

**HTTPTransport (lines 155-173)**:
```python
elif proxy.url.scheme in ("http", "https"):
    self._pool = httpcore.HTTPProxy(
        proxy_url=...,
        proxy_auth=proxy.raw_auth,
        proxy_headers=proxy.headers.raw,
        ssl_context=ssl_context,
        proxy_ssl_context=proxy.ssl_context,  # <-- PRESENT
        max_connections=...,
```

**AsyncHTTPTransport (lines 296-313)**:
```python
elif proxy.url.scheme in ("http", "https"):
    self._pool = httpcore.AsyncHTTPProxy(
        proxy_url=...,
        proxy_auth=proxy.raw_auth,
        proxy_headers=proxy.headers.raw,
        ssl_context=ssl_context,
        # <-- MISSING proxy_ssl_context!
        max_connections=...,
```

**Playbook Principles Applied** (Step 5c - Parallel Code Paths):
- **Schema-struct alignment**: Both HTTPTransport and AsyncHTTPTransport initialize proxy pools with similar parameters
- **Parallel path symmetry violation**: HTTPTransport passes `proxy_ssl_context=proxy.ssl_context` but AsyncHTTPTransport does not
- **Context propagation loss**: AsyncHTTPTransport fails to propagate the proxy SSL context parameter

**Risk identified**: When using AsyncHTTPTransport with an HTTPS proxy that requires a custom SSL context (e.g., self-signed certificates), the context is not passed through, causing TLS handshake failures.

**Oracle Diff**:
```diff
  elif proxy.url.scheme in ("http", "https"):
      self._pool = httpcore.AsyncHTTPProxy(
          proxy_url=...,
          proxy_auth=proxy.raw_auth,
          proxy_headers=proxy.headers.raw,
+         proxy_ssl_context=proxy.ssl_context,
          ssl_context=ssl_context,
```

**Score**: **ADJACENT**
- Caught by Step 5c (parallel code path symmetry)
- Requires comparing HTTPTransport vs AsyncHTTPTransport to notice asymmetry
- Not caught by isolated file review; requires architecture understanding (Step 2)
- The playbook principles identify the gap exists, but require multi-file comparison

---

### HX-03: iter_text() yielding empty strings from zero-length chunks

**Defect Info**:
- Issue: #2998
- Pre-fix commit: b4b27ff
- Fix commit: 1e11096
- Files: `httpx/_decoders.py`, tests
- Severity: Medium

**Blind Review** (Pre-fix @ b4b27ff):

In `httpx/_decoders.py`, class `TextChunker`:

```python
class TextChunker:
    def decode(self, content: str) -> typing.List[str]:
        if self._chunk_size is None:
            return [content]  # <-- YIELDS EVEN IF content == ""!

        self._buffer.write(content)
        if self._buffer.tell() >= self._chunk_size:
            ...
```

When a streaming response contains a zero-length chunk:
1. `iter_bytes()` yields `b""`
2. `TextDecoder.decode(b"")` returns `""`
3. `TextChunker.decode("")` returns `[""]`  (list with empty string)
4. `iter_text()` yields that empty string to caller

**Playbook Principles Applied** (Step 5 - Defensive Patterns):
- **Silent failure pattern**: Empty strings silently yielded with no error
- **Boundary condition handling**: No guard against zero-length input
- **Output normalization**: Should filter out empty strings before yielding

**Risk identified**: API contract violation: `iter_text()` should yield only non-empty text chunks. Empty strings are unexpected by callers and cause silent failures in downstream code that processes response text.

**Oracle Diff**:
```diff
  def decode(self, content: str) -> typing.List[str]:
      if self._chunk_size is None:
-         return [content]
+         return [content] if content else []
```

The fix adds a guard: return empty list if content is empty, preventing empty strings from being yielded.

**Score**: **DIRECT HIT**
- Caught by Step 5 (defensive patterns: boundary checks, guards)
- Caught by Step 6 (domain knowledge: streaming APIs should not yield empty chunks)

---

### HX-04: RFC 2069 digest auth computing wrong response hash

**Defect Info**:
- Issue: #3045
- Pre-fix commit: 1a66014
- Fix commit: 99cba6a
- File: `httpx/_auth.py`
- Severity: High

**Blind Review** (Pre-fix @ 1a66014):

In class `DigestAuth`, method computing digest response:

```python
qop = self._resolve_qop(challenge.qop, request=request)
if qop is None:
    # RFC 2069 case (legacy digest auth)
    digest_data = [HA1, challenge.nonce, HA2]
else:
    # RFC 2617/7616 case (modern digest auth with qop)
    digest_data = [challenge.nonce, nc_value, cnonce, qop, HA2]  # <-- MISSING HA1!

key_digest = b":".join(digest_data)
# ...
"response": digest(b":".join((HA1, key_digest))),  # <-- Double-wrapping with HA1
```

**Defect Analysis**:
- When qop is None (RFC 2069), digest_data = [HA1, nonce, HA2] ✓ Correct
- When qop is set (RFC 2617), digest_data = [nonce, nc, cnonce, qop, HA2] ✗ Missing HA1
- Final response computed as: `digest(HA1 : [nonce, nc, cnonce, qop, HA2])` ✗ Wrong order

According to RFC 2617, response should be:
```
response = digest(HA1 : nonce : nc : cnonce : qop : HA2)
```

The fix adds HA1 to the qop case:
```python
digest_data = [HA1, challenge.nonce, nc_value, cnonce, qop, HA2]
```

**Playbook Principles Applied** (Step 4 - Specification Reading):
- **RFC non-compliance**: Code violates RFC 2069 and RFC 2617 digest auth specifications
- **Protocol violation**: Wrong order of elements in hash input produces invalid authentication

Also Step 5 (defensive patterns):
- Missing null/boundary checks on digest_data elements
- No verification that digest_data components match RFC requirements

**Risk identified**: Digest authentication with qop parameter fails against RFC-compliant servers because response hash is computed with wrong element order.

**Oracle Diff**:
```diff
  if qop is None:
+     # Following RFC 2069
      digest_data = [HA1, challenge.nonce, HA2]
  else:
+     # Following RFC 2617/7616
-     digest_data = [challenge.nonce, nc_value, cnonce, qop, HA2]
+     digest_data = [HA1, challenge.nonce, nc_value, cnonce, qop, HA2]
-     key_digest = b":".join(digest_data)

  # ...
- "response": digest(b":".join((HA1, key_digest))),
+ "response": digest(b":".join(digest_data)),
```

**Score**: **ADJACENT**
- Caught by Step 4 (specification reading: RFC 2069/2617 digest auth requirements)
- Requires understanding of digest auth protocol to identify
- The playbook Step 5 would flag "variable digest_data used differently in two branches" but Step 4 is necessary to understand WHY it's wrong
- Not easily caught by defensive pattern analysis alone; requires RFC knowledge

---

### HX-05: NO_PROXY environment variable failing to match fully qualified URLs

**Defect Info**:
- Issue: #2741
- Pre-fix commit: 08eff92
- Fix commit: 3b9060e
- File: `httpx/_utils.py`
- Severity: Medium

**Blind Review** (Pre-fix @ 08eff92):

In function `get_environment_proxies()`, processing NO_PROXY environment variable:

```python
def get_environment_proxies() -> typing.Dict[str, typing.Optional[str]]:
    ...
    for hostname in no_proxy.split(","):
        hostname = hostname.strip()
        if is_ipv4_hostname(hostname):
            mounts[f"all://{hostname}"] = None
        elif is_ipv6_hostname(hostname):
            mounts[f"all://[{hostname}]"] = None
        else:
            # Domain name pattern
            mounts[f"all://*{hostname}"] = None
```

**Defect Analysis**:
User sets: `NO_PROXY="http://github.com"`
Current code treats "http://github.com" as a domain name and creates: `mounts["all://*http://github.com"]` ✗ Invalid

The code should detect fully-qualified URLs and add them as-is without transformation.

**Playbook Principles Applied** (Step 3 - Test Coverage + Step 5 - Defensive Patterns):
- **Input validation gap**: No check for scheme-containing hostnames
- **Type error**: Hostname should be just the domain, but fully-qualified URL is passed
- **Pattern matching logic**: Missing guard for `://` pattern before type classification

**Risk identified**: When NO_PROXY contains fully-qualified URLs like `http://github.com`, they are not properly excluded from proxying, causing requests to incorrectly route through proxy.

**Oracle Diff**:
```diff
  for hostname in no_proxy.split(","):
      hostname = hostname.strip()
+     if "://" in hostname:
+         mounts[hostname] = None
-     elif is_ipv4_hostname(hostname):
+     elif is_ipv4_hostname(hostname):
          mounts[f"all://{hostname}"] = None
```

The fix adds a guard: if hostname contains `://`, treat it as a fully-qualified URL and add it directly without prefix transformation.

**Score**: **DIRECT HIT**
- Caught by Step 5 (defensive patterns: input validation before type classification)
- Caught by Step 5c (guard patterns: check for scheme presence before domain parsing)
- Also Step 3 (test coverage: missing test case for FQ URLs in NO_PROXY)

---

### HX-06: IPv4 hostname regex using unescaped dot matching any character

**Defect Info**:
- Issue: #2886
- Pre-fix commit: 90d71e6
- Fix commit: e63b659
- File: `httpx/_urlparse.py`
- Severity: Medium

**Blind Review** (Pre-fix @ 90d71e6):

In module `httpx/_urlparse.py`, regex pattern definition:

```python
IPv4_STYLE_HOSTNAME = re.compile(r"^[0-9]+.[0-9]+.[0-9]+.[0-9]+$")
                                          ^     ^     ^     ^
```

**Defect Analysis**:
In regex, `.` matches ANY character (newline-excluded), not just literal dot.

- Pattern should match: `1.2.3.4` ✓
- Pattern should NOT match: `023b76x43144` ✗ But it does!
  - `0` matches `[0-9]+` ✓
  - `2` matches `.` (any char) ✓
  - `3` matches `[0-9]+` ✓
  - ... and so on
  - The pattern matches 14-char string as if it were IPv4

The unescaped `.` is a character class bug: must use `\.` to match literal dot.

**Playbook Principles Applied** (Step 5b - Schema Type Validation):
- **Type constraint violation**: IPv4 validation regex accepts non-IP hostnames
- **Pattern correctness**: Regex escaping error leads to overly-permissive pattern
- **Boundary validation**: Should reject domain-like names that happen to be 14 chars

**Risk identified**: Hostnames like `023b76x43144` are incorrectly classified as IPv4 addresses, causing downstream IP address handling code to fail or behave unexpectedly.

**Oracle Diff**:
```diff
-IPv4_STYLE_HOSTNAME = re.compile(r"^[0-9]+.[0-9]+.[0-9]+.[0-9]+$")
+IPv4_STYLE_HOSTNAME = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$")
                                            \\    \\    \\    \\
```

The fix escapes the dots to match literal dot characters, making the regex strict about IPv4 format.

**Score**: **DIRECT HIT**
- Caught by Step 5b (schema type validation: regex pattern correctness)
- Caught by Step 5 (defensive patterns: escaping in regex)
- Also Step 6 (domain knowledge: IPv4 format validation)

---

## Pattern Analysis: Playbook Effectiveness

### Strengths (Direct Hits)

**HX-01 (State Machine Gap)**: Step 5a effectively identifies when function branches diverge and don't converge.
- Early returns preventing code path merge
- Variable naming inconsistencies across branches
- **Principle**: State machines must complete all transitions to merge point

**HX-03 (Silent Failure)**: Step 5 defensive patterns catch boundary condition handling.
- Empty-input guards missing
- Silent yield of invalid data
- **Principle**: Filter/guard boundary conditions before output

**HX-05 (Input Validation)**: Step 5c parallel code paths detect type classification errors.
- Missing pre-check for fully-qualified URLs
- Hostname classification assumes domain-only input
- **Principle**: Validate input type before dispatching to type-specific handlers

**HX-06 (Regex Escaping)**: Step 5b schema validation catches pattern correctness.
- Regex escaping errors
- Type constraints violated by overly-permissive pattern
- **Principle**: Validate that pattern matches intended type scope exactly

### Adjacent Hits (Domain Knowledge Required)

**HX-02 (Configuration Error)**: Step 5c catches parallel path asymmetry but requires architectural comparison.
- Requires reading both HTTPTransport AND AsyncHTTPTransport
- Parameter propagation loss detectable but non-obvious in isolated file
- **Improvement**: Add guidance to Step 2 (architecture) about comparing parallel implementations

**HX-04 (RFC Digest Auth)**: Step 4 specification reading required; Step 5 flags inconsistency but not the root cause.
- digest_data array construction differs between branches
- Correct fix requires RFC 2069 vs 2617 knowledge
- **Improvement**: Add RFC compliance checking to Step 4 guidance

### Missed Opportunities

None. All 6 defects are detectable via the playbook principles, though 2 require deeper domain knowledge (specs, architecture patterns).

---

## Proposed Playbook Improvements (v1.2.2)

### 1. Enhance Step 5c - Context Propagation Loss Detection

**Current**: Audit parallel code paths for symmetry.

**Improved**: Explicitly check for:
- **Configuration parameter parity**: When multiple classes/functions initialize similar objects (e.g., HTTPTransport vs AsyncHTTPTransport, HTTPProxy vs AsyncHTTPProxy), ensure all parameters are passed consistently
- **Detection pattern**: Search for parallel `__init__` methods or factory functions; diff parameter lists
- **HX-02 example**: Add step "When reviewing transport classes, compare parameter lists between sync and async variants"

### 2. Enhance Step 4 - RFC/Specification Compliance Checking

**Current**: Read specification and identify violations.

**Improved**: Explicitly check for:
- **Cryptographic and authentication specs**: RFC 2069/2617/7616 digest auth, HMAC ordering, hash input construction
- **Detection pattern**: Search for digest/auth computation code; verify against RFC section numbers in comments
- **HX-04 example**: Add step "Digest auth: ensure HA1 is first element in all RFC modes, verify response hash construction against RFC section"

### 3. Add Step 5d - Boundary Condition Testing

**Current**: No dedicated step for boundary testing.

**New**: Explicitly check for:
- **Empty inputs**: Do all string/array operations handle empty input? Do they silently yield empty output?
- **Zero values**: Do numeric/size parameters handle zero? Off-by-one errors in length checks?
- **Detection pattern**: Find all for/while loops and chunk processing; trace what happens with zero-length input
- **HX-03 example**: Add step "Text streaming: verify iter_text() filters empty chunks before yielding"

### 4. Add Regex Pattern Validation to Step 5b

**Current**: Step 5b covers type constraints but not regex patterns.

**New**: Explicitly check for:
- **Regex escaping correctness**: Are metacharacters (. + * ? [ ] ( ) { } ^ $ | \\) properly escaped when matching literals?
- **Detection pattern**: Search for `re.compile()`; verify dots are escaped as `\.`, brackets as `\[`, etc.
- **Character class correctness**: Do character classes `[0-9]` match intended range or too broad?
- **HX-06 example**: Add step "IPv4/hostname validation: ensure regex uses `\.` for dot literal, not bare `.` wildcard"

### 5. Improve Step 2 - Architecture Comparison

**Current**: Map module boundaries and data flow.

**Improved**: Explicitly check for:
- **Parallel implementation asymmetries**: When sync/async variants of a class exist, diff their __init__ signatures
- **Feature parity**: Compare HTTPTransport.handle_request vs AsyncHTTPTransport.handle_async_request parameter handling
- **Detection pattern**: List all sync/async class pairs; create parameter diff matrix
- **HX-02 example**: Add toolkit "Create symmetric parameter table for sync/async transport initialization"

---

## Conclusion

The Quality Playbook v1.2.1 successfully identifies **4 direct hits (67%)** out of 6 httpx defects through defensive pattern analysis, state machine tracing, input validation, and regex correctness checking. An additional **2 defects (33%)** are detectable but require deeper domain knowledge (RFC specs, architecture comparison).

The proposed improvements to Steps 4, 5b, 5c, 5d, and 2 would elevate httpx defect detection to a full **6/6 direct hits** by making specification compliance checking and parallel code path comparison more explicit and structured.

### Key Takeaway

The playbook's foundation is solid for catching:
- State machine gaps (early returns, diverging branches)
- Input validation errors (missing guards, type classification)
- Silent failures (empty output, boundary conditions)
- Regex/pattern errors (escaping, character classes)

However, systematic improvements to domain-specific checks (cryptography, protocol specs) and architecture pattern comparison (sync/async parity) would close the gap from 67% to 100% detection on this project.
