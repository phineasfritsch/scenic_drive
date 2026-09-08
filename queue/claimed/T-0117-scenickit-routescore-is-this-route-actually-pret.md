---
id: T-0117
title: ScenicKit RouteScore: is this route actually pretty, length-weighted and invariant to how the router split the edges
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T13:54:42Z
lease_expires_at: 2026-09-08T15:54:42Z
worktree: .worktrees/T-0117
branch: task/T-0117
exclusive: []
touches: [Sources/ScenicKit/Scoring/, Tests/ScenicKitTests/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "swift test -> 29 tests in 4 suites passed, exit 0"
  - "python .artifacts/mutate-T0117.py -> 8 of 8 mutations caught, exit 0"
  - "RED: each of the 8 mutations alone makes swift test exit 1"
---
## Brief

`LambdaSearch` (T-0116) finds the routes that FIT the time budget. This decides which of them is worth
driving, and whether any of them is.

    0.60 * mean + 0.25 * p90 - 0.15 * dudFraction + 0.10 * min(1, episodes / 3)

Four terms, four different questions, and dropping any one of them lets a bad route score well:

  * **mean** - pretty on average? Alone it rewards a route that is uniformly mediocre.
  * **p90** - is any of it really good? A flat 0.5 the whole way is a commute, not a drive.
  * **dudFraction** - how much is actively dull? The only negative term, and the one that stops a route
    buying a good mean with one spectacular canyon bolted onto twenty minutes of arterial.
  * **episodes** - is the pretty part *sustained*? Prettiness scattered over fifty 200 m fragments is a
    scenic drive's worth of scenery arranged so you never get to enjoy any of it.

Below `honestFailureThreshold` the product says *"not much pretty within 25 minutes of this drive"* instead
of presenting a dull route as an answer.

**No `Package.swift` change**: `Sources/ScenicKit/Scoring/` is inside the existing ScenicKit target path,
which SwiftPM globs. The lock on that serial file is held by T-0114 and was not needed here.

### The difficulty is length weighting, and it is the whole task

The router may return one OSM way as six path-detail intervals, six ways as one, and the route in either
direction. **None of that changes the drive, so none of it may change the score.** A per-edge mean lets a
router that splits a dull edge in half give that edge two votes; a percentile taken over the edge list
answers a question about the router's segmentation rather than about the road.

Every statistic is computed over metres. The plan pins this as two properties - *"RouteScore invariant under
reversal (1e-9) and re-encoding (0.5%)"* - and those are the assertions here that can fail for a real reason.

## Log

### GREEN

    swift test --scratch-path .build-T0117
    Test run with 29 tests in 4 suites passed after 0.030 seconds.   exit 0

### RED, eight ways, and seven of them are the *natural* implementation

    caught  mean over the edge list instead of over metres         exit=1
    caught  percentile by index instead of by length               exit=1
    caught  dud fraction over the edge list instead of over metres exit=1
    caught  ask the episode question per edge                      exit=1
    caught  forget the episode that the route ends on              exit=1
    caught  add the dud fraction instead of subtracting it         exit=1
    caught  drop the clamp and let a duds-only route score negative exit=1
    caught  score an empty route rather than refusing it           exit=1
    8 of 8 mutations caught                                        exit=0

The first four are not sabotage - they are what you write if you are not thinking about metres.
`edges.reduce(0) { $0 + $1.score } / count` is the shorter line, `sorted[Int(0.9 * count)]` is the obvious
percentile, and `if edge.score > 0.6 && edge.length >= 800` is the obvious episode test. Each produces a
number for every route and each describes the router instead of the road.

The fixtures that separate them are small and specific:

  * **10 m at 1.0 against 10 km at 0.1.** Two edges either way. The index percentile calls this route
    spectacular; the length-weighted one returns 0.1, which is what the drive is.
  * **A 5 km canyon returned as twelve 420 m intervals.** Every interval is under the 800 m episode minimum
    on its own, so the per-edge test counts zero episodes for the prettiest road in the region. This is the
    normal case, not an exotic one - OSM splits ways at junctions.
  * **Fifty 200 m gems separated by 300 m of arterial.** Excellent mean, zero episodes.

### One mutation was not caught, and the reason is a finding rather than a hole

`score an empty route as zero rather than refusing` first targeted only `guard !edges.isEmpty`. Nothing
objected, correctly: `guard total > 0, total.isFinite` catches the empty case on its own, so removing the
first guard changes no behaviour. **The two guards are redundant for the empty input.**

That redundancy is kept deliberately - `!edges.isEmpty` states the intent at the point a reader looks for it,
and the cost is a comparison - but a mutation that changes nothing must not be recorded as a caught defect.
Retargeted at both guards together, so an empty route becomes `0/0` and propagates a NaN into a score, it is
caught by `emptyIsNil`.

The distinction matters here specifically: returning 0 for an empty route would make *"the router found
nothing"* indistinguishable from *"the router found a freeway"*, and those need different words on screen.

### `dudThreshold` is not from the plan, and is labelled as such

The plan names the `dud_frac` term and its 0.15 weight and **does not specify the threshold**. 0.25 is chosen
to mean "actively dull rather than merely unremarkable": it puts motorway and trunk (0 by construction) and
bare arterial into the dud bucket while leaving ordinary residential and unclassified out. It is a named
constant, not an inlined literal, so that tuning it is a one-line change with a test that moves - and the
source says plainly that it was chosen here rather than handed down, because a tuning constant mistaken for
a specified one is a constant nobody dares to tune.

### Consistent with the product invariants

`motorwayIsADud` asserts the CLAUDE.md rule from the scoring side: an 8 km motorway shoulder counts fully
toward `dudFraction` and the route still scores, still keeps its episode, and is still returnable. Penalised,
not excluded - the freeway shoulder around a scenic middle is the shape most drives over 15 km have to take.

### Not done

No RouteScore-based candidate selection, no rat-run detection, no `areas` re-issue. Those need the router
and belong to the caller. This is the arithmetic, and it takes a plain array so it can be tested against
exact adversarial shapes with no network, graph or container.
