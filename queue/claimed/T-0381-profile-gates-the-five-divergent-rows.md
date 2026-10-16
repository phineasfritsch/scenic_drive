---
id: T-0381
title: The routing profile gates the five rows it cannot express today (tracktype>=grade3, locked barrier, ford, service values, rough smoothness) - encoded values in config.yml, clauses in car_scenic_base.json
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T19:37:33Z
lease_expires_at: 2026-10-17T19:37:33Z
worktree: .worktrees/T-0381
branch: task/T-0381
exclusive: [routing-profiles]
touches: [services/routing/config.yml, services/routing/profiles/, services/routing/tests/, services/etl/etl/profilegate.py, services/etl/tests/, services/etl/tests/fixtures/gate_parity.json, ops/mutate/profilegate.py]
pins_affected: [P-PROD-01, P-SAFE-01]
reviewer: null
depends_on: [T-0012, T-0188]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0012 built one gate-parity fixture through the ETL, the routing profile and ScenicKit.Gates, and recorded five
rows as typed `divergent`: tracktype>=grade3 on a non-track road, barrier=gate+locked=yes, ford=yes,
service=driveway|parking_aisle (and T-0188's drive-through, emergency_access), where the profile answers
NOT_GATED. T-0188 (PR #268) closed the ETL half; ScenicKit and the ETL now refuse all five. The router is the
last layer that routes a sedan onto them, and the router is what actually chooses the road.

The profile cannot express these today: GraphHopper has no encoded value for them in services/routing/config.yml.
MEASURE first: which GraphHopper 11 encoded values exist for each (track_type, road_access is already there;
barrier/ford/service may need `graph.encoded_values` entries or a custom tag parser like the scenic_score plugin),
the cost of each (graph re-import, memory), and what etl.profilegate can evaluate. RULE the smallest set that
gates all five on positive evidence only (CLAUDE.md: hard gates are safety only; motorway/trunk stay penalised,
never excluded). Then each divergent row's profile half goes away and test_only_the_typed_classes_diverge holds
zero rows; profilegate learns the new clauses (refusing anything it cannot read, as T-0012 rv1 ruled).

Not deployed here: a config.yml change needs a graph re-import on the VPS, which is the owner's step. Record the
re-import command and the expected graph hash change in the Log.

## Log
- 2026-10-16 filed by agent/claude-opus-5 from T-0012 stillOpen and T-0188 stillOpen (the profile half of the five divergent rows was never filed).
- 2026-10-16T19:37:33Z claimed by agent/claude-opus-5; lease until 2026-10-17T19:37:33Z
