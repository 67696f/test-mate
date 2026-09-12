# TestMate — self-audit — 2026-09-12

Target: the TestMate plugin itself. The "source" here is the prompt surface: commands, agent
definitions, skills and their references. Probed for reference integrity, wiring, contradictions
between documented and instructed behaviour, and false safety guarantees.

Confirmed findings: 9 (2 high, 4 medium, 3 low). All verified by reading the files, not inferred.

## Resolution

Kept as a record of what dogfooding the tool on itself actually turned up. Every finding below is
the text as originally written; this table is the only thing added afterwards.

| # | Finding | Status |
|---|---|---|
| 1 | `forbidCommands` / `reportDir` / `exclude` honoured by nothing | **fixed** — `skills/testmate-config`, plus a `PreToolUse` hook that enforces `forbidCommands` for real (`d6e7216`, `21c8cc3`) |
| 2 | Four of six commands ignored the config file | **fixed** — all six load `testmate-config` first (`d6e7216`) |
| 3 | `reportDir` documented but every path hardcoded | **fixed** (`d6e7216`) |
| 4 | Core promise was prose, not enforcement | **partly fixed** — `hooks/guard_commands.py` and opt-in `hooks/guard_writes.py` make two settings structural; the README now states plainly which guarantees are instructed and which are enforced (`21c8cc3`) |
| 5 | Three flags missing from the README | **fixed** — `--dry-run`, `--families` and `--threshold` documented in the command table |
| 6 | `harden.md` told a command to invoke another command | **fixed** — the audit procedure is inlined (`d6e7216`) |
| 7 | "Adding a language is one markdown file" was false | **fixed** — replaced with the two real steps (`21c8cc3`) |
| 8 | No eval suite | **fixed** — eight cases in `evals/`, which then found two further defects in the plugin itself (`ffcb917`) |
| 9 | Consumer `.gitignore` rule in the tool's own repo | **fixed** — rule dropped, this report moved to `docs/` |

Finding 4 is deliberately left as *partly* fixed. The author agent must hold `Write` to produce test
files at all, and no tool grants write access to one subtree only, so "never edits your source"
remains a rule the model follows rather than a wall it cannot cross unless `enforce.sourceWrites` is
switched on.

---

## high · silent-wrongness · Three documented config keys are honoured by nothing
- **Where:** `README.md:88-99`, `examples/config.example.json`
- **Reachable by:** any user who writes a `.testmate/config.json`
- **Input:** `{"forbidCommands": ["mvn deploy", "npm publish"], "reportDir": "...", "exclude": [...]}`
- **What happens:** `forbidCommands` appears in 0 command or agent files. `reportDir` appears in 0.
  Nothing reads them; they are inert. The user sets a control and receives no indication it did
  nothing.
- **Why it is a defect:** `forbidCommands` is presented as a safety control. A user may reasonably
  believe TestMate is *prevented* from running a publish or deploy command. It is not. A safety
  guarantee that does not exist is worse than no guarantee, because it suppresses the user's own
  caution. This is exactly the "unreachable guard" pattern from
  `skills/attack-catalog/references/silent-wrongness.md`.
- **Confirmed:** yes — `grep -rl forbidCommands commands agents skills` returns nothing.
- **Proving test:** a config with `forbidCommands: ["*"]` and a run that executes a build command.

## high · silent-wrongness · Four of six commands ignore the config file entirely
- **Where:** `commands/audit.md`, `commands/harden.md`, `commands/debug.md`, `commands/mutate.md`
- **Reachable by:** any user with a project config
- **What happens:** only `scan.md` and `test.md` instruct the model to read `.testmate/config.json`.
  A project that sets `level: standard` or an `exclude` list gets it applied by two commands and
  silently ignored by the other four.
- **Why it is a defect:** partial obedience with no signal. The user sees the level respected once
  and assumes it holds everywhere. Same family as a filter silently dropped on one code path.
- **Confirmed:** yes — `grep -rln 'config.json' commands/` returns 2 of 6.
- **Proving test:** set `level: low`, run `/testmate:harden`, observe full adversarial output.

---

## medium · silent-wrongness · reportDir is documented but every path is hardcoded
- **Where:** `commands/test.md`, `commands/audit.md`, `commands/harden.md`,
  `agents/testmate-runner.md` — all write to a literal `.testmate/reports/`
