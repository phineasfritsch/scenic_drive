---
id: T-0326
title: Account deletion sweeps PLANS - a deleted user's remembered plan tokens (device id, place, Worker-computed pins) are gone with the account, not after the 12 h TTL (P-PRIV-04)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T01:48:20Z
lease_expires_at: 2026-10-09T09:48:20Z
worktree: .worktrees/T-0326
branch: task/T-0326
exclusive: []
touches: [services/api/src/, services/api/test/, ops/lib/named-tests.json, pins/PINS.yaml, queue/]
pins_affected: [P-PRIV-04]
reviewer: null
depends_on: [T-0319]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

From T-0319 rv1 (PR #209) RECORDABLE, ruled out of T-0319 in its fix-round-1 Log. PLANS (src/planToken.ts) keeps
`plan:<token>` -> {device, place, pins, lambda} for PLAN_TOKEN_TTL_SECONDS (43200). The pins are route coordinates
the Worker computed, keyed to a device id: device-linked location data at rest. DELETE /account (P-PRIV-04,
src/account.ts + src/accountStore.ts) deletes every user-keyed D1 row and never touches KV, so a deleted user's rows
survive up to 12 h. Open questions the claimer RULES before acceptance:
(a) a key a deletion can enumerate - e.g. `plan:<device>:<token>` so recall rebuilds the key from the caller's
device (a foreign device then cannot even read the row) and deletion lists the prefix per device in USER_DEVICES;
KV list() is eventually consistent and paginated (cursor) - rule both;
(b) the KV interface grows list() and delete(); PlanTokenKv's fakes in planReroute.test.ts and closuresCrossing.test.ts
follow;
(c) src/account.ts is whole-file SHA-pinned by identityVerifierPin.test.ts - the diff re-approves that hash;
(d) a PLANS read/write failure must not fail the deletion (answer as revoke_pending does, or a new flag - rule it);
(e) accountDelete.test.ts gains a row: every PLANS key of every one of the user's devices gone, every other key
unchanged, compared whole; bind it under P-PRIV-04 and update the row's count in PINS.yaml.

## Log
- 2026-10-08T15:23:40Z filed by agent/claude-opus-5 (T-0319 owner, fix round 1) from rv1-t0319's P-PRIV-04 note.
- 2026-10-09T01:48:20Z claimed by agent/claude-opus-5; lease until 2026-10-09T09:48:20Z
