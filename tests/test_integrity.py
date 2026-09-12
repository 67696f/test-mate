#!/usr/bin/env python3
"""Structural integrity of the plugin's prompt surface.

The prompt surface is the product, and markdown fails to compile in no way at all. These are the
checks that were run by hand during the 2026-09-12 self-audit (see docs/), turned into tests so they
cannot rot.

Run: python3 -m unittest discover -s tests -v
"""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(path):
    with open(os.path.join(ROOT, path)) as handle:
        return handle.read()


def markdown_files(*dirs):
    found = []
    for d in dirs:
        for base, _, files in os.walk(os.path.join(ROOT, d)):
            for name in files:
                if name.endswith(".md"):
                    found.append(os.path.relpath(os.path.join(base, name), ROOT))
    return sorted(found)


def frontmatter(text):
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


COMMANDS = [f for f in markdown_files("commands")]
AGENTS = [f for f in markdown_files("agents")]
SKILLS = sorted(
    os.path.relpath(os.path.join(ROOT, "skills", d, "SKILL.md"), ROOT)
    for d in os.listdir(os.path.join(ROOT, "skills"))
    if os.path.isfile(os.path.join(ROOT, "skills", d, "SKILL.md"))
)
REFERENCES = [f for f in markdown_files("skills") if "/references/" in f]


