---
id: T-0315
title: The app sends its paid-tier identity (x-scenic-account-token from the StoreKit entitlement, per T-0272) on plan, loop and trip requests, so a subscriber gets the full itinerary and per-day handoff, and a non-subscriber keeps the free preview
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T09:35:56Z
lease_expires_at: 2026-10-08T17:35:56Z
worktree: .worktrees/T-0315
branch: task/T-0315
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-STORE-02, P-COST-01]
reviewer: null
depends_on: [T-0272, T-0313, T-0310]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST: what the Worker's tier seam reads today (T-0272: x-scenic-account-token -> purchase id with a live entitlement; T-0278 R6 IDENTITY_HEADERS migration window) versus the session JWT path (T-0310), which one the app sends and when, where the token comes from (StoreKit 2 originalTransactionID / appAccountToken in the Keychain - plan, Entitlement row), and that it is never logged"
  - "Every request client (PlanClient, TripClient, LoopClient if present) attaches the identity by one shared function; table by full equality over {no purchase, live purchase, expired purchase, session present/absent}; the trip preview vs full itinerary follows the Worker's answer, never a client-side guess"
  - "ios-compile + ios-screenshot pass; digests re-approved; population entries MISSED before and CAUGHT by name after"
---
## Brief

rv1-t0313 recordable 1 / T-0313 owner stillOpen (PR #201): the app sends no x-scenic-account-token, so every trip is the
anon preview and the per-day Apple Maps handoff is unreachable. The plan's paid tier unlocks the full itinerary,
unlimited plans and navigation.

## Log
- 2026-10-08T06:32:40Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0313's recordable 1.
- 2026-10-08T09:35:56Z claimed by agent/claude-opus-5; lease until 2026-10-08T17:35:56Z
