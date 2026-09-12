---
max_turns: 14
allowed_tools: [Read, Glob, Grep, Skill]
---

Write tests for this function. Do not ask me any questions first.

```java
public List<Row> search(String table, String column, String term, String direction) {
    String sql = "SELECT * FROM " + table
               + " WHERE " + column + " LIKE '%" + term + "%'"
               + " ORDER BY " + column + " " + direction;
    return jdbc.query(sql, rowMapper);
}
```

Everything you need is in this message. The working directory is intentionally empty —
there is no repository to open, so answer from the code quoted above rather than looking
for files.
