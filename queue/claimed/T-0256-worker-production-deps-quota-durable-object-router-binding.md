---
id: T-0256
title: Worker production deps - Durable Object quota counters, the ROUTER_URL binding with the secret header, a place resolver, so /plan and /loop stop answering 503 planning_unavailable when the bindings exist
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T12:16:14Z
lease_expires_at: 2026-10-06T00:16:14Z
worktree: .worktrees/T-0256
branch: task/T-0256
exclusive: []
touches: [services/api/]
pins_affected: [P-COST-01, P-COST-02, P-COST-03]
reviewer: null
depends_on: [T-0248, T-0252]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a Durable Object class (one type per file) implements upstream.ts's Counters - reserve-before-call per device per UTC day by tier (anon 3 / free 10 / paid 200 from quota.ts, never a second copy of the numbers) and the monthly MAX_MONTHLY_UPSTREAM_CALLS ceiling - plus a per-kind daily allowance so a free loop is 1/day (plan table) without spending a plan; tested through the shipping handlers over an in-memory DurableObjectState fake by EXACT equality of the counter state after each call"
  - "planDepsFromEnv and the /loop deps factory return real deps exactly when DO binding, ROUTER_URL and the ROUTER_SECRET secret are all present, and still null (503 planning_unavailable, zero upstream) when ANY one is missing - a test per missing binding by name; every upstream fetch carries the secret header (P-COST-03), asserted on the recorded request"
  - "a place resolver for /plan's destination id over the D1 binding (or a ruled bundled table), unknown id 404 with zero upstream calls unchanged"
  - "wrangler.jsonc gains the DO binding + migration and ROUTER_URL as a var with a non-routable placeholder; no secret in the tree; the KILL switch reads KV if bound and the existing env var otherwise (ruled); vitest count quoted RED first then green; a TS mutation population entry for the DO counter arithmetic with a literal floor"
---
## Brief

T-0248 and T-0252 shipped /plan and /loop with injected deps; production answers 503 planning_unavailable because
`planDepsFromEnv` returns null (T-0248 stillOpen 1; T-0252 R10). This task makes the Worker deployable the moment the
owner binds a router and runs `wrangler deploy` - it does NOT deploy, create Cloudflare resources or touch secrets.
Also closes T-0252's stillOpen 'loop quota has no kind'. Copy the shapes of services/api/src/upstream.ts and quota.ts.

