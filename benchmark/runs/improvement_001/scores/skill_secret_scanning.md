# Quality Playbook Review: Secret Scanning Skill
## Skill: `secret-scanning` (awesome-copilot)

**Review Date:** March 31, 2026
**Reviewed By:** Quality Playbook Protocol
**Target:** `/sessions/quirky-practical-cerf/mnt/QPB/repos/awesome-copilot/skills/secret-scanning/`

---

## Executive Summary

The secret-scanning skill provides procedural guidance for GitHub's secret scanning, push protection, custom patterns, and alert remediation. It is **well-structured and operationally sound** for its primary use cases (setup, push resolution, bypass workflows, custom patterns). However, when examined through the Quality Playbook lens—especially for AI agent execution—it reveals several **specification ambiguities, edge case gaps, and verification blind spots** that could lead to inconsistent outcomes or false confidences.

**Signal Quality:** Moderate. The skill correctly instructs on **what to do** in happy paths, but lacks:
- Explicit validation criteria (how to verify the action succeeded)
- False positive handling (agent cannot distinguish real secrets from false alarms)
- Boundary condition guidance (empty repos, monorepos, repos with thousands of alerts)
- Domain knowledge context (entropy, regex evasion, rotation procedures)

**Overall Rating by Step:**
- **Step 4 (Specifications):** 6/10 — Clear workflows, but missing acceptance criteria and failure paths
- **Step 5 (Defensive Patterns):** 5/10 — Limited edge case coverage; no guidance on operator error or system limits
- **Step 5a (State Machines):** 7/10 — Alert states documented, but bypass flow has potential deadlock conditions
- **Step 5c (Parallel Path Symmetry):** 6/10 — Different alert types (user/partner/push protection) not equally well-documented
- **Step 5d (Boundary Conditions):** 4/10 — Empty repos, monorepos, and high-volume scenarios barely addressed
- **Step 6 (Domain Knowledge):** 3/10 — No guidance on false positive mitigation or advanced patterns
- **Verification:** 2/10 — Skill does not include checks that findings are real secrets vs. false alarms

---

## Detailed Findings by Step

### Step 4: Specifications — Are Requirements Clear?

#### Finding 4.1: "Enable Secret Protection" (Step 1) lacks acceptance criteria
**Location:** SKILL.md, lines 45–50

The instruction says:
> Navigate to repository **Settings** → **Advanced Security**, then click **Enable** next to "Secret Protection"

**Issue:** No verification criteria. After clicking Enable, how does an agent know if it succeeded?
- Should the agent take a screenshot and check for a green checkmark?
- Should it wait for a confirmation modal?
- What is the expected UI state after success?
- What is the error condition? (e.g., "GitHub Organization requires SAML SSO" or "License expired")

**Impact:** An AI agent executing this workflow might click Enable, see no immediate feedback, and either repeat the action or assume failure without evidence.

**Evidence:** The reference files (push-protection.md, custom-patterns.md) provide workflow steps but no "verification" sections. For example, custom-patterns.md says "Save and dry run" (line 54) but does not specify: What does the dry-run results page look like? How many results indicate success vs. too many false positives?

#### Finding 4.2: "Validity checks" enable state is ambiguous
**Location:** SKILL.md, lines 98–102 & alerts-and-remediation.md, lines 67–92

The skill instructs:
> Enable "Validity checks" in Settings, then "GitHub periodically sends the secret to the issuer's API" and the "Status shown in alert: `active`, `inactive`, or `unknown`"

**Issue:** No specification of:
1. **Timing:** How long after enabling validity checks does a status appear? Hours? Days?
2. **Coverage:** Does every provider support validity checks, or only a subset? (Implied in the table but not explicit.)
3. **Failure modes:** If GitHub cannot reach the issuer's API (network failure, API downtime), is the result always `unknown`? Or is there retry logic?
4. **User action:** After validity checks return `inactive`, does the alert auto-close? Remain open? (Found in alerts-and-remediation.md but not in main skill.)

**Impact:** An agent enabling validity checks and immediately checking alert status will find `unknown` and incorrectly assume the feature failed or is not working.

#### Finding 4.3: Custom pattern dry-run sample size is vague
**Location:** references/custom-patterns.md, lines 64–101

