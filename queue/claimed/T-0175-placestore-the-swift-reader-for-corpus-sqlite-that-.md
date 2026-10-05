---
id: T-0175
title: PlaceStore - the Swift reader for corpus.sqlite that the plan and T-0030's touches promised and Sources/ lacks
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T08:31:59Z
lease_expires_at: 2026-10-05T18:31:59Z
worktree: .worktrees/T-0175
branch: task/T-0175
exclusive: [package-swift]
touches: [Package.swift, Package.resolved, Sources/PlaceStore/, Tests/PlaceStoreTests/, .github/workflows/linux-core.yml, ops/lib/check-schema-version.py, pins/PINS.yaml, ops/lib/mutate-population-allowlist.json]
pins_affected: [P-PROD-05]
reviewer: null
depends_on: [T-0173]
verify: [ops/test, ops/check-pins]
acceptance:
  - "Sources/PlaceStore is a root-package target (Linux; GRDB pinned exact; libsqlite3-dev in CI) with `PlaceStore.schemaVersion` a typed literal equal to the corpus schema_version; a test opens a corpus built by `python -m etl.corpus` from the committed fixture and reads meta, one segment by id and one R*Tree bbox query, RED by name against a corpus with a bumped schema_version"
  - "P-PROD-05's assertion widens to the Swift value; `swift test --scratch-path <own>` count line quoted; the Linux compile gate stays green (no Apple-only import in the root graph)"
---
## Brief

From the 16:13 panel (CODE lens, grounded). The plan's architecture lists `Sources/PlaceStore/` (GRDB; corpus
reader on plain SQL; user store + migrations) and P-PROD-05 pins `schema_version == PlaceStore.schemaVersion`.
On main Sources/ holds Handoff and ScenicKit only; Package.swift declares two targets; T-0030's `touches:`
promised Sources/PlaceStore/ and its diff was 100 % Python. T-0147 covers only CLAUDE.md's wording of the
target list. Adding a target edits Package.swift, a serial-only file: `exclusive: [package-swift]`.

