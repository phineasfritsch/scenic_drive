"""The mutation population for T-0366: the next-open question after a handoff - the fix's surface
(Sources/ScenicKit/PostDrive/PostDriveFix.swift), the marker's lifecycle (PostDriveNextOpen.swift), the moments that
set it (HandoffMarkingMoments.swift) and the device store (DefaultsHandoffMarker.swift). Driver postdrive.py, runner
postdrive_run.py (waitlist's three-file shape).

  * THE FIX'S BOUNDS (1-12): each half-bound of accuracy and age deleted, made exclusive, widened; the age literal
    moved both ways; the surface forced full on either branch;
  * THE MARKER (13-24): the open count moved both ways, the clamp's upper half, each guard, the re-read, the spend,
    the ask's spend, the surface and the unknown fix forced full, the model's row swapped;
  * THE MOMENTS (25-30): each handoff unmarked, every other moment marked, the inner dropped, the count changed;
  * THE STORE (31-33): the key renamed, the read dropped, a second key written.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "ScenicKit" / "PostDrive"
FIX = _DIR / "PostDriveFix.swift"
OPEN = _DIR / "PostDriveNextOpen.swift"
MOMENTS = _DIR / "HandoffMarkingMoments.swift"
STORE = _DIR / "DefaultsHandoffMarker.swift"
SUBJECTS = (FIX, OPEN, MOMENTS, STORE)
MUTATED_FILES = SUBJECTS

_TESTS = ROOT / "Tests" / "ScenicKitTests" / "PostDrive"
TEST_FILES = (_TESTS / "PostDriveNextOpenTests.swift", _TESTS / "PostDriveFixTests.swift",
              _TESTS / "HandoffMarkingMomentsTests.swift")

LIFE = "T-0366 R2: every stored marker x every reading - asks, the marker after and the fix reads, compared whole"
SEQ = "T-0366 R1/R2: every sequence of four opens after a handoff asks exactly at the first stopped open of three"
ANS = ("T-0366 R6: after an ask every answer reaches the sink as the drive screen's does, and no later open asks "
       "until the next handoff")
SPENT = "T-0366 R2/R4: the marker is re-read after the fix - a marker spent while the fix was read asks nothing"
BOUND = "T-0366 R3: every speed x accuracy x age bound - full exactly on the typed rows, else minimal"
MOM = ("T-0366 R1: every moment x a stored marker x an inner reporter or none - the marker after and what the "
       "inner heard")
DOM = "T-0366 R1: the device store keeps exactly one Int under one key - its whole domain after a handoff and an open"

AGE_MAX = "ageSeconds <= Self.maxAgeSeconds"
MARKS = "case .driveHandedToAppleMaps, .surpriseHandedToAppleMaps:\n            return true\n        case "
OTHERS = "case .planPreviewOnScreen, .surpriseDeclined, .guidanceBegan, .guidanceEnded:\n            return false"

MUTATIONS = [
    ("1 the accuracy's lower bound deleted", FIX, "speedAccuracy >= 0, ", "", [BOUND]),
    ("2 the accuracy's lower bound exclusive", FIX, "speedAccuracy >= 0,", "speedAccuracy > 0,", [BOUND]),
    ("3 the accuracy's lower bound one ulp wide", FIX, "speedAccuracy >= 0,", "speedAccuracy >= (0.0).nextDown,",
     [BOUND]),
    ("4 an infinite accuracy admitted", FIX, "speedAccuracy.isFinite, ", "", [BOUND]),
    ("5 the age's lower bound deleted", FIX, "ageSeconds >= 0, ", "", [BOUND]),
    ("6 the age's lower bound exclusive", FIX, "ageSeconds >= 0,", "ageSeconds > 0,", [BOUND]),
    ("7 the age's upper bound exclusive", FIX, AGE_MAX, "ageSeconds < Self.maxAgeSeconds", [BOUND]),
    ("8 the age's upper bound deleted", FIX, ", " + AGE_MAX + " else", " else", [BOUND]),
    ("9 the age limit 11 s", FIX, "maxAgeSeconds: Double = 10", "maxAgeSeconds: Double = 11", [BOUND]),
    ("10 the age limit 9 s", FIX, "maxAgeSeconds: Double = 10", "maxAgeSeconds: Double = 9", [BOUND]),
    ("11 a known fresh fix always full", FIX, "return DriveSurface(speedMetersPerSecond: speedMetersPerSecond)",
     "return .full", [BOUND]),
    ("12 an unknown or stale fix read by its speed", FIX, "return .minimal",
     "return DriveSurface(speedMetersPerSecond: speedMetersPerSecond)", [BOUND]),
    ("13 four opens after a handoff", OPEN, "opensAfterHandoff = 3", "opensAfterHandoff = 4", [LIFE]),
    ("14 two opens after a handoff", OPEN, "opensAfterHandoff = 3", "opensAfterHandoff = 2", [LIFE]),
    ("15 the clamp's upper half dropped", OPEN, "min(max(stored, 0), opensAfterHandoff)", "max(stored, 0)",
     [LIFE]),
    ("16 a fix read with nothing pending", OPEN,
     "guard pending(marker.opensLeft()) > 0 else { return false }\n", "", [LIFE]),
    ("17 the guard after the read dropped", OPEN, "guard left > 0 else { return false }\n", "", [SPENT]),
    ("18 the marker not re-read after the fix", OPEN, "let left = pending(marker.opensLeft())",
     "let left = pending(opensAfterHandoff)", [LIFE]),
    ("19 an open that does not ask spends nothing", OPEN, "asks ? 0 : left - 1", "asks ? 0 : left", [LIFE]),
    ("20 an ask spends one open only", OPEN, "asks ? 0 : left - 1", "asks ? left - 1 : left - 1", [ANS, LIFE]),
    ("21 the fix's surface ignored, full", OPEN, "surface: surface,", "surface: .full,", [LIFE]),
    ("22 no fix read as full", OPEN, "?? .minimal", "?? .full", [LIFE]),
    ("23 the model's arrived row asked", OPEN, "outcome: .handedOff, moment: .appOpened",
     "outcome: .arrived, moment: .appOpened", [LIFE]),
    ("24 the ask never spends the marker", OPEN, "marker.setOpensLeft(asks ? 0 : left - 1)",
     "marker.setOpensLeft(left - 1)", [ANS]),
    ("25 a Surprise handoff unmarked", MOMENTS, MARKS,
     "case .driveHandedToAppleMaps:\n            return true\n        case .surpriseHandedToAppleMaps, ", [MOM, ANS]),
    ("26 a drive handoff unmarked", MOMENTS, MARKS,
     "case .surpriseHandedToAppleMaps:\n            return true\n        case .driveHandedToAppleMaps, ", [MOM, SEQ]),
    ("27 every other moment marks", MOMENTS, OTHERS,
     "case .planPreviewOnScreen, .surpriseDeclined, .guidanceBegan, .guidanceEnded:\n            return true",
     [MOM]),
    ("28 the inner reporter dropped", MOMENTS, "inner?.report(moment)", "_ = inner", [MOM]),
    ("29 every moment marks", MOMENTS, "if Self.marks(moment) {", "if true {", [MOM]),
    ("30 a handoff leaves one open", MOMENTS, "marker.setOpensLeft(PostDriveNextOpen.opensAfterHandoff)",
     "marker.setOpensLeft(1)", [MOM, SEQ]),
    ("31 the key renamed", STORE, 'key = "postDrive.handoffOpensLeft"', 'key = "postDrive.handoffOpensLeft2"',
     [DOM]),
    ("32 the stored value never read", STORE, "defaults.integer(forKey: Self.key)", "0", [DOM]),
    ("33 a second key written beside it", STORE, "defaults.set(value, forKey: Self.key)",
     'defaults.set(value, forKey: Self.key); defaults.set(1, forKey: "postDrive.when")', [DOM]),
]

EQUIVALENT = [
    ("E1 the clamp's lower half dropped", OPEN, "min(max(stored, 0), opensAfterHandoff)",
     "min(stored, opensAfterHandoff)",
     "a negative stored value fails `pending(...) > 0` with or without the lower clamp, and `left` is used only "
     "after `guard left > 0`, so no return and no write changes"),
]

MIN_MUTATIONS = 33
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 3
