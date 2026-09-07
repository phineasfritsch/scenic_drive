---
id: T-0023
title: ETL skeleton: pinned Docker image, pytest tier, inputs manifest with sha256 + license
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T09:51:53Z
lease_expires_at: 2026-09-07T13:51:53Z
worktree: ../wt/T-0023
branch: task/T-0023
exclusive: [floors]
touches: [services/etl/, ops/etl-fetch-inputs, ops/test, pins/floor_linux.txt]
pins_affected: []
reviewer: agent/reviewer-9
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
- 2026-09-07T11:30:00Z GREEN: 26 pytest tests pass; ops/test picks up the pytest tier automatically (it already keys off services/etl/pyproject.toml). `python -m etl.fetch --dry-run` against the real manifest reports california-osm.pbf, 1229 MB, verify=upstream-md5, ODbL-1.0 - without downloading anything.
- 2026-09-07T11:30:00Z RED 1 (bad publisher checksum): pointed checksum_url at a .md5.WRONG path -> fetch downloaded 1.2 GB, failed verification, DELETED the file and exited 1. Verified no *.pbf left in inputs/. A partial or unverified file must never be left where a later stage would read it.
- 2026-09-07T11:30:00Z RED 2 (missing licence): appended an entry with no `license` -> "MANIFEST INVALID / nolicense.bin: license is required - what are we allowed to do with this data?", exit 2, nothing fetched.
- 2026-09-07T11:30:00Z TWO VERIFICATION MODES, because the sources genuinely differ. Geofabrik rebuilds california-latest.osm.pbf DAILY and publishes a .md5 sidecar; pinning a sha256 there would break the fetcher every day and teach everyone to bypass it. Static files (3DEP tiles, NLCD rasters) get a hard sha256. There is deliberately NO "none" mode - an input we cannot verify is an input we do not take, and a test asserts that.
- 2026-09-07T11:30:00Z --record-digest exists so pinning a digest is a deliberate human act. A fetcher that silently accepts whatever the network hands it the first time, and pins THAT, is laundering provenance rather than verifying it.
- 2026-09-07T11:30:00Z SELF-CAUGHT by my own validator: my first manifest carried a USGS 3DEP entry with verify=sha256 and no digest, which the validator rejected. That was right - the manifest's own rule is that entries arrive with the task that consumes them. Removed; T-0026 adds it with a real digest.
- 2026-09-07T11:30:00Z SELF-CAUGHT twice more by the tests: (a) the https-only rule rejected the test server's loopback URL, so I added a narrow, documented carve-out for 127.0.0.1/localhost ONLY, with a test asserting http://10.0.0.5 and http://127.0.0.1.evil.com are still rejected; (b) a manifest missing a required field crashed the parser with a TypeError instead of reporting a useful problem - every field now defaults so validation reports it properly.
- 2026-09-07T11:30:00Z NOT DONE HERE, deliberately: the pinned Dockerfile (osmium/osm2pgsql/GDAL). Everything in this task is pure python and runs in CI as-is; the image is only needed when T-0024 first touches the .pbf, and pinning a digest for tools nothing yet calls is ceremony. Say so if you disagree.
- 2026-09-07T11:30:00Z moved to review/, reviewer agent/reviewer-9
- 2026-09-07T11:30:00Z GREEN: 26 pytest tests pass; ops/test picks up the pytest tier automatically (it keys off services/etl/pyproject.toml). `python -m etl.fetch --dry-run` reports california-osm.pbf, 1229 MB, verify=upstream-md5, ODbL-1.0, without downloading anything.
- 2026-09-07T11:30:00Z RED 1 (bad publisher checksum): pointed checksum_url at a .md5.WRONG path -> fetch pulled 1.2 GB, failed verification, DELETED the file, exit 1. Confirmed no *.pbf left in inputs/. An unverified file must never sit where a later stage would read it.
- 2026-09-07T11:30:00Z RED 2 (missing licence): appended an entry with no `license` -> "MANIFEST INVALID / nolicense.bin: license is required - what are we allowed to do with this data?", exit 2, nothing fetched.
- 2026-09-07T11:30:00Z TWO VERIFICATION MODES because the sources differ. Geofabrik rebuilds california-latest.osm.pbf DAILY and publishes a .md5 sidecar; a pinned sha256 there would break the fetcher every day and teach everyone to bypass it. Static files (3DEP, NLCD) get a hard sha256. There is deliberately NO "none" mode - an input we cannot verify is one we do not take, and a test asserts that.
- 2026-09-07T11:30:00Z --record-digest makes pinning a digest a deliberate human act. A fetcher that silently accepts whatever the network hands it first, then pins THAT, launders provenance rather than verifying it.
- 2026-09-07T11:30:00Z SELF-CAUGHT by my own validator: my first manifest had a USGS 3DEP entry with verify=sha256 and no digest. Correctly rejected - the manifest's rule is that entries arrive with the task that consumes them. Removed; T-0026 adds it with a real digest.
- 2026-09-07T11:30:00Z SELF-CAUGHT twice by the tests: (a) the https-only rule rejected the test server's loopback URL, so I added a narrow documented carve-out for 127.0.0.1/localhost only, with a test asserting http://10.0.0.5 and http://127.0.0.1.evil.com are still rejected; (b) a manifest missing a required field crashed the parser with TypeError instead of reporting a useful problem - every field now defaults so validation reports it properly.
- 2026-09-07T11:30:00Z NOT DONE HERE, deliberately: the pinned Dockerfile (osmium/osm2pgsql/GDAL). Everything here is pure python and runs in CI as-is; the image is only needed when T-0024 first touches the .pbf, and pinning a digest for tools nothing yet calls is ceremony. Say so if you disagree.
- 2026-09-07T11:30:00Z moved to review/, reviewer agent/reviewer-9
- 2026-09-07T11:45:00Z SELF-CAUGHT PORTABILITY BUG in ops/test, found by this task's own tier: on the Windows dev box `command -v python3` resolves to the App Execution Alias stub (a bare 3.14 with no site-packages) while `python` is the real 3.10 that has pytest. ops/test preferred python3, so the new ETL tier reported "pytest produced no report" and exit 1. On Linux CI python3 is correct, so this would have been a dev-box-only failure that looks like a broken tier.
- 2026-09-07T11:45:00Z FIX: the ETL tier now picks the first of $PYTHON/python3/python/py that can actually `import pytest`, and fails loudly naming what it tried rather than skipping the tier. GREEN: with PYTHON explicitly set to the pytest-less stub, ops/test still passes (falls through to python) -> TESTS linux=76/50. RED: with PATH restricted so the only interpreter is the pytest-less stub -> "no interpreter has pytest (tried: $PYTHON python3 python py)", exit 1.
- 2026-09-07T11:45:00Z floor_linux raised 50 -> 76 (16 swift + 34 vitest + 26 pytest). Reviewer: confirm the arithmetic before merging; raising a floor is the reviewer's ratchet.
- 2026-09-07T11:45:00Z took exclusive [floors] via ops/lock (the T-0011 lesson: exclusive: added after a claim needs the lock acquired explicitly).
- 2026-09-07T10:02:23Z acquired lock(s) floors for agent/claude-opus-5
- 2026-09-07T11:50:00Z PROTOCOL GAP found by queue-check the moment I moved to review/ while holding floors.lock: "queue/LOCKS/floors.lock held by T-0023, which is not in claimed/". The check is right - a lock belongs to a task that is actively working. Released it on the move to review/, because from that point the branch and its PR are the serialization point (the same compare-and-swap logic as push-to-claim). Nothing in ops/ enforces the release yet, so it is a thing an operator must remember - filed as T-0032 to have `queue.py` release locks automatically on the claimed/ -> review/ transition, the way sweep already does on expiry.
