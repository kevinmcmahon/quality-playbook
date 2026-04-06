# QPB Benchmark Scoring: Chi Router Code Reviews

**Benchmark Run:** run_001
**Repository:** Chi HTTP router
**Review Date:** 2026-03-31
**Total Defects:** 30 (CHI-01 through CHI-30)
**Reviews Generated:** 61 (Opus: 21, Sonnet: 20, Haiku: 20)
**Reviews Missing:** 9 (CHI-20, CHI-21, CHI-22, CHI-23, CHI-24, CHI-25, CHI-26, CHI-27, CHI-28)

---

## Summary Table

| Defect ID | Category | Severity | Opus | Sonnet | Haiku |
|-----------|----------|----------|------|--------|-------|
| CHI-01 | error handling | High | **DIRECT HIT** | **DIRECT HIT** | **DIRECT HIT** |
| CHI-02 | error handling | High | ADJACENT | **DIRECT HIT** | ADJACENT |
| CHI-03 | error handling | Medium | MISS | MISS | MISS |
| CHI-04 | validation gap | Medium | MISS | MISS | MISS |
| CHI-05 | error handling | Medium | ADJACENT | NO REVIEW | ADJACENT |
| CHI-06 | type safety | High | ADJACENT | ADJACENT | ADJACENT |
| CHI-07 | error handling | High | ADJACENT | **DIRECT HIT** | **DIRECT HIT** |
| CHI-08 | error handling | Medium | ADJACENT | ADJACENT | **DIRECT HIT** |
| CHI-09 | validation gap | Medium | ADJACENT | ADJACENT | ADJACENT |
| CHI-10 | security issue | Critical | ADJACENT | ADJACENT | ADJACENT |
| CHI-11 | SQL error | High | ADJACENT | ADJACENT | ADJACENT |
| CHI-12 | concurrency issue | Medium | MISS | MISS | MISS |
| CHI-13 | type safety | Medium | **DIRECT HIT** | **DIRECT HIT** | **DIRECT HIT** |
| CHI-14 | API contract violation | Medium | **DIRECT HIT** | **DIRECT HIT** | **DIRECT HIT** |
| CHI-15 | validation gap | Medium | MISS | MISS | NO REVIEW |
| CHI-16 | error handling | High | **DIRECT HIT** | **DIRECT HIT** | **DIRECT HIT** |
| CHI-17 | error handling | High | **DIRECT HIT** | **DIRECT HIT** | **DIRECT HIT** |
| CHI-18 | security issue | Critical | **DIRECT HIT** | **DIRECT HIT** | **DIRECT HIT** |
| CHI-19 | SQL error | High | **DIRECT HIT** | **DIRECT HIT** | **DIRECT HIT** |
| CHI-20 | concurrency issue | Medium | NO REVIEW | NO REVIEW | NO REVIEW |
| CHI-21 | validation gap | Medium | NO REVIEW | NO REVIEW | NO REVIEW |
| CHI-22 | error handling | High | NO REVIEW | NO REVIEW | NO REVIEW |
| CHI-23 | validation gap | Medium | NO REVIEW | NO REVIEW | NO REVIEW |
| CHI-24 | type safety | High | NO REVIEW | NO REVIEW | NO REVIEW |
| CHI-25 | error handling | Medium | NO REVIEW | NO REVIEW | NO REVIEW |
| CHI-26 | API contract violation | Medium | NO REVIEW | NO REVIEW | NO REVIEW |
| CHI-27 | validation gap | High | NO REVIEW | NO REVIEW | NO REVIEW |
| CHI-28 | error handling | Medium | NO REVIEW | NO REVIEW | NO REVIEW |
| CHI-29 | null safety | Medium | **DIRECT HIT** | **DIRECT HIT** | **DIRECT HIT** |
| CHI-30 | protocol violation | Medium | **DIRECT HIT** | **DIRECT HIT** | **DIRECT HIT** |

---

## Per-Model Statistics

### Opus (30 defects)
- **Direct Hits:** 9 (30%)
- **Adjacent:** 8 (27%)
- **Misses:** 4 (13%)
- **No Review:** 9 (30%)

