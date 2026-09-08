---
id: T-0107
title: second region around UCLA, because the developer who has to drive the routes lives in Westwood
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T11:41:59Z
lease_expires_at: 2026-09-08T15:41:59Z
worktree: null
branch: task/T-0107
exclusive: []
touches: [services/etl/regions/, services/etl/etl/region.py, services/etl/etl/dem.py, services/etl/tests/test_dem_tiles.py, ops/etl-extract]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**The plan's success criterion is "the developer drives a route this app made and it was better than the
freeway." The developer is in Westwood. The corpus is 350 miles away.**

Every region artifact today is `sfbay`: the bbox, the recorded counts, the curated seeds, the fixtures, the
human gates. Human gate #1 is five real commutes driven by the person building this, and gate #2 is twenty
more. Neither can happen from Los Angeles against a Bay Area graph, and the plan's own risk table calls
route quality on the developer's own commute *the thing that kills the product*.

So this is not "add a second market". It is **moving the feedback loop to where the developer is**, which
is the difference between tuning the score against roads you can drive tomorrow and tuning it against
screenshots.

**What LA has that makes it a good scenic test bed** — arguably better than the Bay Area:

  * **Santa Monica Mountains**, 15 minutes from UCLA: Mulholland Drive, Topanga, Malibu, Latigo and Las
    Flores canyons. Dense curvature with real elevation, immediately adjacent to dense city.
  * **PCH**, the coastal case, where the road is straight and the score must still be high — a direct test
    that `E` is not merely a proxy for `M`.
  * **Angeles Crest (CA-2)**, an hour out: sustained mountain highway, the long-drive case.
  * **Palos Verdes**, the coastal-suburban case.
  * And the hard negative it shares with nowhere in the Bay Area: **the 405 and Sepulveda Pass**, where a
    scenic detour has to beat a freeway everybody already hates.

Do:

1. `services/etl/regions/socal/region.json` — id, name, counties, bbox. Proposed bbox, argued rather than
   asserted:

        min_lon -119.00   west past Leo Carrillo, so PCH and the Malibu canyons are whole
        max_lon -117.85   east to the far end of Angeles Crest
        min_lat  33.70    south past Palos Verdes
        max_lat  34.45    north over the San Gabriel crest

   1.15 x 0.75 degrees, comfortably inside `region.py`'s MIN_SPAN_DEG/MAX_SPAN_DEG and SMALLER than
   `sfbay`'s 2.07 x 2.07, so the fifteen-minute build promise holds.

2. **Do NOT invent the counts.** `region.json`'s counts block is described in its own comment as *"Recorded
   from a real extract, not invented"*, and `checkbounds` correctly returns 2 (`cannot tell`) for a region
   with none. Ship the region with no counts, and record them with `ops/etl-extract --record-counts` on a
   real extract. A fabricated baseline is worse than none: it would make `ops/sane` assert against a number
   nobody measured.

3. Everything region-scoped has to stop assuming `sfbay`. Grep for the literal before writing code — the
   region id appears in fixture paths, curated seed directories and at least one pin. Whatever is hard-coded
   is the actual size of this task.

4. `curated.yaml` for socal: the plan wants 30 seeds per region. Twelve good ones beat thirty padded — and
   for the human gate, the seeds that matter are the ones within 30 minutes of Westwood.

**Ordering.** The ETL chain (T-0023 through T-0028) has to merge first; those branches carry `region.py`,
the extract and the scoring modules. Filed now because the region choice changes what the fixtures should
be, and fixtures written for sfbay will otherwise have to be written twice.

**Not proposed: dropping sfbay.** The Bay Area fixtures encode real work — the Altamont bbox correction, the
recorded class counts, the flagship 280/Cañada/Skyline shape. Two regions also proves the pipeline is not
accidentally single-region, which is worth having before a third.

## Log
- 2026-09-08T11:41:59Z claimed by agent/claude-opus-5; lease until 2026-09-08T15:41:59Z