The instruction says:
> "Review up to 1,000 sample results" and "Dry runs are essential — always test before publishing to avoid alert noise."

**Issue:** No specification of:
1. **Randomness:** Are the 1,000 results random samples, or the first 1,000 in the repo? (Affects representativeness.)
2. **Thresholds:** What false positive rate is acceptable? 1%? 5%? (Custom guidance: "Start specific — narrow regexes reduce false positives" is good advice but not a specification.)
3. **Coverage:** Does a 1,000-result sample guarantee it covers all major code patterns (test fixtures, docs, examples)?
4. **Abort criteria:** If dry-run returns more than N results, is that a signal to refine the regex? (Not specified.)

**Impact:** An agent might publish a pattern after reviewing only 20 matches from the sample (legitimate workflow) but assumes broader coverage than was actually tested.

#### Finding 4.4: Push protection bypass reason semantics are underspecified
**Location:** push-protection.md, lines 74–84 & SKILL.md, lines 137–145

The skill lists three bypass reasons:
- "It's used in tests"
- "It's a false positive"
- "I'll fix it later"

**Issue:** No specification of:
1. **Consequence difference:** The alert-and-remediation.md file clarifies the alert status resulting from each reason (line 25–29), but the main skill does not. An agent might not understand that "false positive" creates a **closed** alert (case handled), while "I'll fix it later" creates an **open** alert (requires follow-up).
2. **Intent:** "It's used in tests" is ambiguous. Does it mean: (a) the secret is a valid test credential used only in CI, (b) the secret is a fixture that should never run against production, or (c) the detected string is a regex false positive in test documentation?
3. **Recovery:** If a user selects the wrong reason and realizes the mistake, what is the recovery workflow? (Not documented.)

**Impact:** An agent might recommend "false positive" when "used in tests" is more accurate, leading to missed opportunities for remediation.

---

### Step 5: Defensive Patterns — Edge Case Handling

#### Finding 5.1: No handling for "secrets in non-code assets"
**Location:** All files; not addressed

The skill covers Git history, issues, comments, PRs, wikis, and gists. **Not covered:**
- Binary files mistaken for secrets (e.g., image metadata, compiled code containing strings)
- Encrypted files (e.g., `.gpg`, `.encrypted`) that contain valid-looking secrets in encrypted form
- Generated files (e.g., `.min.js`, compiled `.so` files) that may contain fragments of actual secrets from source
- Archived files (`.tar.gz`, `.zip`) containing historical secrets from older codebases

**Scenario:** An agent runs secret scanning on a monorepo with vendor libraries in `node_modules/`. Some packages include test API keys in their own `.npmrc` or `.git/config` snippets. The agent reports these as critical finds, but they are:
1. Not under the team's control
2. Revoked or fake credentials from vendor tests
3. Impossible to remediate without forking the library

**Evidence:** SKILL.md lines 29–34 list surfaces scanned (Git, issues, comments, etc.) but are silent on file type filtering, binary vs. text detection, or guidance on "should this alert be fixed?"

**Severity:** Medium. An agent might flag secrets it cannot and should not remediate, consuming time on false positives.

#### Finding 5.2: "Maximum 1,000 entries in paths-ignore" is a hidden system limit with no mitigation
**Location:** SKILL.md, lines 79–82

The skill states:
> Maximum 1,000 entries in `paths-ignore`; File must be under 1 MB

**Issue:** No guidance on:
1. **Overflow behavior:** When a repo exceeds 1,000 ignore entries, which paths are honored? (First 1,000? Last 1,000? Error?)
2. **Monitoring:** How does an operator know their `.github/secret_scanning.yml` was truncated or rejected?
3. **Alternative:** For repos with thousands of paths to exclude, what is the recommended strategy? (E.g., use glob patterns more aggressively, exclude whole directories instead of individual files.)

**Scenario:** A large monorepo with 150 sub-projects might need to exclude thousands of test/fixture paths. An agent creates an exhaustive `.github/secret_scanning.yml` file, hits the 1,000 entry limit, but the file is silently truncated. Secrets in the 1,001st excluded path still trigger alerts, the agent is confused about why exclusions are not working, and the operator finds the problem weeks later during incident response.

