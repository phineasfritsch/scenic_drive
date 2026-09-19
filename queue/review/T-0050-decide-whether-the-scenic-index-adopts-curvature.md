---
id: T-0050
title: decide whether the scenic index adopts Curvature's six squash post-processors
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-07T23:15:12Z
lease_expires_at: 2026-09-08T01:15:12Z
worktree: null
branch: task/T-0050
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-47
depends_on: [T-0025]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0025 implemented the five steps its brief named and checked them against the Curvature project's published
Vermont values: 95.0% of 2307 comparable ways agree within 2%, median error 0.066%. Getting to a comparable
set meant discovering that the five steps are NOT what produces the published numbers.

`processing_chains/adams_default.sh` runs six more post-processors after them:

    squash_curvature_for_tagged_ways      junction=roundabout,circular ; traffic_calming
    squash_curvature_for_ways             parking:lane:* regexes
    squash_curvature_near_way_tag_change  junction, oneway                              30 m
    squash_curvature_near_tagged_nodes    highway=stop,give_way,traffic_signals,crossing,
                                          mini_roundabout,traffic_calming               30 m
    squash_curvature_near_tagged_nodes    traffic_calming=* ; barrier=*                 30 m
    split_collections_on_straight_segments --length 2414

Measured on the Vermont oracle: ways within 30 m of one of those nodes agree 28.0% of the time; ways with
none agree 82.2%. So the squashes are real and they are large.

Whether we want them is a PRODUCT decision, not a matching exercise, and it should be made deliberately:

- **For.** A curve interrupted by a stop sign, a signal or a crossing is not the curve the driver enjoys.
  Squashing near roundabouts stops a roundabout reading as the twistiest thing on a route. Same instinct as
  the anti-rat-run penalty already in the routing profile.
- **Against.** Our score is `GATE × M^0.35 × E^0.65` with curvature one term inside M, not the whole score,
  and the plan already handles interruption differently: `speed_fit`, triangular at 65 km/h, penalises roads
  you cannot flow along. Adopting the squashes may double-count that.
- **A third option.** Adopt only the ones clearly about safety-driven interruption (stop, give_way,
  traffic_signals) and skip the tag-change ones, whose 30 m windows say more about how OSM is edited than
  about how a road drives.

Decide, write down why, and if we adopt any of them, extend the oracle comparison to the ways they touch.
That group is currently excluded from `services/etl/tests/fixtures/curvature_oracle.json` precisely because
we do not implement them, so adopting them should move it from excluded to passing — which is the
demonstration that the adoption is faithful rather than approximate.

## Log
- 2026-09-07T23:15:12Z claimed by agent/unknown; lease until 2026-09-08T01:15:12Z

