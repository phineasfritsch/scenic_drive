---
id: T-0270
title: the bundled tiny fallback corpus - an ETL target that writes a size-capped LA places-only corpus the app ships in its bundle, so Surprise and the plan sheet are never empty before the first-run download
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T00:35:18Z
lease_expires_at: 2026-10-06T12:35:18Z
worktree: .worktrees/T-0270
branch: task/T-0270
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, ops/, apps/ios/ScenicDrive/Corpus/, .gitignore, Tests/PlaceStoreTests/, ops/mutate/, ops/lib/mutate-population-allowlist.json, ops/lib/mutate_population_table.py]
pins_affected: [P-PROD-05, P-DATA-03, P-ATTR-02]
reviewer: null
depends_on: [T-0266]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST: from the T-0266 LA places, quote per-class counts and the byte size of a places-only corpus at 3 candidate caps; RULE the selection (per-class cap, ranking - e.g. named viewpoints/peaks/beaches/waterfalls/trailheads first, cafes last - and a hard byte ceiling, e.g. <= 1.5 MB) in the Log before any test"
  - "an ETL command (python -m etl.fallback or a flag on the corpus build) writes the fallback corpus deterministically (same input -> byte-identical file, tested by sha256 twice), with the same schema_version, application_id and build_complete as a full corpus, places + places_fts + places_rtree, zero ways/segments, meta.kind = 'fallback', and the ODbL table_licenses rows; a pytest pins the selection by exact equality over a fixture and every per-class cap at its bound"
  - "the file is committed under apps/ios/ScenicDrive/Corpus/ (buildable folder - no pbxproj edit; the .gitignore corpus*.sqlite rule gets one ruled exception for that exact path, and a size guard check refuses the file above the ceiling) and a PlaceStore test in the CI image opens THAT committed file and finds three named LA places by prefix search (equality on the returned rows)"
---
## Brief

Plan 'First run: ... bundled tiny fallback corpus so the app is never empty'. T-0266 filled places from an OSM
allowlist (LA: 4773 named). Nothing ships a corpus to the device yet (first-run download/OTA needs owner R2). This
task is the fallback file only - the app code that opens it is the next task (FeatureSurpriseMe / plan sheet).
ODbL: the file is a Derivative Database of OSM; LICENSE-DATA / NOTICE already cover the corpus (P-ATTR-02) - confirm.

