---
name: stack-adapters
description: Detect a project's language, build tool and test stack, and translate TestMate's abstract test shapes into that stack's idiom — file layout, naming, assertion and refusal syntax, fixtures, parameterization, property-based and mutation tooling, and the commands to run. Load before writing or running tests.
---

# Stack adapters

The attack catalogue defines *what* to test. An adapter defines *how to write and run it here*.

**Existing tests in the repository always outrank an adapter default** — see `test-conventions`.
An adapter is what you use when the project has no precedent.

## Detection

Detect by build manifest first, then confirm with the test tree and lockfiles.

| Signal | Stack | Reference |
|---|---|---|
| `pom.xml`, `build.gradle{,.kts}` | Java / Kotlin / JVM (Spring Boot if the starter is present) | `references/jvm.md` |
| `angular.json` | Angular | `references/angular.md` |
| `package.json` without `angular.json` | Node / React / TypeScript | `references/node.md` |
| `pyproject.toml`, `setup.py`, `requirements.txt` | Python | `references/python.md` |
| `go.mod` | Go | `references/go.md` |
| `Cargo.toml` | Rust | `references/rust.md` |
| `CMakeLists.txt`, `Makefile`, `meson.build`, `configure.ac` | C / C++ | `references/c-native.md` |
| anything else | unsupported | `references/generic.md` |

A repository may match several. Detect **per directory**, not per repository — a `backend/` and a
`frontend/` get different adapters, different levels of the same catalogue, and separate reports.

Record in the recon output: language and version, build tool, test runner, assertion library,
mocking library, whether a coverage tool is configured, whether a property-based or mutation tool
is available, and the exact commands to run one test, one file, and the whole suite.

## What every adapter must supply

1. **Where the test file goes** and what it is named.
2. **The refusal idiom** — how to assert "this call fails with this specific error". The single
   most-used construct in TestMate output.
3. **The fixture idiom** — how to get a fresh, isolated, per-test environment.
4. **The parameterization idiom** — how to run one test body over a set of inputs or targets,
   needed for dialect/locale matrices.
5. **The doubles idiom** — mock, stub, spy, argument capture.
6. **The commands** — run all, run one file, run one test, coverage, mutation.

## Running

Always run what you generate, and prefer the narrowest command that proves the point: one test
while iterating, one file when the file is done, the full suite once at the end to catch
interference. Before reporting, run the full suite **twice** — a test that only passes on a clean
run is leaking state, and that is a finding.

If the build needs a network fetch on first run, say so before starting it rather than hanging.
If the project has no test infrastructure at all, propose the minimal set of dependencies and
**ask before editing the build file**.
