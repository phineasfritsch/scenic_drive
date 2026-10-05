---
id: T-0255
title: PlaceStore decodes the segment geometry BLOB into e7 vertices
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T20:07:17Z
lease_expires_at: 2026-10-06T08:07:17Z
worktree: .worktrees/T-0255
branch: task/T-0255
exclusive: []
touches: [Sources/PlaceStore/, Tests/PlaceStoreTests/, ops/mutate/, ops/lib/mutate_population_table.py, ops/lib/mutate-population-allowlist.json]
pins_affected: []
reviewer: null
depends_on: [T-0175]
verify: [ops/test, ops/check-pins]
acceptance:
  - "Segment exposes its decoded vertices (Int32 e7 lat/lon pairs) equal by exact equality to the ETL's encoder output for every fixture segment; a mutation population under ops/mutate/ with a literal floor"
---
## Brief

Follow-up recorded in T-0175's Log (PR #142, review PASS): geometry is returned as stored bytes today (T-0175 R5) so no PlaceStore file computes a number; decoding is the first numeric code there and ships its own population.

## Log
- 2026-10-05T11:49:04Z filed by agent/claude-opus-5 (orchestrator) from T-0175's stillOpen list.
- 2026-10-05T20:05:56Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0254 (PR #152) merged; PlaceStore free.
- 2026-10-05T20:07:17Z claimed by agent/claude-opus-5; lease until 2026-10-06T08:07:17Z
- 2026-10-05T20:14:46Z RULINGS by agent/claude-opus-5 (owner), before any code. Read: Sources/PlaceStore/*, services/etl/etl/geom.py (`PACK = struct.Struct("<ii")`, `pack`, `to_e7`), segmenter.py (`Segment.geometry = geom.pack(coords)`), corpuswriter.py `write_segments`, schema.py `segments` DDL, extractway.py (lat/lon range refusal), Tests/PlaceStoreTests/*, ops/mutate/surprise*.py, ops/lib/check-mutate-population.py.
  - R1 THE SHIPPING SYMBOL. `Segment.vertices() throws -> [SegmentVertex]` decodes `geometry` in stored order; `SegmentVertex` carries `lonE7: Int32, latE7: Int32` (the blob's own order, the struct's lon-first naming). No helper type: every test calls `vertices()` on a `Segment`, the value `PlaceStore.segment(id:)` returns.
  - R2 WHAT THE ENCODER CAN WRITE, so what the decoder accepts. 8 bytes per vertex (`<ii`, little-endian int32 lon_e7 then lat_e7). schema.py CHECKs `length(geometry) >= 16 AND length(geometry) % 8 = 0`, so the shipping builder never stores fewer than 2 vertices. extractway.py refuses lat outside [-90, 90] and lon outside [-180, 180] before `to_e7`, so every stored lon_e7 is in [-1_800_000_000, 1_800_000_000] and lat_e7 in [-900_000_000, 900_000_000] (the same bounds the DDL puts on min/max_*_e7). Anything else is REFUSED with `SegmentGeometryError`: `partialVertex(byteCount:)` (length % 8 != 0 - this is "odd length" and every truncation that is not a multiple of 8), `tooFewVertices(count:)` (0 or 1), `longitudeOutOfRange(index:lonE7:)`, `latitudeOutOfRange(index:latE7:)`. Check order is length, count, then per vertex lon before lat, first offender wins; the order is table-tested, not prose.
  - R3 TRUNCATION BY A WHOLE VERTEX IS UNDETECTABLE: a 24-byte blob cut to 16 is a valid 2-vertex polyline the encoder could have written. No checksum exists in the schema; the decoder cannot and does not claim to see it. Table row: 24 -> 16 accepted with the whole result compared.
  - R4 RANGE TABLE. The input is `[UInt8]`; NaN, inf, nil, str and bool are not values the type admits, so those rows do not exist. The bounds are integers, so "just outside" is bound +/- 1 (nextafter's integer analogue). Every bound: byte counts 0, 1, 7, 8, 9, 15, 16, 17, 23, 24; lon -1_800_000_001 / -1_800_000_000 / 1_800_000_000 / 1_800_000_001; lat -900_000_001 / -900_000_000 / 900_000_000 / 900_000_001; Int32.min and Int32.max; the offender at index 0, 1 and 2. An accepted row compares the WHOLE vertex list as Int32 literals (not via SegmentVertex's own init, so a swapped init field is seen).
  - R5 GATING. Segment, SegmentVertex and SegmentGeometryError use nothing from GRDB, so they leave `#if canImport(GRDB)` (T-0175 R2 gated the whole module because the READER needs SQLite; a value and its arithmetic do not). The refusal table therefore runs on every toolchain including this Windows box, and the mutation population runs natively here (swift 6.3.3) - the CI image is needed only for the corpus half (R6). PlaceStore, BoundingBox, CorpusMeta, Place, PlaceSearchQuery, PlaceStoreError stay gated.
  - R6 THE ACCEPTANCE ORACLE ("equal by exact equality to the ETL's encoder output for every fixture segment"). A GRDB-gated test builds the fixture corpus with the shipping `python -m etl.corpus`, then runs the ETL's OWN segmenter over the same extract in a separate python process and prints, per (way_id, bucket), `geom.to_e7(lon), geom.to_e7(lat)` for each of `seg.coords` - the encoder's input quantised by the encoder's own function, NOT an unpack of the stored blob (an unpack would be the decoder compared to itself). Every id from `segmentIDs(in:)` over the whole world box is read with `segment(id:)`; the (way, bucket) key sets must be equal (79 measured in T-0175), and `vertices()` must equal the oracle list exactly for each.
  - R7 POPULATION. ops/mutate/segmentgeometry.py (CLI, floor, --prove-floor, --prove-vacuity, --only), segmentgeometry_mutations.py, segmentgeometry_run.py - surprise's three-file shape; SUBJECT_MODULES = Segment.swift, SegmentVertex.swift. SegmentGeometryError.swift is a four-case enum with no operator and goes on the P-PROC-06 allowlist; Segment.swift LEAVES the allowlist (the checker refuses a module both covered and allowlisted). That requires ops/lib/mutate_population_table.py (DRIVERS, COVERED_FLOOR) and ops/lib/mutate-population-allowlist.json: `touches:` widened to name those two files (neither is serial-only).
  - R8 OUT OF SCOPE: a decoded polyline disagreeing with its own row's min/max/mid box. The ETL computes both from the same coords; a cross-check is a corpus-integrity feature for a later task, recorded in stillOpen.