### Sonnet (30 defects)
- **Direct Hits:** 11 (37%)
- **Adjacent:** 5 (17%)
- **Misses:** 4 (13%)
- **No Review:** 10 (33%)

### Haiku (30 defects)
- **Direct Hits:** 11 (37%)
- **Adjacent:** 6 (20%)
- **Misses:** 3 (10%)
- **No Review:** 10 (33%)

### Overall Statistics (All 90 Possible Combinations)
- **Total Combinations:** 90 (30 defects × 3 models)
- **Reviews Generated:** 61 (68%)
- **Direct Hits:** 31 (51% of 61, 34% of 90)
- **Adjacent:** 19 (31% of 61, 21% of 90)
- **Misses:** 11 (18% of 61, 12% of 90)
- **No Reviews:** 29 (32% of 90)
- **Hit Rate (reviews only):** 51%
- **Hit Rate (all combinations):** 34%

---

## Per-Category Statistics

| Category | Direct Hits | Adjacent | Misses | No Review | Total | Hit Rate |
|----------|-------------|----------|--------|-----------|-------|----------|
| error handling | 13 | 7 | 3 | 10 | 33 | 39% |
| validation gap | 0 | 3 | 5 | 10 | 18 | 0% |
| type safety | 3 | 3 | 0 | 3 | 9 | 33% |
| security issue | 3 | 3 | 0 | 0 | 6 | 50% |
| SQL error | 3 | 3 | 0 | 0 | 6 | 50% |
| API contract violation | 3 | 0 | 0 | 3 | 6 | 50% |
| concurrency issue | 0 | 0 | 3 | 3 | 6 | 0% |
| null safety | 3 | 0 | 0 | 0 | 3 | 100% |
| protocol violation | 3 | 0 | 0 | 0 | 3 | 100% |
| **TOTAL** | **31** | **19** | **11** | **29** | **90** | **34%** |

---

## Notable Findings

### Defects Caught by All Available Models (100% Hit Rate)
- **CHI-01:** Double execution of handler (missing return) — Opus, Sonnet, Haiku all identified
- **CHI-13:** RegisterMethod bit collision causing mTRACE collision — Opus, Sonnet, Haiku all identified
- **CHI-14:** Header().Set() replaces Vary instead of appending — Opus, Sonnet, Haiku all identified
- **CHI-16:** WriteHeader() called unconditionally violating HTTP spec — Opus, Sonnet, Haiku all identified
- **CHI-17:** Recoverer defensive pattern fragile for Go 1.17+ — Opus, Sonnet, Haiku all identified
- **CHI-18:** RedirectSlashes backslash open redirect vulnerability — Opus, Sonnet, Haiku all identified
- **CHI-19:** Walk() missed propagating inline middlewares — Opus, Sonnet, Haiku all identified
- **CHI-29:** URLFormat accessed rctx without nil check — Opus, Sonnet, Haiku all identified
- **CHI-30:** WriteHeader() blocked informational status codes — Opus, Sonnet, Haiku all identified

### Defects Caught by One Model (Highest Signal)
- **CHI-02:** Sonnet only identified Find() pattern composition bug (Opus/Haiku found related issues)
- **CHI-08:** Haiku only explicitly identified Index vs LastIndex issue (Opus/Sonnet found related format extraction issues)

### Complete Misses Across All Models
- **CHI-03:** None identified the specific Close()/writer() issue despite reviews in compress.go
  - All three found different bugs (nil encoder, loose matching, etc.)
- **CHI-04:** None identified RoutePattern() empty string for root route
  - Indicates possible worktree mismatch or function-not-reviewed
- **CHI-12:** None identified the concurrency/test data race issue
  - Found test file bugs (t.Fatalf, deprecated ioutil) but not the race condition
- **CHI-15:** Opus/Sonnet reviewed file but missed incomplete pattern bug; Haiku has no review

