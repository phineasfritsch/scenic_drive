---
id: T-0037
title: P-SRC-02 will silently exempt apps/ios/Packages/ScenicApp Swift files once T-0010 lands
state: done
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T15:44:53Z
lease_expires_at: 2026-09-07T18:44:53Z
worktree: ../wt/T-0037
branch: task/T-0037
exclusive: []
touches: [ops/lib/check-line-cap]
pins_affected: []
reviewer: agent/rv2-pr88
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
- 2026-09-07T15:44:53Z claimed by agent/claude-opus-5; lease until 2026-09-07T18:44:53Z
- 2026-09-18T03:20:00Z addressed by [[T-0141]] (`ops/lib/check-line-cap` globs gain `apps/ios/**/*.swift`, demonstrated red with a 301-line file); moves to done/ when T-0141's PR merges, by its reviewer.
- 2026-09-18T18:20:00Z moved to done/ by agent/claude-fable-5-1: addressed by T-0141 (ops/lib/check-line-cap covers apps/ios/**/*.swift with a per-root guard that refuses by root name, demonstrated red), merged as PR #88 (e3bc79a) and reviewed there by agent/rv2-pr88 (round 2 PASS), recorded as reviewer for that reason. agent/reviewer-21 was assigned on 2026-09-07 and never reviewed it; the 2026-09-07 lease had expired.
