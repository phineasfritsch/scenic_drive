---
id: T-0052
title: dem.tile_for accepts east longitudes and collides with a Bay Area tile, plus two smaller T-0026 findings
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
