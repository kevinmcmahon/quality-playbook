# QPB NSQ Benchmark: Scoring Summary v3

## Methodology

**Scoring approach:** Pool-based scoring with requirement-violation patterns.

Each of the 58 NSQ ground truth defects was translated from patch-note form into a requirement-violation entry: a testable statement of what correct behavior looks like, the specific way the code violates it, and the detection signals a reviewer would produce. Search patterns were built from the requirement violation (not the fix description), and matched against ALL 57 reviews in each condition — a bug found in ANY review slot counts.

**Conditions scored:**
- **control** — No playbook. GPT-5.4 via Copilot CLI with generic code review prompt.
- **v1.2.12** — Quality Playbook v1.2.12.
- **v1.2.13** — Quality Playbook v1.2.13 (council-reviewed, two-pass, named bug shapes).

## Headline Results

| Condition | Found | Total | Rate |
|-----------|-------|-------|------|
| control   | 38    | 58    | 65.5% |
| v1.2.12   | 36    | 58    | 62.1% |
| v1.2.13   | 28    | 58    | 48.3% |

## By Requirement Category

| Category | control | v1.2.12 | v1.2.13 |
|----------|---------|---------|---------|
| concurrency (13) | 9 (69%) | 10 (77%) | 8 (62%) |
| resource-lifecycle (10) | 9 (90%) | 7 (70%) | 7 (70%) |
| error-handling (9) | 5 (56%) | 4 (44%) | 4 (44%) |
| api-contract (7) | 6 (86%) | 5 (71%) | 2 (29%) |
| data-integrity (7) | 4 (57%) | 4 (57%) | 3 (43%) |
| arithmetic-boundary (5) | 2 (40%) | 2 (40%) | 2 (40%) |
| input-validation (4) | 1 (25%) | 2 (50%) | 1 (25%) |
| security (3) | 2 (67%) | 2 (67%) | 1 (33%) |

## Key Findings

### 1. Control leads overall, but the gap narrows for concurrency

The control condition (no playbook) found 38/58 defects (65.5%), outperforming both playbook versions. However, v1.2.12 actually edges out the control on concurrency defects (77% vs 69%), and matches or exceeds it on input-validation (50% vs 25%).

### 2. v1.2.13 regressed relative to v1.2.12

v1.2.13 found 28/58 (48.3%) vs v1.2.12's 36/58 (62.1%). The regression is concentrated in **api-contract** (29% vs 71%) and **security** (33% vs 67%). The two-pass structure and named bug shapes in v1.2.13 did NOT improve detection — they may have narrowed the model's attention.

### 3. The playbook adds unique detections but suppresses more

v1.2.13 found 3 bugs the control missed (NSQ-06, NSQ-07, NSQ-14), but the control found 13 bugs that v1.2.13 missed. The playbook's unique contributions are high-value (a data integrity bug, an input validation bug, an error handling bug), but the suppression cost exceeds the added value.

### 4. v1.2.12 was the better playbook version

v1.2.12 found 7 bugs the control missed while losing only 9 — a much tighter differential than v1.2.13's 3 added / 13 lost.

### 5. WEAK requirements are universally hard

None of the 4 WEAK-strength defects (NSQ-11, NSQ-18, NSQ-31, NSQ-32) were found by any condition. These represent defects where the requirement itself is debatable.

### 6. Some defects are just hard for everyone

18 defects were missed by all three conditions. These cluster in: arithmetic-boundary (NSQ-38, NSQ-43, NSQ-58), concurrency edge cases (NSQ-20, NSQ-21), configuration interactions (NSQ-36, NSQ-39, NSQ-44), and the 4 WEAK defects.

## Differential Detail

### v1.2.13 found, control missed (3):
- **NSQ-06** [error-handling] connectCallback missing early return causes duplicate syncs
- **NSQ-07** [data-integrity] PutMessages batch accounting on partial failure
- **NSQ-14** [input-validation] REQ timeout disconnects client (fatal error for out-of-range param)

### Control found, v1.2.13 missed (13):
- **NSQ-12** [api-contract] mem-queue-size=0 creates unbuffered instead of nil
- **NSQ-17** [concurrency] SubEventChan buffer races with subscription cleanup
- **NSQ-24** [error-handling] NSQLookupd os.Exit in daemon code
- **NSQ-26** [error-handling] infinite unbounded ephemeral retry loop
- **NSQ-28** [data-integrity] buffer reuse across message loop iterations
- **NSQ-29** [resource-lifecycle] HTTP client created per sync iteration
- **NSQ-34** [data-integrity] loop variable scoping error in channel aggregation
- **NSQ-37** [api-contract] IPv6 address formatting with string concat
- **NSQ-41** [security] TLS flag override silently disables security
- **NSQ-42** [api-contract] IPv6 not bracketed in admin URLs
- **NSQ-46** [resource-lifecycle] unclosed file handle in test
- **NSQ-56** [input-validation] MPUB binary parameter validation missing
- **NSQ-57** [api-contract] missing messagePump notification for proactive channels

## Implications for v1.2.14

1. **The two-pass structure needs work.** v1.2.13's two-pass didn't help — the model merged all findings into one pass anyway, and the focus areas may have narrowed attention.

2. **Focus area count matters.** v1.2.13 generated 7 focus areas. The control had zero focus areas and found more. The playbook's value-add must come from *better* focus areas, not *more* of them.

3. **api-contract and security categories regressed hardest.** These are areas where the model needs to check protocol-level correctness (negotiation, IPv6 formatting, TLS config). The playbook's concurrency-heavy focus areas may have crowded these out.

4. **v1.2.12 is the better baseline for iteration.** Roll back the v1.2.13 changes and iterate from v1.2.12, incorporating only the council suggestions that don't narrow the model's field of view.
