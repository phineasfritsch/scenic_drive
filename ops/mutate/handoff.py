"""Mutation harness for Sources/Handoff. Every mutation must be caught by a NAMED TEST, not by a build error.

## Why this is in ops/ and not in .artifacts/

It was in `.artifacts/`, which `.gitignore` excludes, while the task's `acceptance:` list named it as the
command that proves the tests are not vacuous. A reviewer pointed out the consequence: from a fresh clone
the acceptance line is unrunnable, and the red evidence disappears with the author's private worktree. Red
evidence that only exists on the machine that produced it is the same shape as no red evidence.

## Why a non-zero exit is not enough

The first version counted ANY non-zero `swift test` as "caught". A mutation that does not compile also exits
non-zero, so a harness scored that way can report 8 of 8 while proving nothing about the tests - it would
give the same answer if every test were deleted. Here each mutation is BUILT first: if it fails to compile
it is reported as `compile-only` and does NOT count as caught, because a compiler error is a fact about
Swift and not about this suite.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "Handoff" / "AppleMapsDirections.swift"
SCRATCH = ".build-mutate-handoff"

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

    ("lose the sign on a southern or western coordinate",
     'return (negative ? "-" : "") + String(whole) + "." + digits',
     'return String(whole) + "." + digits'),

    ("stop zero-padding the fraction",
     "        while digits.count < coordinateDecimals { digits = \"0\" + digits }",
     "        // padding removed"),
]

# ASCII only, deliberately. Swift Testing marks a failing test with U+00D7, and the first version of this
# line matched on that glyph. It reported all twelve mutations as `compile-only`, because `subprocess` was
# decoding the child's UTF-8 output with the Windows code page and the glyph arrived mangled - a harness
# that silently classified every real catch as a non-catch. Both halves are fixed (the runs below decode as
# UTF-8), but the pattern stays ASCII so no decoding question can reach it again.
# "recorded an issue" is what Swift Testing prints for each failed expectation.
FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def build():
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def main() -> int:
    pristine = SRC.read_bytes()
    sys.stdout.write("pristine %s md5 %s\n" % (SRC.name, hashlib.md5(pristine).hexdigest()))

    if build() != 0:
        sys.stdout.write("baseline does not build; nothing below would mean anything\n")
        return 2
    code, out = test()
    sys.stdout.write("BASELINE                                                      exit=%d\n" % code)
    if code != 0:
        sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
        return 2

    text = pristine.decode("utf-8")
    caught, compile_only, missed = 0, [], []
    for name, old, new in MUTATIONS:
        if old not in text:
            sys.stdout.write("SKIP        %-56s anchor not found - harness stale\n" % name)
            missed.append(name)
            continue
        try:
            SRC.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
            if SRC.read_bytes() == pristine:
                sys.stdout.write("SKIP        %-56s mutation did not land\n" % name)
                missed.append(name)
                continue
            built = build()
            if built != 0:
                verdict, code, out = "compile-only", built, ""
            else:
                code, out = test()
                verdict = "caught" if FAIL_LINE.search(out) else ("nonzero" if code != 0 else "MISSED")
        finally:
            SRC.write_bytes(pristine)

        if verdict == "caught":
            caught += 1
            sys.stdout.write("caught      %-56s exit=%d\n" % (name, code))
        elif verdict == "compile-only":
            compile_only.append(name)
            sys.stdout.write("compile-only%-56s exit=%d  NOT a test catch\n" % (" " + name, code))
        elif verdict == "nonzero":
            compile_only.append(name)
            sys.stdout.write("nonzero     %-56s exit=%d  no named test failed\n" % (name, code))
        else:
            missed.append(name)
            sys.stdout.write("MISSED      %-56s exit=0  no test objected\n" % name)

    if SRC.read_bytes() != pristine:
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine\n")
        return 2
    sys.stdout.write("\nrestored, md5 %s\n" % hashlib.md5(SRC.read_bytes()).hexdigest())
    sys.stdout.write("caught by a named test: %d   compile-only: %d   MISSED: %d   of %d\n"
                     % (caught, len(compile_only), len(missed), len(MUTATIONS)))
    for n in compile_only:
        sys.stdout.write("  compile-only: %s\n" % n)
    for n in missed:
        sys.stdout.write("  MISSED: %s\n" % n)
    return 0 if caught == len(MUTATIONS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
