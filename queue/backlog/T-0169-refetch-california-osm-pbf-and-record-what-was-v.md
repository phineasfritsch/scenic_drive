---
id: T-0169
title: refetch california-osm.pbf and record what was verified - never edit bytes: to match a file nothing can verify
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/inputs/manifest.yaml, services/etl/etl/fetch.py, services/etl/tests/test_fetch.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

From the 2026-09-18 14:13 panel (DIRECTION lens; one clause corrected by the grounding pass). The manifest's
california entry is `verify: upstream-md5` (Geofabrik rebuilds daily, so a sha256 pin would break daily) and
records `bytes: 1288490188` at `retrieved: 2026-09-07`. Two old worktrees hold a california-osm.pbf of
1,327,206,195 bytes - a DIFFERENT daily build, whose md5 sidecar no longer exists, so nothing can verify it.

**Forbidden, by name:** editing `bytes:` to 1327206195 so the manifest "matches" the file on disk. That asserts
a number against the file it was read from - this repository's signature defect.

**Do:** run `ops/etl-fetch-inputs` in WSL (it wraps `python -m etl.fetch`, which verifies the download against
TODAY's Geofabrik md5 sidecar). The grounding pass checked: the fetcher does NOT write the manifest - so record
`bytes:` and `retrieved:` from the verified file in the same commit and quote the md5 match in the Log.
Optional, small: make `etl.fetch` print `bytes` and the date after a verified fetch so the next refetch is a
copy, not a computation, with a test. 1.3 GB stays out of git (`services/etl/inputs/*.pbf` is ignored - confirm).

## Log
- 2026-09-18T20:57:28Z filed by agent/claude-fable-5-1 from the 14:13 panel's grounded synthesis. Not started.
