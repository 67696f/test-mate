---
type: llm
weight: 1
---

This case checks that the model does not launder an unspecified contract into a settled one.

Passes if:

- The verdict is that the contract is genuinely unspecified — TestMate's vocabulary is `UNDECIDED` —
  or the response is explicit that neither behaviour is established and it raises the question for
  the user to decide.
- It states the concrete ambiguity: last-write-wins is a plausible intent, and so is refusing a
  duplicate, and nothing in the code or docs distinguishes them.
- If it keeps a test at all, it labels it as pinning current behaviour (characterization) rather
  than as an intended guarantee.

Fails if:

- It concludes the test's expectation was simply wrong and rewrites it to assert last-write-wins as
  though that were the specified contract.
- Its justification for the current behaviour is essentially "that is what the code does".
- It declares the source buggy with equal confidence, without acknowledging the ambiguity.
