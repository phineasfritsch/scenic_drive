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
  * THE CLOSURE LINES (24-33, T-0341 R2): each line softened, dropped or reordered, a card left silent;
  * THE READER (34-44, T-0341 R3, ScenicAPIClient/ClosuresHazardReader.swift): every fail-closed arm opened, a
    field read by value, the reader unwired from PlanResponse.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

COPY = ROOT / "Sources" / "ScenicKit" / "Hazards" / "HazardCopy.swift"
READER = ROOT / "Sources" / "ScenicAPIClient" / "ClosuresHazardReader.swift"
PLAN_RESPONSE = ROOT / "Sources" / "ScenicAPIClient" / "PlanResponse.swift"
SUBJECTS = (COPY, READER)
MUTATED_FILES = (COPY, READER, PLAN_RESPONSE)

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "Hazards" / "HazardCopyTests.swift",
              ROOT / "Tests" / "ScenicAPIClientTests" / "ClosuresHazardTests.swift")

ROW = "every Worker hazard row reads its ruled line, whole"
UNKNOWN = "an unlisted value or kind reads a safe line, never the raw key"
FLAG = "every hazard flag reads its ruled line, whole"
STRIP = "the strip keeps one line per hazard, in order"
WIRE = "no copy line is empty, and none spells a wire key"
CLOSE = "every closure condition reads its ruled lines, whole, on every route card"
SHAPE = "every Worker closures_hazard reads its ruled lines on the plan, trip and loop cards"
UNREAD = "an unreadable closures_hazard reads the safest line on every card, never silence and never a refusal"

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
    # T-0341: the closure lines (R2) and the reader (R3).
    ("24 the crossing line softened", COPY, "expect the road to be blocked and check before you drive",
     "it may still be open", [CLOSE, SHAPE, UNREAD]),
    ("25 a crossing reads nothing", COPY, "closures.crosses ? [closureCrosses] : []", "[]", [CLOSE, SHAPE, UNREAD]),
    ("26 a stale set reads nothing", COPY, "case .stale: lines.append(closuresStale)", "case .stale: break",
     [CLOSE, SHAPE, UNREAD]),
    ("27 an unavailable set reads stale", COPY, "case .unavailable: lines.append(closuresUnavailable)",
     "case .unavailable: lines.append(closuresStale)", [CLOSE, SHAPE, UNREAD]),
    ("28 a dropped closure reads nothing", COPY, "if closures.dropped { lines.append(closuresDropped) }", "",
     [CLOSE, SHAPE, UNREAD]),
    ("29 the dropped line first", COPY, "lines.append(closuresDropped)", "lines.insert(closuresDropped, at: 0)",
     [CLOSE, SHAPE, UNREAD]),
    ("30 the plan strip drops the closure lines", COPY, "closureLines(for: preview.closures) + preview.hazards",
     "preview.hazards", [CLOSE, SHAPE, UNREAD]),
    ("31 the plan strip puts the closure lines last", COPY,
     "closureLines(for: preview.closures) + preview.hazards.map { line(for: $0) }",
     "preview.hazards.map { line(for: $0) } + closureLines(for: preview.closures)", [CLOSE, SHAPE, UNREAD]),
    ("32 the itinerary card silent", COPY, "closureLines(for: itinerary.closures)", "[]", [CLOSE, SHAPE, UNREAD]),
    ("33 the loop card silent", COPY, "        closureLines(for: preview.closures)\n", "        []\n",
     [CLOSE, SHAPE, UNREAD]),
    ("34 an absent key reads unavailable", READER, "guard top.contains(key) else { return .clear }",
     "guard top.contains(key) else { return ClosuresHazard(state: .unavailable) }", [SHAPE]),
    ("35 a key that is not an object reads clear", READER, "return ClosuresHazard(state: .unavailable)\n",
     "return .clear\n", [UNREAD]),
    ("36 an unknown state reads fresh", READER, "default: return .unavailable", "default: return .fresh", [UNREAD]),
    ("37 the state matched loosely", READER, "switch try? box.decode(String.self, forKey: .state) {",
     "switch (try? box.decode(String.self, forKey: .state))?.lowercased().trimmingCharacters(in: .whitespaces) {",
     [UNREAD]),
    ("38 a stale set reads fresh", READER, 'case .some("stale"): return .stale', 'case .some("stale"): return .fresh',
     [SHAPE, UNREAD]),
    ("39 the version unchecked", READER, "guard (try? box.decode(String.self, forKey: .version)) != nil,\n              ",
     "guard ", [UNREAD]),
    ("40 the fetched_at unchecked", READER,
     ",\n              (try? box.decode(String.self, forKey: .fetchedAt)) != nil else", " else", [UNREAD]),
    ("41 a null fetched_at accepted", READER, "(try? box.decode(String.self, forKey: .fetchedAt)) != nil",
     "((try? box.decode(String.self, forKey: .fetchedAt)) != nil || (try? box.decodeNil(forKey: .fetchedAt)) == true)",
     [UNREAD]),
    ("42 dropped read by its value", READER, "dropped: box.contains(.dropped)",
     "dropped: ((try? box.decode(Int.self, forKey: .dropped)) ?? 0) > 0", [UNREAD]),
    ("43 crosses read by its value", READER, "crosses: box.contains(.crosses)",
     "crosses: !((try? box.decode([String].self, forKey: .crosses)) ?? []).isEmpty", [UNREAD]),
    ("44 the reader never wired into the plan", PLAN_RESPONSE,
     "closuresHazard: ClosuresHazardReader.read(top, forKey: .closuresHazard)", "closuresHazard: .clear",
     [SHAPE, UNREAD]),
]

# Cannot change behaviour, so anything but MISSED fails the run. (name, path, old, new, witness)
EQUIVALENT = [
    ("E1 the two kind fallbacks swapped in order", COPY,
     'case "surface": return surfaceFallback\n        case "road_access": return accessFallback',
     'case "road_access": return accessFallback\n        case "surface": return surfaceFallback',
     "the switch cases match distinct string literals, so at most one matches any kind and their order is moot"),
]

MIN_MUTATIONS = 44
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 2
