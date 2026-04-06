# sickn33/antigravity-awesome-skills Defects — Quality Playbook Benchmark (QPB)

**Repository**: [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)
**Language**: Python, JavaScript, Shell, Markdown (AI skill definitions with tooling scripts)
**Repo type**: Skill/Agent Registry
**Defect count**: 3 (AG-01 through AG-03; initial catalog)
**Generated**: 2026-03-31

Large skill registry (1,340+ skills, 29K stars) with CI/security automation. Fix commits are primarily in tooling scripts and skill content rather than in the skill framework itself.

---

## AG-01 | WhatsApp Skill Logs Sensitive API Config Data in Cleartext | security issue | High

**Fix commit**: [`e874770`](https://github.com/sickn33/antigravity-awesome-skills/commit/e874770)
**Pre-fix commit**: `e874770~1`

**Files changed**:
- `skills/whatsapp-cloud-api/scripts/validate_config.py` (3 copies: root, plugin, bundle)
- `tools/scripts/tests/test_whatsapp_config_logging_security.py` (new regression test)

**Commit message**:
```
fix(whatsapp): Stop logging sensitive config data

Sanitize WhatsApp Cloud API validator output across the root skill and
plugin copies so code scanning no longer flags clear-text exposure.

Add a regression test that verifies successful and failed validation
runs do not print sensitive response fields or API error details.
```

**Defect summary**: The WhatsApp Cloud API skill's `validate_config.py` script logged full API response payloads including phone numbers, verified names, and raw API error details on both success and failure paths. Code scanning flagged this as clear-text exposure of sensitive data. The fix replaced detailed response logging with static summary messages (`"Phone-number endpoint reachable"` / `"Graph API rejected the phone-number lookup"`) and added a regression test verifying no sensitive fields appear in output.

**Diff stat**:
```
 4 files changed, ~300 insertions(+), ~200 deletions(-)
```

**Playbook angle**: Step 6 (domain knowledge) — API responses containing PII/credentials must not be logged verbatim. Step 5 (defensive patterns) — sanitize all external API output before printing.

---

## AG-02 | Hugging Face Skill Uses Pipe-to-Shell Install Pattern | security issue | Medium

**Fix commit**: [`5a9bd5f`](https://github.com/sickn33/antigravity-awesome-skills/commit/5a9bd5f)
**Pre-fix commit**: `5a9bd5f~1`
**Issue**: Refs [#417](https://github.com/sickn33/antigravity-awesome-skills/issues/417)

**Files changed**:
- `skills/hugging-face-cli/SKILL.md` (3 copies: root, plugin, bundle)

**Commit message**:
```
fix(hugging-face-cli): Remove pipe-to-shell examples

Replace direct pipe-to-shell install snippets with download, review,
and local execution examples so the docs security suite passes.
```

**Defect summary**: The Hugging Face CLI skill instructed users to install via `curl ... | bash` (pipe-to-shell), a known insecure pattern that executes remote code without inspection. Two instances: the main `hf` CLI install and the `hf-mount` tool install. The fix replaced both with a download-review-execute pattern: `curl -o /tmp/install.sh && less /tmp/install.sh && bash /tmp/install.sh`.

**Diff stat**:
```
 3 files changed, 12 insertions(+), 6 deletions(-)
```

**Playbook angle**: Step 6 (domain knowledge) — pipe-to-shell is a recognized anti-pattern in security-conscious contexts. Step 4 (specifications) — skill instructions should follow the project's security guidelines.

---

## AG-03 | Spoofed Issue Comments Can Inject Optimized SKILL.md Content into PRs | security issue | Critical

**Fix commit**: [`bc49cee`](https://github.com/sickn33/antigravity-awesome-skills/commit/bc49cee)
**Pre-fix commit**: `bc49cee~1`

**Files changed**:
- `scripts/activate-skills.sh`
- `tools/scripts/apply_skill_optimization.cjs`
- `tools/scripts/tests/activate_skills_shell.test.js`
- `tools/scripts/tests/apply_skill_optimization_security.test.js`

**Commit message**:
```
fix(security): harden skill apply and activation flows

Restrict auto-apply to trusted review comments so spoofed issue comments
cannot write optimized SKILL.md content into pull request branches.

Reject activation symlinks that escape the source root and add
regression coverage for both security checks.
```

**Defect summary**: The skill optimization auto-apply workflow accepted review comments from any GitHub user (no `author_association` check). An attacker could post a comment formatted as a "Tessl Skill Review" on a PR, and the CI automation would write the attacker's content into the PR branch as an optimized SKILL.md. Additionally, the activation script did not validate symlinks, allowing directory traversal to escape the source root. The fix added `TRUSTED_AUTHOR_ASSOCIATIONS` (`OWNER`, `MEMBER`, `COLLABORATOR`) validation, configurable allowed bot logins, and symlink escape detection with regression tests for both paths.

**Diff stat**:
```
 5 files changed, 161 insertions(+), 12 deletions(-)
```

**Playbook angle**: Step 5 (defensive patterns) — CI automation accepting untrusted input. Step 6 (domain knowledge) — GitHub `author_association` is the standard trust signal for comment-driven automation. Step 5c (context propagation) — trust context from the comment author must propagate to the file-write decision.

---

## Summary

| ID | Title | Category | Severity | Files |
|----|-------|----------|----------|-------|
| AG-01 | WhatsApp skill logs sensitive data | security issue | High | 4 |
| AG-02 | Pipe-to-shell install pattern | security issue | Medium | 3 |
| AG-03 | Spoofed comments inject into PRs | security issue | Critical | 5 |

**Category distribution**: security issue (3)
**Severity distribution**: Critical (1), High (1), Medium (1)
