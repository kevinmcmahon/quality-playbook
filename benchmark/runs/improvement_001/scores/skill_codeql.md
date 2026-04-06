# CodeQL Skill Assessment

**Date:** 2026-03-31
**Reviewer:** Claude Agent (Quality Playbook Review Protocol)
**Skill:** CodeQL Code Scanning
**Method:** Playbook Step 4–6 Review (adapted for Markdown skills)

---

## Executive Summary

The CodeQL skill is **well-structured, comprehensive, and production-ready** with strong documentation coverage. The skill clearly defines its purpose and provides detailed procedural guidance across GitHub Actions workflows and CLI execution. However, there are **systematic gaps in edge-case handling, defensive patterns, and state machine documentation** that could lead to inconsistent agent behavior under failure conditions.

**Key finding:** The skill excels at the "happy path" but needs explicit handling for 8–10 failure scenarios where agents might make unsafe assumptions or produce inconsistent results.

---

## Step 4 Assessment: Specifications (Clarity and Testability)

### Clarity of Stated Purpose

**Rating: 8/10**

**Positive findings:**
- SKILL.md frontmatter is explicit: "provides procedural guidance for configuring and running CodeQL code scanning"
- "When to Use This Skill" section is comprehensive (lines 12–21)
- Clear scope boundary: GitHub Actions workflows + CLI, not query authoring or architecture
- Language support table (lines 27–38) is unambiguous

