"""Mutation harness for Sources/Handoff. A catch requires a NAMED TEST to fail, not a non-zero exit.

## Why this is in ops/ and not in .artifacts/

It was in `.artifacts/`, which `.gitignore` excludes, while the task's `acceptance:` list named it as the
command proving the tests are not vacuous. From a fresh clone that line was unrunnable and the red evidence
disappeared with the author's private worktree. Red evidence that exists only on the machine that produced
it has the same shape as no red evidence.

## Why a non-zero exit is not enough

The first version counted ANY non-zero `swift test` as "caught". A mutation that does not compile also exits
non-zero, so a harness scored that way would report the same number with every test deleted. Each mutation
is BUILT first; a compile failure is `compile-only` and does not count, because a compiler error is a fact
about Swift and not about this suite. A mutation detected by a TRAP rather than an assertion is reported
separately for the same reason.

Run with `--prove-vacuity` to check the harness itself: it replaces the test file with an empty suite and
requires every mutation to report MISSED.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "Handoff" / "AppleMapsDirections.swift"
TESTS = ROOT / "Tests" / "HandoffTests" / "AppleMapsDirectionsTests.swift"
SCRATCH = ".build-mutate-handoff"

EMPTY_SUITE = ('import Testing\n'
               '@Suite("empty") struct EmptyHandoffSuite {\n'
               '    @Test("nothing") func nothing() { #expect(true) }\n'
               '}\n')

SCALE_LINE = "        let scale = (1..<coordinateDecimals).reduce(10) { acc, _ in acc * 10 }"
SOURCE_ITEM = 'items.append(URLQueryItem(name: "source", value: try Self.pair(source)))'

MUTATIONS = [
    ("truncate instead of refusing",
     "        if waypoints.count > Self.maxWaypoints {\n"
     "            throw HandoffError.tooManyWaypoints(count: waypoints.count, max: Self.maxWaypoints)\n"
     "        }",
     "        let waypoints = Array(waypoints.prefix(Self.maxWaypoints))"),

    ("reverse the waypoint order",
     "        for w in waypoints {",
     "        for w in waypoints.reversed() {"),

    ("sort the waypoints, losing the route order",
     "        for w in waypoints {",
     "        for w in waypoints.sorted(by: { $0.latitude < $1.latitude }) {"),

    ("raise the cap from 9 to 99",
     "public static let maxWaypoints = 9",
     "public static let maxWaypoints = 99"),

    ("lower the cap from 9 to 8",
     "public static let maxWaypoints = 9",
     "public static let maxWaypoints = 8"),

    ("go back to the archived daddr scheme",
     'items.append(URLQueryItem(name: "destination", value: try Self.pair(destination)))',
     'items.append(URLQueryItem(name: "daddr", value: try Self.pair(destination)))'),

    ("helpfully ask Apple to avoid highways",
     'items.append(URLQueryItem(name: "mode", value: mode.rawValue))',
     'items.append(URLQueryItem(name: "mode", value: mode.rawValue))\n'
     '        items.append(URLQueryItem(name: "avoid", value: "highways"))'),

    ("apply the 2-decimal privacy rule that governs OUR server, not this URL",
     "public static let coordinateDecimals = 5",
     "public static let coordinateDecimals = 2"),

    ("off-by-one on the cap, silently dropping a decision point",
     "if waypoints.count > Self.maxWaypoints {",
     "if waypoints.count >= Self.maxWaypoints {"),

    ("drop the range check and keep only the NaN check",
     "        guard c.latitude.isFinite, c.longitude.isFinite,\n"
     "              c.latitude >= -90, c.latitude <= 90,\n"
     "              c.longitude >= -180, c.longitude <= 180 else {",
     "        guard c.latitude.isFinite, c.longitude.isFinite else {"),

    ("truncate the coordinate instead of rounding it",
     "let scaled = (v * Double(scale)).rounded()",
     "let scaled = (v * Double(scale)).rounded(.towardZero)"),

    ("round half to even instead of half away from zero",
     "let scaled = (v * Double(scale)).rounded()",
     "let scaled = (v * Double(scale)).rounded(.toNearestOrEven)"),

    ("lose the sign on a southern or western coordinate",
     'return (negative ? "-" : "") + String(whole) + "." + digits',
     'return String(whole) + "." + digits'),

    ("stop zero-padding the fraction",
     '        while digits.count < coordinateDecimals { digits = "0" + digits }',
     "        // padding removed"),

    ("swap latitude and longitude in the pair",
     'return "\\(decimal(c.latitude)),\\(decimal(c.longitude))"',
     'return "\\(decimal(c.longitude)),\\(decimal(c.latitude))"'),

    # --- reviewer2-pr70's mutations. Every one of these was green against the previous suite, and the
    # --- third is a URL telling Apple Maps the drive starts where it ends.
    ("emit the source under another documented name",
     SOURCE_ITEM,
     'items.append(URLQueryItem(name: "start", value: try Self.pair(source)))'),

    ("emit source-place-id instead of source",
     SOURCE_ITEM,
     'items.append(URLQueryItem(name: "source-place-id", value: try Self.pair(source)))'),

    ("validate the source but send the destination coordinate as the source",
     SOURCE_ITEM,
     "_ = try Self.pair(source)\n"
     '            items.append(URLQueryItem(name: "source", value: try Self.pair(destination)))'),

    ("go back to a locale-consulting formatter, sign preserved",
     SCALE_LINE,
     '        if #available(macOS 10.0, *) {\n'
     '            return String(format: "%.5f", locale: Locale.current, v)\n'
     '        }\n' + SCALE_LINE),

    ("change the precision, which the derived scale must follow",
     "public static let coordinateDecimals = 5",
     "public static let coordinateDecimals = 3"),
]

# Mutations that provably CANNOT change behaviour, and must therefore be MISSED.
#
# Hardcoding the scale is the case that prompted this list. With `coordinateDecimals` at 5 the derived value
# IS 100_000, so the output is byte-identical and no test can tell them apart. It sat in the list above at
# first and reported MISSED - correctly. A harness that demands an equivalent mutant be caught is demanding
# the impossible, and the way a person satisfies it is by anchoring a test on the source text, which
# CLAUDE.md forbids and which would then break on any refactor.
#
# So they are asserted the other way: **a catch here is a FAILURE**, because it means a test has an opinion
# about how the code is written rather than what it does. The protection against hardcoding the scale is
# not this mutation - it is `scaleFollowsTheConstant`, which pins the property that holds for ANY precision
# (the fraction has exactly `coordinateDecimals` digits), so the two-step regression of hardcoding now and
# changing the precision later is caught by the mutation directly above.
EQUIVALENT = [
    ("hardcode the scale to the value coordinateDecimals currently derives",
     SCALE_LINE,
     "        let scale = 100_000"),
]

# ASCII only, deliberately. Swift Testing marks a failing test with U+00D7, and the first version of this
# line matched on that glyph. It reported every mutation as `compile-only`, because subprocess decoded the
# child's UTF-8 output with the Windows code page and the glyph arrived mangled - a harness silently
# classifying every real catch as a non-catch. Both halves are fixed; the pattern stays ASCII so no decoding
# question can reach it again.
FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def build():
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def run_all(text, pristine, mutations=None):
    caught, compile_only, missed, trapped = 0, [], [], []
    for name, old, new in (mutations or MUTATIONS):
        if old not in text:
            sys.stdout.write("SKIP        %-58s anchor not found - harness stale\n" % name)
            missed.append(name)
            continue
        try:
            SRC.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if SRC.read_bytes() == pristine:
                sys.stdout.write("SKIP        %-58s mutation did not land\n" % name)
                missed.append(name)
                continue
            # Built twice before a compile failure is believed: other agents run swift builds on this box
            # concurrently, and a transient scratch collision produced a false compile-only verdict once.
            if build() != 0 and build() != 0:
                verdict, code = "compile-only", 1
            else:
                code, out = test()
                if FAIL_LINE.search(out):
                    verdict = "caught"
                elif code != 0:
                    verdict = "trapped"
                else:
                    verdict = "MISSED"
        finally:
            SRC.write_bytes(pristine)

        if verdict == "caught":
            caught += 1
            sys.stdout.write("caught      %-58s exit=%d\n" % (name, code))
        elif verdict == "trapped":
            trapped.append(name)
            sys.stdout.write("trapped     %-58s the code trapped; no assertion fired\n" % name)
        elif verdict == "compile-only":
            compile_only.append(name)
            sys.stdout.write("compile-only%-58s NOT a test catch\n" % (" " + name))
        else:
            missed.append(name)
            sys.stdout.write("MISSED      %-58s exit=0  no test objected\n" % name)
    return caught, compile_only, missed, trapped


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    wrongly_caught = []
    pristine = SRC.read_bytes()
    pristine_tests = TESTS.read_bytes()
    sys.stdout.write("pristine %s md5 %s\n" % (SRC.name, hashlib.md5(pristine).hexdigest()))

    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: the test file is replaced by an empty suite, so every\n"
                             "mutation must report MISSED. A catch here would mean this harness measures\n"
                             "the Swift compiler rather than these tests.\n")
            TESTS.write_text(EMPTY_SUITE, encoding="utf-8", newline="\n")

        if build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _ = test()
        sys.stdout.write("BASELINE                                                        exit=%d\n" % code)
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2

        caught, compile_only, missed, trapped = run_all(pristine.decode("utf-8"), pristine)

        # The equivalent mutants, asserted the other way round: a catch here is a failure.
        wrongly_caught = []
        if not prove:
            sys.stdout.write("\nEQUIVALENT MUTANTS - these cannot change behaviour, so a catch is a FAILURE\n")
            eq_caught, _, _, _ = run_all(pristine.decode("utf-8"), pristine, mutations=EQUIVALENT)
            if eq_caught:
                wrongly_caught = [n for n, _, _ in EQUIVALENT]
    finally:
        SRC.write_bytes(pristine)
        TESTS.write_bytes(pristine_tests)

    if SRC.read_bytes() != pristine or TESTS.read_bytes() != pristine_tests:
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2
    sys.stdout.write("\nrestored, md5 %s\n" % hashlib.md5(SRC.read_bytes()).hexdigest())
    sys.stdout.write("caught by a named test: %d   trapped: %d   compile-only: %d   MISSED: %d   of %d\n"
                     % (caught, len(trapped), len(compile_only), len(missed), len(MUTATIONS)))
    for n in wrongly_caught:
        sys.stdout.write("  WRONGLY CAUGHT (equivalent mutant): %s\n" % n)
    for n in trapped:
        sys.stdout.write("  trapped (detected, but by a crash and not an assertion): %s\n" % n)
    for n in compile_only:
        sys.stdout.write("  compile-only: %s\n" % n)
    for n in missed:
        sys.stdout.write("  MISSED: %s\n" % n)

    if prove:
        ok = caught == 0
        sys.stdout.write("VACUITY PROOF %s: with no tests present, %d mutations were reported caught\n"
                         % ("OK" if ok else "FAILED", caught))
        return 0 if ok else 1
    return 0 if caught + len(trapped) == len(MUTATIONS) and not wrongly_caught else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
