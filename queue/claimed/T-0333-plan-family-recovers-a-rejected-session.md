---
id: T-0333
title: Before IDENTITY_HEADERS closes, the plan family recovers a session the Worker cannot verify - the Worker signals an unverifiable Bearer (e.g. 401 session_rejected) on /plan, /trip and /loop, and the client drops the session, re-acquires once and retries, so a SESSION_JWT_SECRET rotation or SESSION_TTL_S change never downgrades a subscriber for the rest of the launch
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T10:41:55Z
lease_expires_at: 2026-10-09T20:41:55Z
worktree: .worktrees/T-0333
branch: task/T-0333
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-STORE-02, P-COST-01, P-COST-04]
reviewer: null
depends_on: [T-0322]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 Worker table, through the SHIPPED ROUTES: sessionCarriesAct.test.ts's cross product /plan,/trip,/loop x Bearer {session act live, act expired, no act, expired, wrong secret, wrong TTL, malformed, absent} x IDENTITY_HEADERS {1, unset} x header {live, expired, absent} EQUALS the reference `ruled` picks, where ruled gains `rejected` exactly for the four unverifiable Bearers under unset; the rejected reference is the literal {401, {error: session_rejected}} with the SEEDED quota state, zero upstream fetches and nothing logged; the no-row-ignores-its-variant meta-test covers the new value. Plus `a rejected Bearer reserves nothing` over an EMPTY quota namespace: route x the four unverifiable Bearers x flag - unset is 401 with quota state {} and 0 fetches, 1 equals the header reference (the device bucket reserved). sessionIdentity.test.ts's flag-closed rows read 401 too. `npx vitest run test/sessionCarriesAct.test.ts test/sessionIdentity.test.ts test/requestReadSites.test.ts` green."
  - "A2 Client table, through the SHIPPING PlanClient (plan and reroute), TripClient and LoopClient over a REAL SessionStore and one ScriptedTransport: route x held {Keychain session (acquisition unspent), session acquired this launch (spent)} x Worker {200, 401 then 200, 401 then 401} - the WHOLE ordered request list (attest and route) EQUALS the list recomputed from the variant: 401 once -> the token handed back, ONE acquisition, the byte-identical body resent ONCE with the new Bearer; 401 twice -> exactly two route requests, never a third, no second re-acquisition; a request that carried no Bearer is never retried; meta-test that no row ignores held or Worker. `swift test --filter PlanSessionRetryTests` green."
  - "A3 RED first by name: every new or changed test FAILED by name before the code commit (quoted in the Log), then green."
  - "A4 Population: attestMutants.mjs gains the Worker 401 entries (no 401, 401 under the flag, 401 after the reservation, a 401 for an absent header) and ops/mutate/session_mutations.py the client entries (no retry, retry without the hand-back, re-grant every rejection, never re-grant, retry a Bearer-less request), each CAUGHT by name; floors raised; `python ops/lib/check-mutate-population.py` green."
  - "A5 Gates on the merged head: `python ops/lib/run-named-tests.py P-STORE-02` and `P-COST-04` all passed; digests re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt and every content pin over a touched file re-approved; check-pins-yaml; queue-check; apps/ios untouched (no Apple CI)."
---
## Brief

