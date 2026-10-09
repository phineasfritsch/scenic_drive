#!/usr/bin/env python3
"""P-SAFE-03's hazard-strip clause (T-0339 A7, pre-review finding): the app renders hazards ONLY through
ScenicKit's HazardCopy table - never a raw wire kind or value.

    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-hazard-copy-sites.py
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-hazard-copy-sites.py --root DIR
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-hazard-copy-sites.py --prove-red
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-hazard-copy-sites.py --print-sites

A WHITELIST over SITES, never a blacklist of spellings (CLAUDE.md). A raw run reaches app code only by naming
PlanPreview's `hazards` field or the PlanHazardRun type (a closure, a key path, a rebinding or a new file all spell
one of them), or by reflecting over the preview with Mirror. The closures model (T-0341) is the same class: a
card reaches it only by naming the `closures` field or the ClosuresHazard / ClosuresState types. So every line of every *.swift under apps/ that names
one of IDENTIFIERS must be, WHOLE (trailing whitespace dropped), one of the approved (file, line) pairs in
check-hazard-copy-sites.txt, as many times as it is listed there. Only a line whose first non-blank characters are
`//` is skipped (memory source-guards-fail-closed). An approved site that is gone is red too: the whitelist is
re-approved in the diff that moves it. The task's A7 grep (`run.kind` / `run.value`) was a spelling blacklist;
--prove-red prints, per row, that the grep MISSED the bypass and this check CAUGHT it by name.

WHAT IT CANNOT SEE. A run reached without spelling an identifier - string interpolation or String(describing:)
over a whole PlanPreview, TripItinerary or LoopPreview - `/* */` block comments (a line inside one is read as code, so it can only fail closed),
and Swift outside apps/. Whether the approved lines are RIGHT is the reviewer's, and P-SAFE-03's digest table
(ops/lib/check-safety-disclaimer-pinned) refuses any byte change to the card besides.

EXITS. 0 every site approved and every approved site present. 1 a site refused or an approved site missing.
2 fail-closed: apps/ missing, the whitelist missing or empty, or no site found at all.
"""
from __future__ import annotations

import collections
import io
import os
import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
WHITELIST = pathlib.Path(__file__).resolve().parent / "check-hazard-copy-sites.txt"
SCANNED = ("apps",)
SKIP_DIRS = {".build", "DerivedData", ".swiftpm"}
IDENTIFIERS = ("hazards", "PlanHazardRun", "HazardCopy", "HazardStrip", "HazardFlag", "Mirror",
               "closures", "ClosuresHazard", "ClosuresState", "ClosuresHazardReader")
NAMES = re.compile(r"\b(?:%s)\b" % "|".join(IDENTIFIERS))
TAG = "P-SAFE-03 hazard copy"


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
    rows = [r.rstrip("\r") for r in WHITELIST.read_text(encoding="utf-8").splitlines() if "\t" in r]
    return collections.Counter(rows)


def check(root: pathlib.Path, out=sys.stdout) -> int:
    missing = [top for top in SCANNED if not (root / top).is_dir()]
    if missing:
        out.write("%s: REFUSING - %s missing under %s\n" % (TAG, ", ".join(missing), root))
        return 2
    allowed = approved()
    if not allowed:
        out.write("%s: REFUSING - the whitelist %s is missing or empty\n" % (TAG, WHITELIST.name))
        return 2
    found = sites(root)
    if not found:
        out.write("%s: REFUSING - no line names %s; the check would examine nothing\n" % (TAG, ", ".join(IDENTIFIERS)))
        return 2
    refused = sorted((found - allowed).elements())
    gone = sorted((allowed - found).elements())
    for row in refused:
        out.write("REFUSED  site not on the whitelist: %s\n" % row.replace("\t", ": "))
    for row in gone:
        out.write("REFUSED  approved site missing: %s\n" % row.replace("\t", ": "))
    if refused or gone:
        out.write("%s: FAILED - %d unapproved, %d missing of %d approved\n"
                  % (TAG, len(refused), len(gone), sum(allowed.values())))
        return 1
    out.write("%s: ok - %d sites, every one approved, in %d files\n"
              % (TAG, sum(found.values()), len({r.split("\t")[0] for r in found})))
    return 0


