# Direct Experiment: Cold Review vs Requirements-Guided Review

Three defects that no condition found in the original 57-review benchmark. Reviewed directly by reading the pre-fix source code.

## NSQ-36: E2E Percentile Validation Missing

**The defect:** `E2EProcessingLatencyPercentiles` (a `[]float64` config field) has no validation in `New()`. Values like 100.0, -5.0, or 0.0 are silently accepted and produce incorrect latency calculations.

**Cold review:** In `New()`, I can see validation for MaxDeflateLevel, ID, TLS settings, StatsdPrefix, and several other config values. The E2E percentile field exists in options.go but doesn't appear in `New()` at all. The bug is an absence — a thing that should be there but isn't.

**Would I find it cold?** Probably not, unless I was systematically checking "for every config field with domain constraints, is there validation?" The absence of validation doesn't create a code smell or structural anomaly. The code that IS there is correct. You have to notice what's missing, and that requires knowing what should be there.

**With the requirement** ("percentile values must be validated in (0, 1.0] at parse time"): Trivially found. Grep for `E2EProcessingLatencyPercentiles` in `New()`, confirm it's absent, done. The requirement tells you exactly what to look for and the code clearly doesn't do it.

**With the abstract principle** ("configuration values with domain constraints must be validated at parse time"): This one is interesting. The principle is true and I could apply it by asking "which config fields have domain constraints?" and checking each one. But `E2EProcessingLatencyPercentiles` is one of ~40 config fields. Without knowing that percentiles specifically need validation, I'd need to audit every field. I might get there, but it's a lot of work compared to the specific requirement.

**Verdict:** Requirements make this findable. Cold review almost certainly misses it. Abstract principle might find it with enough diligence, but the search space is large.

---

## NSQ-39: Worker ID Validation Range vs GUID Bit Width

**The defect:** `New()` validates `opts.ID < 0 || opts.ID >= 4096`, but `guid.go` defines `workerIDBits = uint64(10)` (max 1023). IDs 1024-4095 spill into the timestamp field, causing GUID collisions.

**Cold review:** When I see `opts.ID >= 4096` in nsqd.go and `workerIDBits = 10` in guid.go, the mismatch jumps out — 2^10 = 1024, not 4096. The `idChan: make(chan MessageID, 4096)` buffer on line 76 might even be the source of the wrong constant. The GUID arithmetic (`workerID << workerIDShift`) makes the overflow consequence obvious.

**Would I find it cold?** Yes, IF I was reviewing both files together and doing arithmetic on the bit fields. The two numbers (4096 and 10 bits) are in different files. If I only reviewed nsqd.go, the validation `>= 4096` looks fine on its own — it's a power of two, plausible range. The bug only appears when you connect the two files.

The Copilot control review also found this on the tighter file set, confirming that a strong model CAN connect the dots with both files visible.

**With the requirement** ("worker ID must reject >= 1024, GUID uses 10-bit field"): Trivially found. You're told exactly what to check.

**With the abstract principle** ("validation ranges must match the actual bit width of the destination field"): This would guide me to compare the validation bound against the GUID field width. With `workerIDBits = 10` clearly defined, I'd compute 2^10 = 1024 and compare to 4096. Found.

**Verdict:** This defect IS findable cold if you review both files and do the math. Requirements make it faster and more certain. The abstract principle is particularly effective here because it tells you to compare two specific things (validation range vs bit width) that are both well-defined in the code.

---

## NSQ-44: Auth Server Ignores Configured Root CA

**The defect:** `QueryAuthd()` creates `http_api.NewClient(nil, ...)` — the nil TLS config means auth server requests use system default CAs, ignoring `--tls-root-ca-file`.

**Cold review:** I see `NewClient(nil, connectTimeout, requestTimeout)` in authorizations.go. The `nil` first argument is the TLS config. In nsqd.go, `buildTLSConfig()` loads `TLSRootCAFile` into a cert pool for inbound client verification. But this TLS config is never passed to the auth client path.

**Would I find it cold?** No. The `nil` TLS config is the normal-looking pattern for an HTTP client. There's no code smell — no crash risk, no race condition, no resource leak. The function doesn't even accept a TLS config parameter. You'd only question the `nil` if you already knew that the operator expected all outbound connections to use the configured CA. That's pure intent.

In fact, `buildTLSConfig()` sets the root CA as `ClientCAs` (for verifying inbound client certs), not `RootCAs` (for verifying outbound server certs). So even if you traced the TLS config through, you'd see that the existing config is for a different purpose. The fix for NSQ-44 would need to build a separate outbound TLS config with `RootCAs` set. This is NOT an "oops, forgot to pass the config" bug — it's a design gap where a whole code path was never built.

**With the requirement** ("auth server HTTP client must use --tls-root-ca-file for TLS"): Found immediately. Check `QueryAuthd()`, see `NewClient(nil, ...)`, confirm the TLS config is never threaded through. Done.

**With the abstract principle** ("outbound TLS connections must use the configured CA, not system defaults"): This would guide me to check every outbound HTTP/TLS connection for whether it uses the configured CA. I'd find `QueryAuthd()` and see the nil config. Found — but it requires knowing that auth requests are outbound TLS connections, which means understanding the deployment topology.

**Verdict:** This is the strongest case for requirements. No amount of structural code review will find this. The code is correct for what it does — it just doesn't do something it should. You need to know the requirement to see the gap.

---

## Summary

| Defect | Cold | Specific Req | Abstract Principle |
|--------|------|-------------|-------------------|
| NSQ-36 (percentile validation) | No — absence is invisible | Yes — trivial | Maybe — large search space |
| NSQ-39 (worker ID bit width) | Maybe — if both files reviewed and math done | Yes — trivial | Yes — guides comparison |
| NSQ-44 (auth server CA) | No — nil TLS looks normal | Yes — trivial | Yes — guides outbound audit |

**Key insight:** The three defects represent three different failure modes for cold review:

1. **NSQ-36 is an absence bug.** The code that's there is fine; the bug is what's missing. Cold review finds things that are wrong, not things that should exist but don't.

2. **NSQ-39 is a cross-file arithmetic bug.** Each file is correct in isolation. The bug only appears when you compare a constant in one file against a validation bound in another. Cold review can find this if it reviews both files, but it requires connecting dots across files.

3. **NSQ-44 is a design gap.** The code does what it was designed to do — it just wasn't designed to do the right thing. There's no anomaly to detect. You need to know the requirement to see that a whole feature is missing.

All three are trivially found with specific requirements. The abstract principles are effective for NSQ-39 and NSQ-44 (where they guide a specific comparison or audit) but weaker for NSQ-36 (where the search space is too large without knowing which specific field needs validation).

**What this means for the playbook:** The playbook's value is clearest for absence bugs and design gaps (NSQ-36, NSQ-44). These are invisible to structural review. The playbook derives requirements from intent sources, and those requirements make the invisible visible. For cross-file bugs (NSQ-39), the playbook adds speed and certainty but the bug is findable without it.
