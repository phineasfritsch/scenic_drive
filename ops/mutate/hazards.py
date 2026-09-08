#!/usr/bin/env python3
"""Mutation harness for the hazard strip. A catch requires a NAMED TEST to fail, not a non-zero exit.

Shape settled by five rounds of review on the sibling harnesses:

  * each mutation is BUILT first, and a compile failure is `compile-only` and does not count, because a
    compiler error is a fact about Swift and not about this suite;
  * a mutation detected by a TRAP rather than an assertion is reported separately AND DOES NOT COUNT - a
    crash is the suite noticing, but not through a check;
  * EQUIVALENT mutants are asserted the OTHER WAY ROUND: they cannot change behaviour, so a catch there is
    a FAILURE, because it means a test has an opinion about how the code is written rather than what it
    does - and the way a person satisfies such a demand is by anchoring a test on source text;
  * `--prove-vacuity` replaces the test file with an empty suite and requires every mutation to report
    MISSED, which is the only evidence that the harness measures these tests rather than the compiler.

The pass condition is `caught == len(MUTATIONS)`, and that is a CORRECTION. This file first shipped with
`caught + len(trapped) == len(MUTATIONS)`, copied from its siblings, and the reviewer of PR #70 showed what
that buys: with the subject pristine and only a harness's own FAIL_LINE regex broken, every mutation scores
`trapped` and the run exits 0 - the harness cannot tell "the subject is covered" from "I am broken". Two
smaller holes went with it and are closed here too: `--prove-vacuity` now requires `MISSED` to be COMPLETE
rather than merely `caught == 0` (a harness broken in the compile-only direction satisfies `caught == 0`,
and that is this repository's documented history, not a hypothetical), and the EQUIVALENT arm requires its
mutants to go MISSED specifically, so a stale anchor or a mutant that fails to compile no longer reads as
"correctly not caught". SKIP is its own bucket for the same reason - a mutation that did not land means the
harness is stale, which is the opposite of what MISSED means.

Roughly half the mutations move a NUMBER or a comparison direction. A reviewer found that every mutation in
an earlier harness was structural - delete a guard, invert a comparison - and not one touched a constant,
which is exactly where such a suite is blind.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
STRIP = ROOT / "Sources" / "ScenicKit" / "Hazards" / "HazardStrip.swift"
FLAG = ROOT / "Sources" / "ScenicKit" / "Hazards" / "HazardFlag.swift"
TESTS = ROOT / "Tests" / "ScenicKitTests" / "HazardStripTests.swift"
SCRATCH = ".build-mutate-hazards"

EMPTY_SUITE = ('import Testing\n'
               '@Suite("empty") struct EmptyHazardSuite {\n'
               '    @Test("nothing") func nothing() { #expect(true) }\n'
               '}\n')

MUTATIONS = [
    # --- the thresholds -------------------------------------------------------------------------------
    ("surface threshold 2 km -> 0.1, so every rural lane raises it", STRIP,
     "public static let surfaceUnknownMinimumKm = 2.0",
     "public static let surfaceUnknownMinimumKm = 0.1"),

    ("surface threshold 2 km -> 50, so it never fires", STRIP,
     "public static let surfaceUnknownMinimumKm = 2.0",
     "public static let surfaceUnknownMinimumKm = 50.0"),

    ("surface comparison non-strict, so exactly 2 km fires", STRIP,
     "if facts.surfaceUnknownKm > surfaceUnknownMinimumKm {",
     "if facts.surfaceUnknownKm >= surfaceUnknownMinimumKm {"),

    ("no-cell threshold 5 -> 60 minutes", STRIP,
     "public static let noCellMinimumMinutes = 5",
     "public static let noCellMinimumMinutes = 60"),

    ("no-cell comparison strict, so exactly 5 minutes stops firing", STRIP,
     "if facts.noCellMinutes >= noCellMinimumMinutes {",
     "if facts.noCellMinutes > noCellMinimumMinutes {"),

    ("twilight fires on arrival at or before dusk", STRIP,
     "let twilight = facts.civilTwilight, arrival > twilight {",
     "let twilight = facts.civilTwilight, arrival >= twilight {"),

    # --- the ordering, which is the product -----------------------------------------------------------
    ("closures sort last instead of first", FLAG,
     "        case .closure:          return 0",
     "        case .closure:          return 9"),

    ("surface advisory outranks a ford", FLAG,
     "        case .surfaceUnknown:   return 6",
     "        case .surfaceUnknown:   return 0"),

    ("an unrecognised tag sorts below the advisories", FLAG,
     "        case .unrecognised:     return 3",
     "        case .unrecognised:     return 8"),

    ("sort by rank alone, losing the stable order within a severity", STRIP,
     "        return out.enumerated()\n"
     "            .sorted { ($0.element.severityRank, $0.offset) < ($1.element.severityRank, $1.offset) }\n"
     "            .map(\\.element)",
     "        return out.sorted { $0.severityRank > $1.severityRank }"),

    # --- nothing is dropped ---------------------------------------------------------------------------
    ("drop the unclassified tags entirely", STRIP,
     "        for tag in Set(facts.unclassified).sorted() where !tag.isEmpty {\n"
     "            out.append(.unrecognised(tag))\n"
     "        }",
     "        // unclassified dropped"),

    ("stop deduplicating the unknown tags", STRIP,
     "        for tag in Set(facts.unclassified).sorted() where !tag.isEmpty {",
     "        for tag in facts.unclassified where !tag.isEmpty {"),

    ("report a ford as a gate", STRIP,
     "        if facts.hasFord { out.append(.ford) }",
     "        if facts.hasFord { out.append(.gate) }"),

    ("accept a closure with no source", STRIP,
     "        for c in facts.closures where !c.source.isEmpty {",
     "        for c in facts.closures {"),

    ("a clean route gets a reassuring flag", STRIP,
     "        var out: [HazardFlag] = []",
     "        var out: [HazardFlag] = [.unrecognised(\"checked\")]"),
]

# Cannot change behaviour, so a catch here is a FAILURE.
EQUIVALENT = [
    ("reorder two independent appends that cannot collide on rank", STRIP,
     "        if facts.hasFord { out.append(.ford) }\n        if facts.hasGate { out.append(.gate) }",
     "        if facts.hasGate { out.append(.gate) }\n        if facts.hasFord { out.append(.ford) }"),
]

FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def build() -> int:
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def run_all(pristine, mutations):
    """Returns a verdict per mutation. SKIP is its own bucket, never folded into MISSED: a mutation that did
    not land tells you the harness is stale, which is the opposite of what MISSED means."""
    out = {"caught": [], "trapped": [], "compile_only": [], "missed": [], "skipped": []}
    for name, path, old, new in mutations:
        text = pristine[path].decode("utf-8")
        if old not in text:
            sys.stdout.write("SKIP        %-62s anchor not found - harness is stale\n" % name)
            out["skipped"].append(name)
            continue
        try:
            path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if path.read_bytes() == pristine[path]:
                sys.stdout.write("SKIP        %-62s mutation did not land\n" % name)
                out["skipped"].append(name)
                continue
            # Built twice before a compile failure is believed: other agents run swift builds on this box
            # concurrently and a transient scratch collision produced a false compile-only verdict once.
            if build() != 0 and build() != 0:
                verdict, code = "compile_only", 1
            else:
                code, txt = test()
                verdict = "caught" if FAIL_LINE.search(txt) else ("trapped" if code != 0 else "missed")
        finally:
            path.write_bytes(pristine[path])
        out[verdict].append(name)
        label = {"caught": "caught", "trapped": "trapped", "compile_only": "compile-only", "missed": "MISSED"}
        note = {"caught": "exit=%d" % code,
                "trapped": "non-zero exit, but NO named test failed - does not count",
                "compile_only": "a fact about Swift, not about these tests - does not count",
                "missed": "exit=0  no test objected"}
        sys.stdout.write("%-12s%-62s %s\n" % (label[verdict], name, note[verdict]))
    return out


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    pristine = {f: f.read_bytes() for f in (STRIP, FLAG)}
    pristine_tests = TESTS.read_bytes()
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s\n" % (f.name, hashlib.md5(b).hexdigest()))

    eq = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: the test file is replaced by an empty suite, so every\n"
                             "mutation must report MISSED - not merely 'not caught'.\n")
            TESTS.write_text(EMPTY_SUITE, encoding="utf-8", newline="\n")

        if build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _ = test()
        sys.stdout.write("BASELINE                                                              exit=%d\n" % code)
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2

        r = run_all(pristine, MUTATIONS)

        if not prove:
            sys.stdout.write("\nEQUIVALENT MUTANTS - cannot change behaviour, so anything but MISSED is a FAILURE\n")
            eq = run_all(pristine, EQUIVALENT)
    finally:
        for f, b in pristine.items():
            f.write_bytes(b)
        TESTS.write_bytes(pristine_tests)

    if any(f.read_bytes() != b for f, b in pristine.items()) or TESTS.read_bytes() != pristine_tests:
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2

    sys.stdout.write("\nrestored: " + ", ".join(hashlib.md5(f.read_bytes()).hexdigest()[:8] for f in pristine) + "\n")
    sys.stdout.write("caught by a named test: %d of %d   (trapped %d, compile-only %d, MISSED %d, skipped %d)\n"
                     % (len(r["caught"]), len(MUTATIONS), len(r["trapped"]), len(r["compile_only"]),
                        len(r["missed"]), len(r["skipped"])))
    for bucket, why in (("trapped", "detected, but by a crash and not an assertion - DOES NOT COUNT"),
                        ("compile_only", "a compile failure is not a test catch - DOES NOT COUNT"),
                        ("missed", "no test objected"),
                        ("skipped", "anchor missing - the harness is stale")):
        for n in r[bucket]:
            sys.stdout.write("  %s: %s (%s)\n" % (bucket.upper(), n, why))

    if prove:
        ok = len(r["caught"]) == 0 and len(r["missed"]) == len(MUTATIONS)
        sys.stdout.write("VACUITY PROOF %s: with no tests present, caught=%d (need 0) and MISSED=%d of %d\n"
                         "  (requiring MISSED to be complete, not just caught==0, is what stops a harness\n"
                         "   broken in the compile-only direction from proving its own non-vacuity)\n"
                         % ("OK" if ok else "FAILED", len(r["caught"]), len(r["missed"]), len(MUTATIONS)))
        return 0 if ok else 1

    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if not eq_ok and eq is not None:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
