"""The injections: one per clause of a pin's own `statement`, plus the primitives that apply and revert them.

Split from pins_mutation.py because the two change for different reasons. This file grows when a pin is added or
its statement gains a clause; that one changes when the way a run is judged changes.

READ THIS BEFORE ADDING A CASE. The contract is not "make the assertion fail" - `rm -rf Sources` would do that
for six pins at once and prove nothing. The contract is: inject the violation the pin's own `statement` names,
change nothing else, and require the assertion to notice. Each case carries the clause it violates in `clause`;
if you cannot quote a clause, the case is testing your imagination rather than the pin.

Every primitive returns `apply(root) -> revert()` and raises NoOp when the tree no longer contains what the case
expected. NoOp is a failure, never a skip: an injection that silently changes nothing produces a green run that
means nothing, which is the exact defect this task exists to close.

`expect="gap"` marks an injection that is KNOWN to survive today - a hole in the assertion that a filed task
owns. It still runs. If it starts being killed, the run FAILS and tells you to promote it to expect="red" and
delete the exemption, because a stale exemption is a lie about coverage. `gap_task` must name a task that exists
in queue/ and is not yet in done/; pins_mutation.py checks that, so an exemption cannot outlive its ticket.
"""
import re
import subprocess

BANNED = ("CoreLocation", "MapKit", "UIKit", "SwiftUI", "MapLibre", "Ferrostar")
IMPORT_HOST = "Sources/ScenicKit/Model/Coordinate.swift"
TEST_HOST = "Tests/ScenicKitTests/GeoTests.swift"
ORACLE = "Tests/Fixtures/solar/oracle.json"
FIXTURES = "Tests/ScenicKitTests/SolarFixtures.swift"
SOLAR_MATH = "Sources/ScenicKit/Solar/SolarMath.swift"


class NoOp(Exception):
    """The tree no longer contains what this case meant to break."""


def git(root, *args):
    r = subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True)
    if r.returncode != 0:
        raise NoOp(f"git {' '.join(args)}: {(r.stdout + r.stderr).strip()[:200]}")
    return r.stdout


def _read(root, rel):
    p = root / rel
    if not p.is_file():
        raise NoOp(f"{rel} does not exist")
    return p, p.read_text(encoding="utf-8")


def _restorer(p, src):
    return lambda: p.write_text(src, encoding="utf-8", newline="\n")


# ----------------------------------------------------------------------------- primitives
def edit(rel, old, new):
    """Replace every occurrence of `old`. Refuses when `old` is absent - the anchor moved, so does the case."""
    def apply(root):
        p, src = _read(root, rel)
        if old not in src:
            raise NoOp(f"{rel} no longer contains {old!r}")
        p.write_text(src.replace(old, new), encoding="utf-8", newline="\n")
        return _restorer(p, src)
    return apply


def append(rel, text):
    def apply(root):
        p, src = _read(root, rel)
        p.write_text(src.rstrip("\n") + "\n" + text + "\n", encoding="utf-8", newline="\n")
        return _restorer(p, src)
    return apply


def write(rel, text):
    """Overwrite a tracked file wholesale (a floor file, say)."""
    def apply(root):
        p, src = _read(root, rel)
        if src == text:
            raise NoOp(f"{rel} already holds exactly this content")
        p.write_text(text, encoding="utf-8", newline="\n")
        return _restorer(p, src)
    return apply


def remove(rel):
    def apply(root):
        p = root / rel
        if not p.is_file():
            raise NoOp(f"{rel} does not exist")
        data = p.read_bytes()
        p.unlink()
        return lambda: p.write_bytes(data)
    return apply


def keep_first(rel, needle, n):
    """Delete all but the first n lines containing `needle` - genuinely fewer fixtures, not a renamed anchor."""
    def apply(root):
        p, src = _read(root, rel)
        out, seen = [], 0
        for line in src.splitlines(True):
            if needle in line:
                seen += 1
                if seen > n:
                    continue
            out.append(line)
        if seen <= n:
            raise NoOp(f"{rel} has only {seen} line(s) containing {needle!r}; nothing to remove")
        p.write_text("".join(out), encoding="utf-8", newline="\n")
        return _restorer(p, src)
    return apply


