---
id: T-0009
title: Device pipeline proof: device/* push -> TestFlight on the phone in <= 40 min
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/ci_scripts/, .github/workflows/]
pins_affected: []
reviewer: null
depends_on: [T-0007, T-0010]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "git push origin device/T-0009 -> TestFlight build installable on the iPhone within 40 min (timed, logged)"
---
## Brief

Proves the only on-device iteration path this project has (no owned Mac). Blocked on T-0007 and T-0010.

## Log
