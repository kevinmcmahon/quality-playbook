# Functional Test Examples — Python

Reference companion to `functional_tests.md` with all Python/pytest examples.

Name the test file using pytest conventions: `test_functional.py`.

## Structure: Three Test Groups

Organize tests into three logical groups using classes:

```
Spec Requirements
    — One test per testable spec section
    — Each test's documentation cites the spec requirement

Fitness Scenarios
    — One test per QUALITY.md scenario (1:1 mapping)
    — Named to match: test_scenario_N_memorable_name

Boundaries and Edge Cases
    — One test per defensive pattern from Step 5
    — Targets null guards, try/catch, normalization, fallbacks
```

## Import Patterns

- `sys.path.insert(0, "src/")` then bare imports (`from module import func`)
- Package imports (`from myproject.module import func`)
- Relative imports with conftest.py path manipulation

Whatever pattern the existing tests use, copy it exactly. Do not guess or invent a different pattern.

## Test Setup

Create `quality/conftest.py` defining every fixture. Fixtures in `tests/conftest.py` are NOT available to `quality/test_functional.py`. Preferred: write tests that create data inline using `tmp_path` to eliminate conftest dependency.

**Rule: Every fixture or test helper referenced must be defined.** If a test depends on shared setup that doesn't exist, the test will error during setup (not fail during assertion) — producing broken tests that look like they pass.

### Inline Setup (Preferred)

```python
# Python
def test_config_validation(tmp_path):
    config = {"pipeline": {"name": "Test", "steps": [...]}}
```

**Library version awareness:** Check the project's `requirements.txt` to verify what's available. Use `pytest.importorskip()` for optional dependencies.

**After writing all tests, run the test suite and check for setup errors.** Setup errors (fixture not found, import failures) count as broken tests regardless of how the framework categorizes them.

## Spec-Derived Tests

Walk each spec document section by section. For each section, ask: "What testable requirement does this state?" Then write a test.

Each test should:
1. **Set up** — Load a fixture, create test data, configure the system
2. **Execute** — Call the function, run the pipeline, make the request
3. **Assert specific properties** the spec requires

```python
# Python (pytest)
class TestSpecRequirements:
    def test_requirement_from_spec_section_N(self, fixture):
        """[Req: formal — Design Doc §N] X should produce Y."""
        result = process(fixture)
        assert result.property == expected_value
```

## Cross-Variant Testing

If the project handles multiple input types, cross-variant coverage is where silent bugs hide. Aim for roughly 30% of tests exercising all variants.

```python
# Python (pytest)
@pytest.mark.parametrize("variant", [variant_a, variant_b, variant_c])
def test_feature_works(variant):
    output = process(variant.input)
    assert output.has_expected_property
```

If parametrization doesn't fit, loop explicitly within a single test.

**Which tests should be cross-variant?** Any test verifying a property that *should* hold regardless of input type: entity identity, structural properties, required links, temporal fields, domain-specific semantics.

**After writing all tests, do a cross-variant audit.** Count cross-variant tests divided by total. If below 30%, convert more.

## Anti-Patterns — WRONG vs. RIGHT

These patterns look like tests but don't catch real bugs. Always check your Step 5b schema map before choosing mutation values.

```python
# Python — WRONG: tests the validation mechanism
def test_bad_value_rejected(fixture):
    fixture.field = "invalid"  # Schema rejects this!
    with pytest.raises(ValidationError):
        process(fixture)
    # Tells you nothing about output

# Python — RIGHT: tests the requirement
def test_bad_value_not_in_output(fixture):
    fixture.field = None  # Schema accepts None for Optional
    output = process(fixture)
    assert field_property not in output  # Bad data absent
    assert expected_type in output  # Rest still works
```

## Fitness Scenario Tests

For each scenario in QUALITY.md, write a test. This is a 1:1 mapping:

```python
# Python (pytest)
class TestFitnessScenarios:
    """Tests for fitness-to-purpose scenarios from QUALITY.md."""

    def test_scenario_1_memorable_name(self, fixture):
        """[Req: formal — QUALITY.md Scenario 1] [Name].
        Requirement: [What the code must do].
        """
        result = process(fixture)
        assert condition_that_prevents_the_failure
```

## Boundary and Negative Tests

One test per defensive pattern from Step 5. Use your Step 5b schema map when choosing mutation values. Every mutation must use a value the schema accepts.

```python
# Python (pytest)
class TestBoundariesAndEdgeCases:
    """Tests for boundary conditions, malformed input, error handling."""

    def test_defensive_pattern_name(self, fixture):
        """[Req: inferred — from function_name() guard] guards against X."""
        # Mutate to trigger defensive code path
        # Assert graceful handling
```

Systematic approach:
- **Missing fields** — Optional field absent? Set to None.
- **Wrong types** — Field gets different type? Use schema-valid alternative.
- **Empty values** — Empty list? Empty string? Empty dict?
- **Boundary values** — Zero, negative, maximum, first, last.
- **Cross-module boundaries** — Module A produces unusual but valid output — does B handle it?

If you found 10+ defensive patterns but wrote only 4 boundary tests, go back and write more. Target a 1:1 ratio.
