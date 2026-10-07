"""The mutation population for T-0290's saved drives: the five-decimal gate (Sources/PlaceStore/FiveDecimals.swift),
the two values whose public initialisers run it (SavedMidpoint.swift, SavedDrive.swift) and the re-resolve rule
(SavedDriveResolver.swift). The driver is saveddrive.py and the runner saveddrive_run.py (segmentgeometry's
three-file shape).

## What the acceptance names, and where each lives

  * the GATE - finite, range, decimals, the scale and the stored integer - entries 1-6 (R4);
  * the MIDPOINT - each bound, each field label, the field order and both degree accessors - 7-13 (R4, R4c);
  * the DRIVE - lambda's two bounds and field label, its accessor, the stored flag, and a Double field added - 14-19
    (R3, R4a, R7);
  * the RE-RESOLVE rule - the 25 m radius from both sides, the presence check, the flag in both directions, nearest
    and the tie-break, the search box and its 1/cos(lat) widening, the corpus scale and the haversine terms -
    20-33 (R5).

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names in SavedDriveBoundsTests, SavedDriveResolverTests and
SavedDriveFieldsTests, every one of which must go red. EQUIVALENT entries are `(name, path, old, new, witness)` and
must all report MISSED.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "PlaceStore"
GATE = _DIR / "FiveDecimals.swift"
MIDPOINT = _DIR / "SavedMidpoint.swift"
DRIVE = _DIR / "SavedDrive.swift"
RESOLVER = _DIR / "SavedDriveResolver.swift"
SUBJECTS = (GATE, MIDPOINT, DRIVE, RESOLVER)
MUTATED_FILES = SUBJECTS

_TESTS = ROOT / "Tests" / "PlaceStoreTests"
TEST_FILES = (_TESTS / "SavedDriveBoundsTests.swift", _TESTS / "SavedDriveResolverTests.swift",
              _TESTS / "SavedDriveFieldsTests.swift")

LAT = "latitude: both exact bounds accepted, nextafter outward out of range, nextafter inward not 5 dp"
LON = "longitude: both exact bounds accepted, nextafter outward out of range, nextafter inward not 5 dp"
FIVE = "five decimals are stored as their e5 integers; a sixth is refused, never rounded"
ORDER = "check order: latitude before longitude; per field finite, then range, then decimals"
LAMBDA = "lambda: [0, 1000] exact bounds accepted, nextafter outward out of range, inward not 5 dp"
DEG = "the degree accessors return exactly the accepted Doubles"
TABLE = "every re-resolve row over both drives: the whole returned drive equals the row's expected drive"
FIELDS = "no field of a populated SavedDrive carries more than 5 dp: every leaf is Int, Int64, String or Bool"

DECIMALS = "guard scaled / scale == value else"
PRESENT = "if try corpus.segment(id: saved.segmentID) != nil {"
TIE = "meters > current.meters || (meters == current.meters && id > current.id)"
HAVERSINE = "+ cos(lat1 * radians) * cos(lat2 * radians) * sin(dLon / 2) * sin(dLon / 2)"

MUTATIONS = [
    ("1 finite check dropped", GATE, "guard value.isFinite else { throw SavedDriveError.notFinite(field) }", "",
     [LAT, LON, LAMBDA, ORDER]),
    ("2 range check skipped below 1e6", GATE, "guard range.contains(value) else",
     "guard range.contains(value) || value.magnitude < 1e6 else", [LAT, LON, LAMBDA]),
    ("3 decimals check dropped", GATE, DECIMALS, "guard true else", [LAT, LON, FIVE, LAMBDA]),
    ("4 decimals check inverted", GATE, DECIMALS, "guard scaled / scale != value else", [LAT, LON, FIVE, LAMBDA]),
    ("5 scale 1e5 -> 1e4", GATE, "static let scale: Double = 100_000", "static let scale: Double = 10_000",
     [LAT, LON, FIVE, LAMBDA]),
    ("6 stored integer off by one", GATE, "return Int(scaled)", "return Int(scaled) + 1", [LAT, LON, FIVE, LAMBDA]),
    ("7 latitude bound 90 -> 91", MIDPOINT, "static let maxLatitude: Double = 90",
     "static let maxLatitude: Double = 91", [LAT, ORDER]),
    ("8 latitude upper bound exclusive", MIDPOINT, "-Self.maxLatitude...Self.maxLatitude,",
     "-Self.maxLatitude...Self.maxLatitude.nextDown,", [LAT]),
    ("9 longitude bound 180 -> 179.99999", MIDPOINT, "static let maxLongitude: Double = 180",
     "static let maxLongitude: Double = 179.99999", [LON]),
    ("10 longitude refusals labelled latitude", MIDPOINT, "field: .longitude)", "field: .latitude)", [LON, FIVE]),
    ("11 latitude validated from the longitude", MIDPOINT, "latE5 = try FiveDecimals.fixedPoint(latitude,",
     "latE5 = try FiveDecimals.fixedPoint(longitude,", [LAT, LON]),
    ("12 latitude accessor reads lonE5", MIDPOINT, "public var latitude: Double { FiveDecimals.degrees(latE5) }",
     "public var latitude: Double { FiveDecimals.degrees(lonE5) }", [DEG, TABLE]),
    ("13 longitude accessor reads latE5", MIDPOINT, "public var longitude: Double { FiveDecimals.degrees(lonE5) }",
     "public var longitude: Double { FiveDecimals.degrees(latE5) }", [DEG, TABLE]),
    ("14 maxLambda 1000 -> 999.99999", DRIVE, "public static let maxLambda: Double = 1000",
     "public static let maxLambda: Double = 999.99999", [LAMBDA]),
    ("15 lambda lower bound exclusive", DRIVE, "in: 0...Self.maxLambda", "in: Double(0).nextUp...Self.maxLambda",
     [LAMBDA]),
    ("16 lambda refusals labelled latitude", DRIVE, "field: .lambda)", "field: .latitude)", [LAMBDA]),
    ("17 lambda accessor doubled", DRIVE, "public var lambda: Double { FiveDecimals.degrees(lambdaE5) }",
     "public var lambda: Double { FiveDecimals.degrees(lambdaE5) * 2 }", [DEG]),
    ("18 public init drops needsReplan", DRIVE, "        self.needsReplan = needsReplan\n    }\n\n    /// A row",
     "        self.needsReplan = false\n    }\n\n    /// A row", [TABLE]),
    ("19 a Double field added", DRIVE, "    public let createdAt: Int64\n",
     "    public let createdAt: Int64\n    public var speedMetersPerSecond: Double = 0\n", [FIELDS]),
    ("20 radius 25 -> 25.01 m", RESOLVER, "public static let radiusMeters: Double = 25",
     "public static let radiusMeters: Double = 25.01", [TABLE]),
    ("21 radius 25 -> 24.99 m", RESOLVER, "public static let radiusMeters: Double = 25",
     "public static let radiusMeters: Double = 24.99", [TABLE]),
    ("22 presence check dropped: every id searched", RESOLVER, PRESENT, "if false {", [TABLE]),
    ("23 presence check always true: no id replaced", RESOLVER, PRESENT, "if true {", [TABLE]),
    ("24 unresolved drive not flagged", RESOLVER, "unresolved.needsReplan = true", "unresolved.needsReplan = false",
     [TABLE]),
    ("25 resolved drive keeps its old flag", RESOLVER, "resolved.needsReplan = false\n", "\n", [TABLE]),
    ("26 farther candidate wins", RESOLVER, TIE,
     "meters < current.meters || (meters == current.meters && id > current.id)", [TABLE]),
    ("27 tie goes to the highest id", RESOLVER, TIE,
     "meters > current.meters || (meters == current.meters && id < current.id)", [TABLE]),
    ("28 longitude window not widened by 1/cos(lat)", RESOLVER, "? 360 : halfLat / cosine", "? 360 : halfLat",
     [TABLE]),
    ("29 box half-side one radius, not two", RESOLVER, "let halfLat = 2 * radiusMeters",
     "let halfLat = 1 * radiusMeters", [TABLE]),
    ("30 corpus scale 1e7 -> 1e6", RESOLVER, "static let corpusScale: Double = 10_000_000",
     "static let corpusScale: Double = 1_000_000", [TABLE]),
    ("31 earth radius 6400 km", RESOLVER, "static let earthRadiusMeters: Double = 6_371_008.8",
     "static let earthRadiusMeters: Double = 6_400_000", [TABLE]),
    ("32 dLat reads longitudes", RESOLVER, "let dLat = (lat2 - lat1) * radians", "let dLat = (lon2 - lon1) * radians",
     [TABLE]),
    ("33 haversine drops the cos(lat) factor", RESOLVER, HAVERSINE, "+ sin(dLon / 2) * sin(dLon / 2)", [TABLE]),
]

EQUIVALENT = [
    ("E1 radius test exclusive", RESOLVER, "guard meters <= radiusMeters else", "guard meters < radiusMeters else",
     "a candidate is at exactly 25.0 m only if a haversine over e5 and e7 grids returns the Double 25.0; on the "
     "meridian the e7 steps nearest 25 m are 24.99665 m (2248) and 25.00777 m (2249), and no row can hit 25.0"),
    ("E2 asin argument not clamped", RESOLVER, "asin(min(1, a.squareRoot()))", "asin(a.squareRoot())",
     "the clamp only matters when rounding lifts sqrt(a) above 1, i.e. near-antipodal points; candidates come from "
     "a box under 1 km across, where sqrt(a) is below 1e-4"),
]

MIN_MUTATIONS = 33
MIN_EQUIVALENT = 2
MIN_TEST_FILES = 3
