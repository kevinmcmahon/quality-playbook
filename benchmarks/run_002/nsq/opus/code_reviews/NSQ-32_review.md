# NSQ-32 Code Review: nsqadmin/static/js/lib/handlebars_helpers.js

**Reviewer:** Claude Opus 4.6
**Date:** 2026-04-01
**File:** `nsqadmin/static/js/lib/handlebars_helpers.js`

---

### handlebars_helpers.js

- **Line 26:** BUG (High). `prefix.substring(prefix.length, 1)` does not return the last character. `String.prototype.substring(start, end)` swaps arguments when `start > end`, so `substring(prefix.length, 1)` returns `prefix.substring(1, prefix.length)` — i.e., the entire string minus the first character. The comparison `!== '.'` will almost always be true, so a trailing dot is always appended, even if the prefix already ends with `'.'`. The correct expression is `prefix.substring(prefix.length - 1)` or `prefix.charAt(prefix.length - 1)`. If the prefix from `AppState` already ends with `'.'`, this produces a double-dot (`..`) in the statsd key, which would break metric lookups.

- **Line 187-197:** BUG (Low). The `percSuffix` helper computes ordinal suffixes using `Math.floor(f * 100) % 10`, which only examines the last digit. This produces incorrect English ordinals for the "teens": 11→"st" (should be "th"), 12→"nd" (should be "th"), 13→"rd" (should be "th"). For example, the 11th percentile would render as "11st" instead of "11th". Severity is low because percentile values in practice (e.g., 0.99, 0.999) are unlikely to hit the teens range, but the logic is incorrect.

- **Line 93-100:** BUG (Medium). In `genTargets`, when `typ === 'e2e'`, the topic and channel names from `ns1['topic']` and `ns1['channel']` are interpolated directly into the graphite key without being passed through `sanitizeGraphiteKey()`. In contrast, the `typ === 'topic'` (line 79) and `typ === 'channel'` (line 83-84) branches both call `sanitizeGraphiteKey()` on their namespace arguments. If a topic or channel name contains special characters (spaces, slashes, etc.), the e2e graphite key will be malformed or will fail to match the actual metric path that was sanitized by statsdaemon.

- **Line 113-114:** QUESTION (Low). The `default` helper uses `x ? x : defaultValue`, which treats all falsy values (`0`, `""`, `false`, `null`, `undefined`) as missing. If `x` is legitimately `0` or an empty string, the default value is returned instead. This may be intentional for the template contexts where it's used, but `x != null ? x : defaultValue` would be more precise if only null/undefined should trigger the fallback.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 1 |
| BUG (Medium) | 1 |
| BUG (Low) | 1 |
| QUESTION (Low) | 1 |
| **Total** | **4** |

**Overall assessment:** FIX FIRST — The `substring` bug on line 26 is a clear correctness defect that can produce malformed statsd keys with double dots. The missing `sanitizeGraphiteKey` call in the e2e branch is a consistency defect that can cause metric lookup failures for topics/channels with special characters.
