---
id: T-0280
title: App Attest assertions renew a session without a new key, and /attest/challenge is rate-limited per device and globally
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/]
pins_affected: [P-COST-01]
reviewer: null
depends_on: [T-0278]
verify: [ops/test, ops/check-pins]
acceptance:
  - "POST /attest/assert verifies an App Attest assertion for an attested key per Apple's steps (CBOR {signature, authenticatorData}, nonce = SHA256(authenticatorData || SHA256(clientData)) where clientData carries a fresh single-use challenge, ECDSA P-256 over the nonce with the stored public key, rpIdHash, counter strictly greater than the stored counter and stored atomically) and issues a fresh session JWT; every defect (replayed counter, equal counter, unknown keyId, wrong key, stale challenge, rpId mismatch) a table row refused with zero state change, the stored counter compared in full"
  - "POST /attest/challenge is limited per device (ruled N per hour) and by a global daily ceiling, reserved before any D1 write; over the limit -> 429 with zero writes; tests through ROUTES at the exact limit and limit+1; KILL behaviour unchanged (D1-only route); the request-read whitelist extended by equality; a TS mutation population with a literal floor"
---
## Brief

T-0278 R9 out-of-scope items: 'per-request assertions (until they exist, renewing a session means attesting a new key)'
and 'a rate limit on /attest/challenge'. Copy T-0278's store/verify shapes.

## Log
- 2026-10-06T12:09:05Z filed by agent/claude-opus-5 (orchestrator) after PR #168 (T-0278) merged.
