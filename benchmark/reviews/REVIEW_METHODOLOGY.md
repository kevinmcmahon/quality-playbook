# QPB Wide Review Methodology & Findings Archive

**Purpose:** This document records the multi-model review methodology and aggregate findings so they can be compared against actual model performance when running the playbook against repos.

**Date range:** 2026-03-31
**Playbook versions reviewed:** v1.2.6, v1.2.7, v1.2.8, v1.2.9
**Final version after fixes:** v1.2.10

---

## Methodology

### Review Setup

Five AI models independently audit the playbook using a structured "Council of Three" prompt. Each model receives all 8 playbook files as attachments plus a review prompt targeting the specific version's changes.

**Models used:**
1. Claude Opus 4.6 (Extended Thinking) — claude.ai
2. Claude Sonnet 4.6 (Extended Thinking) — claude.ai
3. Claude Haiku 4.5 (Extended Thinking) — claude.ai
4. ChatGPT (with Thinking) — chatgpt.com
5. Gemini Pro (with Deep Thinking) — gemini.google.com

### Review Prompt Structure

Each review prompt includes:
- Context about the playbook and its improvement history
- The QPB benchmark dataset reference (2,592 defects, 55 repos, 15 languages)
- Task: "Act as the Tester" — audit against stated goals
- Rules: only list defects, cite file/line, search before claiming, classify each finding
- Defect classifications: MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM
- 8 scrutiny areas targeted at the specific version's changes
- Output format: structured findings + summary with top 3

### Triage Process

After all 5 reviews come in, a cross-model triage groups findings into unique themes and assigns tiers:
- **Tier 1:** 5/5 models agree (universal consensus)
- **Tier 2:** 3-4/5 models agree (strong consensus)
- **Tier 3:** 2/5 models agree (partial agreement)
- **Tier 4:** 1/5 models flag (single-model, needs verification)

Tier 1 and 2 items are fixed. Tier 3 items are verified and fixed if valid. Tier 4 items are monitored.

---

## Aggregate Trajectory

| Metric | v1.2.6 | v1.2.7 | v1.2.8 | v1.2.9 |
|--------|--------|--------|--------|--------|
| Total findings (raw) | ~90+ | 72 | 35 | 35 |
| Unique themes | ~46 | ~30 | ~23 | 20 |
| Tier 1 (5/5) | ? | 1 | 1 | **0** |
| Tier 2 (3-4/5) | ? | 7 | 5 | 6 |
| Tier 3 (2/5) | ? | 7 | 10 | 3 |
| Tier 4 (1/5) | ? | 13 | 7 | 11 |
| Lines (8 files) | 2,202 | 2,746 | 3,487 | 3,602 |

### Key Transitions

**v1.2.6 → v1.2.7:** Structural fixes. Phase gates, constitution critical rule, plan-first workflow. Finding count −20%.

**v1.2.7 → v1.2.8:** Language expansion. Added C#, Ruby, Kotlin, PHP grep patterns to defensive_patterns.md. 10-language claim introduced. Finding count −51%.

