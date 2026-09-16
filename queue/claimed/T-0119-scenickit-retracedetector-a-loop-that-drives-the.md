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
  - "swift test -> 'Test run with 45 tests in 7 suites passed', exit 0"
  - "python ops/mutate/retrace.py -> 'caught by a named test: 26 of 26   (trapped 0, compile-only 0, MISSED 0, skipped 0)', exit 0. KNOWN GAPS arm 6 MISSED + 1 trapped of 7; EQUIVALENT arm 2 MISSED of 2. No name occurs in two arms: 35 entries across the three lists, 35 distinct names"
  - "python ops/mutate/retrace.py --prove-vacuity -> 'VACUITY PROOF OK: with no tests present, caught=0 (need 0) and MISSED=26 of 26', exit 0"
  - "RED: the plus-shaped neighbourhood [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)] fails BY NAME 'every cell a pair inside the radius can land in is one the index actually searches' (4 issues, exactly one per corner: bearing 75 -> 'a pair 25.0 m apart on bearing 75 landed at cell offset (1, 1), which the index does not search', 165 -> (1, -1), 255 -> (-1, -1), 285 -> (-1, 1)) and 'a divided road on a diagonal is retrace at every phase, corner cells included' (7 of 12 phases - approaches 0, 40, 60, 100, 140, 160 and 260 m - e.g. 'approach 0.0 m: measured 0.3382839184189396 retrace, not 0.5'). 'Test run with 45 tests in 7 suites failed ... with 11 issues', exit 1"
  - "RED: dropping ONE corner from the neighbourhood fails 'every cell a pair inside the radius can land in is one the index actually searches' BY NAME, ONE issue, 'a pair 25.0 m apart on bearing 75 landed at cell offset (1, 1), which the index does not search'. 45 tests, 1 issue, exit 1"
  - "RED: setting indexCellMeters back to retraceRadiusMeters fails FOUR tests by name, 13 issues: 'two points a radius apart are never more than one cell apart, at the WORST grid phase' (worstX -> 2, 'east-west: a pair 25.0 m apart landed 2 cells apart'), 'every cell a pair inside the radius can land in is one the index actually searches' (2 issues, offsets (2, 0) on bearing 90 and (-2, 0) on bearing 270), 'cells are square in metres, at every latitude' (8 issues, '60 m should be one 50 m cell away, got 2') and 'the index cell is larger than the retrace radius, which is what makes the search complete' (2 issues). exit 1"
  - "RED: emptying MUTATIONS makes the harness REFUSE with 'REFUSING: 0 mutations, 2 equivalent mutants and 7 known gaps, expected at least 26, 2 and 7. / A harness that examines nothing exits 0 and proves nothing.', exit 2, nothing built"
  - "RED: deleting exactly ONE mutation (25 of 26), ONE of the two EQUIVALENT mutants (1 of 2), or ONE of the seven KNOWN_MISSED entries (6 of 7) each makes the harness REFUSE, exit 2, nothing built - every floor is its own arm's real population. Deleting one mutation under --prove-vacuity refuses as well"
  - "RED: the subject or ANY ONE of the four test files differing from 'git show HEAD:' makes the harness REFUSE before any build, exit 2, naming both md5s - measured for all five files individually"
  - "RED: TEST_FILES decay is refused in both directions. Without RetraceIndexTests.swift, --prove-vacuity reports 'VACUITY PROOF FAILED: with no tests present, caught=4 (need 0) and MISSED=22 of 26', exit 1 - the four still caught being 'halve the latitude metre, so grid rows cover twice the ground', 'shrink the index cell back to the retrace radius', 'shrink the neighbourhood to a plus, dropping the four diagonal cells' and 'drop ONE diagonal cell from the neighbourhood'. Without RetraceDiagonalTests.swift it reports 'baseline does not build; nothing below would mean anything', exit 2 (the two files share one probe). The 'caught=1' this line used to claim was never measured on the full population: reviewer-fn-pr76's finding 1"
  - "NOTE: the guarantee test AND the new coverage test correctly STAY GREEN at indexCellMeters = 1.002x and 1.5x radius - the correctness edge is radius * 1.001123 and the 2x is policy headroom, not the boundary. At 1.5x exactly ONE test fails, the policy pin 'the index cell is larger than the retrace radius, which is what makes the search complete' (2 issues, verbatim: policy margin, not the correctness edge; see indexCellMeters' own documentation). At 1.002x exactly TWO fail, that pin plus 'cells are square in metres, at every latitude' (8 issues, '60 m should be one 50 m cell away, got 2' - its 60 m probe against a 50 m cell is entangled with indexCellMeters), so the older NOTE's 'Only the constants pin fails there' was FALSE and stays struck: reviewer-sg-pr76's B2"
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
- 2026-09-09T02:00:00Z reviewer-pr76 returned FAIL a second time, with four blocking findings. **F1 says the central claim of my own fix is false, and it is.**
- 2026-09-09T02:00:00Z **F1: the guarantee did not hold, by 0.1123%.** The source said *"every earlier sample within 25 m is guaranteed to be in one of the nine cells"* and *"the radius is then exactly cellSizeMeters"*. But the grid measured longitude at `111_320.0` m/degree while `Geo.distanceMeters` - the thing that decides - is haversine on `Geo.earthRadiusMeters = 6_371_008.8`, which is `2*pi*R/360 = 111_195.08` m/degree. Confirmed by arithmetic before touching anything: a pair exactly 25 true metres apart reads as **1.001123 cells**. Just over one, so the two can land in columns two apart, outside a 3x3 search, where the distance test is never asked. The reviewer measured it end-to-end: road held fixed, anchor swept over 10001 phases, 8 of them flipped a retracing out-and-back to ACCEPTED. That is verbatim G2, the defect this task exists to prevent, relocated from a 14 m separation to a 24.99 m one.
- 2026-09-09T02:00:00Z **THE FIX IS A MARGIN, NOT A TIGHTER CONSTANT.** Split one constant into two: `retraceRadiusMeters = 25.0` is the product decision (the plan's number, measured with haversine) and `indexCellMeters = 2 * retraceRadiusMeters` is an implementation detail. Two points within the radius now differ by at most `25 x 1.001123 / 50 = 0.5006` cells per axis, so their floors differ by at most 1 and the 3x3 neighbourhood always contains both - and it would still hold if the two scales disagreed by up to a **factor of two**. Making the two constants agree would have fixed today's number while leaving the guarantee dependent on a constant in another file staying close enough; a guarantee like that is not one.
- 2026-09-09T02:00:00Z **MY FIRST ATTEMPT AT THE TEST WAS THE WRONG INSTRUMENT, AND MY SECOND HAD A THIRD METRE IN IT.** (a) A route-level sweep over 5 separations x 6 approaches is 30 phases against a failing band the reviewer measured at ~28 mm, about 0.08% of phases: it would have reported green and pinned nothing. (b) Worse, it *failed* - and for a reason that was my fault, not the code's. The fixture laid its carriageways out with `111_132.0` m/degree, so a separation I had labelled 24.99 m was really **25.004 m**, past the radius and correctly not detected. Three different metres in one test - the grid's, the decider's, and the fixture's - which is the entire finding, committed once more inside the test written to close it. The fixture now uses `111_195.080234`, the same sphere the decider uses, with the reason written at the constant.
- 2026-09-09T02:00:00Z **The guarantee is now tested directly instead of sampled.** `indexNeverSeparatesAPairInsideTheRadius` walks the anchor across two whole cells in 2000 steps - every phase inside a cell - and asserts that a pair exactly one radius apart never lands more than one cell index apart on either axis. No routing, deterministic, and it hits the band a route-level sweep misses. RED demonstrated twice: `indexCellMeters` back to `retraceRadiusMeters` (the shipped defect) -> exit 1; and at `1.002 * retraceRadiusMeters` (a margin too thin for the 0.1123% error) -> exit 1. Restored byte-identical, green re-run exit 0.
- 2026-09-09T02:00:00Z **F2: two of the six KNOWN_MISSED reasons were false, so that arm was recording closable gaps as facts** - which is the thing it is most dangerous for. Both are now ordinary mutations with named tests. **F2a**: the reason claimed a zero-length segment *"contributes a sample at a point it already occupies, with the same heading"*. It does not - `Geo.initialBearingDegrees(from: a, to: a)` is **0.0**, not the segment's heading, so a repeated coordinate plants a due-north sample on a southbound road and the next samples within the radius score 180 degrees against it. Duplicated coordinates are ordinary in OSM geometry and GPS traces. `duplicatedCoordinateIsNotARetrace` pins it. **F2b**: the reason claimed the test *"cannot report, because the process is gone"*. True, but self-inflicted: the 1e17 fixture traps when the screen is removed, and **a trap takes the whole test process down**, so splitting it into its own `@Test` was not enough either - I tried that first and the mutation still scored `trapped`. The 1e17 fixture is gone from the suite and its value lives in the guard's own documentation, where it cannot silence a test; ordinary out-of-range latitudes and longitudes now carry the property and the mutation is **caught**. KNOWN_MISSED is down from six entries to four, and the Log's earlier claim of "five" was wrong twice over.
- 2026-09-09T02:00:00Z **F3: the harness reported a clean sheet over nothing.** With the population lists emptied it printed `caught by a named test: 0 of 0 ... exit 0` and `VACUITY PROOF OK ... MISSED=0 of 0` - every arm vacuously true, and the vacuity proof certifying its own vacuity. `MIN_MUTATIONS = 16` and `MIN_EQUIVALENT = 1` now refuse below the floor, the way `ops/lib/check-exec-bits` refuses below `MIN_FILES = 17`. RED: `REFUSING: 0 mutations and 2 equivalent mutants, expected at least 16 and 1. / A harness that examines nothing exits 0 and proves nothing.`, exit 2.
- 2026-09-09T02:00:00Z **F5-prior**: the opposite-heading threshold was bracketed at 80 and 179.9 and nowhere between, so a shift to 105 degrees survived while being absent from both MUTATIONS and KNOWN_MISSED - exactly what that arm's header says must not happen. Added, caught. **F6-prior**: the code reads `f <= maxRetraceFraction` under prose saying *"retrace < 15%"*. The plan says **both** - `< 15%` in the engine section, `<= 0.15` in the property table - so the `<=` is kept, the prose is corrected, the ambiguity is recorded at the declaration, and `exactlyTheThresholdIsAcceptable` pins the boundary. Tightening a product threshold to match a comment would have been the larger change to make silently.
- 2026-09-09T02:00:00Z **F4: the acceptance block was two commits stale** - it claimed 30 tests in 4 suites and 12 caught / 1 trapped. That is the field `ops/merge` and the next reviewer read, so it is part of the deliverable, not commentary. Rewritten and every line re-run: `swift test` -> **41 tests in 5 suites passed**; `python ops/mutate/retrace.py` -> **21 of 21 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0; `--prove-vacuity` -> `caught=0 (need 0) and MISSED=21 of 21`, exit 0. Two RED lines added, because a block of all-green claims proves nothing about whether the check can fail.
- 2026-09-09T02:00:00Z Six harness anchors went stale when `cellSizeMeters` became two constants, and the harness said so - six SKIP lines and exit 1, which is the floor working rather than a nuisance. Re-anchored.

---

## Sign-off pass: agent/so-pr76 failed it, and B1 is that my own fix's test was vacuous

- 2026-09-15T06:00:00Z **B1. The test written to pin the guarantee was itself the signature defect - the third consecutive round in which that has happened on this file.** `indexNeverSeparatesAPairInsideTheRadius` placed its east probe at `radius / (111_320 * cos(lat))` and then handed `cell()` the same `111_320 * cos(lat)`. The division and the multiplication cancel EXACTLY, so `|cE.x - ca.x|` was `ceil(radius/indexCellMeters)` for any value of either constant, and the assertion held against every implementation. It was also placing the pair **24.972 m** apart while calling it 25 - 28 mm short, which is just outside the band the finding is about. The rule it broke is written out two declarations above it, by me, for `mPerDegLat`: *"deriving these from RetraceDetector would make every offset below cancel against the grid it is meant to probe"*.
- 2026-09-15T06:00:00Z FIX, first attempt: place both probes by **bisecting on `Geo.distanceMeters`** - the function that actually decides a retrace - so no metres-per-degree constant enters the probe at all, and assert with the decider that the pair really is `radius` metres apart before concluding anything from it. **That was necessary and not sufficient.**
- 2026-09-15T06:00:00Z **MY REWRITE WAS STILL VACUOUS, and the way I found out is the lesson.** I ran the three red demos, saw exit 1 three times, and wrote "three for three". Then I checked WHICH test had failed: only `the index cell is larger than the retrace radius`, the constants pin next door, which asserts a literal and says nothing about the guarantee. The guarantee test itself passed at `cell == radius` - against the exact shipped defect. Cause, measured: the failing band is `1.001123 - 1 = 0.1123%` of a cell, and a 400-phase sweep resolves 0.25%, so it steps over the band. **Sampling for a band narrower than the step is a lottery, not a test.**
- 2026-09-15T06:00:00Z FIX, second attempt: **construct the worst phase instead of sampling for it.** The anchor is placed so the first point sits at a chosen fractional position inside its cell; at `f >= 1 - 0.001123` a pair 1.001123 cells wide straddles two boundaries. The test now evaluates those constructed phases plus a 5000-step sweep, and fails BY NAME: `east-west: a pair 25.0 m apart landed 2 cells apart`.
- 2026-09-15T06:00:00Z **AND IT CORRECTED A CLAIM OF MINE.** With the guarantee test now able to fail, it fails at `cell == radius` and **stays green at `1.002 * radius` and `1.5 * radius`** - so those margins genuinely satisfy the guarantee, and my earlier note calling 1.002x "a margin too thin" was wrong. The correctness edge is `radius * 1.001123`; the `2 *` I chose is headroom against the two scales drifting further apart, not the boundary. Both the constant's documentation and the policy pin's failure message now say which is which, because somebody shrinking this constant will find the guarantee test still green well below 2x and should know that is expected rather than a bug.
- 2026-09-15T06:00:00Z **Only the EAST axis can break it, and a north-only test would be green against every version of this defect.** The grid's longitude metre (111_320) is LARGER than the decider's (111_195.08), so an east-west pair reads as further apart than it is and can be pushed over a boundary; the grid's latitude metre (111_132) is SMALLER, so a north-south pair reads as 0.999433 cells and can never straddle two. That asymmetry is now written at the constant. **B2 was the same point from the other side**: the previous anchor moved only in longitude, so the north-south half of the test was 2000 identical evaluations. The anchor walks both axes now.
- 2026-09-15T06:00:00Z **The floor did not refuse what its own comment said it refused.** `MIN_MUTATIONS = 16` against a population of 21 meant five mutations could be deleted one at a time, each with a plausible reason, while the run still printed a clean sheet - which is precisely the failure the floor was added to prevent, and the reviewer of a sibling demonstrated it by deleting both motorway mutations and getting `18 of 18 ... exit 0`. Set to the real count. RED: deleting exactly ONE mutation now gives `REFUSING: 20 mutations ... expected at least 21`, exit 2.
- 2026-09-15T06:00:00Z The baseline build is retried, matching every mutation build (T-0132's second defect: a fresh scratch directory on this box can fail once with an I/O 512 symlink error, and a single attempt turns that into "baseline does not build" with nothing measured).
- 2026-09-15T06:00:00Z GREEN: `swift test` -> **41 tests in 5 suites passed**. `python ops/mutate/retrace.py` -> **21 of 21 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED, 0 skipped, exit 0. `--prove-vacuity` -> `caught=0 (need 0) and MISSED=21 of 21`, exit 0.
- 2026-09-15T19:00:00Z **CI caught what I did not run.** The rewrite took `RetraceGridTests.swift` to 328 lines and I pushed without re-running `ops/check-pins --source-only`, so P-SRC-02 went red on the 300-line cap - the one gate I had not repeated after the change. Split along the real seam: `RetraceGridTests` asks what verdict a ROUTE gets, `RetraceIndexTests` asks the question underneath it - can the index ever separate a pair the distance test would have accepted. 241 and 110 lines. `ops/mutate/retrace.py`'s `TEST_FILES` gained the new file **in the same commit**, because a split the vacuity proof does not know about silently stops it emptying all the tests ([[T-0132]], five occurrences). Re-verified: `PINS ok=4 skipped=9 pending=0 expired=0 failed=0`, 41 tests in 6 suites, `--prove-vacuity` caught=0 MISSED=21 of 21.

---

## Fix pass: reviewer-sg-pr76's B1 - the index's four CORNER cells had no witness

- 2026-09-15T22:30:00Z **B1 reproduced by hand before anything was written.** Replaced `neighbourhood` with
  `[(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]` - the 3x3 index minus its four corners - and ran the
  delivered suite: `Test run with 41 tests in 6 suites passed`, exit 0, **zero failing test names**. Subject
  md5 taken from `git show HEAD:` before the mutation and after the restore, `7f93452ba6bd57104e8084bebf29bdf9`
  both times.
- 2026-09-15T22:30:00Z **Why the suite could not see it.** Both probes in
  `indexNeverSeparatesAPairInsideTheRadius` are due EAST and due NORTH, and no fixture anywhere separates a
  pair INSIDE the radius along a diagonal: `dividedOutAndBack` and the 40 m street offset their two passes
  in latitude, and the out-and-back fixtures retrace themselves exactly, which lands in the same cell
  whatever shape the cell is. A pair separated along an axis differs on ONE cell axis. So what was asserted
  was the BOUND (`|dx| <= 1`, `|dy| <= 1`) and what was never asserted is the COVERAGE - that the search
  visits the cell at (+-1, +-1) - which is the half RetraceDetector.swift:53 actually claims. **The bound is
  not the guarantee**, and this is the third consecutive round on this file where a name and a source
  comment asserted a property the assertion underneath did not cover.
- 2026-09-15T22:30:00Z **Two witnesses, one per level, because the defect exists at both.**
  (a) `theSearchCoversEveryCellAPairCanLandIn` places 24 probes one radius from the origin by **bisecting on
  `Geo.distanceMeters`** - `eastUnits` carries a 1/cos(lat) RATIO so the bearings spread evenly, and the
  LENGTH still comes from the decider, so nothing in the probe can cancel against the grid it probes - and
  asserts BOTH halves: every cell offset that occurs is one `neighbourhood` contains, AND all four diagonal
  offsets do occur. The second half is not decoration: an assertion over a set that never contains a corner
  would be green against exactly the mutation it exists for.
  (b) `RetraceDiagonalTests` drives a divided road on bearing 045, 1200 m each way, return carriageway 24 m
  PERPENDICULAR, over twelve approach phases, and pins the retrace at the return leg's share of the route
  (`1200 / (2400 + approach)`, ~~held to 0.005 at every phase~~ - STRUCK 2026-09-16, reviewer-fn-pr76's
  finding 3: this stated a MEASUREMENT as if it were the ASSERTION. The measured deficit is 0.00403502 to
  0.00495061; the assertion at `RetraceDiagonalTests.swift:107` allows `< 0.02`, four times the widest of
  them, and the test does not hold anything to 0.005). It is the product statement: under the plus,
  a third of a real road's retrace disappears, at some grid phases and not others.
- 2026-09-15T22:30:00Z **The independent phase sweep is load-bearing, and I had to correct my own comment
  about why.** A corner needs the pair to straddle a column boundary and a row boundary at once. I first
  wrote that a single f "comes out as the five cells of a plus". Measured, that is false: one f moving both
  anchors together yields SEVEN of the nine offsets over 24 bearings, and it is `(-1, 1)` and `(1, -1)` that
  never occur - confirmed over a 20000-step sweep. Struck in commit `edec7dd`, with the measurement, rather
  than corrected further down. Same commit struck "every route fixture in this repository is axis-aligned",
  which `retraceAcrossNorth` (355/175, 350/010, 010/190) and `reversalInvariant` (200) make false.
- 2026-09-15T22:30:00Z **RED, by NAME, read out of the output and never from an exit code.**
  * plus-shaped neighbourhood -> 2 tests, 11 issues:
    `every cell a pair inside the radius can land in is one the index actually searches` with one issue per
    corner (`a pair 25.0 m apart on bearing 75 landed at cell offset (1, 1), which the index does not
    search`, and 165 -> (1, -1), 255 -> (-1, -1), 285 -> (-1, 1)), and
    `a divided road on a diagonal is retrace at every phase, corner cells included` at 7 of 12 phases
    (`approach 0.0 m: measured 0.3382839184189396 retrace, not 0.5`).
  * drop ONE corner -> 1 test, 1 issue, naming `(1, 1)`. Counting nine cells is not covering nine cells.
  * the neighbourhood reduced to `[(0, 0)]` -> 4 tests by name, 57 issues (not the same mutation as
    MUTATIONS' "search only the sample's own cell", which cuts the flatMap instead; both are caught).
  * `indexCellMeters = retraceRadiusMeters` -> 4 tests by name, including the new one at offsets `(2, 0)`
    and `(-2, 0)` - so the index test now witnesses the F1 defect from the coverage side as well.
- 2026-09-15T22:30:00Z **The EQUIVALENT arm is the control on the new assertion.** `search a 5x5
  neighbourhood` and `list the neighbourhood in a different order` both still go MISSED, so the new test has
  an opinion about WHICH cells are covered and none about how the list is written. That arm is what would
  catch a coverage assertion written in the over-matching direction.
- 2026-09-15T22:30:00Z **B1's second half: a test whose name promised a witness it does not provide.**
  `neighbourhoodIsOneCellNotTwo` was named *"a street 40 m away is a different road, so the neighbourhood
  must not grow"*, and its comment said "the reach needs a witness on BOTH sides". Widening to 5x5 has been
  EQUIVALENT since the distance test went in - this harness's own EQUIVALENT arm records it and every run
  confirms it goes MISSED - so the name claimed a witness that does not exist. Renamed to "whatever reach
  the index has", and the comment now says what it pins (the radius, from the far side) and where the other
  side is witnessed. Not deleted: what it does assert is true.
- 2026-09-15T22:30:00Z **Harness: two mutations added, and every arm now has a floor equal to its own
  population.** `MIN_MUTATIONS` 21 -> 23. `MIN_EQUIVALENT` was **1 against a population of 2** and
  `KNOWN_MISSED` had **no floor at all** (`known_ok` compared 0 == 0), which reviewer-sg-pr76 demonstrated by
  deleting an equivalent mutant and then all four recorded gaps and still getting a clean sheet at exit 0.
  RED for each, in one run: 22 mutations -> REFUSE, 1 equivalent -> REFUSE, 3 known gaps -> REFUSE, all
  exit 2.
- 2026-09-15T22:30:00Z **The harness now refuses a tree that is not the committed one.** `git show HEAD:` for
  the subject and every test file, compared BEFORE any build, and again after the restore instead of against
  the bytes this process happened to load. RED both ways: an already-mutated `RetraceDetector.swift` and an
  edited `RetraceDiagonalTests.swift` each produce `REFUSING: ... differs from git show HEAD:` with both
  md5s, exit 2, nothing built. The cost is real and worth naming: you must commit before you can measure.
- 2026-09-15T22:30:00Z **TEST_FILES gained `RetraceDiagonalTests.swift` in the SAME commit as the file**
  ([[T-0132]], five occurrences). Decay refused in both directions, measured: drop `RetraceIndexTests.swift`
  from the list and `--prove-vacuity` reports ~~`VACUITY PROOF FAILED: caught=1 (need 0)`~~ - **STRUCK
  2026-09-16, reviewer-fn-pr76's finding 1: `caught=1` was never measured on the full population.** On the
  whole 26-mutation list it is `VACUITY PROOF FAILED: with no tests present, caught=4 (need 0) and
  MISSED=22 of 26`, exit 1 - see the 2026-09-16 entry for the four names; drop
  `RetraceDiagonalTests.swift` and it reports `baseline does not build`, exit 2 - the two files share one
  probe, so emptying the index file while leaving the diagonal file in place does not compile. Neither reads
  as green; the second names the build rather than the omission, which is written at `TEST_FILES`.
- 2026-09-15T22:30:00Z **B2: the acceptance NOTE did not reproduce, so the NOTE is what changed.** *"Only the
  constants pin fails there, and it is a policy margin"* is false at 1.002x: `cells are square in metres, at
  every latitude` fails too (`60 m should be one 50 m cell away, got 2`), because its 60 m probe against a
  50 m cell is entangled with `indexCellMeters`. At 1.5x the NOTE was right - the policy pin is the only
  failure. Struck in the frontmatter itself, not corrected further down. The whole acceptance block was
  re-run line by line against this tree, counts included.
- 2026-09-15T22:30:00Z GREEN: `swift test` -> **43 tests in 7 suites passed**, exit 0.
  `python ops/mutate/retrace.py` -> **23 of 23 caught by a named test**, 0 trapped, 0 compile-only, 0 MISSED,
  0 skipped, exit 0 (KNOWN GAPS 3 MISSED + 1 trapped of 4; EQUIVALENT 2 MISSED of 2).
  `--prove-vacuity` -> `caught=0 (need 0) and MISSED=23 of 23`, exit 0.
  `bash ops/check-pins --source-only` -> `PINS ok=4 skipped=9 pending=0 expired=0 failed=0`.
  `bash ops/queue-check` -> `QUEUE OK (109 tasks)`. Lines: RetraceDetector 225, DetectorTests 268,
  GridTests 245, IndexTests 180, DiagonalTests 100 - all under the cap.
- 2026-09-15T22:30:00Z NOT MINE THIS ROUND, and left open rather than half-closed: **N1** (the mutation named
  "give the index cell too little margin for the scale error" is caught by the constants pin, not by a
  guarantee break - the name overstates what the suite detects; measured again here: at 1.002x the guarantee
  test and the new coverage test are both GREEN), **N3** (`exactlyTheThresholdIsAcceptable` never calls
  `isAcceptableLoop`) and **N4** (M4 is in neither MUTATIONS nor KNOWN_MISSED). Each is a live finding
  against this branch and none is closed by this pass. `ops/mutate/retrace.py` is now **459 lines**, still
  outside P-SRC-02's `Sources/**` and `Tests/**` walk, still flagged against T-0058. `bash ops/test` exits 1
  on `services/api exists but vitest produced no report` - checked, not attributed: `services/api/node_modules`
  is absent on this branch and on main alike, which is T-0040.

### Round 5 - reviewer-fn-pr76, and two commits that had never left this disk

- 2026-09-16T01:30:00Z **The fixes for findings 2 to 6 existed only in `.worktrees/T-0119` and had never been
  pushed.** `ops/agent-preflight` said it in one line - `T-0119   unpushed:[2 commit(s) not on origin]` - so
  neither the round-4 reviewer nor CI could have seen `c4e84ae` or `4e48614`, and the PR body and this Log
  still described the tree at `7ce6f0e`. The same worktree also held a **crashed mutation run**:
  `RetraceDetector.swift` carried a live mutant (`if seen.isEmpty { samplesByCell[cell, default: []]...`)
  and all four test files were `--prove-vacuity`'s empty suites. That is the harness's own header defect -
  "a harness that restores the mutant" - arriving as an interrupted process rather than a bug, and it is
  exactly why `refuse_if_not_head` exists. Restored from `git show HEAD:` and hash-verified per file before
  anything was measured. NOTHING in this entry was measured on that tree.
- 2026-09-16T01:30:00Z **BLOCKING 1 CLOSED - the acceptance line understated the vacuity proof by 4x, not
  3x.** It claimed that dropping `RetraceIndexTests.swift` from `TEST_FILES` leaves
  `VACUITY PROOF FAILED: caught=1 (need 0)`. The reviewer measured THREE still caught from a four-mutation
  subset. Re-run on the FULL 26-mutation population, nothing narrowed, at this branch's tip:

      VACUITY PROOF FAILED: with no tests present, caught=4 (need 0) and MISSED=22 of 26      exit 1

  The four the line omitted, verbatim from the run:

      caught      halve the latitude metre, so grid rows cover twice the ground
      caught      shrink the index cell back to the retrace radius
      caught      shrink the neighbourhood to a plus, dropping the four diagonal cells
      caught      drop ONE diagonal cell from the neighbourhood

  Three of those four are the mutations that witness THIS PR's fix, and the fourth
  (`metersPerDegreeLatitude = 55_000.0`) is caught by the DIAGONAL-OFFSETS half of the same new test - which
  I measured rather than took from the comment that says so. With the other three retrace files replaced by
  the empty suites, it fails `every cell a pair inside the radius can land in is one the index actually
  searches` with `no pair inside the radius ever landed at diagonal offset (-1, 1), so the assertion above
  says nothing about the corner cells` and the same for `(1, 1)`: 2 issues, 21 tests, exit 1. So the
  line described the decay of the new coverage test as nearly invisible when it is the loudest thing in the
  run. `caught=1` is struck where it was written, in the frontmatter AND in the 2026-09-15T22:30:00Z Log
  entry above that repeated it. The other direction reproduces unchanged: drop `RetraceDiagonalTests.swift`
  and it is `baseline does not build; nothing below would mean anything`, exit 2.
- 2026-09-16T01:30:00Z **BLOCKING 2 CLOSED (`c4e84ae`) - two `KNOWN_MISSED` reasons this Log had already
  declared FALSE were still standing verbatim, reading as the justification for a different gap.** When
  "drop the coordinate range screen" and "drop the zero-length segment guard" were promoted into `MUTATIONS`
  in `ffdb8f9` the ENTRIES moved and their COMMENTS did not. Every run prints both as `caught`. Struck, and
  the real reason for the sampling-density gap measured rather than inherited. `grep` over `*.py`, `*.swift`
  and `*.md` now finds neither sentence anywhere in the tree.
- 2026-09-16T01:30:00Z **BLOCKING 3 CLOSED (`c4e84ae`) - the witness comment contradicted its own red demo.**
  `RetraceDiagonalTests.swift` said the plus-shaped neighbourhood costs "0.32 to 0.39 at four of these twelve
  phases". Measured, read out of the failing run: SEVEN of twelve (approaches 0, 40, 60, 100, 140, 160, 260),
  0.3248809338339293 to 0.42207776693045557. The same comment stated the measured deficit (0.00403502 to
  0.00495061) as though it were the assertion's band (`< 0.02`); both are now written out separately, and the
  2026-09-15 Log line that repeated "held to 0.005 at every phase" is struck where it stands.
- 2026-09-16T01:30:00Z **BLOCKING 4 CLOSED (`c4e84ae`, `4e48614`) - three mutation names did not describe the
  edit beside them.** "halve the sampling density along a segment" applied `2.0 -> 0.4`, a FIFTH, under the
  same name as the real halving in `KNOWN_MISSED`, so one run printed that string as `caught` and as
  `MISSED`; it is "cut the sampling density to a fifth along a segment" now. "use the equatorial degree for
  latitude too" applied `55_000.0`, which is no degree at all; that entry is "halve the latitude metre" now
  and the slip it used to name, `111_132.0 -> 111_320.0`, is recorded in `KNOWN_MISSED` with what it would
  break. "give the index cell too little margin for the scale error" claimed a guarantee break at 1.002x that
  does not happen, and is "shrink the index cell to 1.002x the radius, above the correctness edge" now.
  Checked mechanically rather than by eye: 35 entries across the three arms, 35 distinct names.
- 2026-09-16T01:30:00Z **N3 / finding 5 CLOSED (`c4e84ae`) - the only real code defect.**
  `exactlyTheThresholdIsAcceptable` asserted `0.15 <= RetraceDetector.maxRetraceFraction`, which is the line
  above it restated, so `return f <= maxRetraceFraction` -> `<` survived the whole suite at exit 0 with zero
  failing names. No route fixture can close it - no geometry here lands on 0.15 exactly - so the comparison
  is split into `isAcceptable(fraction:)`, the boundary is asserted on the predicate at
  `maxRetraceFraction` and `maxRetraceFraction.nextUp`, and the wiring back to `isAcceptableLoop` is asserted
  too. Behaviour unchanged. Two more of the reviewer's survivors got their own witnesses: a two-point route
  (`twoPointRouteIsAnswerable`; `points.count >= 3` flipped it from `Optional(0.0)`/acceptable to
  `nil`/not-acceptable) and the pole guard (`noGridAtThePole`, in `4e48614`; two earlier reviewers disagreed
  about whether it was reachable and a guard nothing pins is how that stays unsettled). The two the suite
  still cannot kill - the mid-latitude longitude scale, and sampling at the segment start - are in
  `KNOWN_MISSED` with the measurement that says why. **N4 is closed as unactionable as written**: it was
  recorded only as the token "M4", and nothing in this repository defines M4, so it is replaced by those four
  named survivors rather than carried forward as a token.
- 2026-09-16T01:30:00Z **Finding 6 CLOSED (`c4e84ae`) - the second half of the new test had never been seen
  red.** "all four diagonal offsets must occur" now has two demonstrations quoted at the assertion, both read
  out of the output: collapsing the sweep to a single `f` fails it with `no pair inside the radius ever
  landed at diagonal offset (-1, 1)` and `(1, -1)` - exactly the two the paragraph above it predicts - and
  `metersPerDegreeLatitude = 55_000.0` fails it with `(-1, 1)` and `(1, 1)`.
- 2026-09-16T01:30:00Z **A unit slip nobody had flagged, in the sentence the margin argument turns on**
  (`c0b1008`). `indexCellMeters`' documentation read "a north-south pair reads as 0.999433 cells" while the
  cell is TWICE the radius; two paragraphs above, the same file writes "25 x 1.001123 / 50 = 0.5006 cells",
  and `ops/mutate/retrace.py` states the same pair as "0.500561 cells instead of 0.499716". The subject and
  the harness disagreed in units about one measurement. Measured against the decider's 111_195.080234
  m/degree: a 25 m north-south pair spans 24.985818 grid metres - 0.999433 of the RADIUS, 0.499716 of the
  50 m cell; the east-west twin spans 25.028086 - 1.001123 and 0.500562. The ratio was right, the unit was
  not, and the conclusion ("never straddles two") survived either way, which is why no test could notice:
  this is prose about a ratio, and CLAUDE.md forbids anchoring a check on a comment.
- 2026-09-16T01:30:00Z **One more stale number, in the shipped harness rather than in a report.**
  `ops/mutate/retrace.py`'s own comment above the numeric mutations said *the acceptance evidence is
  "23 of 23 caught BY NAME"*. The population is 26. A comment that repeats a count the acceptance block owns
  is one more place for that count to be wrong, so it names the property instead of the number. Checked the
  rest of the tree with `git grep` for every count this task has ever published (`23 of 23`, `43 tests`,
  `21 of 21`, `41 tests`, `MIN_MUTATIONS = 23`, `MIN_KNOWN_MISSED = 4`): the only remaining hits are
  (a) dated GREEN lines in this Log, which record what was true at the commit they name and are left
  standing as history, and (b) three past-tense sentences saying the plus-shaped neighbourhood "left all 41
  tests green at exit 0" - true of the suite as it then stood, and the reason the witness was written. Those
  are kept. Today that same mutation fails two named tests with 11 issues out of 45.
- 2026-09-16T01:30:00Z **What I did NOT close, stated as openly as what I did.**
  * `KNOWN_MISSED` still holds 7 entries and every one of them is a real gap, not an alibi. Two came from
    reviewer-fn-pr76's finding 5 and I did not write fixtures for them: `metersPerDegreeLongitude(at:)` at the
    route's southern end instead of its mid-latitude (wrong in principle; over the longest north-south leg in
    this suite the two scales differ by 0.01035%, which moves a 25 m pair by 0.0000429 of a cell) and sampling
    at a step's START instead of its midpoint (a real half-step shift that no fixture's band separates).
    Both are recorded with the measurement that says why, which is the most I can honestly claim.
  * The sampling-density gap (`samplesPerCell 2.0 -> 1.0`) is still uncaught. Closing it needs a fixture built
    so a cell is crossed BETWEEN consecutive samples at 1.0 and not at 2.0 - a different fixture from any here,
    and I did not write it.
  * `ops/mutate/retrace.py` is **545 lines**, up from 459. It is outside P-SRC-02's `Sources/**` and `Tests/**`
    walk, so nothing fails; it is still the same standing exception flagged against [[T-0058]], and it got
    worse this round rather than better.
  * `bash ops/test` exits **1** on `FAIL: services/api exists but vitest produced no report`, AFTER the Swift
    tier prints `Test run with 45 tests in 7 suites passed`. CHECKED, NOT ATTRIBUTED: `services/api/node_modules`
    is absent in the main checkout and in this branch's worktree alike, and no commit on this branch touches
    `services/api`. That is [[T-0040]].
  * The branch is 111 commits behind `origin/main` and has not been rebased. CI on #76 is green on both checks
    (core, pins-source-only); GitHub reports `mergeable: UNKNOWN`, which I did not resolve here.
  * The task is NOT transitioned and `reviewer:` is still null. I am the owner; a reviewer of this task must
    not be me ([[ops/queue-check]]).
- 2026-09-16T01:30:00Z GREEN, every line re-run against the tip of this branch and pasted, not carried
  forward. The previous GREEN line (2026-09-15T22:30:00Z) describes `7ce6f0e` and is superseded by these.

      swift test --scratch-path .build-T0119fix
      Test run with 45 tests in 7 suites passed                                          exit 0

      python ops/mutate/retrace.py
      caught by a named test: 26 of 26   (trapped 0, compile-only 0, MISSED 0, skipped 0) exit 0
        KNOWN GAPS   6 MISSED + 1 trapped of 7
        EQUIVALENT   2 MISSED of 2

      python ops/mutate/retrace.py --prove-vacuity
      VACUITY PROOF OK: with no tests present, caught=0 (need 0) and MISSED=26 of 26      exit 0

      bash ops/check-pins --source-only
      PINS ok=4 skipped=9 pending=0 expired=0 failed=0 tier=linux source-only             exit 0

      bash ops/queue-check
      QUEUE OK (109 tasks)                                                                exit 0

  Both gates were run BARE, not through a pipe: a pipeline's exit status is its last element's, and
  `ops/queue-check | tail -1 && git commit` has already committed over a refusal in this repository.
  Lines: RetraceDetector 249, DetectorTests 297, GridTests 269, IndexTests 189, DiagonalTests 113 - all under
  the 300 cap, DetectorTests with 3 to spare. `ops/mutate/retrace.py` 545, outside the cap's walk.
  `git ls-files -s ops/mutate/retrace.py` -> `100644`, which is what [[T-0127]] requires of a `*.py` there.
- 2026-09-16T01:30:00Z **How this round's numbers were produced, so the next reviewer can repeat them
  exactly.** Four worktrees, each at a named commit with its own `--scratch-path`, and no tracked file
  written in a worktree I do not own:
  * `.worktrees/T-0119` (the branch) - `swift test`, and `python ops/mutate/retrace.py` unmodified.
  * `.worktrees/fx76-decay` - `--prove-vacuity`, and the TEST_FILES-decay experiments. The decay drivers
    import `ops/mutate/retrace.py` BY PATH and override `TEST_FILES` IN MEMORY; the tracked harness is never
    edited. Kept at `.artifacts/decay_full.py` and `.artifacts/decay_diag.py`.
  * `.worktrees/fx76-static` - the three RED demos (`.artifacts/reddemo.py`) and the latitude-metre probe
    (`.artifacts/latmetre.py`), each applying one mutation to the subject, running `swift test`, restoring
    it, and hashing the result against `git show HEAD:`.
  * `.worktrees/fx76-floor` - the eleven REFUSAL arms (`.artifacts/floors.py`) and the 1.002x / 1.5x NOTE
    (`.artifacts/note.py`). Every refusal arm proves nothing was built by monkeypatching `build()`/`test()`
    to record a call and printing `[built anything? False]`.
  Every demo that mutated a tracked file restored it and VERIFIED the restore by hashing against
  `git show HEAD:` - not by trusting a `finally` to have run. All five files came back equal in every arm.
  The harness's own headline numbers were then re-measured a THIRD time, after `2174f01`, so the count in
  the acceptance block describes the exact committed tree and not a tree one comment away from it.
- 2026-09-16T02:10:00Z **RED for the three code defects, by NAME, read out of the output.** The harness
  scores a catch on a failing test line rather than an exit code, but the harness prints counts and not
  names, and this repository has twice concluded "caught" from an exit while the test that failed was an
  unrelated pin next door. So each of the three mutations this round exists for was applied on its own, run
  through `swift test`, and the failing NAME parsed out (`.worktrees/fx76-static/.artifacts/codedefects.py`).
  Subject restored and hashed against `git show HEAD:` after each - `552c42b7279aa9865339672a534a2cf6`,
  equal every time.

      accept only strictly below the threshold, so exactly 15 percent is refused
        -> "exactly the threshold is acceptable, and a hair over it is not", 1 issue:
           `exactly the threshold must be acceptable - the plan's property table says <= 0.15`

      refuse a two-point route, so the shortest real segment is unanswerable
        -> "a two-point route is answerable: no retrace, and an acceptable loop", 2 issues:
           `one segment driven once is 0 retrace, not nil` and
           `a two-point route retraces nothing, so it is acceptable`

      drop the pole guard, so a route with no columns is answered anyway
        -> "there is no grid at the pole, so a route there is refused rather than answered", 2 issues:
           `a route at the pole has no grid, so it has no answer - got Optional(0.0)` and
           `an unanswerable route is not an acceptable loop`

  Each name is the test written for that defect, not a neighbour. The third also settles the argument two
  earlier reviewers had about the pole guard in the only way that lasts: `nil` really does become
  `Optional(0.0)`, printed by the assertion rather than asserted in a Log entry.