## Log
- 2026-10-06T00:33:34Z filed by agent/claude-opus-5 (orchestrator) after PR #157 (T-0266) merged.
- 2026-10-06T00:35:18Z claimed by agent/claude-opus-5; lease until 2026-10-06T12:35:18Z
- 2026-10-06T00:45:28Z MEASURED FIRST (agent/claude-opus-5, owner), before any predicate. Read: corpus.py, corpuswriter.py, schema.py (PRAGMAS, ODBL_TABLES, REQUIRED_META_KEYS), extractplace.py, placeallow.py, Sources/PlaceStore/PlaceStore.swift (init's three refusals, search's SQL), Tests/PlaceStoreTests/CorpusFixture.swift, LICENSE-DATA, pins P-PROD-05 / P-DATA-03 / P-ATTR-02, T-0266's Log. INPUT: T-0266's places stream, main checkout services/etl/work/t0266/la-places.osm.xml, 21,234,228 B, sha256 a08035546fd5bab7ec199c65ab4cf703680416701c8d198cc304a1ccb9b830e9. Driver (throwaway, gitignored) services/etl/work/t0270/measure.py on host python (sqlite 3.40.1), the SHIPPING `placeallow.select` then `corpus.build` over an extract of zero ways:
  - `PLACES places=4773 unnamed=5906 refused_access=48 chain=788 skipped_geometry=0 deduped=2 viewpoint=102 peak=187 waterfall=36 beach=56 trailhead=99 museum=232 cafe=1511 garden=334 park=2112 town=104` (= T-0266's count line, tolerance 0)
  - per class (osm types; mean name bytes): viewpoint 102 (n101 w1; 18.7), peak 187 (n187; 12.9), waterfall 36 (n36; 17.2), beach 56 (n6 w26 r24; 16.4), trailhead 99 (n99; 23.6), museum 232 (n76 w138 r18; 25.6), cafe 1511 (n1365 w146; 14.3), garden 334 (n121 w181 r32; 19.7), park 2112 (n64 w1951 r97; 17.6), town 104 (n104; 9.7)
  - places-only corpus at three uniform per-class caps (ranked by place_id) and uncapped: `CAP 50 places=486 bytes=233472` / `CAP 150 places=1147 bytes=397312` / `CAP 400 places=1950 bytes=585728` / `CAP 100000 places=4773 bytes=1187840`. Bytes grow ~250 B/place over a ~110 KB empty-schema floor.
- 2026-10-06T00:45:28Z RULINGS before any test (agent/claude-opus-5).
  - F1 WHERE. New module services/etl/etl/fallback.py, entry point `python -m etl.fallback --places-osm <places.osm.xml> --out <file> --built-at <ISO> --region <id>`. It runs the SHIPPING `placeallow.select` (T-0266, unchanged), applies the caps (F2), and hands the chosen rows to the SHIPPING `corpus.build` as an extract with `"ways": []` - so schema, application_id, schema_version, table_licenses, content_sha256 and build_complete come from the one writer a full corpus uses, not a second one.
  - F2 SELECTION, per-class caps, ONE ordered table, scenic first and cafes last: viewpoint 200, peak 200, waterfall 200, beach 200, trailhead 200, museum 150, garden 150, park 400, town 150, cafe 50. On the measured LA counts that keeps every viewpoint/peak/waterfall/beach/trailhead/town (102/187/36/56/99/104) and caps museum 232->150, garden 334->150, park 2112->400, cafe 1511->50: 1334 places. Within a class the rank is place_id ascending (segid.place_id: a hash of (osm_type, osm_id) - deterministic, independent of input order, and spatially unbiased; the places rows carry no notability signal). A place whose cls is not in the table is REFUSED (ValueError), never kept or dropped silently: a new allowlist class must be ruled into the table (the table's classes are tested equal to placeallow.CLASSES).
  - F3 CEILING: FALLBACK_BUDGET_BYTES = 1 MiB (1,048,576), refused with corpus.py's `>=` rule and BUDGET_EXIT 3 (file left on disk), passed as corpus.build's own budget_bytes. The uncapped 1,187,840 B is over it, so the ceiling bites on "ship everything"; the ruled selection is measured at ~0.45 MB (to be quoted at the build stage). The SIZE GUARD on the committed file is a pytest (services/etl/tests/test_fallback_committed.py) that refuses the committed path at or above the same literal - seen red by lowering the literal below the file's size.
  - F4 META: corpus.build gains `kind=None`; when given it writes meta.kind (inside content_sha256, before build_complete). The fallback passes 'fallback'. A full corpus writes NO kind key, so every existing corpus and its digests are unchanged (absence = a full corpus; the device task reads it). REQUIRED_META_KEYS unchanged.
  - F5 FILE: apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite (Xcode 26 buildable folder: 3 PBXFileSystemSynchronizedRootGroup in project.pbxproj, so no pbxproj edit). .gitignore gains exactly `!apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite` under its `corpus*.sqlite` rule; .gitattributes already has `*.sqlite binary`. Built with built_at 2026-10-06T00:00:00Z, region la, in the pinned ETL image (scenic-etl, sqlite 3.45.1 - schema.PINNED_SQLITE_VERSION) via WSL docker, twice, sha256 compared; determinism also pinned by a host pytest (two builds of the fixture, byte-identical sha256).
  - F6 T-0175 R6 ("never a committed .sqlite") governs TEST FIXTURES; this file is a product asset. R6's hazard - a committed file keeps its schema forever - is closed by test_fallback_committed.py: the committed file's PRAGMA user_version/application_id, meta.schema_version and its ddl_sha256 must equal a corpus freshly built by the shipping builder, so a DDL bump without a rebuild turns CI red by name.
  - F7 P-DATA-03 (built_at < 30 days) is for the corpus the app downloads (SCENIC_LA_CORPUS / OTA); the fallback's built_at is frozen by design and it says so in meta.kind. Pin unchanged; OPEN for the device task: prefer any downloaded corpus over the fallback, never present the fallback's built_at as fresh.
  - F8 ODbL / P-ATTR-02: the fallback is a subset of the corpus, every row from OSM (placeallow), in schema.ODBL_TABLES (places, places_rtree, places_fts), and meta.table_licenses / attribution / odbl_notice are written by corpus.build exactly as for a full corpus (asserted equal). LICENSE-DATA already names "the scenic segment corpus" as an ODbL derived database of OSM - covers it; no NOTICE file exists in the tree; nothing changes.
  - F9 PLACESTORE TEST: Tests/PlaceStoreTests/PlaceStoreFallbackTests.swift opens THE committed path (located from #filePath, no Package.swift edit, no resource copy) through the shipping PlaceStore.init and asserts search rows by full equality for three named LA places chosen from the classes F2 keeps whole (a peak, a beach, a viewpoint). Expected rows are read from the committed file before the test is written and quoted here.
  - F10 POPULATION: ops/mutate/fallback.py (a selection module), literal floor = its size; DRIVERS and COVERED_FLOOR in ops/lib/mutate_population_table.py gain it (T-0266 R11's whitelist).
