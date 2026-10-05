---
id: T-0267
title: the Worker serves POST /asn - App Store Server Notifications V2, signature chain verified, entitlement row set active/inactive per notification type (P-STORE-02)
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/]
pins_affected: [P-STORE-02]
reviewer: null
depends_on: [T-0256]
verify: [ops/test, ops/check-pins]
acceptance:
  - "POST /asn verifies the signedPayload JWS: ES256 over the x5c chain, the chain ending in a pinned Apple root (the root certificate's SHA-256 fingerprint a typed literal, sourced from apple.com/certificateauthority and quoted in the Log), leaf/intermediate OIDs and validity checked; any failure is 400 with ZERO state change - a table test over every defect (bad signature, chain to a self-made root, expired leaf, missing x5c, alg none/HS256, truncated JWS) built from a test-generated chain"
  - "entitlement state keyed on originalTransactionId (and appAccountToken when present), stored in D1 (a migration, not applied): SUBSCRIBED / DID_RENEW / OFFER_REDEEMED -> active; EXPIRED / REFUND / REVOKE / GRACE_PERIOD_EXPIRED -> inactive; DID_FAIL_TO_RENEW with subtype GRACE_PERIOD -> active until gracePeriodExpiresDate; every other type acknowledged 200 with no change - one test per type by name, the whole row compared by equality; notifications older than the stored signedDate never regress state (idempotent, out-of-order safe); environment Sandbox vs Production ruled"
  - "GET /entitlement (device header) answers the current state; no secret in the tree; vitest RED first; a TS mutation population with a literal floor; range/bound tables per the repo rule"
---
## Brief

Plan M6 'Entitlement: StoreKit 2; keyed on originalTransactionID + appAccountToken; App Store Server Notifications V2
-> Worker /asn; refunds revoke' and pin P-STORE-02 ('/asn sets entitlement inactive on EXPIRED/REFUND/REVOKE').
Code and tests only: no App Store Connect configuration, no deploy, no real Apple payloads. The test suite generates
its own ES256 chain; production pins Apple's published root by fingerprint. Copy T-0256's deps/D1 shapes.

## Log
- 2026-10-05T21:29:18Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 /asn).
