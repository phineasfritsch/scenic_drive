"""The mutation population for T-0253's Surprise selector: Sources/ScenicKit/Surprise/Surprise.swift and its eight
value types. The driver is surprise.py and the runner surprise_run.py (menu's three-file shape).

## What the acceptance names, and where each lives

  * the EIGHT HARD FILTERS, each dropped and each boundary moved - entries 1-22 (R3);
  * the four NOT-THIS reasons - 23-28 (R6);
  * the RANKING - each of the four terms dropped, the novelty cap, the order (29-34) (R4);
  * the SEED and the 20% EXPLORATION, P-PROD-02 - 35-42 (R5);
  * the WHY - the golden-hour window, its clock (43-45) (R7);
  * the eight value types' fields (46-55): the tests render a pick's PROPERTIES, so a swapped field is seen.
  * the pre-review survivors (58-60): the not-my-thing window from below, civil dusk read as sunset, and a
    too-far cut kept past its day - each boundary now pinned from both sides.
  * rv1's survivor (61): a red flag closing a SPARED category; filter 7 now compares the whole red-flag
    permutation to the oracle's scenario R, and the red-flag set to the calm set minus the three fire categories.
  * T-0263's port of the /isochrone reach (62-78): SurpriseIsochrone and its two value types - the even-odd
    crossing, its IEEE expression order, holes, the smallest bucket, the decode shape, and the reach pick takes.
  * the T-0263 pre-review survivors (79-81): the first containing bucket trusted to be the smallest (killed by
    every bucket order), the shape checked on bucket one only (a defect in each bucket), and the budget read from
    the largest bucket (a dial that is not the last bucket's round trip).
  * rv1's B1 and its class (82-94): every scope a decode check can narrow to - buckets, rings (outer vs hole),
    positions (first, middle, last) - and the ring-size rule R4 now carries (a ring, four positions each); one
    table through decode, a defect at every structural position, each refused as malformedResponse by name.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names, every one of which must go red.
"""
from __future__ import annotations

import pathlib

import surprise_fit_mutations
import surprise_offline_mutations

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "ScenicKit" / "Surprise"
SURPRISE = _DIR / "Surprise.swift"
CANDIDATE = _DIR / "SurpriseCandidate.swift"
CATEGORY = _DIR / "SurpriseCategory.swift"
REACH = _DIR / "SurpriseReach.swift"
HISTORY = _DIR / "SurpriseHistory.swift"
FEEDBACK = _DIR / "SurpriseFeedback.swift"
CONTEXT = _DIR / "SurpriseContext.swift"
REASON = _DIR / "SurpriseReason.swift"
PICK = _DIR / "SurprisePick.swift"
ISOCHRONE = _DIR / "SurpriseIsochrone.swift"
BUCKET = _DIR / "SurpriseIsochroneBucket.swift"
POLYGON = _DIR / "SurpriseIsochronePolygon.swift"
SUBJECTS = (SURPRISE, CANDIDATE, CATEGORY, REACH, HISTORY, FEEDBACK, CONTEXT, REASON, PICK, ISOCHRONE, BUCKET,
            POLYGON) + surprise_offline_mutations.SUBJECTS
MUTATED_FILES = SUBJECTS

_TESTS = ROOT / "Tests" / "ScenicKitTests" / "Surprise"
TEST_FILES = (_TESTS / "SurpriseFilterTests.swift", _TESTS / "SurpriseRankTests.swift",
              _TESTS / "SurpriseFeedbackTests.swift", _TESTS / "SurpriseReachParityTests.swift",
              _TESTS / "SurpriseIsochroneTests.swift") + surprise_offline_mutations.TEST_FILES + \
    surprise_fit_mutations.TEST_FILES

