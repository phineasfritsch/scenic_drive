#!/usr/bin/env python3
"""Mutation harness for services/etl/etl/curated.py and curatedslice.py (T-0183); the population is curated_mutations.py.

WHY THESE MODULES HAVE ONE. curated.py holds every numeric bound of curated.yaml (hook length, the bbox, 5 dp,
curation_score 0.6-1.0, dwell, the 365-day freshness) and curatedslice.py the 300 m radius and the 0.5 score
floor the approach road is judged by. CLAUDE.md's Verification section and P-PROC-06: a numeric module ships a
population with a literal floor, in the same PR.

THE CONTRACT is ops/mutate/surfacecoverage.py's, kept identically: a stale anchor is a SKIP and fails; a catch
needs a NAMED test to fail; subjects, the emptied tests and the population are compared to `git show HEAD:`
before and after; MIN_MUTATIONS equals the shipped population; an EQUIVALENT caught is a failure;
`--prove-vacuity` empties both test files and requires every mutation MISSED. Every __pycache__ under
services/etl is purged and the run sleeps past the timestamp granularity before each mutant.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import subprocess
import sys
import time

from curated_mutations import EQUIVALENT, ETL, KNOWN_MISSED, MIN_MUTATIONS, MUTATIONS, ROOT, SUBJECTS, TESTS

EMPTIED = TESTS
# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("services/etl/etl/curated.py", "services/etl/etl/curatedslice.py")
GUARDED = SUBJECTS + EMPTIED + (pathlib.Path(__file__).resolve(),
                                pathlib.Path(__file__).resolve().parent / "curated_mutations.py")
PYTEST = [sys.executable, "-m", "pytest", "-o", "addopts=", "-q"] + [str(t) for t in TESTS]
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
    parser = argparse.ArgumentParser(prog="ops/mutate/curated.py", description=__doc__.splitlines()[0])
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
    import mutate_only  # ops/mutate/ is sys.path[0] for a driver run as a script
    mutate_only.refuse_unsupported(sys.argv[1:])
    sys.exit(main())