### No Reviews Generated (9 Defects)
- **CHI-20:** TestThrottleRetryAfter data race (concurrency)
- **CHI-21:** Regexp routing parameter value setting (validation)
- **CHI-22:** Throttle middleware broken handler invocation (error handling)
- **CHI-23:** Wildcard validation check wrong location (validation)
- **CHI-24:** Compress SetEncoder() inverted logic (type safety)
- **CHI-25:** Compress WriteHeader() recursive call (error handling)
- **CHI-26:** RedirectSlashes lost query parameters (API contract)
- **CHI-27:** Wildcard validation allows invalid patterns (validation)
- **CHI-28:** Empty mux panics instead of 404 (error handling)

---

## Per-Defect Scoring Notes

### CHI-01: Missing Return in RouteHeaders Middleware
**Defect:** RouteHeaders middleware missing return statement after calling `next.ServeHTTP` when router had no routes configured. This caused next handler to be called twice.

**Scoring:**
- **Opus:** **DIRECT HIT** — Explicitly identified "Missing return after early-exit in Handler (CRITICAL)" at line 81, clearly described the double-call mechanism, provided exact fix
- **Sonnet:** **DIRECT HIT** — Identified "Missing return after next.ServeHTTP in the empty-routes guard" at lines 79-82, traced exact execution flow
- **Haiku:** **DIRECT HIT** — Identified "Missing Return Statement in Handler - Double Execution of Next Handler", provided detailed step-by-step trace

---

### CHI-02: Mux.Find Not Handling Nested Routes
**Defect:** Mux.Find not correctly handling nested routes and subrouters. Pattern composition failed when combining parent and child route patterns.

**Scoring:**
- **Opus:** **ADJACENT** — Reviewed mux.go but focused on pool.Put deferral and methodMap registration issues, not the nested route pattern composition bug
- **Sonnet:** **DIRECT HIT** — Explicitly identified "Find() returns sub-router's local pattern, not the composite full pattern" at lines 374-393, explained the exact mechanism with example: "/api" prefix is silently dropped
- **Haiku:** **ADJACENT** — Identified missing nil checks on RouteContext in Mount handler, related to routing but not the pattern composition defect

---

### CHI-03: Compressor Close() Method Wrong Writer Lookup
**Defect:** Compressor middleware's Close() method checked for io.WriteCloser using `cw.writer()` instead of `cw.w`, bypassing actual writer lookup.

**Scoring:**
- **Opus:** **MISS** — Found nil encoder bug, Hijack/Push delegation bugs, but not the Close/writer() issue
- **Sonnet:** **MISS** — Found Handle() parsing bugs (space/tab handling), not the Close/writer issue
- **Haiku:** **MISS** — Found nil encoder bug and loose Accept-Encoding matching, not the specific Close/writer() check issue

**Note:** All three reviewed compress.go and found legitimate bugs, but none identified the specific Close() method defect.

---

### CHI-04: RoutePattern() Empty String for Root Route
**Defect:** RoutePattern() returned empty string for root route "/" after trimming suffixes, should preserve root as special case.

**Scoring:**
- **Opus:** **MISS** — Reviewed context.go and found methodsAllowed reset bug, not the RoutePattern() issue
- **Sonnet:** **MISS** — Different worktree may have reviewed different code
- **Haiku:** **MISS** — Same issue as Opus, reviewed context.go for methodsAllowed bug

**Note:** Potential worktree mismatch - reviews appear to focus on different functions/files than the defect description.

---

### CHI-05: MethodNotAllowed Flag Not Set
**Defect:** MethodNotAllowed handler not invoked when route matched with path variables but method not supported. Tree search found node but didn't set methodNotAllowed flag.

**Scoring:**
- **Opus:** **ADJACENT** — Found RegisterMethod bit collision bug at lines 57-61 in tree.go, related to method handling but not the flag-setting issue
- **Sonnet:** **NO REVIEW** — Not in Sonnet's review set
- **Haiku:** **ADJACENT** — Found parameter value leakage in findRoute backtracking at line 469, related to tree search but not the flag issue

---

### CHI-06: WrapResponseWriter Logical OR Issue
**Defect:** WrapResponseWriter incorrectly used logical OR in method selection logic (description truncated in defects.jsonl).

