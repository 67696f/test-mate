---
type: llm
weight: 1
---

There is no shipped adapter for Elixir and no precedent in the repository, so the model must derive
its conventions rather than invent them, and must not silently install testing infrastructure.

Passes if ALL of:

- It gives an actual plan rather than refusing to proceed without the source.
- It says plainly that there is no existing test precedent in the repository to learn from.
- It would look for precedent elsewhere before choosing anything — a CI workflow, a mix alias, a
  Makefile target, or the ecosystem's own convention.
- It names the ecosystem's real convention (ExUnit, a `test/` directory, `*_test.exs` files) rather
  than transplanting an idiom from another language.
- It would ASK before adding a dependency or creating test infrastructure, rather than editing
  `mix.exs` or scaffolding a test tree unprompted.

Strong signal (not required): it notes that the language-independent test shapes — refusal tests,
boundary sweeps, resource lifecycle, injection — still apply even with no adapter for the language;
or it states that the conventions it adopts are assumptions open to correction.

Fails if it would edit `mix.exs` unprompted, presents an invented convention with no flag that it
was a choice, or declines to plan at all.
