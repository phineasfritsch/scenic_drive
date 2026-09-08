---
id: T-0038
title: services/etl/Dockerfile was never created - T-0023 shipped without the pinned ETL image
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`T-0023`'s brief required `services/etl/Dockerfile` pinned BY DIGEST with osmium-tool, osm2pgsql, GDAL and
python. It was never written. The file does not exist, `git ls-files services/etl` does not list it, and
reviewer-12 signed the task off anyway - nothing in the suite reads it, so nothing went red.

That matters for T-0024 onward: the Bay Area extract runs osmium/osm2pgsql, and without a pinned image every
agent runs a different toolchain and blames the data when the output differs.

- `services/etl/Dockerfile`, base image pinned by `@sha256:` digest (same rule as `swift:6.1-noble` in
  `.github/workflows/linux-core.yml`), with osmium-tool, osm2pgsql, GDAL/ogr2ogr and python3.
- A test that the Dockerfile exists and its `FROM` line carries a `@sha256:` digest - anchored on the file, not
  a comment, so "we'll pin it later" fails the suite instead of passing quietly.
- Demonstrate red: delete the digest from `FROM`, show the test fail, restore, show it pass.

## Log
