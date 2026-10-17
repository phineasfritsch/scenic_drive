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

T-0397 adds a second whitelist on the same terms: every apps/ios line naming conditions, estimateBadge,
showsEstimateBadge or showsEstimate is an approved whole line, so the drive card's conditions line (the disclaimer
staying visible on the route screen) and its estimate caption (shown until the corridor is learned, P-SAFE-07) cannot
be dropped, inverted or rebound without a refusal by name - nor can the plan sheet's, the home screen's or the
disclaimer's own.

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
SHELL_LINE = ("if let drive, let host = DriveHost(preview: drive, sender: DriveRehearsal.rerouter ?? "
              "LivePlanner.rerouter(for: drive), content: { display in DriveScreen(preview: drive, "
              "display: display, onEnd: { self.drive = nil }) }) {")
APPROVED = [
    (SCREEN, "private let display: DriveDisplay"),
    (SCREEN, "public init(preview: PlanPreview, display: DriveDisplay, onEnd: @escaping () -> Void) {"),
    (SCREEN, "self.display = display"),
    (SCREEN, ".onChange(of: display.line) { resolveMap() }"),
    (SCREEN, ".onChange(of: display.showsDetails) { if !display.showsDetails { closeOnMoving() } }"),
    (SCREEN, "if display.showsDetails, let status = display.status {"),
    # T-0397: DriveCard is handed plain values from the display, here and nowhere else.
    (SCREEN, "DriveCard(remainingSeconds: display.remainingSeconds, glanceLine: display.glanceLine,"),
    (SCREEN, "caption: display.showsDetails ? nil : display.status, note: display.note,"),
    (SCREEN, "endTitle: display.actionTitle, endMinHeight: display.actionMinHeight, onEnd: endTapped)"),
    (SCREEN, "if display.showsDetails {"),
    (SCREEN, "if PostDriveQuestion.asks(after: display, alreadyAsked: asked) {"),
    (SCREEN, "route = DriveMapLine.route(for: display.line)"),
    (HOST, "private let content: (DriveDisplay) -> Content"),
    (HOST, "@ViewBuilder content: @escaping (DriveDisplay) -> Content) {"),
    (HOST, "content(navigator.display)"),
    (NAV, "@Published public private(set) var mode: DriveMode"),
    (NAV, "@Published public private(set) var surface: DriveSurface"),
    (NAV, "@Published public private(set) var display: DriveDisplay"),
    (NAV, "display = DriveDisplay(session: session)"),
    (NAV, "display = DriveDisplay(session: controller.session, arrived: voice.hasArrived)"),
    (SHELL, SHELL_LINE),
]
SAFETY_WORD = re.compile(r"(?<![A-Za-z0-9_])(conditions|estimateBadge|showsEstimateBadge|showsEstimate)"
                         r"(?![A-Za-z0-9_])")
PLAN, CARD = S + "FeaturePlanSheet/", S + "FeatureScenicHome/DriveCard.swift"
CONFIRM, HOME = S + "FeatureScenicHome/DriveEndConfirm.swift", S + "FeatureScenicHome/ScenicHomeScreen.swift"
DISCLAIMER = S + "FeatureScenicHome/SafetyDisclaimer.swift"
SAFETY_APPROVED = [
    (PLAN + "LoopPreviewCard.swift", "Text(PlanPreview.estimateBadge)"),
    (PLAN + "LoopPreviewCard.swift", "Text(PlanPreview.conditions)"),
    (PLAN + "PlanPreviewCard.swift", "if preview.showsEstimateBadge {"),
    (PLAN + "PlanPreviewCard.swift", "Text(PlanPreview.estimateBadge)"),
    (PLAN + "PlanPreviewCard.swift", "Text(PlanPreview.conditions)"),
    (PLAN + "PlanPreviewCard.swift", '.accessibilityIdentifier("plan.conditions")'),
    (PLAN + "TripItineraryCard.swift", "Text(PlanPreview.estimateBadge)"),
    (PLAN + "TripItineraryCard.swift", "Text(PlanPreview.conditions)"),
    (CARD, "let showsEstimate: Bool"),
    (CARD, "Text(PlanPreview.conditions)"),
    (CARD, '.accessibilityIdentifier("drive.conditions")'),
    (CARD, "if showsEstimate {"),
    (CARD, "Text(PlanPreview.estimateBadge)"),
    (CONFIRM, "Text(PlanPreview.conditions)"),
    (CONFIRM, '.accessibilityIdentifier("drive.conditions")'),
    (SCREEN, "showsEstimate: preview.showsEstimateBadge,"),
    (DISCLAIMER, "Text(Copy.conditions)"),
    (DISCLAIMER, 'static let conditions = "Conditions change. Verify locally."'),
    (HOME, "conditions"),
    (HOME, "private var conditions: some View {"),
    (HOME, "Text(Copy.conditions)"),
    (HOME, '.accessibilityIdentifier("home.conditions")'),
    (HOME, 'static let conditions = "Conditions change. Verify locally."'),
]
CARD_CONDITIONS = "".join(" " * n + s + "\n" for n, s in [
    (12, "Text(PlanPreview.conditions)"), (16, ".font(.caption)"), (16, ".foregroundStyle(DesignTokens.fg)"),
    (16, ".fixedSize(horizontal: false, vertical: true)"), (16, ".frame(maxWidth: .infinity, alignment: .leading)"),
    (16, '.accessibilityIdentifier("drive.conditions")')])