T-0322 owner stillOpen 1 / rv2-t0322 note (PR #212): while IDENTITY_HEADERS is "1" an unverifiable Bearer now falls
back to the header (no downgrade). After the owner closes the flag (T-0322 R5 step 3), a Bearer the Worker cannot
verify reads anon, and PlanClient / TripClient / LoopClient have no 401 path, so nothing recovers within the launch.
This must land BEFORE step 3. MEASURE FIRST (what each route answers today for an unverifiable Bearer; whether a 401
costs a quota reservation - it must not; how many re-acquisitions per launch the session budget allows; P-COST-04's
request cap per plan), then write the acceptance: a full-equality table over {Bearer valid, expired, rotated secret,
wrong TTL, malformed} x {flag 1, closed} for the Worker answer, and for the client {401 once -> re-acquire + one retry,
401 twice -> no loop}.

## Log
- 2026-10-08T20:50:40Z filed by agent/claude-opus-5 (orchestrator) from T-0322 stillOpen 1.
- 2026-10-09T10:41:55Z claimed by agent/claude-opus-5; lease until 2026-10-09T20:41:55Z
- 2026-10-09T10:58:00Z MEASURED (agent/claude-opus-5, worktree at 322d5ed0). A scratch vitest probe (deleted, never
  committed) drove ROUTES /plan, /trip, /loop with SESSION_JWT_SECRET set, x-scenic-device DEVICE, no account header,
  an EMPTY fake quota, each unverifiable Bearer {expired, wrong secret, wrong TTL, malformed} x flag {1, unset}. All 24
  rows answer 200 routed. Flag "1": billed to the device bucket (`device:0f8b6d5e-...` plan:1 / trip:1 / loop:1).
  Flag unset: billed to the SHARED bucket, e.g.
  `PROBE /plan | wrong secret | flag unset | 200 routed | fetches 7 | quota {"device:unidentified":{"daily":{"day":"2026-10-06","plan":1,"loop":0}},"global":{"monthly":{"month":"2026-10","calls":12}}}`
  `PROBE /trip | malformed | flag unset | 200 routed | fetches 7 | quota {"device:unidentified":{"daily":{"day":"2026-10-06","plan":0,"loop":0,"trip":1}},"global":{"monthly":{"month":"2026-10","calls":12}}}`
  `PROBE /loop | expired | flag unset | 200 routed | fetches 1 | quota {"device:unidentified":{"daily":{"day":"2026-10-06","plan":0,"loop":1}},"global":{"monthly":{"month":"2026-10","calls":3}}}`
  and the same per route for every unverifiable kind. So TODAY a closed flag plus a rotated secret silently downgrades
  a subscriber to the shared anon bucket AND spends a reservation there (7 / 7 / 1 upstream requests). Client today:
  PlanClient, TripClient and LoopClient hand any status to their reader; a 401 is the reader's default (no retry);
  SessionStore spends ONE acquisition per purchase value per launch (`spent`), so a session acquired this launch and
  then rejected cannot be renewed within it. Budgets: ATTEST_CHALLENGES_PER_DEVICE_HOUR = 10 and
  ATTEST_CHALLENGES_PER_DAY = 10000 (attestStore.ts); P-COST-04 caps upstream requests PER PLAN at PLAN_UPSTREAM_COST
  12 / LOOP_UPSTREAM_COST 3 / TRIP_UPSTREAM_COST 12, reserved in guardedPlan before the first fetch.
- 2026-10-09T10:58:00Z RULED before code:
  R1 Worker: with SESSION_JWT_SECRET set and IDENTITY_HEADERS not "1", a /plan, /trip or /loop request whose
     `authorization` header is present but yields no verified claims (expired, another secret, another TTL, malformed,
     or not the Bearer scheme) is 401 {"error":"session_rejected"}. The order up to the identity is unchanged (kill,
     method, body, region, deps, place); the 401 is answered right after identify and BEFORE any plan-token recall,
     reservation, upstream request or log. Under "1" T-0322's fallback stands (the header identity). No header:
     unchanged. Without the secret: unchanged, never 401. Only the plan family: a new identifySession returns the
     rejection; identifyCaller (telemetry, waitlist) maps it to today's unidentified anon, unchanged; routerDeps'
     identify marks the identity `rejected`, which the three handlers answer.
  R2 Cost: a 401 reserves nothing and makes zero upstream requests - shown on a bucket at its limit (the table) AND on
     an empty quota (where a reserve-then-401 would show in the state). P-COST-04 is per plan and unchanged: the
     resent request is its own plan with its own reservation; per user action at most one plan reserves.
  R3 Client: PlanSessionProvider gains planSessionRejected(_ token:). A reply with status 401 to a plan-family request
     that CARRIED a Bearer hands that token back, asks planSession(account:) again for the same purchase, and resends
     the byte-identical body ONCE with the answer (a Bearer, or none); that reply is final and read by the route's
     reader whatever it is. Never a third request; a 401 to a Bearer-less request is not retried. The resend carries
     the same single 2-dp coordinate in identical bytes, refused unused the first time, so the server learns no second
     coordinate: CLAUDE.md's one-coordinate-per-user-action invariant holds.
  R4 Budget: SessionStore.planSessionRejected drops the session as sessionRejected does and, the FIRST time in a launch
     for that purchase value, returns the value's acquisition (un-spends it), so the next ask acquires once more; a
     second plan-family rejection for the same value in the launch drops without granting. At most 2 acquisitions
     (challenges) per purchase value per launch, under the 10 per device-hour limit. A token no longer current is
     ignored. The ledger's sessionRejected is unchanged (no re-grant).
  R5 The Brief's "e.g. 401 session_rejected" is ruled as exactly that literal. The Brief's client table {401 once,
     401 twice} is crossed with held {unspent, spent}, because the spent case is the one today's store cannot recover.
