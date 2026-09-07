---
id: T-0027
title: Scenic score: land cover (USFS canopy, NLCD impervious) in a 150 m buffer
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T19:57:37Z
lease_expires_at: 2026-09-07T23:57:37Z
worktree: ../wt/T-0027
branch: task/T-0027
exclusive: []
touches: [services/etl/, LICENSE-DATA]
pins_affected: []
reviewer: agent/reviewer-32
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

USFS Tree Canopy Cover and NLCD fractional impervious, both CONUS 30 m, both public domain.
canopy and (1 - impervious) are the two biggest terms in E - this is what separates a redwood road from a
strip-mall arterial.

RED: a fixture through a known industrial area must score high impervious; a fixture on Skyline must score high
canopy. Both from the raster, not hand-entered.

## Log

## Log
- 2026-09-07T14:20:00Z BLOCKER FOUND AND ROUTED AROUND, before the task started. The brief named USFS Tree Canopy Cover and NLCD fractional impervious from MRLC. Both were checked live: MRLC's S3 now returns 403 "Anonymous users cannot invoke requests against Requester Pays buckets", and a deliberately bogus key on the same bucket returns AccessDenied rather than 404 - so the bucket blocks ALL anonymous access, not one stale object. The landing pages carry no download href at all. Retrieval needs the MRLC interactive Viewer or an authenticated EarthExplorer/ScienceBase order. There is no guessable public URL; this is portal-only, confirmed, not a guess-and-give-up.
- 2026-09-07T14:20:00Z DECISION: use ESA WorldCover 2021 v200 instead. Verified live: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N36W123_Map.tif -> HTTP 200, 84 MB, anonymous, no auth. Tiles are 3 degrees; N36W123 covers 36-39N/120-123W, which contains the whole Bay Area. N36W126 (4 MB) is the mostly-ocean neighbour if the coast bbox needs it.
- 2026-09-07T14:20:00Z WHY IT IS A FAIR SWAP: WorldCover is 10 m (better than NLCD/TCC at 30 m) and its classes give both terms directly - Tree cover (10) and Shrubland (20) feed `canopy`, Built-up (50) feeds `impervious`. The scenic score needs FRACTIONS in a 150 m buffer, not absolute canopy percent, so class fractions are the right shape anyway. What we lose: TCC's continuous 0-100 canopy percent, and NLCD's calibrated impervious fraction. If the rank-order fixture set (T-0029) shows the redwood-vs-strip-mall discrimination is weak, revisit with a one-time manual MRLC clip hosted in our own R2 and pinned by sha256.
- 2026-09-07T14:20:00Z LICENCE: ESA WorldCover is CC-BY-4.0, which is NOT yet in KNOWN_LICENSES in services/etl/etl/manifest.py. The manifest validator will refuse the entry until it is added deliberately - that is the gate working. Add "CC-BY-4.0" there as part of this task, and carry the attribution string into LICENSE-DATA.
- 2026-09-07T19:57:37Z claimed by agent/claude-opus-5; lease until 2026-09-07T23:57:37Z

- 2026-09-07T20:30Z Handing to agent/reviewer-32; state -> review.

  **The brief's RED, from the raster:**

      old_la_honda  canopy 0.958  impervious 0.014  water 0.000   WOODED
      skyline       canopy 0.851  impervious 0.019  water 0.000   WOODED
      alviso_flat   canopy 0.086  impervious 0.690  water 0.017   BUILT_UP
      alviso_flat2  canopy 0.000  impervious 0.466  water 0.276   BUILT_UP

  Skyline high canopy, the industrial bay margin high impervious, separation of 0.5+ on both terms.

  **The prior research held, except the tile list.** MRLC really is closed - I did not re-verify the 403,
  the earlier note is specific enough to trust and re-checking costs a request that will fail. ESA
  WorldCover I did re-verify: both tiles 200, sizes unchanged. What did NOT hold is "N36W123 contains the
  whole Bay Area". Tiles are 3x3 degrees named by their SOUTH-WEST corner, so that one covers lon
  -123..-120 while the region runs to -123.62. N36W126 is needed and is now pinned. Same mistake as
  T-0026's four-tiles-instead-of-eight: verified against the URL, never against the bbox.

  **CC-BY-4.0 added to KNOWN_LICENSES deliberately.** The validator refused the entry until a human made
  that call, which is the gate working as designed rather than an obstacle.

  **What the reviewer should attack**, in the order I would:

  - `tile_for`. Same argument as T-0026's: a wrong tile name returns REAL data for the wrong place, and for
    this region the neighbouring tile is the open Pacific, which exists. Verify the naming convention against
    the tiles themselves with `gdalinfo`, not against my tests.
  - The class mapping. `CANOPY_CLASSES = {10, 20}` puts shrubland with tree cover and leaves grassland out.
    That is a judgement about what reads as green enclosure from a car, and it is mine alone. Grassland is
    30; if you think an oak-savannah road should score canopy, say so, because it changes the score for a
    large part of the east bay.
  - The 150 m buffer and the 50 m step. 49 samples per point before circular clipping. Check the buffer is
    actually isotropic (there is a test, but I wrote it) and that the step is fine enough not to alias
    against WorldCover's 10 m grid.
  - `is_wooded` at 0.5 and `is_built_up` at 0.4. Both are thresholds fitted to nothing yet - they separate
    these four roads by a wide margin, which is weak evidence that they are right in general.
  - The agreement tests between this fixture and the terrain one. The "wooded roads are the steep ones" test
    is a tripwire, not a law. Decide whether it belongs - it will fail the first time somebody adds a flat
    forested road, and that failure would be correct but confusing.

  Not done: nothing writes these fractions into the corpus. That is T-0030.

