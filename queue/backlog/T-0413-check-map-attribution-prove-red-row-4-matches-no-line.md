---
id: T-0413
title: check-map-attribution --prove-red stops at row 4 on main - its sed anchor in DriveBasemap.swift no longer exists, so rows 4 onward (P5, the footer's own file edited, among them) are never run
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-map-attribution-mutations, queue/]
pins_affected: [P-ATTR-01]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "bash ops/lib/check-map-attribution --prove-red exits 0 with every row refused by name on the current main"
  - "row 4 ('a feature file names a protomaps case') targets a line that exists in DriveBasemap.swift and is seen to change the copy"
---
## Brief

Found by T-0404's author on 2026-10-17 in the main checkout at 34871225 (and the same on task/T-0404):
`bash ops/lib/check-map-attribution --prove-red` prints rows 1-3 refused, then

    THE MUTATION CHANGED NOTHING: a feature file names a protomaps case
    A row whose sed matched no line proves nothing; the anchor it targets has moved.

and exits 1. Row 4 in ops/lib/check-map-attribution-mutations seds
`s/return BasemapResolver.losAngeles(appearance: appearance)/return MapStyle.protomapsLALight/` over
FeatureScenicHome/DriveBasemap.swift, whose line 48 is now `BasemapResolver.losAngeles(appearance: appearance)`
with no `return`. The driver stops at the first dead row, so every later row of the P-ATTR-01 table is unrun.
Re-anchor row 4 on the line as it stands (an implicit-return body), run the whole table, and quote it.

## Log
- 2026-10-17 filed by agent/claude-opus-5 (T-0404 author) from the prove-red run quoted in T-0404's Log.
