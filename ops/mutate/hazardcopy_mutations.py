"""The mutation population for T-0339's hazard copy table (Sources/ScenicKit/Hazards/HazardCopy.swift). Driver
hazardcopy.py, runner hazardcopy_run.py (tripsheet's shape).

  * THE ROWS (1-3): a row's line changed, a row dropped, a whitelisted value added as a row;
  * THE UNKNOWNS (4-8, 21): the wrong kind fallback, the raw key on an unknown kind, the match widened by case or by
    trimming, every run called known, a fallback that spells a wire key;
  * THE STRIP (9-10): runs dropped past a count, unknown runs dropped;
  * THE FLAGS (11-18, 22-23): a blank closure source dropped or untrimmed, the time zone ignored, a 24-hour clock,
    km rounded to whole, minutes rounded, the raw tag shown, the ford and gate warnings softened, the no-reopening
    clause lost;
  * THE FIXED LINES (19-20): the empty-strip line changed, the generic line a wire key.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

COPY = ROOT / "Sources" / "ScenicKit" / "Hazards" / "HazardCopy.swift"
SUBJECTS = (COPY,)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "Hazards" / "HazardCopyTests.swift",)

ROW = "every Worker hazard row reads its ruled line, whole"
UNKNOWN = "an unlisted value or kind reads a safe line, never the raw key"
FLAG = "every hazard flag reads its ruled line, whole"
STRIP = "the strip keeps one line per hazard, in order"
WIRE = "no copy line is empty, and none spells a wire key"

MATCH = "if let line = runLines[run.kind]?[run.value] { return line }"
GENERIC = '"Something on part of this route needs a closer look - check the road before you drive it"'
SURFACE = '"Road surface we cannot name on part of this route - check it suits your car"'
NO_ROW = '"no": "No entry for cars on part of this route - do not drive it",'

MUTATIONS = [
    ("1 a row's line changed", COPY, '"destination": "Local traffic only \\(through)"',
     '"destination": "Private road ahead - local access only"', [ROW]),
    ("2 a row dropped", COPY, '            "sand": "Sand on part of this route - cars can get stuck",\n', "",
     [ROW, WIRE]),
    ("3 a whitelisted value added as a row", COPY, NO_ROW,
     NO_ROW + '\n            "yes": "Open road on part of this route",', [ROW, UNKNOWN, WIRE]),
    ("4 an unlisted access value reads the surface fallback", COPY, 'case "road_access": return accessFallback',
     'case "road_access": return surfaceFallback', [UNKNOWN, STRIP]),
    ("5 an unknown kind reads its raw key", COPY, "default: return genericLine",
     'default: return "\\(run.kind): \\(run.value)"', [UNKNOWN, STRIP]),
    ("6 the match widened by case", COPY, MATCH,
     "if let line = runLines[run.kind]?[run.value.lowercased()] { return line }", [UNKNOWN]),
    ("7 the match widened by trimming", COPY, MATCH,
     "if let line = runLines[run.kind]?[run.value.trimmingCharacters(in: .whitespaces)] { return line }",
     [UNKNOWN]),
    ("8 every run called known", COPY, "runLines[run.kind]?[run.value] != nil", "true", [UNKNOWN]),
    ("9 the strip stops at three", COPY, "preview.hazards.map { line(for: $0) }",
     "preview.hazards.prefix(3).map { line(for: $0) }", [STRIP]),
    ("10 the strip drops unknown runs", COPY, "preview.hazards.map { line(for: $0) }",
     "preview.hazards.filter { isKnown($0) }.map { line(for: $0) }", [STRIP]),
    ("11 a blank closure source reads nothing", COPY, 'named.isEmpty ? "source not named"', 'named.isEmpty ? ""',
     [FLAG]),
    ("12 a closure source untrimmed", COPY, "let named = source.trimmingCharacters(in: .whitespacesAndNewlines)",
     "let named = source", [FLAG]),
    ("13 the time zone ignored", COPY, "formatter.timeZone = timeZone",
     'formatter.timeZone = TimeZone(identifier: "UTC")!', [FLAG]),
    ("14 a 24-hour arrival clock", COPY, 'format(at, "h:mm a", timeZone)', 'format(at, "HH:mm", timeZone)', [FLAG]),
    ("15 km rounded to whole", COPY, '"%.1f"', '"%.0f"', [FLAG]),
    ("16 minutes rounded down to fives", COPY, "about \\(minutes) min", "about \\(minutes / 5 * 5) min", [FLAG]),
    ("17 the raw tag shown", COPY, "case .unrecognised:\n            return genericLine",
     "case let .unrecognised(tag):\n            return tag", [FLAG]),
    ("18 the ford warning softened", COPY, "do not drive in if it is deep or flowing", "take care", [FLAG]),
    ("19 the empty-strip line changed", COPY, '"Nothing unpaved or restricted is flagged on this route."',
     '"No hazards."', [WIRE]),
    ("20 the generic line a wire key", COPY, GENERIC, '"unknown_hazard"', [WIRE, UNKNOWN, FLAG, STRIP]),
    ("21 the surface fallback spells a key", COPY, SURFACE, '"surface: unknown"', [WIRE, UNKNOWN]),
    ("22 the no-reopening clause lost", COPY, '?? ", no reopening time given"', '?? ""', [FLAG]),
    ("23 the gate warning softened", COPY, "it may be closed or locked", "it may be open", [FLAG]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 the two kind fallbacks swapped in order", COPY,
     'case "surface": return surfaceFallback\n        case "road_access": return accessFallback',
     'case "road_access": return accessFallback\n        case "surface": return surfaceFallback',
     "the switch cases match distinct string literals, so at most one matches any kind and their order is moot"),
]

MIN_MUTATIONS = 23
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 1
