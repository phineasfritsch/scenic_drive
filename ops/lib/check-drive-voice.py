#!/usr/bin/env python3
"""P-SAFE-09's voice half on the app side (T-0329 R1): the drive says only what ScenicKit's DriveVoice chose.

DriveVoice (what is said, and when) is Linux-tested whole in DriveVoiceTests, bound by name in P-SAFE-09's row. What
no Linux test can see is whether the app SPEAKS only those strings: a navigator that skips `utterances(after:)`, a
call site that speaks a literal, a step handed to Ferrostar with its own `spokenInstructions` (Ferrostar would then
speak on its own trigger), SSML that rewrites the text, or a second synthesizer anywhere in the app would each compile.
So this is a WHITELIST OF WHOLE LINES: every line under apps/ios naming DriveVoice, SpokenInstruction (any case,
which covers spokenInstructions and spokenInstructionObserver), AVSpeech, SpeechSynthesizer, `speak(` or
`utterances(` is one of the approved lines below, at its file, in scan order (paths sorted, then line order). A line
is dropped only when its trimmed text STARTS with `//`; nothing is cut inside a line (source-guards-fail-closed).

WHAT IT CANNOT SEE: whether the device actually produces sound (a drive on a phone), and Swift outside apps/ios.

    python ops/lib/check-drive-voice.py                  # the tracked tree
    python ops/lib/check-drive-voice.py --app-tree DIR   # a copy of apps/ios
    python ops/lib/check-drive-voice.py --prove-red      # the mutations, each refused by name
"""
from __future__ import annotations

import pathlib
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORD = re.compile(r"DriveVoice|spokeninstruction|avspeech|speechsynthesizer|(?<![A-Za-z0-9_])(speak|utterances)\(",
                  re.IGNORECASE)
MIN_FILES = 60
S = "Packages/ScenicApp/Sources/"
NAV, ROUTE = S + "NavAdapter/DriveNavigator.swift", S + "NavAdapter/FerrostarDriveRoute.swift"
SPEAK = ("let instruction = SpokenInstruction(text: text, ssml: nil, triggerDistanceBeforeManeuver: 0, "
         "utteranceId: UUID())")
APPROVED = [
    (NAV, "private var voice: DriveVoice"),
    (NAV, "voice = DriveVoice(session: session)"),
    (NAV, "for text in voice.utterances(after: controller.session) { speak(text) }"),
    (NAV, "private func speak(_ text: String) {"),
    (NAV, SPEAK),
    (NAV, "core.spokenInstructionObserver.spokenInstructionTriggered(instruction)"),
    (ROUTE, "exits: [], instruction: text, visualInstructions: [banner], spokenInstructions: [],"),
]
MUTATIONS = [
    ("the navigator never asks DriveVoice", NAV,
     "for text in voice.utterances(after: controller.session) { speak(text) }", "_ = controller.session"),
    ("the navigator speaks a literal of its own", NAV,
     "for text in voice.utterances(after: controller.session) { speak(text) }",
     'for text in voice.utterances(after: controller.session) { speak(text) }\n        speak("Turn now")'),
    ("SSML rewrites the chosen text", NAV, "ssml: nil,", 'ssml: "<speak>Hurry</speak>",'),
    ("Ferrostar is handed steps it speaks by itself", ROUTE, "spokenInstructions: [],",
     'spokenInstructions: [SpokenInstruction(text: text, ssml: nil, triggerDistanceBeforeManeuver: 500, '
     'utteranceId: UUID())],'),
    ("the voice is built over another session", NAV, "voice = DriveVoice(session: session)",
     "voice = DriveVoice(session: controller.session)"),
    ("a second synthesizer in a feature file", None, S + "FeatureScenicHome/DriveChatter.swift",
     "import AVFoundation\nenum DriveChatter {\n    static let voice = AVSpeechSynthesizer()\n}\n"),
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
        raise Refusal("a line naming DriveVoice, SpokenInstruction, AVSpeech, SpeechSynthesizer, speak( or "
                      f"utterances( is not an approved whole line ({len(found)} found, {len(APPROVED)} approved)\n"
                      "  unapproved: " + ("\n    ".join([""] + extra) if extra else "none") + "\n  missing: "
                      + ("\n    ".join([""] + missing) if missing else "none (the order differs)")
                      + "\n  The drive speaks exactly what ScenicKit's DriveVoice chose, through Ferrostar's own "
                      "observer, and Ferrostar is handed nothing to speak by itself (P-SAFE-09, T-0329 R1).")


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
    print(f"P-SAFE-09 (voice): {len(APPROVED)} approved whole lines speak under apps/ios, and no other line does: "
          "the drive says only what DriveVoice chose, through Ferrostar's own observer.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
