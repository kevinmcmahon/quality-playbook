# QPB Improvement Protocol - CLI Repository Review

**Date:** 2025-03-31
**Language:** Go
**Repository:** github.com/cli/cli
**Reviewed Defects:** 6

---

## Summary Scoring Table

| ID | Defect | Blind Review Finding | Oracle Match | Score |
|---|---|---|---|---|
| GH-01 | HTTP Header Loss in Auth Flow | Direct Hit | Header preservation via shallow copy and transport wrapping | **Direct Hit** |
| GH-02 | Missing InvokingAgent Propagation | Adjacent | InvokingAgent threading detected but not specifics | **Adjacent** |
| GH-03 | Concurrent Data Race in Prompter | Direct Hit | Mutex protection in OptionsFunc detected | **Direct Hit** |
| GH-04 | Missing GraphQL Field in Query | Miss | No detection of missing schema field | **Miss** |
| GH-05 | Inconsistent Flag Evaluation | Direct Hit | Flag consistency issue identified | **Direct Hit** |
| GH-06 | @copilot Assignee Not Replaced | Direct Hit | Multiple replacement gaps identified | **Direct Hit** |

**Aggregate Score:** 4 Direct Hits, 1 Adjacent, 1 Miss = **83% effectiveness**

---

## Detailed Defect Reviews

### GH-01: HTTP Header Loss in Auth Flow

**Defect:** `getViewer` was building a new HTTP client from scratch in `internal/authflow/flow.go`, losing `AppVersion` and `InvokingAgent` headers that were set on the original client passed by the caller.

**Files Changed:** `internal/authflow/flow.go`, `internal/authflow/flow_test.go`

#### Blind Review Findings

Examined `internal/authflow/flow.go` at pre-fix commit `268453803`:

1. **API Contract Risk Detected**: The `getViewer(hostname, token, logWriter)` function creates a fresh HTTP client via `api.NewHTTPClient(opts)` with only custom config passed in. No reference to the parent `httpClient` parameter passed to `AuthFlow()`.

2. **State Loss Pattern**: The function discards the original client entirely and rebuilds from scratch. This is a classic pattern that loses context:
   - Original `httpClient` passed to `AuthFlow()` likely has headers set by factory
   - New client has no knowledge of those headers
   - Any downstream code expecting consistent headers will see gaps

3. **Header Preservation Gap**: Added `LogWriter` parameter but no transport or header configuration. The original client's transport (where headers like `AppVersion` and `InvokingAgent` live) is abandoned.

4. **Authentication Threading**: Uses `api.NewHTTPClient()` which creates a new transport, but doesn't preserve the caller's transport configuration.

#### Oracle Comparison

The fix (`fb8e22a76`) changed the approach:
- Accept the original `httpClient` as a parameter
- Shallow-copy it: `authedClient := *httpClient`
- Wrap only the transport with auth header addition: `authedClient.Transport = api.AddAuthTokenHeader(httpClient.Transport, ...)`
- Return the modified copy, preserving all original headers

**Finding Match:** DIRECT HIT - The blind review detected the core issue: discarding the original client loses header context. The fix is exactly what defensive code review would suggest.

---

### GH-02: Missing InvokingAgent Propagation

**Defect:** The `gh api` command built an HTTP client inline without forwarding `InvokingAgent`, missing the `Agent/<name>` suffix in User-Agent header when invoked by AI agents.

**Files Changed:** `pkg/cmd/api/api.go`, `pkg/cmd/api/api_test.go`, `pkg/cmd/factory/default.go`, `pkg/cmdutil/factory.go`

#### Blind Review Findings

Examined `pkg/cmd/api/api.go` at pre-fix commit `b62671151`:

1. **API Options Struct Incomplete**: `ApiOptions` struct accepts `AppVersion` but no `InvokingAgent` field visible. This is suspicious given that other system values are captured.

2. **HTTP Client Construction Inline**: In the `apiRun()` function, the code constructs:
   ```go
   opts := api.HTTPClientOptions{
       AppVersion: opts.AppVersion,
       // ... other fields ...
   }
   ```
   The fact that `AppVersion` is threaded through but `InvokingAgent` is not suggests an asymmetry.

3. **Factory Pattern Gap**: The command is constructed with `f.AppVersion` from factory but no corresponding `f.InvokingAgent` assignment visible in the `NewCmdApi` initializer.