- 2026-09-08 — **the region exists, and building it found the reason a second region was impossible.**

  `services/etl/regions/la/region.json`: `-119.00, 33.70` to `-117.85, 34.45`. 1.15 x 0.75 degrees —
  deliberately **smaller** than sfbay's 2.07 x 2.07, so the fifteen-minute build promise holds. Every edge is
  argued in the file rather than asserted: west to keep the Malibu canyons whole (cutting at -118.9 severs
  Yerba Buena and Decker mid-canyon, and a road clipped in half scores as two short ones), east to the far
  end of Angeles Crest, south around Palos Verdes, north clear of the San Gabriel crest so the mountain
  highway is not truncated at its best part.

  **THE BLOCKER, which is the real finding here.** `dem.TILES` is a module constant naming sfbay's eight
  3DEP tiles, and `dem.tile_for` returns `None` for anything outside it. In any second region every point
  therefore has **no elevation** — absent, not wrong — and `elev_gain` and `relief`, two of the four signals,
  are silently zero. A second region was not a configuration change; it was impossible.

  `dem.tiles_for_bbox()` derives the set from a bbox. It walks the integer squares the bbox spans rather
  than sampling its corners, because a bbox wider than one degree has interior squares no corner is in —
  a corner-only version looks correct on any small region and drops the middle of a large one.

  **The derivation is checked against the list that predates it**, which is the only honest oracle available:

        derived for sfbay  minus  the hand-typed TILES  ->  {n37w124}
        the hand-typed TILES  minus  derived for sfbay  ->  {}

  It reproduces all eight, and its one extra is `n37w124` — the tile sfbay's own comment excludes as
  entirely ocean, which USGS 404s. That exception is pinned as a test so the derivation cannot quietly grow
  a ninth tile and have it read as the same known case.

        LA needs exactly: n34w118, n34w119, n35w118, n35w119

  **What is deliberately NOT done:**
  * **No counts.** sfbay's file says its counts are *"Recorded from a real extract, not invented"*, and
    `checkbounds` correctly returns 2 — *cannot tell* — for a region without them. A fabricated baseline is
    worse than none, because `ops/sane` would then assert against a number nobody measured.
  * **The four tiles are not in `inputs/manifest.yaml`.** Pinning them needs their sha256, which needs the
    download, which needs the pinned image. Faking a digest would defeat the manifest's entire purpose.
  * **`tile_for` still reads the constant.** Wiring it to the region is one line, and it is left undone on
    purpose: `dem.py` is under review right now on `task/T-0052` (PR #34) and a signature change would
    collide with a fix in flight. Sequenced, not forgotten.

  **Tests** (`services/etl/tests/test_dem_tiles.py`, 8 cases): the sfbay reproduction both ways, the LA set,
  north-west corner naming, interior squares on a wide bbox, a bbox touching a border not claiming the next
  square, the region file loading with no counts, and the bbox actually containing UCLA, Mulholland, Malibu
  Canyon, Angeles Crest and Palos Verdes — because a region that does not contain where the driver lives is
  the wrong box.

  **One of those expectations was mine and it was wrong**: I asserted a 3x3-degree box touches 12 squares.
  It touches 16 — it starts mid-square and ends mid-square. The code was right and the test was corrected,
  with the mistake left in the comment.

        services/etl  257 passed

- 2026-09-08 — **`touches:` widened to add `services/etl/etl/dem.py` and
  `services/etl/tests/test_dem_tiles.py`, and the pre-commit hook is why this entry exists.**

  It refused the first commit:

        pre-commit: services/etl/etl/dem.py is outside T-0107 touches: [services/etl/regions/ ...]
        pre-commit: refusing commit

  The original `touches:` assumed a second region was a configuration change — a new `region.json` and
  perhaps a flag. It is not: `dem.TILES` is a module constant naming one region's tiles, so the region
  cannot have elevation until that file changes. The hook caught the difference between what the task was
  filed as and what it turned out to be, which is what it is for.

  Worth noting the hook that ran was **this branch's**, not `main`'s. Until today `core.hooksPath` was an
  absolute path into the main checkout and every worktree ran main's hooks ([[T-0106]]); this refusal is the
  corrected configuration doing its job on the first commit after it.

- 2026-09-08 — **the region is real: extracted, counted, and the counts recorded from that run.**

  The gap this task deliberately left is now filled, the honest way round — the counts were measured, not
  typed. `california-latest.osm.pbf` was fetched (1.3 GB, md5-verified against Geofabrik's sidecar; nothing
  in this repository had ever fetched it) and cut:

        bbox -119.0,33.7,-117.85,34.45
        extract   312 MB in 50s
        filter    36 MB in 31s, 19 expressions
        total     2m32s, well inside the fifteen-minute promise
        meta      work/la/meta.json
        recorded  regions/la/region.json

  **The counts pass a sanity check they could easily have failed.** LA's bbox is 20% of sfbay's area, so
  every class should be denser - but *how much* denser is the test, and the pattern is exactly right:

        class          LA      sfbay   per-area ratio
        primary    45,530     26,578      8.51x     <- LA's arterial grid; the highest ratio, correctly
        motorway   17,390     19,515      4.43x     <- the freeway capital
        service   312,495    473,124      3.28x
        residential 99,685   183,831      2.69x
        park        2,580      5,670      2.26x
        viewpoint     302        746      2.01x
        track       8,138     32,236      1.25x     <- near parity
        peak          342      1,470      1.16x     <- near parity

  **Urban classes are several times denser and terrain classes are at parity.** That is what a correct
  extract of Los Angeles looks like against the Bay Area, and it is not what a broken filter or a wrong
  bbox looks like - either of those moves classes together, or moves one alone.

  (The sfbay column is its RECORDED counts, which [[T-0110]] shows are ~20-26% high because they predate the
  bbox correction. The true ratios are higher still; the shape of the comparison does not change.)

  `road: 3` in both regions is the same three ways - a class one mapper's afternoon from moving, noted
  because a count of three will drift.