## Log
- 2026-10-05T12:14:20Z filed by agent/claude-opus-5 (orchestrator) after PR #143 (T-0252) merged.
- 2026-10-05T12:16:14Z claimed by agent/claude-opus-5; lease until 2026-10-06T00:16:14Z
- 2026-10-05T12:32:55Z **RULED before code** (agent/claude-opus-5, owner). Baseline: `npx vitest run` in services/api at 1b525f3 = `Tests 209 passed (209)`.
  - **R1 the DO id scheme.** One class `QuotaCounter` (src/QuotaCounter.ts, binding `QUOTA`, sqlite-backed migration tag v1). Per device: `idFromName("device:" + deviceId)` holds ONE record `daily = {day, plan, loop}` (a new UTC day resets it in place, so no key ever accumulates). Across everyone: `idFromName("global")` holds `monthly = {month, calls}`. Two instances, because a per-device object cannot see everyone's month and a single global object would serialise every device's daily count through one object for no gain.
  - **R2 the device id source, honestly.** There is no App Attest yet, so nothing the server holds can prove which device is calling. The id is the app's install UUID sent as header `x-scenic-device` (RFC 4122 shape, lowercased). A request without it, or with anything not of that shape, is counted in ONE shared bucket `device:unidentified` - every header-less caller shares one anon allowance, which fails closed on cost. KNOWN GAP, not hidden: a client that rotates UUIDs gets a fresh anon allowance each time; the only bound on that is the monthly ceiling (P-COST-02, 90% of 250,000 calls). App Attest is what closes it. The UUID is not a coordinate; P-PRIV-05's one-coordinate rule is untouched.
  - **R3 how tier is known.** It is not: no /attest, no JWT. Every caller is `anon` (DAILY_PLAN_QUOTA.anon = 3). A tier read from a client header would be self-promotion, so none is read.
  - **R4 the per-kind allowance.** `QuotaKind = "plan" | "loop"`. quota.ts gains `DAILY_LOOP_QUOTA = { anon: 1, free: 1, paid: DAILY_PLAN_QUOTA.paid }`: the plan table says Loop free 1/day, paid Unlimited; anon is not in the table and gets the free figure; "Unlimited" is ruled as the paid PLAN cap by reference (a counter needs a finite limit, the monthly ceiling is the real bound) - never a second literal of 3/10/200. checkQuota takes the kind and compares against that kind's table; a loop spends the loop counter, not a plan. The Counters interface gains `kind` on read and `kind` + `tier` on reserve, and the DO's reserve RE-CHECKS the limit inside its transaction (read-then-reserve from the Worker is two round trips; two concurrent requests could both read 2 of 3). A refused reservation throws UpstreamPaused(quota_exhausted) -> 429 before any fetch. The global reserve likewise refuses inside its transaction once killSwitchTripped(current) -> 503. Order: device first, then global; either refusal leaves an over-count, the safe direction.
  - **R5 KV vs env kill switch.** `killSwitch(env)`: `env.KILL === "1"` pauses (the existing override, unchanged); otherwise, if a KV namespace is bound as `KILL_SWITCH`, its key `KILL` equal to "1" pauses, and a KV read that throws pauses (fail closed). Either source pauses - OR, not precedence - because "KV if bound" must never be able to UN-pause a deploy whose env says KILL=1. No KV namespace is added to wrangler.jsonc: creating one is a Cloudflare resource this task does not create; the owner binds it. The read happens once, first, before the body; guardedPlan's `killed` sees that one answer.
  - **R6 the place resolver.** D1 over the existing `DB` binding: table `places(id TEXT PRIMARY KEY, lat REAL NOT NULL, lon REAL NOT NULL)` in services/api/migrations/0001_places.sql (written, NOT applied - the owner runs `wrangler d1 migrations apply`). `SELECT lat, lon FROM places WHERE id = ?1`; no row -> null -> 404 unknown_place, zero upstream (unchanged). A row whose lat/lon is not a finite in-range number, or a D1 error (the table not yet created in production) -> the resolver throws and handlePlan answers 503 planning_unavailable with zero upstream calls and no reservation. Tests apply the SHIPPED migration file (imported ?raw), never a second copy of the DDL.
  - **R7 the secret header.** `x-scenic-router-secret`, exported once as ROUTER_SECRET_HEADER. The production fetchImpl adds it to EVERY upstream request (all of them pass through guardedPlan -> fetchImpl). Its value is the `ROUTER_SECRET` secret; no value is in the tree. The VPS half of P-COST-03 (Caddy refusing without it) is the routing box's, not this diff's.
  - **R8 "present".** Real deps exactly when QUOTA is bound, ROUTER_SECRET is a non-empty string, and ROUTER_URL parses as an https: URL whose hostname is not under `.invalid` (plus DB for /plan, which needs the resolver). wrangler.jsonc ships ROUTER_URL = "https://router.invalid" (RFC 2606 reserved, non-routable), and that placeholder counts as ABSENT - otherwise a deploy with the secret set but the URL forgotten would reserve a plan and then 502. So the shipped config still answers 503 planning_unavailable (the existing SELF tests are the "no ROUTER_SECRET" case on the real wrangler.jsonc).
  - **R9 the in-memory DurableObjectState fake.** `storage.get(key)` returns a structuredClone of the stored value (DO storage is structured-clone serialised, so a caller mutating what it read must not change storage); `storage.put(key, value)` stores a structuredClone; `storage.transaction(fn)` hands fn a txn with get/put over a STAGED copy, commits the staged copy only when fn resolves and discards it when fn throws. The fake namespace maps idFromName(name) -> one QuotaCounter per name, constructed over its own fake state. Tests assert the whole storage of every instance by exact equality after each call.
  - **R10 the population.** services/api/test/mutate/quotaMutants.mjs, the planMutants/loopMutants driver shape (vitest JSON named failures, STALE anchors refuse, tree checked clean, literal MIN_MUTATIONS, every SUBJECT mutated, --prove-vacuity, --prove-floor). Anchors in planMutants/loopMutants that this diff moves are re-pointed at the moved code, the same mutation.
