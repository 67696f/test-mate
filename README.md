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
Boot), Next.js, Angular, Node / React / TypeScript, Python, Go, Rust and native C/C++; anything
else falls back to convention inference from your existing tests.

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
| `/testmate:test [target] [--level] [--dry-run]` | The main one. Generate → run → triage → report. Target is the project, a path, a file or `Class#method`. `--dry-run` designs the cases and shows them without writing anything. |
| `/testmate:audit [path] [--families ...]` | Read-only vulnerability hunt. Ranked findings report, no test files. `--families` narrows to e.g. `injection,authz`. |
| `/testmate:harden [report\|path]` | Turns findings into refusal tests that prove each hole. The ones that fail are your confirmed bugs. |
| `/testmate:debug <test\|bug> [--fix]` | Root-cause loop: minimal reproduction, bisect, one hypothesis at a time, causal chain. `--fix` permits a patch once the cause is proven. |
| `/testmate:mutate [path] [--write] [--threshold N]` | Mutation testing — does your suite actually catch bugs? Surviving mutants become new tests. `--threshold` fails below N%. |

`--dry-run` is the one to reach for on a first run against an unfamiliar codebase: it shows you every
case TestMate would write, and touches nothing.

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

Every command loads the `testmate-config` skill before doing anything else, and the settings are
obligations rather than hints:

- **`forbidCommands`** is checked before every shell command, in the commands and in every agent
  that can run one. A match is not run, is reported, and is not worked around with an equivalent
  command that evades the pattern.
- **`exclude`** filters targets during selection, ranking and writing. An excluded path named
  explicitly gets a question, not silent obedience either way.
- **`reportDir`** is the only place reports go; no path is hardcoded.
- **`allowDependencyChanges`** is `false` by default — TestMate names the dependency a test would
  need, shows the snippet, and asks before touching a build file.
- **`mutation.enabled: false`** stops `/testmate:mutate` outright.

A config file that exists but does not parse stops the run. It is never treated as absent — a
malformed safety config must not silently become no safety config. Runs that used a config say
which settings actually changed behaviour.

## Guarantees

Every test TestMate writes is:

- **Isolated** — a fresh fixture per test, no ordering dependency;
- **Offline** — no real network, no real cloud, no real SMTP;
- **Credential-free** — never reads a real secret, never points at a production URL;
- **Deterministic** — injected clock, seeded RNG, explicit locale and timezone;
- **Non-destructive** — destructive scenarios run against a throwaway fixture the test created.

And TestMate does not edit your source code unless you explicitly ask it to.

### Instructed vs. enforced

Be clear about which is which. Most of the above is **instructed** — it lives in the agent
definitions and the model follows it. The agents are scoped as tightly as their job allows
(`testmate-adversary` holds only `Read`, `Grep` and `Glob`, so its read-only posture is structural),
but the author agent must be able to write test files, and no tool grants write access to one
subtree only. So "never edits your source" is a rule the model obeys, not a wall it cannot cross.

Two settings are **enforced** by a `PreToolUse` hook the plugin ships, and hold regardless:

| Setting | Enforced by | Active when |
|---|---|---|
| `forbidCommands` | `hooks/guard_commands.py` on every `Bash` call | the list is non-empty |
| `enforce.sourceWrites` | `hooks/guard_writes.py` on every `Write`/`Edit` | you set it to `true` |

```json
{
  "forbidCommands": ["mvn deploy", "npm publish", "git push"],
  "enforce": { "sourceWrites": true }
}
```

`enforce.sourceWrites` restricts writes to recognised test paths — `src/test/`, `tests/`,
`__tests__/`, `*_test.go`, `*.test.ts`, `*Test.java`, `conftest.py` and friends. It is **off by
default** on purpose: a plugin hook fires for your own edits too, so switching it on unasked would
break ordinary work. Turn it on for a run where you want the guarantee to be structural.

## Development

```bash
python3 -m unittest discover -s tests    # 41 tests, ~1s, no credentials
claude plugin eval .                     # 8 cases, ~4 min, ~$1.80
```

The unit tests cover the two hooks (including the bypasses you would try first) and the structural
integrity of the prompt surface — that every reference resolves, no reference is orphaned, every
command loads the config skill, every `Bash`-holding agent checks `forbidCommands`, and no report
path is hardcoded. Those checks started as manual greps during the self-audit in `docs/`; they are
tests now so they cannot rot.

See `CONTRIBUTING.md` before changing a grader or a hook.

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
              testmate-config     reads and enforces .testmate/config.json
hooks/        guard_commands.py   blocks forbidCommands (PreToolUse, Bash)
              guard_writes.py     keeps writes in test paths (opt-in)
```

## Does it hold?

The prompt surface is the product, so TestMate ships an eval suite that defends its own defining
behaviours — the ones a reworded instruction could silently remove.

```bash
claude plugin eval .
```

Eight cases, each self-contained: a failing test is triaged as a `BUG` with its assertion intact; an
unspecified contract comes back `UNDECIDED` rather than being laundered into "the test was wrong";
deadline pressure does not buy a green suite; the default level really is adversarial; generated
tests mirror the repository's own fixture and idiom; `forbidCommands` is not worked around; an
unknown stack is asked about rather than invented; a Next.js Server Action is recognised as a public
endpoint. See `evals/README.md`.

Measured per case, three runs each: seven cases at 1.00, and `matches-existing-conventions` at
**0.83** across two independent measurements. Its `skill-fired` grader — does TestMate actually
engage, or did the base model guess the right style unaided — now passes consistently; the residual
is `criteria` failing roughly one run in three, cause not yet isolated.

That case is left failing rather than loosened. Grinding a grader until it goes green is the exact
move TestMate refuses to make in the code it tests, and an honestly red case is more informative
than a quietly relaxed one. CI is set to `--threshold 0.8` to accommodate it explicitly rather than
silently.

### Adding a stack

Two edits, no code:

1. Write `skills/stack-adapters/references/<stack>.md` covering the six sections the parent skill
   lists — where test files go, the refusal idiom, the fixture idiom, parameterization, doubles,
   and the commands to run.
2. Add a detection row to the table in `skills/stack-adapters/SKILL.md` mapping a build manifest to
   that file.

The attack catalogue needs no changes — test shapes are language-independent, and an adapter only
translates them into idiom.

## Licence

MIT.
