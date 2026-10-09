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
  - "Failure never fails the deletion (R6): `a PLANS failure never fails the deletion: <arm>` for {list throws for DEVICE, the first device swept, one delete throws, a page incomplete without a cursor}: 200 {deleted: true, revoke_pending: false, plans_pending: true}, the D1 apple_accounts table holds only the other user's row, and the KV store EQUALS the pre-store minus every key the arm could reach (whole)"
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
- 2026-10-09T03:00:23Z RED, code, GREEN (agent/claude-opus-5).
  RED first, against the T-0319 code with a stub src/planSweep.ts (PLAN_SWEEP_MAX_OPS and the interface only; the
  sweep returned true, unwired): `npx vitest run accountDeletePlans planReroute closuresCrossing accountDelete` ->
  Tests 63 failed | 125 passed (188). FAILED by name: all 8 `every plan key of the user's devices is gone, every other
  key unchanged: <session> x <store>` rows, the 3 `a PLANS failure never fails the deletion: ...` arms, `the sweep's
  operation bound: ...`, `the shipped ROUTES['/account'] sweeps env.PLANS across pages`, planReroute's `a foreign
  device cannot read another device's token: ...` (and every key-shape / DONE row of the existing files). The meta
  test `no row ignores its variant: ...` is test-side only and passed (as it must: it checks the table, not src).
  Ruling correction while green-ing: the `a page incomplete without a cursor` arm's expectation was wrong in the TEST
  (it took the first two USER keys, but the uppercase-token neighbour sorts first, so the fake's first page is
  [upper, T1]); now `user.test(k) && firstPage(device).includes(k)`. The code was right.
  GREEN: the six touched files 198/198; whole services/api vitest 81 files, Tests 2439 passed (2439);
  `python ops/lib/run-named-tests.py P-PRIV-04` -> NAMED P-PRIV-04 passed=68/68.
  Re-approved: identityVerifierPin.test.ts account.ts sha256 3c0cadcb...a790e -> edbb07f6...a69bb9 (sha256sum of
  src/account.ts); requestReadSites.test.ts account.ts lines (the R7 doc line split in two, and the three new lines
  naming user/bindings: devices, swept, the answer). index.ts untouched, so configAnswerPath's hash does not move.
  Mutants (`node test/mutate/siwaMutants.mjs --only=<12 ids>`, population mutations=136 floor 136): RESULT caught=12
  missed=0 of 12 - sweep-stops-on-empty-page (7, the holding rows), sweep-ignores-cursor (2: only `one delete
  throws` beside an authAppleFields timeout - the holding rows converged because deletes shift the first page, so a
  third undeletable neighbour under DEVICE's prefix was added: more than a page, and a cursor-ignoring sweep now
  spins to the bound), sweep-key-shape-prefix-only (7), sweep-delete-failure-ignored (`one delete throws`),
  sweep-list-failure-aborts (`list throws for DEVICE, the first device swept` - the arm was moved from SECOND_DEVICE
  to DEVICE before code because aborting at the LAST device is equivalent there), sweep-no-cursor-complete (`a page
  incomplete without a cursor`), sweep-deletes-unbounded, sweep-list-bound-off-by-one and sweep-bound-raised (the
  bound test: the second device left unlisted at exactly MAX ops; MAX < the Workers' 1000), acct-sweep-session-
  device-only (8), acct-sweep-pending-dropped (5), acct-sweep-unwired (9). Other names in the CAUGHT lists
  (authAppleFields `accepted: payload extra: ...`, `refused: header kid: ...`) are this box's 5 s timeouts under load.
  After the third neighbour (commit 042f117e): `--only=sweep-ignores-cursor` -> CAUGHT by 10 (all four `<session> x
  holding` rows among them), RESULT caught=1 missed=0. planMutants.mjs (population 65, floor 62): `--only=
  token-recall-any-device,token-remember-unkeyed` -> CAUGHT token-recall-any-device by `/plan reroute, empty, clear
  path, router honours: ...` (closuresCrossing), CAUGHT token-remember-unkeyed by `every answer remembers its pins and
  lambda under plan_token for 43200 s`; RESULT caught=2 missed=0 (the first attempt REFUSED on a non-green baseline -
  planCeiling's 120-curve property timing out beside the siwa run; re-run alone, green).
- 2026-10-09T03:40:18Z ACCEPTANCE RE-RUN on the merged head f6e8fce1 (origin/main e3de4d78, PR #215 T-0332 merged in;
  one conflict in planReroute.test.ts, a union of T-0326's foreign-device test and T-0332's reroute-exempt test).
  (1) RULED FIRST: commit db047780 carries R1-R9 and the acceptance before any code. (2) Key: planReroute.test.ts
  green inside the 259 below; `a foreign device cannot read another device's token: ...` bound. (3) Sweep cross
  product, (4) failure arms, (5) bound, (6) shipped wiring: accountDeletePlans.test.ts 14/14. Touched files on the
  merged head: `npx vitest run asnVerify accountDeletePlans accountDelete planReroute closuresCrossing
  identityVerifierPin requestReadSites` -> Test Files 7 passed (7), Tests 259 passed (259). Whole services/api suite
  on the merged head: 2416/2419, the 3 failures (configAnswerPath, sharedEnvWorker, waitlistDedupe) `Test timed out
  in 5000ms` under load plus one pool-start ECONNRESET; re-run alone: Test Files 3 passed, Tests 14 passed.
  (7) Pins: `python ops/lib/run-named-tests.py P-PRIV-04` -> NAMED P-PRIV-04 passed=68/68 (no Swift row in this
  entry, so nothing GRDB-gated is MISSING); `python ops/lib/check-pins-yaml.py` -> PINS-YAML ok pins=48 fields=387;
  account.ts hash and requestReadSites lines re-approved (green above); mutants quoted in the entries above.
  (8) RED first: quoted above. (9) `bash ops/lib/check-line-cap` -> P-SRC-02 none over 300 (Swift only); TS line
  counts: planSweep.ts 63, account.ts 160, planToken.ts 95, accountDeletePlans.test.ts 175, planReroute.test.ts 238;
  closuresCrossing.test.ts is 302 on origin/main already (T-0332's merge) and this branch changes one line in place;
  `bash ops/queue-check` -> QUEUE OK (326 tasks).
- 2026-10-09T04:14:42Z agent/claude-opus-5 (owner) rv1-t0326: acceptance row 4 re-quoted to name the shipped arm `list throws for DEVICE, the first device swept` (the Log's earlier entries unchanged); origin/main merged last (PR #217 T-0331: Tests/ScenicKitTests/Surprise, ops/mutate/session*.py - no overlap).