**Gaps in specification:**
1. **Workflow creation vs. modification** — Skill doesn't state whether agents should create `.github/workflows/codeql.yml` or assume it exists. Line 49 says "commit the workflow file" but the prerequisite state is unclear.
2. **Default setup vs. advanced setup scope** — Skill guidance assumes user chooses one. What if both are active? (Troubleshooting p.3 mentions this, but initial guidance doesn't warn against it.)
3. **Token scope requirements** — Stated on line 253 (CLI) and line 89 (workflow) but inconsistently. SKILL.md says "security-events: write" (line 89) but CLI reference adds "contents: read" + "actions: read." Which combination is actually required for each scenario?
4. **Monorepo categorization** — Lines 149–174 show how to use `category`, but don't specify: when is it *required* vs. optional? What breaks if it's missing?

### Requirements Testability

**Rating: 7/10**

**Testable requirements:**
- "Can generate a valid SARIF v2.1.0 file" (documented in sarif-output.md)
- "CodeQL database creation succeeds with `--source-root` pointing to correct directory"
- "Language identifier matches one of the nine supported languages"
- "Workflow file passes GitHub Actions schema validation"

**Untestable or ambiguous:**
1. **"Appropriate build mode"** (Step 4) — Skill says use `none` for most interpreted languages, `autobuild` for others. But compiled-languages.md shows cases where `none` produces "less accurate" results (line 28). When does an agent know accuracy is "acceptable" vs. requiring `autobuild`?
2. **"Verify build command"** (compiled languages) — No acceptance test. What counts as a successful build?
3. **"Enable dependency caching"** — Skill recommends `dependency-caching: true` (line 132) but doesn't specify: when is caching harmful? (e.g., private feeds, transient dependency changes). No false-positive case defined.

### Contradictions

**Rating: 8/10** (One significant contradiction)

1. **Kotlin handling contradiction:**
   - SKILL.md (line 47): "Default setup uses `none` build mode for most languages"
   - compiled-languages.md (line 139): "If Kotlin code is added to a repo using `none` mode, disable and re-enable default setup to switch to `autobuild`"
   - Implication: Kotlin + `none` is initially valid, then breaks. Skill doesn't warn agents to check for Kotlin *before* choosing `none`.
   - **Impact:** Agent could configure default setup with `none`, which works for Java, then silently fail when Kotlin is added to the codebase.

2. **Path filtering scope contradiction:**
   - Workflow configuration (line 85): "`paths-ignore` controls whether the workflow runs"
   - But (line 85 continued): "When the workflow does run, it analyzes ALL changed files... unless files are excluded via the CodeQL configuration file's `paths-ignore`"
   - **Implication:** Two separate `paths-ignore` mechanisms with different scopes. Skill doesn't clarify: should users set both, one, or neither? Which takes precedence?

---

## Step 5 Assessment: Defensive Patterns (Edge Cases)

### Major Gap: Missing CodeQL Installation Check

**Rating: 3/10**

The CLI workflow section (lines 197–263) assumes CodeQL is installed and available. **No guidance on:**
- How to detect if CodeQL is missing
- Where to download it (only documented in cli-commands.md reference)
- What error messages indicate missing CodeQL
- Fallback behavior if installation fails

**Expected coverage:** Step 2 (Create CodeQL database) should include:
```
# Verify CodeQL is installed
codeql resolve languages || {
  echo "CodeQL not installed"
  # [fallback steps]
}
```

### Gaps: Language Support Validation

**Rating: 5/10**

No defensive checks for unsupported languages:
1. Skill lists 9 supported languages (table, line 27). If agent passes `--language=rust-lang` (typo), CodeQL fails without agent guidance on recovery.
2. Alternative identifiers (line 40) are documented as equivalent, but example doesn't show that `javascript` and `javascript-typescript` produce identical results.
3. No check for "GitHub Actions as a language" (line 38) — agents may not know this is unusual and requires special handling.

**Expected:**
- Table should include error message if language not recognized
- Procedural step should recommend `codeql resolve languages` before database creation

### Gaps: Build Command Failure Handling

**Rating: 4/10**

Compiled language workflows (lines 176–193) show manual build syntax but don't cover:
1. **Build failure scenarios:**
   - What if `make bootstrap` fails but `make release` succeeds? Should both run?
   - Should failures be fatal (`set -e`) or logged and continued?
   - No guidance on interpreting build errors.
2. **Dependency installation** — C# (line 103) mentions NuGet; Java (line 162) mentions Gradle/Maven. But skill doesn't explain: should agents install these, assume they're present, or skip analysis if missing?
3. **Long build times** — No timeout guidance for compiled languages. Skill mentions timeout-minutes (workflow-configuration.md, line 134) but doesn't recommend a value.

### Gaps: SARIF Upload Failures

**Rating: 6/10**

Troubleshooting (p.3) covers SARIF file size and schema validation, but missing:
1. **Token authentication failure** — Troubleshooting (line 255) says "Set GITHUB_TOKEN" but doesn't explain how to diagnose token scope issues at runtime.
2. **Repository permission checks** — No guidance on detecting "user doesn't have access to this repository" before attempting upload.
3. **Rate limiting** — No mention of GitHub API rate limits for SARIF uploads. What if multiple languages are uploaded sequentially?

### Gaps: Partial Analysis Failures

**Rating: 5/10**

Multi-language matrix workflows (lines 97–110) use `fail-fast: false`, meaning one language failure doesn't block others. But:
1. No guidance on partial results: if 3 of 4 languages succeed, should the workflow pass?
2. No alert on inconsistent results: if JavaScript succeeds with 50 alerts and Python fails, how should users interpret the "incomplete" security picture?
3. No mitigation: should users re-run failed languages, or accept gaps?

### Edge Case: Zero Results

**Rating: 4/10**

Skill assumes analysis returns non-empty results. Gaps:
1. No guidance on empty SARIF files (valid but unusual)
2. No warning if "fewer lines scanned than expected" (troubleshooting.md, line 61)
3. No check for "analysis produced 0 alerts" — is this expected or a sign of misconfiguration?

---

## Step 5a Assessment: State Machines and Phase Dependencies

### Workflow Execution State Machine

**Rating: 6/10**

GitHub Actions workflows have implicit phases, but skill doesn't model them explicitly:

**Documented phases:**
1. Checkout (line 124)
2. Initialize (line 126)
3. [Build — optional, only if manual] (line 189)
4. Analyze (line 135)

**Missing: State transition documentation**
- Can `init` be skipped? (No, but not stated)
- Can `analyze` run without `init`? (No — but skill doesn't prevent accidental reordering)
- What state persists between steps? (CodeQL database in `runner_temp` — not documented in SKILL.md)
- Example workflow (workflow-configuration.md, line 376+) shows correct order, but SKILL.md doesn't enforce it.

### Implicit Dependencies: Language-Build-Mode Coupling

**Rating: 5/10**

compiled-languages.md creates hidden dependencies:

| Language | Default Mode | What Happens if Wrong Mode Chosen |
|---|---|---|
| Kotlin | `autobuild` (required) | `none` mode silently skips Kotlin (line 139) |
| Swift | `autobuild` (required) | `none` mode not available; unclear error |
| Go | `autobuild` (default) | `none` mode not available; unclear error |
| Java | `none` (default) | `autobuild` available; agents might over-choose it |

**State machine gap:** Skill doesn't document a decision tree:
```
Language = Swift?
  -> build-mode MUST be autobuild, fail-fast if not
Language = Kotlin?
  -> build-mode MUST be autobuild (unless Java-only), warn if none
Language = Java-only?
  -> none mode recommended; autobuild OK if slower acceptable
Language = C/C++/C#/Rust?
  -> none is default; autobuild/manual if accuracy needed
```

### Implicit Dependency: Default Setup <-> Advanced Setup Exclusivity

**Rating: 4/10**

Lines 44–49 state: "To switch from default to advanced: disable default setup first, then commit the workflow file."

**State machine gap:** No documentation of what happens if both are active:
- Do they conflict? (Troubleshooting p.2 confirms: "Two CodeQL Workflows Running")
- Which takes precedence?
- How does an agent detect this state before it fails?
- What error message indicates this problem?

**Expected:** Defensive step: "Check repository Settings → Advanced Security to confirm only one setup is active"

---

## Step 5c Assessment: Parallel Path Symmetry

### Language Matrix Symmetry

**Rating: 7/10**

The skill handles multiple languages in a matrix (lines 97–110), but with uneven coverage:

**Well-documented:**
- JavaScript/TypeScript, Python, Ruby (interpreted languages) — consistent `none` build mode
- C/C++, C#, Rust (mixed) — options for `none`/`autobuild`/`manual`

**Inconsistent coverage:**
- Swift: only `autobuild` documented (line 179), no alternatives mentioned until compiled-languages.md
- Kotlin: only `autobuild` documented, hidden dependency on Java detection (line 139)
- Go: only `autobuild`, no `none` option (line 108) — not obvious from SKILL.md

**Matrix examples:**
- Multi-language example (workflow-configuration.md, line 156) shows C-cpp (`manual`) + C# (`autobuild`) + Java (`none`) — good symmetry
- But example doesn't explain *why* each language chose its build mode

### Build-Mode Symmetry Across Languages

**Rating: 6/10**

Skill recommends `none` for "most languages" (line 46), but compiled-languages.md shows:
- C/C++: `none` produces "less accurate" results if heavy custom macros (line 28)
- C#: `none` requires internet/private feeds (line 60)
- Java: `none` misses generated code from build (line 150)

**Inconsistency:** SKILL.md treats `none` as universally safe; compiled-languages.md shows it has *different failure modes per language*. Agents need explicit guidance on:
1. When is `none` accurate enough?
2. When does `none` need `autobuild` fallback?
3. How to detect accuracy issues?

### Query Suite Symmetry

**Rating: 8/10**

Well-documented:
- `security-extended` is consistently recommended (line 131)
- `security-and-quality` exists and is mentioned (line 142)
- Troubleshooting warns about file size (p.3, line 214) if using `security-and-quality`

Minor gaps:
- No guidance on which languages support which query suites
- Does Python have `security-and-quality`? (Implied yes, but not explicit)
- Custom packs (lines 288–296) show per-language configuration but not whether all languages accept the same pack format

---

## Step 5d Assessment: Generated and External Tool References

### CodeQL Bundle as External Dependency

**Rating: 5/10**

The skill references an external tool (CodeQL) in CLI workflows but documents it poorly:

**Documented:**
- Download location: cli-commands.md (line 10)
- Platform variants: cli-commands.md (line 19)
- Verification: cli-commands.md (line 38)

**Not documented in SKILL.md:**
- How to detect outdated CodeQL bundles
- When to upgrade CodeQL
- Compatibility: will 2019 CodeQL run 2025 queries? (No documented breaking changes warning)
- What if bundle is corrupted?

### SARIF Output Format Dependency

**Rating: 9/10**

sarif-output.md is comprehensive and well-referenced. Excellent coverage of:
- Top-level structure (lines 14–27)
- Rule object format (lines 50–88)
- Result object format (lines 71–108)
- Upload limits (lines 236–254)

Minor gaps:
- No example of valid vs. invalid SARIF (reference only)
- No tool for validating SARIF (mentioned in troubleshooting.md p.5, line 257, but not in SKILL.md)

### GitHub Actions Dependency

**Rating: 7/10**

Workflow file references `github/codeql-action/init@v4` + other actions. Documented:
- Actions use version pinning (line 383)
- Permissions required (line 89)
- Triggers (on: push, pull_request, schedule)

**Not documented:**
- What happens if `github/codeql-action` is unavailable or deprecated?
- Fallback to CLI for self-hosted runners (mentioned line 265 but not integrated into main guidance)
- Self-hosted runner setup time (no estimate given)

### Private Package Registry Dependency

**Rating: 5/10**

C# (line 61) and Java (line 162) mention private package registries. But:
- No guidance on diagnosing registry misconfiguration
- troubleshooting.md (line 206) mentions private registry diagnostics but Skill doesn't point users there
- No clear step: "verify registry is accessible before running analysis"

---

## Step 6 Assessment: Domain Knowledge (Real CodeQL Failure Modes)

### Known Failure Mode 1: Incomplete Database When Build Fails Partially

**Coverage: 6/10**

**Reality:** Compiled languages often have multi-stage builds. If stage 1 succeeds but stage 2 fails, CodeQL database may be incomplete.

**Skill coverage:**
- troubleshooting.md (line 61): "CodeQL Scanned Fewer Lines Than Expected"
- compiled-languages.md (line 64): Build command must compile full codebase

**Gap:** Skill doesn't explain *how* to detect this. Agents need:
- Metrics: "Compare lines in codebase vs. lines extracted" (mentioned in logs, line 334, but not actionable guidance)
- Recovery: "Re-run with `autobuild` to let CodeQL detect the full build"

### Known Failure Mode 2: False Positives from Unrecognized Sanitizers

**Coverage: 8/10**

Skill addresses:
- Alert management (line 282): "False positive... code uses a pattern CodeQL doesn't recognize as safe"
- alert-management.md (line 121): "Contributing improvements to CodeQL repository"

**Gap:** No list of common false positive patterns. Agents should know:
- Custom string escaping functions (not recognized as safe)
- Framework-specific validation decorators
- Macro-based sanitization

### Known Failure Mode 3: Kotlin + Java Mixed, But Only Java Gets Analyzed

**Coverage: 7/10**

Well-documented:
- compiled-languages.md (line 139): "If Kotlin code is added... disable and re-enable default setup"
- troubleshooting.md (line 73): "Kotlin Detected in No-Build Mode"

**Gap:** Skill doesn't explain *how* to detect Kotlin was missed:
- Check alert count per language?
- Look for Kotlin files in the codebase but zero alerts?
- Monitor extraction metrics?

### Known Failure Mode 4: Out of Memory on Large Codebases

**Coverage: 7/10**

Addressed:
- troubleshooting.md (line 151): "Out of disk or memory"
- Hardware requirements (line 368–375)
- hardwire limits per size (line 254)

**Gap:** No mitigation path for *during* analysis:
- Can you reduce `--threads` mid-run?
- Should analysis fail fast or recover gracefully?
- What exit code indicates OOM vs. logic error?

### Known Failure Mode 5: SARIF Upload Fails Due to File Size

**Coverage: 9/10**

Excellent coverage:
- troubleshooting.md (line 210): "SARIF File Too Large (10 MB limit)"
- sarif-output.md (line 239): Upload limits table
- Mitigation: split across jobs with `--sarif-category`

**Gap:** No automated detection/warning. Skill should recommend:
- Check SARIF file size before upload: `ls -lh results.sarif`
- Pre-upload validation: Microsoft SARIF validator (mentioned in troubleshooting.md, line 257)

### Known Failure Mode 6: Two Workflows Running (Default + Advanced)

**Coverage: 8/10**

troubleshooting.md (p.2, line 115): "Two CodeQL Workflows Running"
- Cause documented
- Solutions documented

**Gap:** No *prevention* guidance in SKILL.md. Agents should:
1. Check Settings → Advanced Security before configuring advanced setup
2. Document the choice (default vs. advanced) in PR comments

### Known Failure Mode 7: C# Compiler Flag Injection Conflicts

**Coverage: 8/10**

compiled-languages.md (line 95): Injected flags documented
- `/p:EmitCompilerGeneratedFiles=true` can break legacy projects (line 97)
troubleshooting.md (line 30): C# compiler failure with specific solution

**Gap:** No detection guidance. Agents should:
- Recognize `.sqlproj` files as potential problem
- Recommend switching to `build-mode: none` if errors persist

### Known Failure Mode 8: Dependency Caching Causes Stale Versions

**Coverage: 4/10**

Skill recommends `dependency-caching: true` (line 132) without warnings.

**Domain knowledge gap:** Cache misses happen when:
- Dependency registry updates (new version released)
- Private feed credentials expire
- Lock files are version-pinned and library removed from registry

**Expected:** Skill should warn:
- Enable caching for speed; disable if results are inconsistent between runs
- Recommendation: `dependency-caching: true` for stable projects; `false` for exploratory analysis

---

## Step 7 Assessment: Quality Checks on Skill Output

### Does the Skill Validate its Own Output?

**Rating: 5/10**

**What skill recommends agents verify:**
1. SARIF schema validation (troubleshooting.md, line 257): Microsoft SARIF validator
2. Workflow syntax: implicit (GitHub Actions will reject invalid YAML)
3. Database creation success: implied by CLI exit code

**What's missing:**
1. **No automated post-scan checklist.** Agents should verify:
   - Database created successfully: `ls -la codeql-db/`
   - Analysis completed: `codeql database analyze <db> ... --output=results.sarif` exit code
   - SARIF uploaded: `codeql github upload-results ... --sarif=results.sarif` exit code
   - Alerts appear in GitHub UI: manual check (not automated)

2. **No comparative metrics.** When result quality is questionable:
   - Compare lines scanned across languages
   - Check for unexpected zero-alert languages
   - Validate against previous runs

3. **No sanity checks for configuration.**
   - Recommended: "Verify build-mode matches language requirements" (documented but not enforced)
   - Missing: "Check that `paths-ignore` in config file doesn't exclude all source"

---

## Summary Findings by Playbook Step

| Step | Rating | Key Gap | Impact |
|---|---|---|---|
| **4 (Specifications)** | 7.5/10 | Ambiguous Kotlin requirements; token scope inconsistency | Agents may misconfigure Kotlin analysis or fail on authentication |
| **5 (Defensive Patterns)** | 5/10 | No CodeQL installation check; missing build failure handling; partial failure guidance | Agents will fail ungracefully when CodeQL missing or build breaks; no recovery path |
| **5a (State Machines)** | 5/10 | No explicit phase documentation; hidden language-mode dependencies; default/advanced mutual exclusivity not checked | Agents may reorder steps, choose wrong build modes, or activate conflicting setups |
| **5c (Parallel Paths)** | 7/10 | Uneven language coverage; `none` mode accuracy varies by language; query suite compatibility unclear | Agents may choose inconsistent build modes across languages; unsafe `none` mode assumptions |
| **5d (Generated/External)** | 6.5/10 | CodeQL bundle version/compatibility not documented; SARIF validator not recommended in main flow; private registry issues | Agents may use incompatible CodeQL versions; upload invalid SARIF; miss registry problems |
| **6 (Domain Knowledge)** | 7/10 | Incomplete database detection; false positive patterns not listed; OOM recovery guidance; cache staleness not warned | Agents won't recognize missed analyses; won't diagnose memory failures; may trust stale caches |
| **7 (Quality Checks)** | 5/10 | No post-scan validation checklist; no metrics sanity checks; no comparative analysis | Agents won't verify analysis completed correctly or detect silent failures |

---

## Signal Quality Assessment

### High-Confidence Guidance (9–10/10)

- SARIF v2.1.0 structure and upload limits (sarif-output.md)
- Language identifiers and alternatives (SKILL.md table)
- Workflow trigger configuration (workflow-configuration.md)
- Hardware requirements for self-hosted runners (compiled-languages.md)
- Alert severity levels and triage (alert-management.md)

### Medium-Confidence Guidance (6–7/10)

- Build mode recommendations per language (compiled-languages.md) — but accuracy implications unclear
- Troubleshooting error table (SKILL.md lines 350–364) — doesn't explain root causes
- Dependency caching recommendation (line 132) — no warning about staleness
- Monorepo category configuration (lines 149–174) — unclear when it's required

### Low-Confidence Guidance (4–5/10)

- Kotlin handling (line 47) — contradicts compiled-languages.md; no pre-check recommended
- Path filtering semantics (workflow-configuration.md, line 85) — two different `paths-ignore` mechanisms confusing
- C# compiler flag injection (compiled-languages.md, line 95) — solution is "disable EmitCompilerGeneratedFiles" but not proactively warned
- When to use `none` vs. `autobuild` (line 113) — "if accuracy is acceptable" is subjective

---

## Recommendations for Improvement

### Priority 1: Add Defensive State Checks

1. **Create "Pre-Flight Checklist" section** in SKILL.md:
   - Verify CodeQL CLI is installed: `codeql resolve languages`
   - Verify only one of default/advanced setup is active (check Settings)
   - Verify build dependencies installed (language-specific)
   - Verify `--source-root` directory exists

2. **Document Kotlin detection** (compiled-languages.md):
   - Add pre-configuration check: Search for `*.kt` files
   - If Kotlin found: recommend `autobuild` mode
   - Warn: "If you enabled default setup with `none` mode before adding Kotlin, re-enable setup to switch modes"

### Priority 2: Clarify State Machine

1. **Create explicit workflow phase documentation:**
   ```
   Phase 1: Checkout (required)
   Phase 2: Initialize CodeQL (required)
   Phase 3: Build [optional, only if build-mode=manual]
   Phase 4: Analyze (required)
   Dependencies: Phase 1 → 2 → (3?) → 4
   ```

2. **Document build-mode decision tree** for each language:
   - Java: default `none`; switch to `autobuild` if "fewer lines scanned than expected"
   - C/C++: default `none`; switch to `autobuild` if accuracy issues with macros
   - Kotlin: **must use `autobuild`; `none` not supported**

### Priority 3: Add Post-Scan Verification

Create "Verify Analysis Completed" section:
```bash
# Check database created
test -d codeql-db && echo "✓ Database exists" || echo "✗ Database missing"

# Check SARIF generated
ls -lh results.sarif && echo "✓ SARIF file exists" || echo "✗ SARIF missing"

# Check upload succeeded
# (Log should show: "Results uploaded to GitHub")

# Verify alerts appear in UI
# Navigate to Security tab and check alert count per language
```

### Priority 4: Expand Failure Recovery

1. **Partial language failures:** Add explicit guidance:
   - If some languages fail: don't block PR; re-run failed languages separately
   - If all languages fail: check hardware requirements and enable debug logging

2. **Build mode selection:** Create a table:
   ```
   | Build Mode | Accuracy | Speed | When to Use |
   | none | Medium | Fast | Default for interpreted; Java/C#/Rust if accuracy acceptable |
   | autobuild | High | Medium | Requires working build system |
   | manual | Highest | Slow | Complex builds; non-standard build systems |
   ```

### Priority 5: Document Real-World Failure Modes

Add section: "When CodeQL Silently Fails (But Looks Successful)":
1. **Kotlin missed:** All languages show alerts, but Kotlin shows 0. (Caused by `none` mode)
2. **Generated code missed:** Java `none` mode shows 80% of expected files. (Caused by missing build)
3. **False positives:** Alert appears in code, but it's a recognized safe pattern. (Caused by custom sanitizer)

---

## Overall Skill Rating

| Dimension | Score | Justification |
|---|---|---|
| **Completeness** | 8/10 | Covers happy path thoroughly; gaps in edge cases |
| **Clarity** | 8/10 | Language is precise; some ambiguities in requirements |
| **Defensiveness** | 5/10 | Few guards against misconfiguration or missing dependencies |
| **Debuggability** | 6/10 | Troubleshooting section exists; no diagnostic checklist |
| **Safety** | 6/10 | No silent failures documented; some contradictions possible |

**Overall Skill Score: 6.6/10** (Production-ready, but needs defensive patterns for edge cases)

### Recommended Usage

- **Use this skill for:** Standard CodeQL setup on GitHub-hosted runners, interpreted languages (Python, JavaScript, Ruby), simple Java analysis
- **Caution required for:** Multi-language monorepos with mixed build modes, Kotlin codebases, self-hosted runners with resource constraints, projects with custom build systems
- **Not recommended for:** Ad-hoc SARIF uploads from third-party tools; CodeQL query authoring; custom query pack development

---

## Conclusion

The CodeQL skill is **comprehensive and well-documented for the happy path**. It provides excellent reference material (sarif-output.md, compiled-languages.md, troubleshooting.md) and covers the major use cases clearly. However, it lacks **defensive patterns, explicit state machine documentation, and real-world failure recovery guidance** that would prevent agents from making unsafe assumptions or failing ungracefully.

**Key vulnerability:** The skill assumes CodeQL is installed, build systems work correctly, and configuration choices are correct. It provides no pre-flight checks or mid-flight error recovery.

**Recommendation:** Add 2–3 defensive sections (pre-flight checks, state machine diagram, failure recovery) and expand troubleshooting to include silent-failure scenarios. Once those are added, this skill can confidently handle complex multi-language CodeQL deployments.
