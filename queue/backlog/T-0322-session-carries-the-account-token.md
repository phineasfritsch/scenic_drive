---
id: T-0322
title: The app's session carries the purchase - /attest and /assert send the appAccountToken so the session JWT has `act`, and plan, trip and loop move to the Bearer before IDENTITY_HEADERS closes, so no subscriber is downgraded to anon on that day
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, apps/ios/Packages/ScenicApp/Sources/, services/api/src/, services/api/test/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-STORE-02, P-PRIV-05]
reviewer: null
depends_on: [T-0315]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST: what /attest and /assert accept today for `act` (T-0278/T-0310), what SessionStore/AttestClient send, how the tier is read when a Bearer verifies (identifyCaller), and the order of the switch-over (session carries act -> clients send Bearer -> IDENTITY_HEADERS may close); a subscriber's tier is never lower during any step"
  - "Full-equality request tables for attest/assert over {no purchase, live, expired} and for plan/trip/loop over {session with act, session without act, no session}; the Worker's answer decides the tier, never the client"
  - "Digests re-approved; ios-compile + ios-screenshot pass; population entries MISSED before and CAUGHT by name after"
---
## Brief

rv1-t0315 recordable R3 / T-0315 owner stillOpen 1 (PR #206): today the paid tier reaches the Worker only through the
bare x-scenic-account-token header, which the Worker honours only while IDENTITY_HEADERS is "1". The session JWT has
no `act` because the app attests without one.

## Log
- 2026-10-08T12:24:40Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0315's recordable R3.
