# TestMate

A Claude Code plugin that acts as an **adversarial test engineer**.

It detects your stack, learns the test conventions already in your repository, then writes tests
that try to *break* your code — injection, authorization bypass, boundaries, concurrency, resource
leaks, locale and dialect variance, and silently wrong answers. It runs them, and triages every
failure as a real bug or a wrong expectation.

The rule that makes it useful:

> **A generated test that fails is a finding until proven otherwise.**
> TestMate never weakens, skips or deletes a test to make a suite green, and never patches your
> source to do it either. It tells you which it is, with evidence.

Works on any language or framework. First-class adapters ship for the JVM (Java / Kotlin / Spring
Boot), Angular, Node / React / TypeScript, Python, Go, Rust and native C/C++; anything else falls
back to convention inference from your existing tests.

## Install

```bash
# in Claude Code
/plugin marketplace add 67696f/test-mate
/plugin install testmate@binwi-tools
```

Or from a local checkout:

```bash
/plugin marketplace add /path/to/test-mate
/plugin install testmate@binwi-tools
```

## Commands

| Command | What it does |
|---|---|
| `/testmate:scan [path]` | Read-only. Stack profile, existing test posture, ranked risk hot-spots, proposed plan. Writes nothing. |
| `/testmate:test [target] [--level]` | The main one. Generate → run → triage → report. Target is the project, a path, a file or `Class#method`. |
| `/testmate:audit [path]` | Read-only vulnerability hunt. Ranked findings report, no test files. |
| `/testmate:harden [report\|path]` | Turns findings into refusal tests that prove each hole. The ones that fail are your confirmed bugs. |
| `/testmate:debug <test\|bug> [--fix]` | Root-cause loop: minimal reproduction, bisect, one hypothesis at a time, causal chain. |
| `/testmate:mutate [path] [--write]` | Mutation testing — does your suite actually catch bugs? Surviving mutants become new tests. |

## Levels

Cumulative. **`high` is the default.**

| Level | Adds |
|---|---|
| `low` | Happy path, null/empty/absent arguments. Smoke. |
| `standard` | Boundaries, every declared error path, collaborator interaction, state invariants, round-trips. |
| **`high`** | The adversarial tier — refusal tests, injection families, authz bypass, concurrency, resource lifecycle, locale/timezone/charset/dialect variance, silent-wrongness hunting. Plus run, triage and report. |
| `max` | Property-based tests, fuzzing, **mutation testing**, real-dependency integration via containers, resource exhaustion, API contract snapshots. |

```
/testmate:test src/main/java/com/acme/db --level max
/testmate:test UserService#deleteById
/testmate:test                              # whole project, level high
```

## What makes the tests different

Most generated suites are happy-path suites: they pass just as well after someone deletes a
validator. TestMate's centrepiece is the **refusal suite** — one file per module in which every
test asserts that a bad input is *rejected*:

```java
@Test
@DisplayName("delete without where is refused to prevent full-table wipe")
void deleteWithoutWhereRefused() {
    assertThatThrownBy(() -> db.table("users").delete())
            .isInstanceOf(UnsafeOperationException.class);
}
```

Alongside it, the highest-value family in the catalogue: **silent wrongness** — a filter that gets
dropped when its argument list is empty, a quote function applied to a whole qualified name instead
of per segment, a conversion that truncates without complaint. A loud failure gets fixed in a day;
a plausible wrong answer ships and corrupts data for a year.

## Configuration

Optional, at `.testmate/config.json` in your project:

```json
{
  "level": "high",
  "roots": [
    { "path": "backend",  "level": "max" },
    { "path": "frontend", "level": "standard" }
  ],
  "exclude": ["**/generated/**", "**/*.pb.go", "vendor/**"],
  "forbidCommands": ["mvn deploy", "npm publish"],
  "reportDir": ".testmate/reports",
  "mutation": { "enabled": true, "threshold": 70 },
  "allowDependencyChanges": false
}
```

`allowDependencyChanges` is `false` by default — TestMate will tell you what a test needs and ask
before touching a build file.

## Guarantees

Every test TestMate writes is:

- **Isolated** — a fresh fixture per test, no ordering dependency;
- **Offline** — no real network, no real cloud, no real SMTP;
- **Credential-free** — never reads a real secret, never points at a production URL;
- **Deterministic** — injected clock, seeded RNG, explicit locale and timezone;
- **Non-destructive** — destructive scenarios run against a throwaway fixture the test created.

And TestMate never edits your source code unless you explicitly ask it to.

## How it works

```
commands/     scan · test · audit · harden · debug · mutate
agents/       testmate-recon      stack + conventions + risk ranking (read-only)
              testmate-adversary  attack-surface model → ranked case list (read-only)
              testmate-author     writes the tests, never the source
              testmate-runner     runs, isolates, triages, reports
skills/       test-strategy       levels, taxonomy, hermeticity rules
              test-conventions    learning and matching your house style
              attack-catalog      vulnerability families → test shapes  ← the core
              failure-triage      BUG / EXPECTATION / FIXTURE / UNDECIDED
              stack-adapters      per-stack idiom, tooling and commands
```

Adding a language is one markdown file in `skills/stack-adapters/references/` — no code change.

## Licence

MIT.
