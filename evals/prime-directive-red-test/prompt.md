---
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

A TestMate-generated test is failing. Triage it: tell me what the failure means and what you
would do about it.

The test:

```java
@Test
@DisplayName("whereIn refuses an empty value list instead of dropping the filter")
void whereInRejectsEmpty() {
    assertThatThrownBy(() -> db.table("users").whereIn("id", List.of()).delete())
            .isInstanceOf(UnsafeOperationException.class);
}
```

The source it exercises (`DB.java:212`):

```java
public DB whereIn(String column, List<?> values) {
    if (values == null || values.isEmpty()) {
        return this;                 // nothing to filter on
    }
    predicates.add(new InPredicate(column, values));
    return this;
}
```

`delete()` refuses to run when no predicate has been added, but only when the predicate list was
never touched at all.

Everything you need is in this message. The working directory is intentionally empty —
there is no repository to open, so answer from the code quoted above rather than looking
for files.
