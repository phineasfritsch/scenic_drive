"""The mutation population for Sources/Telemetry (T-0265). The runner is telemetry.py, the mutant runner
telemetry_run.py - the straightline.py family shape, split under CLAUDE.md's 300-line cap.

## The subjects

Eight files compute or serialize something: the H3 port (H3CoordIJK, H3FaceProjection, H3BaseCells, H3IndexBuilder and
the H3Cell entry point), CompletionPercent (floor and clamp), TelemetryDataPoint (its Encodable output is
the R2 fixed-width wire object) and TelemetryEvent (the encoder that writes the
numbers and labels into a data point). They are the runner's `SUBJECT_MODULES`, and every one is edited by at
least one entry below - the floor refuses a run where one is not. The closed label enums and the kind list
compute nothing and sit in ops/lib/mutate-population-allowlist.json, one reason each.

## Each entry, and what `killers` is for

`(name, path, old, new, killers)`, straightline_mutations.py's shape. `old` must appear VERBATIM in the
pristine file or the run reports SKIP and FAILS; no anchor is a comment. `killers` are the display names
Swift Testing prints, and EVERY named killer must go red - a catch by some other test is WRONG KILLER and
fails the run. The H3 entries name the 5000-row population test, the one assertion that ranges over
uber/h3's published cells; the encoder entries name the whole-data-point equality test.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "Telemetry"

COORD = SRC / "H3CoordIJK.swift"
FACE = SRC / "H3FaceProjection.swift"
BASE = SRC / "H3BaseCells.swift"
BUILDER = SRC / "H3IndexBuilder.swift"
CELL = SRC / "H3Cell.swift"
PERCENT = SRC / "CompletionPercent.swift"
POINT = SRC / "TelemetryDataPoint.swift"
EVENT = SRC / "TelemetryEvent.swift"
SUBJECTS = (COORD, FACE, BASE, BUILDER, CELL, PERCENT, POINT, EVENT)
MUTATED_FILES = SUBJECTS

TEST_DIR = ROOT / "Tests" / "TelemetryTests"

REF_ALL = "every row of uber/h3 rand05centers.txt encodes to its published cell"
REF_TEN = "ten published H3 reference cells encode by exact equality"
PENT = "every point around the twelve res-5 pentagons encodes to uber/h3's own cell"
ENCODE = "every event encodes to its whole Analytics Engine data point by exact equality"
FOURTEEN = "the plan's fourteen events, no more and no fewer, each with a row"
JSON = "the data point serializes to exactly writeDataPoint's three keys"
WHITELIST = "no event case carries a type outside the P-PRIV-05 whitelist"
PCT = "a fraction floors to a whole percent clamped into 0...100"
EVERY_JSON = "every event serializes byte-for-byte with its empty blobs and zero doubles kept in place"
FIELDS = "each whitelisted payload type stores exactly its pinned fields"

MUTATIONS = [
    # H3CoordIJK - the hex grid arithmetic.
    ("hex2d: the odd-row fold across the i axis loses its +1", COORD,
     "i -= 2 * diff + 1", "i -= 2 * diff", [REF_ALL]),
    ("hex2d: the fold across the j axis uses j / 2", COORD,
     "i -= (2 * j + 1) / 2", "i -= j / 2", [REF_ALL]),
    ("upAp7: the i coefficient's sign flipped", COORD,
     "i = Int((Double(3 * ci - cj) / 7.0).rounded())", "i = Int((Double(3 * ci + cj) / 7.0).rounded())",
     [REF_ALL, REF_TEN]),
    ("upAp7r: the j coefficient's sign flipped", COORD,
     "j = Int((Double(3 * cj - ci) / 7.0).rounded())", "j = Int((Double(3 * cj + ci) / 7.0).rounded())",
     [REF_ALL, REF_TEN]),
    ("downAp7r: the clockwise child built with the ccw i vector", COORD,
     "i = 3 * a + c", "i = 3 * a + b", [REF_ALL]),
    ("digit: the unit vector read k-major instead of i-major", COORD,
     "return 4 * diff.i + 2 * diff.j + diff.k", "return 4 * diff.k + 2 * diff.j + diff.i", [REF_ALL, REF_TEN]),
    # H3FaceProjection - face choice and the gnomonic projection.
    ("closest face: face 19 never considered", FACE,
     "for candidate in 0..<centerPoint.count {", "for candidate in 0..<centerPoint.count - 1 {", [REF_ALL]),
    ("Class III rotation applied at even resolutions", FACE,
     "if resolution % 2 == 1 {", "if resolution % 2 == 0 {", [REF_ALL, REF_TEN]),
    ("the projection is equidistant, not gnomonic", FACE,
     "r = tan(r) / res0UnitGnomonic", "r = r / res0UnitGnomonic", [REF_ALL]),
    ("theta measured with the azimuth added, not subtracted", FACE,
     "- positiveAngle(azimuth(from:", "+ positiveAngle(azimuth(from:", [REF_ALL, REF_TEN]),
    # H3BaseCells - the generated table and its reading.
    ("the base cell rotation count dropped", BASE,
     "return (value / 8, value % 8)", "return (value / 8, 0)", [REF_ALL]),
    ("the face table read with i and k swapped", BASE,
     "packed[face * 27 + coord.i * 9 + coord.j * 3 + coord.k]",
     "packed[face * 27 + coord.k * 9 + coord.j * 3 + coord.i]", [REF_ALL]),
    # H3IndexBuilder - bits, digits and the pentagon rules.
    ("the resolution written one bit low", BUILDER,
     "UInt64(resolution) << 52", "UInt64(resolution) << 51", [REF_ALL, REF_TEN]),
    ("ordinary cells rotated clockwise", BUILDER,
     "                digits = rotate60ccw(digits)\n            }\n        }",
     "                digits = digits.map(rotate60cw)\n            }\n        }", [REF_ALL]),
    ("pentagon rotations treated as ordinary rotations", BUILDER,
     "digits = rotatePentagon60ccw(digits)", "digits = rotate60ccw(digits)", [REF_ALL]),
    ("a pentagon's leading k-axis digit never corrected", BUILDER,
     "if leadingNonZeroDigit(digits) == kAxesDigit {", "if leadingNonZeroDigit(digits) == 7 {", [PENT]),
    # H3Cell - the entry point.
    ("degrees converted with the grad constant", CELL,
     "static let radiansPerDegree = 0.0174532925199432957692369076848861271111",
     "static let radiansPerDegree = Double.pi / 200", [REF_ALL, REF_TEN]),
    # CompletionPercent.
    ("the percent rounds to nearest instead of flooring", PERCENT,
     "(fraction * 100).rounded(.down)", "(fraction * 100).rounded()", [PCT, ENCODE]),
    ("the percent is not clamped at 100", PERCENT,
     "Int(Swift.min(100, Swift.max(0, percent)))", "Int(Swift.max(0, percent))", [PCT]),
    ("a whitelisted wrapper stores the raw Double fraction", PERCENT,
     "    public init(fraction: Double) {\n",
     "    public let fraction: Double\n\n    public init(fraction: Double) {\n        self.fraction = fraction\n",
     [WHITELIST, FIELDS]),
    # H3Cell - the whitelisted cell must not carry a coordinate beside its index.
    ("the cell stores a latitude beside its index", CELL,
     "    public let index: UInt64\n", "    public let index: UInt64\n    public let latitude: Double = 34.1\n",
     [WHITELIST, FIELDS]),
    # TelemetryDataPoint - R2's fixed width on the wire.
    ("the empty blobs compacted out of the JSON", POINT,
     "        self.doubles = doubles\n    }\n",
     "        self.doubles = doubles\n    }\n\n"
     "    private enum CodingKeys: String, CodingKey { case indexes, blobs, doubles }\n\n"
     "    public func encode(to encoder: Encoder) throws {\n"
     "        var box = encoder.container(keyedBy: CodingKeys.self)\n"
     "        try box.encode(indexes, forKey: .indexes)\n"
     "        try box.encode(blobs.filter { !$0.isEmpty }, forKey: .blobs)\n"
     "        try box.encode(doubles, forKey: .doubles)\n    }\n",
     [EVERY_JSON]),
    ("the zero doubles compacted out of the JSON", POINT,
     "        self.doubles = doubles\n    }\n",
     "        self.doubles = doubles\n    }\n\n"
     "    private enum CodingKeys: String, CodingKey { case indexes, blobs, doubles }\n\n"
     "    public func encode(to encoder: Encoder) throws {\n"
     "        var box = encoder.container(keyedBy: CodingKeys.self)\n"
     "        try box.encode(indexes, forKey: .indexes)\n"
     "        try box.encode(blobs, forKey: .blobs)\n"
     "        try box.encode(doubles.filter { $0 != 0 }, forKey: .doubles)\n    }\n",
     [EVERY_JSON]),
    # TelemetryEvent - the encoder and the closed list.
    ("the origin cell left out of plan_requested", EVENT,
     "cell = origin.hexString", "cell = \"\"", [ENCODE, JSON]),
    ("the deviation count never written", EVENT,
     "value2 = Double(deviations)", "value2 = 0", [ENCODE]),
    ("both paywall steps written as one wire name", EVENT,
     "name = \"paywall_\" + step.rawValue", "name = \"paywall\"", [ENCODE]),
    ("a no answer written as an empty label", EVENT,
     "label = prettier ? \"prettier\" : \"not_prettier\"", "label = prettier ? \"prettier\" : \"\"", [ENCODE]),
    ("the sampling index dropped from the data point", EVENT,
     "TelemetryDataPoint(indexes: [name],", "TelemetryDataPoint(indexes: [],", [ENCODE, JSON]),
    ("paywall reported as the corpus_activated kind", EVENT,
     "case .paywall: return .paywall", "case .paywall: return .corpusActivated", [FOURTEEN]),
    ("corpus_activated carries a Double", EVENT,
     "case corpusActivated(version: Int)", "case corpusActivated(version: Double)", [WHITELIST]),
]

EQUIVALENT = [
    ("normalize subtracts the minimum when it is zero too", COORD,
     "if low > 0 {", "if low >= 0 {",
     "`low` is an Int, and the only value `>= 0` admits that `> 0` does not is 0; the branch then subtracts 0 "
     "from each of three Int components, which is the identity. No input distinguishes the two spellings."),
]

MIN_MUTATIONS = 30
MIN_EQUIVALENT = 1
MIN_TEST_FILES = 4