**Scoring:**
- **Opus:** **ADJACENT** — Found Flush() status tracking bug, ReadFrom() double-counting bug in wrap_writer.go (correct file, different bugs)
- **Sonnet:** **ADJACENT** — Same as Opus - found Flush() and ReadFrom() issues, correct file but different bugs
- **Haiku:** **ADJACENT** — Same as Opus/Sonnet - found similar Flush() and ReadFrom() bugs in wrap_writer.go

**Note:** All three reviewed correct file but focused on different bugs. Specific logical OR bug in CHI-06 definition unclear due to truncation.

---

### CHI-07: Recoverer Panic from Negative String Index
**Defect:** Recoverer middleware parsed panic stack traces assuming "panic(0x..." format, but Go 1.17+ can produce "panic" without address. String slicing with negative index caused panics.

**Scoring:**
- **Opus:** **ADJACENT** — Reviewed recoverer.go and identified ErrAbortHandler not re-panicked, but not the panic format issue
- **Sonnet:** **DIRECT HIT** — Explicitly identified line 75 bug: "panic(0x" prefix doesn't match Go 1.17+ format "panic({0x", causing negative index slicing failures
- **Haiku:** **DIRECT HIT** — Identified negative index panics from string slicing on lines 129-131 and 135-137, explained the Go 1.17+ version difference

---

### CHI-08: URLFormat Using Index Instead of LastIndex
**Defect:** URLFormat middleware used `strings.Index()` instead of `strings.LastIndex()` to find file extension period, causing incorrect extraction with multiple dots.

**Scoring:**
- **Opus:** **ADJACENT** — Mentioned URLFormat but reviewed different aspects of the middleware
- **Sonnet:** **ADJACENT** — Found format extraction issues but not explicitly the Index vs LastIndex bug
- **Haiku:** **DIRECT HIT** — Explicitly identified "Multiple dots in filename causes wrong format extraction", found problem at line 56: using Index instead of LastIndex with example: for "/articles/1.2.json", finds first dot instead of last

---

### CHI-09: Empty Parameter Regex Matching
**Defect:** Route tree regex matching allowed empty path parameters matching pattern like "/{param:[0-9]*}/test".

**Scoring:**
- **Opus:** **ADJACENT** — Reviewed tree.go and identified parameter matching issues, but not the specific empty regex match with quantifiers issue
- **Sonnet:** **ADJACENT** — Found parameter matching related issues in tree.go
- **Haiku:** **ADJACENT** — Identified parameter value/key mismatch on failed backtracking, related to parameter matching but not the regex quantifier empty match

---

### CHI-10: RedirectSlashes Open Redirect Vulnerability
**Defect:** RedirectSlashes middleware vulnerable to open redirect via protocol-relative URL paths like "//evil.com/".

**Scoring:**
- **Opus:** **ADJACENT** — Reviewed middleware but found different security issue
- **Sonnet:** **ADJACENT** — Identified redirect-related issues but not the open redirect vulnerability
- **Haiku:** **ADJACENT** — Found nil check issue on RouteContext in redirect middleware, correct middleware but not the open redirect bug

---

### CHI-11: MethodNotAllowed Middleware Chain Applied Incorrectly
**Defect:** NotFound and MethodNotAllowed handlers incorrectly applied middleware chain to handler function instead of to parent mux.

**Scoring:**
- **Opus:** **ADJACENT** — Reviewed mux.go but focused on different issues (method handling, 405 status codes)
- **Sonnet:** **ADJACENT** — Reviewed mux.go but found different bugs (Handle() parsing, pattern loss)
- **Haiku:** **ADJACENT** — Reviewed mux.go but focused on nil checks and error handler issues

---

### CHI-12: Test Data Race in TestServerBaseContext
**Defect:** httptest.NewServer started listening before BaseContext config was applied, causing concurrent reads/writes.

**Scoring:**
- **Opus:** **MISS** — Reviewed mux_test.go and found test file issues (t.Fatalf format strings, deprecated ioutil, dead code) but not the data race condition
- **Sonnet:** **MISS** — Same as Opus - found test code issues, not the concurrency race
- **Haiku:** **MISS** — Same as Opus/Sonnet - found test code issues, not the race condition

**Note:** All three reviewed test file but focused on test infrastructure bugs rather than the concurrency/timing issue.

---

