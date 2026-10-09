#!/usr/bin/env python3
"""P-PRIV-05's learned-speed clause (T-0320 R9): learned speeds have no Codable conformance and never leave the
device - no path into ScenicAPIClient or Telemetry.

    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-learned-speeds-sites.py
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-learned-speeds-sites.py --root DIR
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-learned-speeds-sites.py --prove-red

A WHITELIST over SITES, never a blacklist of spellings (CLAUDE.md): every line of every *.swift under Sources/ and
apps/ that names one of IDENTIFIERS must be, WHOLE (trailing whitespace dropped), one of the approved
(file, line) pairs in check-learned-speeds-sites.txt, as many times as it is listed there. Only a line whose first
non-blank characters are `//` is skipped (memory source-guards-fail-closed). So a conformance added to a
declaration, an extension, a typealias, a parameter in ScenicAPIClient or a use in Telemetry or apps/ is a new or
changed line - red, by name. An approved site that is gone is red too: the whitelist is re-approved in the diff
that moves it.

WHAT IT CANNOT SEE. A use that names none of IDENTIFIERS (a value reached through a whitelisted call without its
type spelled), `/* */` block comments (a line inside one is read as code, so it can only fail closed), and files
outside Sources/ and apps/. The conformance half is also held at runtime by ScenicKitTests'
LearnedSpeedsPrivacyTests, which casts each metatype to Encodable.Type and Decodable.Type.

EXITS. 0 every site approved and every approved site present. 1 a site refused or an approved site missing.
2 fail-closed: a root missing, the whitelist missing or empty, or no site found at all.
"""
from __future__ import annotations

import collections
import os
import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
WHITELIST = pathlib.Path(__file__).resolve().parent / "check-learned-speeds-sites.txt"
SCANNED = ("Sources", "apps")
SKIP_DIRS = {".build", "DerivedData", ".swiftpm"}
IDENTIFIERS = ("LearnedCorridorSpeeds", "CorridorSlot", "CorridorRatio", "RetimedRoute", "TrafficProvider", "CorridorClock",
               "CorridorSlotRow", "CorridorLearner", "CorridorRatioRecord", "CorridorRatioStore")
NAMES = re.compile(r"\b(?:%s)\b" % "|".join(IDENTIFIERS))


def sites(root: pathlib.Path) -> collections.Counter:
    found = collections.Counter()
    for top in SCANNED:
        for dirpath, dirnames, filenames in os.walk(root / top):
            dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
            for name in sorted(filenames):
                if not name.endswith(".swift"):
                    continue
                path = pathlib.Path(dirpath) / name
                rel = path.relative_to(root).as_posix()
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    if line.lstrip().startswith("//") or not NAMES.search(line):
                        continue
                    found[rel + "\t" + line.rstrip()] += 1
    return found


def approved() -> collections.Counter:
    if not WHITELIST.is_file():
        return collections.Counter()
    rows = [r for r in WHITELIST.read_text(encoding="utf-8").splitlines() if "\t" in r]
    return collections.Counter(rows)


def check(root: pathlib.Path, out=sys.stdout) -> int:
    missing = [top for top in SCANNED if not (root / top).is_dir()]
    if missing:
        out.write("P-PRIV-05 learned speeds: REFUSING - %s missing under %s\n" % (", ".join(missing), root))
        return 2
    allowed = approved()
    if not allowed:
        out.write("P-PRIV-05 learned speeds: REFUSING - the whitelist %s is missing or empty\n" % WHITELIST.name)
        return 2
    found = sites(root)
    if not found:
        out.write("P-PRIV-05 learned speeds: REFUSING - no line names %s; the check would examine nothing\n"
                  % ", ".join(IDENTIFIERS))
        return 2
    refused = sorted((found - allowed).elements())
    gone = sorted((allowed - found).elements())
    for row in refused:
        out.write("REFUSED  site not on the whitelist: %s\n" % row.replace("\t", ": "))
    for row in gone:
        out.write("REFUSED  approved site missing: %s\n" % row.replace("\t", ": "))
    if refused or gone:
        out.write("P-PRIV-05 learned speeds: FAILED - %d unapproved, %d missing of %d approved\n"
                  % (len(refused), len(gone), sum(allowed.values())))
        return 1
    out.write("P-PRIV-05 learned speeds: ok - %d sites, every one approved, in %d files\n"
              % (sum(found.values()), len({r.split("\t")[0] for r in found})))
    return 0


