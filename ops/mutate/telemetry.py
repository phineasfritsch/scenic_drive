#!/usr/bin/env python3
"""Mutation harness for Sources/Telemetry (T-0265): the H3 resolution-5 port, the completion percent and
the Analytics Engine encoder of the fourteen telemetry events.

    python ops/mutate/telemetry.py
    python ops/mutate/telemetry.py --prove-vacuity
    python ops/mutate/telemetry.py --prove-floor
    python ops/mutate/telemetry.py --only=3,7

The population is ops/mutate/telemetry_mutations.py and the mutant runner - what a build is, what a catch
is, and the six buckets a verdict lands in - is ops/mutate/telemetry_run.py, derived from
straightline_run.py with only the scratch path and the test filter changed. THIS file is the CLI, the
floors and the proof arms. ops/lib/check-mutate-population.py reads the whole `telemetry*.py` family as
this driver's code, and neither sibling carries a `__main__` block.

## The subjects are at HEAD, or nothing runs

Every Swift file the population edits and the harness's own three files are compared with `git show HEAD:`
before the first build, and the Swift files again afterwards. The TEST files are deliberately not guarded:
a red-then-green demonstration runs this population against a suite with a test removed.

`--prove-vacuity` replaces every file in Tests/TelemetryTests with an empty suite and requires every
mutation to report MISSED. `--prove-floor` shows the floor refusing on eight arms and staying quiet on the
real population; it builds nothing and writes nothing.
"""
from __future__ import annotations

import hashlib
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# No bytecode written or read: a population edited and restored inside one second would import from a .pyc
# that still matches on mtime and size (straightline.py's measured T-0199 defect).
sys.dont_write_bytecode = True
shutil.rmtree(pathlib.Path(__file__).resolve().parent / "__pycache__", ignore_errors=True)

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("Sources/Telemetry/H3CoordIJK.swift", "Sources/Telemetry/H3FaceProjection.swift",
                   "Sources/Telemetry/H3BaseCells.swift", "Sources/Telemetry/H3IndexBuilder.swift",
                   "Sources/Telemetry/H3Cell.swift", "Sources/Telemetry/CompletionPercent.swift",
                   "Sources/Telemetry/TelemetryEvent.swift")

from telemetry_mutations import (EQUIVALENT, MIN_EQUIVALENT, MIN_MUTATIONS, MIN_TEST_FILES, MUTATIONS,
                                 MUTATED_FILES, ROOT, SUBJECTS, TEST_DIR)
from telemetry_run import FILTER, build, empty_suite, not_at_head, run_all, test

TESTS = sorted(TEST_DIR.glob("*.swift"))
HARNESS = (pathlib.Path(__file__).resolve(),
           pathlib.Path(__file__).resolve().parent / "telemetry_mutations.py",
           pathlib.Path(__file__).resolve().parent / "telemetry_run.py")


def population_floor():
    """The reason to refuse, or None. A harness that examines nothing exits 0 and proves nothing."""
    if len(MUTATIONS) < MIN_MUTATIONS:
        return "MUTATIONS holds %d entries, below the floor of %d" % (len(MUTATIONS), MIN_MUTATIONS)
    if len(EQUIVALENT) < MIN_EQUIVALENT:
        return "EQUIVALENT holds %d entries, below the floor of %d" % (len(EQUIVALENT), MIN_EQUIVALENT)
    if len(TESTS) < MIN_TEST_FILES:
        return "TESTS globbed %d files from %s, below the floor of %d" % (len(TESTS), TEST_DIR.name,
                                                                          MIN_TEST_FILES)
    nameless = [n for n, _p, _o, _w, killers in MUTATIONS if not killers]
    if nameless:
        return ("these entries name no killer: %s. `0 red of 0 named` is the killer check satisfied "
                "vacuously" % ", ".join(nameless))
    edited = {p for _n, p, _o, _w, _k in MUTATIONS}
    unmutated = [s.name for s in SUBJECTS if s not in edited]
    if unmutated:
        return ("no MUTATIONS entry edits %s, which SUBJECT_MODULES declares. The stated subject would be "
                "wider than what is measured" % ", ".join(unmutated))
    declared = {ROOT / p for p in SUBJECT_MODULES}
    if declared != set(SUBJECTS):
        return "SUBJECT_MODULES and telemetry_mutations.SUBJECTS disagree"
    missing = [p.name for p in MUTATED_FILES if not p.exists()]
    if missing:
        return "these files do not exist: %s" % ", ".join(missing)
    return None