- **What happens:** setting `reportDir` has no effect; reports land in the default location.
- **Confirmed:** yes — 4 hardcoded occurrences, 0 readers of the key.

## medium · unreachable-guard · The core promise is prose, not enforcement
- **Where:** `agents/testmate-author.md:8` (`tools: Read, Write, Edit, Grep, Glob, Bash`),
  `agents/testmate-recon.md:8` (`tools: Read, Grep, Glob, Bash`)
- **What happens:** the author agent is told "never edit a file under the main source tree" and
  holds unrestricted `Write`, `Edit` and `Bash`. The recon agent declares itself read-only and
  holds `Bash`. Only `testmate-adversary` has its posture actually enforced by its tool list
  (`Read, Grep, Glob`).
- **Why it is a defect:** README states flatly that TestMate "never edits your source code". That
  is an instruction the model follows, not a constraint the harness imposes. The claim is stronger
  than the mechanism. Note this is partly unavoidable — the author must write test files, and no
  path-scoped write tool exists — but the README should say which it is.
- **Confirmed:** yes, by reading the frontmatter.

## medium · contract-drift · Three flags exist in commands but not in the README
- **Where:** `--dry-run` (`commands/test.md`), `--families` (`commands/audit.md`),
  `--threshold` (`commands/mutate.md`)
- **What happens:** a user reading the README does not know `--dry-run` exists, which is the flag
  most likely to be wanted on a first run of an unfamiliar tool against a real codebase.
- **Confirmed:** yes — README mentions only `--level`, `--fix`, `--write`.

## medium · correctness · harden.md instructs a command to invoke another command
- **Where:** `commands/harden.md:15` — "run `/testmate:audit` on it first"
- **What happens:** a slash command cannot invoke another slash command; the model will improvise
  an approximation of the audit procedure, with no guarantee it matches.
- **Fix sketch:** say "follow the procedure in the audit command" and name the agents and skills
  directly, as `test.md` already does.

---

## low · documentation · "Adding a language is one markdown file" is not true
- **Where:** `README.md:132`
- **What happens:** adding the Next.js adapter required a second edit — the detection table in
  `skills/stack-adapters/SKILL.md`. Demonstrated in commit `152295c`.
- **Fix sketch:** say "one reference file plus a row in the detection table", or move detection
  into per-file frontmatter so the claim becomes true.

## low · coverage · The plugin has no eval suite
- **Where:** repository root
- **What happens:** a plugin whose entire premise is "your suite does not prove what you think"
  ships with nothing proving its own behaviour. `claude plugin eval` exists for this.
- **Why it matters:** the prompt surface is the product. A reworded instruction can silently
  disable the prime directive and nothing would catch it.
- **Fix sketch:** eval cases asserting the behaviours that define the tool — a failing generated
  test is reported rather than weakened; source is not edited without `--fix`; a pre-existing
  failure is not attributed to the run; an unrecognised stack asks rather than inventing.

## low · hygiene · Consumer config in the tool's own repo
- **Where:** `.gitignore` ignores `.testmate/reports/`
- **What happens:** harmless, but it is a rule written for projects that *use* TestMate sitting in
  the repo that *is* TestMate. Self-audit reports land untracked as a side effect.

---

## Probed and clean

- **Reference integrity** — every `references/*.md` and skill path cited across all 35 markdown
  files resolves to a real file. No dangling links.
- **Orphans** — every one of the 16 reference files is cited from at least one other file. No dead
  documentation.
- **Naming** — all 5 skill `name:` fields match their directory; all 4 agent `name:` fields match
  their filename; all 4 agents are referenced by at least one command.
- **Frontmatter** — present and well-formed on all 15 commands, agents and skills.
- **JSON** — `plugin.json`, `marketplace.json` and `config.example.json` all parse.
- **Tool posture** — correctly enforced for `testmate-adversary`.

## Not probed

- Runtime behaviour. Nothing here has been executed against a real project, so every claim about
  what the agents *do* is a claim about what they are *told* to do. The gap between those two is
  precisely what the missing eval suite would measure.
- Whether the stack adapters' commands and library guidance are accurate in current tool versions.
  They were written from knowledge, not verified against each ecosystem.
