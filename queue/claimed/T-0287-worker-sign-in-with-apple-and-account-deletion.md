---
id: T-0287
title: the Worker serves POST /auth/apple (Sign in with Apple identity token verified against Apple's JWKS) and DELETE /account (every user_id row gone, Apple token revoked) - P-PRIV-04's server half
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T19:00:09Z
lease_expires_at: 2026-10-07T07:00:09Z
worktree: .worktrees/T-0287
branch: task/T-0287
exclusive: []
touches: [services/api/, pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-PRIV-04, P-PRIV-05]
reviewer: null
depends_on: [T-0278]
verify: [ops/test, ops/check-pins]
acceptance:
  - "POST /auth/apple verifies the identity token per Apple's documented steps: RS256 against a key from https://appleid.apple.com/auth/keys selected by kid (fetched and cached with a ruled TTL; an unknown kid triggers one refetch, never a fallback key), iss https://appleid.apple.com, aud = the app's bundle id (typed constant), exp/iat bounds, nonce = SHA256(the session-bound nonce) - every defect a table row refused with zero state change; tests use a test-generated RSA key served by an injected JWKS fetcher; on success the Apple 'sub' is bound to the session's device (D1 migration, not applied) and the session JWT gains it"
  - "DELETE /account (authenticated by the session JWT) deletes EVERY row keyed by the user across ALL D1 tables (a test enumerates the migrations' tables and asserts zero rows for that user afterwards - a new table added later without a delete fails this test by name), calls Apple's /auth/revoke through an injected client (client secret is an owner secret; absent -> deletion still completes and the response says revoke_pending), and is idempotent; P-PRIV-04 registered or extended with these tests by name"
  - "no secret in the tree; the request-read whitelist extended by equality; a TS mutation population with a literal floor; table tests at every bound"
---
## Brief

Plan Auth: 'Sign in with Apple only; deletion calls /auth/revoke' and pin P-PRIV-04 (account deletion <= 3 taps, all
user_id rows gone, /auth/revoke called). Server half only; the app's SIWA button and the 3-tap Settings flow are an
Apple-package task (needs the SIWA entitlement, owner). No deploy.

## Log
- 2026-10-06T18:55:41Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 SIWA + deletion).
- 2026-10-06T19:00:09Z claimed by agent/claude-opus-5; lease until 2026-10-07T07:00:09Z
