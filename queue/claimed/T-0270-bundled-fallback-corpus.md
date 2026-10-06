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
