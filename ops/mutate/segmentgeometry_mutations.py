"""The mutation population for T-0255's geometry decoder: `Segment.vertices()` in Sources/PlaceStore/Segment.swift
and the value it returns, Sources/PlaceStore/SegmentVertex.swift. The driver is segmentgeometry.py and the runner
segmentgeometry_run.py (surprise's three-file shape).

## What the acceptance names, and where each lives

  * the BYTE COUNT refusal and its payload - entries 1-3 (R2);
  * the VERTEX COUNT minimum, both directions and its payload - 4-8 (R2);
  * the LONGITUDE and LATITUDE bounds, each side moved by one and each side dropped, and each payload - 9-24 (R4);
  * the DECODE - byte offsets, shifts, the four-byte OR, vertex stride, loop range, field order - 25-36;
  * SegmentVertex's two stored fields - 37-38: the tests compare `[lonE7, latE7]` projections to Int32 literals,
    never values built through the same init, so a swapped assignment is seen;
  * the BYTE COUNT class - 39-44 (review rv1-t0255 B1): the modulus moved to 4, 2 and 16, the remainder threshold,
    and the minimum moved by one inside the guard. BYTE_TABLE holds every count 0..40, so every residue mod 8
    appears at least five times and each row asserts the typed error or the whole decoded list.

`(name, path, old, new, killers)`. `old` must occur verbatim or the run reports SKIP and fails; no anchor is a
comment. `killers` are Swift Testing display names in SegmentVerticesTests, every one of which must go red.
EQUIVALENT entries are `(name, path, old, new, witness)` and must all report MISSED.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

_DIR = ROOT / "Sources" / "PlaceStore"
SEGMENT = _DIR / "Segment.swift"
VERTEX = _DIR / "SegmentVertex.swift"
SUBJECTS = (SEGMENT, VERTEX)
MUTATED_FILES = SUBJECTS

TEST_FILES = (ROOT / "Tests" / "PlaceStoreTests" / "SegmentVerticesTests.swift",)

MEASURED = "accepts the measured row of way 107 bucket 4, byte for byte, as the ETL wrote it"
HAND = "accepts every byte position and sign: a hand-typed blob with four distinct bytes per int32"
BOUNDS = "accepts every exact bound and the two-vertex minimum, whole result compared"
TRUNC = "a blob cut by one whole vertex is a valid shorter polyline (R3): 24 bytes cut to 16 decode as two"
PARTIAL = "refuses a byte count that is not whole vertices: 1, 7, 9, 15, 17, 23"
TOO_FEW = "refuses fewer than two vertices: 0 bytes and 8 bytes"
LON = "refuses a longitude one past either bound, and Int32.min/max, at the vertex that holds it"
LAT = "refuses a latitude one past either bound, and Int32.min/max, at the vertex that holds it"
BYTE_TABLE = "every byte count 0 through 40, every residue mod 8: the typed error or the whole decoded list"
ORDER = "check order: byte count, then vertex count, then each vertex lon before lat, first offender wins"

LON_GUARD = "lon >= -Self.maxLonE7 && lon <= Self.maxLonE7"
LAT_GUARD = "lat >= -Self.maxLatE7 && lat <= Self.maxLatE7"

MUTATIONS = [
    ("1 byte-count check dropped", SEGMENT, "geometry.count % Self.vertexBytes == 0", "true", [PARTIAL, ORDER]),
    ("2 partialVertex payload is the remainder", SEGMENT, "partialVertex(byteCount: geometry.count)",
     "partialVertex(byteCount: geometry.count % Self.vertexBytes)", [PARTIAL, ORDER]),
    ("3 vertexBytes 8 -> 4", SEGMENT, "static let vertexBytes = 8", "static let vertexBytes = 4", [MEASURED]),
    ("4 minimumVertices 2 -> 1", SEGMENT, "static let minimumVertices = 2", "static let minimumVertices = 1",
     [TOO_FEW, ORDER]),
    ("5 minimumVertices 2 -> 3", SEGMENT, "static let minimumVertices = 2", "static let minimumVertices = 3",
     [BOUNDS, TRUNC]),
    ("6 count >= minimum -> count > minimum", SEGMENT, "count >= Self.minimumVertices",
     "count > Self.minimumVertices", [BOUNDS, TRUNC]),
    ("7 vertex-count check dropped", SEGMENT, "count >= Self.minimumVertices", "true", [TOO_FEW, ORDER]),
    ("8 tooFewVertices payload 0", SEGMENT, "tooFewVertices(count: count)", "tooFewVertices(count: 0)", [TOO_FEW]),
    ("9 maxLonE7 one wider", SEGMENT, "maxLonE7: Int32 = 1_800_000_000", "maxLonE7: Int32 = 1_800_000_001", [LON]),
    ("10 maxLonE7 one narrower", SEGMENT, "maxLonE7: Int32 = 1_800_000_000", "maxLonE7: Int32 = 1_799_999_999",
     [BOUNDS]),
    ("11 lon lower bound dropped", SEGMENT, LON_GUARD, "lon <= Self.maxLonE7", [LON]),
    ("12 lon upper bound dropped", SEGMENT, LON_GUARD, "lon >= -Self.maxLonE7", [LON]),
    ("13 lon lower bound exclusive", SEGMENT, LON_GUARD, "lon > -Self.maxLonE7 && lon <= Self.maxLonE7", [BOUNDS]),
    ("14 lon upper bound exclusive", SEGMENT, LON_GUARD, "lon >= -Self.maxLonE7 && lon < Self.maxLonE7", [BOUNDS]),
    ("15 lon guard reads lat", SEGMENT, LON_GUARD, "lat >= -Self.maxLonE7 && lat <= Self.maxLonE7", [LON]),
    ("16 lon payload index 0", SEGMENT, "longitudeOutOfRange(index: index, lonE7: lon)",
     "longitudeOutOfRange(index: 0, lonE7: lon)", [LON]),
    ("17 maxLatE7 one wider", SEGMENT, "maxLatE7: Int32 = 900_000_000", "maxLatE7: Int32 = 900_000_001", [LAT]),
    ("18 maxLatE7 one narrower", SEGMENT, "maxLatE7: Int32 = 900_000_000", "maxLatE7: Int32 = 899_999_999",
     [BOUNDS]),
    ("19 lat lower bound dropped", SEGMENT, LAT_GUARD, "lat <= Self.maxLatE7", [LAT]),
    ("20 lat upper bound dropped", SEGMENT, LAT_GUARD, "lat >= -Self.maxLatE7", [LAT]),
    ("21 lat lower bound exclusive", SEGMENT, LAT_GUARD, "lat > -Self.maxLatE7 && lat <= Self.maxLatE7", [BOUNDS]),
    ("22 lat upper bound exclusive", SEGMENT, LAT_GUARD, "lat >= -Self.maxLatE7 && lat < Self.maxLatE7", [BOUNDS]),
    ("23 lat guard reads lon", SEGMENT, LAT_GUARD, "lon >= -Self.maxLatE7 && lon <= Self.maxLatE7", [BOUNDS]),
    ("24 lat payload carries lon", SEGMENT, "latitudeOutOfRange(index: index, latE7: lat)",
     "latitudeOutOfRange(index: index, latE7: lon)", [LAT]),
    ("25 vertex stride 1 byte", SEGMENT, "let start = index * Self.vertexBytes", "let start = index", [MEASURED]),
    ("26 lat read at the lon offset", SEGMENT, "littleEndianInt32(geometry, at: start + 4)",
     "littleEndianInt32(geometry, at: start)", [MEASURED]),
    ("27 lat read one byte early", SEGMENT, "littleEndianInt32(geometry, at: start + 4)",
     "littleEndianInt32(geometry, at: start + 3)", [MEASURED]),
    ("28 byte 0 read from byte 1", SEGMENT, "UInt32(bytes[start])", "UInt32(bytes[start + 1])", [HAND]),
    ("29 byte 1 shifted 16", SEGMENT, "UInt32(bytes[start + 1]) << 8", "UInt32(bytes[start + 1]) << 16", [HAND]),
    ("30 byte 2 shifted 8", SEGMENT, "UInt32(bytes[start + 2]) << 16", "UInt32(bytes[start + 2]) << 8", [HAND]),
    ("31 byte 3 shifted 16", SEGMENT, "UInt32(bytes[start + 3]) << 24", "UInt32(bytes[start + 3]) << 16", [HAND]),
    ("32 high byte dropped", SEGMENT, "b0 | b1 | b2 | b3", "b0 | b1 | b2", [HAND, MEASURED]),
    ("33 low byte dropped", SEGMENT, "b0 | b1 | b2 | b3", "b1 | b2 | b3", [HAND]),
    ("34 loop skips the last vertex", SEGMENT, "for index in 0..<count", "for index in 0..<count - 1",
     [MEASURED, TRUNC]),
    ("35 loop skips the first vertex", SEGMENT, "for index in 0..<count", "for index in 1..<count", [MEASURED]),
    ("36 vertex fields swapped at the append", SEGMENT, "SegmentVertex(lonE7: lon, latE7: lat)",
     "SegmentVertex(lonE7: lat, latE7: lon)", [MEASURED]),
    ("37 SegmentVertex.lonE7 stores latE7", VERTEX, "self.lonE7 = lonE7", "self.lonE7 = latE7", [MEASURED]),
    ("38 SegmentVertex.latE7 stores lonE7", VERTEX, "self.latE7 = latE7", "self.latE7 = lonE7", [MEASURED]),
    ("39 byte-count modulus 4 (rv1 B1)", SEGMENT, "geometry.count % Self.vertexBytes == 0", "geometry.count % 4 == 0",
     [BYTE_TABLE]),
    ("40 byte-count modulus 2", SEGMENT, "geometry.count % Self.vertexBytes == 0", "geometry.count % 2 == 0",
     [BYTE_TABLE]),
    ("41 byte-count modulus 16", SEGMENT, "geometry.count % Self.vertexBytes == 0", "geometry.count % 16 == 0",
     [BYTE_TABLE]),
    ("42 byte-count remainder below 4 accepted", SEGMENT, "geometry.count % Self.vertexBytes == 0",
     "geometry.count % Self.vertexBytes < 4", [BYTE_TABLE, PARTIAL]),
    ("43 vertex-count guard minimum - 1", SEGMENT, "count >= Self.minimumVertices",
     "count >= Self.minimumVertices - 1", [BYTE_TABLE, TOO_FEW]),
    ("44 vertex-count guard minimum + 1", SEGMENT, "count >= Self.minimumVertices",
     "count >= Self.minimumVertices + 1", [BYTE_TABLE, BOUNDS, TRUNC]),
]

EQUIVALENT = [
    ("E1 bitPattern -> truncatingIfNeeded", SEGMENT, "Int32(bitPattern: b0 | b1 | b2 | b3)",
     "Int32(truncatingIfNeeded: b0 | b1 | b2 | b3)",
     "UInt32 -> Int32 truncatingIfNeeded keeps the low 32 bits, which are all 32: the identical bit pattern"),
    ("E2 reserveCapacity(0)", SEGMENT, "out.reserveCapacity(count)", "out.reserveCapacity(0)",
     "reserveCapacity is an allocation hint; append grows the array to the same elements either way"),
    ("E3 vertex count rounds up", SEGMENT, "let count = geometry.count / Self.vertexBytes",
     "let count = (geometry.count + Self.vertexBytes - 1) / Self.vertexBytes",
     "the guard above it has already refused geometry.count % vertexBytes != 0, so ceil and floor of an exact "
     "quotient are the same integer"),
]

# The literal floors (CLAUDE.md, Verification): the population is exactly this size today.
MIN_MUTATIONS = 44
MIN_EQUIVALENT = 3
MIN_TEST_FILES = 1
