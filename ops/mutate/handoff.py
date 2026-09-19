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
calls not a catch. The pass condition is now `caught == len(MUTATIONS)`, full stop. A trap, a compile
failure and a stale anchor are each reported and each fail the run. Three consequences, all deliberate:

  * a trap is a real detection but not by a check, so it does not count: either the test that should have
    caught it is missing or the mutation is a poor one, and both need a person;
  * `--prove-vacuity` requires `caught == 0` AND `missed == len(MUTATIONS)`. Requiring only `caught == 0`
    would also be satisfied by a harness broken in the compile-only direction, which is this file's own
    documented history rather than a hypothetical;
  * the EQUIVALENT arm requires its mutants to go MISSED specifically, not merely "not caught": a stale
    anchor or a mutant that fails to compile would otherwise read as "correctly not caught".

SKIP is its own bucket and is never folded into MISSED. A mutation that did not land says the harness is
stale, which is the opposite of what MISSED means.

## The subject is the module, and now that is true

The header said "Mutation harness for Sources/Handoff" while `SRC` named `AppleMapsDirections.swift` and
nothing else, so `HandoffError.swift` - public API, `Equatable` with associated values and a
`CustomStringConvertible` description - had zero mutation coverage and zero assertions behind it. A name
that claims more than the thing underneath it covers is the defect this whole task keeps re-filing, and it
was in the harness written to find it. `SUBJECTS` is now a list, mutations name the file they edit, and
`population_floor()` REFUSES to run if any subject is mutated by nothing.

## The population floor

A harness with an empty `MUTATIONS` list passes `caught == len(MUTATIONS)` trivially, exactly the way
`test -z "$(...)"` over an empty file list passed for `ops/lib/check-exec-bits` until a reviewer noticed.
That check answered with `MIN_FILES`; this one answers with `MIN_MUTATIONS`, `MIN_EQUIVALENT`,
`MIN_TEST_FILES` and the per-subject coverage check. Below any of those the run REFUSES (exit 2) instead of
reporting success over nothing. `--prove-floor` demonstrates that refusal on five arms and a clean control,
because a check never seen red is untested - and it lives here rather than in a gitignored scratch script,
which is the mistake this task's `acceptance:` list already made once.

## Mutations that create files

Some defects are not an edit to an existing line. `Package.swift` declares `path: "Sources/Handoff"`, which
SwiftPM compiles RECURSIVELY, so a locale-bearing helper in `Sources/Handoff/Fmt/point.swift` is live code
- and the source-text checks read one directory and could not see it. An edit-only harness cannot express
that, so an edit whose `old` is None CREATES the file instead, and the cleanup deletes it and any directory
it had to make.

Run with `--prove-vacuity` to check the harness itself: every file in Tests/HandoffTests is replaced by an
empty suite and every mutation must report MISSED.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "Sources" / "Handoff"
SRC = SRC_DIR / "AppleMapsDirections.swift"
ERR = SRC_DIR / "HandoffError.swift"
SUBJECTS = [SRC, ERR]

# What this population covers, repo-relative, for ops/lib/check-mutate-population.py (P-PROC-06).
SUBJECT_MODULES = ("Sources/Handoff/AppleMapsDirections.swift", "Sources/Handoff/HandoffError.swift")

TEST_DIR = ROOT / "Tests" / "HandoffTests"
# GLOBBED, not listed. The hardcoded list was three files; the suite has since split to six, and a reviewer
# showed that a file outside the list still catches mutations during `--prove-vacuity`, which made the proof
# fail loudly - the right direction, but only because somebody looked. A glob cannot fall behind a split.
TESTS = sorted(TEST_DIR.glob("*.swift"))

# Under .build/, which .gitignore already excludes. The previous value, `.build-mutate-handoff`, matched no
# ignore rule (`.gitignore` has `.build/`, not `.build-*/`), so every run left the working tree dirty and a
# reviewer filed it. Still its own scratch path, which CLAUDE.md requires on a shared box.
SCRATCH = ".build/mutate-handoff"

# Floors. Each one is the population below which this harness is not measuring the module it names.
MIN_MUTATIONS = 30
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 3


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
CAP_LINE = "if waypoints.count > Self.maxWaypoints {"
PAIR_LINE = 'return "\\(decimal(c.latitude)),\\(decimal(c.longitude))"'
THROW_LINE = "throw HandoffError.notACoordinate(latitude: c.latitude, longitude: c.longitude)"
TOO_MANY_DESC = ('            return "\\(count) waypoints exceeds the \\(max) this builder will pin; "\n'
                 '                + "select decision points upstream rather than truncating here"')
