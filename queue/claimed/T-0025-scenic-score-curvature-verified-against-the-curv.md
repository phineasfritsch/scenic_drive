---
id: T-0025
title: Scenic score: curvature, verified against the Curvature project's published values
state: claimed
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:59:08Z
lease_expires_at: 2026-09-07T20:59:08Z
worktree: ../wt/T-0025
branch: task/T-0025
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-30
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Reimplement the Curvature project's method exactly: circumcircle radius from every 3 consecutive
OSM nodes, take the MIN of the two triangles a segment belongs to, cap 10 km, run the deflection filter that
zeroes fake curvature when the heading change is below gap_distance/175, then weight length by 2.0/1.6/1.3/1.0/0
at radius <30/<60/<100/<175 m.

THE ORACLE: Curvature publishes computed outputs for Vermont. Our value for the same way ids must match within
2%. That is an external oracle an agent cannot fabricate - the same discipline that caught the bad solar oracle
in T-0011. If the published data is not machine-readable, say so in the log and propose the next best oracle
rather than quietly falling back to self-generated fixtures.

## Log
- 2026-09-07T16:59:08Z claimed by agent/claude-opus-5; lease until 2026-09-07T20:59:08Z