GUARDS = [("DriveDisplay, DriveSurface, DriveMode or display", WORD, APPROVED,
           "The drive screen renders DriveDisplay as the navigator publishes it - anything else can show the full "
           "screen to a moving driver (P-SAFE-09)."),
          ("conditions, estimateBadge, showsEstimateBadge or showsEstimate", SAFETY_WORD, SAFETY_APPROVED,
           "The conditions line stays visible on every route surface and the estimate caption shows until the "
           "corridor is learned (P-SAFE-03, P-SAFE-07).")]
MUTATIONS = [
    ("the drive card drops the conditions line (T-0397 M1)", CARD, CARD_CONDITIONS, ""),
    ("the drive card shows the estimate only once the corridor is learned (T-0397 M2)", SCREEN,
     "showsEstimate: preview.showsEstimateBadge,", "showsEstimate: !preview.showsEstimateBadge,"),
    ("the drive card shows the estimate caption whatever it is handed (T-0397)", CARD, "if showsEstimate {",
     "if true {"),
    ("the drive card never shows the estimate caption (T-0397)", SCREEN,
     "showsEstimate: preview.showsEstimateBadge,", "showsEstimate: false,"),
    ("the screen builds its own full display", SCREEN, "self.display = display",
     "self.display = .init(surface: .full, mode: .guiding)"),
    ("the shell hands the screen a full display", SHELL, "display: display, onEnd:",
     "display: .init(surface: .full, mode: .guiding), onEnd:"),
    ("the host publishes a display of its own", HOST, "content(navigator.display)",
     "content(DriveDisplay(surface: .full, mode: navigator.mode))"),
    ("the navigator publishes a full display", NAV,
     "display = DriveDisplay(session: controller.session, arrived: voice.hasArrived)",
     "display = DriveDisplay(surface: .full, mode: controller.session.mode)"),
    ("the screen asks the post-drive question whatever the display says (T-0358)", SCREEN,
     "if PostDriveQuestion.asks(after: display, alreadyAsked: asked) {",
     "if PostDriveQuestion.asks(after: .init(surface: .full, mode: .guiding, arrived: true), alreadyAsked: asked) {"),
    ("the screen shows the details whatever the display says", SCREEN, "if display.showsDetails {", "if true {"),
    ("the card's End target is the ordinary height while moving (T-0397)", SCREEN,
     "endMinHeight: display.actionMinHeight,", "endMinHeight: 44,"),
    ("the confirm stays up when the drive moves (T-0397)", SCREEN,
     "if !display.showsDetails { closeOnMoving() }", "if !display.showsDetails { }"),
    ("a new feature file branches on DriveSurface", None, S + "FeatureScenicHome/DriveMotion.swift",
     "import ScenicKit\nenum DriveMotion {\n    static let shown = DriveSurface.full\n}\n"),
]


class Refusal(Exception):
    pass


def population(tree: pathlib.Path, word: re.Pattern[str] = WORD) -> list[tuple[str, str]]:
    files = sorted(p for p in tree.rglob("*.swift") if p.is_file())
    if len(files) < MIN_FILES:
        raise Refusal(f"only {len(files)} .swift file(s) under {tree} (expected >= {MIN_FILES}): a whitelist over a "
                      "population that enumerated nothing is green for the wrong reason.")
    found = []
    for path in files:
        rel = path.relative_to(tree).as_posix()
        for raw in path.read_text(encoding="utf-8").split("\n"):
            line = raw.rstrip("\r").strip()
            if line.startswith("//") or not word.search(line):
                continue
            found.append((rel, line))
    return found


def check(tree: pathlib.Path) -> None:
    if not tree.is_dir():
        raise Refusal(f"no such directory: {tree}")
    for words, word, approved, why in GUARDS:
        found = population(tree, word)
        if found != approved:
            extra = [f"{f}: {l}" for f, l in found if (f, l) not in approved]
            missing = [f"{f}: {l}" for f, l in approved if (f, l) not in found]
            raise Refusal(f"a line naming {words} is not an approved whole line ({len(found)} found, "
                          f"{len(approved)} approved)\n  unapproved: " + ("\n    ".join([""] + extra) if extra else
                          "none") + "\n  missing: " + ("\n    ".join([""] + missing) if missing else
                          "none (the order differs)") + f"\n  {why}")


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
    print(f"P-SAFE-03/07 (screens): {len(SAFETY_APPROVED)} approved whole lines name conditions, estimateBadge, "
          "showsEstimateBadge or showsEstimate under apps/ios, and no other line does.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