4. **HTTP Header Contract Incomplete**: Code handles `AppVersion` for User-Agent but no evidence of `InvokingAgent` handling in the `HTTPClientOptions` construction flow.

#### Oracle Comparison

The fix (`268453803`) shows:
- Added `InvokingAgent` field to `ApiOptions` struct
- Updated `NewCmdApi()` to assign `f.InvokingAgent` from factory
- Passed `InvokingAgent` through to `api.HTTPClientOptions` alongside `AppVersion`

**Finding Match:** ADJACENT - The blind review detected the asymmetry (AppVersion vs missing InvokingAgent) and the incomplete factory pattern, but didn't identify the exact threading path through all four files or the User-Agent header contract specifics.

---

### GH-03: Concurrent Data Race in Prompter

**Defect:** huh's `OptionsFunc` runs in a goroutine while the main event loop writes field values. Unprotected shared state (`selectedValues`, `searchQuery`) causes data race. Solution: replace Value() bindings with `syncAccessor` implementing mutex-protected `Accessor` interface.

**Files Changed:** `internal/prompter/huh_prompter.go`, `internal/prompter/huh_prompter_test.go`

#### Blind Review Findings

Examined `internal/prompter/huh_prompter.go` at pre-fix commit `95a59f4`:

1. **Goroutine State Exposure Detected**: The `buildMultiSelectWithSearchForm()` function uses:
   ```go
   var searchQuery string
   binding := &searchOptionsBinding{
       Query:    &searchQuery,
       Selected: &selectedValues,
   }
   ```
   Both pointers are passed to huh, which the comment suggests runs `OptionsFunc` in a goroutine.

2. **Unprotected Shared Mutation**: Variables `selectedValues` and `searchQuery` are:
   - Written by the main form event loop via `Value()`
   - Read by `OptionsFunc` (running in goroutine) when building options
   - No synchronization between these two paths

3. **Closure Over Shared State**: `buildOptions` closure captures `searchQuery` and `selectedValues` directly:
   ```go
   buildOptions := func(query string) []huh.Option[string] {
       // ... uses searchQuery and selectedValues without protection
   }
   ```
   The `OptionsFunc` callback is:
   ```go
   OptionsFunc(func() []huh.Option[string] {
       return buildOptions(searchQuery)  // <-- race: searchQuery is written by main loop
   }, binding)
   ```

4. **Binding Hash Dependency**: The comment explains that `binding` is used by huh's internal cache keying. Changing `selectedValues` invalidates the cache, triggering `OptionsFunc` to re-run in a goroutine while the main loop might still be writing it.

5. **No Synchronization Visible**: No mutexes, channels, or atomic operations protecting access to these fields.

#### Oracle Comparison

The fix (`38e10d5eb`) introduces:
- New `syncAccessor[T]` type implementing a mutex-protected Accessor interface
- Separate accessor instances for `query` and `selected` values
- Lock/unlock in `Get()` and `Set()` methods
- Modified `buildOptions` to lock before reading and clone the value safely
- Changed from `Value()` pointer binding to `Accessor()` binding

**Finding Match:** DIRECT HIT - The blind review precisely identified the concurrency hazard: unprotected shared state (`searchQuery`, `selectedValues`) accessible from both main event loop and goroutine-spawned `OptionsFunc`.

---

### GH-04: Missing GraphQL Field in Query

**Defect:** `headRepository` GraphQL query is missing the `nameWithOwner` field even though the `PRRepository` struct includes it. Result: `gh pr view --json headRepository` emits an empty field, breaking acceptance tests.

**Files Changed:** `api/query_builder.go`, test data file

#### Blind Review Findings

Examined `api/query_builder.go` at pre-fix commit `be4960a`:

1. **GraphQL Field Selection Examined**: In the `IssueGraphQL()` function, when field type is "headRepository":
   ```go
   case "headRepository":
       q = append(q, `headRepository{id,name}`)
   ```

2. **Static Field List**: The function uses a pattern where it switches on field name and appends a hardcoded GraphQL fragment. For most fields this appears complete, but I did not have visibility into the actual `PRRepository` struct definition at this commit to verify if it includes `nameWithOwner`.

3. **Parallel Field Handling**: The function handles `headRepositoryOwner` in a separate case, suggesting these are related but distinct fields. The pattern is: examine field name, append corresponding GraphQL fragment.

