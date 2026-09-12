---
name: test-conventions
description: Learn and match a repository's existing test style — naming, display names, fixtures and base classes, assertion library, parameterization, structure — so generated tests read as if the team wrote them. Load BEFORE writing or adding any test, spec or test case to a project that already has tests, and whenever the request mentions matching, following or fitting the existing tests, style or conventions.
---

# Learning the repository's test conventions

Generated tests that do not look like the surrounding tests get deleted by reviewers. Before
writing a single test, spend the effort to match the house style. If the project has **any**
existing tests, they outrank every default in `stack-adapters`.

## The survey

Read 2–4 of the largest existing test files (largest = most conventions per read) and record:

| Dimension | What to extract |
|---|---|
| **Location & name** | Mirror directory (`src/test/java/...`) or sibling (`foo.spec.ts`, `test_foo.py`)? Suffix or prefix? |
| **Class/suite name** | `<Unit>Test`, `<Unit>Spec`, `Test<Unit>`, `describe('<Unit>')`? |
| **Method name** | `camelCaseVerbPhrase`, `snake_case_should_x`, `it('does x')`? Do they encode the expectation? |
| **Human label** | Is there a `@DisplayName` / `it(...)` sentence? Present tense or "should"? Sentence case? |
| **Assertion library** | AssertJ vs Hamcrest vs plain JUnit; `expect` vs `assert`; the exact negative-path idiom (`assertThatThrownBy`, `pytest.raises`, `expect(...).rejects`). |
| **Fixture** | A shared abstract base class? A `@BeforeEach`? A pytest fixture? A builder? **Reuse it — do not invent a parallel one.** |
| **Mocking** | Which library, and whether the team prefers real objects over mocks. |
| **Granularity** | One assertion concern per test, or several? Follow the majority. |
| **Parameterization** | How the repo runs one body over many inputs — `@ParameterizedTest`, `parametrize`, table-driven subtests, `it.each`. Use it instead of a loop inside a test. |
| **Comments** | Do tests carry a short comment explaining *why* a non-obvious case exists? Match the density. |
| **Grouping** | Nested classes / `describe` blocks / `// --- section ---` banners? |

## Worked example

Given a suite whose files look like:

```java
class DBSafetyTest extends DBTestBase {
    @Test
    @DisplayName("table rejects identifiers that aren't [a-z][a-z0-9_]*")
    void tableRejectsInjection() {
        assertThatThrownBy(() -> db.table("users; DROP TABLE users--"))
                .isInstanceOf(AppException.class);
    }
}
```

the extracted profile is: JUnit 5, AssertJ, a shared `DBTestBase` giving a fresh in-memory DB per
test, `<Area>Test` class names, terse camelCase method names, a `@DisplayName` sentence carrying
the real specification, `assertThatThrownBy(...).isInstanceOf(...)` for refusals, one concern per
test, and safety cases collected in their own file. Every new test must match that shape exactly.

## Rules

1. **Extend, don't duplicate.** If a test file already covers the unit, add cases to it. Create a
   new file only for a genuinely new area — and prefer a dedicated `<Area>SafetyTest` for the
   adversarial cases so they are easy to review as a group.
2. **Reuse the fixture.** If a base class or fixture exists, extend/use it. Building a second way
   to get a database is how suites rot.
3. **The label is the spec.** Where the project uses display names, write them as a precise
   statement of the rule being enforced — a reviewer should be able to read only the labels and
   know what the unit guarantees.
4. **No new dependency without asking.** If an adversarial case needs a library the project does
   not have (a property-based or container library), say so and ask before touching the build file.
5. **Greenfield fallback.** With no existing tests, take defaults from `stack-adapters`, then state
   the conventions you chose in the report so the team can veto them once rather than per file.
