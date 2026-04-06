# Cursor Control Prompts for NSQ Benchmark

## Control 1: v1.2.0 Playbook (Cursor + GPT-5.4)

**Repo folder:** `/Users/andrewstellman/Documents/QPB/repos/nsq-1.2.0`

The v1.2.0 skill files are already installed in `.github/skills/` in that folder.

### Step 1: Generate the playbook

Open the nsq-1.2.0 folder in Cursor, then paste this prompt:

```
Read the skill file at .github/skills/SKILL.md and ALL reference files in .github/skills/references/. Follow the skill instructions exactly.

Generate a complete quality playbook for this project.

Important instructions:
- Skip Step 0 (no chat history)
- Skip Phase 4 (interactive improvement loop)
- Complete Phases 1-3 fully (Explore, Generate, Verify)
- Save all generated files to quality/ in this project
- Create AGENTS.md in the project root

After Phase 3 verification, output a brief summary: files created, test count, scenario count.
```

### Step 2: Run the code reviews

After the playbook is generated and you have a `quality/RUN_CODE_REVIEW.md`, run each defect review in the same Cursor chat. For each defect below, check out the pre-fix commit, run the review, then check out main again.

Paste this for each defect (replacing the variables):

```
git checkout {pre_fix_commit}

Read the code review protocol at quality/RUN_CODE_REVIEW.md and understand the guardrails and focus areas.

Review these specific files:
{file_list}

Follow the code review protocol guardrails exactly:
- Line numbers are mandatory for every finding
- Read function bodies, not just signatures
- If unsure, flag as QUESTION not BUG
- Grep before claiming something is missing
- Do NOT suggest style changes, refactors, or improvements

Report ALL bugs you find. For each finding: BUG/QUESTION, file, line number, severity (Critical/High/Medium/Low), description.

Save your findings to quality/code_reviews/{defect_id}_review.md

git checkout main
```

---

## Control 2: Naive Prompting — No Playbook (Cursor + GPT-5.4)

**Repo folder:** `/Users/andrewstellman/Documents/QPB/repos/nsq-control`

No skill files installed. No playbook generated. Just direct code review prompts.

### Instructions

Open the nsq-control folder in Cursor. For each defect, check out the pre-fix commit, run the review with the generic prompt below, then check out main.

```
git checkout {pre_fix_commit}

Review the following files for bugs. Be thorough — read every function body, check boundary conditions, trace error paths, look for race conditions and resource leaks. Report only real bugs, not style issues.

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Files to review:
{file_list}

Save findings to code_reviews/{defect_id}_review.md

git checkout main
```

---

## Defect List

Run each of these for both controls. Skip NSQ-42 (no changed files).

