# GitHub CLI (cli/cli) Defects — Quality Playbook Benchmark Dataset

**Repository**: [cli/cli](https://github.com/cli/cli) (The GitHub CLI)
**Language**: Go
**Analysis Date**: 2026-03-29
**Analyzer**: Claude Code Agent
**Defect Count**: 20 (GH-01 through GH-20)

This file documents the first 20 real defects from the GitHub CLI repository, analyzed as part of the Quality Playbook Benchmark (QPB) dataset. Each defect was identified by examining the actual fix commit and understanding what the pre-fix code did wrong.

---

## Defect Catalog

### GH-01 | HTTP Header Loss in Auth Flow | High

**Issue**: cli/cli PR #13046 (User-Agent header preservation)
**Fix**: `fb8e22a76` → Parent: `268453803`
**Files changed**: `internal/authflow/flow.go`, `internal/authflow/flow_test.go`

**Defect**: The `getViewer()` function in the auth flow was creating a new HTTP client from scratch using `api.NewHTTPClient()`, discarding the existing client passed into `AuthFlow()`. This caused the client to lose `AppVersion` and `InvokingAgent` headers that were already set in the plain client's middleware stack. Any auth operations would make API requests with incomplete User-Agent headers.

**Fix**: Modified `getViewer()` to accept the existing `httpClient` as a parameter and shallow-copy it, then wrap only its transport with `AddAuthTokenHeader()`. This preserves all header middleware from the original client while adding auth tokens.

**Why this category**: The fix directly addresses header contract violations—the API expected specific headers, but the implementation discarded them during internal auth token negotiation.

**Playbook angle**: Step 5b (schema types) — HTTP client mutation patterns. Should catch this by tracing how clients are constructed and whether they preserve middleware/header chains through function boundaries.

---

### GH-02 | Missing InvokingAgent Propagation | High

**Issue**: cli/cli (InvokingAgent threading)
**Fix**: `268453803` → Parent: `b6267151`
**Files changed**: `pkg/cmd/api/api.go`, `pkg/cmd/api/api_test.go`

**Defect**: The `gh api` command was building its HTTP client inline without forwarding the `InvokingAgent` factory property. When invoked by AI agents (e.g., Copilot CLI), the User-Agent header was missing the `Agent/<name>` suffix that identifies the invoking agent to GitHub APIs, violating the API contract.

**Fix**: Threaded `InvokingAgent` through the factory's `ApiOptions` struct into `HTTPClientOptions`, mirroring the existing `AppVersion` pattern. This ensures all API commands preserve agent identity in User-Agent headers.

**Why this category**: The fix establishes an API contract requirement (User-Agent suffix) that was being violated due to incomplete parameter threading.

**Playbook angle**: Step 2 (architecture) — factory pattern propagation. Should catch by verifying that all optional factory fields are consistently threaded through to HTTP client construction.

---

### GH-03 | Concurrent Data Race in Prompter | High

**Issue**: cli/cli (huh prompter concurrency)
**Fix**: `38e10d5eb` → Parent: `95a59f4`
**Files changed**: `internal/prompter/huh_prompter.go`

**Defect**: The `MultiSelectWithSearch` prompter used `Value()` pointer bindings to expose field state to huh's `OptionsFunc`. However, huh's `OptionsFunc` runs in a goroutine while the main event loop writes field values directly, causing an unprotected data race on shared variables. Concurrent reads/writes would corrupt field state.

**Fix**: Replaced `Value()` pointer bindings with a `syncAccessor` that implements huh's `Accessor` interface with mutex-protected read/write methods. All state access now goes through synchronized gates.

**Why this category**: The fix eliminates a clear concurrency issue—unprotected shared mutable state accessed from multiple goroutines.

**Playbook angle**: Step 5a (state machines) — goroutine synchronization. Should catch by analyzing goroutine spawning and tracing whether shared variables are accessed outside synchronization primitives.

---

### GH-04 | Missing GraphQL Field in Query | Medium

**Issue**: cli/cli (headRepository field)
**Fix**: `5ed8cf0fa` → Parent: `be4960a`
**Files changed**: `pkg/cmd/pr/view/view.go`, `pkg/cmd/pr/view/view_test.go`

**Defect**: An earlier commit added `NameWithOwner` to the `PRRepository` struct for agent-task listings but did not update the `headRepository` GraphQL query to actually fetch the field. When users ran `gh pr view --json headRepository`, the JSON output included `"nameWithOwner":""` with an empty string, breaking acceptance tests that expected the field to be populated.

**Fix**: Added `nameWithOwner` to the GraphQL query projection and updated the test assertion to expect the populated field.

**Why this category**: The fix corrects a type safety issue—the struct field existed but the query contract (GraphQL schema) was not being honored.

**Playbook angle**: Step 4 (specs) — GraphQL schema alignment. Should catch by comparing struct field definitions against the actual GraphQL query selections and verifying all fields are fetched.

---

### GH-05 | Inconsistent Flag Evaluation | Medium

**Issue**: cli/cli (reviewer prompt path)
**Fix**: `391e6616d` → Parent: `bff468ba`
**Files changed**: `pkg/cmd/pr/shared/survey.go`

**Defect**: The reviewer prompt logic checked `reviewerSearchFunc != nil` directly instead of using the `useReviewerSearch` boolean flag. The assignee path used `useAssigneeSearch` at both fetch and prompt gates, but the reviewer path inconsistently checked the function pointer instead. This made the fetch and prompt decisions inconsistent, potentially causing the prompter to attempt operations on uninitialized search functions.

**Fix**: Changed the reviewer path to check `useReviewerSearch` at both gates, mirroring the assignee path logic.

**Why this category**: The fix addresses a validation gap—inconsistent flag evaluation creates semantic invariant violations (the fetch decision doesn't match the prompt decision).

**Playbook angle**: Step 3 (tests) — flag consistency patterns. Should catch by analyzing conditional branches and verifying that the same condition gates both related decisions (fetch and prompt).

---

### GH-06 | @copilot Assignee Not Replaced | High

**Issue**: cli/cli #13009 (assignee replacement)
**Fix**: `bff468baf` → Parent: `6a68ebc`
**Files changed**: `pkg/cmd/pr/shared/survey.go`, `pkg/cmd/pr/create/create.go`

**Defect**: When users ran `gh pr create --assignee @copilot`, the literal string `@copilot` was sent to the API because `NewIssueState()` only ran `MeReplacer` on assignees, not `CopilotReplacer`. The `@copilot` special placeholder was not being replaced with the actual Copilot bot actor login. Additionally, the `replaceActorsForAssignable` mutation requires a `[bot]` suffix on bot actor logins (e.g., `copilot-swe-agent[bot]`), but this suffix was missing.

**Fix**: Switched to using `SpecialAssigneeReplacer` (which handles both `@me` and `@copilot`) like the issue create command already does. Also added logic to append `[bot]` suffix for bot actors in the mutation.

**Why this category**: The fix corrects a silent failure—the command appeared to accept `@copilot` but sent invalid data to the API, violating the mutation contract.

**Playbook angle**: Step 5b (schema types) — assignee mutation API contracts. Should catch by checking mutation input types and verifying that special placeholders (@me, @copilot) are properly resolved before being sent to APIs.

---

### GH-07 | Missing Actor Assignee Mutation | High

**Issue**: cli/cli (actor assignees)
**Fix**: `e6d9019bc` → Parent: `8723e3bb`
**Files changed**: `pkg/cmd/pr/create/create.go`, `pkg/cmd/pr/create/create_test.go`

**Defect**: The `pr create` command with the `--assignee` flag failed on github.com with 'not found' errors. The mutation was attempting to resolve assignee logins to node IDs using the old bulk-fetch path instead of passing logins directly to the `ReplaceActorsForAssignable` mutation. When users provided assignees via CLI flag and then added metadata interactively, the cached `MetadataResult` had no assignee data, causing the lookup to fail.

**Fix**: Set `state.ActorAssignees = true` (which was missing) to enable the login-based assignee mutation path on github.com. Pass assignee logins directly to `ReplaceActorsForAssignable` instead of resolving to node IDs.

**Why this category**: The fix addresses a protocol violation—the wrong mutation endpoint and parameter format were being used for actor assignees.

**Playbook angle**: Step 2 (architecture) — mutation parameter threading. Should catch by verifying that mutation entry points are correctly selected based on feature capabilities and that parameters are formatted according to the mutation's contract.

---

### GH-08 | Hardcoded API Endpoint | Critical

**Issue**: cli/cli #12956 (Copilot API URL)
**Fix**: `78b958f9a` → Parent: `3780dd5`
**Files changed**: `pkg/cmd/agent-task/capi/client.go`, `pkg/cmd/agent-task/capi/client_test.go`, `pkg/cmd/agent-task/shared.go`

**Defect**: The `agent-task` command hardcoded the Copilot API URL as `https://api.githubcopilot.com`, causing 401 authentication errors for ghe.com tenancy users whose Copilot API lives at a different endpoint. The host check in the transport also hardcoded `api.githubcopilot.com`, preventing proper conditional header injection for tenancy-specific Copilot API hosts.

**Fix**: Query `viewer.copilotEndpoints.api` from the GitHub GraphQL API to dynamically resolve the correct Copilot API URL for the user's host. Pass the resolved `capiBaseURL` to `NewCAPIClient()` and parse the host from it for conditional header logic in the transport.

**Why this category**: The fix corrects a critical configuration error—hardcoded hostnames prevent the system from working across different deployment environments.

**Playbook angle**: Step 5b (schema types) — endpoint configuration patterns. Should catch by searching for hardcoded host/URL strings and verifying they should be resolved dynamically or from configuration.

---

### GH-09 | Invalid Search Qualifiers Accepted | Medium

**Issue**: cli/cli (issue search validation)
**Fix**: `519425692` → Parent: `628dea6`
**Files changed**: `pkg/cmd/issue/list/http.go`, `pkg/cmd/issue/list/http_test.go`

**Defect**: The `gh issue list` command accepted pull request-only search qualifiers (e.g., `is:pr`, `type:pr`) without validation. These qualifiers are only valid for `gh pr list`, not for `gh issue list`. Users would provide invalid search qualifiers that the GitHub API would accept but produce no results, with no feedback about the invalid qualifier.

**Fix**: Added a regex check in `searchIssues()` to detect and reject PR-only qualifiers, directing users to use `gh pr list` instead.

**Why this category**: The fix adds a missing validation check at the input boundary to prevent invalid search parameters from being sent to the API.

**Playbook angle**: Step 3 (tests) — input validation boundaries. Should catch by analyzing GitHub API documentation for search qualifiers and checking whether the command validates them before use.

---

### GH-10 | Draft Issue Title/Body Lost | High

**Issue**: cli/cli (project item-edit)
**Fix**: `d21544c08` → Parent: `cf862d6`
**Files changed**: `pkg/cmd/project/item-edit/item_edit.go`, `pkg/cmd/project/item-edit/item_edit_test.go`, `pkg/cmd/project/shared/queries/queries.go`

**Defect**: The `project item-edit` command with partial flags (e.g., `--text` without `--title`) overwrote title and body with empty strings. The code checked `cmd.Flags().Changed()` for individual flags but then unconditionally assigned empty strings to unset fields instead of preserving the current draft issue's title/body. Running `project item-edit --text "new content"` would clear the title.

**Fix**: Fetch the current draft issue data before making updates. Check `cmd.Flags().Changed()` for each field and only update fields that were explicitly provided via flags, preserving unchanged fields.

**Why this category**: The fix corrects a silent failure—the command appeared to work but destroyed user data without warning or validation.

**Playbook angle**: Step 5 (defensive) — partial update semantics. Should catch by analyzing CRUD patterns and verifying that partial updates preserve unchanged fields instead of overwriting them with defaults.

---

### GH-11 | Invalid ANSI Escape Sequence | Medium

**Issue**: cli/cli #12683 (ANSI SGR code)
**Fix**: `48951aca0` → Parent: `3521604`
**Files changed**: `pkg/view/colorize.go`

**Defect**: The JSON and diff colorization used the SGR (Select Graphic Rendition) escape code `1;38`, which is invalid. SGR parameter 38 is the extended foreground color prefix and requires sub-parameters (e.g., `38;5;n` for 256-color or `38;2;r;g;b` for RGB), so using it bare produces a malformed escape sequence. Most terminals silently ignore the invalid parameter, masking the bug. On stricter terminal implementations, the escape sequence would be ignored entirely.

**Fix**: Replaced `1;38` with `1;37` (bold white), which is a valid SGR sequence.

**Why this category**: The fix corrects a serialization error in output formatting—the ANSI codes were being generated incorrectly.

**Playbook angle**: Step 6 (quality risks) — terminal output correctness. Should catch by analyzing ANSI escape sequence generation and validating against SGR specification requirements.

---

### GH-12 | Feature Detection Error Ignored | Medium

**Issue**: cli/cli (workflow run feature detection)
**Fix**: `31f375608` → Parent: `52eca96`
**Files changed**: `pkg/cmd/workflow/run/run.go`

**Defect**: The `workflow run` command silently swallowed feature detection errors when calling `ActionsFeatures()`. If the feature detection query failed (e.g., due to network issues or API unavailability), the command would assume the feature was unsupported and silently degrade functionality instead of reporting the error. This prevented users from knowing whether the failure was due to missing server capability or a transient error.

**Fix**: Changed the error handling to return the error immediately if `ActionsFeatures()` fails instead of assuming the feature is unsupported.

**Why this category**: The fix addresses error handling—errors were being swallowed, causing silent degradation instead of fail-fast behavior.

**Playbook angle**: Step 5 (defensive) — error propagation. Should catch by analyzing error returns and verifying that errors are propagated rather than silently treated as missing features.

---

### GH-13 | URL Encoding Missing | High

**Issue**: cli/cli (workflow dispatch URL)
**Fix**: `36a85fd71` → Parent: `3e9fbbb`
**Files changed**: `pkg/cmd/workflow/run/run.go`

**Defect**: The `workflow run` command compiled the dispatch URL without escaping workflow names, causing the command to break with workflow files containing special characters (e.g., spaces, slashes, or URL-reserved characters). A workflow named `deploy/staging.yml` would generate an invalid URL path.

**Fix**: Applied `url.PathEscape()` when building the dispatch URL path to properly escape special characters in the workflow name.

**Why this category**: The fix addresses an API contract violation—URLs must be properly encoded per RFC 3986, but the implementation violated this requirement.

**Playbook angle**: Step 5b (schema types) — URL encoding contracts. Should catch by identifying all user-supplied data that becomes part of URL paths and verifying that escaping is applied.

---

### GH-14 | Feature Detection Not Implemented | Medium

**Issue**: cli/cli (ActionsFeatures method)
**Fix**: `a0dea00fd` → Parent: `1af282`
**Files changed**: `internal/featuredetection/feature_detection.go`

**Defect**: The feature detection system had no `ActionsFeatures()` method, but the `workflow run` command needed it to detect whether the server supports workflow dispatch with `DispatchRunDetails` capability. The method was called but not implemented, causing a compilation error or runtime panic depending on how the interface was defined.

**Fix**: Implemented the `ActionsFeatures()` method to query the `gh.ActionsFeatureDetection` GraphQL fields and return capability detection results for workflow dispatch operations.

**Why this category**: The fix adds a missing boundary check—a required interface method was not implemented.

**Playbook angle**: Step 3 (tests) — capability detection. Should catch by analyzing interface contracts and verifying that all methods called on a type are actually implemented.

---

### GH-15 | Scope Error Clarification | Low

**Issue**: cli/cli (issue create scope error)
**Fix**: `6f739036b` → Parent: `150834`
**Files changed**: `api/client.go`

**Defect**: When creating issues for projects, the API returned a generic scope error without detail. Users with insufficient permissions would see `scope error` with no indication of which scopes were needed, making it impossible to fix permission issues.

**Fix**: Implemented the `Clarifier` interface on the scope error to provide detailed error message text explaining the required scopes: "Contents:Read and Projects:Write scopes are required."

**Why this category**: The fix improves error handling by providing clear, actionable error messages instead of generic errors.

**Playbook angle**: Step 5 (defensive) — error message clarity. Should catch by analyzing error returns and verifying that error messages provide actionable guidance.

---

### GH-16 | Cannot Clear Reviewers | High

**Issue**: cli/cli (pr edit reviewers)
**Fix**: `d643d5386` → Parent: `7f8ca2c`
**Files changed**: `pkg/cmd/pr/edit/edit.go`, `pkg/cmd/pr/edit/edit_test.go`

**Defect**: The `pr edit --remove-reviewer "*"` command in replace mode couldn't clear all reviewers. Empty slices were being omitted from the GraphQL mutation due to `omitempty` JSON tags and `len > 0` conditional checks in the code. The mutation would never send an explicit empty list to clear the reviewers, so the operation would silently fail to remove anything.

**Fix**: Unconditionally send explicit empty slices for `userLogins`, `botLogins`, and `teamSlugs` in the `RequestReviewsByLogin` mutation, even when empty. Empty slices are harmless no-ops in union mode, simplifying the logic.

**Why this category**: The fix addresses a silent failure—the command appeared to succeed but didn't actually clear reviewers due to JSON serialization behavior.

**Playbook angle**: Step 5 (defensive) — empty collection handling. Should catch by analyzing JSON marshaling and verifying that empty slices are intentionally included in mutations that need to support clearing fields.

---

### GH-17 | Wrong Platform Asset Name | Medium

**Issue**: cli/cli (copilot download)
**Fix**: `bc5a44a4a` → Parent: `10b4a1f`
**Files changed**: `pkg/cmd/copilot/copilot.go`

**Defect**: The `copilot download` command used the Go runtime string `runtime.GOOS` value `"windows"` directly when constructing asset names, but the assets in releases are named with the string `"win32"` (matching Node.js conventions). The asset lookup would fail on Windows with "asset not found" errors.

**Fix**: Added a platform string mapping that converts `runtime.GOOS` value `"windows"` to `"win32"` before using it in asset name construction.

**Why this category**: The fix corrects a configuration error—runtime values need to be mapped to external naming conventions.

**Playbook angle**: Step 2 (architecture) — platform abstraction. Should catch by analyzing platform-specific code paths and verifying that runtime identifiers are mapped to external naming conventions.

---

### GH-18 | Extension Name Collision | High

**Issue**: cli/cli (extension registration)
**Fix**: `10b4a1f42` → Parent: `08a4413`
**Files changed**: `pkg/cmd/root/root.go`, `pkg/cmd/root/extension_registration_test.go`

**Defect**: Extensions with names matching core command names (e.g., an extension named `copilot`, `pr`, or `issue`) were silently registered and would override the core commands. Users installing a malicious extension with a conflicting name could shadow the legitimate command, potentially capturing all usage of that command. No warning was issued.

**Fix**: Added a check against registered core command names and aliases during extension registration. Extensions with colliding names are skipped with a warning message instead of being registered.

**Why this category**: The fix addresses a state machine gap—the command registration order allows extensions to override core commands without validation.

**Playbook angle**: Step 5a (state machines) — command registration ordering. Should catch by analyzing registration logic and verifying that name collisions are detected and rejected.

---

### GH-19 | Invalid Remote Flag Combination | Medium

**Issue**: cli/cli #2722 (repo fork --remote)
**Fix**: `3f0044fd9` → Parent: `6acf74e`
**Files changed**: `pkg/cmd/repo/fork/fork.go`, `pkg/cmd/repo/fork/fork_test.go`

**Defect**: The `gh repo fork --remote` flag with a repo argument silently ignored `--remote`. When providing a repo argument (e.g., `gh repo fork owner/repo --remote`), the command operates independently of the local repository, so there's no local repository to add the remote to. The `--remote` flag should error with a clear message, but instead it was silently ignored, confusing users.

**Fix**: Return an explicit error when both `--remote` and a repo argument are provided, explaining that `--remote` requires no repo argument (it only works with the current local repo).

**Why this category**: The fix adds a missing validation check for mutually exclusive flag combinations.

**Playbook angle**: Step 3 (tests) — mutual exclusivity validation. Should catch by analyzing command flags and verifying that incompatible flag combinations are validated and rejected with clear messages.

---

### GH-20 | Identical Branch Refs Allowed | Medium

**Issue**: cli/cli (pr create branch validation)
**Fix**: `9daa22eba` → Parent: `6acf74e`
**Files changed**: `pkg/cmd/pr/create/create.go`, `pkg/cmd/pr/create/create_test.go`

**Defect**: The `gh pr create` command allowed creating a pull request where the head and base refs pointed to the same ref in the same repository. This would submit a malformed PR request with `head==base` in the same repo, violating the semantic invariant that a PR must differ from its base. Cross-repository PRs with the same branch name (e.g., from forks) remained valid.

**Fix**: Added an early validation check: if head and base refs are identical in the same repository, return a clear error message instead of attempting to create the PR.

**Why this category**: The fix adds a semantic invariant check to prevent invalid PR creation.

**Playbook angle**: Step 5 (defensive) — semantic invariant checks. Should catch by analyzing domain constraints (a PR must differ from its base) and verifying they're enforced before API calls.

---

## Summary

These 20 defects span multiple categories:

- **API contract violations**: GH-01, GH-02, GH-06, GH-13, GH-26, GH-27 (6 defects)
- **Concurrency issues**: GH-03, GH-63 (2 defects)
- **Configuration errors**: GH-08, GH-17, GH-51, GH-54 (4 defects)
- **Error handling**: GH-12, GH-15, GH-29, GH-44, GH-45, GH-47, GH-52, GH-53, GH-56 (9 defects, but only 4 in first 20)
- **Missing boundary checks**: GH-14, GH-38 (2 defects, but only 1 in first 20)
- **Protocol violations**: GH-07, GH-49, GH-55 (3 defects, but only 1 in first 20)
- **Silent failures**: GH-06, GH-10, GH-16, GH-28, GH-31, GH-39, GH-43 (7 defects, but only 3 in first 20)
- **State machine gaps**: GH-18, GH-37, GH-57, GH-58, GH-64, GH-65 (6 defects, but only 1 in first 20)
- **Type safety**: GH-04, GH-36, GH-46, GH-48, GH-61 (5 defects, but only 1 in first 20)
- **Validation gaps**: GH-05, GH-09, GH-19, GH-20, GH-32, GH-34, GH-40 (7 defects, but only 4 in first 20)

**Severity distribution in GH-01 through GH-20**:
- Critical: 1 (GH-08)
- High: 10 (GH-01, GH-02, GH-03, GH-06, GH-07, GH-10, GH-13, GH-16, GH-18)
- Medium: 9 (GH-04, GH-05, GH-09, GH-11, GH-12, GH-14, GH-17, GH-19, GH-20)

All defects were identified by examining actual git diffs and understanding the semantic changes introduced by each fix commit.
