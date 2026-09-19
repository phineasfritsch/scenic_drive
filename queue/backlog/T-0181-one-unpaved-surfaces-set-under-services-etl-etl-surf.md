---
id: T-0181
title: one UNPAVED_SURFACES set under services/etl/etl - surface.py owns it, assemble.py imports it, the Gates.swift anchor moves with the set
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/assemble.py, services/etl/etl/surface.py, services/etl/tests/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0146, T-0173]
verify: [ops/test, ops/check-pins]
acceptance:
  - "grep -rn 'UNPAVED_SURFACES' services/etl/etl prints exactly ONE definition (surface.py) and imports elsewhere; test_assemble.py's _swift_set anchor on Sources/ScenicKit/Gates/Gates.swift asserts the SAME set - RED by name when one value is removed from either side"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From the 18:13 panel (CODE F2, grounded): main has exactly one unpaved list (Gates.swift:80-82); PR #102 adds
`assemble.UNPAVED_SURFACES` (anchored on Gates.swift by regex) and T-0173 adds `surface.UNPAVED_SURFACES`
(anchored on a typed plan:80 list); neither imports the other, and P-PROD-01's assertion is still TODO. Decided
by merge order today; fixed here after both land, not as a round on either PR.

## Log
- 2026-09-19T00:57:37Z filed by agent/claude-fable-5-1 from the 18:13 panel's grounded synthesis. Not started.