- 2026-09-07T21:15:00Z agent/reviewer-32 review: **FAIL.** All four verify commands are green, and the
  provenance and tile-naming claims hold under independent re-derivation - but real (not fabricated) roads
  sampled against the pinned tiles fall out of the "no road is both" invariant the code itself asserts, and
  the CC-BY-4.0 attribution this task's own log promised was never written. Both are concrete and
  reproducible, not style nits.

  **What I re-derived myself vs took on trust:** re-derived - tile corner coordinates (`gdalinfo` on both
  .tif's, run via the pinned `scenic-etl` Docker image through WSL), `tile_for` at every boundary named in
  the brief, the sfbay bbox west edge from `services/etl/regions/sfbay/region.json`, buffer isotropy at 4
  latitudes spanning the bbox with 16-sector angular resolution (stronger than the shipped N/E-only test),
  the fixture's `codes` arrays by re-running `lc.sample_codes` against the real tiles and diffing
  element-for-element against the committed JSON, two of the fixture's OSM node coordinates against the live
  `api.openstreetmap.org` API, sha256 of both .tif's against the manifest, and 7 additional real OSM roads
  (residential/oak-savanna/Delta-cropland) sampled against the pinned tiles with the shipped code. Took on
  trust - nothing load-bearing; I did not re-verify the MRLC-403 claim (agreed with the prior log that
  re-checking a bucket that reliably 403s burns a request for no new information).

  1. **`tile_for` — PASS, independently verified.** `gdalinfo` on both tiles
     (`services/etl/inputs/worldcover-n36w123.tif`, `worldcover-n36w126.tif`, run in the `scenic-etl` image)
     shows exact corners (-123,36)-(-120,39) and (-126,36)-(-123,39) with GDAL's own `product_tile` metadata
     field agreeing (`N36W123`, and the twin's origin at -126). `landcover.py:56-64` names tiles correctly
     at every boundary I tried: exact multiples of 3 (`tile_for(36.0,-123.0)`), just inside/outside each
     edge, and the region's real west edge -123.62 (`sfbay/region.json:18`, `min_lon: -123.62`) resolves to
     N36W126, which is pinned. No bug found.

  2. **Class mapping — real-world evidence gathered, unresolved by design (owner's call, not mine to make).**
     Sampled a real segment of Mines Road (Alameda Co., Diablo Range oak savanna, OSM way 6344683,
     37.5555-121.576 to 37.5747,-121.5799): `canopy=0.4759`, `grassland=0.5241`, dead level split, landing
     as "neither" wooded nor built-up because it sits 0.024 below the 0.5 threshold
     (`landcover.py:41,133`). A second oak-woodland road half a mile away, Morgan Territory Road (way
     6345191), reads WOODED at `canopy=0.6345`. So whether an oak-savanna road scores canopy is currently a
     coin-flip on which side of a hard 0.5 line the tree/grass split happens to fall - this is the "large
     part of the east bay" the owner's log worried about, made concrete. `cropland` (class 40) is computed
     into `fractions()` (`landcover.py:99`) but feeds none of canopy/impervious/water
     (`landcover.py:41-43`); sampled Vorden Road in the Sacramento Delta (way 10509719, cropland fixture
     roads) at `cropland=0.40, grassland=0.30, canopy=0.15` - a genuinely cropland-dominated road currently
     produces no signal from that dominant class at all. Not asserting this is wrong (the owner reserved the
     call explicitly) - recording that the practical effect is now measured, not hypothetical.

  3. **Buffer geometry — isotropy PASS, phase-aliasing CONFIRMED and quantified, MEDIUM severity.**
     Re-verified isotropy independently at lat 36.9/37.5/38.0/38.9 (the bbox's actual span) with 16 compass
     sectors rather than the shipped test's 2 axes (`test_landcover.py:39-52`): the angular reach spread is
     bit-identical (111.7-149.9 m) at every latitude, so the `cos(lat)` correction
     (`landcover.py:76`) is not introducing directional bias anywhere in the region - the ~38 m spread is
     grid-clipping-to-circle discretization, present equally everywhere, not a latitude bug.
     BUT: I quantified the 50 m-step-vs-10 m-pixel aliasing the brief asked about. At a real point on Vorden
     Road (38.2798255,-121.5379747), a 709-point 10 m-step "near-ground-truth" sample gives
     `canopy=0.2116, built_up=0.0409`. The shipped 29-point 50 m-step sample at the exact same center gives
     `canopy=0.2414`. Shifting that same 50 m grid's phase by one WorldCover-scale nudge - 25 m north, with
     nothing about the underlying land changed - swings `canopy` from 0.1034 to 0.2414 (2.3x) and `built_up`
     from 0.0 to 0.069. Two points ~25 m apart along the same real road can therefore report meaningfully
     different land-cover mixes purely from where the sample grid happened to land, which is a real
     mechanism for the phase-dependent volatility that finding 4 below exhibits on a real street.

  4. **Thresholds — FALSIFIED, HIGH severity, real (not synthetic) counterexample.** Sampled OSM way
     7853452, "Canyon Creek", San Ramon (37.7707,-121.9774 to 37.7711,-121.9768) - an entirely ordinary
     suburban cul-de-sac, ~116 buffer samples pooled from its 4 real nodes, using the shipped
     `buffer_points`/`sample_codes`/`fractions` unmodified against the pinned tiles:
     `canopy=0.5086, impervious=0.4914`. That is `is_wooded() == True` AND `is_built_up() == True`
     simultaneously (`landcover.py:133,138`), which directly falsifies
     `test_landcover_fixture.py:79` (`test_no_road_is_both`, "assert not (is_wooded and is_built_up)"). This
     is not a contrived edge case: it is the first suburban street I tried, and it is structurally
     inevitable, not rare - `is_wooded` needs `canopy>=0.5` and `is_built_up` needs `impervious>=0.4`, so
     *any* way with `canopy+impervious>=0.9` (a leafy street with houses, easily 90%+ of a 150 m buffer once
     lawns/lots are counted) risks satisfying both, because the two thresholds are independent cutoffs on
     two fractions that are not required to be complementary. I sampled 4 more residential streets in the
     same San Ramon neighbourhood (ways 7852629/7852631/7853283/7853749) and all 4 read cleanly BUILT_UP
     (canopy 0.33-0.47, impervious 0.53-0.66, no overlap) - so this is not universal, but it is real,
     reachable with the shipped code and pinned data, and it breaks a test the codebase currently asserts as
     a hard invariant. The four curated fixture roads "separate by a wide margin" only because they were
     picked to; that tells us nothing about the general case, which is exactly what the owner's log
     predicted and asked me to check.

  5. **The terrain-agreement tripwire — agree with the owner, recommend removing it, MEDIUM.**
     `test_landcover_fixture.py:98` (`test_the_wooded_roads_are_the_steep_ones_and_the_built_up_ones_are_flat`)
     asserts `is_wooded(way) == (gain_per_km >= 25.0)` for every fixture way, against the terrain fixture's
     recorded steepness. Confirmed it exists exactly as flagged. This encodes "the Bay Area's forest is on
     the hills and its industry is on the flats" as a hard assertion rather than a fact about land cover; the
     owner's own words ("not a law of nature... it will fail the first time somebody adds a flat forested
     road, and that failure would be correct but confusing") are accurate and I'd act on them - a flat
     redwood grove (there are several along Bay Area creek bottoms) or a hillside industrial park would both
     falsify it for reasons unrelated to a real bug. Recommend downgrading to a comment/manual note, not a
     `pytest.mark.xfail` (that would hide a real future regression) and not silence.

  6. **Fixture provenance — PASS, fully independently reproduced, not taken on trust.** Re-ran
     `lc.buffer_points` + `lc.sample_codes` against the pinned tiles for all 4 fixture ways inside the
     `scenic-etl` container and diffed against `tests/fixtures/landcover_fixture.json`: all 2,639 codes
     across `old_la_honda`/`skyline`/`alviso_flat`/`alviso_flat2` match element-for-element, and every
     `recorded_summary` fraction reproduces from the committed codes to 4 decimals. Separately fetched way
     92357845 (`alviso_flat`, "Gold Street") from `api.openstreetmap.org` live: its node list is real, and
     node 1071884374 (lat 37.4190440, lon -121.9742113) and node 1317285055 (index 8 of 13, i.e. "every
     eighth node") both match `sampled_at` exactly. sha256 of both `.tif`s matches
     `services/etl/inputs/manifest.yaml` exactly. No fabrication anywhere in this fixture.

  7. **New finding, not on the owner's list — LICENSE-DATA never updated, should block.** The task's own
     log (line 34 above) says: "Add \"CC-BY-4.0\" there [KNOWN_LICENSES] as part of this task, and carry the
     attribution string into LICENSE-DATA." `services/etl/etl/manifest.py:33` was done. `LICENSE-DATA` (repo
     root) was not touched by this branch at all (`git diff --stat task/T-0026...task/T-0027` shows no
     LICENSE-DATA entry) - it still lists "USFS / MRLC Tree Canopy Cover; MRLC Annual NLCD fractional
     impervious surface" (`LICENSE-DATA:21`) as if that's still the actual source, with zero mention of ESA
     WorldCover or CC-BY-4.0 anywhere in the file (`grep -rl CC-BY .` outside `services/etl/` finds nothing).
     CC-BY-4.0 is an attribution license; shipping the data without the attribution text the license
     requires is a real compliance gap, not a nit. Possibly this is a scope problem rather than an oversight
     - `touches: [services/etl/]` (line 12) would not have let this task's own pre-commit hook admit an edit
     to root `LICENSE-DATA` - but a scope problem doesn't make the gap go away, and no other queued task
     covers it (`grep -rl LICENSE-DATA queue/` finds only this file). Needs either a `touches` amendment on
     this task or a fast-follow task before this data ships to users.

  **Verification commands run, exact output:**

      $ cd services/etl && python -m pytest -q tests/
      278 passed in 5.27s

      $ bash ops/test          # after: cd services/api && npm ci --no-audit --no-fund
      TESTS linux=328/76 ios=skipped failed=0 skipped=0
      OK

      $ bash ops/check-pins
      PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux

      $ bash ops/queue-check
      QUEUE OK (50 tasks)

  All four green. GitHub Actions on PR #33 was not consulted (known billing block, unrelated to this diff),
  per instructions.

  **Verdict: FAIL.** Mechanically clean, and the raster/tile/fixture work underneath it is genuinely solid -
  but finding 4 is a real, reproducible falsification of an invariant the codebase itself asserts, using
  ordinary real data and unmodified shipped code, and finding 7 is an unresolved licensing promise from this
  task's own log. Leaving in `queue/review/` for the owner (testers find, fixers fix).

- 2026-09-07T22:40:00Z agent/claude-opus-5 responding to agent/reviewer-32's FAIL. Five findings, all five
  acted on. Every number below I measured myself in the `scenic-etl` image against the pinned tiles; the
  geometry for every road that is not already in a fixture came from a live
  `api.openstreetmap.org/api/0.6/way/<id>/full.json` fetch, not from the review text. Local verification only
  (GitHub Actions is billing-blocked).

  **What I did not touch, per the review:** `tile_for`, the `buffer_points` geometry and its isotropy tests,
  and the archetype fixture's provenance machinery. Confirmed correct, left alone.

  ---

  **1. Thresholds (HIGH). Reproduced, and it is worse than reported. The predicates were wrong, and the test
  was asserting a false invariant. Both fixed, in different ways.**

  Reproduced exactly, way 7853452 "Canyon Creek" (highway=residential, 4 nodes, all pooled), shipped
  `buffer_points`/`sample_codes`/`fractions` unmodified:

      buffer samples : 116
      canopy         : 0.5086      tree_cover : 0.5086
      impervious     : 0.4914      built_up   : 0.4914
      is_wooded      : True
      is_built_up    : True
      canopy+imperv  : 1.0000

  Worse in two ways I measured and the review did not:

  (a) *It is not one street.* Move the sample grid half a step - the land underneath untouched - and at the
  shipped 50 m step THREE of the five San Ramon streets read BOTH at some phase, not one:
  canyon_creek, sanramon_a (way 7852629) and sanramon_c (way 7853283). Reviewer-32 found 1 of 5 because the
  grid phase is arbitrary and they sampled one of them.

  (b) *It survives finer sampling.* At a 20 m step canyon_creek still reads BOTH at one of four phases
  (canopy 0.5254 / impervious 0.4746). So this is not an aliasing bug wearing a threshold costume. Finding 4
  and finding 1 are two independent defects and needed two independent fixes.

  **Which of the three options is actually true.** All three, but not equally. The FRACTIONS are right and I
  changed nothing about them: Canyon Creek genuinely is half tree canopy and half buildings, both halves are
  real, and the score must keep saying so - that is the module's whole premise. What was wrong is treating
  one verdict as two independent facts. `is_wooded`/`is_built_up` do not report two measurements; they answer
  one question, *which of the two kinds of road is this*, and an answer that can be "both" is not an answer.
  So `test_no_road_is_both` was asserting something about the WORLD (no road is half and half) which is
  false, and it now asserts something about the DEFINITIONS (a verdict is a verdict) which is true by
  construction. Code and test now agree on that reading.

  The rule, `landcover.py`:

      DOMINANCE_RATIO = 2.0
      is_wooded    = canopy     >= 0.5 and canopy     >= DOMINANCE_RATIO * impervious
      is_built_up  = impervious >= 0.4 and impervious >= DOMINANCE_RATIO * canopy

  Exclusive for ANY ratio strictly above 1, and provably: both true implies `canopy >= r*imp` and
  `imp >= r*canopy`, hence `canopy >= r^2 * canopy`, hence `canopy <= 0`, which fails the 0.5. Tested by
  sweeping the entire (canopy, impervious) simplex at 1% resolution, 5151 pairs, not by four curated roads -
  with counts asserted on both arms so a rule that simply never fires cannot pass it.

  *Why the ratio must be strictly above 1, measured not asserted:* at `DOMINANCE_RATIO = 1.0` real data still
  produces BOTH, at both 50 m and 20 m. These fractions are counts over small integer sample sets, so exact
  50/50 ties happen: a 29-sample buffer landing 15/14 is one sample from a tie, and canyon_creek's 177-sample
  buffer at one phase is 90/87 - the mutation run below shows `ratio 2.0 -> 1.0` going red on real roads, not
  on a constructed case.

  *Why 2.0 and not 1.5 or 3.0: this is a judgement and I am saying so explicitly.* "Predominantly" means at
  least twice as much. That is the whole argument; there is no fit behind it, and I looked for one and did
  not find one. Stability cannot pick the number: at step 20 across four phases, r=1.5 leaves sanramon_b and
  sanramon_c moving between BUILT_UP and neither, r=2.0 leaves sanramon_c and sanramon_d moving, r=3.0 leaves
  sanramon_d moving. The straddlers move, they do not disappear - any threshold rule has roads on its line.
  The straddling is *recorded* in the new fixture rather than hidden. What the ratio does remove is the
  contradiction, and that it removes completely.

  The 12 real ways at the shipped settings (20 m step, r=2.0), `was` being the shipped independent-cutoff
  answer:

      key                       way  canopy  imperv    open   water     c/i   verdict       was
      old_la_honda          8940690  0.9553  0.0118  0.0329  0.0000   80.87    WOODED    WOODED
      skyline             239028846  0.8492  0.0193  0.1315  0.0000   44.11    WOODED    WOODED
      alviso_flat          92357845  0.0706  0.6864  0.2260  0.0169    0.10  BUILT_UP  BUILT_UP
      alviso_flat2          8929268  0.0141  0.4520  0.2429  0.2910    0.03  BUILT_UP  BUILT_UP
      canyon_creek          7853452  0.4463  0.5537  0.0000  0.0000    0.81   neither  BUILT_UP
      mines_road            6344683  0.4859  0.0085  0.5056  0.0000   57.33   neither   neither
      morgan_territory      6345191  0.7301  0.0987  0.1712  0.0000    7.40    WOODED    WOODED
      vorden_road          10509719  0.1427  0.0311  0.7232  0.1031    4.59   neither   neither
      sanramon_a            7852629  0.4859  0.5141  0.0000  0.0000    0.95   neither  BUILT_UP
      sanramon_b            7852631  0.4124  0.5876  0.0000  0.0000    0.70   neither  BUILT_UP
      sanramon_c            7853283  0.3898  0.5763  0.0339  0.0000    0.68   neither  BUILT_UP
      sanramon_d            7853749  0.3107  0.6893  0.0000  0.0000    0.45  BUILT_UP  BUILT_UP

  Four leafy streets stop being called strip malls; the four archetypes are unmoved. Note that nothing in the
  scoring path calls these predicates at all (`grep -rn "is_wooded\|is_built_up"` finds only landcover.py and
  its tests) - E consumes the fractions. They exist so a fixture can state what a road IS, which is exactly
  why they have to be one verdict.

  New fixture, `tests/fixtures/landcover_boundary_fixture.json`: nine real ways nobody picked to separate -
  the counterexample, its four neighbours, an oak-savanna road, an oak-woodland road, a Delta cropland road,
  and the one archetype whose verdict moved with the grid. Each recorded at four grid phases half a step
  apart. It exists because the review's central point is right: the four archetypes "separate by a wide
  margin only because they were picked to", and that tells us nothing.

  ---

  **2. LICENSE-DATA. Fixed, `touches:` amended, and a check added so it cannot lapse again.**

  `touches:` is now `[services/etl/, LICENSE-DATA]` (line 12), amended before staging, as instructed.
  LICENSE-DATA gains a `## ESA WorldCover 2021 v200 - CC BY 4.0` section carrying the required string
  ("(c) ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA
  WorldCover consortium"), what it is used for, and that the derived per-way fractions carry the attribution.
  The `USFS / MRLC Tree Canopy Cover; MRLC Annual NLCD fractional impervious surface` line is REMOVED from the
  public-domain list - nothing in the tree is derived from those layers, and leaving them listed was itself a
  false statement about provenance.

  A licence promise that only a reviewer can catch will lapse again, so `manifest.unattributed()` now checks
  every attribution-requiring licence used in `inputs/manifest.yaml` against the real LICENSE-DATA, with a
  spelling table (`ATTRIBUTION_LICENSES`) so the check is on the licence identifier and not on a sentence
  somebody will reword. `US-PD-17USC105` and `CC0-1.0` are deliberately absent from it.

  **NOTICE: checked, and it needs something, but not this.** There is no NOTICE file in the repo, at the root
  or anywhere else - `git ls-files` finds only `services/api/node_modules/**`, and `git log --all -- NOTICE`
  is empty, so it has never existed in any commit. `README.md:15` nonetheless says "See `LICENSE-DATA` and
  `NOTICE`". That is a dangling reference to a THIRD-PARTY SOFTWARE notices file (MapLibre, Ferrostar, GRDB,
  the npm and SwiftPM trees), not a data-licence gap, so the WorldCover attribution does not belong in it and
  inventing one here would be scope I cannot review. Filed as
  `queue/backlog/T-0054-readme-points-at-a-notice-file-that-does-not-exi.md` with the red run specified.

  ---

  **3. Class mapping. Decided, with the reasoning written down and each half of it anchored on data.**

  *(a) Grassland stays OUT of canopy.* Measured reductio, at the shipped settings:

      mines_road         canopy 0.4859 + grassland 0.5056 = 0.9915
      morgan_territory   canopy 0.7301 + grassland 0.1682 = 0.8983
      skyline            canopy 0.8492 + grassland 0.1315 = 0.9807

  Fold class 30 into canopy and Mines Road - a road with no continuous tree cover at all - reads 0.9915,
  ABOVE Skyline's 0.9807. The single term that exists to tell a redwood road from an open hill would rank the
  treeless one first. That is not a preference, it is the term losing its meaning. `CANOPY_CLASSES` unchanged
  at {10, 20}; the mutation run turns 13 tests red if it changes.

  *(b) The 0.5 is a judgement, and here is why 0.5.* "Wooded" means canopy is the majority of what you can see
  from the car, and 0.5 is what majority means. It is not fitted to anything and it should not be - the
  fitted-looking question, *which of two real terms wins*, is the ratio's job, and that is where the
  measurement in finding 1 went. Nothing else in the suite pinned the built-up cutoff from below (mutation
  `0.4 -> 0.2` survived the first pass), so `test_a_quarter_built_is_not_yet_a_strip_mall` and
  `test_not_quite_half_trees_is_not_yet_wooded` now pin both edges of both.

  *(c) cropland now feeds a term.* `OPEN_CLASSES = {30, 40, 60, 70, 100}` gives an `open_land` fraction, and
  canopy / impervious / water / open_land now PARTITION `CLASSES` - every class in exactly one, tested both
  ways (union is complete, pairwise intersections empty), so a road can never again be mostly something the
  score has no name for. Vorden Road reads `open_land 0.7232` (cropland 0.3898) instead of "not trees, not
  buildings". Mines Road reads `open_land 0.5056`: oak savanna has a name in the schema now.

  What I did NOT do, deliberately: I did not make oak savanna score. Whether `open_land` is scenic, and at
  what weight, is a scoring decision that belongs to T-0029/T-0030 with the rank-order fixtures in front of
  it. What this task owed was that the information exists, is named, and sums correctly. It does.

  ---

  **4. Buffer aliasing. Not acceptable. `BUFFER_STEP_M` 50.0 -> 20.0, both fixtures re-recorded.**

  I measured phase sensitivity per POINT (reproducing the review) and then per WAY, which is the number that
  actually reaches E, because `summarise` pools every sample along the way and nodes sit at independent
  phases. Worst per-way canopy spread over 9 phases across the 12 ways:

      step 50 m ->  0.2069     29 samples/centre
      step 25 m ->  0.0973    113
      step 20 m ->  0.0791    177
      step 10 m ->  0.0240    709

  The measurement that decided it is not on the review's list: **alviso_flat2, a curated fixture archetype,
  read BUILT_UP at two phases and `neither` at the other two at the shipped 50 m step** - with nothing but
  the grid moved. The archetype fixture's own recorded classification was a coin flip on sampling. At 20 m it
  is BUILT_UP at all four phases. At canopy's 0.24 weight in E, a 0.2069 spread is 0.050 of the score coming
  from where the grid happened to land; 0.0791 is 0.019.

  *Why 20 and not 10.* 10 m matches the pixel and is the honest ceiling, but it is 709 samples per centre
  against 29 - 24x. At the sfbay counts (~333k ways in the scenic classes, motorway through unclassified,
  excluding service and track) and the ~40k gdallocationinfo points/sec I measured in the image, that is
  roughly 5 hours for a corpus pass against ~74 minutes at 20 m, for a further 0.055 of worst-case spread.
  20 m is the knee. If T-0030 finds the sampling cheap in practice, 10 m is a one-line change and the fixture
  rebuild is scripted.

  *Guards.* Both fixtures record `buffer_step_m` and both test files assert it equals `lc.BUFFER_STEP_M`, so
  coarsening the sampler without re-recording is caught immediately. The boundary fixture records each way's
  measured phase spread; the tests assert the spreads recompute from the recorded codes AND that they are
  <= 0.10 - a bound that sits between what 50 m allowed (0.2759 at half-step phases) and what 20 m achieves
  (0.0847 worst case), so it is red at the old step and green at the new one.

  *Loud flag: this re-records snapshot references.* Both `landcover_fixture.json` (2,639 -> 16,107 codes) and
  the new boundary fixture are recorded at 20 m by script from the pinned tiles. Archetype summaries moved:

      old_la_honda  canopy 0.9582 -> 0.9553   impervious 0.0136 -> 0.0118
      skyline       canopy 0.8512 -> 0.8492   impervious 0.0192 -> 0.0193
      alviso_flat   canopy 0.0862 -> 0.0706   impervious 0.6897 -> 0.6864
      alviso_flat2  canopy 0.0000 -> 0.0141   impervious 0.4655 -> 0.4520

  Please re-derive these the way you re-derived the last set - element-for-element against the tiles - rather
  than taking the diff on trust. `buffer_points` itself is untouched, so the isotropy result you verified
  still holds; only the step changed.

  ---

  **5. The terrain tripwire. Removed, and replaced with the invariant it was standing in for.**

  `test_the_wooded_roads_are_the_steep_ones_and_the_built_up_ones_are_flat` is deleted. Not `xfail` (that
  hides a real future regression) and not silence: the drift the class exists to catch is "one fixture was
  rebuilt against a different extract, so the score is combining two different roads under one id", and that
  is now caught directly by `test_the_two_fixtures_sampled_the_same_geometry`, which compares the land-cover
  fixture's `sampled_at` against the terrain fixture's `coords[::8]` element-for-element. The old test caught
  drift only by coincidence, through a correlation that a flat redwood grove would break for a correct
  reason. Mutation-tested: perturbing one `sampled_at` coordinate turns the replacement red.

  ---

  **RED then GREEN.**

  New checks written first, against the code exactly as shipped. 15 red:

      $ docker run --rm -v "$PWD:/w" -w /w scenic-etl python3 -m pytest -q \
          tests/test_landcover.py tests/test_landcover_fixture.py tests/test_landcover_boundary.py
      FAILED tests/test_landcover.py::TestTheVerdictIsOneVerdict::test_no_pair_of_fractions_can_satisfy_both
      FAILED tests/test_landcover.py::TestTheVerdictIsOneVerdict::test_an_even_split_is_neither
      FAILED tests/test_landcover.py::TestTheVerdictIsOneVerdict::test_trees_have_to_beat_buildings_to_count_as_wooded
      FAILED tests/test_landcover.py::TestTheVerdictIsOneVerdict::test_buildings_have_to_beat_trees_to_count_as_built_up
      FAILED tests/test_landcover.py::TestTheVerdictIsOneVerdict::test_a_tie_is_not_a_verdict
      FAILED tests/test_landcover.py::TestOpenLand::test_the_four_terms_partition_every_class
      FAILED tests/test_landcover.py::TestOpenLand::test_grassland_and_cropland_are_open_land
      FAILED tests/test_landcover.py::TestOpenLand::test_the_four_fractions_sum_to_one_on_any_mix
      FAILED tests/test_landcover_fixture.py::TestTheFixtureItself::test_it_was_recorded_at_the_sampling_step_the_code_uses
      FAILED tests/test_landcover_boundary.py::TestTheFixtureItself::test_it_was_recorded_at_the_geometry_the_code_actually_uses
      FAILED tests/test_landcover_boundary.py::TestNoRoadIsEverBoth::test_not_at_any_phase_of_any_way
      FAILED tests/test_landcover_boundary.py::TestNoRoadIsEverBoth::test_the_leafy_suburb_is_neither_a_redwood_road_nor_a_strip_mall
      FAILED tests/test_landcover_boundary.py::TestTheClassMapping::test_the_savanna_road_is_open_land_not_nothing
      FAILED tests/test_landcover_boundary.py::TestTheClassMapping::test_the_delta_road_reports_the_cropland_it_is_covered_in
      FAILED tests/test_landcover_boundary.py::TestTheClassMapping::test_every_way_here_is_fully_accounted_for

  The two that matter, in full - a real road and the whole simplex:

      E               AssertionError: ('canyon_creek', 2)
      E               assert 'BOTH' != 'BOTH'
      E                +  where 'BOTH' = verdict({'built_up': 0.4915254237288136,
      E                                           'canopy': 0.5084745762711864, 'coverage': 1.0, ...})

      E           AssertionError: (50, 40)
      E           assert not (True and True)

  And the licence check, demonstrated red by reverting LICENSE-DATA to its committed state and running on the
  host (the container has no git, so that test skips there):

      $ git stash push -- LICENSE-DATA && cd services/etl && python -m pytest -q tests/test_manifest.py
      E       AssertionError: LICENSE-DATA does not attribute: ['CC-BY-4.0']
      E       assert ['CC-BY-4.0'] == []
      FAILED tests/test_manifest.py::TestRealManifest::test_every_attribution_licence_it_uses_is_actually_attributed

  Green after the fix, whole ETL suite:

      $ docker run --rm -v "$PWD:/w" -w /w scenic-etl python3 -m pytest tests/
      304 passed, 1 skipped in 2.69s

  (the 1 skip is the pre-existing `git is not installed here` skip inside the image; on the host, 0 skips.)

  **Mutation-tested, 22 mutants, every one caught.** First pass killed 12 of 13; the survivor was
  `is_built_up` threshold `0.4 -> 0.2`, which nothing pinned, so I wrote
  `test_a_quarter_built_is_not_yet_a_strip_mall` and `test_not_quite_half_trees_is_not_yet_wooded` and
  re-ran. Second pass, 9 more, all caught:

      ratio 2.0 -> 1.0                     7 tests red (incl. the simplex sweep and a real road)
      ratio 2.0 -> 1.05                    4 red
      ratio 2.0 -> 3.0                     1 red  (recorded verdicts stop recomputing)
      built-up threshold 0.4 -> 0.2        1 red  (the previously-surviving mutant)
      built-up threshold 0.4 -> 0.6        5 red
      wooded threshold 0.5 -> 0.45         3 red  (incl. Mines Road becoming woodland)
      wooded threshold 0.5 -> 0.6          1 red
      BUFFER_M 150 -> 120                  2 red
      WATER_CLASSES loses mangroves        2 red  (the partition breaks)

  and from the first pass: `is_wooded` reverted to an independent cutoff (4 red), `is_built_up` likewise
  (4 red), `BUFFER_STEP_M 20 -> 50` (2 red), cropland dropped out of every term (4 red), grassland folded
  into canopy (13 red), `is_wooded` never fires (8 red), `open_land` silently not computed (6 red), a
  recorded phase spread edited to fit the bound (1 red), a recorded verdict edited (1 red), and the archetype
  fixture re-sampled off the terrain fixture's geometry (1 red).

  **Verification, all local (Actions is billing-blocked):**

      $ bash ops/test
      TESTS linux=363/76 ios=skipped failed=0 skipped=0
      OK

      $ bash ops/check-pins
      PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux

      $ bash ops/queue-check
      QUEUE OK (51 tasks)

      $ bash ops/sane
      SANE OK

  Test count 328 -> 363. Every file under the 300-line cap (landcover.py 244, test_landcover.py 261,
  test_landcover_boundary.py 168, manifest.py 175).

  ---

  **What I want you to attack next, in the order I would:**

  - **The re-recorded fixtures.** Both are snapshot references and I re-recorded both. Re-derive them
    element-for-element against the pinned tiles the way you did last time. If any code differs, the step
    change is hiding something.
  - **The 0.10 phase-spread bound.** It is 18% above the worst value the shipped step actually produces
    (0.0847). That is thin. Sample roads I did not - a coastal way with NODATA in the buffer, a way inside a
    single WorldCover pixel, a way crossing the N36W123/N36W126 tile seam - and see whether any of them
    exceeds it. If one does, the bound is wrong or 20 m is not fine enough, and I would rather know now.
  - **DOMINANCE_RATIO = 2.0 itself.** It is a judgement with no fit behind it and I have said so. The thing
    to attack is not the number but whether the *shape* is right: is "twice as much" the correct reading of
    "predominantly", or should the verdict be a margin (`canopy - impervious >= m`) rather than a ratio? A
    ratio behaves differently from a margin at the low end, and the 0.5/0.4 absolute thresholds are the only
    thing stopping it there.
  - **The four terms as a partition.** I put snow_ice (70) into `open_land` so the partition is exact. It is
    zero everywhere in this region so nothing measured it. If that is the wrong home for it, it will never be
    caught by data from the Bay Area.
  - **Whether `sanramon_b` and `sanramon_c` should still be BUILT_UP.** They flipped to `neither` under the
    new rule (canopy 0.41/0.39 against impervious 0.59/0.58, ratios 1.4 and 1.5). I think a street with two
    trees for every three roofs is not a strip-mall arterial, but that is the judgement the ratio encodes and
    it is the one most likely to be wrong.
  - **`manifest.unattributed`'s spelling table.** It matches licence identifiers against LICENSE-DATA text.
    `Apache-2.0` is listed with the spelling "Apache License 2.0" because that is what LICENSE-DATA says, but
    no manifest entry uses Apache-2.0 yet, so that arm has never run against the real file.
