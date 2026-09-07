---
id: T-0050
title: decide whether the scenic index adopts Curvature's six squash post-processors
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
depends_on: [T-0025]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0025 implemented the five steps its brief named and checked them against the Curvature project's published
Vermont values: 95.0% of 2307 comparable ways agree within 2%, median error 0.066%. Getting to a comparable
set meant discovering that the five steps are NOT what produces the published numbers.

 runs six more post-processors after them:

    squash_curvature_for_tagged_ways      junction=roundabout,circular ; traffic_calming
    squash_curvature_for_ways             parking:lane:* regexes
    squash_curvature_near_way_tag_change  junction, oneway                              30 m
    squash_curvature_near_tagged_nodes    highway=stop,give_way,traffic_signals,crossing,
                                          mini_roundabout,traffic_calming               30 m
    squash_curvature_near_tagged_nodes    traffic_calming=* ; barrier=*                 30 m
    split_collections_on_straight_segments --length 2414

Measured on the Vermont oracle: ways within 30 m of one of those nodes agree 28.0% of the time; ways with none
agree 82.2%. So the squashes are real and they are large.

Whether we want them is a PRODUCT decision, not a matching exercise, and it should be made deliberately:

- The case FOR: a curve interrupted by a stop sign, a signal or a crossing is not the curve the driver
  enjoys. Squashing near roundabouts stops a roundabout reading as the twistiest thing on the route. This is
  the same instinct as the anti-rat-run penalty already in the routing profile.
- The case AGAINST: our score is  with curvature as one term inside M, not the whole
  score, and the plan already handles interruption differently -  triangular at 65 km/h penalises
  roads you cannot flow along. Adopting the squashes may double-count that.
- A third option: adopt only the ones that are clearly about safety-driven interruption (stop, give_way,
  traffic_signals) and skip the tag-change ones, whose 30 m windows are more about how OSM is edited than
  about how a road drives.

Decide, write down why, and if we adopt any of them, extend the oracle comparison to the ways they touch -
that group is currently excluded from the fixture precisely because we do not implement them, and adopting
them should move it from excluded to passing.

## Log
