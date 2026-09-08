#!/usr/bin/env python3
"""Mutation harness for the GraphHopper sign mapping. A catch requires a NAMED TEST to fail.

This one is written against a finding filed the same day, by the reviewer of ops/mutate/handoff.py, against
every harness in this repository including its own siblings:

    `return 0 if caught + len(trapped) == len(MUTATIONS)` counts `trapped` toward the pass total, even though
    the file's own docstring says a trap is NOT a catch. Demonstrated: with the harness unmodified and a real
    mutation that traps, the run printed "caught by a named test: 0, trapped: 1" and exited 0. Demonstrated
    again with the subject pristine and the harness's own FAIL_LINE regex broken: "caught: 0, trapped: 3",
    exit 0 - so the harness could not tell "the code is fine and I am broken" from "the code is covered".

So the pass condition here is `caught == len(MUTATIONS)`, full stop. A trap, a compile failure and a stale
anchor are each reported and each fail the run. Three consequences follow, and all three are deliberate:

  * A trap is a real detection, but not by a check, so it does not count. If a mutation only ever traps, either
    the test that should have caught it is missing or the mutation is a poor one - both need a person.
  * `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)`. Requiring only `caught == 0` would
    also be satisfied by a harness broken in the compile-only direction, which is this repository's documented
    history rather than a hypothetical.
  * The EQUIVALENT run checks that its mutants went MISSED specifically - not merely "not caught". A stale
    anchor or a mutant that fails to compile would otherwise read as "correctly not caught".

Roughly half the mutations move a NUMBER, because the subject is an integer table and a structural-only
mutation set is blind exactly where an integer table fails.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SIGN = ROOT / "Sources" / "ScenicKit" / "Guidance" / "GuidanceSign.swift"
MAP = ROOT / "Sources" / "ScenicKit" / "Guidance" / "GuidanceMapping.swift"
TESTS = ROOT / "Tests" / "ScenicKitTests" / "GuidanceMappingTests.swift"
SCRATCH = ".build-mutate-guidance"

EMPTY_SUITE = ('import Testing\n'
               '@Suite("empty") struct EmptyGuidanceSuite {\n'
               '    @Test("nothing") func nothing() { #expect(true) }\n'
               '}\n')

MUTATIONS = [
    # --- the integers, which are the whole point of the type ---------------------------------------------
    ("turnLeft -2 -> -4, a value upstream does not declare", SIGN,
     "    case turnLeft = -2", "    case turnLeft = -4"),

    # Both sides move in ONE edit. Changing only one of a pair produces a DUPLICATE raw value, which Swift
    # rejects - the first version of this mutation did exactly that and scored compile-only, i.e. it tested
    # the compiler rather than the suite. A mutation that cannot compile is not evidence about these tests.
    ("swap the integers for uTurnLeft and keepLeft", SIGN,
     "    case uTurnLeft = -8\n    case keepLeft = -7",
     "    case uTurnLeft = -7\n    case keepLeft = -8"),

    ("keepRight 7 -> 10, off the end of the declared space", SIGN,
     "    case keepRight = 7", "    case keepRight = 10"),

    ("finish 4 <-> reachedVia 5", SIGN,
     "    case finish = 4\n    case reachedVia = 5",
     "    case finish = 5\n    case reachedVia = 4"),

    ("ferry 9 -> 99", SIGN, "    case ferry = 9", "    case ferry = 99"),

    ("ptStartTrip 101 -> 100", SIGN, "    case ptStartTrip = 101", "    case ptStartTrip = 100"),

    ("IGNORE becomes Int64 min instead of Java's 32-bit Integer.MIN_VALUE", SIGN,
     "    case ignore = -2_147_483_648", "    case ignore = -9_223_372_036_854_775_808"),

    ("IGNORE off by one - the single-digit typo a ten-digit literal hides", SIGN,
     "    case ignore = -2_147_483_648", "    case ignore = -2_147_483_649"),

    # NOT "delete the case": removing one breaks the exhaustive switch in GuidanceMapping and scores
    # compile-only. That the deletion cannot compile is the plan's build gate working, and it is demonstrated
    # on its own in the task log rather than counted here as test coverage.
    ("unknown -99 -> -97, a value upstream does not declare", SIGN,
     "    case unknown = -99", "    case unknown = -97"),

    # --- the mapping -------------------------------------------------------------------------------------
    ("a sharp left is reported as a normal left", MAP,
     "        case .turnSharpLeft:     return .turn(side: .left,  sharpness: .sharp)",
     "        case .turnSharpLeft:     return .turn(side: .left,  sharpness: .normal)"),

    ("left and right swapped on the slight turns", MAP,
     "        case .turnSlightLeft:    return .turn(side: .left,  sharpness: .slight)",
     "        case .turnSlightLeft:    return .turn(side: .right, sharpness: .slight)"),

    ("keepLeft reported as a slight left turn", MAP,
     "        case .keepLeft:          return .keep(side: .left)",
     "        case .keepLeft:          return .turn(side: .left, sharpness: .slight)"),

    ("a U-turn of unknown side guesses left", MAP,
     "        case .uTurnUnknown:      return .uTurn(side: nil)",
     "        case .uTurnUnknown:      return .uTurn(side: .left)"),

    ("entering and leaving a roundabout collapse to one instruction", MAP,
     "        case .leaveRoundabout:   return .exitRoundabout",
     "        case .leaveRoundabout:   return .enterRoundabout"),

    ("arrive and waypoint collapse", MAP,
     "        case .finish:            return .arrive",
     "        case .finish:            return .reachedWaypoint"),

    # --- the failure this type exists to prevent ---------------------------------------------------------
    ("an unrecognised sign silently becomes 'carry straight on'", MAP,
     "        guard let sign = GuidanceSign(rawValue: raw) else {\n"
     "            throw GuidanceDecodingError.unrecognisedSign(raw)\n"
     "        }",
     "        guard let sign = GuidanceSign(rawValue: raw) else { return .continueStraight }"),

    ("the thrown error forgets which raw value it was", MAP,
     "            throw GuidanceDecodingError.unrecognisedSign(raw)",
     "            throw GuidanceDecodingError.unrecognisedSign(0)"),

    ("the router's own UNKNOWN collapses into 'carry straight on'", MAP,
     "        case .unknown:           return .routerSaidUnknown",
     "        case .unknown:           return .continueStraight"),

    ("a transit leg is folded into 'carry straight on'", MAP,
     "        case .ptStartTrip, .ptTransfer, .ptEndTrip:\n"
     "            return .notApplicableToDriving",
     "        case .ptStartTrip, .ptTransfer, .ptEndTrip:\n"
     "            return .continueStraight"),

    # --- provenance --------------------------------------------------------------------------------------
    ("the recorded upstream release is changed without re-deriving the table", SIGN,
     'public static let sourceRelease = "11.0"', 'public static let sourceRelease = "10.2"'),

    ("the recorded source blob no longer identifies the bytes the table came from", SIGN,
     'public static let sourceBlob = "1638c71bfd6537d9a57ad0f24fec334e2122eaab"',
     'public static let sourceBlob = "0000000000000000000000000000000000000000"'),
]

# Cannot change behaviour, so a catch here is a FAILURE and anything other than MISSED is a failure too.
EQUIVALENT = [
    ("reorder two independent switch cases", MAP,
     "        case .keepLeft:          return .keep(side: .left)\n"
     "        case .keepRight:         return .keep(side: .right)",
     "        case .keepRight:         return .keep(side: .right)\n"
     "        case .keepLeft:          return .keep(side: .left)"),
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
    pristine = {f: f.read_bytes() for f in (SIGN, MAP)}
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
