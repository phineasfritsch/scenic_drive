---
id: T-0119
title: ScenicKit RetraceDetector: a loop that drives the same road out and back is not a loop
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T14:21:47Z
lease_expires_at: 2026-09-08T16:21:47Z
worktree: .worktrees/T-0119
branch: task/T-0119
exclusive: []
touches: [Sources/ScenicKit/Loop/, Tests/ScenicKitTests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "swift test -> 30 tests in 4 suites passed, exit 0"
  - "python ops/mutate/retrace.py -> 12 caught by a named test, 1 trapped, 0 missed, exit 0"
  - "python ops/mutate/retrace.py --prove-vacuity -> 0 caught with the tests removed, exit 0"
---
## Brief

*"Just drive 45 minutes and come back"* is a paid feature, and the thing that ruins it is a route that goes
out along a road and comes back along the same road. GraphHopper's `round_trip` produces those regularly - it
optimises for a distance target and out-and-back is the cheapest way to hit one - so the check is ours,
applied to the geometry it returns, and a route that fails it is reseeded rather than shown.

The plan's parameters: **25 m cells, heading delta > 150 degrees, retrace < 15% of length.**

**No `Package.swift` change**: `Sources/ScenicKit/Loop/` is inside the existing target path.

## Log

    swift test --scratch-path .build-T0119
    Test run with 30 tests in 4 suites passed          exit 0

    python ops/mutate/retrace.py
    caught by a named test: 12   trapped: 1   compile-only: 0   MISSED: 0   of 13    exit 0

    python ops/mutate/retrace.py --prove-vacuity
    VACUITY PROOF OK: with no tests present, 0 mutations were reported caught        exit 0

### Four fixtures that were wrong, and what each one taught

The first harness run caught 6 of 10. None of the four misses was a defect in the detector; all four were
fixtures that could not see the thing they were named for.

**A concatenated route is not a route.** `parallelStreetIsNotRetrace` joined a northbound line to a
southbound line starting 120 m east. Concatenation inserts an implicit segment between them - a 1.4 km
diagonal running back across the outbound leg at a heading 175 degrees off it - and *that*, not the parallel
streets, produced 6.9% retrace and failed the assertion. The detector was right; the fixture described a
route no car could drive. Rebuilt as one continuous route: up, across the block, back down.

**An exact out-and-back cannot test the grid.** `cellsAreMetric` drove a route at three latitudes and
checked the verdict, which passes with the latitude correction deleted - because an exact retrace lands in
the same cell whatever shape the cell is. The real failure of an equatorial constant is that columns become
12.5 m wide at latitude 60, so a road driven out and back with any lateral offset lands in different columns
and is missed. That is invisible to any route fixture, so `cell(_:origin:)` and
`metersPerDegreeLongitude(at:)` were extracted and are now asked directly: 30 m north and 30 m east must be
the same number of cells away, at four latitudes.

**A mis-attribution can be exactly the right size.** `longSegmentsAreSampled` used one 500 m segment out and
one straight back. With one sample per segment both midpoints land in the same cell with opposite headings,
the whole return segment is attributed as retrace, and the fraction is 0.5 either way - the bug is invisible
because the wrong answer coincides with the right one. The fixture that separates them is asymmetric: out as
ONE 600 m segment, back as THREE 200 m segments, so midpoint sampling collides on only the middle one.

**Two passes cannot test what the third pass needs.** `allHeadingsAreRecorded` first crossed a junction at
90 degrees before a two-pass spur. That distinguished nothing: the spur's own cells still had 0 as their
first heading, so the return pass was caught either way, and one junction cell could not move the fraction.
Rebuilt as three passes over one road - out, back, out again, which is what a reseeded loop looks like when
the router keeps returning the same corridor. Every heading recorded gives about two thirds retrace; keeping
only the first gives about one third.

### Every mutation in my previous harnesses was structural. These are not.

A reviewer on T-0116 pointed out that all eight of that harness's mutations delete a guard or invert a
comparison, and **not one touches a number** - so the suite was blind to exactly the constants the plan
specifies. Applied here: `samplesPerCell`, `metersPerDegreeLatitude`, `cellSizeMeters`,
`oppositeHeadingDegrees` in both directions, and `maxRetraceFraction` all have mutations, and
`constantsArePinned` writes out the plan's three numbers so they have a witness rather than being reachable
only through their own symbols.

### `trapped` is a category, not a catch

Removing the non-finite guard makes `Int(nan)` trap. `swift test` exits non-zero, so a harness that scored on
exit code would call that a catch - but no assertion fired; the process died. It is now reported as
`trapped`: the suite did detect the mutation, and not through a check. Counting a crash as a passing
assertion would be the flattery this harness exists to avoid.

### The harness also had a bug, and the harness found it

One mutation reported `compile-only`. Applied by hand it compiles fine, exit 0 - the failure was a transient
scratch-directory collision with the reviewer agents building on this box at the same time. The build is now
retried once before a compile failure is believed. A transient failure silently reclassifying a real catch is
the same defect class as everything else here.

### Not done

No reseeding, no `areas` re-issue on the retraced edges, no seeded loop generation. Those need the router.
This is the property, and it takes a plain array of coordinates so it can be tested against exact shapes.

---

## Fix pass: the test written to catch a self-referential assertion was itself one

reviewer2-pr76 found no correctness bug in the detector and blocked on the suite. The finding:

`cellsAreSquare` placed its east probe at `origin.longitude + d / metersPerDegreeLongitude(at: lat)`, and
`cell()` then multiplied that offset back by the same function. **The two uses cancel exactly**, so
`cE.x = Int(floor((d / M) * M / 25)) = 1` for ANY definition of M - including a constant, which is the
mutation it was written to catch.

That test exists because an out-and-back fixture could not see the grid. It replaced one self-referential
assertion with another, one level down, in the same commit that describes the problem.

The probe offsets now come from a reference constant computed in the test. The grid mutation is still
caught, and `cE.x == 1` is asserted directly rather than only against `cN.y`.

    swift test                       30 tests passed                              exit 0
    python ops/mutate/retrace.py     12 caught, 1 trapped, 0 missed, of 13         exit 0

- 2026-09-08T22:10:00Z reviewer-pr76 returned FAIL with five findings, two of them in the SUBJECT rather than the suite. G2 is the one that matters and it is a real product defect, reached with no adversarial input.
- 2026-09-08T22:10:00Z **G2/G1: the verdict depended on where the grid's boundaries happened to fall.** The reviewer swept one fixed connector: 0 m -> f=0.498 (reject), 6 m -> 0.497 (reject), **12 m -> 0.0 (ACCEPT)**, 18 m -> 0.0, 24 m -> 0.0. The same piece of road, three answers. And reversing a route moved the grid by the 14 m between carriageways, flipping `isAcceptableLoop` outright. `let origin = points[0]` anchored the grid on whichever end the drive started from.
- 2026-09-08T22:10:00Z **I got the fix wrong twice, and this suite caught both.** (1) Half-cell grid phases, taking the worst of four: carriageways 14 m apart are 0.56 of a 25 m cell apart, which is WIDER than a half-cell shift, so the straddle survives every phase - the new sweep test failed against my own fix. (2) Searching the 3x3 neighbourhood: that reaches up to two cells, so a genuinely parallel street 40 m away started reading as the same road - the false positive that ruins an honest loop, caught by a test written for exactly that distance. **The fix that holds** uses the grid as an INDEX and the true distance as the measurement: the nine cells are searched to find candidates (every earlier sample within 25 m is guaranteed to be in one of them) and `Geo.distanceMeters(...) <= cellSizeMeters` decides. The radius is now set by geometry rather than by where a boundary fell.
- 2026-09-08T22:10:00Z **One of my new tests was itself vacuous, and the red demo is what exposed it.** The first phase sweep slid the whole fixture sideways - which does nothing once the grid is anchored on the route's own bounding box, because the grid moves with it. It passed against every implementation. Rebuilt with a variable-length approach leg, so the retracing pair sits at a varying offset FROM the anchor, and it then failed against the shipped code. That is this repository's signature defect committed inside a test written to close a different one, for the twelfth time this session.
- 2026-09-08T22:10:00Z **G5: finiteness was screened, range was not.** `Coordinate(latitude: 34.0689, longitude: 1e17)` is perfectly finite and made the cell arithmetic trap with `Fatal error: Double value cannot be converted to Int because the result would be greater than Int.max`. Added a range screen. It also subsumes the finiteness loop - `(-90...90).contains(.nan)` is false - which the harness now records rather than my deleting a guard on a safety path to make a score go green.
- 2026-09-08T22:10:00Z GREEN: `swift test` -> **35 tests in 5 suites passed**. `bash ops/check-pins` -> `PINS ok=11 skipped=0 pending=2 expired=0 failed=0`. `bash ops/queue-check` -> `QUEUE OK`. Line counts 180 / 249 / 144. The test file reached 377 lines and went over the cap, so the grid questions - which are a different question from "what shapes fool a detector" - were split into `RetraceGridTests.swift`.
- 2026-09-08T22:10:00Z **G3: the harness reported success having measured nothing**, and it had the trapped-counts-as-pass defect its siblings have. Both fixed. The pass condition is now `caught == len(MUTATIONS)`; `--prove-vacuity` requires `MISSED` to be COMPLETE, not merely `caught == 0`; the EQUIVALENT arm requires its mutants to go MISSED specifically; and SKIP is its own bucket, because a mutation that did not land means the harness is stale, which is the opposite of what MISSED means.
- 2026-09-08T22:10:00Z **The vacuity proof caught the file split before I did.** After the tests were split it kept emptying only the first file and reported `VACUITY PROOF FAILED: caught=7 (need 0)`. It now empties both, with an empty suite named after each file - two identically-named structs would not compile, and a compile failure would make the proof pass for the wrong reason. Now: `caught=0 (need 0) and MISSED=16 of 16`, OK.
- 2026-09-08T22:10:00Z HARNESS: **16 of 16 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0. Four new mutations pin the radius itself, which no harness here had touched: drop the distance test, double it, shrink it below a divided road's width, and search only the sample's own cell.
- 2026-09-08T22:10:00Z **NEW: a third arm, `KNOWN_MISSED`, asserted the other way round.** Five mutations cannot be killed by any assertion, and a gap merely absent from the list is a gap nobody can see. Each names why: the finiteness loop is subsumed by the range screen; writing the neighbourhood back into a cell grows the arrays without bound so the process dies before any test reports; the grid anchor stopped deciding any verdict once a boundary could no longer hide a retrace (so the bounding-box anchor is real but **unpinned**, and I am not claiming otherwise); the zero-length segment guard became unkillable when the distance test went in; and no fixture separates two samples per cell from one. The arm FAILS if one starts being caught, because that means the gap closed and it should move up.
- 2026-09-08T22:10:00Z NOT FIXED: `ops/mutate/retrace.py` is now 320 lines. The 300-line cap reaches Python only when T-0058 (PR #44) lands, so P-SRC-02 is green today and will not be then. Flagged rather than pre-emptively split, since the split should follow whatever shape that task settles on. G4's remaining item - longitude scaled at each point's own latitude - is addressed by scaling once at the route's mid-latitude, but like the anchor it has no test that distinguishes it.
