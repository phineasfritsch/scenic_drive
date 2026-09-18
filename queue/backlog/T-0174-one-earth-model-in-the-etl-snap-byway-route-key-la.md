---
id: T-0174
title: one earth model in the ETL - snap.py, byway_route_key.py, landcover.py and geom.py all measure with curvature.RAD_EARTH_M; point_to_segment_m defined once
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0030]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RED BY NAME first: a test that measures the SAME point-to-segment distance through snap.point_to_segment_m and geom.point_to_segment_m and asserts they agree to 1e-9 - red today (the flat pair kx=111320*cos / ky=110540 vs RAD_EARTH_M=6373000 disagree by 0.63 %), green when one delegates to the other"
  - "grep -n '110540\\|111320\\|6371\\|6373' services/etl/etl/*.py prints exactly one definition site (curvature.RAD_EARTH_M) plus documented imports; landcover.py's lat-axis step uses the same constant"
  - "every existing fixture value that moves by the model change is re-derived in its `workings` and quoted; the whole ETL suite count line and zero skips at the final commit"
---
## Brief

From the 16:13 panel (CODE lens, grounded). Three earth models live on main: curvature.py RAD_EARTH_M=6373000
(haversine), Sources/ScenicKit/Geo/Geo.swift 6_371_008.8, and the flat pair kx=111320*cos(lat), ky=110540 in
snap.py (copied verbatim into byway_route_key.py; landcover.py uses 111320 on the LAT axis). 110540 vs
6373000*pi/180 = 111246 is the 0.63 % gap PR #94's reviewer found. T-0030's geom.py imports RAD_EARTH_M
correctly and then defines its own point_to_segment_m / point_to_polyline_m on that model - so one function
name now exists twice with a 0.6 % disagreement, and segment length_mm, snapping and segment_alias.cover_pct
(CHECK BETWEEN 40 AND 100) ride on it. Cross-file today (snap.py, byway_route_key.py, landcover.py, geom.py);
wider every week. The Swift side (Geo.swift, RetraceDetector.swift's hard-coded 111_320) is a separate task
when ScenicKit parity (P-PROD-01) is measured against the corpus.

## Log
- 2026-09-18T23:04:01Z filed by agent/claude-fable-5-1 from the 16:13 panel's grounded synthesis. Not started.