def prove_floor() -> int:
    """`--prove-floor`: the floor REFUSING, one arm at a time, then the control clean. Builds nothing."""
    base = {"MUTATIONS": list(MUTATIONS), "EQUIVALENT": list(EQUIVALENT), "TESTS": list(TESTS),
            "MIN_MUTATIONS": MIN_MUTATIONS}
    killers_gone = [(n, p, o, w, [] if i == 0 else k)
                    for i, (n, p, o, w, k) in enumerate(base["MUTATIONS"])]
    subject_gone = [m for m in base["MUTATIONS"] if m[1] != SUBJECTS[-1]]
    arms = [
        ("MUTATIONS emptied - a clean sheet over nothing", {"MUTATIONS": []}),
        ("MUTATIONS one short of the floor", {"MUTATIONS": base["MUTATIONS"][:MIN_MUTATIONS - 1]}),
        ("the floor raised to %d against a population of %d" % (MIN_MUTATIONS + 1, len(MUTATIONS)),
         {"MIN_MUTATIONS": MIN_MUTATIONS + 1}),
        ("EQUIVALENT emptied", {"EQUIVALENT": []}),
        ("one entry's killers emptied - 0 red of 0 named", {"MUTATIONS": killers_gone}),
        ("every mutation of one declared subject removed", {"MUTATIONS": subject_gone}),
        ("TESTS globbed down to nothing - vacuity would empty nothing", {"TESTS": []}),
        ("TESTS one short of the floor of %d" % MIN_TEST_FILES, {"TESTS": base["TESTS"][:MIN_TEST_FILES - 1]}),
    ]
    g = globals()
    refused = 0
    control = "prove_floor never reached the control arm"
    try:
        for label, patch in arms:
            g.update(base)
            g.update(patch)
            why = population_floor()
            sys.stdout.write("FLOOR ARM   %-56s %s\n" % (label, why or "NO REFUSAL - THIS ARM FAILED"))
            refused += 1 if why is not None else 0
        g.update(base)
        control = population_floor()
        sys.stdout.write("FLOOR ARM   %-56s %s\n"
                         % ("CONTROL: unpatched", control or "no refusal, as required"))
    finally:
        g.update(base)
    ok = refused == len(arms) and control is None
    sys.stdout.write("FLOOR PROOF %s: %d of %d arms refused and the control did not\n"
                     % ("OK" if ok else "FAILED", refused, len(arms)))
    return 0 if ok else 1


def report(r, chosen) -> None:
    sys.stdout.write("caught by the test that names it: %d of %d   (wrong killer %d, trapped %d, "
                     "compile-only %d, MISSED %d, skipped %d)\n"
                     % (len(r["caught"]), len(chosen), len(r["wrong_killer"]), len(r["trapped"]),
                        len(r["compile_only"]), len(r["missed"]), len(r["skipped"])))
    for bucket, why in (("wrong_killer", "caught, but NOT by the test that names it - DOES NOT COUNT"),
                        ("trapped", "detected by a crash and not an assertion - DOES NOT COUNT"),
                        ("compile_only", "a compile failure is not a test catch - DOES NOT COUNT"),
                        ("missed", "no test objected"),
                        ("skipped", "anchor missing - the harness is stale")):
        for n in r[bucket]:
            sys.stdout.write("  %s: %s (%s)\n" % (bucket.upper(), n, why))


