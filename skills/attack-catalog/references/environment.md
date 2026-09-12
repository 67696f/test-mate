# Environment variance

Bugs that pass on the developer's machine and fail in production, or on one customer's tenant.
They are trivial to test once you know to look.

## Locale

- **Case conversion is locale-sensitive.** Uppercasing a lowercase `i` in Turkish produces a
  dotted capital, so an identifier normalized with a default-locale `toUpperCase`/`toLowerCase`
  stops matching. Any case conversion used for a *protocol* purpose — an SQL keyword, an HTTP
  header name, an enum lookup, a file extension — must pass an explicit invariant/root locale.
  **Test it by running the case-conversion path under a Turkish locale.**
- Number formatting: a decimal comma vs. point, grouping separators, and a negative sign that is
  not the ASCII hyphen. Assert that machine-facing output uses an invariant format.
- Collation: sort order differs by locale. Assert which order is guaranteed, or that none is.
- Date formatting and parsing: month names, weekday-of-week-start, and non-Gregorian calendars.

## Timezone and time

- Run the time-dependent path under at least: UTC, a half-hour offset zone, and a zone with DST.
- DST transitions: a local time that does not exist (spring forward) and one that occurs twice
  (fall back). Assert the unit does not throw and does not silently pick the wrong instant.
- Midnight and end-of-day boundaries for anything that buckets by day.
- Assert the clock is injected. A unit that reads the system clock directly cannot be tested for
  any of the above, and that is itself the finding.
- Storage: assert instants are stored with an offset or in UTC, never as a naive local time.

## Character encoding

- Round-trip a string containing non-ASCII, emoji and combining marks through every serialization
  boundary: the database, JSON, the wire, the filesystem, the log.
- Assert an explicit charset is specified everywhere one can be — reading a file, encoding to
  bytes, setting a content type. A platform-default charset is a latent bug.
- Byte-order marks at the start of an input file.
- Line endings: input with CRLF, LF and a mix; assert the parser handles all three.

## Dialect and target variance

If the unit renders to more than one target — an SQL dialect, a database vendor, a browser, an OS,
a protocol version, an API version — then **every rendering test must run against every target**.
Use a parameterized test over the target set so adding a new target automatically extends coverage.

Attack the differences specifically: identifier quoting characters, string concatenation syntax,
pagination syntax, boolean literals, the returning/output clause, case sensitivity of identifiers,
and reserved words that differ between vendors.

## Filesystem and platform

- Path separators, case-insensitive filesystems (two names differing only in case), maximum path
  length, and names that are reserved on Windows.
- File ordering from a directory listing is not guaranteed; assert sorting if order matters.
- Assert temp files are created with restrictive permissions and cleaned up.
