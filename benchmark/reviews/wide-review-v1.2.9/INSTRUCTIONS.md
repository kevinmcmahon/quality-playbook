# Wide Review v1.2.9 — Web UI Instructions

Run all 5 simultaneously. Each takes ~5-15 minutes.

## What to attach

Attach all 8 files from `runs/improvement_001/playbook_versions/v1.2.9/`:
1. `SKILL.md` — the main playbook (673 lines)
2. `references/constitution.md` — reference: quality constitution template (166 lines)
3. `references/defensive_patterns.md` — reference: grep patterns, defect categories, skeleton detection (582 lines)
4. `references/functional_tests.md` — reference: test generation guide (1,072 lines)
5. `references/review_protocols.md` — reference: code review, integration test templates, worked examples (618 lines)
6. `references/schema_mapping.md` — reference: schema-to-test mapping (220 lines)
7. `references/spec_audit.md` — reference: Council of Three audit protocol (152 lines)
8. `references/verification.md` — reference: self-check benchmarks (119 lines)

**Total:** 3,602 lines across 8 files.

## What to type as the message

Paste the contents of `REVIEW_PROMPT.md` as the chat message.

## Targets

### Claude.ai — Opus 4.6
1. Go to claude.ai, new conversation, select **Opus 4.6**, enable **extended thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response to `reviews/wide-review-v1.2.9/opus.md`

### Claude.ai — Sonnet 4.6
1. Go to claude.ai, new conversation, select **Sonnet 4.6**, enable **extended thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response to `reviews/wide-review-v1.2.9/sonnet.md`

### Claude.ai — Haiku 4.5
1. Go to claude.ai, new conversation, select **Haiku 4.5**, enable **extended thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response to `reviews/wide-review-v1.2.9/haiku.md`

### ChatGPT — with Thinking
1. Go to chatgpt.com, new conversation, enable **Thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response to `reviews/wide-review-v1.2.9/chatgpt.md`

### Gemini Pro — with Deep Thinking
1. Go to gemini.google.com, new conversation, enable **Deep Thinking**
2. Attach all 8 files, paste `REVIEW_PROMPT.md` as the message, send
3. Save response to `reviews/wide-review-v1.2.9/gemini-pro.md`

## After All 5 Complete

Bring responses back to the Cowork session for cross-model triage. Compare against v1.2.8 triage to assess diminishing returns and decide whether further iteration is warranted.
