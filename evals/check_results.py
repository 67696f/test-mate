#!/usr/bin/env python3
"""Decide what an eval run actually proved, and distinguish that from what it scored.

`claude plugin eval` exits 1 both when a case genuinely scores below the threshold and when the
run never happened — a session limit, a rate limit, a dead credential. In the aborted case it
still writes a well-formed aggregate-result.json in which every case reads `score: 0.0`, which
looks exactly like a total plugin regression and is worth nothing as evidence. That trap has
already cost this project one run: a six-run sweep reported 0/6 on both graders in seven seconds,
and only the per-run `error` field distinguished it from a real collapse.

So: a zero with an aborted run behind it is NO RESULT, not a failure. Refusing to read a failure
into an absence of evidence is the same discipline `failure-triage` demands of the model, and it
applies to the suite that grades it.

    python3 evals/check_results.py <aggregate-result.json> [--threshold 0.8]

Exit codes, deliberately distinct so CI can tell the three apart:
    0  every case met the threshold
    1  a case genuinely scored below it
    2  the run aborted, or is otherwise not evidence — rerun it, do not read it
"""
import argparse
import json
import sys


def aborted_runs(case):
    """Runs that failed to produce a verdict: a run-level error, or a grader that threw.

    A grader that threw is as disqualifying as a dead run — the case has no verdict either way,
    and its 0.0 means 'unjudged', not 'wrong'.
    """
    out = []
    for arm, runs in (case.get("arms") or {}).items():
        for index, run in enumerate(runs):
            reasons = []
            if run.get("error"):
                reasons.append(str(run["error"]))
            for grader in run.get("graders") or []:
                explanation = str(grader.get("explanation") or "")
                if explanation.startswith("grader threw"):
                    reasons.append(f"{grader.get('name')}: {explanation}")
            if reasons:
                out.append((f"{arm}[{index}]", reasons))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--threshold", type=float, default=0.8)
    args = parser.parse_args()

    try:
        with open(args.path) as handle:
            report = json.load(handle)
    except Exception as exc:
        print(f"NO RESULT: {args.path} could not be read ({exc})")
        return 2

    if report.get("partial"):
        print("NO RESULT: the run is marked partial — it did not finish.")
        return 2

    aborted, failed = [], []
    for case in report.get("cases") or []:
        name = case.get("name", "<unnamed>")
        score = (case.get("aggregates") or {}).get("score")
        broken = aborted_runs(case)
        if broken:
            aborted.append((name, score, broken))
        elif score is None:
            aborted.append((name, score, [("<no score>", ["case produced no aggregate score"])]))
        elif score < args.threshold:
            failed.append((name, score))

    for name, score, broken in aborted:
        print(f"NO RESULT: {name} (reported {score}) — {len(broken)} run(s) did not complete:")
        for label, reasons in broken[:3]:
            print(f"    {label}: {reasons[0]}")
    for name, score in failed:
        print(f"FAIL: {name} scored {score:.3f}, below {args.threshold}")

    if aborted:
        # Reported first and on its own exit code: a suite that did not run tells you nothing
        # about the cases that appear to have failed alongside it.
        print(f"\n{len(aborted)} case(s) produced no usable result. Rerun before drawing any "
              f"conclusion; do not record these scores.")
        return 2
    if failed:
        print(f"\n{len(failed)} case(s) below threshold.")
        return 1

    total = len(report.get("cases") or [])
    print(f"ok: {total} case(s) at or above {args.threshold}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