class TestManifests(unittest.TestCase):
    def test_json_files_parse(self):
        for path in [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json",
                     "examples/config.example.json", "hooks/hooks.json"]:
            with self.subTest(path=path):
                json.loads(read(path))

    def test_plugin_name_matches_marketplace_entry(self):
        plugin = json.loads(read(".claude-plugin/plugin.json"))
        market = json.loads(read(".claude-plugin/marketplace.json"))
        names = [p["name"] for p in market["plugins"]]
        self.assertIn(plugin["name"], names)

    def test_hooks_reference_existing_scripts(self):
        hooks = json.loads(read("hooks/hooks.json"))
        scripts = re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}/([^"\s]+)', json.dumps(hooks))
        self.assertTrue(scripts, "hooks.json declares no scripts")
        for script in scripts:
            with self.subTest(script=script):
                self.assertTrue(os.path.isfile(os.path.join(ROOT, script)), f"{script} missing")


class TestFrontmatter(unittest.TestCase):
    def test_every_component_has_frontmatter(self):
        for path in COMMANDS + AGENTS + SKILLS:
            with self.subTest(path=path):
                self.assertIsNotNone(frontmatter(read(path)), f"{path} has no frontmatter")

    def test_commands_declare_a_description(self):
        for path in COMMANDS:
            with self.subTest(path=path):
                self.assertIn("description", frontmatter(read(path)))

    def test_skill_name_matches_its_directory(self):
        for path in SKILLS:
            with self.subTest(path=path):
                directory = os.path.basename(os.path.dirname(path))
                self.assertEqual(frontmatter(read(path)).get("name"), directory)

    def test_agent_name_matches_its_filename(self):
        for path in AGENTS:
            with self.subTest(path=path):
                stem = os.path.basename(path)[: -len(".md")]
                self.assertEqual(frontmatter(read(path)).get("name"), stem)

    def test_agents_declare_tools(self):
        for path in AGENTS:
            with self.subTest(path=path):
                self.assertIn("tools", frontmatter(read(path)))


class TestWiring(unittest.TestCase):
    """The self-audit's finding 1 and 2: documented behaviour that nothing actually performs."""

    def test_every_reference_file_is_cited_somewhere(self):
        """An uncited reference is documentation no agent will ever read."""
        corpus = "\n".join(read(p) for p in COMMANDS + AGENTS + SKILLS)
        for path in REFERENCES:
            with self.subTest(path=path):
                self.assertIn(os.path.basename(path), corpus,
                              f"{path} is never referenced — dead documentation")

    def test_every_cited_reference_exists(self):
        """A dangling link sends an agent looking for a file that is not there."""
        on_disk = {os.path.basename(p) for p in REFERENCES}
        corpus = "\n".join(read(p) for p in COMMANDS + AGENTS + SKILLS + REFERENCES)
        for cited in set(re.findall(r"references/([a-z0-9-]+\.md)", corpus)):
            with self.subTest(reference=cited):
                self.assertIn(cited, on_disk, f"references/{cited} is cited but does not exist")

    def test_every_cited_path_resolves_from_the_citing_file(self):
        """A citation must be openable, not merely name a file that exists somewhere.

        The check above compares basenames, so a cross-skill citation written as
        `attack-catalog/references/authz.md` passed while resolving to nothing from the
        file that carried it. An agent following that link reads no file and silently
        loses the guidance.
        """
        for rel in COMMANDS + AGENTS + SKILLS + REFERENCES:
            base = os.path.dirname(os.path.join(ROOT, rel))
            for cited in re.findall(r"`([A-Za-z0-9_\-./]+\.md)`", read(rel)):
                if cited.startswith("graders/") or cited in ("prompt.md", "SKILL.md"):
                    continue    # generic references in prose, not links
                with self.subTest(source=rel, cited=cited):
                    self.assertTrue(
                        os.path.exists(os.path.join(base, cited))
                        or os.path.exists(os.path.join(ROOT, cited)),
                        f"{rel} cites {cited}, which resolves neither next to it nor "
                        f"from the plugin root")

    def test_agents_told_to_load_a_skill_can_load_one(self):
        """Every agent's prompt opens by telling it to load skills. It needs the tool.

        This is the defect shape that has bitten this plugin twice: guidance that exists,
        is correct, and sits where the agent doing the work cannot reach it. An agent
        whose `tools:` omits `Skill` is being told to load `failure-triage` with no way
        to do it.
        """
        for path in AGENTS:
            text = read(path)
            if not re.search(r"[Ll]oad (the )?`", text):
                continue
            fields = frontmatter(text) or {}
            tools = [t.strip() for t in fields.get("tools", "").split(",")]
            with self.subTest(agent=path):
                self.assertIn("Skill", tools,
                              f"{path} is told to load a skill but does not declare the "
                              f"Skill tool")

    def test_every_agent_is_used_by_a_command(self):
        corpus = "\n".join(read(p) for p in COMMANDS)
        for path in AGENTS:
            name = os.path.basename(path)[: -len(".md")]
            with self.subTest(agent=name):
                self.assertIn(name, corpus, f"{name} is defined but no command invokes it")

    def test_every_command_loads_the_config_skill(self):
        """Self-audit finding 2: four of six commands silently ignored .testmate/config.json."""
        for path in COMMANDS:
            with self.subTest(path=path):
                self.assertIn("testmate-config", read(path),
                              f"{path} does not load testmate-config, so config would be ignored")

    def test_bash_capable_agents_check_forbid_commands(self):
        """An agent that can run commands must know the list it has to check against."""
        for path in AGENTS:
            fields = frontmatter(read(path))
            if "Bash" not in fields.get("tools", ""):
                continue
            with self.subTest(path=path):
                self.assertIn("forbidCommands", read(path),
                              f"{path} holds Bash but never mentions forbidCommands")

    def test_report_paths_are_not_hardcoded(self):
        """Self-audit finding 3: reportDir was documented while every path was a literal."""
        for path in COMMANDS + AGENTS + SKILLS:
            text = read(path)
            for line_number, line in enumerate(text.splitlines(), 1):
                if ".testmate/reports" not in line:
                    continue
                context = line + " " + "\n".join(text.splitlines()[max(0, line_number - 2):line_number])
                with self.subTest(path=path, line=line_number):
                    self.assertTrue(
                        "default" in context.lower() or "reportDir" in context,
                        f"{path}:{line_number} hardcodes a report path without naming reportDir",
                    )


class TestEvalSuite(unittest.TestCase):
    def test_every_case_has_a_prompt_and_a_grader(self):
        cases = [d for d in os.listdir(os.path.join(ROOT, "evals"))
                 if os.path.isdir(os.path.join(ROOT, "evals", d)) and d != "results"]
        self.assertTrue(cases, "no eval cases found")
        for case in cases:
            with self.subTest(case=case):
                base = os.path.join(ROOT, "evals", case)
                self.assertTrue(os.path.isfile(os.path.join(base, "prompt.md")),
                                f"{case} has no prompt.md")
                graders = os.path.join(base, "graders")
                self.assertTrue(os.path.isdir(graders), f"{case} has no graders/")
                self.assertTrue([g for g in os.listdir(graders) if g.endswith(".md")],
                                f"{case} has no grader files")

    def test_prompts_and_graders_have_frontmatter(self):
        for base, _, files in os.walk(os.path.join(ROOT, "evals")):
            if "results" in base:
                continue
            for name in files:
                if not name.endswith(".md") or name == "README.md":
                    continue
                path = os.path.relpath(os.path.join(base, name), ROOT)
                with self.subTest(path=path):
                    self.assertIsNotNone(frontmatter(read(path)), f"{path} has no frontmatter")


if __name__ == "__main__":
    unittest.main(verbosity=2)
