"""Mutation harness for Sources/Handoff. A catch requires a NAMED TEST to fail, and nothing else counts.

## Why this is in ops/ and not in .artifacts/

It was in `.artifacts/`, which `.gitignore` excludes, while the task's `acceptance:` list named it as the
command proving the tests are not vacuous. From a fresh clone that line was unrunnable and the red evidence
disappeared with the author's private worktree. Red evidence that exists only on the machine that produced
it has the same shape as no red evidence.

## Why a non-zero exit is not enough, and why `trapped` used to be counted anyway

The first version counted ANY non-zero `swift test` as "caught". A mutation that does not compile also exits
non-zero, so a harness scored that way would report the same number with every test deleted. Each mutation
is BUILT first; a compile failure is `compile-only` and does not count, because a compiler error is a fact
about Swift and not about this suite. A mutation detected by a TRAP rather than an assertion was reported
separately for the same reason - and then the pass condition read

    return 0 if caught + len(trapped) == len(MUTATIONS) and not wrongly_caught else 1

which added `trapped` back into the total, i.e. counted as a pass exactly the thing the paragraph above
calls not a catch. The reviewer of PR #70 demonstrated it twice:

  * unmodified harness, real mutation `coordinateDecimals -> 0`, which trapped in `(1..<0)`:
    "caught by a named test: 0, trapped: 1", exit 0;
  * subject PRISTINE and this file's own FAIL_LINE regex broken: "caught: 0, trapped: 3", exit 0 - so the
    harness could not tell "the subject is covered" from "I am broken".

The pass condition is now `caught == len(MUTATIONS)`, full stop. A trap, a compile failure and a stale
anchor are each reported and each fail the run. Three consequences, all deliberate:

  * a trap is a real detection but not by a check, so it does not count: either the test that should have
    caught it is missing or the mutation is a poor one, and both need a person;
  * `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)`. Requiring only `caught == 0`
    would also be satisfied by a harness broken in the compile-only direction, which is this file's own
    documented history rather than a hypothetical;
  * the EQUIVALENT arm requires its mutants to go MISSED specifically, not merely "not caught": a stale
    anchor or a mutant that fails to compile would otherwise read as "correctly not caught".

SKIP is its own bucket and is never folded into MISSED. A mutation that did not land says the harness is
stale, which is the opposite of what MISSED means.

Run with `--prove-vacuity` to check the harness itself: every HandoffTests file is replaced by an empty
suite and every mutation must report MISSED.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "Handoff" / "AppleMapsDirections.swift"
TEST_DIR = ROOT / "Tests" / "HandoffTests"
TESTS = [TEST_DIR / "AppleMapsDirectionsTests.swift",
         TEST_DIR / "AppleMapsDirectionsURLTests.swift",
         TEST_DIR / "HandoffSourceTests.swift"]

# Under .build/, which .gitignore already excludes. The previous value, `.build-mutate-handoff`, matched no
# ignore rule (`.gitignore` has `.build/`, not `.build-*/`), so every run left the working tree dirty and a
# reviewer filed it. Still its own scratch path, which CLAUDE.md requires on a shared box.
SCRATCH = ".build/mutate-handoff"


def empty_suite(path: pathlib.Path) -> str:
    name = path.stem
    return ('import Testing\n'
            '@Suite("empty %s") struct Empty%s {\n'
            '    @Test("nothing") func nothing() { #expect(true) }\n'
            '}\n' % (name, name))


SCALE_LINE = "        let scale = (0..<coordinateDecimals).reduce(1) { acc, _ in acc * 10 }"
SOURCE_ITEM = 'items.append(URLQueryItem(name: "source", value: try Self.pair(source)))'
DEST_ITEM = 'items.append(URLQueryItem(name: "destination", value: try Self.pair(destination)))'
MODE_ITEM = 'items.append(URLQueryItem(name: "mode", value: mode.rawValue))'
SOURCE_BLOCK = ("        if let source {\n"
                "            " + SOURCE_ITEM + "\n"
                "        }")
RETURN_LINE = 'return (negative ? "-" : "") + String(whole) + "." + digits'

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
     DEST_ITEM,
     'items.append(URLQueryItem(name: "daddr", value: try Self.pair(destination)))'),

    ("helpfully ask Apple to avoid highways",
     MODE_ITEM,
     MODE_ITEM + '\n        items.append(URLQueryItem(name: "avoid", value: "highways"))'),

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
     RETURN_LINE,
     'return String(whole) + "." + digits'),

    ("stop zero-padding the fraction",
     '        while digits.count < coordinateDecimals { digits = "0" + digits }',
     "        // padding removed"),

    ("swap latitude and longitude in the pair",
     'return "\\(decimal(c.latitude)),\\(decimal(c.longitude))"',
     'return "\\(decimal(c.longitude)),\\(decimal(c.latitude))"'),

    # --- reviewer2-pr70's mutations. Every one of these was green against the 30-test suite, and the third
    # --- is a URL telling Apple Maps the drive starts where it ends.
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

    # --- reviewer3-pr70's mutations. All six were green against the 34-test suite; the first violates the
    # --- first product invariant in CLAUDE.md for every short drive and every first plan.
    ("ask Apple to avoid highways ONLY when there are no waypoints",
     MODE_ITEM,
     MODE_ITEM + "\n"
     "        if waypoints.isEmpty {\n"
     '            items.append(URLQueryItem(name: "avoid", value: "highways"))\n'
     "        }"),

    ("rename the mode raw values to strings Apple does not document",
     "        case driving, walking, transit, cycling",
     '        case driving = "driving", walking = "walk", transit = "public", cycling = "bike"'),

    ("reintroduce a locale-derived decimal separator, which is neither String(format: nor Locale",
     RETURN_LINE,
     'let point = NumberFormatter().decimalSeparator ?? "."\n'
     '        return (negative ? "-" : "") + String(whole) + point + digits'),

    ("promote the first waypoint to source when the caller gave none",
     SOURCE_BLOCK,
     SOURCE_BLOCK + " else if let first = waypoints.first {\n"
     '            items.append(URLQueryItem(name: "source", value: try Self.pair(first)))\n'
     "        }"),

    ("emit the destination twice",
     DEST_ITEM,
     DEST_ITEM + "\n        " + DEST_ITEM),

    # --- the scale, in both directions. The test named for the scale never fired on a wrong one: its
    # --- assertions held for every scale up to 10^5, so a decade too small was caught only by its neighbours.
    ("a scale one decade too small",
     SCALE_LINE,
     "        let scale = (1..<coordinateDecimals).reduce(1) { acc, _ in acc * 10 }"),

    ("a scale one decade too large",
     SCALE_LINE,
     "        let scale = (0...coordinateDecimals).reduce(1) { acc, _ in acc * 10 }"),

    # Used to TRAP rather than be caught: the fold ran over `1..<coordinateDecimals`, and `(1..<0)` is a
    # Swift precondition failure. It is a plain catch now, which is what makes the trapped bucket empty
    # rather than tolerated.
    ("round the coordinate away entirely, to zero decimals",
     "public static let coordinateDecimals = 5",
     "public static let coordinateDecimals = 0"),
]

# Mutations that provably CANNOT change behaviour, and must therefore be MISSED.
#
# Hardcoding the scale is the case that prompted this list. With `coordinateDecimals` at 5 the derived value
# IS 100000, so the output is byte-identical and no test can tell them apart. It sat in the list above at
# first and reported MISSED - correctly. A harness that demands an equivalent mutant be caught is demanding
# the impossible, and the way a person satisfies it is by anchoring a test on the source text, which
# CLAUDE.md forbids and which would then break on any refactor.
#
# So they are asserted the other way: anything but MISSED is a FAILURE. A catch means a test has an opinion
# about how the code is written rather than what it does; a SKIP or a compile failure means the harness is
# stale and its "correctly not caught" is not evidence of anything. The protection against hardcoding the
# scale is not this mutation - it is `scaleFollowsTheConstant`, plus the two decade mutations above.
EQUIVALENT = [
    ("hardcode the scale to the value coordinateDecimals currently derives",
     SCALE_LINE,
     "        let scale = 100_000"),
]

# ASCII only, deliberately. Swift Testing marks a failing test with U+00D7, and the first version of this
# line matched on that glyph. It reported every mutation as `compile-only`, because subprocess decoded the
# child's UTF-8 output with the Windows code page and the glyph arrived mangled - a harness silently
# classifying every real catch as a non-catch. Both halves are fixed; the pattern stays ASCII so no decoding
# question can reach it again. If this line is ever broken again, every mutation lands in `trapped` and the
# run now FAILS instead of passing.
FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def build():
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def run_all(pristine, mutations):
    """One verdict per mutation, in five mutually exclusive buckets."""
    out = {"caught": [], "trapped": [], "compile_only": [], "missed": [], "skipped": []}
    text = pristine.decode("utf-8")
    for name, old, new in mutations:
        if old not in text:
            sys.stdout.write("SKIP        %-62s anchor not found - the harness is stale\n" % name)
            out["skipped"].append(name)
            continue
        code = 0
        try:
            SRC.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if SRC.read_bytes() == pristine:
                sys.stdout.write("SKIP        %-62s mutation did not land\n" % name)
                out["skipped"].append(name)
                continue
            # Built twice before a compile failure is believed: other agents run swift builds on this box
            # concurrently, and a transient scratch collision produced a false compile-only verdict once.
            if build() != 0 and build() != 0:
                verdict = "compile_only"
            else:
                code, txt = test()
                verdict = "caught" if FAIL_LINE.search(txt) else ("trapped" if code != 0 else "missed")
        finally:
            SRC.write_bytes(pristine)
        out[verdict].append(name)
        label = {"caught": "caught", "trapped": "trapped",
                 "compile_only": "compile-only", "missed": "MISSED"}
        note = {"caught": "a named test failed, exit=%d" % code,
                "trapped": "non-zero exit, but NO named test failed - DOES NOT COUNT",
                "compile_only": "a fact about Swift, not about these tests - DOES NOT COUNT",
                "missed": "exit=0  no test objected"}
        sys.stdout.write("%-12s%-62s %s\n" % (label[verdict], name, note[verdict]))
    return out


def main(argv) -> int:
    prove = "--prove-vacuity" in argv
    pristine = SRC.read_bytes()
    pristine_tests = {t: t.read_bytes() for t in TESTS}
    sys.stdout.write("pristine %-32s md5 %s\n" % (SRC.name, hashlib.md5(pristine).hexdigest()))

    eq = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: every HandoffTests file is replaced by an empty suite, so\n"
                             "every mutation must report MISSED - not merely 'not caught'. A catch here would\n"
                             "mean this harness measures the Swift compiler rather than these tests.\n")
            for t in TESTS:
                t.write_text(empty_suite(t), encoding="utf-8", newline="\n")

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
        SRC.write_bytes(pristine)
        for t, b in pristine_tests.items():
            t.write_bytes(b)

    if SRC.read_bytes() != pristine or any(t.read_bytes() != b for t, b in pristine_tests.items()):
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2
    sys.stdout.write("\nrestored, md5 %s\n" % hashlib.md5(SRC.read_bytes()).hexdigest())
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
    if eq is not None and not eq_ok:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