APP = "apps/ios/Packages/ScenicApp/Sources/"
CARD = APP + "FeaturePlanSheet/PlanPreviewCard.swift"
SHIPPED = "        let lines = HazardCopy.lines(for: preview)"
TRIP = APP + "FeaturePlanSheet/TripItineraryCard.swift"
LOOP = APP + "FeaturePlanSheet/LoopPreviewCard.swift"
TRIP_SITE = "                ForEach(Array(HazardCopy.lines(for: itinerary).enumerated()), id: \\.offset) { _, line in"
# (name, file, old or None to append/create, new). Every row must exit 1 with that file refused by name.
RED_ROWS = (
    ("the strip maps raw kinds by key path", CARD, SHIPPED, "        let lines = preview.hazards.map(\\.kind)"),
    ("a closure reads kind and value", CARD, SHIPPED,
     "        let lines = preview.hazards.map { $0.kind + \" \" + $0.value }"),
    ("a helper takes a run", CARD, None, "private func raw(_ h: PlanHazardRun) -> String { h.value }\n"),
    ("a new file reads the runs", APP + "FeaturePlanSheet/HazardProbe.swift", None,
     "import ScenicKit\nfunc probe(_ p: PlanPreview) -> [String] { p.hazards.map { $0.kind } }\n"),
    ("a Mirror walks the preview", CARD, None, "private func walk(_ p: PlanPreview) { _ = Mirror(reflecting: p) }\n"),
    ("a code line with a trailing comment", CARD, None, "private func runs(_ p: PlanPreview) { _ = p.hazards } // ok\n"),
    ("HazardCopy used from another card", APP + "FeaturePlanSheet/TripItineraryCard.swift", None,
     "private let copyProbe = HazardCopy.noneFlagged\n"),
    ("an approved line repeated", CARD, None, SHIPPED.strip() + "\n"),
    ("the table call is gone", CARD, "Text(HazardCopy.noneFlagged)", "Text(\"No hazards flagged\")"),
    ("a card reads closures beside the site", TRIP, TRIP_SITE,
     "                Text(itinerary.closures.crosses ? \"Road closed ahead\" : \"\")\n" + TRIP_SITE),
    ("the raw closures state reaches a Text", TRIP, TRIP_SITE,
     "                Text(\"closures: \\(itinerary.closures.state)\")\n" + TRIP_SITE),
    ("a helper takes the closures model", LOOP, None,
     "private func word(_ c: ClosuresHazard) -> Bool { c.crosses }\n"),
    ("a helper spells the closures state", LOOP, None,
     "private func word(_ s: ClosuresState) -> String { String(describing: s) }\n"),
)


def a7_grep(root: pathlib.Path) -> bool:
    """The task's old A7 predicate: True when it would have printed something (caught)."""
    for path in (root / APP).rglob("*.swift"):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(root).as_posix()
        if "run.kind" in text or "run.value" in text or ("HazardCopy" in text and rel != CARD):
            return True
    return False


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
    work = pathlib.Path(tempfile.mkdtemp(prefix="hazard-sites-"))
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
                sys.stdout.write("STALE    %-40s anchor found %d times\n" % (name, text.count(old)))
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text.replace(old, new, 1) if old else text + new, encoding="utf-8", newline="\n")
            buf = io.StringIO()
            code = check(work, buf)
            named = any(line.startswith("REFUSED") and rel in line for line in buf.getvalue().splitlines())
            ok = code == 1 and named
            red += ok
            sys.stdout.write("%-8s %-40s A7-grep=%s  sites=%s exit=%d\n"
                             % ("red" if ok else "GREEN", name, "caught" if a7_grep(work) else "MISSED",
                                "CAUGHT by name" if named else "NOT NAMED", code))
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
