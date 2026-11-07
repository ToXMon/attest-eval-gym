"""Self-test: prove the sandbox actually contains the attack corpus.

This is the regression suite for the containment claim, and the evidence the
demo video shows. Run it with:

    python -m scripts.selftest          # from the repo root
    python scripts/selftest.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from attest.attacks import ATTACK_CORPUS          # noqa: E402
from attest.capabilities import analyze_source     # noqa: E402
from attest.oracles import ORACLE_TYPES, GradeContext, grade   # noqa: E402
from attest.sandbox import detect_runtime, run_code  # noqa: E402

BENIGN = """
import json
rows = [{"name": f"item-{i}", "value": i * 3} for i in range(5)]
total = sum(r["value"] for r in rows)
print(json.dumps({"total": total, "count": len(rows)}))
with open("report.csv", "w") as fh:
    fh.write("name,value\\n")
    for r in rows:
        fh.write(f"{r['name']},{r['value']}\\n")
"""


def check_benign() -> tuple[bool, str]:
    """A normal task must still succeed -- containment must not break the work."""
    res = run_code(BENIGN, timeout=40)
    ok = res.exit_code == 0 and '"total": 30' in res.stdout and any(
        a.path.endswith("report.csv") for a in res.artifacts
    )
    return ok, (
        f"exit={res.exit_code} stdout={res.stdout.strip()[:80]!r} "
        f"artifacts={[a.path for a in res.artifacts]}"
    )


def check_attacks() -> list[dict]:
    results: list[dict] = []
    for attack in ATTACK_CORPUS:
        res = run_code(attack.source, timeout=attack.timeout)
        contained, evidence = attack.detector(res)
        intent = analyze_source(attack.source)
        results.append({
            "id": attack.id,
            "title": attack.title,
            "class": attack.cls,
            "contained": contained,
            "evidence": evidence,
            "exit_code": res.exit_code,
            "timed_out": res.timed_out,
            "oom_killed": res.oom_killed,
            "duration_ms": res.duration_ms,
            "static_classes": sorted(intent.classes.keys()),
            "attempted_score": round(intent.attempted_score, 3),
        })
    return results


def check_oracles() -> list[dict]:
    """Exercise every oracle type against a known result."""
    res = run_code(BENIGN, timeout=40)
    ctx = GradeContext(canary="canary-abc123")
    cases = [
        ({"type": "exit_code", "value": 0}, True),
        ({"type": "stdout_regex", "pattern": r'"total": 30'}, True),
        ({"type": "stdout_regex", "pattern": r'"total": 99'}, False),
        ({"type": "json_equals", "path": "total", "value": 30}, True),
        ({"type": "json_equals", "path": "count", "value": 5}, True),
        ({"type": "json_contains", "path": "", "value": "total"}, True),
        ({"type": "numeric_within", "path": "total", "value": 30.0, "tol": 0.01}, True),
        ({"type": "numeric_within", "path": "total", "value": 31.0, "tol": 0.01}, False),
        ({"type": "file_exists", "path": "report.csv", "min_bytes": 10}, True),
        ({"type": "file_exists", "path": "nope.txt"}, False),
        ({"type": "csv_shape", "path": "report.csv", "min_bytes": 10}, True),
        ({"type": "no_secret_leak"}, True),
        ({"type": "containment_held"}, False),
    ]
    out = []
    for spec, want in cases:
        g = grade(spec, res, ctx)
        ok = g.passed == want
        out.append({"oracle": spec["type"], "expected_pass": want, "got": g.passed,
                    "correct": ok, "detail": g.detail})
    # containment_held with a proper context
    g = grade({"type": "containment_held"}, res, GradeContext(containment={"outcome": "contained"}))
    out.append({"oracle": "containment_held(contained)", "expected_pass": True,
                "got": g.passed, "correct": g.passed, "detail": g.detail})
    g = grade({"type": "containment_held"}, res, GradeContext(containment={"outcome": "escaped"}))
    out.append({"oracle": "containment_held(escaped)", "expected_pass": False,
                "got": g.passed, "correct": not g.passed, "detail": g.detail})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-oracles", action="store_true")
    args = ap.parse_args()

    runtime = detect_runtime()
    report: dict = {"runtime": runtime, "oracle_types": len(ORACLE_TYPES)}

    benign_ok, benign_detail = check_benign()
    report["benign"] = {"ok": benign_ok, "detail": benign_detail}

    report["attacks"] = check_attacks()

    if not args.skip_oracles:
        report["oracles"] = check_oracles()

    contained = sum(1 for a in report["attacks"] if a["contained"])
    total = len(report["attacks"])
    oracle_ok = all(o["correct"] for o in report.get("oracles", [])) if "oracles" in report else True

    report["summary"] = {
        "runtime": runtime,
        "benign_ok": benign_ok,
        "attacks_total": total,
        "attacks_contained": contained,
        "all_contained": contained == total,
        "oracles_ok": oracle_ok,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"runtime              : {runtime}")
        print(f"benign task succeeds : {benign_ok}  ({benign_detail})")
        print(f"attacks contained    : {contained}/{total}")
        for a in report["attacks"]:
            mark = "PASS" if a["contained"] else "FAIL"
            print(f"  [{mark}] {a['id']:<26} exit={a['exit_code']:<4} {a['evidence']}")
        if "oracles" in report:
            bad = [o for o in report["oracles"] if not o["correct"]]
            print(f"oracles correct      : {len(report['oracles']) - len(bad)}/{len(report['oracles'])}")
            for o in bad:
                print(f"  [FAIL] {o['oracle']}: {o['detail']}")

    good = benign_ok and contained == total and oracle_ok
    print("\nRESULT:", "ALL GREEN" if good else "NEEDS WORK")
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
