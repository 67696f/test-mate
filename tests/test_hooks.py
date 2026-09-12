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
    """Invoke a guard with a payload; return (decision, message).

    A guard that exits silently is an approval — that is the contract with the harness.
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
    return out["hookSpecificOutput"]["permissionDecision"], out.get("systemMessage", "")


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
        self.assertEqual(self.decide(command="mvn \n deploy")[0], DENY)

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
