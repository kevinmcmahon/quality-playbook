# Functional Test Examples — Scala

Reference companion to `functional_tests.md` with all Scala/ScalaTest examples.

Name the test file using ScalaTest conventions: `FunctionalSpec.scala`.

## Structure: Three Test Groups

Organize tests into three logical groups using traits:

```
Spec Requirements
    — One test per testable spec section
    — Each test's documentation cites the spec requirement

Fitness Scenarios
    — One test per QUALITY.md scenario (1:1 mapping)
    — Named to match: "Scenario 1: [Name]" should "prevent [failure mode]"

Boundaries and Edge Cases
    — One test per defensive pattern from Step 5
    — Targets Option handling, pattern match guards, normalization, fallbacks
```

## Import Patterns

- `import com.example.project._` or `import com.example.project.{ClassA, ClassB}`
- SBT project layout: `src/test/scala/` mirrors `src/main/scala/`

Whatever pattern the existing tests use, copy it exactly. Do not guess or invent a different pattern.

## Test Setup

Mix in a trait with `before`/`after` blocks, or use inline data builders. If using SBT, ensure the test file is in the correct source tree.

**Rule: Every fixture or test helper referenced must be defined.** If a test depends on shared setup that doesn't exist, the test will error during setup (not fail during assertion) — producing broken tests that look like they pass.

**Library version awareness:** Check the project's `build.sbt` to verify what's available. Use ScalaTest `assume()` for optional dependencies.

**After writing all tests, run the test suite and check for setup errors.** Setup errors (fixture not found, import failures) count as broken tests regardless of how the framework categorizes them.

## Spec-Derived Tests

Walk each spec document section by section. For each section, ask: "What testable requirement does this state?" Then write a test.

Each test should:
1. **Set up** — Load a fixture, create test data, configure the system
2. **Execute** — Call the function, run the pipeline, make the request
3. **Assert specific properties** the spec requires

```scala
// Scala (ScalaTest)
class SpecRequirements extends FlatSpec with Matchers {
  // [Req: formal — Design Doc §N] X should produce Y
  "Section N requirement" should "produce Y from X" in {
    val result = process(fixture)
    result.property should equal (expectedValue)
  }
}
```

## Cross-Variant Testing

If the project handles multiple input types, cross-variant coverage is where silent bugs hide. Aim for roughly 30% of tests exercising all variants.

```scala
// Scala (ScalaTest)
Seq(variantA, variantB, variantC).foreach { variant =>
  it should s"work for ${variant.name}" in {
    val output = process(variant.input)
    output should have ('expectedProperty (true))
  }
}
```

If iteration doesn't fit, write separate test cases.

**Which tests should be cross-variant?** Any test verifying a property that *should* hold regardless of input type: entity identity, structural properties, required links, temporal fields, domain-specific semantics.

**After writing all tests, do a cross-variant audit.** Count cross-variant tests divided by total. If below 30%, convert more.

## Anti-Patterns — WRONG vs. RIGHT

These patterns look like tests but don't catch real bugs. Always check your Step 5b schema map before choosing mutation values.

```scala
// Scala — WRONG: tests the decoder, not the requirement
"bad value" should "be rejected" in {
  val input = fixture.copy(field = "invalid")  // Circe decoder fails!
  a [DecodingFailure] should be thrownBy process(input)
  // Tells you nothing about output
}

// Scala — RIGHT: tests the requirement
"missing optional field" should "not produce bad output" in {
  val input = fixture.copy(field = None)  // Option[String] accepts None
  val output = process(input)
  output should not contain badProperty  // Bad data absent
  output should contain (expectedType)   // Rest still works
}
```

## Fitness Scenario Tests

For each scenario in QUALITY.md, write a test. This is a 1:1 mapping:

```scala
// Scala (ScalaTest)
class FitnessScenarios extends FlatSpec with Matchers {
  // [Req: formal — QUALITY.md Scenario 1]
  "Scenario 1: [Name]" should "prevent [failure mode]" in {
    val result = process(fixture)
    result.property should equal (expectedValue)
  }
}
```

## Boundary and Negative Tests

One test per defensive pattern from Step 5. Use your Step 5b schema map when choosing mutation values. Every mutation must use a value the schema accepts.

```scala
// Scala (ScalaTest)
class BoundariesAndEdgeCases extends FlatSpec with Matchers {
  // [Req: inferred — from methodName() guard]
  "defensive pattern: methodName()" should "guard against X" in {
    val input = fixture.copy(field = None)  // Trigger defensive code path
    val result = process(input)
    result should equal (defined)
    result.get should not contain badData
  }
}
```

Systematic approach:
- **Missing fields** — Optional field absent? Set to `None`.
- **Wrong types** — Field gets different type? Use schema-valid alternative.
- **Empty values** — Empty `Seq`? Empty `String`? Empty `Map`?
- **Boundary values** — Zero, negative, maximum, first, last.
- **Cross-module boundaries** — Module A produces unusual but valid output — does B handle it?

If you found 10+ defensive patterns but wrote only 4 boundary tests, go back and write more. Target a 1:1 ratio.
