"""The mutant runner for ops/mutate/straightline.py: what a build is, what a catch is, and the six
mutually exclusive buckets one mutation can land in.

Split out of straightline.py under CLAUDE.md's 300-line cap, the way budget_arms.py and geometry_tree.py
are split out of their drivers: straightline.py keeps the CLI, the floors and the proof arms - everything
that decides whether a run is ALLOWED to happen - and this file is the machinery that runs one mutation and
classifies what came back. ops/lib/check-mutate-population.py reads the whole `straightline*.py` family as
one driver's code, so a function moved here has not moved out of that gate's sight, and this file carries no
`__main__` block: it is not a second driver.

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

A mutation report is a claim about a COMMIT. `not_at_head` is what the driver compares the three mutated
Swift files and its own three harness files with before the first build, and the three again afterwards.
The TEST files are deliberately NOT guarded: the red-then-green demonstration a task Log quotes runs the
same population against a suite with a test removed, and a guard there would forbid the only evidence that
a new test is what kills a survivor.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# No bytecode, for straightline.py's reason: a population edited and restored inside one second imports
# from a .pyc that matches on mtime and size while every tree guard reports the file clean.
sys.dont_write_bytecode = True

from straightline_mutations import ROOT

# Under .build/, which .gitignore already excludes, and its own scratch path because this box is shared.
SCRATCH = ".build/mutate-straightline"
# The target whose suites every `killers` entry names. Narrowing the run to it is what keeps a population
# of eleven mutations inside one sitting; a killer outside it would be refused by the floor.
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
