---
id: T-0291
title: The identity-token content pin covers the JWKS fetch - appleClient.ts keys() decides which keys are trusted, so it joins the pinned verifier files
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T02:11:47Z
lease_expires_at: 2026-10-07T10:11:47Z
worktree: .worktrees/T-0291
branch: task/T-0291
exclusive: []
touches: [services/api/test/identityVerifierPin.test.ts, services/api/test/mutate/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-PRIV-04]
reviewer: null
depends_on: [T-0287]
verify: [ops/check-pins]
acceptance:
  - "identityVerifierPin.test.ts pins services/api/src/appleClient.ts by whole-file sha256 alongside appleIdentity.ts, appleJwks.ts, asnNotification.ts and account.ts; the import-closure test treats appleClient.ts as part of the verifier"
  - "rv4-t0287's mutant (keys() appends an attacker RS256 key to every 200 JWKS answer) is RED by name in the pin test, shown red then green in the Log; a siwaMutants entry for it with MIN_MUTATIONS raised by one"
  - "P-PRIV-04 named tests still pass by name (run-named-tests P-PRIV-04)"
---
## Brief

rv4-t0287 (PR #176 sign-off, recordable): ruling R-rv3-1 left appleClient.ts out of the content pin because it "acts
after acceptance". That is wrong for keys(), the JWKS fetch that decides which keys are trusted; today only the
whole-src requestReadSites whitelist catches a keys() backdoor. Memory runtime-read-recorder.

## Log
- 2026-10-07T01:50:18Z filed by agent/claude-opus-5 (orchestrator) from rv4-t0287's recordable on PR #176.
- 2026-10-07T02:11:47Z claimed by agent/claude-opus-5; lease until 2026-10-07T10:11:47Z
- 2026-10-07T02:17:43Z RULINGS before code (agent/claude-opus-5). R1 FILE LIST - T-0287's R-rv3-1 is overruled for
  appleClient.ts only: keys() is the JWKS fetch whose answer appleKey() turns into the set of trusted keys, so its bytes
  decide acceptance BEFORE the verifier runs; the whole file joins the sha256 table (exchange/revoke ride along, cost: an
  edit of a form post updates the hash in the same diff). accountStore.ts, sessionJwt.ts and index.ts stay OUT for
  R-rv3-1's reasons. The production fetch wrapper `appleClient((url, init) => fetch(url, init))` lives in account.ts,
  already pinned, so the whole key path from global fetch to keyFor is under the pin. R2 WHITELIST - SITE gains `keys`
  and `APPLE_JWKS_URL` (the JWKS fetch's names, part of "the key lookup"); the new approved lines are the measured lines
  of the unmutated tree, quoted in the test. R3 IMPORT CLOSURE - the closure test's roots become appleIdentity.ts,
  appleJwks.ts and appleClient.ts; appleClient.ts imports asnNotification.ts and appleJwks.ts, both pinned. R4 MUTANT -
  `rv4-keys-attacker-jwk` (appleClient.ts): keys() appends an attacker RS256 JWK (kid rv4, a fresh 2048-bit modulus,
  e AQAB) to every 200 {keys} answer and re-serialises it; every other status passes through. The default population
  runs without the pin (R-rv3-3) and is expected to catch it by requestReadSites (rv4's finding); RED/GREEN by name is
  shown with `--only=rv4-keys-attacker-jwk --with-pin`: before, no pin-test name; after, the pin-test names.
  MIN_MUTATIONS 123 -> 124. R5 NAMES - no test title changes, so P-PRIV-04's 51 names, ops/lib/named-tests.json and
  pins/PINS.yaml stay as they are (listed in touches:, not edited).
