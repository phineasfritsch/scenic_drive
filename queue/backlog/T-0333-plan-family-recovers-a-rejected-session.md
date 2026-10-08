---
id: T-0333
title: Before IDENTITY_HEADERS closes, the plan family recovers a session the Worker cannot verify - the Worker signals an unverifiable Bearer (e.g. 401 session_rejected) on /plan, /trip and /loop, and the client drops the session, re-acquires once and retries, so a SESSION_JWT_SECRET rotation or SESSION_TTL_S change never downgrades a subscriber for the rest of the launch
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-STORE-02, P-COST-01, P-COST-04]
reviewer: null
depends_on: [T-0322]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0322 owner stillOpen 1 / rv2-t0322 note (PR #212): while IDENTITY_HEADERS is "1" an unverifiable Bearer now falls
back to the header (no downgrade). After the owner closes the flag (T-0322 R5 step 3), a Bearer the Worker cannot
verify reads anon, and PlanClient / TripClient / LoopClient have no 401 path, so nothing recovers within the launch.
This must land BEFORE step 3. MEASURE FIRST (what each route answers today for an unverifiable Bearer; whether a 401
costs a quota reservation - it must not; how many re-acquisitions per launch the session budget allows; P-COST-04's
request cap per plan), then write the acceptance: a full-equality table over {Bearer valid, expired, rotated secret,
wrong TTL, malformed} x {flag 1, closed} for the Worker answer, and for the client {401 once -> re-acquire + one retry,
401 twice -> no loop}.

## Log
- 2026-10-08T20:50:40Z filed by agent/claude-opus-5 (orchestrator) from T-0322 stillOpen 1.
