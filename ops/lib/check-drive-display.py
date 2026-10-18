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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from drive_display_frozen import BLOCKS  # noqa: E402  (this directory is sys.path[0])
import frozen_comments  # noqa: E402  (T-0407: no /* */ block comment in a frozen file)

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
    # T-0397 rv1 B3: the End confirm renders only on the full surface, whatever `confirming` holds.
    (SCREEN, "} else if confirming && display.showsDetails {"),
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
    # T-0396 (merged from main): the plan preview's conditions line moved into its action block.
    (PLAN + "PlanPreviewActions.swift", "conditions"),
    (PLAN + "PlanPreviewActions.swift", "conditions"),
    (PLAN + "PlanPreviewActions.swift", "private var conditions: some View {"),
    (PLAN + "PlanPreviewActions.swift", "Text(PlanPreview.conditions)"),
    (PLAN + "PlanPreviewActions.swift", '.accessibilityIdentifier("plan.conditions")'),
    (PLAN + "PlanPreviewCard.swift", "if preview.showsEstimateBadge {"),
    (PLAN + "PlanPreviewCard.swift", "Text(PlanPreview.estimateBadge)"),
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
    ("the card fades its conditions line (T-0397 rv1 B2)", CARD, '.accessibilityIdentifier("drive.conditions")\n',
     '.accessibilityIdentifier("drive.conditions")\n                .opacity(0)\n'),
    ("the confirm fades its conditions line (T-0397 rv1 B2)", CONFIRM, '.accessibilityIdentifier("drive.conditions")\n',
     '.accessibilityIdentifier("drive.conditions")\n                .opacity(0)\n'),
    ("the card hides its estimate caption (T-0397 rv1 B2)", CARD, '.accessibilityIdentifier("drive.estimate")\n',
     '.accessibilityIdentifier("drive.estimate")\n                    .hidden()\n'),
    ("the screen fades the whole card (T-0397 rv1 B2)", SCREEN, "                        controls\n",
     "                        controls\n                            .opacity(0)\n"),
    ("moving no longer closes the confirm (T-0397 rv1 B3)", SCREEN,
     "private func closeOnMoving() {\n        confirming = false\n", "private func closeOnMoving() {\n"),
    ("the confirm renders on any surface (T-0397 rv1 B3)", SCREEN, "} else if confirming && display.showsDetails {",
     "} else if confirming {"),
    ("code after the card's struct (T-0397 rv1 B2)", CARD, '.accessibilityIdentifier("drive.end")\n    }\n}\n',
     '.accessibilityIdentifier("drive.end")\n    }\n}\n\nextension DriveCard { var faded: Double { 0 } }\n'),
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


def kept(path: pathlib.Path) -> list[str]:
    """Non-blank lines, trimmed; only a line STARTING with // is dropped (source-guards-fail-closed)."""
    lines = (raw.rstrip("\r").strip() for raw in path.read_text(encoding="utf-8").split("\n"))
    return [line for line in lines if line and not line.startswith("//")]


def frozen(tree: pathlib.Path) -> list[str]:
    """T-0397 rv1 B2/B3: each drive view is its approved whole block, under its approved line, its file's last code."""
    bad = []
    for label, rel, above, want in BLOCKS:
        if (tree / rel).is_file():
            bad += frozen_comments.refusals(tree / rel, label)
        lines = kept(tree / rel) if (tree / rel).is_file() else []
        if lines.count(want[0]) != 1:
            bad.append(f"{label}: `{want[0]}` occurs {lines.count(want[0])} time(s) in {rel}, expected exactly 1")
            continue
        at = lines.index(want[0])
        up = lines[at - 1] if at else "<start of file>"
        if up != above:
            bad.append(f"{label}: the line above `{want[0]}` is `{up}`, approved `{above}`")
            continue
        depth, end = 0, len(lines)
        for j in range(at, len(lines)):
            depth += lines[j].count("{") - lines[j].count("}")
            if depth <= 0:
                end = j + 1
                break
        got = lines[at:end]
        for j, line in enumerate(want):
            if j >= len(got) or got[j] != line:
                bad.append(f"{label} line {j + 1} of {len(want)} in {rel}: approved `{line}`, found "
                           f"`{got[j] if j < len(got) else '<end of block>'}`")
                break
        else:
            if len(got) != len(want):
                bad.append(f"{label} in {rel}: {len(got)} lines, approved {len(want)}; first unapproved "
                           f"`{got[len(want)]}`")
            elif end != len(lines):
                bad.append(f"{label}: code after the block in {rel}, first `{lines[end]}`")
    return bad


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
    bad = frozen(tree)
    if bad:
        raise Refusal(f"a drive view is not its approved whole block (ops/lib/drive_display_frozen.py)\n  "
                      f"{len(bad)} refusal(s)\n  " + "\n  ".join(bad) + "\n  The card, the confirm and the screen draw "
                      "the conditions line, the estimate caption and the End target; an edit is re-approved there.")


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
    print(f"P-SAFE-03/09 (drive views): {len(BLOCKS)} structs ({sum(len(b[3]) for b in BLOCKS)} kept lines) are "
          "their approved whole blocks, each its file's last code.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