TOO_MANY_HEAD = '"\\(count) waypoints exceeds the \\(max) this builder will pin; "'
NOT_A_COORD_DESC = 'return "not a coordinate: \\(latitude), \\(longitude)"'
CSD_EXTENSION = "extension HandoffError: CustomStringConvertible {"

# The subdirectory arm. `LOCALE_HELPER` does not exist in the tree; the mutation creates it, and the
# call-site edit is what makes it live rather than dead code the compiler might not even emit.
LOCALE_HELPER = SRC_DIR / "Fmt" / "point.swift"
LOCALE_HELPER_BODY = ('import Foundation\n'
                      '\n'
                      'func localeDecimalPoint() -> String { NumberFormatter().decimalSeparator ?? "." }\n')

# Each mutation is (name, [(path, old, new), ...]). `old is None` CREATES `path` with `new` as its contents.
MUTATIONS = [
    ("truncate instead of refusing",
     [(SRC,
       "        if waypoints.count > Self.maxWaypoints {\n"
       "            throw HandoffError.tooManyWaypoints(count: waypoints.count, max: Self.maxWaypoints)\n"
       "        }",
       "        let waypoints = Array(waypoints.prefix(Self.maxWaypoints))")]),

    ("reverse the waypoint order",
     [(SRC, "        for w in waypoints {", "        for w in waypoints.reversed() {")]),

    ("sort the waypoints, losing the route order",
     [(SRC, "        for w in waypoints {",
       "        for w in waypoints.sorted(by: { $0.latitude < $1.latitude }) {")]),

    ("raise the cap from 9 to 99",
     [(SRC, "public static let maxWaypoints = 9", "public static let maxWaypoints = 99")]),

    ("lower the cap from 9 to 8",
     [(SRC, "public static let maxWaypoints = 9", "public static let maxWaypoints = 8")]),

    ("go back to the archived daddr scheme",
     [(SRC, DEST_ITEM, 'items.append(URLQueryItem(name: "daddr", value: try Self.pair(destination)))')]),

    ("helpfully ask Apple to avoid highways",
     [(SRC, MODE_ITEM, MODE_ITEM + '\n        items.append(URLQueryItem(name: "avoid", value: "highways"))')]),

    ("apply the 2-decimal privacy rule that governs OUR server, not this URL",
     [(SRC, "public static let coordinateDecimals = 5", "public static let coordinateDecimals = 2")]),

    ("off-by-one on the cap, silently dropping a decision point",
     [(SRC, CAP_LINE, "if waypoints.count >= Self.maxWaypoints {")]),

    ("drop the range check and keep only the NaN check",
     [(SRC,
       "        guard c.latitude.isFinite, c.longitude.isFinite,\n"
       "              c.latitude >= -90, c.latitude <= 90,\n"
       "              c.longitude >= -180, c.longitude <= 180 else {",
       "        guard c.latitude.isFinite, c.longitude.isFinite else {")]),

    ("truncate the coordinate instead of rounding it",
     [(SRC, "let scaled = (v * Double(scale)).rounded()",
       "let scaled = (v * Double(scale)).rounded(.towardZero)")]),

    ("round half to even instead of half away from zero",
     [(SRC, "let scaled = (v * Double(scale)).rounded()",
       "let scaled = (v * Double(scale)).rounded(.toNearestOrEven)")]),

    ("lose the sign on a southern or western coordinate",
     [(SRC, RETURN_LINE, 'return String(whole) + "." + digits')]),

    ("stop zero-padding the fraction",
     [(SRC, '        while digits.count < coordinateDecimals { digits = "0" + digits }',
       "        // padding removed")]),

    ("swap latitude and longitude in the pair",
     [(SRC, PAIR_LINE, 'return "\\(decimal(c.longitude)),\\(decimal(c.latitude))"')]),

    # --- reviewer2-pr70's mutations. Every one of these was green against the 30-test suite, and the third
    # --- is a URL telling Apple Maps the drive starts where it ends.
    ("emit the source under another documented name",
     [(SRC, SOURCE_ITEM, 'items.append(URLQueryItem(name: "start", value: try Self.pair(source)))')]),

    ("emit source-place-id instead of source",
     [(SRC, SOURCE_ITEM,
       'items.append(URLQueryItem(name: "source-place-id", value: try Self.pair(source)))')]),

    ("validate the source but send the destination coordinate as the source",
     [(SRC, SOURCE_ITEM,
       "_ = try Self.pair(source)\n"
       '            items.append(URLQueryItem(name: "source", value: try Self.pair(destination)))')]),

    ("go back to a locale-consulting formatter, sign preserved",
     [(SRC, SCALE_LINE,
       '        if #available(macOS 10.0, *) {\n'
       '            return String(format: "%.5f", locale: Locale.current, v)\n'
       '        }\n' + SCALE_LINE)]),

    ("change the precision, which the derived scale must follow",
     [(SRC, "public static let coordinateDecimals = 5", "public static let coordinateDecimals = 3")]),

    # --- reviewer3-pr70's mutations. All six were green against the 34-test suite; the first violates the
    # --- first product invariant in CLAUDE.md for every short drive and every first plan.
    ("ask Apple to avoid highways ONLY when there are no waypoints",
     [(SRC, MODE_ITEM,
       MODE_ITEM + "\n"
       "        if waypoints.isEmpty {\n"
       '            items.append(URLQueryItem(name: "avoid", value: "highways"))\n'
       "        }")]),

    ("rename the mode raw values to strings Apple does not document",
     [(SRC, "        case driving, walking, transit, cycling",
       '        case driving = "driving", walking = "walk", transit = "public", cycling = "bike"')]),

    ("reintroduce a locale-derived decimal separator, which is neither String(format: nor Locale",
     [(SRC, RETURN_LINE,
       'let point = NumberFormatter().decimalSeparator ?? "."\n'
       '        return (negative ? "-" : "") + String(whole) + point + digits')]),

    ("promote the first waypoint to source when the caller gave none",
     [(SRC, SOURCE_BLOCK,
       SOURCE_BLOCK + " else if let first = waypoints.first {\n"
       '            items.append(URLQueryItem(name: "source", value: try Self.pair(first)))\n'
       "        }")]),

    ("emit the destination twice",
     [(SRC, DEST_ITEM, DEST_ITEM + "\n        " + DEST_ITEM)]),

    # --- the scale, in both directions. The test named for the scale never fired on a wrong one: its
    # --- assertions held for every scale up to 10^5, so a decade too small was caught only by its neighbours.
    ("a scale one decade too small",
     [(SRC, SCALE_LINE, "        let scale = (1..<coordinateDecimals).reduce(1) { acc, _ in acc * 10 }")]),

    ("a scale one decade too large",
     [(SRC, SCALE_LINE, "        let scale = (0...coordinateDecimals).reduce(1) { acc, _ in acc * 10 }")]),

    # Used to TRAP rather than be caught: the fold ran over `1..<coordinateDecimals`, and `(1..<0)` is a
    # Swift precondition failure. It is a plain catch now, which is what makes the trapped bucket empty
    # rather than tolerated.
    ("round the coordinate away entirely, to zero decimals",
     [(SRC, "public static let coordinateDecimals = 5", "public static let coordinateDecimals = 0")]),

    # --- reviewer4-pr70. Six mutations survived the 41-test suite; these are all six, plus the three
    # --- HandoffError edits that file could not express because it only ever mutated one file.
    ("count the origin as one of the nine pinned stops",
     [(SRC, CAP_LINE, "if waypoints.count + (source == nil ? 0 : 1) > Self.maxWaypoints {")]),

    ("enforce the cap only when the caller gave no origin",
     [(SRC, CAP_LINE, "if source == nil, waypoints.count > Self.maxWaypoints {")]),

    ("normalise the longitude, which turns the antimeridian into the prime meridian",
     [(SRC, PAIR_LINE,
       'return "\\(decimal(c.latitude)),'
       '\\(decimal(c.longitude.truncatingRemainder(dividingBy: 180)))"')]),

    ("swap latitude and longitude, but only in the southern hemisphere",
     [(SRC, PAIR_LINE,
       '        if c.latitude < 0 { return "\\(decimal(c.longitude)),\\(decimal(c.latitude))" }\n'
       "        " + PAIR_LINE)]),

    ("the refusal names the offending coordinate with its arguments swapped",
     [(SRC, THROW_LINE,
       "throw HandoffError.notACoordinate(latitude: c.longitude, longitude: c.latitude)")]),

    ("the too-many-waypoints refusal stops saying how many, and how many are allowed",
     [(ERR, TOO_MANY_DESC, '            return "too many waypoints"')]),

    ("count and max swapped in the refusal message",
     [(ERR, TOO_MANY_HEAD, '"\\(max) waypoints exceeds the \\(count) this builder will pin; "')]),

    ("the not-a-coordinate refusal quotes longitude first",
     [(ERR, NOT_A_COORD_DESC, 'return "not a coordinate: \\(longitude), \\(latitude)"')]),

    ("the not-a-coordinate refusal drops the pair entirely",
     [(ERR, NOT_A_COORD_DESC, 'return "not a coordinate"')]),

    # A hand-written `==` suppresses the synthesised one. Nothing stops compiling and nothing looks wrong,
    # but every `#expect(throws: HandoffError.someCase(...))` in the suite silently stops comparing the
    # numbers in the payload - the assertions weaken without a single test being edited.
    ("Equatable stops comparing the payload, weakening every refusal assertion at once",
     [(ERR, CSD_EXTENSION,
       "extension HandoffError {\n"
       "    public static func == (a: HandoffError, b: HandoffError) -> Bool {\n"
       "        switch (a, b) {\n"
       "        case (.notACoordinate, .notACoordinate), (.tooManyWaypoints, .tooManyWaypoints):\n"
       "            return true\n"
       "        default:\n"
       "            return false\n"
       "        }\n"
       "    }\n"
       "}\n"
       "\n" + CSD_EXTENSION)]),

    ("a locale-bearing helper one directory down, which SwiftPM compiles and a flat scan cannot see",
     [(LOCALE_HELPER, None, LOCALE_HELPER_BODY),
      (SRC, RETURN_LINE,
       'return (negative ? "-" : "") + String(whole) + localeDecimalPoint() + digits')]),
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
     [(SRC, SCALE_LINE, "        let scale = 100_000")]),
]

