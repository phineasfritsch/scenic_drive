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
acceptance:
  - "RULED FIRST (Log 2026-10-09T01:53:13Z, R1-R9) and committed before any code: the measured key shape, recall, what DELETE /account deletes, KV list() semantics in the runtime and in the fakes"
  - "Key (R1): PLANS keys are `plan:<device>:<token>`; remember() writes under the plan's device, recall(device, token) reads ONLY the caller's own key. planReroute.test.ts `a foreign device cannot read another device's token: its one read is its own key and it answers the fresh plan` - a record stored under device-2's key, rerouted by device-1 with that token, answers EXACTLY the fresh plan's whole answer and kv.reads EQUALS [`plan:device-1:<token>`]; the remember put's key EQUALS `plan:device-1:<minted>` (existing `every answer remembers ...` test, whole put)"
  - "Sweep (R2-R5), a cross product, test/accountDeletePlans.test.ts `every plan key of the user's devices is gone, every other key unchanged: <session> x <store>` for sessions {apple claim, act only, apple claim with the device unbound, no claims with the device unbound} x stores {empty, holding}: the KV store after DELETE /account EQUALS (whole, sorted entries) the store before minus exactly the keys the TEST's own predicate `^plan:(<device set of the row>):<lowercase uuid>$` selects, where the device set is a function of the session row; the answer EQUALS {deleted: true, revoke_pending: false, plans_pending: false}. The fake lists in pages of 2 with an EMPTY page (list_complete false) after the first, cursor-continued, so a sweep that stops on an empty page or ignores the cursor leaves keys. The holding store carries neighbours that must survive: OTHER_DEVICE's plans, `plan:unidentified:<t>`, a legacy `plan:<t>`, `plan:<DEVICE>:<t>:x`, `plan:<DEVICE>:<T uppercase>`, `plan:<DEVICE>0:<t>`, `quota:<DEVICE>`. Meta: `no row ignores its variant: ...` - the expected holding-store sweep differs between the two device sets and the empty store's is empty"
  - "Failure never fails the deletion (R6): `a PLANS failure never fails the deletion: <arm>` for {list throws for SECOND_DEVICE, one delete throws, a page incomplete without a cursor}: 200 {deleted: true, revoke_pending: false, plans_pending: true}, the D1 apple_accounts table holds only the other user's row, and the KV store EQUALS the pre-store minus every key the arm could reach (whole)"
  - "Bound (R7): `the sweep's operation bound: PLAN_SWEEP_MAX_OPS operations finish, one more leaves plans_pending` - an unbound device holding MAX-1 plan keys (1 list + MAX-1 deletes = MAX ops) answers plans_pending false with none left; holding MAX keys answers plans_pending true with exactly one left and exactly MAX operations made"
  - "Shipped wiring (R8): `the shipped ROUTES['/account'] sweeps env.PLANS across pages` - ROUTES['/account'] with SESSION_JWT_SECRET and a paginating PLANS fake in env: the same whole-store equality; PLANS unbound answers plans_pending false (every existing accountDelete row, DONE now carrying plans_pending: false)"
  - "Pins (R9): the 15 new names bound under P-PRIV-04 in ops/lib/named-tests.json; PINS.yaml P-PRIV-04 says the row binds SIXTY-EIGHT tests and records the NOT ASSERTED residue (KV eventual consistency, a racing /plan, the unidentified bucket); identityVerifierPin.test.ts's account.ts hash re-approved; requestReadSites lines re-approved only if a src change moves them; siwaMutants.mjs gains planSweep/account entries (SUBJECTS + MIN_MUTATIONS), each run --only and CAUGHT by name, quoted in the Log"
  - "RED first: the new tests run against the T-0319 code and FAIL by name before src changes (quoted in the Log); then green"
  - "Gates on the merged head: the touched vitest files, python ops/lib/run-named-tests.py P-PRIV-04 (GRDB-gated Swift rows MISSING on Windows quoted), check-pins-yaml, check-line-cap, queue-check"
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
- 2026-10-09T01:53:13Z MEASURED and RULED before any code (agent/claude-opus-5).
  Measured: src/planToken.ts writes `plan:<token>` (KEY_PREFIX + token) with {device, place, pins, lambda},
  expirationTtl 43200; recall(token) reads that one key; src/plan.ts then requires recalled.device === who.userId.
  PlanTokenKv is {get, put}. DELETE /account (src/account.ts handleDeleteAccount) reads userBindings (USER_BINDINGS:
  every apple_accounts row of the user's subs), revokes, then deleteUser's one D1 batch; it never touches KV.
  USER_DEVICES = the session sub UNION every device_id bound to USER_SUBS = {sub} + userBindings' deviceIds, so the
  device set is computable in the Worker from what the handler already read. Device ids: a session sub is a lowercase
  UUID (attest.ts `UUID.test(sub)`); the legacy header is DEVICE_ID (lowercase UUID) else `unidentified`.
  services/api/wrangler.jsonc binds NO kv_namespaces - PLANS is unbound in every deployed environment (index.ts:
  "not bound in wrangler.jsonc"), so no `plan:<token>` row exists anywhere. KV list() (Workers runtime):
  list({prefix, cursor?, limit<=1000}) -> {keys: [{name, expiration?, metadata?}], list_complete, cursor?}, keys in
  lexicographic order; a page can hold FEWER keys than the limit - even zero - while list_complete is false, so a
  loop ends on list_complete only. list() and delete() are eventually consistent across locations (a write elsewhere
  may be unlisted for ~60 s; a deleted value may be served from another location's cache for ~60 s). The fakes:
  planReroute.test.ts and closuresCrossing.test.ts fake {get, put} only; miniflare's KV is read-your-writes.
  Population: DAILY_PLAN_QUOTA.paid = 200 /plan per device per UTC day (a reroute is a /plan), a 12 h TTL spans at
  most two UTC days -> <= 400 live keys per device; a Worker invocation may make 1000 KV operations.
  R1 (a) key: `plan:<device>:<token>`; remember() keys by plan.device; recall(device, token) builds the key from the
  CALLER's device (plan.ts passes who.userId), so a foreign device reads only its own key and gets null; the stored
  device check stays. Injective: a token is PLAN_TOKEN (no ':'), so the key's last 36 chars are the token.
  R2 no migration of `plan:<token>`: none exists (PLANS never bound); recall stops reading that shape.
  R3 (b) interfaces SPLIT, not grown: PlanTokenKv stays {get, put} (the /plan path never lists or deletes, so its
  fakes change only the key); the sweep takes a new PlanSweepKv {list, delete} in src/planSweep.ts. KVNamespace
  satisfies both. AccountEnv/AccountDeps gain PLANS / plans (null when unbound); index.ts is untouched (Env already
  carries PLANS?: KVNamespace and ROUTES['/account'] hands env to accountDepsFromEnv), so configAnswerPath's index.ts
  hash does not move.
  R4 the device set = unique sorted [session sub, ...userBindings deviceIds] - exactly USER_DEVICES; the sweep runs
  AFTER deleteUser succeeds (a D1 failure stays 503 with nothing swept; the repeat sweeps).
  R5 pagination: per device list({prefix: `plan:<device>:`}) then list({prefix, cursor}) until list_complete; a key
  is deleted only when it is the prefix plus a PLAN_TOKEN (whitelist of the key shape: `plan:<dev>:<t>:x`, an
  uppercase token, another device whose id extends this one are never deleted). Deletes of a page run concurrently.
  R6 (d) a new flag, not revoke_pending (which means Apple's revocation): the answer is {deleted, revoke_pending,
  plans_pending}; plans_pending is true when any list or delete threw, or a page said incomplete without a cursor,
  or R7's bound stopped the sweep; the deletion still answers 200. PLANS unbound -> plans_pending false (nothing is
  stored). The app decodes neither flag yet (no Swift reads revoke_pending), so the added key breaks no client.
  R7 bound: PLAN_SWEEP_MAX_OPS = 900 KV operations (lists + deletes), under the 1000-per-invocation limit; one paid
  device's <= 400 keys fit; past the bound plans_pending is true, a repeat DELETE (idempotent) continues, and the
  rest expire within 43200 s.
  R8 eventual consistency, ruled honestly: the sweep deletes every key list() returns; a plan written at another
  location in the ~60 s before the deletion, or by a /plan racing it, may be unlisted and survives to its TTL
  (<= 12 h); a deleted key may be served to ITS OWN device's recall from another location's cache for ~60 s.
  plans_pending cannot see either. Recorded in P-PRIV-04's NOT ASSERTED. The `unidentified` bucket's plans carry
  no person's device id; a session sub is always a UUID, so a deletion never lists it - not a user row (as waitlist).
  R9 (c)/(e) account.ts's whole-file hash is re-approved in identityVerifierPin.test.ts in the same diff; the new
  tests live in a new file accountDeletePlans.test.ts (accountDelete.test.ts is 180 lines; its DONE gains
  plans_pending: false); P-PRIV-04 binds them by name, 53 -> 68.