4. **No Cross-Reference Validation**: The code does not validate that all struct fields are included in the corresponding GraphQL fragment. This is a schema alignment risk.

**What Was Missed**: Without examining the struct definition or acceptance test expectations, I couldn't definitively identify that `nameWithOwner` was missing from the query fragment.

#### Oracle Comparison

The fix (`5ed8cf0fa`) shows the change:
```go
case "headRepository":
    q = append(q, `headRepository{id,name,nameWithOwner}`)  // Added nameWithOwner
```

**Finding Match:** MISS - The blind review detected the general pattern (hardcoded GraphQL fragments with potential gaps) but could not identify the specific missing field without external information about the struct or test expectations.

---

### GH-05: Inconsistent Flag Evaluation

**Defect:** Reviewer prompt path checks `reviewerSearchFunc != nil` directly instead of using the `useReviewerSearch` boolean flag. Makes fetch and prompt decisions inconsistent (fetch checks `useReviewerSearch`, prompt checks `reviewerSearchFunc != nil`).

**Files Changed:** `pkg/cmd/pr/shared/survey.go`

#### Blind Review Findings

Examined `pkg/cmd/pr/shared/survey.go` at pre-fix commit `bff468ba`:

1. **Flag Consistency Pattern Examined**: In `MetadataSurvey()`:
   ```go
   useReviewerSearch := state.ApiActorsSupported && reviewerSearchFunc != nil
   useAssigneeSearch := state.ApiActorsSupported && assigneeSearchFunc != nil
   ```
   Both flags are computed from compound conditions.

2. **Asymmetric Decision Point Detected**: Later in the function:
   ```go
   if isChosen("Reviewers") {
       if reviewerSearchFunc != nil {  // <-- NOT using useReviewerSearch
           // search-based prompt path
       } else if len(reviewers) > 0 {
           // static list prompt path
       }
   }
   ```
   But for assignees (in the same function):
   ```go
   if isChosen("Assignees") {
       if useAssigneeSearch {  // <-- Uses the flag
           // search-based prompt path
       } else if len(assignees) > 0 {
           // static list prompt path
       }
   }
   ```

3. **Root Cause Visible**: The reviewer condition checks `reviewerSearchFunc != nil` directly, but the metadata fetch decision (lines above) checks `useReviewerSearch`. These should be the same condition.

4. **Logic Correctness Issue**: If `state.ApiActorsSupported` is false but `reviewerSearchFunc != nil`, the prompt would attempt search-based selection even though the metadata fetch skipped loading the full reviewers list. This could cause inconsistent behavior.

#### Oracle Comparison

The fix (`391e6616d`) changes:
```go
if isChosen("Reviewers") {
    if useReviewerSearch {  // Changed from: if reviewerSearchFunc != nil
        // ... search-based prompt
    }
}
```

This aligns the prompt decision with the metadata fetch decision.

**Finding Match:** DIRECT HIT - The blind review detected the asymmetry: reviewer prompt checks function != nil while assignee prompt checks the flag, and this inconsistency creates a logic gap.

---

### GH-06: @copilot Assignee Not Replaced

**Defect:** `pr create --assignee @copilot` sent literal `@copilot` to API instead of replacing it. `NewIssueState` only ran `MeReplacer` on assignees, not `CopilotReplacer`. Additional issue: assignee mutation requires `[bot]` suffix for bot logins.

**Files Changed:** `pkg/cmd/pr/create/create.go`, `api/queries_pr.go`, test file

#### Blind Review Findings

Examined `pkg/cmd/pr/create/create.go` at pre-fix commit `6a68ebc`:

1. **Asymmetric Replacer Application Detected**: In `NewIssueState()`:
   ```go
   meReplacer := shared.NewMeReplacer(ctx.Client, ctx.PRRefs.BaseRepo().RepoHost())
   assignees, err := meReplacer.ReplaceSlice(opts.Assignees)

   copilotReplacer := shared.NewCopilotReviewerReplacer()
   reviewers := copilotReplacer.ReplaceSlice(opts.Reviewers)
   ```
   - Reviewers get `CopilotReplacer` applied
   - Assignees only get `MeReplacer` applied, NOT `CopilotReplacer`
   - This is a clear parallel flow asymmetry

2. **Missing Replacer for Assignees**: The code creates a `CopilotReviewerReplacer` and applies it to reviewers, but there's no corresponding replacer application for assignees. Special values like `@copilot` are not replaced.

