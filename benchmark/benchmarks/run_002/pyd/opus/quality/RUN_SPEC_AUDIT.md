# Spec Audit Protocol: Pydantic

## The Definitive Audit Prompt

Give this prompt identically to three independent AI tools (e.g., Claude Code, Cursor, Copilot).

---

**Context files to read:**

1. `README.md` — Project overview, basic usage examples, key features
2. `quality/QUALITY.md` — Quality constitution, fitness-to-purpose scenarios
3. `pydantic/main.py` — BaseModel core implementation
4. `pydantic/fields.py` — FieldInfo and Field() definitions
5. `pydantic/types.py` — Constrained types (conint, confloat, constr, etc.)
6. `pydantic/config.py` — ConfigDict configuration options
7. `pydantic/errors.py` — Error hierarchy and codes
8. `pydantic/_internal/_generate_schema.py` — Schema generation pipeline
9. `pydantic/_internal/_model_construction.py` — ModelMetaclass and model building
10. `pydantic/_internal/_discriminated_union.py` — Discriminated union resolution

**Task:** Act as the Tester. Read the actual code in `pydantic/` and `pydantic/_internal/` and compare it against the specifications listed above (README, docstrings, type annotations, quality constitution scenarios).

**Requirement confidence tiers:**
Requirements are tagged with `[Req: tier — source]`. Weight your findings by tier:
- **formal** — written by humans in README, docstrings, or documentation. Authoritative. Divergence is a real finding.
- **user-confirmed** — stated by the user. Treat as authoritative.
- **inferred** — deduced from code behavior. Lower confidence. Report divergence as NEEDS REVIEW.

**Rules:**
- ONLY list defects. Do not summarize what matches.
- For EVERY defect, cite specific file and line number(s).
  If you cannot cite a line number, do not include the finding.
- Before claiming missing, grep the codebase.
- Before claiming exists, read the actual function body.
- Classify each finding: MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM
- For findings against inferred requirements, add: NEEDS REVIEW

**Defect classifications:**
- **MISSING** — Spec/docs require it, code doesn't implement it
- **DIVERGENT** — Both spec and code address it, but they disagree
- **UNDOCUMENTED** — Code does it, spec/docs don't mention it
- **PHANTOM** — Spec describes it, but it's actually implemented differently than described

**Project-specific scrutiny areas:**

1. **Schema generation for complex types:** Read `_generate_schema.py` functions that handle `Union`, `Optional`, `Literal`, `Annotated`, and recursive types. Does every type path produce a correct `CoreSchema`? Are there types that silently fall through to a generic handler when they should have specific handling? [Req: inferred — from _generate_schema.py type dispatch]

2. **Field constraint propagation in inheritance:** Read `fields.py` `merge_field_infos()` and `_model_construction.py` field collection. When a child model overrides a parent field with `Field(description="new")`, do all parent constraints (gt, le, min_length, pattern) survive the merge? Trace the `_attributes_set` logic. [Req: inferred — from FieldInfo merge behavior]

3. **`__pydantic_complete__` state machine integrity:** Read `_model_construction.py` `ModelMetaclass.__new__()` and `complete_model_class()`. Map every assignment to `__pydantic_complete__`. Is there any code path where a model is used (validated against, serialized from) while `__pydantic_complete__` is `False`? What happens when `model_rebuild()` is called concurrently? [Req: inferred — from state machine tracking]

4. **Discriminated union edge cases:** Read `_discriminated_union.py` `_ApplyInferredDiscriminator`. What happens when: (a) two union members share a discriminator value, (b) the discriminator field is Optional, (c) the discriminator is on a nested model, (d) `definitions` dict is missing a referenced schema? [Req: inferred — from discriminated union resolution]

5. **Serialization mode consistency:** Read `main.py` `model_dump()` and `model_dump_json()`. For each parameter (`exclude`, `include`, `exclude_none`, `by_alias`, `exclude_defaults`), does the Python serialization and JSON serialization apply the parameter identically? Are there parameters that work in one mode but are silently ignored in the other? [Req: inferred — from serialization paths]

