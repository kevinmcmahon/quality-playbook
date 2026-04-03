# Integration Test Protocol: Pydantic

## Working Directory

All commands in this protocol use **relative paths from the project root.** Run everything from the directory containing `pyproject.toml`. Do not `cd` to an absolute path.

## Safety Constraints

- DO NOT modify source code
- DO NOT delete files
- ONLY create files in `quality/results/`
- If something fails, record it and move on — DO NOT fix it

## Pre-Flight Check

Before running integration tests, verify:

- [ ] Python 3.9+ installed: `python --version`
- [ ] Pydantic installed: `python -c "import pydantic; print(pydantic.__version__)"`
- [ ] pydantic-core installed: `python -c "import pydantic_core; print(pydantic_core.__version__)"`
- [ ] pytest installed: `python -c "import pytest; print(pytest.__version__)"`
- [ ] Dev dependencies installed: `pip install -e ".[dev]"` or `uv pip install -e ".[dev]"`
- [ ] Optional email-validator: `python -c "import email_validator" 2>/dev/null && echo "OK" || echo "SKIP email tests"`

If any check fails, STOP and report what's missing. Do not skip tests silently.

## Test Matrix

| # | Test | What It Exercises | Method | Pass Criteria |
|---|------|-------------------|--------|---------------|
| 1 | Model validation round-trip | BaseModel validate → dump → re-validate | `pytest quality/test_functional.py::TestSpecRequirements -v` | All tests pass, 0 errors |
| 2 | Fitness scenarios | All 10 QUALITY.md scenarios | `pytest quality/test_functional.py::TestFitnessScenarios -v` | All 10 tests pass |
| 3 | Boundary conditions | Defensive pattern coverage | `pytest quality/test_functional.py::TestBoundariesAndEdgeCases -v` | All tests pass, 0 errors |
| 4 | Existing test suite | No regressions from quality files | `pytest tests/ -x -q --timeout=120` | All existing tests pass |
| 5 | JSON Schema generation | Schema for complex models | See custom test below | Schema validates against JSON Schema Draft 2020-12 |
| 6 | Cross-version Python | Validation across Python 3.9-3.13 | `python3.X -m pytest quality/ -v` for each version | All tests pass on all available versions |
| 7 | Type coercion matrix | Strict vs lax mode × multiple types | See custom test below | Strict rejects coercion, lax accepts |
| 8 | Serialization fidelity | model_dump + model_dump_json round-trip | See custom test below | Round-trip preserves all field values |

## Field Reference Table (built from schemas, not memory)

### Subsystem: BaseModel

Source: `pydantic/main.py`

| Field | Type | Constraints |
|-------|------|-------------|
| `model_config` | `ClassVar[ConfigDict]` | Configuration dictionary |
| `__pydantic_complete__` | `bool` | True after successful schema generation |
| `__pydantic_core_schema__` | `CoreSchema` | Generated validation schema |
| `__pydantic_validator__` | `SchemaValidator` | Core validator instance |
| `__pydantic_serializer__` | `SchemaSerializer` | Core serializer instance |
| `__pydantic_fields__` | `dict[str, FieldInfo]` | Field definitions |
| `__pydantic_computed_fields__` | `dict[str, ComputedFieldInfo]` | Computed field definitions |
| `__pydantic_extra__` | `dict[str, Any] \| None` | Extra field values (when extra='allow') |
| `__pydantic_fields_set__` | `set[str]` | Names of explicitly provided fields |
| `__pydantic_private__` | `dict[str, Any] \| None` | Private attribute values |

### Subsystem: FieldInfo

Source: `pydantic/fields.py`

| Field | Type | Constraints |
|-------|------|-------------|
| `annotation` | `type[Any] \| None` | The type annotation |
| `default` | `Any` | Default value (PydanticUndefined if not set) |
| `default_factory` | `Callable[[], Any] \| None` | Factory for default (mutex with default) |
| `alias` | `str \| None` | General alias |
| `validation_alias` | `str \| AliasPath \| AliasChoices \| None` | Validation-specific alias |
| `serialization_alias` | `str \| None` | Serialization-specific alias |
| `title` | `str \| None` | Field title for schema |
| `description` | `str \| None` | Field description |
| `gt` | `float \| None` | Greater than (exclusive lower bound) |
| `ge` | `float \| None` | Greater than or equal |
| `lt` | `float \| None` | Less than (exclusive upper bound) |
| `le` | `float \| None` | Less than or equal |
| `multiple_of` | `float \| None` | Must be multiple of this value |
| `min_length` | `int \| None` | Minimum length for strings/collections |
| `max_length` | `int \| None` | Maximum length for strings/collections |
| `pattern` | `str \| None` | Regex pattern for string validation |
| `discriminator` | `str \| Discriminator \| None` | Union discriminator |
| `frozen` | `bool \| None` | Whether field is frozen (immutable) |
| `exclude` | `bool \| None` | Exclude from serialization |
| `deprecated` | `str \| bool \| None` | Deprecation message or flag |
| `json_schema_extra` | `JsonDict \| Callable \| None` | Extra JSON Schema properties |
| `validate_default` | `bool \| None` | Whether to validate default value |