# Mutations this suite is KNOWN not to catch, asserted the other way round.
#
# EMPTY, and that emptiness is the claim: every mutation in MUTATIONS is expected to be caught by a named
# test. An entry here says "no assertion can kill this", which is worse than no entry at all when the reason
# is false - it records a closable gap as a feature. The six survivors reviewer4 found are in MUTATIONS with
# tests behind them, not here.
KNOWN_MISSED = []

# ASCII only, deliberately. Swift Testing marks a failing test with U+00D7, and the first version of this
# line matched on that glyph. It reported every mutation as `compile-only`, because subprocess decoded the
# child's UTF-8 output with the Windows code page and the glyph arrived mangled - a harness silently
# classifying every real catch as a non-catch. Both halves are fixed; the pattern stays ASCII so no decoding
# question can reach it again. If this line is ever broken again, every mutation lands in `trapped` and the
# run now FAILS instead of passing.
FAIL_LINE = re.compile(r"recorded an issue|Test run with .*failed")


def population_floor():
    """The reason to refuse, or None. An empty harness must never report success over nothing."""
    if len(MUTATIONS) < MIN_MUTATIONS:
        return "MUTATIONS holds %d entries, below the floor of %d" % (len(MUTATIONS), MIN_MUTATIONS)
    if len(EQUIVALENT) < MIN_EQUIVALENT:
        return "EQUIVALENT holds %d entries, below the floor of %d" % (len(EQUIVALENT), MIN_EQUIVALENT)
    if len(TESTS) < MIN_TEST_FILES:
        return "TESTS globbed %d files from %s, below the floor of %d" % (
            len(TESTS), TEST_DIR.name, MIN_TEST_FILES)
    # MUTATIONS only, deliberately not MUTATIONS + EQUIVALENT. An EQUIVALENT entry asserts that nothing
    # catches it, so a subject "covered" only from that list is still measured by nothing that HAS to be
    # caught - which is the exact shape ("stated subject wider than actual subject") this floor refuses.
    edited = {p for _, edits in MUTATIONS for p, _, _ in edits}
    uncovered = [s.name for s in SUBJECTS if s not in edited]
    if uncovered:
        return ("these subjects are mutated by no MUTATIONS entry: %s. The harness's stated subject would "
                "be wider than what it measures." % ", ".join(uncovered))
    missing = [s.name for s in SUBJECTS if not s.exists()]
    if missing:
        return "these subjects do not exist: %s" % ", ".join(missing)
    return None


