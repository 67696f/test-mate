# Silent wrongness

The highest-value family. A loud failure gets fixed in a day; a plausible wrong answer ships and
corrupts data for a year. These are the cases worth a dedicated test file — the reference suite
that inspired TestMate names its file after exactly this idea: *cases that previously failed
silently or only on a specific dialect or locale*.

## How to hunt

Read the implementation looking for places where a bad input produces **an answer** rather than
**an error**. Each one is a candidate.

### 1. The silently dropped constraint

A filter, predicate, scope or condition that disappears when its argument is empty, null, or
malformed — turning a narrow query into a broad one.

```
give the guard an empty collection / null / blank string
assert it is REFUSED
```

Never accept "it just returns everything" as intended unless the code says so explicitly. A dropped
`WHERE` on a delete is data loss; a dropped tenant scope is a breach.

### 2. The over-broad transformation

A function applied to a whole compound value when it should be applied per part: quoting
`schema.table` as one identifier instead of quoting each segment; escaping a full URL instead of
each parameter; trimming a whole CSV line instead of each field.

```
feed a compound value
assert the output is composed correctly, part by part
assert the naive whole-string form does NOT appear in the output
```

### 3. The lossy coercion

A conversion that truncates, rounds or reinterprets without complaint: a wide integer into a narrow
one, a timestamp into a date, a decimal into a float, a string into an enum falling back to a
default, a missing JSON field becoming a zero value.

```
feed a value that cannot survive the conversion
assert refusal or exact preservation — never a quiet approximation
```

Pay special attention to a default that is indistinguishable from a real value: a missing boolean
becoming `false`, a missing count becoming `0`, an unknown enum becoming the first constant.

### 4. The swallowed error

`catch` blocks that log and continue, return `null`, return an empty collection, or return a
default. Each one converts a failure into a plausible answer.

```
make the inner call fail
assert the caller can tell the difference between "failed" and "no results"
```

### 5. The wrong-but-parseable result

Off-by-one pagination that quietly skips a row, a join that duplicates rows so a sum is inflated,
an aggregate computed before a filter is applied, a `count` that ignores the scope the `list`
applies. Test the aggregate and the listing **against the same fixture** and assert they agree.

### 6. The unreachable guard

A validation that is present but bypassed on some path — a second constructor, a builder method, a
deserialization entry point, a copy/clone, an admin code path. Enumerate every way to construct or
mutate the object and assert the guard holds on all of them.

### 7. The asymmetric round-trip

`parse(render(x))` that is not `x`, an encode/decode pair that disagree on an edge case, an
equality that disagrees with a hash, a comparator that is not transitive. These are ideal
property-based tests at level `max`; at level `high` write the specific known-asymmetric cases.

## Writing them up

Silent-wrongness findings are usually **medium or high severity even when they are not security
issues**, because nobody is watching for them. In the report, always state the concrete wrong
answer the caller receives — "returns 12 rows where 3 were requested" lands; "incorrect behaviour"
does not.
