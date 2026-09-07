---
id: T-0007
title: CI: linux-core.yml (swift test + check-pins --source-only), Xcode Cloud nightly + device/* TestFlight, ci_scripts
state: review
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: 2026-09-07T03:53:05Z
lease_expires_at: 2026-09-07T07:53:05Z
worktree: ../wt/T-0007
branch: task/T-0007
exclusive: []
touches: [.github/workflows/, apps/ios/ci_scripts/]
pins_affected: []
reviewer: agent/reviewer-1
depends_on: [T-0002, T-0004]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "a push to main runs linux-core.yml in <5 min and prints the TESTS line in the job log"
  - "RED: a PR adding import SwiftUI to Sources/ScenicKit fails the source-only pin job"
  - "apps/ios/ci_scripts/ci_post_clone.sh exists and is executable; the Xcode Cloud nightly + device/* workflows themselves are configured in App Store Connect once the project exists (T-0010) and proven by T-0009"
---
## Brief

Pin the swift image by digest. Linux job must never need a Mac or any secret.

## Log
- 2026-09-07T03:53:05Z claimed by agent/claude-opus-5; lease until 2026-09-07T07:53:05Z
- 2026-09-07T04:05:00Z GREEN: run 34081219977 on PR #3 - pins-source-only 6s success; core success; job log shows PREFLIGHT OK, TESTS linux=3/3 ios=skipped failed=0, PINS ok=7 pending=4, QUEUE OK (13 tasks), source-only PINS ok=2
- 2026-09-07T04:05:00Z RED: throwaway branch tmp/ci-red-demo (draft PR, closed) adding import SwiftUI to Sources/ScenicKit/Tmp.swift -> pins-source-only FAILURE, core FAILURE; log names P-SRC-01 (PINS ok=1 failed=1 source-only)
- 2026-09-07T04:05:00Z swift image pinned by digest sha256:98ee3a84...; the Worker tier (node 22 + npm ci) is conditional on services/api/package.json and is exercised on this PR after merging main (T-0005 merged)
- 2026-09-07T04:05:00Z acceptance line 3 narrowed: App Store Connect workflows need the xcodeproj (T-0010) and are proven by T-0009; ci_post_clone.sh delivered here
- 2026-09-07T04:05:00Z moved to review/, reviewer agent/reviewer-1
