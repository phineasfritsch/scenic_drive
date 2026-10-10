#!/usr/bin/env python3
"""P-PRIV-05's emit-site clause (T-0355 R5/R6): every telemetry emit site in the app is approved, and every one of
the TelemetryEventKind cases has EXACTLY ONE - an approved emit line, or a pending row naming the task that wires it.

    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-telemetry-emit-sites.py
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-telemetry-emit-sites.py --root DIR
    "${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/check-telemetry-emit-sites.py --prove-red

A WHITELIST over SITES, never a blacklist of spellings (CLAUDE.md). The population is every line of every *.swift
under apps/ that contains `Telemetry` or names `.<case>` of a TelemetryEventKind case; only a line whose first
non-blank characters are `//` is skipped (memory source-guards-fail-closed). Each must equal, WHOLE (trailing
whitespace dropped), an approved row of check-telemetry-emit-sites.txt, as many times as it is listed:
    emit<TAB><case><TAB><file><TAB><line>    the ONE line constructing `TelemetryEvent.<case>`
    site<TAB><file><TAB><line>               any other approved line (a caller, an import, a declaration)
    pending<TAB><case><TAB><T-NNNN>          the case is not emitted yet; that task wires it
The cases are read from Sources/Telemetry/TelemetryEventKind.swift, so a new case is red until it has a row. An
emit row must construct its own case; a site row may construct none; an approved row that is gone is red.

WHAT IT CANNOT SEE. A construction that names neither `Telemetry` nor `.<case>` (impossible without one of them
on some line: the case name or the type), `/* */` block comments (read as code - fails closed), Sources/ (no root
module emits: only apps/ links Telemetry beside a moment, and a new dependency is a serial Package.swift edit).

EXITS. 0 every line approved, every approved line present, every case exactly once. 1 a refusal. 2 fail-closed:
apps/ or the kind file or the whitelist missing or empty, or no case read.
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
WHITELIST = "ops/lib/check-telemetry-emit-sites.txt"
KINDS = "Sources/Telemetry/TelemetryEventKind.swift"
SKIP_DIRS = {".build", "DerivedData", ".swiftpm"}
CASE_LINE = re.compile(r"^\s*case\s+(\w+)\b")
TASK = re.compile(r"^T-\d{4}$")


def cases(root: pathlib.Path) -> list:
    path = root / KINDS
    if not path.is_file():
        return []
    return [m.group(1) for m in map(CASE_LINE.match, path.read_text(encoding="utf-8").splitlines()) if m]


def sites(root: pathlib.Path, names: list) -> collections.Counter:
    named = re.compile(r"Telemetry|\.(?:%s)\b" % "|".join(names))
    found = collections.Counter()
    for dirpath, dirnames, filenames in os.walk(root / "apps"):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if not name.endswith(".swift"):
                continue
            path = pathlib.Path(dirpath) / name
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.lstrip().startswith("//") or not named.search(line):
                    continue
                found[path.relative_to(root).as_posix() + "\t" + line.rstrip()] += 1
    return found


def check(root: pathlib.Path, out=sys.stdout) -> int:
    names = cases(root)
    whitelist = root / WHITELIST
    rows = whitelist.read_text(encoding="utf-8").splitlines() if whitelist.is_file() else []
    if not (root / "apps").is_dir() or not names or not rows:
        out.write("P-PRIV-05 emit sites: REFUSING - apps/, %s or %s missing or empty under %s\n"
                  % (KINDS, WHITELIST, root))
        return 2
    problems = []
    allowed = collections.Counter()
    per_case = collections.defaultdict(list)
    for row in rows:
        cells = row.split("\t")
        if cells[0] == "emit" and len(cells) >= 4:
            case, line = cells[1], "\t".join(cells[2:])
            per_case[case].append("emit")
            allowed[line] += 1
            if not re.search(r"\bTelemetryEvent\.%s\b" % re.escape(case), cells[3]):
                problems.append("emit row for %s does not construct TelemetryEvent.%s: %s" % (case, case, cells[2]))
        elif cells[0] == "site" and len(cells) >= 3:
            allowed["\t".join(cells[1:])] += 1
        elif cells[0] == "pending" and len(cells) == 3 and TASK.match(cells[2]):
            per_case[cells[1]].append("pending " + cells[2])
        else:
            problems.append("malformed whitelist row: %r" % row)
    for case in sorted(set(per_case) - set(names)):
        problems.append("whitelist names %s, which is not a TelemetryEventKind case" % case)
    for case in names:
        if len(per_case[case]) != 1:
            problems.append("case %s has %d rows (%s); exactly one emit or pending row is required"
                            % (case, len(per_case[case]), ", ".join(per_case[case]) or "none"))
    found = sites(root, names)
    for row in sorted((found - allowed).elements()):
        problems.append("site not on the whitelist: %s" % row.replace("\t", ": ", 1))
    for row in sorted((allowed - found).elements()):
        problems.append("approved site missing: %s" % row.replace("\t", ": ", 1))
    emits = {"\t".join(r.split("\t")[2:]) for r in rows if r.startswith("emit\t")}
    construct = re.compile(r"\bTelemetryEvent\.(?:%s)\b" % "|".join(names))
    for row in sorted(found):
        if construct.search(row) and row not in emits:
            problems.append("constructs an event outside an emit row: %s" % row.replace("\t", ": ", 1))
    for problem in problems:
        out.write("REFUSED  %s\n" % problem)
    if problems:
        out.write("P-PRIV-05 emit sites: FAILED - %d refusals\n" % len(problems))
        return 1
    wired = sum(1 for c in names if per_case[c] == ["emit"])
    out.write("P-PRIV-05 emit sites: ok - %d lines approved; %d of %d cases emitted once, %d pending by task\n"
              % (sum(found.values()), wired, len(names), len(names) - wired))
    return 0


LIVE = "apps/ios/Packages/ScenicApp/Sources/PlanAdapter/LiveTelemetry.swift"
SHOWN = "        record(TelemetryEvent.surpriseShown)"
# (name, file, old or None to append, new, expected exit). Each row must refuse; the control must pass.
RED_ROWS = (
    ("a new emit for a pending case", "apps/ios/Packages/ScenicApp/Sources/PlanAdapter/Probe.swift", None,
     "func probe() { LiveTelemetryProbe.record(TelemetryEvent.previewShown) }\n", 1),
    ("a second emit for a wired case", LIVE, SHOWN, SHOWN + "\n" + SHOWN, 1),
    ("the approved emit removed", LIVE, SHOWN, "", 1),
    ("an approved line with a trailing comment", LIVE, SHOWN, SHOWN + " // fine", 1),
    ("a feature calls the client", "apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/Probe.swift", None,
     "func probe() { LiveTelemetry.planResult(.failed) }\n", 1),
    ("an unqualified case named in the app", "apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/Probe.swift",
     None, "let probe: Probe = .driveStarted\n", 1),
    ("a fifteenth case", KINDS, "    case paywall\n", "    case paywall\n    case tripShared = \"trip_shared\"\n", 1),
    ("a wired case also pending", WHITELIST, None, "pending\tplanResult\tT-0361\n", 1),
    ("a pending row removed", WHITELIST, "pending\tpreviewShown\tT-0361\n", "", 1),
    ("an emit row retagged", WHITELIST, "emit\tsurpriseShown\t", "emit\tsurpriseArrived\t", 1),
    ("an emit row demoted to a site", WHITELIST, "emit\tsurpriseShown\t", "site\t", 1),
    ("a pending row without a task", WHITELIST, "pending\tpreviewShown\tT-0361", "pending\tpreviewShown\tlater", 1),
    ("the whitelist emptied", WHITELIST, "", None, 2),
    ("the kind file gone", KINDS, "", None, 2),
)


def mirror(dest: pathlib.Path) -> None:
    for dirpath, dirnames, filenames in os.walk(ROOT / "apps"):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in filenames:
            if name.endswith(".swift"):
                src = pathlib.Path(dirpath) / name
                target = dest / src.relative_to(ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, target)
    for rel in (KINDS, WHITELIST):
        (dest / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dest / rel)


def prove_red() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        control = pathlib.Path(tmp) / "control"
        mirror(control)
        sink = open(os.devnull, "w")
        if check(control, sink) != 0:
            print("PROVE-RED  control is not green - nothing below means anything")
            return 1
        print("PROVE-RED  control: exit 0")
        for i, (name, rel, old, new, want) in enumerate(RED_ROWS):
            root = pathlib.Path(tmp) / ("row%d" % i)
            mirror(root)
            path = root / rel
            if new is None:
                path.unlink()
            elif old is None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text((path.read_text(encoding="utf-8") if path.exists() else "") + new, encoding="utf-8")
            else:
                text = path.read_text(encoding="utf-8")
                if old not in text:
                    print("PROVE-RED  %-40s STALE ROW - %r not found" % (name, old))
                    failures += 1
                    continue
                path.write_text(text.replace(old, new, 1), encoding="utf-8")
            got = check(root, sink)
            verdict = "red" if got == want else "WRONG"
            failures += got != want
            print("PROVE-RED  %-40s exit %d (want %d) %s" % (name, got, want, verdict))
    print("PROVE-RED  %s - %d rows" % ("ok" if not failures else "FAILED", len(RED_ROWS)))
    return 1 if failures else 0


def main(argv: list) -> int:
    if argv[1:] == ["--prove-red"]:
        return prove_red()
    if len(argv) == 3 and argv[1] == "--root":
        return check(pathlib.Path(argv[2]))
    if len(argv) == 1:
        return check(ROOT)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
