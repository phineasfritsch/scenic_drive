---
id: T-0035
title: P-SRC-02 line count is off by one when a file lacks a trailing newline (wc -l)
state: claimed
owner: agent/builder-2
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T15:01:42Z
lease_expires_at: 2026-09-07T17:01:42Z
worktree: ../wt/T-0035
branch: task/T-0035
exclusive: []
touches: [ops/lib/check-line-cap]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
- 2026-09-07T15:01:42Z claimed by agent/builder-2; lease until 2026-09-07T17:01:42Z