F1 = "filter 1: a place whose round trip exceeds the budget, or lies outside the reach, is never picked"
F2 = "filter 2: a place shown within 90 days is never picked; 90 days ago it may return"
F3 = "filter 3: the same category on the same corridor within 30 days is never picked"
F4 = "filter 4: a blocklisted brand or chain is never picked; an unlisted local brand is"
F5 = "filter 5: a place not open from arrival to arrival + dwell + 45 min is never picked unless exempt"
F6 = "filter 6: an unlit unpaved viewpoint arriving after civil twilight is never picked"
F7 = "filter 7: a red-flag day drops exactly park, trailhead and viewpoint - the oracle's red-flag permutation"
F8 = "filter 8: an approach crossing private access is never picked"
TOO_FAR = "not this - too far: the next pick is griffith-02 and no pick that day is 132 min or longer"
NOT_MINE = "not this - not my thing: the next pick is griffith-02 and no park for 30 days"
BEEN = "not this - been there: the next pick is griffith-02 and sgc-05 never returns, even a year on"
WRONG = "not this - wrong time: the next pick is griffith-02 today, and sgc-05 is back tomorrow"
DISTINCT = "P-PROD-02: >= 90 of 100 consecutive seeds give distinct picks over the 127 eligible"
PERM = "the whole pick permutation equals the oracle's: driver-a, driver-c and driver-b with history"
WHY = "the WHY: three picks pinned whole - hook, round trip and the golden-hour line from Solar"
NOTHING = "nothing reachable is nil: a 20 min budget, or no candidates; a 30 min budget reaches one"
PARITY = "every shared point gets the TS reference's recorded round-trip minutes from the decoded body"
OUTSIDE = ("a candidate outside every isochrone bucket is never picked: the ten ojai places, which T-0253's "
           "reach picks")
INTO_WHY = ("the decoded reach is the dial and each smallest bucket's round trip, and those minutes reach "
            "SurpriseReason")
SHAPE = "a body that is not T-0262's shape does not decode: a MultiPolygon, a one-number position, no round trip"
ORDERS = "every bucket order gives the recorded reach: the parity body's three buckets in all six orders"
ANY_BUCKET = ("a defect in any bucket does not decode: a MultiPolygon, a one-number position, no round trip, in each "
              "of the parity body's three buckets")
TABLE = ("every structural defect is refused as malformedResponse: each bucket, each outer and hole ring, its "
         "first, middle and last position")
DIAL = ("the reach's budget is the body's dial, not its largest bucket: dials 45, 100 and 240 over buckets ending "
        "at 90")
CROSSING = "(xj - xi) * (point.latitude - yi) / (yj - yi) + xi"

SHOWN = "$0.candidateId == c.id && days(date, since: $0.date) < shownDays"
CORRIDOR = "$0.category == c.category && $0.corridor == c.corridor"
OPEN = "return opens <= arrival && arrival + c.dwellMinutes + closingMarginMinutes <= closes"
DARK = "if c.category == .viewpoint && !c.lit && c.unpaved && isAfterDusk(c, arrival: arrival, context: context) {"
SCORE = "return c.quality + c.approachScore + novelty + timeFit(minutes: minutes, budget: budget)"
EXPLORE = "let index = h % 100 < explorePercent ? Int((h >> 32) % UInt64(remaining.count)) : 0"
ORDER = "remaining.sort { a, b in a.score != b.score ? a.score > b.score : a.candidate.id < b.candidate.id }"
WRONG_CASE = "case .wrongTime where f.candidateId == c.id && days(date, since: f.date) == 0: return false"
KEY = '"\\(userId)|\\(pad(date.year, 4))-\\(pad(date.month, 2))-\\(pad(date.day, 2))|\\(step)"'

