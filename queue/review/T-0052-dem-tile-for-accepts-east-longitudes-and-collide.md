---
id: T-0052
title: dem.tile_for accepts east longitudes and collides with a Bay Area tile, plus two smaller T-0026 findings
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T20:46:52Z
lease_expires_at: 2026-09-07T22:46:52Z
worktree: null
branch: task/T-0052
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-35
depends_on: [T-0026]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Three findings from agent/reviewer-31's PASS on T-0026. None blocked it; all are real.

**1. MEDIUM — `services/etl/etl/dem.py`: `tile_for` ignores the hemisphere.**
`tile_for(38.0, 122.5)` — that is 122.5 degrees EAST, in China — returns `n38w123`, which is the Bay Area's
own tile. The name is built from `abs(lon)` with no sign check, so an eastern longitude silently collides
with a western tile and the sampler returns real elevation for entirely the wrong continent.

Unreachable today: the region bbox is fixed and every longitude in it is negative. That is exactly why it is
worth fixing now rather than later — the guard costs one comparison, and the failure it prevents is the
hardest kind to notice, a plausible number from the wrong place. Same argument as the ceil-versus-floor bug
the tests already cover.

- Refuse any longitude that is not in the western hemisphere, or build the name from the sign rather than
  from `abs`.
- Demonstrate red with `tile_for(38.0, 122.5)` and a southern-hemisphere latitude.

**2. LOW — `services/etl/tests/test_terrain_fixture.py:14`: stale numbers in a docstring.**
It says the mountain roads score "14.6% and 8.3%". Those were the pre-smoothing values from commit `68c193d`;
`e0166e7` re-recorded the fixture with 3x3 smoothing and they are now 13.65% and 10.47%. The docstring is
prose explaining why the fixture uses mapper geometry, so it is not load-bearing, but a comment that states
numbers the file no longer produces is the beginning of a comment nobody trusts.

**3. DESIGN NOTE — `terrain.smooth3x3` has no production caller, and `dem.sample()` is still callable.**
`sample_smoothed` is what built the fixture, but nothing stops a future caller reaching for the unsmoothed
`sample()` — which is the gap T-0026 already fell into once, where `smooth3x3` was written, tested and never
wired in. reviewer-31 flagged it for T-0030's review rather than as a defect here.

Decide one of: make `sample()` private, have `smooth3x3` used by whatever consumes a grid, or leave both and
write down when each is correct. Any is defensible; silence is not, because the last time this was left
implicit the smoothing simply was not applied.

## Log
- 2026-09-07T20:46:52Z claimed by agent/unknown; lease until 2026-09-07T22:46:52Z

- 2026-09-07T22:40Z claimed and fixed by agent/claude-opus-5, stacked on task/T-0026 (which owns dem.py).
  All three of agent/reviewer-31's findings.

  **1. MEDIUM, the east-longitude collision - fixed and demonstrated red.** `tile_for` built the name from
  `abs(lon)`, so `tile_for(38.0, 122.5)` - 122.5 degrees EAST, in China - returned `n38w123`, the peninsula's
  own tile, and the sampler would have returned real elevation for the wrong continent. `tile_for` now
  refuses anything that is not northern AND western and builds the name from `-lon` rather than `abs(lon)`;
  the western-hemisphere results are unchanged because `-lon == abs(lon)` there, which is why the eight
  existing corner cases still pass untouched.

  Four new tests: east longitudes, southern latitudes, the equator and prime meridian, and one that matters
  more than the other three - `test_the_hemisphere_guard_does_not_lean_on_the_tile_set` monkeypatches two
  extra names into TILES and shows the guard still refuses. That is the honest statement of why this was
  worth fixing while unreachable: today TILES membership is what actually stops the collision, and it stops
  stopping it the moment a second region is added.

  RED demonstrated properly rather than asserted. Reverting the guard to the original `abs(lon)` line:

      guard reverted to abs(lon):  RED  (FAILED ...::test_the_hemisphere_guard_does_not_lean_on_the_tile_set)
      pre-existing tile tests:     still green
      dem.py restored byte-identical
      green suite: exit 0

  The second line is the part worth having. It shows the four new tests fail because of the guard
  specifically, not because reverting it broke the module generally - a red demo that takes everything down
  with it proves much less than it looks like it proves.

  **2. LOW, the stale docstring - fixed, and the reason it drifted written down.** `test_terrain_fixture.py`
  said the mountain roads score "14.6% and 8.3%". Measured from the committed fixture in the pinned image:
  Old La Honda 13.65%, Skyline 10.47% - exactly what reviewer-31 reported, re-derived rather than taken on
  trust. Those were the pre-smoothing values from `68c193d`; `e0166e7` re-recorded with 3x3 smoothing and the
  prose was never updated. Corrected, with a parenthetical saying what happened and pointing at
  `TestTheRecordedSummariesStillHold`, which recomputes and is therefore what actually holds those numbers.

  **3. DESIGN NOTE - answered with a decision, and honestly labelled.** reviewer-31 asked for one of: make
  `sample()` private, wire `smooth3x3` into something, or write down when each is correct. I chose the third,
  because the first breaks `sample_smoothed`, which is built on `sample`, and the second would invent a
  production caller that T-0030 is going to write properly.

  `sample`'s docstring now states which function is correct for which job: `sample` for a single exact
  reading, `sample_smoothed` for ANY road profile and therefore for anything feeding `elevation_gain`,
  `relief` or `grade_percent`. It also says plainly that a comment guards nothing (CLAUDE.md) and names what
  does: `TestSmoothedSampling` already pins that `sample_smoothed` averages its nine cells and that `sample`
  does not, so a future edit that quietly makes the smoothed path unsmoothed goes red. The real enforcement
  point is T-0030's production caller - that is where a reviewer should check the smoothed path is the one
  being used, and it is now written where they will look.

  I did not add a test that `smooth3x3` has a caller. It does not have one yet and inventing one to satisfy a
  test would be worse than the gap.

  **Verification** - pytest in the pinned `scenic-etl` image, the rest from the worktree:
    `pytest -q tests/`   -> 237 passed, 1 skipped
    `ops/test`           -> `TESTS linux=287/76 ios=skipped failed=0 skipped=0` / `OK`
    `ops/check-pins`     -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`
    `ops/queue-check`    -> `QUEUE OK (50 tasks)`
  dem.py 179 lines, test_dem.py 257 - both under the 300 cap.

  Note for whoever runs `ops/test` in a fresh worktree: it first failed here with `FAIL: services/api exists
  but vitest produced no report`, which is T-0040's misleading message for an absent `node_modules`. `npm ci`
  in services/api fixes it. T-0040 is still in queue/ready/ and this is a second sighting of it.

  **What to attack.** The guard refuses `lat <= 0` and `lon >= 0`, so it also refuses the equator and the
  prime meridian outright rather than treating them as edges of a valid tile. That is right for 3DEP's naming
  and irrelevant to this region, but it is a judgement and I have not proven it against USGS's own
  convention for a tile at the meridian. Second: `tile_for` still returns a name for any northern-western
  point and leans on TILES to reject the rest, so the arithmetic is only checked for the eight tiles we
  have - a ninth tile added to the set gets no boundary test for free.
