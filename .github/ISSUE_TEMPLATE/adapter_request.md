---
name: Stack adapter request
about: Ask for support for a language or framework that has no adapter
title: 'Adapter: '
labels: adapter
assignees: ''
---

**Language / framework**

**Test runner and assertion library**
What the ecosystem actually uses, and what this project uses if they differ.

**The refusal idiom**
How you assert "this call fails with this specific error" in that stack. This is the single
most-used construct in TestMate's output, so it matters more than anything else here.

**The fixture idiom**
How a test gets a fresh, isolated environment.

**Parameterization**
How you run one test body over many inputs.

**Commands**
Run all, run one file, run one test, coverage. Plus property-based and mutation tooling if any.

**Anything the language gets wrong that other languages do not**
The compiler-can't-catch-it defects worth attacking specifically.
