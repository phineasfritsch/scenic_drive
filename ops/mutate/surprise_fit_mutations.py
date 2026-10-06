"""T-0283's entries in the Surprise population (124-140): the time-fit that peaks inside the dial (Surprise.timeFit,
R1) and the class prior a mapped place carries as its quality (SurprisePlaceClass.priorQuality, R2). Appended to
surprise_mutations.MUTATIONS like surprise_offline_mutations; same `(name, path, old, new, killers)` shape, killers
are Swift Testing display names and every one must go red. Data only: no `__main__`.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_DIR = ROOT / "Sources" / "ScenicKit" / "Surprise"
SURPRISE = _DIR / "Surprise.swift"
MAPPING = _DIR / "SurprisePlaceMapping.swift"
PLACE_CLASS = _DIR / "SurprisePlaceClass.swift"

TEST_FILES = (ROOT / "Tests" / "ScenicKitTests" / "Surprise" / "SurpriseCorpusFitTests.swift",)

PERM = "the whole pick permutation equals the oracle's: driver-a, driver-c and driver-b with history"
CLASSES = "every corpus class maps to its ruled candidate, field for field (R3)"
CELL = "the corridor is the truncated 0.1 degree cell, on both sides of each edge"
CORPUS = "the card's picks for seeds 0..99 at dials 30, 60, 90 and 120 equal the oracle's, by full equality"
INSIDE = "at a 120-min dial the picks for seeds 0..99 land inside the dial, not at its edge, and mostly scenery"

PEAK = "public static let timeFitPeakPercent = 70"
SLOPE = "public static let timeFitSlope = 2"
FIT = "max(0, 100 - timeFitSlope * abs(minutes * 100 / max(budget, 1) - timeFitPeakPercent))"
SCENIC = "case .viewpoint, .peak, .waterfall, .beach, .trailhead, .garden: return 75"
MIDDLE = "case .park, .museum, .town: return 50"
CAFE = "case .cafe: return 25"
READ = "quality: placeClass.priorQuality,"

MUTATIONS = [
    ("124 the time-fit peak moved down to 65%", SURPRISE, PEAK, PEAK.replace("70", "65"), [PERM, CORPUS]),
    ("125 the time-fit peak moved up to 75%", SURPRISE, PEAK, PEAK.replace("70", "75"), [PERM, CORPUS]),
    ("126 the time-fit slope steeper", SURPRISE, SLOPE, SLOPE.replace("2", "3"), [PERM, CORPUS]),
    ("127 the time-fit slope shallower", SURPRISE, SLOPE, SLOPE.replace("2", "1"), [PERM, CORPUS]),
    ("128 the time-fit clamp at 0 dropped", SURPRISE, FIT, FIT[len("max(0, "):-1], [CORPUS]),
    ("129 the time-fit distance signed, not absolute", SURPRISE, FIT,
     FIT.replace("abs(minutes * 100 / max(budget, 1) - timeFitPeakPercent)",
                 "(minutes * 100 / max(budget, 1) - timeFitPeakPercent)"), [PERM, CORPUS, INSIDE]),
    ("130 T-0253's linear time-fit restored", SURPRISE, FIT, "minutes * 100 / max(budget, 1)",
     [PERM, CORPUS, INSIDE]),
    ("131 the dial percentage rounded to nearest", SURPRISE, FIT,
     FIT.replace("minutes * 100 / max(budget, 1)", "(minutes * 100 + max(budget, 1) / 2) / max(budget, 1)"),
     [PERM, CORPUS]),
    ("132 the scenic tier lowered", PLACE_CLASS, SCENIC, SCENIC.replace("75", "70"), [CLASSES, CORPUS]),
    ("133 the middle tier raised", PLACE_CLASS, MIDDLE, MIDDLE.replace("50", "55"), [CLASSES, CELL, CORPUS]),
    ("134 the cafe tier raised", PLACE_CLASS, CAFE, CAFE.replace("25", "30"), [CLASSES, CORPUS]),
    ("135 gardens demoted to the middle tier", PLACE_CLASS, SCENIC, SCENIC.replace(", .garden", ""),
     [CLASSES, CORPUS]),
    ("136 peaks demoted to the middle tier", PLACE_CLASS, SCENIC, SCENIC.replace(", .peak", ""), [CLASSES, CORPUS]),
    ("137 cafes promoted to the scenic tier", PLACE_CLASS, SCENIC, SCENIC.replace(".garden:", ".garden, .cafe:"),
     [CLASSES, CORPUS]),
    ("138 the mapping reads a flat scenic quality", MAPPING, READ, "quality: 75,", [CLASSES, CORPUS]),
    ("139 the mapping reads a flat cafe quality", MAPPING, READ, "quality: 25,", [CLASSES, CORPUS, INSIDE]),
    ("140 the prior tiers inverted: cafe 75, scenery 25", PLACE_CLASS, SCENIC, SCENIC.replace("75", "25"),
     [CLASSES, CORPUS, INSIDE]),
]