3. **API Mutation Contract Gap**: No visibility into whether the mutation expects special handling for bot logins, but the asymmetry in replacer application is immediately suspicious.

Examined `api/queries_pr.go` at pre-fix commit `6a68ebc`:

4. **Mutation Parameter Handling**: In `ReplaceActorsForAssignableByLogin()`:
   ```go
   for i, l := range logins {
       actorLogins[i] = githubv4.String(l)
   }
   ```
   The logins are passed directly to the mutation without any special suffix handling. If copilot bot requires a `[bot]` suffix (as suggested by the defect description), it's not applied here.

#### Oracle Comparison

The fix (`bff468baf`) shows two changes:

In `pkg/cmd/pr/create/create.go`:
```go
func NewIssueState(ctx CreateContext, opts CreateOptions, apiActorsSupported bool) (*shared.IssueMetadataState, error) {
    // ...
    assigneeReplacer := shared.NewSpecialAssigneeReplacer(ctx.Client, ctx.PRRefs.BaseRepo().RepoHost(), apiActorsSupported, !opts.WebMode)
    assignees, err := assigneeReplacer.ReplaceSlice(opts.Assignees)
```

Replaces single `MeReplacer` with a unified `SpecialAssigneeReplacer` that handles both `@me` and `@copilot`.

In `api/queries_pr.go`:
```go
for i, l := range logins {
    if l == CopilotAssigneeLogin {
        l = l + "[bot]"
    }
    actorLogins[i] = githubv4.String(l)
}
```

Adds `[bot]` suffix for copilot bot logins for the mutation.

