# JVM — Java / Kotlin / Spring Boot

## Defaults

| | |
|---|---|
| Runner | JUnit 5 (Jupiter) |
| Assertions | AssertJ (`assertThat`) — prefer over Hamcrest and bare JUnit asserts |
| Mocking | Mockito (`mock`, `when`, `verify`, `ArgumentCaptor`) |
| Location | `src/test/java/<same package>/<Unit>Test.java`; resources in `src/test/resources` |
| Naming | class `<Unit>Test` or `<Area>Test`; method a terse camelCase phrase; a `@DisplayName` sentence carrying the real specification |
| Safety suite | `<Area>SafetyTest` — all refusal cases together |

## Refusal idiom

```java
assertThatThrownBy(() -> db.table("users; DROP TABLE users--"))
        .isInstanceOf(InvalidIdentifierException.class)
        .hasMessageContaining("identifier");
```

Assert the **specific** exception type. `isInstanceOf(RuntimeException.class)` proves nothing —
a `NullPointerException` would satisfy it. When only a base type is available, additionally assert
on the message so a different failure cannot pass.

For "nothing happened" assertions after a refusal, verify the collaborator was never called:

```java
verifyNoInteractions(jdbc);
```

## Fixture idiom

A shared abstract base with `@BeforeEach`, giving each test a private environment:

```java
abstract class DBTestBase {
    protected DB db;

    @BeforeEach
    void initDatabase() {
        String url = "jdbc:h2:mem:test_" + UUID.randomUUID().toString().replace("-", "_")
                + ";MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1";
        DataSource ds = new SimpleDriverDataSource(new org.h2.Driver(), url, "sa", "");
        DatabasePopulatorUtils.execute(new ResourceDatabasePopulator(
                new ClassPathResource("schema.sql"), new ClassPathResource("seed.sql")), ds);
        db = new DB(new NamedParameterJdbcTemplate(ds));
    }
}
```

The UUID in the database name is what makes tests independent of execution order. Reuse an existing
base class if the project has one; never add a second.

## Parameterization — dialect and locale matrices

```java
@ParameterizedTest
@MethodSource("dialects")
void quotesIdentifiersPerDialect(Dialect dialect, String expected) { ... }

static Stream<Arguments> dialects() {
    return Stream.of(
        arguments(PostgresDialect.INSTANCE, "\"users\""),
        arguments(MysqlDialect.INSTANCE,    "`users`"));
}
```

Locale sensitivity — the Turkish-i case:

```java
@Test
void keywordCasingIsLocaleIndependent() {
    Locale original = Locale.getDefault();
    try {
        Locale.setDefault(Locale.of("tr", "TR"));   // new Locale(..) before Java 19
        assertThat(renderer.render(query)).contains("LIMIT");
    } finally {
        Locale.setDefault(original);
    }
}
```

## Spring Boot

- **Slice over context.** `@WebMvcTest` for controllers, `@DataJpaTest` / `@JdbcTest` for
  persistence, plain constructor injection for services. Reserve `@SpringBootTest` for genuine
  wiring tests; it is slow and hides missing-bean bugs.
- Auto-configuration: assert with `ApplicationContextRunner` — that the bean is created, that a
  user-supplied bean wins (`@ConditionalOnMissingBean`), that the feature disables cleanly via
  property, and that ordering relative to neighbouring auto-configurations is correct.
- Security: `@WithMockUser` / `@WithAnonymousUser` for the authz matrix in `attack-catalog`.
  Always include an anonymous case and a wrong-tenant case.
- Web layer: `MockMvc` for status, body and headers. Assert error responses do not echo internals.
- Transactions: `@Transactional` on a test rolls back and can hide commit-time failures — for
  persistence behaviour, prefer an explicit clean fixture over test-managed rollback.

## Integration with real dependencies (level max)

Testcontainers:

```java
@Testcontainers
class RepositoryIT {
    @Container
    static PostgreSQLContainer<?> db = new PostgreSQLContainer<>("postgres:16-alpine");
}
```

Name them `*IT` and bind them to `maven-failsafe-plugin` so the fast suite stays fast.

## Property-based and mutation (level max)

- Property-based: **jqwik** — `@Property void roundTrips(@ForAll String s)`.
- Mutation: **PIT** (`pitest-maven`). Run with
  `mvn org.pitest:pitest-maven:mutationCoverage -DtargetClasses=com.x.*`.
  Report surviving mutants as suite gaps and write a test for each.

## Commands

| | Maven | Gradle |
|---|---|---|
| All | `mvn -q test` | `./gradlew test` |
| One class | `mvn -q -Dtest=DBSafetyTest test` | `./gradlew test --tests '*DBSafetyTest'` |
| One method | `mvn -q -Dtest=DBSafetyTest#tableRejectsInjection test` | `./gradlew test --tests '*DBSafetyTest.tableRejectsInjection'` |
| Coverage | `mvn -q verify` (JaCoCo bound to `verify`) | `./gradlew jacocoTestReport` |
| Integration | `mvn -q verify` (Failsafe) | `./gradlew integrationTest` |

Add `-o` to Maven for offline runs. Surefire failure detail lives in
`target/surefire-reports/*.txt` — read it rather than guessing from the console summary.
