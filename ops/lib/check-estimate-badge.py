#!/usr/bin/env python3
"""P-SAFE-07's screen half (T-0398, the pre-review mutant pass's M1): every ETA the app draws carries the
*estimate · no traffic data* badge exactly where it is drawn today.

The badge rule itself (>= 5 learned samples) is ScenicKit's and is bound by name in P-SAFE-07's row. What no Linux
test can see is whether a SwiftUI surface still DRAWS the badge beside its ETA: deleting the two `estimateTag` lines
from the Surprise card's ViewThatFits compiled, kept every test green and was caught only by a sha256 digest whose
re-approval is routine on every Swift edit. So two WHITELISTS, both over the approved file
ops/lib/check-estimate-badge-approved.txt:

  SITES   every line under apps/ios naming an ETA or badge identifier - estimate, estimateBadge, etaIsEstimate,
          showsEstimateBadge, estimateTag, roundTripMinutes, roundTrip, roundTripValue, etaLine, etaHero,
          etaMinutes, etaRow, etaSeconds, fastestEtaSeconds, durationSeconds, remainingSeconds, glanceLine (the
          drive card's arrival and its minutes-and-miles line since T-0397 moved them into DriveCard) - counted in code and strings alike, is an approved whole line at its
          file, in scan order (paths sorted, then line order). A new surface that draws an ETA, or a badge line
          removed, moved or respelled, is refused by name.
  BLOCKS  each badge block (the Surprise card's round-trip call, its roundTrip/roundTripValue/estimateTag bodies and
          its Copy literal; the plan card's etaRow (T-0396's hero ETA beside its tag); the plan, loop, trip and
          drive cards' `if ... {` badge blocks) is read from its
          declaration - a whole line that occurs exactly once in its file - to its matching close by counting
          { and } on whole lines, and compared line by line with the approved body, together with the first
          non-blank line ABOVE and BELOW it (an `if false {`, `.hidden()` or `.opacity(0)` around a block is a
          changed fence line, refused).
  DECLS   (T-0398 R2, rv1's B1) every DECLARATION under apps/ios of a name the eleven approved badge bodies use
          (DesignTokens, fgMuted, border, Copy, Text, Capsule, font, padding, ...; string literals dropped) is an
          approved whole line in scan order, with the block it opens when it is not a type declaration - so a
          file-scoped `enum DesignTokens`, a token's value, an `extension Text` init or a View modifier overload is
          refused by name. Rules and the private-helper fixed point in estimate_badge_decls.py; a declaration
          keyword ending a line (the name on the next line) is refused outright.

Lines are trimmed and a trailing CR stripped; a line is dropped only when its trimmed text STARTS with `//`; nothing
is cut inside a line (source guards fail closed). An approved-file edit is the deliberate act; a digest is not one.

COMMENTS (T-0407): check() first refuses ANY /* */ block comment in a file a badge block is read from
(ops/lib/frozen_comments.py, check-file-scope's lexer), so a block commented out under a twin is refused.

WHAT IT CANNOT SEE: whether the badge RENDERS (the ios-screenshot shots), an ETA reaching the screen under a name
none of the words spells, Swift outside apps/ios (ScenicKit's PlanPreview.estimateBadge is bound by
name in P-SAFE-07's row), and a public or internal helper that an approved declaration's body calls (only same-file
private helpers are followed: following every name freezes the whole app - estimate_badge_decls.py).

    python ops/lib/check-estimate-badge.py                  # the tracked tree
    python ops/lib/check-estimate-badge.py --app-tree DIR   # a copy of apps/ios
    python ops/lib/check-estimate-badge.py --prove-red      # the mutations, each refused by name
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import estimate_badge_decls as decls  # noqa: E402
import frozen_comments  # noqa: E402  (T-0407: no /* */ block comment in a file a badge block lives in)

ROOT = pathlib.Path(__file__).resolve().parents[2]
APPROVED_FILE = ROOT / "ops" / "lib" / "check-estimate-badge-approved.txt"
WORD = re.compile(r"(?<![A-Za-z0-9_])(estimate|estimateBadge|etaIsEstimate|showsEstimateBadge|estimateTag|"
                  r"roundTripMinutes|roundTrip|roundTripValue|etaLine|etaHero|etaMinutes|etaRow|etaSeconds|fastestEtaSeconds|"
                  r"durationSeconds|remainingSeconds|glanceLine)"
                  r"(?![A-Za-z0-9_])")
MIN_FILES = 60
S = "Packages/ScenicApp/Sources/"
CARD = S + "FeatureSurpriseMe/SurpriseCard.swift"
PLAN, LOOP, TRIP = (S + "FeaturePlanSheet/PlanPreviewCard.swift", S + "FeaturePlanSheet/LoopPreviewCard.swift",
                    S + "FeaturePlanSheet/TripItineraryCard.swift")
DRIVE = S + "FeatureScenicHome/DriveCard.swift"
MENU = S + "FeatureScenicHome/DriveMenuChips.swift"
BLOCKS = [
    (CARD, "roundTrip(minutes: pick.reason.roundTripMinutes)"),
    (CARD, "private func roundTrip(minutes: Int) -> some View {"),
    (CARD, "private func roundTripValue(minutes: Int) -> some View {"),
    (CARD, "private var estimateTag: some View {"),
    (CARD, 'static let estimate = "estimate \u00b7 no traffic data"'),
    (PLAN, "private var etaRow: some View {"),
    (PLAN, "if preview.showsEstimateBadge {"),
    (LOOP, "if preview.etaIsEstimate {"),
    (TRIP, "if itinerary.etaIsEstimate {"),
    (DRIVE, "if showsEstimate {"),
    (MENU, "VStack(alignment: .leading, spacing: 0) {"),
]


class Refusal(Exception):
    pass


def kept(path: pathlib.Path) -> list[str]:
    lines = [raw.rstrip("\r").strip() for raw in path.read_text(encoding="utf-8").split("\n")]
    return [line for line in lines if not line.startswith("//")]


def swift(tree: pathlib.Path) -> list[tuple[str, list[str]]]:
    files = sorted(tree.rglob("*.swift"), key=lambda p: p.relative_to(tree).as_posix())
    if len(files) < MIN_FILES:
        raise Refusal(f"only {len(files)} .swift files under {tree} (at least {MIN_FILES}): wrong tree")
    return [(path.relative_to(tree).as_posix(), kept(path)) for path in files]


def population(files: list[tuple[str, list[str]]]) -> list[tuple[str, str]]:
    return [(rel, line) for rel, lines in files for line in lines if WORD.search(line)]


def declarations(files: list[tuple[str, list[str]]], blocks: dict) -> list[tuple[str, tuple]]:
    bare = decls.bare(files)
    if bare:
        raise Refusal("a declaration keyword ends a line (its name is on the next line, unseen):\n    " +
                      "\n    ".join(bare[:5]))
    return decls.declarations(files, decls.names([line for value in blocks.values() for line in value[1]]))


def block(tree: pathlib.Path, rel: str, decl: str) -> tuple[str, list[str], str]:
    path = tree / rel
    if not path.is_file():
        raise Refusal(f"{rel}: missing (a badge block lives there)")
    lines = kept(path)
    at = [i for i, line in enumerate(lines) if line == decl]
    if len(at) != 1:
        raise Refusal(f"{rel}: the declaration `{decl}` occurs {len(at)} times (exactly 1 approved)")
    start = end = at[0]
    depth = lines[start].count("{") - lines[start].count("}")
    while depth > 0:
        end += 1
        if end >= len(lines):
            raise Refusal(f"{rel}: `{decl}` never closes")
        depth += lines[end].count("{") - lines[end].count("}")
    above = next((line for line in reversed(lines[:start]) if line), "<start of file>")
    below = next((line for line in lines[end + 1:] if line), "<end of file>")
    return above, lines[start:end + 1], below


def approved() -> tuple[list[tuple[str, str]], dict[tuple[str, str], tuple[str, list[str], str]]]:
    sites, blocks, current, found = [], {}, None, []
    for raw in APPROVED_FILE.read_text(encoding="utf-8").split("\n"):
        if not raw:
            continue
        kind, _, rest = raw.partition("\t")
        if kind == "SITE":
            rel, _, line = rest.partition("\t")
            sites.append((rel, line))
        elif kind == "DECL":
            rel, _, line = rest.partition("\t")
            found.append((rel, [line]))
            current = None
        elif kind == "DLINE" and found and current is None:
            found[-1][1].append(rest)
        elif kind == "BLOCK":
            rel, _, decl = rest.partition("\t")
            current = (rel, decl)
            blocks[current] = ["", [], ""]
        elif kind in ("ABOVE", "BODY", "BELOW") and current is not None:
            entry = blocks[current]
            if kind == "BODY":
                entry[1].append(rest)
            else:
                entry[0 if kind == "ABOVE" else 2] = rest
        else:
            raise Refusal(f"{APPROVED_FILE.name}: unreadable record {raw!r}")
    if sorted(blocks) != sorted(BLOCKS):
        raise Refusal(f"{APPROVED_FILE.name}: its BLOCK records are not this guard's {len(BLOCKS)} blocks")
    return sites, {key: tuple(value) for key, value in blocks.items()}, [(r, tuple(b)) for r, b in found]


def check(tree: pathlib.Path) -> None:
    if not tree.is_dir():
        raise Refusal(f"no such directory: {tree}")
    sites, blocks, approved_decls = approved()
    try:
        hidden = [ln for rel in dict.fromkeys(r for r, _ in BLOCKS) if (tree / rel).is_file()
                  for ln in frozen_comments.refusals(tree / rel, rel)]
    except frozen_comments.CannotRun as e:
        raise Refusal(f"the block-comment rule cannot run ({e}) - a badge file it cannot read is never a pass")
    if hidden:
        raise Refusal("\n  ".join(hidden))
    files = swift(tree)
    found = population(files)
    if found != sites:
        extra = [f"{f}: {l}" for f, l in found if (f, l) not in sites]
        missing = [f"{f}: {l}" for f, l in sites if (f, l) not in found]
        raise Refusal(f"a line naming an ETA or the estimate badge is not an approved whole line ({len(found)} "
                      f"found, {len(sites)} approved)\n  unapproved: " + ("\n    ".join([""] + extra) if extra else
                      "none") + "\n  missing: " + ("\n    ".join([""] + missing) if missing else
                      "none (the order differs)") + "\n  Every ETA shows the estimate · no traffic data badge.")
    for rel, decl in BLOCKS:
        got, want = block(tree, rel, decl), blocks[(rel, decl)]
        if got != want:
            diff = [f"{name}: {g!r} (approved {w!r})" for name, g, w in
                    (("above", got[0], want[0]), ("below", got[2], want[2])) if g != w]
            body = [f"body: {g!r} (approved {w!r})" for g, w in zip(got[1], want[1]) if g != w]
            if len(got[1]) != len(want[1]):
                body.append(f"body: {len(got[1])} lines (approved {len(want[1])})")
            raise Refusal(f"the badge block `{decl}` changed\n  {rel}: " + "; ".join(diff + body)[:400] +
                          "\n  Every ETA shows the estimate · no traffic data badge.")
    got = declarations(files, blocks)
    if got != approved_decls:
        extra = [f"{r}: {' / '.join(b)[:150]}" for r, b in got if (r, b) not in approved_decls]
        missing = [f"{r}: {' / '.join(b)[:150]}" for r, b in approved_decls if (r, b) not in got]
        raise Refusal(f"a declaration of a name the badge blocks use is not approved ({len(got)} found, "
                      f"{len(approved_decls)} approved)\n  unapproved: " + ("\n    ".join([""] + extra[:6]) if extra
                      else "none") + "\n  missing: " + ("\n    ".join([""] + missing[:6]) if missing else
                      "none (the order differs)") + "\n  Every ETA shows the estimate · no traffic data badge.")


MUTATIONS = [
    ("M1 both estimateTag lines dropped from the round trip", CARD,
     "roundTripValue(minutes: minutes)\n                    estimateTag\n                }\n                VStack"
     "(alignment: .leading, spacing: 4) {\n                    roundTripValue(minutes: minutes)\n"
     "                    estimateTag\n", "roundTripValue(minutes: minutes)\n                }\n                VStack"
     "(alignment: .leading, spacing: 4) {\n                    roundTripValue(minutes: minutes)\n"),
    ("the AX branch alone loses the tag", CARD, "spacing: 4) {\n                    roundTripValue(minutes: minutes)"
     "\n                    estimateTag\n", "spacing: 4) {\n                    roundTripValue(minutes: minutes)\n"),
    ("the tag drawn invisible", CARD, '.accessibilityIdentifier("surprise.estimate")',
     '.accessibilityIdentifier("surprise.estimate")\n            .opacity(0)'),
    ("the tag's copy respelled", CARD, 'Text(Copy.estimate)', 'Text("estimate")'),
    ("the round trip hidden at its call", CARD, "roundTrip(minutes: pick.reason.roundTripMinutes)\n",
     "roundTrip(minutes: pick.reason.roundTripMinutes)\n                .hidden()\n"),
    ("the round trip behind `if false {`", CARD, "            roundTrip(minutes: pick.reason.roundTripMinutes)\n",
     "            if false {\n            roundTrip(minutes: pick.reason.roundTripMinutes)\n            }\n"),
    ("the plan card's badge block dropped", PLAN, "if preview.showsEstimateBadge {", "if false {"),
    ("the plan card's AX branch loses its tag", PLAN, "spacing: 6) {\n                etaText\n                estimateTag\n",
     "spacing: 6) {\n                etaText\n"),
    ("the drive card's badge cleared", DRIVE, '.accessibilityIdentifier("drive.estimate")',
     '.accessibilityIdentifier("drive.estimate")\n                    .hidden()'),
    ("the home menu's badge cleared on its own line", MENU, '.accessibilityIdentifier("home.menu.estimate")',
     '.accessibilityIdentifier("home.menu.estimate")\n                .hidden()'),
    ("the drive card's arrival drawn under a new name", DRIVE, "addingTimeInterval(remainingSeconds)",
     "addingTimeInterval(secondsLeft)"),
    ("B1 a file-scoped DesignTokens shadows the tag's colours", CARD, None,
     "\nprivate enum DesignTokens {\n    static let fgMuted = SwiftUI.Color.clear\n    static let border = SwiftUI.Color.clear"
     "\n    static let fg = SwiftUI.Color.clear\n}\n"),
    ("R2-B1 a backticked `DesignTokens` let over a shadow enum", CARD, None,
     "\nprivate enum ShadowTokens {\n    static let `fg` = SwiftUI.Color.clear\n    static let `fgMuted` = SwiftUI.Color"
     ".clear\n    static let `border` = SwiftUI.Color.clear\n}\nprivate let `DesignTokens` = ShadowTokens.self\n"),
    ("an extension Text init swallows the copy", None, S + "FeatureSurpriseMe/SurpriseText.swift",
     "import SwiftUI\nextension Text {\n    init(_ s: String) { self.init(verbatim: \"\") }\n}\n"),
    ("a View modifier overload hides the tag", None, S + "FeatureSurpriseMe/SurpriseStyle.swift",
     "import SwiftUI\nextension View {\n    func fixedSize(horizontal: Bool, vertical: Bool) -> some View { hidden() }\n}\n"),
    ("the border token's dark value cleared", S + "DesignSystem/DesignTokens.swift", "UIColor(white: 1.0, alpha: 0.08)",
     "UIColor(white: 1.0, alpha: 0.0)"),
    ("the private dynamic() helper answers clear", S + "DesignSystem/DesignTokens.swift",
     "traits.userInterfaceStyle == .dark ? srgb(dark) : srgb(light)", "srgb(light, alpha: 0)"),
    ("a declaration split across lines", S + "DesignSystem/DesignTokens.swift", "public static let fgMuted = ",
     "public static let\n    fgMuted = "),
    ("a new surface draws an ETA", None, S + "FeatureSurpriseMe/SurpriseEta.swift",
     "import SwiftUI\nstruct SurpriseEta: View {\n    let etaSeconds: Int\n    var body: some View { Text(\"\\(etaSeconds)\") }\n}\n"),
]


def prove_red(tree: pathlib.Path) -> int:
    check(tree)
    bad = 0
    for name, rel, old, new in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            copy = pathlib.Path(tmp) / "ios"
            shutil.copytree(tree, copy, ignore=shutil.ignore_patterns("*.png", "*.pmtiles", ".build"))
            if rel is None:
                (copy / old).write_text(new, encoding="utf-8")
            elif old is None:
                with (copy / rel).open("a", encoding="utf-8", newline="\n") as tail:
                    tail.write(new)
            else:
                text = (copy / rel).read_text(encoding="utf-8").replace("\r\n", "\n")
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
                print(f"[red] {name}: {str(refusal).splitlines()[0][:110]}")
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
        print(f"P-SAFE-07: {refusal}")
        return 1
    sites, _, found = approved()
    print(f"P-SAFE-07 (screen): {len(sites)} approved whole lines name an ETA or the estimate badge under apps/ios "
          f"and no other line does; {len(BLOCKS)} badge blocks equal their approved bodies and fences; "
          f"{len(found)} declarations ({sum(len(b) for _, b in found)} lines) of the names they use are approved.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
