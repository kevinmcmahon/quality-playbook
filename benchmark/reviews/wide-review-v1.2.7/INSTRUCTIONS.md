# Wide Review v1.2.7 — Web UI Instructions

Run all 5 simultaneously. Each takes ~5-15 minutes.

## What to attach

Attach all 8 files from `runs/improvement_001/playbook_versions/v1.2.7/`:
1. `SKILL.md` — the main playbook (658 lines)
2. `references/constitution.md` — reference: quality constitution template (160 lines)
3. `references/defensive_patterns.md` — reference: grep patterns, defect categories, skeleton detection (411 lines)
4. `references/functional_tests.md` — reference: test generation guide (642 lines)
5. `references/review_protocols.md` — reference: code review, integration test templates, worked examples (583 lines)
6. `references/schema_mapping.md` — reference: schema-to-test mapping (139 lines)
7. `references/spec_audit.md` — reference: Council of Three audit protocol (144 lines)
8. `references/verification.md` — reference: self-check benchmarks (114 lines)

**Total:** 2,851 lines across 8 files.

## What to type as the message

Paste the contents of `REVIEW_PROMPT.md` as the chat message.

## Targets

### Claude.ai — Opus 4.6
1. Go to claude.ai, new conversation, select **Opus 4.6**, enable **extended thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response

### Claude.ai — Sonnet 4.6
1. Go to claude.ai, new conversation, select **Sonnet 4.6**, enable **extended thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response

### Claude.ai — Haiku 4.6
1. Go to claude.ai, new conversation, select **Haiku 4.6**, enable **extended thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response

### ChatGPT — with Thinking
1. Go to chatgpt.com, new conversation, enable **Thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response

### Gemini Pro — with Deep Thinking
1. Go to gemini.google.com, new conversation, enable **Deep Thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response

## After All 5 Complete

Bring responses back to the Cowork session for cross-model triage. We'll compare against the v1.2.6 triage to see which findings were resolved and which are new.
