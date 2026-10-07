---
id: T-0304
title: /ledger holds the "session sub only" identity by behaviour (not only by the request-read whitelist) and caps each user's writes per day
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/ledger.ts, services/api/test/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-PRIV-04, P-COST-01]
reviewer: null
depends_on: [T-0302]
verify: [ops/check-pins]
acceptance:
  - "Behaviour rows through worker.fetch: a session signed {sub: USER_A, apple: X} answers USER_A's rows; the same session plus x-scenic-device: USER_B answers USER_A's rows; an act claim changes nothing - full equality; rv1-t0302's rv-user-is-apple-claim and fm-t0302's get-scoped-by-legacy-device-header are CAUGHT by these rows by name, not only by requestReadSites"
  - "RULE then implement a per-user daily write cap on POST /ledger (a number with its reason, e.g. the paid tier's Surprise ceiling); the cap+1th write answers 429 with the table unchanged; range table at cap-1, cap, cap+1 and across the UTC midnight"
  - "Population entries for both, MISSED before and CAUGHT by name after; new PINS.yaml text double-quoted (memory pins-yaml-strict)"
---
## Brief

rv1-t0302 recordables (a) and (b) on PR #191: identity is held only by the exact-line whitelist against an apple/act
claim or a header beside a valid Bearer; and POST /ledger has no per-user write cap (author marked NOT CLOSED).

## Log
- 2026-10-07T17:44:38Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0302's recordables.
