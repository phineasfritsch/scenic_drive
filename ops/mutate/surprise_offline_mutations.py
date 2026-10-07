"""T-0273's entries in the Surprise population (95-123): the offline reach and the corpus-place mapping the Surprise
card feeds Surprise.pick with - SurpriseOfflineReach, SurprisePlaceMapping and SurprisePlaceClass. Appended to
surprise_mutations.MUTATIONS (that file sits near CLAUDE.md's 300-line cap); same `(name, path, old, new, killers)`
shape, killers are Swift Testing display names and every one must go red. Data only: no `__main__`.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_DIR = ROOT / "Sources" / "ScenicKit" / "Surprise"
OFFLINE = _DIR / "SurpriseOfflineReach.swift"
MAPPING = _DIR / "SurprisePlaceMapping.swift"
PLACE_CLASS = _DIR / "SurprisePlaceClass.swift"
SUBJECTS = (OFFLINE, MAPPING, PLACE_CLASS)

_TESTS = ROOT / "Tests" / "ScenicKitTests" / "Surprise"
TEST_FILES = (_TESTS / "SurpriseOfflineReachTests.swift", _TESTS / "SurprisePlaceMappingTests.swift")
SUITES = "SurpriseOfflineReachTests|SurprisePlaceMappingTests"

CONST = "the ruled constants: road factor 1.4, 750 m a minute, a 120-minute budget, from Westwood"
BOUNDS = "round-trip minutes at every bound: 0 m, the last double at 1, 60 and 120 minutes and the next one"
REACH = "the reach over three committed LA places and the origin itself, by full equality"
ORIGIN = "the reach is measured from the origin handed in, not from Westwood"
BUDGET = "the budget handed in is the budget handed out, and no candidate is dropped by the reach itself"
CLASSES = "every corpus class maps to its ruled candidate, field for field (R3)"
LABELS = "the ten classes are the corpus's ten, in the ruled order, with the ruled labels"
NONE = "an unnamed row, an empty name and a class outside the ten give no candidate"
CELL = "the corridor is the truncated 0.1 degree cell, on both sides of each edge"

MUTATIONS = [
    ("95 the road factor lowered", OFFLINE, "public static let roadFactor = 1.4", "public static let roadFactor = 1.3",
     [CONST, BOUNDS, REACH]),
    ("96 the average speed changed", OFFLINE, "public static let averageMetersPerMinute = 750.0",
     "public static let averageMetersPerMinute = 700.0", [CONST, BOUNDS, REACH]),
    ("97 the budget raised", OFFLINE, "public static let budgetMinutes = 120", "public static let budgetMinutes = 150",
     [CONST]),
    ("98 the round trip rounded to nearest", OFFLINE, ".rounded(.up))", ".rounded())", [BOUNDS]),
    ("99 the round trip rounded down", OFFLINE, ".rounded(.up))", ".rounded(.down))", [BOUNDS, REACH]),
    ("100 one way, not there and back", OFFLINE, "Int((2 * meters * roadFactor", "Int((meters * roadFactor",
     [BOUNDS, REACH]),
    ("101 the reach reports the ruled budget, not the one handed in", OFFLINE,
     "return SurpriseReach(budgetMinutes: budgetMinutes,", "return SurpriseReach(budgetMinutes: Self.budgetMinutes,",
     [BUDGET]),
    ("102 the origin moved", OFFLINE, "Coordinate(latitude: 34.0689, longitude: -118.4452)",
     "Coordinate(latitude: 34.0690, longitude: -118.4452)", [CONST]),
    ("103 the origin renamed", OFFLINE, 'public static let originName = "Westwood"',
     'public static let originName = "Santa Monica"', [CONST]),
    ("104 the reach measured from Westwood, not the origin handed in", OFFLINE,
     "Geo.distanceMeters(origin, candidate.coordinate)", "Geo.distanceMeters(Self.origin, candidate.coordinate)",
     [ORIGIN]),
    ("105 the reach drops the last candidate", OFFLINE, "for candidate in candidates {",
     "for candidate in candidates.dropLast() {", [REACH, BUDGET]),
    ("106 every place's quality flat 50 again (T-0273, before the class prior)", MAPPING,
     "quality: placeClass.priorQuality,", "quality: 50,", [CLASSES]),
    ("107 an approach score invented", MAPPING, "public static let approachScore = 0",
     "public static let approachScore = 1", [CLASSES, CELL]),
    ("108 the corridor cell a whole degree", MAPPING, "public static let corridorCellE7: Int64 = 1_000_000",
     "public static let corridorCellE7: Int64 = 10_000_000", [CLASSES, CELL]),
    ("109 an empty name kept", MAPPING, "guard let name, !name.isEmpty, let placeClass",
     "guard let name, let placeClass", [NONE]),
    ("110 latitude and longitude swapped", MAPPING,
     "Coordinate(latitude: Double(latE7) / 10_000_000, longitude: Double(lonE7) / 10_000_000)",
     "Coordinate(latitude: Double(lonE7) / 10_000_000, longitude: Double(latE7) / 10_000_000)", [CLASSES, CELL]),
    ("111 every place hours-exempt", MAPPING, "hoursExempt: hours == nil,", "hoursExempt: true,", [CLASSES]),
    ("112 every place lit", MAPPING, "lit: false,", "lit: true,", [CLASSES, CELL]),
    ("113 every place unpaved", MAPPING, "unpaved: false,", "unpaved: true,", [CLASSES, CELL]),
    ("114 every approach private", MAPPING, "privateApproach: false\n", "privateApproach: true\n", [CLASSES, CELL]),
    ("115 the name read as a brand", MAPPING, "brand: nil,", "brand: name,", [CLASSES, CELL]),
    ("116 the id spelled differently", MAPPING, "id: String(placeID),", 'id: "p\\(placeID)",', [CLASSES, CELL]),
    ("117 the opening minute read from the closing one", MAPPING, "opensMinute: hours?.opens,",
     "opensMinute: hours?.closes,", [CLASSES]),
    ("118 waterfalls and trailheads filed as parks", PLACE_CLASS, "case .waterfall, .trailhead: return .trailhead",
     "case .waterfall, .trailhead: return .park", [CLASSES]),
    ("119 the museum opens an hour early", PLACE_CLASS, "case .museum: return (600, 1020)",
     "case .museum: return (540, 1020)", [CLASSES]),
    ("120 a cafe stop as long as a park", PLACE_CLASS, "case .cafe: return 30", "case .cafe: return 45", [CLASSES]),
    ("121 a hook reworded", PLACE_CLASS, 'return "A slow cup somewhere new."', 'return "A slow cup somewhere."',
     [CLASSES]),
    ("122 a label respelled", PLACE_CLASS, 'case .cafe: return "Cafe"', 'case .cafe: return "Coffee"', [LABELS]),
    ("123 a viewpoint stop lengthened", PLACE_CLASS, "case .viewpoint: return 20", "case .viewpoint: return 30",
     [CLASSES]),
]
