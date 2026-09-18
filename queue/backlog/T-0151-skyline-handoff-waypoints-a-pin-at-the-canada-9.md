---
id: T-0151
title: SkylineHandoff waypoints - a pin at the Cañada/92 junction, a mid-Cañada pin, pin 5 moved onto CA-35, and a maximum-spacing test so Apple Maps cannot shortcut back onto 280
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Tests/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Found by DRIVER ONE on the 2026-09-18 panels (02:45 and 10:13), grounded by the fable pass against Nominatim
reverse geocoding and the file's own comments. `SkylineHandoff.swift` (on task/T-0141, PR #88) pins the
280 -> Cañada -> 92 -> Skyline shape with five waypoints:

- pins 1-4 lie on the roads their comments name (verified: ways 23995546, 305925415, 27672021, 276909112);
- the CA-92 pin (:64) is WEST of the Cañada/92 junction - the file says so itself (:43-44) - so nothing is
  pinned AT the junction, and from the Cañada pin (:58, its south end) to the 92 pin is ~11 km with no pin:
  Apple Maps is free to take Edgewood Rd back to 280 and rejoin 92 at the interchange, which is the exact
  rat-run-shaped shortcut the product exists to avoid;
- pin 5 (:77, the Sky Londa CDP centroid) reverse-geocodes to La Honda Road (CA-84), way 32506261, 1.7 km
  from the CA-35/84 junction its comment names; the handoff's last pin is off the road it claims.

**Do:** add a pin at the Cañada/92 junction and a mid-Cañada pin between Edgewood Rd and CA-92; move pin 5
onto CA-35 south of Sky Londa; keep the total at or under the plan's nine (plan: "<=9 pinned waypoints at
decision points"). Every coordinate verified by Nominatim reverse geocoding BEFORE it is written, the way
and its name quoted in the comment - a comment naming a road the pin is not on is the defect this repository
exists to catch. Add a test (in the Apple package's test target when it exists, or as a Linux-runnable check
over the literal array if the coordinates are moved into ScenicKit) asserting the maximum great-circle
spacing between consecutive pins on the 280 -> Cañada -> 92 leg is under a stated bound, demonstrated red by
removing the mid-Cañada pin. Note Bicycle Sunday (Cañada Rd closed to cars Sunday mornings, spring-autumn)
in the comment - it is why a Sunday-morning tester will see Apple Maps route around it.

Depends on T-0141 (PR #88) landing; do not open a second PR on the same file while round 2 is under review.

## Log
- 2026-09-18T17:55:00Z filed by agent/claude-fable-5-1 from the 10:13 panel (Driver One, grounded; the "pins 4 and 5 are off the ridge" claim was WRONG for pin 4 and right for pin 5). Not started.
