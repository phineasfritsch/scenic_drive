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

- **agent/reviewer-23, FAIL.** Re-ran everything rather than trusting the log. Full detail below; headline:
  the counting and bounds machinery is sound and independently reproducible, but the bbox itself does not
  cover what its own comment claims, and by a large margin - not "a few extra square kilometres."

  **What was re-derived (not taken on trust):**
  - Synced `~/sd` (WSL) to `origin/task/T-0024` (`f8b202a`, matching the Windows worktree HEAD), confirmed the
    1.33 GB `california-osm.pbf` was already present and `md5sum`-identical to the manifest's byte count, and
    confirmed the host WSL shell has **no `osmium` on PATH at all** (`osmium: command not found`) - so any
    successful run only could have gone through `scenic-etl` (image id `9772f436f6f6`, built from this
    Dockerfile 51 min prior). `extract.py`'s `--no-docker` fallback is opt-in and the default path hard-fails
    (rc=2) if `docker` is missing rather than silently using a host binary - confirmed by reading `extract.py`
    lines 168-172, not just asserted.
  - Ran `bash ops/etl-extract` cold (fresh `work/` dir) end to end: reproduced **all 19 recorded counts
    exactly**, byte-for-byte matching `regions/sfbay/region.json`'s `counts` block. `BOUNDS OK`, `etl-extract
    rc=0`.
  - Independently re-verified 5 of the 19 classes with raw `osmium tags-filter` + `osmium fileinfo -e -j`
    calls run by hand, outside `etl/`'s own code, reading the JSON myself:
    - `motorway` (pure `w`): `w/highway=motorway,motorway_link` -> `fileinfo` reports `ways: 19515,
      nodes: 121202`. The code reads only `ways`; the 121,202 referenced-geometry nodes are correctly never
      summed in. Matches recorded 19,515.
    - `beach` (mixed `nw`, `services/etl/etl/tagfilter.py:38`): `n/natural=beach` -> `nodes: 63`;
      `w/natural=beach` -> `ways: 335, nodes: 10708` (the way's geometry, correctly ignored). 63 + 335 = 398,
      exactly the recorded count. This is the mechanism that makes the naive combined-`nw` filter wrong (it
      would read as tens of thousands, not 398) - confirmed the failure mode, not just the fix.
    - `park` (mixed `wr`, `tagfilter.py:39`): `w/leisure=park` -> `ways: 5486`; `r/leisure=park` ->
      `relations: 184, ways: 784` (referenced member ways, correctly ignored). 5486 + 184 = 5670, exactly the
      recorded count.
    - `service` (pure `w`, the largest class): `w/highway=service` -> `ways: 473124, nodes: 2404837`. Matches
      recorded exactly; 2.57x `residential`, which is ordinary for US OSM tagging (every driveway and parking
      aisle is `highway=service`) - plausible, not a sign of a broken filter.
    - `road` (pure `w`, `n=5`): `w/highway=road` -> `ways: 5`, matching recorded. Dumped the 5 ways with
      `osmium cat -f opl` and read their tags: 3 are unreclassified TIGER import remnants
      (`tiger:cfcc=A41`, `tiger:reviewed=no`) tagged `tiger:county=Lake,%20CA`, one is a flagged
      "reclassify this" edit (Northgate Boulevard), one is a bare `highway=road` with no other tags. All 5 are
      real, currently-tagged `highway=road` ways, not an artifact of a broken filter - `road: 5` is correct.
    - Together this exercises all three counting shapes the brief asked to attack (`w`-only, `nw`, `wr`) and
      confirms `count_class` (`services/etl/etl/extract.py:67-97`) sums the right two tallies for the mixed
      classes without double-counting either the referenced-node or referenced-way geometry osmium keeps.
  - Ran the RED/GREEN cycle myself, in WSL, on the real pipeline:
    - RED 1 (`motorway` deleted from `WAY_CLASSES`): `etl-extract` exited in **0.08s**, rc=2, message
      `motorway is missing from WAY_CLASSES - routing needs it even when it scores 0` - the structural check
      fires before osmium starts, as claimed.
    - RED 2 (`motorway_link` dropped, `motorway` kept): full run, `motorway: 8238 vs recorded 19515 (-57.8%,
      +/-15% allowed)`, `etl-extract rc=4`, and `bash ops/sane` in the same tree printed
      `bounds    FAIL   region counts out of band: ...` and `SANE FAIL exit=4`, rc=4. Exact match to the log.
    - GREEN (restored `tagfilter.py`, fresh full run): all 19 classes back to the recorded values,
      `etl-extract rc=0`, `ops/sane` -> `SANE OK` rc=0.
    - `git status --short` in `~/sd` after the full cycle is empty - the restore was clean.
  - Attacked `checkbounds`/`ops/sane`'s failure modes directly (not just by reading the code), all in WSL
    against a real `work/sfbay/meta.json`:
    - Truncated `meta.json` (`head -c 20`): `checkbounds` rc=2 ("cannot read ... Unterminated string"),
      `ops/sane` -> `bounds FAIL cannot check region counts: ...`, **exit=4**. Not a silent pass.
    - `meta.json` valid JSON but `counts` key removed: `checkbounds` rc=2 ("carries no counts"), `ops/sane`
      exit=4.
    - A second `work/ghostregion/` directory with no matching `regions/ghostregion/region.json`: `checkbounds`
      correctly evaluates both (`max(rc)` across regions, `etl/checkbounds.py:59-67`), reports
      `ghostregion: [Errno 2] No such file or directory: '.../regions/ghostregion/region.json'` alongside
      `BOUNDS ok sfbay: ...`, and `ops/sane` still exits 4 overall - one bad region does not get averaged away
      by a good one.
    - `road: 5`'s exact pass/fail boundary (`services/etl/etl/counts.py:61-66`, `SMALL_CLASS=20`,
      `tolerance=0.15`): `slack = max(1, round(5*0.15)) = 1`, so 4-6 pass and everything else (including 0,
      i.e. the class silently going empty) fails. Worked this out by calling `check_bounds` directly for
      `got` in 0..10. This is the right answer for a 5-object class: a percentage band would be noise either
      way, and +/-1 still catches a total collapse.
    - Confirmed separately (unit tests, re-read not re-run since they need no osmium):
      `test_a_class_that_vanished_is_named_as_missing_not_as_minus_100_percent` and
      `test_an_unexpected_new_class_is_reported_rather_than_accepted` in `test_counts.py` - both hold.
  - `bash ops/test` on the Windows worktree (after `cd services/api && npm ci --no-audit --no-fund`):
    `TESTS linux=152/76 ios=skipped failed=0 skipped=0` / `OK` - matches exactly.
  - `bash ops/check-pins`: `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`.
  - `bash ops/queue-check`: `QUEUE OK (45 tasks)`.
  - `bash ops/sane` (Windows worktree, nothing built here): `bounds skip no extract built here`, `SANE OK` -
    the skip path is real and distinct from a pass on data, and never writes anything (read through the whole
    script; no file is opened for writing anywhere in it).

  **Findings:**

  1. **CRITICAL** - `services/etl/regions/sfbay/region.json:19` (`max_lon: -121.2`), contradicted by its own
     `_comment_bbox` at line 22 ("... east to the Altamont"). Altamont Pass, the boundary the comment names,
     is at lon **-121.658** (Alameda/San Joaquin county line, `37.746,-121.658`). The committed `max_lon` of
     `-121.2` sits **0.46 degrees (~40 km) further east** - past Altamont, past all of Tracy, and to within
     0.09 degrees (~8 km) of downtown Stockton.
     - Verified directly, not by distance math alone: filtering the *unfiltered* regional cut
       (`work/sfbay/sfbay.osm.pbf`, before the highway/POI tag pass) for `n/place=city,town` returns both
       `name=Tracy` at `-121.420139,37.7385507` (population 98,337 per the OSM tag) and `name=Stockton` at
       `-121.290779,37.9577016` (population 305,658) - both **inside** the committed bbox. Neither city is in
       the nine ABAG counties this region is supposed to represent.
     - Quantified the effect: re-extracted the strip from Altamont Pass's longitude to the current east edge
       (`--bbox -121.658,36.85,-121.2,38.92`, i.e. everything the "east to the Altamont" comment says should
       not be there) out of the same regional cut. That strip alone contains **1,114,887 of 4,689,402 ways
       (23.8%)** in the unfiltered regional extract. Filtering just that strip for the three biggest reported
       classes: `service` 124,303 of the recorded 473,124 (26.3%), `residential` 52,519 of 183,831 (28.6%),
       `motorway` 4,365 of 19,515 (22.4%) - all attributable to San Joaquin Valley sprawl east of the pass,
       not the Bay Area. This is not "a few extra square kilometres of graph" (the comment's own words); it
       is roughly a quarter of every major way class.
     - A smaller version of the same pattern exists on the north edge: a strip from the Sonoma/Napa-Lake
       county line (~38.75 deg, confirmed against Middletown, Lake County at 38.7525 deg and the Sonoma AVA
       regulation's stated county-line latitude of 38 deg 45') up to the committed `max_lat` of 38.92 contains
       168,877 of 4,689,402 ways (3.6%) - smaller, but the same shape of overreach, and consistent with the
       3 of 5 `highway=road` ways above being tagged `tiger:county=Lake,%20CA`.
     - Failure scenario: any corpus, routing graph, or curation step built from this region's committed
       counts is silently importing a quarter of its major-class content from Tracy/Stockton residential and
       service streets that are not scenic Bay Area driving and were never meant to be in scope. A future fix
       that correctly tightens `max_lon` back toward Altamont Pass will *legitimately* drop ~25% of
       `service`/`residential`/`motorway` and blow straight through the 15% bounds tolerance - i.e. the
       recorded baseline this task is handing off is already the wrong shape for `check_bounds` to gate
       against. This needs a real bbox fix (or an explicit, argued decision to keep Stockton in scope,
       which contradicts the file's own comment) before this baseline is trustworthy.
     - Not a counting or bounds-logic bug - `check_bounds`, `tagfilter`, and `extract.py` all did exactly what
       they were built to do, correctly, on a rectangle that reaches further than its own author's stated
       intent.

  2. **MINOR** - this task's own Log entry above, and (transitively) the task prompt handed to review, state
     `python -m pytest -q tests/` -> `100 passed`. Re-ran the identical command on the Windows worktree
     (`git` present, so no skip): `102 passed` in `services/etl/tests/` (`test_counts.py` 18,
     `test_dockerfile.py` 9, `test_fetch.py` 9, `test_manifest.py` 19, `test_region.py` 18,
     `test_tagfilter.py` 21, `test_verify_failures.py` 9 = 103... collected 102, one file's count included a
     parametrize block already counted per-case; exact figure from `pytest -v`: `collected 102 items`,
     `102 passed`). Inside the pinned Docker image (no `git` binary) it's `101 passed, 1 skipped` -
     `tests/test_manifest.py:47` skips itself when `git` is unavailable. Either way the true number is 101-102,
     not 100; the suite is fully green either way, so this is a log-accuracy nit, not a code defect, but it is
     exactly the kind of small unverified number the brief asked this review to stop trusting.

  **Not re-derived, taken on trust:** the Geofabrik fetch itself (`ops/etl-fetch-inputs`, 4m01s, the input was
  already present and md5-verified before this review started; re-fetching a 1.3 GB file to re-prove a
  publisher's own md5 sidecar was judged not worth the bandwidth) and the `services/etl/Dockerfile` apt
  package pins (osmium-tool's actual upstream version was not independently cross-checked against Ubuntu
  24.04's archive).

  **Verdict: FAIL.** The counting, bounds-checking, and `ops/sane` integration are solid and reproduced
  exactly under independent re-derivation. The blocking problem is finding 1: the shipped `region.json` bbox
  does not match its own stated design intent and pulls in roughly a quarter of several major feature classes
  from outside the Bay Area, which makes the recorded counts an unsound baseline for the bounds check this
  task exists to add. Left in `queue/review/` for the owner.

### 2026-09-07 - owner response to reviewer-23: the bbox was wrong and the measurement proved it twice

**CRITICAL accepted in full.** `max_lon` was -121.20 while Altamont Pass sits at -121.658, so the extract
reached about 40 km past the boundary the file's own comment claimed. reviewer-23 did not assert this - they
pulled the place nodes out of the unfiltered regional cut and found `name=Tracy` and `name=Stockton`, neither
in the nine ABAG counties, then quantified the strip beyond the pass at 23.8% of all ways, 28.6% of
residential, 26.3% of service and 22.4% of motorway.

Nothing in the pipeline failed. It ran, wrote a valid PBF, and produced plausible numbers. The failure was
that the recorded baseline `ops/sane` gates against described a different region than the one named - and, as
they pointed out, a later correct fix would then have blown the 15% tolerance and looked like the regression.

**Fixed:** `max_lon` -> -121.55, about 9 km east of the pass. The comment now carries the measurement, so the
next person argues with a number rather than a claim.

**New guard, demonstrated red against the old value.**
`test_the_bbox_does_not_reach_into_the_central_valley` asserts Tracy, Stockton, Modesto and Sacramento are
outside the box, and `test_the_bbox_actually_contains_the_places_the_product_promises` now includes Altamont
Pass itself. With `max_lon` put back to -121.2:

    FAILED tests/test_region.py::TestTheCommittedRegion::test_the_bbox_does_not_reach_into_the_central_valley
    E    assert not True                                 exit 1

**Counts re-recorded from a clean run, and the drops confirm the diagnosis independently:**

                        before     after    change    reviewer-23 measured
      residential      183,831   135,776    -26.1%    -28.6%
      service          473,124   361,259    -23.6%    -26.3%
      motorway          19,515    15,572    -20.2%    -22.4%
      all ways               -         -    -23.5%    -23.8%

They measured the contaminated strip by counting place nodes inside it; this measures it by removing the
strip and counting what is left. Two different methods, one answer. That is what makes the diagnosis right
rather than merely plausible.

`viewpoint` barely moves - 746 -> 739, -0.9% - which is its own small check. There are almost no viewpoints
on the Central Valley flats, and a bbox error that had thinned viewpoints proportionally would have meant
something other than a geographic over-reach.

Extract is now 247 MB rather than 300, filtered 51 MB rather than 64.

**Verified after, in the WSL clone at the pushed commit:**

    $ python3 -m etl.checkbounds   -> BOUNDS ok    sfbay: every recorded class within 15%     rc=0
    $ bash ops/sane                -> bounds ok / SANE OK                                     rc=0
    $ cd services/etl && pytest -q -> all pass (31 region tests incl. the two new guards)

**MINOR accepted:** the log said "100 passed" for the pytest suite; it is 102 on the Windows worktree and
101 passed / 1 skipped inside the image, where git is absent and the tracking test self-skips. The number in
the earlier entry was wrong; this one is measured.

Back to agent/reviewer-23 in `review/`. Worth re-deriving rather than trusting: the new counts come from one
run, and the whole point of the finding was that a plausible number is not a checked one.
