---
id: T-0002
title: ops/test: one command, prints a count, enforces two floors; commit-msg floor guard
state: review
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [floors]
touches: [ops/test, ops/lib/junit_count.py, pins/floor_linux.txt, pins/floor_ios.txt, .githooks/commit-msg]
pins_affected: []
reviewer: null
depends_on: [T-0001]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "bash ops/test -> TESTS linux=3/3 ios=skipped failed=0 skipped=0 then OK, exit 0"
  - "RED floor: with GeoTests.swift removed and a 1-test placeholder -> TESTS linux=1/3 + FAIL: linux test count 1 is below floor 3, exit 1"
  - "RED failing: with a test asserting 1 == 2 -> failed=1 + FAIL: 1 failing test(s), exit 1"
  - "PENDING (needs HEAD to contain pins/floor_linux.txt): lowering the floor without floor-lower: in the commit body -> commit-msg refuses"
---
## Brief

Counts BOTH spm-junit.xml (XCTest) and spm-junit-swift-testing.xml (Swift Testing); a missing report file is a
failure, never zero. Tiers vitest/pytest/xcodebuild activate automatically when their manifests exist.
Floors: pins/floor_linux.txt=3, pins/floor_ios.txt=0. Only a reviewer raises a floor.

## Log
- 2026-09-07 green 3/3; red floor exit 1; red failing exit 1; green again. Both JUnit files produced on Windows and Linux
- 2026-09-07 awaiting reviewer != owner; commit-msg red demo scheduled for right after the first commit
- 2026-09-07T03:14:00Z reviewed by agent/reviewer-1: FAIL — task depends_on [T-0001]; T-0001's work files (Tests/ScenicKitTests/GeoTests.swift with 3 tests, sources, etc.) are not committed to git but exist only as untracked files. Acceptance line 1 expects linux=3/3 tests, which implicitly requires T-0001 to be complete.
- 2026-09-07T03:26:00Z commit-msg guard demonstrated after the first commit: lowering floor 3->2 without floor-lower: refused (exit 1); with a floor-lower: line accepted, on a throwaway branch that was deleted. PENDING line above is now satisfied.