def add_tracked(rel, text):
    """Create a file AND stage it. The pins that matter read `git ls-files`, so an untracked file is invisible
    to them - staging is what makes this an injection rather than build junk."""
    def apply(root):
        p = root / rel
        if p.exists():
            raise NoOp(f"{rel} already exists")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
        git(root, "add", "--", rel)

        def revert():
            git(root, "rm", "--cached", "--quiet", "--", rel)
            p.unlink()
        return revert
    return apply


def chmod(rel, flag):
    """Flip the committed mode. core.filemode is false on the Windows checkout, so the index is the only place
    this is visible - which is exactly why P-OPS-01 exists."""
    def apply(root):
        if not git(root, "ls-files", "-s", "--", rel).strip():
            raise NoOp(f"{rel} is not tracked")
        git(root, "update-index", f"--chmod={flag}", "--", rel)
        back = "+x" if flag == "-x" else "-x"
        return lambda: git(root, "update-index", f"--chmod={back}", "--", rel)
    return apply


def untrack(rels):
    """Drop paths from the index, restoring their exact modes afterwards. This is how a floor gets tested: the
    file set the check scans goes below its MIN_FILES."""
    def apply(root):
        modes = {}
        for rel in rels:
            out = git(root, "ls-files", "-s", "--", rel).strip()
            if not out:
                raise NoOp(f"{rel} is not tracked")
            modes[rel] = out.split()[0]
        git(root, "rm", "--cached", "--quiet", "--", *rels)

        def revert():
            git(root, "add", "--", *rels)
            for rel, mode in modes.items():
                git(root, "update-index", f"--chmod={'+x' if mode == '100755' else '-x'}", "--", rel)
        return revert
    return apply


def _done_task(root):
    files = sorted((root / "queue" / "done").glob("T-*.md"))
    if not files:
        raise NoOp("queue/done/ holds no task to corrupt")
    return files[0]


def reviewer(value):
    """Set `reviewer:` on the first done/ task. value None writes null; "owner" writes its own owner."""
    def apply(root):
        p = _done_task(root)
        src = p.read_text(encoding="utf-8")
        m = re.search(r"(?m)^owner:[ \t]*(\S.*)$", src)
        if not m:
            raise NoOp(f"{p.name} has no owner: field")
        new = m.group(1).strip() if value == "owner" else "null"
        out, n = re.subn(r"(?m)^reviewer:[ \t]*.*$", f"reviewer: {new}", src)
        if not n or out == src:
            raise NoOp(f"{p.name}: reviewer: is already {new}")
        p.write_text(out, encoding="utf-8", newline="\n")
        return _restorer(p, src)
    return apply


def overflow_swift(type_name, lines=320):
    body = "\n".join(f"    static let n{i} = {i}" for i in range(1, lines - 1))
    return f"struct {type_name} {{\n{body}\n}}\n"


# ----------------------------------------------------------------------------- the cases
def case(pin, name, clause, apply, expect="red", gap_task=None):
    return {"pin": pin, "name": name, "clause": clause, "apply": apply, "expect": expect, "gap_task": gap_task}


IMPORTS = "Root-package targets import Foundation only"
CAP = "No Swift source file exceeds 300 lines"
MODES = "Every script in ops/ and .githooks/ is committed with the executable bit; data files are not"
EOL = ".gitattributes normalizes every text file to LF"
FLOOR = "iOS 18.4 as the platform floor"
FLOORS = "Test-count floors exist, are integers, and the Linux floor is at least 3"
GRADE = "No task reaches done/ without a reviewer who is not its owner"
ATTR = "LICENSE-DATA exists and credits OpenStreetMap contributors under ODbL"
USNO = "fixtures come from USNO rather than from our own output, and match within 90 s"

