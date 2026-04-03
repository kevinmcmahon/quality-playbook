# Code Review Protocol: Pydantic

## Bootstrap (Read First)

Before reviewing, read these files for context:

1. `quality/QUALITY.md` — Quality constitution and fitness-to-purpose scenarios
2. `pydantic/main.py` — BaseModel core implementation
3. `pydantic/fields.py` — FieldInfo and Field() definitions
4. `pydantic/_internal/_generate_schema.py` — Schema generation pipeline
5. `pydantic/_internal/_model_construction.py` — ModelMetaclass and model building

## What to Check

### Focus Area 1: Schema Generation Pipeline

**Where:** `pydantic/_internal/_generate_schema.py`, `pydantic/_internal/_core_utils.py`
**What:** Verify that type-to-schema conversion handles all edge cases. Look for:
- `isinstance` / `issubclass` guards that miss new types
- `try/except` blocks that catch too broadly (swallowing real errors)
- Schema composition errors in union types, optional types, and nested models
- Forward reference resolution failures that produce `MockCoreSchema` instead of real schemas
**Why:** This is the most complex module (~4000 lines). A schema generation bug silently produces wrong validators for all models using that type.

### Focus Area 2: Field Metadata Merging

**Where:** `pydantic/fields.py` — `FieldInfo`, `merge_field_infos()`, `_apply_field_from_defaults()`
**What:** Verify constraint preservation during:
- Parent→child field inheritance
- `Field()` argument merging with type annotations
- `PydanticUndefined` sentinel comparisons (correctness of `is not PydanticUndefined`)
- `_attributes_set` tracking for explicit vs default values
**Why:** Silent constraint dropping during merge means a child model validates less strictly than its parent — a security and correctness risk.

### Focus Area 3: Model Construction State Machine

**Where:** `pydantic/_internal/_model_construction.py` — `ModelMetaclass.__new__()`, `complete_model_class()`
**What:** Trace the `__pydantic_complete__` state transitions:
- Set to `False` at start of `__new__`
- Set to `True` after successful schema generation
- What happens when schema generation fails (forward refs, circular deps)?
- Are there code paths that use a model when `__pydantic_complete__ == False`?
**Why:** An incomplete model silently accepts any input without validation.

### Focus Area 4: Serialization Fidelity

**Where:** `pydantic/main.py` — `model_dump()`, `model_dump_json()`; `pydantic/_internal/_generate_schema.py` — serialization schema generation
**What:** Verify round-trip fidelity:
- `model_validate(model.model_dump())` must preserve all field values including extras
- `mode='python'` vs `mode='json'` produce appropriately different outputs
- Custom types with separate validation/serialization schemas stay consistent
- `exclude`, `include`, `exclude_none`, `by_alias` parameters interact correctly
**Why:** Data loss during serialization is silent and cascading — downstream systems consume wrong data.

### Focus Area 5: Discriminated Union Resolution

**Where:** `pydantic/_internal/_discriminated_union.py`, `pydantic/types.py` — `Discriminator` class
**What:** Check:
- All discriminator value mappings are unambiguous (no value maps to 2+ members)
- `None` as discriminator value is handled explicitly
- `MissingDefinitionForUnionRef` is raised when definitions are incomplete
- Nested discriminated unions resolve correctly
**Why:** Misrouted union validation produces valid-looking objects with wrong types — the hardest bugs to find.

### Focus Area 6: Type Coercion Boundaries

**Where:** `pydantic/types.py`, `pydantic/config.py` — `strict` mode
**What:** Verify coercion rules:
- Strict mode consistently rejects all type coercions (not just some)
- `conint()`, `confloat()`, `constr()` constraint guards (`is not None`) don't skip constraints
- `allow_inf_nan` correctly blocks `float('inf')` and `float('nan')`
- `Annotated[type, constraints]` applies all constraints, not just the first
**Why:** A missed constraint guard silently accepts invalid values. Users rely on constraints for data integrity.

### Focus Area 7: Validator and Serializer Ordering

**Where:** `pydantic/_internal/_decorators.py`, `pydantic/functional_validators.py`
**What:** Verify:
- `mode='before'` validators always execute before `mode='after'`
- Parent validators execute before child validators within the same mode
- `mode='wrap'` validators receive the correct handler
- Multiple validators on the same field all execute
**Why:** Wrong validator order silently changes behavior — a normalizer running after validation instead of before makes validation useless.

### Focus Area 8: Error Reporting Quality

**Where:** `pydantic/errors.py`, `pydantic_core` error integration
**What:** Verify:
- Every `PydanticUserError` includes a valid `PydanticErrorCodes` code
- `ValidationError.errors()` includes `loc`, `type`, and `msg` for every error
- Nested model errors include full path in `loc` tuple
- Error messages are actionable (not just "validation error")
**Why:** Poor error messages waste developer time. Missing location info makes debugging nested model errors nearly impossible.

## Guardrails

- **Line numbers are mandatory.** If you cannot cite a specific line, do not include the finding.
- **Read function bodies, not just signatures.** Don't assume a function works correctly based on its name.
- **If unsure whether something is a bug or intentional**, flag it as a QUESTION rather than a BUG.
- **Grep before claiming missing.** If you think a feature is absent, search the codebase. If found in a different file, that's a location defect, not a missing feature.
- **Do NOT suggest style changes, refactors, or improvements.** Only flag things that are incorrect or could cause failures.

## Output Format

Save findings to `quality/code_reviews/YYYY-MM-DD-reviewer.md`

For each file reviewed:

### filename.ext
- **Line NNN:** [BUG / QUESTION / INCOMPLETE] Description. Expected vs. actual. Why it matters.

### Summary
- Total findings by severity
- Files with no findings
- Overall assessment: SHIP IT / FIX FIRST / NEEDS DISCUSSION

## Phase 2: Regression Tests

After the code review produces BUG findings, write regression tests in `quality/test_regression.py` that reproduce each bug. Each test should:
- Target the exact code path and line numbers from the finding
- Fail on the current implementation, confirming the bug exists
- Use `unittest.mock.patch` to isolate from external services
- Include the finding description in the test docstring

Report results as a confirmation table:

| Finding | Test | Result | Confirmed? |
|---------|------|--------|------------|
| [description] | test_... | FAILED (expected) | YES — bug confirmed |
| [description] | test_... | PASSED (unexpected) | NO — needs investigation |
