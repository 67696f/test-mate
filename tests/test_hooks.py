#!/usr/bin/env python3
"""Tests for the PreToolUse guards.

These are the only executable code TestMate ships, and they are security controls, so they get the
treatment the plugin demands of everyone else: refusal cases first, concrete adversarial inputs, and
an assertion that legitimate work still passes.

Run: python3 -m unittest discover -s tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")
ALLOW, DENY, ASK = "allow", "deny", "ask"


def run_guard(script, payload):
    """Invoke a guard with a payload; return (decision, reason).

    A guard that exits silently is an approval — that is the contract with the harness.

    The returned payload is checked against the harness contract, not merely against what
    the guards happen to emit: hookSpecificOutput is a discriminated union keyed on
    hookEventName, so an object without it fails validation and the decision is dropped.
    A guard that cannot be heard is not a guard, so that check belongs here, where every
    deny and ask case runs through it.
    """
    proc = subprocess.run(
        [sys.executable, os.path.join(HOOKS, script)],
        input=json.dumps(payload), capture_output=True, text=True, timeout=15,
    )
    if proc.returncode != 0:
        raise AssertionError(f"{script} exited {proc.returncode}: {proc.stderr}")
    if not proc.stdout.strip():
        return ALLOW, ""
    out = json.loads(proc.stdout)
    specific = out["hookSpecificOutput"]
    if specific.get("hookEventName") != "PreToolUse":
        raise AssertionError(
            f"{script} emitted hookSpecificOutput with hookEventName="
            f"{specific.get('hookEventName')!r}; Claude Code requires \"PreToolUse\" or it "
            f"discards the decision")
    decision = specific["permissionDecision"]
    reason = specific.get("permissionDecisionReason", "")
    if not reason:
        raise AssertionError(
            f"{script} returned {decision} with no permissionDecisionReason; the model "
            f"never sees systemMessage, so the decision would arrive unexplained")
    return decision, reason


class GuardTestCase(unittest.TestCase):
    """Fresh project per test, so no test can inherit another's config."""

    script = None

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, ".testmate"), exist_ok=True)
        self.addCleanup(self.tmp.cleanup)

    def write_config(self, config):
        path = os.path.join(self.root, ".testmate", "config.json")
        with open(path, "w") as handle:
            handle.write(config if isinstance(config, str) else json.dumps(config))

    def decide(self, **tool_input):
        return run_guard(self.script, {"cwd": self.root, "tool_input": tool_input})


