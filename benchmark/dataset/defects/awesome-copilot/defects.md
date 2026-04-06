# github/awesome-copilot Defects — Quality Playbook Benchmark (QPB)

**Repository**: [github/awesome-copilot](https://github.com/github/awesome-copilot)
**Language**: Markdown (AI skill/agent definitions with embedded YAML, JSON, Python, Shell)
**Repo type**: Skill/Agent Registry
**Defect count**: 10 (AC-01 through AC-10; initial catalog)
**Generated**: 2026-03-31

This is the first QPB defect file for a non-code repository. Skills and agents are Markdown-based AI instruction documents that define behavior, tool references, API schemas, and workflows. Defects in these files cause agents to fail, produce incorrect output, reference non-existent tools, or give fabricated instructions to users.

---

## AC-01 | Fabricated Install Commands in Copilot CLI Skill | validation gap | High

**Fix commit**: [`6687524`](https://github.com/github/awesome-copilot/commit/6687524)
**Pre-fix commit**: `6687524~1`
**Issue/PR**: Review thread (no issue number)

**Files changed**:
- `skills/copilot-cli-quickstart/SKILL.md`

**Commit message**:
```
fix: add allowed-tools, fix fabricated install commands

- Add allowed-tools field to frontmatter (ask_user, sql,
  fetch_copilot_cli_documentation) addressing review threads
- Note CLI-specific targeting in description
- Replace fabricated install commands (brew, npm, winget, curl)
  with correct GitHub CLI paths (gh copilot)
```

**Defect summary**: The skill contained four completely fabricated installation commands: `brew install copilot-cli`, `npm install -g @github/copilot`, `winget install GitHub.Copilot`, and `curl -fsSL https://gh.io/copilot-install | bash`. None of these packages or URLs exist. Users following these instructions would get package-not-found errors. The correct path is `gh copilot` (built into GitHub CLI). Additionally, the skill's frontmatter was missing the `allowed-tools` field, preventing proper tool sandboxing.

**Diff stat**:
```
skills/copilot-cli-quickstart/SKILL.md | 13 +++++++------
 1 file changed, 7 insertions(+), 6 deletions(-)
```

**Playbook angle**: Step 4 (specifications) — verify that all commands, URLs, and package names referenced in instructions actually exist. Step 6 (domain knowledge) — fabricated package names are a known failure mode of LLM-generated content.

---

## AC-02 | Incorrect GraphQL Return Field in Dependencies Reference | API contract violation | Medium

**Fix commit**: [`cf4e33e`](https://github.com/github/awesome-copilot/commit/cf4e33e)
**Pre-fix commit**: `cf4e33e~1`
**Issue/PR**: [#946](https://github.com/github/awesome-copilot/pull/946)

**Files changed**:
- `skills/github-issues/references/dependencies.md`
- `skills/github-issues/SKILL.md`
- `docs/README.skills.md`

**Commit message**:
```
fix: improve github-issues skill trigger phrases and fix GraphQL dependency examples

- Add dependency/blocking trigger phrases to skill description so the
  skill activates on requests like 'link issues', 'add dependency',
  'blocked by', and 'blocking'
- Fix incorrect GraphQL return field in dependencies.md: blockedByIssue
  does not exist on AddBlockedByPayload; the correct field is
  blockingIssue
```

**Defect summary**: The dependencies reference document contained two GraphQL mutation examples that used `blockedByIssue` as the return field on `AddBlockedByPayload`. This field does not exist in the GitHub GraphQL schema; the correct field is `blockingIssue`. An agent following these examples would generate GraphQL mutations that return schema validation errors.

**Diff stat**:
```
docs/README.skills.md                           | 2 +-
skills/github-issues/SKILL.md                   | 2 +-
skills/github-issues/references/dependencies.md | 4 ++--
 3 files changed, 4 insertions(+), 4 deletions(-)
```

**Playbook angle**: Step 5 (defensive patterns) — verify API field names in reference documentation against actual schemas. Step 6 (domain knowledge) — GraphQL schema mismatches are a common failure mode when reference docs are written from memory rather than tested.

---

## AC-03 | Wrong MCP Tool Names and Missing Search Reference | API contract violation | High

**Fix commit**: [`fca5de1`](https://github.com/github/awesome-copilot/commit/fca5de1)
**Pre-fix commit**: `fca5de1~1`
**Issue/PR**: [#888](https://github.com/github/awesome-copilot/pull/888)

**Files changed**:
- `skills/github-issues/SKILL.md`
- `skills/github-issues/references/search.md` (new)
- `skills/github-issues/references/issue-fields.md` (modified)

**Commit message**:
```
Improve github-issues skill: fix MCP tools, add search reference, fix sub-issues docs
```

**Defect summary**: The github-issues skill referenced MCP tool names that did not match the canonical tool names in the GitHub MCP server. When the agent attempted to invoke these tools, the MCP server would reject the calls with "unknown tool" errors. Additionally, the skill had no reference for advanced search syntax, causing the agent to generate incorrect search queries.

**Diff stat**:
```
 skills/github-issues/SKILL.md                   |  12 ++--
 skills/github-issues/references/issue-fields.md |  45 +++++++++++
 skills/github-issues/references/search.md       | 128 +++++++++++++++++++++++++++
 3 files changed, 179 insertions(+), 6 deletions(-)
```

**Playbook angle**: Step 5 (defensive patterns) — verify tool name references against the actual MCP server/tool registry. Step 4 (specifications) — skill instructions must reference tools by their canonical names.

---

## AC-04 | Large Presentation Converter Crashes on External Assets | missing boundary check | High

**Fix commit**: [`07e1e66`](https://github.com/github/awesome-copilot/commit/07e1e66)
**Pre-fix commit**: `07e1e66~1`
**Issue/PR**: [#1090](https://github.com/github/awesome-copilot/pull/1090)

**Files changed**:
- `skills/publish-to-pages/SKILL.md`
- `skills/publish-to-pages/scripts/convert-pdf.py`
- `skills/publish-to-pages/scripts/convert-pptx.py`
- `skills/publish-to-pages/scripts/publish.sh`

**Commit message**:
```
fix: handle large presentations with external assets mode
```

**Defect summary**: The PPTX-to-HTML converter embedded all images as base64 data URIs in a single HTML file. For large presentations with many high-resolution images, this produced HTML files exceeding browser memory limits, causing silent rendering failures or crashes. The fix added an external assets mode that writes images to a separate directory and references them via relative paths, with automatic detection based on total image payload size.

**Diff stat**:
```
skills/publish-to-pages/SKILL.md                |  21 +++-
skills/publish-to-pages/scripts/convert-pdf.py  |  83 ++++++++++---
skills/publish-to-pages/scripts/convert-pptx.py | 154 +++++++++++++++++-------
skills/publish-to-pages/scripts/publish.sh      |  13 +-
 4 files changed, 212 insertions(+), 59 deletions(-)
```

**Playbook angle**: Step 5d (boundary conditions) — what happens when input is very large? Silent truncation/crash on large inputs is a classic boundary condition failure.

---

## AC-05 | Handoff JSON Schema Undefined in Planner Agent | API contract violation | Medium

**Fix commit**: [`fdef8ed`](https://github.com/github/awesome-copilot/commit/fdef8ed)
**Pre-fix commit**: `fdef8ed~1`

**Files changed**:
- `agents/gem-chrome-tester.agent.md`
- `agents/gem-devops.agent.md`
- `agents/gem-documentation-writer.agent.md`
- `agents/gem-implementer.agent.md`
- `agents/gem-planner.agent.md`
- `agents/gem-researcher.agent.md`
- `agents/gem-reviewer.agent.md`

**Commit message**:
```
fix: handoff json issue
```

**Defect summary**: Seven gem-team agents had vague or missing handoff JSON schemas. The planner agent's workflow said "Return JSON handoff" without specifying the schema, making it impossible for the orchestrator agent to reliably parse planner output. The fix replaced the vague instruction with an explicit schema: `{"status": "success|failed|needs_revision", "task_id": "[task_id]", "summary": "[brief summary]"}`. Similar fixes were applied to 6 other agents in the gem-team.

**Diff stat**:
```
 7 files changed, 15 insertions(+), 15 deletions(-)
```

**Playbook angle**: Step 5a (state machines) — inter-agent communication contracts must be explicit. Step 4 (specifications) — handoff schemas are the API contract between agents.

---

## AC-06 | Invalid File References Across 8 Gem-Team Agents | configuration error | High

**Fix commit**: [`21507bf`](https://github.com/github/awesome-copilot/commit/21507bf)
**Pre-fix commit**: `21507bf~1`

**Files changed**:
- `agents/gem-browser-tester.agent.md`
- `agents/gem-devops.agent.md`
- `agents/gem-documentation-writer.agent.md`
- `agents/gem-implementer.agent.md`
- `agents/gem-orchestrator.agent.md`
- `agents/gem-planner.agent.md`
- `agents/gem-researcher.agent.md`
- `agents/gem-reviewer.agent.md`

**Commit message**:
```
fix: invlaid file references
```

**Defect summary**: Eight agents in the gem-team referenced files and paths that did not exist, including references to non-existent YAML files, incorrect directory structures, and stale file paths from a previous project layout. When agents attempted to read or write to these paths, they would fail silently or produce errors. The orchestrator agent additionally had stale workflow instructions referencing deleted procedures.

**Diff stat**:
```
 8 files changed, 25 insertions(+), 25 deletions(-)
```

**Playbook angle**: Step 5 (defensive patterns) — verify all file path references in agent instructions against actual project structure. Step 5c (parallel path consistency) — when multiple agents reference the same file structure, all references must be consistent.

---

## AC-07 | Deprecated Tool Names in Principal Software Engineer Agent | API contract violation | Medium

**Fix commit**: [`ac30511`](https://github.com/github/awesome-copilot/commit/ac30511)
**Pre-fix commit**: `ac30511~1`
**Issue/PR**: [#1198](https://github.com/github/awesome-copilot/pull/1198)

**Files changed**:
- `agents/principal-software-engineer.agent.md`

**Commit message**:
```
fix: update tool names to canonical VS Code format in principal-software-engineer agent

Replace deprecated/incorrect tool references with canonical VS Code built-in
tool names per https://code.visualstudio.com/docs/copilot/reference/copilot-vscode-features:

 search/changes (add correct prefix)
 vscode/extensions (add correct prefix)
 read/problems (add correct prefix)
 search/usages (add correct prefix)
 execute/testFailure (add correct prefix)
 vscode/VSCodeAPI (correct casing and prefix)
 search/textSearch (renamed tool)
 read/terminalLastCommand (moved to read/)
 read/terminalSelection (moved to read/)
 execute (renamed tool set)
 execute/createAndRunTask (renamed)
```

**Defect summary**: The agent referenced 11+ VS Code tool names using deprecated or incorrect formats (missing namespace prefixes, wrong casing, outdated names from a previous API version). When VS Code's Copilot runtime attempted to resolve these tool references, they would fail with "unknown tool" errors, preventing the agent from performing core operations like searching code, running tests, or reading terminal output.

**Diff stat**:
```
agents/principal-software-engineer.agent.md | 22 +++++++++++-----------
 1 file changed, 11 insertions(+), 11 deletions(-)
```

**Playbook angle**: Step 6 (domain knowledge) — tool names are versioned APIs; agents must reference canonical names. Step 5d (generated/invisible code) — tool name resolution happens at runtime and is invisible in the Markdown source.

---

## AC-08 | Terraform Agent Missing MCP Server Declaration and Broken Config | configuration error | High

**Fix commit**: [`cc56faa`](https://github.com/github/awesome-copilot/commit/cc56faa)
**Pre-fix commit**: `cc56faa~1`
**Issue/PR**: [#369](https://github.com/github/awesome-copilot/pull/369)

**Files changed**:
- `agents/terraform.agent.md`
- `collections/partners.md`
- `docs/README.agents.md`

**Commit message**:
```
fix: Terraform Agent - adding terraform mcp and other fixes
```

**Defect summary**: The Terraform agent was missing its MCP server declaration entirely — the frontmatter had no `mcp-servers` or `tools` field. Without these, the agent had no way to invoke Terraform operations (registry queries, workspace management, run orchestration). The agent's description was also a single run-on sentence that didn't mention MCP capabilities, and the instructions body was incomplete. The fix added the full `mcp-servers` block with Docker-based Terraform MCP server configuration, added the `tools` field, rewrote the description, and substantially expanded the instructions.

**Diff stat**:
```
agents/terraform.agent.md | 123 +++++++++++++++++++++++++++++++---------------
 1 file changed, 85 insertions(+), 42 deletions(-)
```

**Playbook angle**: Step 4 (specifications) — an agent without tool declarations cannot perform its stated purpose. Step 5 (defensive patterns) — check that every agent's frontmatter declares the tools it claims to use in its instructions.

---

## AC-09 | Missing Frontmatter Name Field Prevents Agent Discovery | configuration error | Medium

**Fix commit**: [`3167a45`](https://github.com/github/awesome-copilot/commit/3167a45)
**Pre-fix commit**: `3167a45~1`

**Files changed**:
- `agents/cast-imaging-impact-analysis.agent.md`
- `agents/cast-imaging-software-discovery.agent.md`
- `agents/cast-imaging-structural-quality-advisor.agent.md`

**Commit message**:
```
Frontmatter name field fix
```

**Defect summary**: Three CAST Imaging agents were missing the `name` field in their YAML frontmatter. The agent name was instead embedded in the `description` field (e.g., `description: 'CAST Imaging Impact Analysis Agent is a specialized agent for...'`). Without the `name` field, the agent runtime cannot discover or display the agent by name. The fix extracted the name into a proper `name` field and cleaned up the description to remove the redundant agent name prefix.

**Diff stat**:
```
 3 files changed, 6 insertions(+), 3 deletions(-)
```

**Playbook angle**: Step 4 (specifications) — frontmatter schema compliance. Required fields must be present for the agent to function within the runtime.

---

## AC-10 | Agent Scope Creep Causes Over-Validation and False Requirements | validation gap | Medium

**Fix commit**: [`a601d31`](https://github.com/github/awesome-copilot/commit/a601d31)
**Pre-fix commit**: `a601d31~1`

**Files changed**:
- `agents/repo-architect.agent.md`

**Commit message**:
```
fixed agent getting greedy to do more of what it was asked
```

**Defect summary**: The repo-architect agent's `/validate` command performed deep file inspection (checking frontmatter fields of every `.agent.md`, `.prompt.md`, `.instructions.md`, and `SKILL.md` file) when it should only validate directory structure. This caused the agent to flag false requirements (e.g., requiring `SKILL.md` files to have specific frontmatter when that wasn't part of the project setup). The `/scaffold` command also checked for `package.json` in contexts where it was irrelevant. The fix narrowed both commands to their intended scope: structure-only validation and relevant-framework-only detection.

**Diff stat**:
```
agents/repo-architect.agent.md | 18 ++++++++----------
 1 file changed, 8 insertions(+), 10 deletions(-)
```

**Playbook angle**: Step 5d (boundary conditions) — agent instructions should scope their operations to what's needed, not inspect everything available. Step 6 (domain knowledge) — "greedy" agents that over-inspect create false positives and user confusion.

---

## Summary

| ID | Title | Category | Severity | Files |
|----|-------|----------|----------|-------|
| AC-01 | Fabricated install commands | validation gap | High | 1 |
| AC-02 | Incorrect GraphQL return field | API contract violation | Medium | 3 |
| AC-03 | Wrong MCP tool names | API contract violation | High | 3 |
| AC-04 | Large presentation converter crash | missing boundary check | High | 4 |
| AC-05 | Handoff JSON schema undefined | API contract violation | Medium | 7 |
| AC-06 | Invalid file references in 8 agents | configuration error | High | 8 |
| AC-07 | Deprecated VS Code tool names | API contract violation | Medium | 1 |
| AC-08 | Missing MCP server declaration | configuration error | High | 3 |
| AC-09 | Missing frontmatter name field | configuration error | Medium | 3 |
| AC-10 | Agent scope creep in validation | validation gap | Medium | 1 |

**Category distribution**: API contract violation (4), configuration error (3), validation gap (2), missing boundary check (1)
**Severity distribution**: High (5), Medium (5)