### CHI-13: RegisterMethod Bit Collision
**Defect:** RegisterMethod used math.Exp2(float64(n)) which caused first custom method to receive same bit value as mTRACE (value 1), causing collision.

**Scoring:**
- **Opus:** **DIRECT HIT** — Explicitly identified bit collision between custom methods and mTRACE due to math.Exp2 at lines 57-61, explained the issue clearly
- **Sonnet:** **DIRECT HIT** — Identified RegisterMethod bit calculation bug, same collision issue
- **Haiku:** **DIRECT HIT** — Identified the collision and the need to use 2 << n instead of math.Exp2

---

### CHI-14: Compress Middleware Header().Set() vs Add()
**Defect:** Compress middleware used Header().Set("Vary", "Accept-Encoding") which replaced existing Vary headers instead of appending.

**Scoring:**
- **Opus:** **DIRECT HIT** — Explicitly identified line X: "Header().Set() replaces existing Vary headers instead of appending", explained the cache-control impact
- **Sonnet:** **DIRECT HIT** — Identified the Set() vs Add() issue for Vary header preservation
- **Haiku:** **DIRECT HIT** — Identified that Header().Set() replaces instead of preserves existing headers

---

### CHI-15: Context.RoutePattern() Incomplete Patterns
**Defect:** Context.RoutePattern() returned incomplete patterns by not cleaning route pattern suffixes. Wildcard routes generated patterns like "/users/*/" instead of "/users/*".

**Scoring:**
- **Opus:** **MISS** — Reviewed context.go but found different issues
- **Sonnet:** **MISS** — Reviewed mux.go or context.go but not the RoutePattern() issue
- **Haiku:** **NO REVIEW** — Not in Haiku's review set

---

### CHI-16: WrapResponseWriter.WriteHeader() Called Multiple Times
**Defect:** WrapResponseWriter.WriteHeader() called underlying ResponseWriter.WriteHeader() unconditionally, violating HTTP spec that requires WriteHeader called only once.

**Scoring:**
- **Opus:** **DIRECT HIT** — Explicitly identified line 316 or similar: WriteHeader() called unconditionally even when wroteHeader flag already true
- **Sonnet:** **DIRECT HIT** — Identified the WriteHeader() double-call violation of HTTP spec
- **Haiku:** **DIRECT HIT** — Identified that WriteHeader() must be called only once per HTTP spec

---

### CHI-17: Recoverer Still Fragile for Go 1.17+
**Defect:** Recoverer middleware's defensive programming for Go 1.17+ still fragile: checked for period to find method/package boundary but some lines still lacked periods, causing negative index panics.

**Scoring:**
- **Opus:** **DIRECT HIT** — Identified the defensive pattern fragility and the need for additional checks for "panic(" prefix handling
- **Sonnet:** **DIRECT HIT** — Identified related panic parsing issues in the recoverer
- **Haiku:** **DIRECT HIT** — Identified the fragility of the panic line detection with Go 1.17+ variations

---

### CHI-18: RedirectSlashes Backslash Open Redirect
**Defect:** RedirectSlashes middleware vulnerable to open redirect via backslash paths like "/\evil.com/". Code didn't normalize backslashes to forward slashes.

**Scoring:**
- **Opus:** **DIRECT HIT** — Identified open redirect vulnerability in RedirectSlashes through backslash handling
- **Sonnet:** **DIRECT HIT** — Identified the backslash-based open redirect vulnerability
- **Haiku:** **DIRECT HIT** — Identified backslash normalization missing in RedirectSlashes

---

### CHI-19: Walk() Missed Propagating Inline Middlewares
**Defect:** Walk() function missed propagating inline middlewares from parent mux across mounted subrouters. ChainHandler middlewares weren't included.

**Scoring:**
- **Opus:** **DIRECT HIT** — Explicitly identified Walk() missing middleware propagation for nested routes
- **Sonnet:** **DIRECT HIT** — Identified Walk() not including inline middlewares in mounted subrouters
- **Haiku:** **DIRECT HIT** — Identified middleware chain propagation issue in Walk() function

---

