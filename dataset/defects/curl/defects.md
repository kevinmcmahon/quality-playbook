# curl/curl Defects — Quality Playbook Benchmark (QPB)

**Repository**: [curl/curl](https://github.com/curl/curl)
**Language**: C
**Repo type**: Library
**Defect count**: 5 of 49 (CURL-01 through CURL-05; format sample)
**Generated**: 2026-03-29

---

## CURL-01 | Use-After-Free in Transfer URL Pointer | error handling | High

**Fix commit**: [`86b39c2`](https://github.com/curl/curl/commit/86b39c2)
**Pre-fix commit**: `28fbf4a8`
**Issue/PR**: [#21123](https://github.com/curl/curl/pull/21123)

**Files changed**:
- `lib/transfer.c`

**Commit message**:
```
transfer: clear the URL pointer in OOM to avoid UAF

Since the pointer can be extracted with CURLINFO_EFFECTIVE_URL later it
must not linger pointing to freed memory.

Found by Codex Security

Closes #21123
```

**Issue/PR summary**:
PR #21123 by Daniel Stenberg (bagder). The fix addresses a memory safety vulnerability where `data->state.url` could reference freed memory if `curl_url_get()` fails during `Curl_pretransfer()` execution when `CURLOPT_CURLU` is active. Since the pointer can be extracted with `CURLINFO_EFFECTIVE_URL` later, it must not linger pointing to freed memory. Found by Codex Security.

**Defect summary**: Use-after-free in CURLINFO_EFFECTIVE_URL via OOM path. The `data->state.url` pointer was not cleared when URL extraction failed during pre-transfer setup, leaving a dangling pointer that could be dereferenced by subsequent info queries.

**Diff stat**:
```
lib/transfer.c | 2 ++
 1 file changed, 2 insertions(+)
```

**Playbook angle**: Pointer nullification on allocation failure. Step 6 (error handling) should catch dangling pointer patterns in OOM paths.

---

## CURL-02 | Integer Overflow in Socket Connection on Solaris | missing boundary check | Medium

**Fix commit**: [`248b929`](https://github.com/curl/curl/commit/248b929)
**Pre-fix commit**: `860c57d`
**Issue/PR**: [#21111](https://github.com/curl/curl/pull/21111)

**Files changed**:
- `lib/cf-socket.c`

**Commit message**:
```
cf-socket: avoid low risk integer overflow on ancient Solaris

Spotted by Codex Security

Closes #21111
```

**Issue/PR summary**:
PR #21111 by Daniel Stenberg (bagder). A low-risk integer overflow vulnerability on legacy Solaris systems in socket connectivity code. The PR consisted of a single commit addressing potential integer overflow conditions when computing socket connection parameters. Spotted by Codex Security.

**Defect summary**: Low-risk integer overflow in socket connection on ancient Solaris. Arithmetic on socket-related values could overflow on platforms with narrower integer widths.

**Diff stat**:
```
lib/cf-socket.c | 11 +++++++++--
 1 file changed, 9 insertions(+), 2 deletions(-)
```

**Playbook angle**: Defensive arithmetic bounds checking. Step 5b (schema types) should flag unsafe arithmetic on platform-dependent integer widths.

---

## CURL-03 | Memory Allocation/Deallocation Mismatches | error handling | High

**Fix commit**: [`b71973c`](https://github.com/curl/curl/commit/b71973c)
**Pre-fix commit**: `46d0ade`
**Issue/PR**: [#21099](https://github.com/curl/curl/pull/21099)

**Files changed**:
- `lib/curlx/dynbuf.c`
- `src/tool_cb_hdr.c`
- `src/tool_cfgable.c`
- `src/tool_help.c`
- `src/tool_operate.c`
- `src/tool_operhlp.c`
- `src/var.c`

**Commit message**:
```
tool: fix memory mixups

memory allocated by libcurl must be freed with curl_free() and vice versa,
memory allocated by the tool itself must be freed with curlx_free().

- dynbuf: free libcurl data with curl_free()
- tool_operate: make sure we get URL using the right memory
- tool_operhlp: free libcurl memory with curl_free()
- tool_operate: free curl_maprintf() pointer with curl_free
- var: data from curlx_base64_decode needs curlx_free
- tool_operate: fix memory juggling in etag handling
- tool_cb_hdr: fix memory area mixups
- tool_operate: another mixup in etag management
- tool_cb_hdr: more memory mixup fixes
- tool_cfgable.c: document some details
- tool_help: show global-mem-debug in -V output

Closes #21099
```

**Issue/PR summary**:
PR #21099 by Daniel Stenberg (bagder). Addresses several critical memory management issues: memory allocated by libcurl must be freed with `curl_free()`, and memory allocated by the tool itself must be freed with `curlx_free()`. The PR also adds `--enable-init-mem-debug` / `CURL_DEBUG_GLOBAL_MEM` to detect memory mixups using custom allocators, adds "global-mem-debug" to curl's feature list, and introduces a new valgrind CI job to catch allocator mismatches.

**Defect summary**: Multiple memory allocation/deallocation mismatches across 7 files. The curl tool was using the wrong free function (curl_free vs curlx_free) for memory returned from different allocation sources, which could corrupt the heap when custom allocators are active.

**Diff stat**:
```
lib/curlx/dynbuf.c |  2 +-
 src/tool_cb_hdr.c  | 22 +++++++++++++++-------
 src/tool_cfgable.c | 23 ++++++++++++++++-------
 src/tool_help.c    |  6 ++++++
 src/tool_operate.c | 29 +++++++++++++++++++++--------
 src/tool_operhlp.c | 11 ++++++++---
 src/var.c          |  4 ++--
 7 files changed, 69 insertions(+), 28 deletions(-)
```

**Playbook angle**: Allocator consistency enforcement. Step 6 (error handling) should flag mismatched alloc/free pairs across API boundaries.

---

## CURL-04 | Incorrect Free Function for Escaped URL | error handling | High

**Fix commit**: [`29dfc02`](https://github.com/curl/curl/commit/29dfc02)
**Pre-fix commit**: `14712fa`
**Issue/PR**: [#21075](https://github.com/curl/curl/pull/21075)

**Files changed**:
- `src/tool_getparam.c`

**Commit message**:
```
tool_getparam: use correct free function for libcurl memory

Memory returned from curl_easy_escape() should be fred with curl_free()
to avoid surprises.

Follow-up to f37840a46e5eddaf109c16fa7

Spotted by Codex Security
Closes #21075
```

**Issue/PR summary**:
PR #21075 by Daniel Stenberg (bagder). The fix ensures that strings returned from `curl_easy_escape()` are properly freed using `curl_free()` rather than the tool's internal memory management functions. This prevents potential problems when libcurl uses custom memory allocators. The implementation duplicates the escaped output into tool-owned memory and properly frees the original libcurl allocation. Follow-up to commit f37840a. Spotted by Codex Security.

**Defect summary**: Incorrect free function for `curl_easy_escape()` return value. The tool was using its internal free function on memory owned by libcurl, which would corrupt the heap when custom allocators are configured.

**Diff stat**:
```
src/tool_getparam.c | 6 +++++-
 1 file changed, 5 insertions(+), 1 deletion(-)
```

**Playbook angle**: Allocation context tracking. Step 6 (error handling) should verify that return values from library functions are freed with the library's own free function.

---

## CURL-05 | Memory Leak on Failed Uploads | error handling | Medium

**Fix commit**: [`9820e5d`](https://github.com/curl/curl/commit/9820e5d)
**Pre-fix commit**: `e8c64a0`
**Issue/PR**: [#21062](https://github.com/curl/curl/pull/21062)

**Files changed**:
- `src/tool_operate.c`
- `tests/data/Makefile.am`
- `tests/data/test1673`

**Commit message**:
```
tool_operate: fix memory-leak on failed uploads

Add test case 1673 to do repeated upload failures and verify there is no
leak. This proved a previous leak and now it verifies the fix.

Reported-by: James Fuller
Closes #21062
```

**Issue/PR summary**:
PR #21062 by Daniel Stenberg (bagder). Addresses a memory leak occurring when curl tool uploads fail, particularly in retry scenarios. The fix centralizes per-transfer resource cleanup in a `del_per_transfer()` function, encompassing `per->curl`, `per->url`, `per->outfile`, and `per->uploadfile`, eliminating redundant cleanup code from `post_per_transfer()`. Includes test case 1673 with repeated upload failures to verify no leak. Reported by James Fuller.

**Defect summary**: Memory leak on repeated upload failures. Per-transfer resources (curl handle, URL, output file, upload file) were not consistently cleaned up when uploads failed, causing cumulative memory leaks in retry scenarios.

**Diff stat**:
```
src/tool_operate.c     |  8 ++++----
 tests/data/Makefile.am |  2 +-
 tests/data/test1673    | 25 +++++++++++++++++++++++++
 3 files changed, 30 insertions(+), 5 deletions(-)
```

**Playbook angle**: Resource cleanup in error paths. Step 6 (error handling) should verify that all allocated resources are freed on all exit paths, especially error/retry paths.

---
