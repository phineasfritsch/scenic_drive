#!/usr/bin/env python3
"""Mutation harness AND population for services/etl/etl/surfacecoverage.py (T-0205, ruling R4).

WHY THIS MODULE HAS ONE. It computes numbers that GATE a run: the per-class known fraction, and the
comparison against a literal baseline that exits non-zero and names the class. CLAUDE.md's Verification
section and P-PROC-06 both say a module like that ships a population with a literal floor, in the same PR.

THE CONTRACT is ops/mutate/scenic_tags.py's, kept identically:

  * each entry is `(name, file, old, new)`; `old` must appear VERBATIM in the pristine file or the run
    reports SKIP and FAILS - a stale anchor is a harness that has gone quietly blind;
  * a catch requires a NAMED TEST to fail; a non-zero exit is Python noticing, not a check noticing;
  * every subject, the test file this suite empties, and THIS FILE are compared to `git show HEAD:` before
    anything runs, and the restore is verified afterwards: a mutation report is a claim about a COMMIT;
  * `MIN_MUTATIONS` EQUALS the shipped population, so deleting any one mutation refuses the run;
  * EQUIVALENT mutants cannot change behaviour, so a catch there is a FAILURE - it means a test has an
    opinion about how the code is written rather than about what it does;
  * `--prove-vacuity` empties the test file and requires EVERY mutation to report MISSED.

PYTHON SUBJECTS: every `__pycache__` under services/etl is purged before each run and the run sleeps past the
filesystem's timestamp granularity, because a .pyc whose source mtime matches to the second is reused and the
mutation never lands (the whole-second mtime false green).
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
ETL = ROOT / "services" / "etl"
COVERAGE = ETL / "etl" / "surfacecoverage.py"
COVERAGE_TESTS = ETL / "tests" / "test_surfacecoverage.py"
EMPTIED = (COVERAGE_TESTS,)
SUBJECTS = (COVERAGE,)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/surfacecoverage.py",)
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),)

# Anchors reused by more than one mutation, verbatim from the subject.
ABSENT_TAG = "    if surface is None:\n        return UNKNOWN"
UNPAVED_TAG = "    if surface in UNPAVED_SURFACES:\n        return UNPAVED"
FRACTION = "    return 0.0 if row[TOTAL] == 0 else row[KNOWN] / row[TOTAL]"
SMALL_CLASS = "        if baseline is None or row[TOTAL] < MIN_CLASS_WAYS:"
COMPARE = "        if fraction < baseline:"
REFUSALS_LOOP = "    out = []\n    for cls in sorted(table):"
PARTITION = "        if row[KNOWN] + row[UNKNOWN] + row[UNPAVED] != row[TOTAL]:"
BUCKET_KEYS = "        if not isinstance(row, dict) or set(row) != set(BUCKETS):"
ENCODE = '    return json.dumps(table, sort_keys=True, separators=(",", ":"))'
NO_KEY = '        raise ValueError("%s: meta carries no %s" % (path, META_KEY))'
VERDICT = "    return REFUSAL_EXIT if bad else 0"
TOTAL_COUNT = "        row[TOTAL] += 1"

MUTATIONS = [
    # --- which bucket a way falls in (the three-state rule the coverage question turns on) ---------------
    ("call an untagged way surveyed - the corpus `surface` column's own answer, and the defect R1b names",
     COVERAGE, ABSENT_TAG, "    if surface is None:\n        return KNOWN"),
    ("count a gravel way as surveyed rather than unpaved, so the gated ways vanish from the table",
     COVERAGE, UNPAVED_TAG, "    if surface in UNPAVED_SURFACES:\n        return KNOWN"),
    ("call a gravel way unknown, losing the positive evidence the safety gate is built on",
     COVERAGE, UNPAVED_TAG, "    if surface in UNPAVED_SURFACES:\n        return UNKNOWN"),
    ("stop counting the class total, so the three buckets no longer partition it",
     COVERAGE, TOTAL_COUNT, "        row[TOTAL] += 0"),

    # --- the fraction ------------------------------------------------------------------------------------
    ("count the unsurveyed ways as coverage, which is the number always reading ~1.0",
     COVERAGE, FRACTION,
     "    return 0.0 if row[TOTAL] == 0 else (row[KNOWN] + row[UNKNOWN]) / row[TOTAL]"),
    ("report the coverage of the paved ways only, dividing by the wrong population",
     COVERAGE, FRACTION,
     "    return 0.0 if row[TOTAL] == 0 else row[KNOWN] / max(1, row[TOTAL] - row[UNPAVED])"),

    # --- the refusal -------------------------------------------------------------------------------------
    ("refuse the classes ABOVE their baseline, the comparison inverted", COVERAGE, COMPARE,
     "        if fraction > baseline:"),
    ("never refuse anything - a check that returns a clean sheet whatever it read", COVERAGE,
     REFUSALS_LOOP, "    return []\n    out = []\n    for cls in sorted(table):"),
    ("report the refusal with a passing exit code", COVERAGE, "REFUSAL_EXIT = 1", "REFUSAL_EXIT = 0"),
    ("exit 0 however many classes were refused", COVERAGE, VERDICT, "    return 0"),
    ("raise the minimum count so every real class falls under it and none is ever judged",
     COVERAGE, "MIN_CLASS_WAYS = 25", "MIN_CLASS_WAYS = 250"),
    ("drop the minimum-count floor, so a class of three ways gets a verdict on noise",
     COVERAGE, SMALL_CLASS, "        if baseline is None or row[TOTAL] < 0:"),
    ("set the residential baseline to nothing, the shape of a baseline 'relaxed' to make a build pass",
     COVERAGE, '    "residential": 0.091,', '    "residential": 0.0,'),
    ("set the service baseline above what the window it was measured from can reach",
     COVERAGE, '    "service": 0.029,', '    "service": 0.9,'),

    # --- the table that crosses the corpus boundary ------------------------------------------------------
    ("accept a table whose buckets do not add up to its total", COVERAGE, PARTITION, "        if False:"),
    ("accept a row missing a bucket, so a truncated table reads as a measurement", COVERAGE, BUCKET_KEYS,
     "        if not isinstance(row, dict) or set(row) - set(BUCKETS):"),
    ("write the meta value in dict order, so two builds of one extract differ (P-DATA-01)", COVERAGE,
     ENCODE, '    return json.dumps(table, sort_keys=False, separators=(",", ":"))'),
    ("treat a corpus with no coverage key as a corpus with no classes", COVERAGE, NO_KEY, "        return {}"),
]

# Cannot change behaviour, so anything but MISSED is a FAILURE. Each has its witness in the name.
EQUIVALENT = [
    ("iterate the keys explicitly - sorted(d) IS sorted(d.keys()) for any mapping", COVERAGE,
     REFUSALS_LOOP, "    out = []\n    for cls in sorted(table.keys()):"),
    ("divide by a float - int/int is already true division in Python 3, same value", COVERAGE, FRACTION,
     "    return 0.0 if row[TOTAL] == 0 else row[KNOWN] / float(row[TOTAL])"),
]

# Asserted the other way round: each must still go MISSED, and a gap that CLOSES fails the run so it gets
# promoted into MUTATIONS. Empty is a claim, not an omission.
KNOWN_MISSED = []

MIN_MUTATIONS = 18
PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q", str(COVERAGE_TESTS)]
# Past the filesystem's timestamp granularity, so a mutation always lands rather than hitting a stale .pyc.
SETTLE_S = 1.1


def repo_path(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def head_bytes(path: pathlib.Path) -> bytes:
    out = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + repo_path(path)], capture_output=True)
    if out.returncode != 0:
        raise SystemExit("not in HEAD: %s - a mutation report is a claim about a commit" % repo_path(path))
    return out.stdout.replace(b"\r\n", b"\n")


def assert_pristine(paths) -> None:
    for path in paths:
        if path.read_bytes().replace(b"\r\n", b"\n") != head_bytes(path):
            raise SystemExit("%s differs from HEAD - refusing to report on a dirty tree" % repo_path(path))


def purge_pycache() -> None:
    for cache in ETL.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run_tests() -> tuple:
    purge_pycache()
    time.sleep(SETTLE_S)
    out = subprocess.run(PYTEST, cwd=str(ETL), capture_output=True, text=True)
    failed = [line.split(" ")[1] for line in (out.stdout or "").splitlines() if line.startswith("FAILED ")]
    return out.returncode, failed


def apply(path: pathlib.Path, old: str, new: str) -> bool:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return False
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
    return True


def restore(originals: dict) -> None:
    for path, text in originals.items():
        path.write_text(text, encoding="utf-8", newline="\n")


def arm(population: list, subjects: dict, expect_caught: bool, label: str) -> tuple:
    """Run one population. `subjects` is the SUBJECT files only, so --prove-vacuity's emptied test file
    stays emptied for the whole arm rather than being restored after the first mutation."""
    caught = missed = skipped = 0
    for name, path, old, new in population:
        if not apply(path, old, new):
            print("  SKIP        %s (anchor is not in %s)" % (name, repo_path(path)))
            skipped += 1
            continue
        code, failed = run_tests()
        restore(subjects)
        if failed:
            caught += 1
            print("  caught      %s  <- %s" % (name, failed[0]))
        else:
            missed += 1
            print("  %s      %s (exit %d)" % ("MISSED" if expect_caught else "missed", name, code))
    print("%s: %d caught, %d missed, %d skipped, of %d" % (label, caught, missed, skipped, len(population)))
    return caught, missed, skipped


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops/mutate/surfacecoverage.py", description=__doc__.splitlines()[0])
    parser.add_argument("--prove-vacuity", action="store_true",
                        help="empty the test file and require every mutation to be MISSED")
    args = parser.parse_args(argv)

    if len(MUTATIONS) < MIN_MUTATIONS:
        print("population is %d, floor is %d" % (len(MUTATIONS), MIN_MUTATIONS), file=sys.stderr)
        return 1
    assert_pristine(GUARDED)
    originals = {path: path.read_text(encoding="utf-8") for path in SUBJECTS + EMPTIED}
    subjects = {path: originals[path] for path in SUBJECTS}

    if args.prove_vacuity:
        for path in EMPTIED:
            path.write_text("", encoding="utf-8", newline="\n")
        caught, missed, skipped = arm(MUTATIONS, subjects, False, "VACUITY")
        restore(originals)
        assert_pristine(GUARDED)
        ok = caught == 0 and skipped == 0 and missed == len(MUTATIONS)
        print("VACUITY %s" % ("PROVED" if ok else "FAILED"))
        return 0 if ok else 1

    code, failed = run_tests()
    if code != 0 or failed:
        print("BASELINE is not green: exit %d, %s" % (code, failed), file=sys.stderr)
        return 1
    print("BASELINE exit=0, %d mutations, floor %d" % (len(MUTATIONS), MIN_MUTATIONS))
    caught, missed, skipped = arm(MUTATIONS, subjects, True, "MUTATIONS")
    eq_caught, _eq_missed, eq_skipped = arm(EQUIVALENT, subjects, False, "EQUIVALENT")
    km_caught = km_skipped = 0
    if KNOWN_MISSED:
        km_caught, _km_missed, km_skipped = arm(KNOWN_MISSED, subjects, False, "KNOWN_MISSED")
    assert_pristine(GUARDED)
    ok = (caught == len(MUTATIONS) and skipped == 0 and eq_caught == 0 and eq_skipped == 0
          and km_caught == 0 and km_skipped == 0)
    print("MUTATE %s  caught=%d/%d equivalent_caught=%d" % ("OK" if ok else "FAILED", caught,
                                                            len(MUTATIONS), eq_caught))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
