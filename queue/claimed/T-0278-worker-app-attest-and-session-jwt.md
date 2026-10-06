---
id: T-0278
title: the Worker serves POST /attest - Apple App Attest attestation verified server-side (CBOR attestation object, x5c chain to the pinned Apple App Attestation Root CA, nonce, rpId = App ID hash, counter), then a short-lived session JWT; device identity and tier read from the JWT instead of bare headers
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T09:02:09Z
lease_expires_at: 2026-10-06T23:02:09Z
worktree: .worktrees/T-0278
branch: task/T-0278
exclusive: []
touches: [services/api/]
pins_affected: [P-COST-01, P-PRIV-05]
reviewer: null
depends_on: [T-0256, T-0272]
verify: [ops/test, ops/check-pins]
acceptance:
  - "POST /attest/challenge issues a single-use nonce (KV or DO, TTL ruled); POST /attest verifies the attestation per Apple's documented steps - fmt apple-appattest, x5c chain to the Apple App Attestation Root CA pinned by SHA-256 fingerprint fetched from Apple's published PEM (quote URL + value; fail closed if unverifiable), nonce = SHA256(authData || clientDataHash) in the leaf's 1.2.840.113635.100.8.2 extension, rpIdHash = SHA256(teamID.bundleID) (a typed constant, team id PLANNED until the owner supplies it), counter 0, aaguid appattestdevelop/production ruled - every defect a table row refused with zero state change; tests use a test-generated chain"
  - "a verified key yields an HS256 (or ES256, ruled) session JWT (secret from env, absent -> /attest 503 and every identity falls back to today's anon behaviour), short TTL; identify() reads device id from the JWT's sub and the tier from the entitlement bound to it; the bare x-scenic-device / x-scenic-account-token paths stay for a ruled migration window behind a flag - all through ROUTES by full equality, the requestReadSites whitelist extended by equality"
  - "assertions (per-request App Attest assertions) are OUT of scope - recorded; a TS mutation population with a literal floor; no secret in the tree"
---
## Brief

Plan Auth: 'App Attest anon-first -> own JWT'. T-0272 R5: the appAccountToken is a bearer secret until App Attest +
JWT exist; T-0256 R2: device ids are unattested. This is the server half only - the app's DCAppAttestService call is a
later Apple-package task (needs the App Attest entitlement, owner).

## Log
- 2026-10-06T08:58:52Z filed by agent/claude-opus-5 (orchestrator) from the plan's Auth row and T-0272 R5.
- 2026-10-06T09:02:09Z claimed by agent/claude-opus-5; lease until 2026-10-06T23:02:09Z