**Evidence:** The skill recommends "Be as specific as possible with exclusion paths" (line 86) but gives no guidance on scaling this approach to large repositories.

**Severity:** High. Silent truncation with no alert is a classic theater failure pattern.

#### Finding 5.3: No handling for "alert fatigue" or very high-volume secret findings
**Location:** All files; not addressed

The skill mentions "Generic alerts — maximum 5,000 alerts per repository" (alerts-and-remediation.md, line 57) but provides no guidance on:
1. **What happens when a repo exceeds 5,000 alerts:** Are new alerts dropped? Are old alerts auto-archived? (Not specified; GitHub behavior is not documented in the skill.)
2. **Agent response:** If an agent encounters a repository with 5,000+ open alerts, what is the recommended approach? (Triage all? Bulk dismiss? Filter by validity status?)
3. **Root causes:** Why might a repo have 5,000 alerts? (Likely: misconfigured custom pattern with high false positive rate, old codebase with massive credential leak history.) The skill does not guide on diagnosis.

**Scenario:** A large legacy repo has a custom pattern that matches common code patterns (e.g., database connection strings in documentation). After publishing, it generates 8,000 alerts in the first scan. The alert cap at 5,000 kicks in. The agent reports "5,000 alerts found" but is silent on the fact that 3,000 potential findings were dropped. The operator has no visibility into what was not shown.

**Evidence:** alerts-and-remediation.md, lines 54–59 mentions the limit but gives no mitigation guidance.

**Severity:** High. Silent truncation of security findings is a critical blind spot.

#### Finding 5.4: No handling for "false positive remediation" at scale
**Location:** All files; not addressed

The skill documents how to dismiss individual alerts (alerts-and-remediation.md, lines 207–212) but provides no guidance on:
1. **Bulk dismissal:** If a custom pattern produces 200 false positives, how does an operator dismiss all 200? (API endpoint exists but is not documented in the skill.)
2. **Pattern refinement loop:** After publishing a custom pattern and discovering 30% false positive rate, what is the edit-and-republish workflow? (custom-patterns.md mentions editing line 106 but not the impact on existing alerts.)
3. **Feedback to pattern creator:** If an agent discovers a published custom pattern is producing false positives, how does it communicate this to the pattern owner? (No workflow documented.)

**Scenario:** An agent publishes a custom pattern to detect internal API keys (pattern: `MYAPP_[A-Za-z0-9]{32}`). Dry-run on 5 test repos shows no false positives. After publishing org-wide, it generates 150 alerts in a documentation repo that contains regex examples (e.g., "This matches MYAPP_abcdef0123456789..."). Now the agent must dismiss 150 false positives one at a time (UI) or script a bulk dismissal (REST API, not documented in skill).

**Evidence:** The skill recommends "Always dry run before publishing" (custom-patterns.md, line 102) but does not account for false positives that emerge only at scale.

**Severity:** Medium-High. High false positive rate destroys operator trust in the system.

---

### Step 5a: State Machines — Can the Agent Get Stuck?

#### Finding 5a.1: Push protection bypass has a time-limit deadlock
**Location:** push-protection.md, lines 74–82 & SKILL.md, lines 137–145

The bypass workflow specifies:
> Visit the URL from the error message, select a reason, click **Allow me to push this secret**, then **re-push within 3 hours**

**Issue:** If the 3-hour window expires:
1. **State:** Is the bypass permission revoked? (Implied but not explicit.)
2. **Recovery:** Does the agent re-run the bypass workflow, or does the secret need to be removed? (Not specified.)
3. **Notification:** Is the developer notified when the bypass permission expires, or do they discover it on the next push attempt? (No guidance provided.)

**State machine:**
```
push blocked (secret detected)
    ↓
bypass URL visited & reason selected
    ↓
permission granted (valid for 3 hours)
    ↓
[3 hours elapse] → permission revoked (silent?)
    ↓
push attempted after 3 hours → blocked again
    ↓
[unclear: retry bypass or remove secret?]
```

**Scenario:** A developer is interrupted during a bypass workflow. They visit the bypass URL, select "I'll fix it later" at 14:00. Eight hours later, they try to push. The push is blocked again. Did the permission expire? Is there a UI message explaining this? The developer is confused and might waste 30 minutes troubleshooting, or might give up and remove the secret unnecessarily.

