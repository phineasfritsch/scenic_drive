#!/usr/bin/env python3
"""P-SAFE-09's screen half (T-0324 R7): the drive screen shows what ScenicKit's DriveDisplay says, and nothing else
decides it.

DriveDisplay(surface:mode:) is Linux-tested whole over every DriveSurface x DriveMode (DriveDisplayTests, bound by
name in P-SAFE-09's row). What no Linux test can see is whether the SwiftUI screen READS it: a drive screen that
builds its own `.init(surface: .full, mode: .guiding)`, a shell that hands it one, a host that publishes something
other than the navigator's display, or a feature file that branches on DriveSurface would each show the full screen
to a moving driver and compile. So this is a WHITELIST OF WHOLE LINES: every line under apps/ios naming the words
DriveDisplay, DriveSurface, DriveMode or display - counted in code and in strings alike - is one of the approved
lines below, at its file, in scan order (paths sorted, then line order). A line is dropped only when its trimmed text
STARTS with `//`; nothing is cut inside a line (source-guards-fail-closed). Any other line naming one of the four
words, anywhere in the app tree, is refused by name, and an approved line that is missing is refused too.

WHAT IT CANNOT SEE: whether the screen renders what it reads (that is the drive shot, ios-screenshot's), a value
reaching the screen under a name none of the four words spells, and Swift outside apps/ios.

    python ops/lib/check-drive-display.py                  # the tracked tree
    python ops/lib/check-drive-display.py --app-tree DIR   # a copy of apps/ios
    python ops/lib/check-drive-display.py --prove-red      # the mutations, each refused by name
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORD = re.compile(r"(?<![A-Za-z0-9_])(DriveDisplay|DriveSurface|DriveMode|display)(?![A-Za-z0-9_])")
MIN_FILES = 60
S = "Packages/ScenicApp/Sources/"
SCREEN, HOST, NAV, SHELL = (S + "FeatureScenicHome/DriveScreen.swift", S + "NavAdapter/DriveHost.swift",
                            S + "NavAdapter/DriveNavigator.swift", "ScenicDrive/ScenicDriveApp.swift")
SHELL_LINE = ("if let drive, let host = DriveHost(preview: drive, content: { display in DriveScreen(preview: drive, "
              "display: display, onEnd: { self.drive = nil }) }) {")
APPROVED = [
    (SCREEN, "private let display: DriveDisplay"),
    (SCREEN, "public init(preview: PlanPreview, display: DriveDisplay, onEnd: @escaping () -> Void) {"),
    (SCREEN, "self.display = display"),
    (SCREEN, "if display.showsDetails, let status = display.status {"),
    (SCREEN, "if display.showsDetails {"),
    (SCREEN, 'Label(display.actionTitle, systemImage: "xmark.circle.fill")'),
    (SCREEN, "if !display.showsDetails, let status = display.status {"),
    (SCREEN, ".frame(maxWidth: .infinity, minHeight: display.actionMinHeight)"),
    (HOST, "private let content: (DriveDisplay) -> Content"),
    (HOST, "public init?(preview: PlanPreview, @ViewBuilder content: @escaping (DriveDisplay) -> Content) {"),
    (HOST, "content(navigator.display)"),
    (NAV, "@Published public private(set) var mode: DriveMode"),
    (NAV, "@Published public private(set) var surface: DriveSurface"),
    (NAV, "@Published public private(set) var display: DriveDisplay"),
    (NAV, "display = DriveDisplay(session: session)"),
    (NAV, "display = DriveDisplay(session: controller.session)"),
    (SHELL, SHELL_LINE),
]
MUTATIONS = [
    ("the screen builds its own full display", SCREEN, "self.display = display",
     "self.display = .init(surface: .full, mode: .guiding)"),
    ("the shell hands the screen a full display", SHELL, "display: display, onEnd:",
     "display: .init(surface: .full, mode: .guiding), onEnd:"),
    ("the host publishes a display of its own", HOST, "content(navigator.display)",
     "content(DriveDisplay(surface: .full, mode: navigator.mode))"),
    ("the navigator publishes a full display", NAV, "display = DriveDisplay(session: controller.session)",
     "display = DriveDisplay(surface: .full, mode: controller.session.mode)"),
    ("the screen shows the details whatever the display says", SCREEN, "if display.showsDetails {", "if true {"),
    ("a new feature file branches on DriveSurface", None, S + "FeatureScenicHome/DriveMotion.swift",
     "import ScenicKit\nenum DriveMotion {\n    static let shown = DriveSurface.full\n}\n"),
]


class Refusal(Exception):
    pass


def population(tree: pathlib.Path) -> list[tuple[str, str]]:
    files = sorted(p for p in tree.rglob("*.swift") if p.is_file())
    if len(files) < MIN_FILES:
        raise Refusal(f"only {len(files)} .swift file(s) under {tree} (expected >= {MIN_FILES}): a whitelist over a "
                      "population that enumerated nothing is green for the wrong reason.")
    found = []
    for path in files:
        rel = path.relative_to(tree).as_posix()
        for raw in path.read_text(encoding="utf-8").split("\n"):
            line = raw.rstrip("\r").strip()
            if line.startswith("//") or not WORD.search(line):
                continue
            found.append((rel, line))
    return found


def check(tree: pathlib.Path) -> None:
    if not tree.is_dir():
        raise Refusal(f"no such directory: {tree}")
    found = population(tree)
    if found != APPROVED:
        extra = [f"{f}: {l}" for f, l in found if (f, l) not in APPROVED]
        missing = [f"{f}: {l}" for f, l in APPROVED if (f, l) not in found]
        raise Refusal("a line naming DriveDisplay, DriveSurface, DriveMode or display is not an approved whole line "
                      f"({len(found)} found, {len(APPROVED)} approved)\n  unapproved: " + ("\n    ".join([""] + extra)
                      if extra else "none") + "\n  missing: " + ("\n    ".join([""] + missing) if missing else
                      "none (the order differs)") + "\n  The drive screen renders DriveDisplay as the navigator "
                      "publishes it - anything else can show the full screen to a moving driver (P-SAFE-09).")


def prove_red(tree: pathlib.Path) -> int:
    check(tree)
    bad = 0
    for name, rel, old, new in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            copy = pathlib.Path(tmp) / "ios"
            shutil.copytree(tree, copy)
            if rel is None:
                (copy / old).write_text(new, encoding="utf-8")
            else:
                text = (copy / rel).read_text(encoding="utf-8")
                if text.count(old) != 1:
                    print(f"PROVE-RED STALE: {name}: the anchor does not occur exactly once in {rel}")
                    bad += 1
                    continue
                (copy / rel).write_text(text.replace(old, new), encoding="utf-8")
            try:
                check(copy)
                print(f"PROVE-RED SURVIVED: {name}")
                bad += 1
            except Refusal as refusal:
                print(f"[red] {name}: {str(refusal).splitlines()[2].strip()[:110]}")
    print(f"PROVE-RED {'OK' if bad == 0 else 'FAIL'}: {len(MUTATIONS) - bad}/{len(MUTATIONS)} refused by name")
    return 0 if bad == 0 else 1


def main(argv: list[str]) -> int:
    tree = ROOT / "apps" / "ios"
    if "--app-tree" in argv:
        tree = pathlib.Path(argv[argv.index("--app-tree") + 1])
    try:
        if "--prove-red" in argv:
            return prove_red(tree)
        check(tree)
    except Refusal as refusal:
        print(f"P-SAFE-09: {refusal}")
        return 1
    print(f"P-SAFE-09 (screen): {len(APPROVED)} approved whole lines name DriveDisplay, DriveSurface, DriveMode or "
          "display under apps/ios, and no other line does: the drive screen renders the navigator's DriveDisplay.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
