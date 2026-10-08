---
id: T-0323
title: P-STORE-02 asserts the app's side of the paid tier - the AccountToken suites bound by name, and a whitelist guard that confines the x-scenic-account-token identifier to IdentityHeaders so a fourth client cannot inline it
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, ops/check-pins, pins/PINS.yaml, Tests/ScenicAPIClientTests/]
pins_affected: [P-STORE-02]
reviewer: null
depends_on: [T-0315]
verify: [ops/check-pins]
acceptance:
  - "pins/PINS.yaml P-STORE-02 no longer says the app side is NOT ASSERTED; AccountTokenHeaderTests and AccountTokenCandidateTests are bound by name in ops/lib/named-tests.json (quoted strings per memory pins-yaml-strict); run-named-tests seen red with one mutant, then green"
  - "A guard under ops/lib refuses any occurrence of the header name string outside its approved site(s) in Sources/ and apps/ios (WHITELIST of sites, whole-line per memory source-guards-fail-closed, never a blacklist of spellings); prove-red rows: an inlined header in a new client file, and the identifier split across a concatenation if the guard claims to see it - each refused by name"
  - "R1 of rv1-t0315 ruled in the Log: whether StoreKitAccountToken (Apple-only) gets a behavioural oracle (an Apple-side test target) or stays digest-pinned, with the reason"
---
## Brief

rv1-t0315 recordables R1, R2 and R4 (PR #206).

## Log
- 2026-10-08T12:24:40Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0315's recordables R1, R2, R4.
