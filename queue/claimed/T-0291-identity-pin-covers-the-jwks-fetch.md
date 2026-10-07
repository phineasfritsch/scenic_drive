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