LEARNER = "Sources/ScenicKit/Traffic/LearnedCorridorSpeeds.swift"
RATIO = "Sources/ScenicKit/Traffic/CorridorRatio.swift"
# (name, file, old or None to append/create, new). Every row must exit 1 with the named line refused.
RED_ROWS = (
    ("an extension declares Codable", LEARNER, None, "extension LearnedCorridorSpeeds: Codable {}\n"),
    ("the declaration gains Encodable", LEARNER, "TrafficProvider, Equatable {",
     "TrafficProvider, Equatable, Encodable {"),
    ("CorridorRatio gains Codable", RATIO, "CorridorRatio: Equatable, Sendable {",
     "CorridorRatio: Equatable, Sendable, Codable {"),
    ("ScenicAPIClient takes the learner", "Sources/ScenicAPIClient/LearnedUpload.swift", None,
     "import ScenicKit\nfunc upload(_ speeds: LearnedCorridorSpeeds) {}\n"),
    ("Telemetry aliases a slot", "Sources/Telemetry/SlotAlias.swift", None, "typealias Slot = CorridorSlot\n"),
    ("the app holds a retimed route", "apps/ios/Packages/ScenicApp/Sources/Probe/RetimedProbe.swift", None,
     "let probe: RetimedRoute? = nil\n"),
    ("a code line with a trailing comment", RATIO, None, "extension CorridorRatio: Encodable {} // fine\n"),
    ("an approved line repeated", LEARNER, None,
     "public struct LearnedCorridorSpeeds: TrafficProvider, Equatable {\n"),
    ("CorridorClock gains Codable (T-0325)", "Sources/ScenicKit/Traffic/CorridorClock.swift",
     "CorridorClock: Sendable, Equatable {", "CorridorClock: Sendable, Equatable, Codable {"),
    ("the app holds a corridor clock (T-0325)", "apps/ios/Packages/ScenicApp/Sources/Probe/ClockProbe.swift", None,
     "var probe: CorridorClock?\n"),
    ("CorridorSlotRow gains Codable (T-0343)", "Sources/ScenicKit/Traffic/CorridorSlotRow.swift",
     "CorridorSlotRow: Equatable, Sendable {", "CorridorSlotRow: Equatable, Sendable, Codable {"),
    ("the kept record gains Encodable (T-0343)", "Sources/PlaceStore/CorridorRatioRecord.swift",
     "CorridorRatioRecord: Sendable, Equatable {", "CorridorRatioRecord: Sendable, Equatable, Encodable {"),
    ("Telemetry reads the store (T-0343)", "Sources/Telemetry/StoreProbe.swift", None,
     "func probe(_ store: CorridorRatioStore) {}\n"),
    ("a feature holds the learner (T-0343)", "apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/LearnerProbe.swift",
     None, "var probe: CorridorLearner?\n"),
)


def copy_tree(dest: pathlib.Path) -> None:
    for top in SCANNED:
        for dirpath, dirnames, filenames in os.walk(ROOT / top):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if name.endswith(".swift"):
                    src = pathlib.Path(dirpath) / name
                    to = dest / src.relative_to(ROOT)
                    to.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(src, to)


def prove_red() -> int:
    import io
    work = pathlib.Path(tempfile.mkdtemp(prefix="learned-sites-"))
    try:
        copy_tree(work)
        control = check(work, io.StringIO())
        sys.stdout.write("CONTROL  unmodified copy                          exit=%d (need 0)\n" % control)
        red = 0
        for name, rel, old, new in RED_ROWS:
            path = work / rel
            pristine = path.read_bytes() if path.exists() else None
            text = pristine.decode("utf-8") if pristine is not None else ""
            if old is not None and text.count(old) != 1:
                sys.stdout.write("STALE    %-44s anchor found %d times\n" % (name, text.count(old)))
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text.replace(old, new, 1) if old else text + new, encoding="utf-8", newline="\n")
            buf = io.StringIO()
            code = check(work, buf)
            named = any(line.startswith("REFUSED") and rel in line for line in buf.getvalue().splitlines())
            ok = code == 1 and named
            red += ok
            sys.stdout.write("%-8s %-44s exit=%d %s\n" % ("red" if ok else "GREEN", name, code,
                                                          "refused by name" if named else "NOT NAMED"))
            if pristine is None:
                path.unlink()
            else:
                path.write_bytes(pristine)
        ok = control == 0 and red == len(RED_ROWS)
        sys.stdout.write("PROVE-RED %s: %d of %d rows red by name, control %d\n"
                         % ("OK" if ok else "FAILED", red, len(RED_ROWS), control))
        return 0 if ok else 1
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv) -> int:
    if "--prove-red" in argv:
        return prove_red()
    if "--print-sites" in argv:
        for row in sorted(sites(ROOT).elements()):
            sys.stdout.write(row + "\n")
        return 0
    root = pathlib.Path(argv[argv.index("--root") + 1]) if "--root" in argv else ROOT
    return check(root)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