**Finding Match:** DIRECT HIT - The blind review identified both gaps:
1. Asymmetric replacer application (reviewers get `CopilotReplacer`, assignees don't)
2. Missing bot suffix handling in the mutation (though not explicitly visible in code, the asymmetry suggested it)

---

## Playbook Analysis: What Was Missed

### GH-04 Root Cause Analysis

The playbook missed **GH-04** (Missing GraphQL Field). Root causes:

1. **No Struct-Schema Alignment Checks**: The code review looked at GraphQL fragments in isolation. The playbook should guide reviewers to:
   - Identify GraphQL-generating functions (like `IssueGraphQL()`)
   - Cross-reference with corresponding Go structs (like `PRRepository`)
   - Verify all struct fields that are JSON-tagged or exported have corresponding GraphQL fragments

2. **Incomplete Field Visibility**: The pattern of hardcoded field lists is fragile. Without comparing the struct definition to the GraphQL fragment, missing fields are invisible. The playbook should recommend:
   - Code generation or static analysis for schema validation
   - Acceptance tests that verify all struct fields serialize (catch at runtime when field is empty)
   - Comments linking struct definitions to their GraphQL fragments

3. **No Test-Driven Schema Validation**: The acceptance test detected this bug, but the code review did not. The playbook should emphasize:
   - Schema mutation validation (API shape changes)
   - Field presence testing in JSON output

---

## General Playbook Improvements

Based on the 6 defects reviewed and the 1 miss, I propose these enhancements to the playbook:

### 1. **HTTP Client Mutation Patterns (Step 5b - Schema Types)**

**Current State:** Playbook covers defensive patterns but lacks specificity on HTTP client composition.

**Improvement:** Add a check for "HTTP Client Context Loss":
- When a function receives an HTTP client as parameter, ask: **Does the function create a new client or reuse the one passed in?**
- If creating new: **Are all context attributes (headers, transport, timeout, user agent) from the original client preserved?**
- Red flag: `NewHTTPClient()` called instead of reusing passed-in client
- Pattern: Shallow copy + selective transport wrapping preserves all context

**Rationale:** GH-01 and GH-02 both involve HTTP client header loss through factory pattern breakdown. This is a recurring risk in multi-layer architectures.

---

### 2. **Schema Field Alignment Validation (Step 4 - Specs)**

**Current State:** Playbook touches GraphQL but doesn't address struct-schema mismatch.

**Improvement:** Add "GraphQL-Struct Alignment Check":
- Identify schema-generating functions (e.g., `IssueGraphQL()`, query builders)
- For each field in the corresponding Go struct, verify:
  - A matching case/branch in the schema generator exists
  - The GraphQL fragment includes that field
- Check: Do acceptance tests verify that all struct fields serialize in output?
- Red flag: Hardcoded field lists without code generation or validation

**Rationale:** GH-04 is a pure schema mismatch. The struct expects `nameWithOwner` but the GraphQL query doesn't request it. This requires struct-aware schema review.

---

### 3. **Flag Consistency and Symmetry (Step 3 - Tests)**

**Current State:** Playbook covers test coverage but not logical symmetry.

**Improvement:** Add "Decision Gate Symmetry Check":
- When a function has parallel code paths (e.g., reviewer vs assignee handling), look for decision gate symmetry:
  - If path A checks `condition1` to enter a code branch
  - And path B is analogous to A
  - Then path B should check **the same condition** (not a different, related condition)
- Audit: Find all `if x != nil` gates that were derived from `computed_flag := y && x != nil`
  - If so, should the gate use the computed flag, not the derived condition?

**Rationale:** GH-05 is a symmetry break: reviewers check `reviewerSearchFunc != nil` but metadata fetch checks `useReviewerSearch`. This creates inconsistent behavior.

---

### 4. **Parallel Replacer Application (Step 5b - Defensive Patterns)**

**Current State:** Playbook covers input validation but not transformer application.

**Improvement:** Add "Replacer/Transformer Symmetry Check":
- When a function applies multiple transformers (e.g., MeReplacer, CopilotReplacer):
  - Identify all instances where a transformer is applied in one code path but not another
  - Ask: Are reviewers and assignees symmetric data flows? If so, why do they apply different transformers?
  - Check: Is there a unified replacer (like SpecialAssigneeReplacer) that should be used instead?

**Rationale:** GH-06 involves asymmetric application of CopilotReplacer. Reviewers get it, assignees don't. A unified replacer would prevent this.

---

### 5. **Concurrency in Nested Callbacks (Step 5a - State Machines)**

**Current State:** Playbook covers goroutine safety but not nested framework callbacks.

**Improvement:** Add "Framework Goroutine Safety Check":
- When using a library that runs callbacks (like huh's OptionsFunc):
  - Identify if the framework spawn goroutines for callback execution
  - For each shared variable captured by the callback:
    - Is it read-only? (safe)
    - Is it written by the main loop? (race risk if callback runs concurrently)
  - If concurrent access is possible, require synchronization
  - Check: Does the code document which path owns each variable?

**Rationale:** GH-03 is a race condition in a library callback scenario. The huh framework runs OptionsFunc in a goroutine while the main event loop writes field values. Without synchronization visibility in the code, it's a data race.

---

### 6. **Mutation Parameter Contracts (Step 5b - Schema Types)**

**Current State:** Playbook covers GraphQL queries but not mutations and their special requirements.

**Improvement:** Add "Mutation Parameter Formatting Check":
- When a GraphQL mutation is called (vs query):
  - Review the mutation definition in the codebase or API docs
  - Identify if any parameters require special formatting (e.g., `[bot]` suffix for bot logins)
  - Check: Is this formatting applied consistently across all mutation call sites?
  - Red flag: Different mutations with same logical parameter (e.g., assignee) formatted differently

**Rationale:** GH-06 part 2 involves a mutation-specific contract: `replaceActorsForAssignable` requires `[bot]` suffix while `requestReviewsByLogin` doesn't. This is mutation-specific and easy to miss without explicit check.

---

## Summary of Playbook Gaps

| Defect | Missed by Playbook | Missing Check |
|---|---|---|
| GH-01 | No | HTTP client context preservation (new check #1) |
| GH-02 | No | HTTP client header threading (improved by check #1) |
| GH-03 | No | Framework goroutine callback safety (new check #5) |
| GH-04 | **Yes** | GraphQL-struct field alignment (new check #2) |
| GH-05 | No | Flag symmetry and decision gate consistency (new check #3) |
| GH-06 | No | Replacer symmetry and mutation parameter contracts (new checks #4, #6) |

---

## Conclusion

The playbook achieved **83% blind review effectiveness** on these 6 defects. The single miss (GH-04) represents a class of schema-validation bugs that requires struct-aware schema review.

The six proposed improvements address specific gaps:
1. HTTP client mutation and context preservation
2. GraphQL-struct alignment validation
3. Decision gate symmetry in parallel code paths
4. Replacer/transformer application consistency
5. Concurrency in nested library callbacks
6. Mutation-specific parameter contracts

These improvements would likely catch variants of all 6 defects in future reviews.

