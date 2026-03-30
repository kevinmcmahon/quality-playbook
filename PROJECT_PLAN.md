# QPB Project Plan

This document captures the full roadmap for building, validating, and using the Quality Playbook Benchmark to measure and improve AI-assisted code review.

## Background

The QPB exists to answer a concrete question: *when an AI runs a code review playbook against a codebase with a known bug, does it find the bug?* If it doesn't, we want to know why — and we want to update the playbook until detection rates plateau.

This feeds into an O'Reilly Radar article series. Article 6 ("testing the test") uses the QPB to demonstrate iterative playbook refinement measured against ground truth.

## Current state

- 2,564 defects mined from 50 repos, 14 languages, 14 categories
- Master index: `dataset/DEFECT_LIBRARY.md` + `dataset/defects.jsonl`
- Sample per-repo description files: `curl` (5 of 49) and `cli` (20 of 71)
- Council of three review completed (Cursor/GPT-5.4 and Copilot/Gemini 2.5 Pro)
- Council feedback incorporated: schema normalized, tooling paths fixed, docs corrected, JSONL export added, issue text reuse policy established
- Iterative playbook improvement loop planned but not yet started

## Phase 1: Complete the dataset

### 1a. Generate all per-repo description files

For each of the 50 repos, generate `dataset/defects/<repo>/defects.md` using the curl format (commit message, files changed, diff stat, summarized issue description, playbook angle). This requires:

- Running the extraction against each repo's git history
- Fetching and summarizing issue/PR descriptions (following the reuse policy: summarize in our own words, link to original)
- Quality check: spot-check 3-5 entries per repo against actual diffs

Estimated effort: ~10 parallel agent runs, each handling 5 repos.

### 1b. Add reproducibility manifest

For each repo, record in the description file header:
- GitHub URL
- Clone date
- Full or shallow clone
- Commit range available

### 1c. Build reviewer calibration pack

Create `dataset/CALIBRATION.md` with 15-20 gold-standard scored examples spanning all 14 categories and all 3 score levels (direct hit, adjacent, miss). This serves as scorer training material and inter-rater reliability anchor.

## Phase 2: Iterative playbook improvement

The core loop: run the playbook against a sample, score the results, analyze the misses, update the playbook, re-run, repeat.

### Round 1: Baseline measurement

**Repos** (chosen by greedy set cover for maximum category/language/type diversity):
- cli/cli (GH) — Go, Application, 71 defects
- MassTransit (MT) — C#, Framework, 51 defects
- curl (CURL) — C, Library, 49 defects
- rails (RLS) — Ruby, Framework, 60 defects
- zookeeper (ZK) — Java, Infrastructure, 50 defects

**Total**: 281 defects across 5 languages, 4 repo types, all 14 categories covered.

**Process**:
1. For each defect, check out the pre-fix commit
2. Run the quality playbook scoped to the affected files
3. Score each defect: direct hit / adjacent / miss
4. Record results in `dataset/DETECTION_RESULTS.md`
5. Analyze miss patterns by category, severity, and playbook step

### Round 2+: Targeted improvement

Based on Round 1 miss patterns:
1. Identify which categories and playbook steps have the worst detection rates
2. Update the playbook to address systematic misses (e.g., if all concurrency bugs are missed, add concurrency-specific detection guidance)
3. Re-run against Round 1 repos to measure improvement
4. Pick 5 new repos filling uncovered languages/types (e.g., TypeScript, Python, Rust, Elixir, Kotlin)
5. Run against new repos to test generalization

**Repo selection for later rounds** (tentative):
- Round 2: pydantic (PYD/Python), trpc (TRPC/TypeScript), axum (AX/Rust), phoenix (PHX/Elixir), ktor (KT/Kotlin)
- Round 3: webpack (WP/JavaScript), laravel (LAR/PHP), serde (SER/Rust), akka (AKK/Scala), redis (RED/C)
- Rounds 4+: remaining repos as needed

**Stopping criterion**: When the detection rate improvement between rounds drops below 2 percentage points, we've hit diminishing returns.

### Records kept per round

For each round, record:
- Playbook version used
- Detection rate (direct, direct+adjacent) overall and by category
- List of all misses with analysis of why the playbook missed them
- Specific playbook changes made in response
- Before/after detection rate for targeted defects

## Phase 3: Cross-model comparison

A core research question: *do different models have different detection profiles?* A model might be strong on concurrency bugs but weak on serialization issues, or vice versa.

### 3a. Multi-model detection runs

Run the same playbook version against the same defect set using multiple models:

| Model | Tool | Notes |
|-------|------|-------|
| Claude Opus 4.6 | Cowork / Claude Code | Primary development model |
| Claude Sonnet 4.6 | Cowork / Claude Code | Faster, cheaper — how much detection do we lose? |
| GPT-5.4 | Cursor | Council reviewer, independent implementation |
| Gemini 2.5 Pro | Copilot | Council reviewer, independent implementation |

Each model runs the identical playbook against the identical pre-fix commits and files. The only variable is the model.

### 3b. Analysis dimensions

For each model pair, compute:

**Detection rate by category**: Does Model A find more concurrency bugs than Model B? Are there categories where one model dominates?

**Detection rate by severity**: Do models differ on Critical vs Low severity bugs? (Hypothesis: high-severity bugs with obvious symptoms are caught by all models; subtle medium-severity bugs show the most model variance.)