def main(argv) -> int:
    if "--prove-floor" in argv:
        return prove_floor()
    prove = "--prove-vacuity" in argv
    only = [a.split("=", 1)[1] for a in argv if a.startswith("--only=")]
    refusal = population_floor()
    if refusal is not None:
        sys.stdout.write("REFUSING TO RUN: %s\n" % refusal)
        return 2
    chosen = MUTATIONS
    if only:
        picked = {int(i) for part in only for i in part.split(",")}
        chosen = [m for i, m in enumerate(MUTATIONS, 1) if i in picked]
        sys.stdout.write("PARTIAL RUN over %d of %d mutations (--only); never prints MUTATE OK and is never an\n"
                         "  acceptance command.\n" % (len(chosen), len(MUTATIONS)))
    sys.stdout.write("population  mutations=%d (floor %d)  equivalent=%d (floor %d)  subjects=%d  "
                     "test files=%d\n" % (len(MUTATIONS), MIN_MUTATIONS, len(EQUIVALENT), MIN_EQUIVALENT,
                                          len(SUBJECTS), len(TESTS)))
    dirty = not_at_head(list(MUTATED_FILES) + list(HARNESS))
    if dirty:
        sys.stdout.write("REFUSING: not what HEAD says it is: %s\n" % ", ".join(dirty))
        return 2
    pristine = {f: f.read_bytes() for f in MUTATED_FILES}
    pristine_tests = {t: t.read_bytes() for t in TESTS}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-30s md5 %s  == HEAD\n" % (f.name, hashlib.md5(b).hexdigest()))
    eq = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: every file in Tests/TelemetryTests is replaced by an empty\n"
                             "suite, so every mutation must report MISSED.\n")
            for t in TESTS:
                t.write_text(empty_suite(t), encoding="utf-8", newline="\n")
        if build() != 0 and build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _txt = test()
        sys.stdout.write("BASELINE    --filter %-52s exit=%d\n" % (FILTER, code))
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2
        r = run_all(pristine, chosen, True)
        if not prove and not only:
            sys.stdout.write("\nEQUIVALENT - cannot change behaviour, so anything but MISSED is a FAILURE\n")
            for name, _p, _o, _n, witness in EQUIVALENT:
                sys.stdout.write("  witness     %s: %s\n" % (name, witness))
            eq = run_all(pristine, EQUIVALENT, False)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        for t, b in pristine_tests.items():
            t.write_bytes(b)
    still = not_at_head(MUTATED_FILES)
    if still:
        sys.stdout.write("RESTORE FAILED - not back at HEAD: %s\n" % ", ".join(still))
        return 2
    sys.stdout.write("\nrestored, every subject == HEAD\n")
    report(r, chosen)
    if prove:
        ok = len(r["caught"]) == 0 and len(r["missed"]) == len(MUTATIONS)
        sys.stdout.write("VACUITY PROOF %s: caught=%d (need 0) and MISSED=%d of %d\n"
                         % ("OK" if ok else "FAILED", len(r["caught"]), len(r["missed"]), len(MUTATIONS)))
        return 0 if ok else 1
    if only:
        ok = len(r["caught"]) == len(chosen)
        sys.stdout.write("PARTIAL %s: %d of %d selected mutations caught by the test that names it\n"
                         % ("OK" if ok else "FAILED", len(r["caught"]), len(chosen)))
        return 0 if ok else 1
    eq_caught = 0 if eq is None else len(eq["caught"]) + len(eq["wrong_killer"])
    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required\n"
                         % (0 if eq is None else len(eq["missed"]), len(EQUIVALENT)))
    ok = len(r["caught"]) == len(MUTATIONS) and eq_ok
    sys.stdout.write("MUTATE %s  caught=%d/%d equivalent_caught=%d\n"
                     % ("OK" if ok else "FAILED", len(r["caught"]), len(MUTATIONS), eq_caught))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
