---
id: T-0023
title: ETL skeleton: pinned Docker image, pytest tier, inputs manifest with sha256 + license
state: claimed
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T09:51:53Z
lease_expires_at: 2026-09-07T13:51:53Z
worktree: ../wt/T-0023
branch: task/T-0023
exclusive: []
touches: [services/etl/, ops/etl, ops/etl-fetch-inputs, ops/test]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The machinery before the data. Nothing here downloads 1.2 GB.

- `services/etl/pyproject.toml` + `tests/` so `ops/test` picks up the pytest tier automatically (it already
  looks for `services/etl/pyproject.toml`). The floor rises by whatever this adds.
- `services/etl/Dockerfile` pinned BY DIGEST with osmium-tool, osm2pgsql, GDAL, python. Pinned, because a
  moving tag is a silent toolchain change (same rule as the swift image in linux-core.yml).
- `services/etl/inputs/manifest.yaml`: one entry per external input with `url`, `sha256`, `bytes`, `license`,
  `retrieved`. NOTHING is fetched without a checksum, and the licence field is required - an agent must not be
  able to add a source without recording what we are allowed to do with it.
- `ops/etl-fetch-inputs` downloads to `services/etl/inputs/`, verifies sha256, and REFUSES on mismatch.

RED: point a manifest entry's sha256 at a wrong value -> fetcher exits non-zero and deletes the partial file.
RED: add a manifest entry with no `license` -> the manifest validator fails.
GREEN: `ops/test` shows a pytest count; `ops/etl-fetch-inputs --dry-run` lists what it would fetch with sizes.

## Log
- 2026-09-07T09:51:53Z claimed by agent/claude-opus-5; lease until 2026-09-07T13:51:53Z