**Evidence:** The 3-hour window is mentioned (push-protection.md, line 82) but the expiration consequence is not detailed.

**Severity:** Medium. This is a recoverable state, but unclear enough to frustrate users and agents.

#### Finding 5a.2: Delegated bypass request flow lacks timeout semantics
**Location:** push-protection.md, lines 99–145

The delegated bypass workflow says:
> Bypass requests expire after **7 days** if not reviewed

**Issue:**
1. **Expiration behavior:** When a request expires, is it auto-closed? Does the contributor get a notification? Can they re-submit?
2. **Re-submission cost:** If a request expires after 7 days with no review, can the same contributor immediately re-submit, creating a loop of 7-day expired requests?
3. **Escalation:** Is there a path to escalate a stalled bypass request to a manager?

**State machine (delegated bypass):**
```
push blocked (secret detected)
    ↓
contributor visits URL and submits bypass request with explanation
    ↓
request pending (up to 7 days for review)
    ↓
[7 days elapse] → request auto-expired (no review)
    ↓
[unclear: can resubmit immediately? notification sent?]
```

**Scenario:** An on-call engineer at a startup pushes a database credential during an incident response at 03:00 UTC. Push is blocked. They submit a delegated bypass request: "Incident response, will rotate credential tomorrow." No one reviews the request during the next 7 days because the reviewer is on vacation. The request auto-expires on day 7 at 03:00 UTC. The engineer is unaware. Two weeks later, still no bypass. They have already rotated the credential, but cannot push the commit because bypass request expired. They have to re-submit, wait another 7 days, or remove the commit entirely.

**Evidence:** Expiration is mentioned (line 109) but the outcome is not detailed.

**Severity:** Medium. Distributed teams may miss notification of request expiration, creating frustration.

---

### Step 5c: Parallel Path Symmetry — Are All Secret Types Handled Equally?

#### Finding 5c.1: Partner alerts are documented in a way that hides them from operational visibility
**Location:** alerts-and-remediation.md, lines 31–38

Partner alerts are defined as:
> Generated when GitHub detects a leaked secret matching a partner's pattern. Sent directly to the service provider. **Not** displayed in the repository Security tab.

**Issue:** Parallel path asymmetry:
- **User alerts** (custom patterns, provider patterns) → visible in repo Security tab → operationally discoverable
- **Partner alerts** (provider-native, AWS, Stripe, etc.) → NOT visible in repo → operationally invisible to most developers

**Problem:** An agent might implement a "remediate all secrets" workflow that:
1. Lists all alerts in the repo Security tab
2. Rotates credentials
3. Dismisses alerts

This workflow will **miss partner alerts entirely** because they are not in the API or UI for the repository. The secret has been sent to the provider (good), but:
- The operator has no visibility into what was leaked
- The operator cannot confirm rotation happened (no alert to close)
- The operator cannot generate compliance reports of all leaked credentials

**Evidence:** The skill documents partner alerts in a single paragraph (lines 31–38) without emphasizing the visibility asymmetry or operational implications.

**Scenario:** A developer commits a Stripe API key. GitHub detects it, sends it to Stripe automatically (partner alert), and Stripe revokes the key. The developer, their manager, and the security team have NO VISIBILITY into this event because partner alerts do not appear in the repo. Six months later during a compliance audit, the question "how many Stripe keys have we leaked?" is unanswerable from GitHub's Security tab.

**Severity:** High. Silent notifications to providers create blind spots in compliance and incident response.

#### Finding 5c.2: Push protection alerts are a subset of user alerts, but the distinction is not clear
**Location:** alerts-and-remediation.md, lines 15–29 & SKILL.md, lines 189–193

Two types of alerts are documented:
- **User alerts:** "Secrets found in repository"
- **Push protection alerts:** "Secrets pushed via bypass" with `bypassed: true` filter

**Issue:** Unclear semantics:
1. Is a push protection alert **also** a user alert? (Answer: yes, but not stated explicitly.)
2. If a secret is pushed via bypass, does it **appear twice** in the Security tab — once as a user alert and once as a push protection alert? (Not clarified.)
3. When filtering by `bypassed: true`, are we seeing a **subset** of user alerts, or a different alert type? (The filter syntax suggests the former, but this is implicit.)