6. **Frozen model enforcement completeness:** Read `main.py` `__setattr__`, `__delattr__`, `_check_frozen()`. Does frozen protection cover: (a) field assignment, (b) field deletion, (c) extra field assignment, (d) private attribute assignment? What about `model_copy(update={...})` — does it respect or bypass frozen? [Req: inferred — from frozen enforcement]

7. **TypeAdapter config precedence:** Read `type_adapter.py` `__init__()`. When `TypeAdapter(SomeModel, config=ConfigDict(...))` wraps a BaseModel subclass, which config wins — TypeAdapter's or the model's? Is this documented? Is there a test for the conflict case? [Req: inferred — from TypeAdapter config handling]

8. **Validator decorator ordering guarantees:** Read `_decorators.py` and `functional_validators.py`. Are `mode='before'` validators guaranteed to run before `mode='after'` regardless of definition order in source? What about validators inherited from parent classes vs defined in child classes? Is the ordering documented? [Req: inferred — from decorator collection order]

9. **Error code coverage:** Read `errors.py` `PydanticErrorCodes` Literal union. For each error code, grep the codebase to find where it's raised. Are there codes that are defined but never raised? Are there error conditions that raise a generic exception instead of using the appropriate code? [Req: formal — errors.py PydanticErrorCodes definition]

10. **`model_construct()` safety documentation:** Read `main.py` `model_construct()`. The docstring says it creates an instance without validation. Is it clearly documented that: (a) field types are not checked, (b) validators don't run, (c) defaults for missing fields may not be applied, (d) the resulting instance may violate model constraints? Is there a warning about using it with frozen models? [Req: formal — model_construct() docstring]

**Output format:**

### [filename.ext]
- **Line NNN:** [MISSING / DIVERGENT / UNDOCUMENTED / PHANTOM] [Req: tier — source] Description.
  Spec says: [quote or reference]. Code does: [what actually happens].

---

## Running the Audit

1. Give the identical prompt above to three AI tools (e.g., Claude Code, Cursor, Copilot)
2. Each auditor works independently — no cross-contamination
3. Collect all three reports into `quality/spec_audits/`

## Triage Process

After all three models report, merge findings:

| Confidence | Found By | Action |
|------------|----------|--------|
| Highest | All three | Almost certainly real — fix or update spec |
| High | Two of three | Likely real — verify and fix |
| Needs verification | One only | Could be real or hallucinated — deploy verification probe |

### The Verification Probe

When models disagree on factual claims, deploy a read-only probe:

1. **Select a model** — preferably one that did NOT make the disputed claim.
2. **Give it the claim** — quote the finding exactly.
3. **Ask it to read the code** — "Read `file.py` lines X-Y and report what actually happens when [condition]."
4. **Compare the probe result** against the original claim.

Never resolve factual disputes by majority vote — the majority can be wrong about what code does.

### Categorize Each Confirmed Finding

- **Spec bug** — Spec is wrong, code is fine → update spec/docs
- **Design decision** — Human judgment needed → discuss and decide
- **Real code bug** — Fix in small batches by subsystem
- **Documentation gap** — Feature exists but undocumented → update docs
- **Missing test** — Code is correct but no test verifies it → add to functional tests
- **Inferred requirement wrong** — Inferred req doesn't match intent → correct in QUALITY.md

## Fix Execution Rules

- Group fixes by subsystem, not by defect number
- **Batch size: 3–5 fixes per batch.** Fewer than 3 creates excessive overhead. More than 5 risks introducing new bugs.
- Never one mega-prompt for all fixes
- Each batch: implement, test, have all three reviewers verify the diff
- At least two auditors must confirm fixes pass before marking complete

## Output

Save audit reports to `quality/spec_audits/YYYY-MM-DD-[model].md`
Save triage summary to `quality/spec_audits/YYYY-MM-DD-triage.md`