def prove_floor() -> int:
    """`--prove-floor`: show the floor REFUSING, one arm at a time, then show the control clean.

    A check that has never been seen red is untested, and CLAUDE.md wants that demonstration in the task log
    - which means it has to be runnable from a fresh clone rather than from a script in the author's
    gitignored `.artifacts/`. That mistake is already in this task's history: an `acceptance:` line named a
    harness under `.artifacts/`, and from a clone the line was unrunnable. So the demonstration lives here.

    Builds nothing and mutates nothing; it only patches this module's own lists in memory.
    """
    base = {"MUTATIONS": list(MUTATIONS), "EQUIVALENT": list(EQUIVALENT), "TESTS": list(TESTS)}
    err_gone = [(n, e) for n, e in base["MUTATIONS"] if all(p != ERR for p, _, _ in e)]
    arms = [
        ("MUTATIONS emptied - reports success over nothing", {"MUTATIONS": []}),
        ("MUTATIONS truncated to 5", {"MUTATIONS": base["MUTATIONS"][:5]}),
        ("EQUIVALENT emptied", {"EQUIVALENT": []}),
        ("TESTS globbed down to 2 - a vacuity proof over part of the suite", {"TESTS": base["TESTS"][:2]}),
        ("every HandoffError mutation removed", {"MUTATIONS": err_gone}),
    ]
    g = globals()
    refused = 0
    control = "prove_floor never reached the control arm"
    try:
        for label, patch in arms:
            g.update(base)
            g.update(patch)
            why = population_floor()
            sys.stdout.write("FLOOR ARM   %-52s %s\n"
                             % (label, why or "NO REFUSAL - THIS ARM FAILED"))
            refused += 1 if why is not None else 0
        g.update(base)
        control = population_floor()
        sys.stdout.write("FLOOR ARM   %-52s %s\n"
                         % ("CONTROL: unpatched", control or "no refusal, as required"))
    finally:
        g.update(base)
    ok = refused == len(arms) and control is None
    sys.stdout.write("FLOOR PROOF %s: %d of %d arms refused and the control did not\n"
                     % ("OK" if ok else "FAILED", refused, len(arms)))
    return 0 if ok else 1