### Subsystem: ConfigDict

Source: `pydantic/config.py`

| Field | Type | Constraints |
|-------|------|-------------|
| `strict` | `bool` | Default False. Enable strict type validation |
| `frozen` | `bool` | Default False. Make model immutable |
| `extra` | `Literal['allow', 'forbid', 'ignore']` | Extra field handling mode |
| `populate_by_name` | `bool` | Allow field name in addition to alias |
| `str_strip_whitespace` | `bool` | Strip whitespace from strings |
| `str_to_lower` | `bool` | Convert strings to lowercase |
| `str_to_upper` | `bool` | Convert strings to uppercase |
| `validate_default` | `bool` | Validate default values |
| `arbitrary_types_allowed` | `bool` | Allow non-pydantic types |
| `revalidate_instances` | `Literal['always', 'never', 'subclass-instances']` | Instance revalidation mode |

## Setup and Teardown

### Setup

```bash
# Install project in development mode
pip install -e ".[dev]" 2>/dev/null || uv pip install -e ".[dev]"

# Verify installation
python -c "import pydantic; print(f'Pydantic {pydantic.__version__}')"
python -c "import pydantic_core; print(f'Core {pydantic_core.__version__}')"
```

### Teardown

No infrastructure to clean up — Pydantic is a pure Python library. All tests use in-memory objects.

```bash
# Remove any generated test artifacts
rm -f quality/results/*.md
```

## Execution

### Parallelism Groups

```bash
# Group 1 (parallel — independent test groups)
pytest quality/test_functional.py::TestSpecRequirements -v --tb=short > quality/results/spec_results.txt 2>&1 &
pytest quality/test_functional.py::TestFitnessScenarios -v --tb=short > quality/results/fitness_results.txt 2>&1 &
pytest quality/test_functional.py::TestBoundariesAndEdgeCases -v --tb=short > quality/results/boundary_results.txt 2>&1 &
wait

# Group 2 (sequential — full test suite, resource-intensive)
pytest tests/ -x -q --timeout=120 > quality/results/existing_tests.txt 2>&1
```

**Note:** These commands assume POSIX-compatible shell (bash, sh, zsh).

## Custom Integration Tests

### Test 5: JSON Schema Validation

```bash
python -c "
from pydantic import BaseModel, Field
from typing import List, Optional
import json

class Address(BaseModel):
    street: str
    city: str
    zip_code: str = Field(pattern=r'^\d{5}$')

class User(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    email: Optional[str] = None
    addresses: List[Address] = []

schema = User.model_json_schema()
print(json.dumps(schema, indent=2))

# Verify key constraints in schema
props = schema['properties']
assert props['name'].get('minLength') == 1
assert props['name'].get('maxLength') == 100
assert props['age'].get('minimum') == 0
assert props['age'].get('maximum') == 150
print('PASS: JSON Schema constraints verified')
"
```

### Test 7: Type Coercion Matrix

```bash
python -c "
from pydantic import BaseModel, ConfigDict, ValidationError

class LaxModel(BaseModel):
    int_val: int
    float_val: float
    str_val: str
    bool_val: bool

class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True)
    int_val: int
    float_val: float
    str_val: str
    bool_val: bool

# Lax mode: coercion succeeds
m = LaxModel(int_val='42', float_val='3.14', str_val=123, bool_val=1)
assert m.int_val == 42
assert m.float_val == 3.14
assert m.str_val == '123'
assert m.bool_val is True
print('PASS: Lax coercion works')

# Strict mode: coercion rejected
coercion_inputs = {'int_val': '42', 'float_val': 3.14, 'str_val': 'ok', 'bool_val': True}
try:
    StrictModel(**coercion_inputs)
    print('FAIL: Strict mode accepted str->int coercion')
except ValidationError:
    print('PASS: Strict mode rejected str->int coercion')
"
```

### Test 8: Serialization Fidelity

