# Code Review: PYD-02 — Complex Number Serializer

**Files reviewed:**
- `pydantic-core/src/serializers/type_serializers/complex.rs`
- `pydantic-core/tests/serializers/test_complex.py`

---

### pydantic-core/src/serializers/type_serializers/complex.rs

- **Line 81:** [BUG] `re != 0.0` fails to distinguish `-0.0` from `0.0` due to IEEE 754 comparison semantics (where `-0.0 == 0.0` is true). When the real part is negative zero, the condition is false and the real part is omitted entirely. `complex(-0.0, 1.0)` serializes as `"1j"` instead of `"-0+1j"`. Python's own `str(complex(-0.0, 1.0))` produces `(-0+1j)`, preserving the negative zero. This is a round-trip fidelity loss: deserializing `"1j"` produces `complex(0.0, 1.0)`, not `complex(-0.0, 1.0)`. The fix is to replace `re != 0.0` with `re != 0.0 || re.is_sign_negative()` (or equivalently `!(re == 0.0 && re.is_sign_positive())`). The same loss applies to `complex(-0.0, -0.0)` which serializes as `"-0j"` instead of `"-0-0j"`.

### pydantic-core/tests/serializers/test_complex.py

- **Line 8-23:** [INCOMPLETE] The parametrized test cases do not cover negative zero in the real part. There is no test case for `complex(-0.0, 1.0)` (expected `"-0+1j"`) or `complex(-0.0, -0.0)` (expected `"-0-0j"`). These are exactly the cases that would expose the bug on line 81 of `complex.rs`. The test does cover negative zero in the imaginary part (`complex(1.5, -0.0)` on line 14) but not in the real part.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG | 1 |
| INCOMPLETE (test coverage gap) | 1 |
| QUESTION | 0 |

- **Files with no findings:** None — both files have findings.
- **Overall assessment:** **FIX FIRST** — The negative-zero real-part bug causes silent data loss during serialization, violating round-trip fidelity (`model_validate(model.model_dump())` would not preserve `-0.0` real parts). While `-0.0` is uncommon in typical usage, it has defined IEEE 754 semantics and Python preserves it, so pydantic's serializer should too.