class TestForbidCommands(GuardTestCase):
    script = "guard_commands.py"

    # --- the guard must not fire when nothing asked it to -----------------------------------

    def test_no_config_approves(self):
        """A project that never configured TestMate is unaffected by installing it."""
        self.assertEqual(self.decide(command="mvn deploy")[0], ALLOW)

    def test_empty_forbid_list_approves(self):
        self.write_config({"forbidCommands": []})
        self.assertEqual(self.decide(command="mvn deploy")[0], ALLOW)

    def test_benign_command_approves(self):
        self.write_config({"forbidCommands": ["mvn deploy"]})
        self.assertEqual(self.decide(command="mvn test")[0], ALLOW)

    def test_missing_command_field_approves(self):
        self.write_config({"forbidCommands": ["mvn deploy"]})
        self.assertEqual(self.decide()[0], ALLOW)

    # --- refusals ---------------------------------------------------------------------------

    def test_exact_match_denied(self):
        self.write_config({"forbidCommands": ["mvn deploy"]})
        decision, message = self.decide(command="mvn deploy")
        self.assertEqual(decision, DENY)
        self.assertIn("mvn deploy", message)

    def test_denial_names_the_entry_that_matched(self):
        """The user must be able to tell WHICH rule blocked them, or the block is unactionable."""
        self.write_config({"forbidCommands": ["npm publish", "git push"]})
        _, message = self.decide(command="git push origin main")
        self.assertIn("git push", message)
        self.assertNotIn("npm publish", message)

    def test_command_with_flags_denied(self):
        self.write_config({"forbidCommands": ["mvn deploy"]})
        self.assertEqual(self.decide(command="mvn deploy -DskipTests")[0], DENY)

    def test_extra_whitespace_does_not_evade(self):
        """Reformatting is the laziest bypass; normalisation must absorb it."""
        self.write_config({"forbidCommands": ["mvn deploy"]})
        self.assertEqual(self.decide(command="mvn    deploy")[0], DENY)
        self.assertEqual(self.decide(command="mvn\tdeploy")[0], DENY)
        # A backslash-newline is a continuation: still one `mvn deploy`.
        self.assertEqual(self.decide(command="mvn \\\n deploy")[0], DENY)

    def test_case_does_not_evade(self):
        self.write_config({"forbidCommands": ["mvn deploy"]})
        self.assertEqual(self.decide(command="MVN DEPLOY")[0], DENY)

    def test_embedded_in_a_larger_command_denied(self):
        """Chaining or wrapping must not launder a forbidden command."""
        self.write_config({"forbidCommands": ["git push"]})
        self.assertEqual(self.decide(command="cd /repo && git push origin main")[0], DENY)
        self.assertEqual(self.decide(command="bash -c 'git push'")[0], DENY)
        self.assertEqual(self.decide(command="FOO=1 git push")[0], DENY)

    def test_glob_entry_denied(self):
        self.write_config({"forbidCommands": ["kubectl * delete *"]})
        self.assertEqual(self.decide(command="kubectl -n prod delete pod x")[0], DENY)

    def test_blank_entries_are_ignored_not_matched(self):
        """A stray empty string must not become a rule that blocks everything."""
        self.write_config({"forbidCommands": ["", "   ", "mvn deploy"]})
        self.assertEqual(self.decide(command="ls")[0], ALLOW)
        self.assertEqual(self.decide(command="mvn deploy")[0], DENY)

    # --- data vs. execution -----------------------------------------------------------------

    def test_pattern_as_data_is_not_a_command(self):
        """`echo "git push"` prints a string; it does not push.

        Matching is still substring-based inside each segment. What changed is that a
        segment whose command only reads or prints its arguments is not treated as
        running them.
        """
        self.write_config({"forbidCommands": ["git push", "npm publish"]})
        for command in [
            'echo "git push"',
            'grep -r "git push" docs/',
            'printf "run npm publish to release"',
            'cat README.md | grep "mvn deploy"',
            'rg "npm publish" --files-with-matches',
        ]:
            with self.subTest(command=command):
                self.assertEqual(self.decide(command=command)[0], ALLOW)

    def test_inert_command_does_not_launder_a_later_segment(self):
        """An allowed segment must not cover for a forbidden one beside it."""
        self.write_config({"forbidCommands": ["git push", "npm publish"]})
        for command in [
            'echo "starting" && git push',
            'echo "x"; npm publish',
            'true || git push',
            'cat notes.md | grep foo && git push',
        ]:
            with self.subTest(command=command):
                self.assertEqual(self.decide(command=command)[0], DENY)

    def test_command_substitution_defeats_the_exemption(self):
        """`echo $(git push)` RUNS git push. Data becomes a command here."""
        self.write_config({"forbidCommands": ["git push"]})
        for command in [
            'echo $(git push)',
            'echo `git push`',
            'echo ${x:-$(git push)}',
            'diff <(git push) /dev/null',
        ]:
            with self.subTest(command=command):
                self.assertEqual(self.decide(command=command)[0], DENY)

    def test_newline_separates_commands(self):
        """A newline is a command separator and must survive whitespace normalisation.

        The first version of the segment matcher normalised whitespace BEFORE splitting,
        which folded `echo "starting"` and a `git push` on the next line into one
        echo-led segment and let the push through. A real bypass, shipped for a night.
        """
        self.write_config({"forbidCommands": ["git push", "mvn deploy"]})
        for command in [
            'echo "starting"\ngit push',
            'echo start\ngit push origin main',
            'printf x\n\ngit push',
            'echo a\r\nmvn deploy',
            'grep foo bar.txt\n  git push',
        ]:
            with self.subTest(command=command):
                self.assertEqual(self.decide(command=command)[0], DENY)

    def test_multiline_command_still_matches_reformatted_pattern(self):
        """Normalising per segment must not lose the reformatting protection."""
        self.write_config({"forbidCommands": ["mvn deploy"]})
        self.assertEqual(self.decide(command="mvn \\\n  deploy")[0], DENY)   # continuation
        self.assertEqual(self.decide(command="mvn \\\r\n  deploy")[0], DENY)
        self.assertEqual(self.decide(command="mvn\tdeploy")[0], DENY)

    def test_bare_newline_is_a_separator_not_whitespace(self):
        """`mvn` then `deploy` on the next line runs two commands; neither is `mvn deploy`.

        The previous matcher normalised whitespace first and denied this, which was
        over-matching -- and the same belief, applied to `echo x` + newline + `git push`,
        produced the bypass. A newline separates; a backslash-newline continues.
        """
        self.write_config({"forbidCommands": ["mvn deploy"]})
        self.assertEqual(self.decide(command="mvn\ndeploy")[0], ALLOW)

    def test_interpreter_is_not_inert(self):
        """bash/sh run their arguments, so the exemption must not reach them."""
        self.write_config({"forbidCommands": ["npm publish"]})
        for command in ["bash -c 'npm publish'", 'sh -c "npm publish"',
                        'xargs npm publish']:
            with self.subTest(command=command):
                self.assertEqual(self.decide(command=command)[0], DENY)

    def test_absolute_path_to_a_forbidden_command_denied(self):
        self.write_config({"forbidCommands": ["git push"]})
        self.assertEqual(self.decide(command="/usr/bin/git push origin main")[0], DENY)

    # --- malformed configuration ------------------------------------------------------------

    def test_unparseable_config_asks(self):
        """A malformed safety config must never be treated as an absent one."""
        self.write_config("{not json")
        decision, message = self.decide(command="mvn deploy")
        self.assertEqual(decision, ASK)
        self.assertIn("could not be parsed", message)

    def test_forbid_commands_wrong_type_asks(self):
        """A string where a list belongs is a typo in a safety key, not permission to proceed."""
        self.write_config({"forbidCommands": "mvn deploy"})
        decision, message = self.decide(command="mvn deploy")
        self.assertEqual(decision, ASK)
        self.assertIn("forbidCommands", message)

    def test_non_string_entry_does_not_crash(self):
        self.write_config({"forbidCommands": [123, None, "mvn deploy"]})
        self.assertEqual(self.decide(command="mvn deploy")[0], DENY)

    # --- config discovery -------------------------------------------------------------------

    def test_config_found_from_a_subdirectory(self):
        """Commands run deep in a monorepo are still governed by the project's config."""
        deep = os.path.join(self.root, "services", "billing", "src")
        os.makedirs(deep)
        self.write_config({"forbidCommands": ["mvn deploy"]})
        decision, _ = run_guard(self.script, {"cwd": deep, "tool_input": {"command": "mvn deploy"}})
        self.assertEqual(decision, DENY)


