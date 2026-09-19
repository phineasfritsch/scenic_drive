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
- 2026-09-18T20:57:28Z DEVICE CHECKLIST additions from the 14:13 panel's two focus drivers (grounded): on the FIRST real handoff
  from a phone, record (1) the duration Apple Maps quotes for the Skyline loop - the only honest source for a
  minutes figure on the home screen; two panel lenses guessed "~2h30" and "about an hour", which is why the
  title carries none; (2) whether Apple Maps announces an ARRIVAL at the pin on the Cañada Road / CA-92 corner
  (a waypoint placed on a junction can read as a stop); (3) whether it climbs CA-92 to CA-35 as intended or
  drops to I-280 and comes up CA-84 - the shortcut the ridge-leg pin in T-0151 exists to close.
- 2026-09-19T00:49:41Z LA FIRST, by agent/claude-fable-5-1 (the owner lives in Los Angeles - memory user-lives-in-la): DEVICE CHECKLIST addition: the first real handoff the owner takes is the LA drive (T-0178), not Skyline - Skyline is checked on a desk in Apple Maps or Google Maps; record the LA loop's duration the same way.