**Example:** A developer bypasses push protection and commits `STRIPE_KEY_12345`. The Security tab now shows:
- Alert #42: "Stripe API Key found" (user alert, type=provider)
- Alert #42 with filter `bypassed: true` (same alert marked as bypassed)

Or does it show two separate alerts? The skill does not clarify.

**Evidence:** The alert types are documented separately (lines 7–29) but the relationship is not explicitly stated.

**Severity:** Medium. Operators might double-count alerts or be confused about alert deduplication.

---

### Step 5d: Boundary Conditions — How to Handle Extremes

#### Finding 5d.1: Empty repositories or repos with no secrets
**Location:** All files; not addressed

What is the expected outcome for:
1. **Newly created, empty repo:** Secret scanning is enabled. No secrets found. Is this a success, or should there be a UI/API indication that the system is "working"?
2. **Large, clean repo with legitimately no secrets:** After a full scan, security team sees "0 alerts." Is this actionable feedback that the repo is secure, or is the absence of alerts just the baseline?

**Scenario:** An agent is asked to "verify that secret scanning is enabled and working." It enables the feature on an empty repo. No alerts are generated. Did the agent succeed in enabling secret scanning, or is the absence of alerts preventing confirmation that the feature is actually scanning?

**Evidence:** The skill does not discuss verification strategies for repositories with no secrets.

**Severity:** Low. Not a critical issue, but affects confidence in the system.

#### Finding 5d.2: Monorepos with thousands of custom patterns
**Location:** references/custom-patterns.md; not addressed

If an enterprise defines 500+ custom patterns, and a monorepo with 200+ sub-projects has each pattern enabled:
1. **Alert explosion:** Is the agent expected to manage 500 * 200 = 100,000 potential alert combinations?
2. **Dry-run cost:** Running dry-runs on all 500 patterns across all projects could take hours or days.
3. **Alert prioritization:** With thousands of alerts, how does an operator prioritize remediation?

**Scenario:** A fintech company with enterprise secret scanning and 300 custom patterns (one per client, per environment, per service type) enables all patterns in a large monorepo. The first scan generates 47,000 alerts. The agent is asked to "triage these." Without priority guidance, this is an intractable problem.

**Evidence:** The skill recommends "Be cautious with push protection" for custom patterns (custom-patterns.md, line 164) but does not address the explosion of alerts at scale.

**Severity:** Medium. Not every user will hit this, but those who do will have a very bad experience.

#### Finding 5d.3: Repositories with only binary files
**Location:** All files; not addressed

How does secret scanning handle repositories that contain:
- Compiled binaries (`.so`, `.dll`, `.exe`)
- Archives (`.zip`, `.tar.gz`, `.rar`)
- Containers/images (`.tar` from `docker save`)
- Fonts, images, media (`.ttf`, `.png`, `.mp4`)

**Issue:**
1. Does secret scanning scan inside binary files? (Likely not, but this is not documented.)
2. If a `.zip` file is committed that contains historical `.env` files, is the secret inside the `.zip` detected? (Likely not, unless GitHub unzips and scans.)
3. If scanning skips binary files, should the operator be notified that certain files were not scanned?

**Scenario:** A data science team commits a `.tar.gz` containing a dataset and a historical `.env` file from a previous project. The operator expects secret scanning to find the embedded `.env`, but it is likely skipped because it is inside an archive.

**Evidence:** The skill does not discuss file type filtering or binary file handling.

**Severity:** Low-Medium. Applicable to specific use cases (embedded secrets in archives), but not well-covered.

---

### Step 6: Domain Knowledge — Advanced Patterns and Failure Modes

#### Finding 6.1: No guidance on false positive rates or how to measure them
**Location:** references/custom-patterns.md, line 102 ("Always dry run before publishing to avoid alert noise")

