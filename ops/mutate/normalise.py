#!/usr/bin/env python3
"""Mutation harness for the region's ranking: `etl/normalise.py` and `etl/region_reference.py`.

WHY THESE. `normalise.py` turns five unbounded producer outputs into the 0..1 terms every `scenic_score` is
the mean of - it computes the number, and it sat in P-PROC-06's DEBT list with no population at all.
T-0208 adds `region_reference.py`, which decides WHICH ways are in the curve a rank is taken against; that
is the same number one step earlier, and getting it wrong is exactly the defect T-0204 measured (160 of 190
ways on one clip seam carried two different scores). `assemble.py` is mutated for the lines that hand the
reference on - the library call and the `--reference` CLI line - and stays declared in `scenic_tags.py`'s
SUBJECT_MODULES rather than in this file's; `waydoc.py` is mutated for its `--motorways` CLI line and stays
allowlisted as wiring (rv1-t0208 B1, B2).

THE CONTRACT, the same one ops/mutate/scenic_tags.py and its runner keep:

  * each entry is `(name, file, old, new)`; `old` must appear VERBATIM in the pristine file or the run
    reports SKIP and FAILS - a stale anchor is a harness that has gone quietly blind;
  * a catch requires a NAMED TEST to fail. A non-zero exit is not a catch: a mutation that makes the suite
    error out has been noticed by Python, not by a check;
  * every subject, every test file this suite empties, and THIS FILE are compared to `git show HEAD:` before
    anything runs, and the restore is verified against HEAD afterwards. A mutation report is a claim about a
    COMMIT and is worth nothing about a dirty tree;
  * `MIN_MUTATIONS` EQUALS the shipped population, so deleting any one mutation refuses the run;
  * EQUIVALENT mutants are asserted the other way round - they cannot change behaviour, so a catch there is
    a FAILURE, because it means a test has an opinion about how the code is written rather than what it does;
  * `--prove-vacuity` empties every test file and requires EVERY mutation to report MISSED, which is what
    makes a clean sheet mean something.

PYTHON SUBJECTS NEED TWO THINGS A SWIFT SUBJECT DOES NOT, and both are here because leaving either out
produces a FALSE GREEN: every `__pycache__` under services/etl is purged before each run, and the run sleeps
past the filesystem's timestamp granularity, because a .pyc whose source mtime matches to the second is
reused and the mutation never lands.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import time

# The population lives next to this file, not on the caller's sys.path: `python ops/mutate/normalise.py`
# from the repo root and `./ops/mutate/normalise.py` must both find it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/normalise.py", "services/etl/etl/region_reference.py")

from normalise_mutations import (EMPTIED, EQUIVALENT, ETL, KNOWN_MISSED, MIN_MUTATIONS, MUTATIONS, ROOT,
                                 SUBJECTS)

MUTATIONS_FILE = pathlib.Path(__file__).resolve().parent / "normalise_mutations.py"
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(), MUTATIONS_FILE)

PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q"] + [str(path) for path in EMPTIED]
# Past the filesystem's timestamp granularity, so a mutation always lands rather than hitting a stale .pyc.
SETTLE_S = 1.1


def repo_path(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def head_bytes(path: pathlib.Path) -> bytes:
    out = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + repo_path(path)],
                         capture_output=True)
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
    failed = [line.split(" ")[1] for line in (out.stdout or "").splitlines()
              if line.startswith("FAILED ")]
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
    """Run one population. `subjects` is the SUBJECT files only.

    Only the subjects, deliberately: restoring every guarded file after each mutation would put the EMPTIED
    test files back during `--prove-vacuity` and report a clean sheet with no tests present (scenic_tags.py's
    scar). A vacuity arm that cannot fail proves nothing.
    """
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
    print("%s: %d caught, %d missed, %d skipped, of %d" % (label, caught, missed, skipped,
                                                           len(population)))
    return caught, missed, skipped


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ops/mutate/normalise.py", description=__doc__.splitlines()[0])
    parser.add_argument("--prove-vacuity", action="store_true",
                        help="empty every test file and require every mutation to be MISSED")
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
