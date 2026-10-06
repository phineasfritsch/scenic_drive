#!/usr/bin/env python3
"""Run ops/mutate/funnel_mutations.py against ops/lib/funnel_test.py (T-0284 R7).

    python ops/lib/funnel_mutate.py                   every entry
    python ops/lib/funnel_mutate.py --only=a,b        the entries whose names contain these substrings
    python ops/lib/funnel_mutate.py --prove-floor     the floor arm must refuse a short table, quiet on the real one

Per entry: `old` must occur exactly once in the pristine file (else SKIP, a failure); the file is rewritten with
`new`, __pycache__ is purged and every named killer is run alone (`python -B funnel_test.py Class.test`); the
entry is CAUGHT only when every killer exits non-zero. The file is restored byte-identical in a finally.
Prints `RESULT caught=N missed=M skipped=S of T`; exit 0 only when every entry was caught and the floor holds.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ops" / "mutate"))

import funnel_mutations  # noqa: E402

TEST = ROOT / "ops" / "lib" / "funnel_test.py"


def floor_refusal(mutations, floor: int) -> str | None:
    if len(mutations) < floor:
        return f"FLOOR REFUSED: {len(mutations)} mutations, below the literal floor {floor}"
    subjects = {m[1] for m in mutations}
    for subject in (funnel_mutations.MATH, funnel_mutations.READER):
        if subject not in subjects:
            return f"FLOOR REFUSED: {subject.relative_to(ROOT).as_posix()} has no mutation"
    return None


def red(killer: str) -> bool:
    for cache in (ROOT / "ops" / "lib" / "__pycache__", ROOT / "ops" / "mutate" / "__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    done = subprocess.run([sys.executable, "-B", str(TEST), killer], capture_output=True, cwd=ROOT)
    return done.returncode != 0


def run_one(name, path, old, new, killers) -> str:
    pristine = path.read_bytes()
    text = pristine.decode("utf-8")
    if text.count(old) != 1:
        return f"SKIP {name}: the anchor occurs {text.count(old)} times in {path.name}"
    try:
        path.write_bytes(text.replace(old, new).encode("utf-8"))
        survivors = [k for k in killers if not red(k)]
    finally:
        path.write_bytes(pristine)
    return f"MISSED {name}: green {', '.join(survivors)}" if survivors else f"CAUGHT {name} by {', '.join(killers)}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ops/lib/funnel_mutate.py")
    parser.add_argument("--only", default="")
    parser.add_argument("--prove-floor", action="store_true")
    args = parser.parse_args(argv)
    table, floor = funnel_mutations.MUTATIONS, funnel_mutations.MIN_MUTATIONS
    if args.prove_floor:
        arms = {"empty table": [], "one short of the floor": table[:floor - 1],
                "funnel.py unmutated": [m for m in table if m[1] != funnel_mutations.READER] * 2}
        refused = {arm: floor_refusal(t, floor) is not None for arm, t in arms.items()}
        for arm, ok in refused.items():
            print(f"{'REFUSED' if ok else 'NOT REFUSED'} {arm}")
        quiet = floor_refusal(table, floor) is None
        print(f"{'QUIET' if quiet else 'REFUSED'} the real population")
        return 0 if all(refused.values()) and quiet else 1
    refusal = floor_refusal(table, floor)
    if refusal:
        print(refusal)
        return 1
    print(f"population mutations={len(table)} (floor {floor})")
    baseline = sorted({k for m in table for k in m[4]})
    failing = [k for k in baseline if red(k)]
    if failing:
        print(f"BASELINE RED: {', '.join(failing)}")
        return 1
    print(f"baseline green killers={len(baseline)}")
    wanted = [w for w in args.only.split(",") if w]
    chosen = [m for m in table if not wanted or any(w in m[0] for w in wanted)]
    results = [run_one(*m) for m in chosen]
    for line in results:
        print(line)
    caught = sum(r.startswith("CAUGHT") for r in results)
    missed = sum(r.startswith("MISSED") for r in results)
    skipped = sum(r.startswith("SKIP") for r in results)
    print(f"RESULT caught={caught} missed={missed} skipped={skipped} of {len(results)}")
    return 0 if results and caught == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
