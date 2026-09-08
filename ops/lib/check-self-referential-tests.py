"""Find assertions whose expected value comes from the thing they check.

## Why this exists

In one session this defect was found EIGHT times by six different reviewers, and four of those were inside
tests written specifically to close a previous instance of it. The pattern is not carelessness; it is that
the shape is invisible from the inside. When you have just written `maxRatio = 1.0`, writing
`#expect(r <= LearnedCorridorSpeeds.maxRatio)` reads like a check of the clamp. It is a tautology, and it
stays green when the constant moves to 3.0 - which is how a learned corridor came to return an ETA below the
free-flow duration it was handed, with the badge off.

The real instances, all from `git log`:

  #expect(r2 <= LearnedCorridorSpeeds.maxRatio)          maxRatio 1.0 -> 3.0 stayed green
  #expect(out.duration <= out.ceiling)                   a mutated ceiling was invisible
  for n in 1..<LearnedCorridorSpeeds.confidenceThreshold  became an empty range at 1; passed over 0 iterations
  #expect(cN.y == cE.x)                                  both offsets cancelled the function under test
  #expect(abs(pieces.p90 - whole.p90) < 1e-9)            asserted consistency, never correctness

## What it detects, and what it does not

Three shapes, chosen because they can be recognised from the token stream with no false-positive rate worth
arguing about:

  A. **Tautology against a constant.** A comparison in `#expect(...)` where one side is `Type.member` - a
     static member of a type declared under `Sources/` - and the other side is not a literal. True for any
     value the constant takes.
  B. **Both sides of one object.** `#expect(x.a <op> x.b)`, where the same receiver produces the expected
     value and the actual one.
  C. **A range bound taken from the constant under test.** `for i in 0..<Type.member`. Lower the constant
     and the loop body stops running; the test passes over zero iterations.

**NOT detected.** This list is long on purpose: a check whose stated scope quietly exceeds its real one is
the defect it exists to prevent, and every entry below was found by a reviewer rather than volunteered.

  * Two DIFFERENT objects both produced by the code under test - `pieces.p90` against `whole.p90`. Needs
    dataflow, not pattern matching, and one of the real instances above is of exactly this shape.
  * A function call on the left: `#expect(Geo.distanceMeters(a, b) <= Geo.earthRadiusMeters)`. This is
    arguably the most natural way to write the defect, and it is missed.
  * An `#expect(` split across lines by ordinary formatting - the scan is line-by-line.
  * The trailing-closure form, `#expect { ... }`.
  * The expected value hoisted into a local `let` before the assertion.
  * A nested-type constant reached through the outer type, `Type.Limits.ceiling`.
  * A constant reached through a `typealias`; `declared_types` matches struct/class/enum/actor/protocol.
  * A member in SCREAMING_CASE or starting uppercase; MEMBER requires a lowercase first character.
  * XCTest assertions - `XCTAssertEqual`, `XCTAssertLessThanOrEqual` - which are outside the gate entirely.

So P-TEST-02 says "of the three recognised shapes", not "no assertion anywhere". The check is worth having
because it found three real instances a person had already been told about and still could not see; it is
not a proof that none remain.

## The escape hatch

A line ending in `// self-ref-ok: <reason>` is allowed. The reason is required and must be more than a word,
because "the point of an allowlist is that entries are argued for" is the only thing keeping it from
becoming a way to silence the check.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCES = ROOT / "Sources"
TESTS = ROOT / "Tests"

# Refuse to pass over an empty or truncated tree. The pin this implements exists because checks that
# iterate over nothing exit 0; that is the same defect this file is about, one level up.
MIN_TEST_FILES = 3
MIN_TYPES = 3
# The floor that matters: assertions actually EXAMINED. `MIN_TEST_FILES` counts files present, and three
# files containing no assertions at all cleared it - which is the identical defect this task's own Brief
# indicts in ops/lib/check-review-remedy, "counts case blocks ENTERED, not assertions EXECUTED". Found by
# a reviewer, whose evidence was that two of this check's own scaffold files are a single comment line.
MIN_ASSERTIONS = 10

# The reason must be at least two words. The docstring promised that and nothing enforced it, so a
# single character silenced a real finding on the real tree - and a bare `// self-ref-ok:` with no reason
# at all survived a mutation of this very line.
ALLOW = re.compile(r"//\s*self-ref-ok:\s*(?P<reason>\S+(?:\s+\S+)+)\s*$")
# NON-capturing. The first version captured the operator, so `m.group(3)` in the same-object
# rule returned "<=" instead of the second member and the finding printed "out.duration vs
# out.<=". The match was right and the message was nonsense, which is the kind of thing that
# gets a check ignored.
COMPARISON = r"(?:==|!=|<=|>=|<|>)"

# `Type.member` where Type starts uppercase, and member is NOT followed by `(`.
#
# Deliberately not anchored on a list of known type names: a new type must be covered the day it is added,
# not the day somebody remembers to add it here.
#
# The negative lookahead excludes function calls, and it is there because the first version flagged
# `#expect(Geo.distanceMeters(a, b) == Geo.distanceMeters(b, a))` in the existing suite. That is a
# metamorphic symmetry property - two invocations with different arguments - and it is a legitimate and good
# test. Comparing the code against ITSELF is fine; comparing it against a CONSTANT OF ITS OWN is the defect.
MEMBER = r"[A-Z][A-Za-z0-9_]*\.[a-z][A-Za-z0-9_]*(?!\s*\()"
# A LITERAL is anything whose value is written in the test rather than read from the code. The first
# version accepted only decimal/hex/quoted-string/bool/nil, so it flagged three shapes the remedy text
# itself recommends: `== .5`, `== .infinity`, and `== ["a","b"]`. A check that flags its own advice is a
# check that gets switched off.
LITERAL = re.compile(
    r"^-?("
    r"\.\d+([eE][-+]?\d+)?"                 # .5
    r"|\d[\d_]*(\.\d+)?([eE][-+]?\d+)?"     # 1, 1.5, 1e3
    r"|0x[0-9a-fA-F]+"
    r"|\"[^\"]*\""
    r"|\[.*\]"                              # array or dictionary literal
    r"|\.[a-zA-Z_][A-Za-z0-9_]*"             # .infinity, .nan, an enum case
    r"|true|false|nil"
    r")$")

# `#expect(a == b, "why this matters")` takes a trailing message, and this checker reads the right-hand side
# as the REST OF THE LINE, so it captured `b, "why this matters")`. `.rstrip(")").rstrip(",")` cannot remove
# that, so the literal test failed and the CORRECT pinning shape was reported as self-referential. Found by
# reviewer-pr77 on the real tree: `#expect(Geo.earthRadiusMeters == 6_371_008.8, "WGS84 mean radius")` made
# this check exit 1, which takes P-TEST-02 red on correct code written in the style 7 of the 31 existing
# assertions use - and a check that flags correct code is a check that gets switched off.
#
# The comma is REQUIRED, so `== "some string"` is untouched, and the closing bracket of an array literal
# stops `== ["a", "b"]` from matching.
MESSAGE_TAIL = re.compile(r",\s*\"(?:[^\"\\]|\\.)*\"\s*\)?\s*$")


def declared_types() -> set[str]:
    """Type names declared under Sources/. Only these count as 'the thing under test'."""
    out: set[str] = set()
    for f in SOURCES.rglob("*.swift"):
        for m in re.finditer(r"^\s*(?:public\s+|internal\s+|private\s+|final\s+)*"
                             r"(?:struct|class|enum|actor|protocol)\s+([A-Z][A-Za-z0-9_]*)",
                             f.read_text(encoding="utf-8"), re.M):
            out.add(m.group(1))
    return out


def strip_comment(line: str) -> str:
    """Everything before a `//` that is not inside a string literal. Crude but adequate here."""
    in_string = False
    i = 0
    while i < len(line) - 1:
        c = line[i]
        if c == "\\" and in_string:
            i += 2
            continue
        if c == '"':
            in_string = not in_string
        elif c == "/" and line[i + 1] == "/" and not in_string:
            return line[:i]
        i += 1
    return line


def problems_in(path: pathlib.Path, types: set[str]):
    """Return (findings, assertions_examined, suppressed)."""
    found: list[tuple[int, str, str]] = []
    assertions = 0
    suppressed = 0
    text = path.read_text(encoding="utf-8")
    for n, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw).strip()
        if not line:
            continue
        # Suppression is decided AFTER the comment is stripped, and only for a line that is actually an
        # assertion. Searching the raw line let the marker work inside a Swift string literal, and let a
        # marker on a non-assertion line silence nothing while still reading as deliberate.
        is_assertion = "#expect(" in line or "#require(" in line
        if is_assertion:
            assertions += 1
        # The marker must BEGIN the line's trailing comment. Searching anywhere in the raw line let it work
        # from inside a Swift string literal - `// note: write "// self-ref-ok: ..." to suppress` silenced a
        # real finding - and searching the stripped code would never find it at all, since it is a comment.
        # So: take the comment that `strip_comment` removed, and require the marker at its start.
        comment = raw[len(strip_comment(raw)):].strip()
        if comment.startswith("//") and ALLOW.match(comment):
            if is_assertion:
                suppressed += 1
            continue

        # C. A range bound taken from a static member of the code under test.
        # `\b` after MEMBER, which rule A has and this did not. Without it the engine backtracks one
        # character to satisfy the function-call lookahead, so `0..<LambdaSearch.stepCount(4)` was reported
        # as `LambdaSearch.stepCoun` - a symbol that does not exist. Right instinct, nonsense message, which
        # is exactly the failure mode that gets a check ignored.
        for m in re.finditer(r"(?:\.\.<|\.\.\.)\s*(" + MEMBER + r")\b", line):
            owner = m.group(1).split(".")[0]
            if owner in types:
                found.append((n, "range bound taken from the constant under test", m.group(1)))

        if not is_assertion:
            continue

        # A. A comparison against a static member of the code under test, where the other side is not a
        #    literal - so the assertion holds for any value that member takes.
        for m in re.finditer(r"([A-Za-z0-9_.\[\]!?]+)\s*" + COMPARISON + r"\s*(" + MEMBER + r")\b", line):
            lhs, member = m.group(1).strip(), m.group(2)
            if member.split(".")[0] in types and not LITERAL.match(lhs):
                found.append((n, "compared against the constant it checks; true for any value", member))
        # The right-hand side is taken as the REST OF THE LINE rather than through a character class. A
        # class cannot span `["a", "b"]` - it stops at the first space or quote - so an array literal was
        # captured as `[` and failed the literal test, flagging the CORRECT pinning shape. Trailing `)` and
        # `,` are trimmed because the assertion's own closing paren is not part of the value.
        for m in re.finditer(r"(" + MEMBER + r")\s*" + COMPARISON + r"\s*(.+)$", line):
            member = m.group(1)
            rhs = MESSAGE_TAIL.sub("", m.group(2).strip()).strip().rstrip(")").rstrip(",").strip()
            if member.split(".")[0] in types and not LITERAL.match(rhs):
                found.append((n, "compared against the constant it checks; true for any value", member))

        # B. Both sides of one object: the receiver supplies the expected value and the actual one.
        for m in re.finditer(r"\b([a-z][A-Za-z0-9_]*)\.([a-z][A-Za-z0-9_]*)\s*" + COMPARISON
                             + r"\s*\1\.([a-z][A-Za-z0-9_]*)", line):
            if m.group(2) != m.group(3):
                found.append((n, "both sides come from the same object under test",
                              f"{m.group(1)}.{m.group(2)} vs {m.group(1)}.{m.group(3)}"))
    return found, assertions, suppressed


def main(argv: list[str]) -> int:
    types = declared_types()
    files = sorted(TESTS.rglob("*.swift")) if TESTS.is_dir() else []

    if len(files) < MIN_TEST_FILES:
        sys.stdout.write("SELF-REF FAIL: found %d test files, expected at least %d - "
                         "a check that examines nothing exits 0 and proves nothing\n"
                         % (len(files), MIN_TEST_FILES))
        return 2
    if len(types) < MIN_TYPES:
        sys.stdout.write("SELF-REF FAIL: found %d types under Sources/, expected at least %d - "
                         "with no types to recognise, every assertion looks fine\n" % (len(types), MIN_TYPES))
        return 2

    problems = []
    assertions = 0
    suppressed = 0
    for f in files:
        found, seen, quiet = problems_in(f, types)
        assertions += seen
        suppressed += quiet
        for line_no, why, what in found:
            problems.append((f.relative_to(ROOT).as_posix(), line_no, why, what))

    if assertions < MIN_ASSERTIONS:
        sys.stdout.write("SELF-REF FAIL: examined %d assertion(s), expected at least %d - a check that "
                         "reads files without assertions in them proves nothing\n"
                         % (assertions, MIN_ASSERTIONS))
        return 2

    if "--list-types" in argv:
        sys.stdout.write("types under Sources/: " + ", ".join(sorted(types)) + "\n")

    if problems:
        sys.stdout.write("SELF-REF FAIL: %d assertion(s) take their expected value from the code under test\n"
                         % len(problems))
        for path, line_no, why, what in problems:
            sys.stdout.write("  %s:%d  %s\n      %s\n" % (path, line_no, why, what))
        sys.stdout.write("\n  Compare against a value the test computed, or a literal. If the assertion is\n"
                         "  genuinely right as written, end the line with `// self-ref-ok: <why>`.\n")
        return 1

    # The suppression count is printed on purpose. An unqualified "OK" over a tree with silenced findings
    # is the same shape as a green over an empty one.
    sys.stdout.write("SELF-REF OK (%d assertions in %d test files, %d types under Sources/%s)\n"
                     % (assertions, len(files), len(types),
                        ", %d suppressed by self-ref-ok" % suppressed if suppressed else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
