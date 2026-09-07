---
id: T-0012
title: "ETL gate parity fixture: motorway/trunk/private/unpaved score 0.0 across ETL, router profile and ScenicKit.Gates (P-PROD-01)"
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/, services/routing/profiles/, Sources/ScenicKit/Scoring/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0024]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The same gating rule is written three times, in three languages, by three different tasks:

- **the ETL**, which computes `scenic_score` per way and writes it into the corpus and the tagged PBF
- **the routing profile**, `services/routing/profiles/car_scenic_base.json`, whose `priority` block zeroes
  `road_access == PRIVATE|NO`, the unpaved surfaces, and `road_class == TRACK`
- **ScenicKit**, whose `Gates` are what the app reasons about when it explains a route

Three copies of one rule drift. When they do, nothing fails: the ETL scores a way 0.4, the profile lets it
through, the app says it is fine, and a sedan ends up on a gated dirt track. Every layer is internally
consistent and the product is wrong. That is what P-PROD-01 exists to catch, and it is currently `pending`.

**One fixture set, through all three.** Build a small table of ways — real OSM ways from the Bay Area extract,
by id, so nobody can hand-tune the input — covering at minimum:

    motorway, motorway_link, trunk, trunk_link          score 0.0, NOT gated (penalised, never excluded)
    surface=gravel|dirt|ground|sand|unpaved|compacted|fine_gravel   GATED
    highway=track, tracktype>=grade3                    GATED
    access=private|no|permit|destination                GATED
    motor_vehicle=no, barrier=gate + locked=yes, ford=yes          GATED
    highway=service + service=driveway|parking_aisle    GATED
    surface absent on primary/secondary/tertiary        treated as paved
    surface absent on unclassified/residential          x0.8 and flagged surface_unknown

and assert every layer returns the same verdict for every row. Not "each layer has tests" — one fixture, three
consumers, one expected answer per row.

**The distinction that must not be lost.** Motorway and trunk score 0 and are PENALISED; they are not gated.
Almost every Bay Area commute over 15 km needs freeway shoulders around a scenic middle, and a "tidy-up" that
promotes them from score-0 to excluded makes those routes unroutable rather than unattractive. T-0024's
`tagfilter.problems()` already guards the extract side of this; the fixture must guard the scoring side.
Hard gates are SAFETY ONLY, on positive evidence.

**Demonstrate red three ways, one per layer**, because a parity check that has only been seen red in one place
has only been tested in one place:

1. change a gate in the profile JSON → fixture fails
2. change the equivalent rule in the ETL → fixture fails
3. change `ScenicKit.Gates` → fixture fails

and each failure must name which layer disagreed with which, not just "mismatch".

**Then land the P-PROD-01 assertion**, replacing its `pending:`. `pins/PINS.yaml` currently carries three
pending pins; one of them is this. A pin that stays pending past the task that was supposed to make it real is
the debt `ops/check-pins` is built to refuse.

Depends on T-0024 for the extract the fixture ways are drawn from.

## Log