## Log
- 2026-09-18T23:04:01Z filed by agent/claude-fable-5-1 from the 16:13 panel's grounded synthesis. Not started; depends on T-0173's schema contract.
- 2026-10-05T08:29:54Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator) from the milestone survey (M4 plan sheet needs PlaceStore search); exclusive root-package because it edits the root Package.swift.
- 2026-10-05T08:31:59Z claimed by agent/claude-opus-5; lease until 2026-10-05T18:31:59Z
- 2026-10-05T08:41:22Z RULINGS by agent/claude-opus-5 (owner), before any code. Population measured first: `python -m etl.corpus --input tests/fixtures/corpus_extract.json --built-at 2026-09-18T00:00:00Z` on the host prints `CORPUS region=fixture ways=7 segments=79 collisions=0` / `CORPUS bytes=114688`; PRAGMA application_id=1396919875 ("SCNC"), user_version=2, meta.schema_version='2', build_complete='1'. Ways 101-106 are twelve 100 m segments each along lat 37.90..37.95 (lon -122.5863..-122.6000); way 107 is seven segments in a loop at lat 37.9689..37.9711, lon -122.5915..-122.5885; places is EMPTY (corpus.py writes `write_places([])`).
  - R1 GRDB: `.package(url: "https://github.com/groue/GRDB.swift.git", exact: "7.11.1")` - the newest tag (`git ls-remote --tags`), whose manifest is swift-tools 6.1 = the CI image's swift:6.1-noble. Package.resolved is committed (exact pin + revision; otherwise every worktree grows an untracked one). GRDB on Linux links the SYSTEM sqlite through its `GRDBSQLite` systemLibrary (`link "sqlite3"`, provider apt libsqlite3-dev); linux-core.yml's core job ALREADY installs `libsqlite3-dev sqlite3` ("sqlite headers for GRDB"), so the workflow needs no edit and is left untouched.
  - R2 WINDOWS. The dev box's swift 6.3.3 toolchain has no sqlite3.h / sqlite3.lib (searched: only Python's sqlite3.dll). An unconditional GRDB dependency would break `swift test` on this box for every agent. So the product dependency carries `condition: .when(platforms: [.linux, .macOS, .iOS])` and every PlaceStore source and test file is wrapped in `#if canImport(GRDB)`; on Windows one visible XCTSkip test says why nothing ran - a skip that prints, never a silent absence. The PlaceStore tests are run in the CI image itself (WSL docker, swift:6.1-noble at the linux-core digest, own --scratch-path); the Windows run proves only that the root graph still builds here.
  - R3 API surface: `PlaceStore(path:)` opens READ-ONLY and refuses (PlaceStoreError) a file whose application_id is not SCNC, whose meta.schema_version != `PlaceStore.schemaVersion`, or whose build_complete != '1'; `meta()` -> CorpusMeta (schema_version, min_app_build, region, corpus_version, built_at, attribution); `segment(id:)` -> Segment? (every scalar column + the geometry BLOB as raw bytes); `segmentIDs(in: BoundingBox)` -> sorted ids from segments_rtree by box INTERSECTION. `public static let schemaVersion: Int = 2`, a typed literal.
  - R4 NO SEARCH in this slice. The orchestrator's brief names "places FTS5 search(query:limit:) for the plan sheet"; the DDL (services/etl/etl/schema.py) has NO FTS5 table, and every corpus the shipping builder makes has ZERO places rows. Adding FTS5 is a DDL change -> SCHEMA_VERSION bump -> ETL + Worker + this literal, outside this task, and a search over an always-empty table could not be tested against anything real. Recorded as the follow-up: "corpus places FTS5 table + PlaceStore.search(query:limit:)", to be filed by the orchestrator after T-0146/the POI join fills places.
  - R5 NO NUMERIC MODULE. Geometry is returned as the stored bytes, NOT decoded into vertices: decoding little-endian int32 pairs is arithmetic that reaches the drawn line, and CLAUDE.md makes a numeric module ship a mutation population - which on this box could run only in docker. The decode lands with its first consumer. The bbox query passes Double degrees straight into SQL. So every new Sources/PlaceStore file computes no number and gets a P-PROC-06 allowlist entry with its reason (touches widened to ops/lib/mutate-population-allowlist.json).
  - R6 FIXTURE: BUILT IN TEST SETUP, not committed. The test runs the shipping `python -m etl.corpus` (cwd services/etl, interpreter $PYTHON else python3) over the committed services/etl/tests/fixtures/corpus_extract.json into a temp dir. A committed .sqlite would keep schema_version 2 forever and go stale silently when the DDL moves; building it means a bump in schema.py without a bump in PlaceStore turns this suite red. A missing interpreter is a test FAILURE, never a skip. The bumped corpus is that build with meta.schema_version rewritten to '3' through GRDB.
  - R7 ORACLES by exact equality: meta() == a literal CorpusMeta of the measured values; segment(id: 3003480930389769752) (way 107 bucket 4) == a literal Segment of the measured row incl. its 32-byte geometry hex; bbox query results == the ids a SEPARATE plain-SQL predicate over segments' e7 columns selects for the same box, AND == the measured literal count (box A lat 37.965..37.975 lon -122.595..-122.585 -> exactly way 107's 7 ids; box B lat 37.899..37.901 lon -122.590..-122.586 -> way 101 buckets 0-3, 4 ids, whose west edge CUTS bucket 3 so containment-instead-of-intersection returns 3).
  - R8 P-PROD-05 widens: ops/lib/check-schema-version.py reads a third literal, `public static let schemaVersion: Int = <n>` in Sources/PlaceStore/PlaceStore.swift, all three must agree; --prove-red gains "PlaceStore bumped alone" (exit 1) and "PlaceStore literal deleted" (exit 2). Touches widened to that file and pins/PINS.yaml (the statement's "joins the equality when T-0175 lands" becomes present tense).