CASES = [case("P-SRC-01", f"import {mod} in {IMPORT_HOST}", IMPORTS, append(IMPORT_HOST, f"import {mod}"))
         for mod in BANNED] + [

    # KNOWN GAP: the assertion greps Sources/ only, so a banned import in a root-package TEST target - which
    # breaks Linux CI exactly as hard - is not seen. Filed, not fixed here: fixing it edits pins/PINS.yaml,
    # which is not this task's `touches:`, and a pin change wants its own red/green.
    case("P-SRC-01", f"import UIKit in {TEST_HOST} (test target)", IMPORTS,
         append(TEST_HOST, "import UIKit"), expect="gap", gap_task="T-0099"),

    case("P-SRC-02", "a 320-line tracked Swift file under Sources/", CAP,
         add_tracked("Sources/ScenicKit/Model/MutationOverflow.swift", overflow_swift("MutationOverflow"))),
    case("P-SRC-02", "a 320-line tracked Swift file under Tests/", CAP,
         add_tracked("Tests/ScenicKitTests/MutationOverflow.swift", overflow_swift("MutationOverflowTests"))),
    case("P-SRC-02", "the scanned Swift file set drops below MIN_FILES", CAP,
         untrack(["Tests/ScenicKitTests/GeoTests.swift", "Tests/ScenicKitTests/SolarFixtureTests.swift",
                  "Tests/ScenicKitTests/SolarFixtures.swift", "Tests/ScenicKitTests/SolarMathTests.swift",
                  "Sources/ScenicKit/Geo/Geo.swift"])),
    # KNOWN GAP: check-line-cap globs Sources/ and Tests/ only, so every Swift file in the iOS package is
    # exempt from the cap the statement claims for "no Swift source file". T-0037 owns it.
    case("P-SRC-02", "a 320-line tracked Swift file under apps/ios/Packages/", CAP,
         add_tracked("apps/ios/Packages/ScenicApp/Sources/DesignSystem/MutationOverflow.swift",
                     overflow_swift("MutationOverflowApp")), expect="gap", gap_task="T-0037"),

    case("P-OPS-01", "ops/test committed 100644", MODES, chmod("ops/test", "-x")),
    case("P-OPS-01", "a data file committed 100755", MODES, chmod("ops/lib/ro_cases.json", "+x")),
    case("P-OPS-01", "a required script dropped from the index", MODES, untrack(["ops/prod-read"])),

    case("P-GIT-01", "the eol=lf line deleted from .gitattributes", EOL,
         edit(".gitattributes", "* text=auto eol=lf\n", "")),
    case("P-GIT-01", "eol=lf weakened to text=auto", EOL,
         edit(".gitattributes", "* text=auto eol=lf", "* text=auto")),

    case("P-DATA-02", "the platform floor dropped to iOS 17", FLOOR,
         edit("Package.swift", '.iOS("18.4")', '.iOS("17.0")')),
    case("P-DATA-02", "the floor restated as .v18 (no waypoint URLs)", FLOOR,
         edit("Package.swift", '.iOS("18.4")', ".iOS(.v18)")),

    case("P-TEST-01", "floor_linux.txt is not an integer", FLOORS, write("pins/floor_linux.txt", "fifty\n")),
    case("P-TEST-01", "floor_linux.txt lowered below 3", FLOORS, write("pins/floor_linux.txt", "2\n")),
    case("P-TEST-01", "floor_ios.txt deleted", FLOORS, remove("pins/floor_ios.txt")),

    case("P-PROC-01", "a done/ task graded by its own owner", GRADE, reviewer("owner")),
    case("P-PROC-01", "a done/ task with no reviewer at all", GRADE, reviewer(None)),

    case("P-ATTR-02", "LICENSE-DATA deleted", ATTR, remove("LICENSE-DATA")),
    case("P-ATTR-02", "the OpenStreetMap credit reworded away", ATTR,
         edit("LICENSE-DATA", "OpenStreetMap contributors", "OSM contributors")),
    case("P-ATTR-02", "every ODbL mention removed", ATTR, edit("LICENSE-DATA", "ODbL", "our data license")),

    case("P-SAFE-05", "the oracle's USNO provenance replaced by our own output", USNO,
         edit(ORACLE, "US Naval Observatory", "regenerated from ScenicKit.SolarMath")),
    case("P-SAFE-05", "the fixture set cut to 10 site-days", USNO, keep_first(FIXTURES, "SolarFixture(name:", 10)),
    case("P-SAFE-05", "the solar math shifted by a 2-degree zenith", USNO,
         edit(SOLAR_MATH, "cos(zenith.radians) /", "cos((zenith + 2.0).radians) /")),
]