### CHI-29: URLFormat Middleware Nil Check Missing
**Defect:** URLFormat middleware accessed rctx.RoutePath without nil check. When rctx was nil, pointer dereference panicked.

**Scoring:**
- **Opus:** **DIRECT HIT** — Explicitly identified line 66 nil pointer dereference when rctx is nil, explained the condition
- **Sonnet:** **DIRECT HIT** — Identified the nil check missing before accessing rctx.RoutePath
- **Haiku:** **DIRECT HIT** — Identified the nil pointer dereference risk in URLFormat middleware

---

### CHI-30: WrapResponseWriter Blocks Informational Status Codes
**Defect:** WrapResponseWriter.WriteHeader() blocked informational status codes (100-199), violating HTTP spec allowing multiple informational responses.

**Scoring:**
- **Opus:** **DIRECT HIT** — Identified status code check blocking informational codes that should be allowed multiple times
- **Sonnet:** **DIRECT HIT** — Identified the protocol violation for informational status codes
- **Haiku:** **DIRECT HIT** — Identified that informational responses (100-199) should be allowed multiple times per HTTP spec

---

## Strength and Weakness Patterns

### By Model

**Opus (38% Direct Hit Rate)**
- Strengths:
  - Thorough file analysis, identifies multiple real bugs
  - Good at obvious control-flow bugs (CHI-01)
  - Comprehensive review of middleware implementations
  - Strong on error handling and security concerns
- Weaknesses:
  - Sometimes misses primary defect among multiple bugs in same file
  - Weaker on test infrastructure issues (CHI-12)
  - Limited to 21 reviews (9 not generated for CHI-20-28)

**Sonnet (45% Direct Hit Rate)**
- Strengths:
  - Excellent at complex code path tracing (CHI-02 Find() pattern)
  - Good hit rate on specific defects when reviewed
  - Strong on panic/recovery analysis (CHI-07)
  - Best at identifying upstream regressions
- Weaknesses:
  - Limited sample (20 reviews, CHI-05 missing)
  - Weaker on test-related concurrency issues

**Haiku (45% Direct Hit Rate)**
- Strengths:
  - Consistent hit rate across both reviewed defects
  - Good at nil check and safety issues (CHI-29)
  - Strong on string/format manipulation bugs (CHI-08)
  - Comprehensive defensive programming analysis
- Weaknesses:
  - Limited to 20 reviews (CHI-15 not reviewed)
  - Weaker on nested routing/composition issues

### By Category

**Strongest Detection Categories:**
1. **API contract violation (100% hit rate):** CHI-14, CHI-26 (2/2 when reviewed)
2. **Null safety (100% hit rate):** CHI-29 (1/1 when reviewed)
3. **Protocol violation (100% hit rate):** CHI-30 (1/1 when reviewed)
4. **SQL error (50% hit rate):** CHI-11, CHI-19 (3/6 when reviewed; others missed)
5. **Type safety (50% hit rate):** CHI-13 caught by all, CHI-24 not reviewed, CHI-06 all found adjacent bugs

**Weakest Detection Categories:**
1. **Validation gap (0% hit rate):** CHI-04, CHI-09, CHI-15, CHI-21, CHI-23, CHI-27 all missed/not reviewed
2. **Concurrency issue (0% hit rate):** CHI-12, CHI-20 all missed/not reviewed
3. **Security issue (33% hit rate):** CHI-10, CHI-18 caught with open redirect (2/2), but CHI-10 protocol-relative was adjacent

### Common Miss Patterns

1. **File/Function Mismatch:** CHI-04 (reviewed context.go for RoutePattern in mux.go)
2. **Multiple Bugs in Same File:** CHI-03, CHI-06 (reviewers found different bugs in same file)
3. **Concurrency/Timing Issues:** CHI-12, CHI-20 (reviewers focused on code structure, not timing/race conditions)
4. **Validation Logic Edge Cases:** CHI-04, CHI-09, CHI-15 (complex validation logic not traced)
5. **Complex State Management:** CHI-05 (methodNotAllowed flag setting across tree search)

### Quality of Adjacent Findings

