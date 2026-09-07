---
id: T-0024
title: ETL: Bay Area extract + tag filter, with per-class counts and bounds
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:07:44Z
lease_expires_at: 2026-09-07T20:07:44Z
worktree: ../wt/T-0024
branch: task/T-0024
exclusive: [scenic-index]
touches: [services/etl/, ops/sane, ops/etl-extract]
pins_affected: []
reviewer: agent/reviewer-23
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Geofabrik `california-latest.osm.pbf` -> `osmium extract` to the 9-county Bay Area bbox ->
`osmium tags-filter` to drivable ways + the POI allowlist. Prints a COUNT PER FEATURE CLASS and writes them to
`meta`, so `ops/sane` can assert bounds later (viewpoints >= 400 etc, per the plan's data gate).

RED: a filter that drops motorways entirely -> the drivable-way count falls outside bounds and sane exits 4.

## Log
- 2026-09-07T16:07:44Z claimed by agent/claude-opus-5; lease until 2026-09-07T20:07:44Z

- 2026-09-07 claimed by agent/claude-opus-5, holding the `scenic-index` lock; reviewer agent/reviewer-23.
  Branch stacked on `task/T-0038`, whose pinned image every osmium call in this task runs inside.
  The brief carried `exclusive: []`; the plan's parallelism map puts ETL, graph import, tile build and corpus
  publish behind one lock, so it was set to `[scenic-index]` BEFORE claiming rather than declared after.

- **The pure parts first.** `etl/region.py`, `etl/tagfilter.py` and `etl/counts.py` hold everything that can be
  wrong without a 1.3 GB download: bbox validation, the filter expressions, fileinfo parsing and the bounds
  arithmetic. 100 tests, none of which need osmium or docker. `etl/extract.py` is the only part that shells out.

- **The filter's load-bearing decision is what it does NOT drop.** motorway and trunk are kept. They score 0
  and the router penalises them, but excluding them at the extract stage does not make routes prettier, it
  makes every Bay Area commute over 15 km unroutable - and a missing way looks exactly like a way that was
  never there. `track` is kept for the same reason in reverse: `road_class == TRACK` is a zero-gate in the
  routing profile (P-SAFE-01), and a gate can only be tested against data that still contains the thing being
  gated. `tagfilter.problems()` fails on a routing-critical class deleted or emptied, and on a highway value
  claimed by two classes; five tests drive it red.

- **The real run.** `ops/etl-fetch-inputs` pulled Geofabrik's california-latest.osm.pbf (1,327,078,436 bytes)
  and verified it against the publisher's md5 sidecar in 4m01s - the first exercise of that verification path
  on a real file. Then, inside T-0038's digest-pinned image:

      extract   california-osm.pbf -> sfbay.osm.pbf  bbox -123.62,36.85,-121.2,38.92
                300 MB in 23s
      filter    sfbay.osm.pbf -> sfbay-filtered.osm.pbf  19 expressions
                64 MB in 14s

      motorway    19,515     trunk        5,009     primary      26,578
      secondary   51,556     tertiary    38,111     unclassified  8,319
      residential 183,831    living_st      323     service     473,124
      track       32,236     road             5
      viewpoint      746     peak         1,470     waterfall        91
      picnic_site  1,860     attraction     576     beach           398
      park         5,670     nature_res     611

  Way classes are ways; viewpoint, peak and waterfall are tagged nodes; beach, picnic_site and attraction sum
  their node and way tallies; park and nature_reserve sum ways and relations. ~19.5k motorway ways over nine
  counties is the right order of magnitude, which is the whole point of recording a number a human can argue
  with.

- **Two counting methods were tried first and BOTH produced a number rather than an error.** Worth recording
  because a number is what gets believed:

      1. Filter `nw/natural=beach`, total all three types. osmium tags-filter keeps the nodes a matching way
         refers to - correctly; the output has to stay a usable OSM file - so the node tally was tagged nodes
         PLUS way geometry. motorway came out as 140,717, which is roughly 7k ways and their nodes, and reads
         exactly like a fact.
      2. Add --omit-referenced to strip them. That leaves ways whose nodes are gone, and
         `osmium fileinfo --extended` computes a bounding box from node locations:
         "Geometry error: Invalid location. Usually this means a node was missing from the input data."

  One type at a time, reading only that type's tally, needs neither. Also: osmium has no `-q` flag on extract,
  tags-filter or fileinfo - the first real run died on it, and the flags were then read out of
  `osmium <subcommand> --help` inside the image rather than guessed a second time.

- **The demonstration the brief asks for, run against the real pipeline.**

  RED 1 - motorway deleted from WAY_CLASSES entirely. The structural check fires before osmium is started:

      extract: the tag filter is not structurally sound: motorway is missing from WAY_CLASSES - routing needs
      it even when it scores 0
      etl-extract rc=2

  RED 2 - the subtler edit, and the one the brief actually describes: keep `motorway` but drop
  `motorway_link`, which is what a "tidy up" looks like. The pipeline runs to completion and produces a valid
  PBF; the counts are what catch it:

      motorway: 8238 vs recorded 19515 (-57.8%, +/-15% allowed)
      BOUNDS FAIL  sfbay                       checkbounds rc=4
      bounds    FAIL   region counts out of band:   motorway: 8238 vs recorded 19515 (-57.8%, +/-15% allowed)
      SANE FAIL exit=4                         sane rc=4

  GREEN - restored, full fresh run:

      BOUNDS OK  19 class(es) within 15%       etl-extract rc=0
      bounds    ok     sfbay: every recorded class within 15%
      SANE OK                                  sane rc=0

  Exit 4 was already reserved in ops/sane's header for corpus/graph bounds; this is its first user.

- **ops/sane still never builds and never mutates.** The check reads what a build already wrote. It SKIPS
  where nothing has been built - ops/sane runs on machines that have never seen a 1.3 GB PBF - but a build
  that EXISTS and disagrees with its recorded counts fails, and "cannot tell" (unreadable meta.json, no counts
  recorded yet) fails too rather than passing quietly.

- **Verification** (`ops/test` and `check-pins` on the Windows worktree; the pipeline in WSL, since the plan
  puts ETL in ext4 and never on /mnt/c):

      $ cd services/etl && python -m pytest -q tests/   -> 100 passed
      $ bash ops/test        -> TESTS linux=152/76 ios=skipped failed=0 skipped=0 / OK
      $ bash ops/check-pins  -> PINS ok=10 skipped=0 pending=3 expired=0 failed=0
      $ bash ops/queue-check -> QUEUE OK

- **Not verified: CI.** GitHub Actions has not executed since ~15:11 UTC; a run reports "recent account
  payments have failed or your spending limit needs to be increased", so every job on every branch dies in
  seconds with zero steps. Everything above is local.

- Handing to agent/reviewer-23; state -> review. The reviewer should re-derive the counts rather than trust
  them: the fetch is 4 minutes and the extract about 5, and two of the three counting methods tried here
  produced a plausible wrong number rather than an error.