**v1.2.8 → v1.2.9:** Content propagation. Expanded downstream files (functional_tests.md, schema_mapping.md, verification.md, review_protocols.md) to match 10-language claim. Fixed 4 PHANTOM code bugs (C# public, Ruby comments, PHP async, Go unused var). Finding count stable.

**v1.2.9 → v1.2.10:** Code quality polish. Fixed remaining C# examples, Java CompletableFuture typo, PHP dead variable, Field Reference Table format alignment, duplicate plan-first section removal. No new review round — fixes based on triage + comprehensive code audit.

---

## Model Performance Profiles

### Radar Chart Scores (0–10, aggregated from v1.2.7–v1.2.9)

| Dimension | Opus 4.6 | Sonnet 4.6 | Haiku 4.5 | ChatGPT | Gemini Pro |
|-----------|----------|------------|-----------|---------|------------|
| Code Correctness | 8 | 7 | 6 | 8 | 7 |
| Structural Consistency | 9 | 8 | 6 | 7 | 7 |
| Coverage Completeness | 8 | 8 | 8 | 6 | 8 |
| Documentation Quality | 8 | 7 | 5 | 5 | 6 |
| Workflow/UX | 8 | 8 | 7 | 6 | 6 |
| Accuracy Depth | 9 | 8 | 6 | 7 | 7 |

### Classification Distribution (total across 3 rounds)

| Classification | Opus | Sonnet | Haiku | ChatGPT | Gemini |
|----------------|------|--------|-------|---------|--------|
| MISSING | 5 | 6 | 10 | 2 | 8 |
| DIVERGENT | 9 | 7 | 5 | 5 | 8 |
| UNDOCUMENTED | 7 | 2 | 10 | 0 | 2 |
| PHANTOM | 9 | 8 | 0 | 7 | 2 |

### Model Characterizations

**Opus 4.6 — "Architectural Auditor"**
Deepest cross-file analysis. Traces implications from SKILL.md through reference files to templates. Highest citation precision (always includes line numbers and exact quotes). Catches structural contradictions other models miss. Occasionally misses agent-facing UX gaps.

**Sonnet 4.6 — "Balanced Pragmatist"**
Most balanced profile across all dimensions. Strong at code correctness — caught the Java CompletableFuture<r> typo that only it found. High agreement with Opus — they're the strongest pair. Fewest false positives of any model.

**Haiku 4.5 — "Breadth Scanner"**
Highest finding volume (9 per review average). Best at coverage completeness — spots missing language support faster than others. Dominates UNDOCUMENTED findings. Trade-off: higher false positive rate, lower citation precision, zero PHANTOM detections.

**ChatGPT — "Surgical Specialist"**
Lowest finding count but highest signal-to-noise ratio. Excels at catching code patterns that violate the playbook's own stated rules (e.g., boundary tests using exception-only assertions contradicting anti-pattern guidance). Blind to coverage gaps and documentation quality.

**Gemini Pro — "Thorough Generalist"**
Strong on coverage and format consistency. First to find the Field Reference Table column mismatch. Good at catching when examples don't match mandated templates. Sometimes over-counts by treating sub-items as separate findings.

### Cross-Model Agreement Patterns

**Strongest pairs:**
- Opus + Sonnet: Highest agreement (8+ shared findings). Both catch code quality + structural issues.
- Haiku + Gemini: Both catch coverage gaps. Together they surface MISSING findings comprehensively.

**Complementary pairs:**
- Opus + ChatGPT: Opus catches structural gaps, ChatGPT catches self-contradictions in code examples.
- Sonnet + Gemini: Sonnet validates with precision, Gemini provides breadth.

**Recommended council configurations:**
1. **Opus + Sonnet + ChatGPT** — High precision, low noise. Best for mature playbooks.
2. **Opus + Haiku + Gemini** — Breadth-first discovery. Best for early iterations.
3. **All 5 models** — Maximum coverage. Best for first release or major refactors.

---

## Prediction: What Models Will Find When Running the Playbook

Based on review performance, here's what to expect when each model actually *runs* the playbook against real repos:

**Opus** will likely produce the most architecturally grounded quality playbooks. It should correctly identify cross-module state machines, trace defensive patterns through multiple abstraction layers, and produce fitness-to-purpose scenarios that reference specific code locations. Risk: may over-engineer the quality system for simple projects.

**Sonnet** will likely produce the most balanced and practically useful output. Clean code, correct test assertions, proper framework conventions. Risk: may be conservative with scenario counts, producing fewer but higher-quality scenarios.

**Haiku** will likely produce the broadest coverage (most scenarios, most tests) but with more quality variance. Some tests may be generic or superficially derived. Risk: quantity over quality — may pad scenario counts with less meaningful items.

**ChatGPT** will likely produce focused, high-signal output but miss systemic issues. Strong on individual test correctness but may not connect findings across the codebase. Risk: missing the forest for the trees.

**Gemini** will likely produce thorough output with good format compliance. Should follow the playbook's templates closely. Risk: may over-apply templates mechanically without adapting to project specifics.

These predictions should be compared against actual runs to validate the review methodology.

---

## File Inventory

```
reviews/
├── REVIEW_METHODOLOGY.md          ← this file
├── MODEL_ANALYSIS.md              ← detailed model analysis
├── model_radar_chart.html         ← interactive visualization
├── wide-review-v1.2.6/
│   ├── INSTRUCTIONS.md
│   ├── REVIEW_PROMPT.md
│   ├── TRIAGE.md
│   ├── opus.md
│   ├── sonnet.md
│   ├── haiku.md
│   └── chatgpt.md                 (gemini not available for v1.2.6)
├── wide-review-v1.2.7/
│   ├── INSTRUCTIONS.md
│   ├── REVIEW_PROMPT.md
│   ├── TRIAGE.md
│   ├── opus.md
│   ├── sonnet.md
│   ├── haiku.md
│   ├── chatgpt.md
│   └── gemini-pro.md
├── wide-review-v1.2.8/
│   ├── INSTRUCTIONS.md
│   ├── REVIEW_PROMPT.md
│   ├── TRIAGE.md
│   ├── opus.md
│   ├── sonnet.md
│   ├── haiku.md
│   ├── chatgpt.md
│   └── gemini-pro.md
└── wide-review-v1.2.9/
    ├── INSTRUCTIONS.md
    ├── REVIEW_PROMPT.md
    ├── TRIAGE.md
    ├── opus.md
    ├── sonnet.md
    ├── haiku.md
    ├── chatgpt.md
    └── gemini-pro.md
```
