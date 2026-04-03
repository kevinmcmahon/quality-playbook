# modelcontextprotocol/servers Defects — Quality Playbook Benchmark (QPB)

**Repository**: [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)
**Language**: TypeScript, Python
**Repo type**: Infrastructure (MCP tool server implementations)
**Defect count**: 8 (MCP-01 through MCP-08; initial catalog)
**Generated**: 2026-03-31

The official MCP (Model Context Protocol) reference servers. These implement the tool interfaces that AI agents call — filesystem, git, memory, fetch, sequential-thinking, etc. Defects here directly impact agent capabilities.

---

## MCP-01 | Argument Injection in Git Server (4 Unguarded Functions) | security issue | Critical

**Fix commit**: [`ae40ec2`](https://github.com/modelcontextprotocol/servers/commit/ae40ec2)
**Pre-fix commit**: `ae40ec2~1`
**Issue/PR**: [#3545](https://github.com/modelcontextprotocol/servers/pull/3545)

**Files changed**:
- `src/git/src/mcp_server_git/server.py`
- `src/git/tests/test_server.py`

**Commit message**:
```
fix(git): add missing argument injection guards to git_show, git_create_branch,
git_log, and git_branch

Extends existing startswith("-") input validation to git_show, git_create_branch,
git_log, and git_branch, preventing user-supplied values from being interpreted
as CLI flags by GitPython's subprocess calls to git.
```

**Defect summary**: The git MCP server had argument injection guards on some functions (git_diff, git_commit) but missed four others: `git_show`, `git_create_branch`, `git_log`, and `git_branch`. User-supplied values starting with `-` could be interpreted as CLI flags by GitPython's subprocess calls to git. For example, a malicious revision string like `--exec=<command>` passed to `git_show` could execute arbitrary commands. The fix extends the existing `startswith("-")` validation pattern to all four unguarded functions.

**Diff stat**:
```
 2 files changed, 79 insertions(+)
```

**Playbook angle**: Step 5c (parallel code paths) — the same guard existed on some functions but not all. Step 6 (domain knowledge) — argument injection via `-` prefix is a well-known attack vector for CLI wrappers.

---

## MCP-02 | Windows Drive Letter Normalizes to Current Directory Instead of Root | missing boundary check | High

**Fix commit**: [`b60eca1`](https://github.com/modelcontextprotocol/servers/commit/b60eca1)
**Pre-fix commit**: `b60eca1~1`
**Issue/PR**: [#3434](https://github.com/modelcontextprotocol/servers/pull/3434), fixes [#3418](https://github.com/modelcontextprotocol/servers/issues/3418)

**Files changed**:
- `src/filesystem/path-utils.ts`
- `src/filesystem/__tests__/path-utils.test.ts`

**Commit message**:
```
fix(filesystem): ensure bare Windows drive letters normalize to root

Appends path.sep to bare drive letters (e.g. "C:") before calling
path.normalize(), preventing them from normalizing to "C:." (current
directory on drive) instead of "C:\" (drive root).
```

**Defect summary**: On Windows, `path.normalize("C:")` returns `"C:."` (current directory on C: drive) rather than `"C:\"` (C: drive root). When users specified a bare drive letter as an allowed directory, the filesystem server would normalize it to `"C:."`, breaking subsequent path validation. Files at the drive root would be incorrectly rejected, and the effective allowed directory would silently change based on the process's current working directory.

**Diff stat**:
```
 2 files changed, ~20 insertions(+)
```

**Playbook angle**: Step 5d (boundary conditions) — edge case with bare drive letters. Step 6 (domain knowledge) — Windows `path.normalize()` behavior with drive letters is a known gotcha.

---

## MCP-03 | Boolean Coercion Treats "false" as true in Sequential Thinking | type safety | High

**Fix commit**: [`1cdf806`](https://github.com/modelcontextprotocol/servers/commit/1cdf806)
**Pre-fix commit**: `1cdf806~1`
**Issue/PR**: [#3533](https://github.com/modelcontextprotocol/servers/pull/3533)

**Files changed**:
- `src/sequential-thinking/src/index.ts`

**Commit message**:
```
fix(sequential-thinking): use z.coerce for number and safe preprocess for boolean params

Uses z.coerce.number() for number fields and a z.preprocess() helper for
boolean fields to handle string-typed parameters from LLM clients. The
preprocess approach correctly handles "false" → false, avoiding the
z.coerce.boolean() footgun where Boolean("false") === true.
```

**Defect summary**: LLM clients often send parameters as strings. The sequential-thinking server used Zod schemas with strict types, causing string `"5"` to fail number validation and string `"false"` to fail boolean validation. The naive fix (`z.coerce.boolean()`) would coerce `"false"` to `true` because JavaScript's `Boolean("false") === true`. The fix uses `z.coerce.number()` for numbers and a custom `z.preprocess()` for booleans that correctly handles the string `"false"`.

**Diff stat**:
```
 1 file changed, ~15 insertions(+), ~5 deletions(-)
```

**Playbook angle**: Step 5b (type coercion) — string-to-boolean coercion is a known footgun in JavaScript. Step 5d (generated/invisible code) — LLM clients generate string parameters that the server must handle correctly.

---

## MCP-04 | Memory Server Silently Drops Relations to External Nodes | silent failure | High

**Fix commit**: [`ca7ea22`](https://github.com/modelcontextprotocol/servers/commit/ca7ea22)
**Pre-fix commit**: `ca7ea22~1`
**Issue/PR**: [#3297](https://github.com/modelcontextprotocol/servers/pull/3297)

**Files changed**:
- `src/memory/src/index.ts`

**Commit message**:
```
fix(memory): return relations connected to requested nodes in openNodes/searchNodes

Previously, openNodes and searchNodes only returned relations where BOTH
endpoints were in the result set (using &&). This silently dropped all
relations to/from nodes outside the set — making it impossible to discover
a node's connections without calling read_graph.
```

**Defect summary**: The memory knowledge graph server's `openNodes` and `searchNodes` tools filtered relations using `&&` (both endpoints must be in result set) instead of `||` (either endpoint). This silently dropped all relations connecting to nodes outside the current result set. An agent opening a specific node would see zero connections to the rest of the graph, making the knowledge graph appear disconnected. The only way to see relations was to call `read_graph` (which returns the entire graph), defeating the purpose of targeted node queries.

**Diff stat**:
```
 1 file changed, ~5 insertions(+), ~5 deletions(-)
```

**Playbook angle**: Step 5 (defensive patterns) — `&&` vs `||` in filter predicates is a classic logic error. Step 5a (state machines) — graph traversal queries must correctly handle boundary nodes.

---

## MCP-05 | macOS Symlink Resolution Rejects Valid /tmp Paths | configuration error | Medium

**Fix commit**: [`8f2e9cc`](https://github.com/modelcontextprotocol/servers/commit/8f2e9cc)
**Pre-fix commit**: `8f2e9cc~1`
**Issue/PR**: Fixes [#3253](https://github.com/modelcontextprotocol/servers/issues/3253)

**Files changed**:
- `src/filesystem/index.ts`

**Commit message**:
```
fix(filesystem): resolve symlinked allowed directories to both forms

On macOS, /tmp is a symlink to /private/tmp. When users specify /tmp
as an allowed directory, the server was resolving it to /private/tmp
during startup but then rejecting paths like /tmp/file.txt because
they don't start with /private/tmp.
```

**Defect summary**: The filesystem server resolved allowed directory symlinks during startup (e.g., `/tmp` → `/private/tmp`) but then only validated against the resolved form. Users specifying `/tmp` as an allowed directory found that paths like `/tmp/file.txt` were rejected because the path didn't start with `/private/tmp`. The fix stores both the original normalized path and the resolved path, accepting access through either form.

**Diff stat**:
```
 1 file changed, ~20 insertions(+), ~10 deletions(-)
```

**Playbook angle**: Step 5d (boundary conditions) — symlink resolution must preserve both forms. Step 6 (domain knowledge) — macOS `/tmp` → `/private/tmp` symlink is a well-known platform-specific gotcha.

---

## MCP-06 | Fetch Server Crashes on Malformed JSON-RPC Input | error handling | Medium

**Fix commit**: [`83b2205`](https://github.com/modelcontextprotocol/servers/commit/83b2205)
**Pre-fix commit**: `83b2205~1`
**Issue/PR**: [#3515](https://github.com/modelcontextprotocol/servers/pull/3515)

**Files changed**:
- `src/fetch/src/mcp_server_fetch/server.py`

**Commit message**:
```
fix(fetch): handle malformed input without crashing

Changes raise_exceptions=True to raise_exceptions=False in the fetch
server's Server.run() call, preventing the server from crashing on
malformed JSON-RPC input. This aligns with the SDK's intended default
behavior and is consistent with other reference servers.
```

**Defect summary**: The fetch MCP server was configured with `raise_exceptions=True`, causing it to crash entirely when receiving malformed JSON-RPC input instead of returning a proper error response. Other reference servers used the default `raise_exceptions=False`. A single malformed request would kill the server process, disconnecting all clients.

**Diff stat**:
```
 1 file changed, 1 insertion(+), 1 deletion(-)
```

**Playbook angle**: Step 6 (error handling) — servers must not crash on malformed input. Step 5c (parallel code paths) — inconsistent configuration across sibling servers.

---

## MCP-07 | Filesystem Server Crashes When Configured Directory Is Unavailable | error handling | Medium

**Fix commit**: [`2dfa15d`](https://github.com/modelcontextprotocol/servers/commit/2dfa15d)
**Pre-fix commit**: `2dfa15d~1`

**Files changed**:
- `src/filesystem/index.ts`

**Commit message**:
```
fix(filesystem): gracefully handle unavailable directories

Previously, the server would crash if any configured directory was
unavailable (e.g., unmounted external drive). Now it:
- Filters out inaccessible directories with a warning
```

**Defect summary**: The filesystem server crashed at startup if any configured allowed directory was inaccessible (e.g., unmounted external drive, deleted directory, permission denied). A single unavailable directory in the configuration would prevent the server from starting entirely, even if other configured directories were valid. The fix filters out inaccessible directories with a warning instead of crashing.

**Diff stat**:
```
 1 file changed, ~15 insertions(+), ~5 deletions(-)
```

**Playbook angle**: Step 6 (error handling) — graceful degradation when configuration is partially valid. Step 5d (boundary conditions) — what happens when external resources are unavailable at startup.

---

## MCP-08 | Filesystem structuredContent Returns Array Instead of String | type safety | Low

**Fix commit**: [`968acc2`](https://github.com/modelcontextprotocol/servers/commit/968acc2)
**Pre-fix commit**: `968acc2~1`
**Issue/PR**: [#3113](https://github.com/modelcontextprotocol/servers/pull/3113)

**Files changed**:
- `src/filesystem/src/index.ts`

**Commit message**:
```
fix(filesystem): return string in structuredContent to match outputSchema

The directory_tree, move_file, and list_directory_with_sizes tools were
returning an array in structuredContent.content, but outputSchema declares
the field as a string type.
```

**Defect summary**: Three filesystem tools (`directory_tree`, `move_file`, `list_directory_with_sizes`) declared their `outputSchema` with string-typed content fields but returned arrays in `structuredContent.content`. Clients validating tool responses against the declared schema would reject these responses as type mismatches.

**Diff stat**:
```
 1 file changed, ~10 insertions(+), ~10 deletions(-)
```

**Playbook angle**: Step 5b (type safety) — return type must match declared schema. Step 4 (specifications) — outputSchema is the contract between server and client.

---

## Summary

| ID | Title | Category | Severity | Server |
|----|-------|----------|----------|--------|
| MCP-01 | Argument injection in 4 git functions | security issue | Critical | git |
| MCP-02 | Windows drive letter normalization | missing boundary check | High | filesystem |
| MCP-03 | Boolean "false" coerced to true | type safety | High | sequential-thinking |
| MCP-04 | Relations silently dropped in queries | silent failure | High | memory |
| MCP-05 | macOS symlink rejects valid /tmp paths | configuration error | Medium | filesystem |
| MCP-06 | Fetch crashes on malformed input | error handling | Medium | fetch |
| MCP-07 | Server crashes on unavailable directory | error handling | Medium | filesystem |
| MCP-08 | structuredContent type mismatch | type safety | Low | filesystem |

**Category distribution**: security issue (1), type safety (2), error handling (2), missing boundary check (1), silent failure (1), configuration error (1)
**Severity distribution**: Critical (1), High (3), Medium (3), Low (1)
**Server distribution**: filesystem (4), git (1), memory (1), fetch (1), sequential-thinking (1)