The skill emphasizes testing custom patterns to reduce false positives, but provides **no** guidance on:
1. **What is a good false positive rate?** 5%? 1%? 0.1%?
2. **How to measure it:** If dry-run returns 1,000 results, how many should the agent manually review to estimate the false positive rate? (Recommendation: statistical sampling, but this is not provided.)
3. **Trade-offs:** A more specific regex reduces false positives but might miss real secrets. How should this trade-off be navigated?
4. **Domain-specific patterns:** Database connection strings (Server=...; Password=...) are very specific and have low false positive rates. API keys (MYAPP_...) are more likely to match non-secret strings. This context is not provided.

**Example:** An agent creates a custom pattern for Slack tokens: `xoxb-[0-9]{12,13}-[0-9]{12,13}-[A-Za-z0-9]{24}`. Dry-run returns 150 results across 10 test repos. How many should the agent review to be confident? If it reviews 10 and finds 0 false positives, can it publish with confidence? (Answer: no, but the skill does not guide this.)

**Evidence:** The only quantitative guidance is "dry-run up to 1,000 results" and "optional maximum 5,000 alerts per repo."

**Severity:** Medium. Agents will publish patterns with unvalidated false positive rates, leading to alert noise.

#### Finding 6.2: No guidance on secret rotation procedures
**Location:** alerts-and-remediation.md, lines 119–134

The remediation workflow says:
> **Always rotate (revoke and reissue) the exposed credential first.** This is more important than removing the secret from Git history.

**Issue:** No guidance on:
1. **How to rotate:** Different providers have different rotation procedures (AWS → generate new key/secret, GitHub PAT → revoke and create new, Stripe → delete old key and create new). The skill does not enumerate these.
2. **Verification:** How does the operator confirm that the new credential works in all places the old one was used?
3. **Timing:** Should rotation happen immediately (risky if systems are not ready for the new credential) or during a maintenance window?
4. **Rollback:** If rotation breaks a system, what is the recovery procedure?

**Scenario:** An agent finds a leaked AWS secret key. It knows to rotate, but does not know:
- Whether to deactivate the old key immediately (breaks all systems using it) or after a delay (risks ongoing unauthorized use)
- How to verify all applications have the new key before deactivating the old one
- What to do if one application fails with the new key (network issue? key format mismatch?)

**Evidence:** The skill recommends rotation but does not provide provider-specific guidance or verification steps.

**Severity:** Medium. Operators and agents might skip or botch rotation, leaving systems vulnerable.

#### Finding 6.3: No discussion of regex evasion or advanced secret patterns
**Location:** references/custom-patterns.md; not addressed

Common evasion techniques that custom patterns might miss:
1. **Obfuscation:** Secrets split across multiple lines or files
   ```
   MYAPP_KEY_1 = "abcd"
   MYAPP_KEY_2 = "ef01"  # concatenate with above: abcdef01
   ```
2. **Transformation:** Secrets encoded or hashed
   ```
   MYAPP_TOKEN = base64("real_token_here")
   ```
3. **Fragmentation:** Secret built programmatically
   ```
   secret = config["db"]["password"]  # value not visible to static scan
   ```
4. **Legacy formats:** Old or deprecated secret formats that are harder to detect
   ```
   old_aws_key = AKIA2ABC...  # different format from current AKIAIOSFODNN...
   ```

**Issue:** The skill does not discuss these patterns or acknowledge their existence. An agent might believe its custom pattern is comprehensive when it only catches the easy case.

**Evidence:** custom-patterns.md provides sample regex (lines 31–42) but all are straightforward patterns with no evasion discussion.

**Severity:** Medium. Operators might have false confidence that scanning covers all secrets.

#### Finding 6.4: No guidance on environment-specific secrets
**Location:** All files; not addressed

Different environments have different secrets:
1. **Development** — fake/test credentials, often low-value
2. **Staging** — real but non-prod credentials, moderate value
3. **Production** — critical, high-value credentials

**Issue:** The skill does not distinguish:
1. Whether alerts from `dev/` and `staging/` directories should be handled differently than from `src/` or `src/main/`
2. Whether the exclusion mechanism (paths-ignore) should be used to auto-close dev credentials (debatable practice)
3. Whether custom patterns should be environment-aware (e.g., "only alert on production API keys")

**Scenario:** A codebase includes `test/fixtures/.env` with fake Stripe keys for integration tests. Custom secret scanning pattern detects them. Alert is created. Operator dismisses as "false positive" or "used in tests" every time the codebase is rescanned. This becomes repetitive and error-prone.

