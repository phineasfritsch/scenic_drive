#!/usr/bin/env python3
"""Mutation harness for Sources/Handoff/StraightLineDistance.swift - the straight line the home screen shows.

    python ops/mutate/straightline.py
    python ops/mutate/straightline.py --prove-vacuity
    python ops/mutate/straightline.py --prove-floor

The population is ops/mutate/straightline_mutations.py; this file is the protocol and the floors. The split
is scenic_tags.py/scenic_tags_mutations.py's, for scenic_tags.py's reason: ops/mutate/handoff.py, which
measures the other two files in this target, is 603 lines against CLAUDE.md's 300-line cap, so a second
table was never going into it. Why a separate DRIVER rather than a widening of handoff.py is T-0199's R1:
this number's arithmetic lives in files handoff.py does not and must not declare.

## What counts as a catch, and what does not

A catch is a NAMED test recording an issue, and the name must be one the entry NAMES. Four things that
look like catches and are not, each its own bucket and each failing the run:

  * a non-zero exit with no named failure is `trapped` - Python noticed, no check did;
  * a mutation that does not compile is `compile-only` - a fact about Swift, not about these tests;
  * a mutation whose anchor is gone is `skipped` - the harness has gone blind, which is the opposite of
    MISSED;
  * a mutation caught by some test OTHER than the one it names is `wrong killer`. agent/rv1-pr107's
    finding on geometry.py: `len(red) != len(killers)` is satisfied vacuously by `0 == 0`, so an entry
    whose `killers` list was quietly emptied printed as killed by the test that names it. An empty
    `killers` list is refused by the floor, before anything is built.

## The subject is at HEAD, or nothing runs

A mutation report is a claim about a COMMIT. Every file this harness writes - the three Swift files the
population edits - and the harness's own two files are compared with `git show HEAD:` before the first
build, and the three are compared again afterwards. The TEST files are deliberately NOT guarded: the
red-then-green demonstration a task Log quotes runs the same population against a suite with a test
removed, and a guard there would forbid the only evidence that a new test is what kills a survivor.

## Why the radius and the pins are mutated but not declared

`SUBJECT_MODULES` is one path. `Geo.swift` (the radius, the haversine) and `SkylineRoute.swift` (the pins)
are dependencies: mutated, reported, never claimed. Declaring them would assert a population over
`initialBearingDegrees` and seven pins nothing here measures, and a stated subject wider than the measured
one is the defect the whole ops/mutate/ family exists to refuse.

`--prove-vacuity` replaces every file in Tests/HandoffTests with an empty suite and requires every mutation
to report MISSED - not merely "not caught", which a harness broken in the compile-only direction satisfies.
`--prove-floor` shows the floor refusing on seven arms and staying quiet on the real population; it builds
nothing and writes nothing, patching this module's own globals in memory.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("Sources/Handoff/StraightLineDistance.swift",)

from straightline_mutations import (EQUIVALENT, GEO, MIN_EQUIVALENT, MIN_MUTATIONS, MIN_TEST_FILES,
                                    MUTATIONS, MUTATED_FILES, ROOT, SKYLINE, SUBJECT, TEST_DIR)

TESTS = sorted(TEST_DIR.glob("*.swift"))
HARNESS = (pathlib.Path(__file__).resolve(),
           pathlib.Path(__file__).resolve().parent / "straightline_mutations.py")

# Under .build/, which .gitignore already excludes, and its own scratch path because this box is shared.
SCRATCH = ".build/mutate-straightline"
# The target whose suites every `killers` entry names. Narrowing the run to it is what keeps a population
# of ten mutations inside one sitting; a killer outside it would be refused by the floor below.
FILTER = "HandoffTests"

# A catch is a NAMED test recording an issue, and group 1 is that name. Swift Testing prints
#   x Test "the whole-mile figure is ..." recorded an issue at StraightLineDistanceTests.swift:95:9: ...
# for a display-named test and `Test theFigureIsFloored() recorded an issue` for one without. ASCII only:
# the failure glyph is U+00D7 and a pattern matching it mis-decodes on this Windows console (handoff.py's
# history - every real catch classified as compile-only).
FAIL_LINE = re.compile(r'Test\s+(?:"([^"]*)"|([A-Za-z_]\w*\(\)))\s+recorded an issue')


def failing_test_names(txt: str) -> list:
    """The distinct NAMES that recorded an issue, in order. Empty means nothing named objected."""
    seen = []
    for m in FAIL_LINE.finditer(txt):
        groups = [g for g in (m.groups() or ()) if g]
        name = groups[0] if groups else " ".join(m.group(0).split())[:60]
        if name not in seen:
            seen.append(name)
    return seen


def empty_suite(path: pathlib.Path) -> str:
    """An empty suite named after the file it replaces: two identically-named structs would not compile,
    and a compile failure would make the vacuity proof pass for the wrong reason."""
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (path.stem, path.stem))


def head_bytes(path: pathlib.Path) -> bytes:
    rel = path.resolve().relative_to(ROOT).as_posix()
    out = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:" + rel], capture_output=True)
    if out.returncode != 0:
        raise SystemExit("not in HEAD: %s - a mutation report is a claim about a commit" % rel)
    return out.stdout.replace(b"\r\n", b"\n")


def not_at_head(paths) -> list:
    return [p.resolve().relative_to(ROOT).as_posix() for p in paths
            if p.read_bytes().replace(b"\r\n", b"\n") != head_bytes(p)]


def build() -> int:
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test() -> tuple:
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH, "--filter", FILTER],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


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
                "vacuously, so a mutation nobody is required to catch is not a measurement"
                % ", ".join(nameless))
    edited = {p for _n, p, _o, _w, _k in MUTATIONS}
    if SUBJECT not in edited:
        return ("no MUTATIONS entry edits %s, the one path SUBJECT_MODULES declares. The harness's stated "
                "subject would be wider than what it measures" % SUBJECT.name)
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
    subject_gone = [m for m in base["MUTATIONS"] if m[1] != SUBJECT]
    arms = [
        ("MUTATIONS emptied - a clean sheet over nothing", {"MUTATIONS": []}),
        ("MUTATIONS one short of the floor", {"MUTATIONS": base["MUTATIONS"][:MIN_MUTATIONS - 1]}),
        ("the floor raised to %d against a population of %d" % (MIN_MUTATIONS + 1, len(MUTATIONS)),
         {"MIN_MUTATIONS": MIN_MUTATIONS + 1}),
        ("EQUIVALENT emptied", {"EQUIVALENT": []}),
        ("one entry's killers emptied - 0 red of 0 named", {"MUTATIONS": killers_gone}),
        ("every mutation of the declared subject removed", {"MUTATIONS": subject_gone}),
        ("TESTS globbed down to nothing - vacuity would empty nothing", {"TESTS": []}),
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


def run_all(pristine, population, require_killers: bool):
    """One verdict per mutation, in six mutually exclusive buckets."""
    out = {"caught": [], "wrong_killer": [], "trapped": [], "compile_only": [], "missed": [],
           "skipped": []}
    for entry in population:
        name, path, old, new = entry[0], entry[1], entry[2], entry[3]
        killers = entry[4] if require_killers else []
        text = pristine[path].decode("utf-8")
        if old not in text:
            sys.stdout.write("SKIP        %-62s anchor not found in %s\n" % (name, path.name))
            out["skipped"].append(name)
            continue
        names, code = [], 0
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if path.read_bytes() == pristine[path]:
                sys.stdout.write("SKIP        %-62s mutation did not land\n" % name)
                out["skipped"].append(name)
                continue
            # Built twice before a compile failure is believed: other agents run swift builds on this box
            # concurrently and a transient scratch collision produced a false compile-only verdict once.
            if build() != 0 and build() != 0:
                verdict = "compile_only"
            else:
                code, txt = test()
                names = failing_test_names(txt)
                if not names:
                    verdict = "trapped" if code != 0 else "missed"
                else:
                    red = [k for k in killers if k in names]
                    verdict = "caught" if len(red) == len(killers) else "wrong_killer"
        finally:
            path.write_bytes(pristine[path])
        out[verdict].append(name)
        label = {"caught": "caught", "wrong_killer": "WRONG KILLER", "trapped": "trapped",
                 "compile_only": "compile-only", "missed": "MISSED"}
        note = {"caught": "by: " + " | ".join(names) if names else "no test objected",
                "wrong_killer": "named %s; red were %s" % (killers, names[:3]),
                "trapped": "non-zero exit, but NO named test failed - DOES NOT COUNT",
                "compile_only": "a fact about Swift, not about these tests - DOES NOT COUNT",
                "missed": "exit=%d  no test objected" % code}
        sys.stdout.write("%-14s%-62s %s\n" % (label[verdict], name, note[verdict]))
    return out


def main(argv) -> int:
    if "--prove-floor" in argv:
        return prove_floor()
    prove = "--prove-vacuity" in argv
    only = [a.split("=", 1)[1] for a in argv if a.startswith("--only=")]
    refusal = population_floor()
    if refusal is not None:
        sys.stdout.write("REFUSING TO RUN: %s\n"
                         "  A truncated harness satisfies `caught == len(MUTATIONS)` trivially, which is\n"
                         "  how a green run over nothing gets reported as coverage.\n" % refusal)
        return 2

    chosen = MUTATIONS
    if only:
        picked = {int(i) for part in only for i in part.split(",")}
        chosen = [m for i, m in enumerate(MUTATIONS, 1) if i in picked]
        sys.stdout.write("PARTIAL RUN over %d of %d mutations (--only). This is the red-then-green\n"
                         "  demonstration a task Log quotes; it never prints MUTATE OK and is never an\n"
                         "  acceptance command.\n" % (len(chosen), len(MUTATIONS)))
    sys.stdout.write("population  mutations=%d (floor %d)  equivalent=%d (floor %d)  subject=%s  "
                     "test files=%d\n" % (len(MUTATIONS), MIN_MUTATIONS, len(EQUIVALENT), MIN_EQUIVALENT,
                                          SUBJECT.name, len(TESTS)))
    sys.stdout.write("dependencies mutated, never declared: %s, %s\n" % (GEO.name, SKYLINE.name))

    dirty = not_at_head(list(MUTATED_FILES) + list(HARNESS))
    if dirty:
        sys.stdout.write("REFUSING: not what HEAD says it is: %s\n"
                         "  A mutant left on disk reads as pristine and the run certifies it; a mutation\n"
                         "  body weakened on disk measures nothing either.\n" % ", ".join(dirty))
        return 2
    pristine = {f: f.read_bytes() for f in MUTATED_FILES}
    pristine_tests = {t: t.read_bytes() for t in TESTS}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-30s md5 %s  == HEAD\n" % (f.name, hashlib.md5(b).hexdigest()))

    eq = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: every file in Tests/HandoffTests is replaced by an empty\n"
                             "suite, so every mutation must report MISSED - not merely 'not caught'.\n")
            for t in TESTS:
                t.write_text(empty_suite(t), encoding="utf-8", newline="\n")
        if build() != 0 and build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, txt = test()
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
    sys.stdout.write("\nrestored, md5 " + ", ".join("%s %s" % (f.name, hashlib.md5(f.read_bytes()).hexdigest())
                                                    for f in MUTATED_FILES) + "\n")
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

    if prove:
        ok = len(r["caught"]) == 0 and len(r["missed"]) == len(MUTATIONS)
        sys.stdout.write("VACUITY PROOF %s: with the %d test file(s) emptied, caught=%d (need 0) and\n"
                         "  MISSED=%d of %d. Requiring MISSED to be COMPLETE, not just caught==0, is what\n"
                         "  stops a harness broken in the compile-only direction proving its own vacuity.\n"
                         % ("OK" if ok else "FAILED", len(TESTS), len(r["caught"]), len(r["missed"]),
                            len(MUTATIONS)))
        return 0 if ok else 1
    if only:
        ok = len(r["caught"]) == len(chosen)
        sys.stdout.write("PARTIAL %s: %d of %d selected mutations caught by the test that names it\n"
                         % ("OK" if ok else "FAILED", len(r["caught"]), len(chosen)))
        return 0 if ok else 1

    eq_caught = 0 if eq is None else len(eq["caught"]) + len(eq["wrong_killer"])
    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; anything else means a\n"
                         "  test has an opinion about how the code is WRITTEN rather than what it DOES,\n"
                         "  or that the harness is stale and 'correctly not caught' is not evidence.\n"
                         % (0 if eq is None else len(eq["missed"]), len(EQUIVALENT)))
    ok = len(r["caught"]) == len(MUTATIONS) and eq_ok
    sys.stdout.write("MUTATE %s  caught=%d/%d equivalent_caught=%d\n"
                     % ("OK" if ok else "FAILED", len(r["caught"]), len(MUTATIONS), eq_caught))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
