# Injection families

Injection exists wherever a value crosses from one interpreter into another. Find the crossings
first, then attack each one.

## Finding the crossings

Grep the unit for string construction that feeds an engine: concatenation or interpolation into
SQL, a shell command, a file path, a URL, an HTML/template fragment, an HTTP header, a log line, a
serialized payload, a regex, an LDAP or XPath filter, a JSON/YAML document.

Parameter binding protects **values**. It does **not** protect identifiers, operators, sort
directions, table/column names, `LIKE` patterns, or anything structural. Those need an allowlist —
and the allowlist is what you attack.

## SQL

| Shape | Input | Assert |
|---|---|---|
| Identifier smuggling | `users; DROP TABLE users--`, `users"--`, a backtick-quoted name, as table/column/alias | refused with the specific validation error |
| Case and unicode bypass of an allowlist | `Users`, `USERS`, a fullwidth-character homoglyph, a name with a NUL escape | refused — the allowlist is anchored and ASCII |
| Operator injection | `"; DELETE FROM users WHERE 1=1 --"` as the comparison operator | refused; only a fixed operator set is accepted |
| Order/direction injection | `id; DROP ...`, `id DESC, (SELECT ...)` as an order clause | refused |
| `LIKE` wildcard smuggling | a value containing a percent or underscore where the caller meant a literal | either refused or escaped — assert which, and that the other is impossible |
| Raw-expression escape hatch | a raw fragment with a bind that is missing, extra, or misspelled | refused before reaching the driver |
| Numeric-as-string | `1 OR 1=1` where a number is expected | refused, not coerced |
| Comment and stacked statements | a double dash, a block-comment opener, or a semicolon anywhere in a structural position | refused |

Also assert the **safe** counterpart: a value containing a quote or a semicolon passes through
untouched as a bound parameter and matches literally. A validator that rejects legitimate data is
also a bug.

## Unguarded mutation

Not injection, but it lives in the same safety suite and is the same class of catastrophe.

- `DELETE` or `UPDATE` issued with no `WHERE` clause — assert it is refused, not executed.
- An update that targets the primary key, a tenant discriminator, or an audit column.
- A mutation combined with a clause the engine will ignore (`LIMIT`, `ORDER BY`, a join) so the
  caller believes it is narrower than it is — assert refusal rather than silent widening.
- A filter built from an empty collection: assert it is refused, never dropped. A dropped filter
  turns "delete these three rows" into "delete everything".

## Command execution

- Metacharacters in an argument: a semicolon followed by a destructive command, command
  substitution in either syntax, a pipe, a logical AND, a newline, and a leading dash that turns a
  filename into a flag.
- Assert the implementation passes an argument **vector**, never a shell string. A test that
  proves no shell is spawned is worth more than ten tests of escaping.
- Environment inheritance: assert the child does not receive secrets it does not need.

## Path traversal

- Parent-directory sequences in both separator styles, an absolute path where a relative one is
  expected, a symlink pointing outside the root, percent-encoded traversal if any URL-decoding
  happens, and NUL-byte truncation of an extension check.
- Assert the check is done on the **canonicalized, resolved** path against a root, not on the raw
  string. Test that a legitimate nested path still works.
- Upload/filename handling: a single dot, a double dot, an empty name, a name that is only an
  extension, a name longer than the filesystem limit, a name containing a separator.

## Template, markup and script

- A value containing a script tag, an attribute-breaking payload with an event handler, or a
  template expression in either the double-brace or dollar-brace syntax.
- Assert output is **encoded for its context** — HTML body, attribute, URL parameter and JS string
  need different encodings; one escape function for all four is a bug. Write one test per context.
- Assert any "trusted/raw HTML" bypass is unreachable from caller-supplied data.

## Headers, logs and protocols

- Carriage return and line feed in any value that becomes an HTTP header or a log line.
- Assert log output for a field containing a newline cannot forge a second log record.
- Assert redirect targets are validated against an allowlist. The classic bypasses of a naive
  "starts with a slash" check are a protocol-relative double slash, a scheme with no slashes, and a
  slash followed by a backslash.

## Deserialization and parsers

- Unexpected polymorphic type in the payload; assert type resolution is restricted to an allowlist.
- XML: external entity resolution and exponential entity expansion — assert DTDs and external
  entities are disabled.
- Zip/archive: entry names containing parent-directory sequences (zip-slip), and an entry whose
  declared size is absurd.
- JSON/YAML: duplicate keys, deeply nested structures, very large numbers, and — in JavaScript —
  prototype-polluting keys such as `__proto__` and `constructor`.

## Regex

- A caller-supplied pattern at all: assert it is not accepted, or is compiled with a limit.
- Catastrophic backtracking against internal patterns: feed the pathological input and assert the
  call completes inside a time bound.