**Evidence:** The skill does not discuss environment-specific handling. The exclusion mechanism (paths-ignore) is mentioned, but the decision of whether to use it for test credentials is left to the operator.

**Severity:** Medium-Low. Operationally annoying, but not a critical gap.

---

### Step 7: Verification — Can Agents Validate Findings?

#### Finding 7.1: No verification that a detected secret is a real secret (not a false positive)
**Location:** All files; critical gap

The skill instructs on **finding** and **dismissing** secrets, but provides **no mechanism** for verifying that a detected secret is actually exploitable.

**Current workflow:**
1. Secret scanning detects a string matching a pattern
2. Agent (or operator) sees the alert
3. Agent rotates the credential and closes the alert
4. No verification that the string was actually a valid secret

**Missing capability:**
- The skill mentions "validity checks" (alerts-and-remediation.md, lines 67–92) which can verify if a secret is still active
- But validity checks require the credential to be valid (to test against the provider's API)
- This is **reactive** (found after leak), not **preventative** (verified before leaking)
- Also, validity checks are optional and may not be enabled

**Issue:** An agent cannot reliably distinguish:
- Real secret: `STRIPE_KEY_sk_live_abcd1234...` (actual, exploitable)
- False positive: `STRIPE_KEY_sk_live_deadbeef...` (regex match, but invalid format)
- Example: `STRIPE_KEY_sk_live_example_key_for_docs` (from documentation)

**Scenario:** Custom pattern detects `STRIPE_KEY_sk_live_[a-z0-9]{32}`. It matches a string in `docs/integration.md`: `STRIPE_KEY_sk_live_example_key_for_docs`. This is clearly an example, not a secret. But the agent has no way to verify this short of:
1. Manually reviewing the context
2. Trying to use the credential against Stripe (risky, could trigger fraud detection)
3. Dismissing as "false positive" based on context

**Evidence:** The skill provides no automated verification step. The only mention of verification is validity checks, which are provider-dependent and not universally available.

**Severity:** Critical. This is a fundamental blind spot. Agents (and operators) might confidently dismiss false positives as real secrets, or vice versa.

#### Finding 7.2: No guidance on how to validate that a bypass reason is accurate
**Location:** push-protection.md, lines 74–84

When a developer selects "It's a false positive," the system creates a closed alert. But there is no verification:
1. **Is it actually a false positive?** Or did the developer misunderstand the rule?
2. **Is the bypass reason recorded?** Can an auditor later verify why the secret was allowed?
3. **Is there a review workflow?** Does a security manager approve bypass reasons, or are they self-service?

**Issue:** An agent recommending "dismiss as false positive" has no way to verify the recommendation is correct. The agent might recommend dismissal based on:
- File path heuristics ("it's in `test/`" so it's probably a test secret)
- Pattern context ("the string is followed by `# example`" so it's probably documentation)
- But these are heuristics, not verification

**Scenario:** A developer pushes a secret and selects bypass reason "It's a false positive" to bypass push protection. The agent, not knowing the context, trusts the developer and closes the alert. But the developer was lazy and just wanted to push quickly without rotating. The secret remains active and exploitable. Months later, an attacker uses it.

**Evidence:** The skill documents bypass reasons (lines 137–145) but does not require or suggest verification before accepting the reason.

**Severity:** High. Unverified bypass reasons create a false sense of security.

---

## Summary of Findings

### Strengths
1. **Clear operational workflows** for common use cases (enable scanning, resolve blocked pushes, manage custom patterns)
2. **Good reference organization** with separate files for push protection, custom patterns, and alert remediation
3. **Specific UI navigation** with Step 1, Step 2, etc. makes it followable
4. **Attempt at completeness** covering provider patterns, custom patterns, user/partner/push protection alerts

### Critical Gaps
1. **No acceptance criteria** for configuration steps (how to verify actions succeeded)
2. **No false positive validation** (agent cannot distinguish real secrets from regex matches)
3. **Silent system limits** with no mitigation (1,000 paths-ignore entries, 5,000 alert cap)
4. **Incomplete state machines** (bypass timeout behavior, delegated request expiration)
5. **Missing domain knowledge** (false positive rates, rotation procedures, evasion patterns)
6. **Asymmetric alert visibility** (partner alerts not shown in repo UI)

### Operational Risks
1. **Theater risk:** Silent truncation of paths-ignore entries or alert caps could create false confidence in protection coverage
2. **False confidence risk:** Agents might believe they have comprehensively scanned for secrets when they have only found the easy patterns
3. **Incident response risk:** Operators have no visibility into partner alerts and cannot generate complete inventory of leaked credentials
4. **Scalability risk:** Monorepos with thousands of custom patterns will face alert explosion with no prioritization guidance

---

## Ratings by Step

| Step | Rating | Rationale |
|------|--------|-----------|
| **Step 4: Specifications** | 6/10 | Clear workflows, but missing acceptance criteria, timing specifications, and failure modes. Operators cannot reliably verify that actions succeeded. |
| **Step 5: Defensive Patterns** | 5/10 | Limited edge case coverage. No guidance for repos with thousands of paths, high-volume alerts, binary files, or operator error recovery. |
| **Step 5a: State Machines** | 7/10 | Alert states and bypass workflows are documented, but timeout behavior is vague. Deadlock conditions exist (3-hour bypass window expiration, 7-day delegated request expiration). |
| **Step 5c: Parallel Path Symmetry** | 6/10 | User alerts and partner alerts are handled asymmetrically (different visibility). Push protection alerts are related to user alerts but the relationship is implicit, not explicit. |
| **Step 5d: Boundary Conditions** | 4/10 | Poor coverage. Empty repos, monorepos, repos with only binaries, and high-volume scenarios barely addressed. No mitigation for system limits. |
| **Step 6: Domain Knowledge** | 3/10 | Minimal guidance on false positive rates, rotation procedures, regex evasion, or environment-specific secrets. Operators lack context to make informed decisions about custom patterns. |
| **Verification** | 2/10 | **Critical gap.** Agents cannot verify that detected secrets are real (not regex false positives) or that bypass reasons are accurate. No automated validation mechanism provided. |

---

## Recommendations for Improvement

### Priority 1 (Critical)
1. **Add verification section** to each operational workflow (enable scanning, publish custom pattern, dismiss alert). Include: expected UI state, error conditions, confirmation mechanism.
2. **Document false positive mitigation** with concrete guidance on statistical sampling, acceptable rates, and pattern refinement loops.
3. **Add validity checks context** explaining timing, coverage, and relationship to remediation workflow.
4. **Document system limits** (1,000 paths-ignore entries, 5,000 alert cap) with explicit overflow behavior and mitigation strategies.

### Priority 2 (High)
1. **Clarify state machine edges:** 3-hour bypass window expiration, 7-day delegated request timeout, alert deduplication (user vs. push protection alerts).
2. **Add domain knowledge** on rotation procedures per provider, common evasion patterns, and environment-specific secret handling.
3. **Improve partner alert visibility:** Explain implications of secrets being sent to providers with no visibility to the repo, and provide audit/compliance guidance.
4. **Address monorepo scenarios:** Provide guidance on custom pattern prioritization when dozens or hundreds of patterns are in use.

### Priority 3 (Medium)
1. Expand discussion of binary file and archive handling.
2. Add verification guidance for bypass reasons (what makes a bypass reason accurate?).
3. Clarify relationship between user alerts and push protection alerts (are they the same alert or different types?).

---

## Conclusion

The secret-scanning skill is **operationally functional** for its primary use cases (setup, push resolution, custom patterns). However, when evaluated as an **AI agent instruction document** through the Quality Playbook lens, it reveals **specification gaps, false positive blind spots, and silent system limits** that could lead to inconsistent outcomes or undetected security issues.

**For immediate use:** Suitable for human operators following procedural steps.

**For AI agents:** Requires augmentation with:
- Explicit acceptance criteria for each step
- Validation mechanisms to detect false positives
- Mitigation strategies for system limits
- Domain knowledge on rotation and evasion patterns

**Overall fitness-to-purpose:** Moderate. Works for happy paths; fails to guide on edge cases, verification, and advanced scenarios.

---

**End of Review**
