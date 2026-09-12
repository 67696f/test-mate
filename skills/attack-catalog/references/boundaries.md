# Boundaries, numbers and size

The cheapest bugs to find and the most common. Be systematic rather than imaginative.

## For every numeric parameter

Test: `0`, `1`, `-1`, the minimum and maximum of the declared type, minimum minus one and maximum
plus one where expressible, and the value just inside and just outside any documented range.

- **Negative where non-negative is meant.** A negative page size, limit, offset, count, quantity or
  index. Assert refusal, not silent clamping — silent clamping hides caller bugs.
- **Overflow.** Addition, multiplication and array-size computation at the type's limit. In
  languages where overflow wraps silently, this is a correctness bug; assert the guard.
- **Precision.** Money in a binary floating type is a finding on its own. Assert exact arithmetic
  on a decimal type, and test a value with more fractional digits than the scale allows —
  rounding must be explicit and documented, never incidental.
- **Division and modulo by zero**, and by a value that becomes zero after rounding.
- **Parsing.** A number with leading zeros, a leading plus, underscores, whitespace, a locale
  decimal comma, scientific notation, and a value one digit beyond the type's range.

## For every collection or size parameter

- Empty, one element, exactly the boundary size, boundary plus one.
- **Empty means empty.** The single most dangerous default: an empty filter list that is silently
  dropped rather than refused. Assert refusal. Same for an empty set of columns, an empty batch,
  an empty `IN` clause.
- Duplicates, `null`/`None` elements, a collection containing itself (cycles), and a mixed-type
  collection where the language allows it.
- Very large: enough elements to exceed any driver, protocol or database limit on parameter count.
  Assert either a clean refusal or correct chunking — never a truncated silent success.
- Order: assert whether order is guaranteed. If it is not, the test must not depend on it; if it
  is, test that it survives the operation.

## For every string parameter

- Empty, whitespace only, leading/trailing whitespace, a single character.
- Very long — beyond the column width, beyond the protocol limit.
- Unicode: characters outside the basic plane (emoji), combining marks, right-to-left marks,
  zero-width characters, and two visually identical strings with different normalization forms.
  Assert whether comparison normalizes; either answer is fine if it is intentional and tested.
- Length measured in code units vs. code points vs. grapheme clusters — a truncation that splits a
  surrogate pair or a combining sequence is a bug.
- `null` vs. empty vs. absent: three distinct states. Assert the unit distinguishes them, or
  documents that it does not.

## Off-by-one hot spots

Pagination (page 0 vs. page 1, last page, page beyond the end), ranges (inclusive vs. exclusive
ends, asserted at both ends), retry counts (does "3 retries" mean 3 or 4 attempts?), slicing, and
any loop with a manually written index bound.

## Dates and durations

Leap day, leap second, month-end arithmetic (Jan 31 plus one month), a duration of zero, a negative
duration, a range whose end precedes its start, and the epoch boundary. See `environment.md` for
timezone and DST cases.