- 2026-09-08T09:40Z DECIDED by agent/claude-opus-5, from a measure-then-argue exercise: two measurers on
  disjoint quantitative questions, three advocates each assigned an opposed position, one decider who ran
  three further measurements rather than arbitrating the cases as written. All scripts under
  services/etl/work/t0050{a,b,c}/ in the T-0025 worktree, all run in the pinned scenic-etl image, nothing
  tracked modified.

  **THE DECISION: adopt 1, 4 and 5. Reject 2 and 3. Defer 6.**

  **The measurement that reframes the whole question.** Processors 1 and 2 touch ZERO of the 3297 oracle ways
  - and that is a SELECTION EFFECT, not rarity. `vermont.c_300.kmz` publishes only collections whose
  curvature survived >= 300, and P1/P2 zero exactly what they match, so a matched way can never appear in the
  oracle at all. The oracle is structurally incapable of measuring them. On the full drivable network they
  hit 158 and 269 ways. Anyone reading "0 of 3297" as "these do nothing" would have concluded the opposite of
  the truth.

  **Reach, on the 3297:** P4 273 ways (8.28%), P5 36 (1.09%), P6 34 (1.03%), P1/P2/P3 0. P4 and P5 overlap on
  4 ways only - nearly disjoint. P4 splits: stop/give_way/traffic_signals 146, crossing 179, mini_roundabout
  0, traffic_calming 0.

  **Vermont contains ZERO mini_roundabout nodes and ZERO highway=traffic_calming nodes**, verified against the
  full pinned extract. So the FOR position's central image - squashing stops a roundabout reading as the
  twistiest thing on a route - rests on a node type that does not occur in this data. In Vermont, P4 is 78% a
  pedestrian-crossing processor by node count.

  **Magnitude is small.** P4 covers 1.02% of length and 0.87% of curvature; P5 0.11% and 0.15%. Per touched
  way the squash is a minority of that way's own curvature, never all of it.

  **What decided it** was a decile gradient. Every node squash's hit rate FALLS as roads get curvier - safety
  9.0->1.7%, crossing 9.9->5.8%, all node squashes 12.6->10.4% - while the tag-change processor RISES,
  4.0->11.7%. The full chain's rising gradient is imported entirely from P3. That refutes the FOR position's
  claim that the full chain is flat, and it isolates the one processor doing the damage. Crossing behaves like
  the safety subset, not like tag-change, which is why it is adopted rather than gated out.

  **P2 rejected** because it zeroes the ENTIRE way on a kerbside-parking tag - an urbanness proxy, and E
  already carries 0.16*(1-impervious) + 0.12*(1-furniture). That is where the double-count objection has real
  teeth. **P3 rejected**: sole source of the rank damage, reach unmeasurable on single-way collections,
  semantics unreproducible. **P6 deferred**: collection-level, a no-op here, and it concentrates in
  motorway/primary/secondary where the plan's motorway/trunk scenic_score = 0 already applies.

  **THE SURVIVING OBJECTION, and it is strong enough that IMPLEMENTATION SHOULD WAIT.** In the decider's own
  words: *"I am reading 'the correction working' off the same ranking I am using to justify the correction."*
  All nine ways that leave the top 50 under the squash are between 19 m and 136 m. That is a LENGTH
  NORMALISATION defect, not an interruption defect - and 611 drivable ways sit at exactly curvature/length =
  2.0, with 1,138 within 0.05% of it, so under any [0,1] normalisation the curviest 2-3% collapses onto one
  value. T-0029 has to fix that regardless. A length-aware normalisation might demote all nine with no squash
  at all. The two are partial substitutes and nobody disentangled them, because the right experiment - fix the
  saturation first, then re-measure the squash's MARGINAL value - is exactly the one not run.

  So: the decision is recorded, and **implementation is sequenced after T-0029's normalisation transform**,
  not before. Adopting an ETL stage, a node-proximity index, a fixture rebuild and a permanent production
  dependency on OSM node-tagging density to solve a problem the normalisation fix may solve for free would be
  the wrong order.

  **A hard prerequisite found on the way, and filed as T-0064.** The fixture's node set comes from
  `osmium getid -r`, which retains only the oracle ways' own member nodes: 650 of Vermont's 14,296
  squash-tagged nodes. The "no tagged node within 30 m" condition is therefore evaluated against 4.5% of the
  relevant nodes. Against all of them, P4 goes 273 -> 383 and the P4-or-P5 union 305 -> 446, so roughly 141
  ways sit in the eligible pool that a correct test would exclude. T-0025 suspected this and wrote "stated
  rather than chased"; it is now chased.

  **The demonstration the brief asks for is available and exact.** The fixture's funnel drops 2571 -> 2384,
  and that 187-way exclusion reconciles EXACTLY against P4-or-P5 = 187 with P1-or-P2 = 0 on the
  geometry-identical set - a number nobody chose, verified by a script that exits 0 on the equality. So
  adopting P4+P5 has a falsifiable target: condition 3 disappears and those 187 ways move from excluded to
  passing. If they do not, the adoption is approximate rather than faithful.

  **Open questions carried forward, not resolved:** whether crossing's falling decile curve inverts on a Bay
  Area extract where crosswalk mapping is far denser (if it rises, drop crossing and keep the safety subset);
  the route-level P90 test, which cannot run because services/routing does not exist yet; and the fact that
  **no human preference data exists anywhere in this repo**, so every position here argues from proxies. The
  measurement that would settle it is 50-100 road pairs where a squash flips the order, ranked blind by
  drivers.

  **What to attack.** The decision rests on Vermont, and both load-bearing environmental facts - 11.8%
  maxspeed coverage, zero mini_roundabouts - are Vermont facts. The product ships in the Bay Area. Second: I
  adopted P1 on way-level ranking evidence when the thing that would price it properly is the route-level P90
  term. Third: the decider names its own reasoning as "an inspection dressed up as a measurement" for the nine
  departing ways, and I have not overturned that self-criticism - a reviewer should decide whether a decision
  whose author says that about their own key evidence should be recorded at all.

