---
type: llm
weight: 0.05
arm: with-only
---

This grader checks that the plugin actually engaged, rather than the base model happening to guess
the right style unaided.

This is a diagnostic, not a quality bar — the tests are conformant or they are not, and `criteria`
judges that. At equal weight it made the case flaky: the skill fires about five runs in six, and at
CI's three-run default two misses dropped the case to 0.67, turning the suite red for a reason that
says nothing about the plugin's output.

Two settings keep it out of the way, because one of them is not enough:

- `arm: with-only` drops it from scoring entirely — but **only under `--ablation with-without`**.
  The runner sets `with_only` only when a run belongs to a named arm, so under `--ablation none`
  (what CI uses, to avoid paying for a second no-plugin arm) the flag is silently inert.
- `weight: 0.05` is what actually holds under `--ablation none`. A miss costs 0.05/1.05 of the run,
  so a failure here reads 0.952 — visible in the report, nowhere near the 0.8 gate — while a
  `criteria` failure still collapses the score to 0.048. Weight must be positive, so 0 is not
  available.

Read it in the report; do not gate on it.

Passes if the response shows evidence of having consulted TestMate's conventions guidance — for
example it invoked a TestMate skill, or it explicitly reasons about mirroring the repository's
existing conventions (naming, the shared base class, the assertion idiom, display names,
parameterization) as a deliberate step before writing the tests.

Fails if the tests simply appear with no indication that matching the existing style was a
considered step.