class TestSourceWrites(GuardTestCase):
    script = "guard_writes.py"

    # --- opt-in: silent unless the project asked -------------------------------------------

    def test_no_config_approves_source_write(self):
        self.assertEqual(self.decide(file_path=f"{self.root}/src/main/Db.java")[0], ALLOW)

    def test_enforce_off_approves_source_write(self):
        """Installing TestMate must not start blocking the user's own ordinary edits."""
        self.write_config({"enforce": {"sourceWrites": False}})
        self.assertEqual(self.decide(file_path=f"{self.root}/src/main/Db.java")[0], ALLOW)

    def test_enforce_absent_approves_source_write(self):
        self.write_config({"level": "high"})
        self.assertEqual(self.decide(file_path=f"{self.root}/src/main/Db.java")[0], ALLOW)

    # --- refusals ---------------------------------------------------------------------------

    def test_enforce_on_denies_source_write(self):
        self.write_config({"enforce": {"sourceWrites": True}})
        decision, message = self.decide(file_path=f"{self.root}/src/main/java/Db.java")
        self.assertEqual(decision, DENY)
        self.assertIn("Db.java", message)

    def test_traversal_out_of_a_test_dir_denied(self):
        """A path that resolves into source is source, however it was spelled."""
        self.write_config({"enforce": {"sourceWrites": True}})
        sneaky = f"{self.root}/src/test/../main/java/Db.java"
        self.assertEqual(self.decide(file_path=sneaky)[0], DENY)

    def test_symlink_out_of_a_test_dir_denied(self):
        """A symlink under tests/ pointing at source must not launder the write."""
        self.write_config({"enforce": {"sourceWrites": True}})
        os.makedirs(os.path.join(self.root, "src", "main"))
        os.makedirs(os.path.join(self.root, "tests"))
        target = os.path.join(self.root, "src", "main", "Db.java")
        open(target, "w").close()
        link = os.path.join(self.root, "tests", "Db.java")
        os.symlink(target, link)
        self.assertEqual(self.decide(file_path=link)[0], DENY)

    def test_test_path_outside_the_project_denied(self):
        """The guard is scoped to this repository, not to test-shaped paths everywhere.

        The patterns match on shape alone, so without a containment check a write to
        /anywhere/tests/x.py reads as test surface -- and a guard the user switched on for
        one project becomes permission to write across the filesystem.
        """
        self.write_config({"enforce": {"sourceWrites": True}})
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        victim = os.path.join(outside.name, "tests", "evil.py")
        os.makedirs(os.path.dirname(victim))
        self.assertEqual(self.decide(file_path=victim)[0], DENY)

    def test_sibling_directory_named_tests_denied(self):
        """`../tests/x.py` resolves outside the root and is not this project's surface."""
        self.write_config({"enforce": {"sourceWrites": True}})
        self.assertEqual(
            self.decide(file_path=f"{self.root}/../tests/evil.py")[0], DENY)

    # --- test paths across every shipped adapter --------------------------------------------

    def test_recognised_test_paths_approved(self):
        self.write_config({"enforce": {"sourceWrites": True}})
        for path in [
            "src/test/java/com/acme/DBSafetyTest.java",   # JVM
            "src/test/resources/schema.sql",
            "tests/test_db.py",                            # Python
            "tests/conftest.py",
            "app/actions.test.ts",                         # Node / Next.js
            "src/__tests__/user.spec.tsx",
            "internal/db/db_test.go",                      # Go
            "spec/user_spec.rb",
            "e2e/auth.spec.ts",                            # Playwright
            "src/foo.service.spec.ts",                     # Angular
            ".testmate/reports/2026-01-01-audit.md",       # TestMate's own output
        ]:
            with self.subTest(path=path):
                decision, _ = self.decide(file_path=f"{self.root}/{path}")
                self.assertEqual(decision, ALLOW, f"{path} should be writable")

    def test_source_paths_denied(self):
        self.write_config({"enforce": {"sourceWrites": True}})
        for path in [
            "src/main/java/com/acme/Db.java",
            "app/page.tsx",
            "internal/db/db.go",
            "acme/database.py",
            "pom.xml",
            "package.json",
        ]:
            with self.subTest(path=path):
                decision, _ = self.decide(file_path=f"{self.root}/{path}")
                self.assertEqual(decision, DENY, f"{path} should be blocked")

    def test_missing_file_path_approves(self):
        self.write_config({"enforce": {"sourceWrites": True}})
        self.assertEqual(self.decide()[0], ALLOW)


if __name__ == "__main__":
    unittest.main(verbosity=2)