**Detection rate by language**: Is a model better at Go bugs than Python bugs? (Hypothesis: models trained on more of a language's ecosystem will catch more domain-specific bugs.)

**Detection rate by repo type**: Library bugs vs application bugs vs infrastructure bugs — do models have different strengths?

**Agreement matrix**: For each defect, how often do all models agree (all hit, all miss)? How often does exactly one model catch something the others miss? Unique catches are the most interesting signal.

**Category × model heatmap**: A 14-row × N-column matrix showing detection rate per category per model. This is the core deliverable for the article.

### 3c. Bias analysis

Specifically investigate:
- **Category bias**: Does each model have a "blind spot" category it systematically misses?
- **False positive profiles**: Does one model generate more false positives than another? Are false positives clustered in specific categories?
- **Sensitivity to playbook wording**: If we rephrase the same playbook step differently, does one model respond more than another?
- **Diminishing returns by model**: When we improve the playbook based on Model A's misses, does it also improve Model B's detection? Or are improvements model-specific?

### 3d. Ensemble analysis

Given N models, what detection rate would we achieve by taking the union of all detections? If the ensemble detects 95% but individual models max out at 75%, that's a strong argument for multi-model review workflows.

## Phase 4: Publication

### 4a. Dataset release

Publish the QPB dataset on GitHub with:
- All per-repo description files (2,564 defects)
- Machine-readable exports (JSONL, possibly CSV)
- Methodology and reproducibility documentation
- Calibration pack for scorer training
- All detection results and cross-model comparisons

### 4b. Article: "Testing the test"

O'Reilly Radar Article 6 covers:
- The QPB methodology (mutation testing applied one level up)
- Baseline detection rates and what the playbook catches vs misses
- The iterative improvement loop and how detection rates changed
- Cross-model comparison results and category bias findings
- Ensemble analysis: is multi-model review worth it?
- Lessons learned: which defect categories are hardest for AI to catch, and why

### 4c. Ongoing maintenance

The QPB is a living dataset:
- New repos can be added to fill gaps (e.g., more Rust, more infrastructure projects)
- New defects can be mined from existing repos as they accumulate fix commits
- Detection results accumulate over time as new models and playbook versions are tested
- The calibration pack grows with each scored example

## Appendix: Prefix-to-repo mapping

| Prefix | Repository | Language | Type |
|--------|-----------|----------|------|
| GH | cli/cli | Go | Application |
| CURL | curl/curl | C | Library |
| RLS | rails/rails | Ruby | Framework |
| ZK | apache/zookeeper | Java | Infrastructure |
| MT | MassTransit/MassTransit | C# | Framework |
| PYD | pydantic/pydantic | Python | Library |
| WP | webpack/webpack | JavaScript | Library |
| ESL | eslint/eslint | JavaScript | Library |
| NJ | JamesNK/Newtonsoft.Json | C# | Library |
| OK | square/okhttp | Java | Library |
| AX | tokio-rs/axum | Rust | Framework |
| SER | serde-rs/serde | Rust | Library |
| TRPC | trpc/trpc | TypeScript | Framework |
| ZOD | colinhacks/zod | TypeScript | Library |
| COB | spf13/cobra | Go | Library |
| CHI | go-chi/chi | Go | Library |
| RQ | rq/rq | Python | Library |
| RG | BurntSushi/ripgrep | Rust | Application |
| CFG | lightbend/config | Java | Library |
| HF | HangfireIO/Hangfire | C# | Framework |
| NSQ | nsqio/nsq | Go | Infrastructure |
| PRI | prisma/prisma | TypeScript | Library |
| CAL | calcom/cal.com | TypeScript | Application |
| JF | jellyfin/jellyfin | C# | Application |
| GB | gitbucket/gitbucket | Scala | Application |
| LN | apache/logging-log4net | C# | Library |
| KFK | apache/kafka | Java | Infrastructure |
| FIN | twitter/finatra | Scala | Framework |
| AKK | akka/akka | Scala | Framework |
| HX | encode/httpx | Python | Library |
| FA | tiangolo/fastapi | Python | Framework |
| RED | redis/redis | C | Infrastructure |
| JQ | jqlang/jq | C | Application |
| EXP | expressjs/express | JavaScript | Framework |
| LAR | laravel/framework | PHP | Framework |
| GUZ | guzzle/guzzle | PHP | Library |
| CMP | composer/composer | PHP | Application |
| DEV | heartcombo/devise | Ruby | Library |
| SK | sidekiq/sidekiq | Ruby | Library |
| KT | ktorio/ktor | Kotlin | Framework |
| EXD | JetBrains/Exposed | Kotlin | Library |
| KS | Kotlin/kotlinx.serialization | Kotlin | Library |
| NATS | nats-io/nats.rs | Rust | Library |
| QK | quarkusio/quarkus | Java | Framework |
| VAP | vapor/vapor | Swift | Framework |
| NIO | apple/swift-nio | Swift | Library |
| PHX | phoenixframework/phoenix | Elixir | Framework |
| ECT | elixir-ecto/ecto | Elixir | Library |
| OB | oban-bg/oban | Elixir | Library |
| EQ | raphaelmansuy/edgequake | TypeScript | Application |
| AS | alibaba/AgentScope | Java | Framework |

### Legacy prefixes (from initial mining rounds, retained for continuity)

| Prefix | Repository | Notes |
|--------|-----------|-------|
| G | google/gson | Original round, Java library |
| J | javalin/javalin | Original round, Java framework |
| P | spring-petclinic/spring-petclinic | Original round, Java application |
| O | andrewstellman/octobatch | Original round, Python application |
