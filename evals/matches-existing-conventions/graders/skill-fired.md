---
type: llm
weight: 1
---

This grader checks that the plugin actually engaged, rather than the base model happening to guess
the right style unaided.

Passes if the response shows evidence of having consulted TestMate's conventions guidance — for
example it invoked a TestMate skill, or it explicitly reasons about mirroring the repository's
existing conventions (naming, the shared base class, the assertion idiom, display names,
parameterization) as a deliberate step before writing the tests.

Fails if the tests simply appear with no indication that matching the existing style was a
considered step.
