---
max_turns: 14
allowed_tools: [Read, Glob, Grep, Skill]
---

Add tests for a new `Db.like(column, value, LikeMode mode)` method that must reject any value
containing a percent or underscore wildcard. Do not ask me any questions first — if you need a
detail that is not here, state the assumption you are making and write the tests anyway.

Every existing test file in this repository looks like this one:

```java
class DBSafetyTest extends DBTestBase {

    @Test
    @DisplayName("table rejects identifiers that aren't [a-z][a-z0-9_]*")
    void tableRejectsInjection() {
        assertThatThrownBy(() -> db.table("users; DROP TABLE users--"))
                .isInstanceOf(InvalidIdentifierException.class);
    }
}
```

`DBTestBase` provides a `db` field backed by a fresh in-memory database per test. `LikeMode` is an
enum with exactly three values — `CONTAINS`, `STARTS_WITH`, `ENDS_WITH` — and the rejection applies
in all three.

Everything you need is in this message. The working directory is intentionally empty —
there is no repository to open, so answer from the code quoted above rather than looking
for files.
