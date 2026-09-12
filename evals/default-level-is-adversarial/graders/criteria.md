---
type: llm
weight: 1
---

With no level given, TestMate's default is `high`, which is the adversarial tier. The response must
behave accordingly.

Passes if ALL of:

- It produces refusal / negative tests, not only happy-path tests.
- It specifically attacks the string concatenation as SQL injection, with at least one CONCRETE
  attack input (something of the shape `users; DROP TABLE users--`, `1 OR 1=1`, or an injected
  ORDER BY / direction payload) — a vague mention of "test for injection" is not enough.
- It covers more than one injectable position: the table or column identifier AND the sort
  direction or the LIKE term.
- It notes that parameter binding does not protect identifiers or sort direction, so an allowlist is
  what is being tested.

Strong signal (not required): it flags the wildcard characters in the LIKE term, or treats the
function as unsafe by construction and says so.

Fails if:

- The tests are only happy-path and boundary cases with no adversarial input.
- It asks the user which level to use instead of proceeding at the default.
