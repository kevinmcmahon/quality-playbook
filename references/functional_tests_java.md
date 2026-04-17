# Functional Test Examples — Java

Reference companion to `functional_tests.md` with all Java/JUnit 5 examples.

Name the test file using JUnit conventions: `FunctionalTest.java`.

## Structure: Three Test Groups

Organize tests into three logical groups using classes:

```
Spec Requirements
    — One test per testable spec section
    — Each test's documentation cites the spec requirement

Fitness Scenarios
    — One test per QUALITY.md scenario (1:1 mapping)
    — Named to match: testScenario1MemorableName (or equivalent convention)

Boundaries and Edge Cases
    — One test per defensive pattern from Step 5
    — Targets null guards, try/catch, normalization, fallbacks
```

## Import Patterns

- `import com.example.project.Module;` matching the package structure
- Test source root must mirror main source root

Whatever pattern the existing tests use, copy it exactly. Do not guess or invent a different pattern.

## Test Setup

Use `@BeforeEach`/`@BeforeAll` methods in the test class, or create a shared `TestFixtures` utility class in the same package.

**Rule: Every fixture or test helper referenced must be defined.** If a test depends on shared setup that doesn't exist, the test will error during setup (not fail during assertion) — producing broken tests that look like they pass.

### Inline Setup (Preferred)

```java
// Java
@Test
void testConfigValidation(@TempDir Path tempDir) {
    var config = Map.of("pipeline", Map.of("name", "Test"));
}
```

**Library version awareness:** Check the project's `pom.xml` or `build.gradle` to verify what's available. Use JUnit `Assumptions.assumeTrue()` for optional dependencies.

**After writing all tests, run the test suite and check for setup errors.** Setup errors (fixture not found, import failures) count as broken tests regardless of how the framework categorizes them.

## Spec-Derived Tests

Walk each spec document section by section. For each section, ask: "What testable requirement does this state?" Then write a test.

Each test should:
1. **Set up** — Load a fixture, create test data, configure the system
2. **Execute** — Call the function, run the pipeline, make the request
3. **Assert specific properties** the spec requires

```java
// Java (JUnit 5)
class SpecRequirementsTest {
    @Test
    @DisplayName("[Req: formal — Design Doc §N] X should produce Y")
    void testRequirementFromSpecSectionN() {
        var result = process(fixture);
        assertEquals(expectedValue, result.getProperty());
    }
}
```

## Cross-Variant Testing

If the project handles multiple input types, cross-variant coverage is where silent bugs hide. Aim for roughly 30% of tests exercising all variants.

```java
// Java (JUnit 5)
@ParameterizedTest
@MethodSource("variantProvider")
void testFeatureWorks(Variant variant) {
    var output = process(variant.getInput());
    assertTrue(output.hasExpectedProperty());
}
```

If parametrization doesn't fit, loop explicitly within a single test.

**Which tests should be cross-variant?** Any test verifying a property that *should* hold regardless of input type: entity identity, structural properties, required links, temporal fields, domain-specific semantics.

**After writing all tests, do a cross-variant audit.** Count cross-variant tests divided by total. If below 30%, convert more.

## Anti-Patterns — WRONG vs. RIGHT

These patterns look like tests but don't catch real bugs. Always check your Step 5b schema map before choosing mutation values.

```java
// Java — WRONG: tests the validation mechanism
@Test
void testBadValueRejected() {
    fixture.setField("invalid");  // Schema rejects this!
    assertThrows(ValidationException.class, () -> process(fixture));
    // Tells you nothing about output
}

// Java — RIGHT: tests the requirement
@Test
void testBadValueNotInOutput() {
    fixture.setField(null);  // Schema accepts null for Optional
    var output = process(fixture);
    assertFalse(output.contains(badProperty));  // Bad data absent
    assertTrue(output.contains(expectedType));   // Rest still works
}
```

## Fitness Scenario Tests

For each scenario in QUALITY.md, write a test. This is a 1:1 mapping:

```java
// Java (JUnit 5)
class FitnessScenariosTest {
    @Test
    @DisplayName("[Req: formal — QUALITY.md Scenario 1] [Name]")
    void testScenario1MemorableName() {
        var result = process(fixture);
        assertTrue(conditionThatPreventsFailure(result));
    }
}
```

## Boundary and Negative Tests

One test per defensive pattern from Step 5. Use your Step 5b schema map when choosing mutation values. Every mutation must use a value the schema accepts.

```java
// Java (JUnit 5)
class BoundariesAndEdgeCasesTest {
    @Test
    @DisplayName("[Req: inferred — from methodName() guard] guards against X")
    void testDefensivePatternName() {
        fixture.setField(null);  // Trigger defensive code path
        var result = process(fixture);
        assertNotNull(result);  // Assert graceful handling
        assertFalse(result.containsBadData());
    }
}
```

Systematic approach:
- **Missing fields** — Optional field absent? Set to null.
- **Wrong types** — Field gets different type? Use schema-valid alternative.
- **Empty values** — Empty list? Empty string? Empty map?
- **Boundary values** — Zero, negative, maximum, first, last.
- **Cross-module boundaries** — Module A produces unusual but valid output — does B handle it?

If you found 10+ defensive patterns but wrote only 4 boundary tests, go back and write more. Target a 1:1 ratio.