def build() -> int:
    p = subprocess.run(["swift", "build", "--build-tests", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode


def test():
    p = subprocess.run(["swift", "test", "--scratch-path", SCRATCH],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr)


def restore(pristine, created):
    for path, blob in pristine.items():
        path.write_bytes(blob)
    for path in created:
        if path.exists():
            path.unlink()
        # And any directory the mutation had to make, but never a directory that holds a subject.
        d = path.parent
        while d != SRC_DIR and d != ROOT and d.is_dir() and not any(d.iterdir()):
            d.rmdir()
            d = d.parent


def apply_edits(pristine, edits, created):
    """Writes one mutation, recording created paths into `created` AS THEY ARE MADE.

    The list is the caller's so that a failure halfway through still hands the cleanup everything that got
    written - a `return`ed list is lost on the exception, and the leaked file would then be a stray .swift
    inside a SwiftPM target directory.
    """
    landed = False
    for path, old, new in edits:
        if old is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            created.append(path)
            path.write_text(new, encoding="utf-8", newline="\n")
            landed = True
        else:
            path.write_text(pristine[path].decode("utf-8").replace(old, new, 1),
                            encoding="utf-8", newline="\n")
            if path.read_bytes() != pristine[path]:
                landed = True
    return landed


def stale_reason(pristine, edits):
    for path, old, new in edits:
        if old is None:
            if path.exists():
                return "%s already exists, so creating it would measure nothing" % path.name
        elif path not in pristine:
            return "%s is not a subject of this harness" % path.name
        elif old not in pristine[path].decode("utf-8"):
            return "anchor not found in %s" % path.name
    return None


def run_all(pristine, mutations):
    """One verdict per mutation, in five mutually exclusive buckets."""
    out = {"caught": [], "trapped": [], "compile_only": [], "missed": [], "skipped": []}
    for name, edits in mutations:
        why = stale_reason(pristine, edits)
        if why is not None:
            sys.stdout.write("SKIP        %-62s %s\n" % (name, why))
            out["skipped"].append(name)
            continue
        code, created = 0, []
        try:
            if not apply_edits(pristine, edits, created):
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
            restore(pristine, created)
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
    if "--prove-floor" in argv:
        return prove_floor()

    refusal = population_floor()
    if refusal is not None:
        sys.stdout.write("REFUSING TO RUN: %s\n"
                         "  An empty or truncated harness satisfies `caught == len(MUTATIONS)` trivially,\n"
                         "  which is how a green run over nothing gets reported as coverage.\n" % refusal)
        return 2
    sys.stdout.write("population  mutations=%d (floor %d)  equivalent=%d  known-missed=%d  "
                     "subjects=%d  test files=%d (floor %d)\n"
                     % (len(MUTATIONS), MIN_MUTATIONS, len(EQUIVALENT), len(KNOWN_MISSED),
                        len(SUBJECTS), len(TESTS), MIN_TEST_FILES))

    pristine = {f: f.read_bytes() for f in SUBJECTS}
    pristine_tests = {t: t.read_bytes() for t in TESTS}
    for f, b in pristine.items():
        sys.stdout.write("pristine %-32s md5 %s\n" % (f.name, hashlib.md5(b).hexdigest()))

    eq = None
    known = None
    try:
        if prove:
            sys.stdout.write("PROVING NON-VACUITY: every file in Tests/HandoffTests is replaced by an empty\n"
                             "suite, so every mutation must report MISSED - not merely 'not caught'. A catch\n"
                             "here would mean this harness measures the Swift compiler, not these tests.\n")
            for t in TESTS:
                t.write_text(empty_suite(t), encoding="utf-8", newline="\n")

        # Built TWICE before the baseline is declared broken, for the same reason each mutation is. On this
        # Windows checkout a first build into a fresh scratch directory can fail with "unable to create
        # symbolic link ... I/O error (code: 512)" and succeed immediately after. The mutation loop allowed
        # for that; the baseline did not, so a transient failure aborted the whole run with "baseline does
        # not build" and nothing was ever measured (T-0132, the same defect in every harness here).
        if build() != 0 and build() != 0:
            sys.stdout.write("baseline does not build; nothing below would mean anything\n")
            return 2
        code, _ = test()
        sys.stdout.write("BASELINE                                                              exit=%d\n" % code)
        if code != 0:
            sys.stdout.write("baseline is not green; refusing to call anything a caught mutation\n")
            return 2

        r = run_all(pristine, MUTATIONS)

        if not prove:
            if KNOWN_MISSED:
                sys.stdout.write("\nKNOWN GAPS - claimed unkillable, so a CATCH here is good news and a FAILURE\n")
                known = run_all(pristine, KNOWN_MISSED)
            sys.stdout.write("\nEQUIVALENT MUTANTS - cannot change behaviour, so anything but MISSED is a FAILURE\n")
            eq = run_all(pristine, EQUIVALENT)
    finally:
        restore(pristine, [])
        for t, b in pristine_tests.items():
            t.write_bytes(b)

    dirty = ([f.name for f, b in pristine.items() if f.read_bytes() != b]
             + [t.name for t, b in pristine_tests.items() if t.read_bytes() != b]
             + ([LOCALE_HELPER.name] if LOCALE_HELPER.exists() else []))
    if dirty:
        sys.stdout.write("RESTORE FAILED - the working tree is not pristine: %s\n" % ", ".join(dirty))
        return 2
    sys.stdout.write("\nrestored, md5 " + ", ".join(
        "%s %s" % (f.name, hashlib.md5(f.read_bytes()).hexdigest()) for f in SUBJECTS) + "\n")
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

    known_ok = not KNOWN_MISSED or (known is not None and len(known["missed"]) == len(KNOWN_MISSED))
    if not known_ok:
        sys.stdout.write("KNOWN-GAP ARM FAILED: a gap that closed is good news - move it into MUTATIONS with\n"
                         "  the test that closed it. A gap that SKIPs or fails to compile is not evidence.\n")
    eq_ok = eq is not None and len(eq["missed"]) == len(EQUIVALENT)
    if eq is not None and not eq_ok:
        sys.stdout.write("EQUIVALENT ARM FAILED: %d of %d went MISSED as required; a catch means a test has an\n"
                         "  opinion about how the code is WRITTEN rather than what it DOES.\n"
                         % (len(eq["missed"]), len(EQUIVALENT)))

    # A trap does not count. A compile failure does not count. A stale anchor does not count.
    return 0 if len(r["caught"]) == len(MUTATIONS) and eq_ok and known_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
