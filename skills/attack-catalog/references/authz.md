# Authorization and identity

Authorization defects are rarely missing checks; they are checks that are present but bypassable,
applied to the wrong object, or applied at the wrong layer.

## Test shapes

| Shape | Setup | Assert |
|---|---|---|
| **No principal** | call with a null/absent/anonymous identity | refused — never silently treated as a default or system user |
| **Wrong principal (IDOR)** | user A requests user B's object by id | refused, and the response does not reveal whether B's object exists |
| **Horizontal escalation** | same role, different tenant/owner | refused; assert on a multi-tenant fixture where both rows actually exist |
| **Vertical escalation** | lower role calls a higher-privilege operation | refused |
| **Check/act mismatch** | authorize object X, then mutate object Y in the same call via a nested id in the body | refused — the object acted on is the object authorized |
| **Mass assignment** | request body carries `role`, `isAdmin`, `ownerId`, `id` | those fields are ignored or refused, never bound |
| **Layer bypass** | invoke the service or repository directly, bypassing the controller guard | either refused at the inner layer too, or documented as internal-only and provably unreachable |
| **Filter vs. count** | a list endpoint scoped to a tenant | pagination totals, aggregates and counts are scoped too — a leaking total is a real leak |
| **Token edge cases** | expired, not-yet-valid, wrong audience, wrong issuer, unsigned algorithm, valid signature but revoked | each refused, with a distinct reason |
| **Enumeration** | valid vs. invalid identifier | timing and message do not distinguish "not found" from "not yours" |
| **Error-path leakage** | trigger an internal failure | the message and stack contain no query text, no path, no secret, no other user's data |

## Also assert the positive

For every refusal test, include one test proving the *legitimate* caller succeeds on the same
operation. A check that refuses everyone passes every refusal test and is still broken.

## Secrets

- No credential, token or key appears in a log, an exception message, a `toString`, a serialized
  DTO, or a debug endpoint. Assert by capturing the output and searching for the known value.
- A value read from configuration is not echoed back by any read endpoint.
- Assert that a failed authentication does not log the attempted password.
