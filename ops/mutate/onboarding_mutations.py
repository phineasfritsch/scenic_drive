"""The mutation population for T-0309's first-run onboarding: the state machine (Sources/ScenicKit/Vehicle/
Onboarding.swift) and the closed vehicle enum (Sources/ScenicKit/Vehicle/VehicleProfile.swift). The driver is
onboarding.py and the runner onboarding_run.py (saveddrive's three-file shape).

## What the acceptance names, and where each lives

  * the MACHINE - choose refused when disabled, skip and back and next never accepting, accept only from the
    disclaimer step, done absorbing, the first-launch value - entries 1-9 (R3);
  * the VEHICLE - only .standard enabled, every reason and name whole, the stored read-back, the store key -
    entries 10-15 (R2, R3).

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names in OnboardingTransitionTests, VehicleProfileTests and
OnboardingPlanGateTests, every one of which must go red. EQUIVALENT entries are `(name, path, old, new, witness)`
and must all report MISSED.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "ScenicKit" / "Vehicle"
MACHINE = _DIR / "Onboarding.swift"
VEHICLE = _DIR / "VehicleProfile.swift"
SUBJECTS = (MACHINE, VEHICLE)
MUTATED_FILES = SUBJECTS

_TESTS = ROOT / "Tests" / "ScenicKitTests" / "Vehicle"
TEST_FILES = (_TESTS / "OnboardingTransitionTests.swift", _TESTS / "VehicleProfileTests.swift",
              _TESTS / "OnboardingPlanGateTests.swift")

TRANS = "transition table: send(event) from each state equals the row's whole expected value"
NEVER = "skipping or backing out never marks the disclaimer accepted"
ACCEPT = "accept marks the disclaimer accepted only from the disclaimer step"
FIRST = "first launch is the vehicle step with a standard car and nothing accepted"
GATE = "first launch through onboarding: zero plan requests before accept, one after"
PROFILE = "only standard is enabled; every other case is present with its reason, whole"
STORED = "stored: absent, unknown and disabled raw values read back as standard"

CHOOSE = "if profile.isEnabled { vehicle = profile }"
FORWARD = "case (.vehicle, .next), (.vehicle, .skip):\n            step = .disclaimer"
BACK = "case (.disclaimer, .back):\n            step = .vehicle"
ACCEPTED = "            step = .done\n            disclaimerAccepted = true"
FIRST_INIT = "self.init(step: .vehicle, vehicle: .standard, disclaimerAccepted: false)"

MUTATIONS = [
    ("1 choose ignores isEnabled", MACHINE, CHOOSE, "vehicle = profile", [TRANS]),
    ("2 skip on the disclaimer accepts", MACHINE, "case (.disclaimer, .accept):",
     "case (.disclaimer, .accept), (.disclaimer, .skip):", [TRANS, NEVER]),
    ("3 back on the disclaimer finishes", MACHINE, BACK, "case (.disclaimer, .back):\n            step = .done",
     [TRANS, NEVER]),
    ("4 accept finishes without recording", MACHINE, ACCEPTED,
     "            step = .done\n            disclaimerAccepted = false", [TRANS, ACCEPT, GATE]),
    ("5 accept from the vehicle step", MACHINE, "case (.disclaimer, .accept):",
     "case (.disclaimer, .accept), (.vehicle, .accept):", [TRANS, ACCEPT]),
    ("6 first launch opens on the disclaimer", MACHINE, FIRST_INIT,
     "self.init(step: .disclaimer, vehicle: .standard, disclaimerAccepted: false)", [FIRST, ACCEPT]),
    ("7 first launch already accepted", MACHINE, FIRST_INIT,
     "self.init(step: .vehicle, vehicle: .standard, disclaimerAccepted: true)", [FIRST, GATE]),
    ("8 back leaves done", MACHINE, "case (.disclaimer, .back):", "case (.disclaimer, .back), (.done, .back):",
     [TRANS]),
    ("9 next on the vehicle step finishes", MACHINE, FORWARD,
     "case (.vehicle, .next), (.vehicle, .skip):\n            step = .done", [TRANS, NEVER]),
    ("10 motorcycle enabled", VEHICLE, "disabledReason == nil", "disabledReason == nil || self == .motorcycle",
     [PROFILE, STORED, TRANS]),
    ("11 stored reads back a disabled case", VEHICLE, ", profile.isEnabled else", " else", [STORED]),
    ("12 a reason reworded", VEHICLE, 'case .rv: return "Not yet. The map has no height',
     'case .rv: return "Not yet. The map has no height or weight', [PROFILE]),
    ("13 standard given a reason", VEHICLE, "case .standard: return nil", 'case .standard: return "Not yet."',
     [PROFILE]),
    ("14 store key bumped", VEHICLE, '"vehicle.profile.v1"', '"vehicle.profile.v2"', [PROFILE]),
    ("15 standard renamed", VEHICLE, 'case .standard: return "Standard car"', 'case .standard: return "Car"',
     [PROFILE]),
]

EQUIVALENT = [
    ("E1 choose skips an equal vehicle", MACHINE, CHOOSE, "if profile.isEnabled && profile != vehicle { vehicle = profile }",
     "assigning a VehicleProfile equal to the stored one leaves the value, and so the whole Onboarding, unchanged"),
]

MIN_MUTATIONS = 15
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 3
