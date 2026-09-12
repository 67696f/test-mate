#!/usr/bin/env python3
"""Tests for the eval no-result guard.

The guard exists to stop an aborted run being recorded as a failing one, so the cases that matter
most are the ones where a zero is NOT a failure. Written against the real shapes
`claude plugin eval` emits, including the session-limit abort that motivated the guard.

Run: python3 -m unittest discover -s tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evals", "check_results.py")
OK, FAILED, NO_RESULT = 0, 1, 2


def case(name, score, runs):
    return {"name": name, "aggregates": {"score": score}, "arms": {"with": runs}}


def run(error=None, graders=None):
    return {"error": error, "graders": graders or [{"name": "criteria", "explanation": "judge votes: PASS"}]}


class TestCheckResults(unittest.TestCase):
    def check(self, report, threshold="0.8"):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(report, handle)
            path = handle.name
        self.addCleanup(os.unlink, path)
        proc = subprocess.run([sys.executable, SCRIPT, path, "--threshold", threshold],
                              capture_output=True, text=True, timeout=15)
        return proc.returncode, proc.stdout

    def test_all_cases_pass(self):
        code, out = self.check({"cases": [case("a", 1.0, [run()]), case("b", 0.9, [run()])]})
        self.assertEqual(code, OK)
        self.assertIn("2 case(s)", out)

    def test_genuine_low_score_is_a_failure(self):
        code, out = self.check({"cases": [case("a", 0.333, [run()])]})
        self.assertEqual(code, FAILED)
        self.assertIn("FAIL: a scored 0.333", out)

    def test_session_limit_abort_is_not_a_failure(self):
        """The exact shape that cost us a run: every score 0, every run errored."""
        limit = "exit 1: You've hit your session limit · resets 11:10pm (Asia/Tbilisi)"
        code, out = self.check({"cases": [case("a", 0, [run(error=limit), run(error=limit)])]})
        self.assertEqual(code, NO_RESULT)
        self.assertIn("NO RESULT", out)
        self.assertIn("session limit", out)
        self.assertNotIn("FAIL:", out)

    def test_grader_that_threw_is_not_a_failure(self):
        """A judge call that died leaves the case unjudged, not wrong."""
        code, out = self.check({"cases": [case("a", 0, [run(graders=[
            {"name": "criteria", "explanation": "grader threw: judge call failed: overloaded"}])])]})
        self.assertEqual(code, NO_RESULT)
        self.assertIn("grader threw", out)

    def test_abort_outranks_a_real_failure_elsewhere(self):
        """A half-run suite cannot be used to convict the cases that did run."""
        code, out = self.check({"cases": [
            case("aborted", 0, [run(error="exit 1: rate limited")]),
            case("genuinely-bad", 0.1, [run()]),
        ]})
        self.assertEqual(code, NO_RESULT)
        self.assertIn("Rerun before drawing any conclusion", out)

    def test_partial_run_is_no_result(self):
        code, out = self.check({"partial": True, "cases": [case("a", 1.0, [run()])]})
        self.assertEqual(code, NO_RESULT)
        self.assertIn("partial", out)

    def test_missing_score_is_no_result_not_a_zero(self):
        code, _ = self.check({"cases": [case("a", None, [run()])]})
        self.assertEqual(code, NO_RESULT)

    def test_unreadable_file_is_no_result(self):
        proc = subprocess.run([sys.executable, SCRIPT, "/nonexistent/x.json"],
                              capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, NO_RESULT)
        self.assertIn("NO RESULT", proc.stdout)

    def test_threshold_is_respected(self):
        report = {"cases": [case("a", 0.85, [run()])]}
        self.assertEqual(self.check(report, threshold="0.8")[0], OK)
        self.assertEqual(self.check(report, threshold="0.9")[0], FAILED)


if __name__ == "__main__":
    unittest.main()