| ID | Pre-fix commit | Files |
|----|---------------|-------|
| NSQ-01 | 1362af17 | nsqd/channel.go |
| NSQ-02 | 9d6dad65 | nsqd/channel.go, nsqd/stats.go, nsqd/stats_test.go |
| NSQ-03 | cb2462cc | nsqd/channel.go |
| NSQ-04 | ac1627bb | nsqd/nsqd.go, nsqd/tcp.go |
| NSQ-05 | 7d1d1b04 | nsqlookupd/nsqlookupd.go |
| NSQ-06 | 2305c6fd | nsqd/lookup.go |
| NSQ-07 | b0df52be | nsqd/topic.go |
| NSQ-08 | 844c6a08 | nsqd/http.go, nsqd/stats.go, nsqd/statsd.go |
| NSQ-09 | bc0a6b91 | nsqd/stats.go |
| NSQ-10 | 2d6fae16 | internal/clusterinfo/data.go |
| NSQ-11 | dae9a123 | internal/quantile/aggregate.go |
| NSQ-12 | 6774510b | nsqd/channel.go, nsqd/topic.go |
| NSQ-13 | b15d0adb | nsqd/lookup_peer.go |
| NSQ-14 | 62c38589 | nsqd/protocol_v2.go, nsqd/protocol_v2_test.go |
| NSQ-15 | d4978523 | nsqd/channel.go |
| NSQ-16 | 059d4738 | nsqd/protocol_v2.go |
| NSQ-17 | 1608947e | nsqd/protocol_v2.go |
| NSQ-18 | 74f0dca5 | nsqd/channel.go, nsqd/protocol_v2.go |
| NSQ-19 | e8e1040d | nsqd/protocol_v2.go |
| NSQ-20 | 8c032e46 | examples/nsq_pubsub/nsq_pubsub.go, nsq/reader.go, nsq/reader_test.go, nsq/writer.go, nsqd/channel.go, nsqd/client_v2.go, nsqd/diskqueue.go, nsqd/nsqd.go, nsqd/topic.go |
| NSQ-21 | f85596ca | nsqlookupd/http.go, nsqlookupd/lookup_protocol_v1.go, nsqlookupd/registration_db.go, nsqlookupd/registration_db_test.go |
| NSQ-22 | 9faeb4a8 | internal/protocol/tcp_server.go, nsqlookupd/lookup_protocol_v1_test.go, nsqlookupd/nsqlookupd.go, nsqlookupd/tcp.go |
| NSQ-23 | fd1cde1d | apps/nsqd/nsqd.go, internal/http_api/http_server.go, internal/lg/lg.go, internal/protocol/tcp_server.go, nsqd/nsqd.go |
| NSQ-24 | 00b28f0b | apps/nsqlookupd/nsqlookupd.go, nsqlookupd/nsqlookupd.go |
| NSQ-25 | 71734e92 | nsqd/protocol_v2.go |
| NSQ-26 | 2530631d | nsqd/protocol_v2.go |
| NSQ-27 | b28153e | internal/writers/spread_writer.go |
| NSQ-28 | b2f1641 | nsqd/protocol_v2.go |
| NSQ-29 | a73c39f | apps/nsq_to_file/nsq_to_file.go |
| NSQ-30 | d9b0dc6 | nsqd/topic.go |
| NSQ-31 | 77fe56d | internal/dirlock/dirlock.go, nsqd/nsqd.go |
| NSQ-32 | 4de1606 | nsqadmin/static/js/lib/handlebars_helpers.js |
| NSQ-33 | 51b270f | nsqadmin/http.go |
| NSQ-34 | cb6fd8b | internal/clusterinfo/types.go |
| NSQ-35 | 9d6dad6 | apps/nsq_to_file/topic_discoverer.go |
| NSQ-36 | cb83885 | contrib/nsqd.cfg.example, nsqd/nsqd.go |
| NSQ-37 | c4e2add | internal/clusterinfo/producer_test.go, internal/clusterinfo/types.go |
| NSQ-38 | e4d2956 | internal/quantile/aggregate.go |
| NSQ-39 | 98fbcd1 | nsqd/nsqd.go |
| NSQ-40 | d9d5d94 | apps/nsq_stat/nsq_stat.go |
| NSQ-41 | 77a46db | nsqd/nsqd.go |
| NSQ-43 | 1eba46e | nsqadmin/static/js/views/channel.hbs |
| NSQ-44 | 1d183d9 | internal/auth/authorizations.go, nsqd/client_v2.go, nsqd/nsqd.go |
| NSQ-45 | b121909 | nsqd/topic.go |
| NSQ-46 | 5b67f58 | apps/nsqd/main_test.go |
| NSQ-47 | d3d0bbf | internal/protocol/protocol.go, nsqd/nsqd.go, nsqd/protocol_v2.go, nsqd/protocol_v2_test.go, nsqd/stats.go, nsqd/tcp.go, nsqlookupd/lookup_protocol_v1.go, nsqlookupd/lookup_protocol_v1_test.go, nsqlookupd/nsqlookupd.go, nsqlookupd/tcp.go |
| NSQ-48 | 5ea1012 | apps/nsq_to_file/file_logger.go |
| NSQ-49 | c432e69 | apps/nsq_to_file/file_logger.go |
| NSQ-50 | 29114b3 | apps/nsq_to_file/nsq_to_file.go |
| NSQ-51 | 4405e22 | nsqd/channel.go |
| NSQ-52 | f874049 | nsqd/channel.go |
| NSQ-53 | b2d1537 | nsqd/channel.go |
| NSQ-54 | c5375c5 | nsqd/in_flight_pqueue.go |
| NSQ-55 | 3ee16a5 | nsqd/protocol_v2.go |
| NSQ-56 | 6a237f3 | nsqd/http.go, nsqd/http_test.go |
| NSQ-57 | d2cd54e | nsqd/nsqd.go, nsqd/topic.go |
| NSQ-58 | 2549bc6 | nsqd/statsd.go |