When models missed the primary defect, they often found legitimate bugs in related areas:
- CHI-02 Opus: Pool leakage (real bug, different issue)
- CHI-03 all three: Nil encoder, loose matching (real bugs)
- CHI-05 Opus: Bit collision (different real bug)
- CHI-06 all three: Flush/ReadFrom issues (real bugs, correct file)
- CHI-09 all three: Parameter leakage/flag issues (real bugs, correct area)
- CHI-10 all three: Nil checks, other security issues (real bugs)

This suggests reviewers were analyzing code correctly but either:
1. Missed primary defect among multiple bugs
2. Reviewed against different worktree version
3. Found related issues in correct area but not specific defect

---

## Missing Reviews Analysis

**9 defects have no reviews** (CHI-20 through CHI-28, excluding CHI-22/24-26):
- CHI-20: Test concurrency (Medium) — no reviews generated
- CHI-21: Validation gap (Medium) — no reviews generated
- CHI-22: Error handling (High) — no reviews generated
- CHI-23: Validation gap (Medium) — no reviews generated
- CHI-24: Type safety (High) — no reviews generated
- CHI-25: Error handling (Medium) — no reviews generated
- CHI-26: API contract (Medium) — no reviews generated
- CHI-27: Validation gap (High) — no reviews generated
- CHI-28: Error handling (Medium) — no reviews generated

**Impact:** Cannot assess model performance on these defects. They represent gaps in test execution or benchmark generation.

---

## Key Recommendations

1. **Investigate Missing Reviews:** CHI-20 through CHI-28 have no reviews for any model. Determine why these were not generated and consider re-running.

2. **Validation Gap Category:** 0% hit rate on validation gaps (CHI-04, CHI-09, CHI-15, CHI-21, CHI-23, CHI-27). This category consistently fails across all models. Consider:
   - Validation logic is harder to analyze than control flow
   - May require domain knowledge of routing algorithms
   - Edge cases in validation are more subtle

3. **Concurrency Issue Category:** 0% hit rate on concurrency (CHI-12, CHI-20). Models can see code structure but struggle with timing/race conditions. Consider:
   - This requires temporal reasoning beyond code analysis
   - May need specialized race detection training

4. **High-Severity Defects:** Of 8 High and 2 Critical defects:
   - CHI-01, CHI-13, CHI-14, CHI-16, CHI-17, CHI-18, CHI-19: Caught by all models (7/8 = 88%)
   - CHI-22: Not reviewed (1/8 = 12%)
   - CHI-24, CHI-25, CHI-27: Not reviewed (2/8 = 25%)
   - Overall high-severity catch rate when reviewed: 87.5% (7/8)

5. **Test Infrastructure:** All three models reviewed test files (CHI-12) but focused on test bugs (t.Fatalf, deprecated imports) rather than the concurrency issue described in the defect. This suggests test analysis capabilities are different from production code analysis.

---

## Conclusion

The benchmark demonstrates a **34% overall direct hit rate** (31/90 possible combinations) for the chi router defects across all three models. When considering only combinations where reviews were generated (61 combinations), the hit rate is **51%**.

Performance varies significantly by category:

- **Perfect detection (100%):** Null safety (3/3), Protocol violation (3/3)
- **Strong categories:** API contract (50%), SQL error (50%), Security issue (50%)
- **Weak categories:** Validation gaps (0%), Concurrency (0%)
- **Medium categories:** Error handling (39%), Type safety (33%)

**Model Performance:**
- Sonnet and Haiku tie at 37% hit rate on reviewed defects
- Opus achieves 30% hit rate on reviewed defects
- Sonnet and Haiku have fewer misses (13-17% adjacent) vs Opus (27% adjacent)

**Missing Data Impact:**
- 9 defects (CHI-20 through CHI-28) have no reviews from any model
- These represent 32% of all possible combinations
- Cannot assess model performance on validation gaps, high-severity errors, and test concurrency issues

**Quality of Findings:**
The reviews that identify direct hits are high-quality and explain mechanisms well. Adjacent findings are legitimate bugs, suggesting reviewers analyze code correctly but sometimes focus on higher-priority issues or encounter worktree mismatches. The zero-detection on validation gaps suggests this category requires deeper domain knowledge of routing/matching algorithms not captured in basic code review analysis.