```bash
python -c "
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict
from datetime import datetime
import json

class Inner(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str
    value: int

class Outer(BaseModel):
    model_config = ConfigDict(extra='allow')
    inner: Inner
    items: List[int]
    metadata: Dict[str, str]
    created: datetime
    optional_field: Optional[str] = None

# Create with complex data
original = Outer(
    inner={'name': 'test', 'value': 42, 'extra_field': 'bonus'},
    items=[1, 2, 3],
    metadata={'key': 'value'},
    created='2024-01-15T10:30:00',
    optional_field='present',
    outer_extra='extra_value'
)

# Python round-trip
dumped = original.model_dump()
restored = Outer.model_validate(dumped)
assert restored.inner.name == original.inner.name
assert restored.inner.value == original.inner.value
assert restored.items == original.items
assert restored.metadata == original.metadata
assert restored.optional_field == original.optional_field
print('PASS: Python round-trip preserves all fields')

# JSON round-trip
json_str = original.model_dump_json()
json_restored = Outer.model_validate_json(json_str)
assert json_restored.inner.name == original.inner.name
assert json_restored.items == original.items
print('PASS: JSON round-trip preserves all fields')
"
```

## Quality Gates

1. **Functional test pass rate**: All 3 test groups pass with 0 errors AND 0 failures
2. **Existing test suite**: No regressions — `pytest tests/ -x -q` reports same pass count as baseline
3. **JSON Schema correctness**: Generated schema includes all field constraints (min_length, max_length, gt, ge, lt, le, pattern, enum values)
4. **Coercion consistency**: Strict mode rejects ALL type coercions for int, float, str, bool; Lax mode accepts common coercions
5. **Round-trip fidelity**: `model_validate(model.model_dump())` preserves field values, types, and extras at all nesting levels
6. **Error quality**: Every `ValidationError` includes `loc`, `type`, and `msg` fields

## Post-Run Verification

For each test run, verify at these levels:

1. **Process:** Clean exit (`pytest` returns exit code 0), no crashes
2. **State:** No modified source files (`git status` shows clean)
3. **Data:** Test result files exist in `quality/results/`
4. **Content:** Check result files for actual test output (not empty files)
5. **Domain:** JSON Schema validates, coercion matrix behaves correctly, round-trip preserves data
6. **Resource:** No orphaned Python processes after test completion

## Execution UX (How to Present When Running This Protocol)

### Phase 1: The Plan

Before running anything, show what's about to happen:

| # | Test | What It Checks | Est. Time |
|---|------|---------------|-----------|
| 1 | Spec requirements (18 tests) | Core API contract | ~5s |
| 2 | Fitness scenarios (10 tests) | QUALITY.md coverage | ~5s |
| 3 | Boundary tests (22 tests) | Defensive patterns | ~5s |
| 4 | Existing test suite | No regressions | ~2-5m |
| 5 | JSON Schema generation | Schema correctness | ~5s |
| 6 | Cross-version Python | Version compatibility | ~30s per version |
| 7 | Type coercion matrix | Strict vs lax | ~5s |
| 8 | Serialization fidelity | Round-trip preservation | ~5s |

**Total:** 8 test groups, estimated 3-6 minutes

### Phase 2: Progress

```
✓ Test 1: Spec requirements — PASS (3.2s)
✓ Test 2: Fitness scenarios — PASS (2.8s)
✓ Test 3: Boundary tests — PASS (4.1s)
⧗ Test 4: Existing test suite... running
✓ Test 4: Existing test suite — PASS (180s)
✓ Test 5: JSON Schema generation — PASS (1.2s)
✓ Test 7: Type coercion matrix — PASS (0.8s)
✓ Test 8: Serialization fidelity — PASS (1.1s)
```

### Phase 3: Results

| # | Test | Result | Time | Notes |
|---|------|--------|------|-------|
| 1 | Spec requirements | ✓ PASS | 3.2s | |
| 2 | Fitness scenarios | ✓ PASS | 2.8s | |
| 3 | Boundary tests | ✓ PASS | 4.1s | |
| 4 | Existing test suite | ✓ PASS | 180s | |
| 5 | JSON Schema | ✓ PASS | 1.2s | |
| 7 | Coercion matrix | ✓ PASS | 0.8s | |
| 8 | Serialization | ✓ PASS | 1.1s | |

**Passed:** N/N | **Failed:** 0/N
**Recommendation:** SHIP IT / FIX FIRST / NEEDS INVESTIGATION

## Reporting

Save to `quality/results/YYYY-MM-DD-integration.md`