MUTATIONS = [
    ("1 the reach filter dropped", SURPRISE, "guard minutes <= budget else { return nil }", "", [F1]),
    ("2 the reach made strict", SURPRISE, "guard minutes <= budget else", "guard minutes < budget else", [F1]),
    ("3 the 90-day filter dropped", SURPRISE, SHOWN, SHOWN.replace("days(date, since: $0.date) < shownDays", "false"),
     [F2]),
    ("4 90 days -> 91", SURPRISE, "public static let shownDays = 90", "public static let shownDays = 91", [F2]),
    ("5 90 days -> 89", SURPRISE, "public static let shownDays = 90", "public static let shownDays = 89", [F2]),
    ("6 the category x corridor filter dropped", SURPRISE, CORRIDOR, "false && " + CORRIDOR, [F3]),
    ("7 the corridor ignored", SURPRISE, CORRIDOR, "$0.category == c.category", [PERM]),
    ("8 30 days -> 31", SURPRISE, "public static let categoryCorridorDays = 30",
     "public static let categoryCorridorDays = 31", [F3]),
    ("9 the brand filter dropped", SURPRISE, "if let brand = c.brand, blockedBrands.contains(brand) { return false }",
     "", [F4]),
    ("10 Starbucks off the blocklist", SURPRISE, '["Starbucks", ', "[", [F4]),
    ("11 the hours filter dropped", SURPRISE, "if !c.hoursExempt && !isOpen(c, arrival: arrival) { return false }",
     "", [F5]),
    ("12 no category is hours-exempt", SURPRISE, "if !c.hoursExempt && !isOpen(", "if !isOpen(", [PERM]),
    ("13 the closing margin 45 -> 46", SURPRISE, "public static let closingMarginMinutes = 45",
     "public static let closingMarginMinutes = 46", [F5]),
    ("14 closing made strict", SURPRISE, OPEN, OPEN.replace("<= closes", "< closes"), [F5]),
    ("15 opening made strict", SURPRISE, OPEN, OPEN.replace("opens <= arrival", "opens < arrival"), [F5]),
    ("16 unknown hours count as open", SURPRISE,
     "guard let opens = c.opensMinute, let closes = c.closesMinute else { return false }",
     "guard let opens = c.opensMinute, let closes = c.closesMinute else { return true }", [F5]),
    ("17 the dark-viewpoint filter dropped", SURPRISE, DARK, DARK.replace("if c.category", "if false && c.category"),
     [F6]),
    ("18 lit viewpoints dropped too", SURPRISE, DARK, DARK.replace("!c.lit && ", ""), [F6]),
    ("19 paved viewpoints dropped too", SURPRISE, DARK, DARK.replace("c.unpaved && ", ""), [F6]),
    ("20 dusk read at departure, not arrival", SURPRISE, DARK,
     DARK.replace("isAfterDusk(c, arrival: arrival,", "isAfterDusk(c, arrival: context.departureMinute,"), [F6]),
    ("21 the red-flag filter dropped", SURPRISE, "if context.redFlag && c.category.closesOnRedFlag { return false }",
     "", [F7]),
    ("22 the private-approach filter dropped", SURPRISE, "if c.privateApproach { return false }", "", [F8]),
    ("23 been there forgotten", SURPRISE, "case .beenThere where f.candidateId == c.id: return false",
     "case .beenThere where false: return false", [BEEN]),
    ("24 not my thing forgotten", SURPRISE, "case .notMyThing where f.category == c.category",
     "case .notMyThing where false && f.category == c.category", [NOT_MINE]),
    ("25 not my thing 30 days -> 31", SURPRISE, "public static let notMyThingDays = 30",
     "public static let notMyThingDays = 31", [NOT_MINE]),
    ("26 wrong time kept forever", SURPRISE, WRONG_CASE, WRONG_CASE.replace("== 0", ">= 0"), [WRONG]),
    ("27 too far forgotten", SURPRISE, "budget = min(budget, f.roundTripMinutes - 1)", "budget = min(budget, budget)",
     [TOO_FAR]),
    ("28 too far keeps its own round trip", SURPRISE, "budget = min(budget, f.roundTripMinutes - 1)",
     "budget = min(budget, f.roundTripMinutes)", [TOO_FAR]),
    ("29 quality dropped", SURPRISE, SCORE, SCORE.replace("c.quality + ", ""), [PERM]),
    ("30 approach-road score dropped", SURPRISE, SCORE, SCORE.replace("c.approachScore + ", ""), [PERM]),
    ("31 novelty dropped", SURPRISE, SCORE, SCORE.replace("+ novelty ", ""), [PERM]),
    ("32 time-fit dropped", SURPRISE, SCORE, SCORE.replace(" + timeFit(minutes: minutes, budget: budget)", ""), [PERM]),
    ("33 novelty uncapped", SURPRISE, "since.min().map { min(100, max(0, $0)) } ?? 100",
     "since.min().map { max(0, $0) } ?? 100", [PERM]),
    ("34 lowest score first", SURPRISE, ORDER, ORDER.replace("a.score > b.score", "a.score < b.score"), [PERM]),
    ("35 exploration 20% -> 21%", SURPRISE, "public static let explorePercent: UInt64 = 20",
     "public static let explorePercent: UInt64 = 21", [PERM]),
    ("36 exploration 20% -> 19%", SURPRISE, "public static let explorePercent: UInt64 = 20",
     "public static let explorePercent: UInt64 = 19", [PERM]),
    ("37 exploration reads the low bits", SURPRISE, EXPLORE, EXPLORE.replace("(h >> 32)", "h"), [PERM]),
    ("38 exploitation takes the worst", SURPRISE, EXPLORE, EXPLORE.replace(": 0", ": remaining.count - 1"), [PERM]),
    ("39 a taken place stays in the list", SURPRISE, "taken = remaining.remove(at: index)",
     "taken = remaining[index]", [DISTINCT]),
    ("40 the seed ignored", SURPRISE, "let target = Int(seed % UInt64(remaining.count))", "let target = 0",
     [DISTINCT]),
    ("41 the user ignored by the draw", SURPRISE, KEY, KEY.replace("\\(userId)|", "|"), [PERM]),
    ("42 the hash finaliser dropped", SURPRISE, "h = (h ^ (h >> 30)) &* 0xbf58_476d_1ce4_e5b9", "", [PERM]),
    ("43 no golden hour ever", SURPRISE, "guard sunset >= start && sunset <= end else { return nil }",
     "return nil", [WHY]),
    ("44 the visit has no dwell", SURPRISE, "let end = instant(arrival + c.dwellMinutes, context: context)",
     "let end = instant(arrival, context: context)", [WHY]),
    ("45 the sunset clock offset backwards", SURPRISE, "((utcMinutes + context.utcOffsetMinutes) % 1440",
     "((utcMinutes - context.utcOffsetMinutes) % 1440", [WHY]),
    ("46 arrival is the whole round trip", SURPRISE, "context.departureMinute + roundTrip / 2",
     "context.departureMinute + roundTrip", [F5]),
    ("47 a red flag spares viewpoints", CATEGORY, "case .park, .trailhead, .viewpoint: return true",
     "case .park, .trailhead: return true\n        case .viewpoint: return false", [F7]),
    ("48 candidate lit always false", CANDIDATE, "self.lit = lit", "self.lit = false", [F6]),
    ("49 candidate quality reads approach", CANDIDATE, "self.quality = quality", "self.quality = approachScore",
     [PERM]),
    ("50 reach budget fixed at 180", REACH, "self.budgetMinutes = budgetMinutes", "self.budgetMinutes = 180",
     [NOTHING]),
    ("51 shown corridor blanked", HISTORY, "self.corridor = corridor", "self.corridor = \"\"", [F3]),
    ("52 history shown dropped", HISTORY, "self.shown = shown", "self.shown = []", [F2]),
    ("53 feedback reason read as been there", FEEDBACK, "self.reason = reason", "self.reason = .beenThere",
     [TOO_FAR]),
    ("54 context red flag always false", CONTEXT, "self.redFlag = redFlag", "self.redFlag = false", [F7]),
    ("55 context utc offset zero", CONTEXT, "self.utcOffsetMinutes = utcOffsetMinutes", "self.utcOffsetMinutes = 0",
     [F6]),
    ("56 reason round trip zero", REASON, "self.roundTripMinutes = roundTripMinutes", "self.roundTripMinutes = 0",
     [WHY]),
    ("57 pick name reads its id", PICK, "self.name = name", "self.name = candidateId", [WHY]),
    ("58 not my thing 30 days -> 29", SURPRISE, "public static let notMyThingDays = 30",
     "public static let notMyThingDays = 29", [NOT_MINE]),
    ("59 dusk read from sunset", SURPRISE, "SolarEvents.compute(on: context.date, at: c.coordinate).civilDusk",
     "SolarEvents.compute(on: context.date, at: c.coordinate).sunset", [F6]),
    ("60 too far kept forever", SURPRISE, "f.reason == .tooFar && days(date, since: f.date) == 0",
     "f.reason == .tooFar && days(date, since: f.date) >= 0", [TOO_FAR]),
    ("61 a red flag closes beaches too", CATEGORY, "case .park, .trailhead, .viewpoint: return true\n        case .beach,",
     "case .park, .trailhead, .viewpoint, .beach: return true\n        case", [F7]),
    ("62 a crossing counts a vertex at the point's latitude", ISOCHRONE,
     "if (yi > point.latitude) != (yj > point.latitude)", "if (yi >= point.latitude) != (yj >= point.latitude)",
     [PARITY]),
    ("63 a point on the crossing counts it", ISOCHRONE, "&& point.longitude < (xj - xi)",
     "&& point.longitude <= (xj - xi)", [PARITY]),
    ("64 the crossing's run reversed", ISOCHRONE, CROSSING, "(xi - xj) * (point.latitude - yi) / (yj - yi) + xi",
     [PARITY]),
    ("65 the crossing in the other IEEE order", ISOCHRONE, CROSSING,
     "(xj - xi) * ((point.latitude - yi) / (yj - yi)) + xi", [PARITY]),
    ("66 holes ignored", ISOCHRONE, "!rings.dropFirst().contains(where:",
     "!rings.dropFirst(rings.count).contains(where:", [PARITY]),
    ("67 the last ring read as the outer", ISOCHRONE, "guard let outer = rings.first,", "guard let outer = rings.last,",
     [PARITY]),
    ("68 the largest bucket wins", ISOCHRONE, "bucket.roundTripMinutes < $0", "bucket.roundTripMinutes > $0", [PARITY]),
    ("69 the one-way minutes charged", ISOCHRONE, "{ best = bucket.roundTripMinutes }", "{ best = bucket.minutes }",
     [PARITY]),
    ("70 every ring starts inside", ISOCHRONE, "var inside = false", "var inside = true", [PARITY]),
    ("71 every edge drawn from the last vertex", ISOCHRONE, "            j = i\n", "            j = ring.count - 1\n",
     [PARITY]),
    ("72 the budget halved to the one-way dial", ISOCHRONE,
     "SurpriseReach(budgetMinutes: minutes, roundTripMinutes: roundTrips)",
     "SurpriseReach(budgetMinutes: minutes / 2, roundTripMinutes: roundTrips)", [INTO_WHY]),
    ("73 a place outside the reach charged the dial", ISOCHRONE,
     "if let minutes = roundTripMinutes(at: candidate.coordinate) { roundTrips[candidate.id] = minutes }",
     "roundTrips[candidate.id] = roundTripMinutes(at: candidate.coordinate) ?? self.minutes", [OUTSIDE, INTO_WHY]),
    ("74 any polygon type accepted", ISOCHRONE, 'guard bucket.polygon.type == "Polygon" else',
     "guard !bucket.polygon.type.isEmpty else", [SHAPE]),
    ("75 a one-number position accepted", ISOCHRONE, "$0.count >= 2", "$0.count >= 1", [SHAPE]),
    ("76 snake_case keys not converted", ISOCHRONE, ".convertFromSnakeCase", ".useDefaultKeys", [PARITY, SHAPE]),
    ("77 bucket round trip read as one way", BUCKET, "self.roundTripMinutes = roundTripMinutes",
     "self.roundTripMinutes = minutes", [SHAPE]),
    ("78 polygon rings dropped", POLYGON, "self.coordinates = coordinates", "self.coordinates = []", [SHAPE]),
    ("79 the first containing bucket wins", ISOCHRONE,
     "if best.map({ bucket.roundTripMinutes < $0 }) ?? true { best = bucket.roundTripMinutes }",
     "if best == nil { best = bucket.roundTripMinutes }", [ORDERS]),
    ("80 the shape checked on the first bucket only", ISOCHRONE, "for bucket in reach.buckets {",
     "for bucket in reach.buckets.prefix(1) {", [ANY_BUCKET]),
    ("81 the budget read from the largest bucket", ISOCHRONE,
     "SurpriseReach(budgetMinutes: minutes, roundTripMinutes: roundTrips)",
     "SurpriseReach(budgetMinutes: buckets.last?.roundTripMinutes ?? minutes, roundTripMinutes: roundTrips)", [DIAL]),
    ("82 rv1 B1: positions checked on the outer ring only", ISOCHRONE,
     "guard bucket.polygon.coordinates.allSatisfy(", "guard bucket.polygon.coordinates.prefix(1).allSatisfy(", [TABLE]),
    ("83 positions unchecked on the outer ring", ISOCHRONE, "guard bucket.polygon.coordinates.allSatisfy(",
     "guard bucket.polygon.coordinates.dropFirst().allSatisfy(", [TABLE]),
    ("84 positions unchecked on the last hole", ISOCHRONE, "guard bucket.polygon.coordinates.allSatisfy(",
     "guard bucket.polygon.coordinates.dropLast().allSatisfy(", [TABLE]),
    ("85 only each ring's first position checked", ISOCHRONE, "ring in ring.allSatisfy {",
     "ring in ring.prefix(1).allSatisfy {", [TABLE]),
    ("86 each ring's first position unchecked", ISOCHRONE, "ring in ring.allSatisfy {",
     "ring in ring.dropFirst().allSatisfy {", [TABLE]),
    ("87 each ring's last position unchecked", ISOCHRONE, "ring in ring.allSatisfy {",
     "ring in ring.dropLast().allSatisfy {", [TABLE]),
    ("88 ring size checked on the outer ring only", ISOCHRONE, "bucket.polygon.coordinates.allSatisfy({ $0.count >= 4 })",
     "bucket.polygon.coordinates.prefix(1).allSatisfy({ $0.count >= 4 })", [TABLE]),
    ("89 ring size unchecked on the outer ring", ISOCHRONE, "bucket.polygon.coordinates.allSatisfy({ $0.count >= 4 })",
     "bucket.polygon.coordinates.dropFirst().allSatisfy({ $0.count >= 4 })", [TABLE]),
    ("90 ring size unchecked on the last hole", ISOCHRONE, "bucket.polygon.coordinates.allSatisfy({ $0.count >= 4 })",
     "bucket.polygon.coordinates.dropLast().allSatisfy({ $0.count >= 4 })", [TABLE]),
    ("91 a three-position ring accepted", ISOCHRONE, "$0.count >= 4", "$0.count >= 3", [TABLE]),
    ("92 a polygon with no ring accepted", ISOCHRONE, "guard !bucket.polygon.coordinates.isEmpty,",
     "guard bucket.polygon.coordinates.count >= 0,", [TABLE]),
    ("93 the first bucket's shape unchecked", ISOCHRONE, "for bucket in reach.buckets {",
     "for bucket in reach.buckets.dropFirst() {", [TABLE, ANY_BUCKET]),
    ("94 the last bucket's shape unchecked", ISOCHRONE, "for bucket in reach.buckets {",
     "for bucket in reach.buckets.dropLast() {", [TABLE, ANY_BUCKET]),
]

# Cannot change behaviour, so each must report MISSED; anything else is a FAILURE. `(name, path, old, new, witness)`.
EQUIVALENT = [
    ("E1 the first taken place seeded from the end", SURPRISE, "var taken = remaining[0]",
     "var taken = remaining[remaining.count - 1]",
     "`for step in 0...target` runs at least once (target >= 0) and assigns `taken` on every pass, so the "
     "initial value is never read; the non-empty guard above keeps both subscripts in range"),
    ("E2 the empty guard spelled as a count", SURPRISE, "guard !remaining.isEmpty else { return nil }",
     "guard remaining.count > 0 else { return nil }",
     "Array.isEmpty is defined as count == 0, and count is never negative"),
]

# T-0273's 29 entries (95-123) live in surprise_offline_mutations.py.
MUTATIONS += surprise_offline_mutations.MUTATIONS
# T-0283's 17 entries (124-140) live in surprise_fit_mutations.py.
MUTATIONS += surprise_fit_mutations.MUTATIONS

MIN_MUTATIONS = 140
MIN_EQUIVALENT = 2
MIN_TEST_FILES = 7
