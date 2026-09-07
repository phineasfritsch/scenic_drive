---
id: T-0007
title: CI: linux-core.yml (swift test + check-pins --source-only), Xcode Cloud nightly + device/* TestFlight, ci_scripts
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.github/workflows/, apps/ios/ci_scripts/]
pins_affected: []
reviewer: null
depends_on: [T-0002, T-0004]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "a push to main runs linux-core.yml in <5 min and prints the TESTS line in the job log"
  - "RED: a PR adding import SwiftUI to Sources/ScenicKit fails the source-only pin job"
  - "Xcode Cloud: nightly test workflow and a device/* archive+TestFlight workflow exist (needs T-0010 for the project)"
---
## Brief

Pin the swift image by digest. Linux job must never need a Mac or any secret.

## Log
