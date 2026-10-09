#!/usr/bin/env python3
"""P-PRIV-02 (T-0329 R4/R5): the app's UIBackgroundModes is EXACTLY the ruled set, in the source plist and the built one.

The plan's row: UIBackgroundModes subset of {location, audio}; location only with the drive present. T-0329 ruled the
set to exactly ["audio", "location"] while NavAdapter's DriveNavigator exists (spoken guidance needs audio, and a
backgrounded app gets no fix to speak from without location), and NO key at all without it. A key Apple reads at
install time is not something a Swift test can see, so this reads it:

  * the plist through plistlib (XML or binary), and requires list EQUALITY - order, duplicates, extra modes, a string
    instead of an array, and a missing key all fail;
  * the project: every configuration sets GENERATE_INFOPLIST_FILE = NO and INFOPLIST_FILE = ScenicDrive/Info.plist,
    and no INFOPLIST_KEY_UIBackgroundModes build setting exists - so the built plist's key is the source file's;
  * `--built-products DIR` (ios-compile.yml, after the simulator build) reads the BUILT ScenicDrive.app/Info.plist
    under DIR - exactly one must exist - with the same equality.

    python ops/lib/check-background-modes.py                         # the tracked plist and project
    python ops/lib/check-background-modes.py --built-products DIR    # and the built app's plist
    python ops/lib/check-background-modes.py --prove-red             # the mutations, each refused by name
"""
from __future__ import annotations

import pathlib
import plistlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PLIST = ROOT / "apps" / "ios" / "ScenicDrive" / "Info.plist"
PBXPROJ = ROOT / "apps" / "ios" / "ScenicDrive.xcodeproj" / "project.pbxproj"
DRIVE = ROOT / "apps" / "ios" / "Packages" / "ScenicApp" / "Sources" / "NavAdapter" / "DriveNavigator.swift"
RULED = ["audio", "location"]
CONFIGURATIONS = 2


class Refusal(Exception):
    pass


def modes_refusal(data: bytes, drive_present: bool, where: str) -> str | None:
    try:
        plist = plistlib.loads(data)
    except Exception as error:  # a plist that does not parse is refused, never skipped
        return f"{where} does not parse as a plist: {error}"
    if not isinstance(plist, dict):
        return f"{where} is not a dictionary"
    if not drive_present:
        return None if "UIBackgroundModes" not in plist else (
            f"{where} declares UIBackgroundModes {plist['UIBackgroundModes']!r} with no drive present")
    modes = plist.get("UIBackgroundModes")
    if type(modes) is not list or modes != RULED:
        return f"{where} UIBackgroundModes is {modes!r}, not exactly {RULED!r}"
    return None


def project_refusal(text: str) -> str | None:
    generate = re.findall(r"GENERATE_INFOPLIST_FILE = ([^;]*);", text)
    files = re.findall(r"(?<![A-Z_])INFOPLIST_FILE = ([^;]*);", text)
    if generate != ["NO"] * CONFIGURATIONS:
        return f"GENERATE_INFOPLIST_FILE is {generate!r}, not NO in each of {CONFIGURATIONS} configurations"
    if files != ["ScenicDrive/Info.plist"] * CONFIGURATIONS:
        return f"INFOPLIST_FILE is {files!r}, not ScenicDrive/Info.plist in each of {CONFIGURATIONS} configurations"
    if "INFOPLIST_KEY_UIBackgroundModes" in text:
        return "a build setting INFOPLIST_KEY_UIBackgroundModes would add modes the plist does not show"
    return None


def built_plist(products: pathlib.Path) -> pathlib.Path:
    found = sorted(p for p in products.rglob("Info.plist") if p.parent.name == "ScenicDrive.app")
    if len(found) != 1:
        raise Refusal(f"expected exactly one ScenicDrive.app/Info.plist under {products}, found {len(found)}")
    return found[0]


def check(plist: bytes, project: str, drive_present: bool, built: bytes | None = None) -> None:
    for refusal in (modes_refusal(plist, drive_present, "Info.plist"), project_refusal(project),
                    None if built is None else modes_refusal(built, drive_present, "the BUILT Info.plist")):
        if refusal:
            raise Refusal(refusal)


def prove_red() -> int:
    plist, project = PLIST.read_bytes(), PBXPROJ.read_text(encoding="utf-8")
    check(plist, project, True)

    def modes(value: str) -> bytes:
        return re.sub(rb"<key>UIBackgroundModes</key>\s*<array>.*?</array>", value.encode(), plist, flags=re.S)

    arr = "<key>UIBackgroundModes</key><array>%s</array>"
    s = "<string>%s</string>"
    cases = [
        ("audio only", modes(arr % (s % "audio")), project, True),
        ("location only", modes(arr % (s % "location")), project, True),
        ("an extra mode", modes(arr % (s % "audio" + s % "location" + s % "fetch")), project, True),
        ("the order swapped", modes(arr % (s % "location" + s % "audio")), project, True),
        ("a duplicate", modes(arr % (s % "audio" + s % "audio" + s % "location")), project, True),
        ("a string, not an array", modes("<key>UIBackgroundModes</key><string>audio location</string>"),
         project, True),
        ("the key missing", modes(""), project, True),
        ("modes with no drive present", plist, project, False),
        ("a generated plist", plist, project.replace("GENERATE_INFOPLIST_FILE = NO;", "GENERATE_INFOPLIST_FILE = YES;",
                                                     1), True),
        ("another plist file", plist, project.replace("INFOPLIST_FILE = ScenicDrive/Info.plist;",
                                                      "INFOPLIST_FILE = ScenicDrive/Other.plist;", 1), True),
        ("a build setting adds a mode", plist, project.replace("GENERATE_INFOPLIST_FILE = NO;",
                                                               "GENERATE_INFOPLIST_FILE = NO; "
                                                               "INFOPLIST_KEY_UIBackgroundModes = fetch;", 1), True),
        ("a plist that does not parse", plist[: len(plist) // 2], project, True),
    ]
    bad = 0
    for name, data, proj, drive in cases:
        try:
            check(data, proj, drive)
            print(f"PROVE-RED SURVIVED: {name}")
            bad += 1
        except Refusal as refusal:
            print(f"[red] {name}: {str(refusal)[:110]}")
    built_name = "the BUILT plist adds a mode"
    try:
        check(plist, project, True, plistlib.dumps({"UIBackgroundModes": RULED + ["fetch"]}, fmt=plistlib.FMT_BINARY))
        print(f"PROVE-RED SURVIVED: {built_name}")
        bad += 1
    except Refusal as refusal:
        print(f"[red] {built_name}: {str(refusal)[:110]}")
    total = len(cases) + 1
    print(f"PROVE-RED {'OK' if bad == 0 else 'FAIL'}: {total - bad}/{total} refused by name")
    return 0 if bad == 0 else 1


def main(argv: list[str]) -> int:
    try:
        if "--prove-red" in argv:
            return prove_red()
        built = None
        if "--built-products" in argv:
            built = built_plist(pathlib.Path(argv[argv.index("--built-products") + 1])).read_bytes()
        check(PLIST.read_bytes(), PBXPROJ.read_text(encoding="utf-8"), DRIVE.exists(), built)
    except (Refusal, OSError) as refusal:
        print(f"P-PRIV-02: {refusal}")
        return 1
    print(f"P-PRIV-02: UIBackgroundModes is exactly {RULED!r} with the drive present"
          + (", in the source plist and the BUILT one" if built is not None else " in the source plist")
          + "; the project generates no plist and adds no mode.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
